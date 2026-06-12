import subprocess
import re
from pathlib import Path


def test_e2e_smoke_check():
    repo_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["python", "-m", "shift_pay_reconciler", "examples/sample.csv"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    assert result.returncode == 0, f"CLI exited with code {result.returncode}: {result.stderr}"

    output = result.stdout

    assert "shift-pay-reconciler — reconciliation report" in output

    assert "UNDERPAID" in output

    has_positive_ot = False
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) > 4 and parts[0].isdigit():
            try:
                ot_hrs = float(parts[4])
                if ot_hrs > 0:
                    has_positive_ot = True
                    break
            except (ValueError, IndexError):
                pass

    assert has_positive_ot, "No OT_HRS value > 0 found in output"

    shortfall_match = re.search(r'total shortfall:\s+\$\s*([\d.]+)', output)
    assert shortfall_match is not None, "No total shortfall found in output"
    shortfall = float(shortfall_match.group(1))
    assert shortfall > 0, "Total shortfall is not greater than zero"
