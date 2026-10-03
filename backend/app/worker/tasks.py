from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Optional
import structlog
from app.worker.celery_app import celery_app
log = structlog.get_logger()

def _run_async(coro):
    """Run an async coroutine synchronously, even if an event loop is already active."""
    import concurrent.futures
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


async def run_ingest_pipeline(
    source: str,
    query: str = "",
    since: Optional[str] = None,
    limit: int = 500,
    job_id: Optional[str] = None,
    session_factory=None,
) -> dict:
    """
    Core async ingestion workflow:
    1. Resolve connector from registry
    2. Fetch and normalize records
    3. Persist sources and deduplicate records
    4. Update job status and progress in DB
    """
    from app.connectors.registry import CONNECTOR_REGISTRY, SOURCE_METADATA
    from app.db.session import AsyncSessionLocal
    from app.pipeline.ingestion import deduplicate_and_store, get_or_create_source, update_job_status

    if session_factory is None:
        session_factory = AsyncSessionLocal

    if source not in CONNECTOR_REGISTRY:
        raise ValueError(f"Unknown source: '{source}'. Registered sources: {list(CONNECTOR_REGISTRY.keys())}")

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            log.warning("unparseable_since_date", since=since)

    connector_cls = CONNECTOR_REGISTRY[source]
    connector = connector_cls()
    src_meta = SOURCE_METADATA.get(source, {})

    async with session_factory() as session:
        if job_id:
            await update_job_status(session, job_id, "running", 0.0)
            await session.commit()
        await get_or_create_source(session, source, src_meta.get("connector_type", source))
        await session.commit()

    log.info("ingest_fetching", source=source, query=query, limit=limit)
    records = connector.run(query=query, since=since_dt, limit=limit)
    total = len(records)
    log.info("ingest_fetched", source=source, count=total)

    stored_ids = []
    skipped = 0
    errors = 0

    async with session_factory() as session:
        for i, record in enumerate(records):
            try:
                rec_src = record.source_name or source
                rec_meta = SOURCE_METADATA.get(rec_src, {})
                db_source = await get_or_create_source(
                    session, rec_src, rec_meta.get("connector_type", rec_src)
                )
                conv_id = await deduplicate_and_store(session, record, db_source)
                if conv_id:
                    stored_ids.append(conv_id)
                else:
                    skipped += 1
            except Exception as e:
                errors += 1
                log.warning("ingest_record_error", source=source, error=str(e))

            if job_id and total > 0 and (i + 1) % 25 == 0:
                prog = round((i + 1) / total, 2)
                await update_job_status(session, job_id, "running", prog)
                await session.commit()

        await session.commit()

    result_payload = {
        "stored": len(stored_ids),
        "skipped": skipped,
        "errors": errors,
        "source": source,
        "total_fetched": total,
    }

    if job_id:
        async with session_factory() as session:
            await update_job_status(
                session, job_id, "done", 1.0, payload_update=result_payload
            )
            await session.commit()

    log.info(
        "ingest_complete",
        source=source,
        stored=len(stored_ids),
        skipped=skipped,
        errors=errors,
    )
    return result_payload


@celery_app.task(name="worker.tasks.ping", bind=True)
def ping(self):
    log.info("task_ping_received", task_id=self.request.id)
    return "pong"


@celery_app.task(name="worker.tasks.ingest_source", bind=True, max_retries=3)
def ingest_source(self, source, query="", since=None, limit=500, job_id=None):
    log.info("task_ingest_source_start", source=source, job_id=job_id)
    try:
        return _run_async(run_ingest_pipeline(source, query=query, since=since, limit=limit, job_id=job_id))
    except Exception as exc:
        log.error("ingest_source_error", source=source, error=str(exc))
        if job_id:
            async def _fail():
                from app.db.session import AsyncSessionLocal
                from app.pipeline.ingestion import update_job_status
                async with AsyncSessionLocal() as session:
                    await update_job_status(session, job_id, "failed", error=str(exc))
                    await session.commit()
            try:
                _run_async(_fail())
            except Exception:
                pass
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="worker.tasks.analyze_batch", bind=True)
def analyze_batch(self, conversation_ids):
    log.info("task_analyze_batch_stub", count=len(conversation_ids))
    return {"status": "stub", "message": "Analysis implemented in Phase 3"}

@celery_app.task(name="worker.tasks.cluster_conversations", bind=True)
def cluster_conversations(self):
    log.info("task_cluster_stub")
    return {"status": "stub", "message": "Clustering implemented in Phase 4"}

@celery_app.task(name="worker.tasks.detect_trends", bind=True)
def detect_trends(self):
    log.info("task_trends_stub")
    return {"status": "stub", "message": "Trend detection implemented in Phase 4"}
