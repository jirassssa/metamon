"""Notification and performance snapshot models."""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, DateTime, Date, Boolean, Numeric, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """User notification for trade events and alerts."""

    __tablename__ = "notifications"

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

    # Notification content
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # trade_copied, stop_loss_triggered, portfolio_high, error
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return f"<Notification {self.type}: {self.title[:30]}...>"


class PerformanceSnapshot(Base):
    """Daily snapshot of user portfolio performance for charts."""

    __tablename__ = "performance_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_user_date"),
    )

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

    # Performance data
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    total_pnl: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Date
    snapshot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="performance_snapshots",
    )

    def __repr__(self) -> str:
        return f"<PerformanceSnapshot {self.snapshot_date} value=${self.total_value}>"
