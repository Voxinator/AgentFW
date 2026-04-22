---
type: r7.8 Arm K' batch 4 trial records (FINAL)
date: 2026-04-21
arm: K' (vanilla Arm A, no T1 — ablation)
worker: r7.8-KP-B4
inherited_from: r7.8-KP-B3
---

## Inherited state verification (at B4 start)

- F/G/H staged: YES (inherited from B3; B3 left staged per protocol)
- T1 patch absent: YES — `grep -c _count_consecutive_identical_tool_calls run_agent.py` = 0
- run_agent.py md5: `08dc5ff7454543292ee611c03a4c3362` — matches B3 handoff exactly, no drift across four batches
- Env flags: NO feature flags set at B4 start (clean Arm A inheritance)

## Preflight at B4 start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=86.5 (threshold >=20)
  swap_used_gb=3.0 (threshold <=30)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=0 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

## Env configuration (per-trial)

Driver: `/tmp/r7.8-KP-B4-runner.sh` — cloned from B3's `/tmp/r7.8-KP-B3-runner.sh` by `sed 's/KP-B3/KP-B4/g'`. Only `LOG_DIR`, `SOURCE_PREFIX`, and tmp-file prefixes changed (B3 → B4); all feature-flag unsets, ARM=A, and wrapper invocation remain byte-identical.

Unset/clean for every trial:
- `HERMES_WORKER_OVERLAY` unset
- `HERMES_CHILD_TOOLSET_RESTRICT` unset
- `HERMES_WRITE_BEFORE_CLAIM_GATE` unset
- `HERMES_LOOP_DETECTOR` unset

Exported:
- `ARM=A` (HWO prefix OFF in wrapper)
- `MODEL=gemma-4-26B-A4B-it-MLX-8bit`
- `TOOLSETS=delegation,todo,clarify,file_readonly`
- `OMLX_SWAP_MAX_GB=30`
- `TIMEOUT_PER_TURN=1500`

Log dir: `/tmp/r7.8-KP-B4-logs/`.

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children (trial-window) | Max consec | Status | OMLX | Tripwire |
|---|------|-----|-------------|-----------|------|------------|--------------------------|------------|--------|------|----------|
| 1 | T10 | 4 | 2026-04-21T08:57:22Z | 2026-04-21T09:01:12Z | 230s | 20260421_035722_801aae | 20260421_035731_0f73ba, 20260421_035808_178ef8, 20260421_035930_af82bf, 20260421_040026_8201b4, 20260421_040108_add1d6 | 1 | PASS | CLEAN | MATCH |
| 2 | T4  | 5 | 2026-04-21T09:01:16Z | 2026-04-21T09:01:46Z |  30s | 20260421_040116_bb008d | 20260421_040120_454694 | 1 | PASS | CLEAN | MATCH |
| 3 | T5  | 5 | 2026-04-21T09:01:49Z | 2026-04-21T09:03:24Z |  95s | 20260421_040149_6ef9b4 | 20260421_040153_d22c4f, 20260421_040216_c22eb8 | 1 | PASS | CLEAN | MATCH |
| 4 | T6  | 5 | 2026-04-21T09:03:28Z | 2026-04-21T09:06:49Z | 201s | 20260421_040329_15f444 | 20260421_040334_47e2fd, 20260421_040357_c8c0df, 20260421_040438_3dbc58, 20260421_040528_0dacea, 20260421_040607_1f25fd | 1 | PASS | CLEAN | MATCH |
| 5 | T10 | 5 | 2026-04-21T09:06:54Z | 2026-04-21T09:08:39Z | 105s | 20260421_040654_c3286c | 20260421_040700_a4cdac | 1 | PASS | CLEAN | MATCH |

## Observations

- **5/5 dispatch-compliant.** Every B4 trial returned `RESULT=COMPLIANT` without T1, HWO, A1, or A2 — F+G+H stack continues to be sufficient through the closing batch. Cumulative K' result across all batches: 20/20 PASS.
- **max_consec_identical_tool_calls = 1 for every trial**, parent and children. Across the combined B1+B2+B3+B4 set (20 trials), T1 had zero work to do; the ablation remains invisible at the dispatch-compliance level across the full run.
- **T10-run4 produced 5 trial-window children** and **T6-run5 produced 5 trial-window children** — the two highest child counts yet seen in Arm K', both still max_consec=1 and COMPLIANT. Decomposition shape remained stochastic (1, 2, or 5 children per trial in B4) as in prior batches.
- **No long-wall outliers in B4.** Longest was T10-run4 at 230s; no trial exceeded the 4-minute mark. B4 was the tightest batch by wall-clock: ~11m total vs. B2's 20m42s and B3's 19m10s. No SIGTERM, no 30-min cap hit, no API errors.
- Throughout the batch: OMLX_HEALTH=CLEAN, PREFLIGHT=PASS, tripwire MATCH on every trial, no SIGTERM, no http=000, no APIConnectionError, no RETRY_EXHAUSTED.

## Arm K' cumulative (all 4 batches)

- Total: 20 trials
- Dispatch-compliant: 20/20
- Max consec ever: 1 (was 1 in B1+B2+B3; unchanged in B4)
- Wall-clock total: ~58 minutes (B1 ~7m25s + B2 ~20m42s + B3 ~19m10s + B4 ~11m0s)

Result: the F+G+H stack alone sustains dispatch compliance for Gemma-26B-8bit across 20 trials on the S8 task suite without any loop-detection layer (T1) active. Arm K' closes as a clean ablation: T1 contributes no observed signal when F+G+H are in place.

## Unstage verdict

Unstage sequence (in order: H → G → F → cosmetic r7.7 v2 cleanup):

```
./probe-variantH-stage.sh unstage  → UNSTAGE COMPLETE (run_agent.py + gemma_parser.py restored from .probe-r7.6-orig)
./probe-variantG-stage.sh unstage  → UNSTAGE COMPLETE (run_agent.py restored from .probe-r7.5-orig)
./probe-variantF-stage.sh unstage  → UNSTAGE COMPLETE (toolsets.py + model_tools.py + run_agent.py restored from .probe-r7.4-orig; delegate_worker_v2.py moved out of tools/)
rm -f .../tools/delegate_worker_v2.py.probe-r7.7-orig  → (cosmetic, no-op: file was not present)
```

Verify:

- **run_agent.py md5 restored to baseline `94ad8712678df5e96b9f407446edf249`: YES** — matches spec exactly.
- **All variants unstaged: YES** — H + G + F stage scripts all reported UNSTAGE COMPLETE with verified "no stray marker" checks.
- **Final HERMES.md md5: `0780c232a6cb52e13e432261f0d68ad9` MATCH canonical** (spec prefix `0780c232...`).
- **.probe-r7*orig residue: NOT empty but canonical-backup-chain only** — `ls ~/.hermes/hermes-agent/*.probe-r7*orig ~/.hermes/hermes-agent/tools/*.probe-r7*orig ~/.hermes/hermes-agent/environments/tool_call_parsers/*.probe-r7*orig` returns 8 files: the r7.3/r7.4/r7.5/r7.6 pristine backups (timestamped April 18–19, i.e. pre-dating this session's staging) that the F/G/H stage scripts rely on for idempotent restore. These are NOT mid-run mutations; they are the stage-rollback backing store. The r7.7 cosmetic file named in spec (`tools/delegate_worker_v2.py.probe-r7.7-orig`) IS absent (rm -f cleaned or it was never present). No r7.7- or r7.8-era orig files exist on the VM. Flagging for the parent.
- **Final preflight: PASS** — `[GATE: tripwire] PASS (all 4 canonical)` confirms live `run_agent.py`, `HERMES.md`, `toolsets.py`, and `gemma_parser.py` all match canonical; free_mem_gb=50.5, swap_used_gb=3.0, omlx_active_sessions=0.

## Exit state

- F/G/H **unstaged** (all three): run_agent.py, HERMES.md, toolsets.py, gemma_parser.py, model_tools.py all match canonical. Variant F's `delegate_worker_v2.py` relocated to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`.
- run_agent.py md5 at exit: `94ad8712678df5e96b9f407446edf249` — VM canonical baseline restored.
- T1 patch: ABSENT (never applied in Arm K').
- Final preflight: PREFLIGHT=PASS, OMLX_HEALTH=CLEAN, all 4 canonical tripwires MATCH.
- No detachment; all 5 trials ran serially in-session.
- No halts triggered (no SIGTERM, no tripwire drift).
- Wall-budget used: ~15 min (of 75-min budget).

## Files

- Runner: `/tmp/r7.8-KP-B4-runner.sh`
- Logs: `/tmp/r7.8-KP-B4-logs/T{4,5,6,10}-run{4,5}.log`
- Summary: `/tmp/r7.8-KP-B4-summary.log`
- Prompts: `/tmp/r7.7-S8-prompts/T{4,5,6,10}.txt` (shared across all K' batches)
