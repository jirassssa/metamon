"""Tasks for executing copy trades and monitoring positions."""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, and_
import structlog

from app.tasks.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition
from app.services.copy_engine import copy_engine
from app.services.polymarket import polymarket_service

logger = structlog.get_logger()

# Track last sync time per trader
_last_sync_times: dict[str, datetime] = {}


@celery_app.task(name="app.tasks.execute_copies.check_for_new_trades")
def check_for_new_trades():
    """
    Check for new trades from followed traders and execute copies.

    This task runs every 30 seconds to detect new trades.
    """
    asyncio.run(_check_for_new_trades())


async def _check_for_new_trades():
    """Async implementation of check_for_new_trades."""
    global _last_sync_times

    async with AsyncSessionLocal() as db:
        # Get all unique active trader addresses
        result = await db.execute(
            select(CopyConfig.trader_address)
            .where(CopyConfig.is_active == True)
            .distinct()
        )
        trader_addresses = [row[0] for row in result.all()]

        for address in trader_addresses:
            try:
                # Get last sync time
                last_sync = _last_sync_times.get(address, datetime.min.replace(tzinfo=timezone.utc))

                # Fetch recent trades from Polymarket
                recent_trades = await polymarket_service.get_trader_history(
                    wallet_address=address,
                    limit=20
                )

                # Filter for new trades since last sync
                new_trades = [
                    t for t in recent_trades
                    if _parse_trade_time(t) > last_sync
                ]

                if new_trades:
                    logger.info(
                        f"Found {len(new_trades)} new trades from {address[:10]}..."
                    )

                    for trade in new_trades:
                        # Process each new trade
                        if _is_open_trade(trade):
                            await copy_engine.process_new_trade(db, address, trade)

                # Update last sync time
                _last_sync_times[address] = datetime.now(timezone.utc)

            except Exception as e:
                logger.error(
                    f"Error checking trades for {address}",
                    error=str(e)
                )


def _parse_trade_time(trade: dict) -> datetime:
    """Parse trade timestamp."""
    timestamp = trade.get("timestamp", 0)
    if isinstance(timestamp, str):
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def _is_open_trade(trade: dict) -> bool:
    """Check if trade is an opening trade (not a close)."""
    # This would depend on Polymarket's trade data structure
    # For now, assume all trades are potential copy candidates
    return True


@celery_app.task(name="app.tasks.execute_copies.monitor_stop_losses")
def monitor_stop_losses():
    """
    Monitor all open positions for stop loss triggers.

    This task runs every 10 seconds.
    """
    asyncio.run(_monitor_stop_losses())


async def _monitor_stop_losses():
    """Async implementation of monitor_stop_losses."""
    async with AsyncSessionLocal() as db:
        # Get all open positions with stop loss
        result = await db.execute(
            select(CopiedPosition)
            .where(
                and_(
                    CopiedPosition.status == "open",
                    CopiedPosition.stop_loss_price.isnot(None)
                )
            )
        )
        positions = result.scalars().all()

        if not positions:
            return

        # Update prices and check stop losses
        for position in positions:
            try:
                # Get current price from Polymarket
                # In production, this would use the actual token ID
                current_price = await polymarket_service.get_price(
                    position.market_id
                )

                if current_price is not None:
                    position.current_price = current_price

                    # Calculate P/L
                    if position.side == "YES":
                        pnl = (current_price - position.entry_price) * position.size
                    else:
                        pnl = (position.entry_price - current_price) * position.size

                    position.pnl = pnl
                    position.pnl_percentage = (
                        pnl / (position.entry_price * position.size) * 100
                    )

            except Exception as e:
                logger.error(
                    f"Error updating position {position.id}",
                    error=str(e)
                )

        await db.commit()

        # Check for stop loss triggers
        closed = await copy_engine.check_stop_losses(db)

        if closed:
            logger.info(f"Closed {len(closed)} positions due to stop loss")


@celery_app.task(name="app.tasks.execute_copies.update_position_prices")
def update_position_prices():
    """
    Update current prices for all open positions.

    This task can be triggered on-demand or scheduled.
    """
    asyncio.run(_update_position_prices())


async def _update_position_prices():
    """Async implementation of update_position_prices."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CopiedPosition).where(CopiedPosition.status == "open")
        )
        positions = result.scalars().all()

        for position in positions:
            try:
                current_price = await polymarket_service.get_price(
                    position.market_id
                )

                if current_price is not None:
                    position.current_price = current_price

                    # Calculate P/L
                    if position.side == "YES":
                        pnl = (current_price - position.entry_price) * position.size
                    else:
                        pnl = (position.entry_price - current_price) * position.size

                    position.pnl = pnl
                    position.pnl_percentage = (
                        pnl / (position.entry_price * position.size) * 100
                    )

            except Exception as e:
                logger.error(
                    f"Error updating price for position {position.id}",
                    error=str(e)
                )

        await db.commit()
        logger.info(f"Updated prices for {len(positions)} positions")
