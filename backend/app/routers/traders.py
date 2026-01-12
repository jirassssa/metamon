"""Traders router for discovering and viewing trader profiles."""

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.trader import TraderProfile
from app.schemas.trader import (
    TraderResponse,
    TraderListResponse,
    TraderDetailResponse,
    TraderPerformance,
    TraderRiskMetrics,
    DiscoveredTrader,
    DiscoveredTradersResponse,
)
from app.services.trader_analytics import trader_analytics_service
from app.services.polymarket import polymarket_service

router = APIRouter(prefix="/api/traders", tags=["traders"])

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

# Wallet address validation regex (0x followed by 40 hex chars)
WALLET_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


@router.get("", response_model=TraderListResponse)
async def list_traders(
    db: AsyncSession = Depends(get_db),
    timeframe: str = Query("30d", description="Time period for stats"),
    min_win_rate: int = Query(0, ge=0, le=100, description="Minimum win rate"),
    min_trades: int = Query(10, ge=0, description="Minimum number of trades"),
    sort: Literal["roi", "win_rate", "volume", "trades"] = Query("roi"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get a paginated list of traders with optional filters.

    Filters:
    - timeframe: Stats calculation period (7d, 30d, 90d, all)
    - min_win_rate: Minimum win rate percentage
    - min_trades: Minimum number of trades
    - sort: Sort by roi, win_rate, volume, or trades

    Returns paginated list of traders.
    """
    # Build query
    query = select(TraderProfile).where(
        TraderProfile.total_trades >= min_trades,
        TraderProfile.win_rate >= min_win_rate,
    )

    # Apply sorting
    if sort == "roi":
        query = query.order_by(TraderProfile.roi.desc())
    elif sort == "win_rate":
        query = query.order_by(TraderProfile.win_rate.desc())
    elif sort == "volume":
        query = query.order_by(TraderProfile.total_volume.desc())
    elif sort == "trades":
        query = query.order_by(TraderProfile.total_trades.desc())

    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    traders = result.scalars().all()

    return TraderListResponse(
        traders=[
            TraderResponse(
                id=t.id,
                wallet_address=t.wallet_address,
                total_trades=t.total_trades,
                win_rate=t.win_rate,
                roi=t.roi,
                total_volume=t.total_volume,
                followers_count=t.followers_count,
                risk_score=t.risk_score,
            )
            for t in traders
        ],
        total=total,
        page=page,
        limit=limit,
        has_more=offset + len(traders) < total,
    )


@router.get("/top", response_model=list[TraderResponse])
async def get_top_traders(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get the top performing traders by ROI.

    Returns a list of top traders without pagination.
    """
    traders = await trader_analytics_service.get_top_traders(
        db=db,
        limit=limit,
        min_trades=10,
        min_win_rate=Decimal("50"),
    )

    return [
        TraderResponse(
            id=t.id,
            wallet_address=t.wallet_address,
            total_trades=t.total_trades,
            win_rate=t.win_rate,
            roi=t.roi,
            total_volume=t.total_volume,
            followers_count=t.followers_count,
            risk_score=t.risk_score,
        )
        for t in traders
    ]


# Static routes MUST come before dynamic /{address} route
@router.get("/search", response_model=DiscoveredTradersResponse)
@limiter.limit("30/minute")
async def search_traders(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query (address or name)"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
):
    """
    Search for traders by wallet address or display name.

    - If query starts with '0x', searches by address
    - Full address (42 chars) performs direct lookup from Polymarket
    - Partial address or name searches the leaderboard

    This enables looking up any Polymarket trader by their address.
    """
    traders = await polymarket_service.search_traders(
        query=q,
        limit=limit,
    )

    return DiscoveredTradersResponse(
        traders=[
            DiscoveredTrader(
                wallet_address=t["wallet_address"],
                display_name=t.get("display_name"),
                profit=t.get("profit", 0),
                volume=t.get("volume", 0),
                trades_count=t.get("trades_count", 0),
                win_rate=t.get("win_rate", 0),
                positions_count=t.get("positions_count", 0),
                rank=t.get("rank"),
                avatar_url=t.get("avatar_url"),
            )
            for t in traders
        ],
        total=len(traders),
        source="polymarket",
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/lookup/{address}", response_model=DiscoveredTrader | None)
@limiter.limit("60/minute")
async def lookup_trader(
    request: Request,
    address: str,
):
    """
    Look up a specific trader by their exact wallet address.

    Fetches real-time data from Polymarket for the specified address,
    including positions, trade history, and calculated metrics.

    Returns null if the address has no Polymarket trading history.
    """
    # Validate wallet address format
    if not WALLET_ADDRESS_REGEX.match(address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid wallet address format. Must be 0x followed by 40 hex characters."
        )

    trader = await polymarket_service.lookup_trader_by_address(address)

    if not trader:
        return None

    return DiscoveredTrader(
        wallet_address=trader["wallet_address"],
        display_name=trader.get("display_name"),
        profit=trader.get("profit", 0),
        volume=trader.get("volume", 0),
        trades_count=trader.get("trades_count", 0),
        win_rate=trader.get("win_rate", 0),
        positions_count=trader.get("positions_count", 0),
        rank=trader.get("rank"),
        avatar_url=trader.get("avatar_url"),
    )


@router.get("/discover/polymarket", response_model=DiscoveredTradersResponse)
async def discover_polymarket_traders(
    min_win_rate: float = Query(55.0, ge=0, le=100, description="Minimum win rate %"),
    min_trades: int = Query(20, ge=1, description="Minimum number of trades"),
    limit: int = Query(30, ge=1, le=100, description="Maximum traders to return"),
):
    """
    Discover top traders directly from Polymarket.

    This endpoint fetches real-time data from the Polymarket API
    to find profitable traders with high win rates.

    Filters:
    - min_win_rate: Minimum win rate percentage (default 55%)
    - min_trades: Minimum trades completed (default 20)
    - limit: Maximum traders to return (default 30)

    Returns traders sorted by overall performance (profit * win_rate).
    """
    traders = await polymarket_service.discover_profitable_traders(
        min_win_rate=min_win_rate,
        min_trades=min_trades,
        limit=limit,
    )

    return DiscoveredTradersResponse(
        traders=[
            DiscoveredTrader(
                wallet_address=t["wallet_address"],
                display_name=t.get("display_name"),
                profit=t["profit"],
                volume=t["volume"],
                trades_count=t["trades_count"],
                win_rate=t["win_rate"],
                positions_count=t.get("positions_count", 0),
                rank=t.get("rank"),
                avatar_url=t.get("avatar_url"),
            )
            for t in traders
        ],
        total=len(traders),
        source="polymarket",
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/leaderboard/live", response_model=DiscoveredTradersResponse)
async def get_live_leaderboard(
    limit: int = Query(50, ge=1, le=200, description="Number of traders"),
    min_profit: float = Query(0, ge=0, description="Minimum profit in USD"),
):
    """
    Get live leaderboard directly from Polymarket.

    Returns real-time trader rankings from the Polymarket API
    without filtering by win rate.

    Use this endpoint to browse all top traders by profit.
    """
    traders = await polymarket_service.get_top_traders_with_stats(
        limit=limit,
        min_profit=min_profit,
    )

    return DiscoveredTradersResponse(
        traders=[
            DiscoveredTrader(
                wallet_address=t["wallet_address"],
                display_name=t.get("display_name"),
                profit=t["profit"],
                volume=t["volume"],
                trades_count=t["trades_count"],
                win_rate=t["win_rate"],
                positions_count=t.get("positions_count", 0),
                rank=t.get("rank"),
                avatar_url=t.get("avatar_url"),
            )
            for t in traders
        ],
        total=len(traders),
        source="polymarket",
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/activity/{address}")
async def get_trader_activity(
    address: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum activities to return"),
):
    """
    Get trading activity/history for a specific trader.

    Returns a list of recent trades with market info, side, size, and price.
    """
    activities = await polymarket_service.get_trader_activity(
        wallet_address=address,
        limit=limit,
    )

    return {
        "activities": activities,
        "total": len(activities),
        "wallet_address": address.lower(),
    }


# Dynamic routes with path parameters come LAST
@router.get("/{address}", response_model=TraderDetailResponse)
async def get_trader(
    address: str,
    db: AsyncSession = Depends(get_db),
    include: str = Query("", description="Comma-separated: positions,history"),
):
    """
    Get detailed information about a specific trader.

    The `include` query parameter can be used to include additional data:
    - positions: Include current open positions
    - history: Include trade history

    Returns full trader profile with performance and risk metrics.
    """
    address = address.lower()

    # Try to find trader in database
    result = await db.execute(
        select(TraderProfile).where(TraderProfile.wallet_address == address)
    )
    trader = result.scalar_one_or_none()

    # If not found, try to sync from Polymarket
    if not trader:
        trader = await trader_analytics_service.sync_trader_profile(db, address)

    if not trader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trader not found"
        )

    return TraderDetailResponse(
        id=trader.id,
        wallet_address=trader.wallet_address,
        first_trade_date=trader.first_trade_date,
        last_synced=trader.last_synced,
        performance=TraderPerformance(
            roi=trader.roi,
            win_rate=trader.win_rate,
            total_trades=trader.total_trades,
            total_volume=trader.total_volume,
            max_drawdown=trader.max_drawdown,
            sharpe_ratio=trader.sharpe_ratio,
            profit_factor=trader.profit_factor,
        ),
        risk=TraderRiskMetrics(
            risk_score=trader.risk_score,
            max_drawdown=trader.max_drawdown,
            sharpe_ratio=trader.sharpe_ratio,
            profit_factor=trader.profit_factor,
        ),
        followers_count=trader.followers_count,
    )


@router.post("/{address}/sync", response_model=TraderResponse)
async def sync_trader(
    address: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Force sync a trader's profile from Polymarket.

    This will fetch the latest data from Polymarket and update
    the cached profile.
    """
    trader = await trader_analytics_service.sync_trader_profile(db, address.lower())

    if not trader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not fetch trader data from Polymarket"
        )

    return TraderResponse(
        id=trader.id,
        wallet_address=trader.wallet_address,
        total_trades=trader.total_trades,
        win_rate=trader.win_rate,
        roi=trader.roi,
        total_volume=trader.total_volume,
        followers_count=trader.followers_count,
        risk_score=trader.risk_score,
    )
