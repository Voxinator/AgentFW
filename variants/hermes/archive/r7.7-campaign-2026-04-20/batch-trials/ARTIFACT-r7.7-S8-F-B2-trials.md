---
type: S8 Arm F batch 2 trial records
date: 2026-04-20
campaign: r7.7 Path A
worker: S8-F-B2
---
# Arm F batch 2 — trial records

All 5 trials in batch 2 completed synchronously, serially, and cleanly. No detachment, no background processes, no daemons. Tripwire canonical MATCH preserved across all 5 inter-trial checkpoints plus final exit. Total wall-clock: ~11 minutes — well under the 75-minute budget.

## Staging verdict

All 6 variants staged in forward order (F → G → H → I → J-A1 → J-A2):

- `probe-variantF-stage.sh stage` — STAGED (delegate_worker_v2.py md5 `cadb49504950dc40459f95f33b38dc9f` uploaded; toolsets.py / model_tools.py / run_agent.py patched; `.probe-r7.4-orig` backups in place).
- `probe-variantG-stage.sh stage` — STAGED (run_agent.py turn-0 β-fuse hook inserted in both API branches, 3 marker hits; `.probe-r7.5-orig` backup).
- `probe-variantH-stage.sh stage` — STAGED (run_agent.py Change 1(a)+Change 2; gemma_parser.py PIPE_PATTERN_PREFIXLESS fallback; both py_compile OK; `.probe-r7.6-orig` backups).
- `probe-variantI-stage.sh stage` — STAGED (HERMES-WORKER.md `f866f52bbee28335964ec50d06bbac68` uploaded; delegate_tool.py overlay prepend applied with 2 marker hits; `.probe-r7.6-worker-orig` backup).
- `probe-variantJ-A1-stage.sh stage` — STAGED (idempotent no-op; local md5 `cadb49504950dc40459f95f33b38dc9f` equals remote; A1 patches already embedded in variantF-uploaded delegate_worker_v2.py).
- `probe-variantJ-A2-stage.sh stage` — STAGED (write_before_claim_gate.py md5 `1e01b6fb43e1948ecf78bc5f68bb919d` uploaded; run_agent.py patches (a) gate-invocation and (b) a2_gate_outcome session-log field applied; patched file syntax OK; `.probe-r7.7-orig` backup).

## Preflight at start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=89.7 (threshold >=20)
  swap_used_gb=4.0 (threshold <=30)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=0 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

Fresh preflight was run before every trial (4 inter-trial gates + 1 at start). All reported `PREFLIGHT=PASS` with legitimate numeric `omlx_active_sessions=0` — no `http=000` false-greens. Free memory drifted from 89.7 → 47.4 GB across the batch (expected due to model-loaded weights remaining resident), never approaching the 20 GB threshold. `omlx_loaded_count` advanced from 0 → 1 after trial 1 (gemma-4-26B weights cached) and held at 1 for the remainder — advisory only, not gate-blocking.

Tripwire canonical md5s at start:
- `HERMES.md` = `0780c232a6cb52e13e432261f0d68ad9` MATCH
- `SKILL.md` = `fb1a5a5208a6cf2fcb8252aac10397eb` MATCH

## Trial records

All trials ran serially with `HERMES_WORKER_OVERLAY=1`, `HERMES_CHILD_TOOLSET_RESTRICT=1`, `HERMES_WRITE_BEFORE_CLAIM_GATE=1` via `probe-variantJ-wrapper.sh`, invoked by `/tmp/r7.7-S8-F-B2-run-trial.sh` (clone of the B1 runner). Model: `gemma-4-26B-A4B-it-MLX-8bit`. TIMEOUT_PER_TURN=1500s. Local watchdog cap 1700s/trial. All trials landed COMPLIANT on attempt 0 (no retry chain, no timeouts).

| # | Task | Run | Start | End | Wall-clock | Parent session id | Child session id(s) | a2_gate_outcome (parent) | Status | Tripwire after |
|---|------|-----|-------|-----|------------|-------------------|---------------------|-------------------------|--------|----------------|
| 1 | T5 | 3 | 2026-04-20T20:05:46-05:00 | 2026-04-20T20:06:16-05:00 | 30s | `20260420_200547_2347e2` | `20260420_200556_fcb1aa` (+9s) | CLEAN | PASS (COMPLIANT) | MATCH |
| 2 | T6 | 2 | 2026-04-20T20:06:34-05:00 | 2026-04-20T20:14:04-05:00 | 450s | `20260420_200634_a3eec8` | `20260420_200640_e0b6c3` (+6s); `20260420_201027_43bce2` (+233s) | CLEAN | PASS (COMPLIANT) | MATCH |
| 3 | T10 | 2 | 2026-04-20T20:14:20-05:00 | 2026-04-20T20:15:20-05:00 | 60s | `20260420_201421_a1597d` | `20260420_201425_b17b47` (+4s) | CLEAN | PASS (COMPLIANT) | MATCH |
| 4 | T4 | 4 | 2026-04-20T20:15:39-05:00 | 2026-04-20T20:16:09-05:00 | 30s | `20260420_201539_619f4c` | `20260420_201545_ac9d79` (+6s) | CLEAN | PASS (COMPLIANT) | MATCH |
| 5 | T5 | 4 | 2026-04-20T20:16:22-05:00 | 2026-04-20T20:16:53-05:00 | 31s | `20260420_201623_6c58e1` | `20260420_201628_059415` (+5s) | CLEAN | PASS (COMPLIANT) | MATCH |

Child session id(s) were identified by listing `/home/parallels/.hermes/sessions/` on the VM after each trial and selecting session_*.json files whose mtime fell within the trial's wall-clock window and differed from the parent. Children appeared 4-9 seconds after the parent in 4 of 5 trials; T6-run2 also produced a second distinct child session (`20260420_201027_43bce2`) ~3.9 minutes into its 7.5-minute wall-clock — consistent with a multi-delegation parent turn. All children have `_<hash>` suffixes distinct from the parent.

Contrast with B1: batch 2 produced observable persisted child sessions for all 5 trials, whereas B1's scan found none. No infra difference between B1 and B2 staging is apparent — same variants, same env vars, same wrapper — so either child-persistence behavior is non-deterministic per task/run, or the B1 scanning method missed them. Either way, child presence is recorded here and left for judge evaluation.

`a2_gate_outcome=CLEAN` on all 5 parent session JSONs — the write-before-claim gate reports no claim-before-write violation on any parent. This is the expected outcome when the parent correctly routes work through `delegate_worker_v2` and does not emit a main-session patch/write prior to a completion claim.

Per brief, quality of worker execution (code correctness, usefulness of child output, whether synthesis met the user's actual need) is NOT judged here — this worker records trial outcomes only. Judges will evaluate session JSONs downstream.

## Unstage verdict

All 6 unstaged cleanly in reverse order (J-A2 → J-A1 → I → H → G → F):

- `probe-variantJ-A2-stage.sh unstage` — run_agent.py restored from backup; `write_before_claim_gate.py` removed; restored syntax OK.
- `probe-variantJ-A1-stage.sh unstage` — delegate_worker_v2.py restored from `.probe-r7.7-orig`.
- Residual `.probe-r7.7-orig` on delegate_worker_v2.py — removed via explicit `ssh rm -f /home/parallels/.hermes/hermes-agent/tools/delegate_worker_v2.py.probe-r7.7-orig`.
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

Not halted. All 5 trials in batch 2 completed successfully within ~11 minutes total wall-clock. No preflight FAIL, no `http=000`, no APIConnectionError, no tripwire drift, no oMLX degradation, no watchdog activations.

## Summary

- 5 / 5 trials COMPLIANT on attempt 0
- Total batch wall-clock: ~11 min (vs 75 min budget)
- Zero tripwire drift across 5 inter-trial + final verification points
- Zero halt events, zero oMLX degradation
- `a2_gate_outcome=CLEAN` on all 5 parents
- All 5 parent sessions AND 6 child sessions persisted on VM at `/home/parallels/.hermes/sessions/session_<id>.json` for downstream judge evaluation
- No daemons, no background scripts, no reparented processes — worker ran all trials synchronously in its own context per the anti-detachment hard rule
