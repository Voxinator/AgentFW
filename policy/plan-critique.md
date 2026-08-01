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
judge context driving the C0–C6 rubric over the plan.

## Layer 1 — deterministic validation (`tools/validate-plan`)

The plan embeds exactly one fenced block opening with ```` ```json agentfw-plan ```` and closing with
```` ``` ````. The validator (stdlib-only, exit-code honest) mechanically checks:

1. The block parses as valid JSON with no duplicate object keys at any level (last-wins duplicate
   keys are rejected as silently-accepted ambiguity), and `version` is present and — in default
   mode — `"1.1"`, `"1.2"`, `"1.3"`, `"1.4"`, `"1.5"`, or `"1.6"`: **schema 1.6 is the schema of record**
   (author new plans against it; 1.1 through 1.5 remain valid for plans that predate it). A `"version": "1"`
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
15. **Schema 1.5 necessity tiers (additive over 1.4):** a `"1.5"` block enforces every 1.1–1.4
    rule above PLUS the requirement-inflation defense (D-19). EVERY requirement carries
    `necessity` ∈ `must` | `nice-to-have` | `fluff` — the operator's three levels: won't work
    without it / nice to have / true fluff. A `must` requirement additionally carries a
    non-empty plain-language `because` naming the concrete failure that occurs without it (an
    unjustified must-claim is the inflation the tier exists to catch). Coverage (rule 6) becomes
    **tier-aware**: only `must` requirements demand a covering task; an uncovered
    `nice-to-have` is VALID deferred scope — the plan block doubles as the next-increment
    ledger (D-18) — and a task serving a `fluff` requirement is a defect: fluff is recorded and
    dropped, never built. A task serving ONLY nice-to-have requirements is reported as a
    non-fatal `scope note:` on PASS (confirm a human pulled that scope into the increment). A
    1.1–1.4 block carrying `necessity`/`because` is rejected naming schema 1.5 (keyword
    `version`). The `--digest` flag prints the machine-derived tier counts the operator digest
    must match (see the Operator digest section below).
16. **Schema 1.6 witness pair (additive over 1.5):** a `"1.6"` block enforces every 1.1–1.5 rule
    above PLUS the witness-pair duty (full semantics:
    `policy/acceptance-contract.md` § The witness pair). At A2+, EVERY contract carries
    `witness_pair` — an object containing exactly `red` and `green`, each leg an object
    containing exactly `tree` (non-empty string), `command_sha256`, `exit_code` (a JSON
    integer), and `evidence_path` (non-empty string). Mechanically enforced: BOTH legs'
    `command_sha256` equal the sha256 hex digest of the contract's exact
    `acceptance_command` string — the whole-command-only evidence rule; a record produced from a
    partial or drifted command cannot carry the contract's digest — `red.exit_code != 0`, and
    `green.exit_code == 0` (an impossible-to-pass command is rejected at plan time: no honest
    record can put exit 0 on its green leg). Below A2 the field is optional but fully checked
    when present. A 1.1–1.5 block carrying `witness_pair` is rejected naming schema 1.6
    (keyword `version`). Layer 1 does not judge witness-tree honesty — that is C2's duty (below).

**Schema 1.3 red-path execution duty:** Layer 1 validates the declared mutation roster and the
three known weak command shapes; it does not execute mutation probes. Before Layer 2 dispatch, the
contract producer MUST execute every proposed `acceptance_command` against a deliberately broken
scratch copy and record the raw non-zero/red result. After implementation, the implementation
producer repeats every contracted probe on scratch copies, and the verifier at the contract's
required tier independently executes every probe on fresh scratch copies. Each probe passes only
when the command exits non-zero and does not emit its terminal success signal. Under schema 1.6
this red run is one leg of the mandatory witness pair: the same producer also records the GREEN
witness — the whole command exiting 0 on a planner-authored witness tree — before Layer-2
dispatch (`policy/acceptance-contract.md` § The witness pair). The pair extends the red-path
duty; it never weakens or replaces it.

Exit 0 + `PASS` on success; on any failure, non-zero exit with messages naming the offending
task/requirement id and defect class. All defects are reported, not just the first.

**Defect-keyword contract (stable, grep-able):** harness-facing Layer-1 diagnostics carry one or
more of the stable defect-class keywords `contract`, `cover`, `cycl`, `negative`, `assurance`,
`empty`, `duplicate`, `tier`, `review`, `failure_surface`, `mutation`, `command`, `version`,
`override`, `necessity`, `witness`. A
diagnostic may carry a general and a specific keyword together; fixtures should key on the most
specific stable keyword. `tier` covers every tier-derivation defect — a
missing/invalid `required_verification_tier`, a missing/invalid `integration_seam` or
`risk_class` derivation input, or a declared tier below the mechanically derived floor; `review`
covers every plan-review-tier defect — a missing/invalid `required_plan_review_tier` or one
declared below its derived floor; `failure_surface` covers `failure_surfaces` shape and enum
defects; `mutation` covers every schema-1.3 `mutation_probes` presence and shape defect;
`command` covers the three schema-1.3 weak acceptance-command shapes; `override` covers every
schema-1.4 `overrides` ledger shape defect; `necessity` covers every schema-1.5 necessity-tier
defect — a missing/invalid `necessity`, a must without `because`, or a task serving fluff
(requirement inflation); `witness` covers every schema-1.6 `witness_pair` defect — a missing or
malformed pair, a leg whose `command_sha256` does not match the contract's `acceptance_command`
digest, or wrong exit codes (red = 0 or green ≠ 0); `empty` includes the task-id
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

**Witness pair replaces the temporal split (1.6):** at plan time the `acceptance_command` still
need not run green on the GREENFIELD tree — the implementation does not exist yet — but that is
no longer a waiver of green evidence entirely: under schema 1.6 the command must carry a recorded
witness pair before Layer-2 dispatch — RED on a deliberately broken scratch (the schema-1.3 duty
above, unchanged) and GREEN on a planner-authored witness tree proving the command CAN pass
(`policy/acceptance-contract.md` § The witness pair). A command that has never been shown able to
pass is rejected at plan time, not discovered impossible after burning Layer-2 passes. At
verification time both its green path — now on the REAL tree — and every contracted red path must
run, and be re-run by the verifier at the required tier.

## Layer 2 — semantic judge (C0–C6 rubric)

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
  MUST attempt an empirical C2 probe for every task. On schema-1.6 contracts the probe duty is
  concrete: the critic MUST re-execute BOTH witness legs itself — red on a scratch it breaks
  itself, green on the plan's witness tree (or one it reconstructs from the record) — and MUST
  reject a green witness whose tree still passes with the deliverables stubbed to nothing (a
  void witness tree). The former "wherever feasible" hatch is SCOPED, not open-ended: when
  re-execution is genuinely infeasible in the critic's environment, the C2 result is tagged
  `reasoned` with the infeasibility stated, and the producer's witness records stand as producer
  evidence only — a silent skip is a policy violation; an infeasibility is named. Every C2 result
  and finding is
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
- **C6 necessity audit (D-19) — the anti-coverage check.** Coverage asks "is anything missing?";
  C6 asks the reverse: **"would the objective demonstrably fail without this?"** For every
  requirement labeled `must`, the judge attempts to name the concrete failure that occurs
  without it — independently of the plan's own `because`, then compares. *Pass:* every
  must-claim survives the attempt. When the judge cannot name a failure (and the `because` does
  not supply a real one), the requirement is **DEMOTED to nice-to-have, not debated**: a
  demotion is a scope correction, never a blocker, costs no Layer-2 pass of its own, and routes
  the requirement to the deferred/next-increment default (D-18). Demote-duty makes cutting
  someone's job — the structural counterweight to a critique gate that otherwise only adds. A
  requirement that ENTERED the plan after its first gate entry claiming `must` is additionally
  surfaced to the operator by the digest (see below): a plan that newly cannot ship without
  something it didn't know it needed is either a genuine discovery or inflation, and that call
  is the human's, made on one sentence.
- **Coverage/completeness** — build the requirement→task matrix: map every `must` requirement
  component to the task + `acceptance_command` that mechanically verifies it. *Pass:* no
  component is verified nowhere (the mocked-here-skipped-there hole). Plus per task: "can a
  wrong implementation still pass this acceptance_command?" Coverage and C6 are deliberate
  opposites: coverage stops under-building the musts; C6 stops over-claiming them.

## Operator digest — the plain-language gate artifact (D-20)

Markers are for the grep; the digest is for the human. Every gate event — Layer-1 result,
Layer-2 verdict, every escalation-menu presentation, every override offer — is accompanied by a
short operator digest with the same standing as the plan block. It is written **for someone who
has never read this policy**: no candidate numbers, no rubric letters, no marker syntax, no
framework vocabulary. Fixed shape, a few sentences each:

1. **What this plan builds**, in one sentence.
2. **Scope by necessity:** how many won't-work-without-it requirements, how many nice-to-haves
   (and whether each is being built now or deferred to the next increment), how many dropped as
   fluff. On schema 1.5 these counts MUST match `validate-plan --digest` output — a digest whose
   numbers differ from the block is fiction, and the mismatch is a defect.
3. **What changed since the last version:** every ADDED requirement gets one line — its tier,
   and its plain-language "because" — and every REMOVED or demoted one likewise. This delta is
   the operator's inflation detector: a new must-have after the first gate pass is called out
   explicitly ("the plan now says it can't ship without something it didn't know it needed —
   your call"). No delta section, no digest.
4. **Cost so far:** review cycles and passes spent, in plain numbers.
5. **What is needed from the operator now:** approve / pull a deferred item in / decide a
   flagged must-claim — one line.

**The speak-twice rule.** Any marker or verdict the operator is expected to act on is
accompanied, in the same message, by one sentence a non-reader of the policy can parse.
Governance output the operator cannot parse is governance that does not govern — the economy
calibration applied to language. The digest never replaces the machine-readable artifacts; it
rides beside them, and where prose and block disagree, the block is authoritative and the
disagreement is itself a defect to fix before dispatch.

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

## Global liveness budget — per objective (D-2)

The 2-pass cap bounds a *cycle*; nothing above bounds the *objective* — and empirically the
treadmill lives exactly there: successively revised plans each hit the cap with novel blockers,
each fresh cycle resetting the only counter that existed. *"Bounded locally and unbounded
operationally"* (NoitaMobileSpec M2→M2A; the drydock failure-routing sessions,
`evaluation/field-report-2026-07-31-drydock-scope-accretion.md`). Review expenditure is therefore
tracked per **objective** — the user's goal, not the plan artifact — across every fresh plan,
rename, and revision:

- **Counters.** `cycles` (each pass of a plan or revision through the gate) and `layer2_passes`
  (each Layer-2 pass, at whatever judge count it ran), cumulative for the objective. After each
  gate cycle emit `[LIVENESS: objective <slug> — cycle n/2, layer2 passes m/4]`.
- **Budget.** 2 cycles / 4 Layer-2 passes for reversible A2 work; A3/A4 work may extend by
  exactly one named cycle via explicit human authorization on the authenticated channel — once,
  not chained.
- **No reset.** A fresh plan for the same objective inherits the counters. The model declares
  objective identity honestly — a renamed, renarrowed, or restructured plan chasing the same goal
  is the *same objective* — and the marker trail records the declaration. (Mechanical objective
  identity is not attempted; the honesty obligation is auditable through the markers.)
- **Budget & ledger inheritance — one ledger per root objective (D-22).** These counters are not
  session state: they live in the durable `<plan>.ledger.json` (D-21 below), keyed by
  **`root_objective`** — the root the work rolls up to, equal to `objective` when the objective
  *is* the root. Every derived objective spends from the **root's** ledger, never a fresh one:
  a sub-objective produced by decomposing the goal, a renamed or re-planned objective, and a
  **cross-runtime resume** (Claude Code ↔ Codex, or a new session of either) all read the root
  ledger, add to it, and write it back. Counters therefore **never reset on decomposition**,
  rename, or a runtime hop — those are exactly the three cheap ways to buy a fresh budget, and
  buying one is treadmill laundering.
  Liveness markers name the **root** slug: `[LIVENESS: objective <root-slug> — cycle n/2, layer2
  passes m/4]`, with the sub-objective named alongside if it differs
  (`<root-slug> (sub: <sub-slug>)`), so the marker trail cannot show a rooted budget under two
  names. A resumed session reads the ledger before emitting its first marker; if the ledger is
  missing or unreadable, say so and re-derive it rather than restarting the count at zero.
  Machine-checked: `evaluation/fixtures/liveness-budget.json` carries a
  `sub_objective_inherits_root_counters` case, and `tools/check-liveness-invariants.py` rejects
  any case that names a `root_objective` while declaring `counters_reset: true`.
- **At exhaustion** emit `[LIVENESS-EXCEEDED: objective <slug>]` and STOP planning: further
  plan/critique cycles for this objective are forbidden. The forced fork — machine-checked as a
  decision table (`evaluation/fixtures/liveness-budget.json`,
  `tools/check-liveness-invariants.py`):
  1. open safety-floor blocker → **halt**, preserving the blocker record;
  2. C5 goal/proof contradiction or unavailable required substrate → **explicit rescope
     proposal**: a smaller or different objective, with the evidence that forced it;
  3. otherwise → **proactively offer the delivery override** — the model presents the full D-1
     offer (safety/assumption split, assumption ledger with follow-up tests, expenditure to
     date, exact dispatch scope) without waiting for a delivery-intent turn — and **halts** if
     the human declines.
  Exhaustion is a human fork: a sleep-mode session halts here exactly as at the 2-pass cap.
- **Gate entry on a resumed objective — reconcile first (D-25).** A resumed A2+ objective's FIRST
  gate event is preceded by the reconciliation duty of
  [recovery.md](recovery.md) § 8: read the ledger, re-derive observed state with mechanical
  probes, and emit `[RECONCILE: objective <slug> — ledger claims X, observed Y — MATCH|MISMATCH]`.
  A MISMATCH is corrected in the ledger before the cycle begins — the counters and
  `tasks_verified` this section reads must be the reconciled ones, not the inherited claims.
- **Scope freeze after Layer 1 — the accretion valve (D-18).** Requirements discovered AFTER a
  plan's Layer-1 PASS — in review, conversation, or design exploration — default to a recorded
  **next-increment ledger** beside the plan, never silently into the gated plan. Folding a
  discovery in is a human choice that reopens the gate and spends a cycle from this budget; the
  default is to ship the gated increment and plan the discoveries against the next one.
  Post-gate scope growth is the leading indicator of livelock — a critique gate functioning as
  a scope generator — and the ledger converts it from plan mass into forward work, the same
  conversion discipline the delivery override applies to waived blockers.

## Delivery ledger, scoreboard & zero-dispatch tripwire (D-21)

The liveness budget counts what review *spends*; nothing above counts what the objective
*delivers*. That asymmetry is the treadmill's hiding place: every cycle is individually lawful,
the budget markers all read in-range, and the objective can burn its entire allowance with zero
workers dispatched and zero tasks verified — because no counter of delivered work exists to
contradict the review counters. D-21 supplies the missing counter, forces it into every gate
message, and trips on the failure mode directly.

- **The durable ledger.** Each objective keeps a JSON record beside its plan named
  `<plan>.ledger.json` (for `PLAN-foo.md`, `PLAN-foo.ledger.json`). It survives replans, renames,
  and runtime switches — it belongs to the objective, not the plan file — and carries exactly:
  `objective` (slug), `root_objective` (the root this rolls up to; equal to `objective` when the
  objective *is* the root, so a renarrowed sub-objective cannot buy fresh counters),
  `cycles`, `layer2_passes`, `workers_dispatched`, `tasks_verified`, and `gate_events` — an
  append-only list with **one entry per gate event, each naming the runtime that wrote it**
  (`{"event": ..., "runtime": ..., "date": ...}`). Both runtimes read and update the same file;
  an entry that does not name its writer makes the trail unauditable. `cycles` and
  `layer2_passes` are the same numbers D-2 tracks — one ledger, not two. Shape reference:
  the `ledger_example` record in `evaluation/fixtures/delivery-ledger.json`.
- **Scoreboard marker duty — at EVERY gate event.** Layer-1 result, Layer-2 verdict, every
  escalation-menu presentation, every override offer, every dispatch decision emits, alongside the
  existing markers:
  `[SCOREBOARD: objective <slug> — musts built b/t · workers dispatched w · verified v · cycle n/2 · passes m/4]`
  Counts come from the ledger, which is appended to in the same breath. A gate event without this
  marker is a defect, not an omission: an uncounted ledger cannot fire the tripwire below.
- **Digest rendering duty.** The D-20 operator digest must render the scoreboard in plain
  language, with every count derived from the ledger and from `validate-plan --digest` — never
  from narration. "Two review cycles so far; nothing has been built yet" is the rendering; "good
  progress on the plan" is not. Where the rendered prose and the ledger disagree, the ledger is
  authoritative and the disagreement is itself a defect to fix before dispatch.
- **The zero-dispatch tripwire.** **Two or more completed gate cycles with `workers_dispatched`
  still 0 immediately force the D-2 exhaustion fork — even when liveness budget remains.** The
  fork is the same three-way one: proactive delivery-override offer, explicit rescope proposal, or
  halt; and it is a human fork, so a sleep-mode session halts here exactly as at the 2-pass cap.
  The tripwire latches: additional cycles never clear it, only dispatched work does. Below the
  threshold, or once any worker has been dispatched, it must not fire — a tripwire that fires on
  healthy delivery would be its own treadmill.
- **Machine-checked.** The decision table lives in `evaluation/fixtures/delivery-ledger.json` and
  is validated by `tools/check-delivery-invariants.py` (stdlib only; `--selftest` proves red/green
  discrimination). A table mapping zero-dispatch-at-threshold to CONTINUE, firing the fork below
  the threshold or after dispatch, treating a missing scoreboard as anything but a defect, or
  carrying a ledger record missing a key or an unattributed gate event, is rejected.

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
