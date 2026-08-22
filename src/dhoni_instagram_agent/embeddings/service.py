from __future__ import annotations

import json
from typing import Any

import psycopg

from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.embeddings.client import GeminiEmbeddingClient


def _vector_literal(values: list[float]) -> str:
    return json.dumps(values, separators=(",", ":"))


def index_pending_documents(
    settings: Settings,
    limit: int = 50,
) -> dict[str, int]:
    client = GeminiEmbeddingClient(settings)

    indexed = 0
    skipped = 0

    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    kd.id,
                    kd.title,
                    kd.content,
                    kd.content_hash
                FROM knowledge_documents kd
                LEFT JOIN knowledge_embeddings ke
                    ON ke.knowledge_document_id = kd.id
                   AND ke.embedding_model = %s
                WHERE ke.id IS NULL
                   OR ke.content_hash <> kd.content_hash
                ORDER BY kd.created_at
                LIMIT %s
                """,
                (settings.embedding_model, limit),
            )

            documents = cursor.fetchall()

            for document_id, title, content, content_hash in documents:
                result = client.embed_document(
                    title=title,
                    content=content,
                )

                cursor.execute(
                    """
                    INSERT INTO knowledge_embeddings (
                        knowledge_document_id,
                        embedding_model,
                        embedding_dimension,
                        content_hash,
                        embedding
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::vector
                    )
                    ON CONFLICT (
                        knowledge_document_id,
                        embedding_model
                    )
                    DO UPDATE SET
                        embedding_dimension = EXCLUDED.embedding_dimension,
                        content_hash = EXCLUDED.content_hash,
                        embedding = EXCLUDED.embedding,
                        updated_at = now()
                    """,
                    (
                        document_id,
                        result.model,
                        result.dimension,
                        content_hash,
                        _vector_literal(result.values),
                    ),
                )

                indexed += 1

        connection.commit()

    if not documents:
        skipped = 1

    return {
        "indexed": indexed,
        "skipped": skipped,
    }


def search(
    settings: Settings,
    query: str,
    *,
    collection: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    client = GeminiEmbeddingClient(settings)
    embedding = client.embed_query(query)
    query_vector = _vector_literal(embedding.values)

    top_k = max(1, min(top_k, 50))

    with psycopg.connect(settings.database_url) as connection, connection.cursor() as cursor:
        if collection:
            cursor.execute(
                """
                    SELECT
                        kd.id,
                        kd.source_collection,
                        kd.content,
                        kd.title,
                        kd.source_url,
                        kd.verification_status,
                        1 - (ke.embedding <=> %s::vector) AS score
                    FROM knowledge_embeddings ke
                    JOIN knowledge_documents kd
                      ON kd.id = ke.knowledge_document_id
                    WHERE ke.embedding_model = %s
                      AND kd.source_collection = %s
                    ORDER BY ke.embedding <=> %s::vector
                    LIMIT %s
                    """,
                (
                    query_vector,
                    settings.embedding_model,
                    collection,
                    query_vector,
                    top_k,
                ),
            )
        else:
            cursor.execute(
                """
                    SELECT
                        kd.id,
                        kd.source_collection,
                        kd.content,
                        kd.title,
                        kd.source_url,
                        kd.verification_status,
                        1 - (ke.embedding <=> %s::vector) AS score
                    FROM knowledge_embeddings ke
                    JOIN knowledge_documents kd
                      ON kd.id = ke.knowledge_document_id
                    WHERE ke.embedding_model = %s
                    ORDER BY ke.embedding <=> %s::vector
                    LIMIT %s
                    """,
                (
                    query_vector,
                    settings.embedding_model,
                    query_vector,
                    top_k,
                ),
            )

        rows = cursor.fetchall()

    return [
        {
            "knowledge_id": str(row[0]),
            "collection": row[1],
            "content": row[2],
            "title": row[3],
            "source_url": row[4],
            "verification_status": row[5],
            "score": float(row[6]),
        }
        for row in rows
    ]
