# Plan-Critique Gate — two layers

**WHY:** the plan is the highest-leverage artifact — every worker and judge inherits its quality, yet
nothing verifies it before dispatch. A runtime will happily dispatch an unjudged plan; this policy will
not. The gate splits into a deterministic layer (cheap, mechanical, always runnable) and a semantic
layer (a judge, engaged proportionally).

**WHEN:** Layer 1 runs on every plan that carries a machine-readable block — it costs one command.
Layer 2 fires for **A2+ plans, destructive plans, architectural ambiguity, or shared derived values**
(two tasks depending on the same computed fact). A0/A1 trivial plans SKIP Layer 2 — judging a one-line
plan is Complexity Accumulation; skipping requires naming the relaxation, silence is not one.

**WHAT:** Layer 1 = `tools/validate-plan` over the plan's embedded block; Layer 2 = an independent
judge context driving the C0–C5 rubric over the plan.

## Layer 1 — deterministic validation (`tools/validate-plan`)

The plan embeds exactly one fenced block opening with ```` ```json agentfw-plan ```` and closing with
```` ``` ````. The validator (stdlib-only, exit-code honest) mechanically checks:

1. The block parses as valid JSON with no duplicate object keys at any level (last-wins duplicate
   keys are rejected as silently-accepted ambiguity), and `version` is present and — in default
   mode — `"1.1"`, `"1.2"`, `"1.3"`, or `"1.4"`: **schema 1.4 is the schema of record** (author
   new plans against it; 1.1, 1.2, and 1.3 remain valid for plans that predate it). A `"version": "1"`
   block is rejected as a legacy schema version; unknown version strings are rejected naming the
   version. The `--legacy` flag accepts `"version": "1"` blocks under the ORIGINAL v1 rules
   (rules 2–10 below; none of rules 11–13's newer fields are required — the task-id precheck still
   applies in every mode, being a validator correctness fix rather than a schema rule) — a
   provenance boundary for re-checking plans authored before the 1.1 schema, never a license to
   author new v1 plans.
2. `assurance` is present and one of A0–A4.
3. **Substance:** A2+ plans ⇒ `requirements` and `tasks` lists are non-empty (an assured plan
   cannot be empty of either).
4. **Record shape:** every requirement record carries a non-empty `id` and `text`.
4b. **Task-id precheck:** EVERY task carries a non-empty string `id`, checked BEFORE the
   coverage, dependency, and cycle validations below — a missing/empty task id is its own
   defect (keyword `empty`) naming the task index, never a downstream error or a silent skip.
5. **Identity:** requirement ids are unique; task ids are unique.
6. **Coverage:** every requirement id is covered by ≥1 task's `requirement_ids`, and every
   `requirement_ids` entry names a DECLARED requirement (no phantom references).
7. **Contracts:** every task carries a contract with non-empty `criteria` + `acceptance_command` +
   `expected_signal`; A2+ plans ⇒ every contract also carries the `rerunnable` field.
8. **Dependencies:** `deps` reference existing task ids and are acyclic (real cycle detection).
9. **Risk discipline:** `risk` present ⇒ `negative_cases` non-empty.
10. **Assurance discipline:** A3/A4 plans ⇒ EVERY contract has non-empty `negative_cases`.
11. **Schema 1.1 structured tier derivation:** per contract at A2+ — `integration_seam` (a JSON
    boolean) and `risk_class` (∈ `none` | `standard` | `security` | `destructive`) are REQUIRED
    structured derivation inputs; `required_verification_tier` present, ∈ `producer` |
    `independent` | `adversarial`, and ≥ the MECHANICALLY DERIVED minimum tier
    (`producer` < `independent` < `adversarial`): base floor by assurance — A2 ⇒ `producer`,
    A3 ⇒ `independent`, A4 ⇒ `adversarial`; `integration_seam: true` AND assurance A2 ⇒ floor
    `independent`; `risk_class` `security`/`destructive` ⇒ floor `adversarial` at EVERY
    assurance level (enforced even below A2 whenever the field is present). Free-form `risk`
    prose NEVER enters the derivation. Also per contract at A2+ — non-empty `environment`
    string; `rerunnable` is a JSON boolean (a quoted `"true"` is a type defect). Per contract
    at A3+ — non-empty `evidence` (string or object). `constraints` is explicitly optional,
    type-checked only when present. Field semantics, the mandatory-by-tier table, and the
    derivation table: `policy/acceptance-contract.md`.
12. **Schema 1.2 plan-review tier + failure surfaces (additive over 1.1):** a `"1.2"` block
    enforces every rule above PLUS: plan-level `required_plan_review_tier` present, ∈ `single` |
    `dual`, and ≥ the mechanically derived floor (the derivation and its timing live in the
    compose/stop policy below); at A2+, EVERY contract carries `failure_surfaces` — a JSON array
    (possibly EMPTY: emptiness is a valid declaration, absence is a defect) whose members are a
    subset of `concurrency` | `trust_boundary` | `streaming` | `clock` | `production_only`,
    naming the production-environment failure layers the task's `acceptance_command` must
    exercise. A `"1.1"` block carrying either 1.2-only field is rejected with a diagnostic
    naming schema 1.2. Field semantics and the floor table: `policy/acceptance-contract.md`.
13. **Schema 1.3 mutation probes + known command-shape lint (additive over 1.2):** a `"1.3"`
    block enforces every 1.1 and 1.2 rule above PLUS: `mutation_probes`, when present, is a JSON
    array whose entries are objects containing exactly `mutation` (a non-empty string) and
    `expected` (the literal string `"red"`). A non-empty `mutation_probes` array is REQUIRED for
    every `integration_seam: true` contract and every contract at assurance A3/A4; it remains
    optional elsewhere, but is shape-checked whenever present. A `"1.1"` or `"1.2"` block
    carrying `mutation_probes` is rejected with a diagnostic naming schema 1.3. For every 1.3
    contract with a non-empty command and signal, the validator rejects three known weak
    `acceptance_command` shapes:
    1. a pipe operator before a gating `&&`;
    2. an expected-signal `echo` that is not immediately preceded by `&&`;
    3. an expected-signal `echo` followed by another clause, so the signal is not terminal.
    This is narrow shape lint, not a shell parser or proof of semantic command strength. Field and
    execution semantics: `policy/acceptance-contract.md`.
14. **Schema 1.4 overrides ledger (additive over 1.3):** a `"1.4"` block enforces every 1.1–1.3
    rule above PLUS: an OPTIONAL plan-level `overrides` array — the mechanical record of
    assumption-gated dispatch (see the Human delivery override section below). When present,
    every entry is an object containing exactly `blocker`, `assumption`, `followup_test`, and
    `authorized_turn`, each a non-empty string. A malformed ledger — a non-array `overrides`, a
    non-object entry, a missing or extra field, an empty or non-string value — is its own defect
    (keyword `override`). A `"1.1"`, `"1.2"`, or `"1.3"` block carrying `overrides` is rejected
    with a diagnostic naming schema 1.4 (keyword `version`). A 1.4 block without the field
    validates identically to a 1.3 block. Field semantics and the waiver-conversion rule:
    `policy/acceptance-contract.md`.

**Schema 1.3 red-path execution duty:** Layer 1 validates the declared mutation roster and the
three known weak command shapes; it does not execute mutation probes. Before Layer 2 dispatch, the
contract producer MUST execute every proposed `acceptance_command` against a deliberately broken
scratch copy and record the raw non-zero/red result. After implementation, the implementation
producer repeats every contracted probe on scratch copies, and the verifier at the contract's
required tier independently executes every probe on fresh scratch copies. Each probe passes only
when the command exits non-zero and does not emit its terminal success signal.

Exit 0 + `PASS` on success; on any failure, non-zero exit with messages naming the offending
task/requirement id and defect class. All defects are reported, not just the first.

**Defect-keyword contract (stable, grep-able):** harness-facing Layer-1 diagnostics carry one or
more of the stable defect-class keywords `contract`, `cover`, `cycl`, `negative`, `assurance`,
`empty`, `duplicate`, `tier`, `review`, `failure_surface`, `mutation`, `command`, `version`,
`override`. A
diagnostic may carry a general and a specific keyword together; fixtures should key on the most
specific stable keyword. `tier` covers every tier-derivation defect — a
missing/invalid `required_verification_tier`, a missing/invalid `integration_seam` or
`risk_class` derivation input, or a declared tier below the mechanically derived floor; `review`
covers every plan-review-tier defect — a missing/invalid `required_plan_review_tier` or one
declared below its derived floor; `failure_surface` covers `failure_surfaces` shape and enum
defects; `mutation` covers every schema-1.3 `mutation_probes` presence and shape defect;
`command` covers the three schema-1.3 weak acceptance-command shapes; `override` covers every
schema-1.4 `overrides` ledger shape defect; `empty` includes the task-id
precheck; `version` covers legacy-`"1"`, unknown-version, and
older-schema-carrying-newer-schema-field rejections, the legacy message also naming `--legacy`.
Harness code and fixtures key on these words; changing them is a breaking schema change to this
file, the schema of record.

**Honest limit (Layer 1):** the validator verifies **structure, coverage, schema-1.3 mutation
contracts, and three known weak command shapes**. It **cannot judge command STRENGTH**: whether the
`acceptance_command` truly exercises the lever the `risk` names, or merely exits green around a
shape the narrow lint does not recognize. Producer red-path probes provide execution evidence;
Layer 2 still judges semantic reachability. A Layer-1 PASS raises the floor; it green-lights nothing
semantically.

**Temporal split:** at plan time the `acceptance_command` is read as a spec — it need not run green
on a greenfield tree — but schema-1.3 red-path self-probes must run as specified above. At
verification time both its green path and every contracted red path must run, and be re-run by the
verifier at the required tier.

## Layer 2 — semantic judge (C0–C5 rubric)

**Input-curation (bright line):** the judge receives the **plan + requirements ONLY** — never the
planner's exploration reasoning, never a sibling judge's verdict. Contaminated input produces a judge
that confirms intent instead of checking reality.

Each check with its one-line pass test:

- **C0 Substrate-grounding** — every quantitative/existence claim (a size, a count, "branch exists",
  "file present") is verified against the live substrate. *Pass:* each such claim cites a command run
  against reality, not an assertion.
- **C1 Independence** — tasks sit at real seams. *Pass:* no task secretly bundles two deliverables;
  each could be dispatched alone.
- **C2 Acceptance contract — prose-vs-mechanical (core check)** — the discriminating lever is
  REACHABLE by the `acceptance_command`, not just asserted in `expected_signal` prose. *Pass:* a wrong
  implementation makes the command exit non-zero, and the command exercises the layer the `risk` names
  (concurrency, trust-proxy, streaming/buffering, clock ⇒ blocker if unexercised). Tier-1 lever = ≥1
  negative/regression assertion the command RUNS; Tier-2 = ≥1 disconfirming criterion. The critic
  MUST attempt an empirical C2 probe for every task and SHOULD execute the command against a minimal
  hostile stub or disposable scratch artifact wherever feasible. Every C2 result and finding is
  tagged **demonstrated** (the critic ran a probe and records its command, live output, and exit code)
  or **reasoned** (execution was infeasible and the critic states why). A reasoned inference must
  never be presented as demonstrated. Demonstrated blockers stand unless the plan is fixed or the
  human explicitly selects a named relaxation; reasoned findings may be contested with an empirical
  counter-probe, not mere reassurance.
- **C3 Dependencies + cross-task consistency** — deps stated/acyclic; shared derived values
  reconciled. *Pass:* a shared value is a shared imported artifact (identity asserted) or an in-task
  consistency assertion — UNLESS some task (including an integration task) genuinely exercises the seam.
- **C4 Risk/role + (destructive plans) irreversible-op pre-mortem** — risk/blast-radius/assumptions
  surfaced; role separation mapped; harness proportional. *Pass:* destructive steps carry a complete
  inventory of everything touched + each item's post-op state, verify-on-mirror-before-live, and
  rollback *restorability* (not just backup integrity).
- **C5 Approach-fit (EVERY task)** — acceptance encodes a discriminating fixture, not a
  noun-restatement of the requirement. *Pass:* each task's acceptance asserts the *behavior* the
  requirement specifies; extra scrutiny where the task's own `risk` names an ambiguity. A C5 "concern"
  severity STILL feeds the overall verdict.
- **Coverage/completeness** — build the requirement→task matrix: map every requirement component to
  the task + `acceptance_command` that mechanically verifies it. *Pass:* no component is verified
  nowhere (the mocked-here-skipped-there hole). Plus per task: "can a wrong implementation still pass
  this acceptance_command?"

## Compose / stop policy

- **Judge count — mechanically derived, never inferred from prose.** The count is read off the
  plan block's STRUCTURED fields per the floor table (`single` < `dual`): assurance A3/A4 ⇒
  `dual`; any task with `risk_class` `security` or `destructive` ⇒ `dual`; any task with
  non-empty `failure_surfaces` ⇒ `dual`; otherwise `single`. Free-form `risk` prose NEVER
  participates in the derivation — prose is the judge's reading material, not a tier input.
  `single` remains the default (a deliberate leanness/independence trade).
- **Absent declaration relaxes nothing:** an absent (undeclared) `required_plan_review_tier` — a
  1.1 block, or a block omitting the field — means the derived floor applies exactly as if it had
  been declared.
- **When the count is decided:** after Layer 1 returns, before Layer-2 pass 1 is dispatched. The
  validated block is the derivation input, and the judge lane(s) are fixed before any semantic
  verdict exists to anchor them.
- **What `dual` requires:** recorded evidence of TWO disjoint-input judge dispatches — two
  separate judge contexts, each receiving the plan + requirements only, neither seeing the
  other's verdict. One judge asked twice is not `dual`; a second pass over the first verdict is
  not disjoint.
- **Single-judge blocker:** one confirming independent pass before any re-plan — never re-plan off a
  single unconfirmed verdict.
- **Hard 2-pass cap.** Cap reached with an open blocker ≠ proceed → **escalate to the human**. Never
  auto-dispatch past an open blocker. (The **unattended/sleep posture** does not relax this: the cap
  is a human-only lever, so a sleep-mode session halts here and waits — `assurance-model.md`.) The
  standard, human-selected menu at that escalation is:
  1. **Extend by exactly one named Layer-2 pass.** Eligible only when the open blockers span more
     than one rubric check or at least one blocker is not C2. The authorization names that one pass;
     it is one complete pass at the already-derived judge count and cannot be chained into another
     extension.
  2. **mutation-gated dispatch.** Eligible only when ALL open blockers are C2-local and EACH blocker
     maps one-to-one to a contracted, mechanically executable `mutation_probes` entry whose expected
     result is red. The mapping and probe remain in the affected task's contract, and the verifier
     must execute every probe on a fresh scratch copy. Any non-C2 blocker, unmapped blocker,
     prose-only compensation, or mutation that cannot be executed makes this option ineligible.
  3. **assumption-gated dispatch (human delivery override).** Eligible on any genuine human
     delivery-intent turn once Layer-2 findings exist — at this cap escalation and equally at any
     earlier point in the cycle; the cap is merely one place the menu is presented. Safety-floor
     blockers remain dispatch-blocking; every other open blocker converts to a recorded assumption
     plus a required follow-up test in the affected task's contract, and one subsequent human
     confirmation turn dispatches. Full semantics: the Human delivery override section below.
  4. **Halt.** Always eligible and the default when the human selects no relaxation; preserve the
     blocker record and dispatch nothing.

  Only an explicit human decision may select options 1, 2, or 3. Any alternative is a **bespoke named
  relaxation**: it must state the invariant being waived, exact task/blocker scope, compensating
  mechanical controls, and termination condition, and it requires explicit human authorization.
  The menu is decision support, never standing authorization.
- **Do NOT trust a model-judged convergence signal.** Empirically, later passes each caught a real,
  distinct defect while the model's own "would another pass help?" said no every time — a fixed cap is
  better-calibrated than loop-until-clean. Never a numeric score (invites plan-polishing). Beyond pass
  2 clean = plan-polishing.
- **Disposition by check:** a C5 goal-vs-proof contradiction ⇒ **restart** the plan; C2/C3 defects ⇒
  **local revise**. A check rated "clean" cannot coexist with a real defect mapped to it.
- **Post-blocker protocol.** After ANY blocker verdict the only lawful continuations are: (a) local
  revise → re-run Layer 1 → dispatch a FRESH independent input-curated Layer-2 pass over the revised
  plan — this pass COUNTS toward the hard 2-pass cap above — then proceed only on a clean verdict
  from THAT fresh pass; or (b) escalate to the human, who may select only an eligible standard menu
  option — including a confirmed human delivery override, which a genuine delivery-intent turn may
  also trigger without waiting for an escalation (see the Human delivery override section below) —
  or explicitly authorize a bespoke named relaxation as defined above. No implicit third path
  exists. Dispatch may begin from
  exactly one thing: a clean verdict from a fresh independent Layer-2 pass, or explicit human
  authorization — an eligible menu selection, a confirmed human delivery override, or a bespoke
  named relaxation — nothing else, no matter what Layer 1 reports.
- **A self-checked revision is never a clean verdict** — Layer 1 plus the planner's own confirmation
  does not clear a blocker; only a fresh independent Layer-2 pass, re-run after the revision, can.
  The cap is a ceiling on Layer-2 passes, not a license to dispatch without one: reaching the cap
  with an open blocker still means escalate (see "Hard 2-pass cap" above) — it never means dispatch.

## Human delivery override (assumption-gated dispatch)

**WHY:** review that cannot end is not rigor — it is a treadmill, and governance that is not
economical does not get used. Field evidence: genuine human turns repeatedly selected the practical
outcome ("implement now") and the active policy recognized them only as input to another plan
cycle, burning review spend with zero dispatched workers. This section gives delivery intent a
recognized meaning. The bespoke-relaxation hatch already existed, but its construction burden sat
on the human; here the burden moves to the model — the human holds a cheap lever, the model does
the paperwork. The override is a *quality* valve, never a *safety* valve: everything above the
floor is priced in the human's currency; the floor itself is non-negotiable.

The override is standard escalation-menu option 3 and is human-invocable at ANY point after
Layer-2 findings exist — not only at the 2-pass cap. Seven invariants:

- **Trigger duty.** A genuine human turn expressing delivery intent past open findings
  ("implement now", "stop reviewing", "proceed", or equivalent) means the model
  MUST NOT start a new plan/critique cycle. Its only lawful responses are the override offer
  below or a safety-floor refusal naming the specific floor blockers. Treating a delivery-intent
  turn as mere input to another cycle is a policy violation, not diligence.
- **Safety floor — never waivable.** Six blocker classes remain dispatch-blocking regardless of
  any human turn:
  1. destructive or externally-consequential action without authority/rollback;
  2. security boundary defect;
  3. irreversible architectural commitment;
  4. C5 goal/proof contradiction;
  5. unavailable required substrate;
  6. demonstrated-vacuous acceptance command.
  The floor is deliberately minimal: quality defects are the human's to waive, and these six are
  not quality defects. Nothing may be added to or removed from this list by any relaxation.
- **Conversion.** Each waived blocker becomes a **recorded assumption plus a required follow-up
  test** — a `mutation_probes` entry, a negative case, or a golden vector — attached to the
  affected task's contract. Nothing is silently dropped: waiving trades review-now for
  evidence-later, never for nothing. Conversion mechanics: `policy/acceptance-contract.md`.
- **One confirmation turn.** The offer presents, in a single turn: the safety/assumption split,
  the assumption ledger with its follow-up tests, review expenditure to date, and the exact scope
  of what dispatches (named tasks of this plan; never future cycles). A subsequent genuine human
  turn on the adapter-declared authenticated human channel confirms it, and dispatch begins
  immediately. Provenance rules of `policy/assurance-model.md` apply unchanged: simulated, proxy,
  evaluator-injected, or standing text can neither open the override nor confirm it. NO token or
  nonce ritual for non-destructive work — natural language plus echo-back is the entire ceremony
  (nonces remain adapter territory for destructive authorization where channel provenance is weak).
- **Waived stays waived.** The override binds to the *objective*, not the plan revision. A later
  cycle for the same objective may raise genuinely new findings, and safety-floor findings always
  block — but it may NOT re-raise a waived assumption absent new evidence. If revision resurrected
  waivers, one trivial forced revision would rebuild the treadmill.
- **Audit marker.** Dispatch under override emits a grep-able record preserved with the plan:
  `[OVERRIDE: assumption-gated dispatch — <waived-count> waived → assumptions+tests;
  <retained-count> safety retained; authorized turn <n>]`. This IS the named relaxation,
  standardized — no silent gate-skip. The schema-1.4 `overrides` ledger (Layer-1 rule 14 above)
  is its mechanical counterpart, authored by the model at zero human burden.
- **Self-clearance preserved.** Only a genuine human turn waives; the model never clears its own blockers.
  The override moves the formalization burden to the model — never the authority.

## Honest limit (whole gate)

A clean verdict RAISES THE FLOOR on plan structure + verifiability. Layer 1 machine-checks only the
three known weak command shapes; semantic command strength still depends on red-path evidence and
the judge's reading. The gate does not verify correctness of the eventual work — the downstream
verification tier (see `policy/acceptance-contract.md`) still owns that.

**Contract-bounded verification has a ceiling.** Acceptance contracts bound what verification sees:
a verifier that only re-executes the contracts inherits every blind spot the plan author had.
Verifiers must therefore additionally attempt **off-contract hostile probes** — empty inputs,
duplicate inputs, hostile/seeded user content, bypass paths the contracts never anticipated — and
report them alongside the contract re-runs. This is an empirical lesson, not a hypothetical: the two
probes that broke this framework's own first build (an empty assured plan that PASSed validation, and
a phantom requirement reference that PASSed coverage) were both off-contract.
