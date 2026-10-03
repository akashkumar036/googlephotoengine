from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc, and_, Text
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.models import Conversation, Problem, Cluster, AIAnalysis, Source, Job
from app.db.session import get_db

router = APIRouter()


@router.get("", summary="Get global overview statistics and charts data")
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
) -> Dict[str, Any]:
    """
    Returns aggregated metrics for the Overview Dashboard:
    - 6 KPI numbers (total conversations, problems, emerging, clusters, embeddings, analyzed)
    - Memory dimension distribution
    - Retrieval failure modes distribution
    - Source platform breakdown
    - Recent system activity
    """
    # 1. Total conversations
    total_convs = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0

    # 2. Total problems
    total_problems = (await db.execute(select(func.count(Problem.id)))).scalar() or 0

    # 3. Emerging problems
    emerging_problems = (
        await db.execute(select(func.count(Problem.id)).where(Problem.is_emerging == True))
    ).scalar() or 0

    # 4. Total clusters
    total_clusters = (await db.execute(select(func.count(Cluster.id)))).scalar() or 0

    # 5. Embeddings count
    vector_embeddings = (
        await db.execute(select(func.count(Conversation.id)).where(Conversation.embedding.isnot(None)))
    ).scalar() or 0

    # 6. Analyzed conversations
    analyzed_convs = (await db.execute(select(func.count(AIAnalysis.id)))).scalar() or 0

    # 7. Relevant conversations
    relevant_convs = (
        await db.execute(select(func.count(Conversation.id)).where(Conversation.is_relevant == True))
    ).scalar() or 0

    # 8. Memory dimension distribution
    # Extract from AIAnalysis.memory_types
    analysis_records = (
        await db.execute(
            select(AIAnalysis.memory_types, AIAnalysis.failure_modes)
            .join(Conversation, AIAnalysis.conversation_id == Conversation.id)
            .where(Conversation.is_relevant == True)
            .limit(1000)
        )
    ).all()

    memory_counts: Dict[str, int] = {
        "temporal": 0,
        "spatial": 0,
        "social": 0,
        "visual": 0,
        "event": 0,
        "semantic": 0,
    }
    failure_counts: Dict[str, int] = {
        "keyword_mismatch": 0,
        "temporal_drift": 0,
        "false_positive": 0,
        "no_results": 0,
        "face_failure": 0,
        "poor_ranking": 0,
    }

    for row in analysis_records:
        m_types = row[0] or []
        f_modes = row[1] or []
        for m in m_types:
            key = str(m).lower()
            memory_counts[key] = memory_counts.get(key, 0) + 1
        for f in f_modes:
            key = str(f).lower()
            failure_counts[key] = failure_counts.get(key, 0) + 1

    memory_distribution = [
        {"dimension": k.capitalize(), "count": v}
        for k, v in sorted(memory_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]
    failure_distribution = [
        {"mode": k.replace("_", " ").title(), "count": v}
        for k, v in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    # 9. Source distribution
    source_rows = (
        await db.execute(
            select(Source.name, func.count(Conversation.id))
            .join(Conversation, Conversation.source_id == Source.id)
            .group_by(Source.name)
        )
    ).all()

    source_breakdown = [
        {"source": name.capitalize() if name else "Unknown", "count": count}
        for name, count in source_rows
    ]

    # If no data yet in sources, provide standard defaults
    if not source_breakdown:
        source_breakdown = [
            {"source": "Reddit", "count": 0},
            {"source": "YouTube", "count": 0},
            {"source": "Demo", "count": 0},
        ]

    # 10. Recent Activity feed (Jobs + Problems)
    recent_jobs = (
        (
            await db.execute(
                select(Job).order_by(desc(Job.created_at)).limit(5)
            )
        )
        .scalars()
        .all()
    )

    recent_problems = (
        (
            await db.execute(
                select(Problem).order_by(desc(Problem.created_at)).limit(5)
            )
        )
        .scalars()
        .all()
    )

    activity = []
    for j in recent_jobs:
        activity.append({
            "id": f"job-{j.id}",
            "type": "job",
            "title": f"Pipeline job {j.type} ({j.status})",
            "time": j.created_at.isoformat() if j.created_at else None,
            "status": j.status,
        })
    for p in recent_problems:
        activity.append({
            "id": f"problem-{p.id}",
            "type": "problem",
            "title": f"Problem identified: {p.title[:60]}",
            "time": p.created_at.isoformat() if p.created_at else None,
            "status": "emerging" if p.is_emerging else "active",
        })

    # Sort activity by time descending
    activity.sort(key=lambda x: x.get("time") or "", reverse=True)

    return {
        "kpis": {
            "total_conversations": total_convs,
            "analyzed_conversations": analyzed_convs,
            "relevant_conversations": relevant_convs,
            "total_problems": total_problems,
            "emerging_problems": emerging_problems,
            "total_clusters": total_clusters,
            "vector_embeddings": vector_embeddings,
        },
        "memory_distribution": memory_distribution,
        "failure_distribution": failure_distribution,
        "source_breakdown": source_breakdown,
        "recent_activity": activity[:10],
    }
