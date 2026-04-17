# AgentFW Changelog

## r7 (2026-04-17) — Cross-Model Tuning Pass

### Context
Claude Opus 4.7 landed with behavior deltas — fewer sub-agents dispatched by default, adaptive thinking off by default, stronger intrinsic self-verification, and coding-benchmark gains that tempt loosening structural gates. A tuning pass was needed to keep AgentFW aligned with 4.7 without regressing Opus 4.6, Sonnet 4.6, or GPT-5-tier models. The core firmware stays model-agnostic; 4.7-specific knobs live in a single short appendix with inline `(Anthropic: …)` sidenotes. Ten proposals from the r7 judge artifact were triaged: six shipped as model-agnostic edits, three shipped as reframed principles in a bounded model-family subsection, and four were rejected or deferred. See `PLAN-r7.md` §2–§4.

### Added
- **Self-verification vs. self-review clarifier** — Appended a single sentence to the Self-Review anti-pattern distinguishing in-context intrinsic pre-flight verification (fine, model-provided) from self-review-as-judge (prohibited by Rule 3). Prevents future tuners from weakening Rule 3 on the back of any model's self-verification marketing. See `references/anti-patterns.md`. (PLAN-r7 §2.1.)
- **Explicit fan-out instruction in worker dispatch** — Added a paragraph above `### Include` in the Context Budget for Sub-Agents subsection instructing planners to say "spawn N workers in parallel" literally when decomposing across independent items, not "decompose" alone. Counters 4.7's "fewer subagents by default" tendency; helps every model that takes literal phrasing better than advisory phrasing. See `references/prompt-design.md`. (PLAN-r7 §2.2.)
- **Quote-before-act on state files** — New subsection in state-management.md: worker prompts should include the exact PROGRESS.md line(s) being acted on, and workers are expected to echo them in returned artifacts. Applies to workers and judges equally. See `references/state-management.md`. (PLAN-r7 §2.4.)
- **Cadence annotation for the 3-task health gate** — One-line note after the numbered health-gate steps explaining the cadence is held pending empirical degradation-curve data; long-context retrieval scores do not imply agentic rule-adherence stability. Immunizes the cadence against well-meaning loosening on any vendor's long-context claims. See `references/state-management.md`. (PLAN-r7 §2.5.)
- **Task-state-triggered reflection note** — One-line cross-reference in state-management.md and observability.md clarifying the health gate fires on PROGRESS.md task count, not on a tool-call clock. Pre-empts deletion of the gate by any future tuner reading "remove every-N-tool-calls summarization" advice. See `references/state-management.md` and `references/observability.md`. (PLAN-r7 §2.6.)
- **Model-family knobs (non-binding) subsection** — New ≤25-line subsection at the end of `references/prompt-design.md` covering three reframed principles with inline sidenotes: reasoning effort by role, judges need guaranteed deliberation, token budget as a worker-scope component. Principles are model-agnostic; Anthropic-specific invocations appear only as `(Anthropic Opus 4.7: …)` sidenotes. See `references/prompt-design.md`. (PLAN-r7 §3.)

### Enhanced
- **Reference-file audit for vague generalizations** — Single-pass read of state-management, prompt-design, domain-guidelines, error-recovery, and anti-patterns for "and similar," "etc.," "or equivalent," and abstract generalizations in rule-bearing text. Where found, replaced with explicit enumerations or concrete triggers. Net-neutral or slightly negative on line count. (PLAN-r7 §2.3.)

### Rejected / Deferred
- **P5 — Recalibrate line-count heuristics to tokens for the 4.7 tokenizer.** Rejected. Line counts are more portable across tokenizers than any token-based heuristic; the current "500 lines" / "~175 lines" guidance is directionally correct for all models. (PLAN-r7 §4.)
- **P11 — Route web-research-heavy tasks away from 4.7 (BrowseComp regression).** Deferred. No Artifact A surface quote exists for the specific playbook content; re-evaluate when BrowseComp regression is reproduced in-house. (PLAN-r7 §4.)
- **P12 — Loosen `<20-line` one-shot threshold based on 4.7 coding gains.** Rejected. The clause is a role-separation gate, not a capability gate; benchmark strength does not change whether the main session should implement vs. delegate. (PLAN-r7 §4.)
- **P13 — Weaken Rule 3 (NO SELF-VERIFY) because 4.7 self-verifies.** Rejected. Anthropic does not claim 4.7's built-in self-verification replaces an independent-context judge; loosening rests on a misreading of the source. (PLAN-r7 §4.)

### Baseline Probe
Phase 0 multi-model empirical probe was run at reduced scope on 2026-04-17: Opus 4.7 and Sonnet 4.6 across GT-1, GT-3, and GT-5 only — 6 of 28 cells filled. Opus 4.6 could not be version-pinned via the Claude Code Agent tool model enum; GPT-5.4-Pro was not accessible from the probe tooling; GT-2/4/6/7 require true multi-turn sessions or mid-task event injection that single-dispatch subagents cannot reproduce. Directional signal: Opus 4.7 emitted classification gates correctly on all 3 probed tasks; Sonnet 4.6 missed the marker on GT-5 and was unclear on GT-3. Full-scope baseline deferred. See `evaluation/results-r6-baseline-multimodel-2026-04-17.md`.

### Known Gaps
- Opus 4.6 version-pinning not available in current tooling; non-regression on 4.6 could not be empirically confirmed for r7.
- GPT-5.4-Pro not accessible from probe tooling; cross-vendor non-regression claim is asserted on design grounds, not measured.
- GT-2, GT-4, GT-6, and GT-7 require a multi-turn runner and were not covered in the Phase 0 probe; human-driven runs needed to close the matrix.
- Sonnet-4.6-specific tuning (addressing the classification-gate miss and the DIAGNOSTIC.md classification-marker ambiguity observed in probe transcripts) is documented separately in `ADDENDUM-sonnet-4-6.md` for future revision.

### Migration
Claude Code users should re-sync their global CLAUDE.md from `variants/claude-code/CLAUDE.md`. Other variants (Claude Projects, Generic, Hermes) are deferred to a follow-up sync per PLAN-r7 §7 and will inherit the r7 edits after the Claude-Code variant clears the regression gate on full-scope runs.

### Line Delta
Firmware line-delta budget: ≤70 added lines across `core/`, `references/`, and variants combined, excluding CHANGELOG. Actual delta tracked in PLAN-r7 §5 accounting table.

### Files Modified
- `references/anti-patterns.md` — Self-review clarifier sentence
- `references/prompt-design.md` — Fan-out dispatch paragraph, Model-family knobs (non-binding) subsection
- `references/state-management.md` — Quote-before-act subsection, cadence annotation, task-state-triggered reflection note, vague-generalization audit
- `references/observability.md` — Task-state-triggered reflection cross-reference
- `variants/claude-code/CLAUDE.md` — r7 edits synced from canonical core + references
- `metadata.json` — Version bump to r7, date to 2026-04-17, description updated
- `README.md` — r7 revision references, what's-new section
- `DESIGN.md` — r7 revision references, reduced-scope probe note, model-family posture pointer
- `CHANGELOG.md` — This entry

---

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
