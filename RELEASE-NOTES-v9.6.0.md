# AgentFW v9.6.0 — the operator compass

**Released:** 2026-08-01 · **Schema of record:** 1.6 (unchanged) · **Gate:**
`tools/tests/release-v9.6.sh` (deterministic, green at tag time)

## The field incident

The drydock failure-routing workstream, 2026-07-30 → 2026-08-01: **five review rounds on one
clause of 1 of 13 requirements; 0 of 12 sibling tasks dispatched; ~15 commits, all governance
artifacts, zero product behavior — across BOTH runtimes (Claude Code and Codex) over roughly two
days, each runtime restarting the counters.** The operator learned the delivered-feature count
was zero only by asking three escalating times. Maintainer's summary, verbatim: *"I've been on
this treadmill with BOTH Claude code and yesterday and most of today with Codex.. on the same
problem.. and not even aware that it hadn't produced a single fucking feature from the plan."*

Full evidence:
[field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md)
(execution half) and
[field-report-2026-07-31-drydock-scope-accretion.md](evaluation/field-report-2026-07-31-drydock-scope-accretion.md)
(planning half).

The structural diagnosis: every counter the framework kept measured review **spend** (cycles,
passes, blockers); nothing measured **delivery** — and the counters that did exist lived in
conversation, so every new session and every runtime hop restarted them.

## What ships

- **D-21 — Delivery ledger, scoreboard & zero-dispatch tripwire.** A durable
  `<plan>.ledger.json` beside every A2+ plan (`objective`, `root_objective`, `cycles`,
  `layer2_passes`, `workers_dispatched`, `tasks_verified`, append-only `gate_events` each naming
  its writing runtime; both runtimes read/update one file). A
  `[SCOREBOARD: objective <slug> — musts built b/t · workers dispatched w · verified v · cycle
  n/2 · passes m/4]` marker at EVERY gate event, rendered in plain language in the D-20 operator
  digest, counts derived from the ledger and `validate-plan --digest` — never narration. And the
  tripwire: **≥2 completed gate cycles with `workers_dispatched == 0` immediately force the D-2
  exhaustion fork even when budget remains**, latching until work dispatches. Machine-checked:
  `evaluation/fixtures/delivery-ledger.json` + `tools/check-delivery-invariants.py`.
  **D-24 (proof-cost inversion)** is recorded as folded into D-21's rationale — no mechanical
  rendering exists for the general "apparatus costs more than review" case; the tripwire is its
  enforceable shadow.
- **D-22 — Budget & ledger inheritance.** Liveness counters are not session state: they live in
  the ledger keyed by `root_objective`, and sub-objectives, renames, re-plans, and cross-runtime
  resumes spend from the ROOT ledger. Counters never reset on decomposition; liveness markers
  name the root slug. Enforced by the extended `tools/check-liveness-invariants.py`
  (`sub_objective_inherits_root_counters` required case; any rooted row with `counters_reset:
  true` rejected).
- **D-25 — Session-start reconciliation.** A blocking four-step duty before any new gate cycle
  on a resumed A2+ objective: read the ledger at its root, re-derive observed state with
  mechanical probes (validator run, evidence-file presence, repo greps), emit
  `[RECONCILE: objective <slug> — ledger claims X, observed Y — MATCH|MISMATCH]`, and on
  MISMATCH correct the ledger FIRST. Claimed-verified tasks with absent evidence revert to
  unverified; corrections only move toward observed reality and never spend down
  `cycles`/`layer2_passes` (the ratchet). Machine-checked:
  `evaluation/fixtures/reconcile.json` + `tools/check-reconcile-invariants.py`.
- **Adapter & kernel propagation.** The duties land inside the AGENTFW-SYNC block of both
  adapter `SKILL.md` files (byte-identity enforced by `tools/check-skill-sync.py`) and both
  kernel bootloaders name the scoreboard.
- **Registered but not built:** D-23 (increment-shape check + dependency-edge audit + partial
  dispatch), D-26 (stranded-implementation disposition), D-27 (blocker re-validation on age) —
  proposed in CANDIDATES.md with the drydock evidence attached.

## Build provenance (the release dogfooded itself)

The build ran under the full v9.5 gate plus the mechanism it was building:

- Plan: [PLAN-v9.6-operator-compass.md](PLAN-v9.6-operator-compass.md) — schema 1.6, A2, dual
  review tier; witness pairs recorded for all five acceptance commands (whole-command,
  sha256-matched). Layer-2 pass 1 (dual) returned BLOCKERS — including the demonstration that a
  zero-byte checker passes a bare `--selftest` invocation, which produced the
  selftest-**signal**-gating pattern (`[ "$(cmd --selftest)" = "SIG_OK" ]`) now used by all
  three new checkers. Pass 2 (dual, fresh judges) returned CLEAN at exactly the 2-cycle /
  4-pass liveness budget.
- All five tasks were implemented by dispatched workers and independently verified. The **T5
  verifier REJECTED** the original provenance contract — correct artifacts, weak token-grep
  acceptance command — and the contract was strengthened with the repo's discriminating
  registration check (`tools/check-candidates.py`) plus a `^## v9.6.0` heading anchor, the
  witness pair re-recorded, and the task re-verified. The gate caught and closed its own weak
  check inside one build cycle.
- The build's own ledger,
  [PLAN-v9.6-operator-compass.ledger.json](PLAN-v9.6-operator-compass.ledger.json), records
  every gate event above; a T1 verifier executed the D-25 reconciliation against it mid-build
  (MATCH). Worker/verifier evidence: `evaluation/evidence/v9.6-build/`; witness transcripts:
  `evaluation/evidence/v9.6-witness/`.

## Honest limits

- No new behavioral-evaluation round was run for v9.6.0; the D-6 treadmill eval (a scripted
  objective whose correct behavior is tripping the zero-dispatch wire) remains the missing
  behavioral proof and is the natural next evaluation.
- The ledger is maintained by the model under policy duty — no tooling appends to it
  automatically, and `validate-plan` does not yet require a plan to carry one. Verifier-noted
  hardening (token-grep ceilings on prose-task acceptance, sync-block INSIDE-placement
  enforcement, hollow-entry candidate sections) is recorded in the field report's
  next-increment notes.
- Deferred scope (next-increment ledger of the build plan): D-23, D-26, D-27, D-17
  (cross-substrate consult), increment-shape critique.
