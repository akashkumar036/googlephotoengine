from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.connectors.base import NormalizedRecord
from app.db.models import Conversation, Job, Source
from app.pipeline.cleaning import clean_text
from app.pipeline.deduplication import check_duplicate, compute_source_hash, compute_content_hash

log = structlog.get_logger()


async def get_or_create_source(session: AsyncSession, source_name: str, connector_type: str) -> Source:
    """Fetch or insert a Source record idempotently."""
    result = await session.execute(select(Source).where(Source.name == source_name))
    source = result.scalar_one_or_none()
    if not source:
        source = Source(
            name=source_name,
            connector_type=connector_type,
            is_active=True,
            config={"display_name": source_name},
        )
        session.add(source)
        await session.flush()
    return source


async def deduplicate_and_store(
    session: AsyncSession,
    record: NormalizedRecord,
    source: Source,
) -> Optional[str]:
    """
    Clean, deduplicate, and persist a normalized record.

    Returns:
        Conversation ID if newly created or edited; None if skipped as duplicate.
    """
    clean = clean_text(record.text)
    s_hash = compute_source_hash(record.source_name, record.external_id)
    c_hash = compute_content_hash(record.text)

    is_exact_match, dedup_status, existing = await check_duplicate(
        session=session,
        source_name=record.source_name,
        external_id=record.external_id,
        text=record.text,
        content_hash=c_hash,
    )

    if is_exact_match:
        if dedup_status == "edited" and existing:
            # Update post in place and flag for re-analysis (Edge Case 3.3)
            existing.text = record.text
            existing.cleaned_text = clean.cleaned_text
            existing.language = clean.language
            existing.is_cleaned = True
            existing.is_spam = clean.is_spam
            existing.is_low_information = clean.is_low_information
            existing.was_edited = True
            existing.needs_reanalysis = True
            existing.metadata_ = {
                **(existing.metadata_ or {}),
                "was_edited": True,
                "content_hash": c_hash,
                "pii_detected": clean.pii_detected,
                "token_count": clean.token_count,
            }
            session.add(existing)
            await session.flush()
            log.info("conversation_updated_edited", id=existing.id, external_id=record.external_id)
            return existing.id

        # Exact duplicate — skip silently to avoid inflating counts
        log.debug("conversation_skipped_duplicate", external_id=record.external_id)
        return None

    metadata = {
        **(record.metadata or {}),
        "content_hash": c_hash,
        "pii_detected": clean.pii_detected,
        "token_count": clean.token_count,
        "has_quotes": clean.flags.get("has_quotes", False),
    }

    conv = Conversation(
        source_id=source.id,
        external_id=record.external_id,
        url=record.url,
        author_hash=record.author_hash,
        timestamp=record.timestamp,
        title=record.title,
        text=record.text,
        cleaned_text=clean.cleaned_text,
        language=clean.language,
        engagement=record.engagement,
        metadata_=metadata,
        dedup_status=dedup_status,
        dedup_hash=s_hash,
        is_cleaned=True,
        is_spam=clean.is_spam,
        is_low_information=clean.is_low_information,
        is_demo=record.is_demo,
    )
    session.add(conv)
    await session.flush()
    log.debug("conversation_stored", id=conv.id, source=record.source_name, status=dedup_status)
    return conv.id


async def update_job_status(
    session: AsyncSession,
    job_id: str,
    status: str,
    progress: float = 0.0,
    error: Optional[str] = None,
    payload_update: Optional[Dict[str, Any]] = None,
) -> None:
    """Update job status, progress percentage, error, and timestamp in DB."""
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return
    job.status = status
    job.progress = progress
    if error:
        job.error = error
    if payload_update:
        job.payload = {**(job.payload or {}), **payload_update}
    if status == "running" and not job.started_at:
        job.started_at = datetime.now(timezone.utc)
    if status in ("done", "failed"):
        job.completed_at = datetime.now(timezone.utc)
    await session.flush()
