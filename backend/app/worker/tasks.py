from __future__ import annotations

import structlog

from app.worker.celery_app import celery_app

log = structlog.get_logger()


# ── Smoke-test task ───────────────────────────────────────────────────────
@celery_app.task(name="worker.tasks.ping", bind=True)
def ping(self) -> str:
    """Smoke-test task — verifies worker is running and connected."""
    log.info("task_ping_received", task_id=self.request.id)
    return "pong"


# ── Phase 2 stubs — implemented in later phases ───────────────────────────
@celery_app.task(name="worker.tasks.ingest_source", bind=True)
def ingest_source(self, source: str, query: str = "", since: str | None = None, limit: int = 100):
    """Trigger data ingestion from a connector. Implemented in Phase 2."""
    log.info("task_ingest_source_stub", source=source)
    return {"status": "stub", "message": "Ingestion implemented in Phase 2"}


@celery_app.task(name="worker.tasks.analyze_batch", bind=True)
def analyze_batch(self, conversation_ids: list[str]):
    """Run AI analysis on a batch of conversations. Implemented in Phase 3."""
    log.info("task_analyze_batch_stub", count=len(conversation_ids))
    return {"status": "stub", "message": "Analysis implemented in Phase 3"}


@celery_app.task(name="worker.tasks.cluster_conversations", bind=True)
def cluster_conversations(self):
    """Run semantic clustering. Implemented in Phase 4."""
    log.info("task_cluster_stub")
    return {"status": "stub", "message": "Clustering implemented in Phase 4"}


@celery_app.task(name="worker.tasks.detect_trends", bind=True)
def detect_trends(self):
    """Run trend detection. Implemented in Phase 4."""
    log.info("task_trends_stub")
    return {"status": "stub", "message": "Trend detection implemented in Phase 4"}
