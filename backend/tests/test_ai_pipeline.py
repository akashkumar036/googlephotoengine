from __future__ import annotations
import pytest
from sqlalchemy import select
from app.db.models import Conversation, AIAnalysis, Job
from app.models.providers.mock import MockProvider
from app.pipeline.analysis import (
    analyze_relevance_stage,
    analyze_deep_stage,
    generate_embeddings_stage,
)
from app.pipeline.orchestrator import run_full_pipeline


@pytest.mark.asyncio
async def test_relevance_and_deep_analysis_pipeline(db_session):
    # 1. Create a relevant and an irrelevant test conversation
    conv_rel = Conversation(
        title="Can't find wedding photo",
        text="I am searching for my wedding photo from 2 years ago at the beach, but Google Photos search gives 0 results!",
        cleaned_text="I am searching for my wedding photo from 2 years ago at the beach, but Google Photos search gives 0 results!",
        is_cleaned=True,
    )
    conv_irrel = Conversation(
        title="Fixing my lawn mower engine",
        text="My gasoline lawn mower won't start after sitting all winter.",
        cleaned_text="My gasoline lawn mower won't start after sitting all winter.",
        is_cleaned=True,
    )
    db_session.add_all([conv_rel, conv_irrel])
    await db_session.commit()
    await db_session.refresh(conv_rel)
    await db_session.refresh(conv_irrel)

    mock_prov = MockProvider()

    # 2. Run Stage 1 Relevance
    rel_stats = await analyze_relevance_stage(
        db_session,
        [conv_rel.id, conv_irrel.id],
        provider=mock_prov,
    )
    assert rel_stats["total"] == 2
    assert rel_stats["relevant"] == 1
    assert rel_stats["irrelevant"] == 1

    await db_session.refresh(conv_rel)
    await db_session.refresh(conv_irrel)
    assert conv_rel.is_relevant is True
    assert conv_irrel.is_relevant is False

    # 3. Run Stage 2 Deep Analysis
    deep_stats = await analyze_deep_stage(
        db_session,
        [conv_rel.id, conv_irrel.id],
        provider=mock_prov,
    )
    assert deep_stats["analyzed"] == 1
    assert deep_stats["skipped_irrelevant"] == 1

    # Verify AIAnalysis entry for relevant conversation
    res = await db_session.execute(select(AIAnalysis).where(AIAnalysis.conversation_id == conv_rel.id))
    analysis = res.scalar_one_or_none()
    assert analysis is not None
    assert analysis.primary_intent == "find_photo"
    assert "temporal" in analysis.memory_types or "spatial" in analysis.memory_types
    assert analysis.prompt_version == "analysis-v1.0"
    assert analysis.model_provider == "mock"

    # 4. Verify Caching: Running again skips re-analysis
    cache_stats = await analyze_deep_stage(
        db_session,
        [conv_rel.id],
        provider=mock_prov,
    )
    assert cache_stats["cached"] == 1
    assert cache_stats["analyzed"] == 0

    # 5. Run Stage 3 Embeddings
    embed_stats = await generate_embeddings_stage(
        db_session,
        [conv_rel.id],
        provider=mock_prov,
    )
    assert embed_stats["embedded"] == 1

    await db_session.refresh(conv_rel)
    assert conv_rel.embedding is not None
    assert len(conv_rel.embedding) == 1536
    assert conv_rel.embedding_model == "text-embedding-3-small"

    # 6. Verify Embedding Reuse: Running embedding again skips already embedded
    reembed_stats = await generate_embeddings_stage(
        db_session,
        [conv_rel.id],
        provider=mock_prov,
    )
    assert reembed_stats["reused"] == 1
    assert reembed_stats["embedded"] == 0


@pytest.mark.asyncio
async def test_full_pipeline_orchestrator(db_session, monkeypatch):
    """Test run_full_pipeline runs end-to-end on demo data."""
    engine = db_session.bind
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # Run full pipeline with demo source
    res = await run_full_pipeline(source="demo", limit=15, run_embeddings=True, session_factory=factory)

    assert res["source"] == "demo"
    assert res["records_fetched"] >= 15
    assert res["records_stored"] >= 15
    assert res["relevance"]["total"] >= 15
    assert res["relevance"]["relevant"] >= 1
    assert res["deep_analysis"]["analyzed"] >= 1
    assert res["embeddings"]["embedded"] >= 1
