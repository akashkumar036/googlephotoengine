from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.session import get_db
from app.pipeline.emerging_detection import get_emerging_alerts
from app.pipeline.trend_detection import get_trends_data

router = APIRouter()


@router.get("", summary="Get historical trend data per retrieval problem")
async def list_trends(
    period: str = Query("30d", description="Time window: 7d, 30d, 90d, 6m, 1y"),
    granularity: str = Query("week", description="Aggregation granularity: day, week, month"),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    trends = await get_trends_data(db, period=period, granularity=granularity)
    return {
        "period": period,
        "granularity": granularity,
        "total_problems": len(trends),
        "data": trends,
    }


@router.get("/emerging", summary="Get emerging retrieval problem alerts")
async def get_emerging_problems(
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    alerts = await get_emerging_alerts(db)
    return {
        "total_alerts": len(alerts),
        "alerts": alerts,
    }
