"""Tests for the copy trading engine."""

from decimal import Decimal

import pytest

from app.services.copy_engine import CopyEngine


class TestCopyEngine:
    """Tests for CopyEngine class."""

    def test_calculate_position_size_basic(self):
        """Test basic position size calculation."""
        result = CopyEngine.calculate_position_size(
            allocation=Decimal("1000"),
            trader_portfolio_value=Decimal("10000"),
            trade_size=Decimal("1000"),  # 10% of portfolio
            copy_ratio=Decimal("100"),
        )
        # 1000 * (1000/10000) * (100/100) = 100
        assert result == Decimal("100.00")

    def test_calculate_position_size_with_ratio(self):
        """Test position size with copy ratio."""
        result = CopyEngine.calculate_position_size(
            allocation=Decimal("1000"),
            trader_portfolio_value=Decimal("10000"),
            trade_size=Decimal("1000"),  # 10% of portfolio
            copy_ratio=Decimal("50"),  # 50% copy ratio
        )
        # 1000 * (1000/10000) * (50/100) = 50
        assert result == Decimal("50.00")

    def test_calculate_position_size_respects_max_limit(self):
        """Test that position size respects max limit."""
        result = CopyEngine.calculate_position_size(
            allocation=Decimal("1000"),
            trader_portfolio_value=Decimal("10000"),
            trade_size=Decimal("5000"),  # 50% of portfolio
            copy_ratio=Decimal("100"),
            max_position_size=Decimal("200"),
        )
        # Without limit: 1000 * 0.5 * 1 = 500
        # With limit: capped at 200
        assert result == Decimal("200.00")

    def test_calculate_position_size_respects_remaining_allocation(self):
        """Test that position size respects remaining allocation."""
        result = CopyEngine.calculate_position_size(
            allocation=Decimal("1000"),
            trader_portfolio_value=Decimal("10000"),
            trade_size=Decimal("5000"),  # 50% of portfolio
            copy_ratio=Decimal("100"),
            remaining_allocation=Decimal("100"),
        )
        # Without limit: 500
        # With remaining limit: capped at 100
        assert result == Decimal("100.00")

    def test_calculate_position_size_zero_portfolio(self):
        """Test position size returns zero for zero portfolio value."""
        result = CopyEngine.calculate_position_size(
            allocation=Decimal("1000"),
            trader_portfolio_value=Decimal("0"),
            trade_size=Decimal("100"),
            copy_ratio=Decimal("100"),
        )
        assert result == Decimal("0")

    def test_calculate_stop_loss_price_yes(self):
        """Test stop loss price calculation for YES position."""
        result = CopyEngine.calculate_stop_loss_price(
            entry_price=Decimal("0.50"),
            side="YES",
            stop_loss_percentage=Decimal("20"),
        )
        # 0.50 * (1 - 0.20) = 0.40
        assert result == Decimal("0.40")

    def test_calculate_stop_loss_price_no(self):
        """Test stop loss price calculation for NO position."""
        result = CopyEngine.calculate_stop_loss_price(
            entry_price=Decimal("0.50"),
            side="NO",
            stop_loss_percentage=Decimal("20"),
        )
        # 0.50 * (1 + 0.20) = 0.60
        assert result == Decimal("0.60")

    def test_should_trigger_stop_loss_yes_triggered(self):
        """Test stop loss trigger for YES position when price drops."""
        result = CopyEngine.should_trigger_stop_loss(
            current_price=Decimal("0.35"),
            stop_loss_price=Decimal("0.40"),
            side="YES",
        )
        assert result is True

    def test_should_trigger_stop_loss_yes_not_triggered(self):
        """Test stop loss not triggered for YES when price above stop."""
        result = CopyEngine.should_trigger_stop_loss(
            current_price=Decimal("0.45"),
            stop_loss_price=Decimal("0.40"),
            side="YES",
        )
        assert result is False

    def test_should_trigger_stop_loss_no_triggered(self):
        """Test stop loss trigger for NO position when price rises."""
        result = CopyEngine.should_trigger_stop_loss(
            current_price=Decimal("0.65"),
            stop_loss_price=Decimal("0.60"),
            side="NO",
        )
        assert result is True

    def test_should_trigger_stop_loss_no_not_triggered(self):
        """Test stop loss not triggered for NO when price below stop."""
        result = CopyEngine.should_trigger_stop_loss(
            current_price=Decimal("0.55"),
            stop_loss_price=Decimal("0.60"),
            side="NO",
        )
        assert result is False
