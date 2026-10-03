from __future__ import annotations
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from app.db.models import Conversation, Job
from app.db.session import AsyncSessionLocal
from app.pipeline.analysis import (
    analyze_deep_stage,
    analyze_relevance_stage,
    generate_embeddings_stage,
)
from app.pipeline.cleaning import clean_text
from app.pipeline.ingestion import deduplicate_and_store, get_or_create_source, update_job_status

logger = logging.getLogger(__name__)


async def run_full_pipeline(
    source: str,
    query: str = "",
    since: Optional[datetime] = None,
    limit: int = 500,
    job_id: Optional[str] = None,
    run_embeddings: bool = True,
    session_factory=None,
) -> Dict[str, Any]:
    """
    Master pipeline orchestrator:
    1. Ingestion via Connector
    2. Deduplication & Storage
    3. 8-Step Cleaning Pipeline
    4. Stage 1 Relevance Classification
    5. Stage 2 Deep UX Problem Analysis
    6. Stage 3 Vector Embedding Generation
    """
    from app.connectors.registry import CONNECTOR_REGISTRY

    if source not in CONNECTOR_REGISTRY:
        raise ValueError(f"Unknown source connector: {source}")

    sf = session_factory or AsyncSessionLocal
    logger.info("Starting full pipeline for source: %s, job_id: %s", source, job_id)

    # 1. Update job to running
    if job_id:
        async with sf() as session:
            await update_job_status(session, job_id, "running", 0.05, payload_update={"stage": "fetching"})
            await session.commit()

    # 2. Fetch records
    connector_cls = CONNECTOR_REGISTRY[source]
    connector = connector_cls()
    records = connector.run(query=query, since=since, limit=limit)

    stored_ids: List[str] = []
    skipped = 0
    errors = 0
    source_id = None

    # 3. Ingestion + Dedup + Cleaning
    async with sf() as session:
        db_source = await get_or_create_source(session, source, getattr(connector, "source_name", source))
        if db_source:
            source_id = db_source.id

        for rec in records:
            try:
                conv_id = await deduplicate_and_store(session, rec, db_source)
                if conv_id:
                    stored_ids.append(conv_id)
                else:
                    skipped += 1
            except Exception as exc:
                logger.error("Error ingesting record: %s", exc)
                errors += 1

        await session.commit()

    if job_id:
        async with sf() as session:
            await update_job_status(
                session,
                job_id,
                "running",
                0.25,
                payload_update={"stage": "cleaned", "stored_count": len(stored_ids), "skipped": skipped},
            )
            await session.commit()

    # If no records were stored, load existing records for this source to ensure downstream stages can run
    target_ids = list(stored_ids)
    if not target_ids:
        async with sf() as session:
            q_stmt = select(Conversation.id).limit(limit)
            if source_id:
                q_stmt = q_stmt.where(Conversation.source_id == source_id)
            res = await session.execute(q_stmt)
            target_ids = [row[0] for row in res.fetchall()]

    # 4. Stage 1: Relevance Filter
    rel_stats = {"total": 0, "relevant": 0}
    if target_ids:
        if job_id:
            async with sf() as session:
                await update_job_status(session, job_id, "running", 0.40, payload_update={"stage": "relevance"})
                await session.commit()

        async with sf() as session:
            rel_stats = await analyze_relevance_stage(session, target_ids)

    # 5. Stage 2: Deep Analysis
    deep_stats = {"analyzed": 0}
    if target_ids:
        if job_id:
            async with sf() as session:
                await update_job_status(session, job_id, "running", 0.70, payload_update={"stage": "deep_analysis"})
                await session.commit()

        async with sf() as session:
            deep_stats = await analyze_deep_stage(session, target_ids)

    # 6. Stage 3: Embedding Generation
    embed_stats = {"embedded": 0, "reused": 0}
    if target_ids and run_embeddings:
        if job_id:
            async with sf() as session:
                await update_job_status(session, job_id, "running", 0.90, payload_update={"stage": "embedding"})
                await session.commit()

        async with sf() as session:
            embed_stats = await generate_embeddings_stage(session, target_ids)

    # 7. Complete Job
    final_payload = {
        "source": source,
        "records_fetched": len(records),
        "records_stored": len(stored_ids),
        "records_skipped": skipped,
        "records_error": errors,
        "relevance": rel_stats,
        "deep_analysis": deep_stats,
        "embeddings": embed_stats,
    }

    if job_id:
        async with sf() as session:
            await update_job_status(session, job_id, "done", 1.0, payload_update=final_payload)
            await session.commit()

    logger.info("Pipeline completed successfully for %s: %s", source, final_payload)
    return final_payload
