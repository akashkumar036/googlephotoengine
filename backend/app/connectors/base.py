"""
Base connector interface and data models for the ingestion layer.

Every source connector must subclass BaseConnector and implement:
  - fetch(query, since, limit) -> List[dict]   raw source records
  - normalize(raw) -> NormalizedRecord          mapped to canonical schema

The run() method composes fetch + normalize and is called by the Celery task.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# -- Canonical schema ----------------------------------------------------------

class NormalizedRecord(BaseModel):
    """
    Canonical representation of a single conversation / user review / post.
    All connectors must return records in this format.
    Fields map 1-to-1 with the conversations table columns.
    """

    # Identity
    source_name: str = Field(..., description="Connector source key, e.g. 'reddit'")
    external_id: str = Field(..., description="Unique ID within source, e.g. Reddit post ID")
    url: Optional[str] = None

    # Author (stored hashed - raw value is never persisted)
    author_hash: Optional[str] = Field(
        None,
        description="SHA-256 of original author string; raw author must NOT be stored",
    )

    # Content
    title: Optional[str] = None
    text: str = Field(default="", description="Post / review text")
    timestamp: Optional[datetime] = None

    # Engagement signals (platform-specific, stored as JSONB)
    engagement: Dict[str, Any] = Field(default_factory=dict)

    # Source-specific metadata (stored as JSONB)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Demo flag
    is_demo: bool = False

    @field_validator("author_hash", mode="before")
    @classmethod
    def hash_author(cls, v: Optional[str]) -> Optional[str]:
        """
        Accept either a pre-hashed value (64-char hex) or a raw author string.
        If the value looks like a raw author name, hash it transparently.
        This ensures PII is never stored.
        """
        if v is None:
            return None
        if len(v) == 64 and all(c in "0123456789abcdef" for c in v.lower()):
            return v  # already hashed
        return hashlib.sha256(v.encode()).hexdigest()


class RawRecord(BaseModel):
    """
    Minimal wrapper for a raw record fetched from a source.
    Used as the input type for normalize().
    Connectors may use their own richer raw types that inherit from this.
    """
    raw: Dict[str, Any] = Field(default_factory=dict)


# -- Base connector ------------------------------------------------------------

class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    Subclasses must define:
      - source_name: str            identifier matching CONNECTOR_REGISTRY key
      - rate_limit_per_minute: int  max requests per minute (default: 60)
      - fetch()                     fetch raw records from source
      - normalize()                 convert raw record to NormalizedRecord
    """

    source_name: str
    rate_limit_per_minute: int = 60

    @abstractmethod
    def fetch(
        self,
        query: str = "",
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw records from the source.

        Args:
            query: Search term or topic filter (may be ignored by some connectors).
            since: Only return records newer than this datetime.
            limit: Maximum number of records to return.

        Returns:
            List of raw dicts from the source API / file.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: Dict[str, Any]) -> NormalizedRecord:
        """
        Map a single raw record to NormalizedRecord.

        Args:
            raw: Raw dict as returned by fetch().

        Returns:
            NormalizedRecord instance.
        """
        raise NotImplementedError

    def run(
        self,
        query: str = "",
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NormalizedRecord]:
        """
        Convenience method: fetch + normalize in one call.
        Skips records that fail normalization and logs the error.
        Deduplicates within the current batch (Edge Case 1.9).
        """
        import structlog
        log = structlog.get_logger()

        raw_records = self.fetch(query=query, since=since, limit=limit)
        normalized: List[NormalizedRecord] = []
        seen_keys = set()

        for raw in raw_records:
            try:
                record = self.normalize(raw)
                dedup_key = (record.source_name, record.external_id)
                if dedup_key in seen_keys:
                    log.debug("in_batch_duplicate_dropped", key=dedup_key)
                    continue
                seen_keys.add(dedup_key)
                normalized.append(record)
            except Exception as exc:
                log.warning(
                    "connector_normalize_error",
                    source=self.source_name,
                    error=str(exc),
                    raw_keys=list(raw.keys()) if isinstance(raw, dict) else str(type(raw)),
                )

        return normalized
