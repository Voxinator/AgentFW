# Field report — hermes-brain: the gate that reviews artifacts-about-judging (2026-08-03)

**Reporter:** maintainer (Brian), 2026-08-03, from two agent post-mortems pasted into an AgentFW
maintenance conversation, **revised 2026-08-04** after both sessions reviewed this report and
supplied measured corrections. The sessions ran 2026-08-02 → 2026-08-03 against the hermes-brain /
Chief-of-Staff dashboard workstream (**two different repos**), on **v9.6.0 installed to both
runtimes** (2026-08-01).

This is the third report in the treadmill series and the first taken **after** the v9.6 delivery
instruments shipped. The [scope-accretion report](field-report-2026-07-31-drydock-scope-accretion.md)
explained why plans grew; the [zero-delivery report](field-report-2026-08-01-drydock-zero-delivery.md)
explained why nothing was built from them and produced D-21/D-22/D-25. **This one explains what the
v9.6 instruments measured once they were live, and why the fork they route to could not treat it.**

**Maintainer's summary (verbatim):** *"for the second day in a row, the sessions burned limits on
testing apparatus rather than code. This was especially egregious 1000+ lines of testing apparatus
to prove ~50 lines of code?"*

## Evidence-substrate note — read this before citing any number

Three provenance tiers appear below and are labeled at point of use:

1. **Verified by this report.** Every claim about AgentFW's own policy text. The repo is
   byte-identical to the installed skill; every quotation and every cold-start command was executed
   (see Cold-start verification).
2. **Session-re-derived, maintainer-confirmed.** The LOC and ratio figures. The first draft of this
   report carried the sessions' *asserted* numbers ("~50 lines", ">1,000 lines across 6 files"); both
   sessions then re-derived them from `git diff --stat` against their real trees and **the assertions
   were overstated by ~3× in the direction that flattered the finding.** The corrected numbers are
   used throughout and were **confirmed by the maintainer on 2026-08-04**. One honest limit remains
   for a third party: **the ref `d1c1c7e` is not present in `~/Projects/hermes-brain` (4 commits, no
   matching object) nor in `~/Projects/chief-of-staff-dashboard`**, so the session tree must be
   identified before the diffstat can be re-run from this record. That gap is recorded rather than
   papered over — a report whose one-line finding is *every real defect came from something executing
   against real code* does not get to leave its own headline numbers unlabeled.
3. **Session-asserted, not re-derived.** Round counts, per-round verdicts, and defect attributions.

The two sessions' independent counts of the same six-file acceptance apparatus differ by ~2%
(1,128 itemized vs 1,149 total, a `wc -l`-vs-insertions counting difference). Both are used as
"≈1,130–1,150"; the ratio is insensitive to the difference.

## The accounting

| Fact | Session A | Session B |
|---|---|---|
| Gate rounds spent before anything shipped | **4 Layer-2 passes / 2 cycles** | **5 rejections** |
| Product defects found by plan critique | **0** | **0** (rounds 1–3, 5) |
| Product defects found by the independent verifier | **1** (write amplifier) | **all of them** |
| Deliverable | **163 insertions** (`brain.py` 48, `brain_server.py` 126) — the *functional* delta is ~50 lines; the rest is rationale comment | one requirement's enforcement clause |
| Genuine acceptance apparatus | **≈1,130–1,150 across 6 files** (`wire_baseline` 256, `recall_endpoint_acceptance` 236, `b3_acceptance` 202, `verify_restore` 155, `consumer_replay` 153, `registry_fault_acceptance` 126) | digest-pinned scripts, stub witness modules |
| All test-tree lines touched | **2,350 across 11 files** | — |
| **Apparatus : deliverable** | **≈7:1** (≈14:1 counting the whole test tree) | — |
| Mutation probes passed first attempt | **all product-directed probes (R1–R3), both verifier rounds** — two *apparatus/R7* probes stayed green in round 2 (edited pinned script; removed `k` clamp) | 17/17, once finally run post-implementation |
| Time to ship once the proof apparatus was abandoned | **one turn** | immediate |
| Work that shipped **outside** the formal gate | git baseline, restore rehearsal w/ measured RTO, backup hardening, registry | — |

### The natural experiment — same producer, same repo, same week, same framework

| | `/health` work | the gated item |
|---|---|---|
| Deliverable | **233 lines** | **163 insertions** |
| Test code | **118 lines** (`test_health_markers.py`, ordinary tests) | **≈1,130–1,150** (acceptance apparatus) |
| Ratio | **≈0.5:1** | **≈7:1** |
| Rounds | **1** | **4 passes / 2 cycles** |
| Rejections | **0** | **4** |
| Assurance | **A1, ungated** | **A3, gated** |

The only variables were the assurance tier and an explicit instruction that **nothing's job is to
prove another script ran.** A larger deliverable with a fourteenth of the test mass shipped in one
round. **0.5:1 ungated-A1 versus 7:1 gated-A3 is the empirical spine of D-30 and D-32** — an
in-record natural experiment rather than an argument.

**The core datum:** the gate was not catching bad work; it was generating work. The single item that
entered the gate cycled four times on its own proof machinery, and shipped in one turn when the
demand "prove the acceptance command is strong" was replaced with "write one ordinary test."

## Finding 1 — the framework documents that the mechanism it mandates is unverifiable where it is mandated

`policy/plan-critique.md` rule 16 closes with: *"Layer 1 does not judge witness-tree honesty — that
is C2's duty."* Restated in `policy/acceptance-contract.md` § Schema 1.6: the validator *"does NOT
check: the honesty of the witness tree (a C2 judge duty …)"*.

So schema 1.6 requires the **producer** to author witness trees and both evidence legs before
Layer-2 dispatch; admits Layer 1 cannot check them; and defers the check to the scarcest budget in
the system — where C2's probe duty is not to read the record but to **re-execute both legs itself**
(`plan-critique.md` C2). Cost is front-loaded on the producer at the point of **maximum uncertainty
about the implementation**; the check is back-loaded onto a 2-pass cap.

Both sessions produced **void witness pairs on their first attempt** — independently, in different
repos. Session A's were stub modules returning `'expected'`; session B's recorded green legs were
never end-to-end runs.

**What that convergence does and does not prove.** Two disjoint *judges* converging is strong
evidence because they are adversarial and independent. Two *producers* failing identically under the
same instruction is **correlated failure from a common cause** — it is strong evidence that
*"prove my command can pass"* has a trivially satisfiable reading and that nothing independent
checks which reading was used, but it is evidence of **instruction ambiguity**, not the
judge-lane badge. Stated at its actual strength: the mechanism's most natural misreading is also its
cheapest, and the framework has no check positioned to catch it.

## Finding 2 — the witness pair is a curation leak, not only a cost

The bright line: *"the judge receives the plan + requirements ONLY — never the planner's exploration
reasoning"* (`plan-critique.md` § Layer 2). `witness_pair` is a **producer-authored artifact
asserting that the producer's own acceptance criteria are sound**, and C2's duty routes the critic
through the producer's witness tree — a tree built specifically to make that command go green.

That is [Self-Review](../policy/anti-patterns.md) with one indirection: *"the producing context runs
the verification of record on its own output … it checks for what it intended, not what happened."*
The catalog's own fix — *"verdicts of record come from a fresh, input-curated context that evaluates
artifacts cold"* — is precisely what both sessions concluded independently. Session B's phrasing:
*"The framework already has the right answer and I routed around it… I substituted a hash for a
judge."*

## Finding 3 — the regress is structural, and the schema pins the cheap half

`command_sha256` digests the `acceptance_command` **string**. The trusted surface of any run also
includes the interpreter, `sys.path`, environment, oracle files, and subprocesses — and that surface
is `environment`, a free-form non-empty string nothing checks.

A command's trustworthiness is relative to its trusted computing base; making the command
self-vouching means pinning the TCB; pinning it requires more command, which enlarges the TCB.
**There is no fixed point.** This predicts the observed shape exactly: session A shrank the forgeable
surface three times and a critic found the next layer each time; session B's rounds 1, 2, 3 and 5
were *"the same defect relocating"* (wrong repo → greppable tally string → digest without import
path/env/subprocess → daemon identity by substring). Neither session executed badly. Both were
searching for a fixed point that does not exist.

Adversarial review of a harness has no natural floor, and critics are correctly instructed not to
soften a blocker into a suggestion. Applied to proof apparatus, review terminates when the budget
exhausts, not when the artifact is adequate.

## Finding 4 — proportionality is in the catalog and has no gate hook

`policy/anti-patterns.md` § Complexity Accumulation gives the tell as *"harness scaffolding /
outweighing the work product"* (the phrase wraps lines 22–23), and says explicitly *"This applies to
this framework's own machinery."* ≈1,140 lines of apparatus for a 163-line deliverable is the
textbook instance.

The C0–C6 rubric contains exactly one proportionality clause: three words (*"harness proportional"*)
inside C4's pass-test, whose stated scope is destructive-plan pre-mortems. **For non-destructive work
it never fires.**

The asymmetry is total. Every C-check adds obligations. C6 is the only subtracting mechanism, built
deliberately as *"the structural counterweight to a critique gate that otherwise only adds"* — and it
subtracts **requirements**, never **apparatus**. D-19 built the counterweight one level too high.

This is D-24 (proof-cost inversion) recurring after being folded. The fold's reasoning was that *"any
cost threshold is a velocity opinion the framework has no standing to hold"* and that the
zero-dispatch tripwire is its enforceable shadow. Finding 6 is why the shadow was insufficient; D-30
below is a rendering that survives the fold's objection intact.

## Finding 5 — C2 asks a question that cannot be answered at plan time

*"Can this command pass against a wrong implementation?"* requires an implementation to attack. At
plan time the critic must construct hostile implementations — expensive, speculative — and it forces
the acceptance harness to be essentially complete before planning can conclude. **Planning silently
became building the test harness.** The phase boundary is in the wrong place.

The contrast inside the same sessions is the control: the independent verifier found the real product
defect in one pass, because there was code to attack; session B's 17 mutation probes became real
verification immediately once run post-implementation. `mutation_probes` — already in the schema at
rule 13 — cannot be faked by a stub, because a stub trivially fails to be red. **The right tool is
already in the framework, positioned one phase too early for the green leg and one phase too late for
the discriminating one.**

## Finding 6 — the v9.6 tripwire fired correctly and routed to a menu with no matching entry

Session A reached two completed cycles with zero workers dispatched — precisely D-21's zero-dispatch
tripwire condition, which *"immediately force[s] the D-2 exhaustion fork — even when liveness budget
remains."* **The instrument worked.** The fork it forces offers three options: proactive delivery
override, explicit rescope, or halt. The D-2 cap menu offers four: extend by one pass, mutation-gated
dispatch, assumption-gated dispatch, halt.

Neither menu contains the move that was actually correct: **the plan is sound; the verification
strategy is wrong; change the approach.** Both menus assume the plan is the defective artifact. The
session had to construct a bespoke named relaxation (`plan-critique.md` § Compose/stop) and the
operator had to authorize it — so **the framework charged a human authorization for the right answer,
at the exact moment its own newest tripwire had just fired.**

v9.6 measures this treadmill. v9.5 causes this instance of it.

## Finding 7 — assurance has no change-delta axis, and escalators mechanically override the one question that comes closest

`policy/assurance-model.md` Q1 does ask *"what does this touch; can it be trivially undone?"* — so
reversibility **is** asked. Two gaps remain:

1. **Size and additivity are asked nowhere.** No question distinguishes an additive,
   optional-parameter, compatibility-guaranteed change from a rewrite of the same component.
2. **The escalator list overrides Q1's answer mechanically.** *"production / live infrastructure"*
   bumps to ≥A3 unconditionally, whatever Q1 concluded about reversibility. The calibration paragraph
   that tries to soften this (*"a routine, reversible multi-file refactor with strong tests is A2, not
   A3"*) is prose against a mechanical list.

Session A's contested item was additive with a compatibility guarantee — landing in a shared live
daemon. Escalator fires; A3; dual judges; witness pairs; four passes. The `/health` control in the
same repo the same week: A1, ungated, one round, 0.5:1.

**Correction to the session's own framing (retained deliberately):** the session contrasted the gated
item with a docker operation run ungated against the database holding the only copy of the memory.
That operation is **destructive by operation type** (`assurance-model.md` § Effect classification),
which floors it at A3 + adversarial + explicit authorization. That it ran ungated and went fine is a
**gate bypass that got lucky**, not evidence of good calibration, and citing it would have weakened
the finding. The finding is the missing delta axis and the mechanical escalator override.

## Finding 8 — the vacuity floor has no risk relation, and the obvious fix weakens a floor

*"Demonstrated-vacuous acceptance command"* is one of six non-waivable safety-floor classes
(`plan-critique.md` § Human delivery override). Correct in spirit. Combined with Findings 3 and 4, a
sufficiently determined critic can always place a producer at the floor with no override available,
because the forgeable surface is unbounded.

The session proposed making vacuity risk-relative. As stated that opens a safety floor to
relitigation. **Stronger form:** keep the class non-waivable and define *vacuous* as **failing the
contract's own declared `risk_class` and `failure_surfaces`** — structured fields that already exist
and already drive tier derivation. Vacuity becomes relative to declared risk with no new judgment
axis and no new field: a smoke test is vacuous for `risk_class: security`, adequate for `none`.

## Finding 9 — the witness pair was validated in-domain and promoted to a universal A2+ mandate

Every witness-pair artifact in this repo is AgentFW's own validator fixture material —
`evaluation/evidence/witness-pair-upgrade-2026-07-31/witness-red-plan-bad-16-*`,
`evaluation/evidence/v9.6-witness/T*-red.log`. That is a domain where acceptance commands are
stdlib Python over fixture JSON and *"the command is the whole system"* is very nearly true, so
witness-tree authoring cost rounds to zero and the forgeable surface is genuinely small.

The mechanism was then shipped as **mandatory for every A2+ contract**. These two sessions are its
first out-of-domain use, against a live daemon, a graph database, and a cross-repo consumer. The
process finding generalizes past this feature: **a mechanism validated only where its cost is near
zero should not acquire a universal mandate in the same release.**

## Finding 10 — no multi-repo support anywhere in the ledger model

The root ledger, sub-objective inheritance, and every D-21/D-22 counter assume **one tree**:
`<plan>.ledger.json` sits beside the plan, and `root_objective` keys a budget within it. Session B's
objective spanned **two repos plus a third consumer**. Consequences observed:

- Cross-language constant drift between repos was caught by a **critic**, not by any framework
  mechanism — there is no cross-repo equivalent of C3's shared-derived-value reconciliation.
- The **handoff document was invented ad hoc** because nothing in the framework covers carrying an
  objective across trees.
- D-22 closed the three cheap counter resets (decompose, rename, hop runtimes). **Hopping repos is a
  fourth** and is currently unaccounted for: a sibling repo's plan is a different plan file, hence a
  different ledger path, hence a fresh budget.

## Finding 11 — a Layer-1 PASS reads as "the plan is good"; it means "the plan is well-formed"

Every plan that got blocked in both sessions **passed Layer 1 first.** The validator's own honest
limit says this plainly (*"A Layer-1 PASS raises the floor; it green-lights nothing semantically"*),
but the signal reaching a producer is a green `PASS` at the moment of maximum willingness to proceed.

The concrete gap is the schema-1.3 known-weak-command lint (rule 13), which rejects three shapes: a
pipe before a gating `&&`, a non-`&&`-preceded success `echo`, and a non-terminal success `echo`.
Session B's command `bun test <file> && tsc && echo OK` **passes all three** — and is satisfied by a
**zero-byte test file**. The most common real vacuity in practice (a test invocation with no
assertions in it) is invisible to a lint built around shell shape.

This is the direct companion to Finding 5: the cheap mechanical layer checks the thing that is easy
to check, the expensive semantic layer is asked the thing that cannot be answered yet, and the gap
between them is where four rounds went.

## What worked — and it is most of the executing framework

Recorded so the report is not read as a verdict on the whole system. Both sessions volunteered this
independently:

- **Input curation held under pressure.** Dual disjoint critics converged repeatedly on the same
  real defects without seeing each other's verdicts — the write amplifier, a void baseline, an
  invalid `work:tribal` group id, an armed `DETACH DELETE` that a producer bug was accidentally
  masking.
- **"Run it, don't read it" caught every real defect**, including a `set -e` / `/dev/tty` interaction
  that would have killed the nightly backup, and a `/refresh` 502.
- **Destructive-operation authorization discipline held** and prevented a live delete.
- **Verify-against-the-running-system overturned a large number of confident assumptions**, the
  producers' own included.

**The one-line finding: every real defect across both sessions came from something executing against
real code. None came from reviewing a plan's description of how it would later be tested.**

## Producer-side errors (not framework defects)

Both sessions were explicit about their own share, and the framework criticism stands independently
of it: over-building beyond what "strong acceptance command" required; treating two critics' *"your
command is forgeable"* as a requirement to satisfy rather than a signal the apparatus was mis-sized;
never asking whether a ~1,140-line harness was proportionate to a 163-line change; shipping a
`SystemExit` refusal that printed `REFUSING` and deleted the data anyway; planning a chunk in a repo
no task owned; recommending a rename backwards without checking consumers; flagging a safety cap as a
correctness nit, which produced the write amplifier. **And asserting a ~20:1 ratio that measurement
put at ~7:1** — an error in the direction that flattered the complaint, corrected above.

A meaningful share of the round count is the gate catching real producer errors — that is the gate
working. The framework charge is narrower and survives: **it made those errors expensive to discover
by requiring effort in the wrong order.**

## Disposition — candidates, now registered in CANDIDATES.md (updated 2026-08-04)

Ranked by expected saving against these two sessions. **Every candidate carries a falsifier**, because
a series that accumulates candidates across three reports while arguing against complexity owes the
maintainer a way to retire its own proposals. Full schema entries + status-board rows for all nine
now live in [CANDIDATES.md](../CANDIDATES.md); the disposition below records what shipped versus what
remains proposed as of the v9.7.0 build.

**BUILT, this release ([PLAN-v9.7-verification-placement.md](../PLAN-v9.7-verification-placement.md),
v9.7.0, 2026-08-04): D-28, D-29, D-31.** The remaining six (D-30, D-32, D-33, D-34, D-35, D-36) are
proposed only — registered in CANDIDATES.md with their falsifiers, deliberately deferred because,
unlike the three BUILT here, they could not be satisfied without an implementation existing yet (see
the plan's "Counterweight check").

- **D-28 · Witness-pair demotion — BUILT in v9.7.0.** (Findings 1, 2, 3, 5) — green witness moves to the **verifier**;
  `mutation_probes` becomes the plan-time discriminating duty. The red witness stays (cheap, honest).
  Rationale: a mutation probe is red-only and therefore stub-proof, so the exact failure both sessions
  produced on first attempt becomes unconstructible. Addresses session B's rounds 1, 2, 3, 5.
  **The trade, stated rather than left for the reader:** the green witness exists to reject commands
  that can *never* pass. Demoted, that risk lands on a worker, who can burn an implementation cycle
  against an impossible command before anyone notices. What absorbs it: (a) the retained red witness
  is still one end-to-end run, and an impossible command usually fails *differently* — import error,
  missing binary, bad path — visibly in the red transcript; (b) D-29 catches the largest real class
  (the command targets a file or repo no task touches). **Residual risk is one implementation cycle
  on one task, and it is not zero** — priced against ~1,140 lines of measured apparatus.
  *Falsifier:* post-demotion, verifiers report green without re-execution evidence (rubber-stamping
  the leg they now own), or impossible-to-pass commands reach workers at a rate whose burned cycles
  exceed the apparatus cost saved.
- **D-29 · Enforcement-locality check at Layer 1 — BUILT in v9.7.0.** (Findings 5, 11) — per requirement: *which file
  enforces this, and does a task's declared scope touch that file?* Mechanical, near-free, kills
  wrong-repo plans before any apparatus exists. Currently only surfaces via C5 at Layer 2, after the
  trees are built. **Cheapest check with the largest saving in this record**, and neither session
  proposed it independently of the other's report.
  *Falsifier:* the question has no single honest answer for a majority of real requirements
  (config-driven enforcement, generated code, cross-cutting policy), making the check a false-positive
  generator rather than a filter.
- **D-30 · Apparatus-to-deliverable ratio, measured at verification time** (Finding 4, D-24 unfold) —
  **the two sessions disagreed here and this is the synthesis.** Session A proposed declaring the
  ratio in the plan block and justifying it above 1:1; session B objected that *neither quantity is
  knowable at plan time* — which is precisely the defect Finding 5 diagnoses in C2, reintroduced one
  section later, and declared by the same producer who over-built. **Resolution: no plan-block field
  and no threshold.** The verifier computes the ratio from the diffstat it already has — mechanical,
  free, unfakeable, no new schema field — reports it in the verdict at each round, and a ratio above
  1:1 requires a named justification in that verdict, feeding the next increment's C6 and serving as
  an input to the D-31 re-approach fork. This survives the original fold reasoning intact: a measured
  ratio is not a velocity opinion, and no threshold is set.
  *Falsifier:* measured ratios cluster indistinguishably across gated and ungated work (no signal), or
  high ratios correlate with *caught defects* rather than with treadmills — in which case the ratio is
  measuring thoroughness, not waste.
- **D-31 · `re-approach` fork option — BUILT in v9.7.0.** (Finding 6) — added to BOTH the 2-pass cap menu and the D-2
  exhaustion fork: *plan retained, verification strategy replaced, contracts re-authored, cycle
  counter charged once.* Without it the correct move costs a bespoke relaxation plus a human turn.
  *Falsifier:* it is selected more than once per objective, i.e. it becomes the soft override — the
  same treadmill re-axed onto verification strategies instead of plans.
- **D-32 · Change-delta input to assurance derivation** (Finding 7) — size and additivity, which Q1
  does not ask (Q1 does ask reversibility; the report's first draft overstated this and is corrected).
  **Load-bearing specification:** the delta axis modulates **controls within a tier**, never the tier
  itself. Lowering below an **escalator floor** requires a named relaxation with explicit human
  authorization, exactly as any other floor relaxation. Without that clause D-32 opens the "it's only
  a small change to production" hole the escalators exist to close.
  *Falsifier:* delta-derived control relaxation lets a defect reach production that the
  escalator-derived controls would have caught.
- **D-33 · Vacuity floor relative to declared risk fields** (Finding 8) — floor class retained;
  *vacuous* defined against the contract's own `risk_class` / `failure_surfaces`.
  *Falsifier:* a command passing the risk-relative test ships a defect the absolute test would have
  blocked.
- **D-34 · Out-of-domain validation before universal mandate** (Finding 9) — a mechanism validated
  only against AgentFW's own fixtures ships **advisory** until one out-of-domain evaluation has run.
  Sibling of the Adapter Sprawl rule (*"an adapter you haven't tested is a profile you're lying
  about"*), applied to policy mechanisms rather than platform bindings. **Bootstrapping problem,
  named:** if a mechanism is advisory, who exercises it? These two sessions only exercised witness
  pairs *because they were mandatory*. The candidate is incomplete without a **designated pilot
  objective named at release time**, or the advisory period never ends and the tier becomes a
  graveyard.
  *Falsifier:* advisory mechanisms are never voluntarily adopted, confirming that the tier defers
  adoption rather than de-risking it.
- **D-35 · Multi-repo objectives** (Finding 10) — ledger and counters keyed to an objective that spans
  trees; repo-hopping closed as the fourth counter reset; a cross-repo analogue of C3's
  shared-derived-value reconciliation for constants duplicated across languages.
  *Falsifier:* cross-repo objectives are rare enough that the ledger complexity exceeds the drift it
  prevents — which would make this Complexity Accumulation wearing the framework's own badge.
- **D-36 · Layer-1 PASS semantics + assertion-presence lint** (Finding 11) — rename or re-word the
  PASS signal so it reads as *well-formed*, not *good*; extend the weak-command lint past shell shape
  to the case it currently misses (a test invocation whose target contains no executed assertions —
  the zero-byte-test-file class).
  *Falsifier:* the strengthened lint rejects legitimate commands more often than it catches vacuous
  ones.
- **D-24 (proof-cost inversion)** — **UNFOLD proposed**; see D-30.
- **D-17 (cross-substrate consult)** — unchanged; both sessions again show correlated critics
  converging on apparatus rather than product.

## Cold-start verification

All commands below were executed against this repo on 2026-08-04 and pass as written.

```sh
grep -n "does not judge witness-tree honesty" policy/plan-critique.md          # Finding 1
grep -n "honesty of the witness tree" policy/acceptance-contract.md            # Finding 1
grep -n "plan + requirements ONLY" policy/plan-critique.md                     # Finding 2
grep -n "command_sha256" policy/acceptance-contract.md                         # Finding 3
grep -n "harness scaffolding" policy/anti-patterns.md                          # Finding 4 (phrase wraps 22-23)
grep -n "own machinery" policy/anti-patterns.md                                # Finding 4
grep -n "harness proportional" policy/plan-critique.md                         # Finding 4 (sole hook, C4)
grep -n "otherwise only adds" policy/plan-critique.md                          # Finding 4 (C6 scope)
grep -n "zero-dispatch tripwire" policy/plan-critique.md                       # Finding 6
grep -n "production / live infrastructure" policy/assurance-model.md           # Finding 7
grep -n "trivially undone" policy/assurance-model.md                           # Finding 7 (Q1 asks reversibility)
grep -n "demonstrated-vacuous" policy/plan-critique.md policy/assurance-model.md  # Finding 8
ls evaluation/evidence/witness-pair-upgrade-2026-07-31/ evaluation/evidence/v9.6-witness/  # Finding 9
grep -n "green-lights nothing" policy/plan-critique.md                         # Finding 11 (wraps 161-162)
diff -q policy/plan-critique.md ~/.claude/skills/agentfw/policy/plan-critique.md  # installed == repo
```

**Not verifiable from this repo — identify the tree first.** The LOC figures require the session
trees, and `d1c1c7e` resolves in neither `~/Projects/hermes-brain` nor
`~/Projects/chief-of-staff-dashboard`:

```sh
git diff --stat d1c1c7e..main -- brain.py brain_server.py     # deliverable: expect 163 insertions
wc -l wire_baseline* recall_endpoint_acceptance* b3_acceptance* \
      verify_restore* consumer_replay* registry_fault_acceptance*   # apparatus: expect ~1,130-1,150
wc -l test_health_markers.py                                  # control: expect 118
```
