from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import RequireViewer
from app.db.models import Cluster, ClusterMembership, Conversation, Source
from app.db.session import get_db

router = APIRouter()


@router.get("", summary="List semantic clusters")
async def list_clusters(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = select(Cluster).where(Cluster.is_archived == False)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    res = await db.execute(stmt.order_by(desc(Cluster.member_count)).offset(skip).limit(limit))
    records = res.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": c.id,
                "label": c.label,
                "description": c.description,
                "member_count": c.member_count,
                "has_centroid": c.centroid is not None,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in records
        ],
    }


@router.get("/{cluster_id}", summary="Get cluster detail with member conversations")
async def get_cluster(
    cluster_id: str,
    limit_members: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: None = RequireViewer,
):
    stmt = (
        select(Cluster)
        .options(
            selectinload(Cluster.memberships)
            .selectinload(ClusterMembership.conversation)
        )
        .where(Cluster.id == cluster_id)
    )
    res = await db.execute(stmt)
    cluster = res.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    sources_res = await db.execute(select(Source))
    sources_map = {s.id: s.name for s in sources_res.scalars().all()}

    memberships = sorted(cluster.memberships, key=lambda m: m.similarity_score or 0.0, reverse=True)

    members = []
    for m in memberships[:limit_members]:
        conv = m.conversation
        if conv:
            members.append({
                "conversation_id": conv.id,
                "source": sources_map.get(conv.source_id, "unknown"),
                "title": conv.title,
                "text": (conv.cleaned_text or conv.text or "")[:300],
                "similarity_score": m.similarity_score,
                "timestamp": conv.timestamp,
            })

    return {
        "id": cluster.id,
        "label": cluster.label,
        "description": cluster.description,
        "member_count": cluster.member_count,
        "created_at": cluster.created_at,
        "members": members,
        "conversations": members,
    }
