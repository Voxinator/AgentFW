# Progress — [Task Name]

## AgentFW Version
r4

## Current Status
[One-line summary of where things stand]

## Tasks

| ID | Description | Status | Worker | Attempt | Side-Effects | Checkpoint | Verified By |
|----|-------------|--------|--------|---------|-------------|------------|-------------|
| T1 | [description] | planned | — | 1 | — | — | — |
| T2 | [description] | planned | — | 1 | — | — | — |

### Status Values
`planned` → `dispatched` → `in-progress` → `completed` → `verified` → `failed`

### Rules
- Do not dispatch a task that is already `dispatched` or `completed`
- If a task has `failed`, create a new row with incremented attempt number
- Record side-effects immediately after worker completion
- Record checkpoint (git hash or state snapshot) after verifying side-effects

## Decisions Made
- [Decision]: [Rationale] — [Date/Context]

## Things Learned
- [Insight that should inform future work]
