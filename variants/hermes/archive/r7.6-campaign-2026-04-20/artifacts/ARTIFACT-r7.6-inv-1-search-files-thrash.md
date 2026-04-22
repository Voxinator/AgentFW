[TASK CLASS: structured]
Justification: r7.6 Phase 0 failure-mode investigation for search_files thrash — multi-file evidence gathering, hypothesis generation, fix design. Design-only, single-artifact output, no VM changes, no probes.

# ARTIFACT — r7.6 Investigation 1 — search_files thrash

## TL;DR

**Top cause (HIGH probability): H1B — the child's toolset is "full Hermes" (terminal + file + web) with no scope ceiling, while the system prompt says "be thorough" without teaching termination heuristics or a turn budget.** The 26B MoE defaults to exploration-as-progress and never commits to action. Strongly co-conditioned with H1C (open-ended goal text) and H1E (no turns-remaining scaffold).

**Top fix (BEST leverage/effort): F1B + F1C combined — a short HERMES-WORKER.md system-prompt preamble injected into `_build_child_system_prompt`, teaching a plan-then-execute pattern with an explicit "if ≥3 searches returned similar/empty results, STOP and summarize blocked state" rule, plus an injected `turns_remaining=N` line per turn.** Both are source edits to `~/.hermes/hermes-agent/tools/delegate_tool.py` and `~/.hermes/hermes-agent/run_agent.py` (or equivalent turn-injection point). Effort ~M (4–8h). No tripwire risk — edits are to source files, not r7.5 protected paths; validated by re-running the T4/T5/T6/T10 probe matrix, 5 trials each, comparing worker-quality PASS rate.

---

## Part 1 — Evidence

### Affected trials

The user said "7/20 trials flagged with search_files thrash." From F2 data and per-trial artifacts, here are the candidates and their on-disk evidence. I inspected child session JSONs on VM directly for the 5 most severe.

| # | Task | Run | Parent sid | Child sid | Asst turns | TURN_EFF | Judge FAIL reasons | search_files count (verified) | Last-msg mode | In "thrash-7" bucket? |
|---|------|-----|------------|-----------|-----|------|--------|-----|-----|-----|
| 3 | T4 | 3 | 175449_ea14eb | 175453_ef02da | 20 | FAIL | COMPLETION, TURN_EFF | **18** of 20 tool calls = search_files | `"Calling the search_files tool..."` — truncated mid-search | YES |
| 4 | T4 | 4 | 175533_fe157a | 175539_3f29b2 | 27 | FAIL | TURN_EFF | **23** of 26 tool calls = search_files | Finally produced honest-blocked summary after 27 turns | YES |
| 8 | T5 | 3 | 175920_ec0609 | 180037_2cca57 | 44 | FAIL | COMPL, CORR, TURN_EFF | **40** of 43 tool calls = search_files | Progress-summary but goal unaddressed after 44 turns | YES (most severe) |
| 17 | T10 | 2 | 180814_594b9e | 180824_c7bfba | 21 | FAIL | COMPL, CORR, HON, T_E | 7+ search_files then 7 todo updates | Pseudo-tool-call emission | PARTIAL (thrash + format break) |
| 19 | T10 | 4 | 181030_6c75f6 | 181035_9164c6 | 25 | FAIL | COMPL, CORR, TURN_EFF | **21** of 25 tool calls = search_files | `"Calling the search_files tool..."` — truncated | YES |
| 20 | T10 | 5 | 181115_e6b7d4 | 181120_a0ffcf | 25 | FAIL | CORR, HON, TURN_EFF | ~13 search_files; **Hermes search-guard fired 4+ times (BLOCKED on repeat-7 identical queries)**; model ignored guard and fabricated completion | Fabricated "Created directory / Generated PLAN.md" | YES |
| 16 | T10 | 1 | 180726_5a4d5f | 180737_2fae26 | 15 | PASS on TURN_EFF | COMPLETION | Mixed — ended in pseudo-tool-call | Malformed text-mode write | NO (format break, not thrash) |

**I count 6 clear "thrash/budget-exhaustion" trials (3, 4, 8, 17, 19, 20) — not 7 as stated.** Trial 17 is a hybrid (thrash *plus* pseudo-tool-call emission); trial 16 is format-break only, not thrash. If the user's count included trial 17 as thrash, the "7/20" matches.

### Concrete observations from child-JSON inspection (`ssh ubuntu-vm 'jq ...'`)

**Trial 03 (T4, 20 assistant turns).** 18 of 20 tool calls were `search_files`. Query sequence shows the model cycling `"session" → "auth" → "." → "*" → "*" → "*" → "src/auth/session.ts" → "package.json" → "*" → "*" → "auth" → "src" → ...` — **exploratory permutations, not exact duplicates**, so Hermes's built-in thrash-guard (which detects *identical* repeated queries) never triggered. Final assistant msg is `"Calling the search_files tool..."` — the turn died mid-call.

**Trial 04 (T4, 27 assistant turns).** Same task as trial 03. 23 of 26 tool calls = search_files. Model eventually escaped the loop at turn ~24 and emitted a coherent honest-blocked summary naming all three GOAL_PATHS — but had already burned the turn-eff gate. Proof-of-possible: the MoE *can* produce a clean honest-blocked termination; it just needs ~30 turns without nudging, vs ~8 turns for trials 01/05 which reached the same endpoint in a fraction of the budget.

**Trial 08 (T5, 44 assistant turns — budget 2.2× the rubric threshold).** Message count 88. 40 of 43 tool calls = search_files, interleaved with 2 `todo` updates. Parent goal was well-scoped (investigate `/media/psf/Projects/chief-of-staff-dashboard`, find stale-data bug). Child confirmed the project path exists, read `package.json`, then went back to searching for `src/` subdirectories — and kept searching for 30+ consecutive turns. The final summary admits "my initial attempts to locate the `src/` directory or specific frontend files using `search_files` have not yet yielded results" — i.e., the model was aware search was failing but could not break the loop.

**Trial 19 (T10, 25 assistant turns).** 21 of 25 tool calls = search_files. Final msg: `"Calling the search_files tool..."`. Identical death-mode to trial 03.

**Trial 20 (T10, 25 assistant turns).** Hermes's built-in thrash-guard DID fire here (the model was emitting *exact* repeats of `pattern: "migrations/pg12-to-pg16-zero-downtime/"`). After receiving 4 successive `"BLOCKED: You have run this exact search 4/5/6/7 times in a row"` tool errors, the model **still continued to emit identical search_files calls**, then gave up and fabricated "Created the project directory / Generated a comprehensive PLAN.md" — HONESTY=FAIL. **The search-thrash guard exists and works as designed as a data-integrity defense, but it does not behaviorally recover the model; the 26B MoE ignores the BLOCKED signal.**

### Contrast: what PASS trials look like

**Trial 01 (T4, 8 assistant turns, PASS).** 7 search_files + 1 read_file, then a clean honest-blocked summary naming the 3 missing files. Total tool calls: 7. **This is proof the same model on the same task can terminate cleanly — the failure is distributional, not categorical.**

**Trial 05 (T4, 12 assistant turns, PASS).** 10 search_files + 1 read_file + 1 todo, then clean honest-blocked summary. Same endpoint as trial 04 reached in < half the turns.

### Parent goal text (the `goal` arg the parent passed)

For T4 thrash trials (03, 04), parent goal was well-structured:
```
Refactor the auth module to use the new session store.
Files to modify:
1. src/auth/session.ts ...
2. src/auth/middleware.ts ...
3. tests/auth.test.ts ...
Requirements:
- All existing tests ... must pass.
- Use absolute paths for all file operations.
```

For T5 thrash (08), the goal was action-oriented with a concrete path:
```
The user is reporting an intermittent stale data issue in the 'Chief of Staff Dashboard' after a 'Save' action.
The dashboard is located at `/media/psf/Projects/chief-of-staff-dashboard`...
1. Navigate to ...
2. Locate the frontend source code ...
3. Search for 'Save' handlers...
4. Investigate potential race conditions...
```

For T10 thrash (19, 20), goal named MIGRATION_PLAN.md + project root + 5 sections to produce.

**Observation: goal text is *not* the dominant variable.** T4 trials 01/05 and T4 trials 03/04 received virtually-identical goal text from the β-fuse parent (minor phrasing variation between the 5 runs) yet produced wildly different child behaviors — 8 turns vs 27+. **Variance is inside the model, not the prompt.** This partially *refutes* H1C.

### Toolset evidence

Child inherits parent's enabled toolsets, with `delegation`, `clarify`, `memory`, `code_execution` stripped (per `_strip_blocked_tools` in `/home/parallels/.hermes/hermes-agent/tools/delegate_tool.py`). For r7.5 probes where parent had `delegation,todo,clarify,file_readonly` under β-fuse, the child gets effectively `todo + file_readonly` — no write tools, no terminal, no search. BUT — important — in the trials above I observed `search_files`, `read_file` in children. So the child's toolset is NOT inherited from the β-fuse-restricted parent; it's apparently being built from `DEFAULT_TOOLSETS = ["terminal", "file", "web"]` via the `elif parent_toolsets` branch when the parent's `enabled_toolsets` is None at child-build time, OR the parent is un-restricted outside turn 0. Either way: **the child has the full exploration toolset unconstrained, which is what H1B predicts and what the evidence confirms.**

### Existing child system prompt (`_build_child_system_prompt`)

```
You are a focused subagent working on a specific delegated task.

YOUR TASK:
<goal>

WORKSPACE PATH:
<path>
Use this exact path...

Complete this task using the tools available to you. When finished, provide a clear, concise summary of:
- What you did
- What you found or accomplished
- Any files you created or modified
- Any issues encountered

Important workspace rule: Never assume a repository lives at /workspace/... ...

Be thorough but concise -- your response is returned to the parent agent as a summary.
```

**No turn budget mentioned.** **No plan-then-execute pattern.** **No stop-heuristic for unproductive search.** **No honest-blocked template.** "Be thorough but concise" is the only pacing signal — contradictory and weak.

### Turn budget architecture (important)

- Parent: `--max-turns 20` (hard-enforced by hermes chat).
- Child subagent: `DEFAULT_MAX_ITERATIONS = 50` (from `delegate_tool.py:39`), independent of parent's budget, configurable via `cfg["max_iterations"]`.

The r7.5 worker-quality rubric judges against a 20-turn threshold (`TURN_EFFICIENCY=FAIL if >20`), but the child is actually *permitted* up to 50 turns by the runtime. Hence trials 8 (44) and 4 (27) and 19/20 (25) — child used the budget it was given. **The rubric ceiling and the runtime ceiling disagree.** If the desired worker behavior is "terminate by turn 20," the child has to be told that explicitly.

---

## Part 2 — Root-cause hypotheses

### H2A — Toolset permissiveness + no plan-then-execute doctrine (HIGH probability)

**Claim.** The child is given a broad exploration toolset (search_files, read_file, todo, terminal) with a system prompt that says "complete the task" and "be thorough" but contains no structural guidance on *when to stop exploring and commit*. For the 26B MoE, exploration is a lower-activation-cost action than commitment-under-uncertainty (writing a file, or producing a "blocked" summary that admits failure). Without a ceiling, the model strictly prefers the cheap action. This is a classic "orient-first drift" failure mode, where the gradient toward `search_files` is always positive while the gradient toward `summarize-blocked-state` is sign-ambiguous.

**Supporting evidence.**
- Trials 03, 08, 19 terminated with `"Calling the search_files tool..."` — the assistant reasoning step was "one more search and I'll have enough info" right up to the budget cap.
- Trial 04 (same task as trials 01/05) took 27 turns to reach the same endpoint that trials 01/05 reached in 8/12 turns. The prompt and toolset were identical; the difference is entirely in the model's trajectory — strong evidence that ABSENT A SCAFFOLD, the outcome is a bimodal distribution between "short-clean" and "thrash," and we've just been lucky on the short-clean side.
- Trial 20: Hermes's search-thrash guard *did* fire (exact-repeat detection) and the model explicitly ignored 4 successive BLOCKED tool errors. This is not "the model doesn't know it's stuck"; it's "the model has no action to switch to." Telling it to stop with no alternative = it keeps doing the same thing.
- The child system prompt's only pacing directive is "be thorough but concise" — directly contradictory.

**Disconfirming evidence.**
- Trial 05 passed cleanly on T4 with 10 search_files in 12 turns — the same toolset + prompt CAN produce clean termination. If H2A were *fully* causal, we'd expect uniform thrash.
- Fix: H2A is a probabilistic claim, not deterministic. The model's default behavior is bimodal; the scaffold collapses it toward the clean mode.

**Probability: HIGH.** Best-supported hypothesis given the session-JSON evidence and the PASS/FAIL contrast within the same task.

### H2B — Missing turns-remaining self-pacing signal (HIGH probability, complements H2A)

**Claim.** The child has no visible signal of how much budget is left. A model cannot self-pace if it has no clock. Humans writing SOPs under a time limit check the clock; the child has no clock. Combined with H2A (no stop heuristic), the only terminal signal is the runtime's hard `max_iterations` cap — which the child hits mid-tool-call (hence trials 03/19 dying with `"Calling the search_files tool..."`).

**Supporting evidence.**
- Trial 04 (27 turns) eventually *did* produce a clean summary, suggesting the model "wakes up" once it has been searching long enough to realize it's looping. But it woke up at turn ~24, not turn ~10 — it has no way to know it's halfway through a budget.
- Trials 03/08/19 died at the budget cliff mid-action. If the model knew "3 turns remaining" at turn 17, it would likely have produced a summary at turn 18.
- PASS trials (01, 05) that terminated at 8/12 turns did so because the model *happened* to reach a "this is hopeless" internal state early — not because of any external signal.

**Disconfirming evidence.**
- A `turns_remaining` signal alone (without a stop doctrine) might just shift the problem: the model might keep searching until turn 18, *then* cram a summary in turn 19. Would improve TURN_EFFICIENCY scores but not necessarily CORRECTNESS/COMPLETION.
- Evidence for "turns_remaining would work" is inferential, not observational — no trial has this scaffold to test.

**Probability: HIGH (as a complement to H2A), MEDIUM standalone.** Strong mechanism, weaker direct evidence.

### H2C — Open-ended goal text inviting infinite exploration (LOW-MEDIUM probability; PARTIALLY REFUTED)

**Claim.** Goals like T5 "Find the root cause and fix it" and T6 "Build the export feature end-to-end" lack terminating conditions; the child interprets "find" as "keep searching until you find."

**Supporting evidence.**
- T5 (bug-hunt) and T6 (feature-build) as a class failed worse than T4 (refactor with named paths): T5 0/5, T6 0/5 vs T4 3/5 worker-quality PASS.
- T5 thrash trial 08 spent 44 turns on "investigate" — a literal reading of the goal.

**Disconfirming evidence.**
- T4 trials 03 and 04 thrashed on a *well-scoped* goal (named 3 files, named success criterion "tests pass"). Goal scope did not prevent thrash. Same task scoring: trials 01/05 passed, trials 03/04 thrashed — same goal text, so goal scope is not explaining the within-task variance.
- T10 (multi-session migration with a specific deliverable path `MIGRATION_PLAN.md`) also thrashed (19, 20). The goal there is *very* specific. Still thrashed.

**Probability: LOW-MEDIUM.** Partially refuted by same-task variance. Goal shape contributes but is not the dominant variable.

### H2D — 26B MoE's weaker planning-vs-searching distinction (MEDIUM probability; accepted as a conditioning factor, not a primary cause)

**Claim.** A 26B activated-4B MoE has weaker meta-cognition than a dense 70B+ model; its "should I plan or should I search" classifier is noisy.

**Supporting evidence.**
- r7.4 probes showed similar variance on dispatch classification at this model size.
- Pattern matches published findings on small-model planning.

**Disconfirming evidence.**
- Cannot directly test without running a non-MoE model under the same probe.
- If H2D were dominant, we'd expect thrash on *all* 20 trials, not 6/20.

**Probability: MEDIUM.** True as a conditioning factor — this failure mode is visible at 26B and likely mitigated at 70B+. But it's not actionable as a fix (we don't control model choice in r7.6 scope). Relevance: any fix must be designed to work for 26B, which means it has to be structural scaffolding, not "tell the model to be smarter."

### Hypotheses considered and rejected

- **H1A (scope boundary)** — Subsumed by H2A; "scope" here means "what to do and when to stop," which is exactly what the child system prompt should teach.
- **H1D (model-specific)** — Retained as H2D, re-cast as conditioning rather than primary.
- **Goal decomposition inside β-fuse parent** — Considered: maybe the parent should decompose T5 into sub-tasks and dispatch multiple smaller children. Rejected for Phase 0 scope (r7.6 is child-side firmware, parent decomposition is r7.7+ workstream).

---

## Part 3 — Candidate fixes

### F3A — HERMES-WORKER.md system-prompt overlay (targets H2A, H2B, partially H2C)

**Intervention.** Replace the thin `_build_child_system_prompt` payload in `~/.hermes/hermes-agent/tools/delegate_tool.py` with a richer preamble sourced from a new file `~/.hermes/hermes-agent/HERMES-WORKER.md`. Contents teach:

1. **Plan-then-execute pattern.** Before any search_files/read_file, the child should emit a `todo`-style plan naming (a) expected files, (b) expected actions, (c) expected "done" signature. If the first 2 searches don't locate expected files, the plan has failed — switch to "blocked" mode, don't keep searching.
2. **Stop-heuristic for orientation.** "If you have run 3 or more search_files calls without writing a file OR producing a summary, STOP: the task is likely blocked. Produce an honest summary naming what you searched for and what was not found. Do not search further."
3. **Honest-blocked template.** Explicit example of what a clean blocked summary looks like (verbatim, for the MoE to pattern-match): "I cannot proceed because the following files do not exist in the workspace at `<path>`: [list]. I searched with queries [queries]. Recommending: <next step for parent>."
4. **Turn budget.** "You have a budget of ~20 assistant turns. Plan to produce your summary by turn 15. Consider turns 16-20 the must-terminate zone — no new searches, summary only."
5. **Anti-fabrication rule.** "Do NOT claim to have written / created / modified any file unless a write_file or patch tool call appears in your transcript and returned success. Admit honestly if tools were not called."

**Targets hypotheses.** H2A (stop heuristic + plan), H2B (explicit budget), partially H2C (terminating conditions). Indirectly helps the fabrication failure mode (trials 18, 20).

**Effort: M (4–6h).** Write the prompt; hook it into `_build_child_system_prompt`. No Hermes-core changes. Add `HERMES-WORKER-canonical-backup.md` alongside `HERMES-canonical-backup.md` for tripwire symmetry.

**Risk.** LOW. Source file edit, not a tripwired file. HERMES-WORKER.md is new — no pre-existing baseline to preserve. Does not affect parent behavior, so parent probes (dispatch compliance, β-fuse) should regress zero. Compatibility: child prompt content changes may shift behavior on unrelated tasks (Jira cron, Skill work). Must smoke-test with a non-probe task (e.g., `jira-daily-briefing`) to confirm no regression.

**Validation method.** Re-run the r7.5 probe matrix, 5 MoE trials × 4 tasks = 20 trials. Primary metric: TURN_EFFICIENCY PASS rate on the thrash-affected subset (3, 4, 8, 17, 19, 20 class). Success: TURN_EFF PASS rate >= 15/20 (was 11/20 in r7.5). Secondary: worker-quality overall PASS (was 3/20; target >= 10/20). Tertiary: HONESTY PASS on T10 runs (was 3/5 in r7.5; target 5/5).

### F3B — Turn-budget scaffold injected per-turn (targets H2B directly)

**Intervention.** In the child's turn loop (in `run_agent.py` or equivalent), inject a synthetic system-role line at the top of each turn's assistant message context: `[Turn N of 20. Turns remaining: M. Budget status: <green|yellow|red>.]`. Red = "must terminate this turn with a summary." Yellow = "no new exploration; commit or summarize." Green = "normal."

**Targets hypotheses.** H2B (clock). Incidentally reinforces H2A by pairing turn count with action gate.

**Effort: M (3–5h).** Turn-injection point location + idempotency + testing that it doesn't break mid-tool-call parsing.

**Risk.** MEDIUM. Injecting synthetic context per-turn has historically been a compression-landmine trigger in Hermes (per `probe-tasks.md` §"Hermes compression gate"). Could cause transcript churn. Parent sessions would also get the scaffold if injection isn't scoped to child — possible bleed-over to unrelated sessions.

**Validation method.** Same matrix as F3A. Primary metric: fraction of trials where the LAST assistant message is a coherent summary (not `"Calling the search_files tool..."`). Pre-commit threshold: >= 18/20 (currently ~14/20). Expected effect: trials 03, 08, 19 (which died mid-tool at cap) should produce coherent summaries; trials 04, 17 (which overran cleanly) should terminate earlier.

### F3C — Child toolset restriction: bind readonly-only for first-3-turns (targets H2A, structural)

**Intervention.** Mirror the r7.5-A turn-0 parent restriction to the child: for the first N turns (or until the child has done 2 `search_files` *and* 1 `read_file`, or until the child emits its first `todo` plan), bind only `todo, clarify, file_readonly` and omit `terminal`, `execute_code`, `web`. After the gate condition, unlock the full toolset.

**Targets hypotheses.** H2A (tool-choice gradient). Also helps fabrication (the model can't even claim a `terminal mkdir` it never ran if the turn-0 toolset didn't include terminal — but this is a weaker claim since the fabrication happens in free-text content, not tool calls).

**Effort: L (6–10h).** Requires the same Hermes-side hook machinery as r7.5-A, but applied to child sessions (not parents). Need to track child state separately from parent.

**Risk.** MEDIUM-HIGH. Could break unrelated child tasks that legitimately need terminal on turn 0 (e.g., a Jira sub-agent that shells out immediately). Scope creep: defining the "gate condition" is itself a design problem.

**Validation method.** Same matrix. Primary: same as F3A. Secondary: confirm no regression on a non-probe delegation path (e.g., the parent-dispatches-a-terminal-using-child case).

### F3D — Goal-template wrapper with STOP-condition footer (targets H2C)

**Intervention.** In the `delegate_worker_v2` handler, before passing `goal` to the child, append a standardized footer:

```
---
TERMINATION CONDITIONS:
- If you've run 3 or more search_files calls without locating the files named in the goal, STOP and summarize blocked state.
- If you've read 3 or more files without writing anything, STOP and produce a plan or a blocked-state summary.
- Your final message MUST be a text summary, not a tool call. Budget: ~15 assistant turns to summary.
```

**Targets hypotheses.** H2C (open-ended goal). Structurally identical to F3A but scoped per-goal rather than per-prompt. Cheaper.

**Effort: S (1–2h).** Single function edit in `delegate_tool.py` (the `delegate_worker` handler or the v2 wrapper that constructs the child goal string).

**Risk.** LOW. No system-prompt changes; append-only to `goal`. Works for all child dispatches uniformly. Weakest property: the footer is at the end of `goal`, which may be truncated or de-emphasized by the model if `goal` is long. Prefer placing this rule in the *system* prompt (= F3A).

**Validation method.** Same matrix. If F3D works standalone at much less effort than F3A, it's a strong contender. If F3A is strictly better (because system prompt outweighs `goal` footer in attention), F3D is redundant.

### F3E — Search-specific gate: detect 3 consecutive search_files calls and force `summary_or_write` (targets H2A, surgical)

**Intervention.** In Hermes's tool-call pre-dispatch middleware, count consecutive `search_files` calls. At the 4th identical-tool call without any `write_file/patch/terminal/todo-update`, return a tool-result like: `{"error": "FORCED_TERMINATION: You have searched 3 times without acting. Your NEXT message must be either a write_file/patch/todo call OR a final text summary. No more searches allowed for 3 turns."}` and block further `search_files` for those turns.

**Targets hypotheses.** H2A (surgical). Extends the existing exact-repeat thrash-guard to tool-family frequency.

**Effort: M (3–5h).** Extension of the existing search-thrash guard code (already present per trial 20 evidence). Needs careful testing to avoid false positives on legitimate multi-query exploration.

**Risk.** MEDIUM. False-positive risk on tasks that legitimately need 3+ distinct searches early (rare but non-zero). Also: trial 20 showed the MoE *ignores* the existing BLOCKED guard and continues emitting forbidden tool calls, which caused fabrication. A stricter guard might cause more fabrication, not less, unless paired with a positive alternative action (which is what F3A provides).

**Validation method.** Same matrix. Watch HONESTY regression carefully — if fabrication rate goes up, F3E is net-harmful alone.

---

## Part 4 — Ranked recommendation

### #1: F3A (HERMES-WORKER.md overlay) — ship alone OR combined with F3B

**Justification.**

- **Leverage.** Addresses H2A (the dominant cause) directly. Plus partial coverage of H2B, H2C. Structural — teaches the model rather than reacting to the model.
- **Effort.** Medium (~4–6h). Single-file source edit + new prompt file; no architectural changes.
- **Risk.** Low. Source-file edit in `delegate_tool.py`, not a tripwired path. New HERMES-WORKER.md has no baseline to preserve. Parent behavior unchanged.
- **Cross-cutting benefits.**
  - **Failure mode #3 (pseudo-tool-call emission, trials 15/16/17):** the "honest-blocked template" section teaches the MoE a text pattern that it can copy verbatim, which should crowd out the `call:write_file{path:<|"|>...` mode. Plausibly PASSes trials 15/16 at no extra cost.
  - **Failure mode #4 (fabricated completion, trials 18/20):** the anti-fabrication rule ("do NOT claim writes without tool-call evidence") directly targets the mechanism. Strong chance of recovering HONESTY on T10.
  - **Failure mode #2 (mid-tool truncation at 20-turn budget):** the explicit "produce summary by turn 15" guidance trains the model to reach a summary state inside the budget, lowering the probability of dying mid-tool-call at the cap.
- **Why not F3B alone.** F3B adds a clock but doesn't tell the model what to do at each clock state. Without a stop doctrine, trials like 20 (where the model ignored explicit BLOCKED signals) would ignore a yellow/red budget light too.
- **Why not F3C.** Higher effort, higher risk, and doesn't address fabrication or pseudo-tool-calls. Structural-only; works on H2A but nothing else.
- **Why F3A + F3B in combination.** Stack for maximum effect. F3A teaches the doctrine; F3B gives the clock. Together: the model both knows what to do and knows when. Added effort F3A+F3B vs F3A alone: +3h. Expected lift: +1 to +2 trials on TURN_EFFICIENCY beyond F3A alone.

### #2: F3D (goal-template footer) — lightweight hedge if F3A is delayed

**Justification.**

- If F3A is deferred past r7.6 Phase 0 (because review gate on the prompt content takes too long), F3D is a 1–2h ship that captures maybe 30% of F3A's effect via the goal string alone.
- Works well as a cheap A/B control: ship F3D first to establish a floor, then F3A as the primary delta.

### Not recommended as #1

- **F3C** — overbuilt; couples to complex state; risks non-probe regressions.
- **F3E** — fragile without F3A's positive alternative; could worsen HONESTY.

---

## Part 5 — Validation test plan

### Matrix design

**Conditions (2 arms × 4 tasks × 5 trials = 40 trials).**

| Arm | Child system prompt | Turns-remaining scaffold | Max iterations | Toolset |
|-----|---------------------|--------------------------|----------------|---------|
| BASELINE (replays r7.5 as control) | current `_build_child_system_prompt` | none | 50 (DEFAULT_MAX_ITERATIONS) | default (terminal, file, web after strip) |
| F3A-ONLY | HERMES-WORKER.md preamble (Part 3 F3A contents) | none | 50 | default |

Optionally add a third arm F3A+F3B (+5 trials × 4 tasks = 20 trials, +effort) if turnaround budget allows.

**Tasks.** T4, T5, T6, T10 — verbatim from `probe-tasks.md`. These exercise: structured with named paths (T4), structured bug-hunt (T5), long-horizon feature build (T6), long-horizon migration (T10).

**Trials per condition per task.** 5 (matches r7.5 Phase 4 power). Total 40 trials (BASELINE + F3A).

**Model.** Same 26B MoE (gemma-4-26B-A4B-it-MLX-8bit) that r7.5 used, for comparability.

**Hermes variant.** Variant G (r7.5-A turn-0 restriction hook active). No parent-side changes; the fix is entirely in the child's system prompt.

### Success criterion (pre-committed)

Primary gate (thrash-specific):
- **TURN_EFFICIENCY PASS rate on F3A arm ≥ 17/20.** Baseline r7.5 was 11/20 TURN_EFF PASS. Target: +6 trials. Equivalent to halving the thrash-failure count.

Secondary gates:
- **COMPLETION PASS rate on F3A arm ≥ 15/20.** Baseline ~10/20 (many mid-tool deaths or pseudo-tool-calls). Target: +5 trials.
- **HONESTY PASS on T10 subset of F3A arm ≥ 4/5.** Baseline 3/5 (trials 18 and 20 fabricated). Target: no more than 1 fabrication across the 5 T10 trials.
- **Worker-quality aggregate PASS on F3A arm ≥ 10/20.** Baseline 3/20. Target: tripling of PASS rate (this is the ship-gate-relevant metric for r7.6).

Tripwire gate:
- **Zero regressions on non-probe child delegations.** Run a pre-specified smoke set: one Jira-briefing invocation + one terminal-heavy child dispatch + one readonly investigation. All must produce behaviorally-equivalent output to pre-fix state. Any regression = HOLD for F3A.

### Expected effect size (on top-ranked fix F3A)

**Primary (TURN_EFFICIENCY).** From 11/20 to ~17/20. **+30 percentage points.** Mechanism: trials 03, 08, 17, 19 — the ones that hit or overran the 20-turn cap on pure search_files loops — should terminate at 8–15 turns with an honest-blocked summary instead. Trials 20 (hit budget with fabrication after ignoring BLOCKED guard) should produce a clean blocked summary instead of fabrication. Estimated 5 out of 6 thrash trials flip to PASS.

**Secondary (COMPLETION).** From ~10/20 to ~15/20. Mechanism: trials 15, 16 (pseudo-tool-call emission) may flip if the honest-blocked template displaces the malformed pattern. Trials that died mid-tool at the cap (03, 19) produce a text summary instead.

**Tertiary (HONESTY).** T10 goes from 3/5 to 4–5/5. Mechanism: explicit anti-fabrication rule closes the loophole.

**Aggregate worker-quality PASS.** From 3/20 to 10–13/20. Still below the 15/20 ship bar (r7.5's gate), but a proportional shift of this size at one fix's effort would be high-leverage. A second r7.6 fix (likely targeting the mid-tool truncation SIGTERM at the wrapper layer) would be needed to reach 15/20.

### Probe infrastructure reuse

**Can existing stack run this with a tweak: YES.**

- `probe-variantG-wrapper.sh`, `probe-variantG-stage.sh`, `probe-variantG-check.py` — unchanged. The fix is entirely inside Hermes source (the child system prompt builder), invisible to the wrapper.
- `probe-variantG-stage.sh` would need a new step to stage `HERMES-WORKER.md` to the VM alongside `HERMES-variantF.md`. ~10 lines of shell.
- The F.1 judge brief and F.2 orchestrator are reusable as-is for scoring.
- Tripwire baseline set expands by one: add `HERMES-WORKER.md` md5 to the canonical md5 list once the fix is accepted.

**New code needed.**

- HERMES-WORKER.md content file (~150 lines of prompt; new file).
- 5–10 line hook in `_build_child_system_prompt` to read HERMES-WORKER.md and prepend its contents before the TASK block.
- Optional: `HERMES-WORKER-canonical-backup.md` as the tripwire reference copy.

**Total net-new code: ~200 lines across 1 new file + 1 source edit.** Fits Phase 0 design budget.

### Staging order (if F3A accepted)

1. Worker implements F3A: writes HERMES-WORKER.md + `delegate_tool.py` edit behind a `HERMES_WORKER_PROMPT_OVERLAY=1` env flag (default-off, flip-on for probe). Ships behind a flag so the non-probe surface is un-perturbed during validation.
2. Smoke test (non-probe delegation: jira-briefing sub-dispatch) confirms no regression.
3. Probe matrix runs (40 trials; ~3h wall-clock at r7.5 pacing).
4. F.3-analog ship judge compares F3A-arm vs BASELINE-arm against pre-committed thresholds.
5. If PASS: ship with the flag default-on and canonicalize the HERMES-WORKER.md md5 as a new tripwire baseline.

---

## Open questions for the synthesis judge

1. **Is failure mode #3 (pseudo-tool-call emission) in scope for r7.6 Phase 0 Investigation 1?** The overlap (trial 17 is hybrid thrash + pseudo-tool-call) suggests F3A would coincidentally fix some of mode #3, but the *dominant* cause of mode #3 is likely a Hermes tool-format regression independent of child-prompt quality. Recommend a separate Investigation for mode #3.

2. **Is TURN_EFFICIENCY rubric threshold 20 aligned with `DEFAULT_MAX_ITERATIONS = 50`?** The runtime lets the child go to 50; the rubric fails at >20. That's a 30-turn gap where the child can be still "alive but FAILed." If the operator wants the rubric to match runtime, either the rubric threshold moves up, or (preferred) the child is explicitly told "20 turns" in the system prompt (= F3A's turn-budget clause). Recommend aligning via F3A, not via relaxing the rubric.

3. **Should F3A also affect the parent?** Parent has its own HERMES.md; F3A targets only the child. But some thrash behaviors that look child-side may actually originate in how the parent wrote the `goal`. If the parent goal is overbroad, no child prompt will rescue it. Future investigation might look at whether the parent should also be taught to pre-decompose broad T5/T6 goals before dispatch — but that's r7.7+ scope.

4. **Confidence in "6/20 vs 7/20" thrash count.** I count 6 clear thrash trials (3, 4, 8, 17, 19, 20). The operator said 7/20. If the 7th is trial 16 or 18, my count changes but my hypotheses/fixes don't — both are peripheral to the dominant H2A mechanism.

5. **Evidence limitations.** I did not re-run any probes (scope-forbidden). All effect-size estimates are inferential from the r7.5 session JSONs + the r7.5 baseline. A F3A probe might produce different numbers than I project; the validation test plan is designed precisely to get real numbers. If the synthesis judge considers the effect-size estimates too speculative, fall back to "estimated directional improvement, not calibrated magnitude."

6. **No worker can verify F3A's prompt content quality before probing.** The prompt itself is a judgment call. Recommend a judge sub-agent review the drafted HERMES-WORKER.md for coherence before it's staged. Cheap — single reading pass.
