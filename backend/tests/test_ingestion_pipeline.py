from __future__ import annotations
import pytest
from sqlalchemy import select, func
from app.db.models import Conversation, Job, Source, _uuid
from app.worker.tasks import run_ingest_pipeline


@pytest.mark.asyncio
async def test_demo_ingestion_end_to_end(test_db_session):
    """Verify demo dataset ingests 50+ records and updates job status."""
    job_id = _uuid()
    job = Job(id=job_id, type="ingest", status="queued", payload={"source": "demo"})
    test_db_session.add(job)
    await test_db_session.commit()

    # Pass the session_factory using lambda or current engine
    engine = test_db_session.bind
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    result = await run_ingest_pipeline(
        source="demo",
        job_id=job_id,
        session_factory=factory,
    )
    assert result["stored"] >= 50
    assert result["errors"] == 0

    # Verify records in database
    count_res = await test_db_session.execute(select(func.count(Conversation.id)))
    count = count_res.scalar()
    assert count == result["stored"]

    # Verify job status in database
    await test_db_session.refresh(job)
    assert job.status == "done"
    assert job.progress == 1.0
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_re_ingestion_skips_duplicates(test_db_session):
    """Verify re-running ingestion does not re-insert existing records."""
    engine = test_db_session.bind
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    res1 = await run_ingest_pipeline(source="demo", session_factory=factory)
    assert res1["stored"] >= 50

    # Second run should skip all previously stored records
    res2 = await run_ingest_pipeline(source="demo", session_factory=factory)
    assert res2["stored"] == 0
    assert res2["skipped"] == res1["stored"]


@pytest.mark.asyncio
async def test_conversations_api(client, researcher_headers, test_db_session):
    """Test conversations API: pagination, source filter, q filter, and detail view."""
    engine = test_db_session.bind
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    await run_ingest_pipeline(source="demo", session_factory=factory)

    # 1. List all conversations (viewer / researcher auth)
    resp = await client.get("/conversations", headers=researcher_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 50
    assert len(data["data"]) == min(20, data["total"])

    first_conv = data["data"][0]
    assert "source" in first_conv
    assert "author_hash" in first_conv
    assert "cleaned_text" in first_conv
    assert first_conv["is_demo"] is True

    # 2. Filter by source (e.g. reddit)
    reddit_resp = await client.get("/conversations?source=reddit", headers=researcher_headers)
    assert reddit_resp.status_code == 200
    reddit_data = reddit_resp.json()
    assert reddit_data["total"] >= 1
    assert all(r["source"] == "reddit" for r in reddit_data["data"])

    # 3. Filter by keyword search (q)
    q_resp = await client.get("/conversations?q=Christmas", headers=researcher_headers)
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["total"] >= 1

    # 4. Filter by date range (from_date / to_date)
    date_resp = await client.get("/conversations?from_date=2023-01-01T00:00:00Z&to_date=2026-12-31T23:59:59Z", headers=researcher_headers)
    assert date_resp.status_code == 200
    assert date_resp.json()["total"] >= 1

    # 4. Detail view
    conv_id = first_conv["id"]
    detail_resp = await client.get(f"/conversations/{conv_id}", headers=researcher_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == conv_id


@pytest.mark.asyncio
async def test_jobs_api_and_trigger_ingest(client, researcher_headers):
    """Test triggering ingestion via POST /ingest and tracking via GET /jobs."""
    # 1. Trigger ingestion
    resp = await client.post(
        "/ingest",
        json={"source": "demo"},
        headers=researcher_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "job_id" in body
    assert body["status"] == "queued"
    job_id = body["job_id"]

    # 2. Query specific job
    job_resp = await client.get(f"/jobs/{job_id}", headers=researcher_headers)
    assert job_resp.status_code == 200
    assert job_resp.json()["id"] == job_id

    # 3. List jobs
    jobs_resp = await client.get("/jobs", headers=researcher_headers)
    assert jobs_resp.status_code == 200
    assert jobs_resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_trigger_ingest_unknown_source(client, researcher_headers):
    """Verify POST /ingest with unknown source returns 400."""
    resp = await client.post(
        "/ingest",
        json={"source": "unknown_platform"},
        headers=researcher_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_youtube_and_reddit_ingestion_end_to_end(test_db_session, client, researcher_headers):
    """Verify youtube and reddit connectors run through ingest pipeline and API."""
    engine = test_db_session.bind
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # 1. Test YouTube ingestion pipeline
    yt_res = await run_ingest_pipeline(source="youtube", limit=5, session_factory=factory)
    assert yt_res["stored"] >= 2
    assert yt_res["errors"] == 0

    # 2. Test Reddit (Apify) ingestion pipeline
    reddit_res = await run_ingest_pipeline(source="reddit", limit=5, session_factory=factory)
    assert reddit_res["stored"] >= 2
    assert reddit_res["errors"] == 0

    # 3. Test API trigger for YouTube and Reddit
    yt_api_resp = await client.post(
        "/ingest",
        json={"source": "youtube", "limit": 10},
        headers=researcher_headers,
    )
    assert yt_api_resp.status_code == 200
    assert "job_id" in yt_api_resp.json()

    reddit_api_resp = await client.post(
        "/ingest",
        json={"source": "reddit", "limit": 10},
        headers=researcher_headers,
    )
    assert reddit_api_resp.status_code == 200
    assert "job_id" in reddit_api_resp.json()

