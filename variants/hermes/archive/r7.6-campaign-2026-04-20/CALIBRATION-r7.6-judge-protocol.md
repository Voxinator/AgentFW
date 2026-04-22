# CALIBRATION — r7.6 judge protocol

Codified 2026-04-19 per PLAN-r7.6-P1C-fixes-implementation.md §7.2b, Fix 5.
Formalizes the fresh-sub-agent sample-verify approach first used in the P1-C
rev-1 dispatch (ARTIFACT-r7.6-judge-sample-setup.md + judge-brief-{1..5}.md).

## 1. Purpose

Orchestrator-in-process heuristic judging (e.g. `/tmp/probe-r7.6-P1C-logs/judge-trial.py`)
is fast and cheap but has systematic error in both directions, as demonstrated
by the rev-1 fresh-judge sample (agreement 3/5 against orchestrator). This
protocol makes **fresh-sub-agent sample-verify a standing gate** that MUST run
before any ship decision based on probe aggregate results. The orchestrator
script is a SCREEN, not the judge of record.

Scope: applies to any probe campaign whose outcome feeds a ship-gate or
methodology decision (e.g. P1-C "Arm B vs Arm A +6 delta"). Does not apply to
smoke probes whose only purpose is regression detection.

## 2. Sample selection algorithm (5-trial stratified)

Given an N-trial probe campaign with recorded per-trial verdicts, select
exactly 5 trials honoring ALL of the following constraints simultaneously.
When constraints conflict, prioritize verdict-class coverage first, then
task coverage, then borderline-case inclusion.

1. **Verdict class coverage.** Exactly 2 PASS + 2 FAIL + 1 LOST, OR — if the
   campaign produced <2 of any class — the nearest achievable stratification
   documented in the sample-setup artifact. Never collapse to single-class.
2. **Task coverage.** At least 2 distinct tasks represented among the 5.
   When the campaign includes long-horizon tasks (T10-class), include at
   least 1 long-horizon if any exist in the verdict pool.
3. **Arm coverage (for comparative campaigns).** When comparing two arms
   (e.g. Arm A baseline vs Arm B treatment), sample BOTH arms. Over-sample
   the treatment arm (3A / 2B or 2A / 3B is acceptable; 0 of either is not).
4. **Failure-mode coverage.** If the FAIL pool contains multiple distinct
   sub-criterion failures (e.g. TURN_EFFICIENCY vs CORRECTNESS vs SCOPE),
   prefer selections that cover different sub-criteria.
5. **Borderline inclusion.** At least 1 sample must be an *ambiguous* trial —
   a case where the orchestrator's rationale is terse / formulaic / uses a
   threshold heuristic close to its cutoff. These trials are the primary
   source of informative disagreement.
6. **Child-session existence.** All non-LOST samples must have an on-VM
   child session file verified with `ssh ubuntu-vm 'test -f <path>'`. LOST
   samples must have the sentinel child path or documented no-child state.

Document the selection with an artifact modeled on
`ARTIFACT-r7.6-judge-sample-setup.md`: sample mapping table, stratification
rationale, trade-offs made, and the orchestrator rationale verbatim for
each selected trial (needed for concordance scoring).

## 3. Concordance thresholds and escalation

Compare the 5 fresh-judge `WORKER_QUALITY` verdicts against the orchestrator's
`WORKER_QUALITY` verdicts on the SAME 5 trials. Count exact-match agreement.

| 5-sample result | Action |
|-----------------|--------|
| 5/5 agreement   | PASS — orchestrator calibration accepted for this campaign |
| 4/5 agreement   | PASS — orchestrator calibration accepted; annotate the disagreement in ship artifact |
| 3/5 agreement   | EXPAND — dispatch 5 additional stratified trials (different trials from the first 5); 10-sample requires ≥8/10 agreement to PASS |
| ≤2/5 agreement  | FAIL — ship decision blocked; orchestrator calibration rejected |

**10-sample result (only reached via expand path):**

| 10-sample total agreement | Action |
|---------------------------|--------|
| ≥8/10                     | PASS — calibration accepted |
| 6-7/10                    | FAIL — ship decision blocked; mandatory full fresh-judge re-pass |
| ≤5/10                     | FAIL — orchestrator judge is fundamentally miscalibrated; mandatory code-level diagnosis (Fix-2-style heuristic changes) before any re-use |

Sub-criterion disagreement (e.g. both judges say FAIL but for different
sub-criteria) is NOT counted as agreement at aggregate level — record it as a
separate "rationale divergence" count, informational only, and surface in ship
artifact narrative.

## 4. Fresh-judge brief template

Each fresh-judge dispatch receives a self-contained brief following the F.1
rubric template, modeled verbatim on `ARTIFACT-r7.6-judge-brief-1.md` through
`-5.md`. Required components in every brief:

- **Role framing:** "You are a fresh-context judge... You have no prior
  session context — only this brief..."
- **Pre-substituted F.1 inputs** — all 11 variables filled in concretely:
  1. TRIAL_N
  2. TASK_ID
  3. TASK_CLASS
  4. PARENT_GOAL (verbatim goal text passed to delegate_worker_v2)
  5. PARENT_SESSION_ID
  6. CHILD_SESSION_PATH (absolute on-VM path)
  7. GOAL_PATHS (JSON array of file paths)
  8. TRIPWIRE_BASELINE (JSON object of md5s)
  9. TRIPWIRE_POST (JSON object of md5s)
  10. PER_TRIAL_ARTIFACT_PATH (where the judge writes its verdict)
  11. SSH_TARGET (typically `ubuntu-vm`)
- **Self-contained BACKGROUND** — F.1 protocol description, β-fuse mechanism,
  tripwire definition, child-session JSON schema. No external references.
- **PROCEDURE** — 5 numbered steps (existence check, load, score per
  criterion, assemble verdict, write artifact).
- **Output format** — single-line `WORKER_QUALITY=<PASS|FAIL|LOST>` plus
  sub-criteria JSON plus rationale, AND a written verdict artifact at
  PER_TRIAL_ARTIFACT_PATH.
- **Scope declaration** — read-only VM access; no VM mutations; no Hermes
  invocation; no re-dispatch; local writes confined to the verdict artifact.

**Judge-shielding rule.** The brief MUST NOT contain the orchestrator's
verdict, the orchestrator's rationale, or any hint thereof. Both are held
by the planner for post-hoc comparison. Leakage invalidates the sample.

## 5. Escalation path when calibration fails

When 5-sample agreement is 3/5 or worse, or 10-sample agreement is below
threshold, the ship decision is blocked. In order of preference:

1. **Fix the heuristic judge, re-sample.** If the disagreement pattern points
   at a specific defect in the orchestrator judge (e.g. substring-match
   near-identical heuristic too loose; missing detector class for pseudo-tool-call),
   patch the judge, re-run it on the full trial pool, and dispatch a new
   5-sample against the same trials. This is the Fix-2-style path.
2. **Expand to 10-sample.** If the 3/5 result is within random-sampling
   variance of the ≥4/5 threshold and no specific defect is identified,
   dispatch 5 additional stratified trials and re-check against the 10-sample
   threshold (§3).
3. **Full fresh-LLM re-judgment.** If neither of the above resolves the
   disagreement — i.e. the orchestrator judge is fundamentally misaligned —
   dispatch fresh sub-agents for ALL trials in the campaign. Aggregate
   pass/fail counts derived from the script judge are discarded; ship gate
   uses the fresh-judge numbers exclusively.

Each escalation step produces its own artifact (sample-setup + verdicts +
calibration summary) to preserve the audit trail.

## 6. Hard rule — orchestrator-in-process judging is a FALLBACK

Orchestrator-in-process heuristic judging (Python regex + sub-criterion
scorer) is a DOCUMENTED FALLBACK, not the primary path. Its role is:

- Fast per-trial screen during probe execution (so orchestration decisions
  like "retry this trial" can be made quickly).
- Pre-filter of trial pool for fresh-judge sample selection.
- Backstop when fresh-judge dispatch is unavailable for the whole campaign
  (e.g. methodology regression per plan §7.1b).

The orchestrator judge's aggregate numbers MUST NOT be reported as
ship-gate evidence UNLESS an explicit calibration run per this protocol
has been executed AND the calibration has PASSED per §3.

If fresh-judge dispatch is unavailable for the campaign (see
`probe-preflight.sh` gate 1 `agent_dispatch`), the entire campaign is
flagged as **uncalibrated**. Ship decisions on uncalibrated campaigns are
explicitly forbidden. The pre-flight gate is structural enforcement of this
rule.

## 7. Ship-gate artifact checklist

Every ship-gate artifact that cites probe aggregate data MUST contain:

1. **Calibration reference** — path to this protocol file AND to the
   calibration run's artifacts (sample-setup + verdicts + summary).
2. **Sample-setup artifact** — the stratification document for this campaign
   (modeled on ARTIFACT-r7.6-judge-sample-setup.md).
3. **Per-trial fresh-verdict artifacts** — one per sampled trial (modeled on
   ARTIFACT-r7.6-judge-fresh-verdict-N.md).
4. **Concordance table** — side-by-side orchestrator-vs-fresh verdict for
   each sampled trial, with a total-agreement count and a §3 threshold
   decision.
5. **Escalation record (if any)** — if the initial 5-sample failed the
   threshold, all subsequent escalation steps (expand, judge-fix + re-sample,
   full re-judgment) and their outcomes.
6. **Disagreement narrative** — for each sampled trial where verdicts
   diverged, explain the specific reason (with pointers to child-session
   message indices where possible).
7. **Orchestrator-judge commit ref / file md5** — pinpoint which version of
   the heuristic judge was calibrated, so re-use on future campaigns is
   traceable.
8. **Pre-flight verdict snapshot** — the stdout line from `probe-preflight.sh`
   at the start of the campaign, proving the Agent-dispatch gate passed.

A ship-gate artifact missing ANY of items 1-4 and 8 does not satisfy this
protocol and MUST NOT be used to gate a ship decision.

## 8. Worked example — P1-C rev-1 dispatch

This protocol codifies the procedure already attempted in the P1-C rev-1
sample dispatch. That dispatch:

- Stratified 5 trials: 2 Arm A + 3 Arm B, 2 PASS + 2 FAIL + 1 LOST, tasks T4
  / T5 / T6 (see ARTIFACT-r7.6-judge-sample-setup.md §Stratification).
- Included 1 borderline (brief 2, search-thrash threshold) + 1 ambiguous
  corruption (brief 4, garbled summary).
- Produced 3/5 agreement with orchestrator — triggering this protocol's
  "EXPAND or FIX" escalation.
- Plan rev-2 Fix 2 chose the FIX path: patch `judge-trial.py`'s
  near-identical heuristic + add pseudo-tool-call detector → predicted
  post-fix agreement 5/5 (brief 3 flips PASS→FAIL; brief 2 flips FAIL→PASS).

Post-Fix-2 re-sample against the same 5 briefs closes the calibration loop.
If post-fix agreement is still below 5/5, escalate to path 2 (expand) or
path 3 (full re-judgment) per §5.
