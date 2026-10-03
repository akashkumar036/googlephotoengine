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


@router.post("/cluster", summary="Trigger semantic clustering and problem discovery")
async def trigger_clustering(
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
):
    job_id = _uuid()
    job = Job(
        id=job_id,
        type="clustering",
        status="queued",
        progress=0.0,
        payload={},
    )
    db.add(job)
    await db.commit()

    dispatched = False
    try:
        from app.worker.tasks import cluster_conversations
        cluster_conversations.apply_async(kwargs={"job_id": job_id})
        dispatched = True
    except Exception:
        pass

    if not dispatched:
        async def _background_cluster(jid: str):
            from app.db.session import AsyncSessionLocal
            from app.pipeline.clustering import run_semantic_clustering
            from app.pipeline.problem_discovery import run_problem_discovery
            from app.pipeline.taxonomy import run_taxonomy_assignment
            from app.pipeline.unknown_unknowns import run_unknown_unknowns_detection
            from app.pipeline.ingestion import update_job_status
            try:
                async with AsyncSessionLocal() as session:
                    await update_job_status(session, jid, "running", 0.1)
                    await session.commit()
                    c_res = await run_semantic_clustering(session)
                    await update_job_status(session, jid, "running", 0.4)
                    await session.commit()
                    p_res = await run_problem_discovery(session)
                    await update_job_status(session, jid, "running", 0.7)
                    await session.commit()
                    t_res = await run_taxonomy_assignment(session)
                    u_res = await run_unknown_unknowns_detection(session)
                    res = {
                        "clusters": c_res,
                        "problems": p_res,
                        "taxonomy": t_res,
                        "unknown_unknowns": u_res,
                    }
                    await update_job_status(session, jid, "done", 1.0, payload_update=res)
                    await session.commit()
            except Exception as e:
                async with AsyncSessionLocal() as session:
                    await update_job_status(session, jid, "failed", error=str(e))
                    await session.commit()

        asyncio.create_task(_background_cluster(job_id))

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Clustering and problem discovery job queued",
    }


@router.post("/trends", summary="Trigger trend and emerging problem detection")
async def trigger_trends(
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
):
    job_id = _uuid()
    job = Job(
        id=job_id,
        type="trend_detection",
        status="queued",
        progress=0.0,
        payload={},
    )
    db.add(job)
    await db.commit()

    dispatched = False
    try:
        from app.worker.tasks import detect_trends
        detect_trends.apply_async(kwargs={"job_id": job_id})
        dispatched = True
    except Exception:
        pass

    if not dispatched:
        async def _background_trends(jid: str):
            from app.db.session import AsyncSessionLocal
            from app.pipeline.trend_detection import run_trend_detection
            from app.pipeline.emerging_detection import run_emerging_detection
            from app.pipeline.ingestion import update_job_status
            try:
                async with AsyncSessionLocal() as session:
                    await update_job_status(session, jid, "running", 0.2)
                    await session.commit()
                    t_res = await run_trend_detection(session)
                    await update_job_status(session, jid, "running", 0.7)
                    await session.commit()
                    e_res = await run_emerging_detection(session)
                    res = {"trends": t_res, "emerging": e_res}
                    await update_job_status(session, jid, "done", 1.0, payload_update=res)
                    await session.commit()
            except Exception as e:
                async with AsyncSessionLocal() as session:
                    await update_job_status(session, jid, "failed", error=str(e))
                    await session.commit()

        asyncio.create_task(_background_trends(job_id))

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Trend detection job queued",
    }
