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

3. Replace the skill wholesale (it has no user-owned content). The replacement MUST restore the
   **complete** Step 2 inventory from INSTALL.md — SKILL.md, `policy/`, the validator, AND
   `capability.yaml`. Move the old directory aside rather than deleting it, so a failed copy
   leaves a rollback:

   ```sh
   # from the new release's repo root
   mv ~/.agents/skills/agentfw ~/.agents/skills/agentfw.bak-$(date +%Y%m%d-%H%M%S)
   mkdir -p ~/.agents/skills/agentfw/tools
   cp adapters/codex/skills/agentfw/SKILL.md ~/.agents/skills/agentfw/SKILL.md
   cp -R policy ~/.agents/skills/agentfw/policy
   cp tools/validate-plan ~/.agents/skills/agentfw/tools/validate-plan
   chmod +x ~/.agents/skills/agentfw/tools/validate-plan
   cp adapters/codex/capability.yaml ~/.agents/skills/agentfw/capability.yaml
   ```

   **Why all four:** dropping `tools/validate-plan` leaves the installed skill unable to RUN
   Layer-1 plan validation, and dropping `capability.yaml` blinds the skill's §0 capability
   preflight. Both failures are silent — the skill still loads and the gate simply stops firing.
   An upgrade that restores fewer than four items is a downgrade.

4. Re-merge `config.example.toml` if the new release changed it — again merge, never replace,
   keep the stricter value on conflict.
5. Verify — **both** checks. An upgrade without them is unverified by AgentFW's own standard.

   **5a. Inventory check (mechanical).** INSTALL.md Step 4 is behavioral: it confirms the
   bootloader is loaded and markers are emitted. It CANNOT detect a partial skill copy — the
   bootloader lives in `AGENTS.md`, which an upgrade may not touch at all, so the model still
   describes A0–A4 correctly while the validator is missing. Run this from the release's repo
   root; it goes red on exactly the failure mode above:

   ```sh
   test -f ~/.agents/skills/agentfw/SKILL.md \
     && test -d ~/.agents/skills/agentfw/policy \
     && test -x ~/.agents/skills/agentfw/tools/validate-plan \
     && test -f ~/.agents/skills/agentfw/capability.yaml \
     && diff -r policy ~/.agents/skills/agentfw/policy \
     && python3 ~/.agents/skills/agentfw/tools/validate-plan tools/fixtures/plan-good.md \
     && echo INVENTORY_OK
   ```

   Expect a terminal `INVENTORY_OK` with exit 0. Any missing item, drifted policy copy, or a
   validator that will not execute fails before the signal — the signal is the check.

   **5b. Behavioral check.** Re-run INSTALL.md Step 4.

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
