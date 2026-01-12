"""Trader schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TraderResponse(BaseModel):
    """Basic trader info for list views."""

    id: UUID
    wallet_address: str
    total_trades: int = 0
    win_rate: Decimal = Field(default=0, ge=0, le=100)
    roi: Decimal = 0
    total_volume: Decimal = 0
    followers_count: int = 0
    risk_score: str | None = None

    class Config:
        from_attributes = True


class TraderPerformance(BaseModel):
    """Detailed performance metrics."""

    roi: Decimal = 0
    win_rate: Decimal = 0
    total_trades: int = 0
    total_volume: Decimal = 0
    max_drawdown: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    profit_factor: Decimal | None = None


class TraderRiskMetrics(BaseModel):
    """Risk-related metrics."""

    risk_score: str | None = None
    max_drawdown: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    profit_factor: Decimal | None = None


class TraderDetailResponse(BaseModel):
    """Full trader profile with all details."""

    id: UUID
    wallet_address: str
    first_trade_date: datetime | None = None
    last_synced: datetime | None = None

    # Performance
    performance: TraderPerformance

    # Risk
    risk: TraderRiskMetrics

    # Social
    followers_count: int = 0

    class Config:
        from_attributes = True


class TraderListResponse(BaseModel):
    """Paginated list of traders."""

    traders: list[TraderResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class DiscoveredTrader(BaseModel):
    """Trader discovered from Polymarket API."""

    wallet_address: str
    display_name: str | None = None
    profit: float = 0
    volume: float = 0
    trades_count: int = 0
    win_rate: float = 0
    positions_count: int = 0
    rank: int | None = None
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class DiscoveredTradersResponse(BaseModel):
    """Response for discovered traders from Polymarket."""

    traders: list[DiscoveredTrader]
    total: int
    source: str = "polymarket"
    last_updated: datetime | None = None
