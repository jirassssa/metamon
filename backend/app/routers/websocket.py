"""WebSocket router for real-time updates and copy trade notifications."""

import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import json

from app.database import get_db
from app.services.auth import AuthService
from app.services.copy_engine import CopyEngine
from app.services.trade_watcher import trade_watcher
from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition

router = APIRouter(prefix="/api/ws", tags=["websocket"])
logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections per user."""

    def __init__(self):
        # Map user_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info("WebSocket connected", user_id=user_id)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id)

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a user."""
        if user_id not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)

    async def broadcast_to_user(self, user_id: str, event_type: str, data: dict):
        """Broadcast an event to a user."""
        await self.send_to_user(user_id, {
            "type": event_type,
            "data": data,
        })


manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Dependency to get the connection manager."""
    return manager


@router.websocket("/positions")
async def websocket_positions(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time position updates.

    Connect with: ws://host/api/ws/positions?token=<jwt_token>

    Events sent:
    - position_update: When a position's PnL changes
    - position_opened: When a new position is copied
    - position_closed: When a position is closed
    - copy_updated: When copy config changes
    """
    # Validate token
    payload = AuthService.verify_jwt(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["user_id"]

    await manager.connect(websocket, user_id)

    try:
        # Send initial connection success
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to position updates"},
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for ping/pong or client messages
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user_id)


async def notify_position_update(
    user_id: str,
    position: CopiedPosition,
    event_type: str = "position_update"
):
    """Notify user of position update."""
    await manager.broadcast_to_user(user_id, event_type, {
        "position_id": str(position.id),
        "market_id": position.market_id,
        "market_name": position.market_name,
        "side": position.side,
        "size": str(position.size),
        "entry_price": str(position.entry_price),
        "current_price": str(position.current_price),
        "pnl": str(position.pnl),
        "pnl_percentage": str(position.pnl_percentage),
        "status": position.status,
    })


async def notify_copy_update(user_id: str, copy_config: CopyConfig):
    """Notify user of copy config update."""
    await manager.broadcast_to_user(user_id, "copy_updated", {
        "copy_id": str(copy_config.id),
        "trader_address": copy_config.trader_address,
        "is_active": copy_config.is_active,
        "remaining_allocation": str(copy_config.remaining_allocation),
        "total_pnl": str(copy_config.total_pnl),
    })


@router.websocket("/copy-trades")
async def websocket_copy_trades(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time copy trade notifications.

    Connect with: ws://host/api/ws/copy-trades?token=<jwt_token>

    Events sent to client:
    - connected: Initial connection success
    - pending_trades: List of pending copy trades
    - new_copy_trade: New trade detected from a copied trader
    - trade_status: Update on trade execution status

    Messages from client (JSON):
    - {"type": "get_pending"}: Request all pending trades
    - {"type": "execute_trade", "trade_id": "...", "tx_hash": "..."}: Mark trade as executed
    - {"type": "skip_trade", "trade_id": "..."}: Skip a pending trade
    - {"type": "ping"}: Keep-alive ping
    """
    # Validate token
    payload = AuthService.verify_jwt(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["user_id"]

    await websocket.accept()

    # Register with trade watcher for notifications
    trade_watcher.add_ws_connection(user_id, websocket)

    # Also register with regular manager
    await manager.connect(websocket, user_id)

    try:
        # Send initial pending trades
        pending = trade_watcher.get_pending_trades(user_id)
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to copy trade notifications"}
        })
        await websocket.send_json({
            "type": "pending_trades",
            "trades": [t.to_dict() for t in pending if t.status == "pending"]
        })

        while True:
            try:
                # Wait for messages
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )

                msg_type = data.get("type")

                if msg_type == "get_pending":
                    # Send all pending trades
                    pending = trade_watcher.get_pending_trades(user_id)
                    await websocket.send_json({
                        "type": "pending_trades",
                        "trades": [t.to_dict() for t in pending if t.status == "pending"]
                    })

                elif msg_type == "execute_trade":
                    # Mark trade as executed
                    trade_id = data.get("trade_id")
                    tx_hash = data.get("tx_hash")
                    success = trade_watcher.mark_trade_executed(user_id, trade_id, tx_hash)
                    await websocket.send_json({
                        "type": "trade_status",
                        "trade_id": trade_id,
                        "status": "executed" if success else "not_found",
                        "tx_hash": tx_hash
                    })

                elif msg_type == "skip_trade":
                    # Mark trade as skipped
                    trade_id = data.get("trade_id")
                    success = trade_watcher.mark_trade_skipped(user_id, trade_id)
                    await websocket.send_json({
                        "type": "trade_status",
                        "trade_id": trade_id,
                        "status": "skipped" if success else "not_found"
                    })

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error", user_id=user_id, error=str(e))
    finally:
        trade_watcher.remove_ws_connection(user_id, websocket)
        manager.disconnect(websocket, user_id)


@router.get("/copy-trades/pending")
async def get_pending_copy_trades(
    token: str = Query(..., description="JWT token")
):
    """
    REST endpoint to get pending copy trades.

    Alternative to WebSocket for getting pending trades.
    """
    payload = AuthService.verify_jwt(token)
    if not payload:
        return {"error": "Invalid token", "trades": [], "total": 0}

    user_id = payload["user_id"]
    pending = trade_watcher.get_pending_trades(user_id)
    active_trades = [t.to_dict() for t in pending if t.status == "pending"]

    return {
        "trades": active_trades,
        "total": len(active_trades)
    }
