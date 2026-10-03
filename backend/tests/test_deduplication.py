from __future__ import annotations
import pytest
from app.connectors.base import NormalizedRecord
from app.db.models import Conversation, Source, _uuid
from app.pipeline.deduplication import (
    compute_source_hash,
    compute_content_hash,
    check_duplicate,
)
from app.pipeline.ingestion import deduplicate_and_store, get_or_create_source


def test_hash_computation_consistency():
    h1 = compute_source_hash("reddit", "abc123")
    h2 = compute_source_hash("reddit", "abc123")
    assert h1 == h2
    assert len(h1) == 64

    # Different sources with same ID produce different hashes (Edge Case 1.6)
    h_gplay = compute_source_hash("google_play", "abc123")
    assert h1 != h_gplay

    # Content hash normalizes spaces and casing
    c1 = compute_content_hash("Cannot   Find PHOTOS from 2022")
    c2 = compute_content_hash("cannot find photos from 2022")
    assert c1 == c2


@pytest.mark.asyncio
async def test_exact_duplicate_detection(test_db_session):
    source = await get_or_create_source(test_db_session, "reddit", "reddit")
    await test_db_session.commit()

    rec = NormalizedRecord(
        source_name="reddit",
        external_id="post_exact_1",
        text="Cannot find my Christmas photos from last year.",
    )

    conv_id1 = await deduplicate_and_store(test_db_session, rec, source)
    assert conv_id1 is not None
    await test_db_session.commit()

    # Re-ingesting the exact same record must return None and NOT insert
    conv_id2 = await deduplicate_and_store(test_db_session, rec, source)
    assert conv_id2 is None


@pytest.mark.asyncio
async def test_edited_post_handling(test_db_session):
    """Verify Edge Case 3.3: Edited post is updated in place, not duplicated."""
    source = await get_or_create_source(test_db_session, "reddit", "reddit")
    await test_db_session.commit()

    rec_orig = NormalizedRecord(
        source_name="reddit",
        external_id="post_edited_1",
        text="Cannot find photo.",
    )
    conv_id1 = await deduplicate_and_store(test_db_session, rec_orig, source)
    assert conv_id1 is not None
    await test_db_session.commit()

    # User edits their post to add more detail
    rec_edited = NormalizedRecord(
        source_name="reddit",
        external_id="post_edited_1",
        text="Cannot find photo from trip to Hawaii in August 2023 with my family.",
    )
    conv_id2 = await deduplicate_and_store(test_db_session, rec_edited, source)
    assert conv_id2 == conv_id1  # Same record ID updated

    # Check that text was updated and was_edited is true in metadata
    conv = await test_db_session.get(Conversation, conv_id1)
    assert conv.needs_reanalysis is True
    assert conv.metadata_["was_edited"] is True
    assert "Hawaii" in conv.text


@pytest.mark.asyncio
async def test_cross_post_detection(test_db_session):
    """Verify Edge Case 3.1: Identical text on different platforms marked cross_post."""
    reddit_src = await get_or_create_source(test_db_session, "reddit", "reddit")
    play_src = await get_or_create_source(test_db_session, "google_play", "google_play")
    await test_db_session.commit()

    shared_text = "Google Photos search for screenshot receipts fails completely since the last update."

    rec_reddit = NormalizedRecord(
        source_name="reddit",
        external_id="reddit_post_cross_1",
        text=shared_text,
    )
    id1 = await deduplicate_and_store(test_db_session, rec_reddit, reddit_src)
    assert id1 is not None
    await test_db_session.commit()

    conv1 = await test_db_session.get(Conversation, id1)
    assert conv1.dedup_status == "original"

    # User copy-pastes the same complaint to Play Store
    rec_play = NormalizedRecord(
        source_name="google_play",
        external_id="play_rev_cross_1",
        text=shared_text,
    )
    id2 = await deduplicate_and_store(test_db_session, rec_play, play_src)
    assert id2 is not None
    await test_db_session.commit()

    conv2 = await test_db_session.get(Conversation, id2)
    assert conv2.dedup_status == "cross_post"
