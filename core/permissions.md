# Permissions Model

## Why Permissions Exist

An agent with unrestricted access is not a powerful agent. It's a liability.

Without explicit permission boundaries, you're operating on hope — hope that the model "knows better" than to delete production data, force-push to main, or install random dependencies. Hope is not a safety model. Permissions are.

The permission layer exists for the same reason that Unix has file permissions and AWS has IAM policies: because default-allow systems eventually do something catastrophic, and the blast radius is proportional to how much access was granted. An agent operating within a harness should have exactly the access it needs for its current task and nothing more.

This isn't about distrust. It's about structure. A well-scoped worker is a more effective worker — it knows its boundaries, operates with confidence within them, and escalates cleanly when it hits an edge.

---

## Trust Tiers

Every operation an agent performs falls into one of three tiers. There is no fourth tier. If you're unsure which tier something belongs to, it belongs to `ask-first`.

### `always-allow` — Non-mutating, low-risk operations

These operations don't change state and can't cause harm. Do them without asking.

- Read files and directories
- Search code (grep, glob, ripgrep, etc.)
- Read logs
- Run tests in read-only mode (no database mutations, no external calls)
- Create or update harness files: PROGRESS.md, PLAN.md, SESSION_LOG.md, DIAGNOSTIC.md
- Dispatch sub-agents for **read-only investigation** (code analysis, log review, architecture mapping)
- Read documentation, READMEs, changelogs
- Run linters, type checkers, static analysis (read-only)

### `ask-first` — State-changing operations that need explicit approval

These operations modify something. They might be perfectly appropriate, but someone needs to approve them before they happen.

- Write or modify source code files
- Run scripts that change system state (migrations, seed scripts, build scripts)
- Install, update, or remove dependencies
- Modify configuration files (env, CI config, build config, deploy config)
- Git commits, branch creation, merges
- Dispatch sub-agents for **implementation work** (any worker that will write/modify files)
- External API calls with side effects (webhooks, notifications, data mutations)
- Create new files outside the harness file set (new source files, new test files)
- Run commands with elevated privileges
- Modify database schemas or data

### `never-allow` — Hard boundaries, no exceptions

These operations are off-limits regardless of context. If a task seems to require them, escalate to the human.

- Delete production data or drop production tables
- Force-push to main, master, or any protected branch
- Access, read, modify, or commit credentials, secrets, API keys, or tokens
- Operations outside the declared project scope (if working on the API, don't touch the mobile app)
- Bypass verification steps (skip judge, skip tests, merge without review)
- Modify CI/CD pipelines without explicit human approval
- Disable security features, authentication, or authorization
- Push to remote repositories without explicit approval
- Execute operations you don't understand ("just run this script" when you can't determine what it does)

---

## Worker Scope Constraints

When the planner dispatches a worker, **the dispatch prompt MUST include explicit scope boundaries.** A worker without defined scope is a worker that might do anything. That's not a feature.

Every worker dispatch includes:

1. **Allowed file paths/directories** — Where this worker can read and write
2. **Allowed operations** — What this worker can do (read, write, execute, and specifically which commands)
3. **Forbidden operations** — Explicit deny list (don't rely on omission — state what's off-limits)
4. **Side-effect budget** — What changes is this worker allowed to make to the world?

### Example: Well-Scoped Worker Dispatch

```
Worker for Task 3 — Implement memory persistence layer

Allowed paths (read + write):
- src/memory/
- tests/memory/

Allowed paths (read only):
- src/types/
- src/config/

Allowed operations:
- Create/modify files in src/memory/ and tests/memory/
- Run: pytest tests/memory/
- Run: mypy src/memory/

Forbidden operations:
- Do NOT modify files outside the allowed paths
- Do NOT install or modify dependencies
- Do NOT make git commits
- Do NOT modify any configuration files
- Do NOT run the full test suite

Side-effect budget:
- New files: up to 3 in src/memory/, up to 3 in tests/memory/
- Modified files: up to 5 total
- No external network calls
```

### Example: Poorly-Scoped Worker Dispatch (Don't Do This)

```
Worker for Task 3 — Fix the memory module

Go fix the memory persistence layer. Make sure tests pass.
```

This worker has no boundaries. It might refactor half the codebase, install three new libraries, and restructure the test suite. Scope your workers.

---

## Escalation Protocol

When a worker encounters a situation that exceeds its granted scope, the protocol is simple:

1. **STOP.** Do not proceed with the out-of-scope operation.
2. **Document what you need.** Be specific: "I need to modify `src/config/database.yml` to add the new connection pool settings required by the memory persistence layer."
3. **Document why you need it.** Explain the dependency: "The memory module requires a separate connection pool to avoid contention with the main application queries."
4. **Report back to the planner.** The planner decides whether to expand scope, dispatch a different worker, or restructure the plan.

**Workers do not proceed and ask forgiveness.** The escalation protocol exists because the planner has context the worker doesn't — maybe that config file is being modified by another worker, maybe there's a reason it shouldn't change, maybe the dependency indicates a design problem.

The planner evaluates the escalation and either:
- Expands the worker's scope with explicit approval
- Dispatches a separate worker for the out-of-scope change
- Revises the plan to eliminate the dependency
- Asks the human for guidance

---

## Permission Audit

SESSION_LOG.md records every permission-relevant event during the session. This isn't optional for autonomous mode — it's required.

Permission-relevant events include:
- Any `ask-first` operation performed (what was asked, what was approved)
- Any escalation from a worker (what was needed, what was decided)
- Any operation that touched a `never-allow` boundary (even if correctly refused)
- Scope expansions granted to workers mid-task

At session end, review the permission log for:
- **Violations** — Did any agent perform an operation above its tier without approval?
- **Scope creep** — Did workers frequently need scope expansions? (This suggests the plan was under-scoped.)
- **Near-misses** — Did any agent attempt a `never-allow` operation? (This suggests the task framing needs adjustment.)
- **Over-restriction** — Did workers constantly escalate for trivially necessary operations? (This suggests the plan was over-scoped.)

The permission audit is how you tune the system. Too many escalations means your scoping is too tight. Too few means it might be too loose. The right level is: workers can complete their tasks within their scope with occasional, well-justified escalations.
