from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireResearcher
from app.db.models import Job
from app.db.session import get_db
router = APIRouter()

class IngestRequest(BaseModel):
    source: str
    query: str = ""
    since: Optional[str] = None
    limit: int = 500

@router.post("", summary="Trigger data ingestion from a named connector")
async def trigger_ingest(req: IngestRequest, db: AsyncSession = Depends(get_db), _=RequireResearcher):
    from app.worker.tasks import ingest_source, run_ingest_pipeline
    from app.connectors.registry import CONNECTOR_REGISTRY
    import structlog
    log = structlog.get_logger()

    if req.source not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown source: '{req.source}'. Available: {list(CONNECTOR_REGISTRY.keys())}")

    job = Job(
        type="ingest",
        status="queued",
        payload={"source": req.source, "query": req.query, "since": req.since, "limit": req.limit},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        ingest_source.apply_async(
            kwargs={"source": req.source, "query": req.query, "since": req.since, "limit": req.limit, "job_id": job.id},
        )
    except Exception as exc:
        log.warning("celery_broker_not_ready_using_async_fallback", error=str(exc))
        import asyncio
        asyncio.create_task(
            run_ingest_pipeline(
                source=req.source,
                query=req.query,
                since=req.since,
                limit=req.limit,
                job_id=job.id,
            )
        )

    return {"job_id": job.id, "status": "queued", "source": req.source}
