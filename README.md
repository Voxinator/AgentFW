# AgentFW

## What This Is

AI capabilities look jagged when you ask for one-shot answers. The same model that writes a flawless function will hallucinate a dependency or skip a critical edge case two prompts later. The inconsistency isn't in the model — it's in the lack of structure around it. Apply the same organizational patterns that make human teams effective (task decomposition, parallel execution, independent verification, iterative refinement) and the surface smooths out.

Claude Code 2.1 now supplies those patterns as **native runtime primitives** — the Workflow tool (`agent()`, `parallel()`, `pipeline()`, judge-panel, resume/journal), Agent subagents, Plan mode, Skills, MEMORY, the Task system + Cron/schedule/loop, and permission modes + hooks + worktrees. So as of v8, AgentFW is no longer the machinery. It is a **governance/policy layer over those primitives**: it decides *whether, when, and how well* to orchestrate, while the runtime executes *how* (Rule 6: PREFER NATIVE PRIMITIVES).

AgentFW is still a set of structured Markdown documents that install as standing instructions — not a framework, library, or SDK. What it supplies is the judgment the runtime does not: the Classification Gate, role-separation discipline with judge input-curation, the Tier-1 verification and Context Health enforcement gates, the new Plan-Critique Gate (critique the plan before the first worker dispatch), and the anti-pattern judgment layer (especially Complexity Accumulation — the counterweight to native tooling's bias toward more machinery). v8 is **Claude-Code-only**; cross-model content has been dropped.

> **Hermes variant moved.** The Hermes variant (Gemma-4 running AgentFW as a local orchestrator on Hermes Agent) has been extracted to its own project, **`agentfw-hermes`**, and removed from this repo. It is no longer part of AgentFW core. Historical commits in this repo's git history and `archive/` are unaffected.

## r9 (draft)

**Status: draft — not eval-validated (golden-task re-run pending).**

r9 thesis: *"r9 governs work through portable assurance contracts compiled into native runtime behavior where a runtime exists to compile into, and into explicit, evidence-bearing model commitments where it doesn't — with the honesty to say which is which per adapter."*

**Eval honesty note:** the last golden-task run (2026-05-29, against r8) scored 5 PASS / 3 UNTESTED — the 3 partials were test-design issues, which means those criteria were UNTESTED, not passed; r9 has not yet been evaluated.

### r9 layout

- **`policy/`** — the platform-neutral semantic policy (assurance model, verification tiers, acceptance contracts, Plan-Critique Gate, capability contracts, recovery, anti-patterns). Names no vendor runtime primitive.
- **`adapters/claude-code/`** and **`adapters/codex/`** — native adapters that compile the policy into each runtime's real controls, each with INSTALL/UPGRADE/UNINSTALL docs and a `capability.yaml`. Each capability entry now splits what the platform makes **available** from what a given install has **configured** (with an `activation_probe` to check locally), so assurance gating consults the active install, not the platform brochure.
- **`profiles/`** — guided degradation profiles (`profiles/chatgpt-projects.md` for standard ChatGPT/Projects, `profiles/claude-projects.md` for Claude.ai Projects) for runtimes with no enforcement surface. Explicitly *not* adapters. (ChatGPT Work is a different surface with hosted subagents — the designated r9.1 adapter candidate, deferred until the two shipped adapters pass evals.)
- **`tools/`** — `validate-plan` (deterministic Layer-1 plan validation + fixtures), `agentfw-install` (marker-block installer), and `tests/`.

**Scope boundary (deliberate):** r9 ships exactly two native adapters (Claude Code, Codex) and two guided profiles (standard ChatGPT/Projects, Claude.ai Projects). ChatGPT Work — a different surface with hosted subagents/skills — is acknowledged but deferred to **r9.1** as the designated adapter candidate, per the Adapter Sprawl rule (no platform binding ships before the existing adapters pass evals). This is a deliberate boundary, not full ChatGPT parity.

### Install / upgrade / uninstall per platform

| Platform | Install | Upgrade | Uninstall |
|---|---|---|---|
| Claude Code | `adapters/claude-code/INSTALL.md` | `adapters/claude-code/UPGRADE.md` | `adapters/claude-code/UNINSTALL.md` |
| Codex | `adapters/codex/INSTALL.md` | `adapters/codex/UPGRADE.md` | `adapters/codex/UNINSTALL.md` |

> **Note:** `variants/` (r6-era) is superseded by `adapters/` and retained for history. The r8 sections below still describe `core/` + `references/`, which remain valid until r9 is validated.

## Quick Install

AgentFW v8 targets **Claude Code** exclusively.

Run the bootstrap prompt to detect your environment and install:
```
cat bootstrap.md | claude
```
Or manually copy the core file into place as your CLAUDE.md:
```
cp core/harness-core.md ~/.claude/CLAUDE.md
```
Upgrading from an r6/r7 install overwrites the installed CLAUDE.md — back it up first if you want to keep the prior version. See `bootstrap.md` for the full procedure.

## How It Works

AgentFW v8 layers a governance policy over Claude Code 2.1's runtime, managing the context budget through on-demand loading:

- **Always-load core** (`core/harness-core.md`) is installed as CLAUDE.md. It loads every session and carries the v8 layering: the runtime supplies the harness (Workflow, subagents, Plan mode, Skills, MEMORY, hooks); the firmware supplies the classification, role discipline, verification standard, and restraint the runtime does not supply on its own.
- **`references/native-primitives.md`** is the delegation map — each Claude Code 2.1 primitive paired with the firmware concept it executes and the division of labor — plus the operational Plan-Critique recipe (checklist, Acceptance-Contract schema, convergence/stop policy).
- **On-demand references** cover permissions, verification tiers, error recovery, prompt design (context-budget + judge input-curation), and anti-patterns. Loaded when the task calls for them.
- **Scenario playbooks** provide step-by-step guides for specific work types: feature development, bug hunting, maker projects, PM investigations, and cross-scenario patterns.
- **Templates** (PROGRESS.md, PLAN.md, SESSION_LOG.md, DIAGNOSTIC.md, plus launch prompts) give agents structured starting points for bare-interactive sessions where no native journal applies.
- **Evaluation suite** contains the golden tasks (including GT-8 for the Plan-Critique Gate) and an eval protocol for regression testing AgentFW itself.

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
│   ├── native-primitives.md               # Delegation map (primitive → firmware concept) + Plan-Critique recipe
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
└── archive/
    ├── agentic-harness-project-instructions_r3.md
    ├── agentic-harness-playbook_r3.md
    └── agentic-harness-playbook-pm_r3.md
```

> The Hermes variant that previously lived under `variants/hermes/` has been extracted to its own project (`agentfw-hermes`).

## Key Concepts

- **Decompose-Parallelize-Verify-Iterate** — The core operating pattern. Break problems into verifiable sub-problems, work them independently, verify each piece, iterate on failures with fresh context.
- **Planner-Worker-Judge** — Role architecture with mandatory separation. The session that plans does not implement. The session that implements does not verify. This prevents the agent from carrying implementation assumptions into verification.
- **Permission tiers** — Three levels (always-allow, ask-first, never-allow) that scope what workers can do without human approval. Prevents autonomous agents from taking destructive actions.
- **PROGRESS.md as state machine** — Tasks track status (planned, in-progress, blocked, done, verified, failed), worker ID, attempt number, side-effects, and checkpoints. Not just a checklist.
- **Fresh context as a design feature** — Context window limits are a feature, not a bug. A fresh agent with a summary of what was learned beats a stale agent drowning in accumulated errors. AgentFW is designed around this.
- **Autonomous vs Guided modes** — Autonomous mode dispatches sub-agent judges. Guided mode uses the human as judge. Both enforce role separation.

## What Changed in r8

- **Firmware reframed as a governance layer over Claude Code 2.1 native primitives** — AgentFW is no longer the orchestration machinery. The runtime supplies the harness (Workflow tool, Agent subagents, Plan mode, Skills, MEMORY, Task system + Cron/schedule/loop, permission modes + hooks + worktrees, context compaction); the firmware decides whether/when/how-well to engage it. `core/harness-core.md` rewritten around this layering.
- **Rule 6: PREFER NATIVE PRIMITIVES** — new Critical Rule. Don't hand-roll in prose what the runtime does natively; don't double-bookkeep against the platform.
- **Plan-Critique Gate + Acceptance-Contract spine (validated)** — new gate with no native analog: before the first worker dispatch, drive a Workflow judge-panel OVER THE PLAN (input-curated), scored against checks C0–C5 + coverage. Each task carries an Acceptance Contract `{criteria, acceptance_command, expected_signal, risk}` whose discriminating lever must be mechanically reachable by the command, not just asserted in prose.
- **`references/native-primitives.md`** (NEW) — the delegation map (primitive → firmware concept it executes + division of labor) and the operational Plan-Critique recipe.
- **GT-8** — golden task proving the harness verifies the *plan* before spending worker budget, and that the gate catches its own deepest weakness (a prose lever a wrong implementation passes).
- **Hermes variant extracted to `agentfw-hermes` and removed** — the Gemma-4-on-Hermes-Agent local-orchestration variant and its r7.1–r7.11 probe/campaign work no longer live in this repo. Historical git commits and `archive/` are unaffected.
- **Cross-model content dropped** — v8 is Claude-Code-only. The `references/prompt-design.md` "Model-family knobs (non-binding)" subsection (Anthropic-specific Opus tuning) is removed; `compatibility` is now `["claude-code"]`.

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
- **r7** (2026-04-17): Cross-model tuning pass — model-agnostic edits for Opus 4.7 without non-target regression, bounded model-family knobs subsection, reduced-scope Phase 0 multi-model probe
- **r7.1–r7.11** (2026-04-18 → 2026-04-30): Hermes-variant probe + campaign arc (Gemma-4 local orchestration on Hermes Agent). This work has been extracted to its own project, `agentfw-hermes`, and removed from this repo; the full history remains in `agentfw-hermes` and in this repo's git history.
- **r8** (2026-05-29): v8 governance refactor — firmware reframed as a governance layer over Claude Code 2.1 native primitives (Rule 6: PREFER NATIVE PRIMITIVES), Plan-Critique Gate + Acceptance-Contract spine, `references/native-primitives.md`, GT-8. Cross-model content dropped (Claude-Code-only); Hermes variant extracted to `agentfw-hermes`
