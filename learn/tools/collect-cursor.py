#!/usr/bin/env python3
"""Collect Cursor IDE chat sessions and print as markdown.

Reads from workspaceStorage/*/state.vscdb (SQLite, read-only).
Outputs normalized markdown to stdout, one section per session.

Usage:
    python collect-cursor.py [--since TIMESTAMP] [--budget CHARS]

Exit: always 0. Missing/locked DBs are skipped silently.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


def _workspace_base() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "workspaceStorage"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
    return Path.home() / ".config" / "Cursor" / "User" / "workspaceStorage"


def _after(path: Path, since: float | None) -> bool:
    if since is None:
        return True
    try:
        return path.stat().st_mtime >= since
    except OSError:
        return True


def _turns_to_md(messages: list[dict]) -> str:
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "")
        if role not in ("user", "assistant"):
            continue
        text = msg.get("content", "").strip()
        if not text:
            continue
        tag = "**User**" if role == "user" else "**Assistant**"
        parts.append(f"### {tag}\n\n{text}")
    return "\n\n".join(parts)


def collect(since: float | None = None, base: Path | None = None) -> list[tuple[str, str]]:
    """Return [(label, markdown)] for all readable Cursor sessions."""
    ws = base or _workspace_base()
    if not ws.is_dir():
        return []

    results: list[tuple[str, str]] = []
    for db_path in sorted(ws.glob("*/state.vscdb")):
        if not _after(db_path, since):
            continue
        try:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            row = con.execute(
                "SELECT value FROM ItemTable WHERE key = 'chat.sessions'"
            ).fetchone()
            con.close()
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            continue
        if not row:
            continue
        try:
            sessions = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            continue
        label = db_path.parent.name[:12]
        for session in (sessions if isinstance(sessions, list) else []):
            md = _turns_to_md(session.get("messages", []))
            if md:
                results.append((f"cursor:{label}", md))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=float, default=None)
    parser.add_argument("--budget", type=int, default=40_000)
    args = parser.parse_args()

    sessions = collect(since=args.since)
    if not sessions:
        return

    per = args.budget // len(sessions)
    parts: list[str] = []
    for i, (label, md) in enumerate(sessions, 1):
        parts.append(f"## Session {i} — {label}\n\n{md[-per:]}")
    print("\n\n---\n\n".join(parts))


if __name__ == "__main__":
    main()
