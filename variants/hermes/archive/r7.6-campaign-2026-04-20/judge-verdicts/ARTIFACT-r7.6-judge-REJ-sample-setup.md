[TASK CLASS: structured]
Justification: REJ (full re-judgment) brief-prep setup for r7.6 P1-C fixes. The 10-sample calibration expansion (C2 + C3) hit 7/10 below the ≥8/10 threshold; per CALIBRATION protocol, escalate to full fresh-LLM re-judgment of all untried trials across the 40-trial matrix.

# ARTIFACT — r7.6 REJ judge sample setup (full fresh-LLM re-judgment)

## Purpose

The original 5-sample + C2 5-sample + C3 5-sample fresh-judge calibration rounds produced an aggregate **7/10 agreement** against the patched heuristic — **below the ≥8/10 trustworthiness gate**. Two calibration rounds have failed to clear the gate, so the operator's ship protocol escalates to **full fresh-LLM re-judgment of all untried trials** in the 40-trial matrix (20 Arm A + 20 Arm B).

This REJ round prepares **25 ready-to-dispatch judge briefs** — one per remaining untried trial. After fresh-LLM verdicts are returned, combined with the 15 already-sampled (5 original + 5 C2 + 5 C3), the operator will have fresh-LLM verdicts covering all 40 trials, and the true Arm A vs. Arm B worker-quality PASS counts can be computed directly without relying on the heuristic at all.

## Coverage (already-sampled vs. REJ unsampled)

### Already-sampled (15 trials, DO NOT re-prep)

**Arm A sampled (4):**
- T4-run1 (original brief 1)
- T4-run3 (C3-5)
- T4-run4 (original brief 2)
- T5-run2 (C2-4)

**Arm B sampled (11):**
- T4-run2 (C3-1)
- T4-run3 (original brief 5 — LOST)
- T5-run1 (original brief 3)
- T5-run2 (C3-2)
- T5-run3 (C2-5)
- T6-run1 (C3-3)
- T6-run2 (original brief 4)
- T6-run3 (C3-4)
- T10-run1 (C2-1)
- T10-run3 (C2-3)
- T10-run4 (C2-2)

### REJ unsampled (25 trials, prepped in this round)

**Arm A unsampled (16):** T4-runs 2, 5 | T5-runs 1, 3, 4, 5 | T6-runs 1, 2, 3, 4, 5 | T10-runs 1, 2, 3, 4, 5.
**Arm B unsampled (9):** T4-runs 1, 4, 5 | T5-runs 4, 5 | T6-runs 4, 5 | T10-runs 2, 5.

Total: 25 — all previously-unsampled trials. **Zero overlap** with the already-sampled 15 (verified row-by-row against brief sample-setup files for original, C2, and C3 rounds).

Including the already-sampled 15, combined post-REJ coverage = **40 of 40 trials (100%)**.

## 25-trial mapping

| Brief ID | Arm | Task | Run | Parent session (VM) | Primary child session (VM) | Siblings | Heuristic verdict (for comparison only — NOT in brief) | TASK_CLASS | GOAL_PATHS | Brief file |
|----------|-----|------|-----|----------------------|-----------------------------|----------|----------------------------------------------------------|------------|------------|------------|
| REJ-A-T4-run2 | A | T4 | 2 | 20260419_202132_50f846 | 20260419_202137_75f15d | none | FAIL (heuristic) | structured | src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts | ARTIFACT-r7.6-judge-brief-REJ-A-T4-run2.md |
| REJ-A-T4-run5 | A | T4 | 5 | 20260419_202341_b5c773 | 20260419_202346_d80d77 | none | PASS (heuristic) | structured | src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts | ARTIFACT-r7.6-judge-brief-REJ-A-T4-run5.md |
| REJ-A-T5-run1 | A | T5 | 1 | 20260419_202413_7754a1 | 20260419_202426_0e3f50 | none | FAIL | structured | [] | ARTIFACT-r7.6-judge-brief-REJ-A-T5-run1.md |
| REJ-A-T5-run3 | A | T5 | 3 | 20260419_202706_b5b0d7 | 20260419_202712_b6cb3e | none | FAIL | structured | [] | ARTIFACT-r7.6-judge-brief-REJ-A-T5-run3.md |
| REJ-A-T5-run4 | A | T5 | 4 | 20260419_202831_b11dcf | 20260419_202837_9a0153 | none | FAIL | structured | [] | ARTIFACT-r7.6-judge-brief-REJ-A-T5-run4.md |
| REJ-A-T5-run5 | A | T5 | 5 | 20260419_203003_57b4e2 | 20260419_203009_df0027 | none | FAIL | structured | [] | ARTIFACT-r7.6-judge-brief-REJ-A-T5-run5.md |
| REJ-A-T6-run1 | A | T6 | 1 | 20260419_203110_ce514c | 20260419_203116_b3e1c1 | none | FAIL | long-horizon | features/export-feature/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T6-run1.md |
| REJ-A-T6-run2 | A | T6 | 2 | 20260419_203613_d66559 | 20260419_203619_f0bc6b | none | FAIL | long-horizon | features/export-engine/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T6-run2.md |
| REJ-A-T6-run3 | A | T6 | 3 | 20260419_203833_c7b356 | 20260419_203839_714921 | none | FAIL | long-horizon | features/export-engine/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T6-run3.md |
| REJ-A-T6-run4 | A | T6 | 4 | 20260419_204008_f427ed | 20260419_204013_bee646 | none | FAIL | long-horizon | PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T6-run4.md |
| REJ-A-T6-run5 | A | T6 | 5 | 20260419_204143_1337e5 | 20260419_204149_76db8b | none | FAIL | long-horizon | docs/exports/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T6-run5.md |
| REJ-A-T10-run1 | A | T10 | 1 | 20260419_204636_4ddafd | 20260419_204642_91923a | none | FAIL | long-horizon | migrations/pg-upgrade-2026/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T10-run1.md |
| REJ-A-T10-run2 | A | T10 | 2 | 20260419_204816_751167 | 20260419_204821_a2dc9f | none | FAIL | long-horizon | migrations/pg12-to-pg16/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T10-run2.md |
| REJ-A-T10-run3 | A | T10 | 3 | 20260419_205339_9534b8 | 20260419_205346_da7cd9 | none | FAIL | long-horizon | migrations/pg12-to-pg16/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T10-run3.md |
| REJ-A-T10-run4 | A | T10 | 4 | 20260419_205531_e43f0d | 20260419_205536_2a1eff | none | FAIL | long-horizon | migrations/pg12-to-pg16/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T10-run4.md |
| REJ-A-T10-run5 | A | T10 | 5 | 20260419_205805_806204 | 20260419_205811_39b06b | none | FAIL | long-horizon | MIGRATION_PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-A-T10-run5.md |
| REJ-B-T4-run1 | B | T4 | 1 | 20260419_210750_1f9b62 | 20260419_210800_818e65 | none | PASS | structured | src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts | ARTIFACT-r7.6-judge-brief-REJ-B-T4-run1.md |
| REJ-B-T4-run4 | B | T4 | 4 | 20260419_212423_10d2ca | 20260419_212427_5d1305 | none | PASS | structured | src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts | ARTIFACT-r7.6-judge-brief-REJ-B-T4-run4.md |
| REJ-B-T4-run5 | B | T4 | 5 | 20260419_212442_54c2df | 20260419_212447_173c2b | none | PASS | structured | src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts | ARTIFACT-r7.6-judge-brief-REJ-B-T4-run5.md |
| REJ-B-T5-run4 | B | T5 | 4 | 20260419_214432_52b6a8 | NO_CHILD_SPAWNED | none | LOST (one-shot-no-goal) | structured | [] | ARTIFACT-r7.6-judge-brief-REJ-B-T5-run4.md |
| REJ-B-T5-run5 | B | T5 | 5 | 20260419_214607_43198b | 20260419_214613_def4b3 | none | PASS | structured | [] | ARTIFACT-r7.6-judge-brief-REJ-B-T5-run5.md |
| REJ-B-T6-run4 | B | T6 | 4 | 20260419_221749_e5e803 | NO_CHILD_SPAWNED | none | LOST (one-shot-no-goal) | long-horizon | features/export-engine/PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-B-T6-run4.md |
| REJ-B-T6-run5 | B | T6 | 5 | 20260419_225355_721123 | 20260419_225406_27640d | 20260419_225521_775cf5, 20260419_225547_3a9890 | FAIL | long-horizon | exports-feature/PLAN.md, PROGRESS.md, CONTEXT.md | ARTIFACT-r7.6-judge-brief-REJ-B-T6-run5.md |
| REJ-B-T10-run2 | B | T10 | 2 | 20260419_230051_5f212e | 20260419_230057_3e6ae9 | none | FAIL | long-horizon | MIGRATION_PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-B-T10-run2.md |
| REJ-B-T10-run5 | B | T10 | 5 | 20260419_230405_91730e | 20260419_230410_22a345 | 20260419_230636_79f674 | FAIL | long-horizon | MIGRATION_PLAN.md | ARTIFACT-r7.6-judge-brief-REJ-B-T10-run5.md |

**Heuristic verdicts are sourced from `/tmp/probe-r7.6-P1C-logs.post-fix2/arm-{A,B}-verdicts.replay.txt` (the same post-fix2 replay used for C2/C3 stratification).** They are recorded here for planner-side comparison only and are NOT leaked into any of the 25 fresh-judge briefs.

**Coverage summary for REJ round:**
- **Arm A:** 16 trials (T4×2 + T5×4 + T6×5 + T10×5) — entire Arm A heuristic-FAIL population (15) + one Arm A heuristic-PASS (T4-run5). Combined with the already-sampled 4 Arm A trials, all 20 Arm A trials covered post-REJ.
- **Arm B:** 9 trials (T4×3 + T5×2 + T6×2 + T10×2). Combined with the already-sampled 11 Arm B trials, all 20 Arm B trials covered post-REJ.
- **LOST trials included:** 2 (REJ-B-T5-run4, REJ-B-T6-run4). These were correctly labeled LOST by the orchestrator (parent session classified the task as one-shot and invoked `delegate_worker_v2` without a `goal`, so no child was spawned). Per the F.1 template §0 existence check, the fresh judge will ssh-test the `NO_CHILD_SPAWNED` sentinel path, observe MISSING, and emit `WORKER_QUALITY=LOST reason=CHILD_NOT_FOUND`. The orchestrator treats LOST as not-counted-in-denominator (same convention as armB-T4-run3 / original brief 5).
- **Multi-child trials included:** 2 (REJ-B-T6-run5 with 2 siblings, REJ-B-T10-run5 with 1 sibling). The F.1 template's §1 "evaluate BEST child across siblings" clause will fire on these two briefs; SIBLING_CHILDREN is populated with the sibling session paths. All other 23 briefs have SIBLING_CHILDREN=[].

**VM existence verification (2026-04-19):** All 23 primary child sessions and 3 sibling children (T6-run5 siblings × 2, T10-run5 sibling × 1) were extracted successfully (`ssh ubuntu-vm 'jq -r ".messages[0].content" ...'` returned content for each). Both LOST parent sessions (20260419_214432_52b6a8, 20260419_221749_e5e803) also exist on VM for fresh-judge traceability inspection. No MISSING-at-prep cases.

**Canonical tripwire md5s (baseline == post for all 25, per P1C-run-only and worker-quality per-trial artifacts):**
- HERMES.md = 0780c232a6cb52e13e432261f0d68ad9
- SKILL.md = fb1a5a5208a6cf2fcb8252aac10397eb
- jira-briefing.sh = a1dce6e989527686124d0860830627c9

## Aggregate patched-heuristic verdict distribution for REJ set (planner-only)

Raw from `/tmp/probe-r7.6-P1C-logs.post-fix2/arm-{A,B}-verdicts.replay.txt`:

| Verdict | Count | Trials |
|---------|-------|--------|
| Arm A heuristic-PASS | 1 | REJ-A-T4-run5 |
| Arm A heuristic-FAIL | 15 | REJ-A-T4-run2, REJ-A-T5-runs 1/3/4/5, REJ-A-T6-runs 1/2/3/4/5, REJ-A-T10-runs 1/2/3/4/5 |
| Arm B heuristic-PASS | 4 | REJ-B-T4-runs 1/4/5, REJ-B-T5-run5 |
| Arm B heuristic-FAIL | 3 | REJ-B-T6-run5, REJ-B-T10-runs 2/5 |
| Arm B heuristic-LOST | 2 | REJ-B-T5-run4, REJ-B-T6-run4 |

**This distribution matters for the post-REJ aggregate computation (see Cross-check below).**

## Planner-facing instructions (dispatch protocol)

Dispatch the 25 REJ briefs across **5 batches of 5 concurrent fresh Claude Agent sub-agents** (`subagent_type='general-purpose'`). Each batch runs in parallel; the planner waits for the batch to complete, then launches the next. 5 batches × ~4-6 min per judge = **~20-30 min total wall clock**.

**Suggested batching (arbitrary — any 5-per-batch split works; this one mixes arms/tasks per batch for failure-isolation):**

- **Batch 1:** REJ-A-T4-run2, REJ-A-T4-run5, REJ-A-T5-run1, REJ-A-T5-run3, REJ-B-T4-run1
- **Batch 2:** REJ-A-T5-run4, REJ-A-T5-run5, REJ-A-T6-run1, REJ-A-T6-run2, REJ-B-T4-run4
- **Batch 3:** REJ-A-T6-run3, REJ-A-T6-run4, REJ-A-T6-run5, REJ-A-T10-run1, REJ-B-T4-run5
- **Batch 4:** REJ-A-T10-run2, REJ-A-T10-run3, REJ-A-T10-run4, REJ-A-T10-run5, REJ-B-T5-run5
- **Batch 5:** REJ-B-T5-run4 (LOST), REJ-B-T6-run4 (LOST), REJ-B-T6-run5 (multi-child), REJ-B-T10-run2, REJ-B-T10-run5 (multi-child)

(Batch 5 intentionally groups the 2 LOST and 2 multi-child cases together so any prompt-handling quirks isolate to one batch — LOST judges should return in <1 min on the existence check failing fast; multi-child judges take the longest because they inspect multiple transcripts.)

**Dispatch scope for each fresh judge (planner sets in worker spec):**
- **Allowed operations:** `ssh ubuntu-vm 'jq ...'`, `ssh ubuntu-vm 'test -f ...'`, `ssh ubuntu-vm 'cat ...'`, `ssh ubuntu-vm 'md5sum ...'`; local `/tmp/*` scratch writes; local `Write` to the judge's single `ARTIFACT-r7.6-judge-REJ-fresh-verdict-<arm><task>-run<N>.md` artifact path.
- **Forbidden:** any VM mutation; any Hermes invocation; any re-dispatch of sub-agents; any file write outside the verdict artifact path; reading the patched-heuristic per-trial stdout files under `/tmp/probe-r7.6-P1C-logs.post-fix2/per-trial/` (would leak verdicts); reading any other REJ/C2/C3/original brief file or fresh-verdict artifact (cross-contamination).
- **Time budget:** 20-40 min per judge per F.1 §5; orchestrator may escalate `LOST reason=JUDGE_TIMEOUT` for any judge exceeding 40 min wall clock.
- **Parallelism:** up to 5 concurrent judges per batch (SSH-concurrency-safe for read-only `jq` / `test` / `cat`).

**Per-judge output surface:**
1. Stdout: top-line `WORKER_QUALITY=<PASS|FAIL|LOST>` + 5 sub-criteria lines + metadata + `---RATIONALE---` + JSON block (see F.1 §3).
2. Artifact file: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-judge-REJ-fresh-verdict-<arm>-<task>-run<N>.md` — full transcript summary + evidence + rationale.

## Cross-check — post-REJ aggregate computation

After all 25 fresh-LLM verdicts are collected, combine with the 15 already-sampled fresh-LLM verdicts to compute **true Arm A vs. Arm B worker-quality PASS counts** over the full 40-trial matrix. The heuristic verdicts are no longer authoritative — they are reference signals only.

**Aggregation formula (per F.1 §F):**
- **Denominator:** trials with non-LOST fresh-LLM verdict.
- **Numerator:** trials with `WORKER_QUALITY=PASS`.
- Compute Arm A PASS count / Arm A denominator = true Arm A PASS rate.
- Compute Arm B PASS count / Arm B denominator = true Arm B PASS rate.
- **P1-C delta** = (Arm B PASS rate) − (Arm A PASS rate), measured strictly in fresh-LLM verdicts.

**Expected denominator reductions from known-LOST:**
- Arm A: 0 LOST (all 20 Arm A trials have a child session).
- Arm B: 3 LOST (armB-T4-run3 from original round + REJ-B-T5-run4 + REJ-B-T6-run4). Arm B denominator = 17 max (may be higher if judges flag additional JUDGE_TIMEOUT LOSTs).

**Ship gate (recap of F.1 ship protocol against fresh-LLM ground truth):**
- Arm B PASS rate − Arm A PASS rate **≥ +40 pp** (absolute): ship Fix 2.
- Δ ∈ [+20 pp, +40 pp): retain Fix 2 with documented "direction-correct but under-powered" caveat.
- Δ < +20 pp: do NOT ship Fix 2; investigate why the heuristic over-predicted the Arm B advantage.
- Δ ≤ 0 or reverses sign: Fix 2 is net-harmful; investigate + roll back.

**Sanity check sub-computations (planner should tabulate):**
1. Arm A PASS rate breakdown by task: T4, T5, T6, T10 — look for task-specific reversals.
2. Arm B PASS rate breakdown by task: same.
3. Agreement rate across all 40 trials (fresh vs. heuristic) — estimates the heuristic's true aggregate accuracy, independent of the ship decision.
4. "Over-credit rate" by arm: fraction of heuristic-PASS trials where fresh judge disagreed. Expected signature per C2/C3: ~0% on Arm A (1-trial sample is weak but the pattern in C3-5 was clean), ~50% on Arm B (the reason we're in REJ in the first place).

## Note on LOST handling

Any trial with `CHILD_SESSION_PATH=/home/parallels/.hermes/sessions/session_NO_CHILD_SPAWNED.json` (REJ-B-T5-run4, REJ-B-T6-run4) will fail the F.1 §0 existence check on the first ssh-test line. The fresh judge is instructed to emit `WORKER_QUALITY=LOST reason=CHILD_NOT_FOUND` + N/A for all 5 sub-criteria, write a minimal 1-block per-trial artifact, and stop.

The orchestrator's aggregate formula treats these LOSTs as **not-counted-in-denominator** (same convention the original brief-5 set for armB-T4-run3). Combined post-REJ Arm B denominator is therefore at most 17 (20 − 3 LOST).

## Leakage-avoidance verification

**Content audit of all 25 REJ briefs:**
- Each brief contains only: the 11 F.1 input variables substituted + the F.1 rubric body (BACKGROUND + PROCEDURE + output format + edge cases).
- NO reference to patched-heuristic verdicts or rationales.
- NO reference to any C2/C3/REJ fresh-verdict artifact.
- NO reference to the 7/10 calibration-fail signal or the REJ-escalation decision.
- NO pattern-matching hypothesis disclosure.
- NO batch membership, concurrency limits, or cross-trial comparison guidance.

A fresh judge reading only its assigned REJ brief has zero knowledge of what the heuristic decided, what any prior calibration round found, or that this is a full-matrix re-judgment. Each judge sees only its single trial's inputs + the evaluation rubric, exactly as the original / C2 / C3 fresh judges did.

**Filename audit:** all 25 briefs written to `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-judge-brief-REJ-<arm>-<task>-run<N>.md`. Output verdict paths written to `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-judge-REJ-fresh-verdict-<arm>-<task>-run<N>.md` (one per brief, matching the PER_TRIAL_ARTIFACT_PATH field inside each brief).

## Provenance

- **Parent/child session IDs:** extracted from `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-worker-quality-arm{A,B}-<NN>.md` (the 40 per-trial orchestrator-heuristic artifacts), with trial numbering convention T4=1-5, T5=6-10, T6=11-15, T10=16-20.
- **PARENT_GOAL texts:** extracted verbatim via `ssh ubuntu-vm 'jq -r ".messages[0].content" /home/parallels/.hermes/sessions/session_<child-sid>.json'` — the same method C2/C3 used. For 2 LOST cases, the PARENT_GOAL field is set to the canonical "(EMPTY — parent session classified the task as 'one-shot' ...)" text used in original brief-5.
- **GOAL_PATHS:** derived from the PARENT_GOAL text by pattern-matching file paths (regex over `[*.ts|*.md|*.py|*.js|*.sh|migrations/...|src/...|tests/...|features/...|exports?-feature|PLAN\.md|MIGRATION_PLAN\.md|CONTEXT\.md|PROGRESS\.md]`). For goals that name no specific deliverable path (e.g., T5 stale-data goals that ask for a "report and patch" without committing a write path), GOAL_PATHS is set to `[]`.
- **Sibling children:** from `ARTIFACT-r7.6-P1C-run-only.md` (T6-run5 × 2 siblings, T10-run5 × 1 sibling) + per-trial artifacts (verified match to `sibling_verdicts` blocks in armB-15 and armB-20 artifacts). No other Arm A or Arm B trials have siblings.
- **Tripwire md5s:** from `ARTIFACT-r7.6-P1C-run-only.md` (baseline == post for all 40 trials; no drift).

## Summary

**Prep status:** 25/25 REJ judge briefs written. Master setup written. Zero overlap with the 15 already-sampled. All 23 non-LOST child sessions + both LOST parent sessions + both sibling sets exist on VM. Patched-heuristic verdicts recorded for planner-side comparison but not leaked into any brief. Ready for planner dispatch in 5 batches of 5 concurrent sub-agents each.
