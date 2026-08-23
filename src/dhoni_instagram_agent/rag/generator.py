from __future__ import annotations

import json
import re

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.embeddings.service import search
from dhoni_instagram_agent.llm.models import LLMRequest
from dhoni_instagram_agent.llm.router import LLMRouter
from dhoni_instagram_agent.rag.models import (
    GroundedEvidence,
    RagGenerateResponse,
)

SYSTEM_INSTRUCTION = """
You write Instagram captions for an MS Dhoni fan account.

Use ONLY the supplied verified evidence.

Return ONLY the final caption.

Rules:
1. No invented facts.
2. No invented quotes.
3. No invented statistics.
4. No unsupported claims.
5. Write 2-3 complete sentences.
6. Keep it between 40 and 500 characters.
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
    def __init__(self, settings: Settings) -> None:
        self.router = LLMRouter(settings)

    @staticmethod
    def _clean_caption(text: str) -> str:
        caption = text.strip()

        if caption.startswith("```") and caption.endswith("```"):
            caption = caption[3:-3].strip()

        if len(caption) < 40:
            raise RuntimeError("Caption is too short.")

        if len(caption) > 500:
            raise RuntimeError("Caption is too long.")

        sentence_count = len(re.findall(r"[.!?](?:\s|$)", caption))

        if sentence_count not in {2, 3}:
            raise RuntimeError("Caption must contain 2-3 complete sentences.")

        for prefix in BAD_PREFIXES:
            if caption.lower().startswith(prefix):
                raise RuntimeError(f"Invalid caption prefix returned: {prefix}")

        return caption

    def _build_prompt(
        self,
        request: str,
        evidence: list[GroundedEvidence],
    ) -> str:
        evidence_payload = [
            {
                "knowledge_id": item.knowledge_id,
                "content": item.content,
                "source_url": item.source_url,
                "verification_status": item.verification_status,
            }
            for item in evidence
        ]

        return f"""
User request:
{request}

Verified evidence:
{json.dumps(evidence_payload, ensure_ascii=False, indent=2)}

Write ONE Instagram caption.

Requirements:
- 2-3 complete sentences
- 40-500 characters
- natural fan-account tone
- use ONLY the verified evidence
- do not strengthen or reinterpret claims
- no invented facts
- no fake quotes
- no invented statistics
- no analysis
- no headings
- no drafting text
- return ONLY the caption
"""

    def generate(
        self,
        request: str,
        top_k: int = 5,
    ) -> RagGenerateResponse:
        retrieved = search(
            Settings(),
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

        verified_evidence = [item for item in evidence if item.verification_status == "VERIFIED"]

        if not verified_evidence:
            return RagGenerateResponse(
                request=request,
                caption="",
                grounded=False,
                evidence=evidence,
                evidence_ids=[item.knowledge_id for item in evidence],
                notes=[
                    "No VERIFIED evidence available.",
                    "Human verification required before generation.",
                ],
            )

        generation_evidence = verified_evidence[:2]

        result = self.router.generate(
            LLMRequest(
                prompt=self._build_prompt(
                    request,
                    generation_evidence,
                ),
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=300,
            )
        )

        print(f"RAG writer provider={result.provider} model={result.model}")

        caption = self._clean_caption(result.text)

        return RagGenerateResponse(
            request=request,
            caption=caption,
            grounded=True,
            evidence=verified_evidence,
            evidence_ids=[item.knowledge_id for item in verified_evidence],
            notes=[
                "Generated from VERIFIED evidence.",
                "Automatic LLM critic disabled; human review required before publishing.",
            ],
        )
