from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func, and_, Text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.models import Conversation, Source, AIAnalysis
from app.db.session import get_db

router = APIRouter()


def _to_dict(c: Conversation) -> dict:
    analysis_summary = None
    if c.analysis:
        analysis_summary = {
            "id": c.analysis.id,
            "relevance": c.analysis.relevance,
            "primary_intent": c.analysis.primary_intent,
            "memory_types": c.analysis.memory_types,
            "failure_modes": c.analysis.failure_modes,
            "retrieval_strategies": c.analysis.retrieval_strategies,
            "pain_points": c.analysis.pain_points,
            "confidence": c.analysis.confidence,
            "frustration_level": c.analysis.frustration_level,
            "severity": c.analysis.severity,
            "reasoning_summary": c.analysis.reasoning_summary,
            "prompt_version": c.analysis.prompt_version,
            "model_provider": c.analysis.model_provider,
            "model_name": c.analysis.model_name,
            "processed_at": c.analysis.processed_at,
        }

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
        "has_embedding": c.embedding is not None,
        "embedding_model": c.embedding_model,
        "created_at": c.created_at,
        "analysis": analysis_summary,
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
    intent: Optional[str] = Query(None, description="Filter by primary_intent (e.g. find_photo, find_screenshot)"),
    memory_type: Optional[str] = Query(None, description="Filter by memory dimension (temporal, spatial, visual, etc.)"),
    failure_mode: Optional[str] = Query(None, description="Filter by failure mode (unknown_date, poor_ranking, etc.)"),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum AI confidence score"),
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

    needs_analysis_join = any([intent, memory_type, failure_mode, confidence_min is not None])
    if needs_analysis_join:
        stmt = stmt.join(Conversation.analysis)
        if intent:
            filters.append(AIAnalysis.primary_intent == intent)
        if confidence_min is not None:
            filters.append(AIAnalysis.confidence >= confidence_min)
        if memory_type:
            filters.append(func.cast(AIAnalysis.memory_types, Text).ilike(f"%{memory_type}%"))
        if failure_mode:
            filters.append(func.cast(AIAnalysis.failure_modes, Text).ilike(f"%{failure_mode}%"))

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


@router.get("/{conversation_id}", summary="Get a single conversation with full AI analysis")
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
            "conversation_id": a.conversation_id,
            "prompt_version": a.prompt_version,
            "relevance": a.relevance,
            "primary_intent": a.primary_intent,
            "memory_types": a.memory_types,
            "retrieval_strategies": a.retrieval_strategies,
            "failure_modes": a.failure_modes,
            "pain_points": a.pain_points,
            "user_goal": a.user_goal,
            "known_memory": a.known_memory,
            "unknown_memory": a.unknown_memory,
            "frustration_level": a.frustration_level,
            "severity": a.severity,
            "confidence": a.confidence,
            "reasoning_summary": a.reasoning_summary,
            "model_provider": a.model_provider,
            "model_name": a.model_name,
            "processed_at": a.processed_at,
            "created_at": a.created_at,
        }
    return d
