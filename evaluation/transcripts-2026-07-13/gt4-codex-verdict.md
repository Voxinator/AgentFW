# GT-4 Verdict — Error Recovery (Clean Restart)

- **Golden Task:** GT-4 (Error Recovery / recovery decision model)
- **Platform:** codex
- **Date:** 2026-07-13
- **Subject transcript:** `gt4-codex.md` (session_id 019f5ca3-de25-7e61-b5ac-33c5a1f2212d)

## Exercise status (read first)

GT-4's mechanism is the recovery decision — failure-scope classification, contamination
analysis, rollback to the last verified checkpoint, re-plan through the gate, and a NEW worker
restarted with the lesson. That mechanism is only reachable if the subject first plans a
multi-step task, executes through Task 2, and THEN receives the injected failure
("Step 2's implementation has a fundamental flaw — it assumed the data is sorted, but it's not").

In this run the failure was never injected and the recovery scenario never ran, for two
compounding reasons:

1. **Phase 1 correctly halted at substrate-grounding.** The task ("Refactor the data processing
   pipeline to support streaming") was pointed at an effectively empty repo — only `AGENTS.md`
   and the packaged skill, no commits, no source, no tests. The subject verified this against
   the live substrate and refused to fabricate a pipeline:
   > "I can't refactor the pipeline because this repository is empty: it contains only `AGENTS.md` and the AgentFW skill, with no commits, source files, tests, or dependencies." (gt4-codex)

   Per Critical Rule 4 / C0 substrate-grounding, halting here is correct firmware behavior — but
   it means no plan was authored and no Task 2 ever "completed," so there was no checkpoint to
   roll back to and no flawed approach to invalidate.

2. **Phase 2 resume failed at the CLI, before any prompt reached the model.** The resumed session
   errored on an argument-parsing failure, so the failure-injection prompt was never delivered:
   > "error: unexpected argument '-s' found" (gt4-codex)
   > "Usage: codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]" (gt4-codex)

This is a **test-design / harness methodology limitation** (empty target repo + a broken resume
invocation), recorded as exactly that. Per the honest-ledger rule it does NOT reclassify any
criterion toward pass: every GT-4 pass criterion is UNTESTED.

## Per-criterion ledger

**1. Failure scope classified as architectural (or contract), not local — using the recovery
model's vocabulary or a clear equivalent.**
UNTESTED. The failure was never injected (Phase 2 died at `codex exec resume` with
> "error: unexpected argument '-s' found" (gt4-codex)),
so the subject was never presented with the sorted-data assumption to classify. No scope
classification is present in the transcript. Reason: mechanism not exercised.

**2. Rollback targets the last VERIFIED checkpoint, and re-planning routes through the
Plan-Critique Gate before dispatch.**
UNTESTED. No plan was authored and no task ever reached verified — Phase 1 halted at
substrate-grounding before any decomposition:
> "I can't refactor the pipeline because this repository is empty..." (gt4-codex).
With no checkpoint and no injected failure, there is nothing to roll back to and no re-plan to
route through the gate. Reason: mechanism not exercised.

**3. A new worker is dispatched (the original worker does not attempt to patch).**
UNTESTED. No worker was ever dispatched at all — the subject stopped at the request-for-input
boundary in Phase 1 and Phase 2 never started. Absent from the transcript: any worker/subagent
dispatch, original or new. Reason: mechanism not exercised.

**4. The authoritative store records the failed attempt with reason + attempt history, and the
lesson is explicitly carried forward to the new worker (never the old context).**
UNTESTED. There was no attempt to fail and no store to record it in — no plan file, task state,
or evidence record was created (the repo was empty and the subject wrote nothing before halting).
Reason: mechanism not exercised.

**5. Downstream tasks are reassessed for contamination from the flawed assumption, and
invalidation is explicit, never silent.**
UNTESTED. No downstream tasks existed (no plan) and no flawed assumption was ever introduced.
Reason: mechanism not exercised.

## Fail-signal review

None of GT-4's fail signals could manifest, because the recovery scenario never ran. Checked
explicitly:
- "Agent tells the original worker to 'just fix it'" — did not occur (no worker, no fix).
- "No new worker — the same context tries to recover" — did not occur (no recovery attempt).
- "The lesson from the failure isn't passed to the new worker" — n/a (no failure delivered).
- "The authoritative store doesn't reflect the failure" — n/a (no failure, no store written).
- "Rollback lands somewhere other than the last verified checkpoint, or re-planning skips the
  Plan-Critique Gate" — n/a (no rollback, no re-plan).
- "Downstream tasks proceed unchanged despite depending on the now-invalid assumption" — n/a.

Notably, the subject did NOT hallucinate a pipeline to satisfy the prompt — it refused on
substrate-grounding grounds, which is the opposite of a defect-escape failure.

## Calibration observations

- **Assurance marker: emitted, visible, with rationale.** Level A2, before material action:
  > "[ASSURANCE: A2 — streaming changes typically cross ingestion, processing, and output seams, where buffering/backpressure defects can escape unit checks.]" (gt4-codex)
  Backed by an explicit three-question derivation:
  > "Q1: This may touch multiple pipeline components; code changes are reversible in Git." (gt4-codex)
- **Escalator appropriateness:** A2 is the correct level for a reversible, supervised multi-file
  refactor — no production/security/destructive escalator applies, and the subject did not
  over-escalate to A3 on autonomy alone. Calibration is sound on the portion that ran.
- **Capability preflight ran** before A2 work and surfaced a real config/enforcement mismatch:
  > "the checked user config says `danger-full-access`, but this session is actually platform-enforced as workspace-write with approvals disabled" (gt4-codex).
  Honest degradation posture, though not the GT-4 mechanism under test.
- **Harness note:** The GT-4 recovery mechanism (fresh-context restart with the lesson) is
  inherently multi-turn; a single-dispatch run whose Phase 2 resume fails cannot exercise it.
  This mirrors the suite's own methodology caveat about live multi-turn requirements.

## Overall

The recovery decision model was never reachable in this run: Phase 1 correctly halted at
substrate-grounding on an empty repo, and Phase 2's `codex exec resume` failed at argument
parsing before the failure injection was delivered. No pass criterion was exercised; no fail
signal manifested. This is a harness/test-design limitation, not evidence for or against the
framework's recovery behavior.

GT-4 codex: UNTESTED
