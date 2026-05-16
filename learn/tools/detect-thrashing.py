#!/usr/bin/env python3
"""Detect file thrashing in a Claude Code JSONL session.

Thrashing: the same file is edited N or more times in one session,
indicating unclear direction or repeated rework.

Usage:
    python detect-thrashing.py <session.jsonl> [--threshold N]

Output (stdout):
    THRASH  <file>  (<N> edits)     one line per thrashed file, sorted by count
    (silence = no thrashing detected)

Exit: always 0. Findings go to stdout; errors go to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

THRESHOLD = 3
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}


def detect(jsonl_path: str | Path, threshold: int = THRESHOLD) -> list[dict]:
    """Return [{file, count}] for files edited >= threshold times, sorted descending."""
    edits: Counter[str] = Counter()
    for line in Path(jsonl_path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in obj.get("message", {}).get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") in EDIT_TOOLS:
                fp = (
                    block.get("input", {}).get("file_path")
                    or block.get("input", {}).get("path", "")
                )
                if fp:
                    edits[fp] += 1
    return [{"file": f, "count": c} for f, c in edits.most_common() if c >= threshold]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Path to Claude Code JSONL session file")
    parser.add_argument("--threshold", type=int, default=THRESHOLD,
                        help=f"Min edits to flag as thrashing (default: {THRESHOLD})")
    args = parser.parse_args()

    try:
        results = detect(args.session, args.threshold)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(0)

    for r in results:
        print(f"THRASH  {r['file']}  ({r['count']} edits)")


if __name__ == "__main__":
    main()
