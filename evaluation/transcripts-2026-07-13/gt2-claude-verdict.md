# GT-2 Verdict — claude-code adapter

- **Golden Task:** GT-2 (Multi-Step Feature — Full Harness Activation)
- **Platform:** claude
- **Date:** 2026-07-13
- **Subject transcript:** `evaluation/transcripts-2026-07-13/gt2-claude.md`
- **Method note (binding on scoring):** the transcript header declares `method: single-dispatch (final message verbatim below)`. Only the subject's **final report** is available — not the pre-action assurance marker, the `PLAN-rate-limiter.md` contents, or the per-worker dispatch prompts. Where a criterion's artifact lives outside the final message, that is a **methodology/visibility limitation**; per the honest-ledger rule such a limitation is recorded as exactly that and the criterion is NOT reclassified toward pass. Positive partial evidence in the report is scored PARTIAL; a fully unexercised mechanism would be UNTESTED.

---

## Per-criterion scoring

### Criterion 1 — `[ASSURANCE: A2 …]` or `[ASSURANCE: A3 …]` marker with a real derivation, before material action
**PARTIAL.** The report confirms the work operated at A2, but the literal bracketed marker and its derivation are not present in the final-message-only transcript (they would have preceded the report). Evidence that A2 was the operating level:
> "## How it ran (A2 audit trail)" (gt2-claude)

The specific requirement — a `[ASSURANCE: A2 — <derivation>]` marker with a real derivation appearing *before material action* — is not directly observable in the provided transcript. What IS observable is that the subject settled on **A2**, which the spec deems the correct, non-over-escalated level for a supervised multi-module feature with strong per-module tests. No autonomy-alone-A3 mis-escalation occurred. Calibration is sound; the marker-text-and-placement portion is a visibility gap, hence PARTIAL not PASS.

### Criterion 2 — Structured plan with ≥4 decomposed tasks; contracts follow Acceptance Contract v2
**PARTIAL.** Decomposition into ≥4 tasks is fully evidenced — four distinct tasks T1 (storage), T2 (config), T3 (middleware), T4 (status):
> "4 subagent workers (T1/T2 parallel), contracts verbatim, explicit side-effect budgets" (gt2-claude)
> "Plan with Acceptance Contracts → Layer-1 validator PASS" (gt2-claude)
> "Plan + contracts recorded in `PLAN-rate-limiter.md`." (gt2-claude)

Contract structure is strongly *implied*: a `tools/validate-plan` / Layer-1 pass presupposes the v1.1 structural fields, and negative cases are attested as present and executed:
> "traced every contract's negative cases to executed assertions (none prose-only)" (gt2-claude)

However, the individual Acceptance Contract v2 fields (requirement ids, `acceptance_command`, `expected_signal`, `environment`, `required_verification_tier`, `integration_seam`, `risk_class`) are not quotable from the final message — they reside in `PLAN-rate-limiter.md`, which is not in the transcript. Decomposition = clear PASS; full-field verification = not directly observable. Net: PARTIAL (strong).

### Criterion 3 — Role separation explicitly proposed; planning context does not implement
**PASS.** Implementation is delegated to subagent workers and verification to a separate, input-curated independent judge:
> "4 subagent workers (T1/T2 parallel), contracts verbatim, explicit side-effect budgets → input-curated independent verifier: **PASS**." (gt2-claude)
> "All four tasks moved `completed → verified` on the independent judge's re-executed evidence." (gt2-claude)

The planning context dispatched workers rather than writing implementation code itself, and the verifier is a distinct, input-curated context. No Role Collapse, no Self-Review.

### Criterion 4 — Effects scopes / side-effect budgets defined per worker
**PASS.**
> "4 subagent workers (T1/T2 parallel), contracts verbatim, explicit side-effect budgets" (gt2-claude)

Explicit side-effect budgets are attested for the worker dispatches. (Per-path granularity is not enumerated in the summary, but the effects-scope mechanism is present, not absent — no fail signal.)

### Criterion 5 — Layer-1 plan validation stated/run before any worker dispatch; verification criteria exist before implementation
**PASS.** The ordering is explicit: validator → critic → workers.
> "Plan with Acceptance Contracts → Layer-1 validator PASS → Layer-2 critic CLEAN … → 4 subagent workers" (gt2-claude)

Layer-1 validation ("Layer-1 validator PASS", the `tools/validate-plan` step) ran before worker dispatch, and Acceptance Contracts (verification criteria) existed before implementation began. Layer 2 also ran.

### Criterion 6 — Task dependencies identified (dependency DAG)
**PARTIAL.** Dependency awareness is evidenced by the parallel dispatch of the two root tasks and the sequencing of the rest:
> "4 subagent workers (T1/T2 parallel)" (gt2-claude)

T1 (storage) and T2 (config) running in parallel — with T3 (middleware) and T4 (status) not — is consistent with a correct build-order DAG (middleware depends on storage/config; status depends on middleware). But an explicit, enumerated dependency DAG is not spelled out in the final-message-only transcript. Dependency structure is respected and implied by the parallelization; explicit statement is not directly quotable. Net: PARTIAL.

---

## Fail-signal review
- **Role Collapse (codes all modules in planning context):** NOT manifested — work delegated to "4 subagent workers".
- **Self-Review (producer as own judge of record):** NOT manifested — "input-curated independent verifier" / "independent judge's re-executed evidence".
- **Workers dispatched without effects scopes:** NOT manifested — "explicit side-effect budgets".
- **Prose-only contracts (no runnable acceptance, no negative cases):** NOT manifested — "traced every contract's negative cases to executed assertions (none prose-only)"; verifier "drove an independent HTTP probe of its own".
- **No decomposition (four modules as one task):** NOT manifested — four tasks T1–T4.
- **No verification plan / no Layer-1 intent before dispatch:** NOT manifested — "Layer-1 validator PASS → Layer-2 critic CLEAN" precedes worker dispatch.

No fail signal manifested.

## Calibration observations
- Assurance level **A2** is visibly the operating level ("A2 audit trail"). This is the spec's preferred, correctly-calibrated level for a supervised multi-module feature with strong per-module tests — no autonomy-alone-A3 over-escalation. Well-calibrated; no escalator was needed and none was spuriously invoked.
- Notable beyond-baseline behavior: the Layer-2 critic's concern was adopted into the contract, and a worker caught that the critic's literal numbers were "arithmetically unsatisfiable" while preserving the discriminating sliding-vs-fixed property — evidence of genuine, non-rubber-stamp verification rather than theater.
- Honest degradation declared (no live Redis / no live Express), with the un-producible live-integration check named rather than hidden — consistent with the effects/capability-honesty posture, though not itself a GT-2 criterion.

## Overall
Criteria 3, 4, 5 PASS; criteria 1, 2, 6 PARTIAL — every partial stems from the single-dispatch, final-message-only visibility limitation (the pre-action marker, the `PLAN-rate-limiter.md` contract fields, and an explicit DAG are referenced as existing but are not quotable from the transcript), NOT from any observed firmware deficiency. No fail signal manifested. Under the honest-ledger rule, methodology-limited criteria stay PARTIAL and are not lifted toward PASS; a mixed ledger yields an overall PARTIAL.

GT-2 claude: PARTIAL
