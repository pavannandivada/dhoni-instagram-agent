from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TypedDict


class EvidenceItem(TypedDict):
    content: str
    knowledge_id: str


@dataclass(frozen=True)
class GroundingResult:
    supported: bool
    matched_evidence_ids: list[str]
    issues: list[str]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def check_grounding(
    caption: str,
    evidence: list[EvidenceItem],
) -> GroundingResult:
    """
    Conservative lexical grounding check.

    It looks for meaningful evidence phrases inside the caption.
    It does not replace semantic review; it prevents an LLM critic
    from rejecting claims that are explicitly present in evidence.
    """

    caption_normalized = _normalize(caption)

    matched_ids: list[str] = []

    for item in evidence:
        content = _normalize(item.get("content", ""))

        if not content:
            continue

        phrases = [
            phrase.strip() for phrase in re.split(r"[.!?;]", content) if len(phrase.strip()) >= 20
        ]

        matched = False

        for phrase in phrases:
            if phrase in caption_normalized:
                matched = True
                break

        if matched:
            matched_ids.append(item["knowledge_id"])

    if matched_ids:
        return GroundingResult(
            supported=True,
            matched_evidence_ids=matched_ids,
            issues=[],
        )

    return GroundingResult(
        supported=False,
        matched_evidence_ids=[],
        issues=["No substantial caption phrase was found directly in the supplied evidence."],
    )
