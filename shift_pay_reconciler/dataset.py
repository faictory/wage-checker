import json
from datetime import date
from decimal import Decimal
from importlib import resources


def load_dataset(path=None):
    """Load the minimum wage dataset from bundled or alternate file.

    Args:
        path: Optional filesystem path to dataset JSON file. If None, loads bundled fixture.

    Returns:
        Parsed dataset dict with 'dataset_version' and 'jurisdictions' keys.

    Raises:
        ValueError: If file is unreadable or invalid against schema.
    """
    if path is None:
        # Load from bundled package data
        try:
            files = resources.files('shift_pay_reconciler').joinpath('data')
            dataset_file = files.joinpath('minwage-2026.1.0.json')
            data = json.loads(dataset_file.read_text())
        except (FileNotFoundError, TypeError) as e:
            raise ValueError(f"Failed to load bundled dataset: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in bundled dataset: {e}") from e
    else:
        # Load from specified file path
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise ValueError(f"Dataset file not found: {path}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dataset file: {e}") from e

    # Validate schema
    if 'dataset_version' not in data:
        raise ValueError("Dataset missing required 'dataset_version' field")
    if 'jurisdictions' not in data:
        raise ValueError("Dataset missing required 'jurisdictions' field")

    return data


def dataset_version(dataset):
    """Get the version string from dataset.

    Args:
        dataset: Parsed dataset dict.

    Returns:
        Version string (e.g., '2026.1.0').
    """
    return dataset.get('dataset_version')


def select_rate(dataset, jurisdiction, effective_date):
    """Select the applicable minimum rate and overtime config for a jurisdiction and date.

    Args:
        dataset: Parsed dataset dict.
        jurisdiction: Jurisdiction key (e.g., 'US-WA-Seattle').
        effective_date: datetime.date to look up rate for.

    Returns:
        Tuple of (min_rate: Decimal, overtime_config: dict).

    Raises:
        ValueError: If jurisdiction not found or no applicable rate for date.
    """
    if jurisdiction not in dataset['jurisdictions']:
        raise ValueError(f"unknown jurisdiction: {jurisdiction}")

    jurisdiction_data = dataset['jurisdictions'][jurisdiction]
    rates = jurisdiction_data['rates']

    # Find the latest rate effective on or before the given date
    applicable_rate = None
    for rate_entry in rates:
        rate_effective = date.fromisoformat(rate_entry['effective'])
        if rate_effective <= effective_date:
            if applicable_rate is None or date.fromisoformat(rate_entry['effective']) > date.fromisoformat(applicable_rate['effective']):
                applicable_rate = rate_entry

    if applicable_rate is None:
        raise ValueError(f"No minimum wage rate effective on or before {effective_date} for jurisdiction {jurisdiction}")

    min_rate = Decimal(applicable_rate['min_rate'])
    overtime_config = jurisdiction_data['overtime']

    return (min_rate, overtime_config)
