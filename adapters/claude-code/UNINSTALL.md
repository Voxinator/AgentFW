# AgentFW r9 — Claude Code Uninstall

Status: draft — not eval-validated (golden-task re-run pending).

## Complete removal inventory

AgentFW r9 places exactly these artifacts (`$CLAUDE_DIR` = `~/.claude` unless overridden):

| Artifact | Path | Removed by uninstall |
|---|---|---|
| Bootloader block | the `<!-- AGENTFW:BEGIN … -->` … `<!-- AGENTFW:END … -->` region of `$CLAUDE_DIR/CLAUDE.md` | yes — block only; the rest of the file is preserved byte-for-byte |
| Skill | `$CLAUDE_DIR/skills/agentfw/` (includes the `policy/` copy and `tools/validate-plan`) | yes — whole directory |
| Plan validator | `$CLAUDE_DIR/skills/agentfw/tools/validate-plan` | yes — removed with the skill directory |
| Install manifest | `$CLAUDE_DIR/skills/agentfw/.install-manifest` | yes — read first (it drives agent removal), then removed with the skill directory |
| Agents | `$CLAUDE_DIR/agents/agentfw-implementer.md`, `agentfw-verifier.md`, `agentfw-plan-critic.md` | yes — exactly the manifest's agent entries (see below) |
| `CLAUDE.md` itself | `$CLAUDE_DIR/CLAUDE.md` | only if the block was its sole content (file becomes empty → removed) |
| Backups | `$CLAUDE_DIR/CLAUDE.md.agentfw-backup-*` | **no — intentionally kept** (they are your rollback) |
| Settings entries | whatever you merged from `settings.example.json` into your `settings.json` | **no — never auto-modified; remove by hand** (below) |

## One-command path

```bash
cd /path/to/AgentFW
tools/agentfw-install uninstall
```

The tool backs up `CLAUDE.md` once more before editing, removes every AGENTFW marker block (any
version tag), removes the skill dir and the manifest-recorded agent files, prints an inventory of
everything it removed plus backup locations, and deletes `CLAUDE.md` only if nothing but the block
remained.

### Manifest semantics — what uninstall will and will not remove

Install/upgrade writes `$CLAUDE_DIR/skills/agentfw/.install-manifest`: one CLAUDE_DIR-relative
installed path per line (the skill dir and each agent file the installer copied). Uninstall
removes EXACTLY:

1. the AGENTFW marker block inside `CLAUDE.md` (any version tag),
2. the skill dir `skills/agentfw/` (which consumes the manifest itself), and
3. the agent files listed in the manifest — nothing else in `$CLAUDE_DIR/agents/`.

If no manifest exists (an install predating it), uninstall falls back to the three known shipped
agent filenames — `agentfw-implementer.md`, `agentfw-verifier.md`, `agentfw-plan-critic.md` —
**never a filename glob**. Either way, agent files you created yourself are never touched, even if
they match the `agentfw-*.md` naming pattern (e.g. your own `agentfw-custom.md` survives, verified
by the test suite).

## Manual path (no scripts)

1. Edit `~/.claude/CLAUDE.md`: delete everything from the `<!-- AGENTFW:BEGIN r9 -->` line through
   the `<!-- AGENTFW:END r9 -->` line, inclusive. If the file is now empty, delete the file.
2. `rm -rf ~/.claude/skills/agentfw`
3. `rm ~/.claude/agents/agentfw-implementer.md ~/.claude/agents/agentfw-verifier.md ~/.claude/agents/agentfw-plan-critic.md`
   (remove only these shipped filenames — or the entries listed in
   `~/.claude/skills/agentfw/.install-manifest` before step 2 deletes it; never `agentfw-*.md`
   as a glob, which would also catch agents you created yourself)
4. (Optional) delete old backups: `rm ~/.claude/CLAUDE.md.agentfw-backup-*`

For a project-level install, do the same against the project's `CLAUDE.md` and `.claude/skills/`,
`.claude/agents/`.

## Verify clean removal

```bash
grep -n 'AGENTFW' ~/.claude/CLAUDE.md      # expect: no output (or "No such file")
ls ~/.claude/skills/agentfw                 # expect: No such file or directory
ls ~/.claude/agents/agentfw-*.md            # expect: no matches (except agents YOU created — those are kept)
tools/agentfw-install status                # expect: no block, skill absent, shipped agents absent
```

Also confirm your own content survived: your `CLAUDE.md` (if it still exists) should read exactly
as it did before AgentFW, minus the marker block.

## Intentionally NOT removed

- **Backups** (`CLAUDE.md.agentfw-backup-*`): kept so you can audit or roll back. Delete them
  yourself when you're confident.
- **Merged settings entries:** the installer never wrote to `settings.json`, so uninstall won't
  either. If you merged entries from `settings.example.json`, open your `settings.json` and remove
  the AgentFW additions by hand: the `permissions.allow/ask/deny` entries you added and the
  `PreToolUse` Bash hook guarding force-pushes. Compare against `settings.example.json` in this
  directory to identify them.
