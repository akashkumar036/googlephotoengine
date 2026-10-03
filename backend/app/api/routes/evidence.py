from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.models import Evidence, Conversation, Problem, Source
from app.db.session import get_db

router = APIRouter()


@router.get("/{evidence_id}", summary="Get evidence record with source conversation and linked problem")
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = (
        select(Evidence)
        .options(
            selectinload(Evidence.problem),
            selectinload(Evidence.conversation).selectinload(Conversation.source),
            selectinload(Evidence.conversation).selectinload(Conversation.analysis),
        )
        .where(Evidence.id == evidence_id)
    )
    res = await db.execute(stmt)
    evidence = res.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    conv = evidence.conversation
    prob = evidence.problem

    return {
        "id": evidence.id,
        "problem_id": evidence.problem_id,
        "conversation_id": evidence.conversation_id,
        "excerpt": evidence.excerpt,
        "ai_interpretation": evidence.ai_interpretation,
        "relevance_score": evidence.relevance_score,
        "created_at": evidence.created_at,
        "problem": {
            "id": prob.id,
            "title": prob.title,
            "statement": prob.statement,
            "frequency": prob.frequency,
        } if prob else None,
        "conversation": {
            "id": conv.id,
            "source": conv.source.name if conv and conv.source else None,
            "title": conv.title if conv else None,
            "text": conv.text if conv else None,
            "cleaned_text": conv.cleaned_text if conv else None,
            "url": conv.url if conv else None,
            "timestamp": conv.timestamp if conv else None,
            "author_hash": conv.author_hash if conv else None,
            "analysis": {
                "relevance": conv.analysis.relevance,
                "primary_intent": conv.analysis.primary_intent,
                "memory_types": conv.analysis.memory_types,
                "failure_modes": conv.analysis.failure_modes,
                "frustration_level": conv.analysis.frustration_level,
                "severity": conv.analysis.severity,
            } if conv and conv.analysis else None,
        } if conv else None,
    }
