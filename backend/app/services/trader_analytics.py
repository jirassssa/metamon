"""Service for calculating trader analytics and performance metrics."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.trader import TraderProfile
from app.services.polymarket import polymarket_service

logger = structlog.get_logger()


class TraderAnalyticsService:
    """Service for trader analytics calculations."""

    @staticmethod
    def calculate_win_rate(trades: list[dict[str, Any]]) -> Decimal:
        """Calculate win rate from trade history."""
        if not trades:
            return Decimal("0")

        winning_trades = sum(
            1 for t in trades
            if Decimal(str(t.get("realized_pnl", 0))) > 0
        )
        return Decimal(str(round(winning_trades / len(trades) * 100, 2)))

    @staticmethod
    def calculate_roi(trades: list[dict[str, Any]]) -> Decimal:
        """Calculate ROI from trade history."""
        if not trades:
            return Decimal("0")

        total_invested = sum(
            Decimal(str(t.get("size", 0))) * Decimal(str(t.get("price", 0)))
            for t in trades
        )
        total_pnl = sum(
            Decimal(str(t.get("realized_pnl", 0)))
            for t in trades
        )

        if total_invested == 0:
            return Decimal("0")

        return Decimal(str(round(total_pnl / total_invested * 100, 2)))

    @staticmethod
    def calculate_max_drawdown(equity_curve: list[Decimal]) -> Decimal:
        """Calculate maximum drawdown from equity curve."""
        if not equity_curve:
            return Decimal("0")

        peak = equity_curve[0]
        max_dd = Decimal("0")

        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100 if peak > 0 else Decimal("0")
            if drawdown > max_dd:
                max_dd = drawdown

        return Decimal(str(round(max_dd, 2)))

    @staticmethod
    def calculate_sharpe_ratio(
        returns: list[Decimal],
        risk_free_rate: Decimal = Decimal("0.05")
    ) -> Decimal:
        """Calculate Sharpe ratio from returns."""
        if len(returns) < 2:
            return Decimal("0")

        avg_return = sum(returns) / len(returns)
        std_dev = (
            sum((r - avg_return) ** 2 for r in returns) / len(returns)
        ) ** Decimal("0.5")

        if std_dev == 0:
            return Decimal("0")

        # Annualize (assuming daily returns)
        annualized_return = avg_return * 365
        annualized_std = std_dev * Decimal(str(365 ** 0.5))

        sharpe = (annualized_return - risk_free_rate) / annualized_std
        return Decimal(str(round(sharpe, 2)))

    @staticmethod
    def calculate_profit_factor(trades: list[dict[str, Any]]) -> Decimal:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = sum(
            Decimal(str(t.get("realized_pnl", 0)))
            for t in trades
            if Decimal(str(t.get("realized_pnl", 0))) > 0
        )
        gross_loss = abs(sum(
            Decimal(str(t.get("realized_pnl", 0)))
            for t in trades
            if Decimal(str(t.get("realized_pnl", 0))) < 0
        ))

        if gross_loss == 0:
            return Decimal("0") if gross_profit == 0 else Decimal("999.99")

        return Decimal(str(round(gross_profit / gross_loss, 2)))

    @staticmethod
    def calculate_risk_score(
        win_rate: Decimal,
        max_drawdown: Decimal,
        profit_factor: Decimal
    ) -> str:
        """
        Calculate overall risk score based on metrics.

        Returns: 'Low', 'Medium', or 'High'
        """
        score = 0

        # Win rate scoring
        if win_rate >= 70:
            score += 2
        elif win_rate >= 55:
            score += 1

        # Drawdown scoring (lower is better)
        if max_drawdown <= 10:
            score += 2
        elif max_drawdown <= 25:
            score += 1

        # Profit factor scoring
        if profit_factor >= 2:
            score += 2
        elif profit_factor >= 1.5:
            score += 1

        if score >= 5:
            return "Low"
        elif score >= 3:
            return "Medium"
        else:
            return "High"

    async def sync_trader_profile(
        self,
        db: AsyncSession,
        wallet_address: str
    ) -> TraderProfile | None:
        """
        Sync trader profile data from Polymarket.

        Args:
            db: Database session
            wallet_address: Trader's wallet address

        Returns:
            Updated TraderProfile or None on error
        """
        try:
            wallet_address = wallet_address.lower()

            # Fetch data from Polymarket Data API (working endpoint)
            trader_data = await polymarket_service.lookup_trader_by_address(wallet_address)

            if not trader_data:
                logger.warning("No data found for trader", wallet=wallet_address)
                return None

            # Extract metrics from data-api response
            # Note: Data API provides PnL and volume but not detailed trade history
            profit = Decimal(str(trader_data.get("profit", 0)))
            volume = Decimal(str(trader_data.get("volume", 0)))

            # Calculate win rate proxy from profit
            # If profit > 0, trader is net positive (rough estimate)
            win_rate = Decimal("55") if profit > 0 else Decimal("45")

            # Calculate ROI as profit / volume (if volume > 0)
            roi = Decimal("0")
            if volume > 0:
                roi = Decimal(str(round(float(profit) / float(volume) * 100, 2)))

            # Estimate profit factor from PnL
            # Positive PnL suggests profit_factor > 1
            profit_factor = Decimal("1.5") if profit > 0 else Decimal("0.8")

            # Default values for metrics we can't calculate from data-api
            max_drawdown = Decimal("0")
            portfolio_value = Decimal("0")

            risk_score = self.calculate_risk_score(win_rate, max_drawdown, profit_factor)

            # Get or create trader profile
            result = await db.execute(
                select(TraderProfile).where(
                    TraderProfile.wallet_address == wallet_address
                )
            )
            profile = result.scalar_one_or_none()

            if profile:
                # Update existing profile
                profile.total_trades = trader_data.get("trades_count", 0)
                profile.win_rate = win_rate
                profile.roi = roi
                profile.total_volume = volume
                profile.portfolio_value = portfolio_value
                profile.max_drawdown = max_drawdown
                profile.profit_factor = profit_factor
                profile.risk_score = risk_score
                profile.last_synced = datetime.now(timezone.utc)
            else:
                # Create new profile
                profile = TraderProfile(
                    wallet_address=wallet_address,
                    total_trades=trader_data.get("trades_count", 0),
                    win_rate=win_rate,
                    roi=roi,
                    total_volume=volume,
                    portfolio_value=portfolio_value,
                    max_drawdown=max_drawdown,
                    profit_factor=profit_factor,
                    risk_score=risk_score,
                    last_synced=datetime.now(timezone.utc),
                )
                db.add(profile)

            await db.commit()
            await db.refresh(profile)

            logger.info(
                "Synced trader profile",
                wallet=wallet_address,
                profit=str(profit),
                volume=str(volume),
                roi=str(roi)
            )

            return profile

        except Exception as e:
            logger.error(
                "Failed to sync trader profile",
                wallet=wallet_address,
                error=str(e)
            )
            await db.rollback()
            return None

    async def get_top_traders(
        self,
        db: AsyncSession,
        limit: int = 10,
        min_trades: int = 10,
        min_win_rate: Decimal = Decimal("0")
    ) -> list[TraderProfile]:
        """
        Get top traders by ROI.

        Args:
            db: Database session
            limit: Maximum number of traders to return
            min_trades: Minimum number of trades required
            min_win_rate: Minimum win rate required

        Returns:
            List of TraderProfile sorted by ROI
        """
        result = await db.execute(
            select(TraderProfile)
            .where(TraderProfile.total_trades >= min_trades)
            .where(TraderProfile.win_rate >= min_win_rate)
            .order_by(TraderProfile.roi.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# Singleton instance
trader_analytics_service = TraderAnalyticsService()
