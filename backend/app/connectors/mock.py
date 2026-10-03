from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.connectors.base import BaseConnector, NormalizedRecord

_DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..",
    "data", "demo_dataset.json",
)


class MockConnector(BaseConnector):
    source_name = "demo"
    rate_limit_per_minute = 1000

    def fetch(self, query="", since=None, limit=500):
        dataset_path = os.path.normpath(_DATASET_PATH)
        with open(dataset_path, encoding="utf-8") as f:
            dataset = json.load(f)
        records = dataset["records"]
        if query:
            q = query.lower()
            records = [r for r in records if q in (r.get("title") or "").lower() or q in (r.get("text") or "").lower()]
        if since:
            filtered = []
            for r in records:
                ts = r.get("timestamp")
                if ts:
                    try:
                        rdt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if rdt >= since:
                            filtered.append(r)
                    except ValueError:
                        filtered.append(r)
                else:
                    filtered.append(r)
            records = filtered
        return records[:limit]

    def normalize(self, raw):
        ts_str = raw.get("timestamp")
        ts = None
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError:
                pass
        return NormalizedRecord(
            source_name=raw.get("source", "demo"),
            external_id=raw["id"],
            url=raw.get("url"),
            author_hash=raw.get("author_hash"),
            title=raw.get("title") or None,
            text=raw["text"],
            timestamp=ts,
            engagement=raw.get("engagement", {}),
            metadata={**raw.get("metadata", {}), "demo_id": raw["id"]},
            is_demo=True,
        )
