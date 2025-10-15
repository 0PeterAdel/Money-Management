"""
Celery configuration for async task processing
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "notification_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.email_worker", "app.workers.sms_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
