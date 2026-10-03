from __future__ import annotations
from typing import Dict, Type
from app.connectors.base import BaseConnector
from app.connectors.mock import MockConnector
from app.connectors.reddit import RedditConnector
from app.connectors.google_play import GooglePlayConnector
from app.connectors.app_store import AppStoreConnector
from app.connectors.youtube import YouTubeConnector

CONNECTOR_REGISTRY: Dict[str, Type[BaseConnector]] = {
    "demo": MockConnector,
    "reddit": RedditConnector,
    "google_play": GooglePlayConnector,
    "app_store": AppStoreConnector,
    "youtube": YouTubeConnector,
}

SOURCE_METADATA = {
    "demo": {"display_name": "Demo Dataset", "connector_type": "mock", "is_active": True},
    "reddit": {"display_name": "Reddit (via Apify)", "connector_type": "reddit", "is_active": True},
    "google_play": {"display_name": "Google Play Store", "connector_type": "google_play", "is_active": True},
    "app_store": {"display_name": "Apple App Store", "connector_type": "app_store", "is_active": True},
    "youtube": {"display_name": "YouTube (Data API v3)", "connector_type": "youtube", "is_active": True},
    "google_community": {"display_name": "Google Support Community", "connector_type": "forum", "is_active": True},
}
