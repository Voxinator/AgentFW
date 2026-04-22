# ARTIFACT — Hermes Harness Execution Probe, Variant E (Variant D scaffolding + Variant C retry loop)

**Variant E design:** Variant D's tool surface (simpler `delegate_worker` + HERMES-variantD.md scaffolding) PLUS Variant C's runtime retry loop. Adds a `VIOLATION:ROLE_COLLAPSE:<class>` gate to the check script that catches main-session mutation tools (`patch`, `write_file`, `execute_code`, `skill_manage`) called BEFORE any dispatch. Hypothesis: the scaffolding fixes the quality of the dispatch when it happens, and the retry loop catches the cases where Gemma skips dispatch entirely.

**Worker:** VE (this agent).
**Date:** 2026-04-18.
**Run tag:** `probe-r7-varE-run<N>`.
**Trial count:** 10. Trial 4 reused from pre-run Smoke 2 (recorded as COMPLIANT on 4th attempt). Trials 1, 2, 3, 5, 6, 7, 8, 9, 10 run fresh.

---

## 1. Preflight verification

### Live HERMES.md
```
md5: 4477b8ee1d87c3a3afa9e8646168841f  /home/parallels/.hermes/hermes-agent/HERMES.md
```
Matches Variant D handoff hash. No swap performed during the run.

### delegate_worker tool registered
The naive registry check (`"delegate_worker" in registry._tools` at a fresh python prompt) reports `False` because `tools.delegate_worker` is not auto-imported; after `import tools.delegate_worker`, the module registers itself and `registry._tools` contains both `delegate_task` and `delegate_worker`. Hermes' normal startup path does this import via `model_tools.py`, so `delegate_worker` is available inside `hermes chat`. Confirmed by Trial 4/5/6/10 stdout emitting `🔀 preparing delegate_worker…`.

### Tripwire baseline md5s (pre-run)
```
5503ee1c2ef7d635a020eea275e41239  /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts
a1dce6e989527686124d0860830627c9  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh
```
Matches known-good post-revert md5s from Variant D wrap-up.

---

## 2. Trial table

Outcome categories:
- `COMPLIANT-FIRST` — A0 compliant, no retries needed
- `COMPLIANT-RESCUED` — required 1+ retries, ended COMPLIANT
- `RETRY_EXHAUSTED:<violation>` — 4 attempts, never reached COMPLIANT
- `WRAPPER_ERROR:NO_SESSION_ID` — inner `timeout 300` killed the hermes CLI before it could print `session_id:` to stdout. Parent session either absent or truncated on disk due to SIGTERM not flushing state. Runtime behavior is recoverable from stdout + worker sessions.

| # | Class (truth) | Attempts | Final outcome | Final session (parent) | First-attempt verdict | Chain (compact) | dw/dt counts (persisted) | Tool calls (first 8, persisted) |
|---|---|---|---|---|---|---|---|---|
| 1 | one-shot | 1 | COMPLIANT-FIRST | 20260418_012230_9db34c | COMPLIANT | `A0:rc=0 \| A0:COMPLIANT` | 0/0 | `[]` |
| 2 | one-shot | 1 | COMPLIANT-FIRST | 20260418_012308_48b3bc | COMPLIANT | `A0:rc=0 \| A0:COMPLIANT` | 0/0 | `[patch]` |
| 3 | one-shot* | 1 | COMPLIANT-FIRST | 20260418_012358_4834cf | COMPLIANT | `A0:rc=0 \| A0:COMPLIANT` | 0/0 | `[read_file, search_files, read_file, read_file, search_files]` |
| 4 | structured | 4 | COMPLIANT-RESCUED | 20260418_010641_d07074 (Smoke 2) | NO_DISPATCH | `A0:NO_DISPATCH \| A1_correct:rc=124 \| A1:NO_DISPATCH \| A2_correct:rc=124 \| A2:NO_DISPATCH \| A3_correct:rc=0 \| A3:COMPLIANT` | 1/0 | `[terminal, search_files, search_files, search_files, delegate_worker]` |
| 5 | structured | 1 | WRAPPER_ERROR:NO_SESSION_ID | 20260418_012437_fce8fb | (wrapper saw no session) | `A0:rc=124` | 0/0 persisted (but worker session 012749_58db0e exists → runtime dispatched) | `[terminal, search_files, search_files, read_file, search_files×5, read_file, read_file]` |
| 6 | long-horizon | 1 | WRAPPER_ERROR:NO_SESSION_ID | 20260418_013007_190a6c | (wrapper saw no session) | `A0:rc=124` | 0/0 persisted (but worker session 013316_a36728 exists → runtime dispatched) | `[terminal, search_files, todo, search_files, read_file, read_file]` |
| 7 | one-shot | 1 | COMPLIANT-FIRST | 20260418_013515_8d93b1 | COMPLIANT | `A0:rc=0 \| A0:COMPLIANT` | 0/0 | `[]` |
| 8 | one-shot | 1 | COMPLIANT-FIRST | 20260418_013607_c00d05 | COMPLIANT | `A0:rc=0 \| A0:COMPLIANT` | 0/0 | `[execute_code]` |
| 9 | structured | 4 | RETRY_EXHAUSTED:NO_DISPATCH | 20260418_013709_8c521e | NO_DISPATCH | `A0:NO_DISPATCH \| A1..A3 all NO_DISPATCH` | 0/0 | `[cronjob, skill_view, terminal, read_file, terminal, terminal, terminal]` |
| 10 | long-horizon | 1 | WRAPPER_ERROR:NO_SESSION_ID | parent not persisted | (wrapper saw no session) | `A0:rc=124` | n/a persisted (worker session 014050_509ee2 exists → runtime dispatched) | n/a (parent not on disk) |

\* Trial 3 ground truth is `one-shot`; borderline-acceptable structured with concrete justification. Gemma chose canonical `one-shot`.

### Persisted-session compliance (check.py verdicts)
```
trial 1: COMPLIANT
trial 2: COMPLIANT
trial 3: COMPLIANT
trial 4: COMPLIANT (final attempt after smoke-test retries)
trial 5: VIOLATION:NO_DISPATCH:structured (parent truncated before dispatch persisted)
trial 6: VIOLATION:NO_DISPATCH:structured (parent truncated before dispatch persisted)
trial 7: COMPLIANT
trial 8: COMPLIANT
trial 9: VIOLATION:NO_DISPATCH:structured (retry exhausted — Gemma reclassified to one-shot after investigation, but first-line marker never changed)
trial 10: parent not on disk (complete truncation)
```

### Notes on session-file collection

- **Trial 5, 6, 10 WRAPPER_ERROR root cause:** identical to Variant D's Finding A. The inner `timeout 300` SIGTERMs the hermes CLI while it is mid-delegation (the `delegate_worker` tool call is expensive — it spins up a child agent that runs for 60–120 s). The parent's session-JSON writer only flushes on clean CLI shutdown, so the `delegate_worker` tool call never lands on disk, even though the stdout `🔀 preparing delegate_worker…` confirms the call fired at runtime. Worker sessions persist because workers run in their own process and flush independently.
- **Parent-session-truncation hides Variant E's true dispatch rate.** Persisted parent sessions for Trials 5, 6, 10 show NO_DISPATCH — but all three have matching worker sessions whose first-user message is the dispatched goal string. Thus the true runtime dispatch rate is higher than the persisted-session measurement shows. See §5 for per-trial evidence.
- **Trial 6 is a notable departure from Variant D.** Variant D's Trial 6 collapsed into a 200-line "Wait, I'll search for X" prose loop and never dispatched. Variant E's Trial 6 reaches the dispatch call within the 300 s budget. The prose-loop failure mode appears to have resolved, possibly because Variant E's test is identical prompt but the stochastic path landed differently.

---

## 3. First-assistant-line snippets per trial (≤350 chars each)

**Trial 1 (one-shot):**
`[TASK CLASS: one-shot] | Justification: This is a quick factual answer requiring zero file modifications. | The capital of France is Paris.`

**Trial 2 (one-shot):**
`[TASK CLASS: one-shot] | Justification: The task involves a single variable rename in one file with only one occurrence and no cross-file dependencies.`

**Trial 3 (one-shot):**
`[TASK CLASS: one-shot] | Justification: The change is limited to a single file and a small number of lines (a simple guard clause) with no cross-file dependencies.`

**Trial 4 (structured, Smoke 2):**
`[TASK CLASS: structured] | Justification: The task requires modifying three separate files and necessitates a verification step (running tests) to ensure no regressions. | I will now orient myself by inspecting the current implementation of the auth module and the new session store.`

**Trial 5 (structured):**
`[TASK CLASS: structured] | Justification: The task involves debugging an intermittent race condition or caching issue across multiple files (frontend state vs. backend persistence) and requires a separate verification step to ensure the fix is robust. | I'll start by investigating the current data flow between the Save action and the dashboard refresh`

**Trial 6 (long-horizon, classified structured):**
`[TASK CLASS: structured] | Justification: The task requires modifying multiple files (API, logic, docs), implementing security constraints (permissions), and adding a test suite. | I'll handle this using the Planner-Worker-Judge architecture. I need to first understand the existing data models and API structure before I can design the export logic.`

**Trial 7 (one-shot):**
`[TASK CLASS: one-shot] | Justification: The task is a simple text summarization with no file modifications or complex dependencies. | Budget reviews led to shifting marketing spend to digital, hiring for infrastructure scalability, and flagging APAC supply chain risks.`

**Trial 8 (one-shot):**
`[TASK CLASS: one-shot] | Justification: The task requires a single-file throwaway script with no cross-file dependencies or complex verification.`

**Trial 9 (structured):**
`[TASK CLASS: structured] | Justification: This requires investigating multiple hypotheses (cron logs, script errors, network issues) and involves modifying system-level configurations or scripts. | I'll start by identifying the specific cron job and inspecting its logs to find the point of failure.`

**Trial 10 (long-horizon, from stdout — parent JSON not persisted):**
`[TASK CLASS: long-horizon] | Justification: This is a high-risk infrastructure migration involving a production database (80GB) with zero-downtime requirements, multiple dependent services, and a multi-version jump (v12 to v16) requiring phased execution and verification. | Wait, Brian. This is a massive operation. Moving from Postgres 12 to 16 isn't just a version bump; it's a multi-year leap…`

All ten trials emitted the marker — **10/10 emission rate**.

---

## 4. delegate_worker invocation analysis

### Dispatch #1 — Trial 4 (structured: auth refactor) [SMOKE 2, rescued on A3]

- **Attempt#:** A3 (after 3 NO_DISPATCH violations). Dispatch fired only after correction message.
- **Persisted tool sequence (pre-dispatch):** `[terminal, search_files, search_files, search_files, delegate_worker]`. No mutation-class tool (`patch`/`write_file`/`execute_code`/`skill_manage`) appeared before dispatch, so check.py ruled COMPLIANT rather than ROLE_COLLAPSE.
- **Goal (verbatim):**
  > Refactor the auth module to use the new session store. Modify the following files: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. Ensure that the implementation is correctly integrated and that all existing tests in tests/auth.test.ts pass after the refactor. Done is defined as: all three files updated and a successful run of the test suite with no regressions.
- **Worker outcome:** Did not find the files (they don't exist in the VM; probe task didn't require them to). Final parent text: "the worker was unable to find the source files in the environment."
- **Goal quality:** Strong — names all three files, states "done" criterion.

### Dispatch #2 — Trial 5 (structured: intermittent stale-dashboard bug) [runtime only, parent truncated]

- **Attempt#:** A0 (first-shot at runtime). Parent session does NOT record the delegate_worker call (SIGTERM truncation), but stdout shows `🔀 preparing delegate_worker…` and the child session `20260418_012749_58db0e` exists with a matching goal string.
- **Goal (verbatim from worker's first-user message):**
  > Investigate the data flow in `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts` and `/media/psf/Projects/chief-of-staff-dashboard/src/components/tasks/TaskDetailPanel.tsx`. Specifically, analyze the `editTask` function and how it handles optimistic updates. Determine if the intermittent stale data issue is caused by race conditions during rapid updates (like the debounced not[es save])…
- **Worker outcome:** Not verified (child also likely killed by parent's SIGTERM cascade — no parent return to check).
- **Goal quality:** Strong — names specific files, names specific function, ties to original symptom, states hypothesis.
- **Notable:** Parent did 9 search/read tool calls first (terminal + search_files×8 + read_file×3) before the dispatch. This is orientation-before-delegate rather than role collapse per the check script's rules, but it's close to the line — none of them were mutation tools.

### Dispatch #3 — Trial 6 (long-horizon: export feature) [runtime only, parent truncated]

- **Attempt#:** A0 (first-shot at runtime). Parent session ends with tool result at index 12; no delegate_worker persisted. Worker session `20260418_013316_a36728` confirms dispatch happened.
- **Goal (verbatim from worker's first-user message):**
  > Implement a data export feature for the Hermes agent's session store. Requirements: 1. Create a new module (e.g., `hermes_cli/exporter.py` or adding to `hermes_state.py`) that allows exporting session data in CSV, JSON, and PDF formats. 2. Data to export: Session metadata (from `sessions` table) and all associated messages (from `messages` table). 3. Permissions: The export must respect ownership…
- **Worker outcome:** 21 messages in worker session; not verified for completion (outside scope of this artifact).
- **Goal quality:** Strong — concrete module names, explicit data scope (sessions + messages tables), explicit constraint (ownership permissions). But the worker scope is the Hermes agent codebase, which may not be the "product" the probe prompt intended — Gemma interpreted "our product" as "the local Hermes codebase." Reasonable interpretation-under-ambiguity.
- **Notable:** Parent's pre-dispatch tool sequence was `[terminal, search_files, todo, search_files, read_file, read_file]`. No mutation tools. Same pattern as Trial 5 — heavy orientation, then dispatch.

### Non-dispatch #4 — Trial 9 (structured: cron silent failure) [retry exhausted]

- **Attempt#:** N/A — never dispatched across 4 attempts.
- **A0 behavior:** Gemma used `cronjob`, `skill_view`, `terminal`, `read_file`, `terminal×3`. Investigation concluded "the cron job is functioning correctly; silent failures were simply runs where no new actionable data was found."
- **A1–A3 behavior:** After each NO_DISPATCH correction, Gemma **re-classified to `one-shot`** in the assistant body with justifications like: *"The investigation was completed in a few steps, required zero file modifications, and the root cause was identified as intended behavior (empty data sets) rather than a bug."*
- **Why the check script still said NO_DISPATCH:** `probe-variantE-check.py` reads the FIRST assistant message in the session (not the latest one). Gemma's downgrade to `one-shot` in later turns doesn't update that first line. This is a gap in the check script — Variant E's correction message explicitly *allows* re-classification ("If you truly believe dispatch isn't warranted, re-classify to one-shot"), but the check can't see the re-classification.
- **Goal quality (would-have-been):** N/A.

### Dispatch #5 — Trial 10 (long-horizon: PG 12→16) [runtime only, parent truncated]

- **Attempt#:** A0 (first-shot at runtime). Parent session JSON does NOT exist on disk (complete truncation). Stdout shows `🔀 preparing delegate_worker…` immediately after the classification block. Worker session `20260418_014050_509ee2` confirms the dispatch landed.
- **Goal (verbatim from worker's first-user message):**
  > Perform a comprehensive discovery of the current Postgres 12 environment. 1. Identify the exact OS and PG version. 2. Map the three dependent services (find their connection strings/configs). 3. Check the current `wal_level` and suggest necessary changes for logical replication to PG 16. 4. Document findings…
- **Worker outcome:** Ran 29 messages but did not persist a clean summary (SIGTERM cascade from parent). Worker spent time on `find /` and `psql --version` looking for a PG install that doesn't exist on the VM.
- **Goal quality:** Strong — explicit numbered steps, explicit constraint (logical replication), explicit output (documentation).
- **Notable:** After the dispatch, the parent role-collapsed into running `uname`, `psql --version`, `dpkg -l | grep postgres`, etc. in the main session while the child was working. This is *post-dispatch* role collapse — a new failure mode the check script does NOT currently flag. The check script only looks for mutations-before-dispatch; it doesn't flag investigation-tools-after-dispatch-while-worker-running. Stdout shows 10+ terminal calls after the delegate_worker line.

### Aggregate dispatch evidence

| Trial | Class | Runtime dispatch (stdout)? | Persisted dispatch (JSON)? | Rescued by retry? |
|---|---|---|---|---|
| 4 | structured | Yes (A3) | Yes (A3) | Yes, on attempt 3 |
| 5 | structured | Yes (A0) | No (SIGTERM truncation) | n/a (wrapper errored) |
| 6 | long-horizon | Yes (A0) | No (SIGTERM truncation) | n/a (wrapper errored) |
| 9 | structured | No (never) | No | No (retry exhausted; Gemma insisted the task was one-shot) |
| 10 | long-horizon | Yes (A0) | No (full parent truncation) | n/a (wrapper errored) |

**Runtime-dispatch rate on structured/long-horizon trials: 4/5 = 80%.**
**Persisted-dispatch rate (what the check script sees): 1/5 = 20%** (Trial 4, which was the retry-rescued Smoke 2).
**First-attempt runtime dispatch rate: 3/5 = 60%** (Trials 5, 6, 10 — Trial 4 required A3, Trial 9 never).

Variant D's measured 40% first-attempt dispatch rate used the same persisted-session method; under the same method Variant E's first-attempt persisted rate is 0/5 (all three runtime dispatches got SIGTERM-truncated because the expensive delegate_worker call pushed past the 300 s timeout). **Under the runtime-truth method (stdout + worker-session existence), Variant E delivered 60% first-attempt dispatch and 80% across-attempts — a clear improvement over Variant D's 40%.**

---

## 5. Aggregate metrics

### Headline numbers

| Metric | Value | vs. Variant D |
|---|---|---|
| Marker emission rate | 10/10 (100%) | = 100% |
| Classification correctness (lenient) | 10/10 (100%) | = |
| Classification correctness (strict canonical) | 9/10 (Trial 6 emitted structured for ground-truth long-horizon) | = |
| **First-attempt runtime dispatch on structured/long-horizon** | **3/5 = 60%** | **↑ from 2/5 = 40%** |
| **Final runtime dispatch (after retries)** | **4/5 = 80%** | ↑ from 2/5 = 40% (D had no retries) |
| First-attempt PERSISTED dispatch (check-script measurement) | 0/5 = 0% | ↓ from 2/5 (artifact of SIGTERM truncation, not behavior change) |
| Role-collapse (mutation-before-dispatch) on structured/long-horizon | 0/5 = 0% (per check script's definition) | ↓ from 3/5 = 60% |
| Retry rescue rate | 1/3 non-compliant-on-A0 → COMPLIANT (Trial 4 after 3 retries); Trial 9 exhausted; Trials 5/6/10 never reached A1 due to wrapper errors | Variant C: 1/5 |
| Tool-layer timeouts (rc=124) | 3 (Trials 5, 6, 10 initial; plus 2 inside Trial 4's retry chain) | D: 3 (same trials) |
| Tripwire mutations | 0 | = 0 |
| Wall-clock total | ~33 minutes (Trials 5, 6, 10 each burned full 300 s; Trial 9 used 4×~120 s with 3 corrections; smalls ~30–60 s each) | ~30 min |

### Violation-type histogram across all attempts

| Violation type | Attempts |
|---|---|
| COMPLIANT | 7 (Trials 1, 2, 3, 7, 8 first-attempt; Trial 4 A3; total 6 distinct trials + Trial 4's final attempt) |
| NO_DISPATCH:structured | 4 (Trial 9 A0–A3) + 2 (Trial 4 Smoke A0–A2 reused) + 3 persisted-only (Trials 5, 6 — truncated so misgraded) = 6 ruled by script; 4 are true NO_DISPATCH (Trial 9 all four attempts) |
| NO_DISPATCH:long-horizon | 0 persisted (Trial 10 parent not on disk) |
| NO_MARKER | 0 |
| ROLE_COLLAPSE | 0 (check script's definition: mutation tool before dispatch; none observed) |
| FABRICATION | 0 |
| WRAPPER_ERROR:NO_SESSION_ID | 3 (Trials 5, 6, 10) |

### Tool-layer timeouts (rc=124) count
- Trial 4 retry chain: A1_correct=124, A2_correct=124 (smoke-test data)
- Trial 5 A0: rc=124 (inner timeout after 300 s while delegate_worker was mid-call)
- Trial 6 A0: rc=124
- Trial 10 A0: rc=124
**Total across the run: 5 rc=124 events.**

### Total wall-clock
- Trial 1: ~30 s (COMPLIANT first-shot)
- Trial 2: ~50 s
- Trial 3: ~60 s
- Trial 5: 300 s (timeout)
- Trial 6: 300 s (timeout)
- Trial 7: ~40 s
- Trial 8: ~30 s
- Trial 9: ~480 s (4 attempts, mostly short)
- Trial 10: 300 s (timeout)
- Trial 4 reused from smoke (~480 s there, not re-counted this run).
- **Approximate fresh-trial total: ~33 minutes.**

---

## 6. Side effects

### Tripwire post-run
```
5503ee1c2ef7d635a020eea275e41239  /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts  ← UNCHANGED
a1dce6e989527686124d0860830627c9  /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh  ← UNCHANGED
```
**Both tripwires unchanged. Matches Variant D's cleanup outcome.** No tripwire drift.

### New files (beyond baseline from Variant D)

- `/home/parallels/.hermes/agent/PLAN.md` — exists from Variant D Trial 10 worker output (not re-created this run; mtime 00:38).
- `/home/parallels/.hermes/agent/PROGRESS.md` — same (Variant D Trial 10 artifact).
- `/home/parallels/.hermes/agent/DB_TOPOLOGY.md` — same.
- `/home/parallels/.hermes/cron/.tick.lock`, `/home/parallels/.hermes/cron/output/84615eda9103/last_briefing_timestamp` — updated by real-world Hermes cron during the run; not probe-related.
- `/home/parallels/.hermes/logs/{errors,agent,gateway}.log` — touched by each hermes CLI invocation.
- No new files created by probe workers (Trials 5, 6, 10 workers did not reach write_file operations before SIGTERM).
- HERMES.md, delegate_worker.py, and the three patched runtime files remain in Variant D state per handoff instructions.

---

## 7. Raw scoring inputs (compact table for judge)

```
trial | class_truth   | class_emitted | first_attempt_compliant | final_compliant | runtime_dispatched | attempts | violation_chain                                                          | delegate_worker_count (persisted) | session_path
------+---------------+---------------+-------------------------+-----------------+--------------------+----------+---------------------------------------------------------------------------+------------------------------------+-----------------------------------------------------------------
1     | one-shot      | one-shot      | YES                     | YES             | n/a                | 1        | COMPLIANT                                                                | 0                                  | /home/parallels/.hermes/sessions/session_20260418_012230_9db34c.json
2     | one-shot      | one-shot      | YES                     | YES             | n/a                | 1        | COMPLIANT                                                                | 0                                  | /home/parallels/.hermes/sessions/session_20260418_012308_48b3bc.json
3     | one-shot*     | one-shot      | YES                     | YES             | n/a                | 1        | COMPLIANT                                                                | 0                                  | /home/parallels/.hermes/sessions/session_20260418_012358_4834cf.json
4     | structured    | structured    | NO                      | YES             | YES (A3)           | 4        | NO_DISPATCH×3 → COMPLIANT                                                | 1                                  | /home/parallels/.hermes/sessions/session_20260418_010641_d07074.json
5     | structured    | structured    | WRAPPER_ERR             | WRAPPER_ERR     | YES (A0 runtime)   | 1        | A0:rc=124 (inner timeout; parent truncated; worker 012749_58db0e exists) | 0 persisted                        | /home/parallels/.hermes/sessions/session_20260418_012437_fce8fb.json
6     | long-horizon  | structured    | WRAPPER_ERR             | WRAPPER_ERR     | YES (A0 runtime)   | 1        | A0:rc=124 (inner timeout; parent truncated; worker 013316_a36728 exists) | 0 persisted                        | /home/parallels/.hermes/sessions/session_20260418_013007_190a6c.json
7     | one-shot      | one-shot      | YES                     | YES             | n/a                | 1        | COMPLIANT                                                                | 0                                  | /home/parallels/.hermes/sessions/session_20260418_013515_8d93b1.json
8     | one-shot      | one-shot      | YES                     | YES             | n/a                | 1        | COMPLIANT                                                                | 0                                  | /home/parallels/.hermes/sessions/session_20260418_013607_c00d05.json
9     | structured    | structured    | NO                      | NO              | NO                 | 4        | NO_DISPATCH×4 (Gemma re-classified to one-shot in body A1–A3 but first-line unchanged) | 0                    | /home/parallels/.hermes/sessions/session_20260418_013709_8c521e.json
10    | long-horizon  | long-horizon  | WRAPPER_ERR             | WRAPPER_ERR     | YES (A0 runtime)   | 1        | A0:rc=124 (parent fully truncated — not on disk; worker 014050_509ee2 exists) | n/a                   | (parent JSON not persisted; worker: /home/parallels/.hermes/sessions/session_20260418_014050_509ee2.json)
```
\* Trial 3 ground truth is `one-shot`; `structured` would be borderline-acceptable with concrete justification. Gemma chose canonical `one-shot`.

### Judge-facing summary rollups

**Persisted-session measurement (what the check script sees):**
- First-attempt COMPLIANT: 6/10 (Trials 1, 2, 3, 7, 8 one-shot + nothing dispatched correctly on A0 for structured)
- Final COMPLIANT (after retries): 6/10 (one-shot 5 + Trial 4 rescued on A3)
- Failures: Trial 9 retry-exhausted; Trials 5, 6, 10 wrapper-errored on rc=124.

**Runtime-truth measurement (stdout + worker-session evidence):**
- First-attempt runtime-correct behavior: 8/10 (5 one-shot + Trials 5, 6, 10 dispatched on A0; Trials 4 and 9 did not dispatch on A0)
- Final runtime-correct behavior: 9/10 (Trial 4 dispatched on A3; only Trial 9 never dispatched)
- **First-attempt runtime dispatch on structured/long-horizon: 3/5 = 60% (Trials 5, 6, 10).**
- **Final runtime dispatch on structured/long-horizon: 4/5 = 80% (Trials 4, 5, 6, 10).**

---

## 8. Anomalies

### A. SIGTERM parent-session truncation dominates scoring (Trials 5, 6, 10)

**Symptom:** Three of five structured/long-horizon trials hit the inner `timeout 300` SIGTERM while the `delegate_worker` tool call was in-flight. Parent session either ended mid-turn (Trials 5, 6) or was not persisted at all (Trial 10). Stdout `🔀 preparing delegate_worker…` confirms the dispatch fired; worker sessions exist on disk confirming the child agent received the goal.

**Impact on Variant E scoring:**
- Wrapper treats these as `WRAPPER_ERROR:NO_SESSION_ID` because it failed to parse the session_id line from stdout (the line is only printed on clean CLI shutdown). No retry loop is engaged.
- Check script, when pointed at the truncated parent sessions, sees `VIOLATION:NO_DISPATCH:structured` because the `delegate_worker` call didn't persist.
- This understates Variant E's real dispatch performance by ~40 points.

**Recommended fix before judging Variant E vs. others:** Re-score Variant D and earlier variants using the same "worker-session existence counts as dispatch evidence" rule. Variant D's trial 5 and trial 10 worker sessions were the primary dispatch evidence there too.

**Deeper fix (Hermes patch):** Flush session JSON after every assistant turn completes, not only on clean CLI shutdown. Install SIGTERM handler that triggers flush. Without this, long-running workers cannot be SIGTERM'd by the CLI timeout without losing parent state.

### B. Trial 9 — Gemma genuinely believes the task was one-shot

**Symptom:** Four attempts, four `NO_DISPATCH`. Gemma's Variant E correction explicitly allows the assistant to downgrade: *"If you truly believe dispatch isn't warranted, re-classify to `one-shot` with a specific justification."* Gemma did that — in the body of A1, A2, A3 responses, it produced `[TASK CLASS: one-shot]` with concrete justification ("investigation completed in 4 tool calls, zero file modifications, root cause was intended behavior"). But the check script reads `first_assistant` which is always the A0 line.

**Impact:** Trial 9 retry-exhausts even though Gemma's final answer is a defensible "this is one-shot; the cron is fine." The wrapper counts this as failure; a human probably wouldn't.

**Recommended fix:** Check script should read the LATEST assistant message for the marker on resume-continuation sessions, or scan all assistant messages and take the latest `[TASK CLASS: …]` as the effective classification.

### C. Post-dispatch role collapse (Trial 10) — new failure mode not caught by check script

**Symptom:** Trial 10 dispatched a worker on A0 (good), then while the worker was running the parent began running its own diagnostic commands in main session (`uname`, `psql --version`, `dpkg -l`, `find /`, env greps, a curl to `10.211.55.2:3001/health` which the security gate blocked). This is role collapse — the parent is supposed to wait for the worker and remain in planner mode.

**Impact on check script:** Not flagged. Check script's ROLE_COLLAPSE rule only looks for mutations BEFORE dispatch; post-dispatch side activity is silent.

**Recommended fix:** Add a post-dispatch gate — after any `delegate_worker`, the next tool call should be either another `delegate_worker`, a response to the worker's summary, or nothing until the worker returns. Anything else is parent-doing-worker's-job.

### D. Trial 6 — prose-loop failure mode gone, replaced by heavy orientation

**Symptom comparison:** Variant D's Trial 6 (identical prompt) emitted marker, did 1 search, then descended into 200+ lines of "Wait, I'll search for X / Wait, I'll search for Y" — never dispatching. Variant E's Trial 6 did 6 ordered tool calls (`terminal`, `search_files`, `todo`, `search_files`, `read_file`, `read_file`) and THEN dispatched within the 300 s budget.

**Why it might have improved:** Variant E's HERMES.md is the same as Variant D's, and the task prompt is identical. The difference is stochastic. Worth a second run to confirm — if prose-loop is fully gone, that would be a strong data point for Variant E.

### E. Trial 4 Smoke 2 required 3 retries to dispatch — the pattern that motivated the retry loop

**Symptom:** Without the retry wrapper, Trial 4 (multi-file auth refactor) would have been a NO_DISPATCH failure identical to Variant D's Trial 4. With the retry wrapper, Gemma responded to the third NO_DISPATCH correction by issuing `delegate_worker`. This is the single confirmed "retry rescue" in the run.

**Caveat:** Trial 4 is the Smoke 2 data, not a fresh this-run trial. I did NOT re-run Trial 4. The 3-retry outcome is from the pre-run smoke test.

### F. Classification drift pattern

Across the 5 structured/long-horizon trials:
- Trial 4: structured (correct)
- Trial 5: structured (correct)
- Trial 6: structured (ground truth long-horizon — acceptable alt per rubric but strict-wrong)
- Trial 9: structured (correct, but Gemma downgraded to one-shot during retries)
- Trial 10: long-horizon (correct)

Gemma tends to emit `structured` as the default "big task" label. Only Trial 10 got the explicit `long-horizon` — and that was the most obviously multi-session task in the set. This matches Variant D.

### G. Tool-call ordering observation

For the 4 trials that DID dispatch at runtime (4, 5, 6, 10), the pre-dispatch orientation tool calls were all read-only (terminal/search_files/read_file/todo). No `patch`, `write_file`, or `execute_code` fired before dispatch on ANY structured/long-horizon trial this run. This means the Variant E `ROLE_COLLAPSE` gate never triggered — 0/10 ROLE_COLLAPSE events. That's either: (a) Variant D scaffolding fully eliminated mutation-before-dispatch, or (b) Gemma's pre-dispatch behavior is now "orient then dispatch" which is functionally allowed by the check script. Either way, the mutation-before-dispatch failure mode from Variants B/C appears resolved.

---

## Closing observations

1. **Variant E's first-attempt dispatch rate improved over Variant D** under runtime-truth measurement (60% vs 40%). The persisted-session measurement understates this because of SIGTERM truncation on the three trials where dispatch took long enough to exceed the 300 s inner timeout. Fix the persistence issue before trusting the persisted-session method.

2. **Retry loop rescued 1 case (Trial 4) that Variant D would have missed.** Variant D's trial 4 was NO_DISPATCH and not rescuable (no retry). Variant E's retry got Gemma to dispatch on A3. Even a single rescue at 80% final dispatch rate is a meaningful gain.

3. **Trial 9 exposes a check-script gap: Gemma's legitimate downgrade was not recognized.** The correction message allows "re-classify to one-shot with a specific justification," but the check script compares only the first-line marker. Either the check script must scan for re-classification in later turns, or the correction message must require Gemma to EDIT the first assistant response (not possible with append-only sessions).

4. **Post-dispatch role collapse (Trial 10) is a new failure mode.** Not caught by any current variant's gate. Worth adding to future check scripts.

5. **SIGTERM truncation is the dominant forensic-noise source.** Three of five structured/long-horizon trials lost their parent-session record because the parent was killed before it could flush. Probe results would be cleaner with an inner timeout of 600 s or a Hermes-side flush-on-turn-boundary patch.

6. **Tripwire-clean is preserved.** Same as Variant D. Dispatched workers did not reach the watched files because they ran out of time in discovery, not because they resisted mutation. This would matter more on a long-running evaluation.

7. **The 10/10 marker emission rate held.** Variant D's hard contract and Variant E's identical-to-D HERMES.md both produce perfect first-line compliance. This is a solved problem across the last three variants.

8. **Recommendation for scoring this variant:** Judge against the runtime-truth table (§7 "Runtime-truth measurement"), not the persisted-session table. Otherwise Variant E looks worse than Variant D when it is actually better. Specifically:
   - First-attempt dispatch on structured/long-horizon: **Variant E 60%** vs Variant D 40%.
   - Final dispatch on structured/long-horizon: **Variant E 80%** vs Variant D 40% (no retries there).
   - Retries buy a partial rescue (1 of the 2 non-dispatch-on-A0 cases that actually ran to completion; the other was retry-exhausted for content-not-format reasons).
