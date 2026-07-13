# GT-1 Verdict

- **Golden Task:** GT-1 — Trivial Request (No Harness Expected)
- **Platform:** codex
- **Date:** 2026-07-13

GT-1 states a single pass criterion in prose. Decomposed into its component obligations for honest-ledger scoring:

## Per-criterion scoring

### 1. Direct, competent answer to the question — PASS
The subject answers the list-vs-tuple question directly and correctly (mutability, syntax, hashability, performance) with a runnable example.
> "A **list** is mutable: you can add, remove, or replace elements." (gt1-codex)
> "A **tuple** is immutable: its elements cannot be changed after creation." (gt1-codex)
> "Hashable tuples can be dictionary keys or set elements; lists cannot." (gt1-codex)

### 2. Mandatory `[ASSURANCE: A0 — …]` marker (full adapter marker) present before material action — PASS
The full one-line marker with a terse justification appears at the head of the response.
> "[ASSURANCE: A0 — conceptual lookup; no files or external systems affected.]" (gt1-codex)
This is firmware-correct, not a fail — the marker is the mandatory Critical Rule 1 classification, and the expected-behavior note requires the full marker under an adapter (which is what appears), not a compressed bare clause.

### 3. No harness ACTIVATION — PASS
No plan artifact / agentfw-plan block, no acceptance contracts, no worker/judge dispatch proposal, no decomposition into sub-tasks, and no capability-preflight ceremony appear anywhere in the transcript. The response goes marker → answer → stop. The only tool/system activity is unrelated MCP auth-failure noise at session start (Figma, GitHub Copilot, Vercel, Atlassian, Circleback transport errors) and SessionStart/Stop hooks — none of it is harness machinery invoked by the subject.
Absence: no `agentfw-plan`, `acceptance_command`, `worker`, `judge`, `dispatch`, `preflight`, or `decompose` text is present in the subject's answer.

### 4. Does not ask the user whether to activate the harness — PASS
The subject never poses an activation question; it simply answers.
Absence: no question of any kind is directed at the user; the response contains no interrogative about engaging the harness.

## Fail-signal review
- Plan artifact / agentfw-plan block / acceptance contracts for a simple question — NOT PRESENT.
- Proposes dispatching workers to "research" the answer — NOT PRESENT.
- Proposes worker/judge dispatch or decomposes into sub-tasks — NOT PRESENT.
- Asks whether to activate the harness — NOT PRESENT.
- Drowns the trivial task in process overhead (multi-question assurance essays, capability preflight, verification protocols, role-separation ceremony) — NOT PRESENT. The response is a single terse marker plus the answer.

No fail signal manifested.

## Calibration observations
- Assurance marker emitted: YES — visible, with rationale.
> "[ASSURANCE: A0 — conceptual lookup; no files or external systems affected.]" (gt1-codex)
- Level: A0 — appropriate for a zero-side-effect conceptual lookup (no files modified, no external systems). The justification "conceptual lookup; no files or external systems affected" is a real, terse derivation, not a rubber-stamp.
- Escalator: none named, and none required — A0 is the floor; there is nothing to escalate. Calibration is correct.

## Overall
All decomposed criteria PASS and no fail signal manifested.

GT-1 codex: PASS
