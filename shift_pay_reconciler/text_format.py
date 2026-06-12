from decimal import Decimal


def format_money(amount):
    """Format a Decimal amount as currency with $ prefix and 2 decimal places."""
    if isinstance(amount, Decimal):
        d = amount
    else:
        d = Decimal(str(amount))

    formatted_cents = d.quantize(Decimal('0.01'))
    amount_str = f"{formatted_cents:.2f}"

    # Right-align within 7 chars ($ + space + up to 6 digits for typical amounts)
    return f"${amount_str:>7}"


def format_hours(hours):
    """Format a Decimal hours value to 2 decimal places."""
    if isinstance(hours, Decimal):
        d = hours
    else:
        d = Decimal(str(hours))

    return f"{d:.2f}"


def format_text(shift_results, summary, dataset_version, summary_only=False):
    """
    Format reconciliation results as a human-readable text report.

    Args:
        shift_results: List of dicts with per-shift reconciliation data
        summary: Dict with aggregate summary totals
        dataset_version: String version of the dataset (e.g., "2026.1.0")
        summary_only: If True, emit only the SUMMARY block (no header or per-shift table)

    Returns:
        String containing the formatted report (no trailing newline beyond the block)
    """
    lines = []

    if not summary_only:
        # Header section
        lines.append("shift-pay-reconciler — reconciliation report")
        lines.append(f"dataset: minwage {dataset_version}")
        lines.append("")

        # Per-shift table header
        header = "ROW  DATE        JURISDICTION    REG_HRS  OT_HRS  REQUIRED   PAID      SHORTFALL  STATUS"
        lines.append(header)

        # Per-shift rows
        for result in shift_results:
            row = result['row']
            date = result['date']
            jurisdiction = result['jurisdiction']
            regular_hours = format_hours(result['regular_hours'])
            overtime_hours = format_hours(result['overtime_hours'])
            required_pay = format_money(result['required_pay'])
            paid = format_money(result['pay_received'])
            shortfall = format_money(result['shortfall'])
            status = result['status']

            # Format the row with careful alignment
            # ROW: right-aligned in 3 chars, then 2 spaces
            # DATE: 10 chars (ISO date), then 2 spaces
            # JURISDICTION: left-aligned in 15 chars, then 2 spaces
            # REG_HRS: right-aligned in 7 chars, then 2 spaces
            # OT_HRS: right-aligned in 6 chars, then 2 spaces
            # REQUIRED: right-aligned with $ prefix, then 3 spaces
            # PAID: right-aligned with $ prefix, then 2 spaces
            # SHORTFALL: right-aligned with $ prefix, then 3 spaces
            # STATUS: left-aligned

            row_str = (
                f"{row}    "
                f"{date:<10}  "
                f"{jurisdiction:<14}  "
                f"{regular_hours:>7}  "
                f"{overtime_hours:>6}  "
                f"{required_pay}  "
                f"{paid}  "
                f"{shortfall}   "
                f"{status}"
            )
            lines.append(row_str)

        lines.append("")

    # SUMMARY block
    lines.append("SUMMARY")

    shift_count = summary['shift_count']
    total_hours = format_hours(summary['total_hours'])
    total_required = format_money(summary['total_required'])
    total_paid = format_money(summary['total_paid'])
    total_shortfall = format_money(summary['total_shortfall'])
    underpaid_count = summary['underpaid_count']

    lines.append(f"  shifts:               {shift_count}")
    lines.append(f"  total hours:          {total_hours}")
    lines.append(f"  total required:    {total_required}")
    lines.append(f"  total paid:        {total_paid}")
    lines.append(f"  total shortfall:   {total_shortfall}")
    lines.append(f"  underpaid shifts:     {underpaid_count} of {shift_count}")

    return "\n".join(lines)
