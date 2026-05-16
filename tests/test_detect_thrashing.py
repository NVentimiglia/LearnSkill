"""Integration tests for detect-thrashing.py.

Fixture: claude_thrashing.jsonl
  design.md  — edited 5 times (wrong direction, keep-going, incremental adds)
  SKILL.md   — edited 2 times (below default threshold)

Run with -s to see full detector output for each test.
"""

from .conftest import FIXTURES, audit, run_tool


class TestThrashing:
    def test_detects_thrashed_file(self):
        """
        design.md is edited 5 times — well above threshold=3.
        Expected output:  THRASH  design.md  (5 edits)
        """
        r = run_tool("detect-thrashing.py", str(FIXTURES / "claude_thrashing.jsonl"))
        audit("detect-thrashing - claude_thrashing.jsonl", r)
        assert r.returncode == 0
        assert "THRASH" in r.stdout
        assert "design.md" in r.stdout
        assert "5" in r.stdout

    def test_below_threshold_not_flagged(self):
        """
        SKILL.md is edited 2 times — below default threshold=3.
        Expected: SKILL.md does NOT appear in output.
        """
        r = run_tool("detect-thrashing.py", str(FIXTURES / "claude_thrashing.jsonl"))
        audit("detect-thrashing - threshold check for SKILL.md (2 edits)", r)
        assert "SKILL.md" not in r.stdout

    def test_custom_threshold_catches_lower_count(self):
        """
        With --threshold 2, SKILL.md (2 edits) should also be flagged.
        Expected output includes both design.md and SKILL.md.
        """
        r = run_tool("detect-thrashing.py", str(FIXTURES / "claude_thrashing.jsonl"), "--threshold", "2")
        audit("detect-thrashing - claude_thrashing.jsonl --threshold 2", r)
        assert "SKILL.md" in r.stdout
        assert "design.md" in r.stdout

    def test_clean_session_produces_no_output(self):
        """
        Real session (claude_session.jsonl) has no file edits — only reads and text.
        Expected: empty stdout.
        """
        r = run_tool("detect-thrashing.py", str(FIXTURES / "claude_session.jsonl"))
        audit("detect-thrashing - claude_session.jsonl (no edits — should be clean)", r)
        assert r.stdout.strip() == ""
