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
| `mutation_probes[]` | Schema 1.3 roster of deliberate scratch-copy breakages, each shaped exactly as `{mutation: non-empty string, expected: "red"}`. The acceptance command must exit non-zero and must not emit its terminal success signal under each mutation. |
| `red_witness` | Schema 1.7 record that the WHOLE `acceptance_command` has been run once before Layer-2 dispatch on a deliberately broken/bare scratch (exit ≠ 0), carrying `tree`, `command_sha256` (digest of the contract's exact command string), `exit_code`, and `evidence_path`. Proving the command CAN pass is no longer plan-time evidence — it is the verifier's IMPOSSIBLE-COMMAND duty (see Verification tiers below). |
| `enforced_in` | Schema 1.7 requirement-level field (D-29) — a non-empty array of non-empty repo-relative path strings naming where this requirement is actually enforced. Every `must` requirement's `enforced_in` paths must each be exact-string-matched inside the `touches` of ≥1 covering task — a review round spent on a requirement enforced nowhere any task owns is the vacuity the locality check exists to catch. |
| `touches` | Schema 1.7 task-level field (D-29) — the array of repo-relative path strings this task modifies. It is the OTHER side of the locality check: a task's `touches` satisfies a covered requirement's `enforced_in` path only by exact string equality, never by substring or prefix. |
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

### Producer red-path self-probe

Before Layer 2 dispatch, the planner — as producer of the contract — MUST execute every proposed
`acceptance_command` against at least one deliberately broken **scratch copy** and record the raw
non-zero/red result. The breakage must target the discriminating lever (for example a hardcoded
success token, empty test file, stale generated tag, removed assertion, or seeded leak), not an
unrelated syntax error. Never perform a mutation probe in the authoritative working tree.

For schema 1.3, encode those breakages in `mutation_probes`. Each implementation producer repeats
the contracted probes after the change as part of its own checks, and the verifier at the contract's
required tier executes every probe independently on scratch copies before returning a verified
verdict. `expected: "red"` means the acceptance command exits non-zero **and** cannot reach its
terminal success signal. Record both green-path and red-path output as fresh evidence.

### The witness pair (schema 1.6) — prove the command CAN pass, at plan time

The red-path self-probe proves an `acceptance_command` can FAIL; it never proves the command can
PASS — an impossible-to-pass command aces every red probe while being incapable of ever going
green, which makes it indistinguishable from the strictest command in the room. Under schema 1.6,
before Layer-2 dispatch every `acceptance_command` therefore carries TWO recorded runs — the
**witness pair**:

- **red** — the existing duty, unchanged: one end-to-end run on a deliberately broken or bare
  scratch, exiting non-zero without the terminal success signal;
- **green** — one end-to-end run on a **witness tree**: a planner-authored minimal tree (stubs
  allowed) that satisfies the contract, labeled `witness-tree` in its evidence record. The green
  witness claims exactly one thing — *this command CAN pass* — and is never evidence that work
  was done. No green witness ⇒ the gate rejects the plan at plan time.

**Whole-command-only evidence.** A witness (red or green) counts only if it is one recorded
end-to-end invocation of the ENTIRE command string from the contract, matched to the contract by
`command_sha256` — the sha256 of the exact `acceptance_command` string. Running one leg of a
multi-leg command and reporting the whole command is inadmissible, and its record cannot carry
the contract's digest.

**Void witness trees.** A witness tree that an EMPTY implementation would also satisfy is void.
The mechanical half of the enforcement is the red witness on the bare scratch; the semantic half
is a C2 judge duty — reject a green witness whose tree still passes with the deliverables stubbed
to nothing (`policy/plan-critique.md`). Raw transcripts live beside the plan (e.g.
`.agentfw/evidence/<plan>/witness/`); the plan block's `witness_pair` field carries the
machine-checkable summary per contract (field table in the schema 1.6 section below). At
verification time the green path runs on the REAL tree per the tiers above — the witness tree
never substitutes for that.

**Superseded by schema 1.7 (D-28) — retained here as historical schema documentation.** Schema
1.6 is no longer the schema of record; new plans author against schema 1.7 (below), which demotes
the green leg above to a verifier duty. This section documents 1.6 behavior unchanged, for plans
still declaring `"version": "1.6"`.

### The red witness (schema 1.7) — the pass leg is now a verifier duty

The red-path self-probe proves an `acceptance_command` can FAIL; it never by itself proves the
command can PASS — an impossible-to-pass command aces every red probe while being incapable of
ever going green, which makes it indistinguishable from the strictest command in the room. Schema
1.6 (above) closed that gap with a plan-time green witness on a planner-authored witness tree.
Schema 1.7 (D-28) DEMOTES that green leg: proving the command CAN pass is no longer plan-time
evidence — it becomes the verifier's **IMPOSSIBLE-COMMAND duty** (see "Verification tiers"
below). The red leg is retained UNCHANGED; a schema-1.7 contract carries one recorded plan-time
witness, not two:

- **red** (`red_witness`) — the existing duty, unchanged: one end-to-end run on a deliberately
  broken or bare scratch, exiting non-zero without the terminal success signal.
- **green** — no longer recorded at plan time. Before returning a verified verdict, the verifier
  MUST demonstrate the command passing against a CORRECT implementation. When the verifier cannot
  make the contracted command pass against a correct implementation, it returns
  **IMPOSSIBLE-COMMAND**: a CONTRACT defect, routed to the re-approach fork, never a work defect
  charged to the worker who implemented correctly against a contract that could not be satisfied.

**Whole-command-only evidence.** A red witness counts only if it is one recorded end-to-end
invocation of the ENTIRE command string from the contract, matched to the contract by
`command_sha256` — the sha256 of the exact `acceptance_command` string. Running one leg of a
multi-leg command and reporting the whole command is inadmissible, and its record cannot carry
the contract's digest.

**Why demote the leg instead of dropping the duty.** An impossible-to-pass command is exactly as
dangerous whether it is caught at plan time or at verification time — the danger is a contract no
implementation can satisfy, not the timing of the catch. What schema 1.7 removes is the COST of
authoring a planner witness tree at plan time; what it does NOT remove is the duty to prove
passability before the terminal verified state — that duty simply moves to the verifier, who is
already re-running the command against real work. An impossible red leg (`exit_code: 0` on
`red_witness`) is as void as a schema-1.6 contract whose green leg was faked, and Layer 1 rejects
it at plan time exactly as before.

Shell success signals are ordered, not merely present: each checking clause must gate the next by
exit status; no pipeline may appear before a gating `&&`; and an explicit success signal is emitted
last, only after an immediately preceding successful `&&`. A signal printed before a later clause is
not evidence that the later clause passed.

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

**The IMPOSSIBLE-COMMAND duty (schema 1.7, D-28).** Before returning ANY verified verdict at
`verified_independent` or `verified_adversarial`, the verifier MUST demonstrate the
`acceptance_command` passing against a correct implementation — the plan-time green witness that
schema 1.6 required is gone, and this is where its proof obligation now lives. When the verifier
cannot make the contracted command pass against a correct implementation, it returns
**IMPOSSIBLE-COMMAND** rather than a work-defect verdict: this is a **CONTRACT defect** — the plan
authored an unpassable acceptance test — and it is routed to the **re-approach fork** (the plan
must be revised and re-gated), **never** charged against the worker who implemented correctly
against a contract that could not be satisfied. Conflating IMPOSSIBLE-COMMAND with a work defect
punishes the wrong party and hides the actual bug, which is in the contract, not the
implementation.

**Producer evidence remains evidence at every tier.** Every producer runs its own checks and records
the output, fresh per `produced_after_change`, at every assurance level. What changes across tiers is
not whether that evidence exists but **who must re-execute the `acceptance_command` before the
terminal state is reached**: at `verified_producer` the producer's own recorded run *is* the verdict
of record; at the higher tiers it is input handed to a judge who runs the command again — evidence to
re-execute, not proof to accept.

### Persisted evidence for delegated or platform-opaque execution

The paragraph above assumes the parent's own record captures what ran. It often doesn't: when a
producer runs destructive or verification-bearing commands in a context whose raw output the parent's
record does not capture — a delegated subagent, a platform whose session logs don't expose subagent
traces — the producer MUST persist the raw command output to files in the workspace (an `evidence/`
directory, or the authoritative store) that the parent references by path and that a judge can read.
This is the `evidence` field's freshness (`produced_after_change`) and `rerunnable` discipline applied
at the exact point where, without persistence, there would be nothing left to re-execute against.

Narration is testimony, not evidence: a parent's summary or narration of delegated execution never
satisfies the capture condition, however detailed — no qualifier, no exception clause, and no "for
purposes of" scoping narrows this. A detailed paraphrase of what a subagent did is still not the
recorded output the subagent produced.

Role separation holds unchanged here: the producer persists the files; the judge reads them and
re-executes the `acceptance_command` against the tree, per "Producer evidence remains evidence at
every tier" above — persisted files document that execution happened, they do not substitute for the
judge's own re-run.

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

## Block versioning — `"1.7"` is the schema of record; `"1.1"`–`"1.6"` remain valid; `"1"` is legacy-only

The plan's embedded machine-readable block declares a schema `version`. Schema `"1.7"` is the
**schema of record** — author new plans against it (see the schema 1.7 section below). Schemas
`"1.1"` through `"1.6"` remain valid for plans that predate 1.7: default validation accepts
all seven and rejects a `"version": "1"` block as a legacy schema version. Version `"1"` exists for
HISTORICAL PROVENANCE ONLY — re-checking plans authored before the 1.1 schema — and is accepted
solely under `tools/validate-plan --legacy`, which applies the original v1 rules. Never author a new
plan against v1. Unknown version strings are rejected naming the version.

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

## Schema 1.2 — retained: plan-review tier + failure surfaces

Schema `"1.2"` is ADDITIVE over 1.1: every 1.1 rule above applies unchanged to a 1.2 block, and
two fields are added (machine-enforced by `tools/validate-plan`):

| Field (1.2) | Level | Mandatory at | Rule |
|---|---|---|---|
| `required_plan_review_tier` | plan | always (any assurance) | ∈ `single` \| `dual` — how many independent, input-curated Layer-2 judges must review the PLAN before dispatch; must be ≥ the floor mechanically derived below |
| `failure_surfaces` | per contract | A2+ | a JSON **array** (possibly **EMPTY** — emptiness is a valid declaration, absence is a defect), a SUBSET of `concurrency` \| `trust_boundary` \| `streaming` \| `clock` \| `production_only` — the production-environment failure layers this task's risk lives in; the named `acceptance_command` must exercise those layers |

### `required_plan_review_tier` — mechanical floor derivation

The minimum plan-review tier is DERIVED from structured fields only — the plan-level `assurance`
plus each contract's `risk_class` and `failure_surfaces`. Free-form `risk` prose never enters the
derivation. With the tier order `single` < `dual`, the declared `required_plan_review_tier` must
be ≥ the derived floor; a declaration below its floor is rejected naming the derivation.

| Derivation input | Effect on the minimum plan-review tier |
|---|---|
| assurance A0 / A1 / A2 | base floor `single` |
| assurance A3 / A4 | floor `dual` |
| any task with `risk_class: "security"` or `"destructive"` | floor `dual` — at EVERY assurance level |
| any task with NON-EMPTY `failure_surfaces` | floor `dual` — at EVERY assurance level |

### 1.1 compatibility — the two fields REQUIRE 1.2

Schema 1.1 does not define the two fields above. A `"version": "1.1"` block carrying
`required_plan_review_tier` or `failure_surfaces` is REJECTED with a diagnostic naming schema
1.2 — declaring the fields without declaring the schema that defines them is the
declared-single-on-1.1 dodge, not backward compatibility. Existing 1.1 plans that do not carry
the fields validate exactly as before. Validators that predate 1.2 fail safely on it: they reject
`"version": "1.2"` as an unknown schema version rather than fail open on the unknown fields.

## Schema 1.3 — retained: mutation probes + command-shape lint

Schema `"1.3"` is ADDITIVE over 1.2: every 1.1 and 1.2 rule applies unchanged. It adds one
per-contract field and deterministic lint for three known weak `acceptance_command` shapes:

| Field (1.3) | Level | Mandatory at | Rule |
|---|---|---|---|
| `mutation_probes` | per contract | every `integration_seam: true` contract; every A3/A4 contract | a non-empty JSON array; every entry is an object containing exactly `mutation` (non-empty string) and `expected` (the literal string `"red"`) |

When none of those triggers applies, `mutation_probes` is optional; if present, it is validated to
the same entry shape. The field is not defined by schema 1.1 or 1.2, so either older schema carrying
it is rejected with a diagnostic that requires version 1.3. Existing 1.1 and 1.2 plans without the
field continue to validate exactly as before.

For 1.3 commands, Layer 1 rejects the mechanically recognizable forms demonstrated to fail hollow
implementations: a pipe operator before a gating `&&`; an `echo` that emits the named expected signal
without an immediately preceding `&&`; and an expected-signal `echo` followed by another clause.
This lint is deliberately narrower than a shell parser and does not claim that commands passing it
are semantically strong. Producer red-path execution and independent mutation probing provide that
evidence.

## Schema 1.4 — retained: override follow-up tests + the `overrides` ledger

Schema `"1.4"` is ADDITIVE over 1.3: every 1.1, 1.2, and 1.3 rule applies unchanged. It adds one
OPTIONAL plan-level field — the mechanical record of a human delivery override
(assumption-gated dispatch; full semantics in `policy/plan-critique.md`). A 1.4 block without the
field validates identically to a 1.3 block.

**The conversion rule — a waiver buys evidence-later, never nothing.** When the human waives an
open blocker under the override, that blocker converts to a **recorded assumption plus a REQUIRED
follow-up test attached to the affected task's contract**: a `mutation_probes` entry, a
`negative_cases` entry, or a golden vector the `acceptance_command` runs. A waived blocker with no
follow-up test is a silent drop, and a silent drop is invalid — the ledger below is how the
conversion is recorded so a verifier can mechanically find every debt the waiver created.

| Field (1.4) | Level | Mandatory at | Rule |
|---|---|---|---|
| `overrides` | plan | never — **explicitly optional** | a JSON **array**; every entry is an object containing exactly `blocker`, `assumption`, `followup_test`, and `authorized_turn`, each a non-empty string |

Entry field shapes:

```jsonc
"overrides": [
  {
    "blocker": "C2: probe order unproven for the scan seam",   // the Layer-2 finding being waived — non-empty string
    "assumption": "scan order is stable under the fixture ABI", // the recorded assumption it becomes — non-empty string
    "followup_test": "T3 mutation probe: reverse the scan order on a scratch copy, expected red", // the required test now attached to the affected task's contract — non-empty string
    "authorized_turn": "turn 14 — human confirmation of the override offer" // which genuine human turn authorized the waiver — non-empty string
  }
]
```

A malformed ledger — a non-array `overrides`, a non-object entry, a missing or extra field, an
empty or non-string value — is a Layer-1 defect with stable keyword `override`. The field is not
defined by schema 1.1, 1.2, or 1.3, so any older schema carrying it is rejected with a diagnostic
naming schema 1.4 (keyword `version`). Existing 1.1–1.3 plans without the field continue to
validate exactly as before. The ledger is authored by the model at the override offer — zero human
burden — and the safety floor is out of its reach: floor blockers never appear as `overrides`
entries because they cannot be waived at all.

## Schema 1.5 — retained: necessity tiers (D-19)

Schema `"1.5"` is ADDITIVE over 1.4: every 1.1–1.4 rule applies unchanged. It adds the
requirement-inflation defense — EVERY requirement carries `necessity` ∈ `must` | `nice-to-have` |
`fluff`, a `must` additionally carries a non-empty plain-language `because` naming the concrete
failure without it, and coverage becomes tier-aware (only `must` requirements demand a covering
task; an uncovered nice-to-have is valid deferred scope; a task serving `fluff` is a defect).
Full semantics, the C6 necessity audit, and the `--digest` operator-digest counts:
`policy/plan-critique.md` (Layer-1 rule 15 and the Operator digest section). The
`necessity`/`because` fields are not defined by schemas 1.1–1.4; an older schema carrying them is
rejected naming schema 1.5 (keyword `version`).

*(This section was added retroactively when 1.6 shipped — 1.5 was defined in
`policy/plan-critique.md` and `tools/validate-plan` from v9.4.0, and this file's versioning
header had drifted. The validator was already the authority; the prose now matches it.)*

## Schema 1.6 — retained: the witness pair + whole-command evidence

Schema `"1.6"` is ADDITIVE over 1.5: every 1.1–1.5 rule applies unchanged. It adds one
per-contract field — the machine-checkable summary of the witness pair defined in "The witness
pair (schema 1.6)" above — and a new stable defect keyword `witness`.

| Field (1.6) | Level | Mandatory at | Rule |
|---|---|---|---|
| `witness_pair` | per contract | A2+ (optional below A2; shape/digest-checked when present) | an object containing exactly `red` and `green`; each leg an object containing exactly `tree` (non-empty string; the green leg's tree is the planner-authored witness tree, labeled `witness-tree` in its evidence record), `command_sha256` (the sha256 hex digest of the contract's exact `acceptance_command` string), `exit_code` (a JSON integer — `red` ≠ 0, `green` = 0), and `evidence_path` (non-empty string; the raw transcript beside the plan) |

What Layer 1 checks mechanically: presence at A2+, exact shape, BOTH legs' `command_sha256`
equal to the digest of the contract's own `acceptance_command` (the whole-command rule made
mechanical — a record produced from a partial or drifted command cannot carry the contract's
digest), `red.exit_code != 0`, and `green.exit_code == 0`. A round-3-style impossible command is
rejected at plan time: no honest record can put `exit_code: 0` on its green leg. What Layer 1
does NOT check: the honesty of the witness tree (a C2 judge duty — the critic re-executes both
legs and rejects a green witness whose tree passes with the deliverables stubbed to nothing) and
the existence/content of `evidence_path` (the validator stays a hermetic single-file checker;
judges read the transcripts). The witness pair never weakens the red-path duty: the pair is red
AND green, never green instead.

The `witness_pair` field is not defined by schemas 1.1–1.5; an older schema carrying it is
rejected with a diagnostic naming schema 1.6 (keyword `version`). Existing 1.1–1.5 plans without
the field continue to validate exactly as before.

## Schema 1.7 — the schema of record: the red witness + IMPOSSIBLE-COMMAND verifier duty (D-28)

Schema `"1.7"` is ADDITIVE over 1.6: every 1.1–1.6 rule applies unchanged, EXCEPT that
`witness_pair` is no longer defined — a 1.7 block carrying it is REJECTED, naming the demotion and
pointing at `red_witness` as the migration target (the red leg is retained; the green leg becomes
the verifier's IMPOSSIBLE-COMMAND duty — see "The red witness (schema 1.7)" and "Verification
tiers" above).

| Field (1.7) | Level | Mandatory at | Rule |
|---|---|---|---|
| `red_witness` | per contract | A2+ (optional below A2; shape/digest-checked when present) | an object containing EXACTLY `tree` (non-empty string), `command_sha256` (the sha256 hex digest of the contract's exact `acceptance_command` string), `exit_code` (a JSON integer, must be ≠ 0), and `evidence_path` (non-empty string; the raw transcript beside the plan) |

What Layer 1 checks mechanically: presence at A2+, exact shape, `command_sha256` equal to the
digest of the contract's own `acceptance_command` (the whole-command rule made mechanical — a
record produced from a partial or drifted command cannot carry the contract's digest), and
`exit_code != 0` (an impossible red leg — a command that cannot even fail on a broken scratch — is
as void as a faked green one). What Layer 1 does NOT check: the honesty of the red witness tree (a
C2 judge duty, unchanged from 1.6) and the existence/content of `evidence_path` (the validator
stays a hermetic single-file checker; judges read the transcripts). A `"1.7"` block carrying
`witness_pair` is rejected with keyword `witness`, naming the demotion.

The `red_witness` field is not defined by schemas 1.1–1.6; an older schema carrying it is rejected
with a diagnostic naming schema 1.7 (keyword `version`). Existing 1.1–1.6 plans without the field
continue to validate exactly as before.

### Enforcement locality (schema 1.7, D-29) — a Layer-1 check that a `must` requirement's proof lives where a task actually looks

A full review round can be spent auditing a requirement that is "enforced" in a file no task in the
plan touches — nothing asks the question until a C5 judge notices at Layer 2, after the whole proof
apparatus (contract, mutation probes, red witness) has already been built around it. Schema 1.7 adds
a Layer-1 locality check that catches this at plan time, mechanically, before any of that cost is
spent.

| Field (1.7) | Level | Mandatory at | Rule |
|---|---|---|---|
| `enforced_in` | per requirement | every requirement, every assurance level | a non-empty JSON array of non-empty repo-relative path strings naming where the requirement is enforced |
| `touches` | per task | every task, every assurance level | a JSON array of repo-relative path strings this task modifies (may be empty) |

**The locality check itself:** for every requirement whose `necessity` is `must`, every path in its
`enforced_in` must appear in the `touches` of at least ONE task whose `requirement_ids` include that
requirement's id. The comparison is **exact string element equality — never substring, never
prefix**: a requirement enforced in `src/handler.py` is NOT satisfied by a task touching
`src/handler.py.bak`, even though the latter contains the former as a literal substring. A path
present only in some OTHER, non-covering task's `touches` also does not satisfy the check — the
touching task must be one of the requirement's own covering tasks. `nice-to-have` and `fluff`
requirements are EXEMPT from the locality check, exactly as they are exempt from tier-aware
coverage (D-19): deferred or dropped scope with an unenforced path is not a locality defect.

What Layer 1 checks mechanically: presence and shape of `enforced_in` on every requirement and
`touches` on every task, and the exact-element locality match for every `must` requirement. What
Layer 1 does NOT check: whether the named path is where the requirement's discriminating behavior
actually lives (a C5 judge question — locality proves a task claims to touch the path, not that the
implementation there is correct).

`enforced_in` and `touches` are not defined by schemas 1.1–1.6; an older schema carrying either is
rejected with a diagnostic naming schema 1.7 (keyword `version`). The stable defect keyword for
every presence/shape/locality defect above is `locality`.

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
  "negative_cases": ["parallel writers with injected scheduling jitter still converge to exactly 200"],
  "mutation_probes": [
    {"mutation": "on a scratch copy, replace the atomic increment with read/sleep/write", "expected": "red"}
  ]
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
- **The premature-signal trap.** `check && echo OK && postcheck` prints `OK` before `postcheck` has
  passed. Put the signal last: `check && postcheck && echo OK`. Under schema 1.3, the validator
  rejects a recognizable expected-signal `echo` that is unguarded or non-terminal, and rejects a
  pipe before a gating `&&`.
- General principle: `expected_signal` must be a pattern that **cannot** appear in a failing run. If a
  fail line can print it, the signal is unanchored and the contract is broken.

## Validation

Structural completeness of contracts (non-empty `criteria` + `acceptance_command` + `expected_signal`;
`risk` ⇒ non-empty `negative_cases`; coverage; acyclic deps), schema 1.3 mutation-probe shape and
presence, schema 1.6 witness-pair presence/shape/digest/exit-codes, schema 1.7 red-witness
presence/shape/digest/exit-code, and the known weak command
shapes above are machine-checked by `tools/validate-plan`
against the plan's embedded `json agentfw-plan` block — see `policy/plan-critique.md` Layer 1. Whether
the command is STRONG enough to exercise the lever remains a Layer-2 judge question; passing the
shape lint does not answer it.
