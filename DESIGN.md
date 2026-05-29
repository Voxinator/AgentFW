# AgentFW — Design Specification

**Version:** r8
**Author:** Brian Taylor
**Last updated:** 2026-05-29

---

## 1. Problem Statement

AI agent capabilities appear "jagged" — the same model that writes a flawless function will hallucinate a dependency or skip an edge case two prompts later. This inconsistency is not a model deficiency. It is a structural problem: when we ask for one-shot answers to multi-step problems, we create conditions where errors compound silently and go undetected until it is too late to recover cheaply.

Human teams solved this long ago. Engineers don't write, review, and merge their own code. Project managers decompose work before assigning it. QA evaluates against requirements, not the developer's stated intentions. These patterns — decomposition, parallel execution, independent verification, iterative refinement — are not bureaucracy. They are error-correction mechanisms.

AgentFW applies these patterns to AI agents. As of v8, it does so in a specific division of labor: **Claude Code 2.1 supplies the mechanisms** (the Workflow tool, Agent subagents, Plan mode, Skills, MEMORY, the Task system, permission modes + hooks + worktrees, context compaction), and **AgentFW supplies the governance**. The firmware decides *whether, when, and how well* to orchestrate; the runtime executes *how* (Rule 6: PREFER NATIVE PRIMITIVES). AgentFW is no longer the orchestration machinery — it is the policy layer over it.

It remains a set of structured Markdown documents that install as standing instructions (CLAUDE.md). There is no runtime, no SDK, no library inside AgentFW itself. The "firmware" is the prompt — and the prompt is the product. v8 is **Claude-Code-only**; cross-model content has been dropped (Microsoft 365 Copilot is a footnote-level candidate future target, not built or validated).

---

## 2. Design Principles

### 2.1 The firmware is the product

AgentFW is not scaffolding around a model. It IS the behavioral/governance layer. The quality of agent output is directly proportional to the quality of these instructions. Every line must earn its place: high signal density, no aspirational padding, no content that exists "for completeness." In v8 this is sharper than ever — the runtime now provides the mechanics, so the firmware's only job is the judgment, and judgment that isn't load-bearing is dead weight.

### 2.1a Prefer native primitives (v8)

The firmware decides *whether/when/how-well*; the runtime executes *how*. Where Claude Code 2.1 provides a primitive — Workflow orchestration, subagent dispatch, Plan mode, Skills, MEMORY, permission modes + hooks — the firmware drives it rather than re-implementing it in prose. Hand-rolling what the runtime does natively, or double-bookkeeping state the platform already tracks (the Workflow journal, the Task system, MEMORY), is a defect. `references/native-primitives.md` is the canonical delegation map: each primitive paired with the firmware concept it executes and the division of labor between them.

### 2.2 Fresh context is a feature, not a bug

Context window limits force restarts. AgentFW treats this as a design feature: a fresh agent with a summary of what was learned beats a stale agent drowning in accumulated errors. The entire architecture — persistent state files, structured handoffs, judge restarts — is built around this principle.

### 2.3 Structural enforcement over advisory compliance

An instruction that says "you should delegate" will be followed when the agent has attention budget for it and ignored when it doesn't. A structural gate that requires outputting `[TASK CLASS]` before any work creates a procedural step that is harder to skip. r5 moved decisively from advisory to structural. r6 continues this trajectory.

### 2.4 State-driven over memory-driven

Gates that fire based on observable state (PROGRESS.md task counts, verification status) resist degradation better than gates that require the agent to recall instructions. As conversations grow, instruction recall weakens, but file reads remain reliable.

### 2.5 Separation of concerns is non-negotiable

The context that plans should not implement. The context that implements should not verify. This is not a guideline — it is a structural requirement. A single context that plans, implements, and verifies will carry its implementation assumptions into verification, checking for what it *intended* rather than what *actually happened*.

### 2.6 Complexity is the enemy

Adding coordination machinery when things aren't working is an anti-pattern. The fix is usually cleaner isolation, clearer roles, less coupling — not more process. The right amount of harness is the minimum that still decomposes and verifies. v8 makes this principle load-bearing: native tooling is biased toward MORE machinery (a feature never tells you to stop using it), and the runtime makes another Workflow, judge-panel, or subagent nearly free. Over-orchestration is the new default failure, and the anti-pattern judgment layer (especially Complexity Accumulation) is the deliberate counterweight.

---

## 3. Architecture Overview

AgentFW v8 is a governance policy expressed as layered Markdown that sits over Claude Code 2.1's runtime. The runtime supplies the mechanism layer (Workflow, subagents, Plan mode, Skills, MEMORY, hooks); the documents below supply the judgment layer.

### 3.1 Layered Document Architecture

AgentFW manages context budget through layered loading:

```
┌──────────────────────────────────────┐
│  Always-Load Core (~175 lines)       │  ← Installed as CLAUDE.md / system prompt
│  Operating pattern, role arch,       │     Loaded every session
│  permission tiers, session protocol  │
├──────────────────────────────────────┤
│  On-Demand References (7 files)      │  ← Loaded by condition
│  State mgmt, permissions, verify,   │     (multi-step tasks, side effects,
│  errors, prompts, anti-patterns,    │      autonomous mode, etc.)
│  domain guidelines                   │
├──────────────────────────────────────┤
│  Scenario Playbooks (5 files)        │  ← Loaded by task type
│  Feature dev, bug hunting, maker,   │     Step-by-step guides for
│  PM investigation, cross-scenario   │     autonomous + guided modes
├──────────────────────────────────────┤
│  Templates (4 files + 4 prompts)     │  ← Loaded at harness creation
│  PROGRESS.md, PLAN.md, SESSION_LOG, │     Structured starting points
│  DIAGNOSTIC.md, launch prompts      │
├──────────────────────────────────────┤
│  Evaluation Suite (2 files)          │  ← Loaded for regression testing
│  Golden tasks, eval protocol         │     Tests AgentFW itself
└──────────────────────────────────────┘
```

**Design rationale:** A 500-line monolithic instruction set would exhaust context budget before the agent does any work. The layered approach keeps the always-load footprint small (~175 lines) while making deeper guidance available on demand. The core tells the agent *what* to do; the references tell it *how*; the playbooks tell it *when* and *in what order*.

### 3.2 The Native-Primitives Layer (v8)

v8's defining architectural element is the delegation map between the firmware's concepts and Claude Code 2.1's runtime primitives. It lives in `references/native-primitives.md` and answers, for each firmware concept, "which primitive executes this, and what is the division of labor?"

| Claude Code 2.1 primitive | Firmware concept it executes | Division of labor |
|---|---|---|
| Workflow tool (`agent()`, `parallel()`, `pipeline()`, judge-panel, resume/journal) | Planner-Worker-Judge architecture + the Decompose→Parallelize→Verify→Iterate runtime | firmware decides whether/when to orchestrate; runtime executes the orchestration |
| Agent subagents (typed; final message returns to caller) | Worker/judge dispatch + structural OUTPUT-isolation | firmware decides who to dispatch and curates inputs; runtime isolates outputs |
| Plan mode + Plan agent | The plan-first gate | firmware decides when a plan is required; runtime drafts/holds it |
| Skills (code-review, verify, security-review, deep-research) | Verification execution | firmware sets the recorded-artifact standard; runtime runs the check |
| MEMORY | Durable cross-session state | firmware decides what's worth persisting; runtime stores/retrieves it |
| Task system + Cron/schedule/loop | Long-horizon autonomy | firmware decides cadence + stop conditions; runtime executes the schedule |
| Permission modes + allow/deny/ask + hooks + worktrees | Enforcement of the permission taxonomy | firmware supplies the taxonomy + novel-op judgment; runtime enforces deterministically |
| Context compaction | Window management | firmware triggers the health gate against drift; runtime compacts |

The throughline: the firmware governs *whether/when/how-well*; the runtime executes *how*. What survives as pure firmware is the judgment with no native expression — the Classification Gate, judge input-curation, the two Enforcement Gates, the Plan-Critique Gate, and the anti-pattern judgment layer.

The canonical source is `core/harness-core.md`; it installs as the CLAUDE.md core. v8 has no client variants — it targets Claude Code exclusively.

### 3.3 Bootstrap Installer

`bootstrap.md` is a self-install prompt. Run `cat bootstrap.md | claude` to locate AgentFW files and install `core/harness-core.md` as the CLAUDE.md core. It handles fresh installs, upgrades from r6/r7 (which overwrite the installed CLAUDE.md), and post-install verification.

---

## 4. Core Operating Pattern: Decompose-Parallelize-Verify-Iterate

The fundamental operating loop for all non-trivial work:

```
       ┌──────────┐
       │DECOMPOSE │  Break into verifiable sub-problems
       └────┬─────┘
            │
       ┌────▼──────────┐
       │ PARALLELIZE    │  Work independent pieces in isolated contexts
       └────┬───────────┘
            │
       ┌────▼─────┐
       │  VERIFY   │  Check each piece against explicit criteria
       └────┬──────┘
            │
      ┌─────▼──────┐     ┌──────────┐
      │  Pass?     ├─NO──► ITERATE   │  Restart sub-problem with fresh
      └─────┬──────┘     │ (fresh)   │  context + learnings
            │YES         └───────────┘
            │
       ┌────▼─────┐
       │  NEXT     │
       └──────────┘
```

**Decompose:** Identify natural seams where the problem separates into independently solvable units. Each sub-problem must have clear verification criteria *before* work begins.

**Parallelize:** Work independent sub-problems in parallel with clean isolation. Each gets its own context. Failure in one branch must not contaminate another.

**Verify:** Machine-checkable when possible (compilation, tests, linting), expert-checkable otherwise. The verification must actually run — reasoning about whether code "would compile" is not verification.

**Iterate:** When verification fails, restart that sub-problem with fresh context informed by what was learned. Bring forward the *lesson*, not the accumulated state. Don't patch forward.

---

## 5. Role Architecture: Planner-Worker-Judge

### 5.1 Role Definitions

**Planner** — The orchestrator. Explores the problem space, creates a task breakdown (PLAN.md), defines verification criteria, dispatches workers and judges, evaluates results, decides next steps. The planner does not write implementation code. In Claude Code sessions, the main session is the planner.

**Worker** — The implementer. Picks up a specific task from the plan and executes it in clean isolation. Receives a scoped prompt with exactly the context it needs (see Section 10: Prompt Design). Workers are sub-agents, not the main session. Each worker gets an explicit scope declaration: allowed paths, allowed operations, forbidden operations, side-effect budget.

**Judge** — The verifier. Evaluates completed work against verification criteria from a *fresh context*. Receives only: original requirements, current system state, and verification criteria. Does NOT receive the worker's reasoning, implementation plan, or thought process. A judge that receives the worker's plan will check whether the implementation matches the plan. A judge that receives only the requirements will check whether the system meets the requirements. The second evaluation is the one that matters.

### 5.2 Role Separation Enforcement

This is a HARD RULE, not a guideline.

The main session must never collapse planner, worker, and judge into a single context. A single context that plans, implements, and verifies carries its implementation assumptions into verification — it checks for what it *intended*, not what *actually happened*. This is equivalent to a developer merging their own PR and signing off on their own QA.

**Concrete enforcement in Claude Code:**
1. Main session = Planner + Judge dispatcher (does NOT write implementation code)
2. Workers = Sub-agents for implementation (each gets specific task spec)
3. Judge = Separate sub-agent for verification (different sub-agent than the worker)
4. On judge failure, findings go to the planner, which dispatches a *new* worker (original worker context is not reused)

**Relaxation conditions:**
- One-shot tasks that don't warrant overhead
- Trivial changes with purely mechanical verification
- Quick lookups and orientation reads
- The human is actively co-driving as judge

**Mandatory enforcement:**
- Changes to production systems or live infrastructure
- Bug fixes (implementation and verification MUST be separate)
- Multi-file or multi-component changes
- Autonomous mode

### 5.3 Guided Mode Role Separation

Two valid configurations:
1. **Human-as-Judge (default):** Worker implements, human reviews and decides accept/revise/restart.
2. **Separate Sub-Agent Judge:** Worker implements, human requests a separate sub-agent to verify cold, human reviews the judge's findings.

**Invalid:** The same session that implemented a change evaluating its own work, even if called "switching to judge mode." Self-review is blind to its own assumptions regardless of who is watching.

---

## 6. Task Classification and Delegation

### 6.1 Classification Gate (r5)

Before any work begins, the agent must output a classification block:

```
[TASK CLASS: one-shot | structured | long-horizon]
Justification: <one-line reason>
```

Omitting this classification is a protocol violation. The classification must appear before any implementation work, file modifications, or sub-agent dispatch.

### 6.2 Classification Criteria

**One-shot** — Applies ONLY when: (a) zero files are modified, OR (b) exactly one file is modified with fewer than 20 lines changed AND the change has no cross-file dependencies. No harness needed.

**Structured** — Activate the harness if ANY of these are true:
- The change touches more than one file
- There are independently verifiable components
- The task has side effects worth tracking
- The task requires investigating multiple hypotheses
- You'd benefit from a plan before starting
- Could a bug go undetected by the implementer alone?
- Does this change have failure modes that only appear at integration time?

**Long-horizon** — Spans multiple sessions. Full harness with persistent state, context documents, verification checkpoints, and clean session handoffs.

### 6.3 Anti-Classification Pressure

The pull to one-shot complex work ("I'll just do it all at once") is the most common failure mode. AgentFW treats this pull as a signal to decompose, not to push through. Activating the harness for complex tasks IS the efficient path — one-shotting produces rework.

If the harness is skipped for a task meeting activation criteria, the agent must state which relaxation exception applies and why. Silence is not a valid relaxation.

---

## 7. State Management

### 7.1 PROGRESS.md as State Machine

PROGRESS.md is not a checklist. It is a state machine that tracks:

```
planned → dispatched → in-progress → completed → verified → failed
```

Each task entry includes:

| Field | Purpose |
|-------|---------|
| Status | Current state in the machine |
| Worker ID | Which sub-agent owns this task (prevents duplicate dispatch) |
| Side-effects | Files changed, commands run, external calls made |
| Checkpoint | Git hash or state snapshot (the rollback point) |
| Attempt number | For retries — links to previous attempts |
| Verification Method | How this will be verified (locked at planning time) |
| Verification Artifact | Build log, test output, etc. (recorded at verification) |
| Verified By | Which judge, and how (planner = role-collapse violation) |

### 7.2 Structural Gates on State Transitions

**Verification gate:** A task whose dependencies include any task not yet at `verified` MUST NOT be dispatched. `completed` does not mean correct — it means a worker claims to be done. Only `verified` means a separate judge confirmed it. This is a hard gate.

**Staleness detection:** Any task at `completed` for more than one planner cycle without judge dispatch is a verification gap. The planner must acknowledge the gap and either dispatch a judge or document deferred verification with accepted risk.

**Dedupe rules:** Before dispatching, check PROGRESS.md. If `dispatched` or `in-progress`, don't re-dispatch. If `completed`, it's waiting for verification. If `failed`, create a new attempt entry — the new worker gets judge findings but NOT the previous worker's reasoning.

### 7.3 Multi-Session Continuity

PROGRESS.md must contain enough for a cold-start agent to answer six questions:
1. Where are we? (current status)
2. What's done? (verified tasks with checkpoints)
3. What's in flight? (dispatched/in-progress tasks — worker context is gone)
4. What failed and why? (failed tasks with attempt history and judge findings)
5. What do we know? (Decisions Made and Things Learned sections)
6. Where's the last known-good state? (most recent verified checkpoint)

If a new agent can't answer all six from PROGRESS.md alone, the file is incomplete.

### 7.4 Side-Effect Checkpoints

After each worker completes, record what changed:
- **Code:** Git commit hash
- **External systems:** Resources created, modified, or called
- **Documents:** File paths and timestamps

Checkpoints make "restart cleanly" possible rather than aspirational. Without them, a failed step means manually reconstructing what prior steps did.

---

## 8. Permission Model

### 8.1 Trust Tiers

Every operation falls into one of three tiers. There is no fourth tier.

| Tier | Rule | Scope |
|------|------|-------|
| `always-allow` | Non-mutating, do without asking | Read files, search code, run linters, create harness files, dispatch read-only sub-agents |
| `ask-first` | State-changing, get approval | Write/modify source, install deps, git commits, dispatch implementation workers, mutation scripts |
| `never-allow` | Hard boundaries, no exceptions | Delete production data, force-push protected branches, access/commit secrets, bypass verification, push to remote |

If unsure which tier, it's `ask-first`.

### 8.2 Worker Scope Constraints

Every dispatched worker gets an explicit scope declaration:
1. **Allowed file paths/directories** — Where the worker can read and write
2. **Allowed operations** — What the worker can do (and specifically which commands)
3. **Forbidden operations** — Explicit deny list (don't rely on omission)
4. **Side-effect budget** — What changes the worker is allowed to make

A worker without defined scope is a worker that might do anything.

### 8.3 Escalation Protocol

When a worker encounters an out-of-scope situation:
1. STOP — Do not proceed with the out-of-scope operation
2. Document what is needed and why
3. Report back to the planner

Workers do not proceed and ask forgiveness. The escalation protocol exists because the planner has context the worker doesn't — maybe another worker is modifying that file, maybe there's a reason it shouldn't change, maybe the dependency reveals a design problem.

---

## 9. Verification System

### 9.1 Tier 1: Machine-Checkable

Code compiles or it doesn't. Tests pass or fail. Schema validates or it doesn't.

**Enforcement:** A task CANNOT transition `completed`→`verified` without machine-check output recorded in PROGRESS.md. A judge that reasons about compilation without compiling has NOT performed Tier 1 verification. The verification artifact must be attached to the task entry.

**Domain-specific requirements:**
- **Compiled languages** (C++, Rust, Go, Java, C#, Swift): Judge MUST execute a build first. Build output must be in the verification artifact.
- **Interpreted languages** (Python, JS, TS, Ruby): Judge MUST run tests/linter or at minimum import the module.
- **Long-running services** (web apps, gateways, daemons): Worker/judge MUST restart the service after code changes. No manual restart steps.

### 9.2 Tier 2: Expert-Checkable

Output evaluated by domain expertise against known criteria. Make the criteria explicit before starting. Structure outputs for sniff-checking: lead with decisions and rationale, flag uncertainty, provide evidence inline, make assumptions visible.

### 9.3 Sniff-Check Enablement

The human's most valuable skill in this framework is rapid evaluation without redoing the work. All agent outputs must be structured to enable this: summary → detail → evidence, with clear structure for jumping to areas that matter most.

---

## 10. Prompt Design and Context Budget

### 10.1 The Rule

A worker receiving 500 lines of relevant context will outperform one receiving 2,000 lines of mixed context. The planner's job is curation, not forwarding.

### 10.2 Context Scoping

**Include:** Specific task description from PLAN.md, relevant source files, verification criteria, permission scope.

**Exclude:** Full framework, other tasks' details, SESSION_LOG, unrelated playbooks, previous workers' reasoning (especially for judges).

### 10.3 Judge Shielding

A judge receives only the requirements and current system state — NOT the worker's implementation plan or reasoning. A judge that receives the worker's plan checks whether the implementation matches the plan. A judge that receives only requirements checks whether the system meets the requirements. These are different evaluations. The second is the one that matters.

---

## 11. Error Recovery

### 11.1 Error Classification

**Local errors:** The approach is sound; something small went wrong. Fix and continue.

**Structural errors:** The approach is wrong. Restart with fresh context. Bring forward only what was learned, not the accumulated state.

### 11.2 Late-Discovery Errors

When errors are discovered after multiple tasks have proceeded past the failure point (e.g., a build after three implementation steps reveals errors from step 1):

1. Treat as structural regardless of individual error severity
2. Roll back to the last verified checkpoint in PROGRESS.md
3. Re-plan from that checkpoint with error findings as input
4. Document the verification gap — which tasks lacked verification and why

This scenario is a symptom of missing verification gates.

### 11.3 Recovery Principle

Don't patch forward blindly. A clean restart informed by failure is almost always faster than a fourth patch on a broken foundation. The sunk-cost instinct ("I'm almost there, one more patch") is wrong.

---

## 12. Observability

### 12.1 SESSION_LOG.md

Structured event logging in Markdown table format. Human-readable, scannable, diffable. Not JSON, not YAML — the log needs to be readable by a human scanning it at the end of a session.

### 12.2 Event Types (12)

| Event | When | Key Fields |
|-------|------|-----------|
| SESSION_START | Session begins | Version, task summary, mode, client |
| PLAN_CREATED | Plan produced | Task count, complexity |
| WORKER_DISPATCHED | Sub-agent spun up | Worker ID, task ID, scope, permissions |
| WORKER_COMPLETED | Worker finishes | Outcome, artifacts, side-effects |
| JUDGE_DISPATCHED | Verification agent spun up | Judge ID, task ID, what received, what shielded |
| JUDGE_VERDICT | Judge delivers evaluation | Verdict (accept/reject), findings |
| ERROR | Something goes wrong | Error type (local/structural), blast radius, action taken |
| RESTART | Task restarted with fresh context | Reason, learnings carried forward |
| PERMISSION_CHECK | Boundary encountered | Operation, tier, outcome |
| CONTEXT_HEALTH_CHECK | Health gate fires | Task count, result (OK/DEGRADED), evidence or corrective action |
| SESSION_END | Session closes | Tasks completed, remaining, total sub-agents, notable events |

### 12.3 When to Log

- **Autonomous mode:** Always, every event. Non-negotiable.
- **Guided mode (multi-step):** Strongly recommended.
- **Guided mode (simple):** Optional.
- **Multi-session tasks:** Required regardless of mode.

### 12.4 Review Protocol

At session end, scan the log for: permission violations, self-review incidents, workers exceeding scope, error clustering, restart frequency (>5 suggests plan problems), judge rejection rate (>30-40% suggests scope/criteria problems).

---

## 13. Anti-Patterns

Nine named failure modes:

| Anti-Pattern | Signal | Fix |
|-------------|--------|-----|
| **One-Shot Hero Mode** | Response ballooning past a screen, holding multiple sub-problems | Decompose |
| **Flat Coordination** | Parallel agents sharing context without hierarchy | Use planner-worker-judge |
| **Complexity Accumulation** | Adding orchestration layers to fix orchestration failures | Simplify: cleaner isolation, clearer roles |
| **Context Window Stuffing** | Pasting entire files "for reference," carrying all prior turns | Summarize, restart, continue from progress file |
| **Invisible Assumptions** | Building on unstated choices | State assumptions at top of every plan and output |
| **Patching Over Structural Problems** | Each fix introduces a new failure | Clean restart with lesson learned |
| **Role Collapse** | Main session drops into worker mode ("I already have the context") | Enforce: if you planned it, you don't implement it |
| **Self-Review** | Same context writes and verifies | Dispatch separate judge with fresh context |
| **Rubber-Stamp Compliance** | Protocol markers emitted without genuine assessment | Require evidence in markers; bare `[CONTEXT HEALTH: OK]` is a violation |

---

## 14. Session Protocol

### 14.1 Start

0. Classify the task — output `[TASK CLASS]` block
1. Check for existing PROGRESS.md and context documents
2. Orient: current state, last completed work, what's next
3. If starting fresh, create the harness
4. Determine role — main session is planner + judge dispatcher for non-trivial tasks

### 14.2 During

1. Work against the plan
2. Dispatch sub-agents for implementation — do not drop into worker mode
3. Dispatch separate sub-agents for verification — verifier ≠ implementer
4. Evaluate results from workers and judges; decide next steps
5. Update progress after each sub-task
6. In autonomous mode, maintain SESSION_LOG.md
7. Context health gate — after every 3 tasks reach completed/verified, re-read PROGRESS.md and self-assess against Critical Rules. Output `[CONTEXT HEALTH: OK/DEGRADED]`
8. If context is degraded — summarize, update PROGRESS.md, and restart with fresh context rather than accumulate

### 14.3 End

1. Update PROGRESS.md with current status
2. Document decisions made and insights gained
3. State what's next for the following session
4. Leave the harness so a fresh agent could pick it up cold

---

## 15. Reference Loading Protocol

The core is always loaded. Everything else loads by condition:

| Condition | Reference |
|-----------|-----------|
| Multi-step tasks | `references/state-management.md` |
| Tasks with side effects | `core/permissions.md` |
| Autonomous mode | `references/observability.md` |
| Errors mid-task | `references/error-recovery.md` |
| Dispatching workers | `references/prompt-design.md` |
| Domain-specific work | `references/domain-guidelines.md` |
| All structured/long-horizon tasks | `references/anti-patterns.md` |
| Matching scenario | `playbooks/[scenario].md` |

**Design rationale:** Front-loading all references wastes context budget. The agent reads the full core every session (behavioral rules, role architecture, session protocol) and loads deeper references only when the task demands them. This keeps the per-session footprint small while ensuring comprehensive guidance is available.

---

## 16. Playbook System

### 16.1 Dual-Mode Design

Every playbook supports both autonomous and guided modes with the same underlying structure:

- **Autonomous:** The human front-loads domain knowledge into a launch prompt, the agent runs the full planner-worker-judge loop independently, the human reviews output at the end.
- **Guided:** The human participates as planner and/or judge, the agent dispatches workers for implementation, verification is human-driven or delegated to sub-agent judges.

### 16.2 Playbook Inventory

| Playbook | Use Case | Key State File |
|----------|----------|---------------|
| `feature-dev.md` | New feature development | PROGRESS.md + PLAN.md |
| `bug-hunting.md` | Troubleshooting and diagnosis | DIAGNOSTIC.md |
| `maker-project.md` | Personal build projects with domain knowledge | PROGRESS.md + domain data |
| `pm-investigation.md` | Product/market investigation | PROGRESS.md + deliverable artifacts |
| `cross-scenario-patterns.md` | Mode selection, role separation rules | — |

### 16.3 Launch Prompt Templates

Four copy-paste templates in `templates/launch-prompts/` provide structured starting points for autonomous sessions. Each template includes:
- Complete domain knowledge section (what the agent can't discover on its own)
- Operating instructions (plan → dispatch → verify → maintain state)
- Judge shielding requirements (what judges do NOT receive)
- Verification criteria and data

---

## 17. Evaluation System

### 17.1 Golden Tasks

Seven regression tests that test AgentFW's behavioral correctness:

| Task | Tests | Key Signal |
|------|-------|-----------|
| GT-1: Trivial Request | No false activation | Agent answers directly, no harness |
| GT-2: Multi-Step Feature | Full harness activation, role separation | Plan created, workers dispatched, judges separate |
| GT-3: Bug Diagnostic | Diagnostic discipline, role separation under pressure | Hypotheses before fix, separate implementation and verification |
| GT-4: Error Recovery | Clean restart with fresh context | Structural error classified, new worker dispatched, learnings carried |
| GT-5: Permission Boundary | Ask-first enforcement for destructive operations | Deletion flagged, approval sought |
| GT-6: Late-Session Delegation | Delegation discipline after context accumulation | Phase 2 delegation quality matches Phase 1 |
| GT-7: Context Health Gate | Health gate fires and resists rubber-stamping | Gate fires after 3 tasks, evidence required, PROGRESS.md read |

### 17.2 Evaluation Protocol

- **Fresh session per task** — Prior history biases behavior. Each task must run in clean context.
- **Exact prompts** — Enter the golden task prompt as written. No priming.
- **Partial passes allowed** — Record what was missed; consistent partials on the same task indicate framework weakness.
- **Fix the framework, not the golden task** — If a task fails after a change, the change is suspect.
- **Claude Code only** — v8 targets a single runtime; golden tasks are scored on Claude Code 2.1. GT-8 verifies the Plan-Critique Gate (it fires on a ≥4-task plan, skips a trivial one, escalates on a capped-with-open-blocker run).

### 17.3 Result Tracking

Results recorded in a Markdown table with mandatory notes. Track over time for:
- Consistent partials (framework weakness in that area)
- Pass/fail flipping (ambiguous instructions)
- All passing after major change (verify the change actually took effect)
- New failures after model updates (model behavior interacts with instructions)

---

## 18. Design Decisions and Trade-offs

### 18.1 Why Markdown, not code

AgentFW is instructions, not infrastructure. Markdown installs by copying a file. It works across any AI client that accepts system prompts or custom instructions. There is no runtime dependency, no version compatibility matrix, no build step. The trade-off: no enforcement beyond what the model chooses to follow. The mitigation: structural gates that make compliance the path of least resistance.

### 18.2 Why role separation is a hard rule

The strongest objection to role separation is efficiency: "I already have the context, why not just implement it?" The answer is that the context that planned the fix is the worst context to verify the fix. It will check for what it intended, not what happened. In evaluation, this failure mode (self-review) consistently produces plausible-looking output with subtle bugs. The efficiency loss from dispatching sub-agents is less than the rework cost of undetected errors.

### 18.3 Why ~175 lines for the core

The core must be small enough to fit alongside a real conversation without exhausting the context window, but large enough to contain all behavioral rules that must apply every session. The r4 restructure condensed the core from ~330 lines (r3) to ~150 lines by moving extended content to on-demand references. r5 added structural gates, bringing it to ~175 lines. The target is under 200 lines. Beyond that, low-signal content should move to references.

### 18.4 Why the classification gate is mandatory

The r4 task delegation decision tree was advisory: "if ANY of these are true, activate the harness." The agent could read this and decide not to. Making it mandatory (output `[TASK CLASS]` before any work) forces an explicit decision. The agent must commit to a classification before proceeding. This doesn't prevent misclassification, but it prevents the most common failure: silently skipping the decision entirely.

### 18.5 Why verification gates block downstream dispatch

In r4, `completed` status unblocked downstream tasks. This led to a failure in a UE5 C++ project where three implementation steps "completed" without building — errors accumulated invisibly until a late-stage build revealed cascading breakage. r5 introduced the verification gate: `completed` does NOT unblock downstream; only `verified` does. The overhead (dispatching judges between tasks) is less than the cost of cascading errors.

### 18.6 Why judge findings go to the planner, not the worker

When a judge rejects work, the findings go to the planner, which dispatches a *new* worker. The original worker context is not reused. This is because the original worker's context includes its implementation reasoning — the same reasoning that produced the rejected work. A new worker with fresh context and the judge's findings has a better chance of approaching the problem differently. Accumulated context carries accumulated assumptions.

### 18.7 Why the state machine has six states, not two

A simpler `todo/done` model is tempting but cannot distinguish between "a worker claims to be done" (`completed`) and "a judge confirmed it's correct" (`verified`). It cannot prevent double-dispatch (`dispatched` vs. `planned`). It cannot track retry history (`failed` with attempt numbers). Every state in the machine exists because collapsing it caused an observed failure mode.

### 18.8 Why anti-patterns are named

Named anti-patterns ("One-Shot Hero Mode," "Role Collapse") create shared vocabulary. An agent that has a name for the failure mode can recognize it in its own behavior. "You are about to commit Role Collapse" is more actionable than "you should delegate this." The names are chosen to be memorable and slightly uncomfortable — you don't want to be caught doing "One-Shot Hero Mode."

---

## 19. Known Limitations

### 19.1 Prompt-based enforcement ceiling

AgentFW has no runtime enforcement. All "gates" are instructions the model chooses to follow. A sufficiently pressured or degraded model can skip any gate. The mitigation is structural design — making compliance the path of least resistance — but this is a fundamentally softer guarantee than code-enforced constraints.

### 19.2 Context degradation

As conversations grow long, early instructions lose attention weight. The agent progressively forgets to delegate, verify, and classify. This is the primary motivation for r6. Current mitigations (structural gates, fresh context philosophy) help but don't fully solve the problem for sustained single-session work.

### 19.3 Evaluation non-determinism

Golden tasks can produce different results across runs because model behavior is non-deterministic. A task that passes on one run may partially fail on another. The evaluation protocol accounts for this (partial passes, trend tracking) but cannot eliminate it.

### 19.4 Runtime coupling

v8 couples the firmware to Claude Code 2.1's native primitives. If the runtime renames a primitive, changes the Workflow API shape, or alters subagent output-routing, the delegation map in `references/native-primitives.md` and the prose in the core can drift out of sync with the platform. The recipe sketches in `references/native-primitives.md` are explicitly marked ILLUSTRATIVE for this reason — they must be adapted to the live API, not pasted verbatim. The mitigation is eval-driven: if the coupling drifts, the golden tasks (especially GT-8) will catch the behavioral regression.

### 19.5 Overhead for simple tasks

The harness adds overhead that simple tasks don't need. The classification gate exists to route simple tasks away from the harness, but over-activation (GT-1 failure) remains a risk. The tension between "catch complex tasks early" and "don't drown simple tasks in process" is inherent and managed through the classification criteria, not eliminated.

---

## 20. Version History

| Version | Date | Focus |
|---------|------|-------|
| r1 | 2025-03-01 | Initial single-document version |
| r2 | 2025-05-15 | Scenario playbooks (feature, bug, maker) |
| r3 | 2025-09-01 | Refined role separation, PM investigation playbook |
| r4 | 2026-04-04 | Modular restructure, permission model, evaluation system, observability, bootstrap |
| r5 | 2026-04-06 | Structural enforcement hardening — classification gate, verification gates, Tier 1 enforcement |
| r6 | 2026-04-10 | Context degradation resistance — Critical Rules preamble, state-driven health gate, delegation self-check |
| r7 | 2026-04-17 | Cross-model tuning pass — model-agnostic edits for Opus 4.7 without non-target regression, bounded model-family knobs subsection, reduced-scope Phase 0 multi-model probe |
| r7.1–r7.11 | 2026-04-18 → 2026-04-30 | Hermes-variant probe + campaign arc (extracted to `agentfw-hermes`, removed from this repo) |
| r8 | 2026-05-29 | v8 governance refactor — firmware reframed as a governance layer over Claude Code 2.1 native primitives (Rule 6), Plan-Critique Gate + Acceptance-Contract spine, `references/native-primitives.md`, GT-8; cross-model content dropped (Claude-Code-only); Hermes variant extracted |
