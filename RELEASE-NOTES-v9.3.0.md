# AgentFW v9.3.0 — the economy dials

**Released 2026-07-21.** v9.3.0 adds two independent, human-held levers that put the maintainer's
economy calibration into the runtime: *governance that is not economical does not get used, and an
unused framework governs nothing.* The safety floor is untouched — each lever adds autonomy **up to**
the floor and a cheap human turn **through** it. Design of record:
[CANDIDATES.md](CANDIDATES.md) § D-14 and § D-15; build provenance:
[PLAN-v9.3-sleep-adaptive.md](PLAN-v9.3-sleep-adaptive.md).

## D-14 — adaptive dispatch

An orchestrator that clones its own premium tier onto every subagent pays flagship rates for
mechanical work. **Adaptive dispatch** (the default) lets the orchestrator right-size each
subagent's model to its task.

- **Flagship cap.** Any tier below the adapter-declared **flagship** is free, including
  up-escalation. Casting a subagent **at or above** the flagship tier is an **economic escalation**
  requiring a genuine turn on the adapter-declared authenticated human channel — the same channel
  D-1's delivery override uses, pointed at cost instead of destruction. Simulated, proxy,
  evaluator-injected, or standing text can neither request nor grant it.
- **Verifier tier floor.** Right-sizing applies to producers only; the judge of record (independent
  verifier, plan-critic) is **never** cast below the adapter-declared **floor** tier. Economy
  cheapens producers, never verification.
- **Uniform/Mirror** is the opt-out (every subagent runs the orchestrator's model). Adaptive and the
  sleep posture are independent dials.
- **Model-agnostic core.** The policy names only "the flagship tier" and "the floor tier"; the
  adapter declares the concrete ladder. New **11th capability key `model_selection`** carries
  validator-enforced `tiers`/`flagship`/`floor` sub-fields. When `model_selection` is unavailable or
  unconfigured, adaptive **degrades honestly to Uniform** — declared, never silent.

Full mechanism: [`policy/model-dispatch.md`](policy/model-dispatch.md).

## D-15 — sleep mode (unattended posture)

A third interaction posture beside interactive-with-authenticated-channel and headless. **Sleep
mode** is entered by a genuine authenticated-channel human turn that declares a scope; entry is
itself the (non-standing) authorization.

- While asleep, the agent takes the **recommended** option at **non-floor** forks and proceeds,
  recording each choice.
- At any **floor** blocker it behaves exactly like a **headless** run — halt or degrade, record what
  it would do, and wait for a genuine human turn — because an auto-accept would be standing text,
  which is **never waivable** authorization.
- The floor is non-delegable: the six safety-floor classes **plus** the D-14 flagship escalation.
  The plan-critique cap and the D-1 delivery override stay **human-only levers** sleep never
  auto-pulls.
- The floor-halt invariant is **machine-checked**: a canonical decision-table fixture
  (`evaluation/fixtures/sleep-posture.json`) plus `tools/check-posture-invariants.py` reject any
  table that maps a floor fork to auto-authorize. "Sleep halts at the floor" is falsifiable, not
  prose.
- Truly-unattended resumption depends on `scheduled_resume`, which is `partial/unverified` on both
  runtimes; the supported variant is present-but-away.

Full posture: [`policy/assurance-model.md`](policy/assurance-model.md).

## Deterministic release gate

`tools/tests/release-v9.3.sh` (green) asserts the v9.3.0 identity and runs: the 11-key capability
schema on **both** parser paths with tier-ladder sub-field enforcement; the byte-identical adapter
SKILL sync (`check-skill-sync.py`); the sleep-posture floor-halt invariant (`check-posture-invariants.py`
over the fixture); ledger completeness (`check-candidates.py`); and the existing validator, installer,
and link suites. The SKILL-desync, stale-metadata, and laundered-posture-fixture scratch mutations
each make the gate red.

## Behavioral evidence boundary

**No behavioral-evaluation round was run for v9.3.0.** The bounded v9.0.0 behavioral evidence
remains the behavioral record. v9.3's behavioral tier — the treadmill scenario in
[`evaluation/eval-v9.3-sleep-adaptive.md`](evaluation/eval-v9.3-sleep-adaptive.md) — is specified,
not yet run; the machine-checked decision-table invariant is the deterministic proof that ships now.
Behavioral compliance is model- and version-dependent, not guaranteed.
