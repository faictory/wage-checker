from decimal import Decimal
import io

import pytest

from wage_checker.reconcile import shortfall, reconcile
from wage_checker.csv_input import parse_shifts
from wage_checker.dataset import load_dataset


class TestShortfall:
    def test_shortfall_happy_path(self):
        # required > paid → returns difference
        required = Decimal('100.50')
        paid = Decimal('75.00')
        assert shortfall(required, paid) == Decimal('25.50')

    def test_shortfall_non_negative_invariant(self):
        # paid >= required → returns Decimal('0.00')
        required = Decimal('100.00')
        paid = Decimal('125.00')
        assert shortfall(required, paid) == Decimal('0.00')

    def test_shortfall_paid_equal_required(self):
        # paid == required → returns Decimal('0.00')
        required = Decimal('100.00')
        paid = Decimal('100.00')
        assert shortfall(required, paid) == Decimal('0.00')

    def test_shortfall_rounding_half_up(self):
        # Test that ROUND_HALF_UP is applied
        required = Decimal('100.005')
        paid = Decimal('0')
        result = shortfall(required, paid)
        assert result == Decimal('100.01')

    def test_shortfall_accepts_numeric_types(self):
        # Should accept int, float, str, Decimal and convert properly
        assert shortfall(100, 50) == Decimal('50.00')
        assert shortfall('100.50', '75.00') == Decimal('25.50')
        assert shortfall(Decimal('100'), Decimal('50')) == Decimal('50.00')


class TestReconcile:
    def test_reconcile_3row_acceptance_example(self):
        # The spec's 3-row example with exact value verification
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0
2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00,shift-3,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))

        shift_results, summary = reconcile(records, dataset)

        assert len(shift_results) == 3
        assert shift_results[0]['required_pay'] == Decimal('176.46')
        assert shift_results[1]['required_pay'] == Decimal('206.25')
        assert shift_results[2]['required_pay'] == Decimal('58.00')

        assert shift_results[0]['shortfall'] == Decimal('56.46')
        assert shift_results[1]['shortfall'] == Decimal('56.25')
        assert shift_results[2]['shortfall'] == Decimal('18.00')

        assert all(r['status'] == 'UNDERPAID' for r in shift_results)

        assert summary['shift_count'] == 3
        assert summary['total_required'] == Decimal('440.71')
        assert summary['total_paid'] == Decimal('310.00')
        assert summary['total_shortfall'] == Decimal('130.71')
        assert summary['underpaid_count'] == 3

    def test_reconcile_compliant_shift(self):
        # Compliant shift (pay >= required) → shortfall=Decimal('0.00') and status='OK'
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,176.46,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))

        shift_results, summary = reconcile(records, dataset)

        assert len(shift_results) == 1
        assert shift_results[0]['shortfall'] == Decimal('0.00')
        assert shift_results[0]['status'] == 'OK'
        assert summary['underpaid_count'] == 0

    def test_reconcile_unknown_jurisdiction_error(self):
        # Unknown jurisdiction → re-raise as ValueError(f"row {n}: ...")
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,UNKNOWN-JURISDICTION,100.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))

        with pytest.raises(ValueError) as exc_info:
            reconcile(records, dataset)

        error_msg = str(exc_info.value)
        assert 'row 1:' in error_msg
        assert 'unknown jurisdiction' in error_msg.lower()

    def test_reconcile_weekly_overtime_accumulation(self):
        # Test that weekly hours accumulate across shifts in same week
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:00,US-CA,0,shift-1,0
2026-01-06T09:00,2026-01-06T17:00,US-CA,0,shift-2,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))

        shift_results, summary = reconcile(records, dataset)

        assert len(shift_results) == 2
        # First shift: 8h regular (no weekly threshold hit yet)
        assert shift_results[0]['regular_hours'] == Decimal('8')
        assert shift_results[0]['overtime_hours'] == Decimal('0')
        # Second shift: 8h, but with 8h prior → should go toward weekly threshold
        # US-CA has 40h weekly threshold, so 8+8=16 so far, still under 40
        assert shift_results[1]['regular_hours'] == Decimal('8')
        assert shift_results[1]['overtime_hours'] == Decimal('0')

    def test_reconcile_mixed_status(self):
        # Some shifts compliant, some underpaid
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,176.46,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))

        shift_results, summary = reconcile(records, dataset)

        assert shift_results[0]['status'] == 'OK'
        assert shift_results[1]['status'] == 'UNDERPAID'
        assert summary['underpaid_count'] == 1
        assert summary['shift_count'] == 2
