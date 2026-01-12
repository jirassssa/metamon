"""Copy configuration schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CopyConfigCreate(BaseModel):
    """Request to create a new copy configuration."""

    trader_address: str = Field(..., pattern="^0x[a-fA-F0-9]{40}$")
    allocation: Decimal = Field(..., gt=0, description="Total USDC to allocate")
    max_position_size: Decimal | None = Field(None, gt=0, description="Max per trade")
    copy_ratio: Decimal = Field(default=100, ge=1, le=100, description="Copy ratio percentage")
    stop_loss_percentage: Decimal | None = Field(None, ge=1, le=100, description="Stop loss %")
    take_profit_percentage: Decimal | None = Field(None, ge=1, description="Take profit %")
    auto_copy_new: bool = True
    mirror_close: bool = False
    notify_on_copy: bool = True

    @field_validator("trader_address")
    @classmethod
    def lowercase_address(cls, v: str) -> str:
        return v.lower()


class CopyConfigUpdate(BaseModel):
    """Request to update a copy configuration."""

    allocation: Decimal | None = Field(None, gt=0)
    max_position_size: Decimal | None = Field(None, gt=0)
    copy_ratio: Decimal | None = Field(None, ge=1, le=100)
    stop_loss_percentage: Decimal | None = None
    take_profit_percentage: Decimal | None = None
    auto_copy_new: bool | None = None
    mirror_close: bool | None = None
    notify_on_copy: bool | None = None
    is_active: bool | None = None


class CopyConfigResponse(BaseModel):
    """Response schema for a copy configuration."""

    id: UUID
    trader_address: str
    allocation: Decimal
    remaining_allocation: Decimal
    max_position_size: Decimal | None = None
    copy_ratio: Decimal
    stop_loss_percentage: Decimal | None = None
    take_profit_percentage: Decimal | None = None
    auto_copy_new: bool
    mirror_close: bool
    notify_on_copy: bool
    is_active: bool
    total_pnl: Decimal
    created_at: datetime
    updated_at: datetime

    # Trader info (populated from join)
    trader_name: str | None = None
    trader_roi: Decimal | None = None
    trader_win_rate: Decimal | None = None

    class Config:
        from_attributes = True


class CopyConfigListResponse(BaseModel):
    """List of copy configurations."""

    copies: list[CopyConfigResponse]
    total: int
