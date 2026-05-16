#!/usr/bin/env python3
"""Detect keep-going loops in a Claude Code JSONL session.

Keep-going loop: the user repeatedly has to tell the agent to continue
work it stopped prematurely, indicating the agent is not completing tasks.

Usage:
    python detect-keep-going.py <session.jsonl> [--threshold N]

Output (stdout):
    KEEP-GOING  <N> instance(s)
    EXAMPLE  <quote>          (each occurrence)
    (silence = no keep-going loops detected)

Exit: always 0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

THRESHOLD = 2

PATTERNS = re.compile(
    r"\b(keep going\b|keep working\b|continue\b|you stopped\b|"
    r"you('?re| are) not done\b|finish it\b|don'?t stop\b|"
    r"you didn'?t finish\b|incomplete\b|you left off\b)",
    re.IGNORECASE,
)

_STRIP_TAGS = re.compile(
    r"<(?:ide_opened_file|ide_selection_file|system-reminder)>.*?"
    r"</(?:ide_opened_file|ide_selection_file|system-reminder)>",
    re.DOTALL,
)


def detect(jsonl_path: str | Path, threshold: int = THRESHOLD) -> dict | None:
    """Return {count, examples} if >= threshold occurrences, else None."""
    matches: list[str] = []
    for line in Path(jsonl_path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "user":
            continue
        for block in obj.get("message", {}).get("content", []):
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            text = _STRIP_TAGS.sub("", block.get("text", "")).strip()
            if PATTERNS.search(text):
                matches.append(text[:120])
    if len(matches) < threshold:
        return None
    return {"count": len(matches), "examples": matches}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Path to Claude Code JSONL session file")
    parser.add_argument("--threshold", type=int, default=THRESHOLD,
                        help=f"Occurrences to flag (default: {THRESHOLD})")
    args = parser.parse_args()

    try:
        result = detect(args.session, args.threshold)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(0)

    if result:
        print(f"KEEP-GOING  {result['count']} instance(s)")
        for ex in result["examples"]:
            print(f"EXAMPLE  {ex}")


if __name__ == "__main__":
    main()
