# PLAN: Deep Dive — r6 Hermes Addendum × AgentFW × Live Hermes Install

**Created:** 2026-04-17
**Classification:** structured
**Mode:** guided (user co-present)
**Goal:** Produce a synthesized analysis of (a) the r6 Hermes addendum design, (b) AgentFW's architecture that it plugs into, and (c) the actual Hermes install on ubuntu-vm — then evaluate fit between the three, given the user's tiered stack (Gemma-4-31B primary / Qwen3-VL-8B auxiliary / Claude Code via ACP as external implementer).

## Why this matters

Hermes operates the AgentFW harness locally. The r6 addendum was designed to let a small local model (Gemma class) play Planner/Judge while delegating heavy implementation to an external CLI agent (Claude Code via ACP). We need to verify the addendum's assumptions match what Hermes actually does at runtime, because capability assumptions baked into a harness become silent bugs when the runtime diverges.

## Success criteria

1. Concrete mapping from **r6 addendum design decisions** → **AgentFW core mechanisms they tune** → **Hermes runtime behavior they depend on**.
2. Identification of **assumption gaps**: where the addendum assumes capabilities Hermes may not have, or ignores capabilities it does have (e.g., Qwen3-VL-8B as a summarizer/filter).
3. **Recommendations** that are specific (file:line scoped where possible), actionable, and ranked by impact.

## Decomposition (parallel workers)

### Worker A — r6 Hermes Addendum analysis (read-only)
- Scope: `PLAN-r6-hermes-addendum.md`, `variants/hermes/HERMES.md`, `variants/hermes/install-notes.md`, `PLAN-r6.md` (for r6 context), `ADDENDUM-sonnet-4-6.md` (sibling addendum for contrast), `evaluation/results-r6-baseline-multimodel-2026-04-17.md`.
- Produce: `ARTIFACT-workerA-addendum.md` — what the addendum changes vs base AgentFW, what failure modes it targets, what model-capability assumptions it makes, how it treats summarization/compression.

### Worker B — AgentFW architecture deep dive (read-only)
- Scope: `core/harness-core.md`, `core/permissions.md`, all of `references/`, all of `playbooks/`, all of `templates/`, `DESIGN.md`, `README.md`, `CHANGELOG.md`.
- Produce: `ARTIFACT-workerB-agentfw.md` — the harness's contract with the operating model: what capabilities it assumes, what state it externalizes, what invariants it enforces, where role-separation is mandatory vs relaxable.

### Worker C — Live Hermes install probe (SSH ubuntu-vm, read-only)
- Scope: SSH into ubuntu-vm. Find the Hermes install (likely under `~/hermes` or similar). Inspect:
  - Model config — confirm Gemma-4-31B primary, Qwen3-VL-8B-Instruct-MLX-4bit auxiliary.
  - Routing logic — locate the "Complexity vs. Resource" router in code.
  - `delegate_task` tool — how ACP subprocess is invoked, context handoff format, what comes back.
  - AgentFW integration — is HERMES.md loaded? How? Where does PROGRESS.md/PLAN.md live?
  - Summarization path — is Qwen3-VL used for context compression, or only for vision/OCR?
- Produce: `ARTIFACT-workerC-hermes-live.md` — observed behavior vs claimed behavior, with file paths and evidence.

### Judge — synthesis (fresh context, separate sub-agent)
- Input: all three artifacts + original r6 addendum + HERMES.md.
- Produce: `ARTIFACT-judge-hermes-r6-synthesis.md` — fit analysis, assumption gaps, ranked recommendations.

## Out of scope
- No modifications to AgentFW files, Hermes install, or remote system.
- No running of evals — this is an analysis pass, not a regression test.

## Task states
- [ ] Worker A dispatched
- [ ] Worker B dispatched
- [ ] Worker C dispatched
- [ ] All workers returned
- [ ] Judge dispatched with all artifacts
- [ ] Synthesis delivered to user
