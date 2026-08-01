# AgentFW Changelog

## v9.5.0 (2026-07-31) — RELEASED

The witness-pair release. Field driver: in the drydock failure-routing workstream an
IMPOSSIBLE-to-pass acceptance command survived Layer 1, both Layer-2 judges, and three producer
rounds — red-path calibration only proves a command can FAIL, and an impossible command aces
every red probe. Evidence:
`drydock/.agentfw/evidence/failure-routing/receipt-authority-redesign-2026-07-31/round-3/layer2-pass2/VERDICTS-SUMMARY.md`.

- **Witness pair** (`policy/acceptance-contract.md` § The witness pair; plan schema **1.6**, the
  new schema of record; new defect keyword `witness`): before Layer-2 dispatch every
  `acceptance_command` at A2+ carries a recorded pair — RED on a broken scratch (the schema-1.3
  duty, unchanged) and GREEN on a planner-authored witness tree proving the command CAN pass.
  The green witness claims exactly one thing — "this command CAN pass" — never that work was
  done; verification-time green still runs on the REAL tree. A command never shown able to pass
  is rejected at plan time.
- **Whole-command-only evidence**: each witness leg is one end-to-end run of the ENTIRE command
  string, matched to the contract by `command_sha256`; single-leg runs reported as the whole
  command are inadmissible and mechanically cannot carry the contract's digest.
- **Layer 1 enforcement** (`tools/validate-plan`): `witness_pair` presence at A2+, exact shape,
  digest equality on both legs, `red.exit_code != 0`, `green.exit_code == 0`; pre-1.6 schemas
  carrying the field rejected naming 1.6. Six new fixtures including the round-3 regression
  (`plan-bad-16-round3-contradiction.md`). Pre-1.6 validation proven byte-identical (144
  invocations old-vs-new; sole diff is the precedented moving migrate-pointer in the
  legacy-"1" diagnostic): `evaluation/evidence/witness-pair-upgrade-2026-07-31/`.
- **C2 upgrade** (`policy/plan-critique.md`, both judge prompts): SHOULD→MUST — the critic
  re-executes both witness legs itself and rejects a green witness whose tree passes with the
  deliverables stubbed to nothing; the "wherever feasible" hatch is scoped (named `reasoned`
  infeasibility), never silent. The temporal split is replaced by the witness-pair duty.
- **Drift fix**: `policy/acceptance-contract.md` had no schema-1.5 section and still named 1.4
  the schema of record (validator and plan-critique.md shipped 1.5 in v9.4.0); the section now
  exists and the header matches the validator.

## v9.4.0 (2026-07-31) — RELEASED

The operator release. Five field-driven candidates that make the framework answer to the
operator: respected permission-mode choices, a bounded review budget, frozen post-gate scope,
justified requirements with a judge paid to cut, and plain-language gate output. Full detail:
[RELEASE-NOTES-v9.4.0.md](RELEASE-NOTES-v9.4.0.md); field evidence:
[evaluation/field-report-2026-07-31-drydock-scope-accretion.md](evaluation/field-report-2026-07-31-drydock-scope-accretion.md).

- **D-16 — operator-relaxed enforcement** (`policy/capability-contract.md`): an explicit
  full-access/bypass mode is a standing human lever, not missing substrate — recommend the floor
  once, declare `[FLOOR-RELAXED: operator — <mode>]` (documented residuals only), gate
  destructive/irreversible/outward effects on a genuine human turn, and proceed. Both adapter
  probes rewired; never safety-floor item 5.
- **D-2 — global liveness budget** (`policy/plan-critique.md`): per-objective review budget
  (2 cycles / 4 Layer-2 passes; one named human-authorized extension at A3/A4), no reset on
  renamed same-objective plans, forced fork at exhaustion (halt / rescope / proactive D-1
  offer). Decision table machine-checked by `tools/check-liveness-invariants.py` over
  `evaluation/fixtures/liveness-budget.json`.
- **D-18 — post-gate scope freeze**: requirements discovered after Layer-1 PASS default to a
  next-increment ledger beside the plan; folding one in is a human choice that spends a D-2
  cycle.
- **D-19 — necessity tiers + C6 demote-duty**: plan schema **1.5** (new schema of record) —
  every requirement labeled `must`/`nice-to-have`/`fluff`, musts justified by a plain-language
  `because`, tier-aware coverage, fluff never built (new defect keyword `necessity`); Layer 2
  becomes **C0–C6** with C6 the anti-coverage check (unjustifiable must-claims demoted, not
  debated).
- **D-20 — operator digest**: every gate event carries a plain-language digest (no candidate
  numbers, rubric letters, or marker syntax) whose scope counts must match the new
  `validate-plan --digest` count oracle, with an ADDED/REMOVED delta as the inflation detector;
  plus the speak-twice rule for actionable markers.
- **Proposed, not built:** D-17 cross-substrate consult (field-evidenced); D-7 evidence updated.
- **Release gate** `tools/tests/release-v9.4.sh`: v9.4.0 identity, D-16/D-2/D-18/D-19/D-20
  policy + surfacing facts, schema-1.5 fixture harness incl. the digest oracle, both invariant
  checkers, ledger completeness D-2 + D-14–D-20, plus the existing suites.

**Release evidence:** `tools/tests/release-v9.4.sh` — green. Three input-curated
`agentfw-verifier` passes during the build (D-16; D-2; D-19/D-20), each re-executing acceptance
commands and mutation probes on scratch copies — all PASS.

**Behavioral evidence boundary:** no behavioral-evaluation round was run for v9.4.0; the
machine-checked invariants are the deterministic proof, and field compliance (liveness markers,
C6 demote-duty, digest duty) remains to be measured.

## v9.3.0 (2026-07-21) — RELEASED

The economy-dials release. Adds two independent human-held levers that put the economy calibration
into the runtime. Full detail: [RELEASE-NOTES-v9.3.0.md](RELEASE-NOTES-v9.3.0.md); design of record:
[CANDIDATES.md](CANDIDATES.md) § D-14 + § D-15.

- **D-14 — adaptive dispatch** (`policy/model-dispatch.md`, new): the orchestrator right-sizes each
  subagent's model to its task; casting at or above the adapter-declared **flagship** tier is an
  economic escalation gated on the authenticated human channel; the judge of record is held at or
  above a **floor** tier. **Uniform/Mirror** is the opt-out; absent `model_selection` degrades
  honestly to Uniform. New 11th capability key `model_selection` with validator-enforced
  `tiers/flagship/floor` sub-fields.
- **D-15 — sleep mode** (`policy/assurance-model.md`): a third, unattended interaction posture
  entered by a scoped authenticated human turn; auto-takes the recommended option at non-floor forks
  and halts like a headless run at the floor. The floor gains the flagship escalation; the
  plan-critique cap and the D-1 override stay human-only. Floor-halt is machine-checked by
  `tools/check-posture-invariants.py` over `evaluation/fixtures/sleep-posture.json`.
- **Surfacing**: both adapter SKILLs carry a byte-identical `AGENTFW-SYNC:v9.3` block, gated by
  `tools/check-skill-sync.py`; both kernel blocks gain a one-line pointer.
- **Release gate** `tools/tests/release-v9.3.sh`: 11-key schema on both parser paths, SKILL sync,
  the posture invariant, ledger completeness (`tools/check-candidates.py`), plus the existing
  validator/installer/link suites.

**Release evidence:** `tools/tests/release-v9.3.sh` — green; the SKILL-desync, stale-metadata, and
laundered-posture-fixture scratch mutations each make the gate red.

**Behavioral evidence boundary:** no behavioral-evaluation round was run for v9.3.0. v9.3's
behavioral tier (the treadmill scenario in `evaluation/eval-v9.3-sleep-adaptive.md`) is specified,
not run; the machine-checked decision-table invariant is the deterministic proof.

## v9.2.0 (2026-07-20) — RELEASED

The delivery-invariant release. Adds **D-1: the human delivery override (assumption-gated
dispatch)** — the standard, human-invocable relaxation that ends a plan-review spiral in two
turns without touching the safety floor. Full detail: [RELEASE-NOTES-v9.2.0.md](RELEASE-NOTES-v9.2.0.md);
design provenance: [R92-CANDIDATES.md](R92-CANDIDATES.md) § D-1 + § Maintainer calibration.

- **Policy** (`policy/plan-critique.md`): the escalation menu becomes four options (extend one
  pass / mutation-gated dispatch / **assumption-gated dispatch (human delivery override)** /
  halt, which stays the default); a standalone "Human delivery override" subsection defines the
  trigger duty (after Layer-2 findings exist, a genuine human delivery-intent turn means the
  model MUST NOT start a new plan/critique cycle — it presents the override offer or a
  safety-floor refusal), the six-item never-waivable safety floor, waived-blocker →
  recorded-assumption-plus-follow-up-test conversion, the one-confirmation-turn flow under
  `assurance-model.md` provenance (no nonce ritual for non-destructive work), waived-stays-waived
  per objective, the `[OVERRIDE: …]` audit marker, and the preserved self-clearance prohibition.
  `policy/recovery.md` §7 carries the same menu; `policy/acceptance-contract.md` documents the
  conversion and ledger fields.
- **Schema 1.4** (additive; new schema of record): optional plan-level `overrides` ledger —
  entries exactly `{blocker, assumption, followup_test, authorized_turn}`, all non-empty strings —
  enforced by `tools/validate-plan` with new stable defect keyword `override`; a 1.1/1.2/1.3
  block carrying `overrides` is rejected naming schema 1.4 (fail-safe, keyword `version`).
  Schema 1.1–1.3 behavior unchanged; 5 new fixtures; harness wired.
- **Adapters:** both SKILL.md files surface the four-option menu, trigger duty, and safety floor
  inline — the field report showed the recovery menu living only in an unloaded policy file is a
  recovery menu that does not exist. The override span is byte-identical across both adapters.
- **Build provenance (dogfooded, self-referentially):** the build's own plan gate caught a
  demonstrated-vacuous acceptance command via a null-implementation probe, hit the 2-pass cap
  with that open blocker, escalated to the maintainer, and dispatched under a recorded
  probe-verified relaxation — the exact escalation shape D-1 now standardizes. Two Layer-2
  passes, three workers, independent verifier VERIFIED-WITH-FINDINGS (8/8 contracted mutation
  probes red, 10 off-contract hostile probes clean; its one finding fixed and re-verified).
  Full record: `PLAN-v9.2-d1-override.md`.
- **Deferred (designed, not built):** D-2 global liveness budget, D-3 (delivered for the
  override path only), D-4 drift visibility, D-5 governance-cost instrumentation, D-6
  reversible-prototype-treadmill regression eval — tracked as issues #8–#12.

**Release evidence:** `tools/tests/release-v9.2.sh` (the re-pinned deterministic gate) — release
identity, schema validator fixture harness (incl. the 5 new 1.4 fixtures), installer roundtrip
(28/28), relative links, capability validation through both parser paths, plus new D-1 policy
and adapter-sync assertions, each red-path probed.

**Behavioral evidence boundary:** no golden task, Bonksnake prompt, or behavioral evaluation was
run for v9.2.0. The override's behavioral effectiveness is exactly what D-6 (the
reversible-prototype treadmill) is designed to measure; until it runs, the bounded v9.0.0
behavioral evidence remains the record and D-1's guarantees are the deterministic ones: the
schema, the validator, and the policy/adapter text.

## v9.1.1 (2026-07-20) — RELEASED

Documentation-correctness patch. No policy, schema, validator, or adapter payload changed; the
governance surface is byte-identical to v9.1.0. Full detail:
[RELEASE-NOTES-v9.1.1.md](RELEASE-NOTES-v9.1.1.md).

- **Fixed — Codex upgrade under-restored the installed skill.** `adapters/codex/UPGRADE.md` Case A
  step 3 deleted the skill directory and copied back only `SKILL.md` and `policy/`, while
  `INSTALL.md` Step 2 installs **four** items. An upgrade performed by the book therefore dropped
  `tools/validate-plan` and `capability.yaml`, leaving the installed skill unable to run Layer-1
  plan validation and blind in its §0 capability preflight. Both losses are silent: the skill still
  loads and the gate simply stops firing. Step 3 now restores the complete Step 2 inventory and
  moves the old directory aside instead of deleting it, so a failed copy leaves a rollback.
- **Fixed — the documented verification could not detect that failure.** Step 5 deferred entirely
  to INSTALL.md Step 4, which is behavioral: start a session, ask the model to state its framework,
  confirm markers appear. None of that can go red on a missing validator, because the bootloader
  lives in `AGENTS.md` and an upgrade may never touch it — the model keeps describing A0–A4
  correctly while Layer-1 validation is gone. Step 5 now carries a mechanical inventory check that
  is exit-code gated and emits `INVENTORY_OK` last, verified red against a skill directory built
  the way the old procedure built it.
- **Unaffected: Claude Code.** Its installer is manifest-based and `agentfw-install status` already
  checks the file inventory mechanically. The defect was specific to Codex, which has no installer
  and so relied entirely on the prose being right.

**Field evidence:** `evaluation/field-report-2026-07-20-noita-planning-livelock.md` is published
with this release. It is one field incident, not a calibration result. It documents AgentFW
correctly stopping a real destructive-data mistake and then preventing all implementation through a
planning livelock, and it independently identifies stale-install drift as a contributing cause —
the same distribution failure this patch fixes. Its recommendations (global liveness budget,
separating safety blockers from implementation assumptions, surfacing cap recovery in the adapter,
and failing visibly on policy drift) are **not implemented in v9.1.1** and are candidates for a
later release. Three of its four evidence hashes were reproduced during this release; the fourth
row contained a transcription error and was corrected to the verified value.

**Release evidence:** `tools/tests/release-v9.1.sh` re-pinned to the 9.1.1 identity and green —
validator fixture harness, installer roundtrip (28/28), relative links, and capability validation
through both PyYAML and stdlib-fallback parser paths.

**Behavioral evidence boundary:** no golden task, Bonksnake prompt, or behavioral evaluation was
run for v9.1.1. The bounded n=1 evidence published with v9.0.0 remains the behavioral record and is
not re-presented as fresh evidence.

## v9.1.0 (2026-07-15) — RELEASED

Backward-compatible r9.x evidence-strengthening release. Full detail:
[RELEASE-NOTES-v9.1.0.md](RELEASE-NOTES-v9.1.0.md). All six items in
[R9X-CANDIDATES.md](R9X-CANDIDATES.md) are implemented and verified:

- **C-1 — acceptance-command red paths.** Contract producers must execute deliberately broken
  cases before Layer 2; schema 1.3 also rejects known weak shapes such as a pipe before a gating
  `&&`, an unguarded success signal, or a nonterminal success signal.
- **C-2 — first-class mutation probes.** Additive plan schema **1.3** defines
  `mutation_probes: [{mutation, expected: "red"}]`, requires them at integration seams and A3/A4,
  and makes verifier execution on fresh scratch copies part of the evidence contract. Historical
  schema 1.1 and 1.2 behavior remains supported.
- **C-3 — fixture leak-channel hygiene.** New guidance covers names, contents, comments, committed
  tooling, messages, refs, and reflogs; validation tooling stays outside the artifact under test.
- **C-4 — empirical critic duties.** C2 plan-critic findings are tagged `demonstrated` with live
  output or `reasoned` when execution is infeasible, making the strength of each finding explicit.
- **C-5 — named cap relaxations.** Recovery now defines the standard decision menu after the
  two-pass cap: one named extra pass under bounded conditions, mutation-gated dispatch only for
  mechanically compensated C2-local blockers, or halt.
- **C-6 — resolved command evidence.** Claude Code status preflight records both `command -v` and
  `type` results for `grep`, `sed`, `find`, `md5`, and `sqlite3`, including wrappers/functions and
  missing-command states, in generated active capability evidence.

**Release evidence:** `tools/tests/release-v9.1.sh` gates current version/roadmap/candidate
consistency and provenance presence, then runs the validator fixture harness, the installer
roundtrip suite (28/28), the relative-link checker, and capability validation through both PyYAML
and stdlib-fallback parser paths. Contracted scratch mutations confirm that stale `9.0.0` metadata
and the old README reservation of the deferred adapter for r9.1 both turn the gate red. Raw output
and exit status are in `evidence/release-v9.1.log`.

**Behavioral evidence boundary:** no golden task, Bonksnake prompt, or behavioral evaluation was
run for v9.1.0. The bounded n=1 behavioral evidence published with v9.0.0 is unchanged and is not
presented as fresh v9.1 evidence.

## v9.0.0 (2026-07-15) — RELEASED

Maintainer release decision. r9 ships as `v9.0.0` under the two-tier release bar (`RELEASE-BAR-r9.md`).

- **Deterministic layer machine-verified** (release-blocking, green): installer roundtrip 25/25, `tools/validate-plan` fixture suite (schema 1.2 floors + fail-safe versioning + review-tier emission), capability contracts under both parsers, 57 links resolvable, r8 dirs frozen, hygiene sweep clean.
- **Behavior exercised on Claude Code and Codex**, results linked: `evaluation/results-r9-fixtured-smoke.md`, `results-r9-fixpass2.md`, `results-r9-fixpass3.md`, `results-r9-fixpass4.md` (+ per-pass adversarial audits and an Opus-tier final semantic review on fixpass4).
- **Targeted safety regressions corrected and demonstrated at n=1:** destructive-effect preclassification + informed-authorization (fixpass2), post-blocker protocol / machine-consumed review tier / persisted delegated evidence (fixpass3), and **authorization provenance** (fixpass4) — where the fix inverted the Codex polarity so a labeled-simulated authorization is now refused on both platforms.
- **Behavioral compliance is model- and version-dependent, not guaranteed.** Larger statistical calibration (n≥5, `EVAL-MATRIX-DESIGN.md`) is post-release future work, not a v9.0 blocker.
- Provenance: fix passes gated through the framework's own Plan-Critique Gate (dual judges, hard 2-pass cap, adversarial verification); GitHub issues #3/#4/#5/#6 filed from the evidence and resolved.

## r9 (2026-07-11) — semantic policy + native adapters (DRAFT)

### Context
A cross-model design review of r8 (with GPT 5.6 Sol) surfaced the structural weakness r8 papered over: the governance layer was written *in* Claude Code's vocabulary, so its portability was aspiration, not architecture. r9 splits the framework into a **platform-neutral semantic policy** (`policy/` — names capabilities and invariants, never vendor runtime primitives) and **native adapters** (`adapters/` — compile the policy into each runtime's real controls), and shifts the framing from task classification to **assurance engineering**: how much independent evidence does this change need before it is believed?

### Added
- **`policy/` suite** — the semantic policy core: **assurance model A0–A4** with the 3-question derivation (blast radius/reversibility, defect-escape probability, autonomy/irreversibility); **Acceptance Contract v2** (requirement ids, environment, negative cases, evidence freshness, non-shell evidence path); **two-layer Plan-Critique Gate** — Layer 1 is a real, runnable deterministic validator (`tools/validate-plan`, with positive AND negative fixtures under `tools/fixtures/`), Layer 2 the C0–C5 semantic judge; **capability contracts** (`policy/capability-contract.md` + per-adapter `capability.yaml`, every claim carrying a `verified:` annotation — an unverified true gates as false); **recovery decision model** (failure scope, contamination analysis, retry budget, evidence invalidation, lesson-not-state carry-forward); **anti-patterns** carried forward plus new **Prose-API** (specifying behavior as function signatures no runtime implements) and **Adapter Sprawl** (shipping platform bindings no eval has executed).
- **Adapters.** `adapters/claude-code/` — thin bootloader + skill + agent definitions, with a marker-block installer (`tools/agentfw-install`) whose clean upgrade (including from marker-less r6/r7/r8 installs) and clean uninstall are roundtrip-tested (`tools/tests/install-roundtrip.sh`) to preserve user content byte-for-byte. `adapters/codex/` — doc-grounded: platform capability claims verified against official documentation, annotated per source.
- **Guided profiles.** `profiles/chatgpt-projects.md` (named `profiles/chatgpt.md` before the fix pass below) and `profiles/claude-projects.md` — honest lower-autonomy profiles for runtimes with no enforcement surface; explicitly not adapters.

### Kept deliberately
- **Visible `[ASSURANCE]` / `[CONTEXT HEALTH]` markers as forcing functions** — adapters may hide them from end-user display, but the model must emit them.
- **The input-curation bright line** — a judge of record receives requirements, current state, and acceptance criteria; never the producer's plan, reasoning, or self-assessment.
- **The C0–C5 rubrics** — inherited intact into Layer 2 of the Plan-Critique Gate.
- **The Complexity Accumulation counterweight** — now applied to the framework's *own* machinery: schemas exist only where a real validator consumes them; state/effects are invariants + evidence, never prose-APIs.

### Status
**Draft — not eval-validated (golden-task re-run pending).** r8 remains in `core/` + `references/`, untouched, and stays the validated install until r9 passes evaluation. Eval re-ledger, stated honestly: the last golden-task run (2026-05-29, against r8) is recorded in `evaluation/results-2026-05-29.md` as 5 PASS / 3 PARTIAL / 0 FAIL; under the honest-ledger rule the 3 PARTIALs (test-design issues) are treated as UNTESTED, not passed. An r9 smoke eval has since run (`evaluation/results-2026-07-13.md`, n=1) with no Fail signal in any exercised criterion but a high UNTESTED count — it does not clear the draft bar.

### Fix pass (2026-07-11, post external review)
An adversarial review of the r9 draft (GPT 5.6 Sol; every finding independently re-reproduced against the tree before acceptance) drove eleven hardening fixes, worked as PLAN-r9-fixpass.md:
- **Validator ships with the skill (FR1)** — both installs copy `tools/validate-plan` alongside the installed policy; both SKILL.md files resolve it skill-relative first, repo checkout second. Single source of truth stays in the repo.
- **Validator hardening (FR2)** — mechanically rejects empty A2+ plans, unknown/duplicate/malformed requirement records, and missing `rerunnable` at A2+; hostile fixtures prove each rejection.
- **Manifest-based uninstall (FR3)** — uninstall removes exactly what install recorded; a seeded user `agentfw-custom.md` now survives the roundtrip.
- **Effect-honest settings example (FR4)** — file-dumper and test-runner command allows removed; the example now names the limitation command-name allowlists cannot express.
- **Install routing (FR5)** — `metadata.json` gains `install` → `adapters/<platform>/INSTALL.md`; the r8 installer is relabeled `bootstrap_r8` and `bootstrap.md` carries a two-line r9 notice.
- **Tiered verified states (FR6)** — `verified_producer` / `verified_independent` / `verified_adversarial` with `required_verification_tier` derived from assurance + risk, resolving the producer/independent contradiction.
- **Evidence classes (FR7)** — five classes (behavioral-machine, structural-artifact, source-grounded, expert-judgment, human-authorization) with assurance-tier combinations replace the single mechanical floor for non-code work.
- **ChatGPT profile rescoped (FR8)** — `profiles/chatgpt.md` → `profiles/chatgpt-projects.md`, claims scoped to standard ChatGPT/Projects; ChatGPT Work acknowledged as a different surface (hosted subagents/skills) and the designated r9.1 *adapter* candidate — deferred until both shipped adapters pass evals, per the Adapter Sprawl rule.
- **Capability schema split (FR9)** — `available` (platform offers) vs `configured` (this install activated) with `activation_probe` / `required_for`; both instances migrated honestly (repo-shipped examples say `unknown`, not `true`); claude-code `persistent_state` downgraded to partial (memory/transcripts persist; no atomic task store).
- **A3 escalator narrowed (FR10)** — "autonomous multi-file" alone no longer escalates; escalation requires autonomy PLUS material side effects, unclear seams, elevated defect-escape probability, or absence of rapid human review. Applied in policy and both bootloaders, byte caps held.
- **Marker compression + verifier ceiling (FR11)** — guided profiles may compress the A0 marker to one short clause (never silent); verifier agents gain a standing off-contract hostile-probe instruction, and the policy names contract-bounded verification's ceiling.

### Hardening pass (2026-07-11, post external review #3)
A third adversarial review (GPT 5.6 Sol; all six findings re-reproduced locally before acceptance — one destructive: a tilde-fenced marker block was deleted and NOT restored on uninstall) drove eight hardening requirements, worked as PLAN-r9-hardening.md:
- **CommonMark-aware fence tracking (HR1)** — one shared fence tracker in every scanner: backtick AND tilde fences, opening run length recorded with its character, closes only on a same-character run of at least the opening length, up to 3 leading spaces, info strings allowed; an inner shorter or other-character run (a triple-backtick line inside a four-backtick-opened fence) does not close.
- **Unclosed-fence refusal (HR2)** — an unclosed fence at EOF makes install/upgrade/uninstall REFUSE byte-untouched with a named error; `status` warns without failing. The prior "everything-after-is-fenced" silent semantics are removed.
- **Word-bounded markers (HR3)** — `<!-- AGENTFW:BEGINNING`-style lookalikes are neither treated as markers nor cause refusal; real markers always carry a space after BEGIN/END.
- **Skill/policy sync (HR4)** — claude-code SKILL.md now carries the narrowed conjunctive escalator (autonomy PLUS a compounding risk factor; "autonomous multi-file" alone is gone, with the refactor-is-A2 calibration) and maps test runners to `permissions.ask`, matching the effect-honest `settings.example.json`.
- **Capability state operationalized (HR5)** — the installer packages the adapter's capability.yaml into the installed skill, and `agentfw-install status` writes active-capabilities.yaml with per-rule probe results (each deny signature individually, plus validator/agents/manifest presence); both SKILL.md files gain an explicit A2+ capability preflight (read the packaged files; on Codex run the documented probes manually — no installer there); the codex skill's dangling capability reference now resolves post-install and codex INSTALL.md copies capability.yaml alongside SKILL/policy/validator.
- **Versioned v1.1 contract schema (HR6)** — plan blocks with `"version": "1.1"` additionally require, per contract at A2+, `required_verification_tier` consistent with the assurance (A3 ⇒ independent|adversarial; A4 ⇒ adversarial), a non-empty `environment`, and boolean `rerunnable`; at A3+ a non-empty `evidence`. Version "1" blocks keep v1 rules — historical plans still pass. New hostile fixtures (missing tier, misclassified tier, non-boolean rerunnable); both skills' example blocks upgraded to 1.1; `policy/acceptance-contract.md` and `policy/plan-critique.md` carry the schema of record.
- **Capability schema reconciled + machine-validated (HR7)** — `configured` enum widened to `true | false | partial | unknown | n/a` with one-line definitions; new stdlib `tools/validate-capability` asserts the ten keys, the enums, and per-key `verified:` annotations — passes both live instances, rejects bad fixtures naming the defect.
- **Roundtrip suite extended + scope honesty (HR8)** — Sol's exact repros now roundtrip or refuse correctly (tilde fence, four-backtick fence with inner triple-backtick lines, 3-space-indented fence, unclosed backtick/tilde, BEGINNING lookalike, capability packaging); README states the deliberate r9.1 scope boundary (two native adapters + two guided profiles; ChatGPT Work deferred — not full ChatGPT parity).

### Closure passes + draft pre-release (2026-07-11, external reviews #4–#7)
Four further external review rounds (GPT 5.6 Sol) drove the closing residual fixes; each finding was re-reproduced locally before acceptance:
- **Validator residuals closed.** `agentfw-install status` permission probes now JSON-parse `settings.json` and check each rule individually with canonical-form containment (no substring false positives), first-command truncation for compound commands, and a `settings_schema_valid` diagnostic when the file doesn't parse. `tools/validate-plan` makes the **v1.1 schema mandatory** — version-"1" blocks are accepted only under an explicit `--legacy` provenance mode; **structured tier derivation** computes the required verification tier from `integration_seam`/`risk_class` rather than trusting the declared value alone; a **task-id precheck** rejects plans whose contracts reference undeclared task ids before deeper validation runs. The repo's own plans were migrated to v1.1 and pass the mandatory validator.
- **Skill example sync, permanently mechanical.** The example plan blocks embedded in both adapters' SKILL.md files are validated with `tools/validate-plan` as part of the test suite, so skill/policy drift on the contract schema is caught mechanically, not by review.
- **Final suite state:** install roundtrip **25/25** (the case counter is derived from the executed cases, not hand-maintained); 17 hostile plan fixtures + 3 capability fixtures rejected with the defect named; both capability parser paths exercised; 54 links resolvable.
- **Review #7 verdict: approved for commit sequence — zero open findings.**
- **Released as draft pre-release, tag `r9-draft`.** Outcome evals (golden-task rewrite for the assurance framing + a run against r9) remain the gate to a full r9 release; nothing in these passes constitutes eval validation.

---

## r8 (2026-05-29) — v8 governance refactor + Hermes extraction

### Context
Claude Code 2.1 absorbed AgentFW's *mechanisms* as native runtime primitives — the Workflow tool (`agent()`, `parallel()`, `pipeline()`, judge-panel, resume/journal), Agent subagents, Plan mode + Plan agent, Skills (code-review, verify, security-review, deep-research), MEMORY, the Task system + Cron/schedule/loop, permission modes + allow/deny/ask + hooks + worktrees, and context compaction. The firmware no longer needs to *be* the machinery. r8 reframes AgentFW as a **governance/policy layer over those native primitives**: it decides *whether/when/how-well* to orchestrate; the runtime executes *how*. v8 is **Claude-Code-only** — all cross-model content is dropped. Microsoft 365 Copilot is a footnote-level candidate future target, not built or validated.

### Reframed
- **Firmware = governance layer, not machinery.** `core/harness-core.md` rewritten around the layering: the runtime supplies the harness (Workflow/subagents/Plan mode/Skills/MEMORY/hooks); the firmware supplies the classification, role discipline, verification standard, and restraint the runtime does not supply on its own.
- **Rule 6: PREFER NATIVE PRIMITIVES.** New Critical Rule — don't hand-roll in prose what the runtime does natively; don't double-bookkeep against the platform.
- **Surviving policy layer (what v8 KEEPS):** the Classification Gate (auditable, per-task), role-separation policy + judge **input-curation** (the runtime isolates a subagent's *output* but does not stop you contaminating a judge's *input*), the two Enforcement Gates (Tier-1 verification + Context Health — no native analog), and the anti-pattern judgment layer (esp. Complexity Accumulation — the counterweight to native tooling's bias toward more machinery).

### Added
- **Plan-Critique Gate + Acceptance-Contract spine (validated).** New gate with no native analog: before the first worker dispatch, drive a Workflow judge-panel OVER THE PLAN (input-curated: plan + requirements only), scored against checks C0–C5 + coverage. Each task carries an Acceptance Contract `{criteria, acceptance_command, expected_signal, risk}` whose discriminating lever must be MECHANICALLY REACHABLE by the `acceptance_command`, not merely asserted in prose. Hard 2-pass cap; cap-with-open-blocker escalates to the human via ExitPlanMode.
- **`references/native-primitives.md`** (NEW) — the delegation map (each Claude Code 2.1 primitive → the firmware concept it executes + division of labor) and the operational Plan-Critique recipe (checklist, Acceptance-Contract schema with GOOD/BAD examples, signal-anchoring footguns, convergence/stop policy, illustrative recipe sketch).
- **GT-8** — golden task that proves the harness verifies the *plan* before spending worker budget, and that the Plan-Critique Gate catches its own deepest weakness (a prose lever a wrong implementation passes) rather than rubber-stamping structure.

### Removed
- **Hermes variant extracted to its own project (`agentfw-hermes`) and removed from this repo.** The Gemma-4-on-Hermes-Agent local-orchestration variant and its r7.1–r7.11 probe/campaign work no longer live here. Forward docs (`README.md`, `DESIGN.md`, `metadata.json`, this changelog's top entry) drop Hermes references except an "moved to agentfw-hermes" pointer; historical commits and `archive/` entries are handled separately and left intact.
- **All cross-model content dropped.** The `references/prompt-design.md` "Model-family knobs (non-binding)" subsection (Anthropic-specific Opus tuning) is removed; `compatibility` is now `["claude-code"]` only.

---

## r7.5-campaign-arc (2026-04-21, post-tag) — HOLD

Campaign arc addendum for the Hermes variant. Three follow-up campaigns (r7.6/7.7/7.8) after the `r7.5-hermes-prerelease` tag tested worker-quality interventions; all HOLD. See `variants/hermes/CEILING-FINDING-r7.8.md` for the substrate-ceiling finding, `variants/hermes/campaign-handoff/HANDOFF-post-r7.8.md` for r7.9 options, and `variants/hermes/PROBE-RESULTS-r7.md` §19+ for the full campaign-arc record. No canonical changes to framework; updates scoped under `variants/hermes/`.

---

## r7.5 (2026-04-19) — Hermes variant pre-release — HOLD-narrow

### Context
r7.4 landed β-fuse (SHIP-WITH-CAVEAT for the dispatch layer) with two documented residuals: a dense `todo`/`search_files` first-tool escape on 3/13 measured structured/LH trials, and a parent-side SIGTERM mis-attribution pattern that caused wrapper-reported COMPLIANT verdicts to diverge from on-disk truth on long trials. r7.5 set out to (a) close the dense escape via a Hermes-side turn-0 toolset restriction hook, (b) harden the wrapper/analyzer against SIGTERM mis-attribution with a content-match recovery path and a new `ERROR:WRONG_SESSION` verdict, (c) probe a full 20-trial MoE matrix under the tightened β-fuse v2.1, and (d) for the first time measure **worker quality** — a 5-criterion rubric (COMPLETION / CORRECTNESS / HONESTY / TURN_EFFICIENCY / NO_SIDE_EFFECTS) scored against each child session's persisted transcript. Ship verdict per `ARTIFACT-r7.5-SHIP-judge-verdict.md`: **HOLD-narrow**. This release publishes the substantial progress as a pre-release rather than as production.

### Added
- **`variants/hermes/HERMES-variantF.md` remains the active harness prompt** (md5 `01c0e77bb2a6e753a8ea9063784a25e0`) and `variants/hermes/delegate_worker_v2.py` remains the β-fuse dispatch tool. Both unchanged from r7.4.
- **r7.5-A1 turn-0 toolset restriction hook** — new method `_resolve_tools_for_turn_r75a` in `run_agent.py`. When a session's `enabled_toolsets` is exactly `{delegation, todo, clarify, file_readonly}` and no prior assistant turn has called `delegate_worker_v2`, the tool list sent to the LLM is filtered to `{delegate_worker_v2, clarify}`. Composition-scoped — any other toolset composition bypasses the hook entirely, so canonical flows (cron, hermes-cli, hermes-telegram) are side-effect-free. Staged via `probe-variantG-stage.sh` on top of variantF. See `ARTIFACT-r7.5-A1-impl-notes.md`.
- **r7.5-B1 wrapper hardening** — `probe-variantG-wrapper.sh` adds `TIMEOUT_PER_TURN` env override (default 900s), base64 `--expected-prompt-prefix-b64` SSH-safe transport for the content-match prefix, and `ERROR:WRONG_SESSION` handling. Session-ID fallback recovery now content-matches a candidate session's `messages[0]` against the original prompt's first 80 bytes before accepting it as parent.
- **r7.5-B2 analyzer hardening** — `probe-variantG-check.py` adds `--expected-prompt-prefix` (raw) and `--expected-prompt-prefix-b64` (SSH-safe) flags plus new `ERROR:WRONG_SESSION` verdict with a structured diagnostic JSON (`reason` ∈ {`empty_messages`, `no_user_message`, `first_user_content_prefix_mismatch`}). Gate runs BEFORE `NO_ASSISTANT_RESPONSE` / `NO_MARKER` so mis-attached child sessions are classified as wrapper problems rather than model compliance violations.
- **`probe-omlx-health-check.sh`** — Mac-side oMLX health probe (free memory, swap, loaded-model count, default-model identity). Reads `/health` endpoint; callable from VM via SSH.
- **r7.5 worker-quality rubric and 20-trial probe** — `ARTIFACT-r7.5-F1-judge-brief.md` defines the 5-criterion rubric; `ARTIFACT-r7.5-F2-probe-results.md` captures the 20-trial MoE matrix (T4×5, T5×5, T6×5, T10×5). Per-trial verdicts at `ARTIFACT-r7.5-worker-quality-trial-{01..20}.md`.
- **r7.5 ship judge** — `ARTIFACT-r7.5-SHIP-judge-verdict.md` applies both pre-committed thresholds (dispatch ≥17/20, worker quality ≥15/20) and issues HOLD-narrow with a 7-trial fresh-context sample verification (7/7 agreement with F.2 aggregate).
- **Pre-release documentation** — `RELEASE-NOTES-r7.5-hermes-prerelease.md` (top-level), `variants/hermes/INSTALL.md` (new authoritative install procedure, supersedes frozen `IMPLEMENTATION.md`), `variants/hermes/DEPENDENCIES.md` (tested versions), refreshed `variants/hermes/DESIGN.md` (variantF + turn-0 architecture; prior version described r7 variantD), extended `variants/hermes/NEXT-STEPS.md` (r7.6 agenda + operator decision tree).

### Probe results (MoE, 20 trials)
Pre-committed thresholds: dispatch first-attempt strict PASS ≥17/20, worker-quality 5-criterion PASS ≥15/20, LOST ≤3/20. BOTH must hold for SHIP.

| Gate | Threshold | Actual | Margin | Verdict |
|------|-----------|--------|--------|---------|
| Dispatch first-attempt strict PASS | ≥17/20 | 16/20 | −1 | FAIL |
| Worker quality PASS (5-criterion) | ≥15/20 | 3/20 | −12 | FAIL |
| LOST limit | ≤3/20 | 0/20 | +3 slack | PASS |
| VM canonical at return | Required | Yes | — | PASS |

Two FAILs → HOLD. Dispatch margin context: r7.4 MoE baseline was 17/20 with 3 empty-first-turn misses; r7.5 at 16/20 with 4 empty-first-turn misses is within Poisson variance on the same task matrix. Identical failure signature (`messages[1]` empty, recovery at `messages[3]`) suggests MoE quirk, not induced regression. Worker-quality margin (−12) is not borderline; even with a plausible 1-trial sample-error flip the aggregate would be 4/20.

### Worker-quality failure modes
1. **Turn-budget exhaustion on `search_files` thrash (7 trials).** Children searching unknown cwd for hypothetical files, spinning until budget.
2. **Mid-tool SIGTERM truncation (8 trials).** Wrapper-level artifact; Tier-1 parent-side fix shipped, child-side SIGTERM is the r7.6 mirror problem.
3. **Malformed pseudo-tool-call text emission (3 trials).** 26B MoE emits `call:X{args}<tool_call|>` in content rather than structured `tool_calls`. No actual write occurs.
4. **Fabricated completion claims (2 T10 trials).** Summary claims "Created X" / "Generated Y" with zero `write_file` / `patch` / `terminal` calls in the transcript. Honesty failure.

None of these are failure modes a better dispatch contract can fix — they are child-execution and child-tool-formatting problems orthogonal to β-fuse. Tracked as r7.6 scope.

### Ship status
**r7.5 verdict:** HOLD-narrow. Dispatch missed by 1/20 (within r7.4 variance, same failure signature). Worker quality missed by 12/20 on an orthogonal child-execution surface. β-fuse dispatch thesis INTACT: v2-adoption 20/20 (100%); the 4 first-attempt misses recovered cleanly via the correction loop.

**r7.4 variantF verdict (SHIP-WITH-CAVEAT) NOT RETROACTIVELY WEAKENED.** Per the r7.5 ship judge Part 5: the r7.4 ship decision for the dispatch layer stands. Worker quality wasn't measured in r7.4; r7.5's dispatch numbers are within r7.4 variance; gates should move forward, not backward. The operator may canonicalize variantF on the basis of r7.4's SHIP-WITH-CAVEAT independently of r7.5's worker-quality HOLD — that is an operator call, not a judge call. See `RELEASE-NOTES-r7.5-hermes-prerelease.md` for the decision tree.

### r7.6 scope (deferred)
1. Child-session contract scaffolding (HERMES-WORKER.md analog) — addresses fabrication + turn discipline
2. Child-toolset restriction (analogous to r7.5 turn-0 hook, applied to child spawn) — addresses search-thrash
3. Turn-budget tuning for long-horizon children — addresses T6/T10 budget exhaustion
4. Anti-fabrication post-trial guardrail — addresses HONESTY failures on T10
5. Pseudo-tool-call detection — addresses the 3 malformed-format trials
6. Child-side SIGTERM research (Tier-3 upstream Hermes handler) — addresses the 8 truncation trials

### Probe-fidelity improvements landed
- **Parent SIGTERM mis-attribution eliminated.** Tier-1 content-match recovery + `ERROR:WRONG_SESSION` verdict ensures a child session mis-identified as parent (because the parent's `session_id:` stdout was lost to SIGTERM) is correctly classified as a wrapper-attribution bug rather than a model-compliance violation.
- **Ship judge sample verification.** 7-trial stratified cold re-judgment against raw child session JSONs on VM; 7/7 agreement with F.2 aggregate across all four failure-mode categories + both PASS exemplars.
- **Analyzer stylistic parity preserved.** `probe-variantG-check.py` uses the same manual argv parsing pattern as variantF/variantE — no argparse introduction; no verdict-string changes; all existing verdicts unchanged.

### Files added
- `probe-variantG-stage.sh`, `probe-variantG-wrapper.sh`, `probe-variantG-check.py`
- `probe-omlx-health-check.sh`
- `ARTIFACT-r7.5-A1-impl-notes.md`, `ARTIFACT-r7.5-A2-judge-verdict.md`
- `ARTIFACT-r7.5-B1-impl-notes.md`, `ARTIFACT-r7.5-B2-impl-notes.md`
- `ARTIFACT-r7.5-F1-judge-brief.md`, `ARTIFACT-r7.5-F2-probe-results.md`
- `ARTIFACT-r7.5-phase3-smoke-verdict.md`
- `ARTIFACT-r7.5-worker-quality-trial-{01..20}.md` (20 per-trial verdicts)
- `ARTIFACT-r7.5-SHIP-judge-verdict.md`
- `ARTIFACT-r7.4-sigterm-research.md` (Tier-1/2/3 SIGTERM design work completed during r7.5)
- `RELEASE-NOTES-r7.5-hermes-prerelease.md`
- `variants/hermes/INSTALL.md`, `variants/hermes/DEPENDENCIES.md`

### Files modified (scope audit)
Changes contained to `variants/hermes/`, top-level probe infrastructure, top-level documentation (`README.md`, `CHANGELOG.md`, `metadata.json`, `RELEASE-NOTES-r7.5-hermes-prerelease.md`), and Hermes VM install (`run_agent.py` patched additively with backup). Core (`core/`, `references/`, `playbooks/`, `templates/`) and non-Hermes variants (`claude-code`, `claude-projects`, `generic`) unchanged and byte-identical. No tripwire mutations across any r7.5 probe run. VM returned to canonical (HERMES.md md5 `0780c232a6cb52e13e432261f0d68ad9`) at session end.

---

## r7.4 (2026-04-19) — β-fuse structural dispatch (Hermes Variant F) — SHIP-WITH-CAVEAT

### Context
r7.3 left us with failing first-attempt dispatch thresholds (dense 1/15, MoE 1/15) and a stacked remediation diagnosis that identified Layer-3 β-fuse as the structural backstop: move the classification from a text-marker contract into a required argument on a new `delegate_worker_v2` tool, so the model cannot satisfy the contract without actually dispatching. r7.4 implements that design end-to-end, resolves the Priority-1 probe-fidelity blocker from r7.3, and runs a split-leg probe (MoE 20 trials complete + dense gap-fill) culminating in a ship-decision judge. Verdict per `ARTIFACT-r7.4-ship-judge-verdict-v2.md`: **SHIP-WITH-CAVEAT**.

### Added
- **`variants/hermes/delegate_worker_v2.py`** — ship tool: enforces `classification` (enum `one-shot` | `structured` | `long-horizon`), `justification` (≥30 chars, server-side), and `goal` (conditionally required for structured/long-horizon). Schema description leads with the imperative "Call this tool as your FIRST action on every task" per ζ's R1 high-attention-slot finding. Side-by-side with v1: both callable, HERMES teaches v2 exclusively, v1 emits a `deprecation_warning` in its response. See `ARTIFACT-impl-3-beta-fuse-spec.md` and `ARTIFACT-r7.4-phase-a-impl-notes.md`.
- **`variants/hermes/HERMES-variantF.md`** — sibling variant teaching `delegate_worker_v2` exclusively, with classification enforced as a tool-call argument rather than a text marker. md5 `01c0e77bb2a6e753a8ea9063784a25e0`. Variants D and E preserved as siblings.
- **`probe-variantF-check.py`**, **`probe-variantF-wrapper.sh`**, **`probe-variantF-stage.sh`** — new probe harness reading classification from `tool_calls[0].function.arguments` directly. Filters out runtime-rejected hallucinated tool names (P1 analyzer fix applied) so first-tool classification reflects what the gate actually bound, not what the model emitted before rejection.
- **`ARTIFACT-r7.4-p1-terminal-binding.md`** + **`ARTIFACT-r7.4-p1-judge-verdict.md`** — P1 resolution artifacts proving the r7.3 "terminal" leak was not a gate bypass.
- **`ARTIFACT-r7.4-phase-a-impl-notes.md`** — v2 tool implementation notes (schema, handler, registry, backwards-compat).
- **`ARTIFACT-r7.4-phase-c-judge-verdict.md`** — mid-probe judge verdict.
- **`ARTIFACT-r7.4-phase-d-moe-results.md`** — MoE leg, 20 trials complete.
- **`ARTIFACT-r7.4-phase-d-dense-results.md`** + **`ARTIFACT-r7.4-phase-d-dense-gapfill.md`** — dense leg (13 measured, 7 unmeasured) + gap-fill covering T5 runs 1–5 and T6 runs 1–2.
- **`ARTIFACT-r7.4-ship-judge-verdict.md`** and **v2** — ship-decision judge (v2 is authoritative; v1 is the HOLD verdict that triggered the gap-fill).

### P1 resolution (r7.3 blocker cleared)
The r7.3 "`terminal` bound outside the toolset gate" issue was **not** a gate bypass. Direct probes against the VM confirmed the runtime binds exactly 6 tools (`clarify, delegate_task, delegate_worker, read_file, search_files, todo`) under `TOOLSETS=delegation,todo,clarify,file_readonly` on both models. In all 4 r7.3 "leak" trials, the model *hallucinated* a `terminal` tool name; the runtime rejected the call with `"Tool 'terminal' does not exist"`; no terminal command executed; tripwires stayed clean across 34 trials. The artifact is a 10-line analyzer fix in `probe-variantE-check.py` (and now native in `probe-variantF-check.py`): filter tool calls whose name is not in the session's bound `tools` array, or skip calls immediately followed by a `"Tool '…' does not exist"` tool message. Layer-1 structural property held on every trial. See `ARTIFACT-r7.4-p1-terminal-binding.md` + judge verdict.

### Probe results (ship judge v2, authoritative)
Pre-committed thresholds: dense ≥14/20 first-attempt strict; MoE ≥8/20; v2-adoption on compliant ≥95%; one-shot regression 0.

| Metric | Dense | MoE | Threshold | Verdict |
|--------|-------|-----|-----------|---------|
| Structured/LH first-attempt PASS (absolute) | 10/20 (7 unmeasured) | 17/20 | Dense ≥14, MoE ≥8 | Dense BELOW absolute; MoE PASS >2× margin |
| Structured/LH first-attempt PASS (rate on measured) | 10/13 = 77% | 17/20 = 85% | — | Above 70% / 40% proportional |
| v2-adoption on compliant | 10/10 = 100% | 20/20 eventual / 17/20 strict | ≥95% | PASS (MoE ambiguous on strict) |
| One-shot regression fails | 0/6 | 0/6 | 0 | PASS |

MoE cleared its threshold cleanly with >2× margin; dense is below absolute on the 20-trial scale but the 77% measured rate on 13 independent observations (spanning T4 refactor, T5 bug-hunt, T6 long-horizon) projects to ~15–16/20 under full coverage.

### Key finding — `todo` / `search_files` escape on dense
3/13 measured dense structured/LH trials (T5 run 1, T5 run 2, T6 run 1) bypassed `delegate_worker_v2` by calling `todo` (2×) or `search_files` (1×) as their first tool, then exhausting the retry loop without ever calling v2 (47, 47, 26 messages respectively). These tools are legitimately bound in the current probe TOOLSETS. **β-fuse is necessary-but-not-sufficient under a wide toolset:** it forces classification-as-payload *when the model chooses the delegation path*, but does not force the delegation path itself. MoE shows 0/20 such escapes on the same toolset, confirming the pattern is a dense-specific behavioral pull, not a harness defect. Closure path is a v2.1 toolset-scoping refinement (turn-0 bind only `delegation,clarify`; grant full toolset after v2 is called). Wrapper-layer retry loop still detects and reports these as violations, so defense-in-depth holds.

### Ship status
**SHIP-WITH-CAVEAT** per `ARTIFACT-r7.4-ship-judge-verdict-v2.md`. Documented caveats:
1. Dense absolute count did not strictly clear ≥14/20 on measured data (10/20 measured PASS, 3 FAIL, 7 unmeasured). Proportional rate 77% clears 70% proportional equivalent, but this is a softer reading than the pre-committed threshold.
2. Dense 3/13 exhibit `todo`/`search_files` first-tool-escape. v2.1 should tighten the classification-gate toolset.
3. MoE strict `v2_was_first_tool` is 85% (below the 95% headline); eventual-compliance is 100%.

Productionization steps (canonical HERMES.md swap on VM, cron-safety confirmation, Monday 8am Jira cron monitoring, stage script kept for rollback) are pending operator authorization. Variant F artifacts are staged and ready; VM remains on canonical HERMES.md (md5 `0780c232…`) at session end.

### r7.3 → r7.4 lift
First-attempt dispatch on structured/LH:
- **Dense:** 1/15 (6.7%) → 10/13 (77%) measured = **11.5× lift**.
- **MoE:** 1/15 (6.7%) → 17/20 (85%) = **12.7× lift** (≈17× at the margin stated in the ship verdict).
- **One-shot regression:** 4/4 → 12/12 intact; β-fuse does not force structured dispatch on trivial tasks.

### Cross-model integrity
Changes contained to `variants/hermes/`, top-level probe infrastructure, and Hermes VM install (side-by-side `delegate_worker_v2` registration). Core (`core/`, `references/`, `playbooks/`, `templates/`) and non-Hermes variants (`claude-code`, `claude-projects`, `generic`) unchanged and byte-identical. No tripwire mutations across any r7.4 probe run.

### Files added
- `variants/hermes/delegate_worker_v2.py`
- `variants/hermes/HERMES-variantF.md`
- `probe-variantF-check.py`, `probe-variantF-wrapper.sh`, `probe-variantF-stage.sh`
- `ARTIFACT-r7.4-p1-terminal-binding.md`, `ARTIFACT-r7.4-p1-judge-verdict.md`
- `ARTIFACT-r7.4-phase-a-impl-notes.md`, `ARTIFACT-r7.4-phase-c-judge-verdict.md`
- `ARTIFACT-r7.4-phase-d-moe-results.md`, `ARTIFACT-r7.4-phase-d-dense-results.md`, `ARTIFACT-r7.4-phase-d-dense-gapfill.md`
- `ARTIFACT-r7.4-ship-judge-verdict.md` (HOLD v1) + `ARTIFACT-r7.4-ship-judge-verdict-v2.md` (SHIP-WITH-CAVEAT, authoritative)

### Files modified (scope audit)
Contained to `variants/hermes/` and top-level probe infrastructure. VM-side `delegate_worker_v2` is additive (v1 retained). No edits to `core/`, `references/`, `playbooks/`, `templates/`, or non-Hermes variants.

---

## r7.3 (2026-04-18 → 2026-04-19) — Layer 1+2 remediation attempt (FAILED thresholds)

### Context
Diagnostic from r7.2 plus a 7-worker remediation playbook (Judge θ) identified four compounding causes of low first-attempt dispatch on Gemma: (1) HERMES.md sits in the prompt's attention valley, (2) `delegate_worker` is drowned by an adjacent `delegate_task` schema 3.5x larger and competing read/orient primitives, (3) HERMES.md and the wrapper correction text both contain five legitimate escape clauses inviting re-classify-to-one-shot rationalization, (4) dense and MoE fail at mechanically different decode steps (dense role-collapses to read/orient tools; MoE goes chatbot-mode and emits no tool call). Five layered remediations were designed; this release attempted Layers 1+2 stacked in a single 34-trial probe (15 dense structured/LH + 15 MoE structured/LH + 4 one-shot regression).

### Added
- **`file_readonly` toolset** on the Hermes VM — exposes only `read_file` and `search_files`. Additive, no removal of existing toolsets. Enables Layer 1 (toolset restriction to `delegation,todo,clarify,file_readonly`).
- **`probe-variantE-wrapper.sh` `TOOLSETS` env-var passthrough** — defaults to no `-t` flag if unset, preserves prior probe behaviour.
- **`variants/hermes/HERMES-variantE.md`** — escape-hatch-stripped variant of D. Wrapper correction text tightened in parallel. Sibling file; D unchanged.
- **`variants/hermes/delegate_worker.py`** — unchanged from r7 (no Layer 3 changes shipped).
- **`ARTIFACT-impl-3-beta-fuse-spec.md`** — Layer 3 spec for `delegate_worker_v2` with `classification` + `justification` + `goal` as required args. Design only, not implemented.
- **`ARTIFACT-impl-4-soul-restructure.md`** — Option A1/A2/B/C analysis for SOUL.md / USER.md / MEMORY.md restructuring with 8 operator-decision questions gating implementation.
- **7-worker diagnostic + design swarm artifacts** (workers α through η) plus Judge θ remediation playbook.
- **Wave-2 verifier judge artifact** confirming worker-claim spot-checks against source.
- **34-trial L1+L2 stacked probe** (`ARTIFACT-probe-r7.3-l12-results.md`) with separate analyzer artifact (judge shielding maintained).

### Outcome (FAILED ship thresholds)
Thresholds pre-committed by Judge θ §9 before the probe ran:

| Threshold | Target | Observed | Verdict |
|-----------|--------|----------|---------|
| Dense first-attempt strict dispatch (T4+T6+T9, N=15) | ≥ 7/15 | **1/15** | **FAIL** |
| MoE first-attempt strict dispatch (T4+T6+T9, N=15) | ≥ 4/15 | **1/15** | **FAIL** |
| `tool_not_found` events across 30 structured/LH trials | ≤ 3/30 | 0/30 | PASS |
| Tripwire mutations across 30 trials | 0 | 0 | PASS |
| One-shot regression COMPLIANT (4 trials) | 4/4 | 4/4 | PASS |

The two failing thresholds are the central ones; both fail categorically, not at the edge. Dense final dispatch (any-time) did improve from 40% (r7.2) to 87%, but that is a wrapper-rescue win, not a model-behavior win — the harness goal is first-attempt compliance.

### New failure modes discovered
- **`role-collapse-via-todo`** (11/30 trials, 37%) — closing the `search_files` door pushed the model to use `todo` as the orient-first escape. Plumbing-leak: prompt-language remediation displaces escape behavior rather than eliminating it.
- **T4 dense regressed under L2.** L1-only partial data showed 5/5 first-attempt on T4; L1+L2 dropped to 1/5. The stricter language was actively counterproductive on the easiest case — best hypothesis is that escape-hatch removal made one-shot dispatch feel higher-risk and pushed dense toward "be careful, orient first" behavior.
- **`chatbot-mode` persisted on MoE** (4/15 MoE trials with `NO_TOOL_CALLS` in first assistant). Predicted by worker β; L1+L2 alone does not address it — requires the Layer 3 β-fuse.

### Probe-fidelity issue (BLOCKER for further work)
5 dense trials called `terminal` despite `terminal` not being in `TOOLSETS=delegation,todo,clarify,file_readonly`. Either Hermes binds `terminal` outside the toolset gate, or the wrapper `-t` flag isn't actually restricting at runtime. Until resolved, all Layer-1 numbers are suspect — including the L1-only T4 5/5 result that looked like a win. Investigate before the next probe runs.

### Recommended next steps
1. Investigate `terminal` out-of-band binding (~30 min).
2. Implement Layer 3 β-fuse per `ARTIFACT-impl-3-beta-fuse-spec.md` (~5 hours), re-probe MoE leg.
3. Implement IMPL-4 Option A2 (prompt-builder slot reorder so dispatch instructions arrive before tool descriptions; ~1 hour, gated on operator answers to the 8 questions in IMPL-4).
4. Do not revert L1 or L2 — each contributes (zero `tool_not_found`, intact one-shot regression, lifted final-dispatch). Removing them does not improve first-attempt and likely worsens wrapper-rescue.

### Withdrawn
- Variant E ship-candidate status (formally withdrawn 2026-04-18 per Step A re-tally; see r7.2 entry).

### Files restored at session end (cron safety)
HERMES.md restored to canonical (md5 `0780c232…`) on the VM. HERMES-variantE.md preserved as a sibling for next-session continuation. The `file_readonly` toolset left in `toolsets.py` (additive, harmless under default invocation). All 3 tripwires verified clean.

### Files added
- `variants/hermes/HERMES-variantE.md`
- `ARTIFACT-impl-3-beta-fuse-spec.md`
- `ARTIFACT-impl-4-soul-restructure.md`
- `ARTIFACT-probe-r7.3-l12-results.md` and analyzer outputs
- 7 worker diagnostic artifacts (α–η) + Judge θ playbook + Wave-2 verifier artifact
- `probe-variantE-wrapper.sh` updated with `TOOLSETS` env-var passthrough

### Files modified (scope audit)
Changes contained to `variants/hermes/`, top-level probe infrastructure, and Hermes VM install (`toolsets.py`). Core (`core/`, `references/`, `playbooks/`, `templates/`) and non-Hermes variants unchanged.

---

## r7.2 (2026-04-18) — Dense vs MoE A/B + drift investigation

### Context
Tested `gemma-4-26B-A4B-it-MLX-8bit` (MoE, 4B-active) head-to-head against `gemma-4-31b-it-4bit` (dense) on the Hermes harness. A drift investigation was triggered when the dense baseline appeared to regress from r7's reported 3/5 first-attempt to 1/5 — the gap turned out to be a measurement artifact: r7's wrapper had been counting stdout `🔀 preparing delegate_worker…` markers as dispatches even when the parent session JSON was SIGTERM-truncated before persisting the call. Under a strict on-disk persisted-JSON criterion, r7's true first-attempt dispatch was 0/5 (worse than r7.2's 1/5), and the perceived drift dissolves once measurement is harmonized.

### Added
- **Pre-harness baseline check for MoE** — 3 sanity prompts covering native + custom tool-call format. Passed.
- **r7.2 dense v1 + v2 trial sets** (10 trials each; v2 with the fixed wrapper).
- **r7.2 MoE trial set** (10 trials with MoE-specific failure-mode classification).
- **5-worker drift root-cause investigation** — α (oMLX state), β (session diff), γ (contamination), δ (sampling), ε (r7-vs-r7.2 byte diff) plus a synthesis judge.
- **Step A strict on-disk re-tally** (`ARTIFACT-drift-step-a-retally.md`) — proved r7's 3/5 first-attempt was a wrapper-counted artifact; true r7 strict first-attempt was 0/5.

### Findings
- **Dense v2 strict on-disk:** 1/5 first-attempt, 2/5 final dispatch on structured/LH (Trials 4 + 10).
- **MoE strict on-disk:** 0/5 first-attempt, **5/5 final** (every structured/LH trial retry-rescued).
- **Speed:** MoE ~2x faster than dense on median wall-clock (132s vs 258s); MoE total run 27 min vs dense 61 min for 10 trials.
- **MoE distinct failure mode (β finding):** chatbot-mode termination — emits classification + justification then no tool call (3/5 of MoE structured/LH msg1s).
- **Dense distinct failure mode:** role-collapse — always emits a tool, often a wrong one (`search_files`, `read_file`, or worse, mutating tools `write_file` / `skill_manage` before any dispatch).
- **Tripwire safety:** MoE kept all three tripwires clean across 10 trials; dense mutated SKILL.md on Trial 9 via main-session `skill_manage` (role-collapse with side-effect).
- **Cosmetic native-format token leakage** on MoE (`<|channel>`, `<channel|>`, `<tool_call|>` raw tokens) in 7/10 parent sessions — non-load-bearing in 9/10, but caused one Trial 6 child to abort.
- **"Drift" between r7 and r7.2 was illusory** — measurement artifact, not behavioral regression.

### Wrapper bug fixes
- `TIMEOUT_PER_TURN` raised 300s → 900s (dense was hitting the wall on first structured/LH turns).
- Session-ID fallback recovery added for the case where SIGTERM kills hermes before the `session_id:` line reaches stdout.
- `MODEL_MISMATCH` check now reads the session JSON `model` field directly rather than tail-grepping the oMLX log (the prior method produced false positives from log scrolling). Zero false positives in v2 vs. four in v1.

### Files added
- `ARTIFACT-probe-r7.2-dense-v2.md` — dense leg with fixed wrapper (supersedes v1)
- `ARTIFACT-probe-r7.2-moe.md` — MoE leg with MoE-specific failure-mode classification
- `ARTIFACT-drift-step-a-retally.md` — strict on-disk re-tally proving the r7 measurement artifact
- 5 drift-investigation worker artifacts (α–ε) + synthesis judge
- Updated `probe-variantE-wrapper.sh` (TIMEOUT, fallback, MM-check fixes)
- `variants/hermes/PROBE-RESULTS-r7.md` revisions to be applied per the next entry

### r7 verdict revision
The r7 ship-candidate framing for Variant E rested on inflated numbers driven by stdout-counted dispatches that never persisted to disk. **Withdraw the ship-candidate status.** Under the strict persisted-JSON metric used for r7.2+, r7 underperforms r7.2 (0/5 vs 1/5 first-attempt; 1/5 vs 2/5 final). See `variants/hermes/PROBE-RESULTS-r7.md` revision for details. Cross-run comparisons must use the strict criterion going forward.

---

## r7.1 (2026-04-18) — Hermes-Variant Probe Sweep

### Context
A five-variant probe sweep (A/B/C/D/E) validated that Gemma-4-31B running on Hermes Agent v0.8.0 can operate the AgentFW harness end-to-end as the local parent orchestrator. Key finding: dispatch rate on structured/long-horizon tasks went from 0% (baseline) to 60% first-attempt / 80% after runtime retries once the tool surface was simplified (Jira-skill pattern generalized). Architectural thesis — "Gemma as orchestrator, workers/judges as separate fresh-context child Gemma sessions, 100% local inference" — is validated.

The sweep is contained entirely under `variants/hermes/`. AgentFW core (`core/`, `references/`, `playbooks/`, `templates/`) and non-Hermes variants (claude-code, claude-projects, generic) were not touched. Cross-model integrity preserved.

### Added
- **`variants/hermes/DESIGN.md`** — detailed design spec for the Hermes-flavored AgentFW variant: architecture, the Jira-skill pattern generalized, component breakdown (HERMES-variantD.md system prompt, `delegate_worker` tool, three Hermes source patches, optional retry wrapper), Planner-Worker-Judge flow on Gemma, design constraints, failure modes addressed vs. residual.
- **`variants/hermes/IMPLEMENTATION.md`** — concrete install/activate/rollback/verify procedure; exact diffs for the three Hermes source patches; re-probe procedure; known issues and workarounds.
- **`variants/hermes/PROBE-RESULTS-r7.md`** — consolidated 5-variant sweep results: methodology, cross-variant metric table, dispatch trajectory analysis, runtime-truth vs persisted-session caveat, residual failure modes, cross-model integrity verification, judge independence caveat.
- **`variants/hermes/NEXT-STEPS.md`** — session-handoff doc for follow-up work: N=10 re-probe plan, SIGTERM-truncation fix, worker-quality probe design (r8 scope), production hardening paths.
- **`variants/hermes/HERMES-variantB.md`** — probe sibling: hard output contract variant (classification gate + Critical Rules). Retained for re-probe.
- **`variants/hermes/HERMES-variantD.md`** — **ship candidate:** hard contract + dispatch scaffolding + worked `<tool_call>` example for `delegate_worker`. Operator-activated via `probe-variantD-stage.sh`.
- **`variants/hermes/delegate_worker.py`** — **ship tool:** simplified single-argument dispatch wrapper (`goal: str`) around `delegate_task`. Designed for Gemma's tool-surface preferences.
- **Probe infrastructure at project root** — `PLAN-hermes-harness-probe.md`, `probe-tasks.md`, `probe-reproducibility.md`, `probe-swap.sh`, `probe-variantD-stage.sh`, `probe-variantE-wrapper.sh`, `probe-variantE-check.py`. Retained for re-probing.
- **`archive/hermes-probe-r7-2026-04-18/`** — 19 intermediate probe artifacts (worker reports, trial records, judge verdicts, revert histories) preserved for audit trail.

### Validated
- Gemma-4-31B can classify tasks reliably (10/10 marker emission with Variant B hard contract).
- Gemma-4-31B emits well-formed `delegate_worker` tool calls when the schema is simple and scaffolding is present.
- The Planner-Worker-Judge flow runs end-to-end on local inference (parent Gemma → child Gemma worker → summary → optional judge child Gemma).
- The Jira-skill pattern (narrow tool surface + worked format example + retry wrapper) generalizes from the Jira Daily Briefing to the full harness.

### Known gaps (r8 scope)
- **Worker quality.** When dispatch fires, children sometimes invent data, loop in wrong directories, or don't complete. Estimated operational ceiling at r7 ship state: ~25% useful-completion (80% dispatch × ~30% worker-useful).
- **SIGTERM truncation.** Parent sessions blocked waiting for child workers get killed by VM-side `timeout`, losing the parent's record of the dispatch. Runtime-truth ≠ persisted-session-truth. Workaround documented; upstream contribution candidate.
- **Trial-9-class bug-hunt tasks.** Gemma concludes "no bug" and re-classifies to one-shot in retry body; check script only reads first assistant's first line. False-negative in wrapper metrics. Fix documented in NEXT-STEPS.md.
- **Post-dispatch role collapse.** Parent can emit `delegate_worker` cleanly, then make unrelated mutations in main session while child runs. ROLE_COLLAPSE gate only catches pre-dispatch mutations.

### Cross-model integrity check
All AgentFW core and non-Hermes variant files verified byte-identical before and after the probe. `core/harness-core.md` md5 unchanged. Probe infrastructure (scripts, variant sibling files, documentation) lives entirely under `variants/hermes/` and top-level `probe-*` files — never touching files shared with other variants.

### Files modified (scope audit)
- Added under `variants/hermes/`: DESIGN.md, IMPLEMENTATION.md, PROBE-RESULTS-r7.md, NEXT-STEPS.md, HERMES-variantB.md, HERMES-variantD.md, delegate_worker.py
- Added at top level: PLAN-hermes-harness-probe.md, probe-tasks.md, probe-reproducibility.md, probe-swap.sh, probe-variantD-stage.sh, probe-variantE-wrapper.sh, probe-variantE-check.py
- Added: `archive/hermes-probe-r7-2026-04-18/` directory with README and 19 artifacts
- Unchanged: `core/`, `references/`, `playbooks/`, `templates/`, `variants/claude-code/`, `variants/claude-projects/`, `variants/generic/`, `evaluation/`, all pre-r7 PLAN and ARTIFACT files

---

## r7 (2026-04-17) — Cross-Model Tuning Pass

### Context
Claude Opus 4.7 landed with behavior deltas — fewer sub-agents dispatched by default, adaptive thinking off by default, stronger intrinsic self-verification, and coding-benchmark gains that tempt loosening structural gates. A tuning pass was needed to keep AgentFW aligned with 4.7 without regressing Opus 4.6, Sonnet 4.6, or GPT-5-tier models. The core firmware stays model-agnostic; 4.7-specific knobs live in a single short appendix with inline `(Anthropic: …)` sidenotes. Ten proposals from the r7 judge artifact were triaged: six shipped as model-agnostic edits, three shipped as reframed principles in a bounded model-family subsection, and four were rejected or deferred. See `PLAN-r7.md` §2–§4.

### Added
- **Self-verification vs. self-review clarifier** — Appended a single sentence to the Self-Review anti-pattern distinguishing in-context intrinsic pre-flight verification (fine, model-provided) from self-review-as-judge (prohibited by Rule 3). Prevents future tuners from weakening Rule 3 on the back of any model's self-verification marketing. See `references/anti-patterns.md`. (PLAN-r7 §2.1.)
- **Explicit fan-out instruction in worker dispatch** — Added a paragraph above `### Include` in the Context Budget for Sub-Agents subsection instructing planners to say "spawn N workers in parallel" literally when decomposing across independent items, not "decompose" alone. Counters 4.7's "fewer subagents by default" tendency; helps every model that takes literal phrasing better than advisory phrasing. See `references/prompt-design.md`. (PLAN-r7 §2.2.)
- **Quote-before-act on state files** — New subsection in state-management.md: worker prompts should include the exact PROGRESS.md line(s) being acted on, and workers are expected to echo them in returned artifacts. Applies to workers and judges equally. See `references/state-management.md`. (PLAN-r7 §2.4.)
- **Cadence annotation for the 3-task health gate** — One-line note after the numbered health-gate steps explaining the cadence is held pending empirical degradation-curve data; long-context retrieval scores do not imply agentic rule-adherence stability. Immunizes the cadence against well-meaning loosening on any vendor's long-context claims. See `references/state-management.md`. (PLAN-r7 §2.5.)
- **Task-state-triggered reflection note** — One-line cross-reference in state-management.md and observability.md clarifying the health gate fires on PROGRESS.md task count, not on a tool-call clock. Pre-empts deletion of the gate by any future tuner reading "remove every-N-tool-calls summarization" advice. See `references/state-management.md` and `references/observability.md`. (PLAN-r7 §2.6.)
- **Model-family knobs (non-binding) subsection** — New ≤25-line subsection at the end of `references/prompt-design.md` covering three reframed principles with inline sidenotes: reasoning effort by role, judges need guaranteed deliberation, token budget as a worker-scope component. Principles are model-agnostic; Anthropic-specific invocations appear only as `(Anthropic Opus 4.7: …)` sidenotes. See `references/prompt-design.md`. (PLAN-r7 §3.)

### Enhanced
- **Reference-file audit for vague generalizations** — Single-pass read of state-management, prompt-design, domain-guidelines, error-recovery, and anti-patterns for "and similar," "etc.," "or equivalent," and abstract generalizations in rule-bearing text. Where found, replaced with explicit enumerations or concrete triggers. Net-neutral or slightly negative on line count. (PLAN-r7 §2.3.)

### Rejected / Deferred
- **P5 — Recalibrate line-count heuristics to tokens for the 4.7 tokenizer.** Rejected. Line counts are more portable across tokenizers than any token-based heuristic; the current "500 lines" / "~175 lines" guidance is directionally correct for all models. (PLAN-r7 §4.)
- **P11 — Route web-research-heavy tasks away from 4.7 (BrowseComp regression).** Deferred. No Artifact A surface quote exists for the specific playbook content; re-evaluate when BrowseComp regression is reproduced in-house. (PLAN-r7 §4.)
- **P12 — Loosen `<20-line` one-shot threshold based on 4.7 coding gains.** Rejected. The clause is a role-separation gate, not a capability gate; benchmark strength does not change whether the main session should implement vs. delegate. (PLAN-r7 §4.)
- **P13 — Weaken Rule 3 (NO SELF-VERIFY) because 4.7 self-verifies.** Rejected. Anthropic does not claim 4.7's built-in self-verification replaces an independent-context judge; loosening rests on a misreading of the source. (PLAN-r7 §4.)

### Baseline Probe
Phase 0 multi-model empirical probe was run at reduced scope on 2026-04-17: Opus 4.7 and Sonnet 4.6 across GT-1, GT-3, and GT-5 only — 6 of 28 cells filled. Opus 4.6 could not be version-pinned via the Claude Code Agent tool model enum; GPT-5.4-Pro was not accessible from the probe tooling; GT-2/4/6/7 require true multi-turn sessions or mid-task event injection that single-dispatch subagents cannot reproduce. Directional signal: Opus 4.7 emitted classification gates correctly on all 3 probed tasks; Sonnet 4.6 missed the marker on GT-5 and was unclear on GT-3. Full-scope baseline deferred. See `evaluation/results-r6-baseline-multimodel-2026-04-17.md`.

### Known Gaps
- Opus 4.6 version-pinning not available in current tooling; non-regression on 4.6 could not be empirically confirmed for r7.
- GPT-5.4-Pro not accessible from probe tooling; cross-vendor non-regression claim is asserted on design grounds, not measured.
- GT-2, GT-4, GT-6, and GT-7 require a multi-turn runner and were not covered in the Phase 0 probe; human-driven runs needed to close the matrix.
- Sonnet-4.6-specific tuning (addressing the classification-gate miss and the DIAGNOSTIC.md classification-marker ambiguity observed in probe transcripts) is documented separately in `ADDENDUM-sonnet-4-6.md` for future revision.

### Migration
Claude Code users should re-sync their global CLAUDE.md from `variants/claude-code/CLAUDE.md`. Other variants (Claude Projects, Generic, Hermes) are deferred to a follow-up sync per PLAN-r7 §7 and will inherit the r7 edits after the Claude-Code variant clears the regression gate on full-scope runs.

### Line Delta
Firmware line-delta budget: ≤70 added lines across `core/`, `references/`, and variants combined, excluding CHANGELOG. Actual delta tracked in PLAN-r7 §5 accounting table.

### Files Modified
- `references/anti-patterns.md` — Self-review clarifier sentence
- `references/prompt-design.md` — Fan-out dispatch paragraph, Model-family knobs (non-binding) subsection
- `references/state-management.md` — Quote-before-act subsection, cadence annotation, task-state-triggered reflection note, vague-generalization audit
- `references/observability.md` — Task-state-triggered reflection cross-reference
- `variants/claude-code/CLAUDE.md` — r7 edits synced from canonical core + references
- `metadata.json` — Version bump to r7, date to 2026-04-17, description updated
- `README.md` — r7 revision references, what's-new section
- `DESIGN.md` — r7 revision references, reduced-scope probe note, model-family posture pointer
- `CHANGELOG.md` — This entry

---

## r6 (2026-04-10) — Context Degradation Resistance

### Context
Long Claude Code sessions exhibit progressive behavioral degradation: the agent stops delegating to sub-agents, stops using plan mode, stops dispatching separate judges, and collapses into one-shotting. This happens because (a) core behavioral rules lose attention weight as context fills, and (b) the existing "flag when hitting context limits" instruction is advisory — it requires the agent to remember to self-assess, which is the first thing that degrades. Additionally, the Claude Code variant was found to be missing all r5 structural enforcement gates (classification gate, one-shot hero warning, anti-patterns auto-load), meaning the primary deployment target was running with r4-era logic.

### Fixed
- **Claude Code variant synced to r5 core** — Classification gate, one-shot hero warning, tightened activation criteria, anti-patterns auto-load, and Session Protocol Step 0 now present in `variants/claude-code/CLAUDE.md`. Redundant Extended References section (38 lines) removed.

### Added
- **Critical Rules preamble** — Five numbered rules placed at the top of the core document, before all other behavioral content. Uses imperative framing designed to survive attention deprioritization in long contexts. Explicitly states "regardless of how much context has been consumed." See `core/harness-core.md`.
- **Context Health Gate** — State-driven check that fires after every 3 tasks reach completed/verified in PROGRESS.md. Requires re-reading the state file, self-assessing against Critical Rules, and outputting `[CONTEXT HEALTH: OK/DEGRADED]`. Trigger is the task count, not agent memory. See `references/state-management.md`.
- **Delegation Self-Check** — Procedural gate before any implementation code in the main session. Agent must verify its role and state a reason if not delegating. See `references/state-management.md`.
- **Context degradation as structural error** — When health check reveals degradation, treat as structural error: compact, restart with fresh context, re-verify work completed after last clean check. See `references/error-recovery.md`.
- **Rubber-Stamp Compliance anti-pattern** — Named failure mode for mechanically outputting protocol markers without genuine assessment. See `references/anti-patterns.md`.
- **CONTEXT_HEALTH_CHECK event type** — Observability event for health gate assessments. See `references/observability.md`.
- **PROGRESS.md health check tracking** — Context Health Checks table in the progress template. See `templates/PROGRESS.md`.
- **Golden Task 6: Late-Session Delegation** — Multi-phase test that fills context before testing whether delegation discipline holds. See `evaluation/golden-tasks.md`.
- **Golden Task 7: Context Health Gate Activation** — Tests whether the health gate fires correctly and resists rubber-stamping. See `evaluation/golden-tasks.md`.

### Enhanced
- **Reference Index compressed** — Removed subheaders and blank lines, single-line-per-entry format. Reclaimed 5 lines for Critical Rules. See `core/harness-core.md`.
- **Session Protocol updated** — "Flag when hitting context limits" replaced with concrete health gate trigger and output format. See `core/harness-core.md`.

### Files Modified
- `core/harness-core.md` — Critical Rules preamble, Reference Index compression, Session Protocol health gate
- `variants/claude-code/CLAUDE.md` — Full r5 gate sync, Extended References removed, Critical Rules preamble, health gate
- `references/state-management.md` — Context Health Gate, Delegation Self-Check
- `references/anti-patterns.md` — Rubber-Stamp Compliance anti-pattern
- `references/observability.md` — CONTEXT_HEALTH_CHECK event type
- `references/error-recovery.md` — Context degradation as structural error
- `templates/PROGRESS.md` — Context Health Checks table
- `evaluation/golden-tasks.md` — GT-6 (late-session delegation), GT-7 (health gate activation)
- `evaluation/eval-protocol.md` — GT-6 and GT-7 execution instructions and failure criteria
- `metadata.json` — Version bump to r6
- `CHANGELOG.md` — This entry
- `bootstrap.md` — r5 → r6 references

---

## r5 (2026-04-06) — Structural Enforcement Hardening

### Context
Two observed failures exposed that r4 relies on behavioral compliance rather than structural gates: (1) Claude Code skips the harness for tasks meeting activation criteria because the decision tree is advisory, and (2) in a UE5 C++ project, three planning steps "completed" without building code — errors accumulated invisibly. This release converts advisory instructions into procedural constraints.

### Added
- **Mandatory classification gate** — Agent must output `[TASK CLASS: one-shot | structured | long-horizon]` before any work. Omitting is a protocol violation. See `core/harness-core.md`.
- **Verification gates** — Tasks with unverified dependencies cannot be dispatched. Hard gate, not advisory. See `references/state-management.md`.
- **Staleness detection** — Tasks at `completed` without judge dispatch are flagged as verification gaps. See `references/state-management.md`.
- **Compiled language verification** — Judge must build as first step for C++, Rust, Go, Java, C#, Swift. Reasoning-only review is not Tier 1. See `references/domain-guidelines.md`.
- **Interpreted language verification** — Judge must run tests/linter or at minimum import the module. See `references/domain-guidelines.md`.
- **Late-discovery error protocol** — Errors found after multiple unverified tasks are treated as structural; roll back to last verified checkpoint. See `references/error-recovery.md`.
- **Autonomous mode verification gates** — Judge dispatched between every task, not just at the end. See `playbooks/feature-dev.md`.
- **Long-running service restart rule** — Workers/judges must automatically restart services (web apps, gateways, daemons) after code changes. No manual restart steps. See `references/domain-guidelines.md`.

### Enhanced
- **One-shot criteria tightened** — One-shot now requires: zero files modified, OR one file <20 lines with no cross-file deps. Relaxation requires explicit justification. See `core/harness-core.md`.
- **Tier 1 enforcement** — Tasks cannot transition completed→verified without machine-check output in PROGRESS.md. See `references/verification-tiers.md`.
- **PLAN.md template** — Added required `Verification Method` column (build, test:\<cmd\>, lint:\<cmd\>, schema-check, human-review, expert-subagent). Locked at planning time. See `templates/PLAN.md`.
- **PROGRESS.md template** — Added `Verification Method` and `Verification Artifact` columns. `Verified By` = "planner" is flagged as role-collapse violation. Version bumped to r5. See `templates/PROGRESS.md`.
- **Anti-patterns auto-loaded** — `references/anti-patterns.md` now loads for all structured/long-horizon tasks, not just self-check. One-Shot Hero Mode warning inlined into decision tree. See `core/harness-core.md`.

### Files Modified
- `core/harness-core.md` — Classification gate, tightened one-shot, WARNING callout, anti-patterns auto-load
- `references/state-management.md` — Verification gates, staleness detection, strengthened `completed` state
- `references/domain-guidelines.md` — Compiled and interpreted language verification subsections
- `references/verification-tiers.md` — Tier 1 enforcement language
- `references/error-recovery.md` — Late-discovery error protocol
- `templates/PLAN.md` — Verification Method column and rules
- `templates/PROGRESS.md` — Verification Method, Verification Artifact, role-collapse detection, r5 version
- `playbooks/feature-dev.md` — Autonomous mode verification gates

---

## r4 (2026-04-04) — Modular Restructure + Audit Fixes

### Breaking Changes
- Project restructured from 3 flat files to modular directory. If you have r3 installed as CLAUDE.md, you need to re-install using the r4 variant or bootstrap.
- CLAUDE.md content reduced to ~150-line core. Extended content moved to on-demand references.
- Guided mode no longer instructs the same session to switch between worker and judge roles.

### Added
- **Permission model** [F1]: Three trust tiers (always-allow, ask-first, never-allow), worker scope constraints, escalation protocol. See `core/permissions.md`.
- **Evaluation system** [F3]: 5 golden tasks for regression testing harness behavior. See `evaluation/golden-tasks.md` and `evaluation/eval-protocol.md`.
- **Observability** [F4]: Structured event logging via SESSION_LOG.md. 10 event types for tracking agent behavior. See `references/observability.md`.
- **Bootstrap installer**: Self-install prompt that detects client type and installs the appropriate variant. See `bootstrap.md`.
- **Client variants**: Pre-built install artifacts for Claude Code, Claude Projects, and generic clients.
- **Launch prompt templates**: Standalone copy-paste prompts for autonomous sessions.
- **PLAN.md template**: Task plan template with permission scope column.

### Enhanced
- **State management** [F2]: PROGRESS.md upgraded from checklist to state machine. Tasks now track: status (planned→verified/failed), worker ID, attempt number, side-effects, checkpoints. Dedupe rules prevent double-dispatch. See `references/state-management.md`.
- **Prompt design** [F5]: Added context budget guidance for sub-agents. Workers receive only task-relevant context, not the full framework. See `references/prompt-design.md`.

### Fixed
- **Guided mode self-review** [F6]: Removed pattern where the same session acts as both worker and judge. Human-as-judge is now the default in guided mode. Option to dispatch separate sub-agent judge. See `playbooks/cross-scenario-patterns.md`.

### Architecture
- Core framework condensed from ~330 lines to ~150 lines (always-load)
- All extended content moved to on-demand references (7 files)
- Playbooks extracted to individual files (5 files)
- Templates extracted to dedicated directory (4 files + 4 launch prompts)
- r3 originals preserved in `archive/`

### Audit Trail
Findings from evaluation using OB1 n-agentic-harnesses skill (pre-rename: "Agentic Harness"):
- F1 (High): No permission layer → `core/permissions.md`
- F2 (High): No state model → `references/state-management.md`, `templates/PROGRESS.md`
- F3 (Med-High): No evaluation system → `evaluation/golden-tasks.md`, `evaluation/eval-protocol.md`
- F4 (Medium): No observability → `references/observability.md`, `templates/SESSION_LOG.md`
- F5 (Medium): Unmanaged context budget → core/references split, `references/prompt-design.md`
- F6 (Low-Med): Guided mode self-review → all playbook guided-mode sections
