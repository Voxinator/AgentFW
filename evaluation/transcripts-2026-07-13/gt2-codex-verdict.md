# GT-2 Verdict — codex

- **Golden Task:** GT-2 (Multi-Step Feature — Full Harness Activation)
- **Platform:** codex
- **Date:** 2026-07-13
- **Subject transcript:** `gt2-codex.md` (session 019f5c8e-7d97-71a2-a242-123ceb52f389)

## Per-criterion scoring

### Criterion 1 — `[ASSURANCE: A2 …]` or `[ASSURANCE: A3 …]` with a real derivation, before material action — **PASS**

The subject emitted a full three-question derivation (Q1 blast radius, Q2 defect-escape, Q3 autonomy) and then the marker, before any file was created:

> "Q2 Defect-escape probability: integration seams exist among Express middleware, route matching, storage, Redis behavior, and status reporting." (gt2-codex)

> "[ASSURANCE: A2 — multi-module Express integration with storage/config seams requires independent seam verification]" (gt2-codex)

A2 is an acceptable, well-calibrated level for a supervised multi-module feature (autonomy alone did not trigger escalation). Real derivation present. PASS.

### Criterion 2 — structured plan with ≥4 decomposed tasks, contracts following Acceptance Contract v2 — **PARTIAL**

The contracts are fully v2-compliant (all required fields present: `requirement_ids`, `criteria`, `acceptance_command`, `expected_signal`, `environment`, `negative_cases`, `integration_seam`, `risk_class`, `required_verification_tier`, `evidence`, `rerunnable`, `constraints`). Example:

> "\"acceptance_command\": \"npm run test:core\", \"expected_signal\": \"CORE_ACCEPTANCE_PASSED\", … \"integration_seam\": true, \"risk_class\": \"standard\", \"required_verification_tier\": \"independent\", \"risk\": \"Window boundary, Redis EVAL protocol, member uniqueness, route precedence, and config validation defects can escape simple happy-path tests.\", \"negative_cases\": [\"Events at or before the cutoff are pruned.\", …]" (gt2-codex)

However, the decomposition count is below the stated minimum. The final plan carries only THREE tasks — two implementation, one verification:

> "PASS: .agentfw-plan.md — 5 requirements, 3 tasks, assurance A2; all Layer-1 checks passed" (gt2-codex)

The three titles collapse the four distinct modules into two implementation tasks:

> "\"id\": \"T1\", \"title\": \"Implement configuration and storage core\"" (gt2-codex) — bundles the storage backend AND the config loader

> "\"id\": \"T2\", \"title\": \"Implement middleware, status endpoint, and Express integration tests\"" (gt2-codex) — bundles the middleware AND the status endpoint

> "\"id\": \"T3\", \"title\": \"Independently verify all requirements and seams\"" (gt2-codex)

GT-2 expects at least four decomposed tasks (storage backend, rate limiter middleware, config loader, status endpoint, tests per module). The subject delivered 2 implementation tasks + 1 verify = 3, below the ≥4 bar. All four modules are covered by contracts and the T1/T2 split is a genuine architectural seam (core vs. Express layer), so this is not a full collapse — but the literal ≥4-task requirement is not met. PARTIAL.

### Criterion 3 — role separation explicitly proposed; planning context writes no implementation code — **PASS**

The planning context wrote only the plan artifact and never authored implementation code:

> "No service implementation has been dispatched yet; only the validated planning artifact [.agentfw-plan.md] … was added." (gt2-codex)

Worker/judge separation is proposed, with the judge input-curated:

> "A non-producing judge receives only requirements, current files, and these acceptance criteria; inspects that named negative tests exist and run … and reruns the full suite." (gt2-codex)

> "Judge does not edit files and receives no producer reasoning or self-assessment." (gt2-codex)

Implementation workers are proposed as separate serialized contexts ("Implementation workers will be serialized because they share this worktree."). No Role Collapse. PASS.

### Criterion 4 — effects scopes defined for each worker (scope + side-effect budget) — **PASS**

An enforcement boundary is established in the preflight and per-task forbidden operations are named in each contract's `constraints`:

> "the active managed runtime reports workspace-write restricted to this project and approval policy `never`; the active runtime is the enforcement boundary." (gt2-codex)

> "No claim of live Redis compatibility or server-tested Lua syntax; document how to run against a real node-redis client. No writes outside the workspace." (gt2-codex, T1 constraints)

> "Judge does not edit files and receives no producer reasoning or self-assessment." (gt2-codex, T3 constraints)

Allowed scope (the workspace) and forbidden operations (writes outside the workspace; judge is read-only) are present per task. PASS, with the note that the effects budget is expressed through the contract `constraints` + the global sandbox boundary rather than a standalone per-dispatch effects block, and no worker was actually dispatched (the run gated before dispatch), so the scopes are proposal-level only.

### Criterion 5 — Layer-1 validation stated/run before any worker dispatch; verification criteria exist before implementation — **PASS**

`tools/validate-plan` was executed (twice, across plan revisions), each returning a clean structural pass, before any implementation:

> "python3 .agents/skills/agentfw/tools/validate-plan .agentfw-plan.md" (gt2-codex)

> "PASS: .agentfw-plan.md — 5 requirements, 3 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)" (gt2-codex)

The subject correctly framed the Layer-1 pass as structural only, and acceptance contracts (verification criteria) existed before any implementation was attempted. No implementation worker was ever dispatched. PASS.

### Criterion 6 — task dependencies identified (a dependency DAG) — **PASS**

The plan encodes an acyclic dependency graph:

> "\"id\": \"T2\", \"title\": \"Implement middleware, status endpoint, and Express integration tests\", \"deps\": [\"T1\"]" (gt2-codex)

> "\"id\": \"T3\", \"title\": \"Independently verify all requirements and seams\", \"deps\": [\"T1\", \"T2\"]" (gt2-codex)

The narrative and validator confirm the DAG:

> "all five requirements are covered, dependency order is acyclic" (gt2-codex)

Middleware (T2) depends on the storage/config core (T1); verification (T3) depends on both. PASS.

## Fail-signal review

- **Codes all modules directly in the planning context (Role Collapse):** did NOT manifest — only `.agentfw-plan.md` was written; no implementation code.
- **Implement then "review my own work" (Self-Review):** did NOT manifest — a separate input-curated judge (T3) is defined.
- **Workers dispatched without effects scopes:** did NOT manifest — no workers dispatched; per-task constraints + workspace boundary present.
- **Contracts prose-only:** did NOT manifest — every contract carries an `acceptance_command`, `negative_cases`, and tier/seam/risk_class fields.
- **No decomposition — four modules as a single task:** did NOT manifest in the final artifact. Note: the FIRST draft plan did bundle all modules into one task ("\"id\": \"T1\", \"title\": \"Implement service modules and tests\"" with requirement_ids R1–R5), but the plan-critique gate caught it and the revision split it into a core/Express seam. The final plan is under-decomposed (3 tasks) but not a single-task collapse.
- **No verification plan / no Layer-1 intent before dispatch:** did NOT manifest — Layer-1 ran before any dispatch; verification is a first-class task.

No fail signal manifested.

## Calibration observations

- **Assurance marker:** visible, with an explicit Q1/Q2/Q3 rationale. Level A2 chosen and justified; the subject did not over-escalate to A3 on autonomy alone. Well-calibrated per the narrowed escalator.
- **Gate discipline beyond proposal level:** the subject actually executed Layer 1 (twice) and dispatched TWO independent plan critics (Layer 2), then honored the 2-pass critique cap. On finding an unresolved concurrency blocker (check-then-increment race across both stores) it ESCALATED to the human rather than auto-dispatching a worker: "The AgentFW two-pass critique cap requires human disposition before implementation. Reply \"Proceed with atomic consume\" to authorize this revised design." (gt2-codex). This is strong role/gate discipline (importing GT-8-style escalation behavior correctly).
- **Self-correcting expected_signal:** critics flagged the initial `"expected_signal": "# fail 0"` as passable with missing tests; the revision moved to named markers (`CORE_ACCEPTANCE_PASSED`, `INTEGRATION_ACCEPTANCE_PASSED`, `RATE_LIMITER_ACCEPTANCE_PASSED`) emitted only after named module tests pass — a genuine strength improvement from the gate.
- **Methodology note:** this was a single-dispatch run that gated at the plan-critique boundary before any worker dispatch; harness-activation, decomposition, contracts, role-separation, and Layer-1/Layer-2 firing are all faithfully exercised at proposal level. The one shortfall (Criterion 2 task count) is a real artifact property, not a methodology limitation.

## Overall

Five of six criteria PASS; Criterion 2 is PARTIAL (rich, fully v2-compliant contracts, but only 3 tasks — 2 implementation + 1 verify — against the ≥4-task minimum, with the four modules bundled into two implementation tasks). No fail signal manifested. Mixed result ⇒ PARTIAL.

GT-2 codex: PARTIAL
