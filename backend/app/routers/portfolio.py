"""Portfolio router for viewing user portfolio data."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition
from app.models.notification import PerformanceSnapshot, Notification
from app.models.trader import TraderProfile
from app.schemas.portfolio import PortfolioResponse, PortfolioSummary, PerformancePoint
from app.schemas.position import PositionResponse
from app.schemas.copy_config import CopyConfigResponse
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include: str = Query("", description="Comma-separated: history"),
):
    """
    Get the current user's complete portfolio.

    Returns:
    - Summary with total value, P/L, and statistics
    - Open positions
    - Active copy configurations
    - Performance history for charts
    """
    # Get open positions
    positions_result = await db.execute(
        select(CopiedPosition)
        .where(
            and_(
                CopiedPosition.user_id == current_user.id,
                CopiedPosition.status == "open"
            )
        )
        .order_by(CopiedPosition.opened_at.desc())
    )
    positions = positions_result.scalars().all()

    # Get copy configurations with trader info
    configs_result = await db.execute(
        select(CopyConfig, TraderProfile)
        .outerjoin(
            TraderProfile,
            CopyConfig.trader_address == TraderProfile.wallet_address
        )
        .where(CopyConfig.user_id == current_user.id)
        .order_by(CopyConfig.created_at.desc())
    )
    configs_with_traders = configs_result.all()

    # Get performance history
    snapshots_result = await db.execute(
        select(PerformanceSnapshot)
        .where(PerformanceSnapshot.user_id == current_user.id)
        .order_by(PerformanceSnapshot.snapshot_date.desc())
        .limit(90)  # Last 90 days
    )
    snapshots = snapshots_result.scalars().all()

    # Calculate summary
    total_position_value = sum(
        p.size * (p.current_price or p.entry_price)
        for p in positions
    )
    total_pnl = sum(p.pnl or Decimal("0") for p in positions)
    total_allocation = sum(c.allocation for c, _ in configs_with_traders)
    available_balance = sum(c.remaining_allocation for c, _ in configs_with_traders)

    # Count wins for win rate
    closed_result = await db.execute(
        select(CopiedPosition)
        .where(
            and_(
                CopiedPosition.user_id == current_user.id,
                CopiedPosition.status != "open"
            )
        )
    )
    closed_positions = closed_result.scalars().all()

    total_closed = len(closed_positions)
    wins = sum(1 for p in closed_positions if (p.pnl or 0) > 0)
    win_rate = Decimal(str(round(wins / total_closed * 100, 2))) if total_closed > 0 else Decimal("0")

    # Build response
    summary = PortfolioSummary(
        total_value=total_position_value + available_balance,
        available_balance=available_balance,
        total_pnl=total_pnl,
        total_pnl_percentage=(
            Decimal(str(round(total_pnl / total_allocation * 100, 2)))
            if total_allocation > 0 else Decimal("0")
        ),
        open_positions_count=len(positions),
        active_copies_count=sum(1 for c, _ in configs_with_traders if c.is_active),
        win_rate=win_rate,
    )

    return PortfolioResponse(
        summary=summary,
        positions=[
            PositionResponse(
                id=p.id,
                market_id=p.market_id,
                market_name=p.market_name,
                trader_address=p.trader_address,
                side=p.side,
                size=p.size,
                entry_price=p.entry_price,
                current_price=p.current_price,
                pnl=p.pnl,
                pnl_percentage=p.pnl_percentage,
                status=p.status,
                stop_loss_price=p.stop_loss_price,
                take_profit_price=p.take_profit_price,
                opened_at=p.opened_at,
                closed_at=p.closed_at,
                close_reason=p.close_reason,
            )
            for p in positions
        ],
        copy_configs=[
            CopyConfigResponse(
                id=c.id,
                trader_address=c.trader_address,
                allocation=c.allocation,
                remaining_allocation=c.remaining_allocation,
                max_position_size=c.max_position_size,
                copy_ratio=c.copy_ratio,
                stop_loss_percentage=c.stop_loss_percentage,
                take_profit_percentage=c.take_profit_percentage,
                auto_copy_new=c.auto_copy_new,
                mirror_close=c.mirror_close,
                notify_on_copy=c.notify_on_copy,
                is_active=c.is_active,
                total_pnl=c.total_pnl,
                created_at=c.created_at,
                updated_at=c.updated_at,
                trader_name=None,  # Could be populated from ENS or display name
                trader_roi=t.roi if t else None,
                trader_win_rate=t.win_rate if t else None,
            )
            for c, t in configs_with_traders
        ],
        performance_history=[
            PerformancePoint(
                date=s.snapshot_date,
                total_value=s.total_value,
                total_pnl=s.total_pnl,
            )
            for s in reversed(snapshots)
        ],
    )


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
):
    """
    Get user notifications.

    Args:
        limit: Maximum number of notifications to return
        unread_only: If true, only return unread notifications
    """
    query = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)

    result = await db.execute(query)
    notifications = result.scalars().all()

    # Count unread
    unread_result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    unread_count = unread_result.scalar() or 0

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                type=n.type,
                title=n.title,
                message=n.message,
                data=n.data,
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        total=len(notifications),
        unread_count=unread_count,
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    from uuid import UUID

    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == UUID(notification_id),
                Notification.user_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()

    if notification:
        notification.is_read = True
        await db.commit()

    return {"success": True}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    from sqlalchemy import update

    await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
        .values(is_read=True)
    )
    await db.commit()

    return {"success": True}
