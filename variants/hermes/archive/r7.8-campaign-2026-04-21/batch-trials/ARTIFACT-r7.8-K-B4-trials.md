---
type: r7.8 Arm K batch 4 (FINAL) trial records + full unstage
date: 2026-04-21
arm: K (vanilla + T1 loop detector)
worker: r7.8-K-B4
---
# Arm K batch 4 (FINAL) — trial records + Arm K close-out

Closing batch of Arm K (vanilla Arm A stack + T1 cross-turn loop detector via `HERMES_LOOP_DETECTOR=1`). variantF/G/H inherited-staged from B3 on top of T1-patched run_agent.py. Toolsets: `delegation,todo,clarify,file_readonly`. Model: `gemma-4-26B-A4B-it-MLX-8bit`. `TIMEOUT_PER_TURN=1500`, wall-cap=1800s/trial.

## Staging verification at start

Inherited from B3 — no re-staging needed.

- `run_agent.py` md5 = `3ceda6072461e068902bf97c3988667c` (T1-patched)
- Backup `run_agent.py.probe-r7.8-t1-orig` md5 = `94ad8712678df5e96b9f407446edf249` present
- `probe-variantJ-wrapper.sh` forwards `HERMES_LOOP_DETECTOR=1` (inherited)
- Tripwire pre-batch: HERMES.md `0780c232a6cb52e13e432261f0d68ad9` (canonical)

Preflight at start: `PREFLIGHT=PASS` (free_mem=97.8 GB, swap=3.0 GB, omlx=CLEAN, tripwire=PASS, vm_idle=PASS).

Runner: `/tmp/r7.8-K-B4-runner.sh` (cloned from `B3`; LOG_DIR→`/tmp/r7.8-K-B4-logs`, SOURCE_PREFIX→`probe-r7.8-K-B4-<task>`, TRIALS=`("T10 4" "T4 5" "T5 5" "T6 5" "T10 5")`). B3 parent-SID regex fix retained.

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children | T1 WARNs | Max consec | Status | Tripwire |
|---|------|-----|-------------|-----------|------|------------|----------|----------|------------|--------|----------|
| 1 | T10 | 4 | 07:47:12 | 07:49:02 | 110s | `20260421_024712_9b3281` | 2 | **2** | 5 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 2 | T4  | 5 | 07:49:02 | 07:50:12 | 70s  | `20260421_024903_24915e` | 1 | 0 | 2 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 3 | T5  | 5 | 07:50:13 | 07:51:33 | 80s  | `20260421_025013_00d1a1` | 1 | 0 | 4 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 4 | T6  | 5 | 07:51:33 | 07:53:33 | 120s | `20260421_025133_a8742e` | 2 | 0 | 3 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 5 | T10 | 5 | 07:53:33 | 07:57:54 | 261s | `20260421_025334_d775ed` | 2 | **2** | 5 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |

Total batch wall: 641s (~11 min). All 5 trials returned `RESULT=COMPLIANT attempts=1`.

### Child session IDs (time-adjacency + content-match)

Shared-SID assignments resolved by matching first-user content to the canonical parent task topic.

- **T10-r4** (pg-upgrade-2026 PLAN.md) → children:
  - `20260421_024721_6917a0` (msgs=33, **max_consec=5 — T1 WARN FIRED on `todo`**) — "Create directory 'migrations/pg-upgrade-2026/'…"
  - `20260421_024810_42a5ea` (msgs=31, **max_consec=5 — T1 WARN FIRED on `todo`**) — "The previous worker failed to actually create the directory…"
- **T4-r5** (auth refactor) → children:
  - `20260421_024908_7f501d` (msgs=78, max_consec=2) — "Refactor the auth module to use the new session store…"
- **T5-r5** (stale data) → children:
  - `20260421_025018_cea29c` (msgs=90, max_consec=4) — "Investigate and fix intermittent stale data…"
- **T6-r5** (export multi-phase Phase 1) → children:
  - `20260421_025138_2e5cbc` (msgs=81, max_consec=2) — "Phase 1: Discovery & Planning for the end-to-end export feature…"
  - `20260421_025253_232318` (msgs=27, max_consec=3) — retry of Phase 1
- **T10-r5** (pg-upgrade-2026 PLAN.md, second occurrence) → children:
  - `20260421_025339_39a383` (msgs=75, **max_consec=5 — T1 WARN FIRED on `todo`**) — first pg-upgrade attempt
  - `20260421_025701_075f25` (msgs=49, **max_consec=5 — T1 WARN FIRED on `search_files`**) — retry of directory creation

### T1 firing analysis

**Four T1 WARN injections in B4, zero TERMINATE.** All four WARNs fired on the pg-upgrade-2026 migration PLAN task (T10 family). Three of the four looped on `todo`, one on `search_files`. In all four cases the child course-corrected after WARN — no 6th identical call emitted, last assistant message was a natural-language summary acknowledging the loop and explaining the blocker (e.g. `"I apologize for the loop…"`, `"I am stuck in a loop of calling the `todo` tool and failing to execute the actual file system commands…"`). Parent dispatches in both T10-r4 and T10-r5 still returned `COMPLIANT attempts=1`.

Scanned wrapper logs (`grep -c "r7.8 loop detector" /tmp/r7.8-K-B4-logs/*.log`): 0 across all 5 logs (the wrapper log tracks stderr emissions from run_agent.py's detector; WARN/TERMINATE injections land in session JSON content, not stderr, so log counts of 0 are consistent with 4 in-session WARNs).

### Tripwire checks

Post each trial: `probe-preflight.sh --skip-omlx --skip-vm-idle` → PREFLIGHT=PASS. Full preflight returned OMLX_HEALTH=CLEAN each time (5/5). Batch-end:
- HERMES.md md5 = `0780c232a6cb52e13e432261f0d68ad9` (canonical, unchanged)
- All 4 canonical tripwire files intact.

No SIGTERM. No APIConnectionError. No http=000. oMLX CLEAN after every trial.

## Arm K cumulative (all 4 batches)

- **Total trials: 20 (5+5+5+5)**
- **Dispatch-compliant: 20/20** (100%, all on first attempt, `chain="A0:rc=0 | A0:COMPLIANT"`)
- **T1 WARN firings: 6** (B1=0, B2=2, B3=0, B4=4)
- **T1 TERMINATE firings: 0**
- **Wall-clock total: 1863 + 1030 + 732 + 641 = 4266 s ≈ 71 min** (across 20 trials, spread over 4 sessions)

The T1 WARN incidence escalates sharply in B4 relative to B1-B3: 4/5 T1 firings concentrated in the two T10 trials, both tied to the pg-upgrade-2026 migration PLAN task where the child gets stuck in a `todo`-spam loop after failing to execute file-system writes. In every WARN case the injection caused the child to course-correct (no 6th identical call, natural-language summary instead), and in no case did the failure mode bubble up to break dispatch. Combined B1-B4: **20/20 COMPLIANT on first attempt, 6/20 (30%) of trials triggered T1 WARN at some point in their child tree, 0% reached TERMINATE.** T1's behavioral footprint is now clearly non-trivial on the T10 pg-upgrade family and minimal elsewhere — matches the "adjacent-but-stochastic at this margin with a known failure-mode cluster" framing from B2.

## Unstage verdict

- **run_agent.py md5 restored to baseline: YES** — `94ad8712678df5e96b9f407446edf249` (matches canonical)
- **Wrapper reverted: YES** — `HERMES_LOOP_DETECTOR` forwarding block removed from `probe-variantJ-wrapper.sh` (lines 65-67 deleted; A1/A2 forwarders preserved)
- **variantH unstaged: YES** (`UNSTAGE COMPLETE`, no stray r7.6 markers)
- **variantG unstaged: YES** (`UNSTAGE COMPLETE`, no stray `_resolve_tools_for_turn_r75a`)
- **variantF unstaged: YES** (`UNSTAGE COMPLETE`, delegate_worker_v2.py moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`)
- **r7.7 cosmetic residue cleaned: YES** (`tools/delegate_worker_v2.py.probe-r7.7-orig` removed)
- **Final preflight: PASS** (free_mem=55.2 GB, swap=3.0 GB, omlx=CLEAN, tripwire=PASS, vm_idle=PASS)
- **Final HERMES.md md5: `0780c232a6cb52e13e432261f0d68ad9`** (matches canonical)
- **.probe-r7.8*orig residue on VM: empty** (0 files across hermes-agent/, tools/, environments/tool_call_parsers/)

VM canonical baseline restored. Arm K' (ablation) can stage on top of current state without prior r7.8 interference.

## Artifacts on disk

- Runner: `/tmp/r7.8-K-B4-runner.sh`
- Results TSV: `/tmp/r7.8-K-B4-results.txt` (copy of summary)
- Per-trial logs & stdout: `/tmp/r7.8-K-B4-logs/{T10-run4,T4-run5,T5-run5,T6-run5,T10-run5}.{log,stdout}`
- Session JSONs on VM: `/home/parallels/.hermes/sessions/session_<sid>.json` (5 parents + 8 total children across 5 trials, of which 4 children fired T1 WARN)
- Analysis helper: `/tmp/analyze_children_b4.py` (adapted from B3; ssh-driven since session JSONs live on VM)

## Hand-off to Arm K' (ablation)

VM canonical. No staging present. Wrapper canonical (forwards HWO + A1 + A2 only; no LOOP_DETECTOR). Ablation can:
1. Re-apply the r7.8 T1 patch (with its `.probe-r7.8-t1-orig` backup) selectively, or
2. Apply a variant T1 design on top of current baseline,
and probe vs. Arm K's 20-trial / 6-WARN / 0-TERMINATE baseline. The clearest ablation target is the T10 pg-upgrade task family where T1 demonstrably engaged (4/6 WARNs in Arm K total) — an ablation run of 5x T10-only trials with and without the detector would yield the tightest signal.
