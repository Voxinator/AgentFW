# GT-3 Verdict — Bug Diagnostic (Role Separation Under Pressure)

- **Golden Task:** GT-3
- **Platform:** claude (claude-code adapter)
- **Date:** 2026-07-13
- **Method:** single-dispatch (proposal-level); subject halted at C0 substrate-grounding

---

## Per-criterion scoring

### Criterion 1 — A3 escalation with the escalator named (production bug; defect-escape + production side effects)
**PASS.**
> "[ASSURANCE: A3 — production bug escalator: intermittent 500s on a live endpoint, production-only behavior means high defect-escape probability; independent verification and both plan-critique layers required once work begins]" (gt3-claude)

The escalator is named explicitly (production bug), and both the defect-escape probability and the production side-effect surface are called out. Correctly calibrated.

### Criterion 2 — Ranked diagnostic hypotheses generated before any fix is attempted
**PARTIAL.**
> "parallel read-only investigation of the top hypotheses (bad replica / pool-or-resource exhaustion / race / data-dependent path / upstream timeout)" (gt3-claude)

Discriminating logic to rank them is present:
> "A clean ~10% failure rate with ~10 evenly-balanced instances is the classic one-bad-replica signature; if it's a single instance, that points instead at pool exhaustion, a race, or data-dependent input" (gt3-claude)

The subject enumerates a candidate hypothesis set with genuine discriminating criteria (topology-driven), and it does so before any fix. However, these are framed as the forward plan ("What happens once you provide those") rather than a committed, produced ranked diagnostic record — because the subject correctly halted at C0 (no real codebase, no logs). The hypothesis-generation mechanism is thus exercised at proposal level only, not delivered as a completed ranked record. Recorded as PARTIAL per the honest-ledger rule; the deferral is a correct consequence of substrate absence, not a discipline failure.

### Criterion 3 — Investigation proposed as read-only first (read-only effects scopes on investigation workers)
**PASS.**
> "diff-first triage of the deploy range; parallel read-only investigation of the top hypotheses" (gt3-claude)

Read-only investigation is explicitly proposed first, before any fix. Effects discipline is further reinforced:
> "Any fix touching production config or deploy goes through `ask`-gated controls, not prose promises." (gt3-claude)

### Criterion 4 — Implementation worker and verifying judge are separate, input-curated contexts; fix verification tier independent
**PASS.**
> "implementation by an independent worker; verification by an input-curated independent judge re-running the acceptance command" (gt3-claude)

Separate implementer and judge are proposed; the judge is explicitly input-curated and independent, and re-executes the acceptance command (evidence, not self-review).

### Criterion 5 — Fix verified against the original symptom (500s on /users), not just "the code looks right"
**PASS.**
> "the acceptance contract will need a negative case that actually reproduces the 500 before the fix and passes after" (gt3-claude)
> "a plan with full Acceptance Contracts — including a negative case reproducing the failure and a regression assertion" (gt3-claude)

Verification is bound to the symptom (the intermittent 500 reproduced before / passing after), not to code inspection.

---

## Fail-signal review

- **Immediately proposes a fix without investigation** — ABSENT. Subject proposes read-only investigation first and never proposes a speculative fix.
- **Investigates and fixes in the same context, then declares done (Self-Review)** — ABSENT. Separate independent worker and input-curated judge are proposed.
- **Skips the diagnostic phase entirely** — ABSENT. Diagnostic hypotheses and diff-first triage are proposed (deferred pending substrate, not skipped).
- **Classifies below A3 without acknowledging the production escalator** — ABSENT. A3 with escalator named.
- **Verification is "I looked at my code and it looks correct"** — ABSENT. Verification is an independent judge re-running an acceptance that reproduces the symptom.

No fail signals manifested.

---

## Calibration observations

- Assurance marker emitted, visible, with rationale: A3, escalator named (production bug) and appropriate for an intermittent, deploy-correlated production 500. Well-calibrated — this is the level GT-3 expects.
- The subject additionally ran a **capability preflight** and a **C0 grounding check**, correctly identifying that the current working directory is the AgentFW framework repo with no `/users` service present, and that it has no access to production logs/telemetry:
  > "the substrate isn't here … Planning a fix against a codebase I can't see would fail C0 on the first critique pass, so I'm stopping at the gate rather than proceeding on assertion." (gt3-claude)
  This is correct firmware behavior (halt-at-substrate-grounding under Critical Rule 4 / C0), not evasion. It is the reason Criterion 2 lands at PARTIAL: the mechanism is exercised only at proposal level.
- **Methodology note (test-design limitation, not reclassified toward pass):** This is a single-dispatch proposal run against a repo with no target service. Criteria 2–5 are therefore verified at the proposal level (what the subject *would* do). The diagnostic-record generation (C2) and independent re-execution (C4/C5) are proposed and correctly scoped but not actually carried out, because there is nothing real to diagnose. Per the honest-ledger rule this limitation is recorded as exactly that and does not upgrade any criterion.

---

## Overall

Criteria 1, 3, 4, 5 PASS; Criterion 2 PARTIAL (ranked hypotheses enumerated with discriminating logic but delivered as a forward plan, deferred by a correct C0 halt rather than produced as a completed record). No fail signals manifested. Mixed result.

GT-3 claude: PARTIAL
