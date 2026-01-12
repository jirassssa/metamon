"""Unit tests for copy service."""

from decimal import Decimal

import pytest

from app.services.copy_service import CopyService


class TestCopyServiceCalculations:
    """Tests for CopyService calculation methods."""

    def test_calculate_remaining_allocation_increase(self):
        """Test remaining allocation calculation when allocation increases."""
        # Current: 1000 total, 600 remaining (400 used)
        # New: 1500 total -> 1500 - 400 = 1100 remaining
        result = CopyService.calculate_remaining_allocation_on_update(
            current_allocation=Decimal("1000.00"),
            current_remaining=Decimal("600.00"),
            new_allocation=Decimal("1500.00")
        )
        assert result == Decimal("1100.00")

    def test_calculate_remaining_allocation_decrease(self):
        """Test remaining allocation calculation when allocation decreases."""
        # Current: 1000 total, 600 remaining (400 used)
        # New: 800 total -> 800 - 400 = 400 remaining
        result = CopyService.calculate_remaining_allocation_on_update(
            current_allocation=Decimal("1000.00"),
            current_remaining=Decimal("600.00"),
            new_allocation=Decimal("800.00")
        )
        assert result == Decimal("400.00")

    def test_calculate_remaining_allocation_decrease_below_used(self):
        """Test remaining allocation floors at zero."""
        # Current: 1000 total, 200 remaining (800 used)
        # New: 500 total -> 500 - 800 = -300, should floor at 0
        result = CopyService.calculate_remaining_allocation_on_update(
            current_allocation=Decimal("1000.00"),
            current_remaining=Decimal("200.00"),
            new_allocation=Decimal("500.00")
        )
        assert result == Decimal("0")

    def test_calculate_remaining_allocation_no_change(self):
        """Test remaining allocation when allocation unchanged."""
        result = CopyService.calculate_remaining_allocation_on_update(
            current_allocation=Decimal("1000.00"),
            current_remaining=Decimal("600.00"),
            new_allocation=Decimal("1000.00")
        )
        assert result == Decimal("600.00")

    def test_calculate_remaining_allocation_all_remaining(self):
        """Test when all allocation is still remaining (nothing used)."""
        # Current: 1000 total, 1000 remaining (0 used)
        # New: 500 total -> 500 - 0 = 500 remaining
        result = CopyService.calculate_remaining_allocation_on_update(
            current_allocation=Decimal("1000.00"),
            current_remaining=Decimal("1000.00"),
            new_allocation=Decimal("500.00")
        )
        assert result == Decimal("500.00")
