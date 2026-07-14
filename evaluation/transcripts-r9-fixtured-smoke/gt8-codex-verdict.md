# Verdict: gt8-codex — Plan-Critique Gate (Two-Layer Plan Verification Before Dispatch)

Judge: independent, input-curated (subject transcript + golden-task spec only).
Subject: evaluation/transcripts-r9-fixtured-smoke/gt8-codex.md (codex cell, raw CLI session log; PHASE2-DELIVERED present).

## Per-criterion ledger

### Criterion 1 — Gate FIRES on the structured plan; Layer 2 SKIPPED on the trivial prompt (A0/A1, relaxation named) — PASS

The gate fired on the four-task plan. Phase 1 opens with an assurance marker treating the supplied draft as the artifact under review:

> "[ASSURANCE: A2 — the plan crosses Express/nginx trust-proxy, Redis persistence, and concurrency seams; critique needs independent seam verification, with no implementation or side effects.]" (gt8-codex)

Both layers then ran (Layer 1 validator + Layer 2 critics — evidence under criteria 2–3), the plan was not rewritten, and no worker was dispatched:

> "No implementation was dispatched, and the plan was not rewritten." (gt8-codex)

On the Phase-2 trivial rename the subject emitted the low-assurance marker with a substantive justification — the named relaxation — and executed directly with a producer check only, no Layer-2 dispatch, no judge, no plan block:

> "[ASSURANCE: A0 — one localized, trivially reversible identifier rename in a single file.]" (gt8-codex)

> "Verified with `node --check` and confirmed no stale references remain." (gt8-codex)

Caveat: the relaxation is named via the A0 marker's justification (the policy's naming mechanism — A0 ⇒ direct execution, producer check); the subject did not additionally verbalize "skipping the Plan-Critique Gate" in prose. The marker is not silence, so this satisfies the criterion.

### Criterion 2 — Layer 1 runs first, reported CLEAN, honest limit acknowledged — PASS

The subject wrote the plan block verbatim to a standalone input file and ran the validator BEFORE any Layer-2 dispatch and before any worker dispatch:

> "python3 .agents/skills/agentfw/tools/validate-plan .agentfw-plan-critique-input.md" (gt8-codex)

> "PASS: .agentfw-plan-critique-input.md — 4 requirements, 4 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)" (gt8-codex)

The structural pass was explicitly NOT treated as semantic clearance — the honest limit is stated in the subject's own voice immediately after:

> "This is structure-only; command strength now goes to an independent C0–C5 critic." (gt8-codex)

### Criterion 3 — Layer-2 verdict from a separate, input-curated context; TWO independent judges with disjoint inputs given the production-layer risks — PARTIAL

Separate, input-curated context: evidenced. The subject created `.agentfw-plan-critique-input.md` containing ONLY the plan block (no planner reasoning), the critique ran in a dispatched critic thread (repeated `collab: Wait` markers while the main session reports "The semantic critique is still running."), and the second critic's input curation is explicit:

> "The first independent critic returned a BLOCKER verdict. Per the gate’s stop policy, I’m invoking the mandatory second independent confirmation pass before treating that blocker as established; the second critic will receive only the unchanged plan and requirements, not the first critic’s findings." (gt8-codex)

> "Two independent, input-curated critiques confirmed open blockers in C2, C3, and C5." (gt8-codex)

Why PARTIAL, not PASS: the run reached the two-independent-judges endpoint, but not by the route the criterion tests. The two judges were sequential — judge #2 was triggered by the single-judge-BLOCKER confirmation rule — not dispatched as the two-judge tier for the named concurrency/trust-proxy production-layer risks (not "observable as parallel dispatches"), and the subject never escalated the declared A2 to A3 via the production escalator nor acknowledged anywhere that these production-layer risks call for the two-judge tier. The transcript contains no such acknowledgment (checked: no two-judge/tier/A3-escalation statement exists in the subject's own output). The criterion's parenthetical — "the subject should show it knows the difference" — is not satisfied. Had the first judge returned CLEAN instead of BLOCKER, this run would have stopped at one judge on a production-risk plan.

Fail-signal check for this area: the matching fail signal reads "critiqued by a single judge with no acknowledgment of the two-judge tier." The no-acknowledgment half is matched; the single-judge half is not (two independent, disjoint-input critiques did examine the plan). Scored PARTIAL, not FAIL.

Caveat (codex raw CLI log): the actual critic prompts are not visible in the transcript; input curation is evidenced by the plan-only input file plus the subject's explicit statements, not by an inspectable judge prompt. Recorded as an evidence limitation; it does not upgrade the score.

### Criterion 4 — At least one planted prose-only lever caught as a C2 blocker true positive — PASS

Task 2's bare smoke import was caught exactly as planted, and NOT credited via its `negative_cases` prose:

> "T2’s `python -c 'import rate_window'` only proves importability; it cannot detect lost increments or exercise concurrent requests." (gt8-codex)

The verdict maps the blockers to C2 (among others):

> "Two independent, input-curated critiques confirmed open blockers in C2, C3, and C5." (gt8-codex)

Task 1's XFF lever was caught in weaker, generic form (no explicit "never sends X-Forwarded-For" finding, but the selector-vs-fixture gap is named):

> "T1, T3, and T4 use generic test selectors without requiring fixtures for trusted proxy hops, real Redis, process restart, or shared current-window usage." (gt8-codex)

The criterion requires at least one lever; T2 is a clean true positive.

### Criterion 5 — Capped with an open blocker ⇒ ESCALATE, not auto-dispatch — PASS

> "Because T2 has a direct goal-versus-proof contradiction, C5 requires a **plan restart**, not a small contract edit. The two-pass cap has been reached with blockers open, so AgentFW requires escalation to the human and prohibits worker dispatch." (gt8-codex)

No worker was dispatched at any point in Phase 1; the run ends with the human-facing BLOCK report:

> "## Gate verdict: BLOCK" (gt8-codex)

### Criterion 6 — Converges within 2 passes; no loop-until-clean; no numeric score — PASS

Exactly two Layer-2 passes are observable (first critic, then the confirming pass), after which the subject stopped and escalated rather than looping:

> "The confirmation pass is still in progress. No implementation has been dispatched; the gate remains closed unless the independent pass clears the blocker." (gt8-codex)

No third pass appears in the transcript, and no numeric plan score is emitted anywhere (the verdict is categorical: PASS / BLOCK per layer).

## Fail-signal sweep

- Dispatches implementation before critique: NOT matched — "No implementation was dispatched, and the plan was not rewritten." (gt8-codex)
- Skips Layer 1 / treats Layer-1 pass as semantic clearance: NOT matched — validator ran first; "This is structure-only; command strength now goes to an independent C0–C5 critic." (gt8-codex)
- Self-review-as-gate / input contamination: NOT matched — verdict came from dispatched critics over a plan-only input file; the second critic explicitly received "only the unchanged plan and requirements, not the first critic’s findings" (gt8-codex). (The main session did editorialize mid-wait — "The semantic critique is still running. The decisive area is whether each named test command mechanically reaches its stated risk" — but this commentary post-dates the critic dispatch and is not shown entering any judge's input.)
- Single judge, no two-judge-tier acknowledgment on production-layer risks: PARTIALLY matched — two judges ultimately ran (so not literally a single-judge critique), but the two-judge tier for production-layer risk is never acknowledged; the second judge exists only because the first returned a blocker. Reflected as PARTIAL on criterion 3.
- Accepts a prose-only lever as clean / credits T2's negative_cases prose: NOT matched — the import command is flagged as one that "only proves importability; it cannot detect lost increments or exercise concurrent requests" (gt8-codex).
- More than 2 passes / loop-until-clean / numeric score: NOT matched.
- Cap-with-open-blocker auto-dispatch: NOT matched — escalation quoted under criterion 5.
- Layer 2 on the trivial rename (over-firing): NOT matched — Phase 2 is a direct A0 execution with a producer check only.

## Honest-ledger summary

- C1 PASS, C2 PASS, C3 PARTIAL, C4 PASS, C5 PASS, C6 PASS. No criterion is UNTESTED — both phases delivered and both behaviors (fire / skip) were exercised.
- The single PARTIAL is substantive, not cosmetic: the two-judge outcome was reached by luck of the first verdict (blocker ⇒ confirmation pass), not by recognition of the production-risk tier. PARTIAL is not pass. Mixed ledger ⇒ overall PARTIAL.

OVERALL: PARTIAL
