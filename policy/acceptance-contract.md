# Acceptance Contract v2

**WHY:** the acceptance contract is the load-bearing artifact of verification. It is authored at plan
time, hardened by the Plan-Critique Gate (`policy/plan-critique.md`), copied verbatim into the worker
dispatch, and — at the tiers that require it — RE-EXECUTED by an independent judge after the work
lands. The producer's recorded check output is evidence to re-execute, not proof to accept. A contract
whose discriminating lever lives only in prose verifies nothing — a wrong implementation passes it.

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
| `integration_seam` | JSON **boolean** — does this task sit on an integration seam (its correctness is only observable where two components meet)? A structured tier-derivation input; the free-form `risk` prose never substitutes for it. |
| `risk_class` | One of `none` \| `standard` \| `security` \| `destructive` — the structured classification of the work's blast radius. `security`/`destructive` mechanically floors the tier at `adversarial` regardless of assurance. |
| `required_verification_tier` | Who must re-execute the check before the terminal verified state is reached — field value `producer` \| `independent` \| `adversarial`, selecting the terminal state `verified_producer` / `verified_independent` / `verified_adversarial`. Must be ≥ the floor MECHANICALLY DERIVED from assurance + `integration_seam` + `risk_class` (derivation table below). |

## Tier-1 definition

**Tier-1 = the `acceptance_command` RUNS ≥1 negative/regression assertion.** Not "could", not
"describes" — runs. A bare smoke import (`python -c 'import counter'`) is **never** Tier-1: it exercises
nothing and a wrong implementation passes it. A test invocation whose discriminator sits behind a
skipped/disabled test is equally void — a green run proves nothing when the assertion never executed.
Tier-2 (weaker, for when Tier-1 is genuinely unreachable) = the contract carries ≥1 explicit
disconfirming criterion an independent reviewer checks against the artifact.

A work item CANNOT reach its terminal verified state without recorded machine-check output from the
`acceptance_command`, fresh per `produced_after_change`. **Who** must have executed that run before
the terminal state is reached is fixed by `required_verification_tier` — see the next section.

## Verification tiers — terminal states

`verified` is not one state; it is three. Which one is terminal for a work item is fixed at plan time
by `required_verification_tier`:

| Terminal state | Who re-executes the `acceptance_command` | Sufficient terminal state for |
|---|---|---|
| `verified_producer` | the producing context — recorded machine-check output from the producer, fresh per `produced_after_change` | A0 and A1 work — this is the terminal state, not a waypoint |
| `verified_independent` | an independent, input-curated judge re-executes the `acceptance_command` | A2 integration seams; all A3+ |
| `verified_adversarial` | an independent judge, plus deliberate refutation attempts and probes beyond what the contract anticipated | A4; security/destructive work at any level |

**Producer evidence remains evidence at every tier.** Every producer runs its own checks and records
the output, fresh per `produced_after_change`, at every assurance level. What changes across tiers is
not whether that evidence exists but **who must re-execute the `acceptance_command` before the
terminal state is reached**: at `verified_producer` the producer's own recorded run *is* the verdict
of record; at the higher tiers it is input handed to a judge who runs the command again — evidence to
re-execute, not proof to accept.

### `required_verification_tier` — mechanical floor derivation

The minimum tier is DERIVED from structured fields only — the plan-level `assurance` plus the
per-contract `integration_seam` and `risk_class`. Free-form `risk` prose never enters the
derivation. `tools/validate-plan` enforces the floor mechanically: with the tier order
`producer` < `independent` < `adversarial`, the declared `required_verification_tier` must be
≥ the derived floor.

| Derivation input | Effect on the minimum tier |
|---|---|
| assurance A0 / A1 | base floor `producer` (tier fields optional below A2) |
| assurance A2 | base floor `producer` |
| assurance A3 | base floor `independent` |
| assurance A4 | base floor `adversarial` |
| `integration_seam: true` AND assurance A2 | floor raised to `independent` |
| `risk_class: "security"` or `"destructive"` | floor raised to `adversarial` — at EVERY assurance level |

Selecting a floor tier's terminal state: `producer` → `verified_producer`, `independent` →
`verified_independent`, `adversarial` → `verified_adversarial`.

**Spelling reconciliation (field values vs terminal-state names).** In the plan block, the
`required_verification_tier` FIELD takes the short values `producer` | `independent` | `adversarial`;
each selects the corresponding terminal STATE `verified_producer` / `verified_independent` /
`verified_adversarial`. The `verified_*` spellings name states an item *reaches* — they are **not**
valid field values, and the validator rejects them; write `independent`, never `verified_independent`,
in the field.

## Block versioning — `"version": "1.1"` is MANDATORY; `"version": "1"` is legacy-only

The plan's embedded machine-readable block declares a schema `version`. Schema `"1.1"` is
**mandatory**: default validation REQUIRES `"version": "1.1"` and rejects a `"version": "1"`
block as a legacy schema version. Version `"1"` exists for HISTORICAL PROVENANCE ONLY —
re-checking plans authored before the 1.1 schema — and is accepted solely under
`tools/validate-plan --legacy`, which applies the original v1 rules. Never author a new plan
against v1. Unknown version strings are rejected naming the version.

Blocks declaring `"version": "1.1"` are additionally held, per contract, to the
mandatory-by-tier field table below (machine-enforced by `tools/validate-plan`):

| Field (1.1) | Mandatory at | Rule |
|---|---|---|
| `integration_seam` | A2+ | a JSON **boolean** — structured tier-derivation input |
| `risk_class` | A2+ | ∈ `none` \| `standard` \| `security` \| `destructive` — structured tier-derivation input |
| `required_verification_tier` | A2+ | present; ∈ `producer` \| `independent` \| `adversarial`; ≥ the floor mechanically derived from assurance + `integration_seam` + `risk_class` (derivation table above) |
| `environment` | A2+ | non-empty string |
| `rerunnable` | A2+ | a JSON **boolean** — the quoted string `"true"` is a type defect, not a value |
| `evidence` | A3+ | non-empty (string or object) |
| `constraints` | never — **explicitly optional** | type-checked only when present (string, list, or object) |

Below A2 the tier fields are optional, with one exception that binds at EVERY assurance level:
a contract declaring `risk_class` `security` or `destructive` must declare
`required_verification_tier: "adversarial"` — the floor derivation does not relax below A2.

Fields not listed keep their version-1 rules (`criteria` / `acceptance_command` / `expected_signal`
non-empty; `rerunnable` present at A2+; `risk` ⇒ `negative_cases`; A3/A4 ⇒ `negative_cases` in every
contract).

## Evidence classes — non-code and mixed work

When the deliverable is not (only) executable code, "machine-checkable" fans out into five evidence
classes. A contract for such work names which classes it uses; each class establishes only what it can
establish, and no class substitutes for another.

| Class | What it is | What it establishes — and what it never can |
|---|---|---|
| **behavioral-machine** | a command that exercises the artifact's behavior (test run, executable example, renderer round-trip asserting semantics) | behavior under the exercised conditions — the strongest class wherever any runtime exists |
| **structural-artifact** | link checkers, format/schema validators, rendering checks, pattern searches | form only. A link checker never validates substance; a structural pass says nothing about whether the content is true |
| **source-grounded** | every load-bearing claim traced to a retrievable source, plus contradiction checks across sources | that claims are grounded and mutually consistent — not that the synthesis is complete or well-judged |
| **expert-judgment** | a designated reviewer judging against explicit disconfirming criteria written BEFORE the review | substance quality — valid only when the criteria predate the review and the reviewer records what would have failed the artifact |
| **human-authorization** | explicit human sign-off | permission for irreversible or outward-facing effects — never a substitute for any other class's evidence |

### Combination table — minimum classes by assurance tier

| Work / tier | Minimum evidence-class combination |
|---|---|
| docs / design, A0–A1 | structural-artifact (producer-run) |
| docs / design, A2+ | structural-artifact + expert-judgment (independent, per the item's `required_verification_tier`) |
| research, A0–A1 | source-grounded (producer-run spot checks) |
| research, A2 | structural-artifact + source-grounded + independent expert-judgment |
| research / docs, A3+ | the full A2 row, executed at the item's `required_verification_tier` |
| irreversible or outward-facing effects, any tier | the applicable row above + human-authorization |

Prose-only acceptance ("reads well", "covers the topic") remains **never Tier-1** and never sufficient
on its own: it is expert-judgment with no disconfirming criteria — which is to say, no evidence class
at all. Record every class's output as evidence.

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
