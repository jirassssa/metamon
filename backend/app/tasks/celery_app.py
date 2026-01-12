"""Celery application configuration."""

from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "shadow_copy_trader",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.sync_traders",
        "app.tasks.execute_copies",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "sync-all-traders-hourly": {
        "task": "app.tasks.sync_traders.sync_all_traders",
        "schedule": 3600.0,  # Every hour
    },
    "check-for-new-trades": {
        "task": "app.tasks.execute_copies.check_for_new_trades",
        "schedule": 30.0,  # Every 30 seconds
    },
    "monitor-stop-losses": {
        "task": "app.tasks.execute_copies.monitor_stop_losses",
        "schedule": 10.0,  # Every 10 seconds
    },
}
