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


if __name__ == "__main__":
    import asyncio

    async def _main():
        await seed_admin_user()
        await seed_sources()
        await seed_prompts()
        await seed_demo_dataset()
        await seed_evaluation_benchmarks()

    asyncio.run(_main())
