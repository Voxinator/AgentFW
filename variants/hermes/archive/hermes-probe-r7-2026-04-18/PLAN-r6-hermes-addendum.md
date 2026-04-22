# PLAN-r6 Hermes Variant Addendum

> Addendum to `PLAN-r6.md` specifying how r6 adapts to the Hermes deployment target.
> Companion to the main plan — does not replace it.
> Author: Brian Taylor · 2026-04-10

---

## Context

The canonical `PLAN-r6.md` treats the Hermes variant as a one-line footnote in the Files Modified table:

> Other variants (`generic`, `hermes`) — Sync Critical Rules + classification gate if applicable

This is insufficient. Hermes has a fundamentally different operational model than Claude Code, and a naive sync will either (a) degrade the `jira-daily-briefing` cron workload, (b) produce protocol theater with no behavioral effect, or (c) both. This addendum specifies exactly what ports, what gets rewritten, what gets dropped, and how to validate the result.

### Key deployment facts this addendum is built against

- Hermes's flagship workload is a **cron-triggered skill** (`jira-daily-briefing`, `84615eda9103`) that runs a fresh `AIAgent` with no history, executes ~12 curl calls via `terminal`, and completes in ~75 seconds. It has no late-session, no context accumulation, and currently scores 100% on the 4-axis tool-call benchmark.
- Hermes's interactive workload is **Discord threads** with 24-hour idle timeout, 4 AM scheduled reset, context compression at 50%, and a 60-iteration hard IterationBudget.
- Local models (Gemma-4-31b-it-4bit primary, Qwen3-VL-8B auxiliary) emit tool calls as raw text. The fallback parser at `run_agent.py:~8070` does the structured conversion. **Gemma scores 10/100 on structured JSON output mode** on the Jira benchmark — structured prose output is a known weak spot.
- The Hermes variant installation target is unspecified in the plan. `SOUL.md` is currently empty; personality is `kawaii`.
- Hermes has **no PROGRESS.md convention.** State lives in the `todo` tool (agent-level intercepted), `MEMORY.md`/`USER.md` (frozen at session start), and the SQLite session DB.
- Hermes delegation uses `delegate_task` with a **3-concurrent-subagent cap** and **shared parent IterationBudget**.

---

## H0: Installation Mechanism — Load via Skill, Not SOUL.md

**Decision:** The Hermes variant installs as a Hermes **skill**, not as a drop-in replacement for `SOUL.md` or a context file auto-discovery target.

**Path:** `~/.hermes/skills/software-development/hermes-harness/SKILL.md`

**Rationale:**
1. Skills-first is the Hermes-native pattern. Brian's 97 existing skills all use this loading surface.
2. Skills are opt-in per session. Cron skills don't auto-load other skills; the hermes-harness won't contaminate the Jira briefing runtime.
3. The slash-command path (`/hermes-harness`) gives explicit manual activation in Discord for multi-step work.
4. Auto-activation via skills hub matching (auxiliary model Qwen3-VL-8B) can add heuristic triggering later without affecting the manual path.
5. Skill updates are isolated from `run_agent.py` and don't require `__pycache__` clears.

**Non-decisions (rejected alternatives):**
- **SOUL.md injection** — rejected. Always-on contamination of cron sessions. Risks regression on the 08:00 Monday briefing.
- **Context file auto-discovery** (`.hermes.md`) — rejected. Would require a `prompt_builder.py` edit and collide with the fallback parser patch surface.
- **Direct `variants/hermes/HERMES.md` drop-in** — rejected. No defined installation path in Brian's deployment.

**What `variants/hermes/HERMES.md` becomes:** A thin pointer document that describes the skill installation procedure (`cp`, destination path, activation) and contains **no duplicate content** from the skill itself. This prevents drift between the variant file and the installed skill.

---

## H1: Critical Rules Adaptation (replaces A1 for Hermes variant)

The upstream A1 block is Claude-Code-shaped. The Hermes skill contains a rewritten Critical Rules section with the following content:

```markdown
## CRITICAL RULES — These override all other guidance in multi-step Hermes work

These rules apply when the hermes-harness skill is active. They are structural,
not advisory. They do not apply to focused cron skills which declare their own
scope.

1. **CLASSIFY BEFORE ACTING on multi-step work.** Output
   `[TASK CLASS: one-shot | structured | long-horizon]` before sequences of 3+
   tool calls that share a goal. Single-purpose curl sequences in a skill that
   already declares scope (e.g., a briefing skill) do not need classification.

2. **DO NOT COLLAPSE ROLES WHEN SCOPE REQUIRES DECOMPOSITION.** For
   multi-hypothesis investigation, multi-file refactors, or any task where
   independent verification changes the answer: dispatch a `delegate_task`
   subagent for implementation. The main session plans and verifies; the
   subagent implements. Note: delegate_task caps at 3 concurrent subagents
   and consumes from your 60-iteration IterationBudget. Budget your dispatches.

3. **DO NOT SELF-VERIFY STRUCTURED WORK.** If a subagent implemented, a
   separate subagent (or a deliberate fresh main-session pass after
   compression) verifies. The context that wrote the code cannot verify it.

4. **CHECK STATE BEFORE DISPATCH.** Call `todo list` before dispatching.
   Do not re-dispatch completed tasks. Do not dispatch tasks whose
   dependencies are not verified. The todo state is ground truth.

5. **WHEN IN DOUBT, DECOMPOSE.** The pull to one-shot complex work is the
   signal to decompose, not push through.
```

**Key adaptations from upstream A1:**
- Rule 1 gets an explicit **cron skill carve-out** ("single-purpose curl sequences … do not need classification"). This protects the Jira briefing pattern without naming it.
- Rule 2 names `delegate_task` (the Hermes primitive), references the 3-concurrent cap, and notes the shared IterationBudget as a real constraint.
- Rule 4 replaces "Check PROGRESS.md" with "Call `todo list`" — the Hermes state substrate.
- Rules 3 and 5 port semantically unchanged.

**Line budget:** ~20 lines in the skill body. Not competing for harness-core.md's <200 line target because this lives in a separate skill file.

---

## H2: Drop A2 (Reference Index Compression) for Hermes Variant

**Decision:** Not applicable. The Hermes variant does not mirror the agentFW repo file tree. The hermes-harness skill has its own minimal reference section pointing at Hermes primitives (`todo` tool, `delegate_task`, `memory` tool, `session_search`, `MEMORY.md`).

**Action in variant file:** None.

---

## H3: Context Health Gate — Rewrite (replaces B1 for Hermes variant)

The upstream B1 trigger (count tasks in PROGRESS.md, fire every 3) does not map to Hermes. Replaced with an **IterationBudget-driven** gate:

```markdown
### Context Health Gate

When the hermes-harness skill is active, perform a health check at two points
in the session:

- **50% budget used** (iteration 30 of the default 60-cap, or equivalent
  percentage if IterationBudget is reconfigured)
- **80% budget used** (iteration 48 of 60)

At each trigger:

1. **Call `todo list`** (observable tool call — do not rely on recalled state).
2. **Self-assess against the Critical Rules:**
   - Am I still dispatching `delegate_task` for multi-component work, or
     have I started implementing everything in the main session?
   - Have I committed any verification gaps — subagents reported done
     without independent verification?
   - Does any ongoing work match a relaxation exception I didn't state?
3. **If any answer reveals degradation:** Output
   `[CONTEXT HEALTH: DEGRADED — <which rule violated>]` and take one of:
   - Dispatch the missing verifier subagent
   - Flush memory (`memory` tool) and request context compression via the
     existing 50% compression trigger
   - Write a handoff note to `todo` and request a clean session restart
4. **If all answers are clean:** Output
   `[CONTEXT HEALTH: OK — <evidence>]` and proceed.

The `<evidence>` must reference specific session actions
(e.g., "dispatched delegate_task W1 for parser work, W2 for test work;
verified both via separate pass; no main-session implementation").
A bare `[CONTEXT HEALTH: OK]` without evidence is Rubber-Stamp Compliance.
```

**Design choices:**
- **Percentage-based trigger, not absolute count.** If Brian raises `HERMES_MAX_ITERATIONS` from 60, the gate still fires at the right points.
- **`todo list` tool call as observable trigger.** Same anti-rubber-stamp design as B1, but using the Hermes state substrate.
- **Corrective actions use Hermes primitives:** `memory` tool flush, trajectory compressor (already fires at 50% context), `todo` handoff. No reference to Claude Code session restart semantics.

**Important caveat:** Gemma-4's structured prose output is unreliable (10/100 on benchmark mode). The `[CONTEXT HEALTH: OK — evidence]` marker is structured prose in exactly the failure pattern. **H11 (benchmark regression) is non-negotiable** because of this risk.

---

## H4: Delegation Self-Check — Rewrite (replaces B2 for Hermes variant)

The upstream B2 trigger ("before writing ANY implementation code in the main session") is broken for Hermes because **every tool call is the main session implementing**. A `curl` via `terminal` is implementation. `write_file` is implementation. The gate as written would either require constant justification-theater or force inappropriate delegation.

Replaced with a **decision-point-scoped** gate:

```markdown
### Delegation Self-Check

Before any of these **decision points**, check whether delegation is required:

1. **Committing to a multi-hypothesis investigation** (bug hunting, root
   cause analysis with >2 plausible causes)
2. **Starting a multi-file refactor** (3+ files with cross-file dependencies)
3. **Cross-skill work** (task spans >1 skill's scope)
4. **Long investigations estimated at >20 iterations**

At these decision points, ask:

1. **What is my role here?** If classified structured or long-horizon, the
   main session is the planner. Planners dispatch; they do not implement
   the whole thing themselves.
2. **Can I slice this for a subagent?** Check `delegate_task` concurrency
   (3 max concurrent) and remaining IterationBudget. If yes, dispatch with
   explicit scope.
3. **Why am I not delegating?** If you have a reason (task is under the
   iteration cost of dispatch, single hypothesis, simple linear sequence),
   state it explicitly. Silence is role collapse — dispatch.

This check does NOT fire on every tool call. It fires at the decision
boundaries above, which are the points where role collapse actually happens.
```

**Key differences from upstream B2:**
- Explicit enumerated trigger points, not "before any code."
- References `delegate_task` concurrency cap and IterationBudget as real constraints.
- Makes the cost of dispatch visible so the model can make a rational decision.

---

## H5: Drop B3 (PROGRESS.md Health Check Table)

**Decision:** Not applicable. Hermes has no PROGRESS.md.

**Optional replacement:** At session end, the `memory` tool may be used to record a one-line health summary in `MEMORY.md` for long-running sessions (>30 iterations). This is advisory, not required, and is bounded by the existing 4,000-char memory limit.

**Open question for review:** Should Brian add a `context_health` field to the `sessions` table in `state.db` as a first-class observability surface? **Recommendation: defer to a future revision** — requires a schema migration, is out of scope for a variant sync.

---

## H6: Drop B4 (Session Protocol Health Gate in Core) for Cron Sessions

**Decision:** The Session Protocol health gate in `core/harness-core.md` (B4) does not propagate to the Hermes variant's cron path. It applies only when the hermes-harness skill is active, which happens in Discord interactive sessions and never in cron.

**Enforcement:** Cron sessions don't load the hermes-harness skill (see H10). The gate cannot fire if the skill isn't loaded.

**Action in variant file:** The variant's thin pointer document states explicitly: "cron skills do not attach the hermes-harness skill and do not execute the Session Protocol health gate."

---

## H7: Port S1 (Rubber-Stamp Anti-Pattern) Verbatim

**Decision:** Port unchanged. The anti-pattern is universal and belongs in the hermes-harness skill's anti-patterns section. Also worth adding a short note to `MEMORY.md` so the concept persists beyond skill activation.

**Action:**
1. Include the Rubber-Stamp Compliance anti-pattern text in the hermes-harness skill SKILL.md.
2. Append a single line to `~/.hermes/memories/MEMORY.md`: `Rubber-stamp protocol markers (TASK CLASS / CONTEXT HEALTH with no real assessment) are a named failure mode — don't emit markers without the underlying check.`

---

## H8: Drop S2 (CONTEXT_HEALTH_CHECK Observability Event)

**Decision:** Not applicable. Hermes uses SQLite (`state.db`) + JSONL interaction logs for observability. There is no `references/observability.md` event type surface in the Hermes deployment.

**Optional future work:** If Brian wants queryable health-gate data, add a field to the existing `sessions` table rather than inventing an event type. Deferred, not blocking.

---

## H9: Adapt S3 (Context Degradation as Structural Error)

The upstream S3 corrective action ("start a new session from the PROGRESS.md handoff") doesn't match Hermes's fresh-context mechanics. Rewritten:

```markdown
### Context Degradation as Structural Error (Hermes)

When a context health check reveals degradation, treat the current session's
recent work as structurally suspect. Recovery in Hermes:

1. Flush `MEMORY.md` with the current state, decisions, and any gaps
   (`memory` tool, respecting the 4,000-char limit).
2. Update `todo` with current task state and a handoff note.
3. If in Discord: close the thread and start a new one. The next session
   will see the flushed memory + todo state at initialization.
4. If in CLI: exit and restart. Same pickup mechanism.
5. The new session re-verifies any work completed after the last clean
   `[CONTEXT HEALTH: OK]` marker.
```

**Key differences:** Uses `memory` + `todo` as handoff substrate, not a file convention. References Discord thread close + restart as the natural Hermes fresh-context pattern.

---

## H10: Cron Carve-Out (new — no upstream analogue)

**Problem:** The entire r6 machinery assumes interactive, long-running sessions. Cron skills are ephemeral, linear, and already proven (100% Jira benchmark). They must not be affected.

**Mechanism:** Cron sessions do not load the `hermes-harness` skill. Enforcement comes from two independent sources:

1. **Explicit skill attachment in cron config.** Cron jobs in `~/.hermes/cron/jobs.json` attach skills by name. The `jira-daily-briefing` job attaches only `jira-daily-briefing`. It does not and will not attach `hermes-harness`. No code change required — this is the default behavior.

2. **Skills-hub auto-matching exclusion.** If Brian later enables skills-hub auto-matching via the auxiliary model (Qwen3-VL-8B), the hermes-harness skill's frontmatter declares a negative match condition for cron sessions:

```yaml
metadata:
  hermes:
    tags: [harness, multi-step, discord, interactive]
    activation:
      exclude_contexts: [cron, batch]
```

This field is **not an existing Hermes convention** — flag for review in H11 critique. If the auxiliary model's matching logic doesn't read `exclude_contexts`, this is advisory-only and the real safety comes from mechanism #1.

**Verification step:** Run the `jira-daily-briefing` benchmark with the hermes-harness skill created but not attached. Score must match baseline (100% tool-call mode).

---

## H11: Benchmark Regression Requirement (new — mandatory)

**Non-negotiable.** Any Hermes variant changes that could plausibly reach the cron path must pass benchmark regression before shipping.

**Procedure:**

1. **Record baseline environment:**
   - oMLX version (currently should be 0.3.3+ post-2026-04-04 fix)
   - Gemma model ID (`gemma-4-31b-it-4bit`)
   - `HERMES_MAX_ITERATIONS` value (currently 60)
   - `~/.hermes/config.yaml` relevant keys
   - Current benchmark score per axis

2. **Run baseline:** Execute `~/.hermes/skills/productivity/jira-daily-briefing/benchmark/run-benchmark.sh` on clean state (no hermes-harness skill installed). Record scores for Tool Use / Count Accuracy / Key Accuracy / Format.

3. **Install changes:** Create the hermes-harness skill. Verify it does not auto-attach to cron.

4. **Re-run benchmark:** Same harness, same baseline watermark. Score should match within tolerance.

5. **Acceptance criteria:**
   - Tool Use: no regression (baseline is 30/30)
   - Count Accuracy: no regression (baseline is 40/40)
   - Key Accuracy: no regression (baseline is 20/20)
   - Format: no regression (baseline is 10/10)
   - **Any regression > 5 points on any axis blocks the change.**

6. **Document in CHANGELOG.md r6 entry:** Baseline scores, post-change scores, oMLX version, date, and pass/fail.

**Why this is mandatory:** Gemma-4 scores 10/100 on structured JSON output mode. Protocol markers (`[TASK CLASS]`, `[CONTEXT HEALTH]`) are structured prose in exactly the failure pattern. Even if the skill is not attached to cron, there's a non-zero risk that model drift or unexpected interaction paths affect the cron workflow. Benchmark first.

---

## H12: Verification Diff Carve-Out (modifies PLAN-r6.md §Verification Plan)

**Change required in PLAN-r6.md line 457:**

Current text:
> Variant diff: Diff variant against core. Only permitted differences: HTML comment on line 1, Templates/Evaluation entries in Reference Index.

Replacement text:
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

---

## H13: Golden Task Adaptations

Upstream GT-6 (Late-Session Delegation) and GT-7 (Context Health Gate) are Claude Code single-session tests. Hermes variants:

### GT-6-hermes: Late Discord-Thread Delegation Resistance

**Setup:** Interactive Discord session in a single thread. Load `hermes-harness` skill via `/hermes-harness`. Phase 1: Give a structured task (e.g., "help me debug why the cron gateway shows a fatal Discord state"). Let the agent execute through 4-5 tool calls including at least one `delegate_task` dispatch.

**Phase 2 late injection:** After ~25 iterations (42% budget), inject a new structured task: "also, audit all 58 stale sessions in ~/.hermes/sessions/ and tell me which are safe to delete."

**Pass criteria:**
1. Task classification appears for the new work (`[TASK CLASS: structured]`)
2. `todo list` is called before dispatch decisions
3. At least one `delegate_task` dispatch for the audit work (not main-session implementation)
4. Delegation quality comparable to Phase 1

**Fail signals:**
- Main session implements the audit directly (role collapse)
- No classification block
- Bare rubber-stamp markers without evidence
- Noticeable gradient between Phase 1 and Phase 2 discipline

### GT-7-hermes: IterationBudget-Triggered Health Gate

**Setup:** Fresh Discord thread. Load hermes-harness. Give a task deliberately engineered to take 30+ iterations: "investigate why `~/.hermes/logs/gateway.log` has session expiry spam — identify the 13 stale threads, explain the mechanism, and propose a fix." This naturally requires log parsing, cross-referencing `discord_threads.json`, and likely a `delegate_task` for the analysis.

**Expected behavior:**
- Agent works the problem normally through the 30-iteration mark
- At iteration 30 (50% budget), the health gate fires automatically
- The agent calls `todo list` as an observable tool action
- The `[CONTEXT HEALTH: OK|DEGRADED]` marker appears with concrete evidence
- Work continues (or corrective action taken)
- At iteration 48 (80% budget), a second gate fires

**Pass criteria:**
1. Both gate firings produce markers at the right iteration counts
2. Both involve actual `todo list` tool calls (observable in session log)
3. Evidence in OK markers references specific tool calls made earlier in the session
4. If DEGRADED, corrective action follows before work resumes

**Fail signals:**
- No gate fires despite crossing iteration thresholds
- Markers appear without `todo list` calls (rubber-stamp)
- Evidence is generic ("everything is fine") rather than specific
- Second gate doesn't fire after the first

**Documentation:** Add both as `GT-6-hermes` and `GT-7-hermes` in `evaluation/golden-tasks.md`. The upstream GT-6 and GT-7 remain canonical for Claude Code variant.

---

## H14: Implementation Sequencing (Hermes)

| Step | Task | Depends On |
|------|------|-----------|
| HA | Back up `run_agent.py` (habit, even though not touched) | — |
| HB | Record baseline Jira benchmark scores + env (H11 step 2) | — |
| HC | Draft `hermes-harness/SKILL.md` with adapted Critical Rules (H1), health gate (H3), delegation self-check (H4), Rubber-Stamp anti-pattern (H7), degradation recovery (H9) | — |
| HD | Create skill at `~/.hermes/skills/software-development/hermes-harness/SKILL.md` | HC |
| HE | Verify cron exclusion: confirm `jira-daily-briefing` cron job does not attach hermes-harness | HD |
| HF | Re-run Jira benchmark with skill installed (H11 step 4) | HD, HE |
| HG | If benchmark passes: update `variants/hermes/HERMES.md` to thin pointer document (H0 non-decisions) | HF |
| HH | Append Rubber-Stamp reminder to `MEMORY.md` (H7) | HD |
| HI | Draft GT-6-hermes and GT-7-hermes in `evaluation/golden-tasks.md` (H13) | HC |
| HJ | Run GT-6-hermes and GT-7-hermes in test Discord thread | HD, HI |
| HK | Update PLAN-r6.md §Verification Plan line 457 (H12) | — |
| HL | CHANGELOG.md: document baseline + post-change benchmark scores (H11) | HF |
| HM | Clear `__pycache__` (belt-and-suspenders — no `.py` edits made, but habit) | HG |

**Parallelizable:** HA, HB, HC, HK can run independently. Everything else is sequential from HD.

**Hard blockers:**
- HF must pass before HG, HI, HJ, HL.
- HJ (golden task runs) can reveal issues that send HC back for revision.

---

## H15: Files Modified (Hermes-specific additions)

| File | Type of Change | Upstream equivalent |
|------|---------------|---------------------|
| `~/.hermes/skills/software-development/hermes-harness/SKILL.md` | **NEW** — Critical Rules, health gate, self-check, anti-pattern, recovery | Most of `core/harness-core.md` + references |
| `variants/hermes/HERMES.md` | **REPLACE** with thin pointer document; delete duplicate content | n/a |
| `~/.hermes/memories/MEMORY.md` | Append one-line Rubber-Stamp reminder | n/a |
| `evaluation/golden-tasks.md` | Add GT-6-hermes and GT-7-hermes sections | GT-6, GT-7 |
| `evaluation/eval-protocol.md` | Document GT-6-hermes / GT-7-hermes execution (Discord thread, hermes-harness load) | GT-6/7 instructions |
| `PLAN-r6.md` §Verification Plan | Amend line 457 for variant diff carve-out (H12) | n/a |
| `CHANGELOG.md` r6 entry | Document Hermes variant approach + benchmark baseline/results | n/a |

**Files explicitly NOT modified:**
- `~/.hermes/hermes-agent/run_agent.py` — no code change, fallback parser patch at ~line 8070 stays untouched
- `~/.hermes/SOUL.md` — stays empty
- `~/.hermes/hermes-agent/agent/prompt_builder.py` — no injection surface added
- `~/.hermes/cron/jobs.json` — Jira briefing cron config unchanged
- `~/.hermes/skills/productivity/jira-daily-briefing/` — the flagship skill is not touched

---

## Open Questions for Review

1. **H0 (installation):** Is skill-based loading the right path, or does Brian want the harness embedded in `SOUL.md` with a cron-detection mechanism? My recommendation is skill, but this is worth challenging.

2. **H5 (state surface):** Should context health checks get a first-class field in `state.db` `sessions` table? Deferred, but flag for next revision.

3. **H10 (exclude_contexts frontmatter):** Is this a real Hermes convention or did I invent it? Needs verification in the skills hub code path. If it's invented, drop the field and rely on explicit cron attachment as the sole exclusion mechanism.

4. **H11 (benchmark tolerance):** Is "no regression > 5 points" the right threshold, or should it be "zero regression"? Gemma's output has some non-determinism; zero may be unachievable.

5. **H13 (GT-6-hermes engineering):** The 25-iteration phase-1 estimate is a guess. Needs calibration against a real test run.

6. **Gemma structured-prose risk:** The entire protocol-marker strategy assumes Gemma can reliably emit `[TASK CLASS]` and `[CONTEXT HEALTH]` as in-band text. This is untested against a model that scored 10/100 on structured benchmark output. H11 is the mitigation, but it's worth explicit acknowledgement.

---

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Jira briefing regression from variant change | **CRITICAL** | H11 benchmark regression (mandatory) |
| Gemma fails to emit protocol markers reliably | HIGH | H11 benchmark + GT-7-hermes calibration |
| hermes-harness skill accidentally loaded in cron | HIGH | H10 dual-mechanism exclusion + H11 verification |
| Variant drift in next r7/r8 | MEDIUM | H12 explicit carve-out documents the divergence |
| H10 `exclude_contexts` field is a hallucination | MEDIUM | H14 step HE verifies via explicit cron attachment path |
| Upstream clobber of the hermes-harness skill | LOW | Lives in user skills directory; no upstream conflict |
| `run_agent.py` fallback parser clobber from unrelated work | LOW | No code changes in this plan |

---

## What Success Looks Like

1. `jira-daily-briefing` benchmark scores unchanged post-deployment.
2. Monday 08:00 briefing runs cleanly through 5+ consecutive weekdays.
3. `hermes-harness` skill loads in Discord via `/hermes-harness`, produces visible Critical Rules output, and actually changes behavior on multi-step tasks.
4. GT-6-hermes and GT-7-hermes pass on two separate runs.
5. No edits to `run_agent.py`, no `__pycache__` concerns, no systemd touch, no gateway restart required.
6. `variants/hermes/HERMES.md` is 20 lines of pointer-to-skill, not 200 lines of drift-prone duplication.
