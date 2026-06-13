from decimal import Decimal
from datetime import datetime
from wage_checker.hours import compute_hours


def test_normal_same_day_shift():
    """Test a normal same-day shift produces expected Decimal hours."""
    clock_in = datetime(2026, 1, 5, 9, 0)
    clock_out = datetime(2026, 1, 5, 17, 30)
    result = compute_hours(clock_in, clock_out)
    assert result == Decimal('8.50')


def test_overnight_cross_midnight_shift():
    """Test an overnight cross-midnight shift produces correct hours."""
    clock_in = datetime(2026, 1, 5, 22, 0)
    clock_out = datetime(2026, 1, 6, 6, 0)
    result = compute_hours(clock_in, clock_out)
    assert result == Decimal('8.00')


def test_shift_with_break_minutes():
    """Test that break_minutes deducts correctly from hours."""
    clock_in = datetime(2026, 1, 5, 9, 0)
    clock_out = datetime(2026, 1, 5, 17, 0)
    result = compute_hours(clock_in, clock_out, break_minutes=30)
    assert result == Decimal('7.50')
