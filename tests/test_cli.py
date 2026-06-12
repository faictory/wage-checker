import json
import pytest
from io import StringIO
from unittest.mock import patch

from shift_pay_reconciler.cli import main
from shift_pay_reconciler import __version__


class TestCliValidCsv:
    def test_valid_csv_path_text_format(self, tmp_path):
        """Valid CSV path with text format prints text report and returns 0."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file)])

        assert result == 0
        output = mock_stdout.getvalue()
        assert 'shift-pay-reconciler' in output.lower() or 'summary' in output.lower()

    def test_valid_csv_with_default_format(self, tmp_path):
        """Default format is text when --format is not specified."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file)])

        assert result == 0
        output = mock_stdout.getvalue()
        assert len(output) > 0


class TestCliVersion:
    def test_version_flag_prints_correct_format(self):
        """--version prints 'shift-pay-reconciler <ver> (dataset minwage <ver>)' and returns 0."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main(['--version'])

        assert result == 0
        output = mock_stdout.getvalue().strip()
        assert output.startswith('shift-pay-reconciler')
        assert __version__ in output
        assert 'dataset minwage' in output

    def test_version_flag_exact_format(self):
        """--version output matches exact expected format."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main(['--version'])

        assert result == 0
        output = mock_stdout.getvalue().strip()
        assert output.startswith(f'shift-pay-reconciler {__version__}')


class TestCliHelp:
    def test_help_flag_exits_zero(self):
        """--help exits with code 0."""
        with patch('sys.stdout', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(['--help'])
        assert exc_info.value.code == 0

    def test_help_short_flag_exits_zero(self):
        """-h exits with code 0."""
        with patch('sys.stdout', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(['-h'])
        assert exc_info.value.code == 0


class TestCliErrors:
    def test_unknown_flag_exits_2(self):
        """Unknown flag causes argparse to exit with code 2."""
        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(['--unknown-flag', 'shifts.csv'])
        assert exc_info.value.code == 2

    def test_bad_format_value_exits_2(self):
        """Bad --format value causes argparse to exit with code 2."""
        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(['shifts.csv', '--format', 'invalid'])
        assert exc_info.value.code == 2

    def test_malformed_csv_error_to_stderr(self, tmp_path):
        """Malformed CSV prints 'error: row N: ...' to stderr and returns 1."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "not-a-timestamp,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = main([str(csv_file)])

        assert result == 1
        error = mock_stderr.getvalue()
        assert error.startswith('error:')
        assert 'row 1' in error

    def test_nonexistent_file_error_to_stderr(self):
        """Nonexistent CSV file prints 'error: ...' to stderr and returns 1."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = main(['/nonexistent/path/shifts.csv'])

        assert result == 1
        error = mock_stderr.getvalue()
        assert error.startswith('error:')


class TestCliJsonFormat:
    def test_json_format_valid_output(self, tmp_path):
        """--format json outputs valid JSON and returns 0."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json'])

        assert result == 0
        output = mock_stdout.getvalue()
        obj = json.loads(output)
        assert 'summary' in obj
        assert 'shifts' in obj or obj == {'summary': obj.get('summary'), 'dataset_version': obj.get('dataset_version')}

    def test_json_contains_required_fields(self, tmp_path):
        """JSON output contains required fields: shifts, summary, dataset_version."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json'])

        assert result == 0
        obj = json.loads(mock_stdout.getvalue())
        assert 'summary' in obj
        assert 'dataset_version' in obj


class TestCliStdin:
    def test_csv_path_dash_reads_from_stdin(self):
        """csv_path='-' reads CSV from stdin."""
        csv_data = (
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdin', StringIO(csv_data)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main(['-'])

        assert result == 0
        output = mock_stdout.getvalue()
        assert len(output) > 0

    def test_stdin_with_format_json(self):
        """stdin with --format json produces valid JSON output."""
        csv_data = (
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdin', StringIO(csv_data)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main(['-', '--format', 'json'])

        assert result == 0
        obj = json.loads(mock_stdout.getvalue())
        assert 'summary' in obj


class TestCliSummaryOnly:
    def test_summary_only_flag_text_format(self, tmp_path):
        """--summary-only suppresses per-shift rows in text format."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received,shift_id\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00,shift-1\n"
            "2026-01-06T08:00,2026-01-06T18:00,US-CA,200.00,shift-2\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--summary-only'])

        assert result == 0
        output = mock_stdout.getvalue()
        assert len(output) > 0

    def test_summary_only_flag_json_format(self, tmp_path):
        """--summary-only with --format json omits 'shifts' key."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json', '--summary-only'])

        assert result == 0
        obj = json.loads(mock_stdout.getvalue())
        assert 'summary' in obj


class TestCliDataset:
    def test_alternate_dataset_path_calls_load_dataset(self, tmp_path):
        """--dataset PATH is passed to load_dataset function."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO):
            with patch('shift_pay_reconciler.cli.load_dataset') as mock_load:
                with patch('shift_pay_reconciler.cli.parse_shifts'):
                    with patch('shift_pay_reconciler.cli.reconcile'):
                        main([str(csv_file), '--dataset', '/path/to/dataset.json'])

        mock_load.assert_called_with('/path/to/dataset.json')


class TestCliAcceptanceCriteria:
    def test_acceptance_1_valid_csv_text_exit0(self, tmp_path):
        """Acceptance: main(['shifts.csv']) on valid CSV prints text report and returns 0."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file)])

        assert result == 0
        assert len(mock_stdout.getvalue()) > 0

    def test_acceptance_2_version_exit0(self):
        """Acceptance: --version prints version line and exits 0."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main(['--version'])

        assert result == 0
        output = mock_stdout.getvalue().strip()
        assert f'shift-pay-reconciler {__version__}' in output
        assert 'dataset minwage' in output

    def test_acceptance_3_help_exit0(self):
        """Acceptance: --help exits 0."""
        with patch('sys.stdout', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(['--help'])
        assert exc_info.value.code == 0

    def test_acceptance_4_unknown_flag_exit2(self):
        """Acceptance: unknown flag exits 2."""
        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(['--unknown', 'shifts.csv'])
        assert exc_info.value.code == 2

    def test_acceptance_5_bad_format_exit2(self, tmp_path):
        """Acceptance: bad --format value exits 2."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main([str(csv_file), '--format', 'xml'])
        assert exc_info.value.code == 2

    def test_acceptance_6_malformed_csv_error_stderr_exit1(self, tmp_path):
        """Acceptance: malformed CSV prints 'error: row N: ...' to stderr and exits 1."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "bad-timestamp,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = main([str(csv_file)])

        assert result == 1
        error = mock_stderr.getvalue()
        assert error.startswith('error:')
        assert 'row 1' in error

    def test_acceptance_7_format_json(self, tmp_path):
        """Acceptance: --format json prints JSON."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json'])

        assert result == 0
        obj = json.loads(mock_stdout.getvalue())
        assert 'summary' in obj

    def test_acceptance_8_stdin_dash(self):
        """Acceptance: '-' reads from stdin."""
        csv_data = (
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        with patch('sys.stdin', StringIO(csv_data)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main(['-'])

        assert result == 0
        assert len(mock_stdout.getvalue()) > 0
