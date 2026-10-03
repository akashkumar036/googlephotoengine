"""
Idempotent seed: creates the admin user and connector sources on startup or CLI.
Safe to run multiple times — all operations are idempotent.
"""
from __future__ import annotations

import os
import sys

# Ensure backend root is in sys.path when running standalone
_backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

import structlog
from sqlalchemy import select, func

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.models import User, Source, _uuid
from app.auth.security import hash_password

log = structlog.get_logger()
settings = get_settings()


async def seed_admin_user() -> None:
    """Create default admin user if it doesn't already exist."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == settings.admin_email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                log.info("seed_admin_skip", reason="admin already exists", email=settings.admin_email)
                return

            admin = User(
                id=_uuid(),
                email=settings.admin_email,
                role="admin",
                hashed_password=hash_password(settings.admin_password),
            )
            session.add(admin)
            await session.commit()
            log.info("seed_admin_created", email=settings.admin_email)
    except Exception as exc:
        log.warning("seed_admin_deferred", reason=str(exc))


async def seed_sources() -> None:
    """Create Source rows for each registered connector if they don't exist."""
    try:
        from app.connectors.registry import SOURCE_METADATA

        async with AsyncSessionLocal() as session:
            for source_name, meta in SOURCE_METADATA.items():
                result = await session.execute(
                    select(Source).where(Source.name == source_name)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    continue
                source = Source(
                    id=_uuid(),
                    name=source_name,
                    connector_type=meta["connector_type"],
                    is_active=meta.get("is_active", True),
                    config={"display_name": meta.get("display_name", source_name)},
                )
                session.add(source)
                log.info("seed_source_created", name=source_name)
            await session.commit()
    except Exception as exc:
        log.warning("seed_sources_deferred", reason=str(exc))


async def seed_prompts() -> None:
    """Seed prompt versions into prompt_versions table."""
    try:
        from app.prompts.loader import seed_prompt_versions

        async with AsyncSessionLocal() as session:
            await seed_prompt_versions(session)
            log.info("seed_prompts_completed")
    except Exception as exc:
        log.warning("seed_prompts_deferred", reason=str(exc))


async def seed_demo_dataset() -> None:
    """Seed conversations from data/demo_dataset.json into conversations table."""
    import json
    from datetime import datetime, timezone
    from app.db.models import Conversation

    # Locate demo_dataset.json
    possible_paths = [
        os.path.join(_backend_root, "..", "data", "demo_dataset.json"),
        os.path.join(_backend_root, "data", "demo_dataset.json"),
        "d:/New folder (2)/Photo Discovery Engine/data/demo_dataset.json",
    ]
    file_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if not file_path:
        log.warning("demo_dataset_file_not_found", paths=possible_paths)
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data.get("records", [])
        async with AsyncSessionLocal() as session:
            sources_cache = {}
            inserted = 0

            for rec in records:
                ext_id = rec.get("id")
                # Check if already exists
                existing = (
                    await session.execute(
                        select(Conversation.id).where(Conversation.external_id == ext_id)
                    )
                ).scalar_one_or_none()
                if existing:
                    continue

                source_name = rec.get("source", "demo")
                if source_name not in sources_cache:
                    src = (
                        await session.execute(select(Source).where(Source.name == source_name))
                    ).scalar_one_or_none()
                    if not src:
                        src = Source(id=_uuid(), name=source_name, connector_type=source_name)
                        session.add(src)
                        await session.flush()
                    sources_cache[source_name] = src
                source = sources_cache[source_name]

                ts = None
                if rec.get("timestamp"):
                    try:
                        ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                    except Exception:
                        ts = datetime.now(timezone.utc)

                conv = Conversation(
                    id=_uuid(),
                    source_id=source.id,
                    external_id=ext_id,
                    url=rec.get("url"),
                    author_hash=rec.get("author_hash"),
                    title=rec.get("title") or "",
                    text=rec.get("text") or "",
                    cleaned_text=rec.get("text") or "",
                    timestamp=ts,
                    language="en",
                    engagement=rec.get("engagement") or {},
                    metadata_=rec.get("metadata") or {},
                    dedup_status="original",
                    is_cleaned=True,
                    is_relevant=True,
                    is_spam=False,
                    is_demo=True,
                )
                session.add(conv)
                inserted += 1

            await session.commit()
            log.info("seed_demo_dataset_completed", inserted=inserted, total=len(records))
    except Exception as exc:
        log.warning("seed_demo_dataset_failed", error=str(exc))


async def seed_evaluation_benchmarks() -> None:
    """Seed 30 ground-truth labeled benchmark conversations into evaluation_benchmarks table."""
    from app.db.models import EvaluationBenchmark, Conversation

    try:
        async with AsyncSessionLocal() as session:
            # Check existing benchmark count
            existing_count = (
                await session.execute(select(func.count(EvaluationBenchmark.id)))
            ).scalar() or 0
            if existing_count >= 20:
                log.info("seed_benchmarks_skipped", existing=existing_count)
                return

            # Grab 30 conversations
            convs = (
                (
                    await session.execute(
                        select(Conversation).where(Conversation.is_demo == True).limit(30)
                    )
                )
                .scalars()
                .all()
            )

            intents = ["find_photo", "find_video", "find_screenshot", "cleanup_duplicates", "album_organization"]
            failure_modes_catalog = [
                ["keyword_mismatch"],
                ["temporal_drift", "no_results"],
                ["false_positive", "poor_ranking"],
                ["face_failure"],
                ["keyword_mismatch", "false_positive"],
            ]

            seeded = 0
            for idx, c in enumerate(convs):
                b_exists = (
                    await session.execute(
                        select(EvaluationBenchmark.id).where(EvaluationBenchmark.conversation_id == c.id)
                    )
                ).scalar_one_or_none()
                if b_exists:
                    continue

                is_rel = False if idx in (4, 11, 19, 27) else True
                b = EvaluationBenchmark(
                    id=_uuid(),
                    conversation_id=c.id,
                    ground_truth_relevance=is_rel,
                    ground_truth_intent=intents[idx % len(intents)] if is_rel else None,
                    ground_truth_failure_modes=failure_modes_catalog[idx % len(failure_modes_catalog)] if is_rel else [],
                )
                session.add(b)
                seeded += 1

            await session.commit()
            log.info("seed_evaluation_benchmarks_completed", seeded=seeded)
    except Exception as exc:
        log.warning("seed_evaluation_benchmarks_failed", error=str(exc))


async def seed_problems_and_clusters() -> None:
    """Seed structured problem clusters, evidence links, opportunities, and trends."""
    from datetime import datetime, timezone, timedelta
    from app.db.models import (
        Problem,
        Cluster,
        ClusterMembership,
        Evidence,
        Opportunity,
        Trend,
        Conversation,
        AIAnalysis,
    )

    try:
        async with AsyncSessionLocal() as session:
            existing_p = (await session.execute(select(func.count(Problem.id)))).scalar() or 0
            if existing_p >= 4:
                log.info("seed_problems_skip", reason="problems already exist", count=existing_p)
                return

            convs = (await session.execute(select(Conversation).limit(60))).scalars().all()
            if not convs:
                log.warning("seed_problems_no_convs", reason="seed demo dataset first")
                return

            now = datetime.now(timezone.utc)

            # Ensure AIAnalysis rows exist for conversations
            for idx, c in enumerate(convs):
                existing_a = (
                    await session.execute(select(AIAnalysis.id).where(AIAnalysis.conversation_id == c.id))
                ).scalar_one_or_none()
                if not existing_a:
                    intents = ["find_photo", "find_screenshot", "find_video", "cleanup_duplicates", "album_organization", "troubleshoot_search"]
                    memory_sets = [
                        ["temporal", "visual"],
                        ["spatial", "social"],
                        ["text", "temporal"],
                        ["emotional", "visual"],
                        ["social", "temporal"],
                    ]
                    failure_sets = [
                        ["keyword_mismatch"],
                        ["ocr_failure", "unknown_date"],
                        ["poor_ranking", "false_positive"],
                        ["face_failure"],
                        ["temporal_drift", "no_results"],
                    ]
                    analysis = AIAnalysis(
                        id=_uuid(),
                        conversation_id=c.id,
                        primary_intent=intents[idx % len(intents)],
                        memory_types=memory_sets[idx % len(memory_sets)],
                        failure_modes=failure_sets[idx % len(failure_sets)],
                        frustration_level=round(0.4 + 0.1 * (idx % 6), 2),
                        severity=round(0.5 + 0.08 * (idx % 5), 2),
                        confidence=round(0.85 + 0.02 * (idx % 6), 2),
                        prompt_version="analysis-v1.1",
                    )
                    session.add(analysis)
            await session.flush()

            # Define 5 problem archetypes
            problem_archetypes = [
                {
                    "title": "Natural Language Query Vocabulary Mismatch in Photo Search",
                    "statement": "Users describe scenes using subjective, situational, or relational concepts ('my daughter's birthday cake', 'receipt from the plumber') which traditional keyword indices fail to retrieve.",
                    "taxonomy": ["Semantic Search", "Query Understanding"],
                    "frequency": 38,
                    "source_count": 4,
                    "frustration": 0.82,
                    "severity": 0.78,
                    "growth_rate": 0.35,
                    "is_emerging": True,
                    "segments": ["Everyday Smartphone Shooters", "Organized Archivists"],
                    "opportunity": {
                        "observed": "Users query with natural narrative phrases that return zero or misleading results.",
                        "need": "Multimodal semantic retrieval capable of cross-referencing OCR, visual context, and chronological anchors.",
                        "area": "Context-Aware Semantic Embeddings",
                        "hypothesis": "Providing LLM-guided query rewriting with proactive synonym expansion will reduce zero-result rates by 40%.",
                    },
                },
                {
                    "title": "Receipt & Document Screenshot Ingestion and OCR Degradation",
                    "statement": "Critical financial receipts, travel itineraries, and whiteboard diagrams saved as screenshots are lost in the primary camera roll due to incomplete text indexing and lack of document separation.",
                    "taxonomy": ["OCR & Document Retrieval", "Library Organization"],
                    "frequency": 29,
                    "source_count": 3,
                    "frustration": 0.74,
                    "severity": 0.70,
                    "growth_rate": 0.18,
                    "is_emerging": False,
                    "segments": ["Students & Researchers", "Expense Managers"],
                    "opportunity": {
                        "observed": "Users struggle to locate store receipts months later when text on paper is slightly blurred or folded.",
                        "need": "Zero-friction document capture segregation with automated fuzzy OCR indexing.",
                        "area": "Dedicated Document & Screenshot Siloing",
                        "hypothesis": "Auto-classifying digital screenshots into a distinct utility gallery with searchable line-item entities will eliminate 60% of search friction.",
                    },
                },
                {
                    "title": "Burst Mode and Near-Duplicate Clutter Obscuring Definitive Memory Photos",
                    "statement": "Rapid shutter bursts, bracketed exposures, and repeated social media saves flood search results with dozens of identical thumbnails, making discovery of the single best shot arduous.",
                    "taxonomy": ["Duplicate Detection", "Curation & Decluttering"],
                    "frequency": 24,
                    "source_count": 3,
                    "frustration": 0.68,
                    "severity": 0.65,
                    "growth_rate": 0.28,
                    "is_emerging": True,
                    "segments": ["Action & Sports Photographers", "Social Media Creators"],
                    "opportunity": {
                        "observed": "Search results show 30 near-identical frames of the same jump or expression.",
                        "need": "Intelligent stack collapsing that algorithmically selects and surfaces the top-rated frame.",
                        "area": "Smart Burst Stacking & De-duplication",
                        "hypothesis": "Visual aesthetics scoring to group bursts into a single collapsed hero card will improve retrieval speed by 50%.",
                    },
                },
                {
                    "title": "Temporal Decay and Vague Chronological Search Failure",
                    "statement": "When users forget exact calendar dates ('sometime in fall 2023' or 'when my kid was a toddler'), rigid date-filter interfaces fail to surface memories without exhausting manual scrolling.",
                    "taxonomy": ["Chronological Search", "Memory Anchor Navigation"],
                    "frequency": 21,
                    "source_count": 3,
                    "frustration": 0.72,
                    "severity": 0.69,
                    "growth_rate": 0.12,
                    "is_emerging": False,
                    "segments": ["Long-term Family Archivists"],
                    "opportunity": {
                        "observed": "Users know the relative life chapter but not the calendar month.",
                        "need": "Milestone-based and relative event navigation.",
                        "area": "Milestone-Anchored Chronology",
                        "hypothesis": "Allowing users to navigate memories by life chapters ('College years', 'New house') will resolve 45% of date-drift failures.",
                    },
                },
            ]

            for p_idx, arch in enumerate(problem_archetypes):
                cluster = Cluster(
                    id=_uuid(),
                    label=arch["title"][:80],
                    description=arch["statement"],
                    member_count=arch["frequency"],
                )
                session.add(cluster)
                await session.flush()

                prob = Problem(
                    id=_uuid(),
                    title=arch["title"],
                    statement=arch["statement"],
                    frequency=arch["frequency"],
                    source_count=arch["source_count"],
                    frustration_score=arch["frustration"],
                    severity_score=arch["severity"],
                    growth_rate=arch["growth_rate"],
                    cross_source_score=round(arch["source_count"] / 4.0, 2),
                    evidence_diversity_score=0.88,
                    confidence=0.89,
                    is_emerging=arch["is_emerging"],
                    is_approved=True,
                    taxonomy_categories=arch["taxonomy"],
                    user_segments=arch["segments"],
                )
                session.add(prob)
                await session.flush()

                # Link supporting conversations as Evidence
                assigned_convs = convs[p_idx * 6 : (p_idx + 1) * 6]
                for c in assigned_convs:
                    ev = Evidence(
                        id=_uuid(),
                        problem_id=prob.id,
                        conversation_id=c.id,
                        relevance_score=0.92,
                        excerpt=(c.cleaned_text or c.text or "")[:200],
                    )
                    session.add(ev)
                    cm = ClusterMembership(
                        cluster_id=cluster.id,
                        conversation_id=c.id,
                        similarity_score=0.85,
                    )
                    session.add(cm)

                # Add Opportunity
                opp_data = arch["opportunity"]
                opp = Opportunity(
                    id=_uuid(),
                    problem_id=prob.id,
                    observed_problem=opp_data["observed"],
                    underlying_need=opp_data["need"],
                    opportunity_area=opp_data["area"],
                    solution_hypothesis=opp_data["hypothesis"],
                    confidence=0.86,
                    is_validated=False,
                )
                session.add(opp)

                # Add Trend data points
                for week in range(4):
                    t = Trend(
                        id=_uuid(),
                        problem_id=prob.id,
                        period_start=now - timedelta(days=(4 - week) * 7),
                        period_end=now - timedelta(days=(3 - week) * 7),
                        conversation_count=int(arch["frequency"] * (0.2 + 0.05 * week)),
                        growth_rate=arch["growth_rate"],
                        sources=["reddit", "google_play", "app_store"],
                    )
                    session.add(t)

            await session.commit()
            log.info("seed_problems_and_clusters_completed", count=len(problem_archetypes))
    except Exception as exc:
        log.warning("seed_problems_and_clusters_failed", error=str(exc))


if __name__ == "__main__":
    import asyncio

    async def _main():
        await seed_admin_user()
        await seed_sources()
        await seed_prompts()
        await seed_demo_dataset()
        await seed_evaluation_benchmarks()
        await seed_problems_and_clusters()

    asyncio.run(_main())
