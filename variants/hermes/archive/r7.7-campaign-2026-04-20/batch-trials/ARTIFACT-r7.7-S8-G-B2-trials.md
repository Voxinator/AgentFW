---
type: S8 Arm G batch 2 trial records
date: 2026-04-20
campaign: r7.7 Path A
arm: G (A1-only ablation)
worker: S8-G-B2
---
# Arm G batch 2 — trial records

## Staging verdict (5 variants, NOT 6)

Staged in order F -> G -> H -> J-A1. variantI skipped (no HWO overlay). variantJ-A2 skipped (no write-before-claim gate). Arm G is A1-only relative to Arm F.

- `probe-variantF-stage.sh stage` — uploaded delegate_worker_v2.py (md5 `cadb49504950dc40459f95f33b38dc9f`), patched toolsets.py (+4 refs), model_tools.py (+1 ref), run_agent.py (+2 dispatch branches); `.probe-r7.4-orig` backups in place.
- `probe-variantG-stage.sh stage` — run_agent.py turn-0 β-fuse hook (3 marker hits); `.probe-r7.5-orig` backup in place.
- `probe-variantH-stage.sh stage` — run_agent.py Change 1(a)+2 (2+2 marker hits), gemma_parser.py PIPE_PATTERN_PREFIXLESS (2 hits); both files `py_compile` OK; `.probe-r7.6-orig` backups in place.
- `probe-variantJ-A1-stage.sh stage` — local md5 matches remote (`cadb49504950dc40459f95f33b38dc9f`); idempotent no-op. A1 is env-gated (`HERMES_CHILD_TOOLSET_RESTRICT=1`) on top of the variantF-staged delegate_worker_v2.py, not a file swap. The `.probe-r7.7-orig` backup was already present from prior stage rounds, confirmed for unstage.

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
- Runner: `/tmp/r7.7-S8-G-B2-run-trial.sh` (cloned from `/tmp/r7.7-S8-prompts/run-trial-armG.sh` with LOG_DIR -> `/tmp/r7.7-S8-armG-B2-logs`)

## Trial records

| # | Task | Run | Start (UTC)          | End (UTC)            | Wall | Parent session          | Child session(s)                                                                                                | Status | Tripwire       |
|---|------|-----|----------------------|----------------------|------|-------------------------|-----------------------------------------------------------------------------------------------------------------|--------|----------------|
| 1 | T5   | 2   | 2026-04-21T02:59:00Z | 2026-04-21T03:00:10Z | 70s  | 20260420_215901_d784b1  | 20260420_215905_3e1c1e                                                                                          | PASS   | PREFLIGHT=PASS |
| 2 | T6   | 2   | 2026-04-21T03:00:13Z | 2026-04-21T03:03:24Z | 191s | 20260420_220014_5e20bb  | 20260420_220019_b78a2e, 20260420_220044_3056f0, 20260420_220202_4e8ab2, 20260420_220237_4e6b03                  | PASS   | PREFLIGHT=PASS |
| 3 | T10  | 2   | 2026-04-21T03:03:26Z | 2026-04-21T03:05:56Z | 150s | 20260420_220327_86cc78  | 20260420_220333_de8f04, 20260420_220344_fa3e25, 20260420_220511_dc21cb, 20260420_220526_8cf7ef                  | PASS   | PREFLIGHT=PASS |
| 4 | T4   | 3   | 2026-04-21T03:05:59Z | 2026-04-21T03:06:19Z | 20s  | 20260420_220600_556a28  | 20260420_220605_4eae92                                                                                          | PASS   | PREFLIGHT=PASS |
| 5 | T5   | 3   | 2026-04-21T03:06:22Z | 2026-04-21T03:07:32Z | 70s  | 20260420_220622_56cadc  | 20260420_220626_30d4e9                                                                                          | PASS   | PREFLIGHT=PASS |

Total trial wall-clock: 501s (~8.4 min). All five trials returned `RESULT=COMPLIANT` on first attempt (`attempts=1`), matching B1 pattern. Per-trial OMLX_HEALTH=CLEAN and PREFLIGHT=PASS post-each-trial.

Child-session detection notes:
- Trial 3 (T10-run2) raw child list from the mtime-window scan initially included Trial 2's parent `20260420_220014_5e20bb` as a candidate due to overlapping mtime windows; the actual T10 children are the four 22:03:33-22:05:26 sessions listed above. The entry has been removed from the table; downstream judges should cross-reference by trial start time.
- T10-run2 spawned 4 children (multi-worker dispatch), consistent with T10-run1 in B1 (also 4 children) and prior Arm F T10 trials.
- T6-run2 spawned 4 children, one more than T6-run1 (3); still within typical range for a multi-step task.

(No `a2_gate_outcome` column — Arm G has A2 disabled, so parent JSONs emit no gate records.)

## Unstage verdict

Reverse-order unstage completed cleanly:
1. `probe-variantJ-A1-stage.sh unstage` — delegate_worker_v2.py restored from `.probe-r7.7-orig`.
2. Manual `ssh ubuntu-vm 'rm -f .../delegate_worker_v2.py.probe-r7.7-orig'` — executed, no output (file removed or already absent).
3. `probe-variantH-stage.sh unstage` — run_agent.py and gemma_parser.py restored from `.probe-r7.6-orig`; verified no stray r7.6 markers.
4. `probe-variantG-stage.sh unstage` — run_agent.py restored from `.probe-r7.5-orig`; verified no stray `_resolve_tools_for_turn_r75a` references.
5. `probe-variantF-stage.sh unstage` — toolsets.py, model_tools.py, run_agent.py restored from `.probe-r7.4-orig`; tools/delegate_worker_v2.py moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`; verified no stray v2 references.

`find /home/parallels/.hermes -name "*.probe-r7.7*"` returns empty.

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

Arm G batch 2 completed cleanly: 5/5 trials returned `RESULT=COMPLIANT` (dispatch-level β-fuse compliance) with no retries required. Total trial runtime 8.4 min; end-to-end wall-clock including stage/preflight/unstage under 15 min, well inside the 75-min budget. VM canonical fully restored at exit with tripwires matching and no r7.7-specific backup artifacts remaining. Dispatch-level PASS rate matches B1 (5/5 COMPLIANT). Judge dispatch against these five parent sessions can now proceed on the MoE campaign track; downstream judge verdicts are out of scope for this artifact.
