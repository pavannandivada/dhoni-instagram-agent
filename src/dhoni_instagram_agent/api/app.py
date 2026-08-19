from __future__ import annotations

from fastapi import FastAPI, HTTPException

from dhoni_instagram_agent.api.models import IngestionBatch
from dhoni_instagram_agent.config import Settings
from dhoni_instagram_agent.ingestion.service import ingest_batch

app = FastAPI(
    title="Dhoni Instagram Agent",
    version="0.1.0",
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
