---
type: S8 Arm G batch 4 trial records (final)
date: 2026-04-20
campaign: r7.7 Path A
arm: G (A1-only ablation)
worker: S8-G-B4
---
# Arm G batch 4 — trial records (final batch)

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
- Runner: `/tmp/r7.7-S8-G-B4-run-trial.sh` (cloned from `/tmp/r7.7-S8-G-B3-run-trial.sh` with LOG_DIR -> `/tmp/r7.7-S8-armG-B4-logs`)

## Trial records

| # | Task | Run | Start (UTC)          | End (UTC)            | Wall | Parent session          | Child session(s)                                                                                                                                      | Status | Tripwire       |
|---|------|-----|----------------------|----------------------|------|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|--------|----------------|
| 1 | T10  | 4   | 2026-04-21T03:36:28Z | 2026-04-21T03:46:19Z | 591s | 20260420_223628_ce75a1  | 20260420_223633_68af0c, 20260420_223643_fd047b                                                                                                        | PASS   | PREFLIGHT=PASS |
| 2 | T4   | 5   | 2026-04-21T03:46:22Z | 2026-04-21T03:46:47Z | 25s  | 20260420_224622_30d9e5  | 20260420_224627_47a867                                                                                                                                | PASS   | PREFLIGHT=PASS |
| 3 | T5   | 5   | 2026-04-21T03:46:51Z | 2026-04-21T03:48:36Z | 105s | 20260420_224652_18420f  | 20260420_224656_c336c7, 20260420_224733_2eb9ed                                                                                                        | PASS   | PREFLIGHT=PASS |
| 4 | T6   | 5   | 2026-04-21T03:48:39Z | 2026-04-21T03:54:20Z | 341s | 20260420_224840_ee8c4f  | 20260420_224844_f1dd2e, 20260420_224915_4b247e, 20260420_225020_5aae1d, 20260420_225049_bb192d, 20260420_225131_5da49a, 20260420_225238_45cf58, 20260420_225332_32d246 | PASS   | PREFLIGHT=PASS |
| 5 | T10  | 5   | 2026-04-21T03:54:24Z | 2026-04-21T04:10:45Z | 981s | 20260420_225424_bac87a  | 20260420_225429_27586a, 20260420_230928_882cf4, 20260420_230943_6c5631, 20260420_231003_c3f889                                                        | PASS   | PREFLIGHT=PASS |

Total trial wall-clock: 2043s (~34.1 min). All five trials returned `RESULT=COMPLIANT` on first attempt (`attempts=1`), matching B1/B2/B3 pattern. Per-trial OMLX_HEALTH=CLEAN and PREFLIGHT=PASS post-each-trial.

Child-session detection notes:
- Trial 1 (T10-run4) spawned 2 children — within typical range, but narrower than prior T10 runs (B1 run1 = 4, B2 run2 = 4, B3 run3 = 3, B4 run4 = 2). Dispatch still COMPLIANT on first attempt.
- Trial 5 (T10-run5) ran 981s (~16.4 min) with 4 children; second-longest T10 in Arm G to date. Dispatch COMPLIANT on first attempt; latency is content-dependent and does not affect dispatch-level verdict.
- Trial 4 (T6-run5) spawned 7 children — highest T6 child count in Arm G (prior: B2 run2 = 4, B3 run3 = 3, B3 run4 = 5). Multi-worker dispatch pattern consistent with T6 complexity; all dispatches COMPLIANT.
- Trial 2 (T4-run5) returned in 25s, comparable to B2 T4-run3 (20s), faster than B3 T4-run4 (521s). Content-dependent latency, dispatch-level PASS.
- No mtime-window false positives observed this batch; child scan cleanly isolated each trial's children by the 5s pre-start window filter applied in the B3 runner clone.

(No `a2_gate_outcome` column — Arm G has A2 disabled, so parent JSONs emit no gate records.)

## Unstage verdict

Reverse-order unstage completed cleanly:
1. `probe-variantJ-A1-stage.sh unstage` — delegate_worker_v2.py restored from `.probe-r7.7-orig`.
2. Manual `ssh ubuntu-vm 'rm -f .../delegate_worker_v2.py.probe-r7.7-orig'` — executed; post-rm find returned empty.
3. `probe-variantH-stage.sh unstage` — run_agent.py and gemma_parser.py restored from `.probe-r7.6-orig`; verified no stray r7.6 markers.
4. `probe-variantG-stage.sh unstage` — run_agent.py restored from `.probe-r7.5-orig`; verified no stray `_resolve_tools_for_turn_r75a` references.
5. `probe-variantF-stage.sh unstage` — toolsets.py, model_tools.py, run_agent.py restored from `.probe-r7.4-orig`; tools/delegate_worker_v2.py moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`; verified no stray v2 references.

`ssh ubuntu-vm 'find /home/parallels/.hermes -name "*.probe-r7.7*"'` returns empty. (Older `.probe-r7.4-orig`/`.probe-r7.5-orig`/`.probe-r7.6-orig` leftover backup files from prior stage cycles remain; these stale backups are left in place by the unstage scripts by design.)

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

Arm G batch 4 (final) completed cleanly: 5/5 trials returned `RESULT=COMPLIANT` (dispatch-level β-fuse compliance) with no retries required. Total trial runtime 34.1 min; end-to-end wall-clock including stage/preflight/unstage inside the 75-min budget. VM canonical fully restored at exit with tripwires matching and no r7.7-specific backup artifacts remaining. Dispatch-level PASS rate matches B1, B2, and B3 (5/5 COMPLIANT each). **Cumulative Arm G across B1+B2+B3+B4 = 20/20 dispatch-compliant.** Arm G (A1-only) data collection complete. Judge dispatch against these five parent sessions can now proceed on the MoE campaign track; downstream judge verdicts are out of scope for this artifact.
