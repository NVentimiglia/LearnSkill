# Analysis Prompt

You have collected session text and raw detector output. Now analyze and write outputs.

---

## Signals to look for

| Signal | What to look for |
|---|---|
| **Corrections** | "no", "wrong", "actually", "that's not", "stop", "instead", "don't", "wait" |
| **Repeated instructions** | User restates the same preference or constraint more than once |
| **Keep-going loops** | "keep going", "continue", "you stopped", "finish it" |
| **High back-and-forth** | Many short exchanges, user redirecting every turn |
| **Tool failure loops** | Same tool failing 3+ times without strategy change |
| **Thrashing** | Same file edited or rewritten multiple times |
| **User interrupts** | `[Request interrupted by user]` in the session |

For non-JSONL sessions (Gemini, Codex, Copilot, Antigravity, Cursor), apply the same
signals manually — read the session and note any of the above.

---

## Output files

Create `.learn/` if it does not exist. Write all files.

### `.learn/friction.md`

Raw detector output for each JSONL session, then your observations.

```markdown
# Friction

## {session-filename}

**Detector output:**
```
{raw stdout from each tool that produced output, verbatim}
```

**Observed friction:**
- {quote from session} — {brief explanation}
```

### `.learn/analysis.md`

```markdown
# Analysis

## {Pattern Name}

{Description of the recurring behavior}

**Evidence:**
- "{quote}"
- "{quote}"
```

### `.learn/summary.md`

```markdown
# Learn Summary

**Run:** {ISO timestamp}
**Sessions:** {N} ({date range}, sources: {list})
**Signals detected:** {list of signal names, or "none"}
**Proposals written:** {list of filenames, or "none"}
```

### `.learn/proposals/skill-{name}.md`

One file per proposed skill. Propose anything you noticed — the user will decide what to keep.

```markdown
---
name: {name}
description: {one line}
triggers:
  - {trigger phrase}
---

# {Title}

{Rule body — concrete, actionable, one behavior per skill.}
```

### `.learn/proposals/doc-{name}.md`

Proposed AGENT.md / CLAUDE.md addition — project-level rules that address recurring friction.
