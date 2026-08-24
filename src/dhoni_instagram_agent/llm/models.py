from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    system_instruction: str
    max_output_tokens: int = 500


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
