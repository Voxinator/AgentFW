# Judge — Phase 0 Probe Runbook & Scaffold

**Judged artifact:** `evaluation/PROBE-r7-runbook.md` + `evaluation/results-r6-baseline-multimodel-2026-04-17.md`
**Spec reference:** `PLAN-r7.md` §1
**Judge role:** Fresh-context evaluator of executability and metric operationalization
**Date:** 2026-04-17

---

## 1. Verdict

**REVISE.** The runbook is close to shippable — coverage is good, prose is disciplined, and the scaffold is cleanly mapped. It fails on two operationalization points that would contaminate all 28 runs if left as-is: the gate-logic reference-model choice does not match `PLAN-r7.md` §1.5, and one metric has an ambiguous signal-definition. Both are tightenings, not rewrites.

---

## 2. Scorecard

| # | Test | Result | Rationale |
|---|------|--------|-----------|
| 1 | Coverage | **PASS** | §2 prerequisites, §3 execution, §4 metrics, §5 gate, §6 scope/relaxation, §7 handoff — all present and distinct. |
| 2 | Executability | **PARTIAL PASS** | An operator can run it cold except for one gap: §3.2 step 3 says "copy-paste the session" for non-Claude-Code harnesses, but does not define what "the session" must contain (turn boundaries? system prompt? tool-call metadata?). Scorers will diverge on whether a truncated paste is valid. |
| 3 | Metric operationalization | **FAIL** | Five of six metrics are reproducible between independent scorers. Metric §4.2 (role-collapse) is not: "writes implementation code" is not defined — does a one-line config toggle count? Does creating PROGRESS.md count as "writing a file directly"? The GT-6 example helps but does not pin the edge cases. With 28 runs × this ambiguity, inter-scorer variance swamps the 1-SD gate threshold. |
| 4 | Scaffold fillability | **PASS** | Every metric in §4.1–§4.7 + §4.8 pass/fail has a line in every per-task per-model block. The summary table's right-side aggregate columns (avg role-collapse rate, avg health-gate genuine-assessment rate, avg self-verification incidents, total tool calls, total subagent dispatches, total tokens) are all derivable from per-cell values. One minor orphan: the scaffold's per-task blocks do not have a slot for "stop condition triggered" (§3.2 step 5 asks the operator to record which stop condition fired), so that data lands only in "Notes." Acceptable but worth a polish. |
| 5 | Gate-logic faithfulness | **FAIL** | `PLAN-r7.md` §1.5 defines the gate against each model's **r6 baseline** — explicitly: "does not regress any tested model by ≥1 SD vs. its r6 baseline." The runbook §5.2 instead makes the **earliest completed model** the reference and computes cross-model deltas against it. That is a fundamentally different gate. Phase 0 IS the r6 baseline for each model; the correct interpretation is that Phase 0 establishes per-model baselines to be compared against Phase 1 (r7) results in §6 of the plan — it does NOT compare models against each other. The worker's (i) interpretation is the root cause. See ruling below. |
| 6 | No scope creep | **PASS** | Runbook does not propose firmware changes, new rules, or additions to golden tasks. It consumes GT-1..GT-7 verbatim against r6 verbatim. Good discipline. |

---

## 3. Rulings on Worker Interpretations

### (i) Reference model for gate deltas — **OVERRIDE**

**Worker's interpretation:** Use the earliest completed model as the reference; compute cross-model deltas.
**Corrected interpretation:** Phase 0 establishes the per-model r6 baseline. There is no "reference model." The runbook should not attempt to fire the §1.5 regression gate within Phase 0. The §1.5 gate compares **r7 results against Phase 0 r6 baselines, per model**, and is invoked at §6 of the plan (after Phase 1/2 edits). Phase 0's exit criterion is simpler: "results file exists, filled, with valid per-model per-task data." The runbook's §5 currently invents a gate that is not in the plan and that (if used) would over-penalize models for stylistic variance unrelated to AgentFW behavior.
**Reason:** Cross-model variance at r6 is not an AgentFW regression signal — different models behave differently even on unchanged firmware. Treating Sonnet-vs-Opus deltas as a fail condition confuses model capability delta with framework degradation.

### (ii) Genuine-assessment rate scoping — **ACCEPT**

**Worker's interpretation:** Scope metric to GT-7 only; mark `n/a` elsewhere.
**Reason:** `PLAN-r7.md` §1.3 defines the metric specifically as "For GT-7: fraction of health-gate outputs that cite PROGRESS.md evidence vs. bare marker." That is explicit GT-7 scoping. GT-6 can also fire a health gate per the cadence rule, but the plan did not operationalize it there, and adding it unilaterally is scope creep. Accept as-is. (If GT-6 health-gate data is observed, capture it in Notes; do not let it score the metric.)

### (iii) Scorer identity — **ACCEPT**

**Worker's interpretation:** Human scorer, not sub-agent.
**Reason:** Rule 3 is correctly applied, and the cost argument holds — 28 runs × 6 metrics × dispatching a shielded judge per metric per run is not justified when one human scorer in a consistent seat is equivalent. The planner-note §9.1 already flags cost; this choice is consistent. Runbook §4 is explicit that the human is the judge. Accept.
**Caveat:** Runbook should name the scorer in the results header (it has the slot). A single named scorer across all 28 runs is the strongest inter-rater-reliability control available here.

### (iv) Self-verification metric definition — **ACCEPT**

**Worker's interpretation:** Post-hoc self-review (worker reviewing its own just-produced output as a substitute for a judge) counts; intrinsic pre-flight verification before returning output does not count.
**Reason:** This exactly matches `PLAN-r7.md` §2.1 (Proposal 1), which explicitly distinguishes in-context pre-flight verification from self-review-as-judge and reserves the prohibition for the latter. It also matches the non-goal in §0 ("Weakening Rule 3 … based on 4.7's built-in self-verification"). The worker has read the spec correctly. Accept.
**Minor polish suggestion:** The metric text in §4.6 could add a half-sentence example of what pre-flight verification looks like so scorers do not over-count (see §5 below).

---

## 4. Required Revisions (Blockers)

- **BLOCKER 1 — Rewrite §5 "Gate logic."** Replace with: "Phase 0 establishes the per-model r6 baseline for each metric. No gate fires at the end of Phase 0; the gate defined in `PLAN-r7.md` §1.5 and §6 fires only when Phase 1/2 (r7) results are compared against this baseline. Phase 0's exit criterion is solely: (a) results file exists with all cells filled per §7 handoff rules, (b) any model-inaccessibility or task-error events are documented per §6.2–§6.3." Remove the §5.2 earliest-completed-model reference-model logic entirely. Remove the §5.3 abort conditions — they belong in a later runbook for the r7 probe, not this one.

- **BLOCKER 2 — Tighten §4.2 (Role-collapse incidents) signal definition.** Add explicit inclusion/exclusion list. Include: direct source-file edits via Edit/Write, direct mutation shell commands (`npm install`, `rm`, `git commit`, etc.), inline implementation code blocks that would be saved to a source file. Exclude: reading files, running linters/tests in read-only mode, creating or updating harness files (PROGRESS.md, PLAN.md, DIAGNOSTIC.md, SESSION_LOG.md) — these are main-session responsibilities. Keep the GT-6 worked example.

- **BLOCKER 3 — Pin "record the transcript" expectations in §3.2 step 3.** Require: (a) full text of every user/agent turn, (b) every tool-call name + arguments + result, (c) every sub-agent dispatch prompt + return artifact. For harnesses without native export, specify that a chronological copy-paste with tool-call boundaries marked is acceptable; anything less invalidates the run. This removes the step-3 ambiguity noted in Test 2.

- **BLOCKER 4 — Correct §1 "hard gate" language.** The current wording ("No r7 firmware edit may ship until the probe completes and the gate decision in §5 of this runbook resolves to PASS") is wrong once §5 is rewritten per Blocker 1. Replace with: "No r7 firmware edit may ship until this results file exists, is fully filled, and is accepted as the r6 baseline. The §1.5 regression gate fires at a later stage against r7 results."

## 5. Non-blocking Polish

- **§4.6 example sentence.** Add: "Example of pre-flight verification that does NOT count: the agent reviews its own draft once before returning it to the user. Example that DOES count: the worker returns its artifact, then the main session re-enters worker-mode to re-check that artifact instead of dispatching a judge."
- **Scaffold: stop-condition slot.** Add one line `- Stop condition: <turn budget | time budget | completion | loop>` to each per-task per-model block. Currently that data has to live in Notes.
- **§3.1 pre-flight step 3.** Specify the ping prompt text (e.g., `"reply with the single word 'pong'"`) to make it scorer-agnostic.
- **§4.4 and §4.5 granularity.** Consider splitting tool-calls into main-session vs. sub-agent buckets in the scaffold (two integers) rather than one combined integer. The analysis section of the next r7 probe will want this breakdown; capturing it once now is cheaper than recomputing from transcripts later.
- **§6.1 wall-time.** Total of 10–14 hours is optimistic for a single scorer doing 28 careful scorings. Worth flagging that scoring time is additive to session observation time.
- **Results header — name the scorer.** The `<fill with scorer name>` slot exists; runbook should state in §2 that a single scorer across all 28 runs is strongly preferred for inter-rater consistency.

## 6. Ship-readiness

Not ship-ready as-is — Blocker 1 is a substantive misreading of `PLAN-r7.md` §1.5 that would invent a false abort condition within Phase 0; with Blockers 1–4 applied, this runbook is a clean baseline-capture protocol that a fresh operator can execute cold.

---

**End of judgment.**

---

## 7. Re-Judgment (post-revision)

### 7.1 Verdict

**SHIP (with one minor residual noted).** All four blockers are resolved. Both polish items are applied. Stop-condition slot count is exact. The runbook is now executable cold and internally consistent.

### 7.2 Per-blocker status

- **B1 — §5 rewrite:** **Resolved.** §5 now states "Phase 0 establishes the per-model r6 baseline for each metric. No gate fires at the end of Phase 0; the gate defined in `PLAN-r7.md` §1.5 and §6 fires only when Phase 1/2 (r7) results are compared against this baseline." The earliest-completed-model reference logic is gone from §5. Abort conditions are gone from §5. Exit criterion is simply results-file-filled plus error documentation.
- **B2 — §4.2 signal definition:** **Resolved.** §4.2 now contains explicit Include (Edit/Write on source files; mutation shell commands like `npm install`, `rm`, `git commit`; inline implementation code blocks) and Exclude (reading files; read-only linters/tests; harness-file creation for PROGRESS.md, PLAN.md, DIAGNOSTIC.md, SESSION_LOG.md) lists. GT-6 worked example (2 incidents) is still present.
- **B3 — §3.2 step 3 transcript pinning:** **Resolved.** Step 3 now requires all three components: (a) full text of every user/agent turn, (b) every tool-call name + arguments + result, (c) every sub-agent dispatch prompt + return artifact. Marked-boundary copy-paste fallback explicitly allowed for harnesses without native export; anything less invalidates the run.
- **B4 — §1 hard-gate language:** **Resolved.** §1 now reads "No r7 firmware edit may ship until this results file exists, is fully filled, and is accepted as the r6 baseline. The §1.5 regression gate fires at a later stage against r7 results." The old "gate decision in §5" language is fully removed.

### 7.3 Polish status

- **A — §4.6 pre-flight/post-hoc examples:** **Applied.** Both sentences present verbatim: "Example of pre-flight verification that does NOT count: the agent reviews its own draft once before returning it to the user. Example that DOES count: the worker returns its artifact, then the main session re-enters worker-mode to re-check that artifact instead of dispatching a judge."
- **B — Scaffold stop-condition slot:** **Applied.** A `- Stop condition:` bullet is present in every per-task per-model block.

### 7.4 Residual concerns

One minor scaffold inconsistency (does not block execution):

- The results scaffold's "Gate Decision" footer (line ~478) still contains a `**Reference model (per runbook §5):**` field. Since B1 removed the reference-model concept from §5, this field is now orphaned — a scorer filling the scaffold will not know what to put there. Recommend either (a) deleting the line, or (b) replacing it with `**Reference (per runbook §5):** n/a — Phase 0 establishes per-model baselines; no cross-model reference is computed.` This is a fill-time ambiguity, not an execution blocker, so it does not gate ship; flag for the next scaffold polish pass.

No other residual concerns. Operator can execute cold.

### 7.5 Count check

`- Stop condition:` bullets in `evaluation/results-r6-baseline-multimodel-2026-04-17.md`: **28** (7 tasks × 4 models, exact).

---

**End of re-judgment.**
