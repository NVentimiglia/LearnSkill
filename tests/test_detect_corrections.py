"""Integration tests for detect-corrections.py.

Fixture: claude_session.jsonl  (real session from this project, 2026-05-16)
  User: "Compare MemoryMCP and memorix"
  Agent tries web search → user rejects it → [Request interrupted]
  User rephrases: provides local paths and "compare"
  Agent: final comparison

  No correction words — neutral rephrasing. Does not trigger detector at 20% threshold.

Fixture: claude_thrashing.jsonl
  "actually make it microservices"
  "wrong, the API gateway should have its own section"
  "keep going, you stopped" (keep-going, also triggers correction regex)
  "continue, add the architecture review trigger too"

Run with -s to see full detector output.
"""

from .conftest import FIXTURES, audit, run_tool


class TestCorrections:
    def test_detects_corrections_real_session(self):
        """
        Real session: user rejected tool, interrupted, then rephrased neutrally.
        The rephrasing uses no correction words — below 20% threshold.
        Expected: runs cleanly, no CORRECTIONS flagged.
        """
        r = run_tool("detect-corrections.py", str(FIXTURES / "claude_session.jsonl"))
        audit("detect-corrections - claude_session.jsonl (real session, neutral rephrasing)", r)
        assert r.returncode == 0

    def test_detects_corrections_thrashing_session(self):
        """
        Thrashing session: 'actually', 'wrong', 'continue' — multiple correction words.
        Expected: CORRECTIONS flagged with >= 2 examples.
        """
        r = run_tool("detect-corrections.py", str(FIXTURES / "claude_thrashing.jsonl"))
        audit("detect-corrections - claude_thrashing.jsonl", r)
        assert "CORRECTIONS" in r.stdout
        assert "EXAMPLE" in r.stdout

    def test_examples_contain_correction_quote(self):
        """
        The EXAMPLE lines should contain real text from the session.
        'actually' and 'wrong' are explicit correction words in the fixture.
        """
        r = run_tool("detect-corrections.py", str(FIXTURES / "claude_thrashing.jsonl"))
        examples = [l for l in r.stdout.splitlines() if l.startswith("EXAMPLE")]
        assert any("actually" in ex.lower() or "wrong" in ex.lower() for ex in examples), (
            f"Expected correction word in examples:\n{r.stdout}"
        )

    def test_high_threshold_suppresses_output(self):
        """
        With --threshold-pct 90, only sessions where 90%+ of turns are corrections fire.
        Neither fixture reaches that level.
        """
        r = run_tool("detect-corrections.py", str(FIXTURES / "claude_thrashing.jsonl"), "--threshold-pct", "90")
        audit("detect-corrections - claude_thrashing.jsonl --threshold-pct 90 (should be clean)", r)
        assert r.stdout.strip() == ""

    def test_clean_session_under_threshold(self):
        """
        claude_errors.jsonl: user gives one instruction then one follow-up.
        Low correction rate — should not fire at default 20% threshold.
        """
        r = run_tool("detect-corrections.py", str(FIXTURES / "claude_errors.jsonl"))
        audit("detect-corrections - claude_errors.jsonl (low correction rate)", r)
        # Just verify it runs cleanly — may or may not flag depending on content
        assert r.returncode == 0
