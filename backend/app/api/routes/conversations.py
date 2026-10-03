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


@router.get("/search", summary="Natural-language semantic vector and keyword search across conversations")
async def search_conversations(
    q: str = Query(..., min_length=1, description="Natural language search query"),
    limit: int = Query(20, ge=1, le=100),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    """
    Semantic ANN search across conversation embeddings and text.
    Returns ranked results with similarity scores and highlighted excerpts.
    """
    import math
    from app.models.router import get_model_router

    # 1. Embed query
    query_vec = None
    try:
        router = get_model_router()
        provider = router.get_provider()
        emb_res = await provider.embed([q])
        if emb_res and len(emb_res) > 0:
            query_vec = emb_res[0]
    except Exception:
        query_vec = None

    # 2. Fetch conversations
    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.source),
            selectinload(Conversation.analysis),
        )
        .limit(200)
    )
    result = await db.execute(stmt)
    convs = result.scalars().all()

    def calc_cosine(v1, v2):
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def extract_excerpt(text: str, query: str, window: int = 160) -> str:
        if not text:
            return ""
        q_terms = [w.lower() for w in query.split() if len(w) > 2]
        idx = -1
        for term in q_terms:
            pos = text.lower().find(term)
            if pos != -1:
                idx = pos
                break
        if idx == -1:
            return text[:window] + ("..." if len(text) > window else "")
        start = max(0, idx - 40)
        end = min(len(text), idx + window)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end]}{suffix}"

    scored_items = []
    q_words = set(q.lower().split())

    for c in convs:
        # Base semantic similarity
        sim = 0.0
        if query_vec and c.embedding is not None:
            # Handle list vs pgvector representation
            emb_list = list(c.embedding) if hasattr(c.embedding, "__iter__") else []
            sim = max(0.0, calc_cosine(query_vec, emb_list))
        
        # Keyword boost
        full_text = f"{c.title or ''} {c.cleaned_text or c.text or ''}".lower()
        overlap = sum(1 for w in q_words if w in full_text)
        keyword_score = min(1.0, overlap / max(1, len(q_words)))

        # Blended score
        combined_score = (sim * 0.7) + (keyword_score * 0.3) if query_vec and c.embedding is not None else keyword_score

        if combined_score >= min_similarity:
            item = _to_dict(c)
            item["similarity_score"] = round(combined_score, 4)
            item["highlighted_excerpt"] = extract_excerpt(c.cleaned_text or c.text or "", q)
            scored_items.append(item)

    scored_items.sort(key=lambda x: x["similarity_score"], reverse=True)
    ranked = scored_items[:limit]

    return {
        "query": q,
        "total": len(ranked),
        "data": ranked,
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
