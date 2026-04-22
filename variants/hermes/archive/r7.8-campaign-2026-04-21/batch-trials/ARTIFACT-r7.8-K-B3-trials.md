---
type: r7.8 Arm K batch 3 trial records
date: 2026-04-21
arm: K (vanilla + T1 loop detector)
worker: r7.8-K-B3
---
# Arm K batch 3 — trial records

Continuation of Arm K (vanilla Arm A stack + T1 cross-turn loop detector via `HERMES_LOOP_DETECTOR=1`). Variants F+G+H inherited-staged from B1/B2 on top of T1-patched baseline. Toolsets: `delegation,todo,clarify,file_readonly`. Model: `gemma-4-26B-A4B-it-MLX-8bit`. `TIMEOUT_PER_TURN=1500`, wall-cap=1800s/trial.

## Staging verification at start

Inherited from B2 — no re-staging needed.

- `run_agent.py` md5 = `3ceda6072461e068902bf97c3988667c` (matches B2 exit md5, matches P3c vet)
- Backup `run_agent.py.probe-r7.8-t1-orig` md5 = `94ad8712678df5e96b9f407446edf249` present on VM
- `probe-variantJ-wrapper.sh` `HERMES_LOOP_DETECTOR=1` forwarder present (inherited)
- Tripwire pre-batch: HERMES.md `0780c232a6cb52e13e432261f0d68ad9`, jira-daily-briefing SKILL.md `fb1a5a5208a6cf2fcb8252aac10397eb` (canonical)

Preflight at start:
```
PREFLIGHT=PASS
  agent_dispatch=PASS (AGENT_DISPATCH_AVAILABLE=1)
  omlx=CLEAN (0 active sessions, 0 loaded)
  tripwire=PASS (all 4 canonical)
  vm_idle=PASS
  free_mem_gb=97.0  swap_used_gb=3.0
```

Runner: `/tmp/r7.8-K-B3-runner.sh` (cloned from B2, updated LOG_DIR → `/tmp/r7.8-K-B3-logs`, SOURCE_PREFIX → `probe-r7.8-K-B3-<task>`, TRIALS → T6-r3, T10-r3, T4-r4, T5-r4, T6-r4).

**Parent-SID regex fix applied** (per B2 hand-off note): SID now extracted from the `final_session=<sid>` field in the OUTCOME line on stdout, rather than `session_id: <sid>` from stderr. All 5 B3 parent SIDs captured cleanly (none reported as `unknown`), confirming the fix.

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children | T1 fired? | Max consec | Status | Tripwire |
|---|------|-----|-------------|-----------|------|------------|----------|-----------|------------|--------|----------|
| 1 | T6   | 3   | 07:23:03    | 07:23:43  | 40s   | `20260421_022303_2b8250` | 1 | no | 3 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 2 | T10  | 3   | 07:23:43    | 07:30:44  | 421s  | `20260421_022344_dd5257` | 3 | no | 2 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 3 | T4   | 4   | 07:30:44    | 07:31:44  | 60s   | `20260421_023044_ce0b6c` | 1 | no | 3 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 4 | T5   | 4   | 07:31:45    | 07:33:45  | 121s  | `20260421_023145_ec4ab2` | 2 | no | 2 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 5 | T6   | 4   | 07:33:45    | 07:35:15  | 90s   | `20260421_023345_b9d0e5` | 2 | no | 3 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |

Total batch wall: 732s (~12 min). All trials returned `RESULT=COMPLIANT attempts=1`.

### Child session IDs (time-clamped + content-matched)

Children matched to each parent by time-adjacency (within parent wall window) + first-user-content task match. Shared-SID children (children whose time-window overlaps two parent windows) assigned to the parent whose task topic matches the child's delegation prompt.

- **T6-r3** (export multi-phase) → children:
  - `20260421_022312_a6f642` (msgs=37, max_consec=3) — "Implement an end-to-end export feature (CSV, JSON, PDF)… 5 phases"
- **T10-r3** (pg-upgrade PLAN.md) → children:
  - `20260421_022348_5529be` (msgs=53, max_consec=1) — "Create the directory `migrations/pg-upgrade-2026/`… PLAN.md detailing a zero-downtime migration"
  - `20260421_022541_04b156` (msgs=31, max_consec=1) — retry of same migration PLAN
  - `20260421_022617_fc32be` (msgs=8, max_consec=2) — retry of same migration PLAN
- **T4-r4** (auth refactor) → children:
  - `20260421_023049_fd623f` (msgs=55, max_consec=3) — "Refactor the auth module to use the new session store"
- **T5-r4** (stale data) → children:
  - `20260421_023149_f04fbe` (msgs=23, max_consec=1) — "Investigate and fix intermittent stale data issue in the Chief of Staff Dashboard"
  - `20260421_023224_172fb1` (msgs=40, max_consec=2) — same task with explicit project root context
- **T6-r4** (export multi-phase) → children:
  - `20260421_023350_b33730` (msgs=35, max_consec=1) — "Phase 1: Discovery & Planning" for export feature
  - `20260421_023444_71cfa7` (msgs=29, max_consec=3) — "Previous attempt to create PLAN.md… failed… re-run Phase 1"

### T1 firing check

Scanned all 9 child session JSONs for "r7.8 loop", "consecutive identical tool calls", "loop_detected", and "stop calling tools" markers. Also scanned wrapper logs `/tmp/r7.8-K-B3-logs/*.log`.

**Zero T1 firings observed in B3.** No child reached 5 consecutive identical tool calls (max observed = 3, in three separate children). No WARN injection, no TERMINATE, no loop-detector stderr emission. Wrapper-log count for "r7.8 loop detector": 0 across all 5 logs.

Compared to B2's 2/5 trials with T1 WARN firings (both on `todo`-spam at count=5), B3 has 0/5. The B3 trial mix (T6 x2, T10, T4, T5) included topology variants that had previously fired (T10-r2 and T5-r3 both fired in B2) but in B3 the equivalents (T10-r3, T5-r4) produced shorter, cleaner child runs (T10-r3 child1 mc=1 with 53 msgs; T5-r4 child2 mc=2 with 40 msgs). Consistent with the "adjacent-but-stochastic at this margin" framing — the stuck-on-`todo` failure mode is real but rare.

### Tripwire checks

Post each trial: `probe-preflight.sh --skip-omlx --skip-vm-idle` returned PREFLIGHT=PASS. Full preflight post-trial returned OMLX_HEALTH=CLEAN each time (5/5). At batch end:
- HERMES.md md5 = `0780c232a6cb52e13e432261f0d68ad9` (canonical, unchanged)
- jira-daily-briefing SKILL.md md5 = `fb1a5a5208a6cf2fcb8252aac10397eb` (canonical, unchanged)
- All 4 canonical tripwire files intact

No SIGTERM observed in any hermes-chat process. No APIConnectionError. No http=000. oMLX CLEAN after every trial.

## Exit state

- **T1 still staged:** YES (run_agent.py md5 = `3ceda6072461e068902bf97c3988667c`, backup intact at `run_agent.py.probe-r7.8-t1-orig` md5 = `94ad8712678df5e96b9f407446edf249`)
- **variantF/G/H still staged:** YES (inherited from B2, no modifications during B3)
- **Wrapper mod (HERMES_LOOP_DETECTOR forwarding):** still present
- **Final preflight:** PREFLIGHT=PASS (free_mem_gb=97.9, swap_used_gb=3.0, omlx_active=0, omlx_loaded=0, tripwire=PASS, vm_idle=PASS)
- **Final tripwire:** MATCH
- **VM canonical for a K-arm continuation:** YES — batch 4 can run against current state without re-staging

## Batch 3 summary

5/5 COMPLIANT on first attempt. Zero T1 WARN firings, zero TERMINATEs. Max consecutive-identical-tool-call count across all 9 B3 children = 3 (below the warn threshold of 5). Mean wall per trial 146s, median 90s. T10-r3 at 421s was the longest (3 children, sequential retries of same migration PLAN) but still well inside the 1800s wall cap.

**Combined B1+B2+B3: 15/15 COMPLIANT, 2 T1 WARN firings out of 15 trials (13%), both in B2, zero TERMINATE firings across any Arm K trial.** No regressions from vanilla Arm A. T1's behavioral footprint remains small and stochastic at this margin — consistent with the pre-batch expectation.

The parent-SID regex fix (OUTCOME `final_session=` instead of stderr `session_id:`) worked cleanly: all 5 parent SIDs captured correctly, cross-referenced against session file listings on the VM, confirmed matched.

## Artifacts on disk

- Runner: `/tmp/r7.8-K-B3-runner.sh`
- Results TSV: `/tmp/r7.8-K-B3-results.txt`
- Per-trial logs & stdout: `/tmp/r7.8-K-B3-logs/{T6-run3,T10-run3,T4-run4,T5-run4,T6-run4}.{log,stdout}`
- Session JSONs on VM: `/home/parallels/.hermes/sessions/session_<sid>.json` (5 parents + 9 total children across 5 trials)
- Analysis helper (B3 variant): `/tmp/analyze_children_b3.py` (local and on VM at same path)

## Hand-off to batch 4

Staging intact. Batch 4 can source `/tmp/r7.7-env.sh`, export `HERMES_LOOP_DETECTOR=1`, unset HWO/HCTR/HWBCG, and invoke `./probe-variantJ-wrapper.sh` directly against the T1+F+G+H stack currently on the VM. No re-staging needed. Runner template at `/tmp/r7.8-K-B3-runner.sh` — clone to `B4` and swap the TRIALS array + paths. Parent-SID regex fix in B3 runner (line extracting `final_session=…` from OUTCOME) should be retained.
