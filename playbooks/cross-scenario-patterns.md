# Cross-Scenario Patterns

## What's the Same Everywhere

| Principle | Feature Dev | Bug Hunting | Maker Project | PM Investigation |
|-----------|-------------|-------------|---------------|------------------|
| **Decompose first** | Task breakdown | Hypothesis list | Build pieces | Research tracks |
| **State file** | PROGRESS.md | DIAGNOSTIC.md | Project cost data | PROGRESS.md / Jira board |
| **Verification** | Tests pass | Hypothesis confirmed | Math matches reality | Stakeholder sniff-check |
| **Fresh restart** | New sub-task context | New hypothesis | Recalculate from inputs | Re-scope from findings |
| **Your role (Autonomous)** | Harness builder → Domain oracle → Final sniff-check | Scene report → Domain oracle → Approve fix | Domain data provider → Verify against real costs | Business context → Domain oracle → Review before leadership |
| **Your role (Guided)** | Planner + Judge | Planner + Judge | Domain expert + Judge | Planner + Judge |

---

## Guided vs. Autonomous: When to Choose What

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

---

## When to Use Which Harness Weight

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

---

## The Meta-Skill Across All Scenarios

In every case, the most valuable thing you do is **not the execution** — it's:

1. **Building the harness well** — Front-loading the domain knowledge, constraints, and definition of done so the agent can run without you. The quality of the autonomous prompt IS the quality of the output.
2. **Knowing what "correct" looks like** — The final sniff-check. You look at the output and know in your gut whether it's right. That evaluation skill is worth more than the ability to produce the output yourself.
3. **Bringing knowledge the agent can't get on its own** — Tribal knowledge, stakeholder dynamics, machine quirks, business context. You're the domain oracle. Load it into the harness upfront, or answer when asked.
4. **Deciding when to restart vs. continue** — Whether you're in autonomous or guided mode, recognizing "this approach is off, start over" is a judgment call that humans still make better than agents.

---

## Guided Mode: Role Separation Rules

In guided mode, there are exactly two valid configurations:

### 1. Human-as-Judge (Default)

The worker (Claude) implements a task and presents results with verification evidence. The human reviews, evaluates against the criteria, and decides: accept, revise, or restart. The human IS the judge. Claude does not self-assess.

This is the natural guided mode flow: Claude does the work, you check the work. Same as pairing with a junior engineer — they write the code, you review the PR. You don't ask the junior to also review their own PR and tell you if it's good.

### 2. Separate Sub-Agent Judge

The human wants automated verification but still wants to be in the loop. After the worker completes, the human asks Claude to dispatch a SEPARATE sub-agent to verify. The judge sub-agent receives only the requirements and current state — not the conversation history. The human reviews the judge's findings.

This is useful when verification is more mechanical than judgmental — checking that tests pass, that the math adds up, that all edge cases are covered. The human still makes the accept/revise/restart call, but the verification data comes from a cold evaluator rather than the human doing all the checking manually.

### What is NOT Valid in Guided Mode

The same session that implemented a change then evaluating its own work. Even if you call it "switching to judge mode," it's still self-review — the context carries its implementation assumptions into verification. It will check for what it *intended* to do, not what *actually happened*. It will miss the same edge cases in both passes.

If you wrote it, you don't verify it. This rule doesn't get suspended because a human is watching. The human's presence changes who makes the accept/reject *decision* — it doesn't change the fact that self-review is blind to its own assumptions.
