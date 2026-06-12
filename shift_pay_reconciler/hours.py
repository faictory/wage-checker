from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def compute_hours(clock_in: datetime, clock_out: datetime, break_minutes: int = 0) -> Decimal:
	total_minutes = (clock_out - clock_in).total_seconds() / 60
	worked_minutes = total_minutes - break_minutes
	worked_hours = Decimal(worked_minutes) / Decimal(60)
	return worked_hours.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
