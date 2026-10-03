from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireResearcher, RequireAdmin, RequireViewer
from app.db.models import (
    Conversation,
    AIAnalysis,
    HumanReview,
    Cluster,
    ClusterMembership,
    TaxonomyProposal,
    User,
    _uuid,
)
from app.db.session import get_db

router = APIRouter()


class ReviewSubmission(BaseModel):
    conversation_id: str
    action: str  # "approve", "correct", "invalidate", "bookmark"
    intent: Optional[str] = None
    memory_types: Optional[List[str]] = None
    failure_modes: Optional[List[str]] = None
    is_relevant: Optional[bool] = None
    notes: Optional[str] = None


class ClusterActionRequest(BaseModel):
    action: str  # "rename", "merge", "split"
    new_name: Optional[str] = None
    target_cluster_id: Optional[str] = None
    selected_conversation_ids: Optional[List[str]] = None


class ProposalActionRequest(BaseModel):
    action: str  # "approve", "reject"
    notes: Optional[str] = None


@router.get("/queue", summary="Get queue of AI classifications pending human review")
async def get_review_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    """
    Returns conversations with AI analyses that have not been human-reviewed yet,
    ordered by lowest confidence first to prioritize ambiguous cases.
    """
    stmt = (
        select(Conversation)
        .join(AIAnalysis, AIAnalysis.conversation_id == Conversation.id)
        .options(
            selectinload(Conversation.source),
            selectinload(Conversation.analysis),
        )
        .where(Conversation.is_relevant == True)
    )

    if min_confidence is not None:
        stmt = stmt.where(AIAnalysis.confidence <= min_confidence)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    # Prioritize low confidence items for review
    res = await db.execute(
        stmt.order_by(AIAnalysis.confidence.asc()).offset(skip).limit(limit)
    )
    convs = res.scalars().all()

    queue_items = []
    for c in convs:
        queue_items.append({
            "conversation_id": c.id,
            "title": c.title or "Untitled Conversation",
            "text": c.cleaned_text or c.text or "",
            "source": c.source.name if c.source else "demo",
            "timestamp": c.timestamp,
            "is_demo": c.is_demo,
            "ai_classification": {
                "id": c.analysis.id if c.analysis else None,
                "is_relevant": c.is_relevant,
                "primary_intent": c.analysis.primary_intent if c.analysis else None,
                "memory_types": c.analysis.memory_types if c.analysis else [],
                "failure_modes": c.analysis.failure_modes if c.analysis else [],
                "confidence": c.analysis.confidence if c.analysis else 0.8,
                "reasoning": c.analysis.reasoning_summary if c.analysis else None,
            },
        })

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": queue_items,
    }


@router.post("", summary="Submit human review decision for a conversation")
async def submit_human_review(
    payload: ReviewSubmission,
    db: AsyncSession = Depends(get_db),
    user: User = RequireResearcher,
):
    """
    Applies researcher corrections or approvals:
    - Creates a persistent record in `human_reviews` table
    - Updates `ai_analyses` and `conversations` records
    """
    c_stmt = (
        select(Conversation)
        .options(selectinload(Conversation.analysis))
        .where(Conversation.id == payload.conversation_id)
    )
    conv = (await db.execute(c_stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    analysis = conv.analysis
    original_val = {
        "intent": analysis.primary_intent if analysis else None,
        "memory_types": analysis.memory_types if analysis else [],
        "failure_modes": analysis.failure_modes if analysis else [],
        "is_relevant": conv.is_relevant,
    }

    corrected_val = {
        "intent": payload.intent or original_val["intent"],
        "memory_types": payload.memory_types if payload.memory_types is not None else original_val["memory_types"],
        "failure_modes": payload.failure_modes if payload.failure_modes is not None else original_val["failure_modes"],
        "is_relevant": payload.is_relevant if payload.is_relevant is not None else original_val["is_relevant"],
    }

    # Record review
    review = HumanReview(
        reviewer_id=user.id if hasattr(user, "id") else None,
        target_type="conversation",
        target_id=conv.id,
        action=payload.action,
        original_value=original_val,
        corrected_value=corrected_val,
        notes=payload.notes,
    )
    db.add(review)

    # Update conversation & analysis
    if payload.is_relevant is not None:
        conv.is_relevant = payload.is_relevant
    if analysis:
        if payload.intent:
            analysis.primary_intent = payload.intent
        if payload.memory_types is not None:
            analysis.memory_types = payload.memory_types
        if payload.failure_modes is not None:
            analysis.failure_modes = payload.failure_modes
        # Mark high confidence after human review
        analysis.confidence = 1.0

    await db.commit()
    return {
        "status": "success",
        "review_id": review.id,
        "action": payload.action,
        "conversation_id": conv.id,
        "message": f"Review recorded with action '{payload.action}'",
    }


@router.post("/clusters/{cluster_id}/action", summary="Perform cluster curation action (rename, merge, split)")
async def handle_cluster_action(
    cluster_id: str,
    payload: ClusterActionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = RequireResearcher,
):
    cluster = (await db.execute(select(Cluster).where(Cluster.id == cluster_id))).scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    if payload.action == "rename":
        if not payload.new_name:
            raise HTTPException(status_code=400, detail="new_name is required for rename")
        old_name = cluster.label
        cluster.label = payload.new_name
        review = HumanReview(
            reviewer_id=user.id if hasattr(user, "id") else None,
            target_type="cluster",
            target_id=cluster.id,
            action="rename",
            original_value={"label": old_name},
            corrected_value={"label": payload.new_name},
        )
        db.add(review)
        await db.commit()
        return {"status": "success", "cluster_id": cluster.id, "label": cluster.label}

    elif payload.action == "merge":
        if not payload.target_cluster_id:
            raise HTTPException(status_code=400, detail="target_cluster_id required for merge")
        target_cluster = (
            await db.execute(select(Cluster).where(Cluster.id == payload.target_cluster_id))
        ).scalar_one_or_none()
        if not target_cluster:
            raise HTTPException(status_code=404, detail="Target cluster not found")

        # Move memberships from cluster to target_cluster
        memberships = (
            await db.execute(select(ClusterMembership).where(ClusterMembership.cluster_id == cluster_id))
        ).scalars().all()
        for m in memberships:
            m.cluster_id = target_cluster.id
        
        target_cluster.member_count = (target_cluster.member_count or 0) + len(memberships)
        cluster.is_archived = True

        review = HumanReview(
            reviewer_id=user.id if hasattr(user, "id") else None,
            target_type="cluster",
            target_id=cluster.id,
            action="merge",
            original_value={"merged_from": cluster.id},
            corrected_value={"merged_into": target_cluster.id},
        )
        db.add(review)
        await db.commit()
        return {"status": "success", "merged_into": target_cluster.id}

    raise HTTPException(status_code=400, detail=f"Unsupported cluster action: {payload.action}")


@router.get("/taxonomy", summary="List taxonomy categories and proposals awaiting approval")
async def list_taxonomy_review(
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    from app.pipeline.taxonomy import STANDARD_TAXONOMY_CATEGORIES as PREDEFINED_TAXONOMY
    proposals = (
        await db.execute(
            select(TaxonomyProposal).order_by(desc(TaxonomyProposal.created_at))
        )
    ).scalars().all()

    return {
        "predefined_categories": PREDEFINED_TAXONOMY,
        "proposals": [
            {
                "id": p.id,
                "category_name": p.category_name,
                "description": p.description,
                "evidence_count": p.evidence_count,
                "proposed_by": p.proposed_by,
                "is_approved": p.is_approved,
                "is_rejected": p.is_rejected,
                "created_at": p.created_at,
            }
            for p in proposals
        ],
    }


@router.post("/taxonomy/proposals/{proposal_id}/action", summary="Approve or reject taxonomy proposal")
async def handle_proposal_action(
    proposal_id: str,
    payload: ProposalActionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = RequireAdmin,
):
    proposal = (
        await db.execute(select(TaxonomyProposal).where(TaxonomyProposal.id == proposal_id))
    ).scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Taxonomy proposal not found")

    if payload.action == "approve":
        proposal.is_approved = True
        proposal.is_rejected = False
    elif payload.action == "reject":
        proposal.is_approved = False
        proposal.is_rejected = True
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {payload.action}")

    review = HumanReview(
        reviewer_id=user.id if hasattr(user, "id") else None,
        target_type="taxonomy_proposal",
        target_id=proposal.id,
        action=f"proposal_{payload.action}",
        original_value={"category_name": proposal.category_name},
        corrected_value={"is_approved": proposal.is_approved, "is_rejected": proposal.is_rejected},
        notes=payload.notes,
    )
    db.add(review)
    await db.commit()

    return {
        "status": "success",
        "proposal_id": proposal.id,
        "is_approved": proposal.is_approved,
        "is_rejected": proposal.is_rejected,
    }
