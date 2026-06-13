from decimal import Decimal, ROUND_HALF_UP
from .hours import compute_hours
from .overtime import apply_overtime
from .dataset import select_rate


def shortfall(required, paid):
    """
    Calculate the pay shortfall between required and paid amounts.

    Args:
        required: Decimal amount required by law
        paid: Decimal amount actually paid

    Returns:
        Decimal: max(0, required - paid) rounded to cents with ROUND_HALF_UP
    """
    required = Decimal(str(required))
    paid = Decimal(str(paid))
    diff = required - paid
    return max(Decimal('0'), diff).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def reconcile(records, dataset):
    """
    Reconcile shift records against a minimum wage dataset.

    Groups records by (jurisdiction, ISO-week) to accumulate weekly hours,
    then for each shift computes regular/overtime hours, required pay, and shortfall.

    Args:
        records: List of parsed shift records from csv_input.parse_shifts
        dataset: Loaded dataset dict from dataset.load_dataset

    Returns:
        Tuple of (shift_results, summary) where:
        - shift_results: List of dicts with per-shift data
        - summary: Dict with aggregate totals
    """
    shift_results = []
    week_hours_map = {}

    for record in records:
        row = record['row']
        shift_id = record['shift_id']
        clock_in = record['clock_in']
        clock_out = record['clock_out']
        jurisdiction = record['jurisdiction']
        pay_received = Decimal(str(record['pay_received']))
        break_minutes = record.get('break_minutes', 0)

        effective_date = clock_in.date()

        try:
            min_rate, ot_config = select_rate(dataset, jurisdiction, effective_date)
        except ValueError as e:
            raise ValueError(f"row {row}: {str(e)}") from e

        worked_hours = compute_hours(clock_in, clock_out, break_minutes)

        iso_year, iso_week = clock_in.isocalendar()[:2]
        week_key = (jurisdiction, iso_year, iso_week)

        week_hours_prior = week_hours_map.get(week_key, Decimal('0'))

        daily_threshold = ot_config.get('daily_threshold')
        weekly_threshold = ot_config.get('weekly_threshold')

        regular_hours, overtime_hours = apply_overtime(
            worked_hours,
            daily_threshold,
            weekly_threshold,
            week_hours_prior
        )

        week_hours_map[week_key] = week_hours_prior + worked_hours

        multiplier = Decimal(str(ot_config['multiplier']))
        required_pay = (
            (regular_hours * min_rate) + (overtime_hours * min_rate * multiplier)
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        shortfall_amount = shortfall(required_pay, pay_received)
        status = 'UNDERPAID' if shortfall_amount > Decimal('0') else 'OK'

        shift_result = {
            'row': row,
            'shift_id': shift_id,
            'date': effective_date.isoformat(),
            'jurisdiction': jurisdiction,
            'regular_hours': regular_hours,
            'overtime_hours': overtime_hours,
            'min_rate': min_rate,
            'overtime_multiplier': multiplier,
            'required_pay': required_pay,
            'pay_received': pay_received,
            'shortfall': shortfall_amount,
            'status': status,
        }

        shift_results.append(shift_result)

    total_hours = sum(
        r['regular_hours'] + r['overtime_hours'] for r in shift_results
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    total_required = sum(r['required_pay'] for r in shift_results).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    total_paid = sum(r['pay_received'] for r in shift_results).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    total_shortfall = sum(r['shortfall'] for r in shift_results).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    underpaid_count = sum(1 for r in shift_results if r['status'] == 'UNDERPAID')

    summary = {
        'shift_count': len(shift_results),
        'total_hours': total_hours,
        'total_required': total_required,
        'total_paid': total_paid,
        'total_shortfall': total_shortfall,
        'underpaid_count': underpaid_count,
    }

    return (shift_results, summary)
