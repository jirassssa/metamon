"""Copied position model for tracking positions opened via copy trading."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.copy_config import CopyConfig


class CopiedPosition(Base):
    """A position opened through copy trading."""

    __tablename__ = "copied_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    copy_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copy_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Market info
    market_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    market_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    condition_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Trade details
    trader_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )
    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # 'YES' or 'NO'
    size: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    entry_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )

    # Current state
    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    pnl: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    pnl_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        index=True,
    )  # open, closed, stopped

    # Risk management
    stop_loss_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    take_profit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )

    # Timestamps
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    close_reason: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # manual, stop_loss, take_profit, mirrored

    # Transaction info
    tx_hash: Mapped[str | None] = mapped_column(
        String(66),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="positions",
    )
    copy_config: Mapped["CopyConfig"] = relationship(
        "CopyConfig",
        back_populates="positions",
    )

    def __repr__(self) -> str:
        return f"<CopiedPosition {self.market_name[:20]}... {self.side} ${self.size}>"
