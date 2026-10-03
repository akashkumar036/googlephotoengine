from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func, and_, Text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer, RequireResearcher
from app.db.models import Problem, Evidence, Opportunity, Trend, Conversation, Source
from app.db.session import get_db

router = APIRouter()


class ProblemUpdateRequest(BaseModel):
    title: Optional[str] = None
    statement: Optional[str] = None
    taxonomy_categories: Optional[List[str]] = None
    is_approved: Optional[bool] = None
    is_emerging: Optional[bool] = None
    user_segments: Optional[List[str]] = None


def _problem_to_dict(p: Problem) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "statement": p.statement,
        "taxonomy_categories": p.taxonomy_categories or [],
        "frequency": p.frequency,
        "source_count": p.source_count,
        "frustration_score": p.frustration_score,
        "severity_score": p.severity_score,
        "growth_rate": p.growth_rate,
        "cross_source_score": p.cross_source_score,
        "evidence_diversity_score": p.evidence_diversity_score,
        "confidence": p.confidence,
        "is_emerging": p.is_emerging,
        "is_approved": p.is_approved,
        "user_segments": p.user_segments or [],
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


@router.get("", summary="List discovered retrieval problems (paginated + filterable)")
async def list_problems(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    taxonomy: Optional[str] = Query(None, description="Filter by taxonomy category"),
    source: Optional[str] = Query(None, description="Filter by presence of source in linked evidence"),
    severity_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    growth_min: Optional[float] = Query(None),
    is_emerging: Optional[bool] = Query(None),
    is_approved: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, description="Search in problem title or statement"),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = select(Problem)
    filters = []

    if taxonomy:
        filters.append(func.cast(Problem.taxonomy_categories, Text).ilike(f"%{taxonomy}%"))
    if severity_min is not None:
        filters.append(Problem.severity_score >= severity_min)
    if growth_min is not None:
        filters.append(Problem.growth_rate >= growth_min)
    if is_emerging is not None:
        filters.append(Problem.is_emerging == is_emerging)
    if is_approved is not None:
        filters.append(Problem.is_approved == is_approved)
    if q:
        pat = f"%{q}%"
        filters.append((Problem.title.ilike(pat)) | (Problem.statement.ilike(pat)))

    if source:
        stmt = stmt.join(Problem.evidence).join(Evidence.conversation).join(Conversation.source).where(Source.name == source)

    if filters:
        stmt = stmt.where(and_(*filters))

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    res = await db.execute(stmt.order_by(desc(Problem.frequency)).offset(skip).limit(limit))
    records = res.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_problem_to_dict(p) for p in records],
    }


@router.get("/{problem_id}", summary="Get problem detail with evidence and opportunities")
async def get_problem(
    problem_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = (
        select(Problem)
        .options(
            selectinload(Problem.evidence).selectinload(Evidence.conversation).selectinload(Conversation.source),
            selectinload(Problem.opportunities),
            selectinload(Problem.trends),
        )
        .where(Problem.id == problem_id)
    )
    res = await db.execute(stmt)
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    data = _problem_to_dict(problem)

    data["evidence"] = [
        {
            "id": e.id,
            "conversation_id": e.conversation_id,
            "source": e.conversation.source.name if (e.conversation and e.conversation.source) else None,
            "url": e.conversation.url if e.conversation else None,
            "excerpt": e.excerpt,
            "ai_interpretation": e.ai_interpretation,
            "relevance_score": e.relevance_score,
            "created_at": e.created_at,
        }
        for e in problem.evidence
    ]

    data["opportunities"] = [
        {
            "id": o.id,
            "observed_problem": o.observed_problem,
            "underlying_need": o.underlying_need,
            "opportunity_area": o.opportunity_area,
            "solution_hypothesis": o.solution_hypothesis,
            "confidence": o.confidence,
            "is_validated": o.is_validated,
        }
        for o in problem.opportunities
    ]

    data["trends"] = [
        {
            "period_start": t.period_start,
            "period_end": t.period_end,
            "conversation_count": t.conversation_count,
            "growth_rate": t.growth_rate,
            "sources": t.sources,
        }
        for t in problem.trends
    ]

    return data


@router.patch("/{problem_id}", summary="Update problem annotations (researcher action)")
async def update_problem(
    problem_id: str,
    payload: ProblemUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
):
    res = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if payload.title is not None:
        problem.title = payload.title
    if payload.statement is not None:
        problem.statement = payload.statement
    if payload.taxonomy_categories is not None:
        problem.taxonomy_categories = payload.taxonomy_categories
    if payload.is_approved is not None:
        problem.is_approved = payload.is_approved
    if payload.is_emerging is not None:
        problem.is_emerging = payload.is_emerging
    if payload.user_segments is not None:
        problem.user_segments = payload.user_segments

    await db.commit()
    await db.refresh(problem)
    return _problem_to_dict(problem)


@router.get("/{problem_id}/cross-platform", summary="Get cross-platform breakdown for a problem")
async def get_cross_platform_breakdown(
    problem_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = (
        select(Problem)
        .options(
            selectinload(Problem.evidence).selectinload(Evidence.conversation)
        )
        .where(Problem.id == problem_id)
    )
    res = await db.execute(stmt)
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    sources_res = await db.execute(select(Source))
    sources_map = {s.id: s.name for s in sources_res.scalars().all()}

    platform_breakdown: Dict[str, Dict[str, Any]] = {}

    for e in problem.evidence:
        if not e.conversation:
            continue
        s_name = sources_map.get(e.conversation.source_id, "unknown")
        if s_name not in platform_breakdown:
            platform_breakdown[s_name] = {"count": 0, "excerpts": []}
        platform_breakdown[s_name]["count"] += 1
        if len(platform_breakdown[s_name]["excerpts"]) < 3 and e.excerpt:
            platform_breakdown[s_name]["excerpts"].append(e.excerpt)

    source_cnt = len(platform_breakdown)
    is_isolated = (source_cnt == 1)
    is_widespread = (source_cnt >= 3)

    return {
        "problem_id": problem.id,
        "title": problem.title,
        "source_count": source_cnt,
        "is_isolated": is_isolated,
        "is_widespread": is_widespread,
        "platform_breakdown": platform_breakdown,
    }
