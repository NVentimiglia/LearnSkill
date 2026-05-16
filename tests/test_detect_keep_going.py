"""Integration tests for detect-keep-going.py.

Fixture: claude_thrashing.jsonl
  "keep going, you stopped before adding the data flow section"   (explicit)
  "continue, add the architecture review trigger too"             (explicit)
  → 2 keep-going instances, threshold=2 → fires

Run with -s to see full detector output.
"""

from .conftest import FIXTURES, audit, run_tool


class TestKeepGoing:
    def test_detects_keep_going_loops(self):
        """
        Two 'keep going' / 'continue' messages in claude_thrashing.jsonl.
        Expected:  KEEP-GOING  2 instance(s)
                   EXAMPLE  keep going, you stopped ...
                   EXAMPLE  continue, add the architecture ...
        """
        r = run_tool("detect-keep-going.py", str(FIXTURES / "claude_thrashing.jsonl"))
        audit("detect-keep-going - claude_thrashing.jsonl", r)
        assert r.returncode == 0
        assert "KEEP-GOING" in r.stdout
        assert "2" in r.stdout

    def test_examples_show_actual_phrases(self):
        """Examples should contain the actual keep-going phrases from the session."""
        r = run_tool("detect-keep-going.py", str(FIXTURES / "claude_thrashing.jsonl"))
        assert "keep going" in r.stdout.lower() or "continue" in r.stdout.lower(), (
            f"Expected keep-going phrase in output:\n{r.stdout}"
        )

    def test_threshold_1_catches_single_instance(self):
        """
        With --threshold 1, any single keep-going phrase fires.
        Both fixtures with keep-going should be caught.
        """
        r = run_tool("detect-keep-going.py", str(FIXTURES / "claude_thrashing.jsonl"), "--threshold", "1")
        audit("detect-keep-going - claude_thrashing.jsonl --threshold 1", r)
        assert "KEEP-GOING" in r.stdout

    def test_clean_session_produces_no_output(self):
        """
        Real claude_session.jsonl has no keep-going language.
        Expected: empty stdout.
        """
        r = run_tool("detect-keep-going.py", str(FIXTURES / "claude_session.jsonl"))
        audit("detect-keep-going - claude_session.jsonl (no keep-going — should be clean)", r)
        assert r.stdout.strip() == ""

    def test_errors_session_produces_no_output(self):
        """
        claude_errors.jsonl: user gives one instruction then the correct path.
        No keep-going language. Expected: empty stdout.
        """
        r = run_tool("detect-keep-going.py", str(FIXTURES / "claude_errors.jsonl"))
        audit("detect-keep-going - claude_errors.jsonl (no keep-going)", r)
        assert r.stdout.strip() == ""
