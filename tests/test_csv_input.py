import pytest
from decimal import Decimal
from datetime import datetime
from io import StringIO
from wage_checker.csv_input import parse_shifts


def test_well_formed_three_row_csv():
    """A well-formed 3-row CSV returns 3 records with Decimal pay_received and datetime fields."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.50
2026-01-06T10:00,2026-01-06T18:30,US-CA,200.00
2026-01-07T08:00,2026-01-07T16:00,US-FED,175.75"""

    records = parse_shifts(StringIO(csv_data))

    assert len(records) == 3

    # Check first record
    assert records[0]['row'] == 1
    assert records[0]['clock_in'] == datetime(2026, 1, 5, 9, 0)
    assert records[0]['clock_out'] == datetime(2026, 1, 5, 17, 0)
    assert records[0]['jurisdiction'] == 'US-WA-Seattle'
    assert records[0]['pay_received'] == Decimal('150.50')
    assert isinstance(records[0]['pay_received'], Decimal)
    assert isinstance(records[0]['clock_in'], datetime)
    assert isinstance(records[0]['clock_out'], datetime)

    # Check second record
    assert records[1]['row'] == 2
    assert records[1]['clock_in'] == datetime(2026, 1, 6, 10, 0)
    assert records[1]['clock_out'] == datetime(2026, 1, 6, 18, 30)
    assert records[1]['pay_received'] == Decimal('200.00')

    # Check third record
    assert records[2]['row'] == 3
    assert records[2]['pay_received'] == Decimal('175.75')


def test_missing_jurisdiction_column():
    """A CSV missing the jurisdiction column raises ValueError with exact message."""
    csv_data = """clock_in,clock_out,pay_received
2026-01-05T09:00,2026-01-05T17:00,150.50"""

    with pytest.raises(ValueError, match=r"missing required column\(s\): jurisdiction"):
        parse_shifts(StringIO(csv_data))


def test_missing_multiple_required_columns():
    """A CSV missing multiple required columns raises ValueError listing all missing columns."""
    csv_data = """clock_in,jurisdiction
2026-01-05T09:00,US-WA-Seattle"""

    with pytest.raises(ValueError, match=r"missing required column\(s\)"):
        parse_shifts(StringIO(csv_data))


def test_clock_out_less_than_clock_in():
    """A row with clock_out < clock_in raises the exact error message."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T17:00,2026-01-05T09:00,US-WA-Seattle,150.50"""

    with pytest.raises(ValueError, match=r"row 1: clock_out \(2026-01-05T09:00\) is not after clock_in \(2026-01-05T17:00\)"):
        parse_shifts(StringIO(csv_data))


def test_clock_out_equals_clock_in():
    """A row with clock_out == clock_in raises the error message."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T17:00,2026-01-05T17:00,US-WA-Seattle,150.50"""

    with pytest.raises(ValueError, match=r"row 1: clock_out \(2026-01-05T17:00\) is not after clock_in \(2026-01-05T17:00\)"):
        parse_shifts(StringIO(csv_data))


def test_unparseable_clock_in_timestamp():
    """An unparseable clock_in timestamp raises the exact error message."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
not-a-timestamp,2026-01-05T17:00,US-WA-Seattle,150.50"""

    with pytest.raises(ValueError, match=r"row 1: unparseable timestamp not-a-timestamp"):
        parse_shifts(StringIO(csv_data))


def test_unparseable_clock_out_timestamp():
    """An unparseable clock_out timestamp raises the exact error message."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T09:00,bad-time,US-WA-Seattle,150.50"""

    with pytest.raises(ValueError, match=r"row 1: unparseable timestamp bad-time"):
        parse_shifts(StringIO(csv_data))


def test_row_numbering_excludes_header():
    """Row numbering starts at 1 for the first data row and excludes the header."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T09:00,2026-01-05T08:00,US-WA-Seattle,150.50"""

    with pytest.raises(ValueError, match=r"row 1:"):
        parse_shifts(StringIO(csv_data))


def test_row_numbering_multiple_rows():
    """Row numbers are correct for multiple rows, excluding the header."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.50
2026-01-06T10:00,2026-01-06T09:00,US-CA,200.00"""

    with pytest.raises(ValueError, match=r"row 2:"):
        parse_shifts(StringIO(csv_data))


def test_optional_columns_defaults():
    """Optional columns use correct defaults when missing."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.50"""

    records = parse_shifts(StringIO(csv_data))

    assert records[0]['shift_id'] is None
    assert records[0]['break_minutes'] == 0
    assert records[0]['tips'] is None
    assert records[0]['mileage'] is None


def test_optional_columns_with_values():
    """Optional columns are parsed correctly when present."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received,shift_id,break_minutes,tips,mileage
2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.50,shift-123,30,5.50,2.75"""

    records = parse_shifts(StringIO(csv_data))

    assert records[0]['shift_id'] == 'shift-123'
    assert records[0]['break_minutes'] == 30
    assert records[0]['tips'] == Decimal('5.50')
    assert records[0]['mileage'] == Decimal('2.75')


def test_whitespace_only_shift_id():
    """Whitespace-only shift_id becomes None."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received,shift_id
2026-01-05T09:00,2026-01-05T17:00,US-WA-Seattle,150.50,   """

    records = parse_shifts(StringIO(csv_data))

    assert records[0]['shift_id'] is None


def test_overnight_shift():
    """Overnight shifts (clock_out on next day) are handled correctly."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
2026-01-05T22:00,2026-01-06T06:00,US-WA-Seattle,150.50"""

    records = parse_shifts(StringIO(csv_data))

    assert len(records) == 1
    assert records[0]['clock_in'] == datetime(2026, 1, 5, 22, 0)
    assert records[0]['clock_out'] == datetime(2026, 1, 6, 6, 0)
    assert records[0]['clock_out'] > records[0]['clock_in']


def test_column_order_independence():
    """Columns can be in any order."""
    csv_data = """pay_received,clock_out,jurisdiction,clock_in
150.50,2026-01-05T17:00,US-WA-Seattle,2026-01-05T09:00"""

    records = parse_shifts(StringIO(csv_data))

    assert len(records) == 1
    assert records[0]['clock_in'] == datetime(2026, 1, 5, 9, 0)
    assert records[0]['clock_out'] == datetime(2026, 1, 5, 17, 0)
    assert records[0]['pay_received'] == Decimal('150.50')
    assert records[0]['jurisdiction'] == 'US-WA-Seattle'


def test_whitespace_in_values():
    """Leading/trailing whitespace in values is stripped."""
    csv_data = """clock_in,clock_out,jurisdiction,pay_received
 2026-01-05T09:00 , 2026-01-05T17:00 , US-WA-Seattle , 150.50 """

    records = parse_shifts(StringIO(csv_data))

    assert records[0]['clock_in'] == datetime(2026, 1, 5, 9, 0)
    assert records[0]['jurisdiction'] == 'US-WA-Seattle'
    assert records[0]['pay_received'] == Decimal('150.50')
