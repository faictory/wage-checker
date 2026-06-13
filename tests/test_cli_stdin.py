import subprocess
import sys


class TestCliStdinViaSubprocess:
    def test_stdin_via_dash_produces_identical_output_to_file(self, tmp_path):
        """CSV_PATH='-' via stdin produces identical output to reading from file."""
        csv_file = tmp_path / "shifts.csv"
        csv_content = (
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
            "2026-01-06T08:00,2026-01-06T18:00,US-CA,200.00\n"
        )
        csv_file.write_text(csv_content)

        # Run CLI with file path
        result_file = subprocess.run(
            [sys.executable, "-m", "wage_checker", str(csv_file)],
            capture_output=True,
            text=True,
        )

        # Run CLI with stdin
        result_stdin = subprocess.run(
            [sys.executable, "-m", "wage_checker", "-"],
            input=csv_content,
            capture_output=True,
            text=True,
        )

        # Both should exit 0
        assert result_file.returncode == 0
        assert result_stdin.returncode == 0

        # Output should be identical
        assert result_file.stdout == result_stdin.stdout
