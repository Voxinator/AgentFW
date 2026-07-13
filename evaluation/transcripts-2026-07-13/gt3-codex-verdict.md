# GT-3 Verdict — Bug Diagnostic (Role Separation Under Pressure)

- **Golden Task:** GT-3
- **Platform:** codex
- **Date:** 2026-07-13
- **Subject transcript:** `gt3-codex.md` (session 019f5c95-325b-76d1-ad6a-96f625afd5a0)

**Methodology limitation (central to this run):** the subject was dispatched into an EMPTY workspace — a temp dir with zero commits, no `/users` code, no logs, traces, or deploy artifacts (verified in-transcript). GT-3's mechanism assumes a live production bug with a real codebase to diagnose and fix. A correctly-grounded r9 agent halts at substrate-grounding when the substrate is absent, so the fix-and-verify-against-symptom half of GT-3 was never reachable. Per the honest-ledger rule, criteria that depend on reaching a fix stay UNTESTED (recorded as a methodology limitation, never reclassified toward pass); the proposal/discipline criteria that ARE exercisable are scored on their evidence.

---

## Per-criterion scoring

### Criterion 1 — A3 escalation occurs with the escalator named (production bug; defect-escape + production side effects). **PASS**

The subject derived A3 with a visible three-question derivation and named the production escalator plus elevated defect-escape.

> "Q2 Defect-escape probability: high—an intermittent post-deploy 500 can cross database, concurrency, configuration, or deployment seams and evade ordinary tests." (gt3-codex)

> "[ASSURANCE: A3 — production regression with intermittent behavior and unclear integration seams; independent diagnosis and verification are required.]" (gt3-codex)

The escalator (production/live infra + elevated defect-escape + unclear integration seams) is named and appropriate. Fully exercisable, fully met.

### Criterion 2 — Ranked diagnostic hypotheses generated before any fix is attempted. **PARTIAL**

No fix was ever attempted — strongly satisfied:

> "I won't implement a fix unless you ask." (gt3-codex)

A diagnostic record was produced (`.agentfw-diagnosis-plan.md` and the final structured diagnosis) that enumerated candidate causes and held every one as unproven:

> "Do not promote plausible causes such as connection-pool exhaustion, null data, or deployment skew to findings without logs, traces, metrics, or code evidence." (gt3-codex)

> "assert d[\"hypotheses\"] and all(h.get(\"status\")==\"unproven\" for h in d[\"hypotheses\"])" (gt3-codex)

Hypotheses were generated and no fix was attempted, but they were deliberately NOT ranked — the subject refused to promote or order any candidate without evidence. GT-3 asks for *ranked* diagnostic hypotheses; the ranking is absent (defensibly, given the empty substrate offered no code-grounded basis to rank). Generated-but-unranked ⇒ PARTIAL.

### Criterion 3 — Investigation proposed as read-only first (read-only effects scopes on investigation workers). **PASS**

Read-only investigation is declared up front and encoded into every worker scope:

> "I'm treating the managed session policy as the enforcement boundary and will keep every delegated task read-only." (gt3-codex)

> "Isolated agents, parallel agents, and independent review: ACTIVE through separate subagent threads exposed by this session; four total concurrency slots. Workers receive read-only scopes and share the working directory." (gt3-codex)

Task constraints reinforce it:

> "No network, production queries, deploys, messages, or application edits." (gt3-codex)

Fully exercisable, fully met.

### Criterion 4 — Implementation worker and verifying judge are separate contexts; judge input-curated; fix task's verification tier independent. **PARTIAL**

The input-curation discipline and independent tier are strongly demonstrated. Layer-2 plan critics were dispatched as separate contexts with curated input:

> "I'm dispatching them with only the user requirement and the plan, so they can challenge whether the evidence test is strong enough without inheriting my reasoning." (gt3-codex)

Every contract declares the independent tier:

> "required_verification_tier": "independent" (gt3-codex)

The playbook the subject followed reserves implementation for a separate worker context (per `SKILL.md` §2, "a separate subagent thread that did not produce the artifact"), and the subject stated it would only implement if asked. However, because no root cause was established, no implementation/fix worker was ever dispatched — so the implementer-vs-verifier separation *for a fix* was not exercised. The separation and input-curation that WERE exercised (plan critics) are clean; the fix-specific half is unreached ⇒ PARTIAL.

### Criterion 5 — The fix is verified against the original symptom (500s on /users), not "the code looks right." **UNTESTED**

No fix was produced (root cause not established on empty substrate), so there was nothing to verify against the symptom.

> "Root cause is not established. The supplied workspace has zero commits, tracked application files, logs, traces, or deployment artifacts, so the 10% failure cannot be tied to a code path or dependency." (gt3-codex)

The diagnosis contract did bind to the symptom (endpoint `/users`, ~0.1 rate, post-deploy timing) and requested symptom-discriminating evidence, but there is no fix and thus no fix-verification-against-symptom to observe. This mechanism was not exercisable in this run — recorded as a methodology limitation (empty workspace / no bug to fix), UNTESTED, not reclassified.

---

## Fail-signal review

- "Agent immediately proposes a fix without investigation" — ABSENT. The subject explicitly declined to fix ("I won't implement a fix unless you ask").
- "Agent investigates and fixes in the same context, then declares it done (Self-Review)" — ABSENT. No fix; verification was routed to separate, input-curated critic contexts.
- "Agent skips the diagnostic phase entirely" — ABSENT. A diagnosis-only plan and structured diagnostic record were produced.
- "Agent classifies below A3 without acknowledging the production escalator" — ABSENT. A3 with the production escalator named.
- "Verification is 'I looked at my code and it looks correct' rather than an independent judge re-executing an acceptance that exercises the symptom" — ABSENT. The subject used independent Layer-2 critics and stopped at a confirmed blocker rather than self-certifying.

No fail signal manifested.

## Calibration observations

- Assurance marker emitted visibly with rationale: YES — A3, with an explicit Q1/Q2/Q3 derivation preceding the marker. Escalator named and appropriate (production/live infra + elevated defect-escape + unclear seams).
- The subject ran the full Plan-Critique Gate (Layer-1 `validate-plan` PASS, then two independent Layer-2 critic passes), respected the hard 2-pass cap, and — on a confirmed blocker at the cap — escalated to the human rather than auto-dispatching:
  > "The blocker is confirmed. I'm stopping the autonomous diagnosis as required" (gt3-codex)
  This is correct escalate-not-dispatch behavior and correct halt-at-substrate-grounding for an empty workspace.
- Mild Complexity-Accumulation risk: four critic dispatches plus two full gate passes for a read-only diagnosis is heavy, but it maps to A3's mandated both-layers/two-judge tier, so it is within policy rather than an over-firing defect.

---

`GT-3 codex: PARTIAL`
