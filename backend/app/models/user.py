"""User model for authentication."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.copy_config import CopyConfig
    from app.models.position import CopiedPosition
    from app.models.notification import Notification, PerformanceSnapshot


class User(Base):
    """User model representing authenticated wallet addresses."""

    __tablename__ = "users"

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
    nonce: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    safe_address: Mapped[str | None] = mapped_column(
        String(42),
        nullable=True,
    )
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
    copy_configs: Mapped[list["CopyConfig"]] = relationship(
        "CopyConfig",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["CopiedPosition"]] = relationship(
        "CopiedPosition",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    performance_snapshots: Mapped[list["PerformanceSnapshot"]] = relationship(
        "PerformanceSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.wallet_address[:10]}...>"
