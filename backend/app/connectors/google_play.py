from __future__ import annotations
import hashlib, time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import structlog
from app.connectors.base import BaseConnector, NormalizedRecord
log = structlog.get_logger()
try:
    from google_play_scraper import reviews, Sort
    _GPS_AVAILABLE = True
except ImportError:
    _GPS_AVAILABLE = False
_TARGET_APPS = ["com.google.android.apps.photos"]

class GooglePlayConnector(BaseConnector):
    source_name = "google_play"
    rate_limit_per_minute = 30

    def fetch(self, query="", since=None, limit=100):
        if not _GPS_AVAILABLE:
            raise RuntimeError("google-play-scraper not installed")
        results = []
        per_app = max(10, limit // len(_TARGET_APPS))
        for app_id in _TARGET_APPS:
            if len(results) >= limit: break
            for attempt in range(3):
                try:
                    raw_reviews, _ = reviews(app_id, lang="en", country="us", sort=Sort.NEWEST, count=per_app)
                    for rev in raw_reviews:
                        rev_ts = rev.get("at")
                        if since and rev_ts:
                            if rev_ts.tzinfo is None:
                                rev_ts = rev_ts.replace(tzinfo=timezone.utc)
                            if rev_ts < since: continue
                        results.append({**rev, "_app_id": app_id})
                    break
                except Exception as e:
                    log.warning("gplay_error", app=app_id, error=str(e))
                    time.sleep(2 ** (attempt + 1))
            time.sleep(60.0 / self.rate_limit_per_minute)
        return results[:limit]

    def normalize(self, raw):
        a = raw.get("userName", "")
        ts = raw.get("at")
        if ts and hasattr(ts, "tzinfo") and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return NormalizedRecord(
            source_name="google_play",
            external_id="gplay_" + raw["reviewId"],
            url=None,
            author_hash=hashlib.sha256(a.encode()).hexdigest() if a else None,
            title=None,
            text=raw.get("content", ""),
            timestamp=ts,
            engagement={"rating": raw.get("score", 0), "helpful": raw.get("thumbsUpCount", 0)},
            metadata={"app_id": raw.get("_app_id"), "app_version": raw.get("reviewCreatedVersion")},
            is_demo=False,
        )
