# Error Recovery Protocol

Errors are expected. The harness exists precisely because one-shot perfection is unrealistic. When errors occur:

1. **Don't patch forward blindly.** If an error occurs midway through, it propagates through everything downstream. Recognize this.

2. **Assess the blast radius.** Is this a local error (fix and continue) or a structural error (the approach is wrong)?

3. **For local errors:** Fix, re-verify, continue.

4. **For structural errors:** Restart with fresh context. Bring forward only what was learned, not the accumulated state. This is the judge pattern — a clean restart informed by failure is better than trying to salvage a broken approach.

5. **Document what went wrong** in the progress file so future iterations don't repeat it.

### Late-Discovery Errors (Undetected Accumulation)

When errors are discovered after multiple tasks have proceeded past the point of failure — e.g., a build attempted after three implementation steps reveals errors from step 1 — treat this as a **structural error regardless of the apparent blast radius** of any individual error.

**Do not attempt to fix forward across multiple unverified tasks.** Instead:

1. **Roll back** to the last verified checkpoint in PROGRESS.md.
2. **Re-plan** from that checkpoint with the error findings as input.
3. **Document the verification gap** — which tasks lacked verification and why — in the Things Learned section.

This scenario is a symptom of missing verification gates. After recovery, ensure every subsequent task has judge verification before the next task dispatches.

---

## Rollback via Side-Effect Checkpoints

When recovering from errors, side-effect checkpoints (see `references/state-management.md`) are your rollback points. Every completed task records what it changed — files modified, commands run, external calls made — along with a checkpoint (git hash or state snapshot).

For code work: `git reset` to the last verified checkpoint. For external systems: use the side-effect record to understand what needs to be undone manually.

Without checkpoints, "restart cleanly" means guessing what the failed step actually did. That's not clean — that's hopeful.

## Error Events in SESSION_LOG

Every error — whether local or structural — gets recorded in SESSION_LOG.md with:
- Timestamp
- Task ID (cross-reference to PROGRESS.md)
- What happened
- Blast radius assessment (local vs. structural)
- What was decided (fix-and-continue vs. restart)

The log is how future sessions learn from past failures without repeating the investigation that led to the recovery decision.
