"""Integration tests for collect-cursor.py.

Uses the cursor_db fixture (conftest.py) which creates a real SQLite
state.vscdb with a payment refactoring session containing corrections.

Run with -s to see full collector output for each test.
"""

from .conftest import TOOLS, cursor_db  # noqa: F401


class TestCollectCursor:
    def test_collects_session(self, cursor_db):
        """
        SQLite DB has one session with 6 messages (user/assistant alternating).
        Expected: markdown output with Session header and turn content.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location("collect_cursor", TOOLS / "collect-cursor.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        sessions = mod.collect(since=None, base=cursor_db)
        assert len(sessions) == 1
        label, md = sessions[0]
        print(f"\n{'-'*60}")
        print(f"  collect-cursor - cursor_db fixture")
        print(f"{'-'*60}")
        print(md[:800])
        print(f"{'-'*60}")
        assert "**User**" in md
        assert "**Assistant**" in md

    def test_correction_content_present(self, cursor_db):
        """
        The session contains 'wrong, keep the original method names'.
        This is a clear correction — should be in the markdown output.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location("collect_cursor", TOOLS / "collect-cursor.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        _, md = mod.collect(since=None, base=cursor_db)[0]
        print(f"\n{'-'*60}")
        print(f"  collect-cursor - correction content check")
        print(f"{'-'*60}")
        print(f"  Looking for: 'wrong, keep the original method names'")
        print(f"  Found in output: {'YES' if 'wrong' in md else 'NO'}")
        print(f"{'-'*60}")
        assert "wrong, keep the original method names" in md

    def test_incremental_clarification_present(self, cursor_db):
        """
        'you missed _format_amount()' — user had to add detail after initial response.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location("collect_cursor", TOOLS / "collect-cursor.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        _, md = mod.collect(since=None, base=cursor_db)[0]
        assert "_format_amount()" in md

    def test_missing_db_returns_empty(self, tmp_path):
        """
        A directory with no state.vscdb files returns an empty list gracefully.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location("collect_cursor", TOOLS / "collect-cursor.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        empty = tmp_path / "empty_ws"
        empty.mkdir()
        result = mod.collect(since=None, base=empty)
        print(f"\n{'-'*60}")
        print(f"  collect-cursor - missing DB (should return [])")
        print(f"  Result: {result}")
        print(f"{'-'*60}")
        assert result == []

    def test_since_filters_old_db(self, cursor_db):
        """
        A future timestamp should filter out all sessions.
        """
        import importlib.util, time
        spec = importlib.util.spec_from_file_location("collect_cursor", TOOLS / "collect-cursor.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        future = time.time() + 3600
        result = mod.collect(since=future, base=cursor_db)
        print(f"\n{'-'*60}")
        print(f"  collect-cursor - future timestamp filter (should return [])")
        print(f"  Result: {result}")
        print(f"{'-'*60}")
        assert result == []
