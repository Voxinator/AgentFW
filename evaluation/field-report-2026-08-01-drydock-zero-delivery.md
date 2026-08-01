# Field report — drydock zero delivery: two days, two runtimes, no features (2026-08-01)

**Reporter:** maintainer (Brian), 2026-08-01, from a transcript pasted into an AgentFW maintenance
conversation covering the drydock failure-routing workstream, 2026-07-30 → 2026-08-01. This is the
**execution half** of the drydock record; the
[scope-accretion report](field-report-2026-07-31-drydock-scope-accretion.md) (2026-07-31) is the
planning half. Same objective, same repo (`/Users/briantaylor/Projects/drydock`,
`docs/failure-routing-plan.md`), one day later and one layer down: the 07-31 report explains why
the plan kept growing; this one explains why nothing was ever built from it.

**Maintainer's summary (verbatim):** *"I've been on this treadmill with BOTH Claude code and
yesterday and most of today with Codex.. on the same problem.. and not even aware that it hadn't
produced a single fucking feature from the plan"*

**Evidence-substrate note:** the transcript was pasted into the maintenance conversation; **the
quotes and counts below ARE the durable record.** The drydock repo is local and IS a git
repository (verified 2026-07-31), but it moves; the cold-start commands say whether the live
substrate still matches. If it does not, trust this record as historical evidence and note the
drift.

## The accounting (the numbers that matter)

| Fact | Count |
|---|---|
| Review rounds spent on the receipt-authority sub-objective | **5** |
| What that sub-objective covers | **one clause of 1 of 13 requirements** |
| Sibling tasks dispatched | **0 of 12** |
| Failure-routing commits over the period | **~15, all governance artifacts** (plans, authorizations, verdicts, handoffs) — **zero product behavior** |
| Runtimes the treadmill ran on | **2** — Claude Code and Codex, roughly two days, **each restarting the counters** |
| Times the operator had to ask before learning the delivered-feature count was zero | **3, escalating** |
| Working, twice-adversarially-reviewed lines left stranded in a fixtures directory | **~1,300** |
| Blockers accumulated over the 5 rounds, none required to re-demonstrate failure | **6** |

## Finding 1 — no counter of delivered work existed (D-21)

Every governance counter in the framework measured **review spend**: cycles, Layer-2 passes,
verdicts. Nothing measured **delivery**. So five rounds of individually lawful review could run
with `workers_dispatched == 0` and no marker, digest, or gate message ever contradicted the
appearance of progress. The operator's own question — *how many features has this produced?* — had
no artifact that answered it; the answer had to be extracted by asking three escalating times, and
the answer was zero.

This is why the delivered-work counter, the `[SCOREBOARD: …]` marker at every gate event, and the
zero-dispatch tripwire ship together: a counter nobody is required to say out loud is a counter
nobody reads, and a fact nobody is forced to act on is a fact that changes nothing.

## Finding 2 — counters died at every session and runtime boundary (D-22)

The treadmill ran across BOTH runtimes over roughly two days on the same problem, and **each
runtime restarted the counters.** The sub-objective (`receipt-authority`) was itself a
decomposition of the parent objective, and decomposition minted a fresh budget the same way the
runtime hop did. The parent's 13 requirements starved while its sub-clause consumed the review
budget repeatedly — always lawfully, because every fresh context was genuinely at cycle 1 of
something.

Three cheap resets, all satisfying the letter of D-2's no-reset rule: **decompose, rename, hop
runtimes.** A budget any of those can re-mint is not a budget. The design consequence is stated
plainly in the v9.6 plan: counters and scoreboards CANNOT live in a session or a runtime — the
ledger must be a durable file beside the plan, keyed to the ROOT objective, that whichever runtime
touches the objective reads and writes.

## Finding 3 — fresh contexts planned on top of claims, not the world (D-25)

Each new session inherited plan headers, handoffs, and status prose asserting progress while the
repository contained zero implementation of the objective. Nothing required a resuming context to
check the claims against the tree before opening a new gate cycle, so the fiction propagated
forward one session at a time and the evidence that would have exposed it aged out of reach.

## Finding 4 — plan shape guaranteed the starvation (D-23, proposed)

The plan serialized all **12 sibling tasks** behind one sub-clause of one of its 13 requirements.
Once that sub-clause entered contested review, nothing else was dispatchable — not because anyone
decided to hold it, but because the dependency graph left no alternative. No check in C0–C6 attacks
dependency edges or asks what the first dispatch wave actually delivers end-to-end, so a
fully-serialized plan is indistinguishable at the gate from a deliverable one.

## Finding 5 — working code, stranded (D-26, proposed)

Roughly **1,300 working, twice-adversarially-reviewed lines** sat in a fixtures directory and were
never landed. They passed review; they were not the product; no rule said what happens to them. The
framework counts code that fails review and code that lands, and is silent about code that passes
review in a location that cannot ship.

## Finding 6 — blockers coasted on age (D-27, proposed)

**6 blockers** accumulated over the 5 rounds with no duty on anyone to re-demonstrate that they
still fail. Each round's fixes changed the artifact underneath the older findings; the findings
kept their standing unexamined, and re-litigating them spent cycles charged to the objective.

## Finding 7 — proof cost overtook the thing being proved (D-24, folded)

The apparatus built to prove the contested sub-clause repeatedly cost more than reading the
sub-clause would have — ~15 commits of plans, authorizations, verdicts, and handoffs against zero
product behavior. The diagnosis is real and has no mechanical rendering (any cost threshold is a
velocity opinion the framework has no standing to hold), so it is recorded inside D-21's rationale
rather than shipped as its own mechanism. The zero-dispatch tripwire is its enforceable shadow: the
one case where proof cost has provably overtaken delivery is detected mechanically and forced to a
human fork.

## Disposition

- **D-21 (delivery ledger, scoreboard & zero-dispatch tripwire)** — **BUILT 2026-08-01** by
  [PLAN-v9.6-operator-compass.md](../PLAN-v9.6-operator-compass.md): `policy/plan-critique.md`
  § Delivery ledger; decision table + `ledger_example` in
  `evaluation/fixtures/delivery-ledger.json`, enforced by `tools/check-delivery-invariants.py`.
- **D-22 (budget & ledger inheritance)** — **BUILT 2026-08-01**: counters live in the durable
  ledger keyed by `root_objective`; sub-objectives, renames, and cross-runtime resumes spend from
  the root ledger. Machine-checked by the `sub_objective_inherits_root_counters` case in
  `evaluation/fixtures/liveness-budget.json` + `tools/check-liveness-invariants.py`.
- **D-25 (session-start reconciliation)** — **BUILT 2026-08-01**: `policy/recovery.md` § 8, with
  the gate-entry cross-reference in `policy/plan-critique.md`; blocking four-step duty ending in
  `[RECONCILE: … MATCH|MISMATCH]`.
- **D-24 (proof-cost inversion)** — **FOLDED into D-21's rationale**; id retained, no standalone
  mechanism. See CANDIDATES.md § D-21 and § D-24.
- **D-23 (increment-shape check + dependency-edge audit + partial dispatch)** — newly **proposed**
  from Finding 4.
- **D-26 (stranded-implementation disposition)** — newly **proposed** from Finding 5.
- **D-27 (blocker re-validation on age)** — newly **proposed** from Finding 6.
- **D-17 (cross-substrate consult)** — unchanged; this report adds the cross-runtime treadmill as
  further evidence that runtime hops are currently unaccounted-for state transitions.

## Next-increment notes — hardening findings from THIS build's own verifiers

Recorded here rather than fixed in-flight, per D-18 (post-gate scope freeze). These are
verifier-reported, non-blocking check-strength gaps in the v9.6 build itself; they are honest
limits on what the v9.6 acceptance evidence proves:

1. **T1's acceptance greps are token-level and decoy-satisfiable.** A single decoy comment
   carrying the tokens (`<!-- TODO: SCOREBOARD zero-dispatch ledger.json -->`) keeps the command
   green on an otherwise-stripped policy file. The greps prove the tokens exist, not that the
   section does.
2. **The tripwire threshold constant is not machine-pinned against drift.** A fixture rewritten
   with `tripwire.zero_dispatch_cycles = 50` and its rows made internally consistent still passes;
   R3's "two or more completed cycles" lives in prose, not in a pinned constant the checker
   defends.
3. **T2's policy grep leg is cross-satisfied by D-21's text.** Deleting the entire D-22 amendment
   from `policy/plan-critique.md` leaves the command green, because `root_objective` still occurs
   in the D-21 section authored by a sibling task. The leg does not isolate the R4 amendment.
4. **The required inheritance case is satisfiable in name only.** The checker requires the case
   NAME `sub_objective_inherits_root_counters` and enforces the `root_objective`/`counters_reset`
   rule only when the key is PRESENT — so a case that carries the name while omitting
   `root_objective` everywhere still passes.

5. **RESOLVED during this build (2026-08-01):** the T5 acceptance command originally had the same token-grep weakness — deleting the entire `## D-22` entry section left it GREEN because cross-references elsewhere still carried the token. The T5 verifier REJECTED the contract on exactly this ground; the command was strengthened to run `tools/check-candidates.py` (which requires the section heading, schema labels, and board row per id) plus a `^## v9.6.0` CHANGELOG heading anchor, the witness pair was re-recorded, and the as-written section-deletion probe now goes red. The framework's own gate caught and closed its own weak check inside one build cycle.

Shape of the fix, for whoever picks it up: pin discriminating structure (section headings,
constants, case CONTENT) rather than tokens, and give each requirement's acceptance leg a surface
no sibling task can satisfy on its behalf.

## Cold-start verification

```sh
python3 tools/check-delivery-invariants.py --selftest                                   # DELIVERY_SELFTEST_OK
python3 tools/check-delivery-invariants.py evaluation/fixtures/delivery-ledger.json
python3 tools/check-liveness-invariants.py evaluation/fixtures/liveness-budget.json     # LIVENESS_OK
grep -n "SCOREBOARD\|zero-dispatch" policy/plan-critique.md | head
grep -n "RECONCILE" policy/recovery.md policy/plan-critique.md | head
python3 tools/check-candidates.py D-21 D-22 D-23 D-24 D-25 D-26 D-27                    # CANDIDATES_OK
ls /Users/briantaylor/Projects/drydock/docs/failure-routing-plan.md                     # the drydock plan artifact
```
