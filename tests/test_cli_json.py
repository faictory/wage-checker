import json
import re
import subprocess


class TestCliJsonParity:
    """Integration tests: JSON and text outputs produce identical numbers."""

    def extract_summary_from_text(self, text):
        """Parse SUMMARY section from text report and return dict of values."""
        # Find SUMMARY line and parse the following lines
        lines = text.split('\n')
        summary_idx = None
        for i, line in enumerate(lines):
            if line.strip() == 'SUMMARY':
                summary_idx = i
                break

        if summary_idx is None:
            raise ValueError("No SUMMARY section found in text output")

        summary = {}
        for line in lines[summary_idx + 1:]:
            if not line.strip():
                continue
            # Parse lines like "  shifts:               3" or "  total shortfall:   $  66.08"
            match = re.match(r'\s+([^:]+):\s+(.*)', line)
            if match:
                key, value = match.groups()
                # Extract numeric value, handling money format like "$ 405.46"
                num_match = re.search(r'[\d.]+', value)
                if num_match:
                    try:
                        summary[key] = float(num_match.group())
                    except ValueError:
                        pass
        return summary

    def extract_shifts_from_text(self, text):
        """Parse per-shift rows from text report."""
        lines = text.split('\n')
        shifts = []

        # Find the header line
        header_idx = None
        for i, line in enumerate(lines):
            if 'ROW' in line and 'DATE' in line:
                header_idx = i
                break

        if header_idx is None:
            raise ValueError("No shift table header found in text output")

        # Parse rows until we hit empty line or SUMMARY
        for line in lines[header_idx + 1:]:
            if not line.strip() or line.strip() == 'SUMMARY':
                break
            # Parse shift row
            # Format: ROW  DATE        JURISDICTION    REG_HRS  OT_HRS  REQUIRED   PAID      SHORTFALL  STATUS
            match = re.match(
                r'(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+\$\s*([\d.]+)\s+\$\s*([\d.]+)\s+\$\s*([\d.]+)\s+(\w+)',
                line
            )
            if match:
                row, date, jurisdiction, reg_hrs, ot_hrs, required, paid, shortfall, status = match.groups()
                shifts.append({
                    'row': int(row),
                    'date': date,
                    'required_pay': float(required),
                    'pay_received': float(paid),
                    'shortfall': float(shortfall),
                    'status': status,
                })
        return shifts

    def test_json_parity_with_design_example(self, tmp_path):
        """Run CLI twice on DESIGN example CSV; verify JSON numbers match text."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes\n"
            "2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00,shift-1,0\n"
            "2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00,shift-2,0\n"
            "2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00,shift-3,0\n"
        )

        # Run text format
        result_text = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'text'],
            capture_output=True,
            text=True,
        )
        assert result_text.returncode == 0
        text_output = result_text.stdout

        # Run JSON format
        result_json = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'json'],
            capture_output=True,
            text=True,
        )
        assert result_json.returncode == 0
        json_output = result_json.stdout

        # Parse outputs
        text_summary = self.extract_summary_from_text(text_output)
        text_shifts = self.extract_shifts_from_text(text_output)
        json_obj = json.loads(json_output)

        # Verify JSON structure
        assert 'dataset_version' in json_obj
        assert 'shifts' in json_obj
        assert 'summary' in json_obj

        # Verify shift count matches
        assert len(json_obj['shifts']) == len(text_shifts)
        assert json_obj['summary']['shift_count'] == len(text_shifts)

        # Compare per-shift numbers
        for i, json_shift in enumerate(json_obj['shifts']):
            text_shift = text_shifts[i]
            # Compare required_pay, pay_received, shortfall
            assert abs(json_shift['required_pay'] - text_shift['required_pay']) < 0.01, \
                f"Shift {i} required_pay mismatch: JSON={json_shift['required_pay']}, text={text_shift['required_pay']}"
            assert abs(json_shift['pay_received'] - text_shift['pay_received']) < 0.01, \
                f"Shift {i} pay_received mismatch: JSON={json_shift['pay_received']}, text={text_shift['pay_received']}"
            assert abs(json_shift['shortfall'] - text_shift['shortfall']) < 0.01, \
                f"Shift {i} shortfall mismatch: JSON={json_shift['shortfall']}, text={text_shift['shortfall']}"

        # Compare summary numbers
        assert abs(json_obj['summary']['total_shortfall'] - text_summary['total shortfall']) < 0.01, \
            f"Total shortfall mismatch: JSON={json_obj['summary']['total_shortfall']}, text={text_summary['total shortfall']}"
        assert abs(json_obj['summary']['total_required'] - text_summary['total required']) < 0.01, \
            f"Total required mismatch: JSON={json_obj['summary']['total_required']}, text={text_summary['total required']}"
        assert abs(json_obj['summary']['total_paid'] - text_summary['total paid']) < 0.01, \
            f"Total paid mismatch: JSON={json_obj['summary']['total_paid']}, text={text_summary['total paid']}"

    def test_json_exits_zero(self, tmp_path):
        """--format json exits with code 0."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        result = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'json'],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_json_parses(self, tmp_path):
        """JSON output is valid JSON and parseable."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        result = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'json'],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        obj = json.loads(result.stdout)
        assert isinstance(obj, dict)

    def test_json_has_required_fields(self, tmp_path):
        """JSON output contains dataset_version, shifts, summary."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        result = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'json'],
            capture_output=True,
            text=True,
        )

        obj = json.loads(result.stdout)
        assert 'dataset_version' in obj
        assert 'shifts' in obj
        assert 'summary' in obj

    def test_json_parity_single_shift(self, tmp_path):
        """JSON and text numbers match for single shift."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,100.00\n"
        )

        result_text = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'text'],
            capture_output=True,
            text=True,
        )
        assert result_text.returncode == 0

        result_json = subprocess.run(
            ['python', '-m', 'shift_pay_reconciler', str(csv_file), '--format', 'json'],
            capture_output=True,
            text=True,
        )
        assert result_json.returncode == 0

        text_summary = self.extract_summary_from_text(result_text.stdout)
        json_obj = json.loads(result_json.stdout)

        # Verify total_shortfall matches
        assert abs(json_obj['summary']['total_shortfall'] - text_summary['total shortfall']) < 0.01
