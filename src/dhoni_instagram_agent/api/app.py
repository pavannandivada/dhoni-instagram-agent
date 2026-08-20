from __future__ import annotations

from fastapi import FastAPI, HTTPException

from dhoni_instagram_agent.api.models import (
    EmbeddingIndexRequest,
    IngestionBatch,
    RetrievalRequest,
)
from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.embeddings.service import (
    index_pending_documents,
    search,
)
from dhoni_instagram_agent.ingestion.service import ingest_batch

app = FastAPI(
    title="Dhoni Instagram Agent",
    version="0.2.0",
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
