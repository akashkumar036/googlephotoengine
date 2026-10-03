from __future__ import annotations
import hashlib
from typing import Optional, Tuple
import structlog
from sqlalchemy import func, select, text as sql_text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Conversation

log = structlog.get_logger()


def compute_source_hash(source_name: str, external_id: str) -> str:
    """Unique hash per source platform + external ID."""
    return hashlib.sha256(f"{source_name}:{external_id}".encode()).hexdigest()


def compute_content_hash(text: str) -> str:
    """Canonical content hash of normalized, lowercased whitespace-collapsed text."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


# Backwards compatibility aliases
_source_hash = compute_source_hash
_content_hash = compute_content_hash
compute_dedup_hash = compute_source_hash


async def check_duplicate(
    session: AsyncSession,
    source_name: str,
    external_id: str,
    text: str,
    content_hash: Optional[str] = None,
) -> Tuple[bool, str, Optional[Conversation]]:
    """
    Multi-stage deduplication check:
    1. Exact dedup: source + external_id hash match.
       - If text is identical: (True, "duplicate", existing) -> skip insert.
       - If text was edited: (True, "edited", existing) -> update in place (Edge Case 3.3).
    2. Content hash dedup:
       - If text hash matches another platform: (False, "cross_post", other) -> store as cross_post (Edge Case 3.1).
       - If text hash matches same platform: (False, "duplicate", other) -> store as duplicate.
    3. New unique record:
       - (False, "original", None) -> store as original.

    Returns:
        (is_exact_match, dedup_status, existing_record)
    """
    s_hash = compute_source_hash(source_name, external_id)
    if not content_hash:
        content_hash = compute_content_hash(text)

    # 1. Exact Source + External ID check
    r1 = await session.execute(
        select(Conversation).where(Conversation.dedup_hash == s_hash).limit(1)
    )
    exact_match = r1.scalar_one_or_none()
    if exact_match:
        if exact_match.text.strip() == text.strip():
            log.debug("exact_duplicate_detected", source=source_name, external_id=external_id)
            return True, "duplicate", exact_match
        else:
            log.info("post_edit_detected", source=source_name, external_id=external_id)
            return True, "edited", exact_match

    # 2. Content hash match across existing records
    bind = session.get_bind()
    is_sqlite = bool(bind and bind.dialect.name == "sqlite")

    try:
        if is_sqlite:
            stmt = select(Conversation).options(selectinload(Conversation.source)).where(
                func.json_extract(Conversation.metadata_, "$.content_hash") == content_hash,
                Conversation.dedup_status.in_(["original", "cross_post"]),
            ).limit(1)
        else:
            stmt = select(Conversation).options(selectinload(Conversation.source)).where(
                Conversation.metadata_["content_hash"].astext == content_hash,
                Conversation.dedup_status.in_(["original", "cross_post"]),
            ).limit(1)

        r2 = await session.execute(stmt)
        content_match = r2.scalar_one_or_none()
    except Exception as exc:
        log.warning("content_hash_query_fallback", error=str(exc))
        content_match = None

    if content_match:
        matched_source_name = content_match.source.name if content_match.source else None
        if matched_source_name and matched_source_name != source_name:
            log.info(
                "cross_post_detected",
                source=source_name,
                matched_source=matched_source_name,
                external_id=external_id,
            )
            return False, "cross_post", content_match
        else:
            log.debug("content_duplicate_detected", source=source_name, external_id=external_id)
            return False, "duplicate", content_match

    return False, "original", None


async def mark_semantic_duplicates(
    session: AsyncSession,
    conversation_ids: list[str],
    similarity_threshold: float = 0.95,
) -> int:
    """
    Near-duplicate detection on embedded conversations (Edge Case 3.2).
    Cosine similarity > threshold -> mark as 'possible_duplicate'.
    """
    marked = 0
    for conv_id in conversation_ids:
        result = await session.execute(
            sql_text(
                "SELECT c2.id FROM conversations c1 JOIN conversations c2 ON c2.id != c1.id "
                "WHERE c1.id = :conv_id AND c1.embedding IS NOT NULL AND c2.embedding IS NOT NULL "
                "AND c2.dedup_status = :status AND 1 - (c1.embedding <=> c2.embedding) > :threshold LIMIT 1"
            ),
            {"conv_id": conv_id, "threshold": similarity_threshold, "status": "original"},
        )
        if result.fetchone():
            await session.execute(
                sql_text("UPDATE conversations SET dedup_status = :s WHERE id = :id"),
                {"id": conv_id, "s": "possible_duplicate"},
            )
            marked += 1
    if marked:
        await session.commit()
        log.info("semantic_dedup_marked", count=marked)
    return marked
