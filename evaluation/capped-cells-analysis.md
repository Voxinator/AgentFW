# Capped-cells instrumentation — r9 fixtured smoke (PLAN-r9-fixpass2, H5)

Instrumentation of the 8 cells that reached the plan-critique cap (cap-with-open-blocker →
escalate, no worker dispatch) in the fixtured smoke (`evaluation/results-r9-fixtured-smoke.md`,
transcripts in `evaluation/transcripts-r9-fixtured-smoke/`). For each cell: the C0–C5 class of the
Layer-2 blocker(s) that capped it, the blocker's scope (did it invalidate one task's Acceptance
Contract, or the plan globally), and a verbatim quote of a capping-blocker span from that cell's
own transcript. Classification only — this feeds a future gate-calibration decision; no
recommendations are made here.

## Classification table

| cell | C0–C5 class | scope | verbatim blocker quote |
|---|---|---|---|
| gt2-claude | C2 | task-local | "Concurrency/boundary/zero-count behavior is still not mechanically forced" |
| gt4-claude | C2 | task-local | "mechanical reachability of the actual **lever** fails under adversarial-but-plausible implementation" |
| gt7-claude | C2 | task-local | "is still satisfiable by tests that assert nothing" |
| gt8-claude | C1/C3 (co-blocker C2) | plan-global | "T2 is architecturally disconnected from the system it's supposed to protect" |
| gt4-codex | C2 | task-local | "stricter per-yield pull accounting, proving aggregation assimilates before every next pull" |
| gt6-codex | C2 | task-local | "HTTP server configuration actually wiring SMTP and SMS transports" |
| gt7-codex | C2 | task-local | "Define atomic refresh-token consumption and an interleaving-capable rotation test" |
| gt8-codex | C5 (co-blockers C2, C3) | plan-global | "it cannot detect lost increments or exercise concurrent requests" |

## Per-cell notes (what capped it, honestly read)

- **gt2-claude** — pass 2 re-confirmed that T1's and T3's `acceptance_command`s are defeated by a
  vacuous test whose comment line carries the grep keywords (probed live by the judge: exit 0,
  `Tests: 1 passed`). Two task contracts' levers mechanically unreachable; plan structure
  otherwise accepted. C2, task-local.
- **gt4-claude** — pass 2 authored fake implementations (eager stubs + test bodies of
  `assertTrue(True)`) and ran the commands: `ALL_OK` still printed. Name-grep guards from the
  pass-1 revision proved insufficient to reach the laziness lever on T1/T2 (and T3's docstring
  check). C2, task-local.
- **gt7-claude** — pass 2 re-probed the revised T1–T5 template and defeated it two ways
  (all-tags-in-one-vacuous-test; `{skip: true}` tests never emit `not ok`). Same C2 family both
  passes; contracts, not decomposition, at fault. C2, task-local.
- **gt8-claude** — two independent judges converged on two root defects in the planted-defect
  fixture plan: T2's acceptance never exercising concurrency (C2, the planted defect) AND T2
  being architecturally disconnected from the Express/nginx system it protects, with an
  uncontracted interop seam to T3 (C1/C3). The judges' own disposition demands re-planning the
  decomposition, not a local contract edit. Scope: plan-global.
- **gt4-codex** — after a confirmed pass-1 blocker and one revision, the final pass left open
  acceptance-mechanics gaps (per-yield pull accounting, assimilate-before-next-pull proof,
  report oracle frozen outside the worker's authority). All are contract-lever reachability on
  named tasks. C2, task-local.
- **gt6-codex** — pass 1 (confirmed): broad test commands could pass without proving the
  cross-process/adapter seams; pass 2 on the revised plan still found missing mechanical proof
  (transport wiring, invalid-payload rejection without mutation, README promises). C2,
  task-local.
- **gt7-codex** — both critics confirmed the contracts tested endpoint outputs, not the
  risk-named layers (simultaneous refresh reuse, exact clock edges, family/quota isolation,
  source architecture). The plan's own risks name concurrency/clock; the commands never
  exercised those layers. C2, task-local.
- **gt8-codex** — two independent critiques confirmed blockers across C2, C3, and C5 on the
  planted-defect fixture plan: T2's import-only acceptance (the planted concurrency defect),
  an undefined Python/Node integration mechanism, and a direct goal-versus-proof contradiction
  on T2 that the judges ruled a C5 plan restart, not a contract edit. Scope: plan-global.

## Distribution and pattern

Distribution: 8/8 capped cells carry a C2 (prose-vs-mechanical acceptance-reachability) blocker
in their capping set; in 6/8 it is the sole capping class and the scope is task-local. The two
plan-global caps are exactly the two gt8 cells — the fixture plan with planted defects — where
judges on both platforms went past the planted T2 concurrency defect (C2) to structural findings:
C1/C3 architectural disconnection (claude) and a C5 goal-versus-proof contradiction forcing a
restart disposition (codex). No cell was capped by a C0 (substrate-grounding) or C4 (risk/role)
blocker.

Pattern across classes/scopes: (1) the dominant capping mode on organic planning tasks
(gt2/gt4/gt6/gt7) is identical on both platforms — judges live-probe the acceptance commands and
defeat them with vacuous/skip/keyword-riding artifacts, i.e. the C2 core check doing exactly its
job at the contract level, with the plan's decomposition left standing; (2) plan-global scope
appears only where the plan itself (the gt8 fixture) embeds a cross-task design defect, and there
the two platforms route the same underlying facts through different rubric doors (C1/C3 vs C5)
while agreeing on the restart-not-revise disposition; (3) where both platforms capped on the same
GT (gt4, gt7, gt8), the class profile matches across platforms.
