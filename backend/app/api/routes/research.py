from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.session import get_db
from app.pipeline.research_assistant import execute_rag_research_query

router = APIRouter()


class ResearchQueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None
    limit: Optional[int] = 8


@router.get("/starters", summary="Get suggested starter research questions")
async def get_starter_questions(_: None = RequireViewer):
    return {
        "starters": [
            "What are the most common reasons people fail to find old photos?",
            "Which retrieval failure modes are increasing the fastest across Reddit and YouTube?",
            "What are the top user frustrations related to duplicate cleanup and cloud sync?",
            "How do users describe lost memories when searching without exact dates?",
            "Give me 5 unmet needs related to forgotten photos and screenshots.",
        ]
    }


@router.post("/query", summary="Run RAG-powered research query with evidence grounding")
async def run_research_query(
    payload: ResearchQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
) -> Dict[str, Any]:
    """
    Submits a natural language UX research question.
    Returns an answer strictly grounded in retrieved conversation evidence with inline citations.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    res = await execute_rag_research_query(
        db=db,
        query=payload.query.strip(),
        history=payload.history,
        limit=payload.limit or 8,
    )
    return res
