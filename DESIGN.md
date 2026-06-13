# wage-checker

A worker-side CLI that reconciles recorded shifts against bundled statutory
minimum-wage and overtime floors, flagging each underpaid shift with its dollar
shortfall — turning opaque platform pay into actionable wage-claim evidence.

## Charter

`wage-checker` lets a gig/delivery/warehouse worker run their shift CSV
against a bundled, versioned minimum-wage dataset and get a per-shift + summary
report naming exactly which shifts were paid below the statutory floor and by how
much.

## Command Surface

The tool is a single command (a CLI and an importable library). Invoked as
`wage-checker <CSV_PATH> [options]` or `python -m wage_checker
<CSV_PATH> [options]`. There is one reconcile action; flags only shape input
source and output presentation.

| Token | Kind | Takes | Effect |
|-------|------|-------|--------|
| `CSV_PATH` | positional (required) | a filesystem path, or `-` for stdin | The worker's shift CSV to reconcile. `-` reads the CSV from standard input. |
| `--format {text,json}` | option | one of `text`, `json` (default `text`) | Selects output shape: human-readable table (`text`) or machine-readable JSON (`json`) carrying identical numbers. |
| `--dataset PATH` | option | a filesystem path | Reconcile against an alternate **local** minimum-wage dataset file (same schema as the bundled one) instead of the bundled default. No network is ever used. |
| `--summary-only` | flag | — | Suppress the per-shift rows; emit only the summary totals block (text) or only the `summary` object (json). |
| `--version` | flag | — | Print the tool version and the bundled dataset version, then exit 0. |
| `-h`, `--help` | flag | — | Print usage for the command surface above and exit 0. |

### Input CSV schema

The CSV has a header row. Required columns (any order):

- `clock_in` — ISO-8601 local timestamp, e.g. `2026-01-05T09:00` (supports
  overnight shifts via a later `clock_out` date).
- `clock_out` — ISO-8601 local timestamp; must be strictly after `clock_in`.
- `jurisdiction` — a key present in the dataset, e.g. `US-WA-Seattle`, `US-CA`,
  `US-FED`.
- `pay_received` — decimal dollars the worker was actually paid for the shift.

Optional columns: `shift_id` (echoed in output), `break_minutes` (unpaid break
deducted from hours; default `0`), `tips`, `mileage` (recorded and displayed but
**not** credited toward the minimum — see Non-goals).

The shift's effective date (used to pick the rate in force) is the date of
`clock_in`.

## Output schema/format

The tool writes the report to **stdout** and errors to **stderr**. Exit codes:

- `0` — reconciliation completed and a report was printed (this is returned even
  when underpayments are found; the report, not the exit code, carries the
  finding).
- `1` — input/validation error: malformed CSV (missing required column,
  unparseable timestamp, `clock_out` not after `clock_in`, unknown jurisdiction)
  or an unreadable/invalid dataset. A row-level message names the offending row.
- `2` — CLI usage error (unknown flag, bad `--format` value).

### `text` (default) shape

A header line naming the dataset version, a fixed-column per-shift table (one row
per CSV shift), then a `SUMMARY` block. Money is shown to the cent; hours to two
decimals; `STATUS` is `OK` or `UNDERPAID`.

```
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

A compliant shift renders `$   0.00` in `SHORTFALL` and `OK` in `STATUS`.

### `json` shape

A single object with `dataset_version`, a `shifts` array (one object per row), and
a `summary` object. The numbers are byte-for-byte the same values as the text
report.

```json
{
  "dataset_version": "2026.1.0",
  "shifts": [
    {
      "row": 1,
      "shift_id": "1",
      "date": "2026-01-05",
      "jurisdiction": "US-WA-Seattle",
      "regular_hours": 8.5,
      "overtime_hours": 0.0,
      "min_rate": 20.76,
      "overtime_multiplier": 1.5,
      "required_pay": 176.46,
      "pay_received": 120.00,
      "shortfall": 56.46,
      "status": "UNDERPAID"
    }
  ],
  "summary": {
    "shift_count": 3,
    "total_hours": 27.5,
    "total_required": 440.71,
    "total_paid": 310.00,
    "total_shortfall": 130.71,
    "underpaid_count": 3
  }
}
```

### Error shape (exit 1)

A single `error:` line on stderr identifying the row (1-based, excluding the
header) and the problem, e.g.:

```
error: row 4: clock_out (2026-01-06T08:00) is not after clock_in (2026-01-06T19:00)
```
```
error: missing required column(s): jurisdiction
```

## Default no-flag behavior

Running the tool with only the required CSV path performs the headline use case —
reconcile every shift against the bundled statutory floors and report shortfalls:

```
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

No flags, no config, no network: CSV in, reconciliation report out (exit 0).

## Canonical invocations

1. **Default reconcile (headline)** — text report to stdout:
   ```
   $ wage-checker shifts.csv
   ... (the per-shift table + SUMMARY block shown above) ...
   ```

2. **Machine-readable output** — same numbers as JSON for tooling/spreadsheets:
   ```
   $ wage-checker shifts.csv --format json
   {"dataset_version": "2026.1.0", "shifts": [ ... ], "summary": { ... }}
   ```

3. **Just the bottom line** — only the deterministic totals:
   ```
   $ wage-checker shifts.csv --summary-only
   SUMMARY
     shifts:               3
     total hours:          27.50
     total required:    $ 440.71
     total paid:        $ 310.00
     total shortfall:   $ 130.71
     underpaid shifts:     3 of 3
   ```

4. **Stream from stdin against an alternate dataset**:
   ```
   $ cat shifts.csv | wage-checker - --dataset ./my-minwage.json
   ... reconciliation report computed from ./my-minwage.json ...
   ```

5. **Malformed input** — row-level error, non-zero exit:
   ```
   $ wage-checker broken.csv ; echo "exit=$?"
   error: row 4: clock_out (2026-01-06T08:00) is not after clock_in (2026-01-06T19:00)
   exit=1
   ```

6. **Versions**:
   ```
   $ wage-checker --version
   wage-checker 0.1.0 (dataset minwage 2026.1.0)
   ```

## Acceptance criteria

Each criterion is bound to exactly one command/flag; every token in the Command
Surface appears at least once.

1. **`CSV_PATH` (default reconcile) — shortfall correctness.** Given a shift paid
   below its jurisdiction's bundled statutory minimum, the per-shift row reports
   the exact dollar `SHORTFALL` and `STATUS=UNDERPAID`; a shift paid at or above
   the floor reports `$0.00` and `STATUS=OK`.
2. **`CSV_PATH` (default reconcile) — overtime.** For a shift in a fixture
   jurisdiction whose hours exceed the configured daily/weekly overtime threshold,
   the `OT_HRS` and `REQUIRED` columns reflect the overtime multiplier applied to
   the overflow hours.
3. **`CSV_PATH` (default reconcile) — rate selection.** The minimum rate used for
   a shift is the one for that row's `jurisdiction` in force on the `clock_in`
   date, chosen from the dataset's effective-dated schedule.
4. **`CSV_PATH` (default reconcile) — malformed input.** A CSV with a missing
   required column, an unparseable timestamp, or a `clock_out` not strictly after
   `clock_in` exits `1` and prints a row-level `error:` line naming the offending
   row.
5. **`--summary-only`.** Output contains the `SUMMARY` totals block with a
   deterministic `total shortfall` across the dataset and omits all per-shift
   rows.
6. **`--format json`.** Output is a single parseable JSON object whose
   `shifts`/`summary` numbers equal the text report's numbers for the same input.
7. **`--dataset PATH`.** Pointing at an alternate local dataset with different
   rates changes the computed `REQUIRED`/`SHORTFALL` accordingly, and no network
   call is made.
8. **`--version`.** Prints the tool version and bundled dataset version and exits
   `0`.
9. **`CSV_PATH` = `-`.** Passing `-` reads the CSV from stdin and produces the
   same report as reading that content from a file.
10. **`-h`/`--help`.** Prints usage covering the command surface and exits `0`.

## Coherence requirements (your design is REJECTED unless all hold)

(1) exactly one tool / one contract
(2) every criterion exercises THIS contract
(3) the default invocation demonstrates the headline
(4) NO second/competing contract or mode hiding

## Problem

Gig, delivery, and warehouse workers cannot tell when platform pay algorithms
underpay them, because the pay math is opaque — Human Rights Watch documented seven
platforms using algorithms in ways that evade minimum wage. Seattle's itemized
pay-statement mandate (Jan 2026) gives workers more data but no general tool to
check that data against the statutory floor. The people hurt are low-wage workers
who have the raw shift records but no way to convert them into a defensible
underpayment figure for a wage claim. `wage-checker` closes that gap: it
recomputes what each shift was legally owed and surfaces the shortfall.

## Goals / Non-goals

**Goals**

- Reconcile a worker's shift CSV against a bundled, versioned minimum-wage +
  overtime dataset and report per-shift and total dollar shortfalls.
- Select the correct rate by jurisdiction and effective date, and apply daily/
  weekly overtime multipliers from the dataset.
- Be deterministic, fully offline, and emit both human-readable and JSON output.
- Fail loudly and specifically on malformed input so a worker can fix their CSV.

**Non-goals**

- Tip-credit / tip-pooling modeling: tips and mileage are recorded and displayed
  but never credited toward the statutory minimum.
- Maintaining a comprehensive or legally authoritative national wage database —
  the bundled dataset is a small, clearly-versioned fixture covering the fixture
  jurisdictions only; users may supply their own via `--dataset`.
- Reimbursements, expense rules, scheduling/predictive-pay laws, tax withholding,
  or net-vs-gross pay.
- Any network access, account, upload, or hosted service; no PDF/statement OCR or
  platform API ingestion.
- Filing, formatting, or transmitting a legal claim; the tool produces evidence,
  not a filing.

## Hermetic build constraints

- **Language/toolchain:** Python (packaged project with `pyproject.toml`); lint
  via `ruff`, tests via `pytest`, as the repo Makefile already wires.
- **Offline & secret-free:** builds and tests with no network access, no secrets,
  no paid services, and no real user data. The minimum-wage dataset is a bundled
  versioned fixture shipped inside the package (e.g.
  `wage_checker/data/minwage-2026.1.0.json`); `--dataset` only ever reads
  a local file.
- **Dependencies:** permissive-licensed only (standard library is sufficient for
  CSV, datetime, decimal, and JSON; no heavyweight runtime deps required).
- **Licensing & docs:** ships an OSI-approved `LICENSE` and a `README` describing
  install, the CSV schema, and example invocations.
- **Makefile contract:** the repo Makefile honors the canonical targets —
  `make check` (ruff lint + pytest), `make test` (the pytest suite), `make build`
  (`pip install -e`), and `make run`. **`make run` invokes the real entrypoint on a
  bundled fixture**: it runs `python -m wage_checker examples/sample.csv`,
  where `examples/sample.csv` is shipped in the repo and contains at least one
  underpaid shift and one overtime shift across multiple jurisdictions. `make run`
  therefore prints a real reconciliation report (the table + SUMMARY block above),
  not usage text — a help-only `run` is a hollow build. `SMOKE_ARGS` is set to
  `examples/sample.csv`.

## Test expectations

Every acceptance criterion is covered by at least one named test.

**Unit**

- `compute_hours`: regular/overtime split for a normal shift, an overnight
  (cross-midnight) shift, and a shift with `break_minutes` deducted.
- `select_rate`: returns the rate effective on the `clock_in` date when the
  dataset has multiple effective-dated entries for a jurisdiction; raises on an
  unknown jurisdiction. (AC 3)
- `apply_overtime`: hours above a daily threshold and above a weekly threshold get
  the configured multiplier; hours under threshold do not. (AC 2)
- `shortfall`: `required - paid` for an underpaid shift; clamps to `0` (not
  negative) for a compliant/overpaid shift. (AC 1)
- CSV parsing: rejects missing required column, unparseable timestamp, and
  `clock_out <= clock_in` with a row-indexed error message. (AC 4)

**Integration**

- Default text run over a multi-row fixture asserts the per-shift `STATUS`/
  `SHORTFALL` values and an exact, deterministic `total shortfall`. (AC 1, AC 5)
- `--format json` over the same fixture parses to an object whose numbers equal the
  text run's numbers. (AC 6)
- `--summary-only` emits the SUMMARY block and no per-shift rows. (AC 5)
- `--dataset` pointing at an alternate fixture changes the computed shortfalls vs.
  the bundled dataset. (AC 7)
- Reading the same CSV via `-` (stdin) yields output identical to the file path.
  (AC 9)
- `--version` prints tool + dataset version and exits 0; `--help` exits 0 and lists
  the flags. (AC 8, AC 10)

**End-to-end**

- `make run` on `examples/sample.csv` exits 0 and its stdout contains the report
  header, at least one `UNDERPAID` row, an `OT_HRS` value greater than zero, and a
  non-zero `total shortfall` (the WORKS-vs-HOLLOW smoke check).
- A malformed `examples/` fixture run through the CLI exits non-zero and prints the
  row-level `error:` line. (AC 4)
