---
name: learn
description: >-
  [Learn · session analysis] Analyze recent agent sessions for friction,
  patterns, and rule proposals. Writes friction.md, analysis.md, summary.md,
  and proposals/ to .learn/. No external LLM — uses the ambient agent.
metadata:
  skill_class: analysis
  taxonomy: workflow
  discovers_with: learn,sessions,friction,patterns,rules,analyze,review,behavioral,corrections,proposals
triggers:
  - learn from sessions
  - analyze sessions
  - analyze my sessions
  - what friction did you see
  - session review
  - propose rules from sessions
---

# Session Learning (`learn`)

Analyze recent agent sessions for behavioral friction and propose improvements.
**You are the analysis engine — no external API call needed.**

---

## Step 1 — Read cursor

Read `.learn/lean.stamp`. If present, it is a Unix float timestamp — the last
successful run. Use it as a default starting point to skip already-analyzed sessions.
If absent, process all available sessions.

The user may always ask you to reprocess everything — in that case ignore the stamp.

---

## Step 2 — Collect sessions

Use your Read and Glob tools to collect sessions from each source below.

### Claude Code (JSONL)

Encode the project root path:
- Lowercase the drive letter
- Replace `:`, `\`, `/` with `-`
- Example: `/path/to/project` → `-path-to-project`

Find files: `~/.claude/projects/{encoded}/*.jsonl` — skip `agent-*.jsonl`.

For each JSONL file, extract `type=user|assistant` messages.
Skip lines where content is only `tool_result` blocks (no user-visible text).
Strip `<system-reminder>`, `<ide_opened_file>`, `<ide_selection_file>` tags.
Format as `### **User**` / `### **Assistant**` markdown blocks.

### Gemini CLI (JSONL)

Find: `~/.gemini/transcripts/*.jsonl`
Extract `role=user|model` fields. Map `model` → Assistant.

### OpenAI Codex (JSON)

Find:
- Windows: `%USERPROFILE%\.codex\sessions\*.json`
- macOS/Linux: `~/.codex/sessions/*.json`

Parse JSON array of `{role, content}` objects.

### Antigravity (Markdown)

Find: `~/.antigravity/transcripts/*.md` — read as-is.

### Cursor (SQLite)

Run the cursor collector tool:
```bash
python tools/collect-cursor.py [--since {stamp}]
```

Find `tools/collect-cursor.py` at `$SKILLS_MCP_LIBRARY/learn/tools/collect-cursor.py`
or search `.agents/skills/learn/tools/collect-cursor.py`.

### GitHub Copilot (JSON)

Find:
- Windows: `%APPDATA%\GitHub Copilot Chat\sessions\*.json`
- macOS/Linux: `~/.config/github-copilot/sessions/*.json`

Parse `messages` array of `{role, content}`.

---

## Step 3 — Run signal detectors (Claude Code JSONL only, no LLM cost)

For each Claude Code `.jsonl` file, run all five detectors.
Find tools at `$SKILLS_MCP_LIBRARY/learn/tools/` or `.agents/skills/learn/tools/`.

```bash
python tools/detect-thrashing.py       {session.jsonl}
python tools/detect-error-loops.py     {session.jsonl}
python tools/detect-corrections.py     {session.jsonl}
python tools/detect-keep-going.py      {session.jsonl}
python tools/detect-tool-efficiency.py {session.jsonl}
```

Collect the stdout from each tool. Empty output = signal not detected.
Associate each tool's output with the session file name for use in Step 4.

---

## Step 4 — Analyze and write outputs

Read `analyze.md` (in this skill folder) and follow it exactly.
It contains the signal table, output file formats, and proposal templates.

---

## Step 5 — Update cursor

```bash
python -c "import time, os; os.makedirs('.learn', exist_ok=True); open('.learn/lean.stamp','w').write(str(time.time()))"
```

---

## Done

Tell the user:
- How many sessions were analyzed and from which sources
- What signals the detectors found (quote the raw output)
- What was written to `.learn/` and where to find it
