"""
Idempotent seed: creates the admin user from env vars on every startup.
Safe to run multiple times — skips if user already exists.
"""
from __future__ import annotations

import structlog

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.auth.security import hash_password
from sqlalchemy import select

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
                email=settings.admin_email,
                role="admin",
                hashed_password=hash_password(settings.admin_password),
            )
            session.add(admin)
            await session.commit()
            log.info("seed_admin_created", email=settings.admin_email)
    except Exception as exc:
        log.warning("seed_admin_deferred", reason=str(exc))
