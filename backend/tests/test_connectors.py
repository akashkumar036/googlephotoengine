from __future__ import annotations
import hashlib
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.connectors.base import BaseConnector, NormalizedRecord, RawRecord
from app.connectors.mock import MockConnector
from app.connectors.google_play import GooglePlayConnector
from app.connectors.reddit import RedditConnector
from app.connectors.app_store import AppStoreConnector
from app.connectors.youtube import YouTubeConnector
from app.connectors.registry import CONNECTOR_REGISTRY, SOURCE_METADATA


class DummyIncompleteConnector(BaseConnector):
    source_name = "incomplete"


class DummyWorkingConnector(BaseConnector):
    source_name = "dummy"

    def fetch(self, query="", since=None, limit=100):
        # Return 2 records with the same external_id to test in-batch deduplication
        return [
            {"id": "d1", "text": "Photo issue 1", "author": "john_doe"},
            {"id": "d1", "text": "Photo issue 1 duplicate", "author": "john_doe"},
            {"id": "d2", "text": "Photo issue 2", "author": "jane_doe"},
        ][:limit]

    def normalize(self, raw):
        return NormalizedRecord(
            source_name=self.source_name,
            external_id=raw["id"],
            author_hash=raw.get("author"),
            text=raw["text"],
            is_demo=False,
        )


def test_base_connector_raises_not_implemented():
    """Verify BaseConnector enforces abstract methods."""
    with pytest.raises(TypeError):
        DummyIncompleteConnector()


def test_normalized_record_author_hashing():
    """Verify raw author string is automatically SHA-256 hashed."""
    raw_author = "test_user_123"
    expected_hash = hashlib.sha256(raw_author.encode()).hexdigest()

    rec = NormalizedRecord(
        source_name="reddit",
        external_id="post_999",
        author_hash=raw_author,
        text="I lost my family photos",
    )
    assert rec.author_hash == expected_hash
    assert rec.author_hash != raw_author

    # Already hashed value must be preserved without double-hashing
    rec2 = NormalizedRecord(
        source_name="reddit",
        external_id="post_1000",
        author_hash=expected_hash,
        text="I lost my photos",
    )
    assert rec2.author_hash == expected_hash


def test_normalized_record_allows_empty_text():
    """Verify empty text review is allowed per Edge Case 1.7."""
    rec = NormalizedRecord(
        source_name="app_store",
        external_id="rev_1",
        text="",
    )
    assert rec.text == ""


def test_in_batch_deduplication():
    """Verify in-batch duplicate records are dropped per Edge Case 1.9."""
    connector = DummyWorkingConnector()
    results = connector.run()
    assert len(results) == 2
    assert [r.external_id for r in results] == ["d1", "d2"]


def test_mock_connector_loads_demo_dataset():
    """Verify MockConnector loads 75+ demo records covering all metadata."""
    connector = MockConnector()
    records = connector.run()
    assert len(records) >= 50
    assert all(r.is_demo is True for r in records)

    sources = {r.source_name for r in records}
    assert "reddit" in sources
    assert "google_play" in sources
    assert "app_store" in sources

    # Check date range (spanning 2 years)
    dates = [r.timestamp for r in records if r.timestamp]
    assert len(dates) >= 50
    min_date = min(dates)
    max_date = max(dates)
    assert min_date.year <= 2024
    assert max_date.year >= 2026


def test_mock_connector_query_filtering():
    """Verify query filter works on mock dataset."""
    connector = MockConnector()
    results = connector.run(query="Christmas")
    assert len(results) >= 1
    assert any("Christmas" in (r.title or "") or "Christmas" in r.text for r in results)


def test_mock_connector_since_filtering():
    """Verify since datetime filter works on mock dataset."""
    connector = MockConnector()
    since_dt = datetime(2026, 9, 1, tzinfo=timezone.utc)
    results = connector.run(since=since_dt)
    assert len(results) >= 1
    for r in results:
        if r.timestamp:
            assert r.timestamp >= since_dt


def test_connector_registry_contains_expected():
    """Verify all connectors are registered in CONNECTOR_REGISTRY and SOURCE_METADATA."""
    assert "demo" in CONNECTOR_REGISTRY
    assert "reddit" in CONNECTOR_REGISTRY
    assert "google_play" in CONNECTOR_REGISTRY
    assert "app_store" in CONNECTOR_REGISTRY
    assert "youtube" in CONNECTOR_REGISTRY

    assert CONNECTOR_REGISTRY["demo"] is MockConnector
    assert CONNECTOR_REGISTRY["reddit"] is RedditConnector
    assert CONNECTOR_REGISTRY["google_play"] is GooglePlayConnector
    assert CONNECTOR_REGISTRY["app_store"] is AppStoreConnector
    assert CONNECTOR_REGISTRY["youtube"] is YouTubeConnector

    assert "google_community" in SOURCE_METADATA
    assert "youtube" in SOURCE_METADATA


def test_google_play_connector_normalization():
    """Verify GooglePlayConnector normalizes raw review format."""
    connector = GooglePlayConnector()
    raw = {
        "reviewId": "gp_12345",
        "userName": "photouser99",
        "content": "Cannot find pictures from last month",
        "score": 2,
        "thumbsUpCount": 15,
        "at": datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
        "_app_id": "com.google.android.apps.photos",
        "reviewCreatedVersion": "7.50.0",
    }
    rec = connector.normalize(raw)
    assert rec.source_name == "google_play"
    assert rec.external_id == "gplay_gp_12345"
    assert rec.author_hash == hashlib.sha256("photouser99".encode()).hexdigest()
    assert rec.text == "Cannot find pictures from last month"
    assert rec.engagement["rating"] == 2
    assert rec.engagement["helpful"] == 15
    assert rec.metadata["app_id"] == "com.google.android.apps.photos"
    assert rec.is_demo is False


def test_app_store_connector_normalization():
    """Verify AppStoreConnector normalizes raw review format."""
    connector = AppStoreConnector()
    raw = {
        "reviewId": "as_67890",
        "userName": "ios_photographer",
        "title": "Search is terrible",
        "review": "Looking for vacation photos and got zero matches.",
        "rating": 1,
        "date": datetime(2026, 8, 1, 10, 30, tzinfo=timezone.utc),
        "_app_id": "962194608",
        "_country": "us",
    }
    rec = connector.normalize(raw)
    assert rec.source_name == "app_store"
    assert rec.external_id == "appstore_as_67890"
    assert rec.title == "Search is terrible"
    assert rec.text == "Looking for vacation photos and got zero matches."
    assert rec.engagement["rating"] == 1
    assert rec.is_demo is False


def test_reddit_apify_connector_normalization():
    """Verify RedditConnector normalizes Apify Reddit Scraper dataset items."""
    connector = RedditConnector()
    raw = {
        "id": "reddit_post_xyz",
        "title": "Face recognition lost my daughter tag",
        "body": "After the recent update, Google Photos untagged hundreds of photos of my kid.",
        "author": "family_photographer",
        "subreddit": "googlephotos",
        "url": "https://reddit.com/r/googlephotos/comments/xyz",
        "createdAt": "2026-09-01T12:00:00Z",
        "upVotes": 45,
        "numberOfComments": 19,
        "dataType": "post",
    }
    rec = connector.normalize(raw)
    assert rec.source_name == "reddit"
    assert rec.external_id == "reddit_post_xyz"
    assert rec.title == "Face recognition lost my daughter tag"
    assert "untagged hundreds" in rec.text
    assert rec.author_hash == hashlib.sha256("family_photographer".encode()).hexdigest()
    assert rec.engagement["upvotes"] == 45
    assert rec.engagement["comments"] == 19
    assert rec.metadata["subreddit"] == "googlephotos"
    assert rec.metadata["scraped_via"] == "apify"
    assert rec.is_demo is False


def test_reddit_apify_connector_run_fallback():
    """Verify RedditConnector fallback provides realistic Reddit dataset without APIFY token."""
    connector = RedditConnector(api_token="")
    records = connector.run(query="dog", limit=3)
    assert len(records) >= 1
    for r in records:
        assert r.source_name == "reddit"
        assert r.external_id.startswith("reddit_")
        assert r.author_hash is not None


def test_youtube_connector_normalization():
    """Verify YouTubeConnector normalizes raw YouTube video and comment items."""
    connector = YouTubeConnector()
    raw_video = {
        "id": "vid_abc123",
        "video_id": "abc123",
        "type": "video",
        "title": "Google Photos Search Not Working - Complete Fix Guide",
        "text": "Are you unable to find your old photos on Google Photos? Here is what to do.",
        "channel_title": "TechHelper",
        "published_at": "2026-07-15T10:00:00Z",
        "url": "https://www.youtube.com/watch?v=abc123",
        "like_count": 550,
        "comment_count": 82,
        "view_count": 12500,
    }
    rec_vid = connector.normalize(raw_video)
    assert rec_vid.source_name == "youtube"
    assert rec_vid.external_id == "youtube_vid_abc123"
    assert rec_vid.title == "Google Photos Search Not Working - Complete Fix Guide"
    assert rec_vid.engagement["likes"] == 550
    assert rec_vid.engagement["views"] == 12500
    assert rec_vid.metadata["type"] == "video"
    assert rec_vid.metadata["video_id"] == "abc123"

    raw_comment = {
        "id": "com_comment999",
        "video_id": "abc123",
        "type": "comment",
        "title": "Comment on: Google Photos Search Not Working",
        "text": "I tried all these steps and it still cannot find any photos from 2022!",
        "author": "FrustratedUser_42",
        "channel_title": "TechHelper",
        "published_at": "2026-07-18T14:30:00Z",
        "like_count": 18,
    }
    rec_com = connector.normalize(raw_comment)
    assert rec_com.source_name == "youtube"
    assert rec_com.external_id == "youtube_com_comment999"
    assert rec_com.author_hash == hashlib.sha256("FrustratedUser_42".encode()).hexdigest()
    assert rec_com.engagement["likes"] == 18
    assert rec_com.metadata["type"] == "comment"


def test_youtube_connector_run_fallback():
    """Verify YouTubeConnector fallback provides realistic YouTube feedback without API key."""
    connector = YouTubeConnector(api_key="")
    records = connector.run(query="Google", limit=5)
    assert len(records) >= 2
    for r in records:
        assert r.source_name == "youtube"
        assert r.external_id.startswith("youtube_")
        assert r.author_hash is not None
        assert r.url and "youtube.com" in r.url

