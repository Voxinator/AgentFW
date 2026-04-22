# AgentFW (formerly Agentic Harness) Playbook — PM Feature Investigation [r3 Archive]

> Applying the Decompose → Parallelize → Verify → Iterate framework to Product Management feature work.

---

## Prerequisites: Loading the Framework

This playbook assumes the agent already understands the agentic harness framework — the Decompose → Parallelize → Verify → Iterate pattern, the planner-worker-judge architecture, the progress file protocol, error recovery via clean restart, verification tiers, and all the anti-patterns to avoid.

**The companion document `agentic-harness-project-instructions.md` IS the framework.** It must be loaded into the session before (or alongside) any launch prompt from this playbook.

### How to Load It

**Claude Project (Recommended for PM Work)**
Paste the contents of `agentic-harness-project-instructions.md` into the Project's custom instructions field (Settings → Custom Instructions). Also load your PM methodology skill/context into the same project. This gives the agent both the operating framework and your company-specific process. Then use the launch prompts below as your first message in a new conversation.

**Claude Code**
If you're using Claude Code for document generation or analysis alongside PM work, place `agentic-harness-project-instructions.md` in your project root as `CLAUDE.md` (or reference it from your existing `CLAUDE.md`).

**Claude Chat (No Project)**
Paste the framework document as your first message (or attach it as a file), then follow immediately with the scenario launch prompt.

### The Two-Layer Stack

1. **Layer 1: The Framework** (`agentic-harness-project-instructions.md`) — Teaches Claude *how* to operate as an autonomous agent within a harness. Doesn't change per task.
2. **Layer 2: The Launch Prompt** (from this playbook) — Tells Claude *what* to investigate, loads domain knowledge, and defines "done." Changes every feature.

Both layers together = an autonomous agent with a well-specified harness running against a well-defined investigation.

---

## Two Operating Modes: Guided vs. Autonomous

**Guided Mode** — You act as planner and judge. Claude is the worker. You direct each step, review between tasks, and decide what's next. Useful when the feature is politically sensitive, when you're new to the domain, or when you want to think conversationally.

**Autonomous Mode** — Claude operates as planner, worker, AND judge. You set up the harness (business context, constraints, domain knowledge, definition of done) and let it run the full investigation. You re-enter as **domain oracle** when Claude needs stakeholder input, and as **final sniff-checker** before presenting to leadership.

**Your real role in Autonomous Mode:**
1. **Harness builder** — Front-load the business request, domain knowledge, constraints, and organizational context.
2. **Domain oracle** — Answer stakeholder questions, provide business context the agent can't get from docs.
3. **Final sniff-checker** — Review the investigation package before it goes to leadership.

---

## PM Feature Project — Investigation Through Delivery

**Context:** You're a Product Manager in [Your Value Stream]. You've been assigned a new feature project (e.g., [Feature Name]). You need to take it through the feature intake process: New Request → ROM → Investigation → Investigation Complete → Approved → Implementation → Validation → Done. This is expert-checkable (Tier 2) work — your stakeholders and leadership are the sniff-checkers.

### The Harness Setup

Your existing PM methodology IS a harness. The feature intake process (New Request → ROM → Investigation → Investigation Complete → Approved → Implementation → Validation → Done) already has decomposition, verification checkpoints, and iteration built in. The question is whether you're hand-driving Claude through each step or letting it run the investigation autonomously.

### Option A: Autonomous Mode (Recommended for Investigation Phase)

One launch prompt. Claude runs the full investigation, produces the deliverables, and comes back with a draft investigation document ready for your sniff-check before you take it to leadership.

```
# Feature Investigation: [Feature Name]

## Current Intake Status
New Request → heading toward ROM and Investigation

## Business Request
- Requested by: [who]
- What they want: [their words, not yours yet]
- Why: [business driver]
- Value stream: [Your Value Stream]
- Key stakeholders: [list names and roles]

## Known Context
- Integration points I'm aware of: [list known integration points]
- Related past work: [any previous features or investigations that touch this area]
- Political/organizational context: [anything Claude needs to know about stakeholder dynamics,
  budget sensitivity, competing priorities]

## Domain Knowledge
- [How this area of the product actually works today — the stuff that isn't in Jira]
- [Known technical debt or constraints in the affected area]
- [Things other PMs or engineers have mentioned about this space]

## Constraints
- Feature scope target: 12-16 weeks max
- Investigation accuracy target: ±75%
- Current strategic theme: [your org's current theme, e.g., stability and predictability]
- Must align to OKRs: [list the specific KRs this could connect to]
- Budget status: [known / unknown / needs funding request]

## Operating Instructions
You are the **planner and judge dispatcher** for this investigation. Run autonomously using sub-agents:

1. **Decompose the investigation into parallel research tracks** (this is planning — do it yourself):
   - Technical landscape (what exists, what it touches, architecture implications)
   - Business requirements (users, use cases, scope boundaries)
   - Effort & complexity (modules affected, cross-team dependencies, estimated size)
   - Risk & dependencies (blockers, competing work, backward compatibility)

2. **Dispatch worker agents for each research track.** Each worker receives:
   - The track's specific questions to answer
   - The relevant domain knowledge and constraints from this prompt
   - Instructions to flag assumptions vs. facts
   Workers produce findings. You evaluate and synthesize across tracks.

3. **Dispatch a worker agent to produce the deliverables** from the synthesized findings:
   - Investigation document (using our standard template): problem statement, scope,
     effort vs value, conceptual design, projected solution, resources, timeline, risks
   - Stakeholder questions list: questions I need to take to real humans that you can't answer
   - Risk register: what could block or derail this
   - Recommended next steps: what needs to happen to move from Investigation to Investigation Complete

4. **Dispatch a separate judge agent to review the deliverables.** The judge receives:
   - The original business request and constraints (from this prompt)
   - The produced deliverables
   - This checklist to evaluate against:
     - Does the scope fit 12-16 weeks?
     - Are estimates within ±75%?
     - Did it identify all cross-team dependencies?
     - Does this align with current strategic theme?
     - Is there a quantitative value proposition? (OKR: 50% of features need one)
     - Has it accounted for vendor/contractor resource rotation risk?
     - Is benefit realization measurement defined? (needed for 1/3/6-month assessments)
     - Can leadership sniff-check this in 5 minutes? (Decisions and recommendations up front, detail underneath)
   If the judge finds gaps, dispatch a new worker to address them.

5. **Only come to me when:**
   - You need stakeholder input or business context I haven't provided
   - There's an architectural decision that requires engineering input I'd need to go get
   - The investigation is complete and ready for my review

6. **When you're done**, present: the investigation document, the questions I need to
   go ask humans, and your confidence level on each section (high/medium/low).
```

**What happens after you send this:** Claude decomposes the research, dispatches workers to investigate each track, synthesizes findings, dispatches a worker to produce deliverables, then dispatches a separate judge to review quality. You get back a checked investigation package. You review it, take the stakeholder questions to actual humans, feed answers back in, and Claude revises. Then you're ready for leadership.

### Option B: Guided Mode (Step-by-Step)

Use this when the feature is politically sensitive, when you need to think through it conversationally, or when you're new to the domain and want to learn as you go.

#### Step 1: Discovery & Orientation (Planner Mode)

Set up a Claude Project with your PM methodology skill loaded. First prompt:

```
I've been assigned a new feature project: [Feature Name].

Here's what I know so far:
- Business request: [who asked, what they want, why]
- Value stream: [Your Value Stream]
- Stakeholders: [list]
- Known integration points: [list known systems and services]

I need to take this through our feature intake process.
Starting point: We're at New Request, heading toward ROM.

Help me build an investigation plan. Using our investigation template,
identify what I need to answer before I can produce the ROM:
1. What's the problem statement?
2. What's in scope vs. out of scope?
3. Who do I need to talk to?
4. What existing systems does this touch?
5. What are the obvious risks?
```

#### Step 2: Investigation Decomposition

This is where the agentic framework pays off for PM work. Decompose the investigation into independently researchable pieces:

```
Break the [Feature Name] investigation into parallel research tracks:

Track 1: Technical Landscape
- What existing template systems exist?
- What are the integration points?
- What does the current architecture support?

Track 2: Business Requirements
- Who are the users?
- What are the use cases?
- What does "global" mean in context (all storefronts? all branches?)

Track 3: Effort & Complexity
- Modules affected (front-end, back-end, integrations)
- Cross-team dependencies ([Other Team A]? [Other Team B]?)
- Estimated complexity by component

Track 4: Risk & Dependencies
- What could block this?
- What else is in flight that competes for the same resources?
- Backward compatibility concerns?

For each track, tell me:
- What questions I need answered
- Who I should ask
- What I can research independently vs. what needs a conversation
```

#### Step 3: Produce Artifacts (Worker Mode)

Use Claude as a worker to draft each deliverable. You're the judge.

```
Based on what we've gathered, draft the Investigation Document
using our standard template. Include:

- Problem Statement
- Scope (in/out)
- Effort vs Value positioning
- Conceptual Design (high level)
- Projected Solution
- Resource requirements (flag if specific engineering leads are needed)
- Timeline estimate (remember: ±75% accuracy at investigation, and scope to 12-16 weeks max)
- Risks and dependencies
- Cross-team impacts (does this touch [adjacent system A]? [adjacent system B]?)

Structure it so leadership can sniff-check it in 5 minutes.
Lead with the decision points and recommendations.
```

#### Step 4: Stakeholder-Ready Verification (Judge Mode)

Before presenting to leadership, run your own sniff-check:

```
Before I take this to leadership, let me pressure-test it:

1. Does the scope fit within 12-16 weeks?
2. Are the estimates within ±75% accuracy?
3. Have I identified all cross-team dependencies?
4. Does this align with our current strategic theme (e.g., stability & predictability)?
5. Is the value proposition clear enough for a Portfolio Review?
6. Have I accounted for vendor/contractor resource rotation risk?
7. Is there a quantitative value proposition (KR: 50% of features need one)?

Flag anything that's weak or missing.
```

#### Step 5: Implementation Planning

Once approved, shift the harness to implementation mode:

```
[Feature Name] is approved and moving to Implementation.
Help me build the refinement session agenda:

1. Epic/story breakdown (user story format with acceptance criteria)
2. Technical considerations per story
3. Dependencies between stories (what's the critical path?)
4. QA strategy ([QA team] will need test plans)
5. SDET automation approach ([SDET team])
6. Release strategy (can we do incremental releases?)

Remember: requirements gathering happens during implementation,
not before. Keep stories flexible enough for late-binding requirements.
```

---

## Key Principles for PM Feature Work

- **Your stakeholders are the verification layer.** Structure every artifact so leadership can sniff-check it quickly. The investigation document should have a clear "here's the decision, here's why, here's the risk" structure at the top.
- **Your OKRs are your constraints.** Every recommendation should tie back to the key results you're measured against.
- **Budget awareness is a verification checkpoint.** Before the ROM is complete, confirm budget implications. Don't let that be a surprise at approval.
- **Benefit realization starts at investigation.** If you define the measurable outcome during investigation, you've set yourself up for the 1/3/6-month assessments later.
- **The feature intake board IS your PROGRESS.md.** The Jira statuses (New Request → ROM → Investigation → etc.) serve the same harness function. Use them actively, not just as status labels.

---

## Guided vs. Autonomous: When to Choose What (PM Context)

**Go Autonomous when:**
- The business request is clear and you can articulate the domain context upfront
- You're running a standard investigation through the intake process
- You want to front-load your knowledge dump and get a draft package back to review

**Go Guided when:**
- The feature is politically sensitive or involves competing stakeholder interests
- You're new to the domain area and want to learn as you investigate
- The scope is ambiguous and needs conversational exploration to define
- You want to use the conversation to sharpen your own thinking before stakeholder meetings

**Switch from Autonomous to Guided when:**
- Claude keeps coming back with stakeholder questions (the harness was under-specified on business context)
- The investigation reveals the problem is more complex than expected and needs reframing

**Switch from Guided to Autonomous when:**
- Discovery is done and now you just need the documents produced
- You've established scope and direction and the remaining work is execution
