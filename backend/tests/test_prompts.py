from __future__ import annotations
import pytest
from sqlalchemy import select
from app.db.models import PromptVersion
from app.prompts.loader import get_active_prompt_version, load_prompt, seed_prompt_versions


def test_load_prompt_files():
    # Load relevance prompt
    rel_p = load_prompt("relevance-v1.0")
    assert "relevance_score" in rel_p
    assert "photo retrieval" in rel_p.lower()

    # Load analysis prompt
    ana_p = load_prompt("analysis-v1.0")
    assert "primary_intent" in ana_p
    assert "failure_modes" in ana_p

    # Active versions
    assert get_active_prompt_version("relevance") == "relevance-v1.0"
    assert get_active_prompt_version("analysis") == "analysis-v1.0"


def test_load_nonexistent_prompt_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent-v999.0")


@pytest.mark.asyncio
async def test_seed_prompt_versions(db_session):
    # Seed prompt versions
    await seed_prompt_versions(db_session)

    res = await db_session.execute(select(PromptVersion))
    rows = res.scalars().all()
    version_ids = [r.id for r in rows]

    assert "relevance-v1.0" in version_ids
    assert "analysis-v1.0" in version_ids

    # Idempotent re-run
    await seed_prompt_versions(db_session)
    res_after = await db_session.execute(select(PromptVersion))
    assert len(res_after.scalars().all()) == len(rows)
