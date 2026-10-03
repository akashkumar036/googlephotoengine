from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireResearcher, RequireViewer
from app.db.models import Job
from app.db.session import get_db
router = APIRouter()

@router.get("", summary="List all jobs")
async def list_jobs(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db), _=RequireViewer):
    result = await db.execute(select(Job).order_by(desc(Job.created_at)).offset(skip).limit(limit))
    jobs = result.scalars().all()
    return {"total": len(jobs), "skip": skip, "limit": limit, "data": [
        {"id": j.id, "type": j.type, "status": j.status, "progress": j.progress,
         "payload": j.payload, "error": j.error, "started_at": j.started_at,
         "completed_at": j.completed_at, "created_at": j.created_at}
        for j in jobs
    ]}

@router.get("/{job_id}", summary="Get job status")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db), _=RequireViewer):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.id, "type": job.type, "status": job.status, "progress": job.progress,
            "payload": job.payload, "error": job.error, "started_at": job.started_at,
            "completed_at": job.completed_at, "created_at": job.created_at}
