# Feature: [Feature Name]

## What I Need
[2-3 sentences describing the feature and why it matters]

## Codebase Context
- Entry points: [list main files/modules relevant to this feature]
- Key integration points: [Discord bot, Flask dashboard, memory system, heartbeat engine, etc.]
- Architecture notes: [anything Claude can't learn by reading the code — quirks, conventions,
  unstated constraints, things that look wrong but are intentional]

## Definition of Done
- [ ] [Functional requirement 1]
- [ ] [Functional requirement 2]
- [ ] [Non-functional requirement: performance, compatibility, etc.]
- [ ] Existing tests still pass
- [ ] New functionality has test coverage
- [ ] PROGRESS.md updated with final state

## Domain Knowledge You Won't Find in the Code
- [Architectural quirk or tribal knowledge item]
- [Integration behavior that isn't documented]
- [Constraint from external system]

## Operating Instructions
You are the **planner and judge dispatcher** for this feature. You do NOT implement code directly. Run autonomously using sub-agents:

1. **Plan first.** Read the codebase yourself (read-only investigation is fine for the main session).
   Produce a PLAN.md with decomposed sub-tasks, each with its own verification criteria.
   Do not dispatch any implementation work until the plan exists.

2. **Dispatch sub-agents for implementation.** For each sub-task, spin up a worker agent with:
   - The specific task description from PLAN.md
   - The relevant codebase context it needs
   - The verification criteria for that sub-task
   - Clear scope boundaries (what to touch, what not to touch)
   - Permission scope: allowed paths (read/write), allowed operations, forbidden operations
   The worker implements and returns its artifacts. You do NOT write implementation code
   in the main session.

3. **Dispatch a separate sub-agent for verification.** After a worker completes a sub-task,
   spin up a *different* agent to verify the work. The verifier receives:
   - The original sub-task requirements
   - The current state of the code (post-change)
   - The verification criteria
   It does NOT receive the worker's reasoning or implementation plan.
   It evaluates the artifacts cold — running tests, checking for regressions,
   reviewing the changes against the requirements.

4. **If verification fails**, take the judge's findings and dispatch a *new* worker.
   Do not reuse the original worker's context. Fresh start, informed by what the judge found.

5. **Maintain state throughout.** Use `templates/PROGRESS.md` format for your state file.
   Update it after every sub-task: what's done, what's next, decisions made, things learned.
   Record side-effects and checkpoints for each completed task.
   If this session dies and a new one starts, PROGRESS.md is how continuity survives.

6. **Only come to me when:**
   - You need domain knowledge not in the code or docs
   - You've hit an architectural decision that could go multiple ways and needs my input
   - The feature is complete and ready for my final sniff-check

7. **When you're done**, present: what was built, what was changed, how to verify it,
   and anything I should pay attention to during sniff-check.
