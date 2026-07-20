# AgentFW v9.2.0 — Release Notes

**Released 2026-07-20.** The *delivery invariant* release. v9.2.0 adds one feature — **the human
delivery override (assumption-gated dispatch)** — and it is the most consequential change to how
AgentFW feels to use since the assurance model itself.

## Why this release exists

On 2026-07-18/19, an AgentFW-governed session was asked to build a private, local, reversible game
prototype. The plan gate did its job twice over: it caught a real destructive-data mistake — and
then it prevented all implementation. Four successively narrowed plans each died at the review cap
under new, increasingly specific objections; explicit human requests to implement started new
planning cycles instead of work; roughly $100 of review spend produced zero dispatched workers.
The full incident is published as
[the field report](evaluation/field-report-2026-07-20-noita-planning-livelock.md), and a second,
independent incident the same weekend (a 282-line A4 plan and 786-line verification harness for
what was actually a reversible file copy) confirmed the diagnosis:

**AgentFW's safety invariant was stronger than its delivery invariant.** Every open blocker was
priced the same — dispatch-blocking — and the paying human had no priced-in way to say the
edge-case search had stopped being worth it.

The maintainer's calibration, now recorded as the governing v9.2 design constraint in
[R92-CANDIDATES.md](R92-CANDIDATES.md): AgentFW's domain is ordinary software work, not medical
devices or launch vehicles. *"It needs to help improve the quality of agent output but shouldn't
create a maze the user has to constantly fight. If it's not economical, it won't get used. The
magic is in the middle. A relax lever shouldn't be extremely hard to grab — but it should require
the human."* Economy is a first-class constraint with a safety rationale: **governance that is
not economical does not get used, and an unused framework governs nothing.**

## The feature

### The lever

After Layer-2 findings exist, a genuine human turn expressing delivery intent — *"implement now"*,
*"stop reviewing"*, *"proceed"* — obligates the model to STOP planning. It MUST NOT start another
plan/critique cycle. Its only lawful responses are:

1. **The override offer** — one turn containing: the partition of every open blocker into
   safety-floor (never waivable) vs assumption class (waivable); the assumption ledger, each
   waived blocker converted to a recorded assumption **plus a required follow-up test**; review
   expenditure to date; and the exact dispatch scope.
2. **A safety-floor refusal** naming the specific floor blockers, when floor items are open.

A subsequent genuine human turn confirming the offer dispatches immediately. Total cost of ending
a review spiral: **two turns.** Plain language on both sides — no token, no nonce, no ritual for
non-destructive work. (The incident that motivated this feature involved a nonce-gated
authorization ceremony for a reversible file copy; that pattern is now named in the design record
as the anti-pattern.)

### The floor

Six items are never waivable, by anyone, and the policy states: *"Nothing may be added to or
removed from this list by any relaxation."*

1. destructive or externally-consequential action without authority/rollback
2. security boundary defect
3. irreversible architectural commitment
4. C5 goal/proof contradiction
5. unavailable required substrate
6. demonstrated-vacuous acceptance command

The override is a *quality* valve, never a *safety* valve. The guarantee/encourage boundary — the
framework's load-bearing distinction — is untouched. Quality gates above the floor are priced in
the user's currency; the user holds the lever.

### The guardrails that survive the lever

- **Provenance:** the override rides the same authenticated-human-channel machinery
  `policy/assurance-model.md` built for destructive authorization, pointed the other way.
  Simulated, proxy, evaluator-injected, or standing text can neither open the override nor
  confirm it.
- **Self-clearance is still prohibited:** only a genuine human turn waives; the model never
  clears its own blockers.
- **Waived stays waived, per objective:** a later cycle for the same objective may raise
  genuinely new findings, and floor findings always block — but it may not re-raise a waived
  assumption absent new evidence. One forced revision can no longer resurrect the treadmill.
- **Audit:** dispatch under override emits a grep-able marker —
  `[OVERRIDE: assumption-gated dispatch — N waived → assumptions+tests; M safety retained;
  authorized turn <n>]` — preserved in the plan record. This is not a silent gate-skip; it is the
  named relaxation, standardized.

### Schema 1.4 — the ledger is machine-checked

New additive plan schema (now the schema of record; 1.1–1.3 remain valid): an optional plan-level
`overrides` array, entries exactly `{blocker, assumption, followup_test, authorized_turn}`, all
non-empty strings, enforced by `tools/validate-plan` under the new stable defect keyword
`override`. A waiver without a follow-up test is a deterministic Layer-1 defect, not a judgment
call. Fail-safe versioning holds: a 1.1/1.2/1.3 block carrying `overrides` is rejected naming
schema 1.4. The model authors the ledger — the human never writes paperwork.

### Surfaced in the adapters, not buried in the policy

The field report's distribution finding: the stale install lacked the recovery menu, and even a
current install summarized cap behavior as "escalate" — the feature existed only in a policy file
the session never loaded. Both adapter SKILL.md files now carry the four-option escalation menu
(extend one pass / mutation-gated dispatch / assumption-gated dispatch via human delivery
override / halt), the trigger duty, and the safety floor **inline**, with the override span
byte-identical across the two adapters.

## Build provenance — the feature governed its own build

The D-1 build ran under the full A2 harness and produced a live rehearsal of the exact mechanism
it was building. The plan gate's second critique pass constructed a null implementation and
demonstrated the planner's own T1 acceptance command was vacuous — a safety-floor-class defect
(item 6). The gate hit its 2-pass cap with that blocker open and escalated to the maintainer, who
selected a recorded, probe-verified relaxation; the fix was made, the critic's own
null-implementation probe was re-executed red, and workers dispatched. Two Layer-2 passes (both
caught demonstrated defects), three implementer workers, and an input-curated independent
verifier: **VERIFIED-WITH-FINDINGS** — all 3 acceptance commands re-executed green, all 8
contracted mutation probes red on fresh scratch copies, 10 off-contract hostile probes clean
(whitespace-only ledger fields rejected, duplicate keys rejected, 1.2-carrying-overrides
rejected, no nonce on the non-destructive path, adapter spans byte-identical). The verifier's one
finding — both skills dropped "/rollback" from floor item 1 — was fixed and re-verified. Full
record: `PLAN-v9.2-d1-override.md`.

Note the corollary demonstrated by that escalation: the floor means the override could NOT have
waived that blocker. The lever ends spirals over implementation details; it does not let anyone —
including the maintainer — ship a vacuous check.

## What v9.2.0 does not include

D-2 through D-6 are designed ([R92-CANDIDATES.md](R92-CANDIDATES.md)) and tracked (issues
#8–#12) but **not built**: the global liveness budget across cycles, full drift visibility
(`ACTIVE_POLICY_STALE`), governance-cost instrumentation, and the reversible-prototype-treadmill
regression eval. D-3's inline-surfacing was delivered for the override path specifically.

**No behavioral-evaluation round was run for v9.2.0.** The override's behavioral effectiveness —
does a governed session actually honor the trigger duty under pressure? — is precisely what D-6
is designed to measure. Until it runs, v9.2.0's guarantees are the deterministic ones: the
schema, the validator, the policy text, and the adapter text. The bounded n=1 evidence published
with v9.0.0 remains the behavioral record.

## Verification

`tools/tests/release-v9.2.sh` (the deterministic gate, re-pinned from v9.1.1): release identity
and provenance, the schema validator fixture harness including the five new 1.4 fixtures,
installer roundtrip **28/28**, relative-link resolution, capability validation through **both**
parser paths (PyYAML and the stdlib fallback), plus new D-1 assertions — the policy's floor and
trigger text, the schema-1.4 fixtures, and the adapter sync — each shown to turn the gate red
when reverted.

## Upgrading

| Platform | Path |
|---|---|
| Claude Code | `tools/agentfw-install upgrade` (backs up CLAUDE.md; refreshes skill/policy/validator/agents) |
| Codex | `adapters/codex/UPGRADE.md` (the v9.1.1-corrected four-item procedure; ends with the mechanical `INVENTORY_OK` check) |

Plans you have already authored against schema 1.1–1.3 validate unchanged.
