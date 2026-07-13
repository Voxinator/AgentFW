# AgentFW r9 — Codex upgrade (manual)

r9 is the **first** Codex release of AgentFW, so the only real upgrade case today is r9 → a
future release. The procedure below is general: it replaces any existing AgentFW marker block
regardless of version tag, and it covers the one messy case that can exist now — hand-rolled
AgentFW content pasted in before r9 without markers.

## Rule 0 — backup first, always

```sh
cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.agentfw-backup-$(date +%Y%m%d)
```

No upgrade step runs before this exists. Backups are intentionally left behind (see
UNINSTALL.md).

## Case A — marker block present (the normal case)

1. Locate the block: everything from a line containing `AGENTFW:BEGIN` through the next line
   containing `AGENTFW:END`, inclusive — **regardless of the version tag** inside the marker.
2. Replace the entire block (markers included) with the new release's marker-wrapped payload,
   e.g. for a future rX:

   ```
   <!-- AGENTFW:BEGIN rX -->
   ...contents of the new adapters/codex/AGENTS.md...
   <!-- AGENTFW:END rX -->
   ```

3. Replace the skill wholesale (it has no user-owned content):

   ```sh
   rm -rf ~/.agents/skills/agentfw
   mkdir -p ~/.agents/skills/agentfw
   cp <new-release>/adapters/codex/skills/agentfw/SKILL.md ~/.agents/skills/agentfw/SKILL.md
   cp -R <new-release>/policy ~/.agents/skills/agentfw/policy
   ```

4. Re-merge `config.example.toml` if the new release changed it — again merge, never replace,
   keep the stricter value on conflict.
5. Re-run INSTALL.md Step 4 (post-install verification). An upgrade without the verification
   step is unverified by AgentFW's own standard.

**Idempotence check:** after the replacement, `grep -c 'AGENTFW:BEGIN' ~/.codex/AGENTS.md`
MUST print `1`. More than one block means a previous upgrade appended instead of replacing —
fix that before proceeding.

## Case B — no markers, but AgentFW-looking content (hand-rolled prior install)

Someone may have pasted AgentFW material into `~/.codex/AGENTS.md` (or a repo `AGENTS.md`)
before r9 existed. Detect it by heading heuristics:

```sh
grep -nE '# AgentFW|Agentic Harness Framework|Assurance Kernel|\[TASK CLASS' ~/.codex/AGENTS.md
```

- **Unambiguous** (a clearly delimited AgentFW section — e.g. a heading like
  `# AgentFW — Core Instructions` followed only by AgentFW material until the next top-level
  heading or EOF): delete that section, then perform a fresh INSTALL.md Step 1. Diff the result
  against your backup to confirm only AgentFW material left the file.
- **Ambiguous** (AgentFW phrasing interleaved with the user's own instructions, no clean
  boundary): **refuse to auto-migrate — merge manually.** Extract the user's own lines by hand
  into the space outside the new markers, then install the fresh block. When you cannot tell
  whose sentence something is, it stays — a lost user instruction is worse than a redundant
  line.

## Case C — nothing found

No markers, no heuristic hits: there is nothing to upgrade. Follow INSTALL.md.

## Scope note

Upgrades touch exactly the three inventory items from INSTALL.md (marker block, skill dir,
config keys). If a future release changes this inventory, its UPGRADE.md must say so explicitly.
