# Acceptance Contract v2

**WHY:** the acceptance contract is the load-bearing artifact of verification. It is authored at plan
time, hardened by the Plan-Critique Gate (`policy/plan-critique.md`), copied verbatim into the worker
dispatch, and RE-EXECUTED by an independent judge after the work lands. The producer's recorded check
output is evidence to re-execute, not proof to accept. A contract whose discriminating lever lives only
in prose verifies nothing — a wrong implementation passes it.

## Fields — one-line semantics

| Field | Semantics |
|---|---|
| `requirement_ids[]` | The requirement ids this task discharges; every requirement must be covered by ≥1 task's list. |
| `criteria` | What "correct" means for this task, in behavioral terms — not a restatement of the requirement's nouns. |
| `acceptance_command` | A command RE-RUNNABLE at verification time that exercises the discriminating lever; a wrong implementation makes it exit non-zero. |
| `environment` | Where the evidence is valid (which host/sandbox/config); evidence produced elsewhere does not transfer. |
| `expected_signal` | The exact output/exit pattern that means PASS — anchored so it cannot also match a fail line (see footguns below). |
| `negative_cases[]` | Disconfirming assertions the command runs — inputs/states that a wrong implementation would mishandle. **REQUIRED whenever `risk` is present.** |
| `risk` | The failure this task must not ship — name the layer (concurrency, trust-proxy, streaming/buffering, clock, data loss); the command must exercise THAT layer. |
| `evidence` | Artifact types the check records (test log, build output, diff, rendered page) + **freshness: `produced_after_change`** — evidence older than the change it claims to verify is void. |
| `rerunnable` | Boolean — the check can be executed again, from the tree, by a context that did not produce the work. Non-rerunnable evidence is testimony. |
| `constraints` | Runtime/network/side-effect bounds the check must respect (e.g. no network, sandbox only, read-only on the live store). |

## Tier-1 definition

**Tier-1 = the `acceptance_command` RUNS ≥1 negative/regression assertion.** Not "could", not
"describes" — runs. A bare smoke import (`python -c 'import counter'`) is **never** Tier-1: it exercises
nothing and a wrong implementation passes it. A test invocation whose discriminator sits behind a
skipped/disabled test is equally void — a green run proves nothing when the assertion never executed.
Tier-2 (weaker, for when Tier-1 is genuinely unreachable) = the contract carries ≥1 explicit
disconfirming criterion an independent reviewer checks against the artifact.

A work item CANNOT move `completed` → `verified` without recorded machine-check output from the
`acceptance_command`, fresh per `produced_after_change`, re-executed by the independent judge.

## Non-shell evidence path (docs / research / design work)

When the deliverable has no runtime to exercise, `acceptance_command` may be a **named mechanical
check** — a pattern search over the artifact, a link-checker, a renderer/validator run — **plus a
designated independent reviewer** with explicit disconfirming criteria written before review.
Prose-only acceptance ("reads well", "covers the topic") is **never Tier-1** and never sufficient on
its own: pair the mechanical floor with the independent reviewer, and record both outputs as evidence.

## Exemplar — BAD vs GOOD (concurrency risk)

**BAD — prose-only lever (a wrong implementation still passes):**
```jsonc
{
  "criteria": "counter increments are atomic under concurrency",
  "acceptance_command": "python -c 'import counter'",   // smoke import — exercises nothing
  "expected_signal": "no error; atomicity verified",     // ATOMICITY LIVES ONLY IN PROSE
  "risk": "concurrency",                                 // never exercised => BLOCKER
  "negative_cases": []                                   // risk present, no negative case => invalid
}
```

**GOOD — runs a negative/regression assertion a wrong implementation fails:**
```jsonc
{
  "criteria": "200 parallel increments yield a final count of exactly 200",
  "acceptance_command": "node test/atomicity.test.js  # fires 200 parallel incrs, asserts final===200; exits non-zero on drift",
  "expected_signal": "(✓|PASS).*atomic increment under 200-way concurrency",
  "risk": "concurrency — command spawns real parallel writers, not a serial loop",
  "negative_cases": ["parallel writers with injected scheduling jitter still converge to exactly 200"]
}
```

The rule generalizes: when `risk` names a production-environment failure layer (concurrency,
trust-proxy, streaming/buffering, clock), the command must exercise **that layer** — a unit test one
layer down does not discharge it.

## Signal-anchoring footguns

- **The fail-line trap.** `grep -q '<test name>'` alone is a BUG — it matches a test runner's
  `✕ <test name>` FAIL line as readily as `✓ <test name>`. Anchor `expected_signal` to the pass
  marker: `grep -qE '(✓|PASS).*<test name>'`.
- **The pipe-discards-exit-code trap.** `command | tee log` reports `tee`'s success, not the test's —
  a failing test exits green. Capture `${PIPESTATUS[0]}` (or drop the pipe) so a failing test actually
  fails the gate.
- General principle: `expected_signal` must be a pattern that **cannot** appear in a failing run. If a
  fail line can print it, the signal is unanchored and the contract is broken.

## Validation

Structural completeness of contracts (non-empty `criteria` + `acceptance_command` + `expected_signal`;
`risk` ⇒ non-empty `negative_cases`; coverage; acyclic deps) is machine-checked by `tools/validate-plan`
against the plan's embedded `json agentfw-plan` block — see `policy/plan-critique.md` Layer 1. Whether
the command is STRONG enough to exercise the lever is a Layer-2 judge question; the validator cannot
answer it.
