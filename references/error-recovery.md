# Error Recovery Protocol

Errors are expected. The harness exists precisely because one-shot perfection is unrealistic. When errors occur:

1. **Don't patch forward blindly.** If an error occurs midway through, it propagates through everything downstream. Recognize this.

2. **Assess the blast radius.** Is this a local error (fix and continue) or a structural error (the approach is wrong)?

3. **For local errors:** Fix, re-verify, continue.

4. **For structural errors:** Restart with fresh context. Bring forward only what was learned, not the accumulated state. This is the judge pattern — a clean restart informed by failure is better than trying to salvage a broken approach.

5. **Document what went wrong** in the progress file so future iterations don't repeat it.

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
