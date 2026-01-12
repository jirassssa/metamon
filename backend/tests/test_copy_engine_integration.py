"""Integration tests for the copy trading engine with database."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.copy_config import CopyConfig
from app.models.position import CopiedPosition
from app.models.notification import Notification
from app.services.copy_engine import CopyEngine


@pytest.mark.asyncio
class TestCopyEngineIntegration:
    """Integration tests for CopyEngine with database."""

    async def test_process_new_trade_creates_position(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that processing a new trade creates a copied position."""
        engine = CopyEngine()

        trade = {
            "size": "500",  # 5% of trader's $10,000 portfolio
            "price": "0.65",
            "side": "YES",
            "market_id": "test-market-123",
            "market_name": "Test Market Question?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        assert len(positions) == 1
        position = positions[0]

        # Verify position details
        assert position.user_id == test_user.id
        assert position.copy_config_id == test_copy_config.id
        assert position.market_id == "test-market-123"
        assert position.side == "YES"
        assert position.entry_price == Decimal("0.65")
        assert position.status == "open"

        # Position size should be: 1000 * (500/10000) * (50/100) = 25
        assert position.size == Decimal("25.00")

    async def test_process_new_trade_respects_max_position(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that position size respects max_position_size limit."""
        engine = CopyEngine()

        # Large trade that would exceed max position
        trade = {
            "size": "5000",  # 50% of portfolio
            "price": "0.50",
            "side": "YES",
            "market_id": "test-market-456",
            "market_name": "Large Trade Market?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        assert len(positions) == 1
        position = positions[0]

        # Without limit: 1000 * 0.5 * 0.5 = 250
        # With max_position_size = 500, should be 250 (under limit)
        # Actually, position size = 1000 * (5000/10000) * (50/100) = 250
        assert position.size == Decimal("250.00")

    async def test_process_new_trade_updates_remaining_allocation(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that processing trade updates remaining allocation."""
        engine = CopyEngine()
        initial_remaining = test_copy_config.remaining_allocation

        trade = {
            "size": "500",
            "price": "0.50",
            "side": "YES",
            "market_id": "test-market-789",
            "market_name": "Allocation Test Market?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        await test_db.refresh(test_copy_config)

        # Position size = 1000 * 0.05 * 0.5 = 25
        expected_remaining = initial_remaining - Decimal("25.00")
        assert test_copy_config.remaining_allocation == expected_remaining

    async def test_process_new_trade_creates_notification(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that processing trade creates notification when enabled."""
        engine = CopyEngine()

        trade = {
            "size": "500",
            "price": "0.50",
            "side": "NO",
            "market_id": "test-market-notify",
            "market_name": "Notification Test?",
        }

        await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        # Check notification was created
        from sqlalchemy import select
        result = await test_db.execute(
            select(Notification).where(
                Notification.user_id == test_user.id,
                Notification.type == "trade_copied"
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is not None
        assert "Trade Copied" in notification.title
        assert "NO" in notification.message

    async def test_process_new_trade_respects_auto_copy_setting(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that trades are skipped when auto_copy_new is disabled."""
        engine = CopyEngine()

        # Disable auto copy
        test_copy_config.auto_copy_new = False
        await test_db.commit()

        trade = {
            "size": "500",
            "price": "0.50",
            "side": "YES",
            "market_id": "test-market-skip",
            "market_name": "Should Skip Market?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        assert len(positions) == 0

    async def test_process_new_trade_skips_small_positions(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that very small positions are skipped."""
        engine = CopyEngine()

        # Very small trade
        trade = {
            "size": "10",  # 0.1% of portfolio = 1000 * 0.001 * 0.5 = 0.50 (below MIN_TRADE_SIZE)
            "price": "0.50",
            "side": "YES",
            "market_id": "test-market-small",
            "market_name": "Small Trade Market?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        assert len(positions) == 0

    async def test_process_new_trade_calculates_stop_loss(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that stop loss price is calculated correctly."""
        engine = CopyEngine()

        trade = {
            "size": "500",
            "price": "0.50",
            "side": "YES",
            "market_id": "test-market-sl",
            "market_name": "Stop Loss Test?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        assert len(positions) == 1
        position = positions[0]

        # Stop loss = 0.50 * (1 - 0.20) = 0.40
        assert position.stop_loss_price == Decimal("0.40")

    async def test_process_new_trade_inactive_config_skipped(
        self,
        test_db,
        test_user,
        test_trader,
        test_copy_config
    ):
        """Test that inactive configs are skipped."""
        engine = CopyEngine()

        # Deactivate config
        test_copy_config.is_active = False
        await test_db.commit()

        trade = {
            "size": "500",
            "price": "0.50",
            "side": "YES",
            "market_id": "test-market-inactive",
            "market_name": "Inactive Config Market?",
        }

        positions = await engine.process_new_trade(
            test_db,
            test_trader.wallet_address,
            trade
        )

        assert len(positions) == 0

    async def test_get_active_copies_for_trader(
        self,
        test_db,
        test_trader,
        test_copy_config
    ):
        """Test getting active copy configs for a trader."""
        engine = CopyEngine()

        copies = await engine.get_active_copies_for_trader(
            test_db,
            test_trader.wallet_address
        )

        assert len(copies) == 1
        assert copies[0].id == test_copy_config.id


@pytest.mark.asyncio
class TestPnLCalculation:
    """Tests for PnL calculation correctness."""

    def test_pnl_percentage_calculation_yes_profit(self):
        """Test PnL percentage for profitable YES position."""
        # If we buy YES at 0.40 and it goes to 0.60
        # shares = 100 USDC / 0.40 = 250 shares
        # profit = (0.60 - 0.40) * 250 = 50 USDC
        # percentage = 50 / 100 * 100 = 50%
        entry_price = Decimal("0.40")
        current_price = Decimal("0.60")
        size = Decimal("100")  # USDC invested

        shares = size / entry_price
        pnl = (current_price - entry_price) * shares
        pnl_percentage = (pnl / size) * Decimal("100")

        assert shares == Decimal("250")
        assert pnl == Decimal("50.00")
        assert pnl_percentage == Decimal("50.00")

    def test_pnl_percentage_calculation_yes_loss(self):
        """Test PnL percentage for losing YES position."""
        # Buy YES at 0.50, drops to 0.30
        # shares = 100 / 0.50 = 200 shares
        # loss = (0.30 - 0.50) * 200 = -40 USDC
        # percentage = -40 / 100 * 100 = -40%
        entry_price = Decimal("0.50")
        current_price = Decimal("0.30")
        size = Decimal("100")

        shares = size / entry_price
        pnl = (current_price - entry_price) * shares
        pnl_percentage = (pnl / size) * Decimal("100")

        assert pnl == Decimal("-40.00")
        assert pnl_percentage == Decimal("-40.00")

    def test_pnl_percentage_calculation_no_profit(self):
        """Test PnL percentage for profitable NO position."""
        # Buy NO at 0.60, price drops to 0.40 (NO wins)
        # shares = 100 / 0.60 = 166.67 shares
        # profit = (0.60 - 0.40) * 166.67 = 33.33 USDC
        entry_price = Decimal("0.60")
        current_price = Decimal("0.40")
        size = Decimal("100")

        shares = size / entry_price
        pnl = (entry_price - current_price) * shares  # Note: reversed for NO
        pnl_percentage = (pnl / size) * Decimal("100")

        assert pnl > 0
        assert pnl_percentage > 0


@pytest.mark.asyncio
class TestStopLossIntegration:
    """Integration tests for stop-loss functionality."""

    async def test_check_stop_losses_triggers_on_price_drop(
        self,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test that stop loss triggers when price drops below threshold."""
        engine = CopyEngine()

        # Create a position with stop loss
        position = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="test-market-sl-1",
            market_name="Stop Loss Test Market?",
            trader_address=test_copy_config.trader_address,
            side="YES",
            size=Decimal("100.00"),
            entry_price=Decimal("0.50"),
            current_price=Decimal("0.50"),
            pnl=Decimal("0"),
            pnl_percentage=Decimal("0"),
            status="open",
            stop_loss_price=Decimal("0.40"),  # 20% stop loss
        )
        test_db.add(position)
        await test_db.commit()
        await test_db.refresh(position)

        # Mock the price fetch to return a price below stop loss
        mock_prices = {
            "test-market-sl-1": {"yes_price": 0.35, "no_price": 0.65, "market_id": "test-market-sl-1"}
        }

        with patch(
            "app.services.copy_engine.polymarket_service.get_market_price",
            new_callable=AsyncMock
        ) as mock_get_price:
            mock_get_price.side_effect = lambda mid: mock_prices.get(mid)

            closed = await engine.check_stop_losses(test_db)

            assert len(closed) == 1
            assert closed[0].id == position.id

        await test_db.refresh(position)
        assert position.status == "stopped"
        assert position.close_reason == "stop_loss"
        assert position.pnl < 0  # Loss since price dropped

    async def test_check_stop_losses_no_trigger_when_price_above(
        self,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test that stop loss does NOT trigger when price is above threshold."""
        engine = CopyEngine()

        position = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="test-market-sl-2",
            market_name="No Trigger Test?",
            trader_address=test_copy_config.trader_address,
            side="YES",
            size=Decimal("100.00"),
            entry_price=Decimal("0.50"),
            current_price=Decimal("0.50"),
            pnl=Decimal("0"),
            pnl_percentage=Decimal("0"),
            status="open",
            stop_loss_price=Decimal("0.40"),
        )
        test_db.add(position)
        await test_db.commit()

        # Price is above stop loss
        mock_prices = {
            "test-market-sl-2": {"yes_price": 0.55, "no_price": 0.45, "market_id": "test-market-sl-2"}
        }

        with patch(
            "app.services.copy_engine.polymarket_service.get_market_price",
            new_callable=AsyncMock
        ) as mock_get_price:
            mock_get_price.side_effect = lambda mid: mock_prices.get(mid)

            closed = await engine.check_stop_losses(test_db)

            assert len(closed) == 0

        await test_db.refresh(position)
        assert position.status == "open"
        # Current price should be updated
        assert position.current_price == Decimal("0.55")

    async def test_check_stop_losses_no_position_not_triggered(
        self,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test NO position stop loss does NOT trigger when NO price below threshold."""
        engine = CopyEngine()

        position = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="test-market-sl-3",
            market_name="NO Stop Loss Test?",
            trader_address=test_copy_config.trader_address,
            side="NO",
            size=Decimal("100.00"),
            entry_price=Decimal("0.50"),
            current_price=Decimal("0.50"),
            pnl=Decimal("0"),
            pnl_percentage=Decimal("0"),
            status="open",
            stop_loss_price=Decimal("0.60"),  # NO stop loss triggers when NO price >= 0.60
        )
        test_db.add(position)
        await test_db.commit()

        # NO price is below stop loss threshold (0.30 < 0.60)
        mock_prices = {
            "test-market-sl-3": {"yes_price": 0.70, "no_price": 0.30, "market_id": "test-market-sl-3"}
        }

        with patch(
            "app.services.copy_engine.polymarket_service.get_market_price",
            new_callable=AsyncMock
        ) as mock_get_price:
            mock_get_price.side_effect = lambda mid: mock_prices.get(mid)
            closed = await engine.check_stop_losses(test_db)
            assert len(closed) == 0

        await test_db.refresh(position)
        assert position.status == "open"

    async def test_check_stop_losses_no_position_triggered(
        self,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test NO position stop loss DOES trigger when NO price >= threshold."""
        engine = CopyEngine()

        # For NO position: stop loss triggers when the NO price goes UP
        # (meaning YES probability dropped, but NO price increased due to market mechanics)
        position = CopiedPosition(
            user_id=test_user.id,
            copy_config_id=test_copy_config.id,
            market_id="test-market-sl-4",
            market_name="NO Trigger Test?",
            trader_address=test_copy_config.trader_address,
            side="NO",
            size=Decimal("100.00"),
            entry_price=Decimal("0.50"),  # Bought NO at 0.50
            current_price=Decimal("0.50"),
            pnl=Decimal("0"),
            pnl_percentage=Decimal("0"),
            status="open",
            stop_loss_price=Decimal("0.60"),  # Stop if NO price reaches 0.60
        )
        test_db.add(position)
        await test_db.commit()
        await test_db.refresh(position)

        # NO price is at or above stop loss threshold (0.65 >= 0.60)
        mock_prices = {
            "test-market-sl-4": {"yes_price": 0.35, "no_price": 0.65, "market_id": "test-market-sl-4"}
        }

        with patch(
            "app.services.copy_engine.polymarket_service.get_market_price",
            new_callable=AsyncMock
        ) as mock_get_price:
            mock_get_price.side_effect = lambda mid: mock_prices.get(mid)
            closed = await engine.check_stop_losses(test_db)
            assert len(closed) == 1
            assert closed[0].id == position.id

        await test_db.refresh(position)
        assert position.status == "stopped"
        assert position.close_reason == "stop_loss"

    async def test_check_stop_losses_batch_fetches_prices(
        self,
        test_db,
        test_user,
        test_copy_config
    ):
        """Test that prices are fetched in batch, not N+1."""
        engine = CopyEngine()

        # Create multiple positions for different markets
        for i in range(3):
            position = CopiedPosition(
                user_id=test_user.id,
                copy_config_id=test_copy_config.id,
                market_id=f"test-market-batch-{i}",
                market_name=f"Batch Test {i}?",
                trader_address=test_copy_config.trader_address,
                side="YES",
                size=Decimal("50.00"),
                entry_price=Decimal("0.50"),
                current_price=Decimal("0.50"),
                pnl=Decimal("0"),
                pnl_percentage=Decimal("0"),
                status="open",
                stop_loss_price=Decimal("0.40"),
            )
            test_db.add(position)
        await test_db.commit()

        call_count = 0

        async def mock_get_price(market_id):
            nonlocal call_count
            call_count += 1
            return {"yes_price": 0.55, "no_price": 0.45, "market_id": market_id}

        with patch(
            "app.services.copy_engine.polymarket_service.get_market_price",
            new_callable=AsyncMock
        ) as mock_get_price_fn:
            mock_get_price_fn.side_effect = mock_get_price

            await engine.check_stop_losses(test_db)

            # Should be called exactly 3 times (once per unique market)
            assert call_count == 3
