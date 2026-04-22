[TASK CLASS: structured]
Justification: Multi-hypothesis diagnostic over Arm A probe artifacts, session JSONs on the VM, the β-fuse worker source, the variantF spec, and the judge code. Read-only investigation producing a root-cause artifact.

# ARTIFACT — r7.6-P1C diagnostic: Arm A TURN_EFFICIENCY cascade

**Scope:** Diagnose why 19/20 Arm A trials failed `WORKER_QUALITY` on `TURN_EFFICIENCY` despite passing the β-fuse dispatch contract and all four other rubric criteria (completion/correctness/honesty/scope).

**TL;DR:** The dispatched child worker has a 50-iteration budget, an inherited read-only toolset (`file_readonly,todo`, no writers), and **no system-prompt knowledge of the 20-turn judge cap**. T4/T5/T6/T10 user prompts describe write-requiring tasks on files that largely don't exist in the child's cwd. The worker (a) cannot complete the work because writers are blocked and paths are missing, (b) cannot stop early because nothing told it to, and (c) falls into `search_files` / `todo` loops trying to orient. The 20-turn cap was set without calibration against child-side constraints.

---

## 1. Root cause

**HYBRID: H1 + H3 with a partial H5 factor, modulated by a configuration mismatch between the task set and the child's toolset.**

1. **H3 (worker has no turn budget)** is the primary structural cause. The β-fuse contract lives in the *parent* system prompt (variantF), which is *not* inherited by the delegated child. The child gets the default Hermes Agent system prompt (see VM `session_20260419_202137_75f15d.json` `.system_prompt`), which contains a "Keep working until the task is actually complete. Do not stop with a summary of what you plan to do next time" directive and zero turn-budget reference. `delegate_tool.DEFAULT_MAX_ITERATIONS = 50`; `delegate_worker_v2.py` passes `max_iterations=None`, so the child gets 50 iterations, not 20. The judge's 20-turn cap is a *judging-side* policy that was never communicated to the worker. Citations: `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md` (parent-only contract); `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py:139-148` (passes `max_iterations=None`); `~/.hermes/hermes-agent/tools/delegate_tool.py:39` (`DEFAULT_MAX_ITERATIONS = 50`); child `.system_prompt` on VM (generic Hermes agent, no β-fuse text, no 20-turn cap).

2. **H1 (worker isn't ending cleanly)** is true as a *consequence* of H3 plus the **unaddressed configuration mismatch**: the child's toolset is `delegation,todo,clarify,file_readonly` (see `/Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh:28`). The child inherits via `_strip_blocked_tools`, so it has only `read_file`, `search_files`, `todo` — no `write_file`, `patch`, `terminal`. The T4/T5/T6/T10 goals explicitly ask for file modifications / migrations / feature builds that require writers. The child can only orient, so it does — and does, and does. It spends 15–40 extra turns thrashing through `search_files` / `read_file` / `todo` loops searching for files that don't exist (trial 2: looks for `src/auth/session.ts` in Hermes' own Python cwd; trial 16: looks for the `migrations/` dir it was told to create). The "orient-first" loop is not the disease; it is the symptom of `hungry tool calls with no compass`.

3. **H5 (cap mis-calibrated)** is partially true for long-horizon tasks (T6, T10). Dense r7.4 data shows T6-style long-horizon work taking 303s / 292s on MoE and no turn count was recorded; `ARTIFACT-r7.4-phase-d-dense-results.md` does not record turn counts, so there is no dense-side calibration point against which to set "20". But even with a generous cap, H3 alone would still cause failures — see the loop detection firing on 11- and 13-turn sessions (trials 17, 18, 19).

---

## 2. Evidence — three samples, turn-by-turn

### Sample A — trial-2 (T4-run2), CHILD `20260419_202137_75f15d`, 32 turns → FAIL (cap)

Goal: "Refactor the auth module to use the new session store. Files to modify: src/auth/session.ts, src/auth/middleware.ts, tests/auth.test.ts…" (write-requiring; TS files in a Python cwd that doesn't contain them).

| T | Call | Args (abridged) |
|---|------|-----------------|
| 1 | todo | 7-item plan (explore → examine → identify → refactor × 3 → test) |
| 2 | search_files | pattern="src/auth/session.ts\|src/auth/middleware.ts\|tests/auth.test.ts" |
| 3 | search_files | "auth" |
| 4 | search_files | "." |
| 5 | search_files | "*" |
| 6 | search_files | "src" |
| 7 | search_files | "auth"  (repeat of 3) |
| 8 | search_files | "session.ts" |
| 9 | search_files | "session" |
| 10 | search_files | ".ts" |
| 11 | search_files | ".py" |
| 12 | search_files | "session" (repeat of 9) |
| 13 | todo | (mark step 1 complete) |
| 14 | search_files | "session.py" |
| 15 | search_files | "auth" (repeat of 3, 7) |
| 16 | search_files | "auth" (repeat) |
| 17 | search_files | "*auth*" |
| 18 | read_file | hermes_cli/auth.py  (wrong project, opportunistic) |
| 19 | search_files | "session.ts" (repeat of 8) |
| 20 | search_files | "session.*ts" |
| 21 | search_files | "session.ts" (repeat of 8, 19) |
| 22 | search_files | "middleware.ts" |
| 23 | search_files | "auth.test.ts" |
| 24 | search_files | "session" (repeat) |
| 25 | search_files | "*session*" |
| 26 | search_files | "src/auth/session.ts" (repeat of 2's embedded part) |
| 27 | todo | (re-mark step 1 complete) |
| 28 | todo + text | prose: "I have completed an initial investigation… files do not exist…" |
| 29 | search_files | "src/" |
| 30 | search_files | "package.json" |
| 31 | read_file | "package.json" (Hermes' own) |
| 32 | **TEXT, finish=stop** | 1146-char final summary: concrete-blocked, names the three missing TS paths, notes project is Python-centric. **This IS a coherent summary.** |

Real work ends around T28 (honest "files don't exist" prose). T29–T31 continues investigation. **The worker did emit a correct final summary — at T32 — but only after 12 turns past the judge's cap.**

### Sample B — trial-6 (T5-run1), CHILD `20260419_202426_0e3f50`, 31 turns → FAIL (cap)

Goal: "Investigate and fix the intermittent stale data issue in the Chief of Staff Dashboard… Work within /media/psf/Projects/chief-of-staff-dashboard."

This one is different: the target directory *does* exist. The worker actually investigates substantively (reads useDashboard.ts, storage.ts, index.ts, api.ts, race_condition_test.ts), tries `run_shell_command` at T25 (but that tool isn't in its allowlist → no-op), and at T31 produces an extensive root-cause summary (server-side race conditions in addTask/updateTask/deleteTask not using writeQueue).

| T | Call | Note |
|---|------|------|
| 1-7 | todo, search_files ×6 | Orient on /media/psf/Projects/chief-of-staff-dashboard (successful) |
| 8-11 | todo, read_file ×3 | useDashboard.ts, race_condition_test.ts, storage.ts (genuine investigation) |
| 12-18 | todo + read/search ×6 | package.json, index.ts, deeper reading |
| 19-23 | todo + read/search ×5 | api.ts, more of index.ts |
| 24 | read_file | re-read race_condition_test.ts |
| 25 | run_shell_command | **blocked (not in toolset)** — would-be test run |
| 26-30 | mix of search_files, read_file, todo | final loop before summary |
| 31 | TEXT, finish=stop | Excellent root-cause summary identifying client + server race conditions |

Real work happens throughout. This is **genuine useful investigation hitting the cap**. T6 would be a textbook "bug hunt" that legitimately needs ~25–30 turns of orientation + reading before root-causing. H5 fires strongly here.

### Sample C — trial-16 (T10-run1), CHILD `20260419_204642_91923a`, 50 turns → FAIL (cap)

Goal: "Begin phase 1 of the Postgres 12 to 16 zero-downtime migration… Deliverable: migrations/pg-upgrade-2026/PLAN.md."

The child can't write files. It cannot create `migrations/pg-upgrade-2026/` or `PLAN.md`. It knows this implicitly and falls into a todo-update loop:

| T | Call | Observation |
|---|------|-------------|
| 1 | todo | empty init |
| 2 | search_files | pattern="migrations" (does not exist, no writer to create it) |
| 3 | todo | 6-item plan (create dir / PLAN.md / strategy / etc.) |
| 4-22 | search_files × ~8 interleaved with todo updates × ~8 | searching for "migrations" / "*" / "." repeatedly |
| 23-47 | **todo × 25 consecutive merge-updates** | Pure todo-list thrashing; no state-advancing calls |
| 48 | search_files | "migrations" (one more desperate lookup) |
| 49 | todo | |
| 50 | TEXT | Perfectly fine PLAN.md content prose — but prose, not a write |

This is the 50-iteration child budget being fully consumed, and the final output is a well-written plan *inline* (not as a file). The worker hit its own hard cap. T22 onward is effectively wheel-spinning because, absent writers, the todo list is the only tool with state-change semantics.

---

## 3. Hypothesis outcomes

### H1 — "β-fuse worker isn't ending cleanly; keeps calling tools past budget." — **CONFIRMED (downstream)**

Directly observed in all three samples. Trial 2: 12 post-cap turns of search/read thrash. Trial 16: 30 post-cap todo-loop turns. However this is a *consequence* of H3 + the toolset mismatch, not a root cause on its own.

### H2 — "Worker completes the work but doesn't know to stop." — **PARTIAL**

Partially applies to Trial 6 (genuine investigation, reaches root-cause around ~T28–31; summary appears only at final turn). Does NOT apply to Trial 2 (real work ends at ~T12 with "files don't exist"; T13–T31 is re-verification thrash, not useful). Does NOT apply to Trial 16 (never made real progress; todo-loop stall). Worker's final-message summary IS the first place the summary appears in all three — not emitted earlier-then-ignored.

### H3 — "β-fuse contract doesn't specify a turn budget to the worker." — **CONFIRMED (primary)**

Verified by reading (a) `HERMES-variantF.md` (parent-only contract, no turn budget mentioned, specifies *classification* contract only); (b) `delegate_worker_v2.py:139-148` (passes `max_iterations=None`, no inline turn instruction in the dispatched `goal`); (c) the child session's `.system_prompt` is the generic Hermes Agent prompt with a "Keep working until the task is actually complete" directive and no turn cap; (d) `delegate_tool.DEFAULT_MAX_ITERATIONS = 50`. The rubric's 20-turn cap was invented on the judge side post-hoc; the worker was never told.

### H4 — "MoE MLX runs hotter than dense." — **UNTESTABLE on this data**

`ARTIFACT-r7.4-phase-d-dense-results.md` records elapsed seconds (T4-dense 146-417s; MoE T4 30-66s — MoE is **faster** wall-clock) but does NOT record assistant-turn counts. No turn-level dense calibration exists. Comparing r7.6 Arm A MoE T4 turn counts (12, 16, 16, 16, 32) to dense would require re-running dense with turn instrumentation. On wall-clock evidence alone, MoE is not "hotter"; if anything it's faster per turn. DISPROVEN on the specific "MoE goes 2× dense in turns" claim only because the dense-side number doesn't exist; the more plausible read is that both would fail the 20-turn cap under the current dispatch configuration.

### H5 — "20-turn cap is mis-calibrated." — **PARTIAL**

Strongly applies to T5 / T6 / T10 (genuine multi-file investigations or long-horizon plans legitimately need 25–30+ turns of orient+read). Weakly applies to T4, where a writable environment would plausibly finish in ≤20 turns but a read-only blocked environment takes ~12 and then idles. The cap was set without calibration data (the task set itself, in `probe-tasks.md`, was designed for a *write-capable* parent-session harness, not a read-only delegated child). This is a real problem but it is not the primary root cause — fixing it alone would still leave the loop-detection FAILs (trials 4, 13, 17, 18, 19) firing.

---

## 4. Recommended minimum change

The minimum change that stops the cascade is **H3 remediation: tell the worker about the turn budget via the dispatched `goal`**. This is a one-file, ≤10-line change in the test harness, not a protocol rewrite.

**Preferred fix — judge-visible, harness-scoped:**

Modify `/Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh` so that the initial task prompt (the `$TASK_TEXT` piped to hermes at line ~166) includes a turn-budget preamble, OR modify the probe's task set (`/Users/briantaylor/Projects/AgentFW/probe-tasks.md`) to append a budget constraint to each structured/long-horizon task:

```
BUDGET: Produce your final summary within 18 assistant turns. If the work
cannot be completed in that budget, stop early and report what you've done
with "BLOCKED:" plus concrete reasons.
```

This sits on the *task-input* side, is visible in the child goal, and does not require touching the β-fuse protocol, HERMES-variantF.md, delegate_worker_v2.py, or the judge rubric. It cleanly addresses H3 and secondarily H1 (worker now has an explicit stop condition).

**Secondary, complementary fixes (do not block the minimum change):**

1. **Task-toolset alignment** (addresses the H1-downstream loops): If T4/T5/T6/T10 are supposed to test the worker's ability to *do* multi-file refactors / bug-hunts / migrations, the probe wrapper should allow writers for those tasks. Current `TOOLSETS_ENV="delegation,todo,clarify,file_readonly"` is read-only. Add `file,terminal` (or a dedicated `file_write` toolset if Hermes has one) for write-requiring tasks. File: `/Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh:28`. Alternatively, if Arm A is meant to probe orient-only behavior, rewrite the T4/T5/T6/T10 prompts to frame them as "investigate and report" rather than "implement and verify" — that aligns task semantics with available tools.

2. **Rubric recalibration for long-horizon** (addresses H5): The judge's 20-turn cap is too strict for T6/T10 under read-only orientation. Split the cap by `TASK_CLASS_BY_TASK`: 20 for structured, 30 or 40 for long-horizon. File: `/tmp/probe-r7.6-P1C-logs/judge-trial.py` around line 397 — replace `if turns > 20` with a per-class lookup.

3. **Worker-side stop signal via system-prompt injection** (cleaner long-term than H3-only): Teach `delegate_worker_v2.py` to prepend a short preamble to the dispatched `goal` when the spawn is under a probe-restricted toolset, stating the assistant-turn budget. Or pass a `max_iterations` ≤ 20 via `delegate_worker_v2`'s invocation in the variantF contract. File: `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py:139-148`.

**Do the minimum change first** (prompt preamble in the task text or wrapper). Re-run Arm A. Expect WORKER_QUALITY to jump materially — most likely T4/T5 clear; T6/T10 may still fail unless (2) is also applied.

---

## 5. Falsifiability

The root-cause claim (H3 primary, with toolset-mismatch amplification) would be falsified by any of:

1. **Counter-evidence from Arm B:** If Arm B (which sets `HERMES_WORKER_OVERLAY=1`, presumably injecting additional instructions into the child) shows the same 30–50 turn counts, H3 is weakened — the additional overlay should, hypothetically, include budget guidance. (Check Arm B's `arm-B-outcomes.txt` once complete.)
2. **An existing budget instruction I missed:** If the generic Hermes Agent system prompt (or config.yaml for `delegation.max_iterations`) already contains a turn-budget statement and the worker is ignoring it, H3 is disproven and we're looking at H4-style model-failure-to-follow-instruction. Verified absent by reading `.system_prompt` on session JSONs and `delegate_tool.py`.
3. **Turn count independent of toolset:** If the same probe run with `TOOLSETS_ENV` including writers (e.g., `delegation,todo,file,terminal`) still averages >20 turns, then the toolset-mismatch half of my explanation is wrong; the model is genuinely verbose at the token-bound level and only rubric recalibration (H5) helps. Requires a new Arm to test.
4. **A single-turn budget instruction is ignored:** If injecting "Produce your final summary within 18 assistant turns" into T4/T5 goals does not reduce mean turn count, H3 is disproven. Fast test, cheap to run.

A crisper falsification: if we add **only** a 1-sentence "≤18 turns; stop with BLOCKED if you cannot finish" to each structured task prompt and re-run 5 trials of T4 under the current read-only toolset, we expect mean turns to drop from ~18 (current T4 mean: (16+32+12+16+16)/5 = 18.4) to ≤12. If that doesn't happen, the root-cause diagnosis is wrong.

---

## Appendix — per-trial turn counts and FAIL modes (Arm A, n=20)

| trial | task | turns | TE | FAIL mode |
|-------|------|-------|-------|------|
| 1  | T4  | 16 | PASS | — |
| 2  | T4  | 32 | FAIL | turn count > 20 (cap) |
| 3  | T4  | 12 | PASS | — |
| 4  | T4  | 16 | FAIL | 4+ consecutive near-identical search_files (loop) |
| 5  | T4  | 16 | PASS | — |
| 6  | T5  | 31 | FAIL | turn count > 20 (cap) |
| 7  | T5  | 13 | PASS | — |
| 8  | T5  | 29 | FAIL | turn count > 20 (cap) |
| 9  | T5  | 7  | PASS | — |
| 10 | T5  | 41 | FAIL | turn count > 20 (cap) |
| 11 | T6  | 20 | PASS | — (boundary) |
| 12 | T6  | 15 | PASS | — |
| 13 | T6  | 13 | FAIL | 4+ consecutive near-identical search_files (loop) |
| 14 | T6  | 23 | FAIL | turn count > 20 (cap) |
| 15 | T6  | 43 | FAIL | turn count > 20 (cap) |
| 16 | T10 | 50 | FAIL | turn count > 20 (cap); hit child's 50-iter hard cap |
| 17 | T10 | 13 | FAIL | 3+ consecutive near-identical search_files (loop) |
| 18 | T10 | 13 | FAIL | 4+ consecutive near-identical search_files (loop) |
| 19 | T10 | 11 | FAIL | last 5 tool calls all `todo` on 1 path (loop) |
| 20 | T10 | 4  | PASS | — (but COMPLETION/CORRECTNESS fail for other reasons: child terminated mid-tool) |

Breakdown of 14 TE=FAIL trials: 9 by cap-exceed, 5 by loop-detect. Loop-detect alone would leave ~6 structural failures independent of the cap — evidence that the worker is structurally prone to loops even well under 20 turns, which supports the toolset-mismatch half of the root cause.

---

## Appendix — pointers

- Probe logs: `/tmp/probe-r7.6-P1C-logs/`
- Judge code: `/tmp/probe-r7.6-P1C-logs/judge-trial.py` (turn-efficiency: lines 389–449)
- Wrapper (parent-side): `/Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh` (toolset at line 28; dispatch at lines 166, 235)
- β-fuse parent contract: `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md`
- β-fuse handler: `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py`
- Hermes delegate internals (VM): `~/.hermes/hermes-agent/tools/delegate_tool.py` (default toolsets: line 40; max iterations: line 39)
- Sample child sessions (VM): `/home/parallels/.hermes/sessions/session_{20260419_202137_75f15d,20260419_202426_0e3f50,20260419_204642_91923a}.json`
- Dense comparison: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-phase-d-dense-results.md` (no turn-level data recorded)
