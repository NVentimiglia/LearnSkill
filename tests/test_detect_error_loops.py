"""Integration tests for detect-error-loops.py.

Fixture: claude_errors.jsonl
  Read tool fails 4 consecutive times (src/config.py, config.py, ./config.py,
  settings/config.py) before user provides the correct path (app/config.py).
  The 5th Read succeeds — loop ends at count=4.

Run with -s to see full detector output for each test.
"""

from .conftest import FIXTURES, audit, run_tool


class TestErrorLoops:
    def test_detects_consecutive_read_failures(self):
        """
        Read fails 4 times in a row — above threshold=3.
        Expected output:  ERROR-LOOP  Read  (4 consecutive failures)
        """
        r = run_tool("detect-error-loops.py", str(FIXTURES / "claude_errors.jsonl"))
        audit("detect-error-loops - claude_errors.jsonl", r)
        assert r.returncode == 0
        assert "ERROR-LOOP" in r.stdout
        assert "Read" in r.stdout
        assert "4" in r.stdout

    def test_tool_name_identified(self):
        """
        The detector should name the failing tool, not just report an anonymous loop.
        """
        r = run_tool("detect-error-loops.py", str(FIXTURES / "claude_errors.jsonl"))
        assert "Read" in r.stdout

    def test_custom_threshold_higher(self):
        """
        With --threshold 5, the 4-error loop is below threshold — no output.
        """
        r = run_tool("detect-error-loops.py", str(FIXTURES / "claude_errors.jsonl"), "--threshold", "5")
        audit("detect-error-loops - claude_errors.jsonl --threshold 5 (should be clean)", r)
        assert r.stdout.strip() == ""

    def test_clean_session_produces_no_output(self):
        """
        claude_thrashing.jsonl has no tool errors — all edits succeed.
        Expected: empty stdout.
        """
        r = run_tool("detect-error-loops.py", str(FIXTURES / "claude_thrashing.jsonl"))
        audit("detect-error-loops - claude_thrashing.jsonl (no errors — should be clean)", r)
        assert r.stdout.strip() == ""
