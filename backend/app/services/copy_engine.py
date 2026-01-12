"""Copy trading engine for executing copy trades."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition
from app.models.notification import Notification
from app.models.trader import TraderProfile
from app.services.polymarket import polymarket_service

logger = structlog.get_logger()

# Minimum trade size in USDC
MIN_TRADE_SIZE = Decimal("1.00")


class CopyEngine:
    """Engine for processing and executing copy trades."""

    @staticmethod
    def calculate_position_size(
        allocation: Decimal,
        trader_portfolio_value: Decimal,
        trade_size: Decimal,
        copy_ratio: Decimal,
        max_position_size: Decimal | None = None,
        remaining_allocation: Decimal | None = None
    ) -> Decimal:
        """
        Calculate the position size for a copy trade.

        Uses the formula:
        position_size = allocation * (trade_size / trader_portfolio_value) * (copy_ratio / 100)

        Args:
            allocation: User's total allocation for this trader
            trader_portfolio_value: Lead trader's portfolio value
            trade_size: Size of the lead trader's trade
            copy_ratio: Copy ratio percentage (1-100)
            max_position_size: Maximum position size limit
            remaining_allocation: Remaining allocation available

        Returns:
            Calculated position size
        """
        if trader_portfolio_value <= 0:
            return Decimal("0")

        # Calculate base position size
        trade_percentage = trade_size / trader_portfolio_value
        position_size = allocation * trade_percentage * (copy_ratio / Decimal("100"))

        # Apply max position size limit
        if max_position_size and position_size > max_position_size:
            position_size = max_position_size

        # Apply remaining allocation limit
        if remaining_allocation is not None and position_size > remaining_allocation:
            position_size = remaining_allocation

        # Round to 2 decimal places
        return Decimal(str(round(position_size, 2)))

    @staticmethod
    def calculate_stop_loss_price(
        entry_price: Decimal,
        side: str,
        stop_loss_percentage: Decimal
    ) -> Decimal:
        """
        Calculate stop loss price based on entry price and percentage.

        Args:
            entry_price: Entry price of the position
            side: 'YES' or 'NO'
            stop_loss_percentage: Stop loss percentage (e.g., 20 for 20%)

        Returns:
            Stop loss price
        """
        if side == "YES":
            # For YES positions, stop loss is below entry
            return entry_price * (Decimal("1") - stop_loss_percentage / Decimal("100"))
        else:
            # For NO positions, stop loss is above entry
            return entry_price * (Decimal("1") + stop_loss_percentage / Decimal("100"))

    @staticmethod
    def should_trigger_stop_loss(
        current_price: Decimal,
        stop_loss_price: Decimal,
        side: str
    ) -> bool:
        """
        Check if stop loss should be triggered.

        Args:
            current_price: Current market price
            stop_loss_price: Stop loss price
            side: 'YES' or 'NO'

        Returns:
            True if stop loss should trigger
        """
        if side == "YES":
            return current_price <= stop_loss_price
        else:
            return current_price >= stop_loss_price

    async def get_active_copies_for_trader(
        self,
        db: AsyncSession,
        trader_address: str
    ) -> list[CopyConfig]:
        """Get all active copy configurations for a trader."""
        result = await db.execute(
            select(CopyConfig)
            .where(
                and_(
                    CopyConfig.trader_address == trader_address.lower(),
                    CopyConfig.is_active == True,
                    CopyConfig.remaining_allocation > MIN_TRADE_SIZE
                )
            )
        )
        return list(result.scalars().all())

    async def process_new_trade(
        self,
        db: AsyncSession,
        trader_address: str,
        trade: dict[str, Any]
    ) -> list[CopiedPosition]:
        """
        Process a new trade from a lead trader.

        Args:
            db: Database session
            trader_address: Lead trader's wallet address
            trade: Trade data from Polymarket

        Returns:
            List of created CopiedPosition instances
        """
        trader_address = trader_address.lower()
        created_positions = []

        # Get trader profile for portfolio value
        result = await db.execute(
            select(TraderProfile).where(
                TraderProfile.wallet_address == trader_address
            )
        )
        trader_profile = result.scalar_one_or_none()

        if not trader_profile or trader_profile.portfolio_value <= 0:
            logger.warning(
                "No trader profile found for copy",
                trader=trader_address
            )
            return []

        # Get all active copy configurations
        copy_configs = await self.get_active_copies_for_trader(db, trader_address)

        for config in copy_configs:
            try:
                # Skip if auto-copy disabled
                if not config.auto_copy_new:
                    continue

                # Calculate position size
                trade_size = Decimal(str(trade.get("size", 0)))
                position_size = self.calculate_position_size(
                    allocation=config.allocation,
                    trader_portfolio_value=trader_profile.portfolio_value,
                    trade_size=trade_size,
                    copy_ratio=config.copy_ratio,
                    max_position_size=config.max_position_size,
                    remaining_allocation=config.remaining_allocation
                )

                # Skip if position too small
                if position_size < MIN_TRADE_SIZE:
                    logger.info(
                        "Position size too small, skipping",
                        user_id=str(config.user_id),
                        size=str(position_size)
                    )
                    continue

                # Get current price
                entry_price = Decimal(str(trade.get("price", 0)))
                side = trade.get("side", "YES").upper()
                market_id = trade.get("market_id", "")
                market_name = trade.get("market_name", "Unknown Market")

                # Calculate stop loss if configured
                stop_loss_price = None
                if config.stop_loss_percentage:
                    stop_loss_price = self.calculate_stop_loss_price(
                        entry_price=entry_price,
                        side=side,
                        stop_loss_percentage=config.stop_loss_percentage
                    )

                # Create position record
                # Note: In production, this would also execute the actual trade
                # via the Builder Relayer / Safe wallet
                position = CopiedPosition(
                    user_id=config.user_id,
                    copy_config_id=config.id,
                    market_id=market_id,
                    market_name=market_name,
                    trader_address=trader_address,
                    side=side,
                    size=position_size,
                    entry_price=entry_price,
                    current_price=entry_price,
                    pnl=Decimal("0"),
                    pnl_percentage=Decimal("0"),
                    status="open",
                    stop_loss_price=stop_loss_price,
                )
                db.add(position)

                # Update remaining allocation
                config.remaining_allocation -= position_size

                # Create notification if enabled
                if config.notify_on_copy:
                    notification = Notification(
                        user_id=config.user_id,
                        type="trade_copied",
                        title="Trade Copied",
                        message=f"Copied {side} position on {market_name} - ${position_size}",
                        data={
                            "position_id": str(position.id),
                            "market_id": market_id,
                            "side": side,
                            "size": str(position_size),
                            "entry_price": str(entry_price),
                        }
                    )
                    db.add(notification)

                created_positions.append(position)

                logger.info(
                    "Created copy position",
                    user_id=str(config.user_id),
                    trader=trader_address,
                    market=market_name,
                    size=str(position_size)
                )

            except Exception as e:
                logger.error(
                    "Failed to process copy for config",
                    config_id=str(config.id),
                    error=str(e)
                )
                continue

        await db.commit()
        return created_positions

    async def check_stop_losses(self, db: AsyncSession) -> list[CopiedPosition]:
        """
        Check all open positions for stop loss triggers.

        Uses batch price fetching for performance - fetches all unique market
        prices concurrently instead of N+1 sequential calls.

        Returns:
            List of positions that were closed due to stop loss
        """
        closed_positions = []

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
        positions = list(result.scalars().all())

        if not positions:
            return []

        # Batch fetch all unique market prices concurrently
        unique_market_ids = list({p.market_id for p in positions})
        price_tasks = [
            polymarket_service.get_market_price(market_id)
            for market_id in unique_market_ids
        ]
        price_results = await asyncio.gather(*price_tasks, return_exceptions=True)

        # Build market price lookup
        market_prices: dict[str, dict] = {}
        for market_id, result in zip(unique_market_ids, price_results):
            if isinstance(result, Exception):
                logger.warning(
                    "Failed to fetch market price",
                    market_id=market_id,
                    error=str(result)
                )
                continue
            if result is not None:
                market_prices[market_id] = result

        # Process positions using cached prices
        for position in positions:
            try:
                market_data = market_prices.get(position.market_id)
                if market_data is None:
                    logger.warning(
                        "No price data available for stop loss check",
                        position_id=str(position.id),
                        market_id=position.market_id
                    )
                    continue

                # Get current price based on position side
                price_key = "yes_price" if position.side == "YES" else "no_price"
                current_price = Decimal(str(market_data.get(price_key, 0)))
                if current_price <= 0:
                    continue

                # Update position's current price for tracking
                position.current_price = current_price

                # Check if stop loss triggered
                if self.should_trigger_stop_loss(
                    current_price=current_price,
                    stop_loss_price=position.stop_loss_price,
                    side=position.side
                ):
                    await self._close_position_with_stop_loss(
                        db, position, current_price, closed_positions
                    )

            except Exception as e:
                logger.error(
                    "Error checking stop loss",
                    position_id=str(position.id),
                    error=str(e)
                )
                continue

        await db.commit()
        return closed_positions

    async def _close_position_with_stop_loss(
        self,
        db: AsyncSession,
        position: CopiedPosition,
        current_price: Decimal,
        closed_positions: list[CopiedPosition]
    ) -> None:
        """Close a position due to stop loss trigger."""
        # Close position
        position.status = "stopped"
        position.closed_at = datetime.now(timezone.utc)
        position.close_reason = "stop_loss"

        # Calculate PnL
        # For prediction markets: profit = (exit_price - entry_price) * shares
        # position.size represents USDC collateral, shares = size / entry_price
        shares = position.size / position.entry_price
        if position.side == "YES":
            pnl = (current_price - position.entry_price) * shares
        else:
            pnl = (position.entry_price - current_price) * shares

        position.pnl = pnl
        # PnL percentage based on initial capital (position.size = USDC invested)
        position.pnl_percentage = (pnl / position.size) * Decimal("100")

        # Return allocation to config
        config_result = await db.execute(
            select(CopyConfig).where(
                CopyConfig.id == position.copy_config_id
            )
        )
        config = config_result.scalar_one_or_none()
        if config:
            config.remaining_allocation += position.size
            config.total_pnl += pnl

        # Create notification
        notification = Notification(
            user_id=position.user_id,
            type="stop_loss_triggered",
            title="Stop Loss Triggered",
            message=f"Position closed on {position.market_name} at {position.pnl_percentage:.1f}%",
            data={
                "position_id": str(position.id),
                "pnl": str(pnl),
                "pnl_percentage": str(position.pnl_percentage),
            }
        )
        db.add(notification)

        closed_positions.append(position)

        logger.info(
            "Stop loss triggered",
            position_id=str(position.id),
            pnl=str(pnl)
        )


# Singleton instance
copy_engine = CopyEngine()
