from __future__ import annotations

from google import genai
from google.genai import types

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.embeddings.models import EmbeddingResult


class GeminiEmbeddingClient:
    """Adapter around Google's Gemini embedding API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(),
        )

    def _embed(
        self,
        text: str,
    ) -> EmbeddingResult:
        result = self.client.models.embed_content(
            model=self.settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=self.settings.embedding_dimension,
            ),
        )

        if not result.embeddings:
            raise RuntimeError("Gemini returned no embeddings.")

        values = result.embeddings[0].values

        if values is None:
            raise RuntimeError("Gemini returned an embedding without values.")

        if len(values) != self.settings.embedding_dimension:
            raise RuntimeError(
                "Unexpected embedding dimension: "
                f"expected {self.settings.embedding_dimension}, "
                f"got {len(values)}"
            )

        return EmbeddingResult(
            model=self.settings.embedding_model,
            dimension=len(values),
            values=list(values),
        )

    def embed_document(
        self,
        *,
        title: str | None,
        content: str,
    ) -> EmbeddingResult:
        text = f"title: {title or ''} | text: {content}"
        return self._embed(text)

    def embed_query(self, query: str) -> EmbeddingResult:
        text = f"task: search result | query: {query}"
        return self._embed(text)
