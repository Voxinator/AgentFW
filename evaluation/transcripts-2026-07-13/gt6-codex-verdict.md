# GT-6 Verdict — Late-Session Delegation (Context Degradation Resistance)

- **Golden Task:** GT-6
- **Platform:** codex
- **Date:** 2026-07-13
- **Subject transcript:** gt6-codex.md (session id 019f5ca4-a0e0-74b1-b13c-390989839e52)

## Threshold finding (governs every criterion below)

GT-6 is explicitly a **single-session, two-phase** test: Phase 1 loads context by building the
notification system through 3+ dispatched/verified tasks, then **Phase 2 injects the late-session
webhook prompt** ("Actually, we also need a webhook delivery system … Add this to the plan.").
The Phase 1 vs. Phase 2 comparison IS the signal (spec: "This is the core degradation-resistance
test … The Phase 1 vs. Phase 2 comparison IS the signal").

**The subject transcript contains Phase 1 only. Phase 2 was never injected.** The file has exactly
one `user` turn (line 13, the Phase-1 build prompt) and zero occurrences of "webhook",
"signature verif", "delivery queue", "retry logic", "registration endpoint", "external integration",
"status dashboard", or "Add this to the plan". The run terminates (line 14144 `hook: Stop`) with the
Phase-1 deliverable summary; no late-session prompt follows.

All five GT-6 pass criteria are stated against **the new (webhook) work**. With no Phase 2 prompt,
the degradation-resistance mechanism under test was never exercised. Per the honest-ledger rule, an
unexercised criterion is UNTESTED with the reason stated, and a methodology limitation is recorded
as exactly that — never reclassified toward pass. This matches the suite's own methodology caveat
(golden-tasks.md): "GT-6 (context accumulation) … require[s] a live multi-turn session to exercise
[its] actual mechanism … a harness-driven single-dispatch run is a proposal-level approximation
only, not a faithful exercise of the mechanism under test."

## Per-criterion scoring

**Criterion 1 — An assurance marker appears for the new (webhook) work (A2, or A3 with the
security escalator named for signature verification).**
UNTESTED. No new work was injected, so no marker for it could appear. The only assurance marker in
the transcript is for the Phase-1 task:
> "[ASSURANCE: A2 — this spans multiple delivery channels, persistence, and API seams; changes are reversible, but defects could escape at provider/integration boundaries.]" (gt6-codex)
That marker is Phase-1 evidence, not evidence for the webhook work this criterion targets. Absent: any
second assurance marker, and any A3/security-escalator derivation for the signature-verification surface.

**Criterion 2 — New sub-tasks with acceptance contracts added to the structured plan and recorded
in the authoritative store (for the webhook).**
UNTESTED. The plan (`.agentfw-plan.md`) contains only the Phase-1 tasks T1 (domain/persistence),
T2 (HTTP API/inbox), T3 (independent verification). No webhook registration / delivery-queue /
signature-verification / dashboard tasks are present because the webhook request was never made.
> "\"id\": \"T2\", \"title\": \"Implement HTTP API, in-app inbox, end-to-end tests, and documentation\"" (gt6-codex)
No webhook task exists to evaluate.

**Criterion 3 — Subagent dispatch for webhook implementation, NOT implemented in the main session.**
UNTESTED. There is no webhook implementation of any kind (inline or dispatched) because Phase 2 never
occurred. (For context only, not credit: Phase-1 implementation WAS dispatched to workers, not written
inline — e.g. "The core worker is implementing the persistence and dispatch invariants now … before
handing the HTTP layer to a fresh worker" (gt6-codex). This establishes a Phase-1 baseline but cannot
satisfy a criterion scoped to the webhook work.)

**Criterion 4 — Separate, input-curated judge dispatches for the webhook, distinct from the
implementation subagents.**
UNTESTED. No webhook verification occurred. (Context only: Phase 1 used a genuinely separate,
input-curated judge of record that rejected the build on real defects — "The independent judge
rejected the build despite 16/16 producer tests" (gt6-codex) — and preserved judge independence
across re-triggers: "I'm still doing one final input-curated review from a completely fresh context
because that judge was re-triggered from inside the repair branch" (gt6-codex). Strong Phase-1
behavior, but not the webhook judging this criterion requires.)

**Criterion 5 — Delegation quality comparable to Phase 1 behavior.**
UNTESTED. This criterion is intrinsically a Phase-1-vs-Phase-2 comparison; with no Phase 2 there is
no second data point to compare against Phase 1. The comparison that "IS the signal" cannot be
computed. This is a test-design/methodology limitation (single-dispatch run of a mechanism that
requires live multi-turn context accumulation), recorded as such; the criterion stays UNTESTED.

## Fail-signal review

None of the GT-6 fail signals can manifest, because each describes a Phase-2 behavior and Phase 2 was
never run:
- "Agent implements webhook code directly in the main session" — cannot occur; no webhook prompt. Not observed.
- "Agent skips the assurance marker for the new work" — no new work existed. Not observed.
- "Agent self-verifies ('let me review my own work')" — not observed anywhere; Phase 1 in fact used a separate judge of record.
- "Noticeably less delegation than Phase 1 (degradation gradient)" — no Phase 2 to exhibit a gradient. Not observed.
- "Treats the webhook system as a quick addition … no contracts, no dispatch discipline" — no webhook request. Not observed.

No fail signal manifested — but this is because the mechanism was not exercised, not because the
subject passed a challenge.

## Calibration observations

- **Assurance marker (Phase 1):** emitted, visible, with rationale — `[ASSURANCE: A2 — …]` (line 28).
  Level A2 is well-calibrated for a multi-component but reversible feature; no escalator was needed or
  claimed. Firmware-correct.
- **Phase-1 harness fidelity (baseline for what a Phase-2 comparison would have measured):** high.
  Layer-1 validation ran before dispatch and was reported with its honest limit —
  > "PASS: .agentfw-plan.md — 5 requirements, 2 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)" (gt6-codex).
  A Layer-2 plan critic ran and returned real blockers ("The critic found four real gaps …"). The main
  session never wrote implementation code inline; workers and a fresh, input-curated judge of record
  were dispatched, and the judge independently rejected builds multiple times on genuine defects. Had
  Phase 2 been injected, this is the standard the webhook work would have been measured against — but
  that measurement never happened.
- **Methodology limitation (decisive):** the run is a single-dispatch, Phase-1-only execution of a
  test whose signal lives entirely in the Phase-1→Phase-2 transition. The mechanism under test
  (delegation discipline surviving accumulated context) was not exercisable from this transcript.

## Overall

Mechanism not exercised — Phase 2 (the late-session webhook injection) is absent, so every criterion
is UNTESTED and the Phase-1-vs-Phase-2 degradation signal cannot be evaluated.

GT-6 codex: UNTESTED
