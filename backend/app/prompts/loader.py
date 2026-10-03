from __future__ import annotations
import os
from functools import lru_cache
from typing import Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PromptVersion

_PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PROMPT_VERSIONS: Dict[str, str] = {
    "relevance": "relevance-v1.0",
    "analysis": "analysis-v1.0",
}


@lru_cache(maxsize=32)
def load_prompt(version: str) -> str:
    """Load prompt template text from file system by version name."""
    filename = f"{version}.txt" if not version.endswith(".txt") else version
    filepath = os.path.join(_PROMPTS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt template file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_active_prompt_version(stage: str) -> str:
    """Return the active prompt version identifier for a pipeline stage."""
    return DEFAULT_PROMPT_VERSIONS.get(stage, f"{stage}-v1.0")


async def seed_prompt_versions(db: AsyncSession) -> None:
    """Populate prompt_versions table with active prompts on application startup."""
    for stage, version in DEFAULT_PROMPT_VERSIONS.items():
        try:
            prompt_text = load_prompt(version)
            result = await db.execute(select(PromptVersion).where(PromptVersion.id == version))
            existing = result.scalar_one_or_none()
            if not existing:
                pv = PromptVersion(
                    id=version,
                    stage=stage,
                    prompt_text=prompt_text,
                    notes=f"Default {stage} prompt version {version}",
                )
                db.add(pv)
            else:
                existing.prompt_text = prompt_text
        except Exception as e:
            # Non-blocking if file read error occurs
            pass
    await db.commit()
