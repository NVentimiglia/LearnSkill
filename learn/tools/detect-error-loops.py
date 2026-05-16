#!/usr/bin/env python3
"""Detect error loops in a Claude Code JSONL session.

Error loop: the same tool fails N or more times consecutively without
the agent changing strategy (different tool or explicit user redirect).

Usage:
    python detect-error-loops.py <session.jsonl> [--threshold N]

Output (stdout):
    ERROR-LOOP  <tool>  (<N> consecutive failures)
    (silence = no error loops detected)

Exit: always 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

THRESHOLD = 3


def detect(jsonl_path: str | Path, threshold: int = THRESHOLD) -> list[dict]:
    """Return [{tool, count}] for tools that failed consecutively >= threshold times."""
    # Pass 1: map tool_use_id → tool_name
    tool_names: dict[str, str] = {}
    lines = Path(jsonl_path).read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in obj.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_names[block.get("id", "")] = block.get("name", "unknown")

    # Pass 2: walk tool_results in order, track consecutive errors per tool
    results: list[dict] = []
    current_tool: str | None = None
    current_count = 0

    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in obj.get("message", {}).get("content", []):
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            tool_name = tool_names.get(block.get("tool_use_id", ""), "unknown")
            if block.get("is_error"):
                if tool_name == current_tool:
                    current_count += 1
                else:
                    if current_count >= threshold:
                        results.append({"tool": current_tool, "count": current_count})
                    current_tool = tool_name
                    current_count = 1
            else:
                if current_count >= threshold:
                    results.append({"tool": current_tool, "count": current_count})
                current_tool = None
                current_count = 0

    if current_count >= threshold:
        results.append({"tool": current_tool, "count": current_count})

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Path to Claude Code JSONL session file")
    parser.add_argument("--threshold", type=int, default=THRESHOLD,
                        help=f"Consecutive failures to flag (default: {THRESHOLD})")
    args = parser.parse_args()

    try:
        results = detect(args.session, args.threshold)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(0)

    for r in results:
        print(f"ERROR-LOOP  {r['tool']}  ({r['count']} consecutive failures)")


if __name__ == "__main__":
    main()
