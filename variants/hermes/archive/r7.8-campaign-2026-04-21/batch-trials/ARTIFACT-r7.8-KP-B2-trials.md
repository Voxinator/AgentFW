---
type: r7.8 Arm K' batch 2 trial records
date: 2026-04-21
arm: K' (vanilla Arm A, no T1 — ablation)
worker: r7.8-KP-B2
inherited_from: r7.8-KP-B1
---

## Inherited state verification (at B2 start)

- F/G/H staged: YES (inherited from B1; B1 left staged per protocol)
- T1 patch absent: YES — `grep -c _count_consecutive_identical_tool_calls run_agent.py` = 0
- run_agent.py md5: `08dc5ff7454543292ee611c03a4c3362` — matches B1 handoff exactly, no drift
- Env flags: NO feature flags set at B2 start (clean Arm A inheritance)

## Preflight at B2 start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=48.6 (threshold >=20)
  swap_used_gb=3.0 (threshold <=30)
  omlx_active_sessions=0 (threshold <=1)
  omlx_loaded_count=1 (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

## Env configuration (per-trial)

Driver: `/tmp/r7.8-KP-B2-runner.sh` — cloned from B1's `/tmp/r7.7-S8-prompts/run-trial-armKp.sh`, with `LOG_DIR`, `SOURCE_PREFIX`, and tmp-file prefixes renamed `B1` → `B2`. All feature-flag unsets and ARM=A prefix off remain identical.

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

Log dir: `/tmp/r7.8-KP-B2-logs/`.

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children (trial-window) | Max consec | Status | OMLX | Tripwire |
|---|------|-----|-------------|-----------|------|------------|--------------------------|------------|--------|------|----------|
| 1 | T5  | 2 | 2026-04-21T08:13:06Z | 2026-04-21T08:28:58Z | 952s | 20260421_031306_1db8bb | 20260421_031310_8ee90f, 20260421_032657_29d032, 20260421_032822_b8fb5d | 1 | PASS | CLEAN | MATCH |
| 2 | T6  | 2 | 2026-04-21T08:29:13Z | 2026-04-21T08:30:33Z |  80s | 20260421_032913_862a0b | 20260421_032918_0b82d7, 20260421_032944_8cb879, 20260421_032953_eb546f | 1 | PASS | CLEAN | MATCH |
| 3 | T10 | 2 | 2026-04-21T08:30:38Z | 2026-04-21T08:31:43Z |  65s | 20260421_033038_b33ebe | 20260421_033043_df2207 | 1 | PASS | CLEAN | MATCH |
| 4 | T4  | 3 | 2026-04-21T08:31:47Z | 2026-04-21T08:32:23Z |  36s | 20260421_033148_1f9191 | 20260421_033152_aabeba | 1 | PASS | CLEAN | MATCH |
| 5 | T5  | 3 | 2026-04-21T08:32:28Z | 2026-04-21T08:34:08Z | 100s | 20260421_033228_905b12 | 20260421_033232_865d4a, 20260421_033354_7ac1f5, 20260421_033359_67da29 | 1 | PASS | CLEAN | MATCH |

## Observations

- **5/5 dispatch-compliant.** Every trial returned `RESULT=COMPLIANT` without T1, HWO, A1, or A2 — F+G+H stack alone is sufficient on this batch as well.
- **max_consec_identical_tool_calls = 1 for every trial**, parent and children. Consistent with B1 (same result). Across the combined B1+B2 set (10 trials), T1 had zero work to do; the ablation is invisible at the dispatch-compliance level.
- **T5-run2 was a 952-second outlier** (15m 52s) but returned PASS with max_consec=1 — long wall-clock, not a loop. Three trial-window children detected, including two spawned mid-trial (16-min and 17-min marks). No SIGTERM, no 30-min cap hit, no API errors. The other four trials averaged ~70s.
- **T10-run2 produced only 1 child** (vs B1's T10-run1 which had 5). Task is stochastic in decomposition shape. Still COMPLIANT.
- Total wall for 5 B2 trials: ~20m 42s (dominated by T5-run2). Well inside 75-min budget.
- Throughout the batch: OMLX_HEALTH=CLEAN, PREFLIGHT=PASS, tripwire MATCH on every trial, no SIGTERM, no http=000, no APIConnectionError, no RETRY_EXHAUSTED.

## Exit state

- F/G/H still staged: YES (stage scripts never unstaged; left as-is per protocol)
- run_agent.py md5: `08dc5ff7454543292ee611c03a4c3362` — **unchanged from B2 start, unchanged from B1 handoff** — no mid-batch mutation
- T1 patch: ABSENT at exit (`_count_consecutive_identical_tool_calls` grep = 0)
- Final preflight: PREFLIGHT=PASS, OMLX_HEALTH=CLEAN, all 4 canonical tripwires MATCH
- free_mem_gb=48.2, swap_used_gb=3.0, omlx_active_sessions=0, omlx_loaded_count=1
- No detachment; all 5 trials ran serially in-session
- No halts triggered (no SIGTERM, no tripwire drift)

## Files

- Runner: `/tmp/r7.8-KP-B2-runner.sh`
- Logs: `/tmp/r7.8-KP-B2-logs/T{4,5,6,10}-run{2,3}.log`
- Prompts: `/tmp/r7.7-S8-prompts/T{4,5,6,10}.txt` (shared with B1)
