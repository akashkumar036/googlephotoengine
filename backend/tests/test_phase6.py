import pytest
from httpx import AsyncClient
from app.db.models import (
    Conversation,
    AIAnalysis,
    EvaluationBenchmark,
    HumanReview,
    Source,
    Job,
    _uuid,
)
from app.db.seed import seed_evaluation_benchmarks


@pytest.mark.asyncio
async def test_evaluation_benchmarks_and_metrics(client: AsyncClient, db_session, researcher_headers):
    # 1. Setup sample source & conversation
    source = Source(id=_uuid(), name="demo", connector_type="mock", is_active=True)
    db_session.add(source)
    await db_session.flush()

    conv1 = Conversation(
        id=_uuid(),
        source_id=source.id,
        external_id="post_bench_1",
        title="Can't find screenshots of receipts from last week",
        text="I am trying to find a screenshot of a store receipt from last week.",
        cleaned_text="I am trying to find a screenshot of a store receipt from last week.",
        is_relevant=True,
    )
    conv2 = Conversation(
        id=_uuid(),
        source_id=source.id,
        external_id="post_bench_2",
        title="Best camera for travel photography",
        text="Looking for camera recommendations for my upcoming trip to Japan.",
        cleaned_text="Looking for camera recommendations for my upcoming trip to Japan.",
        is_relevant=False,
    )
    db_session.add_all([conv1, conv2])
    await db_session.flush()

    # 2. Add AI Analysis
    analysis1 = AIAnalysis(
        id=_uuid(),
        conversation_id=conv1.id,
        primary_intent="find_screenshot",
        memory_types=["temporal", "text"],
        failure_modes=["ocr_failure", "unknown_date"],
        confidence=0.92,
        prompt_version="analysis-v1.1",
        model_name="llama-3.3-70b-versatile",
    )
    db_session.add(analysis1)

    # 3. Add Benchmark Ground Truth
    bench1 = EvaluationBenchmark(
        id=_uuid(),
        conversation_id=conv1.id,
        ground_truth_relevance=True,
        ground_truth_intent="find_screenshot",
        ground_truth_failure_modes=["ocr_failure", "unknown_date"],
    )
    bench2 = EvaluationBenchmark(
        id=_uuid(),
        conversation_id=conv2.id,
        ground_truth_relevance=False,
        ground_truth_intent="general_inquiry",
        ground_truth_failure_modes=[],
    )
    db_session.add_all([bench1, bench2])
    await db_session.commit()

    # 4. Test GET /evaluation/benchmarks
    res_b = await client.get("/evaluation/benchmarks", headers=researcher_headers)
    assert res_b.status_code == 200
    b_data = res_b.json()
    assert b_data["total"] >= 2
    assert any(b["ground_truth_intent"] == "find_screenshot" for b in b_data["data"])

    # 5. Test GET /evaluation/results
    res_r = await client.get("/evaluation/results", headers=researcher_headers)
    assert res_r.status_code == 200
    r_data = res_r.json()
    assert "relevance_metrics" in r_data
    assert "intent_accuracy" in r_data
    assert "failure_mode_accuracy" in r_data
    assert r_data["intent_accuracy"] == 1.0
    assert r_data["failure_mode_accuracy"] == 1.0


@pytest.mark.asyncio
async def test_feedback_learning_loop(client: AsyncClient, db_session, researcher_headers):
    # Setup conversation and human review
    source = Source(id=_uuid(), name="demo", connector_type="mock", is_active=True)
    db_session.add(source)
    await db_session.flush()

    conv = Conversation(
        id=_uuid(),
        source_id=source.id,
        external_id="post_rev_1",
        title="Can't find whiteboard photo",
        text="Looking for whiteboard photo taken in 2024",
        cleaned_text="Looking for whiteboard photo taken in 2024",
        is_relevant=True,
    )
    db_session.add(conv)
    await db_session.flush()

    review = HumanReview(
        id=_uuid(),
        target_type="conversation",
        target_id=conv.id,
        action="correct",
        original_value={"intent": "find_photo", "relevance": True},
        corrected_value={"intent": "find_document_whiteboard", "relevance": True},
        notes="Corrected to specific whiteboard document type",
    )
    db_session.add(review)
    await db_session.commit()

    res = await client.get("/evaluation/feedback-loop", headers=researcher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_corrections"] >= 1
    assert "top_intent_corrections" in data
    assert any(
        c["from_intent"] == "find_photo" and c["to_intent"] == "find_document_whiteboard"
        for c in data["top_intent_corrections"]
    )
    assert "prompt_improvement_suggestions" in data
    assert len(data["prompt_improvement_suggestions"]) > 0


@pytest.mark.asyncio
async def test_admin_metrics_endpoint(client: AsyncClient, db_session, admin_headers, viewer_headers):
    # Add a job to test stats
    job = Job(id=_uuid(), type="ingest", status="done")
    db_session.add(job)
    await db_session.commit()

    # Admin access should succeed
    res = await client.get("/admin/metrics", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "ingestion" in data
    assert "ai_processing" in data
    assert "jobs" in data
    assert "system_health" in data
    assert data["jobs"]["total_jobs"] >= 1

    # Viewer access should fail (403 Forbidden)
    res_forbidden = await client.get("/admin/metrics", headers=viewer_headers)
    assert res_forbidden.status_code == 403


@pytest.mark.asyncio
async def test_evaluation_rbac(client: AsyncClient, viewer_headers):
    # Viewer should be forbidden from evaluation endpoints
    res = await client.get("/evaluation/results", headers=viewer_headers)
    assert res.status_code == 403

    res2 = await client.get("/evaluation/benchmarks", headers=viewer_headers)
    assert res2.status_code == 403

    res3 = await client.get("/evaluation/feedback-loop", headers=viewer_headers)
    assert res3.status_code == 403


@pytest.mark.asyncio
async def test_seed_benchmarks_in_db(db_session):
    # Ensure seeding benchmarks populates records without raising errors
    source = Source(id=_uuid(), name="demo", connector_type="mock", is_active=True)
    db_session.add(source)
    await db_session.flush()

    conv = Conversation(
        id=_uuid(),
        source_id=source.id,
        external_id="post_seed_test_1",
        title="Can't find a photo of my dog from 2 years ago",
        text="I want to search for my dog Max when he was a puppy.",
        is_relevant=True,
        is_demo=True,
    )
    db_session.add(conv)
    await db_session.commit()

    await seed_evaluation_benchmarks()
