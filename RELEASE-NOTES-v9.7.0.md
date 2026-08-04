# AgentFW v9.7.0 — verification placement

**Released:** 2026-08-04 · **Schema of record:** 1.7 (additive over 1.6) · **Gate:**
producer + independent-verifier acceptance commands per task, `tools/tests/validate-plan.sh`
green

## The field incident

Two sessions, two different repositories (`hermes-brain` and `chief-of-staff-dashboard`),
2026-08-02 → 2026-08-03, both governed by v9.6.0 installed to both runtimes. Both independently
produced **void witness pairs on their first attempt** under schema 1.6's plan-time
green-witness duty — one a stub module returning `'expected'`, the other a recorded "green" leg
that was never an end-to-end run. The measured cost that followed: **≈1,130–1,150 lines of
acceptance apparatus against a 163-line deliverable (≈7:1) across 4 Layer-2 passes that found
zero product defects.** The in-record control, same producer, same repo, same week: a 233-line
change shipped against 118 lines of ordinary tests (≈0.5:1), one round, zero rejections. The only
variable was where the "is this check any good?" question got asked.

Full evidence:
[field-report-2026-08-03-hermes-brain-apparatus-inversion.md](evaluation/field-report-2026-08-03-hermes-brain-apparatus-inversion.md).
Build plan: [PLAN-v9.7-verification-placement.md](PLAN-v9.7-verification-placement.md).

The structural diagnosis: schema 1.6 required the **producer** to prove its own acceptance
command at the point of maximum uncertainty about the implementation, with nothing independent
checking the tree until the scarcest budget in the system. The framework's own policy admitted the
mechanism it mandated was unverifiable exactly where it was mandated.

## What ships

- **D-28 — Witness-pair demotion.** Schema **1.7** removes the plan-time `witness_pair` GREEN leg.
  Every A2+ contract now carries a single `red_witness` (`tree`, `command_sha256`, `exit_code !=
  0`, `evidence_path`) — red-only, so a stub tree can never satisfy it. The green obligation moves
  entirely to the **verifier**: its whole-command run on the REAL tree is the green evidence of
  record. When the verifier cannot make a contracted command pass against a correct
  implementation, it returns **`IMPOSSIBLE-COMMAND`** — a *contract* defect routed to the D-31
  re-approach fork, never a work defect charged to the worker. Schema 1.6 plans keep validating
  unchanged (demonstrated by re-validating the shipped `PLAN-v9.6-operator-compass.md`).
- **D-29 — Enforcement-locality check at Layer 1.** Every requirement carries `enforced_in`
  (non-empty repo-relative paths); every task carries `touches`. The validator rejects, with
  defect keyword `locality`, any `must` requirement whose enforcement paths are not covered —
  exact-element, never substring — by a covering task. Cheapest check in the record with the
  largest measured saving: this very plan's rev-1 requirement table omitted a covering path for
  `adapters/codex/AGENTS.md` until a human judge found it by reading, which is the strongest field
  argument for building the check that would have caught it mechanically.
- **D-31 — The `re-approach` fork.** A fifth cap-menu option and a fourth D-2 exhaustion-fork
  branch: plan and requirements retained, acceptance contracts re-authored, cycle counter charged
  exactly once, plan re-enters Layer 1. Eligibility is mechanically derived — every open blocker is
  contract-mechanics class and none cites a requirement id — bounded to at most once per
  objective, recorded in the ledger, machine-checked
  (`tools/check-reapproach-invariants.py` + `evaluation/fixtures/reapproach-fork.json`).
- **Adapter & kernel propagation.** Both adapter `SKILL.md` files, both kernel bootloaders
  (`adapters/claude-code/CLAUDE-block.md`, `adapters/codex/AGENTS.md`), and the executing verifier
  surface (`adapters/claude-code/agents/agentfw-verifier.md`) state the demotion consistently; no
  installed surface retains an instruction to author a plan-time witness tree.
- **D-24 (proof-cost inversion) is UNFOLDED into D-30.** D-21's rationale note (2026-08-01) closed
  D-24 with no mechanism because every rendering it tried required an unenforceable cost
  threshold, and reserved a new id for a future mechanical rendering of the general case. This
  release found one: **D-30** measures the apparatus-to-deliverable ratio from the diffstat the
  verifier already has — mechanical, free, unfakeable, no new plan-block field, no threshold —
  reported in the verdict, with a named justification required only above 1:1. D-30 itself ships
  **proposed**, not built, in this release; the unfold is the provenance change.
- **Registered but not built (CANDIDATES.md, each with its own `Falsifier`):** D-30
  (apparatus-to-deliverable ratio), D-32 (change-delta input to assurance derivation, modulating
  controls within a tier only — never the tier, and never below an escalator floor without a
  named human-authorized relaxation), D-33 (vacuity floor relative to declared `risk_class` /
  `failure_surfaces`), D-34 (out-of-domain validation before a universal mandate, with a
  designated pilot objective), D-35 (multi-repo objectives — the fourth counter-reset laundering
  path D-22 didn't consider), D-36 (Layer-1 PASS reworded to *well-formed*, plus an
  assertion-presence lint).
- **Provenance mechanism.** `tools/check-candidates.py` gains `Falsifier` as an eighth *required*
  per-entry schema label, checked inside each entry's own section body — not counted
  file-globally. This closes a real hollow-passability path: nine `Falsifier` lines gathered
  anywhere in the file, even outside every entry section, previously would have satisfied a naive
  file-global count for all nine ids.

## What this build itself found — six vacuity defects in its own acceptance commands

This release is unusual among AgentFW's own build records in what its independent verifiers found
in the plan's OWN contracts, not just in the product the plan describes. Reported here as data,
not decoration, because the framework whose subject is "stop trusting acceptance commands you
haven't attacked" owes an honest account of what happened when its own commands got attacked.

**Six separate acceptance-command vacuity defects, all one class**, were found by independent
verifiers during this build — a `grep -q TOKEN file` leg where TOKEN also occurred:

- in a cross-reference elsewhere in the same file (a bare grep for `IMPOSSIBLE-COMMAND` satisfied
  by any of five incidental mentions, not the paragraph that defines the duty),
- in a sibling task's text sharing the same policy file (T3's own two mentions of
  `IMPOSSIBLE-COMMAND` were deletable while a sibling T1 sentence using the same term kept the
  command green),
- or in the fixture's own **filename**, echoed back by the validator's own diagnostic (a stub
  tree with no fixtures and a do-nothing validator emitted `T1_D28_OK` because the "cannot read
  …plan-bad-17-carrying-**witness**-pair.md" error line itself satisfied `grep -q witness`).

**Every one of these was found by executing a hostile implementation against the command — none
by reading the plan.** Rounds of prose review (approach-fit, necessity audit, plan-mechanics
reasoning) came back clean each time; the defects surfaced only when a judge built the thing that
would make the command lie and ran it.

**A cross-task contamination compounded this.** Four `red_witness`-isolation fixtures, built in an
earlier pass to isolate exactly the D-28 defect above, stopped isolating it once a sibling task
(D-29, locality) added its own requirement — those four fixtures carried no `enforced_in` /
`touches` fields, so disabling all four `red_witness` checks at once still left the whole command
red, just for an unrelated `locality` reason. The witness-isolation probe was passing for the
wrong reason and nobody noticed until the locality requirement landed beside it.

**The general lesson, stated once so it travels:** content-checking acceptance commands — grep
this section, require these nine ledger entries, confirm this phrase — must pin **discriminating
structure**: section headings, numbered lead-ins, phrases verified to live *inside the target
region*, never bare tokens. Verifying that a phrase is *unique* in a file is **not sufficient**; it
must additionally be verified to be *located in the region it claims to pin*. A behavior-checking
command (run a checker's `--selftest`, diff a decision table) is comparatively hard to fool this
way; a content-checking command over prose or a shared policy file is not, and this release's own
provenance work (T5, this task) is exactly that kind of command.

## Build provenance

- Plan: [PLAN-v9.7-verification-placement.md](PLAN-v9.7-verification-placement.md) — schema 1.6
  (the plan itself, dogfooding the outgoing schema for its own gate), A2, dual review tier. The
  plan carries a named, human-authorized relaxation of its own plan-time green-witness duty
  (recorded in the plan under "Named relaxation"), compensated by whole-command red witnesses for
  all five contracts plus mutation probes re-executed by the independent verifier on fresh scratch
  copies.
- Layer-2 pass 1 (dual) returned BLOCKERS on all five contracts, every one contract-mechanics
  class — the exact vacuity pattern described above, found by judges building hostile
  implementations rather than by reading. Rev 2 closed every blocker with existence-gated negative
  legs, structure-anchored greps, and new mutation probes regression-testing each finding.
- Every task's acceptance command, as extracted verbatim from the plan and run whole from the repo
  root, was independently re-verified against the real tree; mutation probes were re-executed on
  fresh scratch copies per the standing hazard this build itself surfaced.

## Honest limits

- D-30, D-32, D-33, D-34, D-35, D-36 are registered candidates, not shipped mechanisms; this
  release's "Counterweight check" explicitly deferred them because, unlike D-28/D-29/D-31, they
  could not be satisfied without an implementation existing yet.
- D-34 (out-of-domain validation before universal mandate) applies reflexively to this very
  release's own mechanisms: D-28/D-29/D-31 have so far been validated only against AgentFW's own
  fixtures and plans. No designated pilot objective outside this repo has exercised them yet.
- The six vacuity defects and the four-fixture cross-task contamination above are recorded as the
  honest cost of building a release about acceptance-command discipline; they were all caught
  before merge, not after, which is the independent-verification tier working as designed —
  but the rate at which this class of defect appeared in one release's own plan is itself a data
  point worth someone eventually holding against D-30's ratio.
