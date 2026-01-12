"""Authentication middleware and dependencies."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import AuthService


class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)


jwt_bearer = JWTBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.

    Args:
        credentials: JWT bearer token
        db: Database session

    Returns:
        The authenticated User

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Verify JWT
    payload = AuthService.verify_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id = UUID(payload.get("user_id"))
    user = await AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(JWTBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    Optional authentication - returns user if authenticated, None otherwise.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
