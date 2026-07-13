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
   mode — exactly `"1.1"`: **schema 1.1 is mandatory**. A `"version": "1"` block is rejected as a
   legacy schema version; unknown version strings are rejected naming the version. The `--legacy`
   flag accepts `"version": "1"` blocks under the ORIGINAL v1 rules (rules 2–10 below; none of
   rule 11's 1.1 fields are required — the task-id precheck still applies in every mode, being a
   validator correctness fix rather than a schema rule) — a provenance boundary for re-checking
   plans authored before the 1.1 schema, never a license to author new v1 plans.
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

Exit 0 + `PASS` on success; on any failure, non-zero exit with messages naming the offending
task/requirement id and defect class. All defects are reported, not just the first.

**Defect-keyword contract (stable, grep-able):** every failure message carries exactly one of the
defect-class keywords `contract`, `cover`, `cycl`, `negative`, `assurance`, `empty`, `duplicate`,
`tier`, `version` (`tier` covers every tier-derivation defect — a missing/invalid
`required_verification_tier`, a missing/invalid `integration_seam` or `risk_class` derivation
input, or a declared tier below the mechanically derived floor; `empty` includes the task-id
precheck; `version` covers legacy-`"1"` and unknown-version rejections, the legacy message also
naming `--legacy`). Harness code and fixtures key on these words; changing them is a breaking
schema change to this file, the schema of record.

**Honest limit (Layer 1):** the validator verifies **structure and coverage** — that a discriminating
command EXISTS for every requirement and the plan graph is sound. It **cannot judge command STRENGTH**:
whether the `acceptance_command` truly exercises the lever the `risk` names, or merely exits green
around it. That is Layer 2's job. A Layer-1 PASS raises the floor; it green-lights nothing semantically.

**Temporal split:** at plan time the `acceptance_command` is read as a spec — it need not run green on
a greenfield tree. At verification time it must run, and be re-run by the independent judge.

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
  negative/regression assertion the command RUNS; Tier-2 = ≥1 disconfirming criterion.
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

- **Judge count:** ONE judge by default (a deliberate leanness/independence trade). TWO independent
  judges with disjoint inputs for **A3+/destructive** plans.
- **Single-judge blocker:** one confirming independent pass before any re-plan — never re-plan off a
  single unconfirmed verdict.
- **Hard 2-pass cap.** Cap reached with an open blocker ≠ proceed → **escalate to the human**. Never
  auto-dispatch past an open blocker.
- **Do NOT trust a model-judged convergence signal.** Empirically, later passes each caught a real,
  distinct defect while the model's own "would another pass help?" said no every time — a fixed cap is
  better-calibrated than loop-until-clean. Never a numeric score (invites plan-polishing). Beyond pass
  2 clean = plan-polishing.
- **Disposition by check:** a C5 goal-vs-proof contradiction ⇒ **restart** the plan; C2/C3 defects ⇒
  **local revise**. A check rated "clean" cannot coexist with a real defect mapped to it.

## Honest limit (whole gate)

A clean verdict RAISES THE FLOOR on plan structure + verifiability. It does not machine-check command
strength beyond a judge's reading, and it does not verify correctness of the eventual work — the
downstream independent verification tier (see `policy/acceptance-contract.md`) still owns that.

**Contract-bounded verification has a ceiling.** Acceptance contracts bound what verification sees:
a verifier that only re-executes the contracts inherits every blind spot the plan author had.
Verifiers must therefore additionally attempt **off-contract hostile probes** — empty inputs,
duplicate inputs, hostile/seeded user content, bypass paths the contracts never anticipated — and
report them alongside the contract re-runs. This is an empirical lesson, not a hypothetical: the two
probes that broke this framework's own first build (an empty assured plan that PASSed validation, and
a phantom requirement reference that PASSed coverage) were both off-contract.
