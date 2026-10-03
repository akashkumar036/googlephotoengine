from __future__ import annotations
import csv
import io
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer, RequireResearcher
from app.db.models import ResearchReport, User
from app.db.session import get_db
from app.pipeline.brief_generator import generate_research_brief

router = APIRouter()


class BriefRequest(BaseModel):
    problem_ids: Optional[List[str]] = None
    source_filter: Optional[str] = None
    time_period: Optional[str] = "30d"


@router.post("/brief", summary="Generate a comprehensive UX research brief")
async def create_research_brief(
    payload: BriefRequest,
    db: AsyncSession = Depends(get_db),
    user: User = RequireResearcher,
) -> Dict[str, Any]:
    """
    Synthesizes an executive research brief across selected problems and evidence chains.
    Persists to database and returns structured JSON + Markdown representation.
    """
    user_id = user.id if hasattr(user, "id") else None
    brief = await generate_research_brief(
        db=db,
        problem_ids=payload.problem_ids,
        source_filter=payload.source_filter,
        time_period=payload.time_period or "30d",
        user_id=user_id,
    )
    return brief


@router.get("", summary="List generated research reports")
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = select(ResearchReport).order_by(desc(ResearchReport.created_at)).offset(skip).limit(limit)
    reports = (await db.execute(stmt)).scalars().all()
    return {
        "total": len(reports),
        "data": [
            {
                "id": r.id,
                "title": r.title,
                "format": r.format,
                "created_at": r.created_at,
                "summary": r.content.get("executive_summary", "")[:200] if r.content else "",
                "problem_count": r.content.get("problem_count", 0) if r.content else 0,
            }
            for r in reports
        ],
    }


@router.get("/{report_id}", summary="Get a generated research report by ID")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    report = (
        await db.execute(select(ResearchReport).where(ResearchReport.id == report_id))
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report.id,
        "title": report.title,
        "format": report.format,
        "created_at": report.created_at,
        "content": report.content,
    }


@router.get("/{report_id}/export", summary="Export a research report as Markdown, JSON, or CSV")
async def export_report(
    report_id: str,
    format: str = Query("markdown", pattern="^(markdown|json|csv)$"),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    report = (
        await db.execute(select(ResearchReport).where(ResearchReport.id == report_id))
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = report.content or {}

    if format == "markdown":
        md = content.get("markdown", "# Research Brief\n\nNo content available.")
        return Response(
            content=md,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="brief-{report.id[:8]}.md"'},
        )
    elif format == "json":
        return Response(
            content=json.dumps(content, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="brief-{report.id[:8]}.json"'},
        )
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Section", "Content"])
        writer.writerow(["Title", content.get("title", "")])
        writer.writerow(["Executive Summary", content.get("executive_summary", "")])
        for p in content.get("key_problems", []):
            writer.writerow(["Key Problem", p])
        for f in content.get("failure_modes", []):
            writer.writerow(["Failure Mode", f])
        for un in content.get("unmet_needs", []):
            writer.writerow(["Unmet Need", un])
        for opp in content.get("opportunity_spaces", []):
            writer.writerow(["Opportunity (Hypothesis)", opp])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="brief-{report.id[:8]}.csv"'},
        )
