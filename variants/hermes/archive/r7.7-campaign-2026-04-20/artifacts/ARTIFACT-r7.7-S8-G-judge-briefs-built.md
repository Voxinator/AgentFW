---
type: Arm G judge-brief build report
date: 2026-04-20
---
# S8 Arm G — 20 judge briefs built

Built 20 per-trial fresh-context judge briefs for Arm G (A1-only ablation) from the
F.1 rubric template and the four S8 Arm G batch artifacts. Generator:
`/tmp/r7.7-judge-briefs/armG/_generate.py` (adapted from the Arm F generator;
removes `A2_GATE_OUTCOME` preamble, adds Arm G note, drops the `a2_gate_outcome`
manifest column, substitutes new per-task GOAL_PATHS). Trial mapping in
`_trial_data.json` (20 rows from B1/B2/B3/B4 = 5/5/5/5).

## Briefs

| # | Task | Run | Parent session | Primary child |
|---|------|-----|-----------------------|------------------------|
| 1 | T4 | 1 | `20260420_214633_4a54d5` | `20260420_214643_ecf4a9` |
| 2 | T5 | 1 | `20260420_214706_9d0c7d` | `20260420_214711_99acf8` |
| 3 | T6 | 1 | `20260420_214754_6c8cd8` | `20260420_214759_7dd9e5` |
| 4 | T10 | 1 | `20260420_214954_484b8a` | `20260420_214959_d7d9fc` |
| 5 | T4 | 2 | `20260420_215518_2c9c99` | `20260420_215523_278ce3` |
| 6 | T5 | 2 | `20260420_215901_d784b1` | `20260420_215905_3e1c1e` |
| 7 | T6 | 2 | `20260420_220014_5e20bb` | `20260420_220019_b78a2e` |
| 8 | T10 | 2 | `20260420_220327_86cc78` | `20260420_220333_de8f04` |
| 9 | T4 | 3 | `20260420_220600_556a28` | `20260420_220605_4eae92` |
| 10 | T5 | 3 | `20260420_220622_56cadc` | `20260420_220626_30d4e9` |
| 11 | T6 | 3 | `20260420_221000_e3a26d` | `20260420_221005_8a66dd` |
| 12 | T10 | 3 | `20260420_221243_0cba13` | `20260420_221248_cdc104` |
| 13 | T4 | 4 | `20260420_222004_fca01e` | `20260420_222009_c0bf68` |
| 14 | T5 | 4 | `20260420_222848_226a88` | `20260420_222852_612e1e` |
| 15 | T6 | 4 | `20260420_222956_7b2ec7` | `20260420_223000_9c5dec` |
| 16 | T10 | 4 | `20260420_223628_ce75a1` | `20260420_223633_68af0c` |
| 17 | T4 | 5 | `20260420_224622_30d9e5` | `20260420_224627_47a867` |
| 18 | T5 | 5 | `20260420_224652_18420f` | `20260420_224656_c336c7` |
| 19 | T6 | 5 | `20260420_224840_ee8c4f` | `20260420_224844_f1dd2e` |
| 20 | T10 | 5 | `20260420_225424_bac87a` | `20260420_225429_27586a` |

Brief paths follow `/tmp/r7.7-judge-briefs/armG/armG-T<id>-run<M>-brief.txt`;
full paths are in `MANIFEST.tsv`. Primary child = first (lowest-timestamp) child
in each trial's child list. Secondary children are listed inline in each brief's
preamble for judge awareness but are not under evaluation.

## Files written

- 20 brief files: `/tmp/r7.7-judge-briefs/armG/armG-T{4,5,6,10}-run{1,2,3,4,5}-brief.txt`
  (sizes 16.6-17.2 KB; 254-267 lines each)
- `/tmp/r7.7-judge-briefs/armG/MANIFEST.tsv` — columns:
  `trial_num | task | run | parent_session_id | child_session_id | brief_path`
  (no `a2_gate_outcome` column; deliberately omitted per Arm G spec)
- `/tmp/r7.7-judge-briefs/armG/_trial_data.json` — source-of-truth trial mapping
- `/tmp/r7.7-judge-briefs/armG/_generate.py` — generator script
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-S8-G-judge-briefs-built.md` — this report

## Multi-child trials (primary vs secondaries)

Twelve of the 20 Arm G trials dispatched multiple children (single-trial parent
spawning more than one child within its wall-clock window). For these, the brief
lists the primary (first-timestamp) child as `CHILD_SESSION_PATH` and records the
secondaries in the preamble with the note "Judge should note their presence but
evaluate the primary child."

| Trial | Task | Run | # children | # secondaries |
|------:|------|----:|-----------:|--------------:|
| 3 | T6 | 1 | 3 | 2 |
| 4 | T10 | 1 | 4 | 3 |
| 7 | T6 | 2 | 4 | 3 |
| 8 | T10 | 2 | 4 | 3 |
| 11 | T6 | 3 | 3 | 2 |
| 12 | T10 | 3 | 3 | 2 |
| 15 | T6 | 4 | 5 | 4 |
| 16 | T10 | 4 | 2 | 1 |
| 18 | T5 | 5 | 2 | 1 |
| 19 | T6 | 5 | 7 | 6 |
| 20 | T10 | 5 | 4 | 3 |

Full secondary-child lists are recorded inline in each brief's preamble and in
`_trial_data.json`. The remaining 9 trials (T4 runs 1-5, T5 runs 1-4) each
spawned a single child; no secondary line in those briefs.

## Verification

- Zero `{{VAR}}` markers in any brief (grep match: 0).
- Zero `A2_GATE_OUTCOME` substrings in any brief (grep match: 0).
- All 20 briefs non-empty (16.6-17.2 KB, 254-267 lines).
- Arm G preamble present in every brief; per-task GOAL_PATHS match user spec;
  PER_TRIAL_ARTIFACT_PATH correctly reads `ArmG`.
- MANIFEST.tsv: 21 lines (1 header + 20 rows), 6 columns, no
  `a2_gate_outcome` column.

## Ready for judge dispatch? YES

All 20 briefs are ready to be passed verbatim to fresh-context Claude sub-agents for
per-trial worker-quality evaluation. The main session should dispatch one judge per
brief and aggregate the `WORKER_QUALITY=...` verdicts, matching the Arm F workflow.
