"""User and authentication schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    wallet_address: str
    safe_address: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NonceResponse(BaseModel):
    """Response containing nonce for SIWE."""

    nonce: str


class AuthVerifyRequest(BaseModel):
    """Request to verify SIWE signature."""

    message: str = Field(..., description="The SIWE message that was signed")
    signature: str = Field(..., description="The signature of the message")


class AuthResponse(BaseModel):
    """Response after successful authentication."""

    token: str
    user: UserResponse
