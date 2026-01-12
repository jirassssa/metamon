"""Copy configuration service for data access abstraction."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition
from app.models.trader import TraderProfile
from app.schemas.copy_config import CopyConfigResponse
from app.schemas.position import PositionResponse


class CopyService:
    """Service for copy configuration data access and business logic."""

    @staticmethod
    async def get_copy_with_trader(
        db: AsyncSession,
        copy_id: UUID,
        user_id: UUID
    ) -> tuple[CopyConfig, TraderProfile | None] | None:
        """
        Get a copy configuration with associated trader profile.

        Args:
            db: Database session
            copy_id: Copy configuration ID
            user_id: User ID for ownership verification

        Returns:
            Tuple of (CopyConfig, TraderProfile) or None if not found
        """
        result = await db.execute(
            select(CopyConfig, TraderProfile)
            .outerjoin(
                TraderProfile,
                CopyConfig.trader_address == TraderProfile.wallet_address
            )
            .where(
                and_(
                    CopyConfig.id == copy_id,
                    CopyConfig.user_id == user_id
                )
            )
        )
        row = result.one_or_none()
        return row if row else None

    @staticmethod
    async def get_copy_by_id(
        db: AsyncSession,
        copy_id: UUID,
        user_id: UUID
    ) -> CopyConfig | None:
        """
        Get a copy configuration by ID with ownership check.

        Args:
            db: Database session
            copy_id: Copy configuration ID
            user_id: User ID for ownership verification

        Returns:
            CopyConfig or None if not found
        """
        result = await db.execute(
            select(CopyConfig).where(
                and_(
                    CopyConfig.id == copy_id,
                    CopyConfig.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_trader_by_address(
        db: AsyncSession,
        trader_address: str
    ) -> TraderProfile | None:
        """Get trader profile by wallet address."""
        result = await db.execute(
            select(TraderProfile).where(
                TraderProfile.wallet_address == trader_address.lower()
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_copies_with_traders(
        db: AsyncSession,
        user_id: UUID
    ) -> list[tuple[CopyConfig, TraderProfile | None]]:
        """
        Get all copy configurations for a user with trader info.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of (CopyConfig, TraderProfile) tuples
        """
        result = await db.execute(
            select(CopyConfig, TraderProfile)
            .outerjoin(
                TraderProfile,
                CopyConfig.trader_address == TraderProfile.wallet_address
            )
            .where(CopyConfig.user_id == user_id)
            .order_by(CopyConfig.created_at.desc())
        )
        return list(result.all())

    @staticmethod
    async def check_existing_copy(
        db: AsyncSession,
        user_id: UUID,
        trader_address: str
    ) -> bool:
        """Check if user is already copying a trader."""
        result = await db.execute(
            select(CopyConfig).where(
                and_(
                    CopyConfig.user_id == user_id,
                    CopyConfig.trader_address == trader_address.lower()
                )
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_copy_positions(
        db: AsyncSession,
        copy_id: UUID
    ) -> list[CopiedPosition]:
        """Get all positions for a copy configuration."""
        result = await db.execute(
            select(CopiedPosition)
            .where(CopiedPosition.copy_config_id == copy_id)
            .order_by(CopiedPosition.opened_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def build_copy_response(
        config: CopyConfig,
        trader: TraderProfile | None
    ) -> CopyConfigResponse:
        """
        Build a CopyConfigResponse from a config and trader.

        Args:
            config: Copy configuration
            trader: Optional trader profile

        Returns:
            CopyConfigResponse schema
        """
        return CopyConfigResponse(
            id=config.id,
            trader_address=config.trader_address,
            allocation=config.allocation,
            remaining_allocation=config.remaining_allocation,
            max_position_size=config.max_position_size,
            copy_ratio=config.copy_ratio,
            stop_loss_percentage=config.stop_loss_percentage,
            take_profit_percentage=config.take_profit_percentage,
            auto_copy_new=config.auto_copy_new,
            mirror_close=config.mirror_close,
            notify_on_copy=config.notify_on_copy,
            is_active=config.is_active,
            total_pnl=config.total_pnl,
            created_at=config.created_at,
            updated_at=config.updated_at,
            trader_name=None,
            trader_roi=trader.roi if trader else None,
            trader_win_rate=trader.win_rate if trader else None,
        )

    @staticmethod
    def build_position_response(position: CopiedPosition) -> PositionResponse:
        """Build a PositionResponse from a position."""
        return PositionResponse(
            id=position.id,
            market_id=position.market_id,
            market_name=position.market_name,
            trader_address=position.trader_address,
            side=position.side,
            size=position.size,
            entry_price=position.entry_price,
            current_price=position.current_price,
            pnl=position.pnl,
            pnl_percentage=position.pnl_percentage,
            status=position.status,
            stop_loss_price=position.stop_loss_price,
            take_profit_price=position.take_profit_price,
            opened_at=position.opened_at,
            closed_at=position.closed_at,
            close_reason=position.close_reason,
        )

    @staticmethod
    def calculate_remaining_allocation_on_update(
        current_allocation: Decimal,
        current_remaining: Decimal,
        new_allocation: Decimal
    ) -> Decimal:
        """
        Calculate new remaining allocation when allocation is updated.

        Preserves the used amount and adjusts remaining proportionally.

        Args:
            current_allocation: Current total allocation
            current_remaining: Current remaining allocation
            new_allocation: New total allocation

        Returns:
            New remaining allocation
        """
        used_allocation = current_allocation - current_remaining
        new_remaining = new_allocation - used_allocation
        return max(new_remaining, Decimal("0"))

    @staticmethod
    async def close_positions_for_copy(
        db: AsyncSession,
        copy_id: UUID,
        close_reason: str = "config_deleted"
    ) -> int:
        """
        Close all open positions for a copy configuration.

        Args:
            db: Database session
            copy_id: Copy configuration ID
            close_reason: Reason for closing (default: "config_deleted")

        Returns:
            Number of positions closed
        """
        result = await db.execute(
            select(CopiedPosition)
            .where(
                and_(
                    CopiedPosition.copy_config_id == copy_id,
                    CopiedPosition.status == "open"
                )
            )
        )
        positions = list(result.scalars().all())

        closed_count = 0
        for position in positions:
            position.status = "closed"
            position.closed_at = datetime.now(timezone.utc)
            position.close_reason = close_reason
            closed_count += 1

        return closed_count


# Singleton instance
copy_service = CopyService()
