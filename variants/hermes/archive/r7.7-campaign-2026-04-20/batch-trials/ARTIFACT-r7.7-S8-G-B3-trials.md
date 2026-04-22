---
type: S8 Arm G batch 3 trial records
date: 2026-04-20
campaign: r7.7 Path A
arm: G (A1-only ablation)
worker: S8-G-B3
---
# Arm G batch 3 — trial records

## Staging verdict (5 variants, NOT 6)

Staged in order F -> G -> H -> J-A1. variantI skipped (no HWO overlay). variantJ-A2 skipped (no write-before-claim gate). Arm G is A1-only relative to Arm F.

- `probe-variantF-stage.sh stage` — uploaded delegate_worker_v2.py (md5 `cadb49504950dc40459f95f33b38dc9f`), patched toolsets.py (+4 refs), model_tools.py (+1 ref), run_agent.py (+2 dispatch branches); `.probe-r7.4-orig` backups in place.
- `probe-variantG-stage.sh stage` — run_agent.py turn-0 β-fuse hook (3 marker hits); `.probe-r7.5-orig` backup in place.
- `probe-variantH-stage.sh stage` — run_agent.py Change 1(a)+2 and gemma_parser.py PIPE_PATTERN_PREFIXLESS; both files `py_compile` OK; `.probe-r7.6-orig` backups in place.
- `probe-variantJ-A1-stage.sh stage` — local md5 matches remote (`cadb49504950dc40459f95f33b38dc9f`); idempotent no-op. A1 is env-gated (`HERMES_CHILD_TOOLSET_RESTRICT=1`) on top of the variantF-staged delegate_worker_v2.py, not a file swap.

All four stage commands reported STAGE COMPLETE.

## Preflight at start

Pre-stage preflight (env sourced):
```
[GATE: agent_dispatch] PASS    [GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire]       PASS    [GATE: vm_idle] PASS
PREFLIGHT=PASS
```

Post-stage re-check confirmed tripwires still canonical:
- HERMES.md md5 = `0780c232a6cb52e13e432261f0d68ad9` MATCH
- SKILL.md (jira-daily-briefing) md5 = `fb1a5a5208a6cf2fcb8252aac10397eb` MATCH

## Runtime env per trial (Arm G)

- `HERMES_CHILD_TOOLSET_RESTRICT=1` (A1 ON)
- `HERMES_WORKER_OVERLAY` unset (HWO OFF)
- `HERMES_WRITE_BEFORE_CLAIM_GATE` unset (A2 OFF)
- `ARM=A` (wrapper prefix omits HWO env)
- Model: `gemma-4-26B-A4B-it-MLX-8bit`
- Toolsets: `delegation,todo,clarify,file_readonly`
- Per-turn timeout: 1500s; per-trial wall cap: 1800s (30 min)
- Wrapper: `probe-variantJ-wrapper.sh`
- Runner: `/tmp/r7.7-S8-G-B3-run-trial.sh` (cloned from `/tmp/r7.7-S8-G-B2-run-trial.sh` with LOG_DIR -> `/tmp/r7.7-S8-armG-B3-logs`)

## Trial records

| # | Task | Run | Start (UTC)          | End (UTC)            | Wall | Parent session          | Child session(s)                                                                                                                    | Status | Tripwire       |
|---|------|-----|----------------------|----------------------|------|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------|--------|----------------|
| 1 | T6   | 3   | 2026-04-21T03:10:00Z | 2026-04-21T03:12:40Z | 160s | 20260420_221000_e3a26d  | 20260420_221005_8a66dd, 20260420_221129_853b7e, 20260420_221201_42bc63                                                              | PASS   | PREFLIGHT=PASS |
| 2 | T10  | 3   | 2026-04-21T03:12:43Z | 2026-04-21T03:19:59Z | 436s | 20260420_221243_0cba13  | 20260420_221248_cdc104, 20260420_221356_1e9024, 20260420_221927_c7848c                                                              | PASS   | PREFLIGHT=PASS |
| 3 | T4   | 4   | 2026-04-21T03:20:03Z | 2026-04-21T03:28:44Z | 521s | 20260420_222004_fca01e  | 20260420_222009_c0bf68                                                                                                              | PASS   | PREFLIGHT=PASS |
| 4 | T5   | 4   | 2026-04-21T03:28:47Z | 2026-04-21T03:29:53Z | 66s  | 20260420_222848_226a88  | 20260420_222852_612e1e                                                                                                              | PASS   | PREFLIGHT=PASS |
| 5 | T6   | 4   | 2026-04-21T03:29:56Z | 2026-04-21T03:33:36Z | 220s | 20260420_222956_7b2ec7  | 20260420_223000_9c5dec, 20260420_223032_658cd1, 20260420_223221_2b28fb, 20260420_223302_7c5369, 20260420_223314_7aadc2              | PASS   | PREFLIGHT=PASS |

Total trial wall-clock: 1403s (~23.4 min). All five trials returned `RESULT=COMPLIANT` on first attempt (`attempts=1`), matching B1/B2 pattern. Per-trial OMLX_HEALTH=CLEAN and PREFLIGHT=PASS post-each-trial.

Child-session detection notes:
- Trial 2 (T10-run3) raw child list from the mtime-window scan initially included Trial 1's parent `20260420_221000_e3a26d` as a candidate due to overlapping mtime windows (the T6-run3 parent session JSON was touched after Trial 1 completed but within Trial 2's start-5s window). The actual T10-run3 children are the three 22:12:48-22:19:27 sessions listed above. Entry removed from the table; downstream judges should cross-reference by trial start time. Same pattern observed in B2 trial 3.
- T10-run3 spawned 3 children (multi-worker dispatch), within the typical range. Prior T10 trials: B1 run1 = 4, B2 run2 = 4, B3 run3 = 3.
- T6-run4 spawned 5 children (more than T6-run2=4 and T6-run3=3), still a reasonable count for a multi-step task.
- T4-run4 took notably longer than prior T4 trials (B2 T4-run3 was 20s; this run was 521s). Dispatch still COMPLIANT on first attempt; the latency is content-dependent and does not affect the dispatch-level verdict.

(No `a2_gate_outcome` column — Arm G has A2 disabled, so parent JSONs emit no gate records.)

## Unstage verdict

Reverse-order unstage completed cleanly:
1. `probe-variantJ-A1-stage.sh unstage` — delegate_worker_v2.py restored from `.probe-r7.7-orig`.
2. Manual `ssh ubuntu-vm 'rm -f .../delegate_worker_v2.py.probe-r7.7-orig'` — executed, confirmed "no r7.7 backups" by post-rm listing.
3. `probe-variantH-stage.sh unstage` — run_agent.py and gemma_parser.py restored from `.probe-r7.6-orig`; verified no stray r7.6 markers.
4. `probe-variantG-stage.sh unstage` — run_agent.py restored from `.probe-r7.5-orig`; verified no stray `_resolve_tools_for_turn_r75a` references.
5. `probe-variantF-stage.sh unstage` — toolsets.py, model_tools.py, run_agent.py restored from `.probe-r7.4-orig`; tools/delegate_worker_v2.py moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`; verified no stray v2 references.

`ssh ubuntu-vm 'find /home/parallels/.hermes -name "*.probe-r7.7*"'` returns empty. (Older `.probe-r7.4-orig`/`.probe-r7.5-orig`/`.probe-r7.6-orig` leftover backup files from prior stage cycles remain; spot-check `diff run_agent.py run_agent.py.probe-r7.4-orig` returns "identical", confirming canonical restoration. These stale backups are left in place by the unstage scripts by design.)

## Final VM canonical

```
0780c232a6cb52e13e432261f0d68ad9  /home/parallels/.hermes/hermes-agent/HERMES.md
fb1a5a5208a6cf2fcb8252aac10397eb  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md
```

Both tripwires match canonical.

Final preflight at exit:
```
[GATE: agent_dispatch] PASS    [GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire]       PASS    [GATE: vm_idle] PASS
PREFLIGHT=PASS
```

## If HALTED early

Not applicable. No halt conditions triggered. No preflight FAIL, no http=000, no APIConnectionError, no tripwire drift. All five trials executed in sequence without interruption.

## Summary

Arm G batch 3 completed cleanly: 5/5 trials returned `RESULT=COMPLIANT` (dispatch-level β-fuse compliance) with no retries required. Total trial runtime 23.4 min; end-to-end wall-clock including stage/preflight/unstage inside the 75-min budget. VM canonical fully restored at exit with tripwires matching and no r7.7-specific backup artifacts remaining. Dispatch-level PASS rate matches B1 and B2 (5/5 COMPLIANT each). Cumulative Arm G across B1+B2+B3 = 15/15 dispatch-compliant. Judge dispatch against these five parent sessions can now proceed on the MoE campaign track; downstream judge verdicts are out of scope for this artifact.
