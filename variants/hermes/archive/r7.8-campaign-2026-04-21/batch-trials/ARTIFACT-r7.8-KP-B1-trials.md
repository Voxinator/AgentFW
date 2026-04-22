---
type: r7.8 Arm K' batch 1 trial records
date: 2026-04-21
arm: K' (vanilla Arm A, no T1 — ablation)
worker: r7.8-KP-B1
---

## Staging
- F/G/H staged: YES (all three probe-variant stage scripts reported STAGE COMPLETE)
- T1 patch absent: YES
  - Pre-staging: `grep -c _count_consecutive_identical_tool_calls run_agent.py` = 0
  - Pre-staging: run_agent.py md5 = 94ad8712678df5e96b9f407446edf249 (baseline match)
  - Post-staging: md5 = 08dc5ff7454543292ee611c03a4c3362 (F+G+H modifications, expected)
  - Post-staging: T1 marker count still 0 — confirmed
- Backups present: 5 probe-*-orig files (F writes 3, G writes 1, H writes 2; count 5 after G/H override F's run_agent.py backup — expected layering)

## Preflight at start
```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=57.6 (threshold >=20)
  swap_used_gb=3.0 (threshold <=30)
  omlx_active_sessions=unknown (oMLX unreachable (http=000) — cold-start; became CLEAN before trial 1)
  omlx_loaded_count=unknown (advisory)
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

## Env configuration (per-trial)

Driver: `/tmp/r7.7-S8-prompts/run-trial-armKp.sh` (newly created — vanilla Arm A with explicit unsets).

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

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children (trial-window) | Max consec | Status | Tripwire |
|---|------|-----|-------------|-----------|------|------------|--------------------------|------------|--------|----------|
| 1 | T4 | 1 | 2026-04-21T08:03:50Z | 2026-04-21T08:04:30Z | 40s | 20260421_030350_dd4c5b | 20260421_030359_4390bc | 1 | PASS | MATCH |
| 2 | T5 | 1 | 2026-04-21T08:04:33Z | 2026-04-21T08:05:44Z | 71s | 20260421_030434_9d0df9 | 20260421_030438_a82e3d (+1 stale from T4) | 1 | PASS | MATCH |
| 3 | T6 | 1 | 2026-04-21T08:05:47Z | 2026-04-21T08:07:47Z | 120s | 20260421_030547_a4ecad | 20260421_030551_85f6e5, 20260421_030625_ca7858, 20260421_030719_b53500 | 1 | PASS | MATCH |
| 4 | T10 | 1 | 2026-04-21T08:07:51Z | 2026-04-21T08:10:36Z | 165s | 20260421_030751_fee309 | 20260421_030756_68a38a, 20260421_030828_ad2d49, 20260421_030859_7a218d, 20260421_030928_3c2c5d, 20260421_031016_0d9ee5 | 1 | PASS | MATCH |
| 5 | T4 | 2 | 2026-04-21T08:10:40Z | 2026-04-21T08:11:15Z | 35s | 20260421_031041_418596 | 20260421_031045_ff7f84 | 1 | PASS | MATCH |

Notes on child-session count: the trial-window detection (mtime > START - 5s) includes any session touched during the trial. Cross-trial bleed-through is harmless; the parent SID is authoritative. All reported parents are distinct per trial.

## Observations

- 5/5 dispatch-compliant. Every trial returned `RESULT=COMPLIANT` with no HWO, no A1, no A2, no T1 — i.e. the F+G+H stack alone is sufficient on this batch.
- **max_consec_identical_tool_calls = 1 for every trial**, parent and children. No consecutive-identical repetition observed anywhere in this batch. This is the comparison-relevant metric vs Arm K (which had 6 T1 WARNs, mostly on T10). On this batch, T1 had no work to do — the absence of T1 is **invisible** at the dispatch-compliance level.
- Total wall for 5 trials: ~7 min 25s. Well inside 75-min budget.
- T10-run1 spawned the most children (5), matching its known decomposition shape; all children finished cleanly and the parent returned COMPLIANT.
- Throughout the batch: OMLX_HEALTH=CLEAN, PREFLIGHT=PASS, tripwire MATCH, no SIGTERM, no http=000, no APIConnectionError, no RETRY_EXHAUSTED.

## Exit state
- F/G/H still staged: YES (stage scripts never unstaged; left as-is for B2 inheritance per protocol)
- run_agent.py md5: `08dc5ff7454543292ee611c03a4c3362` (F+G+H-patched; unchanged from post-staging baseline — no worker mutated it mid-batch)
- T1 patch: ABSENT at exit (`_count_consecutive_identical_tool_calls` grep = 0)
- Final preflight: PREFLIGHT=PASS, OMLX_HEALTH=CLEAN, all 4 canonical tripwires MATCH
- free_mem_gb=45.6, swap_used_gb=3.0, omlx_active_sessions=0
- No detachment; all trials ran serially in-session

## Handoff note for B2

B2 inherits F+G+H staged, T1 absent, md5 = 08dc5ff7454543292ee611c03a4c3362, no feature env flags set. Logs at `/tmp/r7.8-KP-B1-logs/`. Trial driver at `/tmp/r7.7-S8-prompts/run-trial-armKp.sh`.
