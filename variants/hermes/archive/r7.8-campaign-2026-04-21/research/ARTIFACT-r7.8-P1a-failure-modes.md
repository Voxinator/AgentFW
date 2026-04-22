---
type: r7.8 P1a — failure-mode classification
date: 2026-04-21
source_verdicts: 40 (ArmF + ArmG, T4/T5/T6/T10 x run1..5)
fail_population: 28
pass_population: 12
---
# r7.8 P1a — failure-mode classification

## Scope

Classify every Arm F / Arm G FAIL trial from the r7.7 40-run judge cohort by dominant failure mode, attribute each mode to a layer (parser / sampler / prompt / tool-call / environment), and rank modes by (count x generalization potential). No interventions are proposed here — P1a is descriptive only.

Inputs read: 40 verdict artifacts under `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-judge-Arm{F,G}-T{4,5,6,10}-run{1..5}.md`. Session JSONs were sampled on the VM (`ssh ubuntu-vm`) to corroborate the verdicts' failure-mode claims — in every spot-check (4 probe sessions covering channel-leak, degenerate-loop, malformed-final, and all-empty-content patterns) the raw session content matched the verdict evidence.

Baseline: 12/40 PASS (all 5 Arm G T4 runs, all Arm F T10 runs 1-3, Arm F T4 runs 2,3,5, Arm F T5-run3). PASS/FAIL split is dominated by task more than by arm — see "Per-task distribution" below.

## Catalog counts (all 28 FAILs, by dominant mode)

| Mode | Description | Arm F | Arm G | Total | % of 28 | Layer (dominant) |
|------|-------------|------:|------:|------:|--------:|------------------|
| 2 | search-thrash without synthesis | 0 | 5 | 5 | 17.9% | prompt |
| 3 | pseudo-tool-call / `<channel|>` token leak | 2 | 3 | 5 | 17.9% | parser |
| 4 | out-of-context / wrong cwd | 4 | 0 | 4 | 14.3% | environment |
| 5 | SCOPE violation | 0 | 0 | 0 | 0.0% | — |
| L | finish_reason=length mid-turn | 0 | 0 | 0 | 0.0% | sampler |
| D | degenerate planning loop | 5 | 1 | 6 | 21.4% | sampler |
| S | silent post-tool termination | 1 | 2 | 3 | 10.7% | sampler/env |
| R | shell/execute rejected + no recovery | 1 | 4 | 5 | 17.9% | tool-call |
| OTHER | — | 0 | 0 | 0 | 0.0% | — |
| **Total** | | **13** | **15** | **28** | **100%** | |

Notes on counting:
- Every trial carries multiple failure signals (e.g. channel-leak co-occurs with almost every Arm F FAIL). Only the *dominant* mode — the one the verdict's evidence section flags as the proximate cause of the FAIL score on COMPLETION/CORRECTNESS — is counted in the catalog row. Secondary modes are enumerated in the per-trial table below.
- Mode L (length-truncation) never appears as dominant; it always appears as a secondary symptom of Mode D or Mode 4. Harness continuation-injection messages (`[System: Your previous response was truncated...]`) were observed in Arm F T4-run1, T5-run5, T6-run1, T10-run5 and Arm G T10-run5, but in each case the underlying driver was already a degenerate loop or a channel-leak, not length by itself.
- Mode 5 is zero: tripwires show no post-trial drift on any of the 28 FAILs. Two near-misses were logged (Arm G T10-run1 and T10-run2 attempted `mkdir -p /home/parallels/.hermes/hermes-agent/migrations/pg-upgrade-2026/` — a protected-tree target — but the shell tool was unavailable so no write actually occurred).

## Per-task distribution (FAILs only)

|            | T4 | T5 | T6 | T10 | Row total |
|------------|---:|---:|---:|----:|----------:|
| Arm F FAIL |  2 |  4 |  5 |   2 | 13 |
| Arm G FAIL |  0 |  5 |  5 |   5 | 15 |
| **Total**  |  2 |  9 | 10 |   7 | 28 |

PASS count per task (complement against 10 = 2 arms * 5 runs): T4 = 8/10, T5 = 1/10 (only Arm F T5-run3), T6 = 0/10, T10 = 3/10 (all Arm F).

Dominant mode x task:

| Mode | T4 | T5 | T6 | T10 |
|------|---:|---:|---:|----:|
| 2 (thrash) | 0 | 4 | 1 | 0 |
| 3 (channel leak) | 0 | 0 | 5 | 0 |
| 4 (wrong cwd) | 0 | 4 | 0 | 0 |
| D (degenerate loop) | 2 | 0 | 2 | 2 |
| S (silent post-tool) | 0 | 1 | 2 | 0 |
| R (tool rejected) | 0 | 0 | 0 | 5 |

Key patterns from this table:
- T10 (create PLAN.md for PG upgrade) is a tool-rejection factory: the goal explicitly requires directory creation + file write, and every Arm G T10 FAIL is dominant-R (child hallucinated a non-existent shell tool name: `shell_execute`, `run_command`, `execute_command`). Arm F T10 FAILs are also dominated by write-tool absence but manifest as D or R because the child burned turns on narration.
- T5 (investigate dashboard at `/media/psf/Projects/chief-of-staff-dashboard`) is the environment-failure cluster: 4/4 Arm F T5 FAILs are dominant-4 (the child never passed `path=` to `search_files` and ended up enumerating the hermes-agent repo instead of the dashboard repo). Arm G T5 FAILs degrade to pure Mode 2 thrash because the Arm G prompt surface apparently does encourage the `path` arg, but without a runtime thrash-brake the child search-loops the goal path to death.
- T6 (export feature, create docs/features/export-feature/PLAN.md) is a channel-leak factory: 5/10 T6 FAILs are dominant-3 (the child emits `thought\n<channel|>` or `<channel|>` fragments as its entire assistant content across the full session, with no natural-language synthesis ever being produced).
- T4 (refactor auth) is the degenerate-loop anchor: both T4 FAILs are dominant-D (the child enters a text-generation loop narrating tool calls inside prose instead of emitting them as `tool_calls`).

## Per-trial table (all 28 FAILs)

| Arm | Task | Run | Dominant | Secondary | Layer | Child session (.hermes/sessions/session_*.json) | Evidence citation |
|-----|------|-----|----------|-----------|-------|--------------------------------------------------|-------------------|
| F | T4 | 1 | D | 3, R, L | sampler | `...172002_fc5d66...` wait — `20260420_170321_07f156` | Final 3 assistant turns (idx 11, 13, 15) each ~50KB pure-text "PLAN: I will search...(I'll try...)" loop with 0 tool_calls; ends mid-token `(I'll try \``; 2 harness "continue truncated" injections failed to recover. Channel-leak `thought\n<channel|>` in msgs 3,5,7. Terminal rejected msg 6. |
| F | T4 | 4 | D | 3, R | sampler | `20260420_201545_ac9d79` | Final assistant msg (idx 9) is 884-char planning monologue ending on `(Self-correction: I'll use search_files...)` — no summary. Channel-leak in msgs 3,5,7. Terminal rejected msg 8. |
| F | T5 | 1 | 4 | 2, L, 3, R | env | `20260420_172002_fc5d66` | 14 turns, 7 search_files but 2 terminal rejected and all search_files scope either hermes-agent CWD or bare-name patterns; goal path `/media/psf/Projects/chief-of-staff-dashboard` never reached. Multiple turns finish_reason=length. Last msg is mid-plan "I will check contents of..." — not a summary. |
| F | T5 | 2 | 4 | D, 3, R | env | `20260420_194026_061a76` | 5 of 7 tool calls omit `path=` — all land on hermes-agent root (HERMES.md, batch_runner.py). Final assistant (idx 15) is a forward-looking PLAN block "I will analyze useDashboard.ts..." with no follow-through. Content of msgs 3,5,7 is `thought\n<channel|>` or `<channel|>`. |
| F | T5 | 4 | 4 | D, 3, R | env | `20260420_201628_059415` | 3 identical `search_files(pattern:"*", target:"files")` with no path arg; final msg (idx 11) admits "search_files results ... NOT the project directory" but emits another PLAN ("I will search for package.json within...") instead of concrete-blocked summary. |
| F | T5 | 5 | 4 | L, 3, R | env | `20260420_202452_e4e79b` | 2 search_files without path land on hermes repo; harness-injected continuation at idx 8 after length-truncation; final msg ends unclosed `"(Wait, I'll just try search_files(pattern=\"*\", path=\"/media/psf/Projects/chief-of-staff-dashboard\", target=\"files\").)"` — a plan never executed. |
| F | T6 | 1 | D | L | sampler | `20260420_194109_edff35` | Msgs 25, 27, 29 are identical ~55KB repetitions of `"PLAN: I will create the \`docs/features/export-feature/PLAN.md\`... (Executing) (I'll use \`terminal\`...)"`. 2 harness truncation injections (idx 26, 28) failed to recover. Ends mid-sentence `(I'll use \``. |
| F | T6 | 2 | 3 | S | parser | `20260420_200640_e0b6c3` | **All 14 assistant content fields are empty / `thought\n<channel|>` / `<channel|>` / `[]`**. No natural-language text anywhere in the session. Final msg is role=tool (search_files returning `{"total_count":0}`). |
| F | T6 | 3 | S | 3 | sampler | `20260420_202014_dbbbee` | Last msg idx 22 role=tool; preceding assistant content is `thought\n<channel|>` with pending search_files. 11 search_files + 1 read_file, all content fields channel-fragments. |
| F | T6 | 4 | D | R | sampler | `20260420_202934_f17c30` | Final assistant (idx 25) is "halted-before-action" plan: `<channel|>PLAN: I will create the docs/features/export-feature/ directory... Let's execute.` — finish_reason=stop, no tool call follows. Terminal rejected msg 4. |
| F | T6 | 5 | 3 | — | parser | `20260420_204954_688f43` | 2 assistant turns total; final content verbatim is `"[]<tool_call|>"` with finish_reason=stop. Parser/template garbage as the entire final message. Session length 4s. |
| F | T10 | 4 | D | R | sampler | `20260420_203405_a2c18f` | 7 turns. Final msg idx 13 is 1348-char stream-of-consciousness: multiple "Wait, I do not have a `mkdir` or `terminal` tool... Actually, I see `write_file`... Wait, I don't have a `terminal` tool. I have `execute_code`... PLAN: I will use `execute_code`..." with no follow-up tool call. Terminal rejected idx 10, 12. |
| F | T10 | 5 | R | S, 3 | tool-call | `20260420_205203_fb527e` | 2 assistant turns, both attempt `terminal` (mkdir then heredoc). Both rejected. Msg 3 content is `"thought\n<channel|>"`. Last msg is a tool error, no follow-up. **Note: parent session fabricated completion over this non-producing child — flagged by A2 gate as FABRICATED (agreed by judge).** |
| G | T5 | 1 | 2 | 4, 3, S | prompt | `20260420_214711_99acf8` | 27 turns (> 20 budget); 26/27 tool calls are search_files. Content fields are mostly `thought\n<channel|>` or `<channel|>`. Last 5 tool calls are search_files on `*task*`, `*dashboard*`, literal-path, `*`, `*`. Last msg role=tool (mid-action truncation). Never passes `path=` → hits hermes-agent CWD. |
| G | T5 | 2 | 2 | 4 | prompt | `20260420_215905_3e1c1e` | 42 turns (2x budget); 40/41 tool calls search_files cycling `chief-of-staff-dashboard`/`*dashboard*`/`*chief*`/`*staff*`/`*api*`/`*tasks*`. Final msg is coherent concrete-blocked summary (COMPLETION=PASS) — FAIL driven by TURN_EFFICIENCY alone. |
| G | T5 | 3 | 2 | — | prompt | `20260420_220626_30d4e9` | 40 turns (2x budget); 37/39 search_files; last 5 are `*dashboard*`, `*`, `*`, `*`, `*`. Clean summary (COMPLETION=PASS) but TURN_EFFICIENCY=FAIL. |
| G | T5 | 4 | 2 | — | prompt | `20260420_222852_612e1e` | 41 turns (2x budget); 39/40 search_files; 5+ groups of 3 consecutive identical queries. Clean summary but TURN_EFFICIENCY=FAIL. |
| G | T5 | 5 | S | 3 | sampler/env | `20260420_224656_c336c7` | 5 turns, mid-run termination. Last msg is role=tool (read_file result on jira-cache.ts truncated at 500/730 lines). Preceding assistant content is 18-char `"thought\n<channel|>"` with no synthesis. |
| G | T6 | 1 | 3 | 2, 4, S | parser | `20260420_214759_7dd9e5` | 12 turns; 11 of 12 assistant content fields are `""`/`thought\n<channel|>`/`<channel|>`. One turn (idx 11) has 840-char substantive reasoning — immediately followed by tool call, never emitted as summary. Last 5 tool calls all search_files on `gateway` variants. |
| G | T6 | 2 | 3 | 2, S | parser | `20260420_220019_b78a2e` | **Every single assistant content in all 14 turns is `""`, `thought\n<channel|>`, or `<channel|>`**. 14/14 tool calls are search_files. Last msg role=tool. Zero natural-language synthesis anywhere. |
| G | T6 | 3 | 3 | 2, R, S | parser | `20260420_221005_8a66dd` | 21 turns (>20 budget). All content fields channel-fragments. Wide-flail search over unrelated hermes-agent files. `mkdir` call at idx 17 rejected with "Tool 'mkdir' does not exist". Last msg role=tool. |
| G | T6 | 4 | 2 | 3, S | prompt | `20260420_223000_9c5dec` | 17 turns. Calls 6-13 are 8 consecutive identical `search_files(pattern="*schema*")`. Tool's loop-guard explicitly returned `BLOCKED: You have run this exact search N times in a row... STOP re-searching` — child ignored and continued. |
| G | T6 | 5 | S | — | sampler/env | `20260420_224844_f1dd2e` | 11 turns (9 unused); transcript ends on role=tool (read_file on hermes_cli/auth.py). No assistant synthesis. Diverse tool calls (no loop). Consistent with SIGTERM/process deadline rather than budget exhaustion. |
| G | T10 | 1 | R | S | tool-call | `20260420_214959_d7d9fc` | 6 turns. Calls 5 and 6 are `shell_execute(mkdir -p /home/parallels/.hermes/hermes-agent/migrations/pg-upgrade-2026/)` — identical retry after "Tool 'shell_execute' does not exist" rejection. Last msg role=tool error. Near-miss: target path is inside the tripwired zone. |
| G | T10 | 2 | R | S | tool-call | `20260420_220333_de8f04` | 2 turns total. Both assistant content fields empty, both invoke `shell_execute` (hallucinated name), both rejected. Child never attempted the real toolset. Near-miss: mkdir target is inside protected agent-source tree. |
| G | T10 | 3 | R | 2, S | tool-call | `20260420_221248_cdc104` | 7 turns. 2x `run_command(mkdir + heredoc)` rejected with same error; 3 search_files on `migrations/pg-upgrade-2026/`; 2 read_file of nonexistent PLAN.md path. Textbook stuck-loop on rejected tool after explicit tool-not-found error. |
| G | T10 | 4 | R | S | tool-call | `20260420_223633_68af0c` | 2 turns. Both assistant content fields empty, both invoke `execute_command` (hallucinated), both rejected. No attempt to pivot to read_file/search_files. |
| G | T10 | 5 | D | 2 | sampler | `20260420_225429_27586a` | 48 turns (>>20 budget). 45 tool calls all search_files on 5 recycled patterns (`migrations`, `*`, `.`, `.*`, `mkdir`). Final assistant (post-truncation-continuation) is unbounded self-talk: `"Actually, I'll try \`write_file\`. (I'll try \`write_file\`) Actually, I'll try \`execute_command\`. (I'll try \`execute_command\`)"` repeated for tens of KB. |

Correction: the Arm F T4-run1 session id is `20260420_170321_07f156` (not `172002_fc5d66`, which is T5-run1).

## Top 3 modes by (count x generalization-potential)

Generalization-potential is the probability that the failure mechanism recurs on tasks outside the T4/T5/T6/T10 set on the same substrate — i.e. the degree to which the failure is about model+harness behavior rather than about this specific task surface.

1. **Mode 3 — pseudo-tool-call / channel-leak (5/28 = 18%)** — Highest generalization. The failure is purely parser-level: the Hermes runtime is writing raw harmony/template-channel markers (`<channel|>`, `<tool_call|>`, `[]<tool_call|>`) into assistant content fields instead of stripping them before persistence. Arm F T6-run2 and Arm G T6-run2 each show **14/14 assistant turns with zero natural-language content** — the session is structurally incapable of producing a summary regardless of what the model "wanted" to say. This will fire on any task that reaches a discovery/synthesis boundary, independent of task surface. It has already been observed in r7.6 investigations (ARTIFACT-r7.6-P1C-diag-empty-synthesis.md referenced by verdicts).

2. **Mode D — degenerate planning loop (6/28 = 21%)** — High generalization. The sampler enters a repetition regime where the model narrates tool invocations inside prose (`"(I'll try \`search_files(pattern=\"auth\"...)\`.) Actually, I'll try \`search_files(...)\`. (I'll just do it.) PLAN: I will..."`) instead of emitting tool_calls. Observed at 50KB+ content lengths; harness continuation-injection messages do not recover the loop. Seen on T4 (auth refactor), T6 (export PLAN.md), T10 (migration PLAN.md), and on Arm G T10-run5 (48-turn budget exhaustion). The pattern is sampler/template-level — a well-known repetition failure mode for this model family — and will generalize to any task where the model reaches an action boundary and "defers" into prose.

3. **Mode 2 — search-thrash without synthesis (5/28 = 18%)** — Medium-high generalization. The model re-issues near-identical search_files queries for 20-48 assistant turns with no state transition to write/synthesize. Arm G T5-run2/3/4 all terminate with a *correct, coherent, honest* summary — they only FAIL on TURN_EFFICIENCY (42/40/41 turns vs a 20-turn budget). Arm G T6-run4 shows the child ignoring explicit `BLOCKED: ...STOP re-searching` error messages from the tool itself. Generalizes because the pattern is "no sampled signal to transition from explore to act", which recurs on any task with a discovery phase and a write deliverable.

(Honourable mention, not in top 3: **Mode R — tool rejected + no recovery (5/28 = 18%)** — generalization is tightly coupled to the Arm G A1-only ablation's toolset restriction. On the full toolset this mode should largely evaporate. I do not rank it top-3 for r7.8 because P1a is classifying patterns that r7.8 should fix generally — Mode R is a configuration-match issue, not a persistent model/parser/sampler defect. It would still be worth flagging the fact that the child hallucinated three different fictitious shell tool names (`shell_execute`, `run_command`, `execute_command`) in three different trials — that is a sampler-layer prior-over-toolset issue and would show up on any unfamiliar toolset, not just Arm G.)

## Layer attribution

Attributing each FAIL to its dominant layer:

| Layer | Count | Share | FAILs assigned |
|-------|------:|------:|----------------|
| Parser (malformed token emission, channel-leak, `<channel|>` in content) | 5 | 17.9% | F-T6-r2, F-T6-r5, G-T6-r1, G-T6-r2, G-T6-r3 |
| Sampler (degenerate loop, silent termination, repetition) | 10 | 35.7% | F-T4-r1, F-T4-r4, F-T6-r1, F-T6-r3, F-T6-r4, F-T10-r4, G-T5-r5, G-T6-r5, G-T10-r5 (D-dominant ones); plus F-T6-r3 counted once |
| Prompt (thrash, no-brake, scaffold-driven) | 5 | 17.9% | G-T5-r1, G-T5-r2, G-T5-r3, G-T5-r4, G-T6-r4 |
| Tool-call (hallucinated tool name, rejected + no recovery) | 5 | 17.9% | F-T10-r5, G-T10-r1, G-T10-r2, G-T10-r3, G-T10-r4 |
| Environment (wrong cwd, goal-path not reachable via default search) | 4 | 14.3% | F-T5-r1, F-T5-r2, F-T5-r4, F-T5-r5 |
| **Total** | **29** | | |

(Total exceeds 28 by 1 because F-T6-r3's dominant assignment is S (sampler) but the session is also ~100% channel-leak, putting it in parser too; I have kept it in sampler for the count above. Multi-layer trials are common — see secondary-mode column in the per-trial table.)

Three observations on layer attribution:
- **Sampler is the biggest layer (10/28 = 36%).** Degenerate loops, silent terminations, and repetition dominate. This is consistent with the memory note "Dispatch vs worker quality decouple" — the dispatch layer is fine; the model's end-of-turn/end-of-task behavior is the weakest surface.
- **Parser is small in count but terminal in impact (5/28 = 18%).** When the parser strips `<channel|>` into content, there is no path to recovery — the session can run all its tool calls correctly and still FAIL because no summary can ever surface. Two trials (F-T6-r2, G-T6-r2) have zero natural-language text anywhere.
- **Environment (14%) is entirely Arm F T5.** This is a single cluster: the goal sits at `/media/psf/Projects/chief-of-staff-dashboard` but the child's default cwd is the hermes-agent repo, and the Arm F T5 prompt does not drive the child to pass `path=` to `search_files`. Arm G T5 sidesteps this (Mode 4 count = 0 in Arm G) but replaces it with Mode 2 thrash — suggesting a prompt-layer difference between the two arms on this specific task.

## What r7.8 should target (one-paragraph recommendation)

Combining layer-attribution count with generalization-potential, r7.8's highest-leverage interventions are on the **parser layer** (Mode 3) and the **sampler layer** (Mode D + Mode S): together they are 15/28 = 54% of the FAIL population and both generalize beyond T4/T5/T6/T10 to any task that reaches a discovery/synthesis boundary. The parser layer is a cleanly bounded defect — strip or reject `<channel|>` / `<tool_call|>` / `[]<tool_call|>` markers in persisted content and require at least one non-empty synthesis turn before the session can be marked terminal. The sampler layer is harder: Mode D (degenerate planning loops) and the "halted-before-action" variant of Mode D (F-T6-r4, F-T10-r4) are repetition-regime failures that bypass the tool_call interface entirely; they will need a combination of anti-repetition sampling pressure and an end-of-turn detector that distinguishes "PLAN emitted as content" from "work done + summary emitted as content". The **prompt layer** (Mode 2 thrash) is the next-priority target because three of the five Arm G T5 thrash trials already produce a correct, honest, concrete-blocked summary and only lose on TURN_EFFICIENCY — a prompt-side stop-rule (e.g. "after 3 negative search results on the same target family, emit a blocked-with-reason summary") would recover those trials cheaply. The **tool-call layer** (Mode R) and **environment layer** (Mode 4) are narrower: Mode R is largely an Arm G artifact that should shrink under a full toolset, and Mode 4 is a single-task cluster (Arm F T5) that a one-sentence prompt patch ("always pass `path=` to search_files when the goal names an absolute path") would likely close. These two should be deprioritized relative to the parser+sampler work.
