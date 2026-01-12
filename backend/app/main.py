"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, traders_router, portfolio_router, copy_router, websocket_router
from app.services.trade_watcher import trade_watcher

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS for production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MetamonMarket API", env=settings.app_env)

    # Validate production settings
    settings.validate_production_settings()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Sentry if configured
    if settings.sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.app_env,
        )
        logger.info("Sentry initialized")

    # Start trade watcher background task
    import asyncio
    watcher_task = asyncio.create_task(
        trade_watcher.start(settings.database_url)
    )
    logger.info("Trade watcher started")

    yield

    # Stop trade watcher
    trade_watcher.stop()
    try:
        await asyncio.wait_for(watcher_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Trade watcher stop timed out")

    # Shutdown
    logger.info("Shutting down MetamonMarket API")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="MetamonMarket API",
    description="Copy-trading platform for Polymarket",
    version="1.0.0",
    docs_url="/api/docs" if settings.app_debug else None,
    redoc_url="/api/redoc" if settings.app_debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(auth_router)
app.include_router(traders_router)
app.include_router(portfolio_router)
app.include_router(copy_router)
app.include_router(websocket_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MetamonMarket API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.app_debug else None,
    }
