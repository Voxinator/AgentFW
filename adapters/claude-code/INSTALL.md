# AgentFW r9 — Claude Code Install

Current release: **AgentFW v9.5.0**. The `r9` block markers are stable major-version install
markers. v9.2.0 is deterministically verified; it carries forward v9.0.0's bounded behavioral
evidence and does not claim a new behavioral-evaluation round.

## Prerequisites

- Claude Code installed and run at least once (so `~/.claude/` exists — the installer creates it
  if missing).
- `bash`, `awk`, `grep`, `sed` (standard on macOS/Linux; no network access needed).
- A checkout of this AgentFW repo. The installer resolves the repo from its own location — run it
  from the checkout, don't copy the script out alone.
- The repo's `policy/` directory (part of r9). The installer copies it next to the skill so the
  skill's `./policy/` references resolve without the repo; it refuses to install without it.

## What lands where (full inventory)

| Artifact | Source | Destination | How |
|---|---|---|---|
| Bootloader block | `adapters/claude-code/CLAUDE-block.md` | `$CLAUDE_DIR/CLAUDE.md`, wrapped in `<!-- AGENTFW:BEGIN r9 -->` / `<!-- AGENTFW:END r9 -->` | appended to existing content — your text is never overwritten; the file is backed up first |
| Skill | `adapters/claude-code/skills/agentfw/` | `$CLAUDE_DIR/skills/agentfw/` | copied |
| Neutral policy | `policy/` (repo root) | `$CLAUDE_DIR/skills/agentfw/policy/` | copied |
| Plan validator | `tools/validate-plan` (repo root — single source) | `$CLAUDE_DIR/skills/agentfw/tools/validate-plan` | copied, execute bit set; the installer refuses to run without the source file |
| Agents | `adapters/claude-code/agents/agentfw-{implementer,verifier,plan-critic}.md` | `$CLAUDE_DIR/agents/` | copied |
| Install manifest | generated | `$CLAUDE_DIR/skills/agentfw/.install-manifest` | written at install/upgrade; records exactly what was installed so uninstall removes only that |
| Permissions + hooks | `adapters/claude-code/settings.example.json` | your `settings.json` | **NOT auto-modified — manual merge only** (see below) |

`$CLAUDE_DIR` defaults to `~/.claude`; the `CLAUDE_DIR` env var overrides it (used by the test
suite to run in sandboxes — you can use it to dry-run too).

## Global install (all projects)

```bash
cd /path/to/AgentFW
tools/agentfw-install install
tools/agentfw-install status   # verify
```

Behavior on an existing `~/.claude/CLAUDE.md`:

- Your file is backed up to `CLAUDE.md.agentfw-backup-<YYYYMMDD-HHMMSS>` first.
- The AgentFW block is **appended** between markers; every byte of your existing content is kept.
- Re-running `install` is idempotent: if a block already exists (any version), install behaves as
  an upgrade and replaces it in place — never a second block.
- If a marker-less r6/r7/r8 AgentFW install is detected, install hands off to the upgrade path
  (see `UPGRADE.md`).

## Project-level install (one project)

The tool targets the user level. For a single project, place the block manually:

```bash
cd /path/to/your/project
{ echo '<!-- AGENTFW:BEGIN r9 -->'; cat /path/to/AgentFW/adapters/claude-code/CLAUDE-block.md; echo '<!-- AGENTFW:END r9 -->'; } >> CLAUDE.md
mkdir -p .claude/skills .claude/agents
cp -R /path/to/AgentFW/adapters/claude-code/skills/agentfw .claude/skills/agentfw
cp -R /path/to/AgentFW/policy .claude/skills/agentfw/policy
mkdir -p .claude/skills/agentfw/tools
cp -p /path/to/AgentFW/tools/validate-plan .claude/skills/agentfw/tools/validate-plan
chmod +x .claude/skills/agentfw/tools/validate-plan
cp /path/to/AgentFW/adapters/claude-code/agents/agentfw-*.md .claude/agents/
```

Project-level CLAUDE.md is loaded in addition to the global one — don't install the block at both
levels or the kernel appears twice in context.

## Settings (manual merge — never automatic)

The installer **never touches** `settings.json`. Open
`adapters/claude-code/settings.example.json` and merge its `permissions.allow/ask/deny` entries
and the `PreToolUse` force-push-guard hook into your existing `~/.claude/settings.json` (or a
project's `.claude/settings.json`). Merge means: add the entries to your existing arrays; do not
replace the file. Adjust protected-branch names and secret paths to your environment.

## Verify

```bash
tools/agentfw-install status
```

Expect: block present (version tag r9), skill present with `policy/`, validator present +
executable at `skills/agentfw/tools/validate-plan`, install manifest present, three `agentfw-*`
agents, and the configured-state probe lines (settings deny rules yes/no/unknown).
Then start a new Claude Code session and ask a smoke question:

> "You're about to make a multi-file change to production code. What do you do first?"

The answer should derive an assurance level, emit an `[ASSURANCE: …]` marker, and mention invoking
the agentfw skill / independent verification. If it doesn't, the block didn't load — check
`status` output and restart the session.

## Uninstall / Upgrade

See `UNINSTALL.md` and `UPGRADE.md` in this directory. Both are clean and reversible: everything
the installer adds is inventoried, marked, and removable without touching your own content.
