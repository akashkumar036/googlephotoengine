from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireResearcher
from app.db.models import EvaluationBenchmark, Conversation
from app.db.session import get_db
from app.evaluation.metrics import compute_benchmark_metrics
from app.pipeline.feedback import analyze_feedback_learning_loop

router = APIRouter()


@router.get("/results", summary="Get model performance metrics against labeled benchmark")
async def get_evaluation_results(
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
) -> Dict[str, Any]:
    """
    Computes precision, recall, F1, intent classification accuracy,
    and prompt version comparison against the benchmark dataset.
    """
    metrics = await compute_benchmark_metrics(db)
    return metrics


@router.get("/benchmarks", summary="List benchmark labeled dataset records")
async def list_benchmarks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
):
    stmt = (
        select(EvaluationBenchmark)
        .options(
            selectinload(EvaluationBenchmark.conversation).selectinload(Conversation.source)
        )
        .order_by(desc(EvaluationBenchmark.created_at))
        .offset(skip)
        .limit(limit)
    )
    benchmarks = (await db.execute(stmt)).scalars().all()

    return {
        "total": len(benchmarks),
        "data": [
            {
                "id": b.id,
                "conversation_id": b.conversation_id,
                "title": b.conversation.title if b.conversation else "Untitled",
                "text_excerpt": (b.conversation.cleaned_text or b.conversation.text or "")[:180] if b.conversation else "",
                "source": b.conversation.source.name if b.conversation and b.conversation.source else "demo",
                "ground_truth_relevance": b.ground_truth_relevance,
                "ground_truth_intent": b.ground_truth_intent,
                "ground_truth_failure_modes": b.ground_truth_failure_modes,
            }
            for b in benchmarks
        ],
    }


@router.get("/feedback-loop", summary="Get human review feedback learning loop insights")
async def get_feedback_loop_insights(
    db: AsyncSession = Depends(get_db),
    _: None = RequireResearcher,
) -> Dict[str, Any]:
    """
    Surfaces error patterns and prompt improvement suggestions based on
    accumulated researcher review corrections.
    """
    insights = await analyze_feedback_learning_loop(db)
    return insights
