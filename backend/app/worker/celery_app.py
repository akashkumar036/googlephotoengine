from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "photo_discovery",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,              # ack only after completion (crash-safe)
    task_reject_on_worker_lost=True,  # requeue if worker dies
    worker_prefetch_multiplier=1,     # one task at a time per worker slot
    task_track_started=True,
    result_expires=86400,             # keep results for 24h
)
