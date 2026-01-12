"""Integration tests for copy trading API endpoints."""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.copy_config import CopyConfig
from app.services.auth import AuthService


class TestCopyAPI:
    """Integration tests for /api/copies endpoints."""

    @pytest.mark.asyncio
    async def test_list_copies_empty(self, client: AsyncClient, test_user):
        """Test listing copies when user has none."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.get(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["copies"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_copies_with_data(
        self,
        client: AsyncClient,
        test_user,
        test_copy_config
    ):
        """Test listing copies when user has configurations."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.get(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["copies"]) == 1
        assert data["copies"][0]["trader_address"] == test_copy_config.trader_address

    @pytest.mark.asyncio
    async def test_create_copy_success(
        self,
        client: AsyncClient,
        test_user,
        test_trader
    ):
        """Test creating a new copy configuration."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.post(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trader_address": test_trader.wallet_address,
                "allocation": "500.00",
                "max_position_size": "100.00",
                "copy_ratio": "75.00",
                "stop_loss_percentage": "15.00",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["trader_address"] == test_trader.wallet_address.lower()
        assert Decimal(data["allocation"]) == Decimal("500.00")
        assert Decimal(data["copy_ratio"]) == Decimal("75.00")
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_copy_duplicate(
        self,
        client: AsyncClient,
        test_user,
        test_copy_config
    ):
        """Test creating duplicate copy configuration fails."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.post(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trader_address": test_copy_config.trader_address,
                "allocation": "500.00",
            }
        )

        assert response.status_code == 400
        assert "Already copying" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_copy_success(
        self,
        client: AsyncClient,
        test_user,
        test_copy_config
    ):
        """Test getting a specific copy configuration."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.get(
            f"/api/copies/{test_copy_config.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_copy_config.id)
        assert data["trader_address"] == test_copy_config.trader_address

    @pytest.mark.asyncio
    async def test_get_copy_not_found(self, client: AsyncClient, test_user):
        """Test getting non-existent copy configuration."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.get(
            f"/api/copies/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_copy_unauthorized(
        self,
        client: AsyncClient,
        test_db,
        test_copy_config
    ):
        """Test getting another user's copy configuration fails."""
        # Create another user
        from app.models.user import User
        other_user = User(
            wallet_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            nonce="other-nonce"
        )
        test_db.add(other_user)
        await test_db.commit()
        await test_db.refresh(other_user)

        token = AuthService.create_jwt(other_user.id, other_user.wallet_address)

        response = await client.get(
            f"/api/copies/{test_copy_config.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 404 (not 403) to avoid leaking existence info
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_copy_success(
        self,
        client: AsyncClient,
        test_user,
        test_copy_config
    ):
        """Test updating a copy configuration."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.put(
            f"/api/copies/{test_copy_config.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "copy_ratio": "80.00",
                "stop_loss_percentage": "25.00",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["copy_ratio"]) == Decimal("80.00")
        assert Decimal(data["stop_loss_percentage"]) == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_update_copy_allocation_adjusts_remaining(
        self,
        client: AsyncClient,
        test_user,
        test_db,
        test_copy_config
    ):
        """Test that updating allocation adjusts remaining allocation."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        # Simulate some allocation being used
        test_copy_config.remaining_allocation = Decimal("500.00")
        await test_db.commit()

        response = await client.put(
            f"/api/copies/{test_copy_config.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "allocation": "2000.00",
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Original: 1000, Remaining: 500, Used: 500
        # New allocation: 2000, New remaining: 2000 - 500 = 1500
        assert Decimal(data["allocation"]) == Decimal("2000.00")
        assert Decimal(data["remaining_allocation"]) == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_delete_copy_success(
        self,
        client: AsyncClient,
        test_user,
        test_copy_config
    ):
        """Test deleting a copy configuration."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.delete(
            f"/api/copies/{test_copy_config.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify deletion
        response = await client.get(
            f"/api/copies/{test_copy_config.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_copy_not_found(self, client: AsyncClient, test_user):
        """Test deleting non-existent copy configuration."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.delete(
            f"/api/copies/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_copy_with_close_positions(
        self,
        client: AsyncClient,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test deleting copy config with close_positions=true closes open positions."""
        from app.models.position import CopiedPosition

        # Create an open position linked to the copy config
        position = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="test-market-delete",
            market_name="Delete Test Market?",
            trader_address=test_copy_config.trader_address,
            side="YES",
            size=Decimal("50.00"),
            entry_price=Decimal("0.50"),
            current_price=Decimal("0.50"),
            pnl=Decimal("0"),
            pnl_percentage=Decimal("0"),
            status="open",
        )
        test_db.add(position)
        await test_db.commit()
        await test_db.refresh(position)
        position_id = position.id

        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.delete(
            f"/api/copies/{test_copy_config.id}?close_positions=true",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify the position was closed
        from sqlalchemy import select
        result = await test_db.execute(
            select(CopiedPosition).where(CopiedPosition.id == position_id)
        )
        updated_position = result.scalar_one_or_none()

        assert updated_position is not None
        assert updated_position.status == "closed"
        assert updated_position.close_reason == "config_deleted"

    @pytest.mark.asyncio
    async def test_delete_copy_without_close_positions_keeps_open(
        self,
        client: AsyncClient,
        test_db,
        test_user,
        test_trader
    ):
        """Test deleting copy config without close_positions keeps positions open."""
        from app.models.position import CopiedPosition

        # Create a new copy config for this test
        from app.models.copy_config import CopyConfig
        copy_config = CopyConfig(
            user_id=test_user.id,
            trader_address=test_trader.wallet_address,
            allocation=Decimal("500.00"),
            remaining_allocation=Decimal("500.00"),
            copy_ratio=Decimal("50.00"),
        )
        test_db.add(copy_config)
        await test_db.commit()
        await test_db.refresh(copy_config)

        # Create an open position
        position = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=copy_config.id,
            market_id="test-market-keep-open",
            market_name="Keep Open Test?",
            trader_address=copy_config.trader_address,
            side="YES",
            size=Decimal("50.00"),
            entry_price=Decimal("0.50"),
            current_price=Decimal("0.50"),
            pnl=Decimal("0"),
            pnl_percentage=Decimal("0"),
            status="open",
        )
        test_db.add(position)
        await test_db.commit()
        await test_db.refresh(position)
        position_id = position.id

        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        # Delete WITHOUT close_positions
        response = await client.delete(
            f"/api/copies/{copy_config.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify the position is still open
        from sqlalchemy import select
        result = await test_db.execute(
            select(CopiedPosition).where(CopiedPosition.id == position_id)
        )
        updated_position = result.scalar_one_or_none()

        assert updated_position is not None
        assert updated_position.status == "open"

    @pytest.mark.asyncio
    async def test_get_copy_trades_empty(
        self,
        client: AsyncClient,
        test_user,
        test_copy_config
    ):
        """Test getting trades for a copy with no positions."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.get(
            f"/api/copies/{test_copy_config.id}/trades",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["positions"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_copy_trades_with_positions(
        self,
        client: AsyncClient,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test getting trades returns positions correctly."""
        from app.models.position import CopiedPosition

        # Create positions
        position1 = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="trade-market-1",
            market_name="Trade Market 1?",
            trader_address=test_copy_config.trader_address,
            side="YES",
            size=Decimal("50.00"),
            entry_price=Decimal("0.45"),
            current_price=Decimal("0.55"),
            pnl=Decimal("11.11"),
            pnl_percentage=Decimal("22.22"),
            status="open",
        )
        position2 = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="trade-market-2",
            market_name="Trade Market 2?",
            trader_address=test_copy_config.trader_address,
            side="NO",
            size=Decimal("75.00"),
            entry_price=Decimal("0.60"),
            current_price=Decimal("0.50"),
            pnl=Decimal("12.50"),
            pnl_percentage=Decimal("16.67"),
            status="closed",
        )
        test_db.add(position1)
        test_db.add(position2)
        await test_db.commit()

        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.get(
            f"/api/copies/{test_copy_config.id}/trades",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["positions"]) == 2

        # Verify position data is returned correctly
        market_ids = {p["market_id"] for p in data["positions"]}
        assert "trade-market-1" in market_ids
        assert "trade-market-2" in market_ids

        # Check one position's details
        pos1 = next(p for p in data["positions"] if p["market_id"] == "trade-market-1")
        assert pos1["side"] == "YES"
        assert Decimal(pos1["size"]) == Decimal("50.00")
        assert pos1["status"] == "open"

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test endpoints require authentication."""
        # No token
        response = await client.get("/api/copies")
        assert response.status_code == 401

        # Invalid token
        response = await client.get(
            "/api/copies",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


class TestCopyAPIValidation:
    """Validation tests for copy API."""

    @pytest.mark.asyncio
    async def test_create_copy_invalid_allocation(
        self,
        client: AsyncClient,
        test_user,
        test_trader
    ):
        """Test creating copy with invalid allocation fails."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.post(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trader_address": test_trader.wallet_address,
                "allocation": "-100.00",  # Negative allocation
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_copy_invalid_copy_ratio(
        self,
        client: AsyncClient,
        test_user,
        test_trader
    ):
        """Test creating copy with invalid copy ratio fails."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.post(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trader_address": test_trader.wallet_address,
                "allocation": "100.00",
                "copy_ratio": "150.00",  # Over 100%
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_copy_invalid_address(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test creating copy with invalid address fails."""
        token = AuthService.create_jwt(test_user.id, test_user.wallet_address)

        response = await client.post(
            "/api/copies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trader_address": "not-a-valid-address",
                "allocation": "100.00",
            }
        )

        assert response.status_code == 422
