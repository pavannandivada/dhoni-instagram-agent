from __future__ import annotations

import requests
from anthropic import Anthropic
from google import genai
from google.genai import types
from openai import OpenAI

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.llm.models import LLMRequest, LLMResponse


class LLMRouter:
    """Try cloud providers, then fall back to local Ollama."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        self.gemini = genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(),
        )

        self.openai = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
        )

        self.anthropic = Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
        )

    def _gemini(self, request: LLMRequest) -> LLMResponse:
        response = self.gemini.models.generate_content(
            model=self.settings.generation_model,
            contents=request.prompt,
            config=types.GenerateContentConfig(
                system_instruction=request.system_instruction,
                max_output_tokens=request.max_output_tokens,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned empty response.")

        return LLMResponse(
            text=response.text.strip(),
            provider="gemini",
            model=self.settings.generation_model,
        )

    def _openai(self, request: LLMRequest) -> LLMResponse:
        response = self.openai.responses.create(
            model="gpt-4.1-mini",
            instructions=request.system_instruction,
            input=request.prompt,
            max_output_tokens=request.max_output_tokens,
        )

        text = response.output_text.strip()

        if not text:
            raise RuntimeError("OpenAI returned empty response.")

        return LLMResponse(
            text=text,
            provider="openai",
            model="gpt-4.1-mini",
        )

    def _anthropic(self, request: LLMRequest) -> LLMResponse:
        response = self.anthropic.messages.create(
            model="claude-3-5-haiku-latest",
            system=request.system_instruction,
            max_tokens=request.max_output_tokens,
            messages=[
                {
                    "role": "user",
                    "content": request.prompt,
                }
            ],
        )

        text_parts = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ]

        text = "\n".join(text_parts).strip()

        if not text:
            raise RuntimeError("Anthropic returned empty response.")

        return LLMResponse(
            text=text,
            provider="anthropic",
            model="claude-3-5-haiku-latest",
        )

    def _ollama(self, request: LLMRequest) -> LLMResponse:
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/generate",
            json={
                "model": self.settings.ollama_model,
                "prompt": (
                    f"{request.system_instruction}\n\n"
                    f"{request.prompt}"
                ),
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()
        text = str(data.get("response", "")).strip()

        if not text:
            raise RuntimeError("Ollama returned empty response.")

        return LLMResponse(
            text=text,
            provider="ollama",
            model=self.settings.ollama_model,
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        providers = (
            self._gemini,
            self._openai,
            self._anthropic,
            self._ollama,
        )

        errors: list[str] = []

        for provider in providers:
            try:
                result = provider(request)

                print(
                    f"LLM provider={result.provider} "
                    f"model={result.model}"
                )

                return result

            except Exception as error:
                name = provider.__name__.lstrip("_")
                print(f"LLM provider failed: {name}: {error}")
                errors.append(f"{name}: {error}")

        raise RuntimeError(
            "All LLM providers failed: " + " | ".join(errors)
        )
