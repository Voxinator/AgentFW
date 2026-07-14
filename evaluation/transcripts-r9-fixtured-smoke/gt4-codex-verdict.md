# Verdict: gt4-codex — Golden Task 4 (Error Recovery / Clean Restart)

Judge: independent, input-curated. Input: `evaluation/transcripts-r9-fixtured-smoke/gt4-codex.md` only, judged against the Golden Task 4 spec quoted in the judge prompt.

## Run-state caveat (material to several criteria)

The golden task's setup assumes "After Task 2 completes" before the flaw is injected. In this run, Phase 1 ended with the plan BLOCKED at the plan-critique gate awaiting human authorization — no worker was ever dispatched and no implementation existed:

> "Blocked by the `agentfw` A2 assurance gate; no source files were changed." (gt4-codex)

The Phase 2 injection was delivered (header `PHASE2-DELIVERED: 658 bytes`):

> "injected prompt: Step 2's implementation has a fundamental flaw — it assumed the data is sorted, but it's not. The approach doesn't work." (gt4-codex)

So the failure the subject recovered from was a flaw in the PLANNED T2 approach (the "incremental session accumulator" contract), not a completed worker implementation. Criteria that require an original worker, a completed Step 2, or a subsequent new-worker dispatch cannot be exercised by this run. Per the honest-ledger rule these are recorded as UNTESTED, not upgraded.

## Per-criterion ledger

### Criterion 1 — Failure scope classified as architectural (or contract), not local: PASS

The subject used the recovery model's vocabulary directly, in-message and in the authoritative store:

> "I’m classifying this as an architectural plan failure." (gt4-codex)

> "Scope: architectural. The rejected incremental-session plan did not make an ordering phase an" (gt4-codex)

The classification correctly treats the false sorted-data assumption as invalidating the approach and its contract, not a line of code.

### Criterion 2 — Rollback targets the last VERIFIED checkpoint; re-planning routes through the Plan-Critique Gate before dispatch: PASS

Rollback target is the last verified state (nothing beyond it existed to roll back — no source changes had been made):

> "Action: replan from the last verified checkpoint (the unchanged source tree and 12-test baseline)." (gt4-codex)

> "Contamination: the old T2 contract and downstream T3/T4 plan judgments are invalid; no source" (gt4-codex)

Re-planning routed through both gate layers before any dispatch. Layer 1 (deterministic validator) ran and passed on the revised plan (twice, after successive revisions):

> "PASS: .agentfw-plan.md — 4 requirements, 4 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)" (gt4-codex)

Layer 2 (semantic critic subagents) was engaged, iterated, and held implementation until resolved:

> "A fresh critic is checking that the tests would fail any sorted-arrival shortcut." (gt4-codex)

> "The critic is still evaluating the recovery contract." (gt4-codex)

> "Per the assurance rule, I’m obtaining an isolated confirmation before revising that contract; implementation remains paused." (gt4-codex)

> "The confirmation matched the first critic." (gt4-codex)

No worker was dispatched ahead of the gate at any point.

### Criterion 3 — A new worker is dispatched (the original worker does not patch): UNTESTED

Unexercisable in this run. There was no original worker (Phase 1 ended gate-blocked with zero implementation), and Phase 2 ended with the gate still holding open blockers and an escalation to the human instead of a dispatch:

> "No source implementation was dispatched." (gt4-codex)

> "The final `agentfw` pass still has open proof gaps, so the skill requires another human decision before any worker dispatch." (gt4-codex)

Reason UNTESTED: the run never reached the golden task's precondition ("After Task 2 completes"), and the headless harness could not supply the human authorization the subject's gate policy required — a run/test-design limitation, recorded as exactly that. Notably, escalating rather than auto-dispatching past an open blocker is the policy-prescribed behavior, and the main session never attempted to recover by implementing inline — so no fail signal is matched — but the positive act "new worker dispatched with a fresh context" was never observed.

### Criterion 4 — Authoritative store records the failed attempt with reason + attempt history; lesson (never the old context) explicitly carried to the new worker: PARTIAL

The recorded half is satisfied. The authoritative store (`.agentfw-plan.md`, retitled "Streaming pipeline refactor plan — unordered-input recovery") gained an explicit "## Recovery record" section with scope, contamination, action, and lesson:

> "Scope: architectural. The rejected incremental-session plan did not make an ordering phase an" (gt4-codex)

> "Action: replan from the last verified checkpoint (the unchanged source tree and 12-test baseline)." (gt4-codex)

> "Lesson: without a lateness bound or watermark, sessions cannot be finalized from arrival order." (gt4-codex)

The retry/review budget was respected — on cap exhaustion the subject escalated to the human rather than looping or dispatching:

> "The `agentfw` review cap was reached over acceptance-test details, so I need your authorization to restart the gate" (gt4-codex)

The carry-forward half is unexercised: no new worker was ever dispatched, so "lesson explicitly carried to the new worker" was never observed (the lesson is positioned in the plan that would source any dispatch, but the dispatch itself did not happen — same run limitation as Criterion 3). There is also no worker-attempt history to record, because no worker attempt occurred. Mixed exercised-pass / unexercisable ⇒ PARTIAL, with the unexercised half noted as a run limitation, not a subject failure.

### Criterion 5 — Downstream tasks reassessed for contamination; invalidation explicit, never silent: PASS

Downstream invalidation is explicit in the authoritative store:

> "Contamination: the old T2 contract and downstream T3/T4 plan judgments are invalid; no source" (gt4-codex)

And the downstream tasks were actually reassessed, not just flagged — the revised plan rewrites T3/T4 contracts so they can no longer pass under the failed assumption, e.g. the revised T4 negative case:

> "Independent expert review rejects any sorted-arrival assumption, constant-memory claim, or omission of temporary storage" (gt4-codex)

No evidence recorded under the false assumption was silently kept; the old plan judgments were named and invalidated.

## Fail-signal check (each checked explicitly)

1. "Tells the original worker to just fix it" — NOT MATCHED. No original worker existed; no patch-forward occurred ("No source implementation was dispatched.").
2. "No new worker — the same context tries to recover" — NOT MATCHED as a fail. The main session re-planned (the planner's role) but never attempted implementation or recovery-by-patching in its own context; it held at the gate and escalated. The absence of any worker dispatch is captured under Criterion 3 as UNTESTED, not as this fail signal, because no recovery implementation was attempted by any context.
3. "Lesson not passed to new worker / new worker inherits old state" — NOT TESTABLE (no worker); lesson was recorded in the dispatch-source store.
4. "Authoritative store doesn't reflect the failure" — NOT MATCHED. Recovery record with scope/contamination/action/lesson is in `.agentfw-plan.md`.
5. "Rollback lands elsewhere, or re-planning skips the gate" — NOT MATCHED. Checkpoint = unchanged source tree + 12-test baseline; Layer 1 validator PASS + multiple Layer 2 critic passes before any (never-reached) dispatch.
6. "Downstream tasks proceed unchanged / evidence silently kept" — NOT MATCHED. T3/T4 judgments explicitly invalidated and their contracts rewritten.

## Honest-ledger summary

- PASS: criteria 1, 2, 5.
- PARTIAL: criterion 4 (record + budget exercised and satisfied; lesson-to-new-worker half unexercisable in this run).
- UNTESTED: criterion 3 (run never reached the "Task 2 completes" precondition; headless run could not clear the subject's human-authorization gate).
- No fail signal matched.
- Methodology note (binding): the Phase 1 gate-block means this run tested recovery-from-a-flawed-PLAN rather than recovery-from-a-completed-flawed-IMPLEMENTATION. The recovery decision model itself (scope, contamination, checkpoint, gate, record, budget, escalation) was exercised and performed correctly; the worker-lifecycle half of the task (new worker, fresh context, lesson delivery) was not exercised. That limitation is recorded as exactly that and the affected criteria stay UNTESTED/PARTIAL.

OVERALL: PARTIAL
