from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer, RequireResearcher
from app.db.models import TaxonomyProposal
from app.db.session import get_db
from app.pipeline.taxonomy import get_taxonomy_summary

router = APIRouter()


class ProposalReviewRequest(BaseModel):
    action: str  # approve | reject


@router.get("", summary="Get taxonomy category breakdown and proposals")
async def list_taxonomy(
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    return await get_taxonomy_summary(db)


@router.post("/proposals/{proposal_id}/review", summary="Review taxonomy proposal (researcher action)")
async def review_taxonomy_proposal(
    proposal_id: str,
    payload: ProposalReviewRequest,
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
):
    res = await db.execute(select(TaxonomyProposal).where(TaxonomyProposal.id == proposal_id))
    proposal = res.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Taxonomy proposal not found")

    if payload.action == "approve":
        proposal.is_approved = True
        proposal.is_rejected = False
    elif payload.action == "reject":
        proposal.is_approved = False
        proposal.is_rejected = True
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    await db.commit()
    return {
        "id": proposal.id,
        "category_name": proposal.category_name,
        "is_approved": proposal.is_approved,
        "is_rejected": proposal.is_rejected,
    }
