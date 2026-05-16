#!/usr/bin/env python3
"""Detect excessive read-to-edit ratio in a Claude Code JSONL session.

High ratio: agent reads far more files than it edits, suggesting it
is exploring without making progress (analysis paralysis).

Usage:
    python detect-tool-efficiency.py <session.jsonl> [--ratio N]

Output (stdout):
    TOOL-EFFICIENCY  <reads> reads  <edits> edits  (<ratio>:1 ratio)
    (silence = ratio is acceptable or session has no edits)

Exit: always 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RATIO_THRESHOLD = 10  # flag if reads > N * edits

READ_TOOLS  = {"Read", "Glob", "Grep", "LS", "ls"}
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}


def detect(jsonl_path: str | Path, ratio: int = RATIO_THRESHOLD) -> dict | None:
    """Return {reads, edits, ratio} if ratio is excessive, else None."""
    reads = 0
    edits = 0
    for line in Path(jsonl_path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in obj.get("message", {}).get("content", []):
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            if name in READ_TOOLS:
                reads += 1
            elif name in WRITE_TOOLS:
                edits += 1

    if edits == 0 or reads <= ratio * edits:
        return None
    return {"reads": reads, "edits": edits, "ratio": reads // edits}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Path to Claude Code JSONL session file")
    parser.add_argument("--ratio", type=int, default=RATIO_THRESHOLD,
                        help=f"Read:edit ratio to flag (default: {RATIO_THRESHOLD})")
    args = parser.parse_args()

    try:
        result = detect(args.session, args.ratio)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(0)

    if result:
        print(
            f"TOOL-EFFICIENCY  {result['reads']} reads  "
            f"{result['edits']} edits  ({result['ratio']}:1 ratio)"
        )


if __name__ == "__main__":
    main()
