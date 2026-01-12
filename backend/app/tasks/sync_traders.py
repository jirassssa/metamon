"""Tasks for syncing trader data from Polymarket."""

import asyncio

from sqlalchemy import select
import structlog

from app.tasks.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.copy_config import CopyConfig
from app.services.trader_analytics import trader_analytics_service

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.sync_traders.sync_all_traders")
def sync_all_traders():
    """
    Sync all traders that are being copied.

    This task runs hourly to update trader profiles.
    """
    asyncio.run(_sync_all_traders())


async def _sync_all_traders():
    """Async implementation of sync_all_traders."""
    logger.info("Starting trader sync")

    async with AsyncSessionLocal() as db:
        # Get all unique trader addresses being copied
        result = await db.execute(
            select(CopyConfig.trader_address).distinct()
        )
        trader_addresses = [row[0] for row in result.all()]

        logger.info(f"Syncing {len(trader_addresses)} traders")

        for address in trader_addresses:
            try:
                await trader_analytics_service.sync_trader_profile(db, address)
                logger.info(f"Synced trader {address[:10]}...")
            except Exception as e:
                logger.error(f"Failed to sync trader {address}", error=str(e))

    logger.info("Trader sync complete")


@celery_app.task(name="app.tasks.sync_traders.sync_trader_profile")
def sync_trader_profile(wallet_address: str):
    """
    Sync a single trader's profile.

    This task can be triggered on-demand.
    """
    asyncio.run(_sync_trader_profile(wallet_address))


async def _sync_trader_profile(wallet_address: str):
    """Async implementation of sync_trader_profile."""
    async with AsyncSessionLocal() as db:
        await trader_analytics_service.sync_trader_profile(db, wallet_address)
