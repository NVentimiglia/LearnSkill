# learn skill

Analyze recent agent sessions for friction, patterns, and rule proposals.
No external LLM. No API key. The agent running the skill does the analysis.

---

## What you get

Invoke the skill once. The agent reads your recent sessions and produces:

- **Friction** — specific moments where the session went sideways, with quotes.
- **Patterns** — behaviors that recurred across sessions, not one-off mistakes.
- **Rule Proposals** — concrete AGENT.md additions or skill files, ready to copy.

---

## Quick start

**Invoke the skill** in your agent session:
> *"analyze my sessions"*
> *"learn from sessions"*
> *"what friction did you see"*

The agent collects recent sessions, analyzes them, and outputs Friction / Patterns / Rule Proposals inline.

### Output files

The skill writes to `.learn/` in your project root (created automatically):

| File | What it is |
|---|---|
| `summary.md` | One-page run summary: sessions processed, signals found, proposals written |
| `friction.md` | Specific friction moments with quotes from the sessions |
| `analysis.md` | Patterns observed across sessions — recurring behaviors, not one-offs |
| `proposals/skill-*.md` | Proposed new skill files, ready to copy into `.agents/skills/` |
| `proposals/doc-*.md` | Proposed additions to `AGENT.md` or `CLAUDE.md` |
| `lean.stamp` | Timestamp of the last run — next run only reads newer sessions |

**Reprocess all sessions** (ignore the cursor):
```bash
rm .learn/lean.stamp
```

---

## Session sources

| Source | Location |
|---|---|
| **Claude Code** | `~/.claude/projects/{encoded}/` — JSONL |
| **Gemini CLI** | `~/.gemini/transcripts/` — JSONL |
| **Codex** | `~/.codex/sessions/` — JSON |
| **Antigravity** | `~/.antigravity/transcripts/` — markdown |
| **Cursor** | `workspaceStorage/*/state.vscdb` — SQLite |
| **GitHub Copilot** | `%APPDATA%/GitHub Copilot Chat/sessions/` — JSON |

By default, sources are filtered to sessions newer than the last run (via `lean.stamp`). Ask the agent to reprocess everything to override.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| No sessions found | Check that a session directory exists for this project |
| Same sessions every run | Delete `.learn/lean.stamp` to reset the cursor |
| Output too long | Ask the agent to limit to the last N sessions |
| Cursor SQLite locked | Close Cursor IDE first — it will be skipped gracefully if locked |

See [Design.md](Design.md) for architecture and provider path details.
See [Maintenance.md](Maintenance.md) for testing and fixture information.
