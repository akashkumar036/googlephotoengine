from __future__ import annotations
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.db.models import Conversation, AIAnalysis, _uuid
from app.models.providers.base import BaseModelProvider
from app.models.router import get_model_router
from app.models.schemas import DeepAnalysisOutput, RelevanceOutput
from app.prompts.loader import get_active_prompt_version, load_prompt

logger = logging.getLogger(__name__)
settings = get_settings()


async def analyze_relevance_stage(
    db: AsyncSession,
    conversation_ids: List[str],
    provider: Optional[BaseModelProvider] = None,
    prompt_version: Optional[str] = None,
    batch_size: int = 20,
) -> Dict[str, Any]:
    """
    Stage 1: Filter conversations by relevance to photo retrieval research.
    Sets conversation.is_relevant and initializes/updates AIAnalysis.
    """
    router = get_model_router()
    active_provider = provider or router.get_provider()
    version = prompt_version or get_active_prompt_version("relevance")
    prompt_text = load_prompt(version)
    stage1_model = router.get_stage1_model(active_provider.provider_name)

    stats = {
        "total": len(conversation_ids),
        "relevant": 0,
        "irrelevant": 0,
        "errors": 0,
        "processed_ids": [],
    }

    # Process in batches
    for i in range(0, len(conversation_ids), batch_size):
        batch_ids = conversation_ids[i : i + batch_size]
        stmt = select(Conversation).where(Conversation.id.in_(batch_ids))
        res = await db.execute(stmt)
        conversations = res.scalars().all()

        for conv in conversations:
            try:
                # Prepare text (title + cleaned_text or raw text)
                text_parts = []
                if conv.title:
                    text_parts.append(conv.title)
                text_parts.append(conv.cleaned_text or conv.text or "")
                full_text = "\n".join(text_parts)

                # Classify via Stage 1 model
                raw_dict = await active_provider.classify(
                    text=full_text,
                    prompt=prompt_text,
                    model=stage1_model,
                    schema=RelevanceOutput,
                )
                output = RelevanceOutput.model_validate(raw_dict)

                conv.is_relevant = output.is_relevant

                # Check existing AIAnalysis
                a_stmt = select(AIAnalysis).where(AIAnalysis.conversation_id == conv.id)
                a_res = await db.execute(a_stmt)
                analysis = a_res.scalar_one_or_none()

                if not analysis:
                    analysis = AIAnalysis(
                        id=_uuid(),
                        conversation_id=conv.id,
                        prompt_version=version,
                        relevance=output.relevance_score,
                        reasoning_summary=output.reasoning,
                        model_provider=active_provider.provider_name,
                        model_name=stage1_model,
                        processed_at=datetime.now(timezone.utc),
                    )
                    db.add(analysis)
                else:
                    analysis.relevance = output.relevance_score
                    analysis.prompt_version = version
                    analysis.reasoning_summary = output.reasoning
                    analysis.model_provider = active_provider.provider_name
                    analysis.model_name = stage1_model
                    analysis.processed_at = datetime.now(timezone.utc)

                if output.is_relevant:
                    stats["relevant"] += 1
                else:
                    stats["irrelevant"] += 1
                stats["processed_ids"].append(conv.id)

            except Exception as exc:
                logger.error("Error in relevance analysis for conv %s: %s", conv.id, exc)
                stats["errors"] += 1

        await db.commit()

    return stats


async def analyze_deep_stage(
    db: AsyncSession,
    conversation_ids: List[str],
    provider: Optional[BaseModelProvider] = None,
    prompt_version: Optional[str] = None,
    batch_size: int = 20,
) -> Dict[str, Any]:
    """
    Stage 2: Deep UX problem extraction for relevant conversations.
    Extracts intents, memory types, failure modes, pain points, frustration, and severity.
    Includes caching per (conversation_id, prompt_version).
    """
    router = get_model_router()
    active_provider = provider or router.get_provider()
    version = prompt_version or get_active_prompt_version("analysis")
    prompt_text = load_prompt(version)
    stage2_model = router.get_stage2_model(active_provider.provider_name)

    stats = {
        "total": len(conversation_ids),
        "analyzed": 0,
        "cached": 0,
        "skipped_irrelevant": 0,
        "errors": 0,
        "analyzed_ids": [],
    }

    for i in range(0, len(conversation_ids), batch_size):
        batch_ids = conversation_ids[i : i + batch_size]
        stmt = select(Conversation).where(Conversation.id.in_(batch_ids))
        res = await db.execute(stmt)
        conversations = res.scalars().all()

        for conv in conversations:
            # Skip if explicitly irrelevant
            if conv.is_relevant is False:
                stats["skipped_irrelevant"] += 1
                continue

            try:
                # Check cache: existing analysis with same prompt_version
                a_stmt = select(AIAnalysis).where(AIAnalysis.conversation_id == conv.id)
                a_res = await db.execute(a_stmt)
                existing = a_res.scalar_one_or_none()

                if (
                    existing
                    and existing.prompt_version == version
                    and existing.primary_intent
                    and not conv.needs_reanalysis
                ):
                    stats["cached"] += 1
                    stats["analyzed_ids"].append(conv.id)
                    continue

                # Prepare text
                text_parts = []
                if conv.title:
                    text_parts.append(conv.title)
                text_parts.append(conv.cleaned_text or conv.text or "")
                full_text = "\n".join(text_parts)

                raw_dict = await active_provider.classify(
                    text=full_text,
                    prompt=prompt_text,
                    model=stage2_model,
                    schema=DeepAnalysisOutput,
                )
                output = DeepAnalysisOutput.model_validate(raw_dict)

                if not existing:
                    existing = AIAnalysis(
                        id=_uuid(),
                        conversation_id=conv.id,
                        prompt_version=version,
                        model_provider=active_provider.provider_name,
                        model_name=stage2_model,
                    )
                    db.add(existing)

                # Populate full analysis
                existing.primary_intent = output.primary_intent
                existing.memory_types = output.memory_types
                existing.retrieval_strategies = output.retrieval_strategies
                existing.failure_modes = output.failure_modes
                existing.pain_points = output.pain_points
                existing.user_goal = output.user_goal
                existing.known_memory = output.known_memory
                existing.unknown_memory = output.unknown_memory
                existing.frustration_level = output.frustration_level
                existing.severity = output.severity
                existing.confidence = output.confidence
                existing.reasoning_summary = output.reasoning_summary
                existing.model_provider = active_provider.provider_name
                existing.model_name = stage2_model
                existing.prompt_version = version
                existing.processed_at = datetime.now(timezone.utc)

                conv.needs_reanalysis = False
                stats["analyzed"] += 1
                stats["analyzed_ids"].append(conv.id)

            except Exception as exc:
                logger.error("Error in deep analysis for conv %s: %s", conv.id, exc)
                stats["errors"] += 1

        await db.commit()

    return stats


async def generate_embeddings_stage(
    db: AsyncSession,
    conversation_ids: List[str],
    provider: Optional[BaseModelProvider] = None,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Stage 3: Vector Embedding Generation.
    Generates 1536-dimensional embeddings for conversations, skipping already embedded ones.
    """
    router = get_model_router()
    active_provider = provider or router.get_provider()
    model_name = settings.embedding_model or "text-embedding-3-small"

    stats = {
        "total": len(conversation_ids),
        "embedded": 0,
        "reused": 0,
        "errors": 0,
        "embedded_ids": [],
    }

    for i in range(0, len(conversation_ids), batch_size):
        batch_ids = conversation_ids[i : i + batch_size]
        stmt = select(Conversation).where(Conversation.id.in_(batch_ids))
        res = await db.execute(stmt)
        conversations = res.scalars().all()

        to_embed: List[Conversation] = []
        texts: List[str] = []

        for conv in conversations:
            if conv.embedding is not None and not conv.needs_reanalysis:
                stats["reused"] += 1
                continue
            to_embed.append(conv)
            text_rep = f"{conv.title or ''} {conv.cleaned_text or conv.text or ''}".strip()
            texts.append(text_rep if text_rep else "photo retrieval discovery")

        if not to_embed:
            continue

        try:
            vectors = await active_provider.embed(texts, model=model_name)
            for conv, vec in zip(to_embed, vectors):
                conv.embedding = vec
                conv.embedding_model = model_name
                stats["embedded"] += 1
                stats["embedded_ids"].append(conv.id)
            await db.commit()
        except Exception as exc:
            logger.error("Error generating embeddings for batch: %s", exc)
            stats["errors"] += len(to_embed)

    return stats
