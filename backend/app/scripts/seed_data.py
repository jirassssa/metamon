"""Seed script to populate database with sample data."""

import asyncio
import random
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory, init_db
from app.models.trader import Trader


# Sample wallet addresses for testing
SAMPLE_WALLETS = [
    "0x742d35cc6634c0532925a3b844bc9e7595f5a5e4",
    "0x1234567890abcdef1234567890abcdef12345678",
    "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    "0xabcdef1234567890abcdef1234567890abcdef12",
    "0x9876543210fedcba9876543210fedcba98765432",
    "0xfeedfacefeedfacefeedfacefeedfacefeedface",
    "0xcafebabecafebabecafebabecafebabecafebabe",
    "0x0123456789abcdef0123456789abcdef01234567",
    "0xfedcba9876543210fedcba9876543210fedcba98",
    "0xbeefbeefbeefbeefbeefbeefbeefbeefbeefbeef",
]

RISK_SCORES = ["Low", "Medium", "High"]


async def create_sample_traders(db: AsyncSession) -> list[Trader]:
    """Create sample traders with realistic data."""
    traders = []

    for i, wallet in enumerate(SAMPLE_WALLETS):
        # Generate realistic trading stats
        total_trades = random.randint(50, 500)
        win_rate = Decimal(str(random.uniform(45, 75))).quantize(Decimal("0.01"))
        roi = Decimal(str(random.uniform(-20, 150))).quantize(Decimal("0.01"))
        total_volume = Decimal(str(random.uniform(10000, 500000))).quantize(Decimal("0.01"))
        portfolio_value = Decimal(str(random.uniform(5000, 100000))).quantize(Decimal("0.01"))
        followers_count = random.randint(0, 100)

        # Assign risk score based on ROI and win rate
        if roi > 50 and win_rate > 55:
            risk_score = "Low"
        elif roi > 20 or win_rate > 50:
            risk_score = "Medium"
        else:
            risk_score = "High"

        trader = Trader(
            wallet_address=wallet,
            total_trades=total_trades,
            win_rate=win_rate,
            roi=roi,
            total_volume=total_volume,
            portfolio_value=portfolio_value,
            followers_count=followers_count,
            risk_score=risk_score,
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
            updated_at=datetime.utcnow(),
        )
        traders.append(trader)

    db.add_all(traders)
    await db.commit()

    print(f"Created {len(traders)} sample traders")
    return traders


async def main():
    """Main seed function."""
    print("Initializing database...")
    await init_db()

    async with async_session_factory() as db:
        # Check if data already exists
        from sqlalchemy import select
        result = await db.execute(select(Trader).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            print("Sample data already exists. Skipping seed.")
            return

        print("Seeding database with sample data...")
        await create_sample_traders(db)

    print("Seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
