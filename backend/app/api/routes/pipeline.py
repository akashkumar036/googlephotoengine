from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireResearcher
from app.connectors.registry import CONNECTOR_REGISTRY
from app.db.models import Job, _uuid
from app.db.session import get_db

router = APIRouter()


class PipelineRunRequest(BaseModel):
    source: str = Field(..., description="Connector source name: demo, reddit, google_play, app_store")
    query: Optional[str] = Field("", description="Search term or filter query")
    since: Optional[datetime] = Field(None, description="ISO timestamp cutoff for fetching records")
    limit: int = Field(500, ge=1, le=5000, description="Max records to process")
    run_embeddings: bool = Field(True, description="Whether to generate vector embeddings")


@router.post("/run", summary="Trigger end-to-end pipeline (ingest -> clean -> relevance -> deep -> embed)")
async def trigger_pipeline(
    payload: PipelineRunRequest,
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
):
    if payload.source not in CONNECTOR_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source '{payload.source}'. Available sources: {list(CONNECTOR_REGISTRY.keys())}",
        )

    # 1. Create Job record in database
    job_id = _uuid()
    job = Job(
        id=job_id,
        type="full_pipeline",
        status="queued",
        progress=0.0,
        payload={
            "source": payload.source,
            "query": payload.query,
            "since": payload.since.isoformat() if payload.since else None,
            "limit": payload.limit,
            "run_embeddings": payload.run_embeddings,
        },
    )
    db.add(job)
    await db.commit()

    # 2. Try dispatching via Celery worker
    dispatched = False
    try:
        from app.worker.tasks import run_pipeline_chain
        run_pipeline_chain.apply_async(
            kwargs={
                "source": payload.source,
                "query": payload.query,
                "since": payload.since,
                "limit": payload.limit,
                "job_id": job_id,
            }
        )
        dispatched = True
    except Exception:
        # Fallback to in-process background task if Celery broker is offline
        pass

    if not dispatched:
        from app.pipeline.orchestrator import run_full_pipeline

        asyncio.create_task(
            run_full_pipeline(
                source=payload.source,
                query=payload.query,
                since=payload.since,
                limit=payload.limit,
                job_id=job_id,
                run_embeddings=payload.run_embeddings,
            )
        )

    return {
        "job_id": job_id,
        "status": "queued",
        "source": payload.source,
        "message": f"Full pipeline queued for source '{payload.source}'",
    }
