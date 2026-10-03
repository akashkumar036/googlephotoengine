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
from sqlalchemy import select

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


if __name__ == "__main__":
    import asyncio

    async def _main():
        await seed_admin_user()
        await seed_sources()

    asyncio.run(_main())
