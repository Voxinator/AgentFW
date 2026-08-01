# AgentFW r9 — Codex install (manual)

Current release: **AgentFW v9.4.0**. The `r9` block markers are stable major-version install
markers. v9.2.0 is deterministically verified; it carries forward v9.0.0's bounded behavioral
evidence and does not claim a new behavioral-evaluation round.

r9 ships **no installer script for Codex** — installation is a short manual procedure. Every
platform claim below was verified against official Codex documentation on 2026-07-11
(developers.openai.com/codex/* 308-redirects to learn.chatgpt.com/docs/* — URLs cited are the
pages actually fetched; per-capability citations live in `capability.yaml`).

## What gets installed (complete inventory — UNINSTALL.md removes exactly this)

| # | Artifact | Destination |
|---|---|---|
| 1 | Bootloader block (`AGENTS.md` in this adapter) | inside `~/.codex/AGENTS.md`, marker-wrapped |
| 2 | Skill (`skills/agentfw/SKILL.md`) + policy copy + validator (`tools/validate-plan`) + capability contract (`capability.yaml`) | `~/.agents/skills/agentfw/` |
| 3 | Config keys (`config.example.toml`) | merged into `~/.codex/config.toml` |

## Step 1 — Bootloader block into AGENTS.md

Codex layers instructions from a global `~/.codex/AGENTS.md`, then the repo root, then each
directory down to your cwd — closer files appear later in the merged prompt and win; the combined
stack is capped by `project_doc_max_bytes` (32 KiB default).
(Verified: https://learn.chatgpt.com/docs/agent-configuration/agents-md)

1. **Back up first:** `cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.agentfw-backup-$(date +%Y%m%d)`
   (skip if the file does not exist yet).
2. Append the FULL contents of this adapter's `AGENTS.md` to `~/.codex/AGENTS.md`, wrapped
   between exactly these two lines (each on its own line):

   ```
   <!-- AGENTFW:BEGIN r9 -->
   ...contents of adapters/codex/AGENTS.md...
   <!-- AGENTFW:END r9 -->
   ```

   The markers are what make UPGRADE.md and UNINSTALL.md clean, surgical operations — do not
   omit them, and never nest a second block inside them.
3. Your own non-AgentFW content stays outside the markers, untouched.

**Per-project alternative:** put the same marker-wrapped block in a repository-root `AGENTS.md`
instead. Global installs govern every session; repo installs govern one project. Don't do both
for the same content — the layering would duplicate it in the merged prompt.

## Step 2 — Skill placement

Codex reads user-scope skills from `$HOME/.agents/skills` (repo scope: `.agents/skills` scanned
from cwd up to the repo root; each skill is a folder whose `SKILL.md` carries `name` +
`description` frontmatter; Codex loads only name/description/path until the skill is invoked —
progressive disclosure). (Verified: https://learn.chatgpt.com/docs/build-skills)

```sh
mkdir -p ~/.agents/skills/agentfw/tools
cp adapters/codex/skills/agentfw/SKILL.md ~/.agents/skills/agentfw/SKILL.md
cp -R policy ~/.agents/skills/agentfw/policy         # from the AgentFW repo root
cp tools/validate-plan ~/.agents/skills/agentfw/tools/validate-plan   # Layer-1 validator
chmod +x ~/.agents/skills/agentfw/tools/validate-plan
cp adapters/codex/capability.yaml ~/.agents/skills/agentfw/capability.yaml   # capability contract (skill preflight reads ./capability.yaml)
```

The policy copy is what lets the skill's `policy/…` references resolve without the repo
checkout, and the validator copy is what lets the installed skill RUN Layer-1 plan validation
without one — the skill resolves `./tools/validate-plan` next to its SKILL.md first, repo
checkout second. The capability.yaml copy is what the skill's §0 capability preflight reads
(packaged beside the SKILL.md; the repo checkout is only a secondary path). The single source
of truth for all of these stays in the AgentFW repo; the installed files are copies, refreshed
on upgrade, never edited in place.

**Post-install smoke run (proves the copied validator executes):**

```sh
python3 ~/.agents/skills/agentfw/tools/validate-plan tools/fixtures/plan-good.md
# expected: PASS (exit 0), run from the AgentFW repo root for the fixture path
```

**Fallback — Codex version without skills support:** keep the files at exactly the same paths.
The bootloader already points there (`~/.agents/skills/agentfw/SKILL.md` + `policy/`) and
instructs the model to read them directly for A2+ work. You lose progressive disclosure and
`/skills` / `$agentfw` invocation — nothing else.

## Step 3 — Config merge

Merge the keys in `config.example.toml` into `~/.codex/config.toml` — **do not replace the
file**; if a key already exists, keep the stricter value. Keys and allowed values verified
against https://learn.chatgpt.com/docs/config-file/config-reference. Restart Codex afterward.

## Step 4 — Post-install verification (do not skip)

1. Start a fresh Codex session in any project.
2. Run `/skills` — the **agentfw** skill should be listed (skip on the no-skills fallback).
3. Ask: *"State your operating framework and how you classify work before acting."*
   Expect: the A0–A4 assurance model, the three derivation questions, and the
   `[ASSURANCE: Ax — …]` marker convention. An answer that names none of these means the
   bootloader block is not in the active AGENTS.md stack — check marker placement and that the
   combined stack is under the `project_doc_max_bytes` cap.
4. Give it a trivial task and confirm an `[ASSURANCE: A0 — …]` line appears before the action.

## What this install does NOT give you (honest limits)

Per `capability.yaml`: no CLI worktree isolation (desktop-app scheduled tasks only), no
platform-managed task store (plan state is files in your repo), and scheduled/background
execution is managed from the ChatGPT desktop app/web — not the CLI. The adapter never claims
these; neither should you.
