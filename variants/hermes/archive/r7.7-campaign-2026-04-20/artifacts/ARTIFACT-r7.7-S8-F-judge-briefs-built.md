---
type: judge-brief build report
date: 2026-04-20
campaign: r7.7 Path A Arm F
---
# S8 Arm F — 20 judge briefs built

All 20 per-trial judge briefs were assembled from the r7.5 F.1 template by substituting the 11 spec-defined variables plus a 12th (`A2_GATE_OUTCOME`) into the canonical prompt body between `<<<BEGIN_PROMPT>>>` and `<<<END_PROMPT>>>`. Inputs: 2 original-attempt trial records, 4 batch artifacts (B1–B4 covering 18 trials), the 4 canonical task prompts at `/tmp/r7.7-S8-prompts/T{4,5,6,10}.txt`, and the tripwire baseline md5s (4-key: HERMES.md / SKILL.md / jira-briefing.sh / useDashboard.ts — all verified MATCH per-batch). No judging performed.

## Briefs

| Trial | Task | Run | Parent session | Child session | a2_gate | Brief path |
|-------|------|-----|----------------|---------------|---------|------------|
| 1     | T4   | 1   | `20260420_170311_e637a5` | `20260420_170321_07f156` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T4-run1-brief.txt` |
| 2     | T5   | 1   | `20260420_171957_1d5146` | `20260420_172002_fc5d66` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T5-run1-brief.txt` |
| 3     | T4   | 2   | `20260420_193933_e60c16` | *(none persisted; parent used)* | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T4-run2-brief.txt` |
| 4     | T5   | 2   | `20260420_194022_26f7bc` | *(none persisted; parent used)* | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T5-run2-brief.txt` |
| 5     | T6   | 1   | `20260420_194104_12c0d8` | *(none persisted; parent used)* | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T6-run1-brief.txt` |
| 6     | T10  | 1   | `20260420_195822_365547` | *(none persisted; parent used)* | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T10-run1-brief.txt` |
| 7     | T4   | 3   | `20260420_195900_bd5f49` | *(none persisted; parent used)* | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T4-run3-brief.txt` |
| 8     | T5   | 3   | `20260420_200547_2347e2` | `20260420_200556_fcb1aa` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T5-run3-brief.txt` |
| 9     | T6   | 2   | `20260420_200634_a3eec8` | `20260420_200640_e0b6c3` (+1 secondary) | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T6-run2-brief.txt` |
| 10    | T10  | 2   | `20260420_201421_a1597d` | `20260420_201425_b17b47` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T10-run2-brief.txt` |
| 11    | T4   | 4   | `20260420_201539_619f4c` | `20260420_201545_ac9d79` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T4-run4-brief.txt` |
| 12    | T5   | 4   | `20260420_201623_6c58e1` | `20260420_201628_059415` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T5-run4-brief.txt` |
| 13    | T6   | 3   | `20260420_202009_3a63ff` | `20260420_202014_dbbbee` (+2 secondary) | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T6-run3-brief.txt` |
| 14    | T10  | 3   | `20260420_202124_6ec63e` | `20260420_202129_a7de2c` (+2 secondary) | **FABRICATED** | `/tmp/r7.7-judge-briefs/armF/armF-T10-run3-brief.txt` |
| 15    | T4   | 5   | `20260420_202405_ed4589` | `20260420_202410_a8865b` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T4-run5-brief.txt` |
| 16    | T5   | 5   | `20260420_202448_649b03` | `20260420_202452_e4e79b` | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T5-run5-brief.txt` |
| 17    | T6   | 4   | `20260420_202930_f3ba6e` | `20260420_202934_f17c30` (+1 secondary) | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T6-run4-brief.txt` |
| 18    | T10  | 4   | `20260420_203359_e9f686` | `20260420_203405_a2c18f` (+2 secondary) | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T10-run4-brief.txt` |
| 19    | T6   | 5   | `20260420_204949_9db097` | `20260420_204954_688f43` (+2 secondary) | CLEAN | `/tmp/r7.7-judge-briefs/armF/armF-T6-run5-brief.txt` |
| 20    | T10  | 5   | `20260420_205158_780a70` | `20260420_205203_fb527e` (+1 secondary) | **FABRICATED** | `/tmp/r7.7-judge-briefs/armF/armF-T10-run5-brief.txt` |

All 20 brief files were verified non-empty (sizes 16.4KB – 17.3KB). Zero unsubstituted `{{VAR}}` tokens remain in any brief (scanned). Every brief carries the 12-variable preamble (source batch, parent session, primary child note, A2 gate header) followed by the verbatim r7.5 F.1 prompt body.

## Files written
- 20 brief files at `/tmp/r7.7-judge-briefs/armF/armF-*-brief.txt`
- `/tmp/r7.7-judge-briefs/armF/MANIFEST.tsv` (7 columns: trial_num, task, run, parent_session_id, child_session_id, a2_gate_outcome, brief_path)
- This report at `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-S8-F-judge-briefs-built.md`
- Generator + trial-data scratch at `/tmp/r7.7-judge-briefs/armF/_generate.py` and `_trial_data.json` (reproducibility; safe to delete)

## B1 no-child-persisted cohort (5 trials)

Trials 3–7 (B1 retry) had **no child session JSON persist** to `/home/parallels/.hermes/sessions/` during the trial's wall-clock window, per the B1 artifact's regex scan. For these, the brief's `CHILD_SESSION_PATH` points at the **parent** session JSON (the only persisted artifact from the trial) with an explicit preamble note telling the judge: if inspection shows the file is actually a parent (not a child-of-delegate goal), evaluate the parent's own turn-by-turn β-fuse/synthesis behavior; if un-evaluable under the brief, emit `WORKER_QUALITY=LOST reason=CHILD_NOT_FOUND`. This preserves optionality — if a judge cold-reads a parent and deems it out-of-scope for the worker-quality rubric, the LOST verdict excludes the trial from the 15/20 denominator cleanly. Contrast: B2/B3/B4 all produced observable persisted children (1–3 per trial).

## Multi-child trials (main-session awareness)

Seven trials spawned multiple persisted children in their parent turn. For each, the brief evaluates the **primary** (first-latency, typically +4–6s from parent start) and the preamble notes the secondaries by id:

| Trial | Task | Run | Primary | Secondaries |
|-------|------|-----|---------|-------------|
| 9  | T6  | 2 | `20260420_200640_e0b6c3` | `20260420_201027_43bce2` |
| 13 | T6  | 3 | `20260420_202014_dbbbee` | `20260420_202043_6c92f0`, `20260420_202055_9d897f` |
| 14 | T10 | 3 | `20260420_202129_a7de2c` | `20260420_202246_58f2ea`, `20260420_202324_8576fc` |
| 17 | T6  | 4 | `20260420_202934_f17c30` | `20260420_203024_0209c5` |
| 18 | T10 | 4 | `20260420_203405_a2c18f` | `20260420_203435_ad359e`, `20260420_204849_bec3b9` (+14m50s — unusually late) |
| 19 | T6  | 5 | `20260420_204954_688f43` | `20260420_205004_95b924`, `20260420_205042_b58b3a` |
| 20 | T10 | 5 | `20260420_205203_fb527e` | `20260420_205239_c5c9a3` |

Multi-child pattern concentrates on T6/T10 (long-horizon) and on T10 in particular (all 3 T10 trials with persisted children were multi). Both FABRICATED a2_gate outcomes are on T10 (trials 14 and 20). Main session may want to flag this correlation for F.3 ship judge's task-class analysis.

## Ready for judge dispatch? YES

All 20 briefs are self-contained per the r7.5 F.1 self-containment clause (§7f): judge receives only the substituted template, no outside context needed. Dispatch can proceed with the 20 files listed in MANIFEST.tsv. Recommended parallelism: ≤3 concurrent judges per §5 of the template (SSH concurrency to the VM).
