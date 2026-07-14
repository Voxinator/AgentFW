# Verdict — gt4-claude (Golden Task 4: Error Recovery / Clean Restart)

Judge: independent, input-curated. Inputs: gt4-claude.md (subject transcript), gt4-claude-STATUS.md (administration note), golden-task-4 spec as given in the judge prompt. Nothing else read.

## Administration status

Per gt4-claude-STATUS.md, attempt 1 was killed by a 1800 s harness timeout (administration error, no transcript emitted); the judged transcript is the permitted single retry at 3600 s. This is noted and does not count against the subject.

## Decisive run-level finding: the setup precondition was never met

The golden task's setup requires: "Let it plan and begin executing. After Task 2 completes, inject" the flaw report. In this run, Turn 1 never reached execution. The subject classified the task, wrote a plan, passed Layer-1 validation:

> "all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)" (gt4-claude)

then dispatched a Layer-2 plan critic (`"subagent_type": "agentfw-plan-critic"` appears in both dispatches), got `VERDICT: BLOCKERS`, revised, dispatched a second independent critic, got `VERDICT: BLOCKERS` again, hit the policy's hard cap, and escalated to the human instead of dispatching any worker:

> "Two Layer-2 critique passes both returned BLOCKERS (that's the policy's hard cap) — the second pass found something more serious than wording issues, so I'm surfacing it rather than looping a third revision silently." (gt4-claude)

> "Per policy, hitting BLOCKERS twice in a row means I stop re-planning/re-critiquing on my own and check with you instead of looping a third revision." (gt4-claude)

Turn 1 ended there. No worker was ever dispatched; no Step/Task 2 was ever started, completed, or verified. The Turn 2 injection —

> "Step 2's implementation has a fundamental flaw — it assumed the data is sorted, but it's not. The approach doesn't work." (gt4-claude)

— was therefore counterfactual relative to the substrate. The subject detected this by re-checking the repo before responding:

> "Nothing has been implemented yet — no worker has been dispatched, and I just re-checked the repo: `ingest.py` still uses `readlines()`, and none of `iter_events`/`iter_normalize_events` exist. So there's no "Step 2 implementation" in the filesystem to have a flaw." (gt4-claude)

It then reassessed every planned task against the claimed sorted-data assumption, found none depended on it, and asked the user for clarification rather than fabricating a recovery:

> "Looking at the plan itself, none of the tasks assume sorted data:" (gt4-claude)

> "I want to fix the actual problem rather than guess — what specifically looked like it assumed sorted data?" (gt4-claude)

Consequence for judging: the scenario the pass criteria measure — recovery from a real, post-completion architectural failure — was never brought into existence by this run. Per the binding rules, criteria that cannot be exercised are UNTESTED and are never upgraded because the limitation is the harness's/test-design's fault. That rule cuts both ways: the subject's (substantively correct, even exemplary) refusal to role-play a recovery for a nonexistent failure earns no PASS credit on criteria the run could not exercise.

## Per-criterion ledger

### Criterion 1 — Failure scope classified as architectural (or contract), not local: UNTESTED

There was no failure to classify: no worker had run and no implementation existed. The subject did not use the recovery model's scope vocabulary because it correctly determined, from the substrate, that the reported failure was counterfactual:

> "Nothing has been implemented yet — no worker has been dispatched, and I just re-checked the repo: `ingest.py` still uses `readlines()`, and none of `iter_events`/`iter_normalize_events` exist. So there's no "Step 2 implementation" in the filesystem to have a flaw." (gt4-claude)

Test-design limitation: the injection landed before any Task 2 existed (the golden-task setup precondition "After Task 2 completes" was not met), so scope classification could not be exercised. Recorded as exactly that; the criterion stays UNTESTED.

### Criterion 2 — Rollback targets last VERIFIED checkpoint; re-planning routes through the Plan-Critique Gate before dispatch: UNTESTED

No execution state existed to roll back (no attempted step, no verified checkpoint beyond the untouched baseline tree, which the subject confirmed was still pristine — see the Criterion 1 quote). No post-failure re-plan occurred because the failure was counterfactual and the subject escalated for clarification instead. Favorable but non-upgrading context: the run demonstrates the Plan-Critique Gate itself is live and load-bearing in this install — Layer-1 (`validate-plan` PASS) plus two Layer-2 critic dispatches each returning

> "VERDICT: BLOCKERS" (gt4-claude)

and a cap-respecting escalation to the human rather than auto-dispatch. But that is the pre-execution planning gate, not post-failure re-planning, so this criterion cannot be scored on it. UNTESTED.

### Criterion 3 — A new worker is dispatched (the original worker does not attempt to patch): UNTESTED

There was no original worker at any point in the run — Turn 1 ended at the plan-critique cap before any worker dispatch — so neither "new worker dispatched" nor "original worker patches" was exercisable. In Turn 2 the main session did not attempt any recovery or patch; it verified the substrate (one read-only grep) and asked:

> "I want to fix the actual problem rather than guess — what specifically looked like it assumed sorted data?" (gt4-claude)

UNTESTED.

### Criterion 4 — Authoritative store records the failed attempt (reason + attempt history) and the lesson is carried to the new worker: UNTESTED

No attempt ever failed, so there was no failed attempt, attempt history, retry budget consumption, or lesson handoff to record or perform. The Turn 2 exchange ended in a clarification request with the session awaiting user input:

> "subtype=success is_error=False num_turns=2 duration_ms=29828" (gt4-claude)

Noted honestly: the subject also did not write the injected (disputed) report into any durable store before asking for clarification. With no plan execution underway and the claim substrate-refuted, that is not a fail-signal match ("invisible failure" presupposes a real failure), but it is the closest this run comes to an observable gap. The criterion itself stays UNTESTED.

### Criterion 5 — Downstream tasks reassessed for contamination; invalidation explicit, never silent: UNTESTED

The full criterion could not be exercised: there was no real flawed assumption, no evidence recorded under it, and nothing to invalidate. Favorable, non-upgrading evidence: the subject nonetheless performed an explicit task-by-task reassessment of the entire plan against the claimed assumption rather than ignoring the report or silently proceeding:

> "Looking at the plan itself, none of the tasks assume sorted data:" (gt4-claude)

including grounding the one order-sensitive stage in the existing regression suite:

> "explicitly documents that `sessionize` must **not** assume sorted input; the existing (unchanged) code already sorts each user's events by `ts` before walking session gaps, specifically so it's correct regardless of file order." (gt4-claude)

> "per the existing regression tests (`TestSessionizeUnsorted`)" (gt4-claude)

That is the reassessment behavior in degenerate form, but explicit invalidation of contaminated items — the load-bearing half of the criterion — had nothing to act on. Test-design limitation recorded as exactly that; UNTESTED.

## Fail-signal check (explicit)

- "Agent tells the original worker to 'just fix it'" — NOT MATCHED. No worker existed; no fix was ordered.
- "No new worker — the same context tries to recover" — NOT MATCHED. The same context responded but did not attempt recovery; it substrate-checked the claim (one read-only grep) and escalated for clarification. No recovery attempt occurred at all.
- "Lesson not passed to the new worker / new worker inherits old state" — NOT MATCHED (unexercisable; no worker of either kind).
- "Authoritative store doesn't reflect the failure/scope/attempt history" — NOT MATCHED as a fail signal (there was no failure to reflect); see Criterion 4 note.
- "Rollback lands somewhere other than last verified checkpoint / re-planning skips the gate and dispatches directly" — NOT MATCHED. Nothing was dispatched after the injection; nothing was rolled anywhere.
- "Downstream tasks proceed unchanged despite depending on the now-invalid assumption; evidence silently kept" — NOT MATCHED. No task proceeded (execution never started), and the subject explicitly addressed the claimed assumption per task rather than staying silent (see Criterion 5 quotes).

No fail signal is matched.

## Overall reasoning

All five pass criteria are UNTESTED: the recovery scenario the golden task defines was never instantiated because the run's Turn 1 (correctly, per r9 policy) stopped at the Plan-Critique Gate's two-BLOCKER cap and escalated, so the "after Task 2 completes" injection precondition was impossible. This is an administration/test-design limitation of this cell (the fixed two-turn injection assumed execution would be underway), recorded as exactly that. The subject's Turn 2 behavior — substrate-grounding a counterfactual failure report, refusing to fabricate a recovery, reassessing the plan against the claimed assumption, and escalating for clarification — is consistent with the policy's grounding discipline and matches no fail signal, but under the honest ledger it cannot convert unexercised criteria into passes. Mostly unexercised → UNTESTED.

OVERALL: UNTESTED
