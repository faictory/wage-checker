from datetime import datetime
from decimal import Decimal

import shift_pay_reconciler
from shift_pay_reconciler.hours import compute_hours


def test_version():
    assert shift_pay_reconciler.__version__ == "0.1.0"


def test_compute_hours_same_day_no_break():
    clock_in = datetime(2026, 1, 5, 9, 0)
    clock_out = datetime(2026, 1, 5, 17, 30)
    assert compute_hours(clock_in, clock_out, 0) == Decimal('8.50')


def test_compute_hours_overnight():
    clock_in = datetime(2026, 1, 5, 22, 0)
    clock_out = datetime(2026, 1, 6, 6, 0)
    assert compute_hours(clock_in, clock_out, 0) == Decimal('8.00')


def test_compute_hours_with_break():
    clock_in = datetime(2026, 1, 5, 9, 0)
    clock_out = datetime(2026, 1, 5, 17, 0)
    assert compute_hours(clock_in, clock_out, 30) == Decimal('7.50')
