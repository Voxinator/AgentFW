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

1. The block parses as valid JSON, and `version` is present.
2. `assurance` is present and one of A0–A4.
3. **Coverage:** every requirement id is covered by ≥1 task's `requirement_ids`.
4. **Contracts:** every task carries a contract with non-empty `criteria` + `acceptance_command` +
   `expected_signal`.
5. **Dependencies:** `deps` reference existing task ids and are acyclic (real cycle detection).
6. **Risk discipline:** `risk` present ⇒ `negative_cases` non-empty.
7. **Assurance discipline:** A3/A4 plans ⇒ EVERY contract has non-empty `negative_cases`.

Exit 0 + `PASS` on success; on any failure, non-zero exit with messages naming the offending
task/requirement id and defect class. All defects are reported, not just the first.

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
