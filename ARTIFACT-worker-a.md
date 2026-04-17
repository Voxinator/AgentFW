# AgentFW Model-Sensitive Surface Map
**Revision:** r6 (2026-04-10)
**Agent:** Worker A (Research)
**Date:** 2026-04-17

---

## One-Paragraph Recap

AgentFW r6 is a prompt firmware that installs standing instructions (Markdown) to transform single-turn LLMs into structured agents operating via Decompose→Parallelize→Verify→Iterate cycles, with explicit Planner-Worker-Judge role separation, permission tiers, and structural enforcement gates. The r6 tagline: "Context degradation resistance via Critical Rules preamble, state-driven health gates, and mandatory delegation self-checks."

---

## Model-Sensitive Surfaces (27 items)

### Core Behavioral Enforcement

1. **File: `core/harness-core.md`, Section: "CRITICAL RULES"**
   - **Text:** Five numbered imperative rules (CLASSIFY, NO ROLE COLLAPSE, NO SELF-VERIFY, CHECK PROGRESS.md, DECOMPOSE) placed at the very top, before all other content.
   - **Why model-sensitive:** Early behavioral drift in long contexts causes models to forget or deprioritize later instructions. Critical Rules are front-loaded and use imperative framing ("no exceptions," "regardless of context consumed") designed to survive attention deprioritization. Model attention gradients determined this placement strategy.

2. **File: `core/harness-core.md`, Section: "Task Delegation Decision Tree — MANDATORY: Classification Gate"**
   - **Text:** Agent MUST output `[TASK CLASS: one-shot | structured | long-horizon]` before any work. Omitting is a protocol violation.
   - **Why model-sensitive:** Models skip implicit gates (advisory instructions) but stumble over explicit mandatory output markers. The `[TASK CLASS]` block is a hard procedural step that's harder to elide than a "you should classify" recommendation. Observation: r5 tested this gate; r6 made it mandatory based on failure analysis.

3. **File: `core/harness-core.md`, Section: "One-shot" criteria**
   - **Text:** One-shot applies ONLY when zero files modified OR (exactly one file modified AND <20 lines AND no cross-file dependencies).
   - **Why model-sensitive:** Models are optimistic about their ability to one-shot. Without tight criteria, they trigger the harness even on simple tasks. The <20-line threshold emerged from evaluation: below it, models reliably avoid overcomplication; above it, they create unnecessary plans. The cross-file dependency clause catches hidden coupling.

4. **File: `references/state-management.md`, Section: "Context Health Gate"**
   - **Text:** After 3 tasks reach completed/verified, agent performs health check: reads PROGRESS.md, self-assesses against Critical Rules, outputs `[CONTEXT HEALTH: OK/DEGRADED]` with evidence.
   - **Why model-sensitive:** Models lose instruction adherence as context grows. Rather than relying on memory ("remember to verify"), this gate fires based on observable state (task count in PROGRESS.md). The state-driven trigger resists context degradation better than advisory reminders. Modifying the "3 tasks" threshold would be the first tuning lever for a model with different degradation curves.

5. **File: `references/state-management.md`, Section: "Delegation Self-Check"**
   - **Text:** Before writing implementation code, agent checks role, verifies worker dispatch exists, states reason if not delegating.
   - **Why model-sensitive:** Models slip into "I already have context, I'll just code" mode under context pressure. Procedural self-check (observable state check: "is a worker assigned?") is harder to skip than advisory ("you should delegate").

### Role Separation & Verification

6. **File: `core/harness-core.md`, Section: "Planner-Worker-Judge Architecture — HARD RULE: Role Separation"**
   - **Text:** Main session must never collapse planner, worker, judge. Strict separation enforced: main=planner+judge dispatcher, workers=sub-agents for implementation, judge=separate sub-agent.
   - **Why model-sensitive:** Models naturally try to be "efficient" by doing everything in one context. Without structural gates, this is the default. The hard-rule framing and role-mapping are reactions to observed self-review failures where models checked their own code against their own assumptions.

7. **File: `core/permissions.md`, Section: "Trust Tiers"**
   - **Text:** Three tiers (always-allow, ask-first, never-allow) with no fourth tier. If unsure, default to ask-first.
   - **Why model-sensitive:** Models have different tendencies to perform risky operations. Some models require explicit permission boundaries; others need default-deny semantics. The "no fourth tier" and "default to ask-first" clauses close edge cases where models try to invent intermediate tiers.

8. **File: `references/verification-tiers.md`, Section: "Tier 1: Machine-Checkable"**
   - **Text:** Tasks cannot transition completed→verified without machine-check output (build log, test output). Reasoning-only is not Tier 1 verification.
   - **Why model-sensitive:** Models are overconfident in code correctness without execution. They reason well but skip execution. This rule enforces execution; the "must be recorded in PROGRESS.md" requirement ensures the artifact is visible, not just claimed.

9. **File: `references/domain-guidelines.md`, Section: "Compiled Languages"**
   - **Text:** Judge MUST execute build as first step. Build output in verification artifact. "Build verification is non-negotiable."
   - **Why model-sensitive:** Models reviewing C++ code without building are confident in their reasoning but miss linker errors, template issues, etc. The non-negotiable language is reaction to r5 failure (UE5 project with 3 unverified implementation steps). Some models require this enforcement more than others.

10. **File: `references/domain-guidelines.md`, Section: "Long-Running Services"**
    - **Text:** Worker/judge MUST restart service after code changes. "A code change to a running service that hasn't been restarted has not been deployed."
    - **Why model-sensitive:** Models assume code changes propagate without action. This rule explicitly closes the "apply code change but forget to restart" failure mode, which is common across many model behaviors.

### State Machine & Task Tracking

11. **File: `references/state-management.md`, Section: "Task State Machine"**
    - **Text:** State machine: planned→dispatched→in-progress→completed→verified→failed. Downstream tasks cannot dispatch against unverified dependencies.
    - **Why model-sensitive:** Models lose track of task status without explicit state. The six-state machine (not two-state) exists because collapsing any state caused evaluation failures. The "completed≠verified" distinction is hardened because models treat "done" as "correct" without separation.

12. **File: `references/state-management.md`, Section: "Verification Gates"**
    - **Text:** Task with dependencies on unverified tasks MUST NOT be dispatched. Hard gate.
    - **Why model-sensitive:** Models are eager to parallelize or proceed sequentially without waiting for verification. This gate prevents cascading failures from unverified earlier tasks.

13. **File: `references/state-management.md`, Section: "Staleness Detection"**
    - **Text:** Any task at `completed` >1 planner cycle without judge dispatch = verification gap. Must be acknowledged and either addressed or risk-documented.
    - **Why model-sensitive:** Models naturally move on after a worker completes, delaying verification. Staleness detection forces explicit decision: verify now or document deferred risk. The "one planner cycle" threshold is tunable per model behavior.

### Permission & Scope

14. **File: `core/permissions.md`, Section: "Worker Scope Constraints"**
    - **Text:** Every worker dispatch includes explicit scope: allowed paths (read+write), allowed operations, forbidden operations, side-effect budget.
    - **Why model-sensitive:** Without scope, workers take on too much (refactoring beyond task, changing configs). Explicit scope declarations are behavioral anchors. The forbidding-operations list is especially important—models need to be told what NOT to do, not just what to do.

15. **File: `core/permissions.md`, Section: "Escalation Protocol"**
    - **Text:** Workers STOP and report when out-of-scope, not proceed-and-ask-forgiveness.
    - **Why model-sensitive:** Models' default is to be helpful and continue ("I know this is out of scope but I'll do it anyway"). The "STOP" caps-lock and explicit protocol changes that behavior.

### Anti-Patterns & Failure Prevention

16. **File: `references/anti-patterns.md`, "One-Shot Hero Mode"**
    - **Text:** Trying to solve everything in single response. "If you feel the pull to just do it all at once—that's the signal to decompose."
    - **Why model-sensitive:** This is the baseline failure mode of LLMs. The named anti-pattern makes it recognizable. Models can internalize "One-Shot Hero Mode" as a failure signal in a way they can't internalize abstract warnings.

17. **File: `references/anti-patterns.md`, "Role Collapse"**
    - **Text:** Main session drops into worker mode because it "already has context." The phrase "I'll Just Do It Myself Trap" and the comparison to a developer merging their own PR.
    - **Why model-sensitive:** Models are highly confident when they have context. The "developer merging own PR" analogy provides external validation that this is wrong, not just a framework rule.

18. **File: `references/anti-patterns.md`, "Self-Review"**
    - **Text:** Same context writes code and verifies it. Context will check for intended behavior, not actual behavior.
    - **Why model-sensitive:** Models' self-review bias is well-documented. Explicitly naming it and explaining why (checks intent vs. reality) addresses the root issue.

19. **File: `references/anti-patterns.md`, "Rubber-Stamp Compliance"**
    - **Text:** Protocol markers (`[TASK CLASS]`, `[CONTEXT HEALTH: OK]`) output without genuine assessment. "Bare markers are a violation."
    - **Why model-sensitive:** r6 addition addressing observation that models output markers without performing underlying work. Explicit rule that evidence must accompany markers closes this loophole.

### Observability & Logging

20. **File: `references/observability.md`, Section: "EVENT TYPES"**
    - **Text:** 12 event types logged to SESSION_LOG.md: SESSION_START, PLAN_CREATED, WORKER_DISPATCHED, WORKER_COMPLETED, JUDGE_DISPATCHED, JUDGE_VERDICT, ERROR, RESTART, PERMISSION_CHECK, CONTEXT_HEALTH_CHECK, SESSION_END.
    - **Why model-sensitive:** Structured logging resists model forgetting. Events are facts written to disk, not memory-based tracking. The specific event types (CONTEXT_HEALTH_CHECK is r6-new) track what models tend to forget.

21. **File: `references/observability.md`, Section: "When to Log"**
    - **Text:** Autonomous mode: always, required. Guided multi-step: strongly recommended. Simple: optional. Multi-session: required.
    - **Why model-sensitive:** Models' logging discipline varies by autonomy level. Explicit requirements per mode override per-model defaults.

### Context Budget & Reference Loading

22. **File: `core/harness-core.md`, Section: "Reference Loading Protocol"**
    - **Text:** Core always loaded (~175 lines). Everything else on-demand by condition (multi-step → state-management, autonomous → observability, errors → error-recovery, etc.).
    - **Why model-sensitive:** Context budget is the binding constraint on model behavior. The ~175-line core is tuned to fit alongside real conversation; larger cores cause the harness to crowd out domain content. Larger models might tolerate bigger cores; smaller models require tighter constraints. The 175-line threshold is model-sensitive.

23. **File: `references/prompt-design.md`, Section: "Context Budget for Sub-Agents"**
    - **Text:** 500 lines of relevant context outperforms 2000 lines of mixed context. Workers receive curated context only—exclude full framework, other tasks, previous workers' reasoning.
    - **Why model-sensitive:** Shorter context windows and models with lower signal-to-noise ratios need tighter filtering. The 500-vs-2000 comparison is empirical but would shift for different model types.

24. **File: `references/prompt-design.md`, Section: "Judge Shielding"**
    - **Text:** Judge receives only requirements + system state + verification criteria. NOT worker's implementation plan or reasoning.
    - **Why model-sensitive:** Judge shielding prevents assumption-carrying. Models that inherit too much context from workers repeat the worker's mistakes. This is the second-order effect of role separation.

### Evaluation & Iteration

25. **File: `evaluation/golden-tasks.md`, "GT-1: Trivial Request"**
    - **Text:** Simple knowledge question ("What's the difference between a list and a tuple?") should NOT activate harness. Pass: direct answer. Fail: create PLAN.md.
    - **Why model-sensitive:** Over-activation (false positives) is the inverse failure of under-activation. Some models are more trigger-happy on harness activation. This test calibrates the threshold.

26. **File: `evaluation/golden-tasks.md`, "GT-6: Late-Session Delegation"**
    - **Text:** Multi-phase test: Phase 1 (context loading) vs. Phase 2 (late-session test). Pass: delegation quality comparable. Fail: role collapse under context pressure.
    - **Why model-sensitive:** This is the core r6 test. Different models degrade at different context lengths. Phase 1 vs. Phase 2 degradation gradient is model-dependent. A model with better long-context performance might pass this; one with sharper degradation might fail.

27. **File: `evaluation/golden-tasks.md`, "GT-7: Context Health Gate Activation"**
    - **Text:** After 3rd task, health gate fires. Must read PROGRESS.md, output evidence-backed `[CONTEXT HEALTH]` marker. Bare marker = rubber-stamp violation.
    - **Why model-sensitive:** The "3 tasks" threshold for health gate trigger is tunable. A model with better context stability might lengthen this; one that degrades faster should shorten it. This is the Opus 4.7-specific tuning dial.

---

## Assumed Model Behavior Profile

AgentFW r6 encodes assumptions about the underlying model's weaknesses:

1. **Attention degradation over context:** Core rules placed at top; state-driven gates (PROGRESS.md task count) trigger more reliably than advisory instructions. Assumption: model's instruction-following decays as context fills, but file-reading remains reliable.

2. **Optimism bias on one-shotting:** Models are overconfident in one-shot ability. Classification gate and <20-line one-shot threshold are structural blocks. Assumption: models will attempt hero-mode without guardrails.

3. **Role collapse under context pressure:** When a model has context for a task, it tries to implement it directly rather than dispatch. Delegation self-check and role-separation hard rules react to this. Assumption: efficiency pull is strong; role discipline needs procedural enforcement, not advisory.

4. **Self-review blindness:** Models verify code against their own assumptions, not requirements. Judge shielding and fresh-context verification enforce external evaluation. Assumption: single-context verification is systematically unreliable.

5. **Task state tracking loss:** Models lose track of which tasks are verified vs. completed. Explicit state machine with 6 states (not 2) enforces precision. Assumption: memory-based tracking fails; file-based state is more reliable.

6. **Risky operations without approval:** Models take destructive actions without explicit permission. Three-tier model (always-allow, ask-first, never-allow) with no fourth tier and "default to ask-first" close gaps. Assumption: models need narrow permission boundaries.

7. **Verification skipping under pressure:** Models skip machine-checkable verification (building code, running tests) when they're confident in reasoning. Tier 1 enforcement + domain-specific verification rules (build for C++, tests for Python, restart for services) force execution. Assumption: reasoning-only verification is insufficient.

8. **Procedural marker pollution:** Models output markers (`[TASK CLASS]`, `[CONTEXT HEALTH: OK]`) without performing underlying work. Rubber-Stamp Compliance anti-pattern and evidence-requirement clauses close this. Assumption: markers are cheap; models produce them without backing.

9. **Context accumulation pathology:** Long sessions accumulate errors invisibly. Late-discovery error protocol, error-recovery restarts, and fresh-context doctrine address this. Assumption: accumulated context carries accumulated assumptions; clean restart beats patching forward.

10. **Verification gap invisibility:** Unverified tasks proceed unnoticed. Staleness detection, verification gates, and health checks make gaps visible. Assumption: models need explicit prompting to notice missing verification.

---

## Tuning Dials for Opus 4.7

If behavioral data for Opus 4.7 becomes available, these knobs are actually tunable vs. architectural:

### Tunable Thresholds
- **"3 tasks" for health gate trigger** (state-management.md): If Opus 4.7 exhibits slower degradation (long-context stability), increase to 4-5. If faster, decrease to 2. This is the lowest-friction tuning dial.
- **"<20 lines" for one-shot threshold** (core): Models with better code understanding might handle 30-40 lines; those with worse understanding might require <10.
- **Context health gate firing cadence:** Currently after every 3 completed/verified tasks. Could be adjusted to after every N tokens of context consumed, or every M new turns (if Opus 4.7 provides token usage data).

### Tunable Prompt Wording
- **Critical Rules preamble imperatives:** Framing ("no exceptions," "regardless of context consumed") is tunable. Opus 4.7-specific language might be more effective if it maps to the model's training distribution.
- **Permission tier defaults:** Currently "when unsure, default to ask-first." If Opus 4.7 shows different default behavior (more conservative or more aggressive), rephrase the tier descriptions to match its natural tendency and correct for differences.
- **Anti-pattern names and comparisons:** "One-Shot Hero Mode," "developer merging own PR"—these are culturally anchored. Opus 4.7-specific analogies might resonate differently. The names themselves are tunable surface area.

### Tunable Gate Placement
- **Classification gate location:** Currently before all work. Opus 4.7 might benefit from repeating the gate mid-task if degradation is sharper. This is architectural but could be customized per model.
- **Delegation self-check trigger:** Currently "before writing implementation code." Opus 4.7 might need broader triggers ("before any edit operation," "before reading task-specific files") if its role-collapse pattern is subtly different.
- **Judge shielding specificity:** Currently "exclude worker's plan and reasoning." Opus 4.7 might need "also exclude the planner's framing" or vice versa. The granularity of shielding is tunable.

### Tunable Default Tool Choices
- **Worker dispatch mechanism:** Currently "dispatch sub-agent." Opus 4.7 on Claude Code uses specific dispatch syntax. If Opus 4.7 has better long-context performance with interleaved subtasks vs. separated agents, this default could change.
- **Verification method priorities:** Currently "machine-check first, then expert-check." Opus 4.7's machine-checking accuracy might allow "expert-check first, spot-check with machines" for Tier 2 work.

### NOT Tunable (Architectural)
- **Role separation principle:** Fundamental to avoiding self-review bias. Doesn't become negotiable for any model.
- **State machine structure:** Six states exist because collapsing any caused failures. The distinction between completed and verified is load-bearing.
- **Verification tier system (Tier 1 vs. Tier 2):** The need for external machine-checked verification is architectural, not model-dependent.
- **Permission tiers (always-allow, ask-first, never-allow):** Three-tier model is architectural. No renegotiation based on model.
- **Fresh context on structural error:** The iterate-with-fresh-context doctrine is core, not tunable. All models need this.

---

## Known Eval Signal: Results 2026-04-06

The most recent evaluation file (evaluation/results-2026-04-06.md) reports:

| Task | Version | Result |
|------|---------|--------|
| GT-1: Trivial Request | r5 | PASS |

This is a single data point (only GT-1 tested on r5). The file shows the evaluation infrastructure is in place but not yet comprehensive. GT-2 through GT-7 results are not yet recorded—these are regression tests designed to be run after each major change. For r6, the new tests (GT-6: Late-Session Delegation and GT-7: Context Health Gate) are the canary tests for context degradation resistance.

Implication: **If Opus 4.7 evaluation were conducted, GT-6 and GT-7 would be the highest-signal tests.** GT-6 directly tests whether Opus 4.7 maintains delegation discipline under context pressure (the core r6 improvement). GT-7 tests whether the health gate fires and produces genuine assessment (resistance to rubber-stamping). A full Opus 4.7 eval should run all 7 golden tasks to establish baseline, then periodically re-run GT-6 and GT-7 as sensitivity tests for context-window tuning.

---

## Summary Table: Surfaces by Category

| Category | Count | Key Files |
|----------|-------|-----------|
| Core Enforcement | 5 | harness-core.md |
| Role Separation & Verification | 5 | harness-core.md, permissions.md, domain-guidelines.md |
| State Machine & Tracking | 3 | state-management.md |
| Permission & Scope | 2 | permissions.md |
| Anti-Patterns | 4 | anti-patterns.md |
| Observability | 2 | observability.md |
| Context Budget | 3 | harness-core.md, prompt-design.md |
| Evaluation | 3 | golden-tasks.md |
| **TOTAL** | **27** | — |

---

**End of Artifact**
