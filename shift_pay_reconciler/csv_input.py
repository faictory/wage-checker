import csv
from datetime import datetime
from decimal import Decimal


def parse_shifts(text_stream):
    """
    Parse and validate a shift CSV from a text stream.

    Args:
        text_stream: An open text iterable/file object (already opened)

    Returns:
        A list of record dicts in file order, with parsed timestamps and decimals

    Raises:
        ValueError: If required columns are missing, timestamps are unparseable,
                   or clock_out is not after clock_in
    """
    reader = csv.DictReader(text_stream)

    # Check that all required columns are present
    if reader.fieldnames is None:
        raise ValueError("missing required column(s): clock_in, clock_out, jurisdiction, pay_received")

    required_columns = {'clock_in', 'clock_out', 'jurisdiction', 'pay_received'}
    fieldnames_set = set(reader.fieldnames)
    missing = required_columns - fieldnames_set

    if missing:
        missing_str = ', '.join(sorted(missing))
        raise ValueError(f"missing required column(s): {missing_str}")

    records = []

    for row_num, row in enumerate(reader, start=1):
        try:
            # Parse timestamps
            clock_in_str = row['clock_in'].strip()
            clock_out_str = row['clock_out'].strip()

            try:
                clock_in = datetime.fromisoformat(clock_in_str)
            except (ValueError, TypeError):
                raise ValueError(f"row {row_num}: unparseable timestamp {clock_in_str}")

            try:
                clock_out = datetime.fromisoformat(clock_out_str)
            except (ValueError, TypeError):
                raise ValueError(f"row {row_num}: unparseable timestamp {clock_out_str}")

            # Validate clock_out is after clock_in
            if clock_out <= clock_in:
                raise ValueError(f"row {row_num}: clock_out ({clock_out_str}) is not after clock_in ({clock_in_str})")

            # Parse pay_received as Decimal
            pay_received = Decimal(row['pay_received'].strip())

            # Parse optional fields
            shift_id = row.get('shift_id')
            if shift_id is not None:
                shift_id = shift_id.strip() if shift_id else None

            break_minutes_str = row.get('break_minutes', '0')
            break_minutes = int(break_minutes_str.strip()) if break_minutes_str else 0

            tips_str = row.get('tips')
            tips = Decimal(tips_str.strip()) if tips_str and tips_str.strip() else None

            mileage_str = row.get('mileage')
            mileage = Decimal(mileage_str.strip()) if mileage_str and mileage_str.strip() else None

            # Build record dict
            record = {
                'row': row_num,
                'shift_id': shift_id,
                'clock_in': clock_in,
                'clock_out': clock_out,
                'jurisdiction': row['jurisdiction'].strip(),
                'pay_received': pay_received,
                'break_minutes': break_minutes,
                'tips': tips,
                'mileage': mileage,
            }

            records.append(record)

        except ValueError:
            raise

    return records
