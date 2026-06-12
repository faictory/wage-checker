from decimal import Decimal, ROUND_HALF_UP


def compute_hours(clock_in, clock_out, break_minutes=0):
    """
    Convert a shift's clock-in/clock-out and unpaid break into worked hours.

    Args:
        clock_in: datetime.datetime object for shift start
        clock_out: datetime.datetime object for shift end
        break_minutes: int, unpaid break in minutes (default 0)

    Returns:
        Decimal: worked hours rounded to 2 decimal places using ROUND_HALF_UP
    """
    total_minutes = (clock_out - clock_in).total_seconds() / 60
    worked_minutes = total_minutes - break_minutes
    worked_hours = Decimal(str(worked_minutes)) / Decimal('60')
    return worked_hours.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
