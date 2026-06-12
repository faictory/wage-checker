import subprocess
import sys

from shift_pay_reconciler import __version__


class TestVersionFlag:
    def test_version_outputs_correct_format(self):
        """--version outputs shift-pay-reconciler <version> (dataset minwage <version>)."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--version'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        assert output == f'shift-pay-reconciler {__version__} (dataset minwage 2026.1.0)'

    def test_version_exit_code_zero(self):
        """--version exits with code 0."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--version'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_version_contains_tool_version(self):
        """--version output includes the tool version 0.1.0."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--version'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        assert '0.1.0' in output

    def test_version_contains_dataset_version(self):
        """--version output includes the dataset version 2026.1.0."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--version'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout.strip()
        assert '2026.1.0' in output


class TestHelpFlag:
    def test_help_exit_code_zero(self):
        """--help exits with code 0."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_help_contains_format_flag(self):
        """--help output mentions --format flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert '--format' in output

    def test_help_contains_dataset_flag(self):
        """--help output mentions --dataset flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert '--dataset' in output

    def test_help_contains_summary_only_flag(self):
        """--help output mentions --summary-only flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert '--summary-only' in output

    def test_help_contains_csv_path_positional(self):
        """--help output mentions csv_path positional argument."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        # Check for either the argument name or references to CSV in the help
        assert 'csv_path' in output or 'CSV' in output or 'shift' in output.lower()

    def test_help_mentions_all_required_flags(self):
        """--help output contains all required flags and positional argument."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        required_items = ['--format', '--dataset', '--summary-only']
        for item in required_items:
            assert item in output, f"{item} not found in help output"


class TestHShortFlag:
    def test_h_short_flag_exit_code_zero(self):
        """-h exits with code 0."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '-h'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_h_short_flag_contains_format_flag(self):
        """-h output mentions --format flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '-h'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert '--format' in output

    def test_h_short_flag_contains_dataset_flag(self):
        """-h output mentions --dataset flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '-h'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert '--dataset' in output

    def test_h_short_flag_contains_summary_only_flag(self):
        """-h output mentions --summary-only flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '-h'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert '--summary-only' in output

    def test_h_short_flag_mentions_all_required_flags(self):
        """-h output contains all required flags and positional argument."""
        result = subprocess.run(
            [sys.executable, '-m', 'shift_pay_reconciler', '-h'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        required_items = ['--format', '--dataset', '--summary-only']
        for item in required_items:
            assert item in output, f"{item} not found in -h output"
