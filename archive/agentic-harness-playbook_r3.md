# AgentFW (formerly Agentic Harness) Playbook — Three Scenarios [r3 Archive]

> How to apply the Decompose → Parallelize → Verify → Iterate framework to real work across Claude Code sessions and personal maker projects.

## Two Operating Modes: Guided vs. Autonomous

Every scenario in this playbook offers two modes. Choose based on how much you want to be in the loop.

**Guided Mode** — You act as planner and judge. Claude is the worker. You direct each step, review between tasks, and decide what's next. This is useful when you're learning a new domain, the stakes are high and irreversible, or you genuinely want to co-drive the work.

**Autonomous Mode** — Claude operates as planner, worker, AND judge. You set up the harness (initial context, constraints, domain knowledge, definition of done) and let it run. You re-enter as **domain oracle** when Claude hits a question only you can answer, and as **final sniff-checker** when the work is presented as complete. This is the Cursor model — zero nudges, multi-day runs, planner-worker-judge hierarchy all internal to the agent.

**Your real role in Autonomous Mode is three things:**
1. **Harness builder** — You write the initial prompt that defines the problem, the constraints, what "done" looks like, and the domain knowledge Claude doesn't have. The quality of the harness determines the quality of the output.
2. **Domain oracle** — You answer questions the codebase and docs can't. Architectural quirks, business context, unstated constraints, tribal knowledge.
3. **Final sniff-checker** — Before anything ships, you look at it and say "yes" or "no." That's the last gate.

The autonomous prompts in this playbook are designed to be **dropped into Claude Code or a Claude Project as a single launch prompt** — one message that sets up the full harness and lets the agent run.

---

## Prerequisites: Loading the Framework

The launch prompts in each scenario assume the agent already understands the agentic harness framework — the Decompose → Parallelize → Verify → Iterate pattern, the planner-worker-judge architecture, the progress file protocol, error recovery via clean restart, verification tiers, and all the anti-patterns to avoid. Without that foundation, the operating instructions in each launch prompt are just rules without reasoning. The agent won't know *why* it should restart with fresh context instead of patching forward, or what "judge mode" actually means, or how to structure PROGRESS.md.

**The companion document `agentic-harness-project-instructions.md` IS the framework.** It must be loaded into the session before (or alongside) any launch prompt from this playbook.

### How to Load It — By Platform

**Claude Code (CLAUDE.md)**
Place `agentic-harness-project-instructions.md` in your project root as `CLAUDE.md` (or include/reference it from your existing `CLAUDE.md`). Claude Code reads this file automatically at the start of every session. This is the cleanest approach — the framework is always present, and your launch prompts from this playbook become the first message in the session.

```
# In your project root:
cp agentic-harness-project-instructions.md CLAUDE.md

# Or if you already have a CLAUDE.md, append or include it:
cat agentic-harness-project-instructions.md >> CLAUDE.md
```

If your `CLAUDE.md` is already large (e.g., OpenClaw has its own project conventions), you can keep the harness instructions as a separate file and reference it:

```markdown
# CLAUDE.md (existing project file)

## Project-Specific Instructions
[Your existing OpenClaw conventions, architecture notes, etc.]

## Agentic Operating Framework
See `agentic-harness-project-instructions.md` in project root for the full framework.
When operating autonomously, follow the Decompose → Parallelize → Verify → Iterate
pattern and the planner-worker-judge architecture described there.
```

**Claude Project (Custom Instructions)**
Paste the contents of `agentic-harness-project-instructions.md` into the Project's custom instructions field (Settings → Custom Instructions). This loads the framework into every conversation within that project. Then use the launch prompts from this playbook as your first message in a new conversation.

**Claude Chat (No Project)**
If you're working in a standalone Claude conversation without a Project, paste the framework document as your first message (or attach it as a file), then follow immediately with the scenario launch prompt. This is the least persistent option — the framework only lives for that conversation.

### The Two-Layer Stack

Think of it as two layers:

1. **Layer 1: The Framework** (`agentic-harness-project-instructions.md`) — Loaded once into the project or session. Teaches Claude *how* to operate as an autonomous agent within a harness. Doesn't change per task.

2. **Layer 2: The Launch Prompt** (from this playbook) — Sent as your first message for each specific task. Tells Claude *what* to work on, loads domain knowledge, and defines "done." Changes every time.

Layer 1 without Layer 2 = an agent that knows how to work but has nothing to do.
Layer 2 without Layer 1 = a task description with operating rules the agent doesn't fully understand.
Both together = an autonomous agent with a well-specified harness running against a well-defined task.

---

## Scenario 1: New OpenClaw Feature (Claude Code Session)

**Context:** You're adding a new capability to your already complex Dex/OpenClaw installation — a multi-agent autonomous assistant with Discord, Google Calendar, Twilio/ElevenLabs, Notion, Flask dashboard, heartbeat engine, hybrid memory search, and tiered model routing. The codebase is large and customized. A single-turn approach will fail.

### The Harness Setup

**Before you write a single line of code**, create the scaffolding that lets Claude Code operate as a planner-worker-judge system across your session.

### Option A: Autonomous Mode (Recommended)

Drop this as your launch prompt. One message. Then walk away until Claude comes back with results or a domain question.

```
# Feature: [Feature Name]

## What I Need
[2-3 sentences describing the feature and why it matters]

## Codebase Context
- Entry points: [list main files/modules relevant to this feature]
- Key integration points: [Discord bot, Flask dashboard, memory system, heartbeat engine, etc.]
- Architecture notes: [anything Claude can't learn by reading the code — quirks, conventions,
  unstated constraints, things that look wrong but are intentional]

## Definition of Done
- [ ] [Functional requirement 1]
- [ ] [Functional requirement 2]
- [ ] [Non-functional requirement: performance, compatibility, etc.]
- [ ] Existing tests still pass
- [ ] New functionality has test coverage
- [ ] PROGRESS.md updated with final state

## Domain Knowledge You Won't Find in the Code
- [Architectural quirk or tribal knowledge item]
- [Integration behavior that isn't documented]
- [Constraint from external system]

## Operating Instructions
You are the **planner and judge dispatcher** for this feature. You do NOT implement code directly. Run autonomously using sub-agents:

1. **Plan first.** Read the codebase yourself (read-only investigation is fine for the main session).
   Produce a PLAN.md with decomposed sub-tasks, each with its own verification criteria.
   Do not dispatch any implementation work until the plan exists.

2. **Dispatch sub-agents for implementation.** For each sub-task, spin up a worker agent with:
   - The specific task description from PLAN.md
   - The relevant codebase context it needs
   - The verification criteria for that sub-task
   - Clear scope boundaries (what to touch, what not to touch)
   The worker implements and returns its artifacts. You do NOT write implementation code
   in the main session.

3. **Dispatch a separate sub-agent for verification.** After a worker completes a sub-task,
   spin up a *different* agent to verify the work. The verifier receives:
   - The original sub-task requirements
   - The current state of the code (post-change)
   - The verification criteria
   It does NOT receive the worker's reasoning or implementation plan.
   It evaluates the artifacts cold — running tests, checking for regressions,
   reviewing the changes against the requirements.

4. **If verification fails**, take the judge's findings and dispatch a *new* worker.
   Do not reuse the original worker's context. Fresh start, informed by what the judge found.

5. **Maintain PROGRESS.md throughout.** This is your state file. Update it after
   every sub-task: what's done, what's next, decisions made, things learned.
   If this session dies and a new one starts, PROGRESS.md is how continuity survives.

6. **Only come to me when:**
   - You need domain knowledge not in the code or docs
   - You've hit an architectural decision that could go multiple ways and needs my input
   - The feature is complete and ready for my final sniff-check

7. **When you're done**, present: what was built, what was changed, how to verify it,
   and anything I should pay attention to during sniff-check.
```

**What happens after you send this:** Claude Code reads the codebase, produces PLAN.md, dispatches worker agents for implementation, dispatches separate judge agents for verification, and iterates until done. You check in when you want to — or wait until it's done. If it hits a domain question, it asks. Otherwise, it runs.

### Option B: Guided Mode (Step-by-Step)

Use this when you want to co-drive — maybe you're exploring an unfamiliar part of the codebase, or the feature touches something delicate you want to supervise.

#### Step 1: Orient (Planner Mode)

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

#### Step 2: Create PROGRESS.md

Have Claude Code create this file in your project root. This is the harness state.

```markdown
# PROGRESS — [Feature Name]

## Feature Summary
[One paragraph: what this does and why]

## Architecture Impact
- Modules touched: [list]
- Integration points: [list]
- Risk areas: [list]

## Task Breakdown
- [ ] Task 1: [description] — Verify by: [how]
- [ ] Task 2: [description] — Verify by: [how]
- [ ] Task 3: [description] — Verify by: [how]

## Decisions Made
[Accumulate as you go]

## Things Learned
[Accumulate as you go]
```

#### Step 3: Execute in Worker Mode

Now work through tasks one at a time. For each sub-task:

```
We're on Task 2 from PROGRESS.md. Work in clean isolation on this task only.
- Here's what Task 1 produced: [brief summary or point to the artifact]
- Here's what "done" looks like for Task 2: [verification criteria]
- Don't touch anything outside this task's scope.
- When you're done, tell me how to verify it.
```

#### Step 4: Judge After Each Task

After each sub-task completes, switch to judge mode:

```
Let's verify Task 2 before moving on.
- Does it pass the verification criteria we set?
- Did it break anything Task 1 established?
- Run [tests/checks] and show me results.
- Update PROGRESS.md with the outcome.
```

**If verification fails:** Don't patch. Restart the sub-task with fresh context. Tell Claude Code what went wrong and what you learned, but let it approach the problem clean.

#### Step 5: Session Handoff

If you need to continue in a new Claude Code session:

```
Read PROGRESS.md and the PLAN.md in this project.
Orient yourself: what's done, what's next, what decisions were made.
Then pick up where we left off.
```

### Key Principles for OpenClaw Features

- **Your tiered routing architecture is itself a harness.** When planning features that affect routing (Haiku/Gemini Flash/Sonnet), think about which tier handles what and how the feature changes those boundaries.
- **The heartbeat engine, memory system, and Discord bot are independent workers.** Treat them that way — changes to one shouldn't require holding the full context of the others.
- **Your Proxmox/Tailscale infrastructure is a verification layer.** You can test in isolation on your Debian containers before anything goes live.
- **Sniff-check opportunity:** After Claude Code produces the implementation, you should be able to read the key files and tell within minutes if the approach is sound. If you can't, the code isn't structured well enough — push back.

---

## Scenario 2: Troubleshooting a Transient Bug (Claude Code Session)

**Context:** Something's broken in OpenClaw, and it's intermittent. This is fundamentally different from feature work — you're in detective mode, not builder mode. The harness adapts.

### The Harness Setup

Troubleshooting has its own version of Decompose → Parallelize → Verify → Iterate, but the decomposition is about hypotheses, not tasks.

### Option A: Autonomous Mode (Recommended)

One launch prompt. Claude runs the full diagnostic cycle — hypothesize, test, rule out, converge, fix, verify — and comes back with a root cause and fix.

```
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

1. **Create DIAGNOSTIC.md** as your state file. List 3-5 ranked hypotheses,
   each with a specific test that confirms or rules it out.

2. **Dispatch sub-agents for investigation.** For each hypothesis, spin up a worker agent
   to run the diagnostic checks (read logs, inspect configs, test API calls, etc.).
   Investigation is read-only — no changes to the system yet.
   After each worker returns, evaluate the results yourself and update DIAGNOSTIC.md:
   confirmed, ruled out, or inconclusive.

3. **Do not jump to fixes.** Confirm root cause first. The biggest failure mode
   in debugging is "I think I see it" followed by a patch that masks the real problem.

4. **When root cause is confirmed**, plan the minimal fix. Then enforce separation:
   - **Dispatch a worker agent** to implement the fix. Give it: the root cause,
     the fix specification, and clear scope boundaries.
   - **Dispatch a separate judge agent** to verify. Give it: the original symptoms,
     the current system state (post-fix), and verification criteria.
     The judge does NOT receive the fix implementation plan — it evaluates cold.
     It should verify: symptom is resolved, nothing else broke, observability
     was added to catch recurrence.
   - If the judge finds issues, dispatch a *new* worker with the judge's findings.

5. **Only come to me when:**
   - You need to reproduce the bug and need me to trigger it in the live environment
   - You've ruled out all hypotheses and need more domain context
   - The fix requires a judgment call about acceptable tradeoffs
   - Root cause is found and fixed — ready for my review

6. **When you're done**, present: root cause, what was changed, how to verify the
   fix, and what observability was added to catch recurrence.
```

**Especially important for transient bugs:** If Claude exhausts its initial hypotheses without finding root cause, the right move is to add observability (logging, metrics, state dumps) and ask you to let it run until the bug manifests again with better evidence. That's not failure — that's the correct diagnostic approach for intermittent issues.

**Why role separation matters especially for bug fixes:** The Discord channel bug is a textbook example. The main session identified root cause, wrote the fix scripts, then verified its own work by scanning for the same patterns it just fixed. It checked for what it *intended* to fix. A cold judge might have also checked: do the modified prompts actually parse correctly? Do the delivery targets match the stated intent for each job? Are there other delivery paths (HEARTBEAT.md signal handlers) that hit the same failure mode? A fresh context asks different questions.

### Option B: Guided Mode (Step-by-Step)

Use this when the bug is in a critical path and you want eyes on every diagnostic step, or when you suspect the bug involves interactions between systems that require your real-time environment access.

#### Step 1: Scene Report (Planner Mode)

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

#### Step 2: Create DIAGNOSTIC.md

This is your troubleshooting harness state file.

```markdown
# DIAGNOSTIC — [Bug Description]

## Symptoms
[Summary]

## Hypotheses
1. **[Hypothesis]** — Likelihood: High/Med/Low
   - Confirm by: [check]
   - Rule out by: [check]
   - Status: ⏳ Untested

2. **[Hypothesis]** — Likelihood: High/Med/Low
   - Confirm by: [check]
   - Rule out by: [check]
   - Status: ⏳ Untested

## Evidence Collected
- [timestamp] [finding]

## Ruled Out
- [Hypothesis X] — because [evidence]

## Root Cause
[Fill in when found]

## Fix Applied
[What was changed and why]

## Verification
[How we confirmed the fix works]
```

#### Step 3: Investigate in Worker Mode

Work through hypotheses one at a time, highest likelihood first. Each investigation is a clean sub-task:

```
Let's investigate Hypothesis 1: [description].
The check we need to run is: [specific diagnostic].
Show me the command/code and let's see the results.
Don't fix anything yet — just gather evidence.
```

#### Step 4: Judge Each Hypothesis

After each diagnostic:

```
Based on what we found:
- Does this confirm or rule out Hypothesis 1?
- Update DIAGNOSTIC.md
- Do we need to adjust our remaining hypotheses?
- What's the next most efficient check to run?
```

#### Step 5: Fix with Verification

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

### Key Principles for Transient Bug Hunting

- **Transient bugs are verification problems.** The bug is intermittent because a condition is intermittent. Your job is to identify and verify the condition, not the symptom.
- **Don't let Claude Code jump to fixes.** The biggest failure mode is "I think I see the problem, let me fix it" before the hypothesis is confirmed. Enforce the diagnostic discipline.
- **Fresh context is your friend.** If you've been chasing a hypothesis for 20+ minutes and it's going nowhere, restart with a clean context. Tell the new context what you've ruled out and let it approach fresh.
- **Logs are your machine-checkable tier.** Add logging before you add fixes. A transient bug you can't reproduce on demand is a bug you need better observability for.
- **Your Tailscale access means you can run diagnostics remotely from iOS.** Use that to capture evidence when the bug occurs naturally rather than trying to reproduce it on demand.

---

## Scenario 3: Personal Manufacturing Cost Calculator (Web Tool)

**Context:** You want to build a web-based pricing tool for your personal maker business. You're producing suncatchers using a multi-step manufacturing process: 3D printing (filament), laser engraving (xTool P2 CO2 or F2 Ultra MOPA), UV printing (EufyMake E1), and acrylic stock. Materials come from Amazon. You need to understand true cost per unit to price correctly.

### The Harness Setup

This is a build project where you have irreplaceable domain knowledge — your actual manufacturing process, real costs, machine quirks, and waste rates. Claude can plan and dispatch workers to build and judges to verify, but it needs your production reality as input. The autonomous mode front-loads all that domain knowledge so Claude can run the full build without interruption.

### Option A: Autonomous Mode (Recommended)

One launch prompt with your complete production data. Claude builds the full tool — cost model engine, UI, persistence — and comes back with a working product for you to verify against real numbers.

```
# Build: Suncatcher Manufacturing Cost Calculator

## What I Need
A web-based tool I'll actually use in my workshop to understand true cost-per-unit
and set profitable pricing for my suncatcher products. This is a real business tool,
not a demo.

## My Manufacturing Process (Complete)
Each suncatcher goes through these steps in order:

### Step 1: 3D Print Frame/Base
- Machine: [printer model]
- Filament: [type, brand]
- Cost per roll: $[X] for [weight] from Amazon
- Estimated grams per unit: [X]g (including supports/waste)
- Print time per unit: [X] minutes
- Failure/scrap rate: ~[X]% (failed prints, adhesion issues, etc.)

### Step 2: Laser Engrave/Cut Acrylic
- Machine: xTool P2 CO2 and/or xTool F2 Ultra MOPA fiber
- Acrylic stock: [size] sheets, $[X] per sheet from [source]
- Units per sheet: [X] (accounting for kerf and spacing)
- Machine time per unit: [X] minutes
- Waste rate: ~[X]% (cracked pieces, alignment errors)
- Consumables: CO2 tube replacement every ~[X] hours ($[X])

### Step 3: UV Print Color Layer
- Machine: EufyMake E1
- Ink cost: $[X] per cartridge set
- Estimated prints per cartridge set: [X]
- Machine time per unit: [X] minutes
- Waste rate: ~[X]% (misprints, alignment issues)

### Step 4: Assembly
- Additional materials: [glue, hardware, etc. with costs]
- Assembly time per unit: [X] minutes

### Step 5: Finishing/Packaging
- Packaging materials: $[X] per unit
- Packaging time: [X] minutes

## Machine Inventory (for depreciation)
| Machine | Purchase Price | Expected Lifespan | Annual Hours Used |
|---------|---------------|-------------------|-------------------|
| 3D Printer [model] | $[X] | [X] years | ~[X] hrs |
| xTool P2 CO2 | $[X] | [X] years | ~[X] hrs |
| xTool F2 Ultra MOPA | $[X] | [X] years | ~[X] hrs |
| EufyMake E1 | $[X] | [X] years | ~[X] hrs |

## Other Overhead
- Electricity estimate: ~$[X]/kWh
- My labor rate: $[X]/hour (what I want to pay myself)
- Workspace cost: $[X]/month (or $0 if home workshop, no allocation)
- Amazon shipping: [Prime member? Per-order shipping costs?]

## Verification Data (Critical)
Here's a real project I've already made and roughly costed:
- Product: [specific suncatcher design]
- Actual materials used: [specifics]
- Actual time spent: [X] minutes total
- What I think it costs me: ~$[X] per unit
- What I've been charging: $[X]
→ The calculator MUST get within 15% of my known cost. If it doesn't, the model is wrong.

## Functional Requirements
- [ ] Accurate cost-per-unit breakdown: materials, machine time, labor, depreciation, overhead
- [ ] Input a new product's specs and see instant cost breakdown
- [ ] Set target margin percentage, see recommended retail price
- [ ] Save projects for future reference (persistent storage)
- [ ] Dashboard showing all products and their margins
- [ ] Editable material prices (costs change, Amazon prices fluctuate)
- [ ] Compare different production approaches (P2 vs F2 for same cut, for example)

## Operating Instructions
You are the **planner and judge dispatcher** for this build. You do NOT write implementation code directly. Run autonomously using sub-agents:

1. **Plan the build order.** Cost model engine first, then UI, then persistence.
   Produce a brief PLAN.md. Do not dispatch implementation until the plan exists.

2. **Dispatch a worker agent to build the cost model engine.**
   Give it: the full manufacturing process data, the cost categories, and the
   verification data (my real project with known cost). The worker builds the
   engine and returns the module.

3. **Dispatch a separate judge agent to verify the cost model.**
   Give it: the verification project data and the cost model module (no
   implementation reasoning). The judge runs my known project through the model
   and checks: does it land within 15%? Are all cost categories accounted for?
   Does the math make sense? If it fails, take the judge's findings and
   dispatch a new worker to fix it.

4. **Once the cost model is verified, dispatch a worker to build the UI.**
   Practical, clean, workshop-friendly. Not a design showcase.
   I need to use this with dirty hands and limited patience.
   Build as a React artifact with persistent storage.

5. **Dispatch a judge to verify the full tool.**
   - Cost model: does the math check out against my known project?
   - UI: does every input actually affect the calculation correctly?
   - Persistence: do saved projects survive across sessions?
   - Edge cases: what happens with zero quantities, missing inputs, extreme values?

6. **Only come to me when:**
   - The cost model doesn't match my verification data and you need more production details
   - There's a UX decision that depends on how I actually work (e.g., do I batch or make one-offs?)
   - The tool is ready for me to test with real numbers

7. **When you're done**, present the working tool and show me the cost breakdown
   for my verification project so I can sniff-check the math immediately.
```

**What makes this different from guided mode:** You're giving Claude your complete domain knowledge upfront — the entire manufacturing process, real costs, real waste rates, machine inventory. That's the harness. With all of that loaded, Claude can plan, dispatch workers to build, dispatch judges to verify, and iterate — all without you in the loop until the final sniff-check. Your re-entry point is testing it against reality.

### Option B: Guided Mode (Step-by-Step)

Use this if you're still figuring out your own production process and want to think through the cost model conversationally before building anything. Also useful if you want to iterate on the UI design interactively.

#### Step 1: Process Mapping (Planner Mode)

Before any code, map the manufacturing process. This is the domain knowledge that Claude doesn't have.

```
I'm building a web-based cost calculator for my suncatcher production.
Before we build anything, help me map out the cost model.

My manufacturing process:
1. 3D print a frame/base (filament: [type], [cost per roll], [estimated grams per unit])
2. Laser engrave design onto acrylic (xTool P2 or F2 Ultra MOPA)
   - Acrylic sheets: [size, cost per sheet, units per sheet]
   - Machine time: [estimated minutes per unit]
3. UV print color layer (EufyMake E1)
   - Ink cost: [cost per cartridge set, estimated prints per set]
   - Machine time: [estimated minutes per unit]
4. Assembly: [any additional materials, time estimate]

Cost categories I need to track:
- Raw materials (filament, acrylic, ink)
- Machine consumables (laser tube life, print head life)
- Machine time (electricity, depreciation)
- My time (labor rate I want to pay myself)
- Amazon shipping / per-unit material cost
- Waste/scrap rate
- Packaging and shipping to customer (if applicable)

Help me build the cost model BEFORE we build the UI.
What am I missing? What should I track that I'm not thinking about?
```

#### Step 2: Decompose the Build

```
Now let's plan the tool itself. Decompose this into buildable pieces:

Piece 1: Cost Model Engine
- Input: material costs, machine parameters, labor rate
- Output: cost per unit with full breakdown
- Verify by: I can manually check the math against a known project

Piece 2: Material Database
- Track my actual Amazon purchase prices over time
- Calculate per-unit material costs (e.g., $25 roll / X grams per unit)
- Handle multi-pack pricing, shipping costs

Piece 3: Machine Cost Calculator
- Depreciation over expected lifespan
- Consumable replacement schedule
- Power consumption estimates
- Per-minute operating cost for each machine

Piece 4: Pricing Interface
- Input a new product's specs
- See full cost breakdown
- Set target margin
- Get recommended retail price
- Compare different production approaches

Piece 5: Project History
- Save past projects with actual costs
- Track estimated vs actual over time
- See which products are most/least profitable

Build these as independent modules. Which should we start with?
```

#### Step 3: Build Iteratively (Worker Mode)

Start with the cost model engine — it's the foundation and it's machine-checkable (the math is either right or it isn't).

```
Let's build Piece 1: the Cost Model Engine.

Requirements:
- Takes raw inputs: material costs, quantities, machine time, labor time
- Calculates: material cost, machine cost, labor cost, overhead, total cost per unit
- Outputs a full breakdown I can review line by line

Build this as a standalone module first. I want to verify the math
against a real project before we add any UI.

Here's a real example to test against:
- [Your actual suncatcher project with known costs]
- I know this costs me approximately $X to make
- The calculator should get within 10% of that
```

#### Step 4: Verify With Real Data (Judge Mode)

```
Let's verify the cost model against my actual production data:

Project: [Specific suncatcher design]
- Filament used: [X] grams of [type] from [Amazon link, price]
- Acrylic: [size] sheet, [cost], got [N] pieces from it
- Laser time: [X] minutes on P2/F2
- UV print time: [X] minutes
- Assembly: [X] minutes
- My labor rate: $[X]/hour

Expected total cost: ~$[X] per unit
What does the calculator say?
Where are the discrepancies? Adjust the model.
```

#### Step 5: Layer on the UI

Only after the cost model is verified:

```
The cost model is solid. Now let's build the pricing interface.

I want a clean, practical tool — not a flashy demo.
This is a tool I'll actually use in my workshop.

Key interactions:
- Quick-add a new project: select machines used, enter material quantities
- See instant cost breakdown as I enter specs
- Set my target margin (e.g., 40%) and see the price
- Save the project for future reference
- Dashboard showing all my products and their margins

Build this as a React artifact I can use.
Use persistent storage so my projects survive across sessions.
```

### Key Principles for the Cost Calculator

- **You are the domain expert AND the judge.** Only you know your actual production costs, machine quirks, and waste rates. Claude builds the tool; you verify it against reality.
- **Real data is your Tier 1 verification.** Test every calculation against actual projects you've already costed out by hand (or by gut feel). If the numbers don't match your experience, the model is wrong.
- **Start with the math, not the UI.** The cost model engine is the core value. If the math is right but the UI is ugly, you still have a useful tool. If the UI is beautiful but the math is wrong, you have nothing.
- **Account for the things that are easy to forget:** waste/scrap rate, failed prints, machine warm-up time, material that's consumed but doesn't end up in the product (laser kerf, support material, purge lines).
- **Your Amazon purchase history is a data source.** Track actual prices paid over time, not listed prices. Prices fluctuate, shipping costs vary, and multi-pack vs single pricing matters.
- **Depreciation is real.** Your xTool P2, F2 Ultra, EufyMake E1, and 3D printer all have finite lifespans. The cost per unit should include a fraction of the machine cost amortized over its expected total output.

---

## Cross-Scenario Patterns

### What's the Same Everywhere

| Principle | Scenario 1 (Feature) | Scenario 2 (Bug) | Scenario 3 (Maker) |
|-----------|----------------------|-------------------|---------------------|
| **Decompose first** | Task breakdown | Hypothesis list | Build pieces |
| **State file** | PROGRESS.md | DIAGNOSTIC.md | Project cost data |
| **Verification** | Tests pass | Hypothesis confirmed | Math matches reality |
| **Fresh restart** | New sub-task context | New hypothesis | Recalculate from inputs |
| **Your role (Autonomous)** | Harness builder → Domain oracle → Final sniff-check | Scene report → Domain oracle → Approve fix | Domain data provider → Verify against real costs |
| **Your role (Guided)** | Planner + Judge | Planner + Judge | Domain expert + Judge |

### Guided vs. Autonomous: When to Choose What

**Go Autonomous when:**
- You can fully describe the problem, constraints, and "done" criteria upfront
- The work is primarily execution against a well-understood goal
- Verification is machine-checkable (tests, compilation, math) or you can sniff-check the final output
- You trust the domain knowledge you've loaded into the harness
- You'd rather spend your time on something else and review later

**Go Guided when:**
- You're still figuring out what you want (the problem definition is fuzzy)
- The domain is new to you and you want to learn alongside the work
- The stakes are high and mistakes are irreversible (production infrastructure, stakeholder-facing deliverables)
- You need the conversational back-and-forth to think through the problem
- You enjoy co-driving and want to be in the loop

**Switch from Autonomous to Guided when:**
- Claude keeps coming back with domain questions (the harness was under-specified)
- The sniff-check reveals the approach is fundamentally off (need to redirect, not just fix)
- The problem turned out to be more ambiguous than expected

**Switch from Guided to Autonomous when:**
- You've established the direction and now it's just execution
- You realize you're giving the same kind of feedback repeatedly (encode it in the harness instead)
- You're bottlenecking progress by being in the loop on every step

### The Meta-Skill Across All Three Scenarios

In every case, the most valuable thing you do is **not the execution** — it's:

1. **Building the harness well** — Front-loading the domain knowledge, constraints, and definition of done so the agent can run without you. The quality of the autonomous prompt IS the quality of the output.
2. **Knowing what "correct" looks like** — The final sniff-check. You look at the output and know in your gut whether it's right. That evaluation skill is worth more than the ability to produce the output yourself.
3. **Bringing knowledge the agent can't get on its own** — Tribal knowledge, stakeholder dynamics, machine quirks, business context. You're the domain oracle. Load it into the harness upfront, or answer when asked.
4. **Deciding when to restart vs. continue** — Whether you're in autonomous or guided mode, recognizing "this approach is off, start over" is a judgment call that humans still make better than agents.

### When to Use Which Harness Weight

**Two dimensions to consider: complexity AND autonomy.**

| | Simple Task | Structured Task | Long-Horizon Task |
|---|---|---|---|
| **No harness needed** | Quick question, one-shot answer | — | — |
| **Guided** | Small edit you want to co-drive | Feature you want to learn from | Sensitive multi-session work |
| **Autonomous** | — (overkill) | Feature, bug fix, full product build | Large codebase changes, multi-session builds |

**Harness weight by complexity:**
- **Lightweight** (mental model only, no files): One-shot tasks, quick questions, simple edits
- **Medium** (PROGRESS.md + plan): Multi-step features, structured builds, diagnostic sessions
- **Heavyweight** (full state management + context docs + verification checkpoints): Multi-session projects, complex troubleshooting, cross-team coordination

Match the harness weight to the problem. Over-engineering the harness for a simple task wastes time. Under-engineering it for a complex task guarantees context loss and rework.

**The autonomous launch prompt IS the harness.** The more domain knowledge, constraints, and verification criteria you load into it, the longer and better the agent runs without you. Think of writing the autonomous prompt as an investment — 30 minutes of harness-building can save hours of back-and-forth.
