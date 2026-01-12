"""Trader profile model for caching trader data from Polymarket."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TraderProfile(Base):
    """Cached trader profile data from Polymarket."""

    __tablename__ = "trader_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    wallet_address: Mapped[str] = mapped_column(
        String(42),
        unique=True,
        nullable=False,
        index=True,
    )

    # Performance metrics
    total_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    win_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=0,
    )
    roi: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
    )
    total_volume: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=0,
    )
    portfolio_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=0,
    )

    # Social metrics
    followers_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # Risk metrics
    risk_score: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    max_drawdown: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    profit_factor: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Timestamps
    first_trade_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_synced: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<TraderProfile {self.wallet_address[:10]}... ROI={self.roi}%>"
