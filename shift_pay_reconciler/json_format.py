import json
from decimal import Decimal


def format_json(shift_results, summary, dataset_version, summary_only=False):
    """
    Render reconciliation results as JSON with numbers identical to text report.

    Args:
        shift_results: List of shift dicts from reconcile()
        summary: Summary dict from reconcile()
        dataset_version: String version of the dataset (e.g., '2026.1.0')
        summary_only: If True, omit shifts; emit only dataset_version and summary

    Returns:
        JSON string representing a single object
    """

    def decimal_to_float(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    if summary_only:
        obj = {
            'dataset_version': dataset_version,
            'summary': {
                'shift_count': summary['shift_count'],
                'total_hours': decimal_to_float(summary['total_hours']),
                'total_required': decimal_to_float(summary['total_required']),
                'total_paid': decimal_to_float(summary['total_paid']),
                'total_shortfall': decimal_to_float(summary['total_shortfall']),
                'underpaid_count': summary['underpaid_count'],
            },
        }
    else:
        obj = {
            'dataset_version': dataset_version,
            'shifts': [
                {
                    'row': shift['row'],
                    'shift_id': shift['shift_id'],
                    'date': shift['date'],
                    'jurisdiction': shift['jurisdiction'],
                    'regular_hours': decimal_to_float(shift['regular_hours']),
                    'overtime_hours': decimal_to_float(shift['overtime_hours']),
                    'min_rate': decimal_to_float(shift['min_rate']),
                    'overtime_multiplier': decimal_to_float(shift['overtime_multiplier']),
                    'required_pay': decimal_to_float(shift['required_pay']),
                    'pay_received': decimal_to_float(shift['pay_received']),
                    'shortfall': decimal_to_float(shift['shortfall']),
                    'status': shift['status'],
                }
                for shift in shift_results
            ],
            'summary': {
                'shift_count': summary['shift_count'],
                'total_hours': decimal_to_float(summary['total_hours']),
                'total_required': decimal_to_float(summary['total_required']),
                'total_paid': decimal_to_float(summary['total_paid']),
                'total_shortfall': decimal_to_float(summary['total_shortfall']),
                'underpaid_count': summary['underpaid_count'],
            },
        }

    return json.dumps(obj)
