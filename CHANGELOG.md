# AgentFW Changelog

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
