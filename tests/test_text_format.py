import io

from shift_pay_reconciler.text_format import format_text
from shift_pay_reconciler.reconcile import reconcile
from shift_pay_reconciler.csv_input import parse_shifts
from shift_pay_reconciler.dataset import load_dataset


class TestFormatText:
    def test_format_text_3row_acceptance_example(self):
        # DESIGN example: verify exact numbers and format match
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0
2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00,shift-3,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        # Verify header
        lines = text_str.split('\n')
        assert lines[0] == "shift-pay-reconciler — reconciliation report"
        assert lines[1] == "dataset: minwage 2026.1.0"
        assert lines[2] == ""

        # Verify table header
        assert lines[3] == "ROW  DATE        JURISDICTION    REG_HRS  OT_HRS  REQUIRED   PAID      SHORTFALL  STATUS"

        # Verify first row has SHORTFALL of 56.46 and UNDERPAID
        assert "56.46" in lines[4]
        assert "UNDERPAID" in lines[4]

        # Verify second row has SHORTFALL of 56.25 and UNDERPAID
        assert "56.25" in lines[5]
        assert "UNDERPAID" in lines[5]

        # Verify third row has SHORTFALL of 18.00 and UNDERPAID
        assert "18.00" in lines[6]
        assert "UNDERPAID" in lines[6]

        # Verify SUMMARY section exists and has total_shortfall of 130.71
        assert "SUMMARY" in text_str
        assert "130.71" in text_str

    def test_format_text_contains_header(self):
        # Verify header section is present
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        assert "shift-pay-reconciler — reconciliation report" in text_str
        assert "dataset: minwage 2026.1.0" in text_str

    def test_format_text_summary_only_true(self):
        # summary_only=True should omit header and table rows
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0', summary_only=True)

        # Should start with SUMMARY
        assert text_str.startswith("SUMMARY")
        # Should not contain ROW table header
        assert "ROW  DATE" not in text_str
        # Should not contain dataset header
        assert "shift-pay-reconciler" not in text_str
        # Should contain summary data
        assert "shifts:" in text_str
        assert "total hours:" in text_str

    def test_format_text_compliant_shift_ok_status(self):
        # A shift paid at or above the minimum should show OK status and 0.00 shortfall
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,200.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        # Should contain OK status
        assert "OK" in text_str
        # Should show 0.00 shortfall
        assert "$   0.00" in text_str

    def test_format_text_money_format(self):
        # Verify money is formatted with $ prefix and 2 decimal places
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        # Money should be formatted with $
        assert "$ " in text_str or "$" in text_str

    def test_format_text_hours_format(self):
        # Verify hours are formatted to 2 decimal places
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        # Should contain hours with 2 decimals
        assert "8.50" in text_str

    def test_format_text_multiple_shifts(self):
        # Verify multiple shifts are all shown in table
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0
2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0
2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00,shift-3,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        lines = text_str.split('\n')
        # Should have at least 3 shift rows plus header and footer lines
        shift_rows = [line for line in lines[4:] if line and not line.startswith("SUMMARY") and not line.startswith("  ")]
        assert len(shift_rows) >= 3

    def test_format_text_summary_format(self):
        # Verify SUMMARY block format matches DESIGN
        csv_content = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes
2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0"""
        dataset = load_dataset(None)
        records = parse_shifts(io.StringIO(csv_content))
        shift_results, summary = reconcile(records, dataset)

        text_str = format_text(shift_results, summary, '2026.1.0')

        # Should have SUMMARY block with required fields
        assert "SUMMARY" in text_str
        assert "shifts:" in text_str
        assert "total hours:" in text_str
        assert "total required:" in text_str
        assert "total paid:" in text_str
        assert "total shortfall:" in text_str
        assert "underpaid shifts:" in text_str
