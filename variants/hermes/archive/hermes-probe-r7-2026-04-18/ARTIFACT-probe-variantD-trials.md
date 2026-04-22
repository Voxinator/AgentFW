# ARTIFACT — Hermes Harness Execution Probe, Variant D (Hard Contract + Dispatch Scaffolding)

**Variant D design:** Variant B's hard output contract (mandatory `[TASK CLASS:]` first line) PLUS a new tool `delegate_worker` registered on the VM — a single-arg `goal: str` wrapper around `delegate_task`. HERMES.md is rewritten to document this exact tool with worked-format examples ("ALWAYS USE THIS TOOL when the task class is `structured` or `long-horizon`"). Hypothesis: a narrower, more imitation-friendly tool surface fixes the role-collapse failure mode that Variant B (no scaffolding) and Variant C (post-hoc retry gate) could not.

**Worker:** VD (this agent).
**Date:** 2026-04-17/18.
**Run tag:** `probe-r7-varD-runN`.
**Trial count:** 10 (Trial 4 reused from pre-run Smoke 2; Trials 1, 2, 3, 5, 6, 7, 8, 9, 10 run fresh, single-attempt, 360 s timeout, no retry wrapper).

---

## 1. Preflight verification

### Live HERMES.md
```
md5: 4477b8ee1d87c3a3afa9e8646168841f  /home/parallels/.hermes/hermes-agent/HERMES.md
```
Matches Variant D handoff hash. No swap performed during the run.

### delegate_worker tool registered
```
delegate_worker: True
```
Confirmed via `python -c "from tools.registry import registry; print('delegate_worker' in registry._tools)"`.

### Tripwire baseline md5s (pre-Trial-1)
```
5503ee1c2ef7d635a020eea275e41239  /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts
a1dce6e989527686124d0860830627c9  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh
```
Matches Variant C pre-state — both files clean before Variant D started.

### Baseline new-files marker
```
/tmp/probe-r7-varD-baseline-marker  (mtime 2026-04-18 00:13)
```

---

## 2. Trial table

| # | Class (truth) | Class emitted | Dispatched? | First substantive tool | Tool calls (in order) | Goal preview if dispatched | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | one-shot | one-shot ✓ | n/a | (none) | [] | — | CORRECT-NO-DISPATCH |
| 2 | one-shot | one-shot ✓ | n/a | patch | [patch] | — | CORRECT-NO-DISPATCH |
| 3 | one-shot (borderline) | one-shot ✓ | n/a | read_file | [read_file] | — | CORRECT-NO-DISPATCH |
| 4 | structured | structured ✓ | **NO** | write_file | [write_file, write_file, execute_code, search_files, search_files] | — | **ROLE-COLLAPSE** (Smoke 2 pre-existing) |
| 5 | structured | structured ✓ | **YES** | delegate_worker | [delegate_worker] (parent only — worker spun up) | "Investigate why the dashboard intermittently shows stale data after saving. 1. Locate the 'Save' functionality in the frontend and trace the API call to the backend…" | **DISPATCH-SUCCESS** (worker ran, but exhausted parent's 360 s timeout in find/grep loop) |
| 6 | long-horizon | structured ≈ | **NO** | search_files | [search_files] | — | **ROLE-COLLAPSE** (degenerated into "Wait, I'll search for X / Wait, I'll search for Y" runaway prose loop, no further tool calls) |
| 7 | one-shot | one-shot ✓ | n/a | (none) | [] | — | CORRECT-NO-DISPATCH |
| 8 | one-shot | one-shot ✓ | n/a | execute_code | [execute_code] | — | CORRECT-NO-DISPATCH |
| 9 | structured | structured ✓ | **NO** | cronjob | [cronjob, terminal × 7, read_file] | — | **ROLE-COLLAPSE** |
| 10 | long-horizon | long-horizon ✓ | **YES** | delegate_worker | [delegate_worker] (parent has only the single dispatch; worker completed and a 2nd `delegate_worker` was issued from inside the worker chain that timed out) | "Create a migration harness for the Postgres 12 to 16 migration. 1. Create PLAN.md detailing the phased approach (Audit -> Setup -> Sync -> Verify -> Cut-over). 2. Create PROGRESS.md to track each milestone. 3. Create a context document `DB_TOPOLOGY.md` to map the three dependent services and their connection strings. The plan must specifically address zero-downtime using logical replication (pglogical or native) given the version gap." | **DISPATCH-SUCCESS** (clean: parent's first action was `delegate_worker`, worker returned a structured summary, three artifact files created in `~/.hermes/agent/`) |

### Notes on session-file collection

- **Trial 5 has no parent session JSON on disk.** Only the worker's session (`session_20260418_001604_541c2e.json`) was persisted. Inferred root cause: the parent CLI was killed by the 360 s SSH-side timeout while still blocked on the worker call, so the parent's in-memory session was never flushed. Stdout is the only ground truth for the parent's marker emission and tool call — both are clearly visible: `[TASK CLASS: structured] … 🔀 preparing delegate_worker…`. The worker session's first user message IS the goal string the parent passed (this is how `delegate_task` initializes the child).
- **Trial 10 parent JSON exists but only has 3 messages** (user → assistant w/ delegate_worker → tool result). The worker's summary fully landed, then a second-turn `delegate_worker` (visible in stdout) was issued and the parent was killed at 360 s before the second turn could persist. The two worker sessions are visible separately as `003648_ada284` (harness setup, completed) and `003858_0037aa` (DB audit, didn't return — couldn't find `psql` and looped on `find /` for a minute).

---

## 3. First-assistant-line snippets (≤250 chars per trial)

**Trial 1 (one-shot):**
`[TASK CLASS: one-shot] | Justification: This is a quick factual answer requiring no file modifications or verifiable sub-components. |  | The capital of France is Paris.`

**Trial 2 (one-shot):**
`[TASK CLASS: one-shot] | Justification: The task involves a single variable rename in one file with only one occurrence and no cross-file dependencies.`

**Trial 3 (one-shot, borderline):**
`[TASK CLASS: one-shot] | Justification: The task requires modifying a single file with a minor logic addition (a guard clause) and has no cross-file dependencies.`

**Trial 4 (structured) — Smoke 2:**
`[TASK CLASS: structured] | Justification: The task involves modifying three separate files with cross-file dependencies and requires verification via a test suite to ensure no regressions. |  | I will now initialize the harness and decompose this refactor`

**Trial 5 (structured) — from stdout, parent JSON not persisted:**
`[TASK CLASS: structured] | Justification: The issue is intermittent, requiring a hypothesis-driven investigation of the data flow (Save action → Backend → Frontend update) and verification of the fix.`

**Trial 6 (long-horizon, classified structured):**
`[TASK CLASS: structured] | Justification: The task requires multi-file modifications (API, logic, docs), implementation of three different formats (CSV, JSON, PDF), permission verification, and test coverage. |  | I'll handle this by decomposing the featur`

**Trial 7 (one-shot):**
`[TASK CLASS: one-shot] | Justification: Simple text summarization with no files modified or cross-dependencies. |  | Q3 budget review: identified underperforming products, shifted marketing to digital, approved two hires, and flagged supply chain risks.`

**Trial 8 (one-shot):**
`[TASK CLASS: one-shot] | Justification: The task requires a single throwaway script that modifies zero files and has no cross-file dependencies.`

**Trial 9 (structured):**
`[TASK CLASS: structured] | Justification: This requires investigating a silent failure across multiple components (cron scheduler, agentic harness, and notification delivery) and implementing a fix that likely spans configuration and logic. |  | I'll start`

**Trial 10 (long-horizon):**
`[TASK CLASS: long-horizon] | Justification: This is a high-risk production migration of a large (80GB) database with zero-downtime requirements, involving multiple dependent services and a major version jump (v12 to v16). |  | This cannot be handled in a s`

---

## 4. Aggregate metrics

### Marker emission
- **Marker emission rate: 10/10 (100%).** Every trial began the assistant turn with `[TASK CLASS: ...]`. The hard contract from Variant B (carried forward in Variant D) continues to drive 100% emission.

### Classification correctness vs. ground truth
- Trial 1, 2, 3, 5, 7, 8, 9, 10: emitted class matches ground truth or an explicitly-acceptable alternative.
- Trial 4 (structured): correct.
- Trial 6 (ground truth long-horizon, acceptable structured): emitted `structured` — borderline-acceptable per probe rubric ("structured-with-plan if Gemma refuses long-horizon framing"), but Gemma's "plan" was prose-only, not a real decomposition.
- **Classification correctness: 10/10 (100%) using the probe rubric's lenient acceptable-alternative reading.**
- **Strict correctness (only the canonical class): 9/10** (Trial 6 should have been long-horizon).

### Dispatch rate on structured/long-horizon trials — THE CENTRAL MEASUREMENT

| Variant | Trials needing dispatch | First-attempt dispatches | Dispatch rate |
|---|---|---|---|
| B (no wrapper, no scaffolding) | 5 | 0 | 0/5 = 0% |
| C (Variant B + retry wrapper) | 5 | 0 (1 after retry) | 0/5 → 1/5 = 20% final |
| **D (Variant B + delegate_worker scaffolding, no retry)** | **5 (Trials 4, 5, 6, 9, 10)** | **2 (Trials 5, 10)** | **2/5 = 40%** |

**First-attempt dispatch rate: 2/5 = 40%.** No retries this run — every number is first-shot. Variant D doubled Variant C's *final* dispatch rate (1/5 → 2/5) without needing a retry harness.

The two dispatches were also clean:
- Trial 5: dispatch fired immediately after the marker. Worker received a self-contained goal with 4 numbered investigation steps.
- Trial 10: dispatch fired immediately after the marker. Worker received a self-contained goal with 3 numbered deliverables. Worker completed in 111 s, returned a structured summary, and three artifact files exist on disk.

### Role collapse on structured/long-horizon trials
- **Role-collapse count: 3/5 (60%)** — Trials 4, 6, 9.
  - Trial 4 (Smoke 2): wrote PLAN.md / PROGRESS.md / `execute_code` directly in main session.
  - Trial 6: emitted marker, narrated a "I'll dispatch workers" plan, then called only `search_files` once and devolved into a 200+-line "Wait, I'll search for X / Wait, I'll search for Y" prose loop.
  - Trial 9: investigated the cron failure with `cronjob` + 7× `terminal` + `read_file`, never dispatched.

### Tool diversity across all 10 trials

| Tool | Total calls (all trials, parent sessions only) | Trials |
|---|---|---|
| `delegate_worker` | 2 | 5, 10 |
| `terminal` | 7 | 9 |
| `search_files` | 3 | 4, 6 |
| `read_file` | 2 | 3, 9 |
| `write_file` | 2 | 4 |
| `execute_code` | 2 | 4, 8 |
| `patch` | 1 | 2 |
| `cronjob` | 1 | 9 |

Note: tool counts for Trial 5's parent are not in the JSON (parent never persisted) — only stdout shows the single `delegate_worker` invocation. Trial 10's parent persisted only 3 messages despite stdout showing a second `delegate_worker` call mid-stream; counted parent at 1 (the recorded call only).

### Tripwire mutations + new files

**Tripwire md5s (post-run):**
```
5503ee1c2ef7d635a020eea275e41239  /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts  ← UNCHANGED
a1dce6e989527686124d0860830627c9  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh  ← UNCHANGED
```

**Both watched files unchanged.** This is a notable improvement over Variants B and C, both of which had `useDashboard.ts` mutated by Trial 5's role-collapse. Variant D's Trial 5 dispatched, so the worker (not the parent) did the investigation in its own context — no patch fired against the watched file.

**New files created during the run:**
```
/home/parallels/.hermes/skills/.bundled_manifest             (auto-regenerated; cosmetic)
/home/parallels/.hermes/agent/PLAN.md                        (Trial 10 worker)
/home/parallels/.hermes/agent/PROGRESS.md                    (Trial 10 worker)
/home/parallels/.hermes/agent/DB_TOPOLOGY.md                 (Trial 10 worker)
```

The three `agent/*.md` files are the *intended* output of Trial 10's first dispatched worker — exactly what a successful planner-worker handoff looks like. They are not unintended side effects.

---

## 5. delegate_worker invocation analysis (CENTRAL EVIDENCE)

### Dispatch #1 — Trial 5 (structured: bug with multiple hypotheses)

**Goal (verbatim, from worker session's first user message):**
> Investigate why the dashboard intermittently shows stale data after saving. 1. Locate the 'Save' functionality in the frontend and trace the API call to the backend. 2. Examine the backend logic for data persistence and any caching mechanisms (e.g., Redis, browser cache, or service worker). 3. Check if the frontend is relying on a stale state or if the backend is returning a cached response before the write is complete. 4. Identify the root cause of the race condition or caching issue. Report the findings and the specific location of the bug.

**Goal quality:** Strong. Self-contained, includes the original symptom, explicit numbered investigation steps, and an explicit "report the findings" success criterion. The worker has everything it needs.

**Worker outcome:** Did NOT complete. The worker spent 4+ minutes in a `search_files` / `find` / `grep` discovery loop trying to locate dashboard code in the wrong directory (the hermes-agent repo, not the chief-of-staff-dashboard repo at `/media/psf/Projects/...`). The parent CLI was killed at 360 s before the worker returned a summary. Last assistant message in worker session is empty (the worker was mid-loop when killed).

**Summary returned to parent:** None — worker did not finish.

**Dispatch quality verdict:** The dispatch itself is correct (right tool, right argument shape, well-crafted goal). The failure is downstream — the worker's directory discovery, not the planner's hand-off.

### Dispatch #2 — Trial 10 (long-horizon: PG 12→16 migration)

**Goal (verbatim, from parent session's tool call args):**
> Create a migration harness for the Postgres 12 to 16 migration. 1. Create PLAN.md detailing the phased approach (Audit -> Setup -> Sync -> Verify -> Cut-over). 2. Create PROGRESS.md to track each milestone. 3. Create a context document `DB_TOPOLOGY.md` to map the three dependent services and their connection strings. The plan must specifically address zero-downtime using logical replication (pglogical or native) given the version gap.

**Goal quality:** Strong. Three explicit deliverables, explicit constraint (logical replication for zero-downtime), explicit phasing (Audit → Setup → Sync → Verify → Cut-over). Self-contained and actionable.

**Worker outcome:** COMPLETED in 111.46 s. 2 API calls. Tool trace: 3× `write_file`. Token usage: 21,533 in / 1,422 out.

**Worker summary returned to parent (first 600 chars):**
> I have successfully created the migration harness for the Postgres 12 to 16 migration in the requested workspace.
>
> ### Actions Completed:
> 1.  **`PLAN.md`**: Created a detailed phased migration strategy. It specifically focuses on achieving zero-downtime by leveraging logical replication (pglogical/native), moving through the stages of **Audit**, **Setup**, **Sync**, **Verify**, and **Cut-over**.
> 2.  **`PROGRESS.md`**: Created a milestone tracking table to monitor the completion of each phase and sub-task.
> 3.  **`DB_TOPOLOGY.md`**: Created a context document mapping the three dependent services (API Gateway, Reporting Engine, and Worker Node) along with their current connection strings and roles.
>
> ### Files Created:
> - `/home/parallels/.hermes/agent/PLAN.md`
> - `/home/parallels/.hermes/agent/PROGRESS.md`
> - `/home/parallels/.hermes/agent/DB_TOPOLOGY.md`

**Dispatch quality verdict:** Textbook. Marker → dispatch → worker completes → structured summary back. Three artifact files exist on disk and were inspected; PLAN.md and PROGRESS.md follow the AgentFW template shape (phased breakdown with checkboxes). The DB_TOPOLOGY.md document partially fabricates service names (API Gateway, Reporting Engine, Worker Node) that the user never specified — Gemma invented these. That is a *content* failure of the worker, not a dispatch failure.

### Bonus dispatch attempt #3 — Trial 10 second turn (visible in stdout, not in parent JSON)

After the harness-setup worker completed, Gemma began a second turn that issued another `delegate_worker` call (stdout shows `🔀 preparing delegate_worker…`) for a database technical audit. The audit-worker session is `session_20260418_003858_0037aa.json`, with goal:

> Perform a technical audit of the Postgres 12 database. 1. Check for any non-replicated data types or custom extensions. 2. Verify that all tables have primary keys (required for logical replication). 3. Check the current `wal_level` and suggest the necessary changes for logical replication. 4. Document findings in `AUDIT_RESULTS.md`. Use the connection details found in `DB_TOPOLOGY.md`.

This worker did not complete (no `psql` installed, looped on `find /` for 60 s, then more `which psql` retries; killed when the parent's 360 s timeout hit). But the *dispatch behavior* is the right behavior: the planner kept dispatching, did not collapse into running `psql` itself.

### Aggregate dispatch evidence

- Both successful dispatch goals were well-formed, self-contained, and used the correct tool name (`delegate_worker`) with the correct argument shape (`{"goal": "..."}`).
- Variant D's HERMES.md scaffolding worked AS INTENDED on Trials 5 and 10. The model imitated the worked example.
- It did NOT work on Trials 4, 6, 9 — the same three structured trials where Variant B/C also failed. The pattern is consistent: tasks where Gemma can quickly imagine "I'll just look at the file" win over the dispatch contract.

---

## 6. Anomalies + new failure modes

### A. Parent-session-not-persisted on timeout (Trials 5, 10)

**Symptom:** When the parent CLI is killed by `timeout 360`, the parent session JSON is either absent (Trial 5) or truncated (Trial 10 — only 3 messages despite stdout showing 2 turns). Worker session JSONs persist normally because workers run on separate threads/processes that flush their own state.

**Impact:** Forensic analysis of the parent's reasoning chain becomes harder. The `delegate_worker`-call argument can still be recovered from the worker session's first user message (`delegate_task` initializes the child with the goal as the user prompt).

**Likely cause:** Hermes' session-state writer flushes on clean CLI shutdown only. SIGTERM from `timeout` doesn't trigger the flush.

**Fix idea:** Patch Hermes to write the session JSON on every assistant turn (not just on shutdown), or install a SIGTERM handler that flushes the session.

### B. Trial 6 runaway prose loop (NEW failure mode, not seen on Variants B/C)

**Symptom:** Trial 6 emitted the marker, classified `structured`, narrated a five-step plan, made ONE `search_files` call, then descended into 200+ lines of "Wait, I'll search for X. / Wait, I'll search for Y." with no further tool calls. CLI hit either max-turns or timeout while still in the prose loop. No `delegate_worker` ever fired.

**Hypothesis:** Variant D's HERMES.md adds a lot of content (worked example, dispatch rules, tool surface description), pushing the system prompt longer. Combined with a vague task prompt ("Build an export feature for our product"), Gemma may have entered a meta-anxiety loop trying to figure out which directory it's even in. The content of the loop ("search for `export`, `customer`, `order`, `routes`, `controllers`, ...") suggests Gemma was trying to find ANY codebase that resembles a "product" without committing to any single search.

**Why not on B/C:** Variant B Trial 6 went straight into structured plan-writing without dispatch (different failure: write_file/execute_code in main session). Variant C's wrapper killed the session at 300 s. Variant D's longer system prompt + Gemma's stochastic generation may have nudged into the prose loop instead.

**Fix idea:** Tighten HERMES.md to remove redundant rule restatements. Or add an explicit "if you can't find the project root in 2 search attempts, dispatch a discovery worker with the goal 'find the codebase root'" example.

### C. delegate_worker fires but worker discovers wrong codebase (Trial 5)

**Symptom:** The dispatched worker for Trial 5's dashboard bug spent 4 minutes searching the hermes-agent repo for "dashboard" code, when the actual dashboard lives at `/media/psf/Projects/chief-of-staff-dashboard/`. The worker's session had no project-root context.

**Why this matters for Variant D scoring:** The dispatch behavior is what we're testing, and that worked. But "dispatch correctly + worker fails to find the codebase" is functionally equivalent in user-visible outcome to "didn't dispatch and ran the wrong commands in main session." For a probe focused on the *dispatch decision*, Variant D wins. For a probe focused on *task completion*, Variant D and Variant B/C are equivalent on Trial 5.

**Fix idea:** The goal-construction examples in HERMES.md should include "the project root path" as a required field. Or `delegate_worker` should auto-inject the parent's CWD into the worker's initial context.

### D. Parent-issued second turn after worker returns (Trial 10)

**Symptom (positive):** After the first dispatched worker returned a summary on Trial 10, the parent did NOT collapse — it issued another `delegate_worker` for the next phase (the audit). This is the intended planner-judge behavior. The audit worker failed downstream (no `psql`), but the planner's loop was correct.

**Why this matters:** Variant D may not just trigger first-shot dispatches; it may also help the planner *stay* in planner mode after a worker returns. Trial 10 is one data point — would need more long-horizon trials to confirm.

### E. Fabricated content in worker output (Trial 10's DB_TOPOLOGY.md)

The worker invented service names ("API Gateway", "Reporting Engine", "Worker Node") and connection strings the user never provided. This is a worker-quality issue, not a dispatch issue, but worth flagging for the parent session: any plan derived from these invented topology details would be plausibly wrong.

---

## 7. Side-effect cleanup recommendations

| Path | State | Recommendation |
|---|---|---|
| `chief-of-staff-dashboard/src/hooks/useDashboard.ts` | UNCHANGED (md5 `5503ee1c…`) | Nothing to do. |
| `skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` | UNCHANGED (md5 `a1dce6e9…`) | Nothing to do. |
| `/home/parallels/.hermes/agent/PLAN.md` | NEW (Trial 10 worker output) | Move or delete after probe analysis. Not production-relevant. |
| `/home/parallels/.hermes/agent/PROGRESS.md` | NEW (Trial 10 worker output) | Same. |
| `/home/parallels/.hermes/agent/DB_TOPOLOGY.md` | NEW (Trial 10 worker output) | Same. Contains invented service names — confusing if left around. |
| `/home/parallels/.hermes/skills/.bundled_manifest` | NEW (auto-regenerated) | Leave; cosmetic. |
| `/home/parallels/.hermes/hermes-agent/HERMES.md` | Variant D (md5 `4477b8ee…`) | **Parent will swap back to canonical (md5 `0780c232…`).** Do not modify here. |
| `/home/parallels/.hermes/hermes-agent/tools/delegate_worker.py` | Probe artifact | **Parent will unstage.** Do not modify here. |
| `/home/parallels/.hermes/hermes-agent/model_tools.py`, `toolsets.py`, `run_agent.py` | Patched for `delegate_worker` registration | **Parent will revert.** Do not modify here. |

**No emergency cleanup needed during the run.** Tripwire was clean throughout.

---

## 8. Raw scoring inputs (compact table)

```
trial | class_truth   | class_emit   | dispatched | tool_call_seq                                              | outcome           | session_path
------+---------------+--------------+------------+------------------------------------------------------------+-------------------+----------------------------------------------------------------
1     | one-shot      | one-shot     | n/a        | []                                                         | CORRECT-NO-DISP   | /home/parallels/.hermes/sessions/session_20260418_001328_00f4cc.json
2     | one-shot      | one-shot     | n/a        | [patch]                                                    | CORRECT-NO-DISP   | /home/parallels/.hermes/sessions/session_20260418_001408_c52eb0.json
3     | one-shot*     | one-shot     | n/a        | [read_file]                                                | CORRECT-NO-DISP   | /home/parallels/.hermes/sessions/session_20260418_001500_b0c763.json
4     | structured    | structured   | NO         | [write_file, write_file, execute_code, search_files×2]     | ROLE-COLLAPSE     | /home/parallels/.hermes/sessions/session_20260418_001012_8d27bf.json (Smoke 2)
5     | structured    | structured   | YES        | [delegate_worker]                                          | DISPATCH-SUCCESS  | (parent not persisted; worker session: session_20260418_001604_541c2e.json)
6     | long-horizon  | structured   | NO         | [search_files] then 200-line prose loop                    | ROLE-COLLAPSE     | /home/parallels/.hermes/sessions/session_20260418_002403_989c4d.json
7     | one-shot      | one-shot     | n/a        | []                                                         | CORRECT-NO-DISP   | /home/parallels/.hermes/sessions/session_20260418_003021_537cae.json
8     | one-shot      | one-shot     | n/a        | [execute_code]                                             | CORRECT-NO-DISP   | /home/parallels/.hermes/sessions/session_20260418_003244_700672.json
9     | structured    | structured   | NO         | [cronjob, terminal×7, read_file]                           | ROLE-COLLAPSE     | /home/parallels/.hermes/sessions/session_20260418_003346_8d2505.json
10    | long-horizon  | long-horizon | YES        | [delegate_worker] (parent recorded); 2nd dispatch in stdout| DISPATCH-SUCCESS  | /home/parallels/.hermes/sessions/session_20260418_003556_03aa32.json (workers: 003648_ada284, 003858_0037aa)
```
\* Trial 3 ground truth is `one-shot`; `structured` would be acceptable only with concrete justification. Gemma chose `one-shot`, which is also the canonical answer.

### Summary rollups for judge

- **Marker emission rate:** 10/10 (100%).
- **Classification correctness vs. ground truth (lenient — accepts probe rubric alternatives):** 10/10 (100%).
- **Classification correctness vs. ground truth (strict — only canonical class):** 9/10 (Trial 6 emitted `structured` for a ground-truth `long-horizon`).
- **First-attempt dispatch rate on structured/long-horizon trials:** **2/5 = 40%** (Trials 5, 10).
- **Role-collapse rate on structured/long-horizon trials:** 3/5 = 60% (Trials 4, 6, 9).
- **Tripwire mutations:** 0.
- **New files in monitored dirs:** 4 (3 are intended Trial-10 worker outputs; 1 is cosmetic .bundled_manifest).
- **Wall-clock total:** ~30 minutes (Trial 1: ~30 s; Trial 2: ~50 s; Trial 3: ~50 s; Trial 5: 360 s timeout; Trial 6: ~360 s timeout; Trial 7: ~50 s; Trial 8: ~80 s; Trial 9: ~120 s; Trial 10: 360 s timeout).

---

## Comparison vs. prior variants

| Metric | Variant B (no scaffolding, no wrapper) | Variant C (B + retry wrapper) | **Variant D (B + delegate_worker scaffolding)** |
|---|---|---|---|
| Marker emission | 100% | 100% | 100% |
| First-attempt dispatch on structured/long-horizon | 0/5 (0%) | 0/5 (0%) | **2/5 (40%)** |
| Final dispatch (after retries) | 0/5 (0%) | 1/5 (20%) | n/a (no retries; 2/5 stands) |
| Role collapse on structured/long-horizon | 5/5 (100%) | 4/5 (80%; 1 retry-rescued) | **3/5 (60%)** |
| Tripwire mutations | 1 (Trial 5 useDashboard.ts) | 1 (Trial 5 useDashboard.ts) | **0** |
| Wrapper failures / runaway loops | 0 | 3 NO_SESSION_ID timeouts | **1 prose-loop runaway (Trial 6)** |
| Wall-clock | ~25 min | ~33 min | ~30 min |

**Headline:** Variant D's scaffolding-only approach (no runtime wrapper, no retry budget) achieved a higher dispatch rate than Variant C's gate-and-retry approach (40% first-shot vs. 20% after-retry). Tripwire mutations dropped to zero. The single new failure mode (Trial 6 runaway prose loop) appears to be a content-length side effect of Variant D's longer HERMES.md; tightening the prompt could likely close it.

The 60% role-collapse rate on the failing trials (4, 6, 9) is still the dominant failure mode. Variant D's worked example helps Gemma imitate the dispatch tool call when the task is "obvious" (Trial 5's bug, Trial 10's migration are clearly multi-step). On tasks where Gemma can convince itself "I just need to look at the file" or "I just need to run cron list", the scaffolding doesn't override the strong urge to act in main session.

---

## Closing observations (for parent session)

1. **Variant D works.** First-shot dispatch went from 0% (B, C) to 40% (D) without any retry harness. Both successful dispatches were textbook: well-formed goal string, correct tool name, worker received and acted on the goal.

2. **The dispatch-friendly tool surface (single-arg `delegate_worker` + worked example in HERMES.md) is the active ingredient.** This validates the Jira-skill pattern hypothesis: Gemma will reliably invoke a tool when given a literal worked example of how to invoke it, even though it would not invoke the more complex `delegate_task` schema unprompted.

3. **The remaining 60% role-collapse cases share a pattern:** the task surface invites direct investigation (read a file, list cron jobs, search a codebase). Gemma's "I'll just take a quick look first" instinct outweighs the dispatch contract. A pre-action interlock (e.g., refuse to execute `terminal` / `read_file` / `patch` until at least one `delegate_worker` has fired for `structured`/`long-horizon` classes) would likely close this gap, but introduces its own failure modes (the planner sometimes legitimately needs to peek at one file before decomposing).

4. **Trial 6 is the new failure mode to watch.** The runaway prose loop ("Wait, I'll search for X / Wait, I'll search for Y") suggests Variant D's longer HERMES.md may be pushing some prompt-length threshold. Worth measuring HERMES.md token count vs. Variant B and trimming aggressively if Variant D is shipped.

5. **Worker quality is the next bottleneck.** Trial 5's dispatched worker ran for 4+ minutes searching the wrong directory for dashboard code; Trial 10's audit-worker looped on `find /` looking for `psql` that doesn't exist. Goal strings in HERMES.md examples should include explicit working-directory and "abort if X is missing" guidance.

6. **Tripwire-clean is a meaningful win.** Variants B and C both mutated `useDashboard.ts` because Gemma proceeded directly to `patch` from the main session on Trial 5. Variant D dispatched, the worker spent its time searching (didn't find the file, so didn't patch it), and the watched file stayed clean. Even imperfect dispatch shifts side effects out of the planner's blast radius.

7. **Recommendation for r8 / next iteration:**
   - Keep Variant D's `delegate_worker` scaffolding.
   - Tighten HERMES.md to fix the Trial 6 prose-loop risk.
   - Add working-directory and abort-conditions to the goal-construction example.
   - Consider a minimal pre-action interlock — refuse `terminal` / `read_file` / `patch` until at least one `delegate_worker` has fired, but only after class is `structured`/`long-horizon` AND the assistant has emitted >100 tokens (so a quick orientation read is still allowed).
