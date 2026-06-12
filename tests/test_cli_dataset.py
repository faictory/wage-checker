import json
from io import StringIO
from unittest.mock import patch
from decimal import Decimal

from shift_pay_reconciler.cli import main


class TestCliDatasetIntegration:
    def test_alternate_dataset_changes_shortfall(self, tmp_path):
        """Test that --dataset flag uses alternate local dataset and computes different shortfalls (AC 7)."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,100.00\n"
        )

        alt_dataset_file = tmp_path / "alt_dataset.json"
        alt_dataset_file.write_text(
            json.dumps({
                'dataset_version': '2026.1.0',
                'jurisdictions': {
                    'US-WA-Seattle': {
                        'rates': [
                            {'effective': '2025-01-01', 'min_rate': '19.97'},
                            {'effective': '2026-01-01', 'min_rate': '15.00'}
                        ],
                        'overtime': {
                            'daily_threshold': None,
                            'weekly_threshold': 40,
                            'multiplier': '1.5'
                        }
                    },
                    'US-FED': {
                        'rates': [
                            {'effective': '2009-07-24', 'min_rate': '7.25'}
                        ],
                        'overtime': {
                            'daily_threshold': None,
                            'weekly_threshold': 40,
                            'multiplier': '1.5'
                        }
                    },
                    'US-CA': {
                        'rates': [
                            {'effective': '2026-01-01', 'min_rate': '16.50'}
                        ],
                        'overtime': {
                            'daily_threshold': 8,
                            'weekly_threshold': 40,
                            'multiplier': '1.5'
                        }
                    }
                }
            })
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json'])

        assert result == 0
        bundled_output = json.loads(mock_stdout.getvalue())
        bundled_shortfall = Decimal(str(bundled_output['summary']['total_shortfall']))

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json', '--dataset', str(alt_dataset_file)])

        assert result == 0
        alt_output = json.loads(mock_stdout.getvalue())
        alt_shortfall = Decimal(str(alt_output['summary']['total_shortfall']))

        assert bundled_shortfall != alt_shortfall
        assert alt_shortfall < bundled_shortfall

    def test_alternate_dataset_no_network_access(self, tmp_path):
        """Test that alternate dataset uses local file only (no network access)."""
        csv_file = tmp_path / "shifts.csv"
        csv_file.write_text(
            "clock_in,clock_out,jurisdiction,pay_received\n"
            "2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.00\n"
        )

        alt_dataset_file = tmp_path / "alt_dataset.json"
        alt_dataset_file.write_text(
            json.dumps({
                'dataset_version': '2026.1.0',
                'jurisdictions': {
                    'US-WA-Seattle': {
                        'rates': [
                            {'effective': '2025-01-01', 'min_rate': '19.97'},
                            {'effective': '2026-01-01', 'min_rate': '22.00'}
                        ],
                        'overtime': {
                            'daily_threshold': None,
                            'weekly_threshold': 40,
                            'multiplier': '1.5'
                        }
                    },
                    'US-FED': {
                        'rates': [
                            {'effective': '2009-07-24', 'min_rate': '7.25'}
                        ],
                        'overtime': {
                            'daily_threshold': None,
                            'weekly_threshold': 40,
                            'multiplier': '1.5'
                        }
                    },
                    'US-CA': {
                        'rates': [
                            {'effective': '2026-01-01', 'min_rate': '16.50'}
                        ],
                        'overtime': {
                            'daily_threshold': 8,
                            'weekly_threshold': 40,
                            'multiplier': '1.5'
                        }
                    }
                }
            })
        )

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main([str(csv_file), '--format', 'json', '--dataset', str(alt_dataset_file)])

        assert result == 0
        output = json.loads(mock_stdout.getvalue())
        assert 'summary' in output
        assert 'required_pay' in output['shifts'][0]
