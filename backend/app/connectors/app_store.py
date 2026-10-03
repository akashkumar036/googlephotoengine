from __future__ import annotations
import hashlib, time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import structlog
from app.connectors.base import BaseConnector, NormalizedRecord
log = structlog.get_logger()
try:
    from app_store_scraper import AppStore
    _ASS_AVAILABLE = True
except ImportError:
    _ASS_AVAILABLE = False
_TARGET_APPS = [{"app_name": "google-photos", "app_id": 962194608, "country": "us"}]

class AppStoreConnector(BaseConnector):
    source_name = "app_store"
    rate_limit_per_minute = 20

    def fetch(self, query="", since=None, limit=100):
        if not _ASS_AVAILABLE:
            raise RuntimeError("app-store-scraper not installed")
        results = []
        per_app = max(10, limit // len(_TARGET_APPS))
        for cfg in _TARGET_APPS:
            if len(results) >= limit: break
            try:
                app = AppStore(country=cfg["country"], app_name=cfg["app_name"], app_id=str(cfg["app_id"]))
                app.review(how_many=per_app)
                for rev in (app.reviews or []):
                    ts = rev.get("date")
                    if since and ts:
                        if hasattr(ts, "tzinfo") and ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        if ts < since: continue
                    results.append({**rev, "_app_id": str(cfg["app_id"]), "_country": cfg["country"]})
                time.sleep(60.0 / self.rate_limit_per_minute)
            except Exception as e:
                log.warning("appstore_error", app=cfg["app_name"], error=str(e))
        return results[:limit]

    def normalize(self, raw):
        a = raw.get("userName", "") or raw.get("author", "")
        ts = raw.get("date")
        if ts and hasattr(ts, "tzinfo") and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        text = raw.get("review", "") or raw.get("body", "") or ""
        return NormalizedRecord(
            source_name="app_store",
            external_id="appstore_" + str(raw.get("reviewId", id(raw))),
            url=None,
            author_hash=hashlib.sha256(a.encode()).hexdigest() if a else None,
            title=raw.get("title") or None,
            text=text,
            timestamp=ts,
            engagement={"rating": raw.get("rating", 0)},
            metadata={"app_id": raw.get("_app_id"), "country": raw.get("_country")},
            is_demo=False,
        )
