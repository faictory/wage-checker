# wage-checker

A worker-side CLI that reconciles recorded shifts against bundled statutory minimum-wage and overtime floors, flagging each underpaid shift with its dollar shortfall — turning opaque platform pay into actionable wage-claim evidence.

## What it does

`wage-checker` lets a gig, delivery, or warehouse worker run their shift CSV against a bundled, versioned minimum-wage dataset and get a per-shift and summary report naming exactly which shifts were paid below the statutory floor and by how much.

The tool:
- Reconciles shifts against statutory minimum-wage and overtime rules by jurisdiction
- Reports per-shift shortfalls and a total summary
- Supports both human-readable and machine-readable (JSON) output
- Runs fully offline with no network access
- Accepts shifts from a file or stdin

## Installation

Install the package locally:

```bash
pip install -e .
```

Or build via Make:

```bash
make build
```

## Input CSV Schema

The CSV must have a header row with the following columns:

### Required columns (any order):

- **`clock_in`** — ISO-8601 local timestamp, e.g. `2026-01-05T09:00` (supports overnight shifts via a later `clock_out` date)
- **`clock_out`** — ISO-8601 local timestamp; must be strictly after `clock_in`
- **`jurisdiction`** — a key present in the dataset, e.g. `US-WA-Seattle`, `US-CA`, `US-FED`
- **`pay_received`** — decimal dollars the worker was actually paid for the shift

### Optional columns:

- **`shift_id`** — shift identifier, echoed in output
- **`break_minutes`** — unpaid break time deducted from hours (default: `0`)
- **`tips`** — recorded and displayed but not credited toward the minimum
- **`mileage`** — recorded and displayed but not credited toward the minimum

The shift's effective date (used to pick the rate in force) is the date of `clock_in`.

## Example Invocations

### Default reconcile (headline use case)

Text report with per-shift rows and summary:

```bash
$ wage-checker shifts.csv
wage-checker — reconciliation report
dataset: minwage 2026.1.0

ROW  DATE        JURISDICTION    REG_HRS  OT_HRS  REQUIRED   PAID      SHORTFALL  STATUS
1    2026-01-05  US-WA-Seattle      8.50    0.00  $ 176.46  $ 120.00  $  56.46   UNDERPAID
2    2026-01-06  US-CA              8.00    3.00  $ 206.25  $ 150.00  $  56.25   UNDERPAID
3    2026-01-07  US-FED             8.00    0.00  $  58.00  $  40.00  $  18.00   UNDERPAID

SUMMARY
  shifts:               3
  total hours:          27.50
  total required:    $ 440.71
  total paid:        $ 310.00
  total shortfall:   $ 130.71
  underpaid shifts:     3 of 3
```

### Machine-readable output (JSON)

Same numbers as the text report, in JSON format for tools and spreadsheets:

```bash
$ wage-checker shifts.csv --format json
{"dataset_version": "2026.1.0", "shifts": [ ... ], "summary": { ... }}
```

### Just the bottom line

Only the summary totals, suppressing per-shift rows:

```bash
$ wage-checker shifts.csv --summary-only
SUMMARY
  shifts:               3
  total hours:          27.50
  total required:    $ 440.71
  total paid:        $ 310.00
  total shortfall:   $ 130.71
  underpaid shifts:     3 of 3
```

### Read from stdin with an alternate dataset

Stream CSV from stdin and use a custom local minimum-wage dataset:

```bash
$ cat shifts.csv | wage-checker - --dataset ./my-minwage.json
... reconciliation report computed from ./my-minwage.json ...
```

### Check the version

Print the tool version and bundled dataset version:

```bash
$ wage-checker --version
wage-checker 0.1.0 (dataset minwage 2026.1.0)
```

## Command-line Options

- **`CSV_PATH`** (required) — path to shift CSV file, or `-` to read from stdin
- **`--format {text,json}`** (default: `text`) — output format: human-readable table or JSON
- **`--dataset PATH`** — use an alternate local minimum-wage dataset file instead of the bundled default (no network access)
- **`--summary-only`** — suppress per-shift rows; emit only the summary totals
- **`--version`** — print tool and dataset versions, then exit
- **`-h`, `--help`** — print usage and exit

## Exit Codes

- `0` — reconciliation completed (report printed regardless of whether underpayments were found)
- `1` — input/validation error (malformed CSV, missing required column, unparseable timestamp, unknown jurisdiction)
- `2` — CLI usage error (unknown flag, bad `--format` value)

## More Information

For full project design, goals, and acceptance criteria, see [DESIGN.md](DESIGN.md).
