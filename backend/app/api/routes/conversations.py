from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.models import Conversation, Source
from app.db.session import get_db

router = APIRouter()


def _to_dict(c: Conversation) -> dict:
    return {
        "id": c.id,
        "source": c.source.name if c.source else None,
        "source_id": c.source_id,
        "external_id": c.external_id,
        "url": c.url,
        "author_hash": c.author_hash,
        "title": c.title,
        "text": c.text,
        "cleaned_text": c.cleaned_text,
        "timestamp": c.timestamp,
        "language": c.language,
        "engagement": c.engagement,
        "metadata": c.metadata_,
        "dedup_status": c.dedup_status,
        "is_cleaned": c.is_cleaned,
        "is_relevant": c.is_relevant,
        "is_spam": c.is_spam,
        "is_low_information": c.is_low_information,
        "is_demo": c.is_demo,
        "created_at": c.created_at,
    }


@router.get("", summary="List conversations (paginated + filterable)")
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    source: Optional[str] = Query(None, description="Filter by source name, e.g. 'reddit', 'google_play', 'demo'"),
    language: Optional[str] = Query(None),
    is_demo: Optional[bool] = Query(None),
    is_relevant: Optional[bool] = Query(None),
    is_spam: Optional[bool] = Query(None),
    dedup_status: Optional[str] = Query(None, description="Filter by dedup_status (original, duplicate, cross_post)"),
    from_date: Optional[datetime] = Query(None, description="Filter records with timestamp >= from_date"),
    to_date: Optional[datetime] = Query(None, description="Filter records with timestamp <= to_date"),
    q: Optional[str] = Query(None, description="Keyword search in title/text"),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = select(Conversation).options(
        selectinload(Conversation.source),
        selectinload(Conversation.analysis),
    )
    filters = []

    if source:
        stmt = stmt.join(Conversation.source).where(Source.name == source)
    if is_demo is not None:
        filters.append(Conversation.is_demo == is_demo)
    if is_relevant is not None:
        filters.append(Conversation.is_relevant == is_relevant)
    if is_spam is not None:
        filters.append(Conversation.is_spam == is_spam)
    if dedup_status:
        filters.append(Conversation.dedup_status == dedup_status)
    if language:
        filters.append(Conversation.language == language)
    if from_date:
        filters.append(Conversation.timestamp >= from_date)
    if to_date:
        filters.append(Conversation.timestamp <= to_date)
    if q:
        pat = f"%{q}%"
        filters.append((Conversation.text.ilike(pat)) | (Conversation.title.ilike(pat)) | (Conversation.cleaned_text.ilike(pat)))

    if filters:
        stmt = stmt.where(and_(*filters))

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    result = await db.execute(stmt.order_by(desc(Conversation.created_at)).offset(skip).limit(limit))
    records = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_to_dict(c) for c in records],
    }


@router.get("/{conversation_id}", summary="Get a single conversation")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.source),
            selectinload(Conversation.analysis),
        )
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    d = _to_dict(conv)
    if conv.analysis:
        a = conv.analysis
        d["analysis"] = {
            "id": a.id,
            "relevance": a.relevance,
            "primary_intent": a.primary_intent,
            "memory_types": a.memory_types,
            "failure_modes": a.failure_modes,
            "pain_points": a.pain_points,
            "user_goal": a.user_goal,
            "frustration_level": a.frustration_level,
            "severity": a.severity,
            "confidence": a.confidence,
            "reasoning_summary": a.reasoning_summary,
            "processed_at": a.processed_at,
        }
    return d
