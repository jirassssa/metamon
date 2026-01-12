"""Trade watcher service for monitoring trader activity and triggering copy trades."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import structlog

from app.config import settings
from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition
from app.models.trader import TraderProfile
from app.models.notification import Notification
from app.services.polymarket import polymarket_service

logger = structlog.get_logger()


class PendingCopyTrade:
    """Represents a pending copy trade waiting for user execution."""

    def __init__(
        self,
        id: str,
        user_id: UUID,
        copy_config_id: UUID,
        trader_address: str,
        market_id: str,
        market_title: str,
        market_slug: str,
        event_slug: str,
        side: str,
        size: Decimal,
        price: Decimal,
        original_trade_id: str,
        timestamp: int,
    ):
        self.id = id
        self.user_id = user_id
        self.copy_config_id = copy_config_id
        self.trader_address = trader_address
        self.market_id = market_id
        self.market_title = market_title
        self.market_slug = market_slug
        self.event_slug = event_slug
        self.side = side
        self.size = size
        self.price = price
        self.original_trade_id = original_trade_id
        self.timestamp = timestamp
        self.created_at = datetime.now(timezone.utc)
        self.status = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "copy_config_id": str(self.copy_config_id),
            "trader_address": self.trader_address,
            "market_id": self.market_id,
            "market_title": self.market_title,
            "market_slug": self.market_slug,
            "event_slug": self.event_slug,
            "side": self.side,
            "size": str(self.size),
            "price": str(self.price),
            "original_trade_id": self.original_trade_id,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


class TradeWatcher:
    """
    Watches for new trades from copied traders and creates pending copy trades.

    This service:
    1. Polls Polymarket activity API for traders being copied
    2. Detects new trades since last check
    3. Creates pending copy trades for users to execute via their wallets
    4. Notifies connected clients via WebSocket
    """

    def __init__(self):
        # Track last seen trade per trader to avoid duplicates
        self.last_trade_timestamps: dict[str, int] = {}
        # Store pending copy trades by user_id
        self.pending_trades: dict[str, list[PendingCopyTrade]] = {}
        # WebSocket connections by user_id for notifications
        self.ws_connections: dict[str, list] = {}
        # Running flag
        self.is_running = False
        # Poll interval in seconds
        self.poll_interval = 15

    def add_ws_connection(self, user_id: str, websocket):
        """Add a WebSocket connection for a user."""
        if user_id not in self.ws_connections:
            self.ws_connections[user_id] = []
        self.ws_connections[user_id].append(websocket)
        logger.info("WebSocket connected", user_id=user_id)

    def remove_ws_connection(self, user_id: str, websocket):
        """Remove a WebSocket connection for a user."""
        if user_id in self.ws_connections:
            self.ws_connections[user_id] = [
                ws for ws in self.ws_connections[user_id] if ws != websocket
            ]
            if not self.ws_connections[user_id]:
                del self.ws_connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id)

    async def notify_user(self, user_id: str, message: dict[str, Any]):
        """Send a message to all WebSocket connections for a user."""
        if user_id in self.ws_connections:
            dead_connections = []
            for ws in self.ws_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning("Failed to send WS message", user_id=user_id, error=str(e))
                    dead_connections.append(ws)

            # Clean up dead connections
            for ws in dead_connections:
                self.ws_connections[user_id].remove(ws)

    def get_pending_trades(self, user_id: str) -> list[PendingCopyTrade]:
        """Get pending copy trades for a user."""
        return self.pending_trades.get(user_id, [])

    def mark_trade_executed(self, user_id: str, trade_id: str, tx_hash: str | None = None):
        """Mark a pending trade as executed."""
        if user_id in self.pending_trades:
            for trade in self.pending_trades[user_id]:
                if trade.id == trade_id:
                    trade.status = "executed"
                    logger.info("Trade marked executed", trade_id=trade_id, tx_hash=tx_hash)
                    return True
        return False

    def mark_trade_skipped(self, user_id: str, trade_id: str):
        """Mark a pending trade as skipped (user declined)."""
        if user_id in self.pending_trades:
            for trade in self.pending_trades[user_id]:
                if trade.id == trade_id:
                    trade.status = "skipped"
                    logger.info("Trade marked skipped", trade_id=trade_id)
                    return True
        return False

    def cleanup_old_trades(self, max_age_minutes: int = 30):
        """Remove old pending trades."""
        cutoff = datetime.now(timezone.utc)
        for user_id in list(self.pending_trades.keys()):
            self.pending_trades[user_id] = [
                t for t in self.pending_trades[user_id]
                if (cutoff - t.created_at).total_seconds() < max_age_minutes * 60
            ]
            if not self.pending_trades[user_id]:
                del self.pending_trades[user_id]

    async def check_trader_activity(
        self,
        db: AsyncSession,
        trader_address: str,
        copy_configs: list[CopyConfig]
    ) -> list[PendingCopyTrade]:
        """
        Check a trader's recent activity and create pending copy trades.

        Args:
            db: Database session
            trader_address: Trader wallet address
            copy_configs: List of copy configurations for this trader

        Returns:
            List of new pending copy trades
        """
        new_trades = []

        # Fetch recent activity from Polymarket
        activities = await polymarket_service.get_trader_activity(
            wallet_address=trader_address,
            limit=20
        )

        if not activities:
            return new_trades

        # Get last seen timestamp for this trader
        last_timestamp = self.last_trade_timestamps.get(trader_address, 0)

        # Get trader portfolio value for sizing
        result = await db.execute(
            select(TraderProfile).where(
                TraderProfile.wallet_address == trader_address.lower()
            )
        )
        trader_profile = result.scalar_one_or_none()
        trader_portfolio = trader_profile.portfolio_value if trader_profile else Decimal("10000")

        for activity in activities:
            trade_timestamp = activity.get("timestamp", 0)
            trade_id = activity.get("id", "")

            # Skip if already processed
            if trade_timestamp <= last_timestamp:
                continue

            # Process this trade for each copy config
            for config in copy_configs:
                if not config.is_active or not config.auto_copy_new:
                    continue

                if config.remaining_allocation <= Decimal("1"):
                    continue

                # Calculate position size
                trade_usdc_size = Decimal(str(activity.get("usdc_size", 0)))
                if trade_usdc_size <= 0:
                    continue

                # Calculate proportional position size
                trade_percentage = trade_usdc_size / trader_portfolio
                position_size = config.allocation * trade_percentage * (config.copy_ratio / Decimal("100"))

                # Apply max position size limit
                if config.max_position_size and position_size > config.max_position_size:
                    position_size = config.max_position_size

                # Apply remaining allocation limit
                if position_size > config.remaining_allocation:
                    position_size = config.remaining_allocation

                # Skip if too small
                if position_size < Decimal("1"):
                    continue

                position_size = Decimal(str(round(float(position_size), 2)))

                # Create pending copy trade
                pending_trade = PendingCopyTrade(
                    id=f"{config.id}-{trade_id}",
                    user_id=config.user_id,
                    copy_config_id=config.id,
                    trader_address=trader_address,
                    market_id=activity.get("market_slug", ""),
                    market_title=activity.get("market_title", "Unknown Market"),
                    market_slug=activity.get("market_slug", ""),
                    event_slug=activity.get("event_slug", ""),
                    side=activity.get("side", "BUY"),
                    size=position_size,
                    price=Decimal(str(activity.get("price", 0))),
                    original_trade_id=trade_id,
                    timestamp=trade_timestamp,
                )

                # Store pending trade
                user_id_str = str(config.user_id)
                if user_id_str not in self.pending_trades:
                    self.pending_trades[user_id_str] = []
                self.pending_trades[user_id_str].append(pending_trade)
                new_trades.append(pending_trade)

                # Notify user via WebSocket
                await self.notify_user(user_id_str, {
                    "type": "new_copy_trade",
                    "trade": pending_trade.to_dict()
                })

                logger.info(
                    "Created pending copy trade",
                    user_id=user_id_str,
                    trader=trader_address,
                    market=pending_trade.market_title,
                    size=str(position_size)
                )

            # Update last seen timestamp
            if trade_timestamp > self.last_trade_timestamps.get(trader_address, 0):
                self.last_trade_timestamps[trader_address] = trade_timestamp

        return new_trades

    async def run_once(self, db: AsyncSession):
        """Run one iteration of the trade watcher."""
        try:
            # Get all active copy configurations grouped by trader
            result = await db.execute(
                select(CopyConfig).where(
                    and_(
                        CopyConfig.is_active == True,
                        CopyConfig.auto_copy_new == True,
                        CopyConfig.remaining_allocation > 1
                    )
                )
            )
            configs = list(result.scalars().all())

            if not configs:
                return

            # Group by trader address
            traders: dict[str, list[CopyConfig]] = {}
            for config in configs:
                addr = config.trader_address.lower()
                if addr not in traders:
                    traders[addr] = []
                traders[addr].append(config)

            # Check each trader's activity
            for trader_address, trader_configs in traders.items():
                try:
                    await self.check_trader_activity(db, trader_address, trader_configs)
                except Exception as e:
                    logger.error(
                        "Error checking trader activity",
                        trader=trader_address,
                        error=str(e)
                    )

            # Cleanup old pending trades
            self.cleanup_old_trades()

        except Exception as e:
            logger.error("Trade watcher error", error=str(e))

    async def start(self, database_url: str):
        """Start the trade watcher background task."""
        if self.is_running:
            logger.warning("Trade watcher already running")
            return

        self.is_running = True
        logger.info("Starting trade watcher", poll_interval=self.poll_interval)

        # Create async engine for background task
        engine = create_async_engine(database_url)
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        while self.is_running:
            try:
                async with async_session() as db:
                    await self.run_once(db)
            except Exception as e:
                logger.error("Trade watcher iteration failed", error=str(e))

            await asyncio.sleep(self.poll_interval)

        await engine.dispose()
        logger.info("Trade watcher stopped")

    def stop(self):
        """Stop the trade watcher."""
        self.is_running = False
        logger.info("Stopping trade watcher")


# Singleton instance
trade_watcher = TradeWatcher()
