# Scenario: PM Feature Investigation (Claude Project / Claude Code)

> Applying the Decompose → Parallelize → Verify → Iterate framework to Product Management feature work.

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

---

## Option A: Autonomous Mode (Recommended for Investigation Phase)

One launch prompt. Claude runs the full investigation, produces the deliverables, and comes back with a draft investigation document ready for your sniff-check before you take it to leadership.

See `templates/launch-prompts/autonomous-pm.md` for the standalone launch prompt template.

**What happens after you send this:** Claude decomposes the research, dispatches workers to investigate each track, synthesizes findings, dispatches a worker to produce deliverables, then dispatches a separate judge to review quality. You get back a checked investigation package. You review it, take the stakeholder questions to actual humans, feed answers back in, and Claude revises. Then you're ready for leadership.

---

## Option B: Guided Mode (Step-by-Step)

Use this when the feature is politically sensitive, when you need to think through it conversationally, or when you're new to the domain and want to learn as you go.

### Step 1: Discovery & Orientation (Planner Mode)

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

### Step 2: Investigation Decomposition

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

### Step 3: Produce Artifacts (Worker Mode)

Use Claude as a worker to draft each deliverable. You review the output — you are the judge.

```
Based on what we've gathered, draft the Investigation Document
using our standard template. Include:

- Problem Statement
- Scope (in/out)
- Effort vs Value positioning
- Conceptual Design (high level)
- Projected Solution
- Resource requirements (flag if specific engineering leads are needed)
- Timeline estimate (remember: +/-75% accuracy at investigation, and scope to 12-16 weeks max)
- Risks and dependencies
- Cross-team impacts (does this touch [adjacent system A]? [adjacent system B]?)

Structure it so leadership can sniff-check it in 5 minutes.
Lead with the decision points and recommendations.
```

After Claude produces the draft, **you review it against the quality criteria.** Before presenting to leadership, pressure-test:

1. Does the scope fit within 12-16 weeks?
2. Are the estimates within +/-75% accuracy?
3. Have I identified all cross-team dependencies?
4. Does this align with our current strategic theme (e.g., stability & predictability)?
5. Is the value proposition clear enough for a Portfolio Review?
6. Have I accounted for vendor/contractor resource rotation risk?
7. Is there a quantitative value proposition (KR: 50% of features need one)?

Flag anything that's weak or missing and have Claude revise.

If you want automated quality review instead of doing it yourself, dispatch a **separate sub-agent** with the deliverables and the checklist above. Don't ask the same session that drafted the document to also judge whether its own document is ready for leadership.

### Step 4: Implementation Planning

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
