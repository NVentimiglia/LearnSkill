# Design: learn skill

Replace LearnMCP's Python pipeline + external LLM call with a SkillMCP skill that delegates
analysis to the ambient LLM already running the session.

---

## Goals

- Single `learn` skill invocation: collect sessions → run detectors → analyze → output friction, patterns, proposals.
- Zero external LLM calls — the agent running the skill IS the analysis engine.
- Configurable session sources via a provider pattern (add a new source = add a new provider).
- Minimal code: skill instructions + one Cursor helper script + five signal detector scripts.
- No idle hooks, no background processes, no daemon.

## Non-goals

- Real-time / post-turn behavioral monitoring.
- MCP server exposure (`get_audit_report`, `get_suggestions` tools).
- Automatic hook registration into agent host configs.
- Handoff / context-memory compression (separate concern).

---

## Architecture

```
User invokes skill
       │
       ▼
  SKILL.md loaded by SkillMCP
       │
       ▼
  Agent reads skill instructions
       │
       ├─ 1. Read cursor (.learn/lean.stamp)
       │
       ├─ 2. Collect sessions using native agent tools (Read, Glob)
       │         │
       │         ├─ Provider: claude-code   ~/.claude/projects/{encoded}/*.jsonl
       │         ├─ Provider: gemini-cli    ~/.gemini/transcripts/*.jsonl
       │         ├─ Provider: codex         ~/.codex/sessions/*.json
       │         ├─ Provider: antigravity   ~/.antigravity/transcripts/*.md
       │         ├─ Provider: cursor        collect-cursor.py (SQLite helper)
       │         └─ Provider: copilot       %APPDATA%/GitHub Copilot Chat/sessions/*.json
       │
       ├─ 3. Run signal detectors on each Claude Code JSONL (subprocess, no LLM cost)
       │         detect-thrashing.py / detect-error-loops.py / detect-corrections.py
       │         detect-keep-going.py / detect-tool-efficiency.py
       │
       ├─ 4. Analyze (reads analyze.md for signal table + output templates)
       │
       └─ 5. Write cursor (.learn/lean.stamp)
```

Session collection for 5 of 6 providers is done entirely with the agent's native
Read/Glob tools — no helper script needed. Only Cursor requires a helper
(`collect-cursor.py`) because its sessions are stored in SQLite.

The signal detectors run as subprocesses against each JSONL file, producing
plain-text output that is folded verbatim into `friction.md`. This gives free,
deterministic pre-annotation with no LLM tokens spent.

---

## Full Flow

### Step 1 — Read cursor

- File: `.learn/lean.stamp` (Unix float timestamp, written after each successful run)
- If absent: first run — process all available sessions.
- The cursor is a default starting point. The user can ask the agent to reprocess
  everything at any time — the agent ignores the stamp.

### Step 2 — Collect sessions (native agent tools)

The agent uses Read and Glob directly. No helper script for 5 of 6 providers.

**Provider: claude-code**
- Session dir: `~/.claude/projects/{encoded}/`
- Path encoding: absolute project path, lowercase drive letter, replace `:` `\` `/` with `-`
  - `D:\Projects\Foo` → `d--Projects-Foo`
- Files: `*.jsonl`, skip `agent-*.jsonl`
- Parse each line as JSON, extract `type=user|assistant` messages
- Skip lines where content is only `tool_result` blocks (no user-visible text)
- Strip `<system-reminder>`, `<ide_selection_file>`, `<ide_opened_file>` tags
- Emit as markdown: `### **User**` / `### **Assistant**` blocks

**Provider: gemini-cli**
- Session dir: `~/.gemini/transcripts/`
- Files: `*.jsonl`
- Parse each line as JSON, extract `role=user|model` messages
- Map `model` → Assistant

**Provider: codex**
- Session dir: `~/.codex/sessions/` (Windows: `%USERPROFILE%\.codex\sessions\`)
- Files: `*.json`
- Parse JSON array of `{role, content}` objects → normalize to markdown turns

**Provider: antigravity**
- Session dir: `~/.antigravity/transcripts/`
- Files: `*.md`, emit as-is (already markdown)

**Provider: cursor**
- Requires helper — SQLite cannot be read with native tools:
  ```bash
  python tools/collect-cursor.py [--since {stamp}]
  ```
- DB: `workspaceStorage/*/state.vscdb`
- Platform paths:
  - Windows: `%APPDATA%\Cursor\User\workspaceStorage\`
  - macOS: `~/Library/Application Support/Cursor/User/workspaceStorage/`
  - Linux: `~/.config/Cursor/User/workspaceStorage/`
- Query: `SELECT value FROM ItemTable WHERE key = 'chat.sessions'`
- Parse JSON → normalize to markdown turns

**Provider: copilot**
- Session dir:
  - Windows: `%APPDATA%\GitHub Copilot Chat\sessions\`
  - macOS: `~/.config/github-copilot/sessions/`
- Files: `*.json`, parse `messages` array of `{role, content}`

### Step 3 — Run signal detectors

For each Claude Code `.jsonl` file, run all five detectors as subprocesses.
All detectors are pure Python stdlib — no dependencies, no LLM cost.

| Tool | Detects | Output when triggered |
|---|---|---|
| `detect-thrashing.py` | Same file edited 3+ times | `THRASH  {file}  ({count} edits)` |
| `detect-error-loops.py` | Same tool failing 3+ times consecutively | `ERROR-LOOP  {tool}  ({count} consecutive failures)` |
| `detect-corrections.py` | ≥20% of user turns contain correction words | `CORRECTIONS  N/total user turns (pct%)` |
| `detect-keep-going.py` | 2+ keep-going / continue prompts | `KEEP-GOING  N instance(s)` |
| `detect-tool-efficiency.py` | Read:write tool ratio ≥ 10:1 | `TOOL-EFFICIENCY  N reads  M edits  (N:M ratio)` |

Empty stdout = signal not detected. Each detector always exits 0.

### Step 4 — Analyze and write outputs

The agent reads `analyze.md` (in the skill folder) for:
- The full signal table (what patterns to look for in non-JSONL sessions)
- Output file templates for `friction.md`, `analysis.md`, `summary.md`, `proposals/`

`friction.md` includes the raw detector stdout verbatim, then the agent's own
observations. This makes the detector output visible in the project without any
post-processing.

The agent proposes anything it notices. No session-count threshold — the user
decides what to keep.

### Step 5 — Write cursor

```bash
python -c "import time, os; os.makedirs('.learn', exist_ok=True); open('.learn/lean.stamp','w').write(str(time.time()))"
```

---

## File Layout

```
LearnSkill/                         ← repo root (publishable as a standalone skill repo)
  learn/
    SKILL.md                        ← skill orchestration (loaded by SkillMCP)
    analyze.md                      ← analysis prompt resource (signal table + output templates)
    tools/
      collect-cursor.py             ← Cursor SQLite helper (only script needed)
      detect-thrashing.py           ← signal detector
      detect-error-loops.py         ← signal detector
      detect-corrections.py         ← signal detector
      detect-keep-going.py          ← signal detector
      detect-tool-efficiency.py     ← signal detector
  Design.md                         ← this file
  README.md                         ← user guide
  Maintenance.md                    ← developer notes (testing, fixtures)
  tests/
    __init__.py
    conftest.py                     ← shared helpers: run_tool(), audit(), cursor_db fixture
    fixtures/
      claude_session.jsonl          ← real Claude Code session (tool rejection + rephrasing)
      claude_thrashing.jsonl        ← synthetic: 5 edits, corrections, keep-going loops
      claude_errors.jsonl           ← synthetic: 4 consecutive Read failures
      claude_exploration.jsonl      ← synthetic: 14 reads, 1 edit (14:1 ratio)
    test_collect_cursor.py
    test_detect_thrashing.py
    test_detect_error_loops.py
    test_detect_corrections.py
    test_detect_keep_going.py
    test_detect_tool_efficiency.py
```

### Skill repository conventions

A skill repo contains exactly one skill. It can be consumed three ways:

1. **Copied** into a project's `skill_folders` path.
2. **Symlinked** from a central skills library (e.g. `~/.agents/skills/learn → /path/to/LearnSkill`).
3. **Registered** in `skillmcp.toml` directly: `skill_folders = ["/path/to/LearnSkill/learn"]`.

The repo is self-contained: tests run without SkillMCP installed, using only stdlib.

---

## Requirements

| # | Requirement |
|---|---|
| R1 | Skill runs with zero external LLM calls |
| R2 | All six session providers supported |
| R3 | Cursor timestamp used as default starting point; user can override at any time |
| R4 | Signal detectors run as subprocesses, no LLM cost, always exit 0 |
| R5 | `collect-cursor.py` and all detectors have no dependencies beyond stdlib |
| R6 | Skill works from any agent host that supports SkillMCP |
| R7 | Output always includes friction.md, analysis.md, summary.md, proposals/ |
| R8 | Cursor written only on successful completion |
| R9 | Integration tests cover all five detectors and the Cursor collector |
| R10 | `analyze.md` contains the full analysis prompt as a standalone readable resource |

---

## Verification

- [ ] Invoking the skill produces friction.md, analysis.md, summary.md in `.learn/`
- [ ] `.learn/lean.stamp` is updated after a successful run
- [ ] `uv run pytest LearnSkill/tests/` passes — 28 tests, no network or API calls
- [ ] Each detector produces correct output on its corresponding fixture
- [ ] `collect-cursor.py` returns empty list when given a directory with no `.vscdb` files
- [ ] Asking the agent to "reprocess everything" bypasses the stamp (no hard gate)
