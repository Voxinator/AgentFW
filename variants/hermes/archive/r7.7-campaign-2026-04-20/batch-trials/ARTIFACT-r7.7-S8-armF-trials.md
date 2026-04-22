---
type: S8 Arm F probe trial records
date: 2026-04-20
campaign: r7.7 Path A
worker: S8-armF
---
# S8 Arm F probe — trial records

## Staging verdict

All 6 variants staged successfully (verified 2026-04-20 prior to trial-1):

| Variant | Post-stage state | Notes |
|---------|------------------|-------|
| variantF (r7.4 β-fuse delegate_worker_v2) | STAGED (heuristic flags "PARTIAL" because run_agent.py accumulates delegate_worker_v2 refs from layered variantG+H+J-A1 on top — expected when full stack is staged; actual patch count matches expected per-layer totals, backups in place) | toolsets=4 model_tools=1 run_agent=12 (v2-ref count) |
| variantG (r7.5 turn-0 toolset restriction) | STAGED (r7.5 Variant G on top of r7.4 Variant F) | 3 _resolve_tools_for_turn_r75a hook hits |
| variantH (r7.6 Gemma-MoE channel fixes) | STAGED (r7.6-P1A Variant H) | 2 channel_marker + 2 empty_synthesis_trailer + 2 PIPE_PATTERN_PREFIXLESS hits |
| variantI (r7.6 HERMES-WORKER.md overlay) | STAGED (r7.6-P1C Variant I) | delegate_tool.py overlay hook in place; HERMES-WORKER.md uploaded |
| variantJ-A1 (child toolset restriction) | STAGED (r7.7 J-A1 active; idempotent no-op at file level — delegate_worker_v2.py md5 match) | |
| variantJ-A2 (write-before-claim gate, detect-only) | STAGED | patch (a)+patch (b) applied; gate gated by HERMES_WRITE_BEFORE_CLAIM_GATE=1 |

Preflight re-run after staging: `PREFLIGHT=PASS` (agent_dispatch, oMLX CLEAN, tripwires all 4 canonical, vm_idle).

Runtime env per trial (via wrapper):
`HERMES_WORKER_OVERLAY=1 HERMES_CHILD_TOOLSET_RESTRICT=1 HERMES_WRITE_BEFORE_CLAIM_GATE=1 AGENT_DISPATCH_AVAILABLE=1 OMLX_SWAP_MAX_GB=5.5 TIMEOUT_PER_TURN=1500`  arm=B (overlay active); model=`gemma-4-26B-A4B-it-MLX-8bit`; toolsets=`delegation,todo,clarify,file_readonly`.

Canonical task prompts: extracted verbatim from `ARTIFACT-r7.6-judge-brief-REJ-A-{T4,T5,T6,T10}-run1.md` PARENT_GOAL fields. Saved locally on Mac at `/tmp/r7.7-S8-prompts/T{4,5,6,10}.txt`. GOAL_PATHS:
- T4: src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts (structured, scaffold-known-good concrete-blocked — repo has no such files)
- T5: [] — hunt inside /media/psf/Projects/chief-of-staff-dashboard (structured, thrash-prone; useDashboard.ts tripwire in scope)
- T6: features/export-feature/PLAN.md (long-horizon, no real project files)
- T10: migrations/pg-upgrade-2026/PLAN.md (long-horizon, fabrication attractor)

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent session | Child session(s) | a2_gate_outcome | Status |
|---|------|-----|-------------|-----------|------|----------------|------------------|-----------------|--------|
| 1 | T4 | 1 | 2026-04-20T22:03:10Z | 2026-04-20T22:17:37Z | 867s | 20260420_170311_e637a5 | 20260420_170321_07f156 | CLEAN | PASS |
| 2 | T5 | 1 | 2026-04-20T22:19:57Z | 2026-04-20T22:29:38Z | 581s | 20260420_171957_1d5146 | 20260420_172002_fc5d66 | CLEAN | PASS |
| 3..20 | see below | | | | | | | | *IN PROGRESS (see worker-handoff)* |

## Worker-handoff notice (interim status, 2026-04-20T22:34Z)

The S8 Arm F campaign was dispatched as a single Claude worker with a budget of 4-5h wall-clock.
Actual per-trial wall-clock observed: trial 1 = 867s (14.5 min), trial 2 = 581s (9.7 min). At this
rate, 20 trials × ~12 min avg = ~4h runtime, within budget — BUT a single Claude session cannot
monitor a 4h campaign end-to-end given context constraints.

**Accordingly, the worker has fully detached the trial runner from the Claude session, and fully
detached an unstage watcher that will execute the end-of-campaign cleanup automatically.**

### Still-running processes (survive Claude session exit — PPID=1, fully detached)

- **`run-all.sh`** (pid 77197): serial trial runner. Driving trials 3–20 in the order
  `T6-r1, T10-r1, T4-r2, T5-r2, T6-r2, T10-r2, T4-r3, T5-r3, T6-r3, T10-r3, T4-r4, T5-r4, T6-r4, T10-r4, T4-r5, T5-r5, T6-r5, T10-r5`.
  For each trial: preflight → wrapper invocation → oMLX health check → append record to artifact.
  On `OMLX_HEALTH=DEGRADED` or preflight FAIL, writes a halt marker (`/tmp/r7.7-S8-halt-marker`) and exits.
- **`unstage-watcher.sh`** (pid 79070): waits for run-all completion (via pid-exit OR halt-marker OR
  ≥19 records), then runs `unstage-all.sh` (J-A2 → J-A1 → I → H → G → F), runs a final preflight +
  oMLX health check + residue scan, and appends an `## End-of-run` block to THIS artifact.

### How to monitor

```bash
tail -f /tmp/r7.7-S8-armF-logs/run-all.out      # live per-trial progress
tail -f /tmp/r7.7-S8-armF-logs/records.tsv      # machine-parseable per-trial records
cat    /tmp/r7.7-S8-armF-logs/unstage-watcher.out  # watcher heartbeat
cat    /Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-S8-armF-trials.md  # artifact table (row 31+ appended as trials complete)
ps -p 77197,79070                                # confirm processes alive
```

### If you want to halt early

```bash
touch /tmp/r7.7-S8-halt-marker                   # signals watcher to unstage now; does NOT kill in-flight trial
kill 77197                                        # hard-kills run-all (watcher will still unstage)
```

### Known gap (worker notes, not a blocker)

- `run-all.sh` as invoked at 22:19Z did NOT include the end-of-run unstage logic; the worker added
  it in a later edit to the same file, but bash does not re-read scripts mid-execution, so the
  in-memory copy inside pid 77197 still lacks it. This is why `unstage-watcher.sh` was spun up
  as a separate sidecar to guarantee unstaging regardless. The artifact ordering (end-of-run
  block appended by watcher) is therefore correct even if the in-memory run-all version is stale.
- Early trial records appended by `run-all.sh` itself insert below the header via a Python
  heuristic. If row ordering looks off after full completion, sort by trial index (#) column.


## End-of-run

- Trials completed (record count):        1/19 (trial 1 was appended separately; total 1 +        1)
- Variants unstaged (count matching UNSTAGED/canonical heuristic): 5/6
- Final preflight: PREFLIGHT=FAIL detail=agent_dispatch
PREFLIGHT=UNKNOWN
- Tripwire gate: UNKNOWN
- Final oMLX status: OMLX_HEALTH=DEGRADED detail=mem_low,swap_high
OMLX_HEALTH=UNKNOWN
- Residue (.probe-*-orig files remaining on VM, from unstage-all scan): 23 (0 desired)

### Run log pointers
- run-all log: /tmp/r7.7-S8-armF-logs/run-all.out
- records TSV: /tmp/r7.7-S8-armF-logs/records.tsv
- unstage log: /tmp/r7.7-S8-armF-logs/unstage.out
- per-trial wrapper logs: /tmp/probe-r7.7-S8-armF-*-run*-wrapper.log, /tmp/probe-r7.7-S8-armF-*-run*-stdout.txt

### Judge dispatch pointers
- All parent/child session JSONs live on VM at /home/parallels/.hermes/sessions/session_<id>.json
- Trial records table above provides parent + child session IDs per trial
- Canonical goal prompts: /tmp/r7.7-S8-prompts/T{4,5,6,10}.txt (local Mac) or regenerated from trial record Wall column
