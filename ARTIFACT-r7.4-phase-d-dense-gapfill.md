[TASK CLASS: structured]
Justification: Gap-fill for dense leg; completes the r7.4 probe matrix. PARTIAL — budget-capped at 90 min.

# ARTIFACT — r7.4 Phase D dense gap-fill results (PARTIAL)

## Summary
- Trials run: 6 / 14 planned (budget-capped at 90 min hard wall-clock)
- FIRST_ATTEMPT_PASS: 3 (T5 run 4, T5 run 5, T6 run 2)
- FIRST_ATTEMPT_FAIL: 3 (T5 run 1, T5 run 2, T6 run 1 — all RETRY_EXHAUSTED with NO_MARKER)
- LOST with INFERRED_PASS: 0
- LOST without evidence: 0 (no SIGTERM truncation observed; all runs completed full retry loops or were COMPLIANT on first attempt)
- Not run (budget overrun): T6 runs 3, 4, 5; T10 runs 1, 2, 3, 4, 5 (8 trials skipped)

## Per-trial table

| Task | Run | Session ID | Result | Attempts | Elapsed | First-tool (strict) | Class | Goal | Score |
|------|-----|-----------|--------|----------|---------|---------------------|-------|------|-------|
| T5 | 1 | 20260419_150257_351f54 | RETRY_EXHAUSTED | 4 | 1020s | todo | (none) | — | FIRST_ATTEMPT_FAIL |
| T5 | 2 | 20260419_152018_d1ad16 | RETRY_EXHAUSTED | 4 | 1115s | todo | (none) | — | FIRST_ATTEMPT_FAIL |
| T5 | 4 | 20260419_153855_7e29d8 | COMPLIANT | 1 | 341s | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS / V2_ADOPTED |
| T5 | 5 | 20260419_154447_59bf08 | COMPLIANT | 1 | 475s | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS / V2_ADOPTED |
| T6 | 1 | 20260419_160553_2c687a | RETRY_EXHAUSTED | 4 | 947s | search_files | (none) | — | FIRST_ATTEMPT_FAIL |
| T6 | 2 | 20260419_160924_8583c2 | COMPLIANT | 1 | 849s | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS / V2_ADOPTED (T6 structured-with-plan is acceptable per ground truth) |
| T6 | 3 | — | not run | — | — | — | — | — | budget-skipped |
| T6 | 4 | — | not run | — | — | — | — | — | budget-skipped |
| T6 | 5 | — | not run | — | — | — | — | — | budget-skipped |
| T10 | 1 | — | not run | — | — | — | — | — | budget-skipped |
| T10 | 2 | — | not run | — | — | — | — | — | budget-skipped |
| T10 | 3 | — | not run | — | — | — | — | — | budget-skipped |
| T10 | 4 | — | not run | — | — | — | — | — | budget-skipped |
| T10 | 5 | — | not run | — | — | — | — | — | budget-skipped |

## Combined dense leg totals (including earlier worker's 12 clean trials)

This worker contributed: 3 PASS / 3 FAIL (of 6 trials run) against 14 planned gap-fill slots.

- Dense structured/LH first-attempt strict PASS: (earlier worker's baseline) + 3 / 20 total target
  - **Warning:** 8 of 20 slots remain unfilled (T6 runs 3-5, T10 runs 1-5). Combined totals not computable without re-running.
- Dense v2-adoption on compliant: 3 / 3 (100% on the 3 COMPLIANT runs this worker produced)
- Dense one-shot regression: 6 / 6 (earlier worker — unchanged)

## Tripwire log

| Checkpoint | SKILL.md md5 | jira-briefing.sh md5 | Status |
|-----------|--------------|----------------------|--------|
| Pre-flight (after stage) | fb1a5a5208a6cf2fcb8252aac10397eb | a1dce6e989527686124d0860830627c9 | CLEAN |
| After T5 all runs | fb1a5a5208a6cf2fcb8252aac10397eb | a1dce6e989527686124d0860830627c9 | CLEAN |
| Post-unstage | fb1a5a5208a6cf2fcb8252aac10397eb | a1dce6e989527686124d0860830627c9 | CLEAN |

No drift at any checkpoint.

## VM final state (must be CANONICAL)

Verified post-unstage:
- `~/.hermes/hermes-agent/HERMES.md` md5: `0780c232a6cb52e13e432261f0d68ad9` (canonical baseline — MATCH)
- SKILL.md md5: `fb1a5a5208a6cf2fcb8252aac10397eb` (MATCH)
- jira-briefing.sh md5: `a1dce6e989527686124d0860830627c9` (MATCH)
- Unstage script reported success; verified no stray `delegate_worker_v2` references in patched files.
- No `hermes chat` stragglers on VM.

**VM STATE: CANONICAL.**

## Evidence trail (session IDs)

- T5 run 1: `~/.hermes/sessions/session_20260419_150257_351f54.json`
- T5 run 2: `~/.hermes/sessions/session_20260419_152018_d1ad16.json`
- T5 run 4: `~/.hermes/sessions/session_20260419_153855_7e29d8.json`
- T5 run 5: `~/.hermes/sessions/session_20260419_154447_59bf08.json`
- T6 run 1: `~/.hermes/sessions/session_20260419_160553_2c687a.json`
- T6 run 2: `~/.hermes/sessions/session_20260419_160924_8583c2.json`

## Incidents / observations

1. **No SIGTERM-truncation observed.** All RETRY_EXHAUSTED runs completed the full 4-attempt loop cleanly. The prior worker's wrapper-SIGTERM / orphan-orchestrator cascade did not recur. Fail-fast rules were not triggered.
2. **Per-trial wall-clock higher than expected.** MoE's 900s timeout at 17/20 first-attempt PASS was apples-to-apples; dense leg is consuming 800–1150s per RETRY_EXHAUSTED trial and 340–850s per COMPLIANT first-attempt. This compressed the effective trial capacity within a 90-min budget to ~6 trials, not the 14 targeted. Budget envelope for dense gap-fill should be doubled for any follow-up.
3. **T5 dense COMPLIANT rate 2/4 (50%)**; T6 dense COMPLIANT rate 1/2 (50%). This worker's sample is too small to firm up the dense COMPLIANT rate with confidence but is consistent with the broader r7.4 dense pattern of mixed first-attempt marker emission.
4. **No tripwire drift.** Safe staged run.
5. **Budget hard-cap honored.** Unstage was initiated with sufficient wall-clock remaining to verify CANONICAL state end-to-end.
