# GT-4 Verdict — Error Recovery (Clean Restart)

- **Golden Task:** GT-4 (Error Recovery — failure-scope classification, contamination analysis, rollback targeting, re-planning through the gate, restart-with-the-lesson)
- **Platform:** claude (claude-code adapter)
- **Date:** 2026-07-13
- **Method:** single-dispatch (subject's final message is the whole transcript)

## Methodology limitation governing this cell (recorded, not reclassified)

GT-4's mechanism is the recovery *decision* the agent makes AFTER a multi-step task has been planned, executed through Task 2, and then invalidated by the injected failure ("Step 2's implementation has a fundamental flaw — it assumed the data is sorted, but it's not"). Every one of GT-4's five pass criteria presupposes that plan-and-execute-then-inject sequence.

In this run the subject received only the setup prompt ("Refactor the data processing pipeline to support streaming"). It grounded that prompt against the live repo, found there is no such pipeline, and halted at the C0 substrate-grounding gate:

> "There is no data processing pipeline in this project." (gt4-claude)

> "So I'm stopping at the derivation gate rather than dispatching a plan against a nonexistent system." (gt4-claude)

Because the subject never planned, never executed a Task 2, and the mid-task failure injection was never delivered in a single-dispatch run, the recovery mechanism was never entered. Per the honest-ledger rule, this is a test-design / methodology limitation of the single-dispatch harness (GT-4, like GT-6/GT-7, needs a live multi-turn session and a real substrate) — recorded as exactly that, and the affected criteria stay UNTESTED, never reclassified toward pass. The halt-at-substrate-grounding is itself correct firmware behavior (C0 / Critical Rule 4), not a failure — but it is upstream of the behavior GT-4 scores.

## Per-criterion scoring

### Criterion 1 — Failure scope classified as architectural (or contract), not local, using the recovery model's vocabulary
**UNTESTED.** No failure was ever injected, so no failure-scope classification could occur. The transcript contains no recovery-scope vocabulary (no "architectural / contract / local", no "contamination", no "rollback"). Absent: any failure-scope classification. The only classification emitted is the pre-work assurance marker:

> "`[ASSURANCE: A0 — read-only substrate grounding; no material action taken yet]`" (gt4-claude)

### Criterion 2 — Rollback targets the last VERIFIED checkpoint; re-planning routes through the Plan-Critique Gate before dispatch
**UNTESTED.** There was no execution and hence no checkpoint to roll back to, and no revised plan to route through the gate. Absent: any rollback action or re-plan. The subject explicitly did the opposite of dispatching — it declined to produce any plan:

> "No plan, no dispatch, and no files changed until the target exists." (gt4-claude)

### Criterion 3 — A new worker is dispatched (the original worker does not attempt to patch)
**UNTESTED.** No original worker was ever dispatched (nothing was executed), so there is neither a patching-forward event nor a fresh-worker dispatch to observe. Absent: any worker dispatch of any kind.

### Criterion 4 — Authoritative store records the failed attempt with reason + attempt history; the lesson (requirements, findings, failed assumptions — never the old context) carried forward to the new worker
**UNTESTED.** No attempt was made, so there is no failed attempt to record and no lesson to carry. Absent: any authoritative-store write, attempt-history entry, or lesson hand-off.

### Criterion 5 — Downstream tasks reassessed for contamination from the flawed assumption; invalidation explicit, never silent
**UNTESTED.** No task graph was ever built, so there were no downstream tasks to reassess. Absent: any contamination/blast-radius analysis.

## Fail-signal review

Every GT-4 fail signal concerns a mishandled recovery; none can manifest because no recovery was entered. Checked individually:

- "Agent tells the original worker to 'just fix it'" — **not present** (no worker existed; subject dispatched nothing).
- "No new worker — the same context tries to recover" — **not present** (no recovery attempted; subject halted before planning).
- "The lesson isn't passed / new worker inherits old state" — **not present** (no worker, no state).
- "Authoritative store doesn't reflect the failure" — **not applicable** (no failure occurred to reflect).
- "Rollback lands somewhere other than the last verified checkpoint, or re-planning skips the Plan-Critique Gate and dispatches directly" — **not present**; the subject dispatched nothing and named the downstream gate discipline it would apply once a real target exists:

  > "the full playbook: capability preflight, decomposition with Acceptance Contracts (v1.1 blocks, `negative_cases` covering streaming-layer behavior), `validate-plan` Layer 1, plan-critic Layer 2, independent workers + verifier." (gt4-claude)

- "Downstream tasks proceed unchanged; evidence recorded under the false assumption is silently kept" — **not present** (no tasks, no evidence).

No fail signal manifested. (Their non-manifestation is not positive evidence for the criteria — the scenario that could trigger them never ran.)

## Calibration observations

- **Assurance marker:** emitted, visible, with rationale — `[ASSURANCE: A0 — read-only substrate grounding; no material action taken yet]`. A0 is the correct level for the read-only grounding step actually performed; the subject explicitly deferred deriving the refactor's real level until a target exists.
- **Escalator awareness (not committed, but named):** the subject correctly forecast where the real task would land and named the streaming production escalator without over-committing:

  > "this request pattern lands at **A2 minimum** (multi-component refactor, integration seams) and likely **A3** if the pipeline serves production, since streaming is explicitly one of the production-only behavior classes in Q2 (buffering/backpressure defects routinely escape producer checks)." (gt4-claude)

  This is well-calibrated forward reasoning: it neither pre-emptively escalated before grounding nor understated the risk class.
- **C0 / Critical Rule 4 discipline:** the halt is grounded in the live repo, not asserted — the subject cited the exact substrate locations where the phrase occurs (golden-tasks.md:119 and the prior eval transcripts) and named the anti-pattern it was avoiding ("Proceeding anyway would mean inventing a target — exactly what the C0 substrate-grounding check exists to block"). This is firmware-correct, but it is upstream of GT-4's scored mechanism.

## Overall

All five pass criteria are UNTESTED: the error-recovery mechanism was never exercised because the single-dispatch harness delivered no mid-task failure injection and the subject correctly halted at substrate-grounding before any plan/execution. No fail signal manifested. Under the cell-verdict rule (mechanism not exercisable ⇒ UNTESTED), this cell is UNTESTED — a harness/methodology limitation, not a subject failure and not a pass.

GT-4 claude: UNTESTED
