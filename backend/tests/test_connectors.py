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

    assert CONNECTOR_REGISTRY["demo"] is MockConnector
    assert CONNECTOR_REGISTRY["reddit"] is RedditConnector
    assert CONNECTOR_REGISTRY["google_play"] is GooglePlayConnector
    assert CONNECTOR_REGISTRY["app_store"] is AppStoreConnector

    assert "google_community" in SOURCE_METADATA


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
