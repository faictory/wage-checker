import argparse
import sys

from . import __version__
from .csv_input import parse_shifts
from .dataset import load_dataset, dataset_version
from .reconcile import reconcile
from .text_format import format_text
from .json_format import format_json


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if '--version' in argv:
        try:
            bundled_dataset = load_dataset()
            version_str = dataset_version(bundled_dataset)
            print(f"shift-pay-reconciler {__version__} (dataset minwage {version_str})")
            return 0
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    parser = argparse.ArgumentParser(
        prog='shift-pay-reconciler',
        description='Reconcile worker shift records against minimum wage requirements',
    )

    parser.add_argument(
        'csv_path',
        help='Path to the CSV file with shift records, or "-" to read from stdin',
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format: text (default) or json',
    )

    parser.add_argument(
        '--dataset',
        type=str,
        help='Path to an alternate local dataset file',
    )

    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Suppress per-shift rows; emit only summary totals',
    )

    args = parser.parse_args(argv)

    try:
        if args.csv_path == '-':
            csv_text = sys.stdin.read()
        else:
            with open(args.csv_path, 'r') as f:
                csv_text = f.read()

        from io import StringIO
        csv_stream = StringIO(csv_text)
        shifts = parse_shifts(csv_stream)

        dataset = load_dataset(args.dataset)
        shift_results, summary = reconcile(shifts, dataset)

        version = dataset_version(dataset)

        if args.format == 'json':
            report = format_json(shift_results, summary, version, args.summary_only)
        else:
            report = format_text(shift_results, summary, version, args.summary_only)

        print(report)
        return 0

    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
