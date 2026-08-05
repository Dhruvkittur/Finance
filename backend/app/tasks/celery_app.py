"""
FinPilot AI — Celery Application & Tasks
==========================================
Async background task processing for:
- Document processing pipeline
- Report generation
- Email delivery
- Scheduled analytics
"""

import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Celery App ────────────────────────────────────────────────────────────────

celery_app = Celery(
    "finpilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=settings.CELERY_TASK_TIMEOUT,
    task_time_limit=settings.CELERY_TASK_TIMEOUT + 60,
    task_max_retries=settings.CELERY_MAX_RETRIES,
    task_default_queue="default",
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "documents"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },
)
