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

## Model-family knobs (non-binding)

Principles below are model-agnostic; sidenotes in parentheses are Anthropic-specific invocations. Adapt per model family. None of this is load-bearing for correctness — the Critical Rules and role separation are.

1. **Reasoning effort by role.** Workers doing implementation or investigation warrant higher reasoning effort than judges doing focused verification. Mechanical lookups and file-moves warrant the lowest effort. *(Anthropic Opus 4.7: `effort=xhigh` for workers, `high` for judges, `low`/`medium` for mechanical tasks.)*

2. **Judges benefit from explicit deliberation biasing.** Judge prompts are short and shielded by design, which can cause silent under-thinking on models with adaptive reasoning. Include a longer explicit rubric (evaluation criteria spelled out inline) to bias the judge toward deliberate evaluation. *(Anthropic Opus 4.7: enable `thinking: {type: 'adaptive'}` in judge dispatch; prefer a summarized display so progress is visible.)*

3. **Worker scope may include a token budget.** Worker scope already carries allowed paths, allowed operations, and forbidden operations. For bounded tasks, a token budget — an advisory cap on reasoning + tool tokens across the full worker loop — is a natural fourth component. Do NOT set for judges or open-ended investigation. *(Anthropic Opus 4.7: use the `task-budgets-2026-03-13` beta header where supported; minimum 20k.)*
