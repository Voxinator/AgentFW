---
type: S8 Arm G batch 1 trial records
date: 2026-04-20
campaign: r7.7 Path A
arm: G (A1-only ablation)
worker: S8-G-B1
---
# Arm G batch 1 — trial records

## Staging verdict (5 variants, NOT 6)

All four stage commands reported STAGE COMPLETE. variantI NOT staged (no HWO overlay). variantJ-A2 NOT staged (no write-before-claim gate). Arm G is therefore the A1-only ablation relative to Arm F.

- `probe-variantF-stage.sh stage` — patches delegate_worker_v2.py, toolsets.py (+4 refs), model_tools.py (+1 ref), run_agent.py (+2 dispatch branches); backup `.probe-r7.4-orig`.
- `probe-variantG-stage.sh stage` — run_agent.py turn-0 β-fuse hook (3 marker hits); backup `.probe-r7.5-orig`.
- `probe-variantH-stage.sh stage` — run_agent.py Change 1(a) + Change 2 (2+2 hits), gemma_parser.py PIPE_PATTERN_PREFIXLESS (2 hits); backups `.probe-r7.6-orig`.
- `probe-variantJ-A1-stage.sh stage` — delegate_worker_v2.py already matched local md5 `cadb49504950dc40459f95f33b38dc9f` (A1 logic is env-gated within the same file variantF uploads); idempotent no-op, `.probe-r7.7-orig` backup confirmed present.

Note on variantJ-A1 overlay: the local `variants/hermes/delegate_worker_v2.py` is the same file variantF stages, because A1's runtime behavior is gated by `HERMES_CHILD_TOOLSET_RESTRICT=1`. A1 activation is an env flag on the wrapper, not a file swap on top of variantF. Backup was still created/present so unstage could remove the r7.7 marker.

## Preflight at start

```
[GATE: agent_dispatch] PASS (AGENT_DISPATCH_AVAILABLE=1)
  free_mem_gb=101.1, swap_used_gb=3.7, omlx_active_sessions=0, omlx_loaded_count=0
[GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire] PASS (all 4 canonical)
[GATE: vm_idle] PASS (no hermes chat)
PREFLIGHT=PASS
```

Tripwire canonical md5s at start (post-stage):
- HERMES.md = `0780c232a6cb52e13e432261f0d68ad9` MATCH
- SKILL.md (jira-daily-briefing) = `fb1a5a5208a6cf2fcb8252aac10397eb` MATCH

## Runtime env per trial (Arm G)

- `HERMES_CHILD_TOOLSET_RESTRICT=1`   (A1 ON)
- `HERMES_WORKER_OVERLAY` unset        (HWO OFF)
- `HERMES_WRITE_BEFORE_CLAIM_GATE` unset (A2 OFF)
- `ARM=A` (wrapper prefix omits HWO env)
- Model: `gemma-4-26B-A4B-it-MLX-8bit`
- Toolsets: `delegation,todo,clarify,file_readonly`
- Per-turn timeout: 1500s; per-trial wall cap: 1800s (30 min)
- Wrapper: `probe-variantJ-wrapper.sh` (forwards A1 env flag via `HWO_PREFIX` when A1 env set; HWO prefix omitted because `HERMES_WORKER_OVERLAY` unset)

## Trial records

| # | Task | Run | Start (UTC)          | End (UTC)            | Wall  | Parent session            | Child session(s)                                                                 | Status | Tripwire         |
|---|------|-----|----------------------|----------------------|-------|---------------------------|----------------------------------------------------------------------------------|--------|------------------|
| 1 | T4   | 1   | 2026-04-21T02:46:32Z | 2026-04-21T02:47:02Z | 30s   | 20260420_214633_4a54d5    | 20260420_214643_ecf4a9                                                           | PASS   | PREFLIGHT=PASS   |
| 2 | T5   | 1   | 2026-04-21T02:47:06Z | 2026-04-21T02:47:51Z | 45s   | 20260420_214706_9d0c7d    | 20260420_214711_99acf8                                                           | PASS   | PREFLIGHT=PASS   |
| 3 | T6   | 1   | 2026-04-21T02:47:54Z | 2026-04-21T02:49:49Z | 115s  | 20260420_214754_6c8cd8    | 20260420_214759_7dd9e5, 20260420_214835_0c662e, 20260420_214908_0c790a           | PASS   | PREFLIGHT=PASS   |
| 4 | T10  | 1   | 2026-04-21T02:49:54Z | 2026-04-21T02:55:14Z | 320s  | 20260420_214954_484b8a    | 20260420_214959_d7d9fc, 20260420_215016_7d50ee, 20260420_215346_dae245, 20260420_215428_5d5c57 | PASS   | PREFLIGHT=PASS   |
| 5 | T4   | 2   | 2026-04-21T02:55:17Z | 2026-04-21T02:55:47Z | 30s   | 20260420_215518_2c9c99    | 20260420_215523_278ce3                                                           | PASS   | PREFLIGHT=PASS   |

Total wall-clock: 540s (9 min). All five trials produced `RESULT=COMPLIANT` verdicts from the check script. Per-trial OMLX_HEALTH=CLEAN after each trial. No retries needed — all initial β-fuse dispatches passed the check on first attempt (`attempts=1` in every OUTCOME line).

Child-session detection notes:
- Trial 3 (T6) listed Trial 2's parent `20260420_214706_9d0c7d` as an additional candidate due to the mtime-only window filter in the runner; the actual Trial 3 children are the three 21:47:59–21:49:08 sessions. The runner records the full window set; downstream judges should cross-reference by trial start time.
- Trial 4 (T10) spawned four child sessions, consistent with multi-worker dispatch observed in prior Arm F T10 trials.

(No `a2_gate_outcome` column — Arm G has A2 disabled, so no gate data is produced in parent JSONs.)

## Unstage verdict

Unstage sequence executed in reverse stage order:
1. `probe-variantJ-A1-stage.sh unstage` — delegate_worker_v2.py restored from `.probe-r7.7-orig`.
2. Manual removal of `delegate_worker_v2.py.probe-r7.7-orig` on VM (per task instruction).
3. `probe-variantH-stage.sh unstage` — run_agent.py and gemma_parser.py restored from `.probe-r7.6-orig`; no stray markers.
4. `probe-variantG-stage.sh unstage` — run_agent.py restored from `.probe-r7.5-orig`; no stray `_resolve_tools_for_turn_r75a` references.
5. `probe-variantF-stage.sh unstage` — toolsets.py, model_tools.py, run_agent.py restored from `.probe-r7.4-orig`; delegate_worker_v2.py moved to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`; no stray v2 references.

All unstage steps exited cleanly. No r7.7-specific backups remain on the VM.

## Final VM canonical

```
0780c232a6cb52e13e432261f0d68ad9  /home/parallels/.hermes/hermes-agent/HERMES.md
fb1a5a5208a6cf2fcb8252aac10397eb  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md
```

Both tripwires match canonical. `find /home/parallels/.hermes -name "*.probe-r7.7*"` returns empty.

Final preflight:
```
[GATE: agent_dispatch] PASS    [GATE: omlx] PASS (OMLX_HEALTH=CLEAN)
[GATE: tripwire]       PASS    [GATE: vm_idle] PASS
PREFLIGHT=PASS
```

## Summary

Arm G batch 1 completed cleanly: 5/5 trials returned `RESULT=COMPLIANT` (dispatch-level β-fuse compliance) with no retries required. Total runtime 9 minutes, well under the 75-min budget. VM canonical fully restored at exit. No HALT conditions triggered. Judge dispatch against these five sessions can now proceed on the MoE campaign track. Note: this artifact only records dispatch-level PASS (β-fuse check); downstream judge PASS counts are not yet known and will be generated by the separate fresh-judge pass used for Arm F comparison.
