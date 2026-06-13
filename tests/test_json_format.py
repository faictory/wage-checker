import json
import io

from wage_checker.json_format import format_json
from wage_checker.reconcile import reconcile
from wage_checker.csv_input import parse_shifts
from wage_checker.dataset import load_dataset


class TestFormatJson:
    def test_format_json_3row_acceptance_example(self):
        # DESIGN example: verify exact numbers match text report
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0
2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00,shift-3,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0')
        obj = json.loads(json_str)

        # Verify required_pay for first shift
        assert obj['shifts'][0]['required_pay'] == 176.46
        # Verify total_shortfall
        assert obj['summary']['total_shortfall'] == 130.71
        # Verify dataset_version
        assert obj['dataset_version'] == '2026.1.0'

    def test_format_json_dataset_version(self):
        # Verify dataset_version is correctly set
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0')
        obj = json.loads(json_str)

        assert obj['dataset_version'] == '2026.1.0'

    def test_format_json_summary_only_true(self):
        # summary_only=True should omit 'shifts' key
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0', summary_only=True)
        obj = json.loads(json_str)

        assert 'shifts' not in obj
        assert 'dataset_version' in obj
        assert 'summary' in obj

    def test_format_json_parseable(self):
        # Output string must be json.loads-parseable
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0')
        # Should not raise
        obj = json.loads(json_str)
        assert isinstance(obj, dict)

    def test_format_json_all_shift_keys_present(self):
        # Verify all required shift keys are present
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0')
        obj = json.loads(json_str)

        shift = obj['shifts'][0]
        required_keys = {
            'row', 'shift_id', 'date', 'jurisdiction',
            'regular_hours', 'overtime_hours', 'min_rate', 'overtime_multiplier',
            'required_pay', 'pay_received', 'shortfall', 'status'
        }
        assert set(shift.keys()) == required_keys

    def test_format_json_all_summary_keys_present(self):
        # Verify all required summary keys are present
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0')
        obj = json.loads(json_str)

        required_keys = {
            'shift_count', 'total_hours', 'total_required',
            'total_paid', 'total_shortfall', 'underpaid_count'
        }
        assert set(obj['summary'].keys()) == required_keys

    def test_format_json_numeric_conversion(self):
        # Verify Decimals are converted to floats for JSON
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        json_str = format_json(shift_results, summary, '2026.1.0')
        obj = json.loads(json_str)

        # All numeric fields should be floats (not Decimal)
        assert isinstance(obj['shifts'][0]['regular_hours'], float)
        assert isinstance(obj['shifts'][0]['min_rate'], float)
        assert isinstance(obj['summary']['total_hours'], float)
        assert isinstance(obj['summary']['total_shortfall'], float)
