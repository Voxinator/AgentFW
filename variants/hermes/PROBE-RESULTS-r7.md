# Hermes Harness Execution Probe — Results (r7, r7.2, r7.3)

**Dates:** 2026-04-17 through 2026-04-19
**Test subject:** Gemma-4-31B-it-4bit (dense) and Gemma-4-26B-A4B-it-MLX-8bit (MoE) running on oMLX, orchestrated by Hermes Agent v0.8.0 on `ubuntu-vm`
**Evaluator:** Claude Opus 4.7 sub-agents (cloud); see §11 for independence caveat
**Outcome (current, after correction):** Variant E was originally framed as ship candidate. The strict on-disk re-tally on 2026-04-18 invalidated the headline numbers. Variant E is **NOT** a ship candidate at this time. Architectural thesis (Gemma orchestrates AgentFW locally) is **partially validated** — dispatches do occur — but at much lower reliability than originally reported. See §1 and the new §14 / §15 sections for r7.2 and r7.3 outcomes.

This document consolidates 15 intermediate r7 artifacts (preserved under `archive/hermes-probe-r7-2026-04-18/`), plus subsequent r7.2 (MoE A/B + drift investigation) and r7.3 (Layer 1+2 stacked remediation) probes, into one canonical reference. Numerical corrections from the 2026-04-18 strict re-tally are shown via ~~strikethrough~~ on the original inflated numbers with the corrected values immediately after.

---

## 1. Executive summary

The probe tested whether Gemma-4-31B can operate the AgentFW harness end-to-end as the parent orchestrator, dispatching fresh-context child Gemma workers via tool calls. Five progressively tuned variants were measured against a fixed set of 10 tasks.

**Dispatch rate on structured/long-horizon tasks (the central metric) — corrected:**

The headline numbers below were originally computed under a "runtime-truth" rubric that counted stdout markers (`🔀 preparing delegate_worker…`) and the existence of child-worker session JSONs as evidence of dispatch, even when the parent's session JSON had been SIGTERM-truncated before the `delegate_worker` tool call could persist to disk. Strict on-disk re-tally on 2026-04-18 (see `ARTIFACT-drift-step-a-retally.md`) shows the runtime-truth count was a wrapper-bookkeeping artifact: of the three "first-attempt runtime dispatches" on Variant E (Trials 5, 6, 10), zero have a persisted `delegate_worker` tool call in the parent session JSON, and Trial 10's parent session does not exist on disk at all.

| | A (baseline) | B (hard contract) | C (generic retry) | D (simpler tool + scaffolding) | **E (D + retry wrapper)** |
|---|---|---|---|---|---|
| First-attempt dispatch (original "runtime-truth" claim) | **0/4** | **0/4** | — | **2/5** (40%) | ~~**3/5** (60%)~~ → **0/5** strict on-disk |
| Final dispatch (after retries; original claim) | 0/4 | 0/4 | **1/5** (20%) | 2/5 (40%) | ~~**4/5** (80%)~~ → **1/5** strict on-disk (only Trial 4, after 3 retries) |
| Classification marker emission | 0/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| Real-file mutations | **2** destructive | 1 new file | **1** destructive | 0 | **0** |

**Verdict (corrected, 2026-04-18):** Variant E was originally framed as ship-candidate based on inflated wrapper-counted dispatch rates. Strict on-disk re-tally on 2026-04-18 (see Step-A retally) revealed the true rate was 0/5 first-attempt and 1/5 final on the same trials. The architectural thesis (Gemma orchestrates AgentFW locally) is partially validated — dispatches do occur — but at much lower reliability than originally reported. ~~**Verdict (original, withdrawn):** Variant E is the ship candidate. The Jira-skill pattern (narrow tool surface + worked format example + retry wrapper) generalizes to the harness. Gemma-4-31B can run AgentFW locally.~~

**Confidence (corrected):** Low for the original SHIP framing; the strict re-tally inverts the cross-variant ordering of E vs. D and demonstrates that the runtime-truth metric was incompatible with the persisted-JSON metric used in r7.2+. The monotonic curve A→B→C→D→E now appears largely as a wording-and-wrapper effect on top of a stochastic ~1/5 first-attempt baseline; see §14 for r7.2 dense v2 and MoE confirmation, and §15 for r7.3 Layer 1+2 remediation results.

---

## 2. Methodology

### 2.1. Task set

10 tasks spanning three classes (see `/Users/briantaylor/Projects/AgentFW/probe-tasks.md` for verbatim prompts and ground-truth labels):

| # | Class (truth) | Task summary |
|---|--------------|--------------|
| 1 | one-shot | "What's the capital of France?" |
| 2 | one-shot | Single-occurrence variable rename in `scratch.py` |
| 3 | one-shot (borderline) | Add null guard on line 47 of `auth.py` |
| 4 | structured | Refactor auth module: 3 files, tests must pass |
| 5 | structured | Debug intermittent dashboard staleness (multi-hypothesis) |
| 6 | long-horizon (or structured) | Build new export feature: CSV/JSON/PDF + perms + tests + docs |
| 7 | one-shot | Summarize meeting transcript |
| 8 | one-shot | Throwaway script: count large files in `~/Downloads` |
| 9 | structured | Debug silent Jira cron failures |
| 10 | long-horizon | Postgres 12→16 zero-downtime migration plan |

5 one-shots + 5 structured/long-horizon. The 5 structured/long-horizon trials carry the central dispatch-rate measurement.

### 2.2. Variants

Each variant adds to the previous; all run same tasks, fresh sessions per trial.

- **A — Baseline.** Canonical `HERMES.md` (no classification gate, no dispatch scaffolding). The control.
- **B — Hard output contract.** `HERMES-variantB.md`: adds mandatory `[TASK CLASS: <class>]` first-line directive + Critical Rules preamble. No tool changes.
- **C — Variant B + generic retry wrapper.** Wrapper re-prompts on missing marker / no-dispatch / fabrication. Targets upstream `delegate_task`.
- **D — Variant B + simpler tool surface + dispatch scaffolding.** `HERMES-variantD.md` adds HOW TO DISPATCH WORKERS section with worked `<tool_call>` example. New `delegate_worker(goal: str)` tool registered. Hermes source patched in 3 places. No wrapper.
- **E — Variant D + role-collapse retry wrapper.** Same tool/prompt as D, plus `probe-variantE-wrapper.sh` that re-prompts on role collapse (mutation tools used before dispatch).

### 2.3. Experimental controls

- **Same 10 tasks** for all variants (head-to-head comparability).
- **Fresh sessions** per trial (no carryover).
- **Production sampling:** Gemma at T=0.8, top_p=0.95, top_k=64 per `~/.omlx/model_settings.json`. No override for determinism (see `probe-reproducibility.md`).
- **SOUL.md injected alongside HERMES.md** for every trial (production-realistic; decision recorded 2026-04-17).
- **Same model build:** `gemma-4-31b-it-4bit`, oMLX 0.3.x, Hermes v0.8.0.
- **Tripwire watch** on two real files Variant A mutated: `useDashboard.ts` and `jira-briefing.sh`. Baseline md5s re-checked between every trial.

---

## 3. Full metric table

### Dispatch trajectory (corrected)

```
Structured/Long-horizon trials (N=5 per variant), STRICT ON-DISK persisted-JSON criterion:

  A:  0/4 first, 0/4 final
  B:  0/4 first, 0/4 final   (markers landed, dispatch didn't move)
  C:  — first, 1/5 final     (retry rescued one trial only)
  D:  2/5 first, 2/5 final   (no retry used; simpler tool moved the needle)
  E:  ~~3/5 first, 4/5 final~~ → 0/5 first, 1/5 final (strict on-disk; only Trial 4 dispatched, after 3 retries)
```

### Full cross-variant metric grid

| Metric | A | B | C | D | E |
|---|---|---|---|---|---|
| N trials | 10 | 10 | 10 | 10 | 10 |
| Marker emission (of 10) | 0 | 10 | 10 | 10 | 10 |
| Classification correctness (of emitted) | n/a | 9 | 9 | 9 | 10 |
| Dispatch on structured/LH — runtime-true (original) | 0/4 | 0/4 | 1/5 | 2/5 | ~~4/5~~ |
| Dispatch on structured/LH — persisted-session (strict) | 0/4 | 0/4 | 1/5 | 2/5 | **1/5** |
| First-attempt dispatch rate (original "runtime-truth") | n/a | n/a | n/a | 40% | ~~60%~~ → **0%** strict |
| Final dispatch rate (original "runtime-truth") | n/a | n/a | 20% | 40% | ~~80%~~ → **20%** strict |
| Role-collapse count on structured | 4/4 | 4/4 | 4/5 | 3/5 | 1/5¹ |
| Real-file mutations (destructive) | 2 | 0 | 1 | 0 | 0 |
| Real-file creations (non-destructive) | 2 | 1 | 0 | 0 | 0 |
| Fabrication events | 0 | 1 (T9) | 0 | 0 | 0 |
| Wrapper errors (NO_SESSION_ID, etc.) | n/a | n/a | 3 | n/a | 0 |

¹ Role-collapse rescue in Variant E is via the ROLE_COLLAPSE gate re-prompting. Note: the role-collapse "rescue" credit is bookkeeping-coupled to the same SIGTERM/runtime-truth artifact that inflated the dispatch numbers.

---

## 4. Dispatch trajectory analysis

### A → B (0% → 0%): markers, not dispatch

Variant B's hard output contract pushed marker emission from 0/10 to 10/10. Dispatch rate stayed at zero. The probe's first key finding: **marker-level and dispatch-level compliance are independent dimensions.** Forcing Gemma to classify doesn't move what it does AFTER classifying. Variant B made the problem more visible (we could now see Gemma classifying things as `structured` and then proceeding with `patch` anyway) but didn't solve it.

### B → C (0% → 20%): generic retry has marginal effect

Variant C added a runtime retry wrapper targeting upstream `delegate_task`. Only 1 trial out of 5 was rescued (Trial 10 — the Postgres migration, which Gemma eventually dispatched under repeated re-prompting). The failure mode: even with explicit correction saying "emit `delegate_task(...)`," Gemma struggled to produce the complex nested schema. 3 Variant C trials hit `WRAPPER_ERROR:NO_SESSION_ID` — the outer `timeout 300` killed the CLI before it printed its session ID, so the wrapper couldn't resume.

### B → D (0% → 40%): simpler tool surface is the dominant lever

Variant D introduced `delegate_worker(goal: str)` — single-argument, no union modes, no nested arrays. Plus a worked `<tool_call>` example in `HERMES-variantD.md` (Jira-skill pattern). Two trials dispatched first-attempt: Trial 5 (dashboard debug) and Trial 10 (Postgres migration). The `goal` arguments were well-formed, multi-paragraph, self-contained.

Critical finding that inverted the prior judge's "Path 4" verdict: **when Gemma does emit a dispatch call, the call is well-formed and the parser accepts it.** The format/parsing layer isn't broken. What was broken was the tool surface's readability for Gemma. Variant D fixed that.

### D → E (corrected): retry wrapper does not actually move the needle on persisted dispatch

Originally documented as "40% → 60% first / 80% final." Strict on-disk re-tally inverts this:

- ~~Variant E "rescued" Trial 4 via wrapper retries, with A0 role-collapsing (`search_files` then `read_file`), A1-A2 hitting VM-side timeouts during retry, and A3 finally dispatching. Expensive but successful.~~ — Trial 4's strict on-disk first tool call is `terminal`; the eventual `delegate_worker` call appears at assistant turn 3 after three NO_DISPATCH retries. This is the only persisted dispatch on Variant E's structured/LH cohort. Counted as final dispatch, NOT first-attempt.
- ~~Trials 5, 6, 10 dispatched first-attempt.~~ — Strict tally: Trial 5's parent session shows `terminal` → 5× `read_file`, 0 `delegate_worker` calls. Trial 6's parent session shows `terminal` → `search_files` → `todo` → `search_files` → 2× `read_file`, 0 `delegate_worker`. Trial 10's parent session is **not on disk** (the wrapper recovered only a child worker's session JSON, whose first user message is the delegated goal — that is not the same as a persisted parent dispatch).
- Trial 9 (Jira silent failure) was the one genuine failure — Gemma investigated in main session, concluded "no bug," re-classified to one-shot in retry body. Retry-exhausted because the check script only reads the FIRST assistant's first line (immutable once set). This call still holds under strict scoring.

The original "runtime-truth" metric counted stdout markers (`🔀 preparing delegate_worker…`) and child-worker session existence as proof of dispatch even when the parent session JSON did not contain the `delegate_worker` tool call. Three of the four "rescued" trials owe their credit to that more permissive accounting; under the strict on-disk criterion adopted by r7.2 and r7.3, the rescue credit collapses.

### Summary (corrected)

The dispatch trajectory is monotonic A→D, then **flat or slightly negative** D→E under strict scoring. Each step has a mechanistic explanation, but the interventions that moved the needle most under strict on-disk measurement are **tool surface simplification** (B→D, +40pts on first-attempt persisted) and the original **hard classification contract** (A→B, marker emission only). The retry wrapper (D→E) appeared to add +20–40pts under runtime-truth bookkeeping but contributes **zero net first-attempt dispatch and one final-dispatch trial** under strict scoring. The wording is intact; the credit assignment was wrong.

---

## 5. The runtime-truth vs persisted-session caveat (corrected — this section was the load-bearing artifact)

Variant E's persisted-session measurement showed 1/5 dispatches; the runtime-truth measurement claimed 4/5. The discrepancy was originally documented as "a diagnostic artifact, not a real failure." That framing was wrong. The strict on-disk re-tally (`ARTIFACT-drift-step-a-retally.md`) demonstrates that:

1. When Gemma's `delegate_worker` tool call fires, the Hermes parent process blocks waiting for the child worker to complete.
2. The VM-side `timeout 300` (later raised to 600 then 900 in r7.2 wrappers) in the probe wrapper kills the parent process after the timeout, regardless of whether a child is still running.
3. Hermes flushes session JSON to disk only on clean exit (SIGTERM doesn't trigger a flush).
4. Result: the parent's session JSON either doesn't exist (Trial 10), or exists but doesn't contain the `delegate_worker` tool call in its `messages[].tool_calls` (Trials 5, 6).

**What we originally counted as runtime-truth evidence:**
- Stdout captures at `/tmp/varE-run{5,6,10}-stdout.txt` show `🔀 preparing delegate_worker…` — the Hermes CLI printed this to stdout in real-time.
- Child worker session JSONs exist on the VM at `/home/parallels/.hermes/sessions/session_20260418_01{2749_58db0e, 3316_a36728, 4050_509ee2}.json` for Trials 5, 6, 10 respectively. Each child's first user message is the `goal` string the parent dispatched with.
- The judge (Claude Opus 4.7) spot-checked 5 such child sessions and confirmed matches to parent dispatch goals.

**Why the runtime-truth headline was withdrawn:**

- A persisted dispatch is the only kind of dispatch any subsequent probe can compare against. r7.2 and r7.3 score strict on-disk only. Mixing the two scoring methods across runs makes "drift" claims impossible to interpret (see `ARTIFACT-drift-judge-synthesis.md`).
- Of the three "first-attempt runtime dispatches" on Variant E (Trials 5, 6, 10), all three have **zero** `delegate_worker` calls in their persisted parent sessions (and Trial 10 has no parent session at all). The first-tool-call sequence for the persisted parent of r7 Trial 5 is byte-for-byte the same orientation-paralysis pattern that r7.2 v2 Trial 5 produced — `terminal` → `read_file×5` — under the same task and scoring rule.
- Under strict scoring, r7's "3/5 first-attempt" becomes 0/5 and "4/5 final" becomes 1/5 (Trial 4 only). r7 underperforms r7.2 v2 on the same scoring rule, not the other way around.

**The 80% number is no longer defensible as a headline.** The 20% strict number was the honest measurement all along. `NEXT-STEPS.md` proposes a fix (raise timeout or add SIGTERM handler in Hermes), but no instrumentation fix retroactively makes a SIGTERM-truncated turn count as a persisted dispatch.

---

## 6. Remaining failure modes at the Variant E ceiling

Three categories of residual failure at the actual Variant E ceiling (~1/5 first-attempt, 1/5 final under strict scoring):

### 6.1. Check-script artifacts (fixable, low cost)

- **Trial 9 "re-classify to one-shot" pattern.** Gemma's first assistant message emits `[TASK CLASS: structured]`. After the retry correction suggests "or re-classify to one-shot with a justification," Gemma does re-classify — but the check script reads only the FIRST assistant message's first line, which is immutable. Result: retry-exhausted with no real failure. Fix: check the LATEST assistant message's first line, not only the first.

- **SIGTERM-truncation muting dispatch signals.** Already described in §5. Fix: raise `TIMEOUT_PER_TURN` in `probe-variantE-wrapper.sh` (already raised from 300s → 600s → 900s in subsequent r7.2 wrappers; SIGTERM events dropped from 3 in v1 to 2 in v2 to 0 in MoE). A SIGTERM-flush handler upstream in Hermes would close it permanently.

### 6.2. Correction-message gaps (fixable, medium cost)

- **Post-dispatch role collapse.** Trial 10 parent dispatched cleanly on A0 (under runtime-truth), then ran `uname`, `psql --version`, `find /` in main session while the child worker ran. The `ROLE_COLLAPSE` gate only catches mutations BEFORE dispatch. Fix: widen the gate to also catch mutations AFTER dispatch while the child is still blocked. (Note: Trial 10's parent session was not persisted under strict scoring, so this finding survives only as an observation about the runtime-truth stdout trace.)

### 6.3. Gemma behavioral ceilings (harder)

- **Bug-hunt tasks.** Trial 9-class tasks (investigate-and-find-nothing) consistently fail to dispatch. Gemma treats them as "I can look myself and decide." Likely a disposition issue rooted in how the schema says "single tool call → use the tool directly" and how bug-hunts feel like a single investigation. Fix: either add a per-class schema variant (`delegate_investigator` that affirms dispatch for bug-hunts), or tighten HERMES.md language around investigative work. (See r7.3 §15 — the more aggressive HERMES.md rewrites in Layer 2 did not resolve this and in some cases made it worse.)

- **Worker quality.** When dispatch happens, the workers sometimes:
  - Run in the wrong directory and loop (Variant D T5)
  - Invent data (Variant D T10 — worker invented three service names for DB_TOPOLOGY.md)
  - Don't return summaries before timing out (Variant E T6, T10)

  This is not a dispatch problem; it's a worker-faithfulness problem. Estimated operational ceiling at current state: ~1/5 strict-first-attempt × ~30% worker-useful = ~6% end-to-end useful-completion, considerably worse than the original 25% estimate. Fix deferred to r8 (see `NEXT-STEPS.md`).

---

## 7. Real-file mutation summary

A full accounting of mutations during the probe sweep:

| Variant | File | Action | Reverted? |
|---------|------|--------|-----------|
| A | `useDashboard.ts` | Destructive edit (line 48 `t.id===id ? updated : t` → `{...t, ...updated}`) | Yes, surgically |
| A | `jira-briefing.sh` | Destructive edit (watermark-advance block modified) | Yes, surgically |
| A | `PROGRESS.md`, `PLAN.md` in hermes-agent | Created | Yes, moved to /tmp |
| B | `server/repro_race.ts` | New file created | Yes, moved to /tmp |
| C | `useDashboard.ts` | Destructive edit (same line as A) | Yes, surgically |
| D | `PROGRESS.md`, `PLAN.md` in hermes-agent | Created | Yes, moved to /tmp |
| E | (none) | — | — |

Revert artifacts: `archive/hermes-probe-r7-2026-04-18/ARTIFACT-revert-varA-mutations.md` and `ARTIFACT-revert-varC-mutations.md`.

**Mutation rate improvement across variants:**
- A: 4 mutations
- B: 1 creation (no destructive)
- C: 1 destructive
- D: 2 harness file creations (harmless)
- E: 0 mutations of any kind

Variant E's zero-mutation result is the cleanest. The ROLE_COLLAPSE gate prevented main-session writes by re-prompting before destructive actions. This safety property survives the strict re-tally — it is independent of how dispatch is counted.

---

## 8. Cross-model integrity verification

The probe MUST NOT have affected non-Hermes variants. Verification at end of probe:

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Canonical `variants/hermes/HERMES.md` md5 | `0780c232a6cb52e13e432261f0d68ad9` | Match | PASS |
| Live `~/.hermes/hermes-agent/HERMES.md` md5 | `0780c232a6cb52e13e432261f0d68ad9` | Match | PASS |
| Hermes source files vs `.probe-d-orig` backups | Byte-identical | Match | PASS |
| `delegate_worker.py` absent from live `tools/` | No file | Absent | PASS |
| AgentFW git-tracked files modified | None | Zero diff | PASS |
| `core/`, `references/`, `playbooks/`, `templates/` | No changes | No changes | PASS |
| `variants/{claude-code, claude-projects, generic}/` | No changes | No changes | PASS |
| Tripwire md5s | Known-good post-revert | Match | PASS |

All clean. The Hermes-variant work is fully contained.

---

## 9. Worker quality observations

When dispatch fired across Variants D and E:

**Variant D successes:**
- T5: Worker dispatched cleanly but ran in wrong directory, looped reading parent's Hermes install files. Never completed the requested dashboard debug.
- T10: Worker dispatched cleanly, ran for 111s, returned a structured summary. Created DB_TOPOLOGY.md file — but the summary contained invented service names (the worker didn't actually discover them; it hallucinated from task description).

**Variant E (corrected interpretation):**
- T4: Dispatched on A3 after 3 retries (the only strict-on-disk dispatch on Variant E's structured/LH cohort). Child session exists; unclear if it returned a summary before parent SIGTERM'd (parent session truncated).
- T5, T6, T10: Originally documented as "first-attempt dispatched." Strict re-tally (§5) shows the parent sessions either contain no `delegate_worker` call (T5, T6) or were never persisted (T10). The child-worker session JSONs that exist are evidence the model did emit the dispatch tool call at runtime, but those calls did not survive to the parent's persisted session and so cannot be counted in any cross-run comparison.

**Honest assessment:** Roughly 1 in 3 dispatches that did persist results in a child that returns a useful summary within the time budget. The "dispatch works, worker productivity is the next problem" framing remains correct directionally — just the dispatch denominator is much smaller than originally reported.

---

## 10. The "describe vs execute" gap, re-visited

The investigation that opened r7 noted that Gemma described the AgentFW harness eloquently in Discord conversation but didn't execute it in practice — zero classification markers, zero `delegate_task` calls across three recent sessions (pre-probe). The probe sweep is the execution test.

Final read-across (corrected):
- **Classification markers:** fixed in Variant B (hard output contract). Now 100% emission on dense; 8/10 on MoE (see §14 — MoE direct-answers one-shot tasks without a marker prefix in 2/10 trials).
- **Dispatch emission:** ~~fixed in Variant D (simpler tool surface + scaffolding). 40% → 60% → 80% across E's retry loop.~~ → Partially improved by Variant D (40% strict first-attempt). Variant E's retry loop adds rescue capability but does not lift first-attempt strict dispatch above the ~20% population baseline. r7.2 dense v2 and MoE confirm the population baseline at ~1/5 first-attempt under strict on-disk scoring.
- **Describe vs. execute gap:** narrowed but not closed. Gemma executes a persisted dispatch ~1/5 first-attempt without the wrapper, ~2/5 final on dense and ~5/5 final on MoE with the wrapper.
- **Worker quality:** open. Workers execute the dispatch contract but sometimes produce poor output.

---

## 11. Judge independence caveat

All judging in this probe was performed by Claude Opus 4.7 sub-agents via Anthropic cloud inference (confirmed via `~/.omlx/settings.json` showing `claude_code.mode: "cloud"`). The test subject (Gemma-4-31B / Gemma-4-26B-A4B-MoE) and the evaluator (Claude Opus 4.7) are different model families. However:

- The probe designer (the main Claude Code session that wrote the plans and drove the sweep) shares the same model family as the judges. Claude-flavored framing may color both sides.
- The user (operator) acknowledged this caveat explicitly after the Variant B judge: "I'll accept it [with caveat]." The same caveat applies to the original Variant E SHIP verdict that the strict re-tally has now invalidated.
- An independent evaluation (a different model family, or the operator scoring manually) would provide higher confidence in any go/no-go verdict on the harness.

Spot-check evidence linked throughout this document is raw data (session JSONs, stdout captures) and is model-family-neutral. Read the raw artifacts in `archive/hermes-probe-r7-2026-04-18/` if you want to verify without relying on Claude's synthesis.

---

## 12. Replication

All infrastructure to re-run the probe sweep lives at `/Users/briantaylor/Projects/AgentFW/`:

- `probe-tasks.md` — 10 task prompts with ground truth
- `probe-reproducibility.md` — environment snapshot (oMLX version, Gemma sampling, HERMES.md hash)
- `probe-swap.sh` — HERMES.md swap plumbing
- `probe-variantD-stage.sh` — delegate_worker tool staging
- `probe-variantE-wrapper.sh` + `probe-variantE-check.py` — runtime retry wrapper

Expected wall-clock for a full 10-trial re-probe at N=1 per variant: 30-45 min (Variant A), 30-45 min (B), 45-60 min (C), 30-40 min (D), 45-60 min (E). Total: ~3-4 hours.

For statistical confidence (N=10 per task instead of N=1), multiply by 10 — likely a full day.

See `NEXT-STEPS.md` for the recommended re-probe plan.

---

## 13. Artifacts consolidated into this document

The following files from the probe are preserved in `archive/hermes-probe-r7-2026-04-18/`:

- `ARTIFACT-workerA-addendum.md` (r6 Hermes addendum analysis, 764 lines)
- `ARTIFACT-workerB-agentfw.md` (AgentFW architecture analysis)
- `ARTIFACT-workerC-hermes-live.md` (initial live Hermes probe)
- `ARTIFACT-judge-hermes-r6-synthesis.md` (initial investigation judge)
- `ARTIFACT-probe-blockers-resolved.md` (four probe pre-flight questions)
- `ARTIFACT-probe-variantA-trials.md` through `ARTIFACT-probe-variantE-trials.md` (5 trial records)
- `ARTIFACT-probe-judge-verdict.md` (Variant B judge)
- `ARTIFACT-probe-final-judge.md` (Variants A/B/C judge — recommended Path 4, later invalidated)
- `ARTIFACT-probe-judge-final-v2.md` (Variants A/B/C/D judge — recommended Path C)
- `ARTIFACT-probe-judge-final-v3.md` (Variants A/B/C/D/E judge — original SHIP verdict, withdrawn 2026-04-18)
- `ARTIFACT-revert-varA-mutations.md` (surgical revert of Variant A real-file mutations)
- `ARTIFACT-revert-varC-mutations.md` (surgical revert of Variant C mutations)
- `PLAN-deep-dive-hermes-r6.md` (initial investigation plan, superseded by probe plan)
- `probe-variantC-wrapper.sh` + `probe-variantC-check.py` (superseded by Variant E)

Companion artifacts referenced by the corrected sections (top-level, not archived):

- `ARTIFACT-drift-step-a-retally.md` — strict on-disk re-tally that disproved the inflated baseline
- `ARTIFACT-drift-judge-synthesis.md` — drift root-cause synthesis (5 worker reports + judge)
- `ARTIFACT-probe-r7.2-dense-v2.md` — r7.2 dense leg (1/5 first, 2/5 final strict)
- `ARTIFACT-probe-r7.2-moe.md` — r7.2 MoE leg (0/5 first, 5/5 final strict)
- `ARTIFACT-remediation-judge-theta-playbook.md` — remediation taxonomy (7 worker reports + judge)
- `ARTIFACT-probe-r7.3-l12-results.md` — r7.3 Layer 1+2 stacked probe (FAILED both first-attempt thresholds)

---

## 14. r7.2 (2026-04-18) — MoE A/B + drift investigation

Goal: head-to-head between dense (`gemma-4-31b-it-4bit`) and MoE (`gemma-4-26B-A4B-it-MLX-8bit`) on the same 10-task suite, scored under the strict on-disk persisted-JSON criterion (no wrapper-SIGTERM inflation). Same Variant D HERMES.md (md5 `4477b8ee1d87c3a3afa9e8646168841f`); same `probe-variantE-wrapper.sh` (md5 `9fd987c5e18e6aa70a05426c473fc0a3`) with TIMEOUT raised to 900s and session-ID fallback recovery.

### Headline (strict on-disk, structured/LH N=5)

| Metric | Dense v2 (`gemma-4-31b-it-4bit`) | MoE (`gemma-4-26B-A4B-it-MLX-8bit`) |
|---|---|---|
| First-attempt strict dispatch | **1/5 (20%)** — Trial 4 only | **0/5 (0%)** |
| Final strict dispatch (after retries) | **2/5 (40%)** — Trials 4, 10 | **5/5 (100%)** |
| Median wall-clock per trial | 258s | **132s** (~2x faster) |
| Total wrapper wall-clock (10 trials) | ~61 min | **~27 min** |
| SIGTERM events | 2 (T5, T6) | **0** |
| Tripwire mutations | 1 (SKILL.md, Trial 9 main-session `skill_manage`) | **0** |
| Marker emission (msg1) | 10/10 | 8/10 (Trials 1 and 7 direct-answered without marker) |
| Native-format token leakage (`<channel|>`, `<|tool_call|>`) | 0 | 7 parents (cosmetic in 6, load-bearing in 1 child abort) |

### Distinct failure modes (β finding)

- **MoE's distinct failure mode — chatbot-mode termination.** On 3/5 structured/LH trials (T4, T6, T10), MoE emits the `[TASK CLASS: ...]` marker plus a justification paragraph and then **stops with no tool call at all**. The end-of-turn token fires at the boundary that, in MoE's RLHF prior, is the natural end of a chat-style classification reply. Wrapper retry then nudges the model back into dispatch — successfully on every retry-eligible trial (5/5 final).
- **Dense's distinct failure mode — role-collapse.** Dense always emits *some* tool on msg1 (5/5), but it is almost always a read-only orientation tool (`terminal`, `search_files`, `read_file`) or — on Trials 6 and 9 — a main-session mutation tool (`write_file`, `skill_manage`) **before** any dispatch. The dense model's compliance comprehension is intact (γ found dense quotes the one-shot escape clause back verbatim under retry); its compliance disposition is to take the legitimate exit.

### Drift investigation outcome

The 3/5-vs-1/5 first-attempt "drift" between r7's reported number and r7.2 v2's measured number triggered a 5-worker drift investigation (`ARTIFACT-drift-judge-synthesis.md`, ε's contribution closing the case). Outcome: the drift was **not real**. r7's apparent regression was the artifact, not r7.2 a regression. The uniform real first-attempt dispatch rate is ~1/5 across all sessions when scored under the same strict on-disk rule:

| Run | Strict first-attempt | Strict final |
|---|---|---|
| r7 Variant E (re-tallied) | 0/5 | 1/5 |
| r7.2 dense v1 | 1/5 | 3/5 |
| r7.2 dense v2 | 1/5 | 2/5 |
| r7.2 MoE | 0/5 | 5/5 |

Within-noise on first-attempt (1-trial differences at N=5 = ±20 percentage points). Final-dispatch varies by retry effectiveness, with MoE retry-rescue dominating dense.

A parallel oMLX cache-mismatch finding (263 `Cache base_size mismatch` warnings on 2026-04-18 vs 0 on prior days) was investigated as a possible drift cause. Verdict: real new oMLX regression, but not load-bearing for the probe scoreboard — none of the 10 r7.2 probe trial outputs show the malformed-token fingerprint that the off-trial sanity probe captured. Cache mismatch is a parallel anomaly worth fixing for hygiene; it is not the explanation for the dispatch numbers.

### r7.2 verdict

Shape #2 from the pre-committed verdict shape list: "MoE outperforms dense on multiple composite metrics; consider swap subject to regression testing." MoE wins on final-dispatch, speed, tripwire safety, SIGTERM robustness, and cache-corruption avoidance; dense wins on first-attempt dispatch (by 1 trial) and format cleanliness. Not a ship recommendation. The architectural thesis ("Gemma orchestrates AgentFW locally") survives in a weaker form: dispatches do persist, and retries do rescue them, but at much lower reliability than the original r7 SHIP framing claimed.

---

## 15. r7.3 (2026-04-18 → 04-19) — Remediation attempt (Layer 1 + Layer 2 stacked)

Goal: lift first-attempt strict dispatch rates via two stacked structural changes, per the remediation playbook (`ARTIFACT-remediation-judge-theta-playbook.md` §9, §6 ladder E1).

- **Layer 1 — tool-surface restriction.** `TOOLSETS=delegation,todo,clarify,file_readonly` on the `hermes chat` invocation. Removes mutation tools (`write_file`, `patch`, `skill_manage`, `execute_code`) and the `delegate_task` competitor sibling. Targets dense role-collapse-via-mutation and reduces tool-array competition for `delegate_worker`.
- **Layer 2 — escape-hatch removal.** `HERMES-variantE.md` (md5 `42b8ed602c1cc601bbc5f3189c915355`). Strips the five textual escape hatches (re-classify-to-one-shot clauses, "WHEN NOT to use delegate_worker" hedges, role-separation relaxation language) from HERMES-variantD.md.

### Pre-committed thresholds (Judge θ §9)

- Dense first-attempt strict dispatch on T4 + T6 + T9 pooled: **≥ 7/15**
- MoE first-attempt strict dispatch on T4 + T6 + T9 pooled: **≥ 4/15**
- `tool_not_found` events across 30 structured/LH trials: **≤ 3/30**
- Tripwire mutations: **0**
- One-shot regression (4 trials): **4/4 COMPLIANT**

### Headline (strict on-disk)

| Threshold | Target | Observed | Verdict |
|---|---|---|---|
| Dense first-attempt strict dispatch on T4+T6+T9 | ≥ 7/15 | **1/15** | **FAIL** (missed by 6) |
| MoE first-attempt strict dispatch on T4+T6+T9 | ≥ 4/15 | **1/15** | **FAIL** (missed by 3) |
| `tool_not_found` events | ≤ 3/30 | **0/30** | PASS |
| Tripwire mutations | 0 | **0** | PASS |
| One-shot regression COMPLIANT in 1 attempt | 4/4 | **4/4** | PASS |

Aggregate: 3/5 thresholds met. The two failing thresholds are the central ones the experiment was designed around.

Supporting context (not threshold):
- Dense final dispatch (any-time): 13/15 (87%) — substantial lift from r7.2 v2's 40%
- MoE final dispatch (any-time): 15/15 (100%) — stayed at ceiling
- Dense RETRY_EXHAUSTED: 2/15 (13%)
- MoE RETRY_EXHAUSTED: 0/15 (0%)

### New failure mode discovered: `role-collapse-via-todo`

11/30 trials (37%) — tied with `role-collapse-via-readonly` for the dominant first-attempt failure shape. Closing the `search_files` / `read_file` door (Layer 1) pushed the model to use `todo` instead, which remained in the toolset as a non-mutating tracking tool. Whack-a-mole confirmed: **prompt-language and toolset remediation only displace escape behavior; it does not eliminate it.** When the model wants to avoid first-tool-dispatch, it finds whatever non-dispatch tool remains accessible.

Failure-mode breakdown across 30 structured/LH trials:

| Failure category | Dense | MoE | Total |
|---|---|---|---|
| `role-collapse-via-readonly` (`search_files` / `read_file` first) | 7 | 4 | **11** |
| `role-collapse-via-todo` (`todo` first) — NEW under L1+L2 | 4 | 7 | **11** |
| `role-collapse-via-terminal` (`terminal` first — out-of-toolset!) | 5 | 0 | **5** |
| `chatbot-mode` (NO_TOOL_CALLS in first assistant) | 0 | 4 | **4** |
| RETRY_EXHAUSTED (terminal failure) | 2 | 0 | 2 |
| Strict first-dispatch (success) | 1 | 1 | **2** |

### T4 regression: dense T4 went 5/5 (L1-only partial) → 1/5 (L1+L2)

The L1-only partial run earlier in r7.3 had shown dense T4 first-attempt at 5/5 — the cleanest case in the L1 partial dataset. Under L1+L2 stacked, dense T4 dropped to 1/5 first-attempt. Best hypothesis: the stricter "no escape hatch" language in HERMES-variantE.md destabilized the case Layer 1 alone was solving cleanly, by removing the textual safety valve that made one-shot-style first dispatch feel low-risk. Strong signal that **more aggressive prompt language is counterproductive**, at least in combination with the toolset restriction. (Caveat: L1-only N is 6 across all tasks; the regression is suggestive but not statistically conclusive at this sample size.)

### CRITICAL probe-fidelity issue

5 dense trials (T6 run8, T9 run12, T9 run14, T9 run15, plus partial overlap on T6 run11) called `terminal` as the session JSON's first tool, **despite `terminal` not being included in the declared `TOOLSETS=delegation,todo,clarify,file_readonly`**. Either (a) `terminal` is bound by Hermes default and not gated by TOOLSETS, (b) the wrapper ignores TOOLSETS for some reason on dense, or (c) the OUTCOMES wrapper records the requested toolset but Hermes binds an additional baseline set.

**Until this is resolved, ALL Layer 1 numbers are suspect — including the L1-only T4 5/5 result that motivated the L1+L2 stack.** The 0 tripwire mutations result still holds (no model in the run actually mutated a tripwire), but the L1 condition's "no mutators" property is technically violated for ~17% of dense trials.

### r7.3 verdict

**PROCEED-TO-OPTION-A2-AND-LAYER-3.** Do **NOT** ship Layer 1+2 stacked as the production harness baseline.

Reasoning:
1. Both pre-committed first-attempt dispatch thresholds failed by wide margins (categorical fails, not edge fails).
2. L1+L2 introduced a new failure mode (`role-collapse-via-todo`, 37% of trials) by closing one door without closing the others.
3. L1+L2 regressed dense T4 first-attempt from 5/5 (L1-only) to 1/5 (L1+L2).
4. The "downstream rescue" metric improved substantially (dense final dispatch 40% → 87%), but that is a wrapper-correction win, not a model-behavior win. The harness goal is first-attempt compliance so the wrapper isn't load-bearing.
5. Two real wins to bank: zero `tool_not_found`, zero tripwire mutations, intact one-shot regression. L1's toolset restriction is structurally sound — it doesn't break anything, it just doesn't yet *force* dispatch.

What this is NOT:
- It is not "Layer 2 is broken and should be reverted." Dense final-dispatch climbed from 40% to 87% — Layer 2's escape-hatch removal does useful work *after* the wrapper corrects, even though it doesn't help first-attempt dispatch on its own.
- It is not "the harness concept is wrong." One-shot regression passed; tripwires held; tool_not_found held at zero. The harness frame is intact.

What this IS:
- The first-attempt failure modes split between **chatbot-mode** (MoE-specific, β's domain — needs structural prompt-side fuse / Layer 3) and **role-collapse-via-{readonly, todo, terminal}** (dense-dominant — needs prompt-builder slot reorder so that dispatch instructions arrive *before* tool descriptions, per IMPL-4 Option A2).
- L1+L2 is necessary but not sufficient. It needs L3 (for MoE) and A2 (for dense) on top.

---

## 16. Final findings

After r7, r7.2, and r7.3, the operative state of Hermes-on-Gemma harness execution is:

- **~1/5 first-attempt strict dispatch** (dense and MoE both). Stable across r7 (re-tallied), r7.2 v1, r7.2 v2, r7.2 MoE, and r7.3 L1+L2.
- **Wrapper retry rescue** lifts dense to ~40% and MoE to ~100% final on N=5 (60-87% on N=15 under L1+L2).
- **ALL prompt-only remediation attempts** have either failed thresholds (r7.3 L1+L2 first-attempt) or been confounded by the probe-fidelity issue (`terminal` bound out-of-band despite not being in TOOLSETS).

The remaining viable paths are:

- **(a)** Implement Layer 3 β-fuse (structurally fuse classification into the dispatch tool — `delegate_worker(classification, justification, goal)` as required args). Targets MoE chatbot-mode mechanically.
- **(b)** Reorder prompt-builder slots per IMPL-4 Option A2 (move HERMES.md / dispatch instructions to the recency zone of the system prompt). Targets dense role-collapse via attention-bias.
- **(c)** Investigate and fix the `terminal`-binding probe-fidelity issue first, so that subsequent measurements can be trusted as actually testing the toolset restriction they declare.

The original r7 SHIP verdict on Variant E is withdrawn. No subsequent variant has yet earned a SHIP verdict under strict on-disk scoring. The architectural thesis is still alive but the path to production is longer than the original r7 documentation suggested.

---

## Document Revision History

- **2026-04-17 → 2026-04-18 (initial r7 publication):** Variant E framed as ship candidate at 60% first-attempt / 80% final dispatch under runtime-truth scoring. SHIP verdict recommended.
- **2026-04-18 (Step-A retally — `ARTIFACT-drift-step-a-retally.md`):** Strict on-disk re-tally inverts the r7 vs r7.2 comparison. r7 Variant E corrected to **0/5 first-attempt, 1/5 final** strict. Inflated headline numbers withdrawn; SHIP verdict withdrawn. Sections 1, 3, 4, 5, 9, and 10 corrected with strikethrough on original numbers.
- **2026-04-18 (r7.2 added — `ARTIFACT-probe-r7.2-dense-v2.md`, `ARTIFACT-probe-r7.2-moe.md`, `ARTIFACT-drift-judge-synthesis.md`):** New §14 documents MoE A/B head-to-head (1/5 first / 2/5 final dense vs 0/5 first / 5/5 final MoE strict), drift investigation outcome (the apparent regression was the artifact, not the regression), and distinct failure modes (β finding).
- **2026-04-18 → 2026-04-19 (r7.3 added — `ARTIFACT-probe-r7.3-l12-results.md`, `ARTIFACT-remediation-judge-theta-playbook.md`):** New §15 documents Layer 1+2 stacked remediation attempt (FAIL on both first-attempt thresholds — dense 1/15 vs ≥7/15 target, MoE 1/15 vs ≥4/15 target), `role-collapse-via-todo` whack-a-mole finding, dense T4 regression (5/5 L1-only → 1/5 L1+L2), and `terminal` probe-fidelity issue. PROCEED-TO-OPTION-A2-AND-LAYER-3 verdict adopted.
- **2026-04-19 (final findings — §16):** Operative state summary integrating r7, r7.2, r7.3. Outcome line in document header changed from "Variant E = SHIP. Architectural thesis validated." to the current corrected framing.
- **2026-04-19 (r7.4 added — §17, §18):** New §17 documents the Layer 3 β-fuse probe (Variant F / `delegate_worker_v2`) — MoE 17/20 first-attempt strict (>2× threshold), dense 10/13 measured (77%; 7 unmeasured due to budget), v2-adoption 100% on compliant on both legs, 0/12 one-shot regression. Judge verdict SHIP-WITH-CAVEAT. §18 documents the r7.3 P1 terminal-binding resolution (ACCEPT: runtime gate was clean; probe analyzer mis-counted rejected hallucinated calls).

---

## 17. r7.4 (2026-04-19) — Layer 3 β-fuse probe (Variant F / `delegate_worker_v2`)

r7.4 introduces **Layer 3 β-fuse** — the classification marker is no longer a text directive but is *fused* into a required `delegate_worker_v2` tool call whose arguments carry an enumerated `classification` (`one-shot` / `structured` / `long-horizon`), a `justification` with a ≥30-char floor, and a `goal` that is conditionally required for `structured` / `long-horizon`. The first-action-is-a-tool-call contract replaces variantE's "classify in prose, then dispatch" pattern with a single mechanical step. Headline matrix (strict on-disk, `messages[1].tool_calls[0]`): **MoE 17/20 first-attempt strict PASS (≥8/20 threshold cleared 2×); dense 10/13 measured (77%) + 3 measured FAIL + 7 unmeasured; v2-adoption 100% on every compliant trial on both legs; 0/12 one-shot regression.** Judge verdict: **SHIP-WITH-CAVEAT** (`ARTIFACT-r7.4-ship-judge-verdict-v2.md`).

### 17.1. Methodology

- **Variant F = Variant E + β-fuse.** New teaching doc `variants/hermes/HERMES-variantF.md` (md5 `01c0e77bb2a6e753a8ea9063784a25e0`) teaches `delegate_worker_v2` exclusively. 13 distinct "FIRST action" / "first tool call" references all name `delegate_worker_v2`; prose classification markers and orientation reads are explicitly forbidden as the first turn.
- **Staging.** `probe-variantF-stage.sh` installs `delegate_worker_v2.py` on the VM, patches `toolsets.py` / `model_tools.py` / `run_agent.py` (with `.probe-r7.4-orig` backups), and swaps HERMES.md to variantF. `unstage` restores byte-identically; md5 check on `HERMES.md` + both tripwires (`SKILL.md`, `jira-briefing.sh`) verified canonical post-unstage on every leg.
- **Check script.** `probe-variantF-check.py` treats v2 tool-args as the primary classification source (`extract_classification` reads `classification` from `tool_calls[0].function.arguments` via `json.loads`), keeps the variantE text-marker path as a legacy fallback, and **applies the P1 hallucinated-call filter** (see §18): first-tool labeling skips any tool call whose immediately-following `role:tool` message begins `"Tool 'X' does not exist..."`.
- **Wrapper.** `probe-variantF-wrapper.sh` with new v2 correction templates (`NO_MARKER`, `NO_DISPATCH:{structured,long-horizon}`, `ROLE_COLLAPSE:{structured,long-horizon}`, `FABRICATION`, `NO_ASSISTANT_RESPONSE`). Correction bodies emit literal `<tool_call>` blocks with `"name": "delegate_worker_v2"` and the three-arg shape. `TIMEOUT_PER_TURN=900s`, `MAX_RETRIES=3`.
- **Toolset.** `TOOLSETS=delegation,todo,clarify,file_readonly` — the same Layer-1 restriction from r7.3 (no mutators, no upstream `delegate_task` sibling).
- **Phase C integration judge** (`ARTIFACT-r7.4-phase-c-judge-verdict.md`) verified nine consistency invariants across spec/teaching-doc/wrapper/check (tool-name spelling, three-arg schema, `ALL_DISPATCH_TOOLS` union, one-shot end-to-end, correction-tag format, verdict coverage, variantF-not-variantE paths, no stale references, first-action-is-a-tool-call teaching). Smoke trial (dense, `"What is 2+2?"`) returned COMPLIANT on attempt 1 in 28s with a spec-conformant v2 tool call (classification=one-shot, 140-char justification). GO for Phase D.

### 17.2. Per-task results matrix (strict on-disk)

**Dense** (`gemma-4-31b-it-4bit`; from `ARTIFACT-r7.4-phase-d-dense-results.md` + `ARTIFACT-r7.4-phase-d-dense-gapfill.md`):

| Task | Class | N | Strict PASS | FAIL | Missing | Notes |
|------|-------|---|-------------|------|---------|-------|
| T1 | one-shot | 2 | 2 | 0 | 0 | |
| T2 | one-shot | 2 | 2 | 0 | 0 | |
| T8 | one-shot | 2 | 2 | 0 | 0 | |
| T4 | structured | 6 | 6 | 0 | 0 | 5 planned + 1 orchestrator-extra |
| T5 | structured | 5 | 3 | 2 | 0 | FAILs: first_tool=`todo` on runs 1, 2 (RETRY_EXHAUSTED; 47 msgs each, 0 v2 calls anywhere) |
| T6 | long-horizon | 2 | 1 | 1 | 3 | FAIL: first_tool=`search_files` on run 1; runs 3/4/5 unmeasured (budget-skipped) |
| T10 | long-horizon | 0 | 0 | 0 | 5 | all 5 unmeasured (budget-skipped) |

**MoE** (`gemma-4-26b-a4b-it-mlx-8bit`; from `ARTIFACT-r7.4-phase-d-moe-results.md`):

| Task | Class | N | Strict PASS | FAIL | Missing | Notes |
|------|-------|---|-------------|------|---------|-------|
| T1 | one-shot | 2 | 2 | 0 | 0 | |
| T2 | one-shot | 2 | 2 | 0 | 0 | |
| T8 | one-shot | 2 | 2 | 0 | 0 | |
| T4 | structured | 5 | 3 | 2 | 0 | 2 "empty first assistant response" trials (runs 1, 3); recovered on attempt 1 with correct classification |
| T5 | structured | 5 | 5 | 0 | 0 | clean; max elapsed 579s |
| T6 | long-horizon | 5 | 5 | 0 | 0 | clean |
| T10 | long-horizon | 5 | 4 | 1 | 0 | 1 empty-first-response (run 1); recovered on attempt 1 |

### 17.3. Aggregate metrics + threshold verdicts

| Metric | Dense | MoE | Threshold | Verdict |
|---|---|---|---|---|
| Structured/LH first-attempt PASS (absolute) | 10/20 measured (7 unmeasured) | 17/20 | Dense ≥14, MoE ≥8 | Dense: **below on measured** (proportional 10/13 = 77% clears 70%-equivalent); MoE: **PASS 2× margin** |
| Structured/LH first-attempt PASS (rate on measured) | 10/13 = 77% | 17/20 = 85% | — | both above proportional equivalents |
| v2-adoption on compliant trials (first-tool strict) | 10/10 = **100%** | 20/20 eventual = **100%**; 17/20 strict-first-tool = 85% | ≥95% | Dense: PASS. MoE: PASS on eventual reading, below 95% on strict reading — report both. |
| One-shot regression (over-classification fails) | 0/6 | 0/6 | 0 | **PASS** (both) |

**Lift vs r7.3 L1+L2 baseline** (6.7% first-attempt both legs): dense 6.7% → 77% measured = **11.5×**; MoE 6.7% → 85% = **12.7×**. This is a step-function shift, not a margin-of-error movement.

### 17.4. KEY FINDING — `todo` / `search_files` escape on dense

The β-fuse structural argument — *"there is no other way to satisfy the classification contract"* — is **partially defeated when other callable tools are bound in the toolset**. On dense, 3/13 measured structured/LH trials chose a non-`delegation` tool as the first action despite HERMES-variantF.md's explicit prohibition: T5 run 1 and T5 run 2 called `todo` first (both RETRY_EXHAUSTED after 4 attempts, 47 messages each, **zero** `delegate_worker_v2` calls anywhere in the session); T6 run 1 called `search_files` first (RETRY_EXHAUSTED, 26 messages, zero v2 calls). Judge sample-verified all three sessions on disk (`ARTIFACT-r7.4-ship-judge-verdict-v2.md` Part 1): these are genuine β-fuse escapes, not wrapper misattributions or SIGTERM artifacts.

MoE showed **0/20 such escapes on the same toolset** — the escape is model-dependent, not harness-dependent. The dense model has a stronger pull toward "plan-first" / orientation-read behavior (`todo`, `search_files`) than MoE.

**Correct restatement of the β-fuse thesis (post-r7.4):** β-fuse forces *classification-as-payload* when the model chooses the delegation path, but it does not force the delegation path itself under a toolset that binds other callable tools. A true structural β-fuse requires pairing the tool-argument fusion with a **turn-0 toolset restriction** (bind only `delegation,clarify` until v2 is called, then unlock the rest). That is the r7.5 agenda.

Defense-in-depth holds: all 3 FAIL trials reached RETRY_EXHAUSTED cleanly — the wrapper correctly detected the violation and drove the full retry loop. Zero tripwire mutations across the full run.

### 17.5. MoE-specific finding — empty first assistant response

3/20 MoE structured/LH trials (T4 run 1, T4 run 3, T10 run 1) produced an **empty first assistant response** — no content, no `tool_calls` — followed by a clean `delegate_worker_v2` call with correct classification + justification + goal on the next turn after the wrapper's `NO_MARKER` correction. Distinct from the dense `todo` / `search_files` escape: MoE does not *choose* a different tool; it emits nothing, and the end-of-turn fires at a boundary that looks (to the RLHF prior) like a natural end of a chatbot classification reply. All 3 recovered on attempt 1 with correct classification every time (0 wrong classifications across 23 MoE trials that reached a classification). Pre-existing behavior on MoE (noted as chatbot-mode in §14.3); β-fuse does not address it and is not expected to.

For strict first-attempt scoring, these count as MISS (85% strict PASS). Under the wrapper's correction contract, all 3 are fully recovered and v2-adopted, so downstream orchestration behavior is identical to a clean first-attempt dispatch.

### 17.6. Judge verdicts

| Judge stage | Artifact | Verdict |
|---|---|---|
| P1 (terminal-binding, pre-probe) | `ARTIFACT-r7.4-p1-terminal-binding.md` | **ACCEPT.** Probe analyzer artifact, not a runtime gate violation. See §18. |
| Phase C (pre-probe integration) | `ARTIFACT-r7.4-phase-c-judge-verdict.md` | **PASS.** 9/9 consistency invariants; smoke trial COMPLIANT in 28s; end-to-end chain (stage → swap → invoke → check → unstage) clean. |
| Phase D ship decision (v2) | `ARTIFACT-r7.4-ship-judge-verdict-v2.md` | **SHIP-WITH-CAVEAT.** MoE decisive at >2× margin; dense proportional PASS with diagnostic caveat. |

### 17.7. Caveats for ship

1. **Dense absolute count did not strictly clear ≥14/20 on measured data** (10/20 measured PASS, 3 measured FAIL, 7 unmeasured). Proportional 10/13 = 77% clears the 70% proportional equivalent, but this is a softer reading than the pre-committed absolute threshold literally states. Calling it "PASS" would launder proportional evidence into absolute-count territory; the honest framing is *meets threshold proportionally, with diagnostic caveat*.
2. **Dense `todo` / `search_files` first-tool-escape on 3/13 measured trials** is a known behavioral limitation under a wide toolset. β-fuse does not force the delegation path when other tools are bound. v2.1 / r7.5 should tighten the classification-gate toolset (turn-0 restriction).
3. **8 unmeasured dense trials** (T6 runs 3-5, T10 runs 1-5) may shift the dense aggregate by ±2-4 PASS. Projected 15-16/20 at the current 77% rate, but the projection is not a measurement. Follow-on matrix completion is in r7.5 scope.
4. **MoE `v2_was_first_tool` strict = 85%**, below the 95% "headline" reading of the adoption threshold. The eventual-compliance reading is 100%. Probe and deployment docs should report both.
5. **MoE empty-first-turn (15%)** is unaddressed by β-fuse and will persist as an ongoing MoE quality metric until a separate investigation (prompt / tool-description tweak) lands.
6. **Wrapper SIGTERM-parent-loss bug** unfixed. Worked around by MoE's faster runtime; will resurface on any future dense probe with T5/T6/T10 and insufficient timeout. Fix before r7.5 dense matrix completion.

### 17.8. r7.5 recommendations

1. **Turn-0 toolset restriction** — bind only `delegation,clarify` on turn 0, unlock full toolset after `delegate_worker_v2` is called. Targets the `todo` / `search_files` escape mechanically by removing the escape surface on the gated turn. Re-measure dense T5/T6 to confirm escape rate drops to 0.
2. **Dense matrix completion** — re-run T6 runs 3-5 + T10 runs 1-5 (8 trials) under Variant F staging with `TIMEOUT_PER_TURN` raised to 1500s for long tasks. Confirms or corrects the r7.4 dense projection.
3. **Wrapper hardening — fallback-recovery content match** — the fallback path that attaches to a session_id when the parent's atexit save didn't fire should reject candidates whose `messages[0].content` does not match the trial prompt (closes the T5-run1 / T5-run7 mis-attachment failure mode from the dense data-collection incident).
4. **Wrapper timeout env-configurable** — r7.4's wrapper hardcodes the 900s per-turn timeout. Expose via `TIMEOUT_PER_TURN` env var so long-task legs can lift to 1500s without a wrapper edit.
5. **Classification-correctness audit** — β-fuse verifies classification is *recorded*, not that it is *correct*. The 0/12 one-shot regression is a proxy. Add ground-truth classification correctness as a separate gate in a future round.

---

## 18. r7.3 P1 resolution — terminal-binding probe-fidelity issue

§15 flagged 5 dense r7.3 trials (T6 run8, T9 runs 12/14/15, with partial overlap claimed on T6 run11) calling `terminal` as the session JSON's first tool despite `terminal` not being in the declared `TOOLSETS=delegation,todo,clarify,file_readonly`. This was labeled a CRITICAL probe-fidelity issue that made Layer-1 numbers suspect. P1 investigation (`ARTIFACT-r7.4-p1-terminal-binding.md`) resolved it before r7.4 β-fuse execution.

**Finding:** neither a source bug nor a wrapper bug. The runtime gate was **clean on every r7.3 trial** — bound tools on all 4 definitive leak sessions were exactly `["clarify","delegate_task","delegate_worker","read_file","search_files","todo"]` (6 tools, no `terminal`); dense + MoE direct probes on 2026-04-19 confirmed the same 6-tool bound set; `terminal` was absent from both. What the session JSONs actually contain is **rejected hallucinated tool calls**: Gemma's decode produced `<tool_call>{"name": "terminal", ...}</tool_call>` on Linux-administration-flavored prompts (`crontab -l`, `ls -R`), and Hermes' runtime tool-call validator (`run_agent.py` lines 8685-8710) rejected each with a `"Tool 'terminal' does not exist. Available tools: clarify, delegate_task, delegate_worker, read_file, search_files, todo"` tool-message stub. No terminal command ever executed; tripwire-zero held across all 34 r7.3 trials. T6 run 11's "partial overlap" was a mis-classification: its first tool was `search_files`, not `terminal` — it was never a leak.

**Fix:** a 10-line change to the probe analyzer, not to the runtime. `probe-variantF-check.py` (and its successors) filter tool calls whose immediately-following `role:tool` message begins `"Tool '<name>' does not exist"`, so the first-tool label reflects *accepted* calls rather than hallucinated-rejected ones. Applied to r7.4 scoring from Phase C onward.

**Effect on r7.3 numbers:** the `role-collapse-via-terminal` row (5/30) collapses to 0; 4 dense trials re-label into `role-collapse-via-readonly` (their first accepted tool call was `search_files`). The r7.3 headline findings (dense 1/15, MoE 1/15 first-attempt strict) are **unchanged** — the gate verdict was always stable; only the failure-mode attribution shifts.

**Judge verdict:** ACCEPT. Gate is sound. r7.4 β-fuse probe proceeded with the existing wrapper + toolset configuration.
