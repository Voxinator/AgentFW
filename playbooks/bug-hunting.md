# Scenario: Troubleshooting a Transient Bug (Claude Code Session)

> Extracted from the AgentFW Playbook — Scenario 2.

**Context:** Something's broken in OpenClaw, and it's intermittent. This is fundamentally different from feature work — you're in detective mode, not builder mode. The harness adapts.

## The Harness Setup

Troubleshooting has its own version of Decompose → Parallelize → Verify → Iterate, but the decomposition is about hypotheses, not tasks.

---

## Option A: Autonomous Mode (Recommended)

One launch prompt. Claude runs the full diagnostic cycle — hypothesize, test, rule out, converge, fix, verify — and comes back with a root cause and fix.

See `templates/launch-prompts/autonomous-bug.md` for the standalone launch prompt template.

**Especially important for transient bugs:** If Claude exhausts its initial hypotheses without finding root cause, the right move is to add observability (logging, metrics, state dumps) and ask you to let it run until the bug manifests again with better evidence. That's not failure — that's the correct diagnostic approach for intermittent issues.

**Why role separation matters especially for bug fixes:** The Discord channel bug is a textbook example. The main session identified root cause, wrote the fix scripts, then verified its own work by scanning for the same patterns it just fixed. It checked for what it *intended* to fix. A cold judge might have also checked: do the modified prompts actually parse correctly? Do the delivery targets match the stated intent for each job? Are there other delivery paths (HEARTBEAT.md signal handlers) that hit the same failure mode? A fresh context asks different questions.

---

## Option B: Guided Mode (Step-by-Step)

Use this when the bug is in a critical path and you want eyes on every diagnostic step, or when you suspect the bug involves interactions between systems that require your real-time environment access.

### Step 1: Scene Report (Planner Mode)

Start by giving Claude Code everything you know. Don't theorize yet — just dump the evidence.

```
I've got a transient bug in OpenClaw. Here's everything I know:

**Symptoms:**
- What happens: [exact behavior]
- When it happens: [frequency, timing, conditions]
- When it doesn't happen: [what's different]

**Recent changes:**
- [Anything deployed recently]
- [Config changes]
- [Dependency updates]

**Environment:**
- [Proxmox container details]
- [Relevant service versions]
- [Any resource constraints observed]

**Logs/evidence:**
[Paste relevant log snippets]

Before we fix anything, I need you to:
1. Generate 3-5 hypotheses ranked by likelihood
2. For each hypothesis, specify what evidence would confirm or rule it out
3. Identify the fastest diagnostic checks we can run
```

### Step 2: Create DIAGNOSTIC.md

This is your troubleshooting harness state file. See `templates/DIAGNOSTIC.md` for the template.

### Step 3: Investigate Hypotheses (Worker Mode)

Work through hypotheses one at a time, highest likelihood first. Each investigation is a clean sub-task. Claude operates as the worker:

```
Let's investigate Hypothesis 1: [description].
The check we need to run is: [specific diagnostic].
Show me the command/code and let's see the results.
Don't fix anything yet — just gather evidence.
```

After each diagnostic, **you evaluate the results.** You are the judge in guided mode.

- Does this confirm or rule out the hypothesis?
- Do we need to adjust the remaining hypotheses?
- What's the next most efficient check to run?

Update DIAGNOSTIC.md with the outcome.

If you want automated evaluation instead of reviewing yourself, dispatch a **separate sub-agent** to assess the diagnostic results against the hypothesis criteria.

### Step 4: Fix with Verification

Once root cause is identified:

```
Root cause is confirmed: [description].

Now, plan the fix:
1. What's the minimal change that resolves this?
2. How do we verify the fix works?
3. How do we verify nothing else broke?
4. Can we add a check/log/test that catches this if it recurs?

Implement the fix and verification together.
```

After Claude implements the fix, **you review it** — or dispatch a separate sub-agent to verify the fix cold (receiving only the original symptoms, current system state, and verification criteria).

---

## Key Principles for Transient Bug Hunting

- **Transient bugs are verification problems.** The bug is intermittent because a condition is intermittent. Your job is to identify and verify the condition, not the symptom.
- **Don't let Claude Code jump to fixes.** The biggest failure mode is "I think I see the problem, let me fix it" before the hypothesis is confirmed. Enforce the diagnostic discipline.
- **Fresh context is your friend.** If you've been chasing a hypothesis for 20+ minutes and it's going nowhere, restart with a clean context. Tell the new context what you've ruled out and let it approach fresh.
- **Logs are your machine-checkable tier.** Add logging before you add fixes. A transient bug you can't reproduce on demand is a bug you need better observability for.
- **Your Tailscale access means you can run diagnostics remotely from iOS.** Use that to capture evidence when the bug occurs naturally rather than trying to reproduce it on demand.
