"""Stub routes — to be implemented in Phase 2–5."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import RequireResearcher

router = APIRouter()

@router.post("", summary="Trigger data ingestion job")
async def trigger_ingest(_=RequireResearcher):
    return {"status": "queued", "message": "Ingestion routes coming in Phase 2"}

@router.get("/{job_id}", summary="Get job status")
async def get_job(job_id: str, _=RequireResearcher):
    return {"job_id": job_id, "status": "stub — Phase 2"}
