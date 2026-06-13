import subprocess
import sys


class TestCliText:
    def test_cli_text_run_with_design_example(self, tmp_path):
        """AC 1: Assert per-shift STATUS/SHORTFALL and deterministic total shortfall."""
        # Create CSV with the DESIGN example: US-WA-Seattle 8.5h/$120, US-CA 11h/$150, US-FED 8h/$40
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00\n"
            "2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00\n"
            "2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00\n"
        )

        # Run CLI via subprocess
        result = subprocess.run(
            [sys.executable, "-m", "wage_checker", str(csv_file)],
            capture_output=True,
            text=True
        )

        # Assert exit 0
        assert result.returncode == 0
        output = result.stdout

        # Assert header is present
        assert "wage-checker — reconciliation report" in output

        # Assert each shift shows SHORTFALL values and UNDERPAID status
        assert "56.46" in output  # US-WA-Seattle shortfall
        assert "56.25" in output  # US-CA shortfall
        assert "18.00" in output  # US-FED shortfall

        # All shifts should be UNDERPAID
        underpaid_count = output.count("UNDERPAID")
        assert underpaid_count == 3

        # Assert SUMMARY contains exact total shortfall
        assert "SUMMARY" in output
        assert "130.71" in output
        # Verify it's in the total shortfall line
        assert "total shortfall:" in output
        lines = output.split('\n')
        shortfall_lines = [line for line in lines if "total shortfall:" in line]
        assert len(shortfall_lines) > 0
        assert "130.71" in shortfall_lines[0]

    def test_cli_text_summary_only_flag(self, tmp_path):
        """AC 5: --summary-only shows SUMMARY block and does NOT contain per-shift table header ROW."""
        # Create the same CSV
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:30,US-WA-Seattle,120.00\n"
            "2026-01-06T08:00,2026-01-06T19:00,US-CA,150.00\n"
            "2026-01-07T07:00,2026-01-07T15:00,US-FED,40.00\n"
        )

        # Run CLI with --summary-only flag
        result = subprocess.run(
            [sys.executable, "-m", "wage_checker", str(csv_file), "--summary-only"],
            capture_output=True,
            text=True
        )

        # Assert exit 0
        assert result.returncode == 0
        output = result.stdout

        # Assert SUMMARY block is present
        assert "SUMMARY" in output

        # Assert per-shift table header "ROW" is NOT present
        assert "ROW  DATE" not in output

        # Assert summary totals are present
        assert "shifts:" in output
        assert "total shortfall:" in output
