"""WebSocket integration tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
import json

from app.main import app
from app.services.auth import AuthService
from app.routers.websocket import manager, notify_position_update


class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection_without_token(self):
        """Test WebSocket connection rejected without token."""
        client = TestClient(app)

        # WebSocket without token should be rejected
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/positions"):
                pass

    @pytest.mark.asyncio
    async def test_websocket_connection_with_invalid_token(self):
        """Test WebSocket connection rejected with invalid token."""
        client = TestClient(app)

        # WebSocket with invalid token should be rejected
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/positions?token=invalid"):
                pass

    @pytest.mark.asyncio
    async def test_websocket_connection_with_valid_token(self, test_db, test_user):
        """Test WebSocket connection accepted with valid token."""
        # Create a valid JWT
        token = AuthService.create_jwt(str(test_user.id), test_user.wallet_address)

        client = TestClient(app)

        with client.websocket_connect(f"/api/ws/positions?token={token}") as ws:
            # Should receive connected message
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert "Connected" in data["data"]["message"]

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, test_db, test_user):
        """Test WebSocket ping/pong mechanism."""
        token = AuthService.create_jwt(str(test_user.id), test_user.wallet_address)

        client = TestClient(app)

        with client.websocket_connect(f"/api/ws/positions?token={token}") as ws:
            # Receive connected message
            ws.receive_json()

            # Send ping
            ws.send_text("ping")

            # Should receive pong
            response = ws.receive_text()
            assert response == "pong"


class TestConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.mark.asyncio
    async def test_manager_tracks_connections(self, test_db, test_user):
        """Test that manager tracks user connections."""
        user_id = str(test_user.id)

        # Initially no connections
        assert user_id not in manager.active_connections

        # After connecting, connection should be tracked
        token = AuthService.create_jwt(str(test_user.id), test_user.wallet_address)
        client = TestClient(app)

        with client.websocket_connect(f"/api/ws/positions?token={token}") as ws:
            ws.receive_json()  # Consume connected message

            # Connection should be tracked
            assert user_id in manager.active_connections
            assert len(manager.active_connections[user_id]) == 1

        # After disconnect, connection should be removed
        assert user_id not in manager.active_connections or len(manager.active_connections[user_id]) == 0

    @pytest.mark.asyncio
    async def test_manager_send_to_user(self):
        """Test sending messages to specific users."""
        # Non-existent user should not raise
        await manager.send_to_user("non-existent-user", {"type": "test"})

    @pytest.mark.asyncio
    async def test_manager_broadcast_to_user(self):
        """Test broadcasting events to users."""
        # Non-existent user should not raise
        await manager.broadcast_to_user("non-existent-user", "test_event", {"key": "value"})


class TestWebSocketBroadcast:
    """Test WebSocket message broadcasting."""

    @pytest.mark.asyncio
    async def test_websocket_receives_position_update(
        self, test_db, test_user, test_copied_position
    ):
        """Test that a connected client receives broadcast position updates."""
        import asyncio

        token = AuthService.create_jwt(str(test_user.id), test_user.wallet_address)
        client = TestClient(app)

        with client.websocket_connect(f"/api/ws/positions?token={token}") as ws:
            # Consume connected message
            ws.receive_json()

            # Broadcast position update in background
            async def send_update():
                await asyncio.sleep(0.1)
                await notify_position_update(
                    user_id=str(test_user.id),
                    position=test_copied_position,
                    event_type="position_update"
                )

            # Run broadcast
            asyncio.get_event_loop().run_until_complete(send_update())

            # Receive the broadcast message
            data = ws.receive_json()
            assert data["type"] == "position_update"
            assert data["data"]["position_id"] == str(test_copied_position.id)
            assert data["data"]["market_name"] == test_copied_position.market_name
            assert data["data"]["side"] == "YES"
            assert data["data"]["status"] == "open"
