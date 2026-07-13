# AgentFW r9 — Claude Code Upgrade

Status: draft — not eval-validated (golden-task re-run pending).

One command covers every prior state:

```bash
cd /path/to/AgentFW
tools/agentfw-install upgrade
tools/agentfw-install status   # verify
```

Your `CLAUDE.md` is always backed up to `CLAUDE.md.agentfw-backup-<YYYYMMDD-HHMMSS>` before any
edit. Non-AgentFW content is preserved in the live file in all paths below.

## Case 1 — upgrading a marked install (r9 or later re-installs)

If your `CLAUDE.md` contains an `<!-- AGENTFW:BEGIN … -->` / `<!-- AGENTFW:END … -->` block (any
version tag), the tool replaces that block **in place** with the new payload. Everything outside
the markers is untouched. If duplicate blocks somehow exist, they collapse to one.

The skill dir (`$CLAUDE_DIR/skills/agentfw/`, including its `policy/` copy and the packaged
`tools/validate-plan`) and the shipped `agentfw-*` agent files are refreshed wholesale — they are
AgentFW-owned; don't keep local edits there (put local policy in your own CLAUDE.md content or
settings instead). Upgrade also (re)writes the install manifest
(`skills/agentfw/.install-manifest`), so a later uninstall removes only what was installed.

## Case 2 — upgrading a marker-less r6/r7/r8 install

r6–r8 installed AgentFW as a whole file or plain append, with **no delimiter markers**. The tool
detects these by heading heuristics: `# AgentFW — Core Instructions` (r6/r8) or an
`Agentic Harness Framework` heading (r3-lineage). On detection it:

1. Prints what it detected and which lines it will excise.
2. Backs up the **full original file** (this backup contains the old AgentFW content — that's
   your rollback).
3. Conservatively excises the old AgentFW content — from the AgentFW heading (plus its preceding
   `<!-- AgentFW … -->` comment, if any) through the last AgentFW-known section. Trailing content
   that doesn't look like AgentFW section material (e.g. your own notes after the Reference
   Index) is left in place.
4. Keeps everything else — content before the heading and every later non-AgentFW section (your
   MCP rules, personal instructions, etc.) stays in the live file.
5. Inserts the new marked r9 block where the old content was.

### Manual-merge fallback (ambiguous detection)

If detection is ambiguous — multiple AgentFW headings, AgentFW sections interleaved with your own
sections, or a heading with no recognizable AgentFW body — the tool **refuses and changes
nothing**. It will never guess-delete user content. In that case:

1. Open `~/.claude/CLAUDE.md` and delete the old AgentFW sections yourself (everything from
   `# AgentFW — Core Instructions` through its Reference Index / Future-target note).
2. Keep your own content.
3. Re-run `tools/agentfw-install install`.

## What changes r8 → r9 (summary)

- `[TASK CLASS: …]` classification is replaced by the assurance model: `[ASSURANCE: A0–A4 — …]`
  derived from 3 questions. Old marker text in your muscle memory maps roughly: one-shot → A0/A1,
  structured → A2, long-horizon/prod → A3+.
- The always-loaded content shrinks to a ≤2,500-byte safety kernel; the full playbook moves to the
  `agentfw` skill (progressive disclosure) with the platform-neutral policy under
  `skills/agentfw/policy/`.
- Plan critique splits into Layer 1 (`tools/validate-plan`, deterministic) + Layer 2 (the
  `agentfw-plan-critic` agent, C0–C5).
- Three agent definitions and a settings example ship natively instead of prose descriptions.

## Verify after upgrade

1. `tools/agentfw-install status` — expect: block version tag r9, exactly one block, skill with
   `policy/`, validator present + executable, manifest present, three agents.
2. `grep -c 'AGENTFW:BEGIN' ~/.claude/CLAUDE.md` — expect `1`.
3. Confirm your own content survived: skim `~/.claude/CLAUDE.md` for your sections (or diff
   against the backup).
4. Smoke question in a fresh session: *"You're about to make a multi-file change to production
   code. What do you do first?"* — expect an `[ASSURANCE: …]` derivation and a reference to the
   agentfw skill / independent verification.

## Rollback

Every mutation made a timestamped backup:

```bash
ls ~/.claude/CLAUDE.md.agentfw-backup-*
cp ~/.claude/CLAUDE.md.agentfw-backup-<TIMESTAMP> ~/.claude/CLAUDE.md
```

To also drop the r9 skill/agents after rolling the file back, run
`tools/agentfw-install uninstall` — with the pre-r9 file restored it removes only the skill dir
and agent files (uninstall never deletes marker-less content).
