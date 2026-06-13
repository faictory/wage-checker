import json
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from wage_checker.dataset import dataset_version, load_dataset, select_rate


class TestLoadDataset:
    def test_load_bundled_dataset(self):
        dataset = load_dataset()
        assert dataset is not None
        assert isinstance(dataset, dict)
        assert 'dataset_version' in dataset
        assert 'jurisdictions' in dataset

    def test_load_dataset_from_path(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                'dataset_version': '2026.1.0',
                'jurisdictions': {
                    'TEST': {
                        'rates': [{'effective': '2026-01-01', 'min_rate': '20.00'}],
                        'overtime': {'daily_threshold': None, 'weekly_threshold': 40, 'multiplier': '1.5'}
                    }
                }
            }
            json.dump(test_data, f)
            f.flush()
            temp_path = f.name

        try:
            dataset = load_dataset(temp_path)
            assert dataset['dataset_version'] == '2026.1.0'
            assert 'TEST' in dataset['jurisdictions']
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_file_not_found(self):
        with pytest.raises(ValueError, match="Dataset file not found"):
            load_dataset('/nonexistent/path/to/file.json')

    def test_load_dataset_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{invalid json}')
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_dataset(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_missing_version(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {'jurisdictions': {}}
            json.dump(test_data, f)
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="dataset_version"):
                load_dataset(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_missing_jurisdictions(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {'dataset_version': '2026.1.0'}
            json.dump(test_data, f)
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="jurisdictions"):
                load_dataset(temp_path)
        finally:
            Path(temp_path).unlink()


class TestDatasetVersion:
    def test_dataset_version_bundled(self):
        dataset = load_dataset()
        version = dataset_version(dataset)
        assert version == '2026.1.0'

    def test_dataset_version_custom(self):
        custom_dataset = {'dataset_version': '2025.0.1', 'jurisdictions': {}}
        version = dataset_version(custom_dataset)
        assert version == '2025.0.1'


class TestSelectRate:
    def test_select_rate_seattle_2026_01_05(self):
        dataset = load_dataset()
        rate, overtime = select_rate(dataset, 'US-WA-Seattle', date(2026, 1, 5))
        assert rate == Decimal('20.76')
        assert isinstance(overtime, dict)
        assert 'daily_threshold' in overtime
        assert 'weekly_threshold' in overtime
        assert 'multiplier' in overtime

    def test_select_rate_seattle_2025_06_01(self):
        dataset = load_dataset()
        rate, overtime = select_rate(dataset, 'US-WA-Seattle', date(2025, 6, 1))
        assert rate == Decimal('19.97')
        assert isinstance(overtime, dict)

    def test_select_rate_federal(self):
        dataset = load_dataset()
        rate, overtime = select_rate(dataset, 'US-FED', date(2026, 1, 1))
        assert rate == Decimal('7.25')

    def test_select_rate_california(self):
        dataset = load_dataset()
        rate, overtime = select_rate(dataset, 'US-CA', date(2026, 1, 1))
        assert rate == Decimal('16.50')

    def test_select_rate_unknown_jurisdiction(self):
        dataset = load_dataset()
        with pytest.raises(ValueError, match="unknown jurisdiction: UNKNOWN"):
            select_rate(dataset, 'UNKNOWN', date(2026, 1, 1))

    def test_select_rate_no_effective_rate(self):
        dataset = load_dataset()
        with pytest.raises(ValueError, match="No minimum wage rate effective"):
            select_rate(dataset, 'US-WA-Seattle', date(2024, 1, 1))

    def test_select_rate_unsorted_rates(self):
        unsorted_dataset = {
            'dataset_version': '2026.1.0',
            'jurisdictions': {
                'TEST': {
                    'rates': [
                        {'effective': '2026-01-01', 'min_rate': '20.00'},
                        {'effective': '2025-01-01', 'min_rate': '19.00'}
                    ],
                    'overtime': {'daily_threshold': None, 'weekly_threshold': 40, 'multiplier': '1.5'}
                }
            }
        }
        rate, _ = select_rate(unsorted_dataset, 'TEST', date(2025, 6, 1))
        assert rate == Decimal('19.00')
        rate, _ = select_rate(unsorted_dataset, 'TEST', date(2026, 6, 1))
        assert rate == Decimal('20.00')

    def test_select_rate_returns_latest_effective(self):
        dataset = {
            'dataset_version': '2026.1.0',
            'jurisdictions': {
                'TEST': {
                    'rates': [
                        {'effective': '2024-01-01', 'min_rate': '15.00'},
                        {'effective': '2025-01-01', 'min_rate': '17.00'},
                        {'effective': '2026-01-01', 'min_rate': '19.00'}
                    ],
                    'overtime': {'daily_threshold': None, 'weekly_threshold': 40, 'multiplier': '1.5'}
                }
            }
        }
        rate, _ = select_rate(dataset, 'TEST', date(2025, 6, 1))
        assert rate == Decimal('17.00')

    def test_select_rate_overtime_config(self):
        dataset = load_dataset()
        _, overtime = select_rate(dataset, 'US-WA-Seattle', date(2026, 1, 5))
        assert overtime['daily_threshold'] is None
        assert overtime['weekly_threshold'] == 40
        assert overtime['multiplier'] == '1.5'
