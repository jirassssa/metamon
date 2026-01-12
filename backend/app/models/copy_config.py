"""Copy configuration model for tracking copy relationships."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, Numeric, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.position import CopiedPosition


class CopyConfig(Base):
    """Configuration for copying a specific trader."""

    __tablename__ = "copy_configs"
    __table_args__ = (
        UniqueConstraint("user_id", "trader_address", name="uq_user_trader"),
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
    trader_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
        index=True,
    )

    # Allocation settings
    allocation: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    remaining_allocation: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    max_position_size: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    copy_ratio: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=100,
    )

    # Risk settings
    stop_loss_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    take_profit_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Behavior settings
    auto_copy_new: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    mirror_close: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    notify_on_copy: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    total_pnl: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=0,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="copy_configs",
    )
    positions: Mapped[list["CopiedPosition"]] = relationship(
        "CopiedPosition",
        back_populates="copy_config",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CopyConfig user={self.user_id} trader={self.trader_address[:10]}...>"
