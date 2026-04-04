# AgentFW — Hermes Install Notes

## How Hermes Loads Context Files

Hermes loads context files in this priority (first found wins for project context):
1. `.hermes.md` / `HERMES.md` — walks to git root
2. `AGENTS.md` — cwd only
3. `CLAUDE.md` — cwd only

`SOUL.md` from `~/.hermes/` is always loaded independently (identity slot).

## Install Options

### Option A: Project-level install (recommended)

Copy `HERMES.md` into your project root. It loads automatically every session when you're in that directory.

```bash
cp variants/hermes/HERMES.md /path/to/your/project/HERMES.md
```

### Option B: Global install via SOUL.md

Append to your existing `~/.hermes/SOUL.md` or replace it. This loads for every session regardless of directory.

```bash
# Append to existing SOUL.md
cat variants/hermes/HERMES.md >> ~/.hermes/SOUL.md

# Or replace (back up first)
cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak
cp variants/hermes/HERMES.md ~/.hermes/SOUL.md
```

Note: SOUL.md has a 20,000 character cap. The AgentFW core is well under that, but if you have extensive persona content already, consider project-level install instead.

### Option C: Merge with existing project context

If your project already has a HERMES.md or AGENTS.md with project-specific instructions, put AgentFW above the project-specific content:

```markdown
# AgentFW — Core Instructions (Hermes Variant)
[... AgentFW content ...]

---

# Project-Specific Instructions
[... your existing project context ...]
```

## Hermes-Specific Notes

### Subagent Dispatch
Hermes uses `delegate_task` for subagent dispatch. Key constraints:
- **Max 3 concurrent** subagents in batch mode
- **Depth limit of 2** — subagents cannot spawn further subagents
- **Blocked tools** for children: `delegate_task`, `clarify`, `memory`, `send_message`, `execute_code`
- Children get fresh context — pass ALL relevant info via the `context` field

### Toolset Scoping
Use the `toolsets` parameter to restrict what workers can do:
- `["terminal", "file"]` — general implementation work
- `["file"]` — read/write files only, no shell access
- `["terminal", "file", "web"]` — research tasks that need web access

### What's Different from Claude Code
- Claude Code has unlimited sub-agent depth. Hermes has depth 2.
- Claude Code sub-agents inherit tools automatically. Hermes requires explicit `toolsets`.
- Hermes children cannot use `execute_code` — they reason step-by-step with terminal/file tools instead.
- Hermes children cannot call `clarify` — they cannot ask the user questions. The parent must provide all necessary context upfront.

## Verify Install

Start a new Hermes session in the project directory and ask:
```
What operating framework are you running? Describe the task delegation decision tree.
```

It should mention AgentFW, Decompose-Parallelize-Verify-Iterate, and the three task tiers (one-shot, structured, long-horizon).
