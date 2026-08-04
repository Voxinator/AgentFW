# PLAN — AgentFW v9.7 "verification placement" (D-28 / D-29 / D-31) — rev 2

**Revision note (rev 2, 2026-08-04).** Local revise after Layer-2 pass 1 (dual, both judges
BLOCKERS, all contract-mechanics class; plan reasoning, approach-fit and necessity audit clean in
both reports). Every blocker was demonstrated by a judge building a hostile implementation and
running the contract against it — the review this plan predicted would be cheap did exactly what
the plan's thesis says review should do. Changes:

1. **T1's three negative legs were vacuous** — all three bad-fixture filenames contain the string
   `witness`, so the validator's "cannot read …plan-bad-17-carrying-**witness**-pair.md" error
   satisfied `grep -q witness`, and a stub tree with a do-nothing 1.7 validator and no fixtures at
   all emitted `T1_D28_OK`. Every negative leg in T1 and T2 is now existence-gated (`test -s
   <fixture> &&`) before the validator runs.
2. **T1's `exit_code != 0` lever was verified nowhere** — new fixture leg
   `plan-bad-17-red-witness-exit0.md` plus a matching mutation probe.
3. **T4 passed while the Claude kernel bootloader still taught the removed duty** — the
   residual-duty negative greps covered only the two SKILL files; `adapters/claude-code/CLAUDE-block.md`
   is now covered, with a probe.
4. **The Codex kernel bootloader was covered by nothing** — `adapters/codex/AGENTS.md` carries the
   removed duty today, appeared in no task's command, and was missing from R5's own enforcement
   table despite R5 requiring "both adapter kernel bootloaders." Now covered in both. *This plan's
   own proposed locality check would have caught it, which is the strongest field evidence for R3
   in the record.*

Folded suggestions: the two mis-sourced citations corrected (`worktree_isolation` lives in
`capability.yaml`, not the active snapshot; `mktemp` is not in the command-resolution map); the
new `locality` defect keyword now has a task owner in the stable keyword contract; T4 validates the
Codex SKILL's embedded block too; T5's hollow-passability closed by making `Falsifier` a required
per-entry schema label in `check-candidates.py` rather than a file-global grep count; T2 gains a
substring-collision fixture for the exact risk its own `risk` field names. Also folded: R4's
eligibility predicate is now mechanically derivable rather than a judgment field (below).

All five red legs re-recorded against the new command digests.

**Objective (root):** `verification-placement` — move the expensive verification question from
plan time, where it cannot be answered honestly, to verification time, where answering it is one
command. A producer must never again be required to build proof machinery about a program that
does not exist yet.

**Field evidence:** two sessions, two repos, 2026-08-02 → 2026-08-03, on v9.6.0 installed to both
runtimes — `evaluation/field-report-2026-08-03-hermes-brain-apparatus-inversion.md`. Nine of that
report's eleven findings converge on one placement error. The measured shape: ≈1,140 lines of
acceptance apparatus against a 163-line deliverable (≈7:1) over four Layer-2 passes and zero
product defects found by plan critique — against an in-record control in the same repo the same
week, 118 lines of ordinary tests against 233 lines of product (≈0.5:1), one round, zero
rejections. The only variable was where the "is this check any good?" question got asked.

**Design keystone.** The green witness never proved anything the verifier does not already prove
better. The acceptance command must pass on the REAL tree before any work item reaches a verified
state — that duty already exists. Schema 1.6 additionally demanded the producer prove the command
*could* pass on a tree the producer authored, at the moment of maximum uncertainty, with nothing
independent checking the tree. This plan deletes that demand, keeps the red leg (cheap, honest,
one command), and gives the residual risk it creates an explicit named outcome rather than a
silent burned cycle.

**Counterweight check (applied to this plan itself).** v9.7 is close to plan-time-work-neutral in
schema mass and sharply negative in plan-time *effort*: it removes a four-field object per
contract (the green leg) plus the witness tree that object describes, and adds two
list-of-strings fields answerable from the repo on day zero. Every mechanism below can be
satisfied without an implementation existing. That is the test each one had to pass to be in this
plan; D-30, D-32, D-33, D-34, D-36 are deferred below partly because they could not.

**The irony, declared.** Schema 1.6 is the schema of record, so this plan — the plan that removes
plan-time green witnesses — carries plan-time green witnesses for all five of its own contracts.
That is deliberate: exempting itself would be the weakest possible argument. The measured cost of
authoring them here is recorded in the Witness evidence section as a live data point for D-34
(in-domain cost ≈ 0 vs the out-of-domain ≈1,140 lines the field report measured).

## Named relaxation — human-authorized, 2026-08-04 (read this before critiquing)

**This plan does NOT pass Layer 1.** It carries five `witness` defects — one per contract — and no
others. They are present by an explicit operator decision, not by omission, and the model did not
clear them itself.

- **Invariant waived:** schema 1.6's plan-time GREEN witness leg (`witness_pair.green`) — the
  producer-authored witness tree proving each `acceptance_command` CAN pass.
- **Exact scope:** the five contracts T1–T5 of this plan. Not the red leg, which is recorded for
  all five. Not any other objective.
  **STATUS AT REV 2: LAPSED — awaiting re-authorization.** The authorization granted 2026-08-04
  named rev 1 only, and rev 2 changed all five command strings. The waiver does not carry forward
  on its own terms; a genuine operator turn must extend it to rev 2, or the five green legs must
  be recorded. The model does not renew its own relaxation.
- **Why:** the measured cost of the waived artifact is ≈1,700 lines of witness trees (sizing table
  in Witness evidence below) — more than the ≈1,140-line apparatus whose cost is this release's
  entire subject — to pre-prove five commands the workers will run for real within hours. The
  operator was given the alternatives (record them anyway; or author at schema 1.5, which needs no
  waiver and which this plan declines as schema laundering) and selected the waiver.
- **Compensating mechanical controls, all in force:**
  1. All five RED legs are recorded, whole-command, digest-matched to each contract's exact
     `acceptance_command` — and already caught two C0 substrate defects in these contracts.
  2. Every contract carries 4–5 `mutation_probes`, executed by the producer after implementation
     AND independently re-executed by the judge on fresh scratch copies at the `independent` tier.
  3. The green evidence is not waived, only relocated: no task reaches a verified state without the
     judge running the whole command green on the REAL tree.
  4. The risk this waiver creates is discharged inside this same build — R2/T1 ships
     `IMPOSSIBLE-COMMAND`, the named outcome for a contracted command that cannot pass.
- **Termination condition:** the waiver expires when T1 lands. Schema 1.7 removes the obligation
  entirely, so no successor plan needs or inherits it.

**Fair game for the critics:** that this waiver is self-serving — the plan removing plan-time green
witnesses exempted itself from plan-time green witnesses. That objection is legitimate and is the
first thing a hostile reader should press. The counter-argument, stated once so it can be attacked
rather than assumed: the waived artifact's cost was measured, not asserted; the retained red leg
demonstrably found real defects in these very contracts; and every discriminating check the green
leg would have performed is still performed, by an independent judge, against real code.

## Assurance derivation

- **Q1 blast radius & reversibility:** policy documents, the Layer-1 validator, plan fixtures, one
  new stdlib checker, SKILL/kernel text, and provenance files — all inside this git repo, every
  edit trivially reversible. Nothing destructive; no history rewriting; no external effects. The
  released artifact later installs to two live runtimes, but installation is a separate
  human-run step outside this plan.
- **Q2 defect-escape probability:** real. Three seams: validator behavior ↔ policy text ↔
  fixtures; schema 1.7 ↔ schema 1.6 back-compatibility (existing gated plans must keep
  validating); policy ↔ both adapter kernels (the D-16 documented prose/mechanical divergence
  class). A producer-only check plausibly misses each.
- **Q3 autonomy & irreversibility:** planner supervised; workers dispatched one task at a time;
  no irreversible or outward-facing step. No A3 escalator applies — this is not production
  infrastructure, not security-sensitive, not destructive.

⇒ **A2**, `required_plan_review_tier: dual` — declared above the derived `single` floor for the
same reason v9.6 declared it: this plan changes the gate itself, and a gate change reviewed by one
judge is a gate change reviewed by its own author's nearest neighbour. Verification: producer
always; `independent` at every task.

**Capability preflight (declared degradation).** The installed snapshot
`~/.claude/skills/agentfw/active-capabilities.yaml` (`generated: "20260801-023155"`) reports
`deterministic_permissions_configured: false` — the `settings.example.json` deny rules are not
merged on this install. All work here is repo-local reversible file editing, so the behavioral
ask-tier and per-worker scope budgets carry the control load. Recommended once: merge the deny
set. Declared, not blocking, not a floor item.

`worktree_isolation` is `partial` / unverified — sourced from the packaged **`capability.yaml`**,
not from the active snapshot, which carries no entry for it (corrected in rev 2; rev 1 cited the
wrong file). That is why the task graph below serializes every pair of tasks that share a file
rather than assuming platform worktree isolation.

## Requirements

**Musts (won't work without it):**

- **R1 — Schema 1.7 demotes the witness pair to a red witness.** At A2+ every contract carries
  `red_witness` — one leg: `tree`, `command_sha256`, `exit_code` (≠ 0), `evidence_path` — and the
  plan-time green obligation is gone. A 1.7 block carrying `witness_pair` is rejected with a
  diagnostic naming the demotion and pointing at the migration. Schema 1.6 blocks keep validating
  under 1.6 rules unchanged.
  *Because:* without deleting the plan-time green demand, nothing else in this plan matters — it
  is the demand that produced ≈1,140 lines of apparatus and four passes that found zero product
  defects.

- **R2 — The green obligation moves to the verifier, and its failure mode gets a name.** The
  verifier's green run on the REAL tree is the green evidence of record. When the verifier cannot
  make the contracted command pass against a correct implementation, it returns
  **`IMPOSSIBLE-COMMAND`** — classified as a *contract* defect that routes to the re-approach fork
  (R4), never as a work defect charged to the worker.
  *Because:* this is the risk D-28 introduces, stated in the field report as non-zero. Deleting
  the green witness without naming what replaces it would move the failure from "expensive at plan
  time" to "silent at implementation time," which is worse.

- **R3 — Enforcement locality, checked at Layer 1.** Every requirement carries `enforced_in` — a
  non-empty list of repo-relative paths where the requirement is enforced — and every task carries
  `touches`, the list of paths it modifies. The validator rejects any `must` requirement whose
  `enforced_in` paths are not all covered by the `touches` of at least one task covering that
  requirement. Defect keyword `locality`.
  *Because:* a full review round was spent on requirements enforced in a repo no task owned. The
  question is answerable on day zero from the repo, and nothing in the framework asks it until C5,
  after the apparatus is built.

- **R4 — The re-approach fork.** A fifth option on the 2-pass cap menu and a fourth branch on the
  D-2 exhaustion fork: *plan and requirements retained; acceptance contracts re-authored; charges
  exactly one cycle; the re-authored plan re-enters Layer 1.* Eligible only when every open blocker
  is contract-mechanics class (C2 or the new `locality`) and no requirement is itself contested.
  **Bounded: at most once per objective**, recorded in the ledger; a second selection is
  ineligible and the objective takes the existing three-way fork. Machine-checked as a decision
  table, same pattern as D-2/D-21.
  *Because:* both sessions' correct move — plan sound, verification strategy wrong — existed on no
  menu, so it cost a bespoke named relaxation plus a human authorization turn, at the exact moment
  the zero-dispatch tripwire had already fired.

- **R5 — No installed surface contradicts schema 1.7.** SKILL.md §3, both adapter kernel
  bootloaders, the CHANGELOG, RELEASE-NOTES-v9.7.0, the CANDIDATES board (D-28…D-36 entries and
  rows, D-24 unfolded), and the field report's disposition section all state the demotion
  consistently; `check-skill-sync.py` passes on the cross-adapter block.
  *Because:* a schema change whose installed kernel still teaches the old duty is the D-16
  documented prose/mechanical divergence class — the next session reads the kernel, not the repo.

**Enforcement locality of this plan's own requirements** (dogfooding R3 in prose, since the field
does not exist yet — and demonstrating that the question is answerable at plan time):

| Requirement | Enforced in | Touched by |
|---|---|---|
| R1 | `tools/validate-plan`, `policy/acceptance-contract.md`, `policy/plan-critique.md` | T1 |
| R2 | `policy/acceptance-contract.md` | T1 |
| R3 | `tools/validate-plan`, `policy/acceptance-contract.md` | T2 |
| R4 | `policy/plan-critique.md`, `tools/check-reapproach-invariants.py`, `evaluation/fixtures/reapproach-fork.json` | T3 |
| R5 | `adapters/claude-code/skills/agentfw/SKILL.md`, `adapters/codex/skills/agentfw/SKILL.md`, `adapters/claude-code/CLAUDE-block.md`, **`adapters/codex/AGENTS.md`**, **`adapters/claude-code/agents/agentfw-verifier.md`**, **`tools/check-candidates.py`**, `CHANGELOG.md`, `CANDIDATES.md`, `RELEASE-NOTES-v9.7.0.md` | T4, T5 |

The three bolded paths were **absent from this table in rev 1**, and `adapters/codex/AGENTS.md` —
which carries the removed duty today — was consequently covered by no task's acceptance command.
A judge found it by reading; **the locality check this plan proposes (R3) would have found it
mechanically at Layer 1.**

**It happened twice more.** `adapters/claude-code/agents/agentfw-plan-critic.md` was ALSO missing
from this table — a sixth installed surface still instructing the critic to re-execute both witness
legs against a planner-authored witness tree — found by T4's own producer noticing it sat outside
every task's scope. And `tools/tests/validate-plan.sh` carries assertions against adapter text that
T4 had to change while being forbidden to edit the test script; that one resolved itself only
because T4 chose to retain the 1.6 paragraph verbatim.

Three coverage gaps in one plan's requirement→file mapping, every one of them the exact defect
class R3 exists to catch, all three found by humans-or-judges reading rather than by any mechanism.
This plan failing its own proposed check three times is the strongest field evidence for R3 in the
record — and it argues that R3's `enforced_in` should be authored by asking "what would have to
change for this requirement to become false?", not by listing the files one already intends to edit.

**Deferred to the next increment (D-18 ledger — deliberately NOT in this build):**

- **R6** — apparatus-to-deliverable ratio measured at verification time from the diffstat (D-30)
- **R7** — change-delta input to assurance derivation, modulating controls within a tier only (D-32)
- **R8** — vacuity floor defined against `risk_class` / `failure_surfaces` (D-33)
- **R9** — out-of-domain validation before universal mandate, with a designated pilot (D-34)
- **R10** — multi-repo objectives and repo-hop as the fourth counter reset (D-35)
- **R11** — Layer-1 PASS semantics + assertion-presence lint past shell shape (D-36)

R6–R11 are real and are recorded here as forward work, not dropped. R10 in particular is a
different problem that merely surfaced in the same sessions.

## Machine-readable plan

```json agentfw-plan
{
  "version": "1.6",
  "assurance": "A2",
  "required_plan_review_tier": "dual",
  "overrides": [
    {
      "blocker": "Layer-1 schema-1.6 witness defect on contracts T1-T5 (rev 2): no plan-time green witness leg recorded",
      "assumption": "each acceptance_command CAN pass against a correct implementation; unproven at plan time, and the measured cost of proving it here is approximately 1700 lines of witness-tree material against a build whose entire subject is that cost",
      "followup_test": "the independent judge runs the whole acceptance_command green on the REAL tree before any task reaches verified, and re-executes every contracted mutation probe on fresh scratch copies; a command that cannot be made to pass returns IMPOSSIBLE-COMMAND and routes to re-approach rather than to a worker retry",
      "authorized_turn": "operator turn 2026-08-04 extending the rev-1 named relaxation to rev 2 as part of the delivery override"
    },
    {
      "blocker": "T1 exit_code != 0 lever asserted, not demonstrated: the red-witness-exit0 fixture does not exist yet so no hostile tree has attacked that leg",
      "assumption": "the exit0 fixture leg discriminates a validator that drops the red_witness exit-code check",
      "followup_test": "contracted T1 mutation probe: drop the exit_code != 0 check on a scratch copy; plan-bad-17-red-witness-exit0 must then PASS and the whole command must exit non-zero. Producer runs it; the independent verifier re-runs it on a fresh scratch copy",
      "authorized_turn": "operator turn 2026-08-04 confirming the delivery override offer"
    },
    {
      "blocker": "T2 locality matcher never attacked with a hostile validator: the locality fixtures do not exist yet",
      "assumption": "the locality check compares exact path elements rather than requirement ids or substrings",
      "followup_test": "contracted T2 mutation probes: id-comparison mutation and substring-comparison mutation must each drive plan-bad-17-orphan-enforcement / plan-bad-17-locality-substring to PASS and the whole command to exit non-zero. Verifier-executed on fresh scratch copies",
      "authorized_turn": "operator turn 2026-08-04 confirming the delivery override offer"
    },
    {
      "blocker": "T3 selftest-signal gate unprobed: check-reapproach-invariants.py does not exist yet",
      "assumption": "the selftest signal gate rejects a zero-byte or signal-less checker, and the decision table discriminates all five contracted rows",
      "followup_test": "contracted T3 mutation probes: zero-byte checker plus the four table-row inversions, each of which must drive the whole command non-zero. Verifier-executed",
      "authorized_turn": "operator turn 2026-08-04 confirming the delivery override offer"
    },
    {
      "blocker": "T5 per-entry Falsifier enforcement unprobed: the check-candidates.py extension does not exist yet",
      "assumption": "Falsifier is validated inside each entry's own section body rather than counted file-globally",
      "followup_test": "contracted T5 mutation probes: delete the Falsifier line from the D-33 entry only, and gather all nine Falsifier lines outside any entry section; each must drive the whole command non-zero. Verifier-executed",
      "authorized_turn": "operator turn 2026-08-04 confirming the delivery override offer"
    }
  ],
  "requirements": [
    {"id": "R1", "text": "Schema 1.7: at A2+ every contract carries red_witness (tree, command_sha256, exit_code != 0, evidence_path); the plan-time green witness obligation is removed; a 1.7 block carrying witness_pair is rejected with a diagnostic naming the demotion; schema 1.6 blocks continue to validate unchanged under 1.6 rules", "necessity": "must", "because": "the plan-time green demand is what produced roughly 1,140 lines of acceptance apparatus against a 163-line deliverable across four Layer-2 passes that found zero product defects; without deleting it nothing else in this plan changes the outcome"},
    {"id": "R2", "text": "The green obligation moves to the verifier: its green run on the real tree is the green evidence of record, and a contracted command that cannot be made to pass against a correct implementation returns IMPOSSIBLE-COMMAND, a contract defect routed to the re-approach fork rather than a work defect charged to the worker", "necessity": "must", "because": "removing the plan-time green witness moves the impossible-command risk onto a worker who can burn an implementation cycle before anyone notices; unnamed, that failure is silent at implementation time, which is worse than expensive at plan time"},
    {"id": "R3", "text": "Enforcement locality at Layer 1: every requirement carries enforced_in (non-empty list of repo-relative paths) and every task carries touches (list of paths it modifies); the validator rejects any must requirement whose enforced_in paths are not all covered by the touches of at least one task covering that requirement, defect keyword locality", "necessity": "must", "because": "a full review round was spent on requirements enforced in a repository no task owned, and nothing asks the question until C5 at Layer 2 after the proof apparatus has already been built"},
    {"id": "R4", "text": "Re-approach fork: a fifth cap-menu option and a fourth exhaustion-fork branch retaining plan and requirements while re-authoring acceptance contracts, charging exactly one cycle, re-entering Layer 1, with eligibility MECHANICALLY DERIVED — eligible iff every open blocker is contract-mechanics class and no open blocker's finding cites a requirement id, so no free-text judgment field decides eligibility — bounded to at most once per objective and recorded in the ledger, machine-checked as a decision table", "necessity": "must", "because": "the correct move in both field sessions — plan sound, verification strategy wrong — was on no menu, so it cost a bespoke named relaxation plus a human authorization turn at the exact moment the zero-dispatch tripwire had already fired"},
    {"id": "R5", "text": "No installed surface contradicts schema 1.7: SKILL.md section 3, both adapter kernel bootloaders, CHANGELOG, RELEASE-NOTES-v9.7.0, the CANDIDATES board entries and rows for D-28 through D-36 with D-24 unfolded, and the field report disposition all state the demotion consistently, with check-skill-sync.py passing on the cross-adapter block", "necessity": "must", "because": "a schema change whose installed kernel still teaches the removed duty is the documented prose/mechanical divergence failure class, and the next session reads the installed kernel rather than the repo"},
    {"id": "R6", "text": "Apparatus-to-deliverable ratio measured at verification time from the diffstat, reported in the verdict, justification required above 1:1, no threshold and no plan-block field (D-30)", "necessity": "nice-to-have"},
    {"id": "R7", "text": "Change-delta input to assurance derivation, modulating controls within a tier only; lowering below an escalator floor requires a named relaxation (D-32)", "necessity": "nice-to-have"},
    {"id": "R8", "text": "Vacuity floor class retained but defined against the contract's declared risk_class and failure_surfaces (D-33)", "necessity": "nice-to-have"},
    {"id": "R9", "text": "Out-of-domain validation before a universal mandate, with a designated pilot objective named at release time (D-34)", "necessity": "nice-to-have"},
    {"id": "R10", "text": "Multi-repo objectives: ledger and counters keyed across trees, repo-hop closed as the fourth counter reset, cross-repo shared-value reconciliation (D-35)", "necessity": "nice-to-have"},
    {"id": "R11", "text": "Layer-1 PASS semantics reworded to well-formed rather than good, plus an assertion-presence lint past shell shape (D-36)", "necessity": "nice-to-have"}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "D-28: schema 1.7 red_witness + IMPOSSIBLE-COMMAND verifier duty — validator, policy, fixtures",
      "deps": [],
      "contract": {
        "requirement_ids": ["R1", "R2"],
        "criteria": "tools/validate-plan accepts \"version\": \"1.7\" and enforces, at A2+, a red_witness object containing exactly tree, command_sha256, exit_code, evidence_path with command_sha256 equal to the sha256 of the contract's exact acceptance_command string and exit_code != 0; a 1.7 block carrying witness_pair is rejected with a diagnostic carrying the stable keyword witness and naming the demotion; a 1.7 A2+ contract missing red_witness is rejected with keyword witness; a red_witness declaring exit_code 0 is rejected with keyword witness (an impossible red leg is as void as a faked green one); schema 1.6 blocks validate exactly as before, demonstrated by re-validating the shipped PLAN-v9.6-operator-compass.md; policy/acceptance-contract.md replaces the witness-pair section with a red-witness section and adds the verifier's IMPOSSIBLE-COMMAND duty (a contracted command that cannot pass against a correct implementation is a contract defect routed to re-approach, never a work defect); policy/plan-critique.md rule 17 and the defect-keyword contract state the same; EVERY negative leg is existence-gated with test -s before the validator runs, so a missing fixture can never satisfy a keyword grep against the validator's own cannot-read diagnostic (the pass-1 blocker); the full existing fixture suite still passes so no earlier schema regressed",
        "acceptance_command": "bash -c 'T=$(mktemp) && bash tools/tests/validate-plan.sh > \"$T\" 2>&1 && grep -q PASS \"$T\" && test -s tools/fixtures/plan-good-17.md && python3 tools/validate-plan tools/fixtures/plan-good-17.md > \"$T\" 2>&1 && grep -q PASS \"$T\" && test -s tools/fixtures/plan-bad-17-carrying-witness-pair.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-carrying-witness-pair.md > \"$T\" 2>&1 && grep -q \"is demoted from plan-time evidence\" \"$T\" && test -s tools/fixtures/plan-bad-17-missing-red-witness.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-missing-red-witness.md > \"$T\" 2>&1 && grep -q \"a recorded FAILING run of the whole\" \"$T\" && test -s tools/fixtures/plan-bad-17-red-witness-digest.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-red-witness-digest.md > \"$T\" 2>&1 && grep -q \"does not match the sha256 of the contract\" \"$T\" && test -s tools/fixtures/plan-bad-17-red-witness-exit0.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-red-witness-exit0.md > \"$T\" 2>&1 && grep -q \"must record the whole command FAILING\" \"$T\" && python3 tools/validate-plan PLAN-v9.6-operator-compass.md > \"$T\" 2>&1 && grep -q PASS \"$T\" && grep -q \"^### The red witness (schema 1.7)\" policy/acceptance-contract.md && grep -q \"^\\*\\*The IMPOSSIBLE-COMMAND duty\" policy/acceptance-contract.md && grep -q \"punishes the wrong party\" policy/acceptance-contract.md && grep -q \"^17\\. \\*\\*Schema 1.7 red witness\" policy/plan-critique.md && echo T1_D28_OK'",
        "expected_signal": "terminal line exactly T1_D28_OK with exit 0",
        "environment": "repo checkout, Python 3, bash, no network; grep resolves to /usr/bin/grep per command_resolution in the installed active-capabilities.yaml (~/.claude/skills/agentfw/, generated 20260801-023155). mktemp is NOT in that map — it is an unrecorded system-binary dependency of this command, declared here rather than assumed, and a verifier on a host lacking it must report an environment mismatch instead of a defect",
        "evidence": "validator output, fixture-suite output, and witness transcripts under evaluation/evidence/v9.7-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, make the validator accept a 1.7 block carrying witness_pair (delete the rejection branch) — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, make red_witness optional at A2+ — plan-bad-17-missing-red-witness then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, drop the command_sha256 equality check for red_witness — plan-bad-17-red-witness-digest then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, drop the red_witness exit_code != 0 check — plan-bad-17-red-witness-exit0 then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, make the 1.7 branch reject 1.6 blocks — re-validating PLAN-v9.6-operator-compass.md then fails and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete ONLY the substantive paragraph that defines the IMPOSSIBLE-COMMAND duty from policy/acceptance-contract.md, leaving every incidental cross-reference to the term intact elsewhere in the file — the command must exit non-zero. (Rev-2 verifier REJECTED T1 on exactly this: the leg was a bare whole-file grep for a term occurring 5 times, so gutting the definition left it green. The leg now anchors on the bolded lead-in line and on a phrase unique to the definition.)", "expected": "red"},
          {"mutation": "on a scratch copy, delete ONLY the '### The red witness (schema 1.7)' section heading line from policy/acceptance-contract.md, leaving the body text — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete ONLY Layer-1 rule 17's numbered lead-in from policy/plan-critique.md, leaving other red_witness mentions intact — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete every plan-bad-17-* fixture while leaving a permissive 1.7 validator in place — the command must exit non-zero at the first test -s gate rather than passing on cannot-read diagnostics (the pass-1 blocker, now regression-probed)", "expected": "red"},
          {"mutation": "on a scratch copy, keep the bolded IMPOSSIBLE-COMMAND lead-in line but replace the paragraph BODY with a stub — the command must exit non-zero. (Pass-3 verifier finding: the prior anchor phrase turned out to live in a different section of the file entirely, so a hollowed-out paragraph passed.)", "expected": "red"},
          {"mutation": "on a scratch copy, disable ALL FOUR red_witness checks in the validator at once while leaving the fixtures valid — the command must exit non-zero BECAUSE the bad-17 fixtures then PASS, and the failure must name a red_witness diagnostic rather than any unrelated defect. (Pass-3 verifier finding: the bad-17 fixtures carried no enforced_in/touches, so they tripped an unrelated locality defect while the generic keyword grep matched their own FILENAME — every witness probe was passing for the wrong reason.)", "expected": "red"}
        ],
        "risk": "a schema change that silently invalidates already-gated 1.6 plans, or that removes the green leg without the validator still proving the red leg's digest binds to the contract's exact command — either would trade a costly duty for an unenforced one",
        "negative_cases": [
          "a 1.7 block carrying witness_pair is rejected naming the demotion, not silently accepted",
          "a 1.7 A2+ contract with no red_witness is rejected with keyword witness",
          "a red_witness whose command_sha256 does not match the contract's acceptance_command digest is rejected",
          "a red_witness declaring exit_code 0 is rejected, and a fixture leg exercises it",
          "a tree in which the bad-17 fixtures are absent fails the command at the existence gate rather than passing on the validator's cannot-read diagnostic",
          "the shipped 1.6 plan PLAN-v9.6-operator-compass.md still validates unchanged"
        ]
      }
    },
    {
      "id": "T2",
      "title": "D-29: enforcement locality — enforced_in / touches fields + Layer-1 locality check",
      "deps": ["T1"],
      "contract": {
        "requirement_ids": ["R3"],
        "criteria": "under schema 1.7, every requirement record carries enforced_in (a non-empty JSON array of non-empty repo-relative path strings) and every task carries touches (a JSON array of path strings); the validator rejects, with the stable defect keyword locality, any must requirement having an enforced_in path not present in the touches of at least one task whose requirement_ids include it; path comparison is exact-element, never substring — a requirement enforced in tools/validate-plan is NOT satisfied by a task touching tools/validate-plan.sh; nice-to-have and fluff requirements are exempt from the locality check exactly as they are exempt from tier-aware coverage; policy/acceptance-contract.md documents both fields in the field table and the schema 1.7 section, and policy/plan-critique.md's stable defect-keyword contract gains locality as an owned keyword (a keyword with no owner in that contract is unenforceable by fixtures that key on it); every negative leg is existence-gated with test -s; the full fixture suite and the T1 fixtures still pass",
        "acceptance_command": "bash -c 'T=$(mktemp) && bash tools/tests/validate-plan.sh > \"$T\" 2>&1 && grep -q PASS \"$T\" && test -s tools/fixtures/plan-good-17.md && python3 tools/validate-plan tools/fixtures/plan-good-17.md > \"$T\" 2>&1 && grep -q PASS \"$T\" && test -s tools/fixtures/plan-bad-17-orphan-enforcement.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-orphan-enforcement.md > \"$T\" 2>&1 && grep -q locality \"$T\" && test -s tools/fixtures/plan-bad-17-missing-enforced-in.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-missing-enforced-in.md > \"$T\" 2>&1 && grep -q locality \"$T\" && test -s tools/fixtures/plan-bad-17-missing-touches.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-missing-touches.md > \"$T\" 2>&1 && grep -q locality \"$T\" && test -s tools/fixtures/plan-bad-17-locality-substring.md && ! python3 tools/validate-plan tools/fixtures/plan-bad-17-locality-substring.md > \"$T\" 2>&1 && grep -q locality \"$T\" && test -s tools/fixtures/plan-good-17-nice-to-have-unenforced.md && python3 tools/validate-plan tools/fixtures/plan-good-17-nice-to-have-unenforced.md > \"$T\" 2>&1 && grep -q PASS \"$T\" && grep -q \"^### Enforcement locality\" policy/acceptance-contract.md && grep -q \"exact-element\" policy/acceptance-contract.md && grep -q \"never substring\" policy/acceptance-contract.md && grep -q locality policy/plan-critique.md && echo T2_D29_OK'",
        "expected_signal": "terminal line exactly T2_D29_OK with exit 0",
        "environment": "repo checkout, Python 3, bash, no network; same command_resolution provenance as T1",
        "evidence": "validator output and witness transcripts under evaluation/evidence/v9.7-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, delete the locality check entirely — plan-bad-17-orphan-enforcement then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, apply the locality check to nice-to-have requirements too — plan-good-17-nice-to-have-unenforced then FAILs and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, accept an empty enforced_in array — plan-bad-17-missing-enforced-in then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, make the locality check compare requirement ids instead of paths — plan-bad-17-orphan-enforcement then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, make the path comparison a substring test rather than exact-element — plan-bad-17-locality-substring then PASSes and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete the locality entry from the stable defect-keyword contract in policy/plan-critique.md — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete every plan-bad-17-* locality fixture while leaving a permissive validator in place — the command must exit non-zero at the first test -s gate", "expected": "red"},
          {"mutation": "on a scratch copy, delete the ENTIRE '### Enforcement locality' section from policy/acceptance-contract.md while leaving the two field-table rows that mention enforced_in and touches intact — the command must exit non-zero. (Pass-1 verifier hostile probe: the two documentation legs were bare whole-file greps for tokens occurring 6 and 8 times, so gutting the section that defines the rule left the command green.)", "expected": "red"}
        ],
        "risk": "a locality check that matches on the wrong key (requirement id, task id, or substring) would PASS the exact wrong-repo plan it exists to reject, while looking green — the vacuity class this whole release is about",
        "negative_cases": [
          "a must requirement whose enforced_in path appears in no covering task's touches is rejected with keyword locality",
          "an empty or absent enforced_in on a must requirement is rejected",
          "an absent touches on a task covering a must requirement is rejected",
          "an uncovered nice-to-have requirement with unenforced paths still PASSes (deferred scope is not a locality defect)",
          "a path present in some non-covering task's touches does not satisfy the check",
          "a touched path that merely CONTAINS the enforced_in path as a substring does not satisfy the check",
          "a tree with the locality fixtures absent fails at the existence gate rather than passing on cannot-read diagnostics"
        ]
      }
    },
    {
      "id": "T3",
      "title": "D-31: re-approach fork — cap menu option 5, exhaustion-fork branch 4, decision table + checker",
      "deps": ["T1"],
      "contract": {
        "requirement_ids": ["R4"],
        "criteria": "policy/plan-critique.md gains re-approach as option 5 on the hard-2-pass-cap menu and as the fourth branch of the D-2 exhaustion fork, stating: plan and requirements retained, acceptance contracts re-authored, exactly one cycle charged, re-entry through Layer 1 required, and a hard bound of at most once per objective recorded in the ledger; ELIGIBILITY IS MECHANICALLY DERIVED, not judged — a re-approach is eligible iff every open blocker is contract-mechanics class AND no open blocker's finding cites a REQUIREMENT id (a blocker citing only task or contract ids is contract-mechanics by construction; a blocker citing an R-id means the requirement itself is in dispute and re-authoring contracts cannot answer it), so no field exists whose free-text filling decides eligibility; evaluation/fixtures/reapproach-fork.json encodes the decision table (eligible-first-selection ALLOW, second-selection-same-objective INELIGIBLE, non-contract-mechanics-blocker INELIGIBLE, blocker-cites-requirement-id INELIGIBLE, blocker-cites-task-id-only ELIGIBLE, IMPOSSIBLE-COMMAND verdict routes to re-approach); tools/check-reapproach-invariants.py (stdlib only) validates the table and its --selftest proves red/green discrimination, emitting exactly REAPPROACH_SELFTEST_OK, so a zero-byte or signal-less checker fails the command itself",
        "acceptance_command": "bash -c '[ \"$(python3 tools/check-reapproach-invariants.py --selftest)\" = \"REAPPROACH_SELFTEST_OK\" ] && test -s evaluation/fixtures/reapproach-fork.json && python3 tools/check-reapproach-invariants.py evaluation/fixtures/reapproach-fork.json && grep -q \"^  5\\. \\*\\*Re-approach (D-31)\\.\\*\\*\" policy/plan-critique.md && grep -q \"^  4\\. re-approach eligible\" policy/plan-critique.md && grep -q \"once per objective\" policy/plan-critique.md && grep -q \"routes here rather than to a\" policy/plan-critique.md && grep -q \"verdict is outstanding\" policy/plan-critique.md && grep -q \"cites a requirement id\" policy/plan-critique.md && echo T3_D31_OK'",
        "expected_signal": "terminal line exactly T3_D31_OK with exit 0",
        "environment": "repo checkout, Python 3, bash, no network; same command_resolution provenance as T1",
        "evidence": "checker output and witness transcripts under evaluation/evidence/v9.7-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, change the second-selection-same-objective row to ALLOW — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, change the non-contract-mechanics-blocker row to ALLOW — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, change the blocker-cites-requirement-id row to ALLOW — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, change the blocker-cites-task-id-only row to INELIGIBLE — the command must exit non-zero (the predicate must not reject healthy contract-mechanics blockers)", "expected": "red"},
          {"mutation": "on a scratch copy, replace check-reapproach-invariants.py with a zero-byte file — the command must exit non-zero (selftest-signal gate)", "expected": "red"},
          {"mutation": "on a scratch copy, delete the once-per-objective bound sentence from policy/plan-critique.md — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete the IMPOSSIBLE-COMMAND routing row from the fixture — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete the ENTIRE D-2 exhaustion-fork branch 4 from policy/plan-critique.md while leaving cap-menu option 5 fully intact — the command must exit non-zero. (Pass-1 verifier hostile probe h1: the criteria requires BOTH locations and the original four grep legs pinned neither independently, so deleting half the deliverable stayed green.)", "expected": "red"},
          {"mutation": "on a scratch copy, delete BOTH of this task's own IMPOSSIBLE-COMMAND mentions from policy/plan-critique.md while leaving sibling task T1's rule-17 mention of the same term intact — the command must exit non-zero. (Pass-1 verifier hostile probe h2: the bare token grep was satisfied entirely by a sibling task's unrelated sentence in the same shared file.)", "expected": "red"}
        ],
        "risk": "an unbounded re-approach option becomes a soft override — the same treadmill re-axed from plans onto verification strategies, which is the field report's own stated falsifier for this candidate",
        "negative_cases": [
          "a second re-approach selection on the same objective is INELIGIBLE",
          "a re-approach requested while any non-contract-mechanics blocker is open is INELIGIBLE",
          "a re-approach requested while any open blocker's finding cites a requirement id is INELIGIBLE — derived from the finding's cited ids, not from a judgment field",
          "a re-approach requested while every open blocker cites only task or contract ids is ELIGIBLE",
          "an IMPOSSIBLE-COMMAND verifier verdict routes to re-approach rather than to a work-defect retry",
          "a first eligible selection charges exactly one cycle and requires Layer-1 re-entry"
        ]
      }
    },
    {
      "id": "T4",
      "title": "R5a: migration + kernel/adapter sync so no installed surface teaches the removed duty",
      "deps": ["T2", "T3"],
      "contract": {
        "requirement_ids": ["R5"],
        "criteria": "both adapter SKILLs (adapters/claude-code/skills/agentfw/SKILL.md and adapters/codex/skills/agentfw/SKILL.md) state schema 1.7 as the schema of record, describe red_witness and the verifier-owned green evidence, describe enforced_in/touches, and list re-approach in the escalation menu; BOTH kernel bootloaders — adapters/claude-code/CLAUDE-block.md and adapters/codex/AGENTS.md — carry the same statements (the pass-1 blockers: the Claude bootloader was covered by no residual-duty grep, and the Codex bootloader, which carries the removed duty today at AGENTS.md line 66, was covered by nothing at all); the executing verifier surface adapters/claude-code/agents/agentfw-verifier.md carries the IMPOSSIBLE-COMMAND duty, because a duty stated only in policy is not on the surface the judge actually reads; NO adapter surface retains an instruction to author a witness tree at plan time, checked on all four surfaces; the AGENTFW-SYNC cross-adapter block remains byte-identical (check-skill-sync.py, whose --selftest signal is SKILL_SYNC_SELFTEST_OK and whose plain-run signal is SKILL_SYNC_OK); BOTH SKILLs still validate as single-block validator inputs, preserving the roundtrip property on each",
        "acceptance_command": "bash -c 'T=$(mktemp) && [ \"$(python3 tools/check-skill-sync.py --selftest)\" = \"SKILL_SYNC_SELFTEST_OK\" ] && [ \"$(python3 tools/check-skill-sync.py)\" = \"SKILL_SYNC_OK\" ] && python3 tools/validate-plan adapters/claude-code/skills/agentfw/SKILL.md > \"$T\" 2>&1 && grep -q PASS \"$T\" && python3 tools/validate-plan adapters/codex/skills/agentfw/SKILL.md > \"$T\" 2>&1 && grep -q PASS \"$T\" && grep -q \"1.7\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"1.7\" adapters/codex/skills/agentfw/SKILL.md && grep -q red_witness adapters/claude-code/skills/agentfw/SKILL.md && grep -q red_witness adapters/codex/skills/agentfw/SKILL.md && grep -q enforced_in adapters/claude-code/skills/agentfw/SKILL.md && grep -q enforced_in adapters/codex/skills/agentfw/SKILL.md && grep -q \"re-approach\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"re-approach\" adapters/codex/skills/agentfw/SKILL.md && grep -q red_witness adapters/claude-code/CLAUDE-block.md && grep -q red_witness adapters/codex/AGENTS.md && grep -q IMPOSSIBLE-COMMAND adapters/claude-code/agents/agentfw-verifier.md && ! grep -q \"planner-authored witness tree\" adapters/claude-code/skills/agentfw/SKILL.md && ! grep -q \"planner-authored witness tree\" adapters/codex/skills/agentfw/SKILL.md && ! grep -q \"planner-authored witness tree\" adapters/claude-code/CLAUDE-block.md && ! grep -q \"planner-authored witness tree\" adapters/codex/AGENTS.md && grep -q red_witness adapters/claude-code/agents/agentfw-plan-critic.md && ! grep -q \"planner-authored witness tree\" adapters/claude-code/agents/agentfw-plan-critic.md && ! grep -q \"re-execute BOTH witness\" adapters/claude-code/agents/agentfw-plan-critic.md && echo T4_SYNC_OK'",
        "expected_signal": "terminal line exactly T4_SYNC_OK with exit 0",
        "environment": "repo checkout, Python 3, bash, no network; check-skill-sync.py compares the two adapter SKILL files; same command_resolution provenance as T1",
        "evidence": "sync checker output, validator output on SKILL.md, and witness transcripts under evaluation/evidence/v9.7-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, change one word inside the AGENTFW-SYNC block in one adapter only — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, restore the phrase 'planner-authored witness tree' to either adapter SKILL — the command must exit non-zero (residual-duty guard)", "expected": "red"},
          {"mutation": "on a scratch copy, restore that phrase to adapters/claude-code/CLAUDE-block.md ONLY, leaving both SKILLs clean — the command must exit non-zero (pass-1 blocker 3, now regression-probed)", "expected": "red"},
          {"mutation": "on a scratch copy, leave adapters/codex/AGENTS.md entirely unmodified so it still teaches the removed duty — the command must exit non-zero (pass-1 blocker 4, now regression-probed)", "expected": "red"},
          {"mutation": "on a scratch copy, update the Claude Code SKILL only and leave the Codex SKILL on the old duty — the command must exit non-zero (single-adapter drift guard)", "expected": "red"},
          {"mutation": "on a scratch copy, delete the IMPOSSIBLE-COMMAND duty from adapters/claude-code/agents/agentfw-verifier.md — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, leave adapters/claude-code/agents/agentfw-plan-critic.md entirely unmodified so it still instructs the critic to re-execute BOTH witness legs against a planner-authored witness tree — the command must exit non-zero. (Found by T4's own producer while in scope-boundary: this was a SIXTH installed surface teaching the removed duty, and it was outside every task's declared scope because R5's enforcement-locality table omitted it.)", "expected": "red"},
          {"mutation": "on a scratch copy, corrupt the Codex SKILL's embedded plan block so it no longer validates — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, corrupt the Claude Code SKILL's embedded plan block so it no longer validates — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, replace check-skill-sync.py with a zero-byte file — the command must exit non-zero (selftest-signal gate)", "expected": "red"}
        ],
        "risk": "the documented prose/mechanical divergence class — an installed kernel that still instructs plan-time witness trees would keep producing the exact apparatus this release removes, and the next session reads the kernel rather than the repo",
        "negative_cases": [
          "a one-word divergence inside the cross-adapter sync block fails the check",
          "a residual witness-tree instruction fails the check on ANY of the four surfaces — both SKILLs and both kernel bootloaders — not merely on the two SKILLs",
          "an unmodified adapters/codex/AGENTS.md fails the check (it carries the removed duty today)",
          "a verifier agent definition without the IMPOSSIBLE-COMMAND duty fails the check",
          "each SKILL's own embedded plan block must still validate (roundtrip property preserved on both)",
          "a zero-byte sync checker fails the command rather than passing vacuously"
        ]
      }
    },
    {
      "id": "T5",
      "title": "R5b: provenance — CHANGELOG, release notes, CANDIDATES D-28..D-36 + rows, D-24 unfold, field-report disposition",
      "deps": ["T4"],
      "contract": {
        "requirement_ids": ["R5"],
        "criteria": "tools/check-candidates.py gains Falsifier as a REQUIRED per-entry schema label alongside its existing seven, so falsifier presence is validated inside each entry's own section body rather than counted file-globally (the pass-1 suggestion: nine Falsifier lines in one blob previously satisfied the check for all nine ids); CANDIDATES.md then carries full schema entries and status-board rows for D-28 through D-36, each with its own falsifier, with D-24 restated as unfolded into D-30 rather than folded into D-21; CHANGELOG.md carries a ^## v9.7.0 section naming the demotion, the locality check, and the re-approach fork; RELEASE-NOTES-v9.7.0.md exists and is non-empty; the field report's disposition section marks D-28/D-29/D-31 as built and the rest as proposed",
        "acceptance_command": "bash -c '[ \"$(python3 tools/check-candidates.py --selftest)\" = \"CANDIDATES_SELFTEST_OK\" ] && python3 tools/check-candidates.py --require-falsifier D-28 D-29 D-30 D-31 D-32 D-33 D-34 D-35 D-36 && python3 tools/check-candidates.py D-2 D-14 D-15 D-16 D-17 D-18 D-19 D-20 D-21 D-22 && grep -q \"^## v9.7.0\" CHANGELOG.md && test -s RELEASE-NOTES-v9.7.0.md && grep -q \"unfolded\" CANDIDATES.md && grep -q \"BUILT\" evaluation/field-report-2026-08-03-hermes-brain-apparatus-inversion.md && echo T5_DOCS_OK'",
        "expected_signal": "terminal line exactly T5_DOCS_OK with exit 0",
        "environment": "repo checkout, Python 3, bash, no network; same command_resolution provenance as T1",
        "evidence": "candidates checker output and witness transcripts under evaluation/evidence/v9.7-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": false,
        "risk_class": "none",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, blank the body of the D-28 section in CANDIDATES.md leaving the heading — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete the D-31 status-board row — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, truncate RELEASE-NOTES-v9.7.0.md to zero bytes — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete the Falsifier line from the D-33 entry only, leaving the other eight intact — the command must exit non-zero (per-entry, not file-global)", "expected": "red"},
          {"mutation": "on a scratch copy, move all nine Falsifier lines into a single block outside any D-2x section — the command must exit non-zero (the pass-1 hollow-passability path)", "expected": "red"},
          {"mutation": "on a scratch copy, revert check-candidates.py to its pre-v9.7 label set so Falsifier is not required — the selftest signal gate must fail and the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, make the Falsifier label unconditionally required rather than gated behind --require-falsifier — the legacy leg over D-2/D-14..D-22 must then fail and the command must exit non-zero. (Found post-implementation: an unconditional label broke the release gates of v9.3, v9.4, v9.5 and v9.6, all of which run check-candidates.py over pre-D-28 ids that carry no Falsifier. T5's own acceptance command could not see it because it only checked D-28..D-36.)", "expected": "red"}
        ],
        "risk": "provenance that claims a mechanism the repo does not carry, or a candidate board that accumulates proposals with no stated way to retire them — the framework's own over-accumulation failure",
        "negative_cases": [
          "a hollow D-28 heading with a blanked body fails check-candidates.py",
          "a missing status-board row for any of D-28..D-36 fails",
          "a zero-byte release-notes file fails the test -s leg",
          "a single entry missing its own Falsifier label fails, even when eight siblings carry theirs",
          "nine falsifier lines gathered outside any entry section satisfy nothing"
        ]
      }
    }
  ]
}
```

## Task graph and why it serializes

`T1 → {T2, T3} → T4 → T5`.

T1 lands first because it owns the schema-1.7 branch in `tools/validate-plan` and the witness
section of `policy/acceptance-contract.md`; T2 and T3 both build on that branch existing. T2 and
T3 then run in parallel on **disjoint files** — T2 owns `tools/validate-plan` and the
`acceptance-contract.md` field table; T3 owns `policy/plan-critique.md`, the new fixture, and the
new checker. The verifier's `IMPOSSIBLE-COMMAND` duty (R2) is deliberately placed in T1 rather
than T3, even though it is the thing that absorbs R4's risk, precisely so T2 and T3 do not both
edit `policy/acceptance-contract.md`.

The serialization is not caution for its own sake: `worktree_isolation` is `partial` / unverified
in the installed capability snapshot, so per the capability contract this plan assumes no platform
worktree isolation and never lets two concurrent workers hold the same file.

## Rollback

Every task is repo-local file editing on a git-clean tree. Rollback is `git checkout --` of the
task's declared paths, or `git revert` of the task's commit. No task is destructive, none rewrites
history, and none touches an installed runtime — installation to `~/.claude/skills/agentfw` and the
Codex runtime is a separate human-run release step outside this plan, after the release gate.

## Witness evidence (rev 1) — five red legs recorded, five green legs NOT recorded

**Red legs: recorded, all five, in 5 seconds.** Whole-command-only runs of each contract's exact
`acceptance_command` against a bare tree (the repo before any v9.7 deliverable exists), transcripts
with digests at `evaluation/evidence/v9.7-witness/T{1..5}-red.log`:

| Task | `command_sha256` (first 16) | exit | red for the right reason |
|---|---|---|---|
| T1 | `9ab105e34029a305` | 1 | defining IMPOSSIBLE-COMMAND paragraph deleted, 5 cross-refs left |
| T2 | `3f231b1a42db2eb3` | 1 | entire '### Enforcement locality' section deleted, field-table rows left |
| T3 | `c9b4a53a6502d566` | 1 | exhaustion-fork branch 4 deleted / T3's own IMPOSSIBLE-COMMAND mentions deleted, sibling T1 text left |
| T4 | `41ba79bed72a82da` | 1 | adapter SKILLs carry no 1.7 statement |
| T5 | `f709ee40d4c838f4` | 1 | RELEASE-NOTES-v9.7.0.md absent |

Recording them **caught two substrate defects in this plan's own contracts** before any review pass
spent on them: T4 addressed `SKILL.md` at the repo root, where no such file exists (the adapters
hold it at `adapters/{claude-code,codex}/skills/agentfw/SKILL.md`), and gated on
`check-skill-sync.py --selftest` emitting `SKILL_SYNC_OK` when it actually emits
`SKILL_SYNC_SELFTEST_OK`. Both are C0 substrate-grounding failures; both were free to find. **The
red leg pays for itself, which is why R1 keeps it.**

**Green legs: deliberately not recorded — and the measurement is the finding.** Sizing each witness
tree against the comparable artifact already shipped in this repo:

| Task | what a green tree must contain | measured comparable |
|---|---|---|
| T1 | a validator 1.7 branch + 4 plan fixtures | fixtures avg 53 lines each ⇒ ~300 |
| T2 | a validator locality check + 4 plan fixtures | ~270 |
| T3 | a working invariants checker + decision-table fixture | `check-delivery-invariants.py` is **317** + fixture **77** ⇒ ~400 |
| T4 | 1.7 statements in both adapter SKILLs + kernel block | ~60 |
| T5 | 9 CANDIDATES entries at full schema + CHANGELOG + notes | D-21's own entry is **72** lines ⇒ ~700 |
| | | **≈1,700 lines** |

**That is more than the ≈1,140 lines of apparatus in the field report that triggered this release**,
to prove five commands the actual workers will run for real within hours.

**This corrects Finding 9 of the field report.** The report predicted in-domain witness cost ≈ 0 and
attributed the hermes-brain blowup to out-of-domain promotion. The real variable is not the domain —
it is **whether the acceptance command checks behavior or content.** A behavior-checking command can
be satisfied by a small stub, which is why v9.5 and v9.6 felt free: their commands ran checker
selftests against compact JSON fixtures. A **content-checking** command — grep this policy section,
require these nine ledger entries — can only be satisfied by a tree that *contains the deliverable's
content*, so the witness tree converges on the deliverable itself. Documentation, policy,
configuration, and schema work produce content-checking commands almost exclusively. The mechanism
is most expensive exactly where this framework does most of its work, and v9.7 is the proof.

**Status: this plan is Layer-1 BLOCKED on five `witness` defects and nothing else.** Every other
Layer-1 check passes — structure, coverage, tier derivation, necessity tiers, dependency acyclicity,
command shape. The operator's fork is stated in the handoff below; the model does not clear its own
blockers.

## Deliberately out of scope

R6–R11 above. Also out: any change to input curation, the dual-critic lane, destructive-operation
authorization, or the delivery override's six-item safety floor — the field report found all four
working, and a release that removes machinery has no business quietly editing the machinery that
earned its place. Also out: renaming or re-tiering the verifier roles, and any throughput or
velocity target (the framework reports, never optimizes).
