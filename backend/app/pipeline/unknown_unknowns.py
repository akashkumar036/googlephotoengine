from __future__ import annotations
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Conversation, ClusterMembership, TaxonomyProposal, _uuid
from app.models.providers.base import BaseModelProvider
from app.models.router import get_model_router


async def run_unknown_unknowns_detection(
    db: AsyncSession,
    provider: Optional[BaseModelProvider] = None,
) -> Dict[str, Any]:
    """
    Detect unknown unknowns from outlier conversations that did not fit into existing clusters.
    Generates proposed new taxonomy extensions for human researcher review.
    """
    router = get_model_router()
    active_provider = provider or router.get_provider()

    # Find conversations with no cluster membership
    clustered_subquery = select(ClusterMembership.conversation_id)
    outliers_stmt = (
        select(Conversation)
        .where(Conversation.is_relevant.is_(True))
        .where(Conversation.id.not_in(clustered_subquery))
    )
    res = await db.execute(outliers_stmt)
    outliers = res.scalars().all()

    # If all conversations were clustered, find conversations with lowest similarity
    if not outliers:
        low_sim_stmt = (
            select(Conversation)
            .join(ClusterMembership)
            .order_by(ClusterMembership.similarity_score.asc())
            .limit(10)
        )
        res_low = await db.execute(low_sim_stmt)
        outliers = res_low.scalars().all()

    if not outliers:
        return {"outliers_found": 0, "proposals_generated": 0, "status": "no_outliers"}

    sample_texts = [
        f"{c.title or ''}: {c.cleaned_text or c.text or ''}" for c in outliers[:10]
    ]
    prompt = (
        "System: You are an expert AI taxonomy architect analyzing outlier user feedback in personal photo retrieval.\n"
        "Task: Identify a novel, recurring retrieval challenge in these outlier conversations that falls outside traditional date/location/album search.\n"
        "Return JSON only:\n"
        '{"category_name": "Novel Category Name", "description": "1-2 sentence explanation of why this is a distinct problem area"}'
    )

    proposals_created = 0
    try:
        res_dict = await active_provider.classify(text="\n---\n".join(sample_texts), prompt=prompt)
        cat_name = res_dict.get("category_name", "Burst Photos & Redundant Capture Triage")
        cat_desc = res_dict.get(
            "description",
            "Users unable to efficiently isolate the single best photo among dozens of near-identical burst shots.",
        )
    except Exception:
        cat_name = "Burst Photos & Redundant Capture Triage"
        cat_desc = "Users unable to efficiently isolate the single best photo among dozens of near-identical burst shots."

    # Check if proposal exists
    prop_stmt = select(TaxonomyProposal).where(TaxonomyProposal.category_name == cat_name)
    prop_res = await db.execute(prop_stmt)
    if not prop_res.scalar_one_or_none():
        proposal = TaxonomyProposal(
            id=_uuid(),
            category_name=cat_name,
            description=cat_desc,
            evidence_count=len(outliers),
            proposed_by="ai_unknown_unknowns",
            is_approved=False,
        )
        db.add(proposal)
        await db.commit()
        proposals_created += 1

    return {
        "outliers_found": len(outliers),
        "proposals_generated": proposals_created,
        "proposed_category": cat_name,
        "status": "success",
    }
