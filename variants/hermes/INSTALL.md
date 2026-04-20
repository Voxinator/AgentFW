# Hermes Variant — Installation

**Status:** pre-release. The dispatch layer is validated; the worker-quality ship gate is not yet met. See `/RELEASE-NOTES-r7.5-hermes-prerelease.md` for what this means for your use case. This file supersedes `IMPLEMENTATION.md` (frozen as historical) as the authoritative install procedure.

**Audience:** someone installing the variant from a clone of this repo onto a Mac + VM rig matching `DEPENDENCIES.md`.

---

## Prerequisites

See `DEPENDENCIES.md` for exact tested versions. Summary:

- A Mac with oMLX `0.3.6` installed, serving on `localhost:8000`, with at least one Gemma model loaded:
  - `gemma-4-31b-it-4bit` (dense, covered by r7.4 probe), or
  - `gemma-4-26B-A4B-it-MLX-8bit` (MoE, covered by r7.4 + r7.5 probes — recommended)
- Hermes Agent `v0.8.0` (`v2026.4.8`, commit `86960cdb`) on a Linux VM. Tested combo: Parallels Desktop 26.3.0 + Ubuntu 24.04.4 LTS.
- SSH alias `ubuntu-vm` in your `~/.ssh/config` pointing at the VM.
- The VM can reach oMLX at `10.211.55.2:8000`.
- `OMLX_API_KEY` exported in the operator's Mac shell (optional — only required for authenticated oMLX health probes). The probe scripts do NOT persist the key; pass it via environment.

---

## Files in this variant

### Under `variants/hermes/` (source of truth)

| File | Purpose | Current shipped state |
|------|---------|-----------------------|
| `HERMES.md` | Canonical base system prompt (no harness). Byte-identical to upstream Hermes. md5 `0780c232a6cb52e13e432261f0d68ad9`. | Frozen — do not edit. |
| `HERMES-variantB.md` | Probe sibling: hard classification contract only. | Frozen. |
| `HERMES-variantD.md` | r7 ship candidate — retained for historical re-probe. md5 `4477b8ee1d87c3a3afa9e8646168841f`. | Superseded by variantF. |
| `HERMES-variantE.md` | r7.3 sibling: escape-hatch-removed. | Superseded by variantF. |
| `HERMES-variantF.md` | **r7.5 active harness prompt** — β-fuse + turn-0 toolset restriction expectations. md5 `01c0e77bb2a6e753a8ea9063784a25e0`. | Current pre-release. |
| `delegate_worker.py` | r7 legacy single-arg dispatch tool (retained; emits deprecation notice). | Legacy. |
| `delegate_worker_v2.py` | **β-fuse tool.** Requires `classification` (`one-shot` / `structured` / `long-horizon`), `justification` (≥30 chars), and `goal` (conditionally required). md5 `d31876fe987331a26c8640202334fd46`. | Current. |
| `DESIGN.md`, `DEPENDENCIES.md`, `INSTALL.md`, `NEXT-STEPS.md`, `PROBE-RESULTS-r7.md` | Documentation. | |
| `IMPLEMENTATION.md` | Historical r7 install doc. | Frozen — use `INSTALL.md` instead. |

### At repo root (probe infrastructure, run from Mac)

| Script | What it does |
|--------|--------------|
| `probe-variantF-stage.sh` | Stage/unstage `delegate_worker_v2` + the three Hermes source patches (`model_tools.py`, `toolsets.py`, `run_agent.py` terminal-binding edits). Layers below variantG. |
| `probe-variantG-stage.sh` | Stage/unstage the r7.5 turn-0 toolset restriction hook on `run_agent.py`. Layers on top of variantF. |
| `probe-variantF-wrapper.sh`, `probe-variantF-check.py` | β-fuse-aware wrapper + gate-check analyzer (classification reads directly from `tool_calls[0].function.arguments`). |
| `probe-variantG-wrapper.sh`, `probe-variantG-check.py` | r7.5 wrapper + analyzer with SIGTERM content-match recovery (`--expected-prompt-prefix-b64`) and `ERROR:WRONG_SESSION` verdict. |
| `probe-variantD-stage.sh`, `probe-variantE-wrapper.sh`, `probe-variantE-check.py` | r7 / r7.3 predecessors. Retained for legacy re-probes. |
| `probe-omlx-health-check.sh` | Mac-side oMLX health probe (free memory, swap, loaded models). Invoke from the VM via ssh or run locally. |
| `probe-swap.sh` | Swap `HERMES.md` between canonical and a variant sibling on the VM. |
| `probe-tasks.md` | The 10 probe tasks used across all r7.x campaigns. |
| `probe-reproducibility.md` | Environment snapshot (oMLX config, model sampling, VM state). |

---

## HERMES.md, SOUL.md, and the prompt assembly

Read this section before installing if your Hermes install already has a customized `SOUL.md`, `USER.md`, or `MEMORY.md`. The variant's contract is carried by `HERMES.md`, but it shares the system prompt with those files, and their content can interact with it in ways that shift measured dispatch behavior.

### What each file is

- **`HERMES.md`** — The AgentFW harness instructions for Hermes. The canonical file lives at `~/.hermes/hermes-agent/HERMES.md` on the VM. Hermes auto-discovers it via a cwd-walk-to-git-root lookup in its prompt-builder. The variantF version (β-fuse) teaches the model to call `delegate_worker_v2` as its first action on every task.
- **`SOUL.md`** — Persona and standing behavioral rules. A Hermes-native file, NOT shipped with this variant — every operator writes their own. Loaded into the system prompt alongside `HERMES.md`.
- **`USER.md` / `MEMORY.md`** — User context (rolodex, preferences) and cross-session memory. Same injection pattern as `SOUL.md`; same operator-owned status.

### How they appear in the system prompt

Reverse-engineered from `_build_system_prompt` in `~/.hermes/hermes-agent/agent/run_agent.py` (~lines 2582-2740), the current assembly order is:

1. system role markers
2. `SOUL.md` (persona block; near the sink zone — high attention)
3. `USER.md` (user context)
4. `MEMORY.md` (cross-session memory)
5. date/time
6. platform banner
7. toolsets / tools declaration
8. active-skills list
9. skills index (large — ~11.8 KB)
10. **`HERMES.md`** (the `context_files_prompt` block)
11. active-file context (if any)
12. `PLATFORM_HINTS[cli]` (CLI markdown formatting hint)

Slot numbers are rough and may shift across Hermes versions. The load-bearing fact is that **`HERMES.md` sits at slot 10, behind the skills index, not in the recency zone** — while `SOUL.md` sits near the top (sink zone, also high attention).

### Why this matters for the variant's contract

- `HERMES.md` teaches the first-tool-call contract (`delegate_worker_v2` first). For the model to obey it, the teaching has to compete successfully against everything else in high-attention regions of the prompt.
- `SOUL.md` sits in the sink zone. Its content competes with `HERMES.md` for the model's output shaping.
- **Interaction risk:** `SOUL.md` directives that bias toward prose-first or conversational responses (e.g., "match his register", "be concise and conversational", "write naturally") can push the model away from the tool-call-first contract. Even when `HERMES.md` is explicit, a `SOUL.md` that says "answer naturally" is telling the model to generate prose before tool calls — and on a 4-bit quantized local model, that pressure sometimes wins.

### Guidance for installers

- **If you don't have a `SOUL.md` already:** start with a minimal one, or none. Without a competing persona block, `HERMES.md` is the main signal shaping output.
- **If you have a customized `SOUL.md`:** audit it before installing the variant. Red flags that can conflict with the first-tool-call contract:
  - "Be conversational" / "match register" / "write naturally"
  - "Answer concisely" / "don't be verbose"
  - Any directive that says "when X, respond with prose" without carving out tool-calling exceptions
- **Dogfood before production.** Run a representative structured task through the variant BEFORE swapping `HERMES.md` canonical on a production install. Watch for the model emitting prose before tool calls. If it happens repeatedly, your `SOUL.md` is probably dominating.
- **Don't trim `SOUL.md`/`USER.md`/`MEMORY.md` casually.** If those files are load-bearing for your working relationship with Hermes, changes need to be probed empirically — they can shift classification and dispatch behavior in non-obvious ways. See the `ARTIFACT-r7.4-phase-d-*` series for what a proper probe matrix looks like.

### Future direction (not in this pre-release)

- **IMPL-4 Option A2** — a proposed prompt-builder edit that moves `HERMES.md` from slot 10 to slot 12 (recency zone). May improve classification-first attention. Not yet landed; gated on 8 operator-decision questions about `SOUL.md`/`USER.md`/`MEMORY.md` trim scope. Full analysis in `archive/hermes-probe-r7.2-r7.3-2026-04-18/ARTIFACT-impl-4-soul-restructure.md`.
- **`HERMES-WORKER.md` analog** (r7.6 scope) — extends the first-tool-call contract to CHILD sessions, which currently have no harness-side scaffolding. Addresses the worker-quality failure modes identified in the r7.5 probe.

---

## Installation procedure

Run all commands from `/Users/briantaylor/Projects/AgentFW/` on the Mac host. Steps 2 and 3 stage VM-side patches; step 4 swaps the canonical prompt; step 5 verifies.

### Step 1 — Clone and confirm tools

```bash
git clone <your-fork-url> AgentFW
cd AgentFW
ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md'
# Expected: 0780c232a6cb52e13e432261f0d68ad9  (canonical baseline)
```

If your VM's HERMES.md md5 differs from `0780c232…`, reconcile before staging: either your fork is ahead, or a previous variant was left staged. `probe-variantF-stage.sh status` will report.

### Step 2 — Stage variantF (β-fuse dispatch)

```bash
./probe-variantF-stage.sh stage
```

This uploads `variants/hermes/delegate_worker_v2.py` to the VM and patches `model_tools.py` (+1 line import), `toolsets.py` (registers `delegate_worker_v2` in the `delegation` bundle), and `run_agent.py` (both `delegate_task` dispatch sites extended to handle `delegate_worker_v2`). All patches create `.probe-r7.4-orig` backups before editing. Idempotent — safe to re-run.

Verify:

```bash
./probe-variantF-stage.sh status
```

### Step 3 — Stage variantG (r7.5 turn-0 toolset restriction)

```bash
./probe-variantG-stage.sh stage
```

This patches `run_agent.py` with a `_resolve_tools_for_turn_r75a` method and wires it into both the Anthropic-branch and OpenAI-branch tool lists inside `_build_api_kwargs`. Creates `.probe-r7.5-orig` backup. The hook fires ONLY when the session's `enabled_toolsets` is exactly `{delegation, todo, clarify, file_readonly}` — canonical cron / hermes-cli / hermes-telegram sessions are untouched.

Verify:

```bash
./probe-variantG-stage.sh status
# Expected: "STATE: STAGED (r7.5 Variant G on top of r7.4 Variant F)"
```

### Step 4 — Swap HERMES.md to variantF

```bash
scp variants/hermes/HERMES-variantF.md ubuntu-vm:~/.hermes/hermes-agent/HERMES-variantF.md
ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && cp HERMES.md HERMES-canonical-backup.md && cp HERMES-variantF.md HERMES.md && md5sum HERMES.md'
# Expected: 01c0e77bb2a6e753a8ea9063784a25e0
```

The `HERMES-canonical-backup.md` on the VM is the rollback target. Do not delete it.

### Step 5 — Verify installation with a smoke trial

```bash
MODEL=gemma-4-26b-a4b-it-mlx-8bit TOOLSETS='delegation,todo,clarify,file_readonly' \
  ./probe-variantG-wrapper.sh smoke-01 <<'EOF'
What is 2+2? Answer in one sentence.
EOF
```

Expected `OUTCOME` line: `RESULT=COMPLIANT attempts=1` on this one-shot. If you see `VIOLATION:NO_MARKER` or `ERROR:WRONG_SESSION`, see "Known issues" below.

For a structured-class smoke, substitute a prompt from `probe-tasks.md` (T4 refactor is the most stable).

---

## Rollback

Reverse order:

```bash
# 4 — restore canonical HERMES.md
ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && cp HERMES-canonical-backup.md HERMES.md && md5sum HERMES.md'
# Expected: 0780c232a6cb52e13e432261f0d68ad9

# 3 — unstage variantG
./probe-variantG-stage.sh unstage

# 2 — unstage variantF
./probe-variantF-stage.sh unstage
```

Unstage is idempotent. Both scripts restore from their `.probe-r7.5-orig` / `.probe-r7.4-orig` backups. Post-unstage, `grep -c delegate_worker_v2 ~/.hermes/hermes-agent/run_agent.py` on the VM should report 0 (canonical has no v2 references).

---

## Known issues and their workarounds

- **SIGTERM truncation on long trials (>15 min).** The wrapper's per-trial timeout (`TIMEOUT_PER_TURN`, default 900s) can kill the Hermes parent process mid-turn, truncating the parent session JSON before the `delegate_worker_v2` tool call persists. Tier-1 mitigation is landed: `probe-variantG-wrapper.sh` passes `--expected-prompt-prefix-b64` to the analyzer, which matches a candidate session to the original prompt content before accepting it as the parent (prevents mis-attachment of a child session when the parent's `session_id:` stdout line was lost). Tier-3 mitigation (upstream Hermes SIGTERM handler) is designed (`ARTIFACT-r7.4-sigterm-research.md`) but not applied. For tasks that routinely exceed 15 min, raise `TIMEOUT_PER_TURN` via env var to 1500s+.
- **Pre-existing slice error in the v2 handler.** Observed on some r7.5 structured trials; does not block dispatch but can surface on specific tool-call shapes. Tracked for r7.6 follow-up.
- **oMLX memory-pressure accumulation on sustained dense-model runs.** Across multi-hour campaigns the dense model's engine pool state can drift. Symptom: response latency creeps up; `/health` reports degraded free memory. Mitigation: restart oMLX between campaigns. `probe-omlx-health-check.sh` is a VM-side probe that reads oMLX `/health` via SSH to the Mac (path: from VM, `ssh <mac-host-alias> bash < probe-omlx-health-check.sh`).
- **Turn-0 hook does not fire under canonical toolsets.** By design. If you invoke `hermes chat` without `-t delegation,todo,clarify,file_readonly`, the r7.5 hook short-circuits and you get vanilla variantF behavior. Verify your wrapper invocation sets `TOOLSETS` correctly.
- **Child sessions run with full Hermes toolset by default.** This is the r7.5 worker-quality ship-gate failure surface. Children dispatched via `delegate_worker_v2` inherit the full canonical toolset (not the β-fuse-restricted one) and no HERMES-WORKER.md analog — they are AgentFW-dispatched but not AgentFW-constrained. If your use case depends on child quality, read `RELEASE-NOTES-r7.5-hermes-prerelease.md` and `ARTIFACT-r7.5-SHIP-judge-verdict.md` carefully before relying on child output.

---

## How to probe your installation

Run the full campaign (20 trials across 4 tasks, 5 runs each):

```bash
MODEL=gemma-4-26b-a4b-it-mlx-8bit \
TOOLSETS='delegation,todo,clarify,file_readonly' \
TIMEOUT_PER_TURN=900 \
  ./probe-variantG-wrapper.sh t4-r1 < <(sed -n '/^## T4/,/^## T5/p' probe-tasks.md | head -N)
```

Adapt the shell fragment above to iterate T4 / T5 / T6 / T10 × runs 1–5. See `ARTIFACT-r7.5-F2-probe-results.md` for the reference matrix and `probe-tasks.md` for verbatim task prompts.

Expected numbers on this pre-release (MoE, 20 trials):
- Dispatch first-attempt strict PASS: ~16/20 (r7.5 measured; r7.4 baseline was 17/20)
- Worker-quality 5-criterion PASS: ~3/20 (r7.5 measured — BELOW the operator's 75% floor)

If your numbers differ by more than 2–3 trials in either direction, read `probe-reproducibility.md`, check oMLX health, and review `NEXT-STEPS.md` for known failure modes.

---

## Directory layout on VM after a clean install

```
~/.hermes/hermes-agent/
├── HERMES.md                             # md5 01c0e77b… (variantF active)
├── HERMES-canonical-backup.md            # md5 0780c232… (rollback target)
├── HERMES-variantF.md                    # md5 01c0e77b… (staging source)
├── tools/
│   ├── delegate_worker.py                # legacy v1 (deprecation-notice emitter)
│   └── delegate_worker_v2.py             # β-fuse tool
├── model_tools.py                        # patched (+1 import)
├── model_tools.py.probe-d-orig           # backup
├── toolsets.py                           # patched (delegation, core tools)
├── toolsets.py.probe-d-orig              # backup
├── run_agent.py                          # patched (variantF + variantG hooks)
├── run_agent.py.probe-r7.4-orig          # variantF backup
└── run_agent.py.probe-r7.5-orig          # variantG backup
```

`core/`, `references/`, `playbooks/`, `templates/`, and non-Hermes variants on the repo side are untouched throughout. Cross-model integrity is a hard constraint — if staging ever touches a file outside `variants/hermes/` or the VM's `hermes-agent/` install, stop and investigate.
