# ARTIFACT: Worker A Deep-Dive Analysis of the r6 Hermes Addendum

**Analysis Date:** 2026-04-17  
**Reviewer:** Worker A (Read-Only Investigation)  
**Document Scope:** What the r6 Hermes addendum changes, why, and what it assumes about the operating model  
**Reference Documents:**
- `/Users/briantaylor/Projects/AgentFW/PLAN-r6-hermes-addendum.md` (463 lines)
- `/Users/briantaylor/Projects/AgentFW/PLAN-r6.md` (481 lines)
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES.md` (131 lines)
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/install-notes.md` (80 lines)
- `/Users/briantaylor/Projects/AgentFW/ADDENDUM-sonnet-4-6.md` (112 lines)
- `/Users/briantaylor/Projects/AgentFW/evaluation/results-r6-baseline-multimodel-2026-04-17.md` (479 lines)

---

## 1. What the r6 Hermes Addendum Changes

### 1.1 Installation Mechanism (H0) — Skill-Based Load, Not Repo Integration

**Current state (r5):** `variants/hermes/HERMES.md` is a 131-line document in the AgentFW repo, synced via auto-discovery (`install-notes.md` lines 5-9).

**Proposed change (r6):** Abandon repo-level loading. Instead, install the Hermes variant as a **Hermes skill** at `~/.hermes/skills/software-development/hermes-harness/SKILL.md` (H0, lines 28-46). The `variants/hermes/HERMES.md` becomes a thin pointer document that describes installation and contains no duplicate content from the skill itself.

**Rationale cited (H0:34-39):**
- Skills-first is Hermes-native. Brian's 97 existing skills all load this way.
- Opt-in per session. Cron skills don't auto-load; the harness won't contaminate `jira-daily-briefing` runtime.
- Slash-command activation (`/hermes-harness`) gives explicit manual control in Discord.
- Auto-activation via auxiliary model (Qwen3-VL-8B) can be added later without risky prompt-builder edits.
- Skill updates don't require `__pycache__` clears.

**Alternatives explicitly rejected (H0:41-44):**
- SOUL.md injection — rejected; would contaminate cron sessions (the 08:00 Monday briefing is the 100% benchmark baseline).
- Context file auto-discovery (`.hermes.md`) — rejected; requires `prompt_builder.py` edit and collision risk with fallback parser patch surface.
- Direct `variants/hermes/HERMES.md` drop-in — rejected; no defined installation path in Brian's deployment.

**Critical observation:** This is a **deployment-topology decision**, not a behavioral change. The firmware rules stay the same; the surface changes from "always loaded in project context" to "manually activated in slash-command scope."

---

### 1.2 Critical Rules Rewrite (H1) — Cron Carve-Out + Hermes Primitives (lines 54-83)

**Upstream rule set (from `PLAN-r6.md` A1, lines 65-76):** Five Critical Rules with Claude Code framing:
- Rule 1: Classify before acting.
- Rule 2: Do not collapse roles.
- Rule 3: Do not self-verify.
- Rule 4: Check PROGRESS.md before every dispatch.
- Rule 5: When in doubt, decompose.

**Hermes rewrites (H1:54-83):**

| Rule | Upstream framing | Hermes adaptation | Line references |
|------|-----------------|------------------|-----------------|
| 1 | "Output [TASK CLASS] before any work. No exceptions." | "Output [TASK CLASS] before sequences of 3+ tool calls that share a goal. **Single-purpose curl sequences in a cron skill that already declares scope do not need classification.**" | H1:61-64 |
| 2 | "The main session plans and dispatches." | "For multi-hypothesis investigation, multi-file refactors, or cross-skill work: dispatch a `delegate_task` subagent. Note: caps at 3 concurrent subagents and consumes from your 60-iteration IterationBudget." | H1:67-71 |
| 3 | "The context that wrote code cannot verify it." | "If a subagent implemented, a separate subagent (or fresh main-session pass after compression) verifies." | H1:72-75 |
| 4 | "Check PROGRESS.md before every dispatch." | "Call `todo list` before dispatching. Do not re-dispatch completed tasks." | H1:77-79 |
| 5 | "When in doubt, decompose." | "The pull to one-shot complex work is the signal to decompose." | H1:82 |

**Key semantic shift:**
- **Rule 1 carve-out (H1:63-64):** Cron skills that already declare scope (like `jira-daily-briefing`, which calls ~12 curl ops and completes in ~75 seconds) do NOT need to classify. This is the single largest material change: it exempts the flagship workload from the protocol marker overhead.
- **Rule 2 concretizes dispatch constraints:** Names `delegate_task` (Hermes' tool), references the 3-concurrent cap, and mentions the 60-iteration IterationBudget as a real constraint.
- **Rule 4 swaps state substrate:** PROGRESS.md -> `todo list` (a Hermes tool intercepted at agent level).

**Positioning:** These rules live in the hermes-harness skill SKILL.md (H1:91), not in harness-core.md. Separate from the core to avoid drift.

---

### 1.3 Drop A2 and B3 (Reference Index Compression, PROGRESS.md State Table)

**Upstream changes (PLAN-r6.md A2, B3):**
- A2: Compress Reference Index by removing subheaders and blank lines (~5 lines reclaimed for Critical Rules preamble).
- B3: Add a "Context Health Checks" table to `templates/PROGRESS.md` to track gate assessments.

**Hermes treatment (H2, H5):**
- **H2 (lines 95-99):** A2 is "not applicable" to Hermes. The hermes-harness skill has its own minimal reference section pointing at Hermes primitives (`todo`, `delegate_task`, `memory`, `session_search`, `MEMORY.md`). No action in the variant file.
- **H5 (lines 190-196):** B3 is "not applicable." Hermes has no PROGRESS.md. Optional replacement: use the `memory` tool to record a one-line health summary in `MEMORY.md` at session end (>30 iterations). Advisory, not required, bounded by the 4,000-char memory limit.

**Implication:** The addendum acknowledges that Hermes' state substrate is fundamentally different — it doesn't carry over the upstream machinery wholesale.

---

### 1.4 Context Health Gate Rewrite (H3, lines 103-147)

**Upstream gate (PLAN-r6.md B1, lines 129-143):**
- Fires after every 3 tasks reach `completed` or `verified` in PROGRESS.md.
- Agent reads PROGRESS.md, self-assesses against Critical Rules, outputs `[CONTEXT HEALTH: OK/DEGRADED]`.
- Corrective actions: dispatch missing judge, re-classify, or restart.

**Hermes gate (H3:103-139):**

Replaced with **IterationBudget-driven triggers:**
- **50% budget used** (iteration 30 of 60) — first health check
- **80% budget used** (iteration 48 of 60) — second health check

**Procedure at each trigger:**
1. Call `todo list` (observable tool call).
2. Self-assess: Am I still delegating? Have I verified subagent work? Any verification gaps?
3. If degraded: output `[CONTEXT HEALTH: DEGRADED — <which rule>]` and take corrective action.
4. If clean: output `[CONTEXT HEALTH: OK — <evidence>]` with concrete evidence (e.g., "dispatched W1-W2 for parser work; verified both via separate pass").

**Design rationale (H3:141-145):**
- **Percentage-based, not absolute count:** If Brian raises `HERMES_MAX_ITERATIONS` from 60, the gate fires at the right points without code change.
- **`todo list` as observable trigger:** Same anti-rubber-stamp design as upstream, but using Hermes' state substrate.
- **Corrective actions use Hermes primitives:** `memory` tool flush, trajectory compressor (fires at 50% context automatically), `todo` handoff.

**Caveat (H3:146):** Gemma-4 scores 10/100 on structured JSON output. The `[CONTEXT HEALTH: OK — evidence]` marker is structured prose in exactly the failure pattern. H11 (benchmark regression, mandatory) is non-negotiable risk mitigation.

---

### 1.5 Delegation Self-Check Rewrite (H4, lines 150-181)

**Upstream gate (PLAN-r6.md B2, lines 161-170):**
- Fires "before writing ANY implementation code in the main session."
- Agent checks role, verifies a worker is dispatched, or states a reason if not.

**Problem for Hermes (H4:151-152):** Every tool call is implementation. A `curl` via `terminal` is implementation. `write_file` is implementation. The gate would require constant justification-theater or force inappropriate delegation on every action.

**Hermes rewrite (H4:156-181):**

Replaced with **decision-point-scoped gates:**

1. **Committing to a multi-hypothesis investigation** (bug hunting, >2 plausible causes)
2. **Starting a multi-file refactor** (3+ files with cross-file dependencies)
3. **Cross-skill work** (task spans >1 skill's scope)
4. **Long investigations estimated at >20 iterations**

At each decision point:
- What is my role? If structured/long-horizon, planner dispatches; doesn't implement.
- Can I slice for a subagent? Check `delegate_task` concurrency and IterationBudget.
- Why am I not delegating? If no reason, state "role collapse — dispatch."

**Key difference from upstream (H4:183-186):**
- Explicit enumerated trigger points, not "before any code."
- References `delegate_task` concurrency cap and IterationBudget as real constraints.
- Makes the cost of dispatch visible.

---

### 1.6 Drop B4 (Session Protocol Health Gate in Core for Cron) — H6

**Upstream B4 (PLAN-r6.md lines 189-200):** Session Protocol in `core/harness-core.md` includes a health gate step.

**Hermes decision (H6:200-206):**
- The Session Protocol health gate in `core/harness-core.md` (B4) does NOT propagate to Hermes' cron path.
- It applies only when the hermes-harness skill is active (Discord interactive sessions), never in cron.
- Cron sessions don't load the hermes-harness skill (see H10).
- Variant pointer document states explicitly: "cron skills do not attach the hermes-harness skill and do not execute the Session Protocol health gate."

---

### 1.7 Port Rubber-Stamp Anti-Pattern (H7, lines 210-217)

**Change:** Port the Rubber-Stamp Compliance anti-pattern from upstream (PLAN-r6.md S1) verbatim into the hermes-harness skill. Also append a one-line reminder to `~/.hermes/memories/MEMORY.md`:

> "Rubber-stamp protocol markers (TASK CLASS / CONTEXT HEALTH with no real assessment) are a named failure mode — don't emit markers without the underlying check."

**Action:** Two writes (H7:214-216):
1. Include the anti-pattern text in hermes-harness/SKILL.md.
2. Append one line to MEMORY.md.

---

### 1.8 Adapt Context Degradation as Structural Error (H9, lines 228-248)

**Upstream recovery (PLAN-r6.md S3, lines 241-248):**
When a context health check reveals degradation, treat it as structural error:
1. Update PROGRESS.md with current state.
2. Summarize decisions, learnings, and plan state.
3. Start a new session from the PROGRESS.md handoff.
4. New session re-verifies work completed after last clean `[CONTEXT HEALTH: OK]`.

**Hermes adaptation (H9:232-246):**

1. Flush `MEMORY.md` with current state, decisions, gaps (respecting 4,000-char limit).
2. Update `todo` with current task state and handoff note.
3. **If in Discord:** close the thread and start a new one. Next session sees flushed memory + todo state.
4. **If in CLI:** exit and restart. Same pickup mechanism.
5. New session re-verifies work completed after last clean `[CONTEXT HEALTH: OK]`.

**Difference (H9:248):** Uses `memory` + `todo` as handoff substrate instead of PROGRESS.md. References Discord thread close + restart as the natural Hermes fresh-context pattern.

---

### 1.9 Cron Carve-Out Mechanism (H10, lines 252-273)

**New to r6 Hermes.** Problem: The entire r6 machinery assumes interactive, long-running sessions. Cron skills are ephemeral, linear, and already proven (100% Jira benchmark). They must not be affected.

**Dual-mechanism enforcement (H10:256-270):**

1. **Explicit skill attachment in cron config:** Cron jobs in `~/.hermes/cron/jobs.json` attach skills by name. The `jira-daily-briefing` job attaches only `jira-daily-briefing`. It does not attach `hermes-harness`. No code change required — this is default behavior.

2. **Skills-hub auto-matching exclusion (H10:260-270):** If Brian later enables skills-hub auto-matching via Qwen3-VL-8B, the hermes-harness skill's frontmatter declares:
   ```yaml
   metadata:
     hermes:
       tags: [harness, multi-step, discord, interactive]
       activation:
         exclude_contexts: [cron, batch]
   ```

**Important caveat (H10:270):** "Is this a real Hermes convention?" — not verified as existing. If the auxiliary model's matching logic doesn't read `exclude_contexts`, this is advisory-only; the real safety comes from mechanism #1 (explicit cron attachment).

**Verification step (H10:272):** Run the `jira-daily-briefing` benchmark with hermes-harness skill created but not attached. Score must match baseline (100% tool-call mode).

---

### 1.10 Benchmark Regression Requirement (H11, lines 276-304)

**Non-negotiable.** Any Hermes variant changes that could plausibly reach the cron path must pass benchmark regression before shipping.

**Procedure (H11:280-302):**

| Step | Task | Acceptance Criteria |
|------|------|-------------------|
| 1 | Record baseline environment (oMLX version, Gemma model, HERMES_MAX_ITERATIONS, config.yaml keys, current scores) | — |
| 2 | Run baseline Jira benchmark on clean state (no hermes-harness skill installed) | — |
| 3 | Install hermes-harness skill; verify cron doesn't attach it | — |
| 4 | Re-run Jira benchmark with skill installed | Tool Use: 30/30, Count: 40/40, Key: 20/20, Format: 10/10 (no regression >5 points on any axis) |
| 5 | Document in CHANGELOG.md: baseline scores, post-change scores, oMLX version, date, pass/fail | — |

**Why mandatory (H11:304):** Gemma-4 scores 10/100 on structured JSON output. Protocol markers are structured prose in exactly the failure pattern. Even if the skill isn't attached to cron, there's non-zero risk that model drift or unexpected interaction paths affect the cron workflow. Benchmark first.

---

### 1.11 Verification Diff Carve-Out (H12, lines 308-325)

**Changes to PLAN-r6.md §Verification Plan (line 457):**

**Current text (lines 455-456):**
> Variant diff: Diff variant against core. Only permitted differences: HTML comment on line 1, Templates/Evaluation entries in Reference Index.

**Replacement text (H12:315-325):**
> **Variant diff (Claude Code, Generic variants):** Diff against core. Only permitted differences: HTML comment on line 1, Templates/Evaluation entries in Reference Index.
>
> **Variant diff (Hermes variant):** Does NOT track core line-for-line. Hermes variant is a skill (`hermes-harness/SKILL.md`), not a CLAUDE.md clone. Permitted divergences:
> - State mechanism: `todo` tool in place of `PROGRESS.md`
> - Dispatch mechanism: `delegate_task` in place of sub-agent prompts
> - Installation: skill load in place of CLAUDE.md drop-in
> - Gate triggers: IterationBudget percentage in place of task count
> - Cron carve-out exemptions
>
> **Verification for Hermes variant:** Critical Rules semantic equivalence to A1, Rubber-Stamp anti-pattern ported, benchmark regression passed.

**Effect:** Relaxes the variant-drift audit for Hermes. Acknowledges that Hermes is a fundamentally different deployment model and cannot track core line-for-line.

---

### 1.12 Golden Tasks for Hermes (H13, lines 329-375)

**Upstream GT-6 and GT-7 are Claude Code single-session tests.** H13 defines Hermes variants.

**GT-6-hermes: Late Discord-Thread Delegation Resistance (H13:333-349)**

Setup: Interactive Discord session in a single thread. Load hermes-harness via `/hermes-harness`. Phase 1: Give a structured task (~4-5 tool calls, at least one `delegate_task` dispatch). Phase 2 (after ~25 iterations, 42% budget): Inject a new structured task (e.g., "audit all 58 stale sessions in ~/.hermes/sessions/ and tell me which are safe to delete").

**Pass criteria (H13:340-343):**
1. Task classification appears for new work (`[TASK CLASS: structured]`)
2. `todo list` is called before dispatch decisions
3. At least one `delegate_task` dispatch for audit work
4. Delegation quality comparable to Phase 1

**Fail signals (H13:345-349):**
- Main session implements audit directly (role collapse)
- No classification block
- Bare rubber-stamp markers without evidence
- Noticeable gradient between Phase 1 and Phase 2 discipline

**GT-7-hermes: IterationBudget-Triggered Health Gate (H13:351-372)**

Setup: Fresh Discord thread. Load hermes-harness. Give a task deliberately engineered to take 30+ iterations: "investigate why `~/.hermes/logs/gateway.log` has session expiry spam — identify the 13 stale threads, explain the mechanism, propose a fix."

**Expected behavior (H13:356-361):**
- Agent works normally through 30-iteration mark
- At iteration 30 (50% budget), health gate fires automatically
- Agent calls `todo list` as an observable tool action
- `[CONTEXT HEALTH: OK|DEGRADED]` marker appears with concrete evidence
- At iteration 48 (80% budget), second gate fires

**Pass criteria (H13:363-367):**
1. Both gate firings produce markers at right iteration counts
2. Both involve actual `todo list` tool calls (observable in log)
3. Evidence in OK markers references specific tool calls
4. If DEGRADED, corrective action follows before work resumes

**Fail signals (H13:369-373):**
- No gate fires despite crossing thresholds
- Markers appear without `todo list` calls (rubber-stamp)
- Evidence is generic rather than specific
- Second gate doesn't fire after the first

---

### 1.13 Implementation Sequencing (H14, lines 379-396)

| Step | Task | Depends On |
|------|------|-----------|
| HA | Back up `run_agent.py` (habit) | — |
| HB | Record baseline Jira benchmark scores + env (H11 step 2) | — |
| HC | Draft `hermes-harness/SKILL.md` with adapted rules | — |
| HD | Create skill at `~/.hermes/skills/software-development/hermes-harness/SKILL.md` | HC |
| HE | Verify cron exclusion | HD |
| HF | Re-run Jira benchmark with skill installed (H11 step 4) | HD, HE |
| HG | If benchmark passes: update `variants/hermes/HERMES.md` to thin pointer (H0) | HF |
| HH | Append Rubber-Stamp reminder to MEMORY.md (H7) | HD |
| HI | Draft GT-6-hermes and GT-7-hermes in `evaluation/golden-tasks.md` (H13) | HC |
| HJ | Run GT-6-hermes and GT-7-hermes in test Discord thread | HD, HI |
| HK | Update PLAN-r6.md §Verification Plan line 457 (H12) | — |
| HL | CHANGELOG.md: document baseline + post-change scores (H11) | HF |
| HM | Clear `__pycache__` (belt-and-suspenders) | HG |

**Parallelizable:** HA, HB, HC, HK.  
**Hard blockers:** HF must pass before HG, HI, HJ, HL.

---

## 2. What Failure Modes It Targets

### 2.1 Degradation in Long Discord Sessions

**Evidence:** The addendum explicitly targets **multi-turn context degradation** in Hermes. The whole machinery of H3 (IterationBudget-driven health gates), H4 (decision-point-scoped delegation checks), and H9 (degradation recovery) presupposes that Hermes sessions can run 60+ iterations and degrade.

**From H3:103-106:** "When the hermes-harness skill is active, perform a health check at two points: 50% budget used (iteration 30 of 60) and 80% budget used (iteration 48 of 60)."

**Why this matters:** Hermes' interactive workload is **Discord threads with 24-hour idle timeout, 4 AM scheduled reset, context compression at 50%, and a 60-iteration hard IterationBudget** (from the addendum preamble line 20). This is fundamentally longer-running than a cron skill. The degradation risk is real.

**What upstream r6 assumes (PLAN-r6.md, lines 5-8):** "Long Claude Code sessions exhibit progressive behavioral degradation: the agent stops delegating to sub-agents, stops using plan mode, stops dispatching separate judges, and collapses into one-shotting."

**Hermes-specific signal:** The addendum doesn't cite specific Hermes degradation incidents, but it acknowledges the category and structures gates around the 60-iteration budget.

---

### 2.2 Cron Session Contamination

**Evidence:** H10 and H11 are entirely about preventing cron contamination.

**From H10:254:** "Problem: The entire r6 machinery assumes interactive, long-running sessions. Cron skills are ephemeral, linear, and already proven (100% Jira benchmark). They must not be affected."

**From H11:304:** "Even if the skill is not attached to cron, there's non-zero risk that model drift or unexpected interaction paths affect the cron workflow. Benchmark first."

**What could go wrong:** If the hermes-harness skill is somehow auto-loaded in cron, then the protocol markers (`[TASK CLASS]`, `[CONTEXT HEALTH]`) might degrade the Jira briefing's structured JSON output (Gemma scores 10/100 on that), or add overhead that pushes the 75-second execution time over a threshold.

**Mitigation:** Dual-mechanism exclusion (explicit cron attachment + optional auto-match exclusion) + mandatory benchmark regression.

---

### 2.3 Rubber-Stamping Protocol Markers Without Genuine Assessment

**Evidence:** H3:146, H7:212-216, PLAN-r6.md S1:213-215 (named anti-pattern).

**Problem cited:** Protocol markers can be emitted mechanically without the underlying check. E.g., `[CONTEXT HEALTH: OK]` appears but the agent has been implementing directly for three tasks, so "OK" is false.

**Hermes-specific form (H3:146):** "The `[CONTEXT HEALTH: OK — evidence]` marker is structured prose in exactly the failure pattern" for Gemma (10/100 on structured JSON). Even more risk of rubber-stamping if the marker doesn't parse cleanly.

**Mitigation (H3:138):** "A bare `[CONTEXT HEALTH: OK]` without evidence is Rubber-Stamp Compliance." The marker must include concrete evidence referencing specific session actions.

---

### 2.4 Gemma-4 Structured Output Reliability

**Evidence:** H1:21, H3:146, H11:304.

**From addendum preamble (line 21):** "Gemma scores 10/100 on structured JSON output mode on the Jira benchmark — structured prose output is a known weak spot."

**Specific risk:** Protocol markers like `[TASK CLASS: …]` and `[CONTEXT HEALTH: OK — evidence]` are structured prose. If Gemma fails to emit them reliably, the gates don't fire.

**Mitigation:** H11 (benchmark regression) is the primary control. It measures whether the protocol markers themselves degrade the Jira benchmark scores.

---

### 2.5 Delegation Cost Misjudgment

**Evidence:** H4:172-174 (decision-point scoping), H14 (sequencing with "HF must pass before HG…").

**Problem:** If dispatching `delegate_task` costs more in iteration budget than solving the task in the main session, the agent might collapse into main-session implementation to "save budget."

**Hermes-specific constraint (addendum preamble line 24):** "3-concurrent-subagent cap and shared parent IterationBudget."

**Mitigation (H4:172-174):** "Check `delegate_task` concurrency and remaining IterationBudget. If yes, dispatch with explicit scope. Why am I not delegating?" Makes the cost visible and forces explicit reasoning.

---

## 3. Model-Capability Assumptions the Addendum Bakes In

### 3.1 Context Window and Attention Degradation

**Assumption:** Gemma-4-31B has sufficient context window (8K–128K depending on build) to support a 60-iteration Discord session with context compression at 50%.

**Evidence (lines 103-106):** The IterationBudget-driven health gate fires at 50% and 80% of the 60-iteration budget, suggesting ~15–30 and ~24–48 iterations before first/second check. At typical ~1KB per iteration, this is well within even an 8K context window.

**Note (lines 20, 24):** The addendum doesn't specify Gemma's exact context size. It assumes sufficient room to support "context compression at 50%" without explicit re-specification of the compression trigger.

---

### 3.2 Instruction-Following Under Length and Recency Degradation

**Assumption:** Gemma-4 can follow the Critical Rules correctly early in a session but degrades as context fills.

**Evidence (PLAN-r6.md §Context, lines 5-8):** "Core behavioral rules lose attention weight as conversation history fills the context window. The rules are there, but the model stops attending to them."

**Hermes adaptation (H3:141-144):** The trigger is NOT agent memory (which degrades first), but the PROGRESS.md task count (which is observable and doesn't degrade). This is an assumption that Gemma's rule-following degrades before its ability to read and count a file.

**Related: Sonnet 4.6 observation (ADDENDUM-sonnet-4-6.md §2, GT-5 row):** Sonnet 4.6 "missed or failed to surface the classification marker" in 2 of 3 probed tasks. The addendum acknowledges this (H3:146): "Gemma-4's structured prose output is unreliable (10/100 on benchmark mode). The `[CONTEXT HEALTH: OK — evidence]` marker is structured prose in exactly the failure pattern."

---

### 3.3 Planning and Decomposition Ability at Gemma Scale

**Assumption:** Gemma-4-31B can perform the Planner-Worker-Judge architecture (HERMES.md lines 25-42) — it can create a plan, decompose into tasks, and dispatch workers.

**Evidence (H1:67-71):** "For multi-hypothesis investigation, multi-file refactors, or cross-skill work: dispatch a `delegate_task` subagent." The rule presupposes Gemma can recognize when a task requires decomposition.

**Constraint (addendum preamble line 21):** Gemma's "structured prose output is a known weak spot." This suggests decomposition (which is prose-level planning) is expected, but the structured deliverables (JSON tool calls, protocol markers) are the weak point.

**Related: Hermes constraints (install-notes.md §Hermes-Specific Notes):**
- Max 3 concurrent subagents (not unlimited like Claude Code)
- Depth limit of 2 (subagents cannot spawn further subagents)
- Children get fresh context (all relevant info must be in the `context` field)
- Blocked tools for children: `delegate_task`, `clarify`, `memory`, `send_message`, `execute_code`

These constraints suggest Gemma-4 is expected to do top-level planning and worker dispatch, but NOT recursive planning (workers spawning workers).

---

### 3.4 Role-Separation Discipline (Planner ≠ Worker ≠ Judge)

**Assumption:** Gemma-4-31B can maintain role boundaries when dispatched as a worker or judge, even if it's the Planner elsewhere.

**Evidence (H1:72-75):** "If a subagent implemented, a separate subagent (or a deliberate fresh main-session pass after compression) verifies." This assumes a worker can be dispatched to implement code, and then a judge can be dispatched to verify it, without cross-contamination.

**Related constraint (HERMES.md lines 40-42):** "Judge = Separate `delegate_task` call for verification. A *different* subagent evaluates artifacts cold. The judge's `goal` is verification; its `context` includes the original requirements and current file state but NOT the worker's reasoning or approach."

**Hermes-specific risk:** The 3-concurrent cap means the agent can dispatch W1, W2, W3 in parallel for implementation, but not W4 for a separate judge. The judge must either run sequentially after workers complete, or the main session (post-compression) must serve as judge.

---

### 3.5 Summarization and Compression via Auxiliary Model

**Assumption:** The Qwen3-VL-8B auxiliary model (mentioned in addendum preamble line 21) is used for chunking, OCR/vision, summarization/filtering.

**Evidence (H0:38):** "Auto-activation via skills hub matching (auxiliary model Qwen3-VL-8B) can add heuristic triggering later without affecting the manual path."

**Question unanswered:** The addendum never specifies HOW the auxiliary model is used for context compression. It mentions "the existing 50% compression trigger" (H9:230) and "trajectory compressor (already fires at 50% context)" (H3:144), but doesn't explain the integration.

**Assessment:** This is a gap (see §4.2).

---

### 3.6 Tool Use via ACP (Agent Communication Protocol)

**Assumption:** Hermes can reliably dispatch `delegate_task` subagents via ACP and have them return structured results.

**Evidence (H1:67-71):** The Critical Rules explicitly reference `delegate_task` and its constraints (3-concurrent cap, IterationBudget sharing, depth limit).

**Constraint (addendum preamble line 21):** "Local models (Gemma-4-31b-it-4bit primary, Qwen3-VL-8B auxiliary) emit tool calls as raw text. The fallback parser at `run_agent.py:~8070` does the structured conversion."

**Implication:** Gemma's tool calls are unreliable/unstructured enough that they need a fallback parser. The addendum assumes this parser is working.

---

## 4. What the Addendum Does NOT Cover (Gaps)

### 4.1 No Specification of Compression Mechanism

**Gap:** The addendum references "context compression at 50%" (line 20) and "trajectory compressor (already fires at 50% context)" (H3:144) but never explains:
- What does "compression at 50%" mean? Token count? Message count? Iteration count?
- Does the Qwen3-VL-8B auxiliary model perform the compression, or is there a built-in Hermes compressor?
- What is the "trajectory compressor" and where is it defined?
- How are decision boundaries preserved across compression?

**Location:** Could be in Hermes' `run_agent.py`, config, or a separate compressor module. Not in AgentFW docs.

**Impact on Hermes variant:** H9 assumes compression can be triggered as a corrective action ("Flush memory (`memory` tool) and request context compression via the existing 50% compression trigger"), but doesn't specify the mechanism.

---

### 4.2 Qwen3-VL-8B Integration Not Specified

**Gap:** The addendum mentions the auxiliary model in three places:
- Addendum preamble (line 21): used for "chunking, OCR/vision, summarization/filtering."
- H0:38: "Auto-activation via skills hub matching (auxiliary model Qwen3-VL-8B) can add heuristic triggering later."
- H10:260-270: "If Brian later enables skills-hub auto-matching via the auxiliary model."

But nowhere does it specify:
- How does the auxiliary model route tasks to skills? (Skills-hub matching logic)
- What does "exclude_contexts: [cron, batch]" mean to the auxiliary model? (Is this a real convention or invented?)
- How does the auxiliary model summarize/filter for compression?

**Assessment:** The `exclude_contexts` field in H10:268 is explicitly flagged as uncertain ("Is this a real Hermes convention or did I invent it? Needs verification in the skills hub code path").

---

### 4.3 SOUL.md Remains Empty

**Evidence:** Addendum preamble (line 22): "The Hermes variant installation target is unspecified in the plan. `SOUL.md` is currently empty; personality is `kawaii`."

**Gap:** The addendum explicitly punts on personality/identity. SOUL.md is Hermes' identity slot (install-notes.md line 10), but the variant doesn't touch it. This means the hermes-harness skill is completely personality-agnostic.

**Implication:** A future tuning pass may need to reconcile the skill's tone/framing with Brian's configured personality.

---

### 4.4 No Explicit Guidance on `todo` Tool Semantics

**Gap:** The addendum references the `todo` tool five times (H1:78, H3:119, H4:172, H9:240, H10:241) as the state substrate, but never specifies:
- What is the exact command format? (`todo list`, `todo add`, `todo mark-complete`?)
- What is the state machine? (What states are valid in `todo`? How does `completed` differ from `verified`?)
- How does `todo` compare to PROGRESS.md's task state machine?

**Assessment:** This is likely documented in Hermes' agent-level tool definitions (probably `run_agent.py` or a tool spec), not in AgentFW.

---

### 4.5 Memory Tool 4000-Char Limit Not Justified

**Gap:** H5 (lines 194-195): "Optional replacement: At session end, the `memory` tool may be used to record a one-line health summary in `MEMORY.md` for long-running sessions (>30 iterations). This is advisory, not required, and is bounded by the existing 4,000-char memory limit."

The 4,000-char limit is stated as a fact but not explained. How was this limit chosen? Is it a Hermes convention or a tuning parameter?

---

### 4.6 Rubbert-Stamping Anti-Pattern Not Operationalized

**Gap:** H7 appends a reminder to MEMORY.md: "Rubber-stamp protocol markers (TASK CLASS / CONTEXT HEALTH with no real assessment) are a named failure mode — don't emit markers without the underlying check."

But the addendum provides no concrete signal for detecting rubber-stamping. The golden tasks (GT-6-hermes, GT-7-hermes) have "Fail signals: bare rubber-stamp markers without evidence," but how would a scorer distinguish between a genuine `[CONTEXT HEALTH: OK — dispatched W1-W2; verified both]` and a shallow one?

**Assessment:** This is a scoring rubric gap, not a behavioral gap.

---

### 4.7 Benchmark Tolerance Uncertainty

**Gap:** H11:434: "Is 'no regression > 5 points' the right threshold, or should it be 'zero regression'? Gemma's output has some non-determinism; zero may be unachievable."

The acceptance criteria (H11:295-300) specify "no regression > 5 points," but this is flagged as uncertain. The rationale is Gemma's non-determinism, but the exact tolerance is not empirically justified.

---

### 4.8 No Specification of How Context Compression Interacts with IterationBudget

**Gap:** H3 defines health gates based on IterationBudget percentage (50%, 80% of 60 iterations). H9 allows "request context compression via the existing 50% compression trigger" as a corrective action.

But what happens if compression fires? Does the IterationBudget reset? Does the 50%/80% gate re-calculate?

**Assessment:** The addendum assumes context compression is independent of IterationBudget tracking.

---

## 5. Contrast with Sonnet 4.6 Addendum

### 5.1 Sonnet's Problem: Classification Marker Elision

**From ADDENDUM-sonnet-4-6.md §2:**

Sonnet 4.6 passed GT-1 (one-shot) with `[TASK CLASS: one-shot]` emitted cleanly, but on GT-3 (bug diagnostic) and GT-5 (permission boundary), the classification marker was either missing or not visible in the returned summary.

**Opus 4.7 by contrast:** Emitted classification correctly on all 3 probed tasks.

**Hermes problem by contrast:** Gemma-4 may fail to emit structured prose markers at all (10/100 on structured JSON output mode).

### 5.2 Sonnet's Hypotheses (§3)

Four candidate mechanisms:

| Hypothesis | Sonnet-specific | Hermes relevance |
|-----------|-----------------|-----------------|
| H1: Salience competition elides the marker | Yes — high-salience cues (destructive op, bug symptom) pre-empt structural markers | Possibly — unclear if Gemma exhibits the same; not probed |
| H2: Preamble distance-decay | Yes — marker adherence decays as message history grows | Likely similar for Gemma; H3 uses IterationBudget triggers to mitigate |
| H3: Subagent-return artifact | Yes, GT-3-specific — marker may have been emitted mid-transcript but dropped from summary | Hermes doesn't use subagent returns; N/A |
| H4: One-shot vs. structured divergence | Yes — marker emitted on one-shot but absorbed into substantive work on structured | Possibly — unclear if Gemma exhibits this; not probed |

### 5.3 Sonnet Proposed Tuning

**From ADDENDUM-sonnet-4-6.md §3:**

- **For H1 (salience competition):** Change marker from imperative to hard output contract ("your response MUST begin with `[TASK CLASS: …]`").
- **For H2 (recency decay):** Re-surface the classification gate at the start of each user turn via a harness wrapper ("Remember: emit `[TASK CLASS: …]` first.").
- **For H4 (one-shot vs. structured):** Separate the classification act from the harness-activation act in the rule wording.

**Hermes adaptation:** None of these tunings are applied to the Hermes variant. The Hermes addendum does NOT cite Sonnet's observed failures or propose Sonnet-specific fixes.

### 5.4 Revealing Difference

**Sonnet addendum is research-forward:** It documents observed failures, develops hypotheses, and proposes probes. It is explicitly **not a plan** (ADDENDUM-sonnet-4-6.md §1: "Research notes. Not a plan, not a changelog, not a firmware edit").

**Hermes addendum is deployment-focused:** It assumes the machinery works (H11 is the safety valve), documents the Hermes-specific adaptations, and specifies sequencing for implementation.

**Implication:** The Hermes addendum trusts Gemma-4 can emit the protocol markers reliably enough for the gates to fire. The Sonnet addendum documents evidence that Sonnet can't.

---

## 6. Open Questions for the Judge

### 6.1 Is Skills-Based Loading the Right Install Path?

**From H0:428-429:** "Is skill-based loading the right path, or does Brian want the harness embedded in `SOUL.md` with a cron-detection mechanism? My recommendation is skill, but this is worth challenging."

**Rationale for skills:** Opt-in per session, explicit activation, no contamination risk, existing Hermes pattern.

**Counter-arguments (implicit in the rejection text, H0:41-44):**
- SOUL.md is simpler (one file, global).
- Skills require management (file creation, path naming).
- Cron-detection in SOUL.md could work with explicit conditionals.

**Question:** Has Brian signed off on the skills-based approach, or is this still open?

---

### 6.2 Does `exclude_contexts` Exist in Hermes' Skills Hub?

**From H10:270:** "Is this a real Hermes convention or did I invent it? Needs verification in the skills hub code path. If it's invented, drop the field and rely on explicit cron attachment as the sole exclusion mechanism."

**Assessment:** This is a binary question with a clear test: grep Hermes' skills-hub code for `exclude_contexts` or equivalent.

---

### 6.3 What Does "Context Compression at 50%" Mean Precisely?

**From H3:144:** "request context compression via the existing 50% compression trigger."

**Unknown:**
- 50% of what? Tokens? Messages? Iterations?
- How is the compressor invoked? Is there a tool call?
- What guarantees does compression provide about decision preservation?

**Assessment:** This is a critical piece of the degradation-recovery flow (H9), but the mechanism is opaque.

---

### 6.4 How Does the Qwen3-VL-8B Auxiliary Model Integrate with Skills-Hub Matching?

**From H10:260-270:** The auxiliary model performs skills-hub matching, reading the hermes-harness skill's frontmatter metadata to decide auto-activation.

**Unknown:**
- Is skills-hub matching a real Hermes feature, or planned?
- If planned, when will it ship?
- Does the auxiliary model's matching logic actually read YAML frontmatter, or does it use a different signal?

**Assessment:** H10 punts this to "future work" but assumes it as a potential second line of defense against cron contamination.

---

### 6.5 What Is the Exact `todo` State Machine?

**Evidence (H1:78, H3:119, H4:172, H9:240, H10:241):** The addendum assumes a `todo` tool with at least these operations:
- `todo list` — read current state (observable tool call)
- Status values: completed, verified, (implied) in-progress, pending

**Unknown:**
- Is `todo` a Hermes built-in, or a custom tool in this variant?
- What other status values exist?
- Can a task be marked as both `completed` and `verified`, or is one a substate?
- How does `todo` relate to PROGRESS.md's state machine?

**Assessment:** Critical for understanding H3 and H4 gate mechanics.

---

### 6.6 Has Gemma-4-31B's Structured Output Improved Since Benchmarking?

**From H11:304:** "Gemma scores 10/100 on structured JSON output mode on the Jira benchmark — structured prose output is a known weak spot."

**Question:** When was this benchmark run? Is 10/100 still current, or has there been improvement in later Gemma builds?

**Assessment:** This directly affects H11's acceptance criteria and risk assessment.

---

### 6.7 Why 60-Iteration Budget for Discord Sessions?

**From addendum preamble (line 20):** "context compression at 50%, and a 60-iteration hard IterationBudget."

**Unknown:**
- What is the empirical basis for 60? (Cost of compression? Token budget? Degradation curve?)
- Is this configurable (HERMES_MAX_ITERATIONS)? (Addendum mentions it at H3:142 but doesn't confirm.)
- How was the 50%/80% gate trigger points chosen relative to the 60-iteration cap?

**Assessment:** The IterationBudget is the backbone of H3 and H4, but the reasoning is not visible.

---

### 6.8 Can GT-6-hermes Phase-1 Estimate (25 Iterations) Be Calibrated Before Live Run?

**From H13:336, H5:436:** "Phase 1: Give a structured task (e.g., 'help me debug why the cron gateway shows a fatal Discord state'). Let the agent execute through 4-5 tool calls including at least one `delegate_task` dispatch." The addendum estimates "after ~25 iterations (42% budget)" (H13:343).

**Question:** Is 25 iterations an empirically calibrated estimate, or a guess?

**Assessment:** This affects the test design. If Phase 1 typically takes 10 iterations, the late injection (H13:343) happens much earlier than intended. If it takes 40, the injection happens at 67% budget, not 42%.

---

### 6.9 What Happens If Cron Attachment is Missing from jobs.json?

**From H10:256-259:** "Cron sessions do not load the hermes-harness skill. Enforcement comes from: Explicit skill attachment in cron config. Cron jobs in `~/.hermes/cron/jobs.json` attach skills by name. The `jira-daily-briefing` job attaches only `jira-daily-briefing`. It does not attach `hermes-harness`."

**Question:** If jobs.json is misconfigured and hermes-harness is accidentally attached to jira-daily-briefing, what's the fallback? Does the cron job fail gracefully, or does it proceed with degraded output?

**Assessment:** H11 (benchmark regression) catches this via regression detection, but H6 suggests there's a second-line exclusion mechanism (exclude_contexts in skills-hub). How are these layered?

---

## 7. Summary: Three Levels of Risk and Mitigation

### Critical Risk: Gemma Structured Output Unreliability

**Risk:** Gemma-4 scores 10/100 on structured JSON; protocol markers may not be emitted reliably.

**Mitigation:** H11 (benchmark regression) is **mandatory**. It measures directly whether the protocol markers degrade the Jira benchmark.

**Residual uncertainty:** H11 only catches regressions that drop the benchmark score by >5 points. If marker-elision happens silently without degrading the benchmark (e.g., Gemma still completes the Jira calls correctly but stops emitting `[CONTEXT HEALTH]`), H11 won't catch it. GT-7-hermes (health gate firing) would catch it in a multi-turn test, but GT-7-hermes is a human-driven run (not automated).

### High Risk: Cron Session Contamination

**Risk:** hermes-harness skill is accidentally attached to jira-daily-briefing, degrading the 100% baseline.

**Mitigation:** H10 (dual-mechanism exclusion: explicit attachment + optional exclude_contexts) + H11 (benchmark regression).

**Residual uncertainty:** The `exclude_contexts` mechanism is unverified (H10:270). If it doesn't exist, explicit attachment is the only control. This is sufficient but leaves no margin for operator error.

### Medium Risk: Benchmark Tolerance Uncertainty

**Risk:** The "no regression > 5 points" threshold (H11:295-300) may be too loose or too tight.

**Mitigation:** Explicit acceptance criteria with line-by-line scores (Tool Use, Count Accuracy, Key Accuracy, Format).

**Residual uncertainty:** Gemma's non-determinism may cause baseline drift. Two benchmark runs on the same model might score 28/30 and 30/30 on Tool Use, passing both times but not "zero regression."

---

## 8. Conclusion: What the Addendum Assumes and Achieves

### Assumptions Baked In

1. **Gemma-4-31B can follow role-separation discipline** (planner ≠ worker ≠ judge) with fresh-context isolation via ACP.
2. **Context compression at 50%** is available and preserves decision boundaries.
3. **The `todo` tool** provides observable state-driven triggers for health gates.
4. **The fallback parser** at `run_agent.py:~8070` reliably converts Gemma's raw-text tool calls to structured format.
5. **The Qwen3-VL-8B auxiliary model** can perform skills-hub matching and summarization/filtering (future).
6. **Protocol markers** (`[TASK CLASS]`, `[CONTEXT HEALTH]`) can be emitted by Gemma reliably enough for gates to fire (H11 validates this).
7. **Cron skills are linear and can be isolated** via explicit skill attachment in jobs.json.

### What It Achieves

1. **Hermes-specific Critical Rules:** Adapts upstream r6 rules for Hermes' `delegate_task` primitive and `todo` state substrate, with explicit cron carve-out.
2. **IterationBudget-driven health gates:** Replaces upstream PROGRESS.md-count triggers with percentage-based triggers that scale if the 60-iteration budget changes.
3. **Decision-point-scoped delegation checks:** Replaces upstream "before any code" with enumerated decision points (multi-hypothesis investigation, multi-file refactor, cross-skill work, >20-iteration task).
4. **Safe installation path:** Skills-based load avoids SOUL.md contamination and allows opt-in Discord activation.
5. **Benchmark regression gate:** Mandatory re-baseline before deployment ensures cron skills are not degraded.
6. **Golden tasks for Hermes:** GT-6-hermes (late-session delegation resistance) and GT-7-hermes (health gate activation) test Hermes-specific degradation scenarios.

### What It Does NOT Achieve

1. **No specification of compression mechanism:** Assumes compression exists but doesn't explain how.
2. **No operational definition of rubber-stamping detection:** Flags the anti-pattern but no concrete scorer rubric.
3. **No resolution of Sonnet's marker-elision issues:** Hermes addendum ignores the classification-marker elision observed in Sonnet 4.6.
4. **No SOUL.md personality guidance:** Personality remains Brian-configured and unspecified in the variant.

### Net Assessment

The r6 Hermes addendum is a **well-scoped, deployment-focused adaptation of r6's degradation-resistance machinery to Hermes' fundamentally different operating model** (60-iteration Discord sessions, 3-concurrent subagent cap, `delegate_task` dispatch, `todo`-based state). It preserves the architectural spirit of r6 (state-driven gates, observable checks, role separation) while translating the mechanics to Hermes' substrate. The critical risk is Gemma's structured output unreliability, mitigated by a mandatory benchmark regression gate. The design leaves several gaps (compression mechanism, auxiliary model integration, exact `todo` semantics) unspecified, but these are either documented in Hermes' implementation codebase or flagged explicitly as "needs verification" (exclude_contexts, benchmark tolerance).

---

**End of Analysis**
