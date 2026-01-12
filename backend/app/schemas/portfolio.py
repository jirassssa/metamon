"""Portfolio schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.position import PositionResponse
from app.schemas.copy_config import CopyConfigResponse


class PortfolioSummary(BaseModel):
    """Portfolio summary statistics."""

    total_value: Decimal = 0
    available_balance: Decimal = 0
    total_pnl: Decimal = 0
    total_pnl_percentage: Decimal = 0
    open_positions_count: int = 0
    active_copies_count: int = 0
    win_rate: Decimal = 0


class PerformancePoint(BaseModel):
    """Single data point for performance chart."""

    date: date
    total_value: Decimal
    total_pnl: Decimal


class PortfolioResponse(BaseModel):
    """Full portfolio response."""

    summary: PortfolioSummary
    positions: list[PositionResponse]
    copy_configs: list[CopyConfigResponse]
    performance_history: list[PerformancePoint]
