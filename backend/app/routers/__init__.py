"""API routers."""

from app.routers.auth import router as auth_router
from app.routers.traders import router as traders_router
from app.routers.portfolio import router as portfolio_router
from app.routers.copy import router as copy_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "traders_router",
    "portfolio_router",
    "copy_router",
    "websocket_router",
]
