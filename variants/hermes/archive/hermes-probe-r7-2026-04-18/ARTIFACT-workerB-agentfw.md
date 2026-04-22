# ARTIFACT-workerB-agentfw.md

## AgentFW Architectural Analysis — Worker B Deep Dive

**Date:** 2026-04-17
**Scope:** AgentFW r5 → r6 → r7 evolution, contract mechanics, capability assumptions

---

## 1. What AgentFW Is

AgentFW is **standing instructions for AI agents** encoded as structured Markdown documents. It is neither a framework, library, SDK, nor runtime. It is **the firmware itself** — a behavioral specification that teaches agents to decompose work, dispatch sub-agents, verify independently, manage persistent state, and recover from errors. Installation means copying a file (CLAUDE.md, system prompt, or custom instructions) to your client. The agent reads it every session.

The architectural promise: apply the organizational structures that make human teams effective — decomposition, parallelization, independent verification, iteration — and AI output becomes predictable instead of jagged.

### Layer diagram

```
┌─────────────────────────────────────────────┐
│ Always-Load Core (~175 lines)               │ ← Installed as CLAUDE.md every session
│ • Operating pattern (Decompose-Parallelize  │   Contains: behavior rules, role architecture,
│   -Verify-Iterate)                          │   permission tiers, session protocol
│ • Planner-Worker-Judge role architecture    │
│ • Critical Rules (5)                        │
│ • Permission tiers (3)                      │
│ • Task classification gate                  │
├─────────────────────────────────────────────┤
│ On-Demand References (7 files, ~450 lines)  │ ← Loaded by task condition
│ • state-management.md (PROGRESS/PLAN)       │
│ • verification-tiers.md (Tier 1/2)          │
│ • error-recovery.md                         │
│ • anti-patterns.md (9 named failure modes)  │
│ • prompt-design.md                          │
│ • observability.md (SESSION_LOG events)     │
│ • domain-guidelines.md                      │
├─────────────────────────────────────────────┤
│ Scenario Playbooks (5 files, ~265 lines)    │ ← Loaded by task type
│ • feature-dev.md (autonomous + guided)      │
│ • bug-hunting.md                            │
│ • maker-project.md                          │
│ • pm-investigation.md                       │
│ • cross-scenario-patterns.md                │
├─────────────────────────────────────────────┤
│ Templates & Launch Prompts (8 files)        │ ← Loaded at harness creation
│ • PROGRESS.md, PLAN.md, SESSION_LOG.md      │
│ • DIAGNOSTIC.md, 4 launch prompts           │
├─────────────────────────────────────────────┤
│ Evaluation Suite (2 files)                  │ ← Loaded for regression testing
│ • golden-tasks.md (7 behavioral tests)      │
│ • eval-protocol.md                          │
├─────────────────────────────────────────────┤
│ Variants (4 clients)                        │ ← Pre-built for deployment
│ • claude-code/CLAUDE.md                     │
│ • claude-projects/custom-instructions.md    │
│ • generic/system-prompt.md                  │
│ • hermes/HERMES.md (delegate_task API)      │
└─────────────────────────────────────────────┘
```

Design rationale: Always-load footprint (~175 lines) fits alongside real work. Deeper guidance (state machines, anti-patterns, playbooks) loads on-demand. The core tells *what* to do; references tell *how*; playbooks tell *when* and *in what order* (DESIGN.md §3.1).

---

## 2. The Planner-Worker-Judge Contract

The role-separation hard rule is the non-negotiable core of AgentFW. From `harness-core.md` Critical Rule 2 (harness-core.md:12):

> "DO NOT COLLAPSE ROLES. The main session plans and dispatches. Sub-agents implement. Different sub-agents verify."

**Why it is mandatory:**

A single context that plans, implements, and verifies carries its implementation assumptions into verification. It checks for what it *intended*, not what *actually happened*. This is equivalent to a developer merging their own PR and signing off on their own QA (DESIGN.md §5.2:47).

**Concrete enforcement in Claude Code:**

1. **Main session = Planner + Judge dispatcher** (harness-core.md:50-51)
2. **Workers = Sub-agents for implementation** (harness-core.md:52-54)
3. **Judge = Separate sub-agent for verification** (harness-core.md:53). Receives only: requirements + current system state + verification criteria. Does NOT receive worker's reasoning (references/prompt-design.md:42).
4. **On judge failure**, findings go to planner, which **dispatches a new worker** (DESIGN.md §5.2:54).

**When role-separation is relaxable** (harness-core.md:56-60): one-shot tasks, trivial mechanical verification, quick lookups, human co-driving.

**When mandatory** (harness-core.md:62-66): production systems, bug fixes, multi-file/multi-component changes, autonomous mode.

**Mechanism enforcement:**

- **Classification gate** (harness-core.md:90-100) — `[TASK CLASS]` before any work. Procedural step harder to skip than advisory guidance.
- **PROGRESS.md state machine** (references/state-management.md:9-22) — `planned → dispatched → in-progress → completed → verified → failed`. Cannot reach `verified` without separate judge sign-off.
- **Verification gates** — Tasks with unverified dependencies MUST NOT dispatch. `completed` does NOT unblock downstream; only `verified` does.
- **Worker scope constraints** (core/permissions.md:64-103) — Every dispatch includes explicit boundaries.
- **Delegation Self-Check** (references/state-management.md:90-98) — Before writing implementation code in main session, agent verifies role and states reason if not delegating.

---

## 3. State Externalization — The Harness Files

The harness operates on persistent files on disk, not memory. This is a design feature, not a constraint.

### PROGRESS.md — The State Machine

**Schema:** `| ID | Description | Status | Worker | Attempt | Side-Effects | Checkpoint | Verification Method | Verification Artifact | Verified By |`

**State machine:** `planned → dispatched → in-progress → completed → verified → failed`

- **planned** — Task exists in plan; no worker assigned yet
- **dispatched** — Worker assigned; prevents re-dispatch (dedupe rule)
- **in-progress** — Worker actively executing
- **completed** — Worker finished; artifacts exist; **awaiting judge verification**
- **verified** — Judge (separate context) confirmed correctness; unblocks dependent tasks
- **failed** — New attempt entry linked to previous

**Critical properties:**
- **Verification gate** — Tasks whose dependencies include unverified tasks MUST NOT dispatch
- **Staleness detection** — Tasks at `completed` without judge dispatch flagged as verification gaps
- **Dedupe rules** — Check status before dispatch; if `dispatched`/`in-progress`, do not re-dispatch
- **Side-effect checkpoints** — After each worker completes, record git hash, created/modified resources

### PLAN.md — Task Decomposition

**Schema:** `| ID | Description | Dependencies | Verification Method | Verification Criteria | Permission Scope |`

**Key rule:** Verification Method **is locked at planning time** (templates/PLAN.md:16-18). Changing after implementation requires explicit plan amendment.

**Verification Method** must be concrete: `build`, `test:<command>`, `lint:<command>`, `schema-check`, `human-review`, `expert-subagent`.

**Permission Scope** per task: `read+write: [paths] | run: [commands] | deny: [explicit forbiddens]`.

### SESSION_LOG.md — Structured Event Log

**Purpose** (references/observability.md:3-9) — Chat transcript is a river of text. SESSION_LOG is the audit trail.

**12 event types:** SESSION_START, PLAN_CREATED, WORKER_DISPATCHED, WORKER_COMPLETED, JUDGE_DISPATCHED, JUDGE_VERDICT, ERROR, RESTART, PERMISSION_CHECK, CONTEXT_HEALTH_CHECK, SESSION_END.

**When to log:**
- Autonomous mode: always
- Guided mode (multi-step): strongly recommended
- Multi-session tasks: required

### DIAGNOSTIC.md — Bug Investigation Specific

Used only in bug-hunting playbook. Tracks ranked hypotheses, investigation results, and root cause discovery.

### Context-Health Gate Mechanism

**Trigger:** After every 3 tasks reach `completed` or `verified`, fire gate **before dispatching next worker**.

**Procedure:**
1. Read PROGRESS.md from disk (do not rely on memory)
2. Count completed + verified tasks; if count crosses multiple of 3, proceed
3. Self-assess against Critical Rules
4. If degraded: `[CONTEXT HEALTH: DEGRADED — <which rule>]`; take corrective action
5. If clean: `[CONTEXT HEALTH: OK — <specific evidence>]`

**Key design point** (references/state-management.md:82-87): Cadence held at 3 pending empirical degradation-curve data. Long-context retrieval scores do NOT imply agentic rule-adherence stability. Task-state-triggered (PROGRESS.md), not tool-call-interval-triggered.

**Evidence requirement:** Bare `[CONTEXT HEALTH: OK]` without evidence is **Rubber-Stamp Compliance** anti-pattern (references/anti-patterns.md:27-28).

### State: In-Memory vs. On-Disk

**On-disk (persistent):** PROGRESS.md, PLAN.md, SESSION_LOG.md, DIAGNOSTIC.md, context documents

**In-memory (session context):** behavioral rules, permission model, active session state, accumulated learnings

**Why this split:** Context windows are finite. Agent's memory of rules degrades as context fills. Files don't degrade.

---

## 4. The Critical Rules — Quoted

From `harness-core.md` lines 7-16:

1. **"CLASSIFY BEFORE ACTING."** Output `[TASK CLASS: one-shot | structured | long-horizon]` before any work. No exceptions.
2. **"DO NOT COLLAPSE ROLES."** Main session plans and dispatches. Sub-agents implement. Different sub-agents verify.
3. **"DO NOT SELF-VERIFY."** Context that wrote code cannot verify code. Dispatch a separate judge.
4. **"CHECK PROGRESS.md BEFORE EVERY DISPATCH."** State file is ground truth, not memory.
5. **"WHEN IN DOUBT, DECOMPOSE AND FAN OUT."** When independent sub-problems exist, spawn one subagent per sub-problem in same turn.

**Explanation:**

- **Rule 1** establishes a procedural gate harder to skip than advisory guidance. Omitting is a protocol violation.
- **Rule 2** prevents role collapse — structural enforcement of Planner-Worker-Judge. Context that plans a fix carries planning assumptions into implementation; context that implements carries implementation assumptions into verification.
- **Rule 3** is the judge-independence requirement. Model's intrinsic pre-flight check is fine; what's prohibited is using implementing context as judge of record (r7 clarifier).
- **Rule 4** operationalizes state awareness. File is ground truth; memory is not. Prevents dedupe failures and dispatch-before-verify failures.
- **Rule 5** operationalizes parallelization. Explicit "spawn N workers in parallel" is better than advisory "decompose" — counters model tendency to read decompose as advisory.

---

## 5. Task Classification Gate

### One-Shot (No Harness Needed)
**Criteria:** ONLY when (a) zero files modified, OR (b) exactly one file modified with <20 lines changed AND no cross-file dependencies.

### Structured (Activate Harness)
Activate if ANY:
- Change touches more than one file
- Independently verifiable components exist
- Side effects worth tracking
- Multiple hypotheses to investigate
- Would benefit from a plan
- Could a bug go undetected by implementer alone?
- Failure modes appearing at integration time?

Activating the harness for complex tasks IS the efficient path. One-shotting complex work produces rework.

### Long-Horizon
Spans multiple sessions, accumulated knowledge, multiple approaches. Full harness with persistent state, context documents, verification checkpoints, clean handoffs.

### Anti-Classification Pressure
**One-Shot Hero Mode** (references/anti-patterns.md:3-4): "Trying to solve everything in a single massive response. You'll recognize this when your response is ballooning past a screen and you're holding six sub-problems in your head simultaneously — that's when errors compound silently."

---

## 6. Permission Model — Three Tiers

### Tier 1: `always-allow` (Non-mutating)
Read files, search code, run read-only tests, create/update harness files (PROGRESS/PLAN/SESSION_LOG/DIAGNOSTIC), dispatch read-only investigation sub-agents, run linters/type-checkers.

### Tier 2: `ask-first` (State-changing)
Write/modify source, run mutation scripts, install/update/remove deps, modify configs, git commits/branches/merges, dispatch implementation workers, external API calls with side effects, new files outside harness set, elevated-privilege commands, database schema/data.

### Tier 3: `never-allow` (Hard boundaries)
Delete production data, force-push protected branches, access/commit secrets, bypass verification, modify CI/CD without approval, disable security/auth, push to remote without approval.

### Worker Scope Rule
Every dispatch gets: allowed paths (read+write), allowed operations, forbidden operations, side-effect budget.

### Escalation Protocol
Worker STOPS when out-of-scope, documents need, reports to planner. Planner expands scope, dispatches different worker, revises plan, or asks human.

---

## 7. Verification Tiers

### Tier 1: Machine-Checkable
Code compiles or doesn't. Tests pass or fail. **Always run the check.**

Task CANNOT transition `completed` → `verified` without machine-check output recorded in PROGRESS.md.

**Compiled languages** (C++, Rust, Go, Java, C#, Swift, Unreal C++): Judge MUST execute build. Reasoning-only does NOT constitute verification.

**Interpreted languages** (Python, JS, TS, Ruby): Judge MUST execute test suite or linter. If no tests, run entry point or import module.

**Long-running services:** Worker/judge MUST restart service after code changes. Change isn't verifiable until service runs new code.

### Tier 2: Expert-Checkable
Output evaluated by domain expertise against known criteria. Make criteria explicit before starting. Structure outputs for sniff-checking.

---

## 8. Anti-Patterns — All 9

1. **One-Shot Hero Mode** — Solving everything in one massive response. Errors compound silently in middle third.
2. **Flat Coordination** — Parallel efforts sharing state without hierarchy. Produces contradictory changes.
3. **Complexity Accumulation** — Adding machinery when things aren't working. Often the fix is simplification.
4. **Context Window Stuffing** — Pasting entire files, carrying all prior turns. Performance degrades gradually.
5. **Invisible Assumptions** — Working from assumptions human can't see or challenge.
6. **Patching Over Structural Problems** — Each fix introduces new failure. Sunk-cost instinct is wrong.
7. **Role Collapse** — Main session drops from planner/judge into worker mode.
8. **Self-Review** — Same context writes code and verifies. Misses same edge cases in both passes. Model's intrinsic pre-flight is fine; same-context judge-of-record is prohibited.
9. **Rubber-Stamp Compliance** — Mechanically outputting protocol markers without actual assessment.

---

## 9. Variants System

Four deployment variants, all tracking canonical `core/harness-core.md`:

### claude-code/
Claude Code IDE with native FS/git/Python. Dispatch via Claude Code sub-agent API. ~2000 lines total.
**Drift history:** In r6, was missing all r5 gates. Caught by golden task evaluation. Fixed by syncing to r5 core.

### claude-projects/
Claude Projects with custom instructions field and knowledge files. Core as custom instructions; references uploaded as knowledge. Deferred in r7.

### generic/
Any client accepting system prompts. Core + references as contiguous system prompt. Portable. Deferred in r7.

### hermes/
Hermes orchestration with `delegate_task()` API. Workers dispatched via structured API. **Key difference:** Workers are "subagents dispatched via `delegate_task`," not "sub-agents, not the main session." Not synced in r7 (Worker A's scope).

### Variant Drift Risk
**Design principle** (DESIGN.md §3.2:88-90): Canonical source is `core/harness-core.md`; variants must track it. Drift is regression. Golden task evaluation catches behavioral drift.

---

## 10. Evolution: r5 → r6 → r7

### r5 (2026-04-06) — Structural Enforcement Hardening
**Problem:** Claude Code was skipping harness because decision tree was advisory. UE5 C++ project had three implementation steps "completed" without building — errors accumulated invisibly.

**Key changes:**
1. Mandatory classification gate (`[TASK CLASS]` before work)
2. Verification gates — tasks with unverified dependencies cannot dispatch
3. Staleness detection
4. Compiled language verification — judge MUST build
5. Interpreted language verification — judge MUST run tests/linter
6. Late-discovery error protocol — roll back to last verified checkpoint
7. Autonomous mode: judge dispatched between every task
8. One-shot criteria tightened (<20 lines, no cross-file deps)
9. Tier 1 enforcement — cannot transition completed→verified without machine-check output
10. Anti-patterns auto-loaded for structured/long-horizon

**Impact:** Moved from advisory to structural enforcement.

### r6 (2026-04-10) — Context Degradation Resistance
**Problem:** Long Claude Code sessions showed progressive behavioral degradation — agent stopped delegating, stopped dispatching judges, collapsed to one-shotting. Claude Code variant drifted from r5 core — missing classification gate, anti-patterns auto-load — running with r4-era logic.

**Key changes:**
1. Critical Rules preamble — five numbered rules at top of core, survive attention deprioritization
2. Context Health Gate — state-driven check after every 3 tasks
3. Delegation Self-Check — procedural gate before any implementation code in main session
4. Context degradation as structural error — triggers session restart
5. Rubber-Stamp Compliance anti-pattern named
6. Claude Code variant sync to r5 gates

**Impact:** Shifted from memory-driven to state-driven gates.

### r7 (2026-04-17) — Cross-Model Tuning Pass
**Problem:** Claude Opus 4.7 landed with fewer sub-agents, adaptive thinking off, stronger intrinsic self-verification, coding-benchmark gains tempting loosening of structural gates. Phase 0 multi-model probe: Sonnet 4.6 missed classification marker on GT-5.

**Key changes:**
1. Self-verification vs. self-review clarifier (distinguish intrinsic pre-flight from judge-of-record)
2. Explicit fan-out instruction ("spawn N workers in parallel")
3. Quote-before-act on state files
4. Cadence annotation for 3-task health gate (held pending empirical data)
5. Model-family knobs (non-binding) subsection with inline model sidenotes
6. Reference-file audit (removed vague language)

**Impact:** Core stayed model-agnostic; model-specific knobs isolated to bounded section.

---

## 11. Capability Assumptions

AgentFW assumes the operating model can:

### Context Window & Instruction Adherence
- ~175-line core loaded every session alongside real conversation
- Instruction recall decays with context fill but reliable for ~first 1000 lines
- Critical Rules survive deprioritization if numbered and imperative
- File reads remain reliable as context fills, more so than memory

### Task Classification Discipline
- Output `[TASK CLASS]` block before any work when gated as mandatory
- Follow enumerated activation criteria

### Sub-Agent Dispatch
- Spawn N workers in parallel for independent sub-problems when phrasing is literal
- Dispatch count varies by model (Opus 4.7 defaults to fewer); explicit phrasing helps

### Role Separation Maintenance
- Distinguish Planner (dispatch), Worker (implement), Judge (verify) when named and separated
- Role collapse is #1 failure mode under context pressure

### Verification Discipline
- Execute machine-checkable verifications (compilation, tests, linting)
- Tier 1 enforced by requiring artifact output in state file

### Self-Verification Resistance
- Intrinsic self-verification is fine (pre-flight check)
- Self-review as judge of record is prohibited (r7 clarifier)

### State Machine Recall
- Read and update PROGRESS.md reliably
- Follow state transition rules if explicit
- Refuse invalid transitions if gated as hard rule

### Permission Tier Enforcement
- Classify operations into tiers when definitions are enumerable
- Refuse `never-allow` reliably
- Weakens under context pressure — over-context, starts treating ask-first as auto-allow

### Multi-Session Continuity
- Cold-start from PROGRESS.md if file is complete
- Cannot recall multi-session context from memory alone

### Degradation Curve
- Long sessions (>50 tasks, >20k tokens) show progressive degradation
- Nonlinear; adherence drops steeply around task counts 15-25
- Health gate at 3-task intervals catches before cascade

---

## 12. Extension Seams

### Auxiliary Summarizer Model
**Where:** references/state-management.md, "Multi-Session Continuity" section.
**Mechanism:** At session end with substantial PROGRESS.md, dispatch separate "summarizer" sub-agent to read full files, extract key decisions/constraints/patterns, produce concise context document (one page max).
**Current state:** Manual; operator updates context documents. Could be automated with dedicated summarizer role.

### ACP Delegation
**Where:** references/prompt-design.md "Model-family knobs (non-binding)" section.
**Mechanism:** Before dispatching workers, query ACP service for model capabilities (reasoning effort, token budgets, task-allocation limits).
**Current state:** Fixed; assumes Opus 4.7 / Sonnet 4.6 / GPT-5-tier equivalence.

### Role-Separation Enforcement Points
**File:** core/harness-core.md lines 45-66.
**Five concrete enforcement points:**
1. Classification gate (line 11)
2. Delegation self-check (references/state-management.md:90-98)
3. PROGRESS.md state machine (completed doesn't unblock downstream)
4. Worker scope constraints (core/permissions.md:64-72)
5. Judge shielding (references/prompt-design.md:40-42)

### Verification Tier Extension
**File:** references/verification-tiers.md, references/domain-guidelines.md.
**Extension point:** Add Tier 3 for specialized verification (security audit, compliance, performance benchmark). Document when to invoke, judge shielding, artifact format.

---

## Summary: The Contract

AgentFW is a behavioral specification, not infrastructure. It assumes the model:

1. **Maintains role separation under instruction** if roles named, gates structural, transitions file-enforced
2. **Degrades predictably** as context fills; resistant if detected by task-count gates, not memory-driven
3. **Follows enumerated criteria** better than abstract principles
4. **Manages persistent state** via file reads when memory is unreliable
5. **Complies with hard gates** more consistently than advisory guidance
6. **Breaks predictably** under context pressure (fewer subagents, more self-review, skipped classification)

Fault-tolerance mechanisms:
- **State externalization** — observable state more reliable than memory
- **Structural gates** — mandatory procedural steps harder to skip
- **Role separation** — prevents single context checking its own work
- **Fresh context** — restart with learnings, not accumulated state
- **Health gates** — detect degradation before cascade

If the operating model can dispatch workers, maintain state files, follow procedural gates, and restart on degradation, AgentFW makes agent output predictable and verifiable at long context.
