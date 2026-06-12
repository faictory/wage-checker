from decimal import Decimal


def apply_overtime(shift_hours, daily_threshold, weekly_threshold, week_hours_prior=Decimal('0')):
    """
    Split a shift's worked hours into regular vs overtime hours under daily and weekly overtime rules.

    Args:
        shift_hours: Decimal, hours worked in this shift
        daily_threshold: number or None, daily hours threshold for overtime
        weekly_threshold: number or None, weekly hours threshold for overtime
        week_hours_prior: Decimal, hours worked in the week before this shift (default 0)

    Returns:
        tuple of (regular_hours, overtime_hours) as Decimals that sum to shift_hours
    """
    # Convert thresholds to Decimal
    if daily_threshold is not None:
        daily_threshold = Decimal(str(daily_threshold))
    if weekly_threshold is not None:
        weekly_threshold = Decimal(str(weekly_threshold))

    # Ensure shift_hours and week_hours_prior are Decimals
    shift_hours = Decimal(str(shift_hours))
    week_hours_prior = Decimal(str(week_hours_prior))

    # Calculate daily overtime
    if daily_threshold is not None:
        daily_overtime = max(Decimal('0'), shift_hours - daily_threshold)
    else:
        daily_overtime = Decimal('0')

    # Calculate weekly overtime
    if weekly_threshold is not None:
        # weekly_overtime = clamp(0, (week_hours_prior + shift_hours) - weekly_threshold, shift_hours)
        cumulative_hours = week_hours_prior + shift_hours
        hours_over_threshold = cumulative_hours - weekly_threshold
        weekly_overtime = max(Decimal('0'), min(hours_over_threshold, shift_hours))
    else:
        weekly_overtime = Decimal('0')

    # overtime_hours is the maximum of daily and weekly overtime
    overtime_hours = max(daily_overtime, weekly_overtime)

    # regular_hours is the remainder
    regular_hours = shift_hours - overtime_hours

    return (regular_hours, overtime_hours)
