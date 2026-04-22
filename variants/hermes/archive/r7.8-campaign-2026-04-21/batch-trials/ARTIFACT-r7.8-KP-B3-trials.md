---
type: r7.8 Arm K' batch 3 trial records
date: 2026-04-21
arm: K' (vanilla Arm A, no T1 — ablation)
worker: r7.8-KP-B3
inherited_from: r7.8-KP-B2
---

## Inherited state verification (at B3 start)

- F/G/H staged: YES (inherited from B2; B2 left staged per protocol)
- T1 patch absent: YES — `grep -c _count_consecutive_identical_tool_calls run_agent.py` = 0
- run_agent.py md5: `08dc5ff7454543292ee611c03a4c3362` — matches B2 handoff exactly, no drift
- Env flags: NO feature flags set at B3 start (clean Arm A inheritance)

## Preflight at B3 start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=50.0 (threshold >=20)
  swap_used_gb=3.0 (threshold <=30)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=1 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

## Env configuration (per-trial)

Driver: `/tmp/r7.8-KP-B3-runner.sh` — cloned from B2's `/tmp/r7.8-KP-B2-runner.sh` by `sed 's/KP-B2/KP-B3/g'`. Only `LOG_DIR`, `SOURCE_PREFIX`, and tmp-file prefixes changed (B2 → B3); all feature-flag unsets, ARM=A, and wrapper invocation remain byte-identical.

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

Log dir: `/tmp/r7.8-KP-B3-logs/`.

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children (trial-window) | Max consec | Status | OMLX | Tripwire |
|---|------|-----|-------------|-----------|------|------------|--------------------------|------------|--------|------|----------|
| 1 | T6  | 3 | 2026-04-21T08:36:00Z | 2026-04-21T08:37:35Z |  95s | 20260421_033600_52da6c | 20260421_033605_30c363, 20260421_033638_5f2685, 20260421_033712_09b365 | 1 | PASS | CLEAN | MATCH |
| 2 | T10 | 3 | 2026-04-21T08:37:41Z | 2026-04-21T08:39:21Z | 100s | 20260421_033741_21c5c6 | 20260421_033746_1e7733, 20260421_033819_c3532a | 1 | PASS | CLEAN | MATCH |
| 3 | T4  | 4 | 2026-04-21T08:39:26Z | 2026-04-21T08:40:26Z |  60s | 20260421_033926_596caf | 20260421_033930_be5530 | 1 | PASS | CLEAN | MATCH |
| 4 | T5  | 4 | 2026-04-21T08:40:29Z | 2026-04-21T08:41:39Z |  70s | 20260421_034029_bbbf90 | 20260421_034034_54b108 | 1 | PASS | CLEAN | MATCH |
| 5 | T6  | 4 | 2026-04-21T08:41:44Z | 2026-04-21T08:55:10Z | 806s | 20260421_034144_a0efbe | 20260421_034149_790236 | 1 | PASS | CLEAN | MATCH |

## Observations

- **5/5 dispatch-compliant.** Every trial returned `RESULT=COMPLIANT` without T1, HWO, A1, or A2 — F+G+H stack continues to be sufficient through the third batch as well. Cumulative K' result: 15/15 PASS across B1+B2+B3.
- **max_consec_identical_tool_calls = 1 for every trial**, parent and children. Across the combined B1+B2+B3 set (15 trials), T1 had zero work to do; the ablation remains invisible at the dispatch-compliance level.
- **T6-run4 was an 806-second outlier** (13m 26s), mirroring B2's T5-run2 (952s). Returned PASS with max_consec=1 — long wall-clock, not a loop. Only one trial-window child detected despite the long duration; the wall was dominated by a single deep sub-task rather than by decomposition churn. No SIGTERM, no 30-min cap hit, no API errors.
- **T6-run3 produced 3 trial-window children**, T10-run3 produced 2, T4-run4 and T5-run4 produced 1 each — decomposition shape remains stochastic as seen in B1/B2. All COMPLIANT.
- Total wall for 5 B3 trials: ~19m 10s (dominated by T6-run4). Well inside 75-min budget.
- Throughout the batch: OMLX_HEALTH=CLEAN, PREFLIGHT=PASS, tripwire MATCH on every trial, no SIGTERM, no http=000, no APIConnectionError, no RETRY_EXHAUSTED.

## Exit state

- F/G/H still staged: YES (stage scripts never unstaged; left as-is per protocol)
- run_agent.py md5: `08dc5ff7454543292ee611c03a4c3362` — **unchanged from B3 start, unchanged from B2 handoff, unchanged from B1 handoff** — no mid-batch mutation across three batches
- T1 patch: ABSENT at exit (`_count_consecutive_identical_tool_calls` grep = 0)
- Final preflight: PREFLIGHT=PASS, OMLX_HEALTH=CLEAN, all 4 canonical tripwires MATCH
- free_mem_gb=86.9, swap_used_gb=3.0, omlx_active_sessions=0, omlx_loaded_count=0
- No detachment; all 5 trials ran serially in-session
- No halts triggered (no SIGTERM, no tripwire drift)

## Files

- Runner: `/tmp/r7.8-KP-B3-runner.sh`
- Logs: `/tmp/r7.8-KP-B3-logs/T{4,5,6,10}-run{3,4}.log`
- Prompts: `/tmp/r7.7-S8-prompts/T{4,5,6,10}.txt` (shared with B1/B2)
