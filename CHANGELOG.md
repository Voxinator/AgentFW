# AgentFW Changelog

## r6 (2026-04-10) — Context Degradation Resistance

### Context
Long Claude Code sessions exhibit progressive behavioral degradation: the agent stops delegating to sub-agents, stops using plan mode, stops dispatching separate judges, and collapses into one-shotting. This happens because (a) core behavioral rules lose attention weight as context fills, and (b) the existing "flag when hitting context limits" instruction is advisory — it requires the agent to remember to self-assess, which is the first thing that degrades. Additionally, the Claude Code variant was found to be missing all r5 structural enforcement gates (classification gate, one-shot hero warning, anti-patterns auto-load), meaning the primary deployment target was running with r4-era logic.

### Fixed
- **Claude Code variant synced to r5 core** — Classification gate, one-shot hero warning, tightened activation criteria, anti-patterns auto-load, and Session Protocol Step 0 now present in `variants/claude-code/CLAUDE.md`. Redundant Extended References section (38 lines) removed.

### Added
- **Critical Rules preamble** — Five numbered rules placed at the top of the core document, before all other behavioral content. Uses imperative framing designed to survive attention deprioritization in long contexts. Explicitly states "regardless of how much context has been consumed." See `core/harness-core.md`.
- **Context Health Gate** — State-driven check that fires after every 3 tasks reach completed/verified in PROGRESS.md. Requires re-reading the state file, self-assessing against Critical Rules, and outputting `[CONTEXT HEALTH: OK/DEGRADED]`. Trigger is the task count, not agent memory. See `references/state-management.md`.
- **Delegation Self-Check** — Procedural gate before any implementation code in the main session. Agent must verify its role and state a reason if not delegating. See `references/state-management.md`.
- **Context degradation as structural error** — When health check reveals degradation, treat as structural error: compact, restart with fresh context, re-verify work completed after last clean check. See `references/error-recovery.md`.
- **Rubber-Stamp Compliance anti-pattern** — Named failure mode for mechanically outputting protocol markers without genuine assessment. See `references/anti-patterns.md`.
- **CONTEXT_HEALTH_CHECK event type** — Observability event for health gate assessments. See `references/observability.md`.
- **PROGRESS.md health check tracking** — Context Health Checks table in the progress template. See `templates/PROGRESS.md`.
- **Golden Task 6: Late-Session Delegation** — Multi-phase test that fills context before testing whether delegation discipline holds. See `evaluation/golden-tasks.md`.
- **Golden Task 7: Context Health Gate Activation** — Tests whether the health gate fires correctly and resists rubber-stamping. See `evaluation/golden-tasks.md`.

### Enhanced
- **Reference Index compressed** — Removed subheaders and blank lines, single-line-per-entry format. Reclaimed 5 lines for Critical Rules. See `core/harness-core.md`.
- **Session Protocol updated** — "Flag when hitting context limits" replaced with concrete health gate trigger and output format. See `core/harness-core.md`.

### Files Modified
- `core/harness-core.md` — Critical Rules preamble, Reference Index compression, Session Protocol health gate
- `variants/claude-code/CLAUDE.md` — Full r5 gate sync, Extended References removed, Critical Rules preamble, health gate
- `references/state-management.md` — Context Health Gate, Delegation Self-Check
- `references/anti-patterns.md` — Rubber-Stamp Compliance anti-pattern
- `references/observability.md` — CONTEXT_HEALTH_CHECK event type
- `references/error-recovery.md` — Context degradation as structural error
- `templates/PROGRESS.md` — Context Health Checks table
- `evaluation/golden-tasks.md` — GT-6 (late-session delegation), GT-7 (health gate activation)
- `evaluation/eval-protocol.md` — GT-6 and GT-7 execution instructions and failure criteria
- `metadata.json` — Version bump to r6
- `CHANGELOG.md` — This entry
- `bootstrap.md` — r5 → r6 references

---

## r5 (2026-04-06) — Structural Enforcement Hardening

### Context
Two observed failures exposed that r4 relies on behavioral compliance rather than structural gates: (1) Claude Code skips the harness for tasks meeting activation criteria because the decision tree is advisory, and (2) in a UE5 C++ project, three planning steps "completed" without building code — errors accumulated invisibly. This release converts advisory instructions into procedural constraints.

### Added
- **Mandatory classification gate** — Agent must output `[TASK CLASS: one-shot | structured | long-horizon]` before any work. Omitting is a protocol violation. See `core/harness-core.md`.
- **Verification gates** — Tasks with unverified dependencies cannot be dispatched. Hard gate, not advisory. See `references/state-management.md`.
- **Staleness detection** — Tasks at `completed` without judge dispatch are flagged as verification gaps. See `references/state-management.md`.
- **Compiled language verification** — Judge must build as first step for C++, Rust, Go, Java, C#, Swift. Reasoning-only review is not Tier 1. See `references/domain-guidelines.md`.
- **Interpreted language verification** — Judge must run tests/linter or at minimum import the module. See `references/domain-guidelines.md`.
- **Late-discovery error protocol** — Errors found after multiple unverified tasks are treated as structural; roll back to last verified checkpoint. See `references/error-recovery.md`.
- **Autonomous mode verification gates** — Judge dispatched between every task, not just at the end. See `playbooks/feature-dev.md`.
- **Long-running service restart rule** — Workers/judges must automatically restart services (web apps, gateways, daemons) after code changes. No manual restart steps. See `references/domain-guidelines.md`.

### Enhanced
- **One-shot criteria tightened** — One-shot now requires: zero files modified, OR one file <20 lines with no cross-file deps. Relaxation requires explicit justification. See `core/harness-core.md`.
- **Tier 1 enforcement** — Tasks cannot transition completed→verified without machine-check output in PROGRESS.md. See `references/verification-tiers.md`.
- **PLAN.md template** — Added required `Verification Method` column (build, test:\<cmd\>, lint:\<cmd\>, schema-check, human-review, expert-subagent). Locked at planning time. See `templates/PLAN.md`.
- **PROGRESS.md template** — Added `Verification Method` and `Verification Artifact` columns. `Verified By` = "planner" is flagged as role-collapse violation. Version bumped to r5. See `templates/PROGRESS.md`.
- **Anti-patterns auto-loaded** — `references/anti-patterns.md` now loads for all structured/long-horizon tasks, not just self-check. One-Shot Hero Mode warning inlined into decision tree. See `core/harness-core.md`.

### Files Modified
- `core/harness-core.md` — Classification gate, tightened one-shot, WARNING callout, anti-patterns auto-load
- `references/state-management.md` — Verification gates, staleness detection, strengthened `completed` state
- `references/domain-guidelines.md` — Compiled and interpreted language verification subsections
- `references/verification-tiers.md` — Tier 1 enforcement language
- `references/error-recovery.md` — Late-discovery error protocol
- `templates/PLAN.md` — Verification Method column and rules
- `templates/PROGRESS.md` — Verification Method, Verification Artifact, role-collapse detection, r5 version
- `playbooks/feature-dev.md` — Autonomous mode verification gates

---

## r4 (2026-04-04) — Modular Restructure + Audit Fixes

### Breaking Changes
- Project restructured from 3 flat files to modular directory. If you have r3 installed as CLAUDE.md, you need to re-install using the r4 variant or bootstrap.
- CLAUDE.md content reduced to ~150-line core. Extended content moved to on-demand references.
- Guided mode no longer instructs the same session to switch between worker and judge roles.

### Added
- **Permission model** [F1]: Three trust tiers (always-allow, ask-first, never-allow), worker scope constraints, escalation protocol. See `core/permissions.md`.
- **Evaluation system** [F3]: 5 golden tasks for regression testing harness behavior. See `evaluation/golden-tasks.md` and `evaluation/eval-protocol.md`.
- **Observability** [F4]: Structured event logging via SESSION_LOG.md. 10 event types for tracking agent behavior. See `references/observability.md`.
- **Bootstrap installer**: Self-install prompt that detects client type and installs the appropriate variant. See `bootstrap.md`.
- **Client variants**: Pre-built install artifacts for Claude Code, Claude Projects, and generic clients.
- **Launch prompt templates**: Standalone copy-paste prompts for autonomous sessions.
- **PLAN.md template**: Task plan template with permission scope column.

### Enhanced
- **State management** [F2]: PROGRESS.md upgraded from checklist to state machine. Tasks now track: status (planned→verified/failed), worker ID, attempt number, side-effects, checkpoints. Dedupe rules prevent double-dispatch. See `references/state-management.md`.
- **Prompt design** [F5]: Added context budget guidance for sub-agents. Workers receive only task-relevant context, not the full framework. See `references/prompt-design.md`.

### Fixed
- **Guided mode self-review** [F6]: Removed pattern where the same session acts as both worker and judge. Human-as-judge is now the default in guided mode. Option to dispatch separate sub-agent judge. See `playbooks/cross-scenario-patterns.md`.

### Architecture
- Core framework condensed from ~330 lines to ~150 lines (always-load)
- All extended content moved to on-demand references (7 files)
- Playbooks extracted to individual files (5 files)
- Templates extracted to dedicated directory (4 files + 4 launch prompts)
- r3 originals preserved in `archive/`

### Audit Trail
Findings from evaluation using OB1 n-agentic-harnesses skill (pre-rename: "Agentic Harness"):
- F1 (High): No permission layer → `core/permissions.md`
- F2 (High): No state model → `references/state-management.md`, `templates/PROGRESS.md`
- F3 (Med-High): No evaluation system → `evaluation/golden-tasks.md`, `evaluation/eval-protocol.md`
- F4 (Medium): No observability → `references/observability.md`, `templates/SESSION_LOG.md`
- F5 (Medium): Unmanaged context budget → core/references split, `references/prompt-design.md`
- F6 (Low-Med): Guided mode self-review → all playbook guided-mode sections
