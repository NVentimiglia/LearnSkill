# Learn skill

Analyze recent agent sessions for friction, patterns, and rule proposals.
No external LLM. No API key. The agent running the skill does the analysis.

Pairs well with [SkillsMCP](https://github.com/NVentimiglia/SkillsMCP) for skill management and [claude-mem](https://github.com/thedotmack/claude-mem) for long-term memory.

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

---

## Example Output

#### summary.md
```
# Learn Summary

**Run:** 2026-05-16T22:27:00Z
**Sessions:** 5 (2026-05-16, sources: Claude Code, Antigravity)
**Signals detected:** Thrashing, Corrections, Manual Audit Requests
**Proposals written:** doc-pii-audit.md, doc-viewmodel-pattern.md
```

#### friction.md
```
# Friction

## 058f9ca1-6ae3-4b52-a341-1ff559841ea6.jsonl (Claude Code)

**Detector output:**

THRASH  \Charts\_VixTermStructureCard.cshtml  (3 edits)
THRASH  \ViewModels\WeightedSpxAdvanceDeclineViewModel.cs  (3 edits)
CORRECTIONS  3/10 user turns (30%)
EXAMPLE  compare with these findings:
Listed directory Pages
Listed directory Charts
Viewed Macro.cshtml:1-40
Viewed Macro.cshtm
EXAMPLE  Now do a review of the ViewModel layer.
ViewModels should transpose the data shapes from the services into a format usab
EXAMPLE  Can you do another pass of rendering / chart layer.
I want to make sure that charts can easily be added as componenets 


**Observed friction:**
- "Can you do another pass of rendering / chart layer. I want to make sure that charts can easily be added as componenets" — User had to explicitly ask for a componentization pass after the initial implementation.
- "Now do a review of the ViewModel layer. ViewModels should transpose the data shapes..." — User providing architectural guidance that should perhaps be in a project rule.

## faefb1d6-e9f9-46ad-8039-b0b0629bcb89 (Antigravity)

**Observed friction:**
- "Do a audit and review... look for hard coded paths, reference to my name, keys..." — User had to manually request a PII/Path audit before pushing. This suggests a need for an "Audit" ritual or rule.
- "The final push failed due to a credential mismatch..." — Model tried to push but didn't verify credentials/account first.

## 62ccc10a-a00a-46c9-b596-b2d994111faa (Antigravity)

**Observed friction:**
- None. Model correctly pivoted from SymbolicLink to Junction on Windows.

```

#### doc-viewmodel-pattern.md
```
# ViewModel and Componentization Ritual

When implementing new UI features (Charts, Pages):
1.  **ViewModel First**: Ensure a clear separation between services and the view. Data should be transposed into a display-ready format in the ViewModel.
2.  **Componentize**: If a piece of UI is likely to be reused (e.g., a specific chart type), implement it as a partial view or component rather than inlining it.
3.  **Review Pass**: After initial implementation, perform a "Refactor Pass" specifically looking for opportunities to improve modularity.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| No sessions found | Check that a session directory exists for this project |
| Same sessions every run | Delete `.learn/lean.stamp` to reset the cursor |
| Output too long | Ask the agent to limit to the last N sessions |
| Cursor SQLite locked | Close Cursor IDE first — it will be skipped gracefully if locked |

See [Design.md](Design.md) for architecture and provider path details.