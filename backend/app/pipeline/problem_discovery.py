from __future__ import annotations
import math
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    Cluster,
    ClusterMembership,
    Conversation,
    AIAnalysis,
    Problem,
    Evidence,
    Opportunity,
    Source,
    _uuid,
)
from app.models.providers.base import BaseModelProvider
from app.models.router import get_model_router


def _calculate_entropy(counts: List[int]) -> float:
    """Calculate Shannon entropy for source diversity."""
    total = sum(counts)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return round(float(entropy), 4)


async def _synthesize_problem(
    provider: BaseModelProvider,
    cluster_label: str,
    cluster_desc: str,
    sample_conversations: List[Conversation],
) -> Dict[str, Any]:
    """Synthesize structured problem title, statement, segments, and opportunities."""
    samples_text = "\n---\n".join([
        f"Title: {c.title}\nText: {c.cleaned_text or c.text}" for c in sample_conversations[:8]
    ])

    prompt = (
        "System: You are a principal UX researcher in personal media & photo retrieval systems.\n"
        "Task: Based on these user complaints in a cluster, synthesize a high-impact Problem record.\n"
        "Return JSON only:\n"
        "{\n"
        '  "title": "Clear user problem title (5-10 words)",\n'
        '  "statement": "Comprehensive problem statement describing the friction, mental model mismatch, and why users fail",\n'
        '  "user_segments": ["casual_mobile", "power_organizer", "traveler"],\n'
        '  "taxonomy_categories": ["Temporal Retrieval", "Semantic Retrieval"],\n'
        '  "opportunity": {\n'
        '    "observed_problem": "Summary of observed problem",\n'
        '    "underlying_need": "Core user need",\n'
        '    "opportunity_area": "Product opportunity area",\n'
        '    "solution_hypothesis": "Hypothesized product feature or AI capability to test"\n'
        "  }\n"
        "}\n"
    )

    try:
        res = await provider.classify(text=f"Cluster: {cluster_label}\n{cluster_desc}\n\nEvidence:\n{samples_text}", prompt=prompt)
        if res and "title" in res:
            return res
    except Exception:
        pass

    # Heuristic fallback
    return {
        "title": cluster_label,
        "statement": f"Users struggle with: {cluster_desc}. When searching through large photo collections, contextual mental models do not match the index attributes.",
        "user_segments": ["casual_mobile_users", "memory_seekers"],
        "taxonomy_categories": ["Semantic Retrieval", "Search Query Formulation Problems"],
        "opportunity": {
            "observed_problem": cluster_desc,
            "underlying_need": "Intuitive discovery without remembering precise metadata",
            "opportunity_area": "Contextual Semantic Querying",
            "solution_hypothesis": "Implement fuzzy memory dimension filters (vague dates, companion recognition, scene vibes)",
        },
    }


async def run_problem_discovery(
    db: AsyncSession,
    provider: Optional[BaseModelProvider] = None,
) -> Dict[str, Any]:
    """
    Synthesize discovered problems from clusters and link evidence.
    """
    router = get_model_router()
    active_provider = provider or router.get_provider()

    # Total registered sources count & source name lookup
    sources_res = await db.execute(select(Source))
    all_sources = sources_res.scalars().all()
    sources_map = {s.id: s.name for s in all_sources}
    total_sources_count = len(all_sources) or 1

    # Preload all analyses to avoid async lazy loading
    analyses_res = await db.execute(select(AIAnalysis))
    analyses_map = {a.conversation_id: a for a in analyses_res.scalars().all()}

    # Load all clusters with memberships
    clusters_stmt = (
        select(Cluster)
        .options(selectinload(Cluster.memberships))
        .where(Cluster.member_count > 0)
    )
    res = await db.execute(clusters_stmt)
    clusters = res.scalars().all()

    if not clusters:
        return {"problems_created": 0, "evidence_linked": 0, "status": "no_clusters"}

    # Clear previous evidence and opportunities before regenerating
    await db.execute(delete(Evidence))
    await db.execute(delete(Opportunity))
    await db.execute(delete(Problem))
    await db.flush()

    problems_created = 0
    evidence_linked = 0
    opportunities_created = 0

    for cluster in clusters:
        conv_ids = [m.conversation_id for m in cluster.memberships if m.conversation_id]
        if not conv_ids:
            continue

        c_stmt = select(Conversation).where(Conversation.id.in_(conv_ids))
        convs = (await db.execute(c_stmt)).scalars().all()
        if not convs:
            continue

        # Calculate composite metrics
        frequency = len(convs)

        sources_seen = set()
        source_counts: Dict[str, int] = {}
        for c in convs:
            s_name = sources_map.get(c.source_id, "unknown")
            sources_seen.add(s_name)
            source_counts[s_name] = source_counts.get(s_name, 0) + 1

        source_count = len(sources_seen)
        cross_source_score = round(min(1.0, source_count / max(total_sources_count, 1)), 4)
        evidence_diversity_score = _calculate_entropy(list(source_counts.values()))

        # Average analysis scores
        analyses = [analyses_map[c.id] for c in convs if c.id in analyses_map]
        frustrations = [a.frustration_level for a in analyses if a.frustration_level is not None]
        severities = [a.severity for a in analyses if a.severity is not None]
        confidences = [a.confidence for a in analyses if a.confidence is not None]

        frustration_score = round(sum(frustrations) / len(frustrations), 4) if frustrations else 0.6
        severity_score = round(sum(severities) / len(severities), 4) if severities else 0.5
        confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.85

        # Synthesize problem via LLM
        synth = await _synthesize_problem(
            active_provider,
            cluster.label or "Retrieval Problem",
            cluster.description or "",
            convs,
        )

        problem_id = _uuid()
        problem = Problem(
            id=problem_id,
            title=synth.get("title", cluster.label),
            statement=synth.get("statement", cluster.description),
            taxonomy_categories=synth.get("taxonomy_categories", ["Semantic Retrieval"]),
            frequency=frequency,
            source_count=source_count,
            frustration_score=frustration_score,
            severity_score=severity_score,
            growth_rate=0.0,
            cross_source_score=cross_source_score,
            evidence_diversity_score=evidence_diversity_score,
            confidence=confidence,
            is_emerging=False,
            is_approved=True,
            user_segments=synth.get("user_segments", []),
        )
        db.add(problem)
        await db.flush()
        problems_created += 1

        # Create Evidence links (up to 10 supporting conversations per problem)
        for c in convs[:10]:
            excerpt = (c.cleaned_text or c.text or "")[:400]
            analysis = analyses_map.get(c.id)
            interpretation = analysis.reasoning_summary if analysis else None
            rel_score = analysis.relevance if (analysis and analysis.relevance is not None) else 0.9

            evidence_obj = Evidence(
                id=_uuid(),
                problem_id=problem_id,
                conversation_id=c.id,
                excerpt=excerpt,
                ai_interpretation=interpretation,
                relevance_score=rel_score,
            )
            db.add(evidence_obj)
            evidence_linked += 1

        # Create initial Opportunity record
        opp_data = synth.get("opportunity", {})
        if opp_data:
            opp = Opportunity(
                id=_uuid(),
                problem_id=problem_id,
                observed_problem=opp_data.get("observed_problem", problem.statement),
                underlying_need=opp_data.get("underlying_need", "Better retrieval"),
                opportunity_area=opp_data.get("opportunity_area", "Search Intelligence"),
                solution_hypothesis=opp_data.get("solution_hypothesis", "Develop improved semantic indexing"),
                confidence=confidence,
                is_validated=False,
            )
            db.add(opp)
            opportunities_created += 1

    await db.commit()

    return {
        "problems_created": problems_created,
        "evidence_linked": evidence_linked,
        "opportunities_created": opportunities_created,
        "status": "success",
    }
