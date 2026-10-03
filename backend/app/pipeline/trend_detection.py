from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Problem, Evidence, Conversation, Trend, Source, _uuid


def _parse_period_days(period_str: str) -> int:
    mapping = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "6m": 180,
        "1y": 365,
    }
    return mapping.get(period_str.lower(), 30)


async def run_trend_detection(
    db: AsyncSession,
    bucket_days: int = 7,
) -> Dict[str, Any]:
    """
    Compute time-series trends and growth rates for all discovered problems.
    Stores historical buckets into `trends` table and updates `problem.growth_rate`.
    """
    now = datetime.now(timezone.utc)

    # Preload sources to avoid lazy loading
    sources_res = await db.execute(select(Source))
    sources_map = {s.id: s.name for s in sources_res.scalars().all()}

    # Clear old trend records before recomputing
    await db.execute(delete(Trend))
    await db.flush()

    prob_stmt = select(Problem).options(
        selectinload(Problem.evidence).selectinload(Evidence.conversation)
    )
    res = await db.execute(prob_stmt)
    problems = res.scalars().all()

    trends_created = 0

    for prob in problems:
        convs = [e.conversation for e in prob.evidence if e.conversation]
        if not convs:
            continue

        # Group conversation timestamps into buckets
        # Default bucket: 7 days
        buckets: Dict[str, List[Conversation]] = defaultdict(list)
        for c in convs:
            ts = c.timestamp or c.created_at or now
            # Bucket key: YYYY-MM-DD
            b_date = ts.date()
            # Align to week start or 7-day window
            b_start = b_date - timedelta(days=b_date.weekday())
            buckets[str(b_start)].append(c)

        sorted_bucket_keys = sorted(buckets.keys())
        prior_count = 0
        latest_growth = 0.0

        for b_key in sorted_bucket_keys:
            b_convs = buckets[b_key]
            current_count = len(b_convs)
            b_start_dt = datetime.fromisoformat(b_key).replace(tzinfo=timezone.utc)
            b_end_dt = b_start_dt + timedelta(days=bucket_days)

            growth = (current_count - prior_count) / max(prior_count, 1) if prior_count > 0 else 0.0
            latest_growth = growth

            # Collect source breakdown in this bucket
            sources_dict: Dict[str, int] = {}
            for bc in b_convs:
                s_name = sources_map.get(bc.source_id, "unknown")
                sources_dict[s_name] = sources_dict.get(s_name, 0) + 1

            trend_row = Trend(
                id=_uuid(),
                problem_id=prob.id,
                period_start=b_start_dt,
                period_end=b_end_dt,
                conversation_count=current_count,
                growth_rate=round(growth, 4),
                sources=sources_dict,
            )
            db.add(trend_row)
            trends_created += 1
            prior_count = current_count

        prob.growth_rate = round(latest_growth, 4)

    await db.commit()

    return {
        "problems_processed": len(problems),
        "trends_created": trends_created,
        "trends_calculated": trends_created,
        "status": "success",
    }


def _to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def get_trends_data(
    db: AsyncSession,
    period: str = "30d",
    granularity: str = "week",
) -> List[Dict[str, Any]]:
    """Fetch time-series trend data per problem for chart visualization."""
    days = _parse_period_days(period)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    res = await db.execute(
        select(Problem).options(selectinload(Problem.trends))
    )
    problems = res.scalars().all()

    output = []
    for p in problems:
        # Filter trends by period
        filtered_trends = [
            t for t in p.trends if t.period_start and (_to_naive_utc(t.period_start) or datetime.min) >= cutoff
        ]
        # Sort by period_start
        filtered_trends.sort(key=lambda t: _to_naive_utc(t.period_start) or datetime.min)

        data_points = [
            {
                "date": t.period_start.strftime("%Y-%m-%d") if t.period_start else "unknown",
                "count": t.conversation_count,
                "sources": t.sources,
            }
            for t in filtered_trends
        ]

        # If data points are sparse, add synthetic baseline points from evidence
        if not data_points and p.evidence:
            data_points = [
                {"date": (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d"), "count": max(1, p.frequency // 2)},
                {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "count": p.frequency},
            ]

        output.append({
            "problem_id": p.id,
            "title": p.title,
            "label": p.title,
            "frequency": p.frequency,
            "growth_rate": p.growth_rate or 0.0,
            "is_emerging": p.is_emerging,
            "data_points": data_points,
        })

    return output
