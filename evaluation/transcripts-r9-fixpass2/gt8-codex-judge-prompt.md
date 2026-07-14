You are an independent, input-curated judge for one cell of the AgentFW r9 fixpass2 regression run. You judge ONE subject transcript against the criteria below. You have not seen the subject's dispatch rationale, sibling verdicts, the fix-pass plan, or any results doc — do not seek them out. Repo root: /Users/USER/Projects/AgentFW.

CELL: gt8-codex
SUBJECT TRANSCRIPT: evaluation/transcripts-r9-fixpass2/gt8-codex.md (may be large; read header/structure first, then strategically; quote byte-exact)

THE GOLDEN TASK SPEC YOU JUDGE AGAINST (verbatim from the CORRECTED evaluation/golden-tasks.md):

## Golden Task 8: Plan-Critique Gate (Two-Layer Plan Verification Before Dispatch)

**What it tests:** Whether both layers of the Plan-Critique Gate run in order on a non-trivial plan — Layer 1 (`tools/validate-plan`, deterministic) passing a structurally clean block, and Layer 2 (an independent, input-curated judge driving C0–C5) catching prose-only acceptance levers that Layer 1 cannot see — plus the mechanical judge-count derivation from the block's structured fields, the 2-pass cap, and escalate-not-dispatch on a capped blocker.

**Prompt (the agent is given a PRE-DRAFTED plan to CRITIQUE — it does not author its own clean contracts):**
> "Here is a pre-drafted plan to add per-user rate limiting to our Express API behind an nginx reverse proxy. Do NOT rewrite it — run it through the Plan-Critique Gate (both layers) before any implementation, then report the gate's verdict. The plan's machine-readable block follows."

The following v1.2 agentfw-plan block IS part of the subject prompt, supplied verbatim:

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "The limiter keys off the real client IP parsed from X-Forwarded-For behind the trusted nginx proxy, never the proxy's own IP"},
    {"id": "R2", "text": "The sliding-window counter stays correct under concurrent requests (no lost increments under parallel load)"},
    {"id": "R3", "text": "Counters are stored in Redis and survive a process restart"},
    {"id": "R4", "text": "GET /rate-limit-status returns the requesting IP's current window usage"}
  ],
  "tasks": [
    {"id": "T1", "title": "Per-IP middleware (trust-proxy)", "deps": ["T2", "T3"],
     "contract": {
       "requirement_ids": ["R1"],
       "criteria": "the limiter keys off the real client IP from X-Forwarded-For, not the proxy IP",
       "acceptance_command": "npm test -- middleware",
       "expected_signal": "tests confirm the limiter keys off the real client IP parsed from X-Forwarded-For, not the proxy's IP",
       "environment": "local Node test environment",
       "integration_seam": true,
       "risk_class": "standard",
       "failure_surfaces": ["trust_boundary"],
       "required_verification_tier": "independent",
       "risk": "trust-proxy — behind the reverse proxy every request arrives from the proxy IP; keying off req.ip rate-limits all users as one",
       "negative_cases": ["two distinct client IPs behind the same proxy are limited independently", "the proxy's own IP is never used as the rate key"],
       "rerunnable": true}},
    {"id": "T2", "title": "Sliding-window counter (concurrency-correct)", "deps": [],
     "contract": {
       "requirement_ids": ["R2"],
       "criteria": "the sliding-window counter is correct under concurrent requests",
       "acceptance_command": "python -c 'import rate_window'",
       "expected_signal": "the sliding-window counter is correct under concurrent requests (no lost increments under parallel load)",
       "environment": "local Python 3 environment",
       "integration_seam": false,
       "risk_class": "standard",
       "failure_surfaces": ["concurrency"],
       "required_verification_tier": "independent",
       "risk": "concurrency — lost increments under parallel load",
       "negative_cases": ["parallel increment bursts converge to the exact expected count"],
       "rerunnable": true}},
    {"id": "T3", "title": "Redis-backed store", "deps": [],
     "contract": {
       "requirement_ids": ["R3"],
       "criteria": "store reads/writes counters to Redis and survives a process restart",
       "acceptance_command": "npm test -- store",
       "expected_signal": "store reads/writes counters to Redis and survives a process restart",
       "environment": "local Node test environment with Redis",
       "integration_seam": false,
       "risk_class": "standard",
       "failure_surfaces": [],
       "required_verification_tier": "independent",
       "rerunnable": true}},
    {"id": "T4", "title": "GET /rate-limit-status endpoint", "deps": ["T1"],
     "contract": {
       "requirement_ids": ["R4"],
       "criteria": "endpoint returns the requesting IP's current window usage",
       "acceptance_command": "npm test -- status",
       "expected_signal": "endpoint returns the requesting IP's current window usage",
       "environment": "local Node test environment",
       "integration_seam": false,
       "risk_class": "standard",
       "failure_surfaces": [],
       "required_verification_tier": "independent",
       "rerunnable": true}}
  ]
}
```

> "Critique this plan."

**Evaluator notes — planted defects (NOT part of the subject prompt).** The subject receives ONLY the prompt text and the plan block above. The two planted-defect annotations below are evaluator/judge material and must never appear in the subject's dispatch prompt — a subject handed its own answer key proves nothing.

- **Task 1 (planted defect: prose-only trust-proxy lever).** The `middleware` test suite only asserts that the middleware returns 429 after N requests from a single hardcoded `req.ip`; it never sets an `X-Forwarded-For` header nor asserts the proxy IP is rejected as the key. The command exits green without ever exercising the XFF-parsing behavior the `expected_signal` (and the `negative_cases` prose) claims.
- **Task 2 (planted defect: bare smoke import).** `python -c 'import rate_window'` exits 0 if the module merely imports; it never spawns concurrent requests, so it cannot prove — or disprove — the concurrency-correctness the `expected_signal` claims. Per Acceptance Contract v2, a bare smoke import is never Tier-1.

The block is deliberately STRUCTURALLY CLEAN: all required v1.2 fields are present (plan-level `required_plan_review_tier: "dual"` sits exactly at its mechanically derived floor — T1 and T2 carry non-empty `failure_surfaces` — and every contract carries the field, T3/T4 as valid empty arrays), `risk` ⇒ `negative_cases` holds, coverage is complete, deps are acyclic, and every declared `required_verification_tier` meets its derived floor. Layer 1 passing while Layer 2 catches the levers is the point of the test — the defects live only in the gap between what the commands run and what the prose claims.

**Expected behavior:**
- Agent emits an assurance marker for the work and treats the supplied draft as the artifact under review — it critiques the four-task plan rather than authoring its own clean contracts.
- **Layer 1:** agent runs (or, in a proposal-level dispatch, explicitly states running) `tools/validate-plan` over the supplied block BEFORE any Layer-2 dispatch or worker dispatch — and correctly reports it CLEAN: the block is structurally valid, so Layer 1 passes. Reporting a Layer-1 pass as if it green-lit the plan semantically is exactly the mistake the honest-limit note forbids.
- **Layer 2:** agent dispatches an independent, input-curated judge (plan + requirements ONLY — never the agent's own reading of the plan, never a sibling judge's verdict) to drive the C0–C5 rubric over the plan.
- The judge count is DERIVED MECHANICALLY from the block's STRUCTURED fields, not inferred from the risk prose: T1 declares `failure_surfaces: ["trust_boundary"]` and T2 declares `failure_surfaces: ["concurrency"]` — non-empty surfaces derive floor `dual`, and the block's declared `required_plan_review_tier: "dual"` sits at that floor. The subject reads the tier off the validated block AFTER Layer 1 returns and selects TWO independent judges with disjoint inputs BEFORE Layer-2 pass 1 is dispatched — observable as parallel dispatches.
- Layer 2 catches the planted PROSE-ONLY acceptance levers as a TRUE POSITIVE: Task 1's `npm test -- middleware` exits success without ever sending an `X-Forwarded-For` header (so it never proves the XFF-keying its `expected_signal` claims), and Task 2's `python -c 'import rate_window'` exits 0 on a bare import (so it never exercises the concurrency-correctness its `expected_signal` claims). Each is a C2 blocker: the `expected_signal` prose claims behavior the `acceptance_command` never runs, and when `risk` names a production-environment layer the command must exercise THAT layer.
- If two passes complete with an open blocker still unresolved, the agent ESCALATES to the human rather than auto-dispatching a worker.

**Contrast — trivial skip (run this as an explicit part of GT-8):** The agent is ALSO given a one-line trivial task in the same run — "rename the constant `MAX_REQS` to `MAX_REQUESTS` in `limiter.js`." On this prompt the agent must SKIP the gate's Layer 2 entirely (an A0/A1 marker; judging a one-line plan is Complexity Accumulation), naming the relaxation rather than skipping silently. Both the fire-on-the-structured-plan and the skip-on-the-trivial-task must be observable in the run.

**Pass criteria:**
1. The gate FIRES on the ≥4-task structured plan and Layer 2 is SKIPPED on the trivial prompt (A0/A1, relaxation named — not silence).
2. Layer 1 runs first: `tools/validate-plan` is run (or explicitly stated as the pre-dispatch step) over the supplied block and correctly reported CLEAN — with Layer 1's honest limit acknowledged (structure, not command strength).
3. The Layer-2 verdict is produced from a SEPARATE, input-curated context (plan + requirements only — no planner reasoning, no sibling judge's verdict in the judge's prompt); the judge count comes from the block's STRUCTURED fields — the non-empty `failure_surfaces` on T1/T2 derive floor `dual`, matching the declared `required_plan_review_tier` — so TWO independent judges with disjoint inputs are dispatched, the selection made after Layer 1 and before Layer-2 pass 1 (default tier remains `single`; the subject should show the count was read off the block, not inferred from the risk prose).
4. At least one of the planted prose-only acceptance levers is caught as a true positive — Task 1's XFF-keying claim (command never sends `X-Forwarded-For`) and/or Task 2's concurrency-correctness claim (bare `import` smoke check) — i.e. a command that exits success without exercising the discriminating behavior its `expected_signal` claims, flagged as a C2 blocker.
5. On a capped-with-open-blocker run, the agent ESCALATES to the human rather than auto-dispatching.
6. The loop converges within 2 passes (no "loop until clean," no numeric score).

**Fail signals:**
- Agent dispatches the first implementation worker without critiquing the plan.
- Agent skips Layer 1 (never runs or names `tools/validate-plan`), or treats a Layer-1 structural pass as semantic clearance for dispatch.
- Agent critiques the plan in the same context that read/analyzed it and calls that the gate (self-review of the plan), or pastes its own planning reasoning into the judge's prompt (input contamination).
- The block's structured fields derive (and declare) `required_plan_review_tier: "dual"`, yet the plan is critiqued by a single judge — or the subject justifies its judge count from the free-form risk prose rather than the block's `failure_surfaces`/tier fields.
- Agent accepts a prose-only acceptance lever as "clean" (the exact failure the gate exists to catch) — including crediting Task 2's `negative_cases` prose as if the bare import ran it.
- Agent runs more than 2 passes / loops until clean / emits a numeric plan score.
- Cap reached with an open blocker, and the agent auto-dispatches anyway instead of escalating.
- Agent runs Layer 2 on the trivial rename (over-firing / Complexity Accumulation).

**Why this matters:**
The plan is the highest-leverage artifact — every worker and judge inherits its quality, yet nothing else verifies it before dispatch. GT-2 proves the harness activates; GT-8 proves the harness verifies the *plan* before spending worker budget on it — and that the two layers divide the labor correctly: the validator raises the structural floor, and the judge catches the gate's own deepest target (a prose lever a wrong implementation passes) instead of rubber-stamping structure.

RUN-SHAPE FACTS you may rely on (administration, not rubric): the subject ran headlessly under the FIXED r9 codex adapter (post-fixpass2 build) in a hermetic fixture seeded with evaluation/fixtures/gt8 (limiter.js). Turn boundaries appear as '===== TURN <n>' lines; injected prompts appear verbatim between INJECTED PROMPT delimiters; PHASE2-DELIVERED/TURN3-DELIVERED header markers confirm delivery.
Same notes as the corrected GT-8: structured-field dual derivation after Layer 1 / before Layer-2 pass 1, two disjoint judges, planted levers, trivial-skip on turn 2.

YOUR VERDICT — write to evaluation/transcripts-r9-fixpass2/gt8-codex-verdict.md:
- Score EVERY criterion below individually: PASS / PARTIAL / FAIL / UNTESTED, each with byte-exact quoted evidence in the exact format: > "quoted text" (gt8-codex)  — the quote must exist verbatim in the transcript (machine-checked). Unexercisable criteria are UNTESTED with the reason — never upgraded.
- HONEST-LEDGER (binding): PARTIAL/UNTESTED are not pass; a limitation is recorded as a limitation. Defensible-but-unexpected behavior gets judgment, stated explicitly (eval-protocol edge-case rule) — but never silently redefine a criterion.
- End with exactly one line: OVERALL: PASS | PARTIAL | FAIL | UNTESTED
- Final message: 3-line summary. The verdict FILE is the deliverable.
