from __future__ import annotations
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Problem, TaxonomyProposal, _uuid

STANDARD_TAXONOMY_CATEGORIES = [
    "Temporal Retrieval",
    "Location Retrieval",
    "Person Retrieval",
    "Object Retrieval",
    "Event Retrieval",
    "Semantic Retrieval",
    "Visual Retrieval",
    "Text/OCR Retrieval",
    "Screenshot Retrieval",
    "Video Retrieval",
    "Document Retrieval",
    "Downloaded Media Retrieval",
    "Cross-Source Retrieval",
    "Deleted/Archived Retrieval",
    "Album/Organization Problems",
    "Search Query Formulation Problems",
    "Ranking/Relevance Problems",
    "Privacy/Permission Constraints",
    "Other",
]


def classify_taxonomy_categories(title: str, statement: str) -> List[str]:
    """Map problem title and statement to standard taxonomy categories."""
    combined = f"{title} {statement}".lower()
    cats = []

    if any(k in combined for k in ["date", "time", "year", "month", "ago", "chronolog", "temporal"]):
        cats.append("Temporal Retrieval")
    if any(k in combined for k in ["location", "place", "city", "trip", "map", "gps", "spatial", "beach", "country"]):
        cats.append("Location Retrieval")
    if any(k in combined for k in ["person", "people", "face", "family", "friend", "mom", "dad", "child"]):
        cats.append("Person Retrieval")
    if any(k in combined for k in ["screenshot", "screen capture", "receipt", "invoice"]):
        cats.append("Screenshot Retrieval")
    if any(k in combined for k in ["video", "clip", "recording", "footage"]):
        cats.append("Video Retrieval")
    if any(k in combined for k in ["ocr", "text", "sign", "writing", "document"]):
        cats.append("Text/OCR Retrieval")
    if any(k in combined for k in ["album", "folder", "organize", "cleanup", "duplicate", "storage"]):
        cats.append("Album/Organization Problems")
    if any(k in combined for k in ["query", "keywords", "formulation", "describe", "cant describe"]):
        cats.append("Search Query Formulation Problems")
    if any(k in combined for k in ["ranking", "irrelevant", "accuracy", "wrong results", "relevance"]):
        cats.append("Ranking/Relevance Problems")
    if any(k in combined for k in ["lost", "deleted", "trash", "restore", "archived", "recover"]):
        cats.append("Deleted/Archived Retrieval")

    if not cats:
        cats = ["Semantic Retrieval", "Ranking/Relevance Problems"]

    # Limit to 3 max
    return cats[:3]


async def run_taxonomy_assignment(
    db: AsyncSession,
    provider: Optional[BaseModelProvider] = None,
) -> Dict[str, Any]:
    """Assign standard categories to all problems and propose novel categories if needed."""
    res = await db.execute(select(Problem))
    problems = res.scalars().all()

    assigned_count = 0
    proposals_count = 0

    for prob in problems:
        cats = classify_taxonomy_categories(prob.title, prob.statement or "")
        prob.taxonomy_categories = cats
        assigned_count += 1

        # If problem describes a specific novel pattern (e.g. meme search or handwriting recognition)
        if "meme" in (prob.statement or "").lower():
            prop_res = await db.execute(select(TaxonomyProposal).where(TaxonomyProposal.category_name == "Meme & Viral Media Retrieval"))
            if not prop_res.scalar_one_or_none():
                prop = TaxonomyProposal(
                    id=_uuid(),
                    category_name="Meme & Viral Media Retrieval",
                    description="Retrieval friction specifically for saved memes, gifs, and internet humor images.",
                    evidence_count=prob.frequency,
                    proposed_by="ai_pipeline",
                    is_approved=False,
                )
                db.add(prop)
                proposals_count += 1

    await db.commit()

    return {
        "classified": assigned_count,
        "problems_processed": assigned_count,
        "new_proposals": proposals_count,
        "standard_categories_count": len(STANDARD_TAXONOMY_CATEGORIES),
    }


async def get_taxonomy_summary(db: AsyncSession) -> Dict[str, Any]:
    """Get category distribution across problems and list of proposals."""
    res = await db.execute(select(Problem.taxonomy_categories))
    cat_lists = res.scalars().all()

    distribution: Dict[str, int] = {cat: 0 for cat in STANDARD_TAXONOMY_CATEGORIES}
    for lst in cat_lists:
        if isinstance(lst, list):
            for c in lst:
                if c in distribution:
                    distribution[c] += 1
                else:
                    distribution[c] = distribution.get(c, 0) + 1

    # Load proposals
    p_res = await db.execute(select(TaxonomyProposal).order_by(TaxonomyProposal.created_at.desc()))
    proposals = [
        {
            "id": p.id,
            "category_name": p.category_name,
            "description": p.description,
            "evidence_count": p.evidence_count,
            "is_approved": p.is_approved,
            "proposed_by": p.proposed_by,
        }
        for p in p_res.scalars().all()
    ]

    return {
        "categories": distribution,
        "proposals": proposals,
        "total_proposals": len(proposals),
        "total_problems": len(cat_lists),
    }
