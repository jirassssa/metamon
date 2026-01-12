"""Position schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PositionResponse(BaseModel):
    """Response schema for a single position."""

    id: UUID
    market_id: str
    market_name: str
    trader_address: str
    side: str
    size: Decimal
    entry_price: Decimal
    current_price: Decimal | None = None
    pnl: Decimal | None = None
    pnl_percentage: Decimal | None = None
    status: str = "open"
    stop_loss_price: Decimal | None = None
    take_profit_price: Decimal | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    close_reason: str | None = None

    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    """List of positions."""

    positions: list[PositionResponse]
    total: int
