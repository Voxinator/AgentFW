# AgentFW

## What This Is

AI capabilities look jagged when you ask for one-shot answers. The same model that writes a flawless function will hallucinate a dependency or skip a critical edge case two prompts later. The inconsistency isn't in the model — it's in the lack of structure around it. Apply the same organizational patterns that make human teams effective (task decomposition, parallel execution, independent verification, iterative refinement) and the surface smooths out.

AgentFW encodes that lesson as standing instructions for AI agents. It is not a framework, library, or SDK. It's a set of structured Markdown documents that teach agents how to plan work, delegate to sub-agents, verify results with role separation, manage persistent state across sessions, and recover from errors. You install it by giving it to your agent as instructions.

## Quick Install

**Claude Code (recommended)**

Run the bootstrap prompt to auto-detect your environment and install:
```
cat bootstrap.md | claude
```
Or manually copy the variant file:
```
cp variants/claude-code/CLAUDE.md ~/.claude/CLAUDE.md
```

**Claude Projects**

Paste the contents of `variants/claude-projects/custom-instructions.md` into your project's custom instructions field. Upload reference files from `core/`, `references/`, and `playbooks/` as project knowledge.

**Generic**

Use `variants/generic/system-prompt.md` as your system prompt. Append relevant reference files as needed for your client.

## How It Works

AgentFW uses a layered architecture to manage the context budget:

- **Always-load core** (~150 lines) is installed as CLAUDE.md or equivalent. It loads every session and contains the operating pattern, role architecture, and session protocol.
- **On-demand references** (7 files) cover state management, permissions, verification tiers, error recovery, observability, prompt design, and anti-patterns. Loaded when the task calls for them.
- **Scenario playbooks** (5 files) provide step-by-step guides for specific work types: feature development, bug hunting, maker projects, PM investigations, and cross-scenario patterns.
- **Templates** (4 files + 4 launch prompts) give agents structured starting points for PROGRESS.md, PLAN.md, SESSION_LOG.md, and DIAGNOSTIC.md. Launch prompts are copy-paste starters for autonomous sessions.
- **Evaluation suite** (2 files) contains 5 golden tasks and an eval protocol for regression testing AgentFW itself.

## Directory Structure

```
agentfw/
├── metadata.json                          # Project metadata and version info
├── bootstrap.md                           # Self-install prompt (detects client, installs variant)
├── README.md                              # This file
├── CHANGELOG.md                           # Version history with audit trail
│
├── core/
│   ├── harness-core.md                    # Always-load core (~150 lines) — the agent firmware
│   └── permissions.md                     # Trust tiers, worker scoping, escalation protocol
│
├── references/
│   ├── state-management.md                # Task state machine, checkpoints, dedupe rules
│   ├── verification-tiers.md              # Machine-checkable vs expert-checkable verification
│   ├── error-recovery.md                  # Blast radius assessment, restart vs patch protocol
│   ├── observability.md                   # SESSION_LOG format, 10 structured event types
│   ├── prompt-design.md                   # Sub-agent context scoping, context budget guidance
│   ├── anti-patterns.md                   # Failure modes and how to avoid them
│   └── domain-guidelines.md               # Code, product, research, and documentation patterns
│
├── playbooks/
│   ├── feature-dev.md                     # New feature development (autonomous + guided)
│   ├── bug-hunting.md                     # Troubleshooting transient bugs (autonomous + guided)
│   ├── maker-project.md                   # Personal build projects (autonomous + guided)
│   ├── pm-investigation.md                # Product/strategy investigation (autonomous + guided)
│   └── cross-scenario-patterns.md         # Patterns shared across scenarios, guided mode fixes
│
├── templates/
│   ├── PROGRESS.md                        # State-machine progress tracker template
│   ├── PLAN.md                            # Task plan template with permission scope column
│   ├── SESSION_LOG.md                     # Structured event log template
│   ├── DIAGNOSTIC.md                      # Bug investigation diagnostic template
│   └── launch-prompts/
│       ├── autonomous-feature.md          # Copy-paste launch prompt for feature work
│       ├── autonomous-bug.md              # Copy-paste launch prompt for bug hunting
│       ├── autonomous-maker.md            # Copy-paste launch prompt for maker projects
│       └── autonomous-pm.md               # Copy-paste launch prompt for PM investigation
│
├── evaluation/
│   ├── golden-tasks.md                    # 5 golden tasks for regression testing
│   └── eval-protocol.md                   # How to run evals and score results
│
├── variants/
│   ├── claude-code/
│   │   ├── CLAUDE.md                      # Ready-to-install CLAUDE.md for Claude Code
│   │   └── install-notes.md              # Claude Code-specific install instructions
│   ├── claude-projects/
│   │   ├── custom-instructions.md         # Ready-to-paste custom instructions
│   │   └── install-notes.md              # Claude Projects-specific install instructions
│   └── generic/
│       ├── system-prompt.md               # Ready-to-use system prompt for any client
│       └── install-notes.md              # Generic client install instructions
│
└── archive/
    ├── agentic-harness-project-instructions_r3.md
    ├── agentic-harness-playbook_r3.md
    └── agentic-harness-playbook-pm_r3.md
```

## Key Concepts

- **Decompose-Parallelize-Verify-Iterate** — The core operating pattern. Break problems into verifiable sub-problems, work them independently, verify each piece, iterate on failures with fresh context.
- **Planner-Worker-Judge** — Role architecture with mandatory separation. The session that plans does not implement. The session that implements does not verify. This prevents the agent from carrying implementation assumptions into verification.
- **Permission tiers** — Three levels (always-allow, ask-first, never-allow) that scope what workers can do without human approval. Prevents autonomous agents from taking destructive actions.
- **PROGRESS.md as state machine** — Tasks track status (planned, in-progress, blocked, done, verified, failed), worker ID, attempt number, side-effects, and checkpoints. Not just a checklist.
- **Fresh context as a design feature** — Context window limits are a feature, not a bug. A fresh agent with a summary of what was learned beats a stale agent drowning in accumulated errors. AgentFW is designed around this.
- **Autonomous vs Guided modes** — Autonomous mode dispatches sub-agent judges. Guided mode uses the human as judge. Both enforce role separation.

## What Changed in r6

- **Critical Rules preamble** — Five numbered rules at the top of the core document that survive attention deprioritization in long contexts
- **Context Health Gate** — State-driven check after every 3 tasks reach completed/verified; requires re-reading PROGRESS.md and self-assessing against Critical Rules
- **Delegation Self-Check** — Procedural gate before any implementation code in the main session
- **Context degradation as structural error** — Health check failures trigger session restart and re-verification
- **Rubber-Stamp Compliance anti-pattern** — Named failure mode for emitting protocol markers without genuine assessment
- **CONTEXT_HEALTH_CHECK event type** — Observability event for health gate assessments
- **PROGRESS.md health check tracking** — Context Health Checks table in progress template
- **Golden Tasks 6 & 7** — Late-session delegation resistance and health gate activation tests
- **Reference Index compressed** — Single-line-per-entry format reclaims space for Critical Rules
- **Claude Code variant synced** — All r5 structural enforcement gates now present; redundant Extended References section removed

## What Changed in r5

- **Mandatory classification gate** — Agent must output `[TASK CLASS: one-shot | structured | long-horizon]` before any work begins
- **Verification gates** — Tasks with unverified dependencies cannot be dispatched; `completed` no longer unblocks downstream tasks
- **Staleness detection** — Tasks stuck at `completed` without judge dispatch are flagged as verification gaps
- **Domain-specific verification** — Compiled languages require build-first; interpreted languages require test/linter execution
- **Tier 1 enforcement** — Tasks cannot transition `completed`→`verified` without machine-check output recorded
- **Late-discovery error protocol** — Errors found after multiple unverified steps trigger structural rollback
- **Autonomous mode gates** — Judge verification required between every task, not just at the end
- **One-shot criteria tightened** — Zero files modified, or one file <20 lines with no cross-file deps
- **Anti-patterns auto-loaded** for all structured/long-horizon tasks with inline warning
- **Template enforcement** — `Verification Method` column required in PLAN.md and PROGRESS.md; role-collapse detection in `Verified By`
- **Golden task runner** updated with selective test execution (run individual tests by number)

## Version History

- **r1** (2025-03-01): Initial version as a single document
- **r2** (2025-05-15): Added scenario playbooks for feature dev, bug hunting, and maker projects
- **r3** (2025-09-01): Refined role separation, added PM investigation playbook
- **r4** (2026-04-04): Modular restructure, permission model, evaluation system, observability, self-install
- **r5** (2026-04-06): Structural enforcement hardening — classification gate, verification gates, domain-specific build requirements, Tier 1 enforcement
- **r6** (2026-04-10): Context degradation resistance — Critical Rules preamble, state-driven health gate, delegation self-check
