"""Notification schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for a notification."""

    id: UUID
    type: str
    title: str
    message: str
    data: dict[str, Any] | None = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int
