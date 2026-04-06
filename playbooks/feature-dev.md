# Scenario: New Feature Development (Claude Code Session)

> Extracted from the AgentFW Playbook — Scenario 1: New OpenClaw Feature.

**Context:** You're adding a new capability to your already complex Dex/OpenClaw installation — a multi-agent autonomous assistant with Discord, Google Calendar, Twilio/ElevenLabs, Notion, Flask dashboard, heartbeat engine, hybrid memory search, and tiered model routing. The codebase is large and customized. A single-turn approach will fail.

## The Harness Setup

**Before you write a single line of code**, create the scaffolding that lets Claude Code operate as a planner-worker-judge system across your session.

---

## Option A: Autonomous Mode (Recommended)

Drop this as your launch prompt. One message. Then walk away until Claude comes back with results or a domain question.

See `templates/launch-prompts/autonomous-feature.md` for the standalone launch prompt template.

**What happens after you send this:** Claude Code reads the codebase, produces PLAN.md, dispatches worker agents for implementation, dispatches separate judge agents for verification, and iterates until done. You check in when you want to — or wait until it's done. If it hits a domain question, it asks. Otherwise, it runs.

**Verification gates in autonomous mode:** Every task that produces code MUST have judge verification complete before the next task begins. The planner MUST NOT evaluate its own workers' output as a substitute for judge dispatch — this is role collapse (see `references/anti-patterns.md`). For compiled languages (C++, Rust, Go, etc.), the judge MUST build the project as the first verification step. Reasoning-only review does not count as verification.

Claude dispatches judges between tasks, not just at the end. A sequence of implement-implement-implement-verify-at-end is a verification gap — errors from early tasks compound invisibly through later ones.

---

## Option B: Guided Mode (Step-by-Step)

Use this when you want to co-drive — maybe you're exploring an unfamiliar part of the codebase, or the feature touches something delicate you want to supervise.

### Step 1: Orient (Planner Mode)

Start your Claude Code session by giving it the lay of the land. Don't jump to implementation.

```
I need to add [feature description] to my OpenClaw installation.

Before we write any code, I need you to act as a planner:
1. Read the existing codebase structure — here are the key entry points: [list main files/modules]
2. Identify which modules this feature will touch
3. Identify integration points (Discord bot? Flask dashboard? Memory system? Heartbeat engine?)
4. Identify what could break
5. Produce a PLAN.md with decomposed sub-tasks, each independently verifiable

Do NOT start coding yet. Plan first.
```

### Step 2: Create PROGRESS.md

Have Claude Code create this file in your project root. Use the template from `templates/PROGRESS.md`. This is the harness state.

### Step 3: Execute Task by Task (Worker Mode)

Now work through tasks one at a time. For each sub-task, Claude operates as the worker:

```
We're on Task 2 from PROGRESS.md. Work in clean isolation on this task only.
- Here's what Task 1 produced: [brief summary or point to the artifact]
- Here's what "done" looks like for Task 2: [verification criteria]
- Don't touch anything outside this task's scope.
- When you're done, show me the results and the verification evidence.
```

When Claude completes the task, **you review the results.** You are the judge in guided mode. Look at:
- Does it meet the verification criteria you set?
- Did it break anything from previous tasks?
- Run the relevant tests/checks and review the output.

If it looks right, update PROGRESS.md and move to the next task. If something's off, tell Claude what's wrong and have it redo the task — or, if the approach is fundamentally broken, restart the task with a fresh description informed by what you learned.

If you want automated verification instead of reviewing yourself, dispatch a **separate sub-agent** for it. Don't ask the same session that just implemented the change to evaluate its own work.

### Step 4: Session Handoff

If you need to continue in a new Claude Code session:

```
Read PROGRESS.md and the PLAN.md in this project.
Orient yourself: what's done, what's next, what decisions were made.
Then pick up where we left off.
```

---

## Key Principles for Feature Work

- **Your tiered routing architecture is itself a harness.** When planning features that affect routing (Haiku/Gemini Flash/Sonnet), think about which tier handles what and how the feature changes those boundaries.
- **The heartbeat engine, memory system, and Discord bot are independent workers.** Treat them that way — changes to one shouldn't require holding the full context of the others.
- **Your Proxmox/Tailscale infrastructure is a verification layer.** You can test in isolation on your Debian containers before anything goes live.
- **Sniff-check opportunity:** After Claude Code produces the implementation, you should be able to read the key files and tell within minutes if the approach is sound. If you can't, the code isn't structured well enough — push back.
