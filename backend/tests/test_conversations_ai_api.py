from __future__ import annotations
import pytest
from app.pipeline.orchestrator import run_full_pipeline


@pytest.mark.asyncio
async def test_conversations_api_with_ai_filters_and_pipeline(client, researcher_headers, test_db_session):
    # 1. Run pipeline to populate and analyze demo conversations
    engine = test_db_session.bind
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    await run_full_pipeline(source="demo", limit=15, run_embeddings=True, session_factory=factory)

    # 2. Query GET /conversations to verify AI annotations are present
    resp = await client.get("/conversations?limit=20", headers=researcher_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    records_with_analysis = [r for r in data["data"] if r.get("analysis") is not None]
    assert len(records_with_analysis) >= 1

    sample_rec = records_with_analysis[0]
    analysis = sample_rec["analysis"]
    assert "primary_intent" in analysis
    assert "confidence" in analysis
    assert "prompt_version" in analysis
    assert "model_provider" in analysis
    assert sample_rec["has_embedding"] is True

    # 3. Filter by intent
    intent_val = analysis["primary_intent"]
    intent_resp = await client.get(f"/conversations?intent={intent_val}", headers=researcher_headers)
    assert intent_resp.status_code == 200
    intent_data = intent_resp.json()
    assert intent_data["total"] >= 1
    for r in intent_data["data"]:
        assert r["analysis"]["primary_intent"] == intent_val

    # 4. Filter by confidence_min
    conf_resp = await client.get("/conversations?confidence_min=0.5", headers=researcher_headers)
    assert conf_resp.status_code == 200
    assert conf_resp.json()["total"] >= 1

    # 5. Filter by is_relevant
    rel_resp = await client.get("/conversations?is_relevant=true", headers=researcher_headers)
    assert rel_resp.status_code == 200
    assert rel_resp.json()["total"] >= 1

    # 6. Test GET /conversations/{id} detail endpoint
    conv_id = sample_rec["id"]
    detail_resp = await client.get(f"/conversations/{conv_id}", headers=researcher_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == conv_id
    assert detail["analysis"] is not None
    assert detail["analysis"]["conversation_id"] == conv_id
    assert detail["analysis"]["relevance"] is not None
    assert detail["analysis"]["reasoning_summary"] is not None

    # 7. Test POST /pipeline/run endpoint
    pipe_res = await client.post(
        "/pipeline/run",
        json={"source": "demo", "limit": 10},
        headers=researcher_headers,
    )
    assert pipe_res.status_code == 200
    pipe_body = pipe_res.json()
    assert "job_id" in pipe_body
    assert pipe_body["status"] == "queued"
