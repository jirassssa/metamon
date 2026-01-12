"""Authentication router for SIWE."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas.user import NonceResponse, AuthVerifyRequest, AuthResponse, UserResponse
from app.services.auth import AuthService
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/nonce", response_model=NonceResponse)
@limiter.limit("30/minute")
async def get_nonce(request: Request):
    """
    Get a new nonce for SIWE authentication.

    Returns a cryptographically secure nonce that should be included
    in the SIWE message.
    """
    nonce = AuthService.generate_nonce()
    return NonceResponse(nonce=nonce)


@router.post("/verify", response_model=AuthResponse)
@limiter.limit("10/minute")
async def verify_signature(
    request: Request,
    body: AuthVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify SIWE signature and authenticate user.

    This endpoint verifies the signed SIWE message and returns a JWT token
    if the signature is valid.
    """
    # Parse the SIWE message
    parsed = AuthService.parse_siwe_message(body.message)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SIWE message format"
        )

    # Verify the signature
    recovered_address = AuthService.verify_signature(
        body.message,
        body.signature
    )

    if not recovered_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Check that recovered address matches the message
    if recovered_address.lower() != parsed["address"].lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature does not match address in message"
        )

    # Get or create user
    user = await AuthService.get_or_create_user(db, recovered_address)

    # Generate JWT
    token = AuthService.create_jwt(user.id, user.wallet_address)

    return AuthResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            wallet_address=user.wallet_address,
            safe_address=user.safe_address,
            created_at=user.created_at,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current authenticated user's information.

    Requires a valid JWT token in the Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        wallet_address=current_user.wallet_address,
        safe_address=current_user.safe_address,
        created_at=current_user.created_at,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout the current user.

    Note: Since we use stateless JWTs, this endpoint doesn't actually
    invalidate the token. The client should discard the token.
    In a production environment, you might want to implement a token
    blacklist using Redis.
    """
    # In a real implementation, you might add the token to a blacklist
    return None
