"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, TraderProfile, CopyConfig, CopiedPosition


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        wallet_address="0x1234567890123456789012345678901234567890",
        nonce="test-nonce-12345",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_trader(test_db: AsyncSession) -> TraderProfile:
    """Create a test trader profile."""
    from decimal import Decimal

    trader = TraderProfile(
        wallet_address="0x0987654321098765432109876543210987654321",
        total_trades=100,
        win_rate=Decimal("75.5"),
        roi=Decimal("125.3"),
        total_volume=Decimal("50000.00"),
        portfolio_value=Decimal("10000.00"),
        followers_count=50,
        risk_score="Low",
    )
    test_db.add(trader)
    await test_db.commit()
    await test_db.refresh(trader)
    return trader


@pytest_asyncio.fixture
async def test_copy_config(
    test_db: AsyncSession,
    test_user: User,
    test_trader: TraderProfile
) -> CopyConfig:
    """Create a test copy configuration."""
    from decimal import Decimal

    config = CopyConfig(
        user_id=test_user.id,
        trader_address=test_trader.wallet_address,
        allocation=Decimal("1000.00"),
        remaining_allocation=Decimal("1000.00"),
        max_position_size=Decimal("500.00"),
        copy_ratio=Decimal("50.00"),
        stop_loss_percentage=Decimal("20.00"),
    )
    test_db.add(config)
    await test_db.commit()
    await test_db.refresh(config)
    return config


@pytest_asyncio.fixture
async def test_copied_position(
    test_db: AsyncSession,
    test_copy_config: CopyConfig
) -> CopiedPosition:
    """Create a test copied position."""
    from decimal import Decimal

    position = CopiedPosition(
        copy_config_id=test_copy_config.id,
        market_id="0x123abc",
        market_name="Will BTC reach $100k by 2025?",
        trader_address=test_copy_config.trader_address,
        side="YES",
        size=Decimal("100.00"),
        entry_price=Decimal("0.65"),
        current_price=Decimal("0.70"),
        pnl=Decimal("7.69"),
        pnl_percentage=Decimal("7.69"),
        status="open",
    )
    test_db.add(position)
    await test_db.commit()
    await test_db.refresh(position)
    return position
