"""Tests for authentication."""

import pytest
from uuid import uuid4

from app.services.auth import AuthService


class TestAuthService:
    """Tests for AuthService class."""

    def test_generate_nonce(self):
        """Test nonce generation."""
        nonce1 = AuthService.generate_nonce()
        nonce2 = AuthService.generate_nonce()

        # Nonce should be 64 characters (32 bytes hex)
        assert len(nonce1) == 64
        assert len(nonce2) == 64

        # Nonces should be unique
        assert nonce1 != nonce2

    def test_parse_siwe_message_valid(self):
        """Test parsing a valid SIWE message."""
        message = """shadow-copy-trader.com wants you to sign in with your Ethereum account:
0x1234567890123456789012345678901234567890

Sign in to MetamonMarket

URI: https://shadow-copy-trader.com
Version: 1
Chain ID: 137
Nonce: abc123def456
Issued At: 2026-01-12T10:00:00Z"""

        result = AuthService.parse_siwe_message(message)

        assert result is not None
        assert result["domain"] == "shadow-copy-trader.com"
        assert result["address"] == "0x1234567890123456789012345678901234567890"
        assert result["nonce"] == "abc123def456"
        assert result["chain_id"] == 137

    def test_parse_siwe_message_invalid(self):
        """Test parsing an invalid SIWE message."""
        message = "This is not a valid SIWE message"

        result = AuthService.parse_siwe_message(message)

        assert result is None

    def test_create_and_verify_jwt(self):
        """Test JWT creation and verification."""
        user_id = uuid4()
        wallet_address = "0x1234567890123456789012345678901234567890"

        token = AuthService.create_jwt(user_id, wallet_address)

        assert token is not None
        assert len(token) > 0

        # Verify the token
        payload = AuthService.verify_jwt(token)

        assert payload is not None
        assert payload["user_id"] == str(user_id)
        assert payload["wallet_address"] == wallet_address.lower()

    def test_verify_jwt_invalid(self):
        """Test verification of invalid JWT."""
        result = AuthService.verify_jwt("invalid.token.here")

        assert result is None

    def test_verify_jwt_expired(self):
        """Test verification of expired JWT."""
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.config import settings

        # Create an expired token
        payload = {
            "user_id": str(uuid4()),
            "wallet_address": "0x1234567890123456789012345678901234567890",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=25),
        }
        expired_token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

        result = AuthService.verify_jwt(expired_token)

        assert result is None


@pytest.mark.asyncio
class TestAuthServiceAsync:
    """Async tests for AuthService."""

    async def test_get_or_create_user_new(self, test_db):
        """Test creating a new user."""
        wallet_address = "0xabcdef1234567890abcdef1234567890abcdef12"

        user = await AuthService.get_or_create_user(test_db, wallet_address)

        assert user is not None
        assert user.wallet_address == wallet_address.lower()
        assert len(user.nonce) == 64

    async def test_get_or_create_user_existing(self, test_db, test_user):
        """Test getting an existing user."""
        original_nonce = test_user.nonce

        user = await AuthService.get_or_create_user(
            test_db,
            test_user.wallet_address
        )

        assert user is not None
        assert user.id == test_user.id
        # Nonce should be updated
        assert user.nonce != original_nonce

    async def test_get_user_by_wallet(self, test_db, test_user):
        """Test getting user by wallet address."""
        user = await AuthService.get_user_by_wallet(
            test_db,
            test_user.wallet_address
        )

        assert user is not None
        assert user.id == test_user.id

    async def test_get_user_by_wallet_not_found(self, test_db):
        """Test getting non-existent user by wallet."""
        user = await AuthService.get_user_by_wallet(
            test_db,
            "0x0000000000000000000000000000000000000000"
        )

        assert user is None

    async def test_get_user_by_id(self, test_db, test_user):
        """Test getting user by ID."""
        user = await AuthService.get_user_by_id(test_db, test_user.id)

        assert user is not None
        assert user.wallet_address == test_user.wallet_address

    async def test_get_user_by_id_not_found(self, test_db):
        """Test getting non-existent user by ID."""
        from uuid import uuid4

        user = await AuthService.get_user_by_id(test_db, uuid4())

        assert user is None
