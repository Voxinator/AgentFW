# Bug Report: [Short Description]

## Symptoms
- What happens: [exact behavior, exact error messages if any]
- Frequency: [every time / intermittent / only under conditions X]
- When it started: [date/event, or "not sure"]
- What's different when it works vs. when it doesn't: [any pattern you've noticed]

## Recent Changes
- [Deployments, config changes, dependency updates, infrastructure changes]
- [Or "nothing obvious" if that's the case]

## Environment
- Container: [Proxmox container ID, OS, relevant service versions]
- Related services: [what else is running that might interact]
- Resource state: [any memory/CPU/disk observations]

## Logs & Evidence
[Paste everything you have — log snippets, error output, screenshots described, timing data]

## Domain Knowledge
- [Anything about the system's behavior that isn't obvious from the code]
- [Known fragile areas, previous similar bugs, workarounds in place]
- [Integration behaviors with external services — Discord API quirks, Twilio rate limits, etc.]

## Operating Instructions
You are the **planner and judge dispatcher** for this diagnostic. Run autonomously using sub-agents:

1. **Create DIAGNOSTIC.md** as your state file (see `templates/DIAGNOSTIC.md` for the format).
   List 3-5 ranked hypotheses, each with a specific test that confirms or rules it out.

2. **Dispatch sub-agents for investigation.** For each hypothesis, spin up a worker agent
   to run the diagnostic checks (read logs, inspect configs, test API calls, etc.).
   Investigation is read-only — no changes to the system yet.
   Give each worker: the hypothesis to test, the specific checks to run, and the relevant
   system context. Include permission scope: read-only access to specified paths, no writes.
   After each worker returns, evaluate the results yourself and update DIAGNOSTIC.md:
   confirmed, ruled out, or inconclusive.

3. **Do not jump to fixes.** Confirm root cause first. The biggest failure mode
   in debugging is "I think I see it" followed by a patch that masks the real problem.

4. **When root cause is confirmed**, plan the minimal fix. Then enforce separation:
   - **Dispatch a worker agent** to implement the fix. Give it: the root cause,
     the fix specification, clear scope boundaries, and permission scope
     (allowed paths, allowed operations, forbidden operations).
   - **Dispatch a separate judge agent** to verify. Give it: the original symptoms,
     the current system state (post-fix), and verification criteria.
     The judge does NOT receive the fix implementation plan — it evaluates cold.
     It should verify: symptom is resolved, nothing else broke, observability
     was added to catch recurrence.
   - If the judge finds issues, dispatch a *new* worker with the judge's findings.

5. **Maintain state throughout.** Update DIAGNOSTIC.md after each hypothesis test.
   Use `templates/PROGRESS.md` format if the fix becomes multi-step.
   Record side-effects and checkpoints for any changes made.

6. **Only come to me when:**
   - You need to reproduce the bug and need me to trigger it in the live environment
   - You've ruled out all hypotheses and need more domain context
   - The fix requires a judgment call about acceptable tradeoffs
   - Root cause is found and fixed — ready for my review

7. **When you're done**, present: root cause, what was changed, how to verify the
   fix, and what observability was added to catch recurrence.
