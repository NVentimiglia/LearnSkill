"""Shared paths and helpers for LearnSkill integration tests."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO     = Path(__file__).parent.parent
TOOLS    = REPO / "learn" / "tools"
FIXTURES = Path(__file__).parent / "fixtures"


def run_tool(tool: str, *args: str) -> subprocess.CompletedProcess:
    """Run a detection tool as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, str(TOOLS / tool), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def audit(title: str, result: subprocess.CompletedProcess) -> None:
    """Print tool output for human audit. Visible with pytest -s."""
    bar = "-" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)
    if result.stdout.strip():
        print(result.stdout.rstrip())
    else:
        print("  (no output — signal not detected)")
    if result.stderr.strip():
        print(f"  stderr: {result.stderr.strip()}")
    print(bar)


@pytest.fixture()
def cursor_db(tmp_path: Path) -> Path:
    """A minimal cursor workspaceStorage with a real-pattern session."""
    ws = tmp_path / "workspaceStorage" / "abc123def456"
    ws.mkdir(parents=True)
    db = ws / "state.vscdb"
    sessions = [
        {
            "messages": [
                {"role": "user",      "content": "refactor PaymentProcessor into smaller functions"},
                {"role": "assistant", "content": "Split into charge(), validate(), and notify()."},
                {"role": "user",      "content": "wrong, keep the original method names, just split internals"},
                {"role": "assistant", "content": "Kept method names. Extracted _validate_card() and _send_receipt()."},
                {"role": "user",      "content": "you missed _format_amount(), split that out too"},
                {"role": "assistant", "content": "Added _format_amount() helper."},
            ]
        }
    ]
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE ItemTable (key TEXT, value TEXT)")
    con.execute("INSERT INTO ItemTable VALUES (?, ?)", ("chat.sessions", json.dumps(sessions)))
    con.commit()
    con.close()
    return tmp_path / "workspaceStorage"
