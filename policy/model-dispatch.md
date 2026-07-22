# Model Dispatch — Adaptive vs Uniform (D-14)

**WHY.** Economy is a first-class constraint: governance that is not economical does not get used,
and an unused framework governs nothing. An orchestrator that clones its own premium tier onto
every subagent pays flagship rates for mechanical work. Adaptive dispatch lets the orchestrator
right-size each worker to its task, while one cheap human-held lever guards the single escalation
that actually costs — spawning the flagship tier.

## Adaptive (the default)
The orchestrator selects a per-subagent model tier fit to the task: cheap tiers for mechanical
producers, stronger tiers where the work is genuinely hard. Right-sizing DOWN is free. Right-sizing
UP is free too — up to the flagship cap.

## The flagship cap (the gate)
Dispatching a subagent **at or above the adapter-declared `flagship` tier** is an **economic
escalation**: it requires a genuine human turn on the adapter-declared authenticated human channel —
the same channel `assurance-model.md` uses for destructive authorization and D-1's delivery
override, pointed at cost instead of destruction. Provenance is unchanged: simulated, proxy,
evaluator-injected, or standing text can neither request nor grant the escalation. Everything below
the flagship is free, including up-escalation — a cheaper orchestrator may cast a stronger
sub-flagship tier for a hard subtask without a lever. Self-cloning the flagship is the flagship
case, and is therefore gated.

Emit a grep-able marker on dispatch:
- below the cap: `[DISPATCH: adaptive — T3→<tier>, T5→<tier> (below cap)]`
- gated: `[DISPATCH: flagship-gated — T7 requests <flagship>; awaiting authorization]`

## Verifier tier floor
Adaptive right-sizing applies to **producers/implementers only**. The **judge of record — the
independent verifier and the plan-critic — is never cast below the adapter-declared `floor`
tier.** Economy must not erode the verification-tier binding (`assurance-model.md`): a cheap
worker's output at an A2 seam is still judged by a floor-or-above independent context. Right-size
the work; hold the judge.

## Uniform / Mirror (the opt-out)
A single toggle turns adaptive off: every subagent runs the orchestrator's own model. Uniform is
more expensive and makes no tier judgment; it exists for runs where the human wants one model
throughout. Adaptive and the sleep posture (`assurance-model.md`) are **independent dials** — either
may be set without the other; an adapter may offer an "away" preset that flips both.

## Model-agnostic core
The semantic policy names only "the flagship tier" and "the floor tier". The **adapter declares the
concrete ladder** — `model_selection.tiers` (ordered cheapest → flagship), `.flagship`, `.floor` in
its `capability.yaml` — because model ids churn and belong in the adapter, exactly as the rest of
the capability contract keeps vendor facts out of the policy.

## Honest degradation
When `model_selection` is unavailable or not configured ACTIVE on the runtime (consult the ACTIVE
capability state, not the brochure — `capability-contract.md`), adaptive dispatch **degrades to
Uniform**: every subagent runs whatever single model the runtime provides, **declared to the user,
never silent**.

## Under sleep mode
The flagship cap is a **floor item** for the unattended posture. Sleep mode auto-selects the
recommended option at non-floor forks, but it **cannot authorize a flagship dispatch** — it halts
and waits for a genuine human turn, exactly as it halts at a destructive gate (`assurance-model.md`,
the unattended/sleep posture). Autonomy up to the floor, never through it.
