from __future__ import annotations

import json
import re

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.llm.models import LLMRequest
from dhoni_instagram_agent.llm.router import LLMRouter
from dhoni_instagram_agent.rag.grounding import check_grounding
from dhoni_instagram_agent.rag.models import CriticResult

SYSTEM_INSTRUCTION = """
You are a strict factual critic for an MS Dhoni Instagram account.

Check ONLY factual support.

Return exactly:

STATUS: PASS
ISSUES: none

OR

STATUS: REVISE
ISSUES:
- clear reason

Do not use vague labels.
"""


class GroundingCritic:
    def __init__(self, settings: Settings) -> None:
        self.router = LLMRouter(settings)

    @staticmethod
    def _deterministic_checks(caption: str) -> list[str]:
        issues: list[str] = []

        text = caption.strip()

        if len(text) < 40:
            issues.append("Caption is shorter than 40 characters.")

        if len(text) > 500:
            issues.append("Caption is longer than 500 characters.")

        sentence_count = len(re.findall(r"[.!?](?:\s|$)", text))

        if sentence_count < 2:
            issues.append("Caption must contain at least 2 complete sentences.")

        if text.startswith(('"', "'", "“", "‘")) and text.endswith(('"', "'", "”", "’")):
            issues.append("Caption is wrapped in unnecessary quotation marks.")

        return issues

    def evaluate(
        self,
        caption: str,
        evidence: list[dict],
    ) -> CriticResult:
        deterministic_issues = self._deterministic_checks(caption)

        if deterministic_issues:
            return CriticResult(
                status="REVISE",
                issues=deterministic_issues,
            )

        grounding = check_grounding(
            caption=caption,
            evidence=evidence,
        )

        # Exact/supporting evidence found.
        # Do not let an LLM critic reject a claim explicitly supported
        # by the knowledge base.
        if grounding.supported:
            return CriticResult(
                status="PASS",
                issues=[],
            )

        prompt = f"""
CAPTION:
{caption}

EVIDENCE:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

Check every factual claim in the caption.

Reject:
- unsupported facts
- unsupported statistics
- unsupported quotes
- claims stronger than the evidence supports

Approve only when factual claims are supported.
"""

        result = self.router.generate(
            LLMRequest(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=300,
            )
        )

        print(f"RAG critic provider={result.provider} model={result.model}")

        raw = result.text.strip()

        status = "REVISE"
        issues: list[str] = []

        lines = [line.strip() for line in raw.splitlines() if line.strip()]

        for line in lines:
            upper = line.upper()

            if upper.startswith("STATUS:"):
                value = line.split(":", 1)[1].strip().upper()

                if value in {"PASS", "REVISE"}:
                    status = value

            elif upper.startswith("ISSUES:"):
                value = line.split(":", 1)[1].strip()

                if value.lower() not in {"none", ""}:
                    issues.append(value)

            elif line.startswith("- "):
                issues.append(line[2:].strip())

        if not issues and status == "REVISE":
            issues.append("LLM critic rejected the caption without a clear reason.")

        return CriticResult(
            status=status,
            issues=issues,
        )
