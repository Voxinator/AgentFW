# State Management

## Progress File Protocol

For any multi-step task, maintain a **PROGRESS.md** file (or equivalent) that tracks task state, decisions, and accumulated knowledge. This file is the harness. It's what allows the next session (or the next agent iteration) to pick up where things left off without losing accumulated progress.

See `templates/PROGRESS.md` for the enhanced template with full task state tracking.

### Task State Machine

Each task in PROGRESS.md must have a status field with one of these values:

```
planned → dispatched → in-progress → completed → verified → failed
```

- **planned** — Task exists in the plan but no worker has been assigned.
- **dispatched** — A worker has been assigned. Do not re-dispatch.
- **in-progress** — Worker is actively executing. The Worker ID field identifies which sub-agent owns it.
- **completed** — Worker has finished. Artifacts exist. Awaiting verification by a separate judge.
- **verified** — A judge (separate context) has confirmed the work meets criteria.
- **failed** — Verification failed or the worker could not complete the task. Create a new attempt entry.

### Required Fields Per Task

Every task entry in PROGRESS.md includes:

| Field | Purpose |
|-------|---------|
| **Status** | Current state (see state machine above) |
| **Worker ID** | Which sub-agent owns this task — prevents duplicate dispatch |
| **Side-effects list** | Files changed, commands run, external calls made |
| **Checkpoint** | Git hash or state snapshot after completion — the rollback point |
| **Attempt number** | For retries: links back to previous attempts |
| **Verified By** | Which judge context verified this, and how |

### Dedupe Rules

Before dispatching a worker for a task, check PROGRESS.md:

- If the task is already `dispatched` or `in-progress` — **do not re-dispatch.** You already have a worker on it.
- If the task is `completed` — **do not re-dispatch.** It's waiting for verification, not re-implementation.
- If the task is `verified` — it's done. Move on.
- If the task is `failed` — **create a new attempt entry** linked to the previous one. Increment the attempt number. The new worker gets the judge's findings from the failed attempt, but NOT the previous worker's implementation reasoning. Fresh context, informed by what went wrong.

This is not bureaucracy. This is how you prevent the most common failure mode in autonomous sessions: the planner losing track of what's already been dispatched and spinning up duplicate workers that step on each other's changes.

### Side-Effect Checkpoints

After each worker completes, record what changed. This is your rollback point if the next step fails.

- **For code work:** Git commit hash. If the next task breaks something, you know exactly where to revert to.
- **For external systems:** What was created, modified, or called. API resources created, database records changed, services restarted.
- **For document/analysis work:** File paths and timestamps of artifacts produced.

The checkpoint is what makes "restart that sub-problem cleanly" possible rather than aspirational. Without it, a failed step three means you're manually figuring out what steps one and two actually did.

### SESSION_LOG.md Relationship

PROGRESS.md and SESSION_LOG.md serve different purposes and complement each other:

- **PROGRESS.md tracks task state** — the *what*. Which tasks exist, what status they're in, who owns them, what side-effects they produced.
- **SESSION_LOG.md tracks events** — the *when* and *how*. Permission-relevant events, escalations, errors, decisions with timestamps.

Cross-reference by task ID. When you see a task failed in PROGRESS.md, the SESSION_LOG tells you what happened and when. When you see an error event in SESSION_LOG, the task ID tells you which piece of work it affected.

### Multi-Session Continuity

A cold-start agent picking up work from a previous session needs PROGRESS.md to fully orient. The file must contain enough for that agent to answer:

1. **Where are we?** — Current status line at the top.
2. **What's done?** — All tasks with `verified` status, their checkpoints, and their side-effects.
3. **What's in flight?** — Any tasks that were `dispatched` or `in-progress` when the previous session ended. These need attention — the worker context is gone.
4. **What failed and why?** — Failed tasks with attempt history and judge findings.
5. **What do we know?** — Decisions Made and Things Learned sections.
6. **Where's the last known-good state?** — The most recent checkpoint from a verified task.

If a new agent can't answer all six questions from PROGRESS.md alone, the file is incomplete.

---

## Memory and Context Documents

For ongoing projects, maintain context documents that capture:
- **Architecture decisions** and their rationale
- **Domain knowledge** accumulated during the work
- **Constraints discovered** that weren't in the original brief
- **Patterns that worked** and patterns that didn't

These documents are the "persistent memory" of the harness. They survive context window resets.
