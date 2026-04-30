# AgentFW

## What This Is

AI capabilities look jagged when you ask for one-shot answers. The same model that writes a flawless function will hallucinate a dependency or skip a critical edge case two prompts later. The inconsistency isn't in the model — it's in the lack of structure around it. Apply the same organizational patterns that make human teams effective (task decomposition, parallel execution, independent verification, iterative refinement) and the surface smooths out.

AgentFW encodes that lesson as standing instructions for AI agents. It is not a framework, library, or SDK. It's a set of structured Markdown documents that teach agents how to plan work, delegate to sub-agents, verify results with role separation, manage persistent state across sessions, and recover from errors. You install it by giving it to your agent as instructions.

## Hermes variant status (internal RC)

The Hermes variant — Gemma-4 running AgentFW as a local orchestrator on Hermes Agent — has reached **`hermes-r7.11-rc1` internal RC** (2026-04-30). r7.11 introduces the verified-state multi-session resumable architecture with execution-tier acceptance verification (tier 3.7), closing the synthesis-trust gap that r7.5–r7.10 surfaced (verifier-pass without acceptance-pass).

Empirical baseline (item 9, n=5 on T6 capability-curve workload): **3/5 strict completion** (cleared the pre-committed RC threshold). 0/5 trials reproduced the trial-3 verifier-pass / acceptance-fail mode. See `variants/hermes/r7.9-research/r7.11/README.md` for the full milestone tree (source modules, design, HANDOFF, test suite, followup ledger). Tag: `hermes-r7.11-rc1`.

**Install** (requires Hermes Agent on a remote VM; see `variants/hermes/INSTALL.md` for prerequisites + manual procedure):

```bash
bash variants/hermes/install.sh --check    # pre-flight only
bash variants/hermes/install.sh            # install
bash variants/hermes/install.sh --uninstall # restore canonical
```

**Use it**: see `variants/hermes/USAGE.md` for progressive examples — Level 0 (10-second smoke) through Level 5 (build your own scaffold). Levels 0-2 take under 5 minutes total and prove the lifecycle works; Level 4 reproduces the campaign-baseline T6 result.

The β-fuse dispatch architecture from r7.4 (still part of the worked stack) and the r7.5 worker-quality ship gate are now subsumed by r7.11's parent-as-orchestrator + per-phase verification design. Worker-quality concerns from r7.5 are addressed via the verified-state-between-phases mechanism rather than direct worker-side intervention.

Non-Hermes variants (claude-code, claude-projects, generic) are byte-identical to r7 and unaffected by the r7.x–r7.11 Hermes probe and campaign work.

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
│   ├── generic/
│   │   ├── system-prompt.md               # Ready-to-use system prompt for any client
│   │   └── install-notes.md              # Generic client install instructions
│   └── hermes/                            # Hermes Agent variant (Gemma-4 local orchestration) — PRE-RELEASE
│       ├── HERMES.md                      # Canonical base system prompt (upstream, unchanged)
│       ├── HERMES-variantB.md             # Historical probe sibling: hard output contract (r7)
│       ├── HERMES-variantD.md             # Historical r7 ship candidate (superseded by variantF)
│       ├── HERMES-variantE.md             # Historical r7.3 sibling (superseded by variantF)
│       ├── HERMES-variantF.md             # r7.4 β-fuse harness prompt — current pre-release
│       ├── delegate_worker.py             # Legacy v1 dispatch tool (retained; emits deprecation notice)
│       ├── delegate_worker_v2.py          # β-fuse dispatch tool — required classification + justification
│       ├── DESIGN.md                      # Architecture and rationale (refreshed for r7.5)
│       ├── INSTALL.md                     # Authoritative install procedure (r7.5)
│       ├── DEPENDENCIES.md                # Tested versions, hardware notes, Hermes requirements
│       ├── IMPLEMENTATION.md              # Historical r7 install doc (frozen)
│       ├── PROBE-RESULTS-r7.md            # Consolidated r7 probe sweep results (historical)
│       ├── NEXT-STEPS.md                  # Follow-up work: r7.6 agenda + operator decision tree
│       └── install-notes.md              # Hermes-specific install instructions
│
└── archive/
    ├── agentic-harness-project-instructions_r3.md
    ├── agentic-harness-playbook_r3.md
    ├── agentic-harness-playbook-pm_r3.md
    └── hermes-probe-r7-2026-04-18/        # Raw artifacts from the r7.1 Hermes probe sweep (19 files)
```

## Key Concepts

- **Decompose-Parallelize-Verify-Iterate** — The core operating pattern. Break problems into verifiable sub-problems, work them independently, verify each piece, iterate on failures with fresh context.
- **Planner-Worker-Judge** — Role architecture with mandatory separation. The session that plans does not implement. The session that implements does not verify. This prevents the agent from carrying implementation assumptions into verification.
- **Permission tiers** — Three levels (always-allow, ask-first, never-allow) that scope what workers can do without human approval. Prevents autonomous agents from taking destructive actions.
- **PROGRESS.md as state machine** — Tasks track status (planned, in-progress, blocked, done, verified, failed), worker ID, attempt number, side-effects, and checkpoints. Not just a checklist.
- **Fresh context as a design feature** — Context window limits are a feature, not a bug. A fresh agent with a summary of what was learned beats a stale agent drowning in accumulated errors. AgentFW is designed around this.
- **Autonomous vs Guided modes** — Autonomous mode dispatches sub-agent judges. Guided mode uses the human as judge. Both enforce role separation.

## What Changed in r7.11 (Hermes — internal RC)

- **Hermes variant reaches internal RC** — tagged `hermes-r7.11-rc1` (pre-release on GitHub; branch `hermes-r7.11-internal-rc` not merged to main). Full milestone tree at `variants/hermes/r7.9-research/r7.11/`. Self-contained: source modules, 227-test suite, original DESIGN doc, HANDOFF campaign-close runbook, schema/howto docs, followup ledger.
- **Verified-state multi-session resumable architecture.** `verified-state.json` is the machine-authoritative phase state file; the parent's narrative is non-authoritative. Each phase runs as its own Hermes session via a thin Python wrapper (`hermes_multi.py`); session boundaries are sentinel-file driven. The wrapper polls sentinels, archives sessions, and routes via the state file (read-only).
- **Execution-tier verification (tier 3.7 acceptance-runner).** First execution-based verification tier in the campaign. Subprocess-runs the phase's stated `Acceptance Command:` (declared in PLAN.md per phase) under a B1-style augmented PYTHONPATH; structured exit-code interpretation distinguishes `[ACCEPTANCE_PASSED]` / `[ACCEPTANCE_FAILED:N]` / `[ENVIRONMENT:reason]` / `[INCONCLUSIVE:reason]`. Static-only verification (presence + syntax + imports + wiring + opt-in importlib smoke) is necessary but not sufficient — tier 3.7 closes the synthesis-trust gap.
- **Tool-description teaching as the working doctrine-delivery mechanism.** Loud doctrine in HERMES.md or system prompts reaches the parent at 0% in pre-r7.11 measurements; teaching embedded in tool descriptions (e.g., `write_plan_md`'s acceptance_command teaching, `end_session_for_handoff`'s STANDARD PATTERN nudge) reaches the parent at 60-100% across n=5.
- **Item 9 n=5 confirmation: 3/5 strict completion on T6.** Pre-committed RC threshold: ≥3/5. Met. Two ESCALATEs surfaced parent-side variance (recovery quality on tier-3 catches; bootstrap ceremonial-sentinel-firing) — both fired correctly per design with operator-actionable corrective_dispatch. **0/5 trials reproduced the trial-3 failure mode** (verifier-pass without acceptance-pass).
- **6 followups CLOSED in r7.11**: B1 (F-5 resolution: PYTHONPATH-injection at probe time only), F-4 (content_verify absolute-path), F-7 (synthesis-trust gap → tier 3.7), F-8 (parent batches phases → handoff nudge), F-9 part B (orphan-collision detection in tier 3) + part C (scaffold-baseline empty-stub convention), F-11 (write_plan_md acceptance_command teaching).
- **6 followups DEFERRED to r7.12**: F-1 (Hermes SessionDB regression — independent), F-2 (registry.dispatch upstream), F-10 (tier-3.5 path-walker), F-12 (content_verify rubric noise), plus 2 new from n=5 (parent-recovery quality on tier-3 catches; bootstrap-handoff ceremony strengthening). r7.12 architecture review is the next planning milestone.
- **AgentFW-portable findings** (these inform AgentFW core; documented in the variant README): verified-state-between-phases as the synthesis-trust mechanism; execution-tier verification pattern; wrapper-as-dumb-substrate / parent-as-orchestrator; tool-description teaching; sentinel-file-driven session boundaries; tiered verifier with structured exit-code interpretation. The variant README also calls out Hermes-specific implementation mechanics (the `_session_messages_live` patch, parser-bug workaround, tool registration mechanics, SessionDB regression workarounds) that should NOT generalize without substrate knowledge.

## What Changed in r7.5 (Hermes pre-release)

- **Hermes variant reaches pre-release status** — tagged `r7.5-hermes-prerelease`. See `/RELEASE-NOTES-r7.5-hermes-prerelease.md`.
- **β-fuse dispatch architecture validated (r7.4).** `delegate_worker_v2` required-argument tool moved MoE first-attempt dispatch to 17/20 strict (85%), dense to 77% measured — 11.5×–17× lift over r7.3 pre-intervention baselines. v2-adoption 100% on compliant trials. Ship verdict: SHIP-WITH-CAVEAT for the dispatch layer (see `ARTIFACT-r7.4-ship-judge-verdict-v2.md`).
- **r7.5 turn-0 toolset restriction hook** — closes the dense `todo`/`search_files` escape at the mechanism layer (tools filtered to `{delegate_worker_v2, clarify}` at turn 0 under the exact β-fuse toolset composition). Composition-scoped: canonical flows unaffected.
- **Worker-quality ship gate measured for the first time — FAILED.** r7.5 20-trial MoE probe: 3/20 PASS vs 15/20 floor. Root causes identified and reproducible: search_files thrash, SIGTERM truncation, pseudo-tool-call text emission, fabricated completions. Tracked as r7.6 scope. β-fuse dispatch thesis remains intact; dispatch and worker-quality are independent axes.
- **Probe-fidelity hardening** — r7.4 P1 analyzer fix (filter hallucinated tool names), r7.5 Tier-1 SIGTERM content-match recovery (`--expected-prompt-prefix-b64`), `ERROR:WRONG_SESSION` verdict for mis-attached child sessions, oMLX health-check probe.
- **Measurement caveat on r7.1 numbers** — the original r7.1 "60% first-attempt / 80% final" headline was inflated by a wrapper counting stdout markers as dispatches. Strict on-disk re-tally (`ARTIFACT-drift-step-a-retally.md`) showed r7.1 true first-attempt was 0/5. All numbers from r7.2 forward use strict on-disk criteria; cross-version comparisons must use the strict metric.
- **Documentation refresh** — new `variants/hermes/INSTALL.md` (authoritative; supersedes `IMPLEMENTATION.md`), `variants/hermes/DEPENDENCIES.md`, refreshed `variants/hermes/DESIGN.md`, extended `variants/hermes/NEXT-STEPS.md` with r7.6 agenda + operator decision tree.
- **Cross-model integrity preserved** — `core/`, `references/`, `playbooks/`, `templates/`, and non-Hermes variants byte-identical throughout the r7.x Hermes probe campaign.

## What Changed in r7.4 (Hermes — β-fuse)

- **β-fuse structural dispatch (`delegate_worker_v2`)** — classification moved from a text marker to a required tool-call argument. `HERMES-variantF.md` teaches v2 exclusively. SHIP-WITH-CAVEAT ship verdict for the dispatch layer. Dense 77% measured / MoE 85% first-attempt strict. See CHANGELOG §r7.4.

## What Changed in r7.3 (Hermes — L1+L2 attempt, FAILED)

- **Layer 1 + 2 stacked remediation** — new `file_readonly` toolset bundle, escape-hatch-stripped `HERMES-variantE.md`, toolset restriction. Dispatch dropped below baseline on both models (1/15 each). Diagnosis: language-only remediation displaces escape behavior rather than eliminating it. Led directly to the β-fuse design that landed in r7.4. See CHANGELOG §r7.3.

## What Changed in r7.2 (Hermes — dense vs MoE + measurement correction)

- **Strict on-disk re-tally** inverted r7's headline ordering — the 60%/80% numbers were wrapper-counted artifacts, not dispatches. Dense strict first-attempt was 1/5; MoE was 0/5 first / 5/5 final (wrapper-retry-rescued). Variant E ship-candidate status formally withdrawn. See CHANGELOG §r7.2.

## What Changed in r7.1 (Hermes — initial probe sweep, numbers later corrected)

- **Hermes-variant probe sweep** — original 5-variant sweep (A/B/C/D/E) on `gemma-4-31b-it-4bit`. Original headline claim was 60% first-attempt / 80% final dispatch on structured/long-horizon. **These numbers were inflated** per the r7.2 strict re-tally: true first-attempt was 0/5 strict on-disk. The architectural thesis ("Gemma as orchestrator, local inference only") was partially validated — dispatches do occur — at much lower reliability than originally reported. See `variants/hermes/PROBE-RESULTS-r7.md` for the corrected history.
- **Hermes variant design artifacts** — initial `DESIGN.md`, `IMPLEMENTATION.md`, `PROBE-RESULTS-r7.md`, `NEXT-STEPS.md`. DESIGN.md refreshed in r7.5; IMPLEMENTATION.md frozen, superseded by `INSTALL.md`.
- **Variant D ship candidate** — `HERMES-variantD.md` + `delegate_worker.py`. Superseded by r7.4's variantF / `delegate_worker_v2.py`.

## What Changed in r7

- **Cross-model tuning pass** — Applied six model-agnostic edits and three reframed principles from `PLAN-r7.md` to keep AgentFW aligned with Claude Opus 4.7 without regressing Opus 4.6, Sonnet 4.6, or GPT-5-tier models
- **Self-verification vs. self-review clarifier** — Clarifier sentence in the Self-Review anti-pattern distinguishing model-provided intrinsic pre-flight checks from prohibited self-review-as-judge
- **Explicit fan-out instruction** — Worker-dispatch guidance now says "spawn N workers in parallel" literally when decomposing across independent items, counters "fewer subagents by default" tendencies
- **Quote-before-act on state files** — Worker prompts include the exact PROGRESS.md line(s) being acted on; workers echo them in returned artifacts
- **Cadence annotation for the 3-task health gate** — Documents why cadence is held pending empirical degradation-curve data rather than loosened on long-context retrieval scores
- **Model-family knobs (non-binding) subsection** — Bounded ≤25-line subsection at the end of `references/prompt-design.md` with three reframed principles and inline `(Anthropic Opus 4.7: …)` sidenotes for reasoning effort, judge deliberation, and token budgets
- **Reference-file audit** — Removed vague generalizations ("and similar," "etc.," "or equivalent") from rule-bearing text across references
- **Known gaps** — Phase 0 multi-model probe was run at reduced scope (6 of 28 cells); full-scope baseline pending human-driven runs for GT-2/4/6/7 and access to Opus 4.6 and GPT-5.4-Pro. Sonnet-4.6-specific tuning notes parked in `ADDENDUM-sonnet-4-6.md`

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
- **r7.1** (2026-04-18): Hermes-variant initial probe sweep (numbers later corrected by r7.2 strict re-tally)
- **r7.2** (2026-04-18): Dense vs MoE A/B + strict on-disk re-tally that corrected r7.1's inflated headline; Variant E ship-candidate status withdrawn
- **r7.3** (2026-04-18/19): Layer 1+2 remediation attempt (toolset restriction + escape-hatch removal) — FAILED dispatch thresholds (1/15 both models); diagnosis led to β-fuse design
- **r7.4** (2026-04-19): β-fuse structural dispatch (`delegate_worker_v2` with classification as a required argument) — SHIP-WITH-CAVEAT for dispatch layer; MoE 17/20, dense 77% measured, 11.5×–17× lift over r7.3 baseline
- **r7.5** (2026-04-19): Hermes pre-release — turn-0 toolset restriction + SIGTERM mitigation + worker-quality ship gate measurement. HOLD-narrow verdict: dispatch thesis intact, worker-quality gate failed (3/20 vs 15/20 floor), tracked as r7.6 scope
- **r7.6–r7.10** (2026-04-20 → 2026-04-25): Hermes worker-quality / decomposition campaign — explored child-side interventions, then pivoted to parent-decomposition via `write_plan_md` minimum-mechanism (CEILING FINDING: tool-description teaching reaches the parent reliably; r7.10 budget-n10 + n5 found 0/25 strict completion content-verified, surfacing the synthesis-trust gap that motivated r7.11)
- **r7.11** (2026-04-26 → 2026-04-30): Hermes internal RC — verified-state multi-session resumable architecture with execution-tier acceptance verification (tier 3.7). Item 9 n=5: 3/5 strict completion on T6 (cleared pre-committed RC threshold). 0/5 trials reproduced the trial-3 failure mode. Tag `hermes-r7.11-rc1`
