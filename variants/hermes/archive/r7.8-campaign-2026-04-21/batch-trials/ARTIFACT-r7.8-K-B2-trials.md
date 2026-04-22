---
type: r7.8 Arm K batch 2 trial records
date: 2026-04-21
arm: K (vanilla + T1 loop detector)
worker: r7.8-K-B2
---
# Arm K batch 2 — trial records

Continuation of Arm K (vanilla Arm A stack + T1 cross-turn loop detector via `HERMES_LOOP_DETECTOR=1`). Variants F+G+H inherited-staged from B1 on top of T1-patched baseline. Toolsets: `delegation,todo,clarify,file_readonly`. Model: `gemma-4-26B-A4B-it-MLX-8bit`. `TIMEOUT_PER_TURN=1500`, wall-cap=1800s/trial.

## Staging verification at start

Inherited from B1 — no re-staging needed.

- `run_agent.py` md5 = `3ceda6072461e068902bf97c3988667c` (matches B1 exit md5, matches P3c vet)
- `_count_consecutive_identical_tool_calls` marker count = 2 (helper + hook, unchanged)
- Backup `run_agent.py.probe-r7.8-t1-orig` present on VM
- `probe-variantJ-wrapper.sh` `HERMES_LOOP_DETECTOR=1` forwarder present (lines 65-66)
- Tripwire pre-batch: HERMES.md `0780c232a6cb52e13e432261f0d68ad9`, jira-daily-briefing SKILL.md `fb1a5a5208a6cf2fcb8252aac10397eb` (canonical)

Preflight at start:
```
PREFLIGHT=PASS
  agent_dispatch=PASS
  omlx=CLEAN (0 active sessions, 0 loaded)
  tripwire=PASS (all 4 canonical)
  vm_idle=PASS
  free_mem_gb=94.4  swap_used_gb=3.0
```

Runner: `/tmp/r7.8-K-B2-runner.sh` (cloned from B1, updated LOG_DIR → `/tmp/r7.8-K-B2-logs`, SOURCE_PREFIX → `probe-r7.8-K-B2-<task>`, TRIALS → T5-r2, T6-r2, T10-r2, T4-r3, T5-r3).

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children | T1 fired? | Max consec | Status | Tripwire |
|---|------|-----|-------------|-----------|------|------------|----------|-----------|------------|--------|----------|
| 1 | T5   | 2   | 06:59:42    | 07:00:52  | 70s   | `20260421_015942_47afc4` | 2 | no | 2 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 2 | T6   | 2   | 07:00:52    | 07:05:22  | 270s  | `20260421_020053_820cf9` | 4 | no | 4 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 3 | T10  | 2   | 07:05:23    | 07:10:43  | 320s  | `20260421_020523_372164` | 3 | **YES** (child1) | **5** | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 4 | T4   | 3   | 07:10:43    | 07:11:33  | 50s   | `20260421_021044_a3bcb7` | 1 | no | 1 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 5 | T5   | 3   | 07:11:34    | 07:16:54  | 320s  | `20260421_021134_b20e04` | 4 | **YES** (child4) | **5** | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |

Total batch wall: ~1030s (~17 min). All trials returned `RESULT=COMPLIANT attempts=1`.

### Child session IDs (time-clamped + content-matched)

Children matched to each parent by time-adjacency (within parent wall window) + first-user-content task match. Shared SIDs (e.g., `20260421_020056_991c6a` which falls in both T5-r2 and T6-r2 windows) assigned to the parent whose task topic matches the child's delegation prompt.

- **T5-r2** → children:
  - `20260421_015951_f67af1` (msgs=33, max_consec=2) — "Investigate and fix intermittent stale data issue in Chief of Staff Dashboard"
  - `20260421_020026_fd7ffc` (msgs=22, max_consec=1) — "Unable to find directory /media/psf/Projects/chief-of-staff-dashboard"
- **T6-r2** → children:
  - `20260421_020056_991c6a` (msgs=42, max_consec=4) — "Phase 1: Discovery & Planning"
  - `20260421_020208_6e75bc` (msgs=18, max_consec=1) — "Previous worker reported completing Phase 1 but PLAN.md cannot be found"
  - `20260421_020231_7973e7` (msgs=92, max_consec=3) — "Previous attempts to locate PLAN.md have failed"
  - `20260421_020349_f18b6e` (msgs=42, max_consec=2) — "Previous workers failed to provide usable PLAN.md"
- **T10-r2** → children:
  - `20260421_020528_e7ccff` (msgs=33, **max_consec=5 — T1 WARN FIRED**) — pg-upgrade-2026 migration PLAN.md creation
  - `20260421_020602_961d66` (msgs=7, max_consec=2) — retry of same migration PLAN
  - `20260421_020618_819c88` (msgs=8, max_consec=1) — retry with explicit path
- **T4-r3** → children:
  - `20260421_021049_db76bb` (msgs=46, max_consec=1) — "Refactor auth module to use new session store"
- **T5-r3** → children:
  - `20260421_021139_e4bba2` (msgs=92, max_consec=4) — "Investigate and fix stale data in chief-of-staff-dashboard"
  - `20260421_021329_7d5780` (msgs=6, max_consec=1) — "Implement fix for race condition in storage.ts"
  - `20260421_021341_538b12` (msgs=42, max_consec=2) — "Verify fix for stale data issue"
  - `20260421_021412_1a3cfb` (msgs=67, **max_consec=5 — T1 WARN FIRED**) — "Find correct path for project"

### T1 firing check

Scanned all child session JSONs for "consecutive identical tool calls", "loop_detected", "loop detector", and "r7.8 loop" markers. **Two firings observed:**

1. **T10-r2 / child1 `20260421_020528_e7ccff`** — msg[31] (role=user) contains the warn injection:
   > `[System: r7.8 loop detector — you have emitted the same tool call (todo) 5 turns in a row. If this is not intentional, stop calling tools and produce a natural-language summary explaining what you have found, what you could not find, and the concrete blocker. One more identical call will terminate the session.]`
   
   The repeating call was `todo`. After the warn, no 6th identical call was emitted — session ended organically within the next couple of turns without a TERMINATE. Parent T10-r2 still returned COMPLIANT on first attempt.

2. **T5-r3 / child4 `20260421_021412_1a3cfb`** — msg[65] (role=user) contains identical warn injection, also triggered by 5 consecutive `todo` calls. No subsequent TERMINATE; session ended organically. Parent T5-r3 also COMPLIANT on first attempt.

Wrapper-log scan (`/tmp/r7.8-K-B2-logs/*.log`) for "r7.8 loop detector" string: **0 hits** (the warn lives in the child session JSON, not in the wrapper stderr/stdout stream, which is consistent with the patch design — injection goes into the conversation, not into orchestration logs).

Compared to B1 (zero T1 firings, one near-miss at max_consec=5 in T10-r1/child2), B2 has **two confirmed T1 WARN injections** on trials with the same "stuck repeating `todo`" failure mode. The fact that in both cases the child course-corrected after warn (no 6th call, no TERMINATE) and the parent dispatch still reached COMPLIANT is the first in-run evidence that T1's warn injection has behavioral effect.

### Tripwire checks

Post each trial: `probe-preflight.sh --skip-omlx --skip-vm-idle` returned PREFLIGHT=PASS. Full preflight post-trial returned OMLX_HEALTH=CLEAN each time. At batch end:
- HERMES.md md5 = `0780c232a6cb52e13e432261f0d68ad9` (canonical, unchanged)
- jira-daily-briefing SKILL.md md5 = `fb1a5a5208a6cf2fcb8252aac10397eb` (canonical, unchanged)
- All 4 canonical tripwire files intact

No SIGTERM observed in any hermes-chat process. No APIConnectionError. No http=000. oMLX CLEAN after every trial.

## Exit state

- **T1 still staged:** YES (run_agent.py md5 = `3ceda6072461e068902bf97c3988667c`, helper+hook present, backup intact at `run_agent.py.probe-r7.8-t1-orig`)
- **variantF/G/H still staged:** YES (md5 matches P3c vet, no modifications during B2)
- **Wrapper mod (HERMES_LOOP_DETECTOR forwarding):** still present (lines 65-66 of `probe-variantJ-wrapper.sh`)
- **Final preflight:** PREFLIGHT=PASS (free_mem_gb=50.4, swap_used_gb=3.0, omlx_active=0, omlx_loaded=1, tripwire=PASS, vm_idle=PASS)
- **Final tripwire:** MATCH
- **VM canonical for a K-arm continuation:** YES — batch 3 can run against current state without re-staging

## Batch 2 summary

5/5 COMPLIANT on first attempt. **Two T1 WARN firings** (T10-r2/child1 and T5-r3/child4, both triggered by `todo` spam at count=5). Neither escalated to TERMINATE; both children course-corrected and their parent dispatches still returned COMPLIANT. This is the first batch under Arm K where T1 demonstrably engaged — consistent with B1's "adjacent-but-stochastic at this margin" signal now crossing threshold.

Mean wall per trial 206s, median 270s. No outlier T10 run this time (320s vs B1's 1311s) — consistent with warmer oMLX state across the two batches and T1 possibly shortening T10-r2's long tail via the warn injection (child1 terminated shortly after warn rather than grinding).

Combined B1+B2: 10/10 COMPLIANT, 2 T1 warn firings out of 10 trials (20%), both on tasks where the child got stuck repeating `todo`, both recovering within 1-2 turns of the warn. No TERMINATE firings yet across any Arm K trial.

## Artifacts on disk

- Runner: `/tmp/r7.8-K-B2-runner.sh`
- Results TSV: `/tmp/r7.8-K-B2-results.txt`
- Per-trial logs & stdout: `/tmp/r7.8-K-B2-logs/{T5-run2,T6-run2,T10-run2,T4-run3,T5-run3}.{log,stdout}`
- Session JSONs on VM: `/home/parallels/.hermes/sessions/session_<sid>.json` (parents + 14 total children across 5 trials)
- Analysis helpers: `/tmp/analyze_children.py`, `/tmp/find_t1_context.py`

## Hand-off to batch 3

Staging intact. Batch 3 can source `/tmp/r7.7-env.sh`, export `HERMES_LOOP_DETECTOR=1`, unset HWO/HCTR/HWBCG, and invoke `./probe-variantJ-wrapper.sh` directly against the T1+F+G+H stack currently on the VM. No re-staging needed. Runner template at `/tmp/r7.8-K-B2-runner.sh` — clone to `B3` and swap the TRIALS array + paths.
