# Plan — AgentFW r7 (Cross-Model Tuning)

**Revision target:** r7
**Date drafted:** 2026-04-17
**Planner:** main session (planning worker)
**Predecessor:** r6 (context degradation resistance, 2026-04-10)

---

## §0 — Goal & Non-Goals

**Goal.** Tune AgentFW to work well under Claude Opus 4.7 while holding or improving performance on Claude Opus 4.6, Claude Sonnet 4.6, and GPT-5-tier OpenAI models. r7 acts on the ten passing proposals from `ARTIFACT-judge.md`, but only after an empirical multi-model probe validates each change does not regress non-target models. The core firmware stays model-agnostic; 4.7-specific knobs live in a single short appendix and inline `(Anthropic: …)` sidenotes.

**Non-goals.**
- Adding model-specific branches into Critical Rules or the main rule text of any `core/` file.
- Growing core file size. `core/harness-core.md` must remain at or near its current line count.
- Anthropic-SDK-specific language inside playbooks, anti-patterns, state-management, or error-recovery.
- Weakening Rule 2 (role separation) or Rule 3 (no self-verify) based on 4.7's built-in self-verification. Anthropic does not claim 4.7 self-verification replaces an independent judge.
- Retuning the `<20-line` one-shot threshold based on 4.7 coding gains. That threshold is a role-gate, not a capability-gate.

---

## §1 — Phase 0: Multi-Model Empirical Probe (Blocking Gate)

Phase 0 MUST complete before any Phase 1 edit is dispatched. The probe produces the baseline against which r7 changes are judged.

### 1.1 Models to test

| Model | Role | Access note |
|-------|------|-------------|
| Claude Opus 4.7 (`claude-opus-4-7`) | Primary tuning target | Required |
| Claude Opus 4.6 | Non-target — must hold | Required |
| Claude Sonnet 4.6 | Non-target — must hold | Required |
| GPT-5.4-Pro (or nearest-tier OpenAI) | Non-Anthropic non-target — must hold | Best-effort |

If a model is inaccessible, record "NOT TESTED" in the results matrix and do not block the gate on it, but flag it as an empirical gap in the r7 CHANGELOG entry.

### 1.2 Tasks to run

Run GT-1 through GT-7 on **unchanged r6** for each accessible model. Golden tasks are defined in `evaluation/golden-tasks.md`. Follow the fresh-session-per-task rule from `evaluation/eval-protocol.md` (GT-6 remains the documented single-session exception).

### 1.3 Metrics per run

Per `ARTIFACT-judge.md §5a`, record the following per (model × task):

| Metric | Definition |
|--------|-----------|
| Classification-gate compliance | `[TASK CLASS: …]` block emitted before work = 1, else 0. |
| Role-collapse incidents | Count of turns where main session writes implementation code on a structured task. |
| Genuine-assessment rate | For GT-7: fraction of health-gate outputs that cite PROGRESS.md evidence vs. bare marker. |
| Tool-call count | Total tool calls per task. |
| Subagent-dispatch count | Workers + judges dispatched per task. |
| Self-verification incidents | Count of turns where the worker also verifies its own output. |

Record token usage per task as well (covers §6 regression gate).

### 1.4 Output

File: `evaluation/results-r6-baseline-multimodel-YYYY-MM-DD.md`

Table shape: one row per (model × GT-N), columns are the six metrics plus token usage and pass/fail. Include a narrative "notable observations" section per model.

### 1.5 Gate

r7 changes do **not** ship unless both hold:

1. The change demonstrably fixes a real failure observed in the probe, or it addresses a documented 4.7 behavior delta with clear risk to AgentFW structural gates (cited to `ARTIFACT-worker-b.md` official-tier source).
2. The change does not regress any tested model by ≥1 standard deviation vs. its r6 baseline on any metric in §1.3.

**Phase 0 is a hard gate. Phase 1 worker dispatch is forbidden until the results file exists.**

---

## §2 — Phase 1: Ship-As-Is Changes (Cross-Model Safe)

Six proposals from `ARTIFACT-judge.md` are model-agnostic in substance: **1, 2, 4, 6, 7, 9**. Each diff spec below quotes the Artifact A surface, cites the justification, and commits to a success criterion.

**Total added-line budget across these six: ≤ 60 lines.** If a worker produces changes that exceed 60 added lines in aggregate, cut scope (drop the lowest-leverage item — candidate is P9, which is annotation-only).

### 2.1 Proposal 1 — Clarify self-verification vs. self-review

**File:** `references/anti-patterns.md`
**Section:** "Self-Review" anti-pattern (Artifact A surface 18)
**Current surface (verbatim, line 25):** *"The same context that wrote code or made changes then runs verification checks on its own work. It will check for what it intended, not what happened. It will miss the same edge cases in both passes. Verification must come from a fresh context that evaluates artifacts cold, without access to the implementer's reasoning or intent."*
**Proposed change:** Append a single clarifier sentence immediately after the existing paragraph, preserving the blank-line separator to the next anti-pattern. The clarifier distinguishes in-context self-verification (a model-intrinsic pre-flight check before returning) from self-review-as-judge (using the implementing context as the judge). The first is fine and model-provided; the second is prohibited by Rule 3.
**Why it helps every model:** All frontier models increasingly do some intrinsic pre-flight verification. The clarifier prevents future tuners across any model from reading Anthropic's "4.7 self-verifies" guidance (or GPT-5's equivalent) and weakening Rule 3. Model-agnostic principle, model-agnostic language.
**Success criterion:** In the r7 probe, zero new self-verification incidents (per §1.3) are treated by the agent as acceptable substitutes for a separate judge.

### 2.2 Proposal 2 — Explicit fan-out instruction in worker-dispatch templates

**File:** `references/prompt-design.md`
**Section:** `## Context Budget for Sub-Agents` (heading at line 15; Artifact A surface 23). Subsections are `### Include`, `### Exclude`, `### The Rule`.
**Current surface:** The `## Context Budget for Sub-Agents` subsection governs what a sub-agent receives when dispatched. It does not currently address *how many* sub-agents to dispatch when decomposing across independent items.
**Proposed change:** Add a short paragraph **above `### Include`** (directly under the `## Context Budget for Sub-Agents` intro sentence) — fan-out is a dispatch-decision concern that precedes per-agent context curation, so it belongs at the top of the subsection before the Include/Exclude/The Rule mechanics. Paragraph text: "When decomposing across independent items (files, modules, hypotheses), dispatch one subagent per item in the same turn. Use the plural language explicitly ('spawn N workers in parallel'). Do not say 'decompose' alone — some models take that as advisory."
**Why it helps every model:** Explicit fan-out phrasing improves parallelism across all models. It does not introduce any Anthropic-specific mechanism. Artifact B §5.D notes this directly counters 4.7's "fewer subagents by default" tendency; the instruction is literal enough that more literal models benefit most.
**Success criterion:** Probe shows subagent-dispatch count on GT-2 (multi-module feature) is within 1 SD of the cross-model median, not systematically lower on 4.7.

### 2.3 Proposal 4 — Audit reference files for "and similar" / generalization language

**File:** `references/` (state-management, prompt-design, domain-guidelines, error-recovery, anti-patterns)
**Section:** All rule-bearing text.
**Current surface:** `core/harness-core.md` CRITICAL RULES are already imperative and pass the audit (Artifact A surface 1 + judge note on Proposal 4). Reference files are not guaranteed to be.
**Proposed change:** Single-pass read of each referenced file looking for "and similar," "etc.," "or equivalent," and abstract generalizations without concrete triggers. Where found, replace with explicit enumerations or concrete triggers. Worker dispatches one file per pass (fan-out from Proposal 2).
**Why it helps every model:** Literal/explicit instructions improve rule adherence across models. This is a write-quality improvement, not a model-specific one.
**Success criterion:** Reference files contain zero "and similar" / "etc." formulations inside rule-bearing sentences after this pass (mechanical check).
**Line budget note:** Audit should be net-neutral or slightly negative on line count. Count as +0 for this plan.

### 2.4 Proposal 6 — Quote-before-act on state files

**File:** `references/state-management.md`
**Section:** PROGRESS.md protocol (Artifact A surfaces 4, 11)
**Current surface:** Rule 4 in the core: "CHECK PROGRESS.md BEFORE EVERY DISPATCH … The state file is ground truth."
**Proposed change:** In `references/state-management.md` (not core), add a short subsection titled "Quoting state files in worker prompts." Worker prompts should include the exact PROGRESS.md line(s) the worker is acting on, and the worker is expected to echo them in its output. Applies to workers and judges equally.
**Why it helps every model:** All frontier models handle explicit quotation better than implicit reference. Not a 4.7-only effect.
**Success criterion:** Workers dispatched after r7 include a quoted PROGRESS.md line in their returned artifacts (mechanical check on a single probe re-run post-r7).

### 2.5 Proposal 7 — Hold the 3-task health-gate cadence, document why

**File:** `references/state-management.md`
**Section:** Context Health Gate (Artifact A surface 4)
**Current surface (verbatim opening line, line 66):** *"After every 3 tasks reach `completed` or `verified` status in PROGRESS.md, the planner MUST perform a context health check before dispatching the next worker:"* — the rule continues as a numbered list (steps 1–5) through approximately line 80.
**Proposed change:** Add a one-line annotation comment *after the numbered list ends* (post-line ~80), labeled as a note on why the 3-task cadence is held rather than loosened for newer models. Annotation text: "Cadence held at 3 pending empirical degradation-curve data. Retrieval accuracy on long contexts does not imply agentic rule-adherence stability; do not loosen based on needle-in-haystack scores." Keep the proposal in only one file (`references/state-management.md`); do not split across files.
**Why it helps every model:** Immunizes the cadence against well-meaning loosening based on any model's retrieval marketing (Anthropic 1M / 98.5%, OpenAI long-context claims, Gemini 2M context). Model-agnostic defensive comment.
**Success criterion:** Future tuners encountering new long-context benchmark claims do not propose loosening without citing an empirical degradation probe.

### 2.6 Proposal 9 — Annotate that the health gate survives "remove N-tool-call scaffolding" advice

**File:** `references/observability.md`
**Section:** CONTEXT_HEALTH_CHECK event type / "When to Log" (Artifact A surfaces 20, 21). One-line cross-reference back into `references/state-management.md` near the health gate.
**Current surface:** Health gate is task-state-triggered (Artifact A surface 4).
**Proposed change:** Add a one-line note: "Task-state-triggered reflection is distinct from fixed tool-call-interval scaffolding. The health gate fires on observable state (PROGRESS.md task count), not on a tool-call clock." Place in both `references/state-management.md` (beside the cadence annotation from Proposal 7) and `references/observability.md` (beside CONTEXT_HEALTH_CHECK event type).
**Why it helps every model:** Pre-empts deletion of the health gate by any future tuner reading any vendor's "remove every-N-tool-calls summarization" advice (Anthropic has this; others may add it). Model-agnostic.
**Success criterion:** Annotation present; no behavioral change required.

### 2.7 Phase 1 line accounting

| Proposal | File | Estimated added lines |
|----------|------|----------------------|
| P1 | `references/anti-patterns.md` | +3 to +5 |
| P2 | `references/prompt-design.md` | +5 to +8 |
| P4 | Audit across `references/` | ±0 (net-neutral) |
| P6 | `references/state-management.md` | +6 to +10 |
| P7 | `references/state-management.md` | +1 to +2 |
| P9 | `references/observability.md` + `references/state-management.md` cross-ref | +2 to +3 |
| **Total** | — | **~17 to ~28** (budget ≤ 60) |

---

## §3 — Phase 2: Reframed-As-Principle Changes (Model-Family Sidenotes)

Proposals 3, 8, 10 are 4.7-specific in their current framing. They are admissible in r7 only if reframed as model-agnostic principles with the Anthropic-specific invocation relegated to an inline sidenote or a single bounded subsection.

### 3.1 Destination

New subsection at the **end** of `references/prompt-design.md`, titled: **"Model-family knobs (non-binding)."** Not in `core/harness-core.md`. Not in any playbook. Total subsection length budget: **≤ 25 lines**, including the subsection heading, intro sentence, and all three items.

### 3.2 Proposal 3 reframed — Reasoning effort by role

**Principle (model-agnostic):** Workers doing implementation or investigation warrant higher reasoning effort than judges doing focused verification. Mechanical lookups and file-moves warrant the lowest effort. `max`-equivalent settings are reserved for genuinely frontier problems; on structured outputs they can overthink.
**Sidenote:** `(Anthropic Opus 4.7: effort=xhigh for workers, high for judges, low/medium for mechanical tasks, max only when warranted.)`
**OpenAI sidenote (optional, only if observed to help in the probe):** `(OpenAI reasoning models: equivalent tier — use 'high' for workers and 'medium' for judges as starting defaults.)`

### 3.3 Proposal 8 reframed — Judges need guaranteed deliberation

**Principle (model-agnostic):** Short prompts risk silent under-thinking on any model whose thinking or reasoning is adaptive. Judges receive short, shielded prompts by design; therefore judge prompts should include a longer explicit rubric (evaluation criteria spelled out inline) to bias adaptive/gated reasoning toward deliberate evaluation.
**Sidenote:** `(Anthropic Opus 4.7: adaptive thinking is off by default on 4.7 — set thinking: {type: 'adaptive'} in judge dispatch; prefer a summarized display so the user sees progress.)`

### 3.4 Proposal 10 reframed — Token budget as worker-scope component

**Principle (model-agnostic):** Worker scope already includes allowed paths, allowed operations, forbidden operations, and side-effect budget. A token budget — an advisory cap on reasoning + tool tokens for the full worker loop — is a natural fourth component for bounded tasks. Judges and open-ended investigations do not receive a token budget.
**Sidenote:** `(Anthropic Opus 4.7: use the task-budgets-2026-03-13 beta header where available; minimum 20k.)`

### 3.5 Phase 2 line accounting

| Placement | Budget |
|-----------|--------|
| New subsection in `references/prompt-design.md` | ≤ 25 lines total |
| Any other file | 0 |

---

## §4 — Rejected Proposals (Documented)

| # | Proposal | Decision | Reason |
|---|----------|----------|--------|
| 5 | Recalibrate line-count heuristics to tokens for new 4.7 tokenizer | **Reject** | Line counts are more portable across tokenizers than any token-based heuristic. Changing the "500 lines" / "~175 lines" guidance to tokens tunes toward 4.7 at the expense of every other tokenizer in use. The current wording is directionally correct for all models. Document here so future tuners do not re-propose. |
| 11 | Route web-research-heavy tasks away from 4.7 (BrowseComp regression) | **Defer** | Judge flagged this as PARTIAL on the 3-bar test: behavior cited but no Artifact A surface quote exists for the specific playbook content. Re-evaluate when Artifact A is extended to cover playbook routing rules, or when BrowseComp regression is reproduced in-house. |
| 12 | Loosen `<20-line` one-shot threshold based on 4.7 coding gains | **Reject** | The `<20-line` clause is a role-separation gate, not a capability gate. Benchmark strength affects correctness at task completion, not whether the main session should implement vs. delegate. Loosening this because a model is "smarter" is the exact role-collapse failure mode AgentFW exists to prevent. |
| 13 | Weaken Rule 3 (NO SELF-VERIFY) because 4.7 self-verifies | **Reject** | Anthropic does not claim 4.7's built-in self-verification replaces an independent-context judge. Artifact B §5.D states role separation remains necessary. Loosening Rule 3 rests on a misreading of the source. |

---

## §5 — Bloat Budget & File-Size Accounting

"The bloat budget" is the hard cap on new lines introduced by r7. **Target total: ≤ 70 lines** across all files except CHANGELOG.

| File | Expected line delta | Justification |
|------|---------------------|---------------|
| `core/harness-core.md` | **+0** (net) | Per the user's hard constraint. No Critical Rules or main rule text gains model-specific content. Proposal 4 audits it but does not add lines. Any increase requires explicit Planner-note justification in §9. |
| `references/anti-patterns.md` | **+≤ 5** | Proposal 1 clarifier only. |
| `references/prompt-design.md` | **+≤ 30** | Proposals 2 (fan-out) + §3 model-family subsection (≤ 25). |
| `references/state-management.md` | **+≤ 10** | Proposals 6 (quote-before-act), 7 (cadence annotation), 9 cross-ref (1 line). Judge budget said ≤5 but P6 realistically needs up to 10; cut P6 wording if combined exceeds 10. |
| `references/observability.md` | **+≤ 2** | Proposal 9 annotation only. |
| `core/permissions.md` | **+0** | Proposal 10 moves to the §3 model-family subsection rather than into core/permissions.md. This reduces core creep. Judge suggested ≤4; we cut to 0. |
| `CHANGELOG.md` | **+10 to +20** | r7 entry in r6 style. Excluded from the ≤70-line bloat budget. |
| `metadata.json` | n/a | Version/revision/date bump only. |
| `DESIGN.md` | **+0** | Version-history row added as part of the r7 merge commit, not this plan. Out of bloat budget. |

**Running total:** 5 + 30 + 10 + 2 + 0 + 0 = **≤ 47 lines** (with headroom under 70). If any Phase 1 or Phase 2 worker exceeds its per-file sub-budget, the fix is to cut scope on that item, not to raise the cap.

---

## §6 — Regression Gate (Post-Phase 1/2)

After Phase 1 and Phase 2 edits are applied, re-run the Phase 0 probe against r7.

### 6.1 Ship criteria (all must hold)

- Every metric in §1.3 is flat-or-better against the r6 baseline on **every** tested model.
- Classification-gate compliance is ≥ r6 baseline across all models.
- Role-collapse rate is ≤ r6 baseline across all models.
- Genuine-assessment rate on GT-7 is ≥ r6 baseline across all models.

### 6.2 Abort criteria (any one triggers abort)

- Any model regresses ≥ 1 SD on classification-gate compliance vs. its r6 baseline.
- Any model regresses ≥ 1 SD on role-collapse rate vs. its r6 baseline.
- Any model's total token usage per task increases ≥ 15 % vs. its r6 baseline.

*Rationale for mixed thresholds:* Token threshold is absolute because SD is undefined on per-task token variance until a baseline exists.

### 6.3 Abort response

Do not ship r7. Either (a) roll back the specific change correlated to the regression and re-probe, or (b) park the change in a research backlog and ship only the subset that passes.

---

## §7 — Rollout

| Step | Action | Dependency |
|------|--------|-----------|
| 1 | Apply Phase 1 and Phase 2 edits to `variants/claude-code/` (primary variant) first | Phase 0 gate passed |
| 2 | Run the §6 regression gate against the Claude-Code variant | Step 1 complete |
| 3 | Sync edits into `variants/generic/system-prompt.md` | Step 2 passed |
| 4 | Sync edits into `variants/claude-projects/custom-instructions.md` | Step 2 passed |
| 5 | Sync edits into `variants/hermes/HERMES.md` | Step 2 passed |
| 6 | Write CHANGELOG.md entry following r6 style (Context section → Fixed → Added → Enhanced → Files Modified) | All syncs complete |
| 7 | Update `metadata.json`: version 6.0.0 → 7.0.0, revision r6 → r7, updated date → rollout date | Step 6 complete |
| 8 | Update `DESIGN.md` §20 version history with an r7 row | Step 7 complete |
| 9 | Tag release; commit messages follow existing `AgentFW r7 — Cross-model tuning` convention | Step 8 complete |

Variant sync is sequential on regression-gate pass, not parallel, to ensure the Claude-Code variant carries the authoritative tuning before derivative variants inherit it.

---

## §8 — Out-of-Scope for r7 (Research Backlog)

Parking explicitly so they do not re-enter r7 scope creep:

1. **Empirical 4.7 agentic-context degradation curve** (Artifact-judge §4 gap 1). Requires either Anthropic to publish the curve or AgentFW to run a staged long-context probe.
2. **Self-verification-vs-independent-judge comparison experiment** (Artifact-judge §4 gap 2). Would let us re-baseline Rule 3 quantitatively.
3. **Subagent-spawning threshold quantification** (Artifact-judge §4 gap 3). Would inform whether Proposal 2's fan-out phrasing is calibrated correctly.
4. **Effort-tier measured quality curves for judge prompts** (Artifact-judge §4 gap 4). Would confirm the `high`-vs-`xhigh`-vs-`max` choice for judges.
5. **Task-budget behavior across subagents** (Artifact-judge §4 gap 5). Needed to make Proposal 10's sidenote tighter.
6. **Adaptive-thinking engagement rate on short/shielded judge prompts** (Artifact-judge §4 gap 7). Would confirm Proposal 8's risk.

Each of these produces data that could drive r7.1 or r8. None of them is a gate on r7 shipping.

---

## §9 — Planner Notes

Five items of friction with the instructions. Plan is produced as specified regardless; flagging for reviewer awareness:

1. **Phase 0 probe is likely the expensive step.** GT-1..GT-7 across four models is 28 runs, several of which (GT-2, GT-4, GT-6, GT-7) are long sessions. If access to non-Anthropic models is limited, the gate in §1.5 auto-relaxes to "tested models only," and the probe's value as a cross-model guard is reduced. The gate still holds against Opus 4.6 and Sonnet 4.6, which is the core of the user's non-degradation constraint.

2. **Proposal 4 (audit) is broader than its line budget suggests.** A rigorous audit of five reference files for "and similar" / "etc." patterns could produce meaningful behavioral change without net-added lines. The success criterion is mechanical (no such phrases in rule-bearing text). Worth dispatching as a dedicated worker even though its line delta is ±0.

3. **Proposal 6 (quote-before-act) has the highest risk of bloat among Phase 1 items.** Judge allocated +≤5 lines to state-management.md for Proposals 7+9 combined, but quote-before-act pattern needs an example to be usable. I raised the sub-budget to +≤10. If workers cannot keep P6 inside +≤7, cut the example and keep only the principle.

4. **The §3 model-family subsection risks becoming the place where all future model-specific tuning accretes.** A 25-line cap is strict today but will feel tight in r8 once Mythos lands and a second OpenAI column becomes live. Flag for future revisit: the subsection may need to become its own reference file (`references/model-family-knobs.md`) before r8, not now.

5. **The user instruction to preserve `core/permissions.md` with +≤4 lines for Proposal 10 was superseded by the judge's reframing.** By moving Proposal 10 into the §3 model-family subsection, `core/permissions.md` gets +0. This gives us more of the bloat budget and keeps `core/` cleaner. Flagging because §5 in the brief explicitly budgeted +≤4 to permissions.md. I believe moving it is correct; I am noting the disagreement per instruction.

---

**End of Plan**
