from __future__ import annotations
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from app.db.models import (
    Conversation,
    Source,
    AIAnalysis,
    Cluster,
    ClusterMembership,
    Problem,
    Evidence,
    Opportunity,
    Trend,
    TaxonomyProposal,
    _uuid,
)
from app.models.providers.mock import MockProvider
from app.pipeline.clustering import run_semantic_clustering
from app.pipeline.problem_discovery import run_problem_discovery
from app.pipeline.taxonomy import run_taxonomy_assignment, get_taxonomy_summary
from app.pipeline.trend_detection import run_trend_detection, get_trends_data
from app.pipeline.emerging_detection import run_emerging_detection, get_emerging_alerts
from app.pipeline.unknown_unknowns import run_unknown_unknowns_detection
from app.pipeline.orchestrator import run_full_pipeline


async def _seed_test_dataset(db_session):
    """Seed sources, conversations with embeddings, and AIAnalysis for testing."""
    sources = [
        Source(id="src-reddit", name="reddit", connector_type="reddit", is_active=True),
        Source(id="src-play", name="google_play", connector_type="google_play", is_active=True),
        Source(id="src-apple", name="app_store", connector_type="app_store", is_active=True),
    ]
    for s in sources:
        db_session.add(s)
    await db_session.commit()

    # Create mock embeddings with slight distinct directions for clustering
    # Cluster 1: Semantic search / Natural language query failures
    # Cluster 2: Duplicate detection / Library clutter
    # Cluster 3: Backup sync / Cloud storage missing photos
    import numpy as np

    conv_specs = [
        # Group 1: Search failure
        ("Cannot find dog photos from 2021", "reddit", 4, 4, [1.0, 0.1, 0.0, 0.0]),
        ("Search for 'beach sunset' returns zero results", "google_play", 5, 5, [0.95, 0.15, 0.0, 0.0]),
        ("Natural language photo query completely broken", "app_store", 4, 3, [0.98, 0.12, 0.0, 0.0]),
        ("Can't find receipts by searching text", "reddit", 3, 4, [0.92, 0.18, 0.0, 0.0]),
        ("Keywords search never returns matching photos", "google_play", 4, 4, [0.96, 0.14, 0.0, 0.0]),
        ("Search by face or person tag missing", "app_store", 5, 4, [0.94, 0.11, 0.0, 0.0]),
        # Group 2: Duplicates & Clutter
        ("Library full of duplicate screenshots and memes", "reddit", 4, 3, [0.0, 1.0, 0.1, 0.0]),
        ("Duplicates cleanup tool deletes the wrong photos", "google_play", 5, 5, [0.1, 0.95, 0.15, 0.0]),
        ("Thousands of repeated whatsapp photos clogging storage", "app_store", 3, 3, [0.05, 0.98, 0.12, 0.0]),
        ("Burst shots not grouped, gallery completely cluttered", "reddit", 4, 4, [0.12, 0.92, 0.18, 0.0]),
        ("App does not identify similar photos for deletion", "google_play", 3, 3, [0.08, 0.96, 0.14, 0.0]),
        ("Cluttered gallery with unorganized screenshots", "app_store", 4, 4, [0.11, 0.94, 0.11, 0.0]),
        # Group 3: Backup & Sync
        ("Photos from last week did not sync to cloud backup", "reddit", 5, 5, [0.0, 0.0, 1.0, 0.1]),
        ("Sync stuck at 99% and battery drains instantly", "google_play", 4, 4, [0.1, 0.05, 0.95, 0.15]),
        ("Lost old vacation photos during cloud restoration", "app_store", 5, 5, [0.0, 0.12, 0.98, 0.12]),
        ("Backup failed silently and lost recent trip album", "reddit", 5, 5, [0.15, 0.0, 0.92, 0.18]),
        ("Automatic background sync stopped working after update", "google_play", 4, 4, [0.1, 0.08, 0.96, 0.14]),
        ("Camera roll sync error 404 on restore", "app_store", 4, 5, [0.08, 0.11, 0.94, 0.11]),
    ]

    now = datetime.now(datetime.timezone.utc).replace(tzinfo=None) if hasattr(datetime, "timezone") else datetime.utcnow()
    conversations = []
    analyses = []

    for i, (title, src_name, frust, sev, base_vec) in enumerate(conv_specs):
        vec = [0.0] * 1536
        for vi, val in enumerate(base_vec):
            vec[vi] = float(val)

        created_at = now - timedelta(days=(i % 14))
        c = Conversation(
            id=f"conv-{i+1:03d}",
            source_id=f"src-{src_name.split('_')[0]}",
            title=title,
            text=f"User complaint: {title}. This is causing significant user friction.",
            cleaned_text=f"User complaint: {title}. This is causing significant user friction.",
            url=f"https://{src_name}.com/post/{i+1}",
            created_at=created_at,
            is_cleaned=True,
            is_relevant=True,
            embedding=vec,
            embedding_model="text-embedding-3-small",
        )
        conversations.append(c)

        a = AIAnalysis(
            id=f"analysis-{i+1:03d}",
            conversation_id=c.id,
            prompt_version="analysis-v1.0",
            model_provider="mock",
            primary_intent="find_photo",
            frustration_level=frust,
            severity=sev,
            confidence=0.88,
            memory_types=["temporal", "spatial"],
        )
        analyses.append(a)

    db_session.add_all(conversations)
    db_session.add_all(analyses)
    await db_session.commit()


@pytest.mark.asyncio
async def test_semantic_clustering_and_problem_discovery(db_session):
    """Test clustering execution, centroid generation, problem synthesis, and evidence links."""
    await _seed_test_dataset(db_session)
    provider = MockProvider()

    # 1. Run semantic clustering
    cluster_res = await run_semantic_clustering(db_session, provider=provider)
    assert cluster_res["clusters_created"] >= 2
    assert cluster_res["memberships_assigned"] >= 12

    # Verify clusters in DB
    clusters = (await db_session.execute(select(Cluster))).scalars().all()
    assert len(clusters) >= 2
    for cl in clusters:
        assert cl.label is not None
        assert cl.member_count > 0
        assert cl.centroid is not None
        assert len(cl.centroid) == 1536

    # Verify memberships
    memberships = (await db_session.execute(select(ClusterMembership))).scalars().all()
    assert len(memberships) >= 12

    # 2. Run problem discovery
    prob_res = await run_problem_discovery(db_session, provider=provider)
    assert prob_res["problems_created"] >= 2
    assert prob_res["evidence_linked"] >= 6
    assert prob_res["opportunities_created"] >= 2

    # Verify problems in DB
    problems = (await db_session.execute(select(Problem))).scalars().all()
    assert len(problems) >= 2
    for p in problems:
        assert p.title is not None
        assert p.statement is not None
        assert p.frequency >= 1
        assert p.source_count >= 1
        assert p.frustration_score is not None
        assert p.severity_score is not None
        assert p.cross_source_score is not None
        assert p.evidence_diversity_score is not None
        assert p.confidence is not None

    # Verify evidence links
    evidence_items = (await db_session.execute(select(Evidence))).scalars().all()
    assert len(evidence_items) >= 6
    for ev in evidence_items:
        assert ev.problem_id is not None
        assert ev.conversation_id is not None

    # Verify initial opportunities
    opps = (await db_session.execute(select(Opportunity))).scalars().all()
    assert len(opps) >= 2


@pytest.mark.asyncio
async def test_taxonomy_assignment_and_proposals(db_session, client, viewer_headers, researcher_headers):
    """Test taxonomy classification, proposal storage, and review workflow."""
    await _seed_test_dataset(db_session)
    provider = MockProvider()
    await run_semantic_clustering(db_session, provider=provider)
    await run_problem_discovery(db_session, provider=provider)

    # 1. Run taxonomy assignment
    tax_res = await run_taxonomy_assignment(db_session, provider=provider)
    assert tax_res["classified"] >= 2

    # Verify problems have taxonomy assigned
    problems = (await db_session.execute(select(Problem))).scalars().all()
    for p in problems:
        assert p.taxonomy_categories is not None
        assert len(p.taxonomy_categories) >= 1

    # 2. Verify taxonomy summary
    summary = await get_taxonomy_summary(db_session)
    assert "categories" in summary
    assert "proposals" in summary
    assert "total_problems" in summary
    assert summary["total_problems"] >= 2

    # 3. Test GET /taxonomy API
    resp = await client.get("/taxonomy", headers=viewer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert "proposals" in data

    # 4. Create a proposal directly and test review endpoint
    proposal = TaxonomyProposal(
        category_name="Visual Semantic Memory",
        description="Problems relating to semantic memory of images",
        evidence_count=5,
        proposed_by="ai_miner",
    )
    db_session.add(proposal)
    await db_session.commit()
    await db_session.refresh(proposal)

    # Review as viewer -> forbidden (requires researcher)
    resp = await client.post(
        f"/taxonomy/proposals/{proposal.id}/review",
        json={"action": "approve"},
        headers=viewer_headers,
    )
    assert resp.status_code == 403

    # Review as researcher -> approve
    resp = await client.post(
        f"/taxonomy/proposals/{proposal.id}/review",
        json={"action": "approve"},
        headers=researcher_headers,
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["is_approved"] is True
    assert res_data["is_rejected"] is False

    # Review as researcher -> reject
    resp = await client.post(
        f"/taxonomy/proposals/{proposal.id}/review",
        json={"action": "reject"},
        headers=researcher_headers,
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["is_approved"] is False
    assert res_data["is_rejected"] is True


@pytest.mark.asyncio
async def test_trend_and_emerging_detection(db_session, client, viewer_headers):
    """Test trend bucket calculations, growth rate, and emerging problem alerts."""
    await _seed_test_dataset(db_session)
    provider = MockProvider()
    await run_semantic_clustering(db_session, provider=provider)
    await run_problem_discovery(db_session, provider=provider)

    # 1. Run trend detection
    trend_res = await run_trend_detection(db_session)
    assert trend_res["trends_calculated"] >= 2

    # Verify trends in DB
    trends = (await db_session.execute(select(Trend))).scalars().all()
    assert len(trends) >= 2

    # 2. Test GET /trends endpoint
    resp = await client.get("/trends?period=30d&granularity=week", headers=viewer_headers)
    assert resp.status_code == 200
    trends_json = resp.json()
    assert "data" in trends_json
    trends_data = trends_json["data"]
    assert len(trends_data) >= 2
    first_trend = trends_data[0]
    assert "problem_id" in first_trend
    assert "data_points" in first_trend
    assert "growth_rate" in first_trend

    # 3. Mark one problem to meet emerging criteria
    prob = (await db_session.execute(select(Problem))).scalars().first()
    prob.growth_rate = 0.45
    prob.source_count = 3
    prob.frequency = 6
    await db_session.commit()

    emerging_res = await run_emerging_detection(db_session)
    assert emerging_res["emerging_flagged"] >= 1

    # Verify Problem.is_emerging flag
    await db_session.refresh(prob)
    assert prob.is_emerging is True
    assert prob.is_approved is False

    # 4. Test GET /trends/emerging endpoint
    resp = await client.get("/trends/emerging", headers=viewer_headers)
    assert resp.status_code == 200
    alerts_json = resp.json()
    assert "alerts" in alerts_json
    alerts = alerts_json["alerts"]
    assert len(alerts) >= 1
    alert = alerts[0]
    assert alert["problem_id"] == prob.id
    assert alert["growth_rate"] == 0.45
    assert len(alert["sources"]) >= 1


@pytest.mark.asyncio
async def test_unknown_unknowns_detection(db_session):
    """Test mining outlier conversations to surface novel taxonomy proposals."""
    # Seed an outlier conversation with unclustered status (no cluster membership)
    conv_outlier = Conversation(
        id="conv-outlier-01",
        title="Photos corrupted by cosmic ray bitflips on SD card",
        text="My photos got partially corrupted on my drone SD card with weird pixel artifacts and broken EXIF headers.",
        cleaned_text="My photos got partially corrupted on my drone SD card with weird pixel artifacts and broken EXIF headers.",
        is_relevant=True,
    )
    db_session.add(conv_outlier)
    await db_session.commit()

    provider = MockProvider()
    res = await run_unknown_unknowns_detection(db_session, provider=provider)
    assert res["outliers_found"] >= 1
    assert res["proposals_generated"] >= 1

    proposals = (await db_session.execute(select(TaxonomyProposal))).scalars().all()
    assert len(proposals) >= 1
    assert any("SD Card" in p.category_name or "Hardware" in p.category_name or "Corruption" in p.category_name for p in proposals)


@pytest.mark.asyncio
async def test_problem_and_cluster_api_endpoints(db_session, client, viewer_headers, researcher_headers):
    """Test full GET/PATCH problem, cluster, and evidence endpoints."""
    await _seed_test_dataset(db_session)
    provider = MockProvider()
    await run_semantic_clustering(db_session, provider=provider)
    await run_problem_discovery(db_session, provider=provider)
    await run_taxonomy_assignment(db_session, provider=provider)

    # 1. GET /problems (list & filter)
    resp = await client.get("/problems", headers=viewer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["data"]) >= 2
    problem_id = data["data"][0]["id"]

    # Test filtering by min_severity
    resp_filter = await client.get("/problems?min_severity=0.3", headers=viewer_headers)
    assert resp_filter.status_code == 200

    # 2. GET /problems/:id (detail)
    resp_detail = await client.get(f"/problems/{problem_id}", headers=viewer_headers)
    assert resp_detail.status_code == 200
    prob_detail = resp_detail.json()
    assert prob_detail["id"] == problem_id
    assert "evidence" in prob_detail
    assert "opportunities" in prob_detail
    assert "trends" in prob_detail

    # 3. PATCH /problems/:id (update status & validation)
    patch_payload = {
        "is_approved": True,
        "title": "Updated Problem Title",
        "taxonomy_categories": ["Search Failures", "UX Issues"],
    }
    resp_patch = await client.patch(
        f"/problems/{problem_id}",
        json=patch_payload,
        headers=researcher_headers,
    )
    assert resp_patch.status_code == 200
    updated_prob = resp_patch.json()
    assert updated_prob["is_approved"] is True
    assert updated_prob["title"] == "Updated Problem Title"
    assert "Search Failures" in updated_prob["taxonomy_categories"]

    # 4. GET /problems/:id/cross-platform
    resp_xp = await client.get(f"/problems/{problem_id}/cross-platform", headers=viewer_headers)
    assert resp_xp.status_code == 200
    xp_data = resp_xp.json()
    assert xp_data["problem_id"] == problem_id
    assert "platform_breakdown" in xp_data
    assert "is_isolated" in xp_data
    assert "is_widespread" in xp_data

    # 5. GET /clusters
    resp_clusters = await client.get("/clusters", headers=viewer_headers)
    assert resp_clusters.status_code == 200
    clusters_data = resp_clusters.json()
    assert len(clusters_data["data"]) >= 2
    cluster_id = clusters_data["data"][0]["id"]

    # 6. GET /clusters/:id
    resp_cl_detail = await client.get(f"/clusters/{cluster_id}", headers=viewer_headers)
    assert resp_cl_detail.status_code == 200
    cl_detail = resp_cl_detail.json()
    assert cl_detail["id"] == cluster_id
    assert "conversations" in cl_detail

    # 7. GET /evidence/:id
    ev_item = (await db_session.execute(select(Evidence))).scalars().first()
    assert ev_item is not None
    resp_ev = await client.get(f"/evidence/{ev_item.id}", headers=viewer_headers)
    assert resp_ev.status_code == 200
    ev_detail = resp_ev.json()
    assert ev_detail["id"] == ev_item.id
    assert "conversation" in ev_detail
    assert "problem" in ev_detail


@pytest.mark.asyncio
async def test_pipeline_cluster_and_trends_trigger(client, researcher_headers):
    """Test triggering clustering and trend detection via /pipeline endpoints."""
    # POST /pipeline/cluster
    resp = await client.post("/pipeline/cluster", headers=researcher_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"

    # POST /pipeline/trends
    resp = await client.post("/pipeline/trends", headers=researcher_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"
