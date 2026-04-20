# Hermes-flavored AgentFW — Implementation Guide

**Companion to:** `DESIGN.md` (architecture rationale) and `PROBE-RESULTS-r7.md` (validation data).
**Purpose:** Concrete, step-by-step install/verify/rollback for the Hermes variant. A fresh agent or human should be able to execute from this doc alone.

---

## 1. File inventory

### Source-of-truth files (in this repo, under `variants/hermes/`)

| File | Purpose | LOC |
|------|---------|-----|
| `HERMES.md` | Canonical base system prompt (no harness; byte-identical to upstream Hermes variant) | 130 |
| `HERMES-variantB.md` | Probe sibling: hard output contract only. Retained for re-probe. | ~180 |
| `HERMES-variantD.md` | **Ship candidate:** hard contract + dispatch scaffolding. Loaded as live `HERMES.md` when harness is active. | ~230 |
| `delegate_worker.py` | **Ship tool:** simplified single-arg dispatch wrapper around `delegate_task`. | ~80 |
| `DESIGN.md`, `IMPLEMENTATION.md`, `PROBE-RESULTS-r7.md`, `NEXT-STEPS.md` | Documentation | — |

### Runtime infrastructure (at project root, under `/Users/briantaylor/Projects/AgentFW/`)

| Script | Purpose |
|--------|---------|
| `probe-swap.sh` | Swap `HERMES.md` between canonical and a variant sibling (stage / swap-in / swap-out / status) |
| `probe-variantD-stage.sh` | Stage/unstage the `delegate_worker.py` tool + Hermes source patches |
| `probe-variantE-wrapper.sh` | Optional runtime retry wrapper (one trial per invocation) |
| `probe-variantE-check.py` | Gate-check logic used by the wrapper |
| `probe-tasks.md` | 10 probe tasks (regression fixtures) |
| `probe-reproducibility.md` | Environment snapshot (oMLX config, model sampling, VM state) |
| `PLAN-hermes-harness-probe.md` | The plan that drove the r7 probe (re-probe reference) |

### What gets deployed to the Hermes install

On `ubuntu-vm` (the Hermes orchestrator host):
- `~/.hermes/hermes-agent/tools/delegate_worker.py` — new file
- `~/.hermes/hermes-agent/model_tools.py` — +1 line import
- `~/.hermes/hermes-agent/toolsets.py` — +2 edits (core tools list + delegation toolset)
- `~/.hermes/hermes-agent/run_agent.py` — +2 edits (both `delegate_task` dispatch sites)
- `~/.hermes/hermes-agent/HERMES.md` — swapped to `HERMES-variantD.md` content
- `~/.hermes/hermes-agent/HERMES-canonical-backup.md` — backup of the original `HERMES.md`
- `~/.hermes/hermes-agent/{model_tools,toolsets,run_agent}.py.probe-d-orig` — backups of the three patched source files

On the Mac host (oMLX server side): nothing changes.

---

## 2. Prerequisites

### Host requirements
- Mac host running oMLX with `gemma-4-31b-it-4bit` loaded (the model Hermes calls).
- Ubuntu VM (Parallels) with Hermes Agent v0.8.x installed at `~/.hermes/hermes-agent/`.
- SSH access from Mac to VM as `ssh ubuntu-vm` (confirmed in `probe-reproducibility.md`).
- Canonical HERMES.md on the VM matches the canonical in this repo (md5 `0780c232a6cb52e13e432261f0d68ad9`). If drifted, reconcile first.

### Permission level
- Staging modifies live production Hermes source (three files). Every patch creates a `.probe-d-orig` backup first. Roll back with a single `cp` per file.
- The swap script backs up live `HERMES.md` to `HERMES-canonical-backup.md` before overwriting. Reversible via the same script.
- **Classification: `ask-first`.** Stage only when you intend to run the harness. Unstage when done.

---

## 3. Install / activate the harness

Order matters. Run from `/Users/briantaylor/Projects/AgentFW/` on the Mac host.

### Step 1 — Stage `delegate_worker` + Hermes source patches

```bash
./probe-variantD-stage.sh stage
```

What this does:
1. Uploads `variants/hermes/delegate_worker.py` to `ubuntu-vm:~/.hermes/hermes-agent/tools/delegate_worker.py` (via scp).
2. Creates `.probe-d-orig` backups of `toolsets.py`, `model_tools.py`, `run_agent.py` if not already present (idempotent — safe to re-run).
3. Patches `toolsets.py`:
   - Adds `"delegate_worker"` to `_HERMES_CORE_TOOLS` list (line ~56)
   - Adds `"delegate_worker"` to the `delegation` toolset's `tools` array (line ~193)
4. Patches `model_tools.py`:
   - Adds `"tools.delegate_worker",` to the `_modules` import list (line ~156)
5. Patches `run_agent.py`:
   - Changes `elif function_name == "delegate_task":` to `elif function_name in ("delegate_task", "delegate_worker"):` at both dispatch sites (lines ~6010 and ~6386)

Expected output:
```
[probe-variantD-stage] STAGE COMPLETE.
  delegate_worker.py on VM: md5 031df77464d3a3643be4ac7316307356
  toolsets.py.probe-d-orig + model_tools.py.probe-d-orig backups in place
```

### Step 2 — Swap in Variant D HERMES.md

```bash
scp variants/hermes/HERMES-variantD.md ubuntu-vm:~/.hermes/hermes-agent/HERMES-variantD.md
ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && cp HERMES.md HERMES-canonical-backup.md && cp HERMES-variantD.md HERMES.md && md5sum HERMES.md'
```

Expected: `4477b8ee1d87c3a3afa9e8646168841f` (Variant D md5).

Alternatively, use `probe-swap.sh` if you want its md5-verification plumbing; note it's currently hardcoded for Variant B but trivially adaptable.

### Step 3 — Verify

```bash
ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && ./venv/bin/python -c "
import model_tools
from tools.registry import registry
dw = registry._tools.get(\"delegate_worker\")
print(\"delegate_worker registered:\", dw is not None)
print(\"HERMES.md live md5:\", __import__(\"hashlib\").md5(open(\"HERMES.md\",\"rb\").read()).hexdigest())
print(\"total tools:\", len(registry._tools))
"'
```

Expected:
```
delegate_worker registered: True
HERMES.md live md5: 4477b8ee1d87c3a3afa9e8646168841f
total tools: 52
```

---

## 4. Run a single harness task (no wrapper)

Direct invocation — Gemma runs the harness on its own, no retry scaffolding:

```bash
ssh ubuntu-vm "P=\$(cat); cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q --max-turns 20 --checkpoints -q \"\$P\" --source your-task-tag" <<'TASKEOF'
<your task prompt here>
TASKEOF
```

Expected behavior on a `structured` task: Gemma's first-line marker is `[TASK CLASS: structured]`, followed by a `Justification:` line, then a `<tool_call>{"name": "delegate_worker", ...}</tool_call>` block.

Expected dispatch rate at this level: ~40% first-attempt (per r7 probe).

---

## 5. Run a single task with the runtime retry wrapper

For ~20 additional percentage points on dispatch rate:

```bash
./probe-variantE-wrapper.sh <run_id> <<'TASKEOF'
<your task prompt here>
TASKEOF
```

The wrapper:
- Runs the task; parses the resulting session JSON.
- On violation (missing marker, no dispatch, role collapse, fabrication), re-prompts via `hermes chat --resume`.
- Loops up to 3 retries. Prints one `OUTCOME` line on exit.
- Full chain log at `/tmp/varE-run<run_id>-wrapper.log`.

Expected dispatch rate with wrapper: 80% after retries (runtime-true).

The wrapper does not require any state beyond `/tmp/` and the VM-side session JSON store. Safe to invoke in parallel for different `run_id`s, but sequential recommended (Gemma inference is the bottleneck).

---

## 6. Deactivate / roll back

When you're done using the harness, or something went wrong:

### Step 1 — Restore canonical HERMES.md

```bash
ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && cp HERMES-canonical-backup.md HERMES.md && md5sum HERMES.md'
```

Expected: `0780c232a6cb52e13e432261f0d68ad9` (canonical).

### Step 2 — Unstage `delegate_worker` + source patches

```bash
./probe-variantD-stage.sh unstage
```

What this does:
1. Copies `toolsets.py.probe-d-orig` → `toolsets.py`, etc. for all three patched files.
2. Moves `tools/delegate_worker.py` to `/tmp/delegate_worker.py.probe-d-removed` (move, not delete — recoverable).
3. Leaves the `.probe-d-orig` backup files in place (harmless; useful for re-staging).

Verify by confirming `git status` on the Hermes repo shows no delegate_worker references. (Note: the user's Hermes install is a fork with other local modifications; ignore those.)

### Step 3 — Post-deactivation tripwire check

Known-good post-revert md5s for the two probe-watched files:
- `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts` → `5503ee1c2ef7d635a020eea275e41239`
- `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` → `a1dce6e989527686124d0860830627c9`

```bash
ssh ubuntu-vm 'md5sum /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh'
```

If drift detected, Gemma mutated a real file during harness execution. See the revert playbook in `archive/hermes-probe-r7-2026-04-18/ARTIFACT-revert-*.md` for surgical-revert procedure.

### Step 4 — Clean up any harness artifacts Gemma created

During structured tasks, Gemma may write `PROGRESS.md` and `PLAN.md` in `~/.hermes/hermes-agent/`. Move them out so the next session starts clean:

```bash
ssh ubuntu-vm 'mv ~/.hermes/hermes-agent/PROGRESS.md /tmp/hermes-harness-progress-$(date +%Y%m%d).md 2>/dev/null; mv ~/.hermes/hermes-agent/PLAN.md /tmp/hermes-harness-plan-$(date +%Y%m%d).md 2>/dev/null; ls /tmp/hermes-harness-*.md 2>/dev/null'
```

---

## 7. Required Hermes source patches — exact diffs

For reference or manual application if the stage script can't be used.

### `toolsets.py` (lines ~56, ~193)

```diff
- "execute_code", "delegate_task",
+ "execute_code", "delegate_task", "delegate_worker",
```

```diff
- "tools": ["delegate_task"]
+ "tools": ["delegate_task", "delegate_worker"]
```

The `sed` in `probe-variantD-stage.sh` also inserts `delegate_worker` into two composite toolsets (lines ~248 and ~276) that reference `delegate_task`. Total: 4 `delegate_worker` insertions. Harmless for composites that don't opt into the delegation toolset.

### `model_tools.py` (line ~156)

```diff
  "tools.delegate_tool",
+ "tools.delegate_worker",
  "tools.process_registry",
```

### `run_agent.py` (lines ~6009, ~6386)

```diff
- elif function_name == "delegate_task":
+ elif function_name in ("delegate_task", "delegate_worker"):
```

Both call sites inside the same method. The body of the elif remains unchanged — it calls `_delegate_task(...)` with `parent_agent=self`, which correctly routes `delegate_worker` through the underlying `delegate_task` function.

---

## 8. Verification matrix

Known good states the verification script should report:

| State | HERMES.md md5 | delegate_worker registered | source patches applied |
|-------|---------------|---------------------------|------------------------|
| **Harness active** | `4477b8ee…` (Variant D) | True | Yes |
| **Canonical / harness off** | `0780c232…` | False | No |
| **Partial stage (error)** | either | True but not patched, or inverse | investigate |

The `probe-variantD-stage.sh verify` subcommand reports this (has a cosmetic bash bug in the summary line but the per-item numbers are correct).

---

## 9. Known issues and workarounds

### SIGTERM truncation on long dispatches

When a parent session calls `delegate_worker` and the child worker takes longer than the VM-side `timeout` used in wrapper scripts (default 300s), the `timeout` signal kills the parent BEFORE its session JSON flushes the tool_call entry. The dispatch actually happened (child worker session exists on disk with the parent-issued goal), but the parent's record of it is lost.

**Workaround:** Raise the timeout in `probe-variantE-wrapper.sh` (`TIMEOUT_PER_TURN`) from 300 to 600+ seconds for tasks with long-running workers. Or, for investigation: look in `~/.hermes/sessions/` for any sessions whose first user message matches the parent's dispatch goal — that's the child that ran.

### Trial-9-style bug-hunt tasks

Gemma may classify a bug-hunt task as `structured`, investigate in the main session, conclude "no bug exists," and either re-classify to `one-shot` in the response body (first-line marker stays structured) or keep the structured marker but never dispatch. The retry wrapper can't distinguish this from "refuses to dispatch." Result: retry-exhausted.

**Current behavior:** treated as failure by the gate checker.
**Future fix:** widen the check to accept re-classification-to-one-shot (check the LATEST assistant's first line, not only the first assistant message).

### Worker quality

When dispatch fires, children occasionally:
- Run in the wrong working directory and loop
- Invent data (e.g., inventing service names for a discovery task)
- Don't return summaries before timing out

This is an r8-scope problem. For now, always spot-check worker output against ground truth before trusting it in high-stakes flows.

### Tool registration must happen before the gateway imports registry

`model_tools.py` imports happen at module load. If you stage `delegate_worker.py` but don't restart the gateway (PID 2509972 on the reproducibility snapshot), the new tool may not appear in the tool list served to the model — because Hermes's gateway process imported `model_tools` at its own startup.

**Workaround:** The Hermes CLI (`hermes chat`) spawns a new Python process per invocation, so it picks up tool changes immediately. The GATEWAY (used for Discord/messaging) does not. If using the harness via Discord, restart the gateway after staging.

---

## 10. Re-probe procedure (for confidence / regression testing)

To re-run the r7 probe sweep:

1. `./probe-variantD-stage.sh stage` — stage Variant D infrastructure
2. `./probe-swap.sh swap-in` (or manual scp+cp) — swap HERMES-variantB.md in for Variant B trials, or variantD.md for D/E
3. For each of the 10 tasks in `probe-tasks.md`:
   - Variant A/B/C/D: `ssh ubuntu-vm '... hermes chat ...'` with appropriate task text
   - Variant E: `./probe-variantE-wrapper.sh <N> <<< "<task>"`
4. Score sessions using `probe-variantE-check.py` (the wrapper does this inline)
5. Consolidate into a new `ARTIFACT-probe-variantX-trials.md`
6. Unstage everything

Full re-probe wall-clock: ~2-4 hours (Variant E with retries is the slow one).

Statistical note: N=10 total trials per variant, 5 of which are structured/long-horizon. To improve confidence, run each task twice (N=10 on structured) or add 5 more structured tasks to `probe-tasks.md`. See `NEXT-STEPS.md`.

---

## 11. Files that MUST NOT be touched during Hermes-variant work

- `/Users/briantaylor/Projects/AgentFW/core/*`
- `/Users/briantaylor/Projects/AgentFW/references/*`
- `/Users/briantaylor/Projects/AgentFW/playbooks/*`
- `/Users/briantaylor/Projects/AgentFW/templates/*`
- `/Users/briantaylor/Projects/AgentFW/variants/claude-code/*`
- `/Users/briantaylor/Projects/AgentFW/variants/claude-projects/*`
- `/Users/briantaylor/Projects/AgentFW/variants/generic/*`

Cross-model integrity is a hard requirement. If Hermes-variant work reveals a need to modify any of the above, STOP and escalate to the repo owner.
