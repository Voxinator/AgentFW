---
type: S8 Arm F batch 3 trial records
date: 2026-04-20
campaign: r7.7 Path A
worker: S8-F-B3
---
# Arm F batch 3 — trial records

All 5 trials in batch 3 completed synchronously, serially, and cleanly. No detachment, no background processes, no daemons. Tripwire canonical MATCH preserved across all 5 inter-trial checkpoints plus final exit. Total wall-clock: ~10 minutes 30 seconds (20:20:09 → 20:30:39) — well under the 75-minute budget.

## Staging verdict

All 6 variants staged in forward order (F → G → H → I → J-A1 → J-A2):

- `probe-variantF-stage.sh stage` — STAGED (delegate_worker_v2.py md5 `cadb49504950dc40459f95f33b38dc9f` uploaded; toolsets.py / model_tools.py / run_agent.py patched with 4 / 1 / 2 marker hits respectively; `.probe-r7.4-orig` backups in place).
- `probe-variantG-stage.sh stage` — STAGED (run_agent.py turn-0 β-fuse hook inserted in both API branches, 3 marker hits; `.probe-r7.5-orig` backup).
- `probe-variantH-stage.sh stage` — STAGED (run_agent.py Change 1(a) detection gate + Change 2 trailer with 2 marker hits and 2 trailer hits; gemma_parser.py PIPE_PATTERN_PREFIXLESS fallback with 2 hits; both py_compile OK; `.probe-r7.6-orig` backups).
- `probe-variantI-stage.sh stage` — STAGED (HERMES-WORKER.md `f866f52bbee28335964ec50d06bbac68` uploaded; delegate_tool.py overlay prepend with 2 marker hits; `.probe-r7.6-worker-orig` backup).
- `probe-variantJ-A1-stage.sh stage` — STAGED (idempotent no-op; local md5 `cadb49504950dc40459f95f33b38dc9f` equals remote; A1 patches already embedded in variantF-uploaded delegate_worker_v2.py).
- `probe-variantJ-A2-stage.sh stage` — STAGED (write_before_claim_gate.py md5 `1e01b6fb43e1948ecf78bc5f68bb919d` uploaded; run_agent.py patch (a) gate-invocation + patch (b) a2_gate_outcome session-log field applied; patched file syntax OK; `.probe-r7.7-orig` backup).

## Preflight at start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=56.7 (threshold >=20)
  swap_used_gb=4.0 (threshold <=30)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=1 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

Fresh preflight was run before every trial (4 inter-trial gates + 1 at start). All reported `PREFLIGHT=PASS` with legitimate numeric `omlx_active_sessions=0` — no `http=000` false-greens. Free memory oscillated within 42.5–56.7 GB across the batch (well above the 20 GB threshold). `swap_used_gb` held steady at 3.9–4.0. `omlx_loaded_count=1` throughout (gemma-4-26B weights resident from batch 2) — advisory only.

Tripwire canonical md5s at start:
- `HERMES.md` = `0780c232a6cb52e13e432261f0d68ad9` MATCH
- `SKILL.md` = `fb1a5a5208a6cf2fcb8252aac10397eb` MATCH

## Trial records

All trials ran serially with `HERMES_WORKER_OVERLAY=1`, `HERMES_CHILD_TOOLSET_RESTRICT=1`, `HERMES_WRITE_BEFORE_CLAIM_GATE=1` via `probe-variantJ-wrapper.sh`, invoked by `/tmp/r7.7-S8-F-B3-run-trial.sh` (clone of the B2 runner). Model: `gemma-4-26B-A4B-it-MLX-8bit`. TIMEOUT_PER_TURN=1500s. Local watchdog cap 1700s/trial. All trials exited RC=0 on attempt 0 (no retry chain, no timeouts).

| # | Task | Run | Start | End | Wall | Parent session id | Child session id(s) | a2_gate (parent) | Status | Tripwire |
|---|------|-----|-------|-----|------|-------------------|---------------------|------------------|--------|----------|
| 1 | T6 | 3 | 2026-04-20T20:20:09-05:00 | 2026-04-20T20:21:09-05:00 | 60s | `20260420_202009_3a63ff` | `20260420_202014_dbbbee` (+5s); `20260420_202043_6c92f0` (+34s); `20260420_202055_9d897f` (+46s) | CLEAN | PASS (RC=0) | MATCH |
| 2 | T10 | 3 | 2026-04-20T20:21:23-05:00 | 2026-04-20T20:23:53-05:00 | 150s | `20260420_202124_6ec63e` | `20260420_202129_a7de2c` (+5s); `20260420_202246_58f2ea` (+82s); `20260420_202324_8576fc` (+120s) | FABRICATED | PASS (RC=0) | MATCH |
| 3 | T4 | 5 | 2026-04-20T20:24:05-05:00 | 2026-04-20T20:24:35-05:00 | 30s | `20260420_202405_ed4589` | `20260420_202410_a8865b` (+5s) | CLEAN | PASS (RC=0) | MATCH |
| 4 | T5 | 5 | 2026-04-20T20:24:47-05:00 | 2026-04-20T20:29:17-05:00 | 270s | `20260420_202448_649b03` | `20260420_202452_e4e79b` (+4s) | CLEAN | PASS (RC=0) | MATCH |
| 5 | T6 | 4 | 2026-04-20T20:29:29-05:00 | 2026-04-20T20:30:39-05:00 | 70s | `20260420_202930_f3ba6e` | `20260420_202934_f17c30` (+4s); `20260420_203024_0209c5` (+54s) | CLEAN | PASS (RC=0) | MATCH |

Child session id(s) were identified by listing `/home/parallels/.hermes/sessions/` on the VM after each trial and selecting `session_*.json` files whose mtime fell within the trial's wall-clock window and whose id differed from the parent. Children appeared 4–5 seconds after the parent in every trial (first-child latency), consistent with the B1/B2 pattern. T6-run3 produced 3 children; T10-run3 produced 3 children; T6-run4 produced 2 children — consistent with multi-delegation parent turns for more complex task prompts. T4-run5 and T5-run5 each produced a single child.

`a2_gate_outcome` on parent session JSONs: **4 / 5 CLEAN, 1 / 5 FABRICATED** — T10-run3 parent (`20260420_202124_6ec63e`) reports `a2_gate_outcome=FABRICATED` from the write-before-claim detect-only gate. The other 4 parents (T6-run3, T4-run5, T5-run5, T6-run4) all report CLEAN. This is the first FABRICATED in the S8 Arm F campaign across B1+B2+B3 (both prior batches were 5/5 CLEAN). Worth noting that T10-run3's wall-clock (150s) is materially longer than B2's T10-run2 (60s), suggesting different dispatch trajectory. Per brief, this worker does not judge the meaning of the FABRICATED signal — judges will inspect the session JSONs downstream.

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

Both canonical md5s MATCH at close. No drift observed at any of the 5 inter-trial tripwire checks, nor at final post-unstage verification.

## If HALTED early

Not halted. All 5 trials in batch 3 completed successfully within ~10.5 minutes total wall-clock. No preflight FAIL, no `http=000`, no APIConnectionError, no tripwire drift, no oMLX degradation, no watchdog activations.

## Summary

- 5 / 5 trials RC=0 on attempt 0
- Total batch wall-clock: ~10.5 min (vs 75 min budget)
- Zero tripwire drift across 5 inter-trial + final verification points
- Zero halt events, zero oMLX degradation
- `a2_gate_outcome`: 4 CLEAN, 1 FABRICATED (T10-run3 parent) — first FABRICATED in S8 Arm F campaign; recorded here for downstream judge analysis
- All 5 parent sessions AND 10 child sessions persisted on VM at `/home/parallels/.hermes/sessions/session_<id>.json` for downstream judge evaluation (T6×2 produced 3+2 children; T10 produced 3; T4+T5 each produced 1)
- No daemons, no background scripts, no reparented processes — worker ran all trials synchronously in its own context per the anti-detachment hard rule
