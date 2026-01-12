"""Authentication service using SIWE (Sign-In with Ethereum)."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from eth_account.messages import encode_defunct
from eth_account import Account
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


class AuthService:
    """Service for handling SIWE authentication."""

    @staticmethod
    def generate_nonce() -> str:
        """Generate a cryptographically secure nonce."""
        return secrets.token_hex(32)

    @staticmethod
    def verify_signature(message: str, signature: str) -> str | None:
        """
        Verify an Ethereum signature and return the recovered address.

        Args:
            message: The message that was signed
            signature: The signature

        Returns:
            The recovered wallet address if valid, None otherwise
        """
        try:
            # Encode the message for Ethereum signing
            message_hash = encode_defunct(text=message)

            # Recover the address from the signature
            recovered_address = Account.recover_message(
                message_hash,
                signature=signature
            )

            return recovered_address.lower()
        except Exception:
            return None

    @staticmethod
    def parse_siwe_message(message: str) -> dict | None:
        """
        Parse a SIWE message to extract components.

        Args:
            message: The SIWE formatted message

        Returns:
            Dictionary with parsed components or None if invalid
        """
        try:
            lines = message.strip().split("\n")
            result = {}

            for line in lines:
                if " wants you to sign in with your Ethereum account:" in line:
                    # Extract domain from first line
                    result["domain"] = line.split(" wants")[0]
                elif line.startswith("0x") and len(line) == 42:
                    result["address"] = line.lower()
                elif line.startswith("Nonce:"):
                    result["nonce"] = line.replace("Nonce:", "").strip()
                elif line.startswith("Chain ID:"):
                    result["chain_id"] = int(line.replace("Chain ID:", "").strip())
                elif line.startswith("Issued At:"):
                    result["issued_at"] = line.replace("Issued At:", "").strip()

            return result if "address" in result and "nonce" in result else None
        except Exception:
            return None

    @staticmethod
    def create_jwt(user_id: UUID, wallet_address: str) -> str:
        """
        Create a JWT token for the authenticated user.

        Args:
            user_id: The user's UUID
            wallet_address: The user's wallet address

        Returns:
            JWT token string
        """
        payload = {
            "user_id": str(user_id),
            "wallet_address": wallet_address.lower(),
            "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
            "iat": datetime.now(timezone.utc),
        }

        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def verify_jwt(token: str) -> dict | None:
        """
        Verify a JWT token and return the payload.

        Args:
            token: The JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        wallet_address: str
    ) -> User:
        """
        Get existing user or create a new one.

        Args:
            db: Database session
            wallet_address: The user's wallet address

        Returns:
            User instance
        """
        wallet_address = wallet_address.lower()

        # Try to find existing user
        result = await db.execute(
            select(User).where(User.wallet_address == wallet_address)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update nonce for next login
            user.nonce = AuthService.generate_nonce()
            await db.commit()
            return user

        # Create new user
        user = User(
            wallet_address=wallet_address,
            nonce=AuthService.generate_nonce(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def get_user_by_wallet(
        db: AsyncSession,
        wallet_address: str
    ) -> User | None:
        """Get user by wallet address."""
        result = await db.execute(
            select(User).where(User.wallet_address == wallet_address.lower())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: UUID
    ) -> User | None:
        """Get user by ID."""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
