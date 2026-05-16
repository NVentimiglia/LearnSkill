"""Integration tests for detect-tool-efficiency.py.

Fixture: claude_exploration.jsonl
  14 read-only tool calls (Read ×12, Glob ×1, Grep ×1)
   1 write tool call    (Edit ×1)
  → ratio = 14:1 → above threshold=10 → fires

Fixture: claude_thrashing.jsonl
  0 reads, 7 edits → ratio undefined (no reads) → does not fire

Run with -s to see full detector output.
"""

from .conftest import FIXTURES, audit, run_tool


class TestToolEfficiency:
    def test_detects_excessive_read_ratio(self):
        """
        14 reads, 1 edit → 14:1 ratio. Above default threshold (10).
        Expected:  TOOL-EFFICIENCY  14 reads  1 edits  (14:1 ratio)
        """
        r = run_tool("detect-tool-efficiency.py", str(FIXTURES / "claude_exploration.jsonl"))
        audit("detect-tool-efficiency - claude_exploration.jsonl", r)
        assert r.returncode == 0
        assert "TOOL-EFFICIENCY" in r.stdout
        assert "14" in r.stdout
        assert "1" in r.stdout

    def test_ratio_value_reported(self):
        """The reported ratio should be 14:1."""
        r = run_tool("detect-tool-efficiency.py", str(FIXTURES / "claude_exploration.jsonl"))
        assert "14:1" in r.stdout, f"Expected '14:1' in:\n{r.stdout}"

    def test_custom_ratio_threshold(self):
        """
        With --ratio 20, the 14:1 ratio is below threshold — no output.
        """
        r = run_tool("detect-tool-efficiency.py", str(FIXTURES / "claude_exploration.jsonl"), "--ratio", "20")
        audit("detect-tool-efficiency - claude_exploration.jsonl --ratio 20 (should be clean)", r)
        assert r.stdout.strip() == ""

    def test_edit_heavy_session_not_flagged(self):
        """
        claude_thrashing.jsonl: 7 edits, 0 reads. No efficiency problem.
        Expected: empty stdout (no reads to flag).
        """
        r = run_tool("detect-tool-efficiency.py", str(FIXTURES / "claude_thrashing.jsonl"))
        audit("detect-tool-efficiency - claude_thrashing.jsonl (edit-heavy — should be clean)", r)
        assert r.stdout.strip() == ""

    def test_clean_session_produces_no_output(self):
        """
        claude_session.jsonl: no tool calls at all.
        Expected: empty stdout.
        """
        r = run_tool("detect-tool-efficiency.py", str(FIXTURES / "claude_session.jsonl"))
        audit("detect-tool-efficiency - claude_session.jsonl (no tools — should be clean)", r)
        assert r.stdout.strip() == ""
