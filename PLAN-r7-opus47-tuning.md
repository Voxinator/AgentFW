# PLAN — Opus 4.7 Tuning Feasibility Assessment

**Created:** 2026-04-17
**Status:** in_progress
**Objective:** Determine whether enough public information about Claude Opus 4.7 exists to meaningfully tune AgentFW, and if so, identify the concrete tuning levers.

## Decomposition

| # | Task | Owner | Role | Verify by |
|---|------|-------|------|-----------|
| 1 | Codebase surface map — list every AgentFW rule, gate, prompt, threshold that is model-sensitive | sub-agent (Explore) | Worker A | Judge reads artifact cold |
| 2 | Opus 4.7 external research — model card, behavior differences vs 4.6, benchmarks, community reports | sub-agent (general-purpose) | Worker B | Judge reads artifact cold |
| 3 | Sufficiency judgment — sufficient / partial / insufficient + named tuning levers | sub-agent (general-purpose, fresh) | Judge | Main session reviews |

## Verification criteria

A "sufficient" answer requires, for each proposed tuning change: (a) an observed Opus 4.7 behavior, (b) the AgentFW surface it touches, (c) the direction of change. Anything less is "partial" or "insufficient."

## Scope

- Allowed: read entire AgentFW repo, WebSearch, WebFetch
- Forbidden: modifying any AgentFW files, committing, dispatching additional workers
- Side-effect budget: writes only to ARTIFACT-worker-a.md and ARTIFACT-worker-b.md
