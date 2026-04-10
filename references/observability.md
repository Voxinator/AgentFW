# Observability Protocol

## Purpose

You cannot improve what you cannot observe. You cannot debug across sessions without structured records.

The chat transcript is not an audit trail. It's a river of text with decisions buried in paragraphs, errors lost between tool calls, and no way to scan for patterns. When something goes wrong in session 4 of a 6-session project, you need to be able to trace back through what happened — what was dispatched, what was verified, what failed, and what was learned.

Structured event logging gives you that. It's the difference between "something went wrong somewhere" and "Worker W3 failed Task T2 at 14:32 due to a structural error, which was correctly identified and restarted with fresh context at 14:35."

---

## Event Types

Every event has a **timestamp**, **event type**, and **details**. Some events carry additional required fields. Here's the full catalog.

### SESSION_START
Logged once at the beginning of every session.

Required fields:
- Timestamp
- AgentFW version (e.g., r6)
- Task summary (one line — what are we here to do?)
- Operating mode: Autonomous or Guided
- Client: Claude Code, Claude Projects, or other

### PLAN_CREATED
Logged when the planner produces a PLAN.md.

Required fields:
- Timestamp
- Task count (how many sub-tasks in the plan)
- Complexity assessment (one-shot / structured / long-horizon)

### WORKER_DISPATCHED
Logged every time a sub-agent is spun up for implementation work.

Required fields:
- Timestamp
- Worker ID (W1, W2, etc. — sequential per session)
- Task ID (which task from the plan)
- Scope boundaries (allowed paths, allowed operations — abbreviated is fine)
- Permissions granted (what tier of operations this worker can perform)

### WORKER_COMPLETED
Logged when a worker finishes (successfully or not).

Required fields:
- Timestamp
- Worker ID
- Task ID
- Outcome: success / failure / escalation
- Artifacts produced (files created, files modified — list them)
- Side-effects performed (commands run, dependencies installed, etc.)

### JUDGE_DISPATCHED
Logged every time a verification sub-agent is spun up.

Required fields:
- Timestamp
- Judge ID (J1, J2, etc. — sequential per session)
- Task ID being verified
- What the judge received (requirements, current system state, verification criteria)
- What the judge did NOT receive (the worker's reasoning, implementation plan, etc.)

This last field matters. If you can't articulate what the judge was shielded from, you might not be doing real role separation.

### JUDGE_VERDICT
Logged when a judge delivers its evaluation.

Required fields:
- Timestamp
- Task ID
- Verdict: accept / reject / accept-with-notes
- Findings summary (what the judge observed, in 1-3 sentences)

### ERROR
Logged when something goes wrong during execution.

Required fields:
- Timestamp
- Task ID (or "session-level" if not task-specific)
- Error type: local (fix and continue) or structural (approach is wrong)
- Blast radius: what downstream work is affected?
- Action taken: fixed in place / restarting task / escalating to human

### RESTART
Logged when a task is restarted with fresh context after failure.

Required fields:
- Timestamp
- Task ID being restarted
- Reason for restart
- Learnings carried forward (what the new worker will know that the old one didn't)

### PERMISSION_CHECK
Logged for every `ask-first` or `never-allow` operation encountered.

Required fields:
- Timestamp
- Operation attempted (what the agent wanted to do)
- Permission tier: always-allow / ask-first / never-allow
- Outcome: approved / denied / escalated

You don't need to log `always-allow` operations — that would be noise. Log the boundaries, not the routine.

### CONTEXT_HEALTH_CHECK
Logged when the planner performs a context health gate.

Required fields:
- Timestamp
- Task count at time of check
- Result: OK / DEGRADED
- If DEGRADED: which Critical Rule was violated, corrective action taken

### SESSION_END
Logged once at session close.

Required fields:
- Timestamp
- Tasks completed (count and IDs)
- Tasks remaining (count and IDs)
- Total sub-agents dispatched (workers + judges)
- Notable events (brief summary of anything unusual)

---

## SESSION_LOG.md Format

The log lives in SESSION_LOG.md at the project root (or harness directory). It's a markdown table — human-readable, scannable, and diffable.

```markdown
| Timestamp | Event | Task ID | Details |
|-----------|-------|---------|---------|
| 09:15 | SESSION_START | — | r6, autonomous, "Add caching layer to API" |
| 09:17 | PLAN_CREATED | — | 4 tasks, structured complexity |
| 09:18 | WORKER_DISPATCHED | T1 | W1, scope: src/cache/, tests/cache/, read+write |
| 09:25 | WORKER_COMPLETED | T1 | W1, success, created 2 files, modified 1 |
| 09:26 | JUDGE_DISPATCHED | T1 | J1, received: requirements + current code, shielded from: W1 reasoning |
| 09:29 | JUDGE_VERDICT | T1 | Accept — cache invalidation logic correct, tests cover edge cases |
```

Timestamps can be approximate. The point is sequence and traceability, not nanosecond precision.

Don't use JSON. Don't use YAML. The log needs to be readable by a human scanning it at the end of a session. Markdown tables hit the sweet spot between structure and readability.

---

## When to Log

**Autonomous mode:** Always. Every event, every time. This is non-negotiable. When an agent is operating without human oversight, the log is the only record of what happened and why.

**Guided mode (multi-step work):** Strongly recommended. The human is present, but they're not tracking every sub-agent dispatch and permission check in their head. The log gives them a clean summary at the end.

**Guided mode (simple tasks):** Optional. If it's a one-shot task that doesn't warrant harness activation, a log would be overhead.

**Multi-session tasks:** Required, regardless of mode. When work spans sessions, the log is how the next session orients. Without it, the next agent starts blind.

---

## Review Protocol

At the end of every session (before writing SESSION_END), scan the log for:

1. **Permission violations** — Did any agent perform an operation above its tier without approval? This is a red flag. Document it and flag it in the session summary.

2. **Self-review incidents** — Did the same context implement and verify work? Look for cases where a WORKER_COMPLETED and JUDGE_VERDICT reference the same agent context. This violates role separation.

3. **Workers exceeding scope** — Did any worker modify files or run commands outside its declared scope? Cross-reference WORKER_DISPATCHED scope with WORKER_COMPLETED side-effects.

4. **Error patterns** — Are errors clustering around a particular task or component? Recurring errors in the same area suggest a structural problem, not bad luck.

5. **Restart frequency** — How many restarts happened this session? One or two is healthy — the system is self-correcting. Five or more suggests the plan was wrong, the task is under-specified, or the workers are under-scoped.

6. **Judge rejection rate** — If judges are rejecting more than 30-40% of work, either the verification criteria are too strict, the workers aren't getting enough context, or the task decomposition is off.

The review isn't about blame. It's about tuning the system. Every session teaches you something about how well the harness is calibrated for this type of work.
