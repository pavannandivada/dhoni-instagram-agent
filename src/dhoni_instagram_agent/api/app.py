from __future__ import annotations

from datetime import date, time

from fastapi import FastAPI, HTTPException

from dhoni_instagram_agent.api.models import (
    ContentCalendarCreateRequest,
    ContentCalendarUpdateRequest,
    EmbeddingIndexRequest,
    IngestionBatch,
    RagCriticRequest,
    RagGenerateRequest,
    RetrievalRequest,
)
from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.content_calendar.repository import (
    create_post,
    list_posts,
    update_post,
)
from dhoni_instagram_agent.embeddings.service import (
    index_pending_documents,
    search,
)
from dhoni_instagram_agent.ingestion.service import ingest_batch
from dhoni_instagram_agent.publishing.assets import (
    attach_available_asset,
)
from dhoni_instagram_agent.publishing.service import (
    publish_post,
)
from dhoni_instagram_agent.rag.critic import GroundingCritic
from dhoni_instagram_agent.rag.generator import GroundedGenerator

app = FastAPI(
    title="Dhoni Instagram Agent",
    version="0.3.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ingestion/batch")
def ingest(batch: IngestionBatch) -> dict[str, object]:
    try:
        return ingest_batch(
            Settings(),
            batch.source_system,
            batch.source_collection,
            batch.records,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/v1/embeddings/index")
def index_embeddings(
    request: EmbeddingIndexRequest,
) -> dict[str, int]:
    try:
        return index_pending_documents(
            Settings(),
            limit=request.limit,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Embedding indexing failed: {error}",
        ) from error


@app.post("/v1/retrieval/search")
def retrieval_search(
    request: RetrievalRequest,
) -> dict[str, object]:
    try:
        results = search(
            Settings(),
            request.query,
            collection=request.collection,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "count": len(results),
            "results": results,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {error}",
        ) from error


@app.post("/v1/rag/generate")
def generate_rag(
    request: RagGenerateRequest,
) -> dict[str, object]:
    try:
        result = GroundedGenerator(Settings()).generate(
            request=request.request,
            top_k=request.top_k,
        )

        return result.model_dump()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG generation failed: {error}",
        ) from error


@app.post("/v1/rag/critic")
def critic(
    request: RagCriticRequest,
) -> dict[str, object]:
    try:
        evidence = [item.model_dump() for item in request.evidence]

        result = GroundingCritic(Settings()).evaluate(
            caption=request.caption,
            evidence=evidence,
        )

        return result.model_dump()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG critic failed: {error}",
        ) from error


@app.post("/v1/content-calendar")
def create_content_calendar_post(
    request: ContentCalendarCreateRequest,
) -> dict[str, object]:
    try:
        scheduled_date = (
            date.fromisoformat(request.scheduled_date) if request.scheduled_date else None
        )
        scheduled_time = (
            time.fromisoformat(request.scheduled_time) if request.scheduled_time else None
        )

        settings = Settings()

        import psycopg

        with psycopg.connect(settings.database_url) as connection:
            return create_post(
                connection,
                post_id=request.post_id,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                content_type=request.content_type,
                topic=request.topic,
                quote_stat=request.quote_stat,
                source_url=request.source_url,
                asset_id=request.asset_id,
                caption=request.caption,
                overlay_text=request.overlay_text,
                status=request.status,
            )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Content calendar create failed: {error}",
        ) from error


@app.get("/v1/content-calendar")
def get_content_calendar(
    status: str | None = None,
) -> list[dict[str, object]]:
    try:
        settings = Settings()

        import psycopg

        with psycopg.connect(settings.database_url) as connection:
            return list_posts(connection, status=status)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Content calendar list failed: {error}",
        ) from error


@app.patch("/v1/content-calendar/{post_id}")
def patch_content_calendar(
    post_id: str,
    request: ContentCalendarUpdateRequest,
) -> dict[str, object]:
    try:
        updates = request.model_dump(exclude_none=True)

        if "scheduled_date" in updates:
            updates["scheduled_date"] = date.fromisoformat(updates["scheduled_date"])

        if "scheduled_time" in updates:
            updates["scheduled_time"] = time.fromisoformat(updates["scheduled_time"])

        settings = Settings()

        import psycopg

        with psycopg.connect(settings.database_url) as connection:
            result = update_post(
                connection,
                post_id,
                updates,
            )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Post not found: {post_id}",
            )

        return result

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Content calendar update failed: {error}",
        ) from error


@app.post("/v1/content-calendar/{post_id}/attach-asset")
def attach_content_calendar_asset(
    post_id: str,
) -> dict[str, object]:
    try:
        import psycopg

        settings = Settings()

        with psycopg.connect(settings.database_url) as connection:
            return attach_available_asset(
                connection,
                post_id,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Asset attachment failed: {error}",
        ) from error


@app.post("/v1/instagram/publish/{post_id}")
def publish_instagram_post(
    post_id: str,
    dry_run: bool = True,
) -> dict[str, object]:
    try:
        import psycopg

        settings = Settings()

        with psycopg.connect(settings.database_url) as connection:
            return publish_post(
                connection,
                post_id,
                dry_run=dry_run,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Instagram publishing failed: {error}",
        ) from error
