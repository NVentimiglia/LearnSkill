#!/usr/bin/env python3
"""Detect correction patterns in a Claude Code JSONL session.

Corrections: user messages containing phrases that indicate the agent
produced something wrong and needs to redo it.

Usage:
    python detect-corrections.py <session.jsonl> [--threshold-pct N]

Output (stdout):
    CORRECTIONS  <N>/<total> user turns (<pct>%)
    EXAMPLE  <quote>          (up to 5 examples)
    (silence = no corrections detected above threshold)

Exit: always 0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

THRESHOLD_PCT = 20  # flag if >= this % of user turns contain corrections

PATTERNS = re.compile(
    r"\b(no[,\s]|nope\b|wrong\b|that'?s not\b|i said\b|actually\b|"
    r"wait[,\s]|stop[,\s]|instead\b|don'?t\b|why did you\b|"
    r"incorrect\b|not what i\b|i meant\b|go back\b|revert\b)",
    re.IGNORECASE,
)

_STRIP_TAGS = re.compile(
    r"<(?:ide_opened_file|ide_selection_file|system-reminder)>.*?"
    r"</(?:ide_opened_file|ide_selection_file|system-reminder)>",
    re.DOTALL,
)


def _user_texts(jsonl_path: Path) -> list[str]:
    texts: list[str] = []
    for line in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "user":
            continue
        for block in obj.get("message", {}).get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text = _STRIP_TAGS.sub("", block.get("text", "")).strip()
                if text:
                    texts.append(text)
    return texts


def detect(jsonl_path: str | Path, threshold_pct: int = THRESHOLD_PCT) -> dict | None:
    """Return {count, total, pct, examples} if above threshold, else None."""
    texts = _user_texts(Path(jsonl_path))
    if not texts:
        return None
    corrections = [t for t in texts if PATTERNS.search(t)]
    pct = round(len(corrections) / len(texts) * 100)
    if pct < threshold_pct:
        return None
    return {
        "count": len(corrections),
        "total": len(texts),
        "pct": pct,
        "examples": [t[:120] for t in corrections[:5]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", help="Path to Claude Code JSONL session file")
    parser.add_argument("--threshold-pct", type=int, default=THRESHOLD_PCT,
                        help=f"Correction rate %% to flag (default: {THRESHOLD_PCT})")
    args = parser.parse_args()

    try:
        result = detect(args.session, args.threshold_pct)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(0)

    if result:
        print(f"CORRECTIONS  {result['count']}/{result['total']} user turns ({result['pct']}%)")
        for ex in result["examples"]:
            print(f"EXAMPLE  {ex}")


if __name__ == "__main__":
    main()
