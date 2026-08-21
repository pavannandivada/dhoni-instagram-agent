from __future__ import annotations

import json

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.embeddings.service import search
from dhoni_instagram_agent.llm.models import LLMRequest
from dhoni_instagram_agent.llm.router import LLMRouter
from dhoni_instagram_agent.rag.critic import GroundingCritic
from dhoni_instagram_agent.rag.models import (
    GroundedEvidence,
    RagGenerateResponse,
)


SYSTEM_INSTRUCTION = """
You write Instagram captions for an MS Dhoni fan account.

Use ONLY the supplied evidence.

Return ONLY the final caption.

DO NOT return:
- analysis
- reasoning
- drafting notes
- headings
- labels
- markdown
- "drafting sentences"
- "checking constraints"

Rules:
1. No invented facts.
2. No invented quotes.
3. No invented statistics.
4. No unsupported claims.
5. Write 2-3 complete short sentences.
6. Keep it under 500 characters.
"""


BAD_PREFIXES = (
    "drafting sentences",
    "checking constraints",
    "thinking",
    "analysis:",
    "final answer:",
    "here is",
)


class GroundedGenerator:
    MAX_REVISIONS = 2

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router = LLMRouter(settings)
        self.critic = GroundingCritic(settings)

    @staticmethod
    def _clean_caption(text: str) -> str:
        caption = text.strip()

        for prefix in BAD_PREFIXES:
            if caption.lower().startswith(prefix):
                raise RuntimeError(
                    f"Invalid caption prefix returned: {prefix}"
                )

        if caption.startswith("```") and caption.endswith("```"):
            caption = caption[3:-3].strip()

        if len(caption) < 20:
            raise RuntimeError("Caption is too short.")

        if len(caption) > 500:
            raise RuntimeError("Caption is too long.")

        return caption

    def _generate(self, prompt: str) -> str:
        result = self.router.generate(
            LLMRequest(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=300,
            )
        )

        print(
            f"RAG writer provider={result.provider} "
            f"model={result.model}"
        )

        return self._clean_caption(result.text)

    def _build_prompt(
        self,
        request: str,
        evidence: list[GroundedEvidence],
        previous_caption: str | None = None,
        critic_issues: list[str] | None = None,
    ) -> str:
        evidence_payload = [
            {
                "knowledge_id": item.knowledge_id,
                "content": item.content,
                "source_url": item.source_url,
                "verification_status": item.verification_status,
                "score": item.score,
            }
            for item in evidence
        ]

        revision = ""

        if previous_caption:
            revision = f"""
Previous caption:
{previous_caption}

Critic issues:
{json.dumps(critic_issues or [], ensure_ascii=False)}

Rewrite it.
Return ONLY the final caption.
"""

        return f"""
User request:
{request}

Relevant verified evidence:
{json.dumps(evidence_payload, ensure_ascii=False, indent=2)}

Write ONE final Instagram caption.

Requirements:
- 2-3 complete sentences
- 20-500 characters
- natural fan-account tone
- use ONLY the relevant evidence
- no unsupported claims
- no fake quotes
- no invented statistics
- no analysis
- no drafting text
{revision}
"""

    def generate(
        self,
        request: str,
        top_k: int = 5,
    ) -> RagGenerateResponse:

        retrieved = search(
            self.settings,
            request,
            top_k=top_k,
        )

        evidence = [
            GroundedEvidence(
                knowledge_id=item["knowledge_id"],
                collection=item["collection"],
                content=item["content"],
                source_url=item["source_url"],
                verification_status=item["verification_status"],
                score=item["score"],
            )
            for item in retrieved
        ]

        verified_evidence = [
            item
            for item in evidence
            if item.verification_status == "VERIFIED"
        ]

        if not verified_evidence:
            return RagGenerateResponse(
                request=request,
                caption="",
                grounded=False,
                evidence=evidence,
                evidence_ids=[
                    item.knowledge_id for item in evidence
                ],
                notes=[
                    "No VERIFIED evidence available.",
                    "Human verification required before generation.",
                ],
            )

        # Keep all verified evidence in the API response,
        # but give only the top 2 relevant facts to writer + critic.
        generation_evidence = verified_evidence[:2]

        caption = self._generate(
            self._build_prompt(
                request,
                generation_evidence,
            )
        )

        for revision in range(self.MAX_REVISIONS + 1):

            critic_result = self.critic.evaluate(
                caption=caption,
                evidence=[
                    item.model_dump()
                    for item in generation_evidence
                ],
            )

            if critic_result.status == "PASS":
                return RagGenerateResponse(
                    request=request,
                    caption=caption,
                    grounded=True,
                    evidence=verified_evidence,
                    evidence_ids=[
                        item.knowledge_id
                        for item in verified_evidence
                    ],
                    notes=[
                        f"Critic PASS after {revision} revision(s)."
                    ],
                )

            if revision == self.MAX_REVISIONS:
                return RagGenerateResponse(
                    request=request,
                    caption=caption,
                    grounded=False,
                    evidence=verified_evidence,
                    evidence_ids=[
                        item.knowledge_id
                        for item in verified_evidence
                    ],
                    notes=[
                        "Critic could not approve the caption.",
                        *critic_result.issues,
                    ],
                )

            caption = self._generate(
                self._build_prompt(
                    request,
                    generation_evidence,
                    previous_caption=caption,
                    critic_issues=critic_result.issues,
                )
            )

        raise RuntimeError("Unexpected RAG revision state.")
