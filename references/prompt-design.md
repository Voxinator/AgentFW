# Prompt Design for Agentic Work

The system's behavior is disproportionately determined by prompt design. For sub-tasks and delegated work:

- **Include the complete context** the agent needs — don't rely on inference
- **Define what "correct" looks like** explicitly
- **Specify the verification method** (how will we know this is right?)
- **Set boundaries** on scope (what's in and what's out)
- **Provide examples** of good output when possible

The prompt IS the harness specification for any given sub-task. Invest in it.

---

## Context Budget for Sub-Agents

When dispatching a worker or judge, explicitly scope the context. A sub-agent drowning in irrelevant context will underperform one that receives exactly what it needs.

When decomposing across independent items (files, modules, hypotheses), spawn one subagent per independent sub-problem in the same turn. Use plural language explicitly ("spawn N workers in parallel"). Do not say "decompose" alone — some models read that as advisory.

### Include

- The specific task description from PLAN.md
- Relevant source files the worker needs to read/modify
- The verification criteria for this task
- The permission scope (what they can and cannot do — see `core/permissions.md`)

### Exclude

- The full framework document
- Other tasks' details from PROGRESS.md
- The SESSION_LOG
- Unrelated playbooks or references
- Previous workers' reasoning or implementation approaches (especially for judges — they must evaluate artifacts cold, not inherit the implementer's assumptions)

### The Rule

A worker receiving 500 lines of relevant context will outperform one receiving 2,000 lines of mixed context. Less is more. The planner's job is **curation, not forwarding.**

You are not helping the worker by giving it everything. You are burying the signal in noise. Every line of context that isn't directly relevant to the task is a line that competes for attention with the lines that matter. The planner reads everything; the worker receives only what it needs.

This applies doubly to judges. A judge that receives the worker's implementation plan will check whether the implementation matches the plan. A judge that receives only the requirements and the current system state will check whether the system actually meets the requirements. Those are different evaluations, and the second one is the one that matters.

---

## Model & Effort Tier for Sub-Agents

Context budget scopes *what* a worker sees; tier scopes *how much capability* it spends. Both are part of the dispatch scope — set them deliberately. The default failure is over-provisioning: routing mechanical work to the session's own top tier at high effort because it's the frictionless choice. That is Complexity Accumulation in capability spend — slower and costlier with no gain on bounded work.

Match tier + effort to the task, not to your comfort:

- **Mechanical / bounded** — edit from a clear spec, search & extraction, formatting, bulk classification, run-and-report → lowest tier (Haiku), low–medium effort. Most workers land here.
- **Standard implementation & analysis** — a feature from an approved plan, ordinary debugging, structured research over known sources → mid tier (Sonnet), medium effort.
- **Hard reasoning** — ambiguous or multi-constraint design, large-hypothesis-space debugging, the plan-critique judge, adversarial verification where a false pass is costly → top tier (Opus), high–max effort.

Mechanics: the `Agent` tool takes a `model` override (omit to inherit the session model); Workflow `agent(prompt, opts)` takes `opts.model` and `opts.effort` per call (omit to inherit). Cheap fan-out stages take `{model:'haiku', effort:'low'}`; reserve the higher tiers for the verify/judge step.

Rules of thumb:
- The planner spends the reasoning; workers execute — most workers should run *below* the session tier, not at it.
- Scale the fleet cheap and the judge expensive: N cheap workers plus one top-tier judge beats one top-tier agent doing all N pieces itself.
- Escalate reactively — re-dispatch a single piece one tier up when its output shows the task genuinely needed more; don't pre-provision every worker for the hardest case.
- When genuinely unsure, pick one tier down and let verification catch the miss. A judge-caught error on a cheap worker costs less than running everything at max.
