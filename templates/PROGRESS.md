# Progress — [Task Name]

## AgentFW Version
r6

## Current Status
[One-line summary of where things stand]

## Tasks

| ID | Description | Status | Worker | Attempt | Side-Effects | Checkpoint | Verification Method | Verification Artifact | Verified By |
|----|-------------|--------|--------|---------|-------------|------------|--------------------|-----------------------|-------------|
| T1 | [description] | planned | — | 1 | — | — | build | pending | — |
| T2 | [description] | planned | — | 1 | — | — | test:pytest | pending | — |

### Status Values
`planned` → `dispatched` → `in-progress` → `completed` → `verified` → `failed`

**Note:** `completed` does NOT mean verified. Downstream tasks cannot dispatch against `completed` dependencies — only `verified` ones.

### Rules
- Do not dispatch a task that is already `dispatched` or `completed`
- If a task has `failed`, create a new row with incremented attempt number
- Record side-effects immediately after worker completion
- Record checkpoint (git hash or state snapshot) after verifying side-effects
- **Verified By** must include an agent ID or "human" — never "planner". Any entry where Verified By is the planner's own session is a **role-collapse violation**. Flag and re-verify with a separate judge.

## Decisions Made
- [Decision]: [Rationale] — [Date/Context]

## Things Learned
- [Insight that should inform future work]

## Context Health Checks
| Check # | After Task | Result | Evidence |
|---------|-----------|--------|----------|
| 1 | T3 | OK | W1-W3 dispatched, J1-J2 verified, no gaps |
