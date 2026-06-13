import subprocess


class TestE2eMalformed:
    def test_malformed_csv_exits_nonzero_with_row_error(self):
        """E2E: running on broken.csv exits non-zero with row-level error."""
        result = subprocess.run(
            ["python", "-m", "wage_checker", "examples/broken.csv"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert result.returncode == 1
        assert "error:" in result.stderr
        assert "error: row" in result.stderr
        assert "clock_out" in result.stderr
        assert "is not after" in result.stderr
        assert "clock_in" in result.stderr
