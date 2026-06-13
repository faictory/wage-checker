from decimal import Decimal
from wage_checker.overtime import apply_overtime


def test_daily_overtime_split():
    """Test hours above daily threshold are split into overtime."""
    regular, overtime = apply_overtime(
        shift_hours=11,
        daily_threshold=8,
        weekly_threshold=40,
        week_hours_prior=0,
    )
    assert regular == Decimal('8')
    assert overtime == Decimal('3')


def test_weekly_overtime_split():
    """Test hours pushing cumulative week hours above weekly threshold are split."""
    regular, overtime = apply_overtime(
        shift_hours=10,
        daily_threshold=None,
        weekly_threshold=40,
        week_hours_prior=35,
    )
    assert regular == Decimal('5')
    assert overtime == Decimal('5')


def test_no_overtime():
    """Test hours under both thresholds result in zero overtime."""
    regular, overtime = apply_overtime(
        shift_hours=6,
        daily_threshold=8,
        weekly_threshold=40,
        week_hours_prior=0,
    )
    assert regular == Decimal('6')
    assert overtime == Decimal('0')
