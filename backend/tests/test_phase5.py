from __future__ import annotations
import pytest
from datetime import datetime, timezone
from app.db.models import Conversation, Problem, Cluster, Evidence, AIAnalysis, TaxonomyProposal, User
from app.auth.security import hash_password


@pytest.mark.asyncio
async def test_overview_stats_endpoint(client, db_session, admin_headers):
    # Setup test conversations and problem
    c1 = Conversation(
        title="Can't find wedding photo in Google Photos",
        text="The search bar for my wedding in June doesn't work.",
        cleaned_text="The search bar for my wedding in June doesn't work.",
        is_relevant=True,
        is_demo=True,
    )
    p1 = Problem(
        title="Temporal and event retrieval failures",
        statement="Users cannot locate photos from past major life events without exact dates.",
        frequency=15,
        is_emerging=True,
        severity_score=0.85,
    )
    cl1 = Cluster(label="Wedding & Event Retrieval", member_count=5)

    db_session.add_all([c1, p1, cl1])
    await db_session.commit()
    await db_session.refresh(c1)

    a1 = AIAnalysis(
        conversation_id=c1.id,
        relevance=0.95,
        primary_intent="find_photo",
        memory_types=["temporal", "event"],
        failure_modes=["temporal_drift", "no_results"],
        confidence=0.9,
    )
    db_session.add(a1)
    await db_session.commit()

    resp = await client.get("/stats", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "kpis" in data
    assert data["kpis"]["total_conversations"] >= 1
    assert data["kpis"]["relevant_conversations"] >= 1
    assert data["kpis"]["total_problems"] >= 1
    assert data["kpis"]["emerging_problems"] >= 1
    assert data["kpis"]["total_clusters"] >= 1

    assert "memory_distribution" in data
    assert len(data["memory_distribution"]) >= 1

    assert "failure_distribution" in data
    assert len(data["failure_distribution"]) >= 1

    assert "source_breakdown" in data
    assert "recent_activity" in data


@pytest.mark.asyncio
async def test_conversations_semantic_search_endpoint(client, db_session, admin_headers):
    conv = Conversation(
        title="Search bar ignores pet name",
        text="When I search 'golden retriever on grass' Google Photos returns random dogs.",
        cleaned_text="When I search golden retriever on grass Google Photos returns random dogs.",
        is_relevant=True,
        is_demo=False,
    )
    db_session.add(conv)
    await db_session.commit()

    resp = await client.get("/conversations/search?q=golden+retriever", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["query"] == "golden retriever"
    assert data["total"] >= 1
    hit = data["data"][0]
    assert "similarity_score" in hit
    assert "highlighted_excerpt" in hit
    assert "retriever" in hit["highlighted_excerpt"].lower() or "golden" in hit["highlighted_excerpt"].lower()


@pytest.mark.asyncio
async def test_rag_research_assistant_endpoints(client, db_session, admin_headers):
    # Test starter questions
    starters_resp = await client.get("/research/starters", headers=admin_headers)
    assert starters_resp.status_code == 200
    assert len(starters_resp.json()["starters"]) >= 3

    # Add conversation evidence
    conv = Conversation(
        title="Lost vacation photos after iOS update",
        text="All photos from my vacation in Hawaii disappeared from the library after updating.",
        cleaned_text="All photos from my vacation in Hawaii disappeared from the library after updating.",
        is_relevant=True,
        is_demo=True,
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    analysis = AIAnalysis(
        conversation_id=conv.id,
        primary_intent="find_photo",
        memory_types=["spatial", "event"],
        failure_modes=["no_results", "temporal_drift"],
        confidence=0.88,
    )
    db_session.add(analysis)
    await db_session.commit()

    # Query RAG
    query_payload = {
        "query": "Why do users lose photos from Hawaii vacation?",
        "limit": 5,
    }
    resp = await client.post("/research/query", json=query_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "answer" in data
    assert len(data["answer"]) > 10
    assert "answer_type" in data
    assert "evidence" in data
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["citation_id"] == "E-1"


@pytest.mark.asyncio
async def test_human_review_workflow(client, db_session, admin_headers):
    # Create conversation with analysis
    conv = Conversation(
        title="Ambiguous photo search query",
        text="I am trying to find a screenshot of a receipt from last month.",
        cleaned_text="I am trying to find a screenshot of a receipt from last month.",
        is_relevant=True,
        is_demo=True,
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    analysis = AIAnalysis(
        conversation_id=conv.id,
        primary_intent="find_photo",
        memory_types=["temporal"],
        failure_modes=["keyword_mismatch"],
        confidence=0.65,
    )
    db_session.add(analysis)
    await db_session.commit()

    # 1. Fetch review queue
    q_resp = await client.get("/reviews/queue", headers=admin_headers)
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert queue["total"] >= 1
    item = next((i for i in queue["items"] if i["conversation_id"] == conv.id), None)
    assert item is not None

    # 2. Submit correction review
    review_payload = {
        "conversation_id": conv.id,
        "action": "correct",
        "intent": "find_screenshot",
        "memory_types": ["temporal", "visual"],
        "failure_modes": ["keyword_mismatch", "poor_ranking"],
        "notes": "Verified receipt was a screenshot, corrected primary intent.",
    }
    submit_resp = await client.post("/reviews", json=review_payload, headers=admin_headers)
    assert submit_resp.status_code == 200
    sub_data = submit_resp.json()
    assert sub_data["status"] == "success"

    # Verify updated in DB
    await db_session.refresh(analysis)
    assert analysis.primary_intent == "find_screenshot"
    assert "visual" in analysis.memory_types
    assert analysis.confidence == 1.0


@pytest.mark.asyncio
async def test_cluster_curation_and_taxonomy_actions(client, db_session, admin_headers):
    # 1. Cluster actions
    cl = Cluster(label="Old Cluster Name", member_count=3)
    db_session.add(cl)
    await db_session.commit()
    await db_session.refresh(cl)

    rename_resp = await client.post(
        f"/reviews/clusters/{cl.id}/action",
        json={"action": "rename", "new_name": "Curated Cluster Name"},
        headers=admin_headers,
    )
    assert rename_resp.status_code == 200
    assert rename_resp.json()["label"] == "Curated Cluster Name"

    # 2. Taxonomy proposal actions
    prop = TaxonomyProposal(
        category_name="Spatial Geo-Tag Drift",
        description="Failures when GPS coordinates drift across borders.",
    )
    db_session.add(prop)
    await db_session.commit()
    await db_session.refresh(prop)

    # List taxonomy review
    tax_resp = await client.get("/reviews/taxonomy", headers=admin_headers)
    assert tax_resp.status_code == 200
    assert len(tax_resp.json()["proposals"]) >= 1

    # Approve proposal
    appr_resp = await client.post(
        f"/reviews/taxonomy/proposals/{prop.id}/action",
        json={"action": "approve", "notes": "Approved for next sprint"},
        headers=admin_headers,
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["is_approved"] is True


@pytest.mark.asyncio
async def test_research_brief_generator_and_exports(client, db_session, admin_headers):
    # Add problem with evidence
    conv = Conversation(
        title="Family reunion photos missing",
        text="Can't find any photos from our huge family reunion at the lake.",
        cleaned_text="Can't find any photos from our huge family reunion at the lake.",
        is_relevant=True,
        is_demo=True,
    )
    prob = Problem(
        title="Family Gathering Memory Retrieval Failure",
        statement="Users fail to rediscover multi-person family events without tagged faces.",
        frequency=28,
        severity_score=0.9,
    )
    db_session.add_all([conv, prob])
    await db_session.commit()
    await db_session.refresh(conv)
    await db_session.refresh(prob)

    ev = Evidence(
        problem_id=prob.id,
        conversation_id=conv.id,
        excerpt="Can't find any photos from our huge family reunion at the lake.",
        ai_interpretation="Demonstrates face clustering and social memory breakdown.",
    )
    db_session.add(ev)
    await db_session.commit()

    # 1. Generate Brief
    brief_resp = await client.post(
        "/reports/brief",
        json={"problem_ids": [prob.id], "time_period": "30d"},
        headers=admin_headers,
    )
    assert brief_resp.status_code == 200
    brief = brief_resp.json()

    assert "id" in brief
    assert "title" in brief
    assert "executive_summary" in brief
    assert "markdown" in brief
    assert "key_problems" in brief
    assert "representative_quotes" in brief
    assert "opportunity_spaces" in brief

    report_id = brief["id"]

    # 2. List reports
    list_resp = await client.get("/reports", headers=admin_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 3. Export as Markdown
    md_resp = await client.get(f"/reports/{report_id}/export?format=markdown", headers=admin_headers)
    assert md_resp.status_code == 200
    assert "text/markdown" in md_resp.headers["content-type"]
    assert "# " in md_resp.text

    # 4. Export as JSON
    json_resp = await client.get(f"/reports/{report_id}/export?format=json", headers=admin_headers)
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]

    # 5. Export as CSV
    csv_resp = await client.get(f"/reports/{report_id}/export?format=csv", headers=admin_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "Executive Summary" in csv_resp.text
