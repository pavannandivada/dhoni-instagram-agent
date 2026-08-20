from __future__ import annotations

import json

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.llm.models import LLMRequest
from dhoni_instagram_agent.llm.router import LLMRouter
from dhoni_instagram_agent.rag.models import CriticResult


SYSTEM_INSTRUCTION = """
You are a strict fact-checking critic for an MS Dhoni Instagram account.

Check the caption ONLY against the supplied evidence.

PASS only when:
1. All factual claims are supported.
2. No quote is invented.
3. No statistic is invented.
4. Caption is complete.
5. Caption has at least 2 complete sentences.
6. Caption is between 40 and 500 characters.

REVISE when any rule fails.

Return only:

STATUS: PASS
ISSUES: none

OR

STATUS: REVISE
ISSUES:
- issue 1
- issue 2
"""


class GroundingCritic:
    """Check caption facts and basic caption quality using the LLM router."""

    def __init__(self, settings: Settings) -> None:
        self.router = LLMRouter(settings)

    def evaluate(
        self,
        caption: str,
        evidence: list[dict],
    ) -> CriticResult:

        prompt = f"""
CAPTION:
{caption}

EVIDENCE:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

Check:
- Are all facts supported?
- Is any quote invented?
- Is any statistic unsupported?
- Is the caption complete?
- Does it contain at least 2 complete sentences?
- Is it between 40 and 500 characters?
"""

        result = self.router.generate(
            LLMRequest(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=300,
            )
        )

        print(
            f"RAG critic provider={result.provider} "
            f"model={result.model}"
        )

        raw = result.text.strip()

        lines = [
            line.strip()
            for line in raw.splitlines()
            if line.strip()
        ]

        status = "REVISE"
        issues: list[str] = []

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

        return CriticResult(
            status=status,
            issues=issues,
        )
