---
type: S8 Arm F batch 4 (final) trial records
date: 2026-04-20
campaign: r7.7 Path A
worker: S8-F-B4
---
# Arm F batch 4 — trial records

All 3 trials in batch 4 completed synchronously, serially, and cleanly. No detachment, no background daemons, no reparented processes. Tripwire canonical MATCH preserved across all 3 inter-trial checkpoints plus final post-unstage verification. Total wall-clock: ~24.3 minutes (20:33:59 → 20:58:18) — well under the 45-minute budget. All 3 trials exited RC=0 on attempt 0; no retries, no watchdog activations, no APIConnectionErrors.

## Staging verdict

All 6 variants staged in forward order (F → G → H → I → J-A1 → J-A2):

- `probe-variantF-stage.sh stage` — STAGED (delegate_worker_v2.py md5 `cadb49504950dc40459f95f33b38dc9f` uploaded; toolsets.py / model_tools.py / run_agent.py patched with 4 / 1 / 2 marker hits respectively; `.probe-r7.4-orig` backups in place).
- `probe-variantG-stage.sh stage` — STAGED (run_agent.py turn-0 β-fuse hook inserted with 3 marker hits; `.probe-r7.5-orig` backup).
- `probe-variantH-stage.sh stage` — STAGED (run_agent.py Change 1(a) detection gate + Change 2 trailer 2 marker / 2 trailer hits; gemma_parser.py PIPE_PATTERN_PREFIXLESS fallback 2 hits; both py_compile OK; `.probe-r7.6-orig` backups).
- `probe-variantI-stage.sh stage` — STAGED (HERMES-WORKER.md `f866f52bbee28335964ec50d06bbac68` uploaded; delegate_tool.py overlay prepend 2 marker hits; `.probe-r7.6-worker-orig` backup).
- `probe-variantJ-A1-stage.sh stage` — STAGED (idempotent no-op; local md5 equals remote; A1 patches already embedded in variantF-uploaded delegate_worker_v2.py).
- `probe-variantJ-A2-stage.sh stage` — STAGED (write_before_claim_gate.py md5 `1e01b6fb43e1948ecf78bc5f68bb919d` uploaded; run_agent.py patch (a) gate-invocation + patch (b) a2_gate_outcome session-log field applied; patched file syntax OK; `.probe-r7.7-orig` backup).

## Preflight at start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=59.2 (threshold >=20)
  swap_used_gb=3.9 (threshold <=30)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=1 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

Fresh preflight was run before every trial (2 inter-trial gates + 1 at start). All reported `PREFLIGHT=PASS` with legitimate numeric `omlx_active_sessions=0` — no `http=000` false-greens. Free memory oscillated within 41.0–59.2 GB across the batch (well above the 20 GB threshold). `swap_used_gb` held steady at 3.8–3.9. `omlx_loaded_count=1` throughout (gemma-4-26B weights resident from prior batches) — advisory only.

Tripwire canonical md5s at start:
- `HERMES.md` = `0780c232a6cb52e13e432261f0d68ad9` MATCH
- `SKILL.md` = `fb1a5a5208a6cf2fcb8252aac10397eb` MATCH

## Trial records

All trials ran serially with `HERMES_WORKER_OVERLAY=1`, `HERMES_CHILD_TOOLSET_RESTRICT=1`, `HERMES_WRITE_BEFORE_CLAIM_GATE=1` via `probe-variantJ-wrapper.sh`, invoked by `/tmp/r7.7-S8-F-B4-run-trial.sh` (clone of the B3 runner — no path substitutions needed; runner uses `$SOURCE_PREFIX` parameter). Model: `gemma-4-26B-A4B-it-MLX-8bit`. TIMEOUT_PER_TURN=1500s. Local watchdog cap 1700s/trial. All trials exited RC=0 on attempt 0.

| # | Task | Run | Start | End | Wall | Parent session id | Child session id(s) | a2_gate (parent) | Status | Tripwire |
|---|------|-----|-------|-----|------|-------------------|---------------------|------------------|--------|----------|
| 1 | T10 | 4 | 2026-04-20T20:33:59-05:00 | 2026-04-20T20:49:20-05:00 | 921s | `20260420_203359_e9f686` | `20260420_203405_a2c18f` (+6s); `20260420_203435_ad359e` (+36s); `20260420_204849_bec3b9` (+14m50s) | CLEAN | PASS (RC=0) | MATCH |
| 2 | T6  | 5 | 2026-04-20T20:49:48-05:00 | 2026-04-20T20:51:28-05:00 | 100s | `20260420_204949_9db097` | `20260420_204954_688f43` (+5s); `20260420_205004_95b924` (+15s); `20260420_205042_b58b3a` (+53s) | CLEAN | PASS (RC=0) | MATCH |
| 3 | T10 | 5 | 2026-04-20T20:51:58-05:00 | 2026-04-20T20:58:18-05:00 | 380s | `20260420_205158_780a70` | `20260420_205203_fb527e` (+5s); `20260420_205239_c5c9a3` (+41s) | FABRICATED | PASS (RC=0) | MATCH |

Child session id(s) were identified by listing `/home/parallels/.hermes/sessions/` on the VM after each trial and selecting `session_*.json` files whose mtime fell within the trial's wall-clock window and whose id differed from the parent. Children appeared 5–6 seconds after the parent in every trial (first-child latency), consistent with the B1/B2/B3 pattern. T10-run4 and T6-run5 each produced 3 children; T10-run5 produced 2 children — consistent with multi-delegation parent turns for the more complex T6/T10 prompts.

T10-run4 wall-clock (921s / 15m21s) is the longest single trial observed across S8 Arm F B1-B4. The third child (`20260420_204849_bec3b9`) materialized at +14m50s from parent start, suggesting an extended synthesis or late-cycle delegation tail. Parent RC=0 from the runner, so no turn timeout fired (TIMEOUT_PER_TURN=1500s was not breached). T10-run5 wall-clock (380s) falls between B2 T10-run2 (60s) and B3 T10-run3 (150s) and this batch's T10-run4 (921s) — indicating real variance in T10 trajectory length independent of staging.

`a2_gate_outcome` on parent session JSONs: **2 / 3 CLEAN, 1 / 3 FABRICATED** — T10-run5 parent (`20260420_205158_780a70`) reports `a2_gate_outcome=FABRICATED` from the write-before-claim detect-only gate. T10-run4 and T6-run5 parents both report CLEAN. This is the second FABRICATED in the S8 Arm F campaign (first was T10-run3 in B3). Both FABRICATED signals are on T10 (task 10), suggesting task-class correlation worth downstream judge analysis. Per brief, this worker does not judge meaning of FABRICATED — judges will inspect session JSONs downstream.

Per brief, quality of worker execution (code correctness, usefulness of child output, whether synthesis met the user's actual need) is NOT judged here — this worker records trial outcomes only.

## Unstage verdict

All 6 unstaged cleanly in reverse order (J-A2 → J-A1 → I → H → G → F):

- `probe-variantJ-A2-stage.sh unstage` — run_agent.py restored from backup; `write_before_claim_gate.py` removed; restored syntax OK.
- `probe-variantJ-A1-stage.sh unstage` — delegate_worker_v2.py restored from `.probe-r7.7-orig`.
- Residual `.probe-r7.7-orig` on delegate_worker_v2.py — removed via explicit `ssh rm -f /home/parallels/.hermes/hermes-agent/tools/delegate_worker_v2.py.probe-r7.7-orig` (returned `RESIDUE_CLEANUP_OK`).
- `probe-variantI-stage.sh unstage` — delegate_tool.py restored from `.probe-r7.6-worker-orig`; no stray `_r76_worker_overlay` markers; HERMES-WORKER.md removed from `~/.hermes/hermes-agent/`.
- `probe-variantH-stage.sh unstage` — run_agent.py + gemma_parser.py restored from `.probe-r7.6-orig`; no stray r7.6 markers.
- `probe-variantG-stage.sh unstage` — run_agent.py restored from `.probe-r7.5-orig`; no stray `_resolve_tools_for_turn_r75a` references.
- `probe-variantF-stage.sh unstage` — toolsets.py + model_tools.py + run_agent.py restored from `.probe-r7.4-orig`; `tools/delegate_worker_v2.py` moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`; no stray `delegate_worker_v2` references in patched files.

Post-unstage residue scan for `.probe-r7.7-orig` files anywhere under `/home/parallels/.hermes/hermes-agent/`: EMPTY. Zero r7.7 backups remain on VM.

## Final VM canonical

```
0780c232a6cb52e13e432261f0d68ad9  /home/parallels/.hermes/hermes-agent/HERMES.md                                                        MATCH
fb1a5a5208a6cf2fcb8252aac10397eb  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md                    MATCH
```

Both canonical md5s MATCH at close. No drift observed at any of the 3 inter-trial tripwire checks, nor at final post-unstage verification.

## If HALTED early

Not halted. All 3 trials in batch 4 completed successfully within ~24.3 minutes total wall-clock. No preflight FAIL, no `http=000`, no APIConnectionError, no tripwire drift, no oMLX degradation, no watchdog activations.

## Summary

- 3 / 3 trials RC=0 on attempt 0
- Total batch wall-clock: ~24.3 min (vs 45 min budget)
- Zero tripwire drift across 3 inter-trial + final verification points
- Zero halt events, zero oMLX degradation
- `a2_gate_outcome`: 2 CLEAN, 1 FABRICATED (T10-run5 parent) — second FABRICATED in S8 Arm F campaign; both FABRICATED instances are on T10, warranting downstream judge attention to task-class correlation
- All 3 parent sessions AND 8 child sessions persisted on VM at `/home/parallels/.hermes/sessions/session_<id>.json` for downstream judge evaluation (T10-run4: 3 children; T6-run5: 3 children; T10-run5: 2 children)
- No daemons, no background scripts, no reparented processes — worker ran all trials synchronously in its own context per the anti-detachment hard rule
- T10-run4 (921s / 15m21s) is the longest single trial observed across S8 Arm F B1-B4; third child materialized at +14m50s from parent start without breaching TIMEOUT_PER_TURN=1500s
- Arm F campaign totals across B1+B2+B3+B4: 18 / 18 trials RC=0, 16 CLEAN + 2 FABRICATED (both on T10)
