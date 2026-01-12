"""Celery background tasks."""

from app.tasks.celery_app import celery_app
from app.tasks.sync_traders import sync_all_traders, sync_trader_profile
from app.tasks.execute_copies import check_for_new_trades, monitor_stop_losses

__all__ = [
    "celery_app",
    "sync_all_traders",
    "sync_trader_profile",
    "check_for_new_trades",
    "monitor_stop_losses",
]
