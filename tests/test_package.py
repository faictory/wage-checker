from datetime import datetime
from decimal import Decimal

import wage_checker
from wage_checker.hours import compute_hours
from wage_checker.overtime import apply_overtime


def test_version():
    assert wage_checker.__version__ == "0.1.0"


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


def test_apply_overtime_acceptance_1():
    # shift_hours=11, daily_threshold=8, weekly_threshold=40, week_hours_prior=0
    # → (Decimal('8'), Decimal('3'))
    regular, overtime = apply_overtime(11, 8, 40, Decimal('0'))
    assert regular == Decimal('8')
    assert overtime == Decimal('3')


def test_apply_overtime_acceptance_2():
    # shift_hours=10, daily_threshold=None, weekly_threshold=40, week_hours_prior=35
    # → (Decimal('5'), Decimal('5'))
    regular, overtime = apply_overtime(10, None, 40, Decimal('35'))
    assert regular == Decimal('5')
    assert overtime == Decimal('5')


def test_apply_overtime_acceptance_3():
    # shift_hours=6, daily_threshold=8, weekly_threshold=40, week_hours_prior=0
    # → (Decimal('6'), Decimal('0'))
    regular, overtime = apply_overtime(6, 8, 40, Decimal('0'))
    assert regular == Decimal('6')
    assert overtime == Decimal('0')
