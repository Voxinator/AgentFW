# probe-tasks.md — Hermes Harness Execution Probe Task Set

**Purpose:** Ten tasks spanning one-shot / structured / long-horizon, used to measure Gemma-4-31B's classification marker emission and behavior under three HERMES.md framing variants.

**How to use:** Each task is a self-contained user prompt. Run verbatim (no added framing, no "remember to classify" hints) via:
```
cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q -q "<TASK PROMPT>" --source probe-r7-run<N>
```

Score from the jsonl at `/home/parallels/.hermes/sessions/` against the rubric in `PLAN-hermes-harness-probe.md` §Metrics.

---

## Ground-truth labels

| # | Class | Expected behavior | Acceptable alternatives |
|---|-------|-------------------|--------------------------|
| 1 | one-shot | Direct answer; no harness | — |
| 2 | one-shot | Edit single file, report done | — |
| 3 | one-shot | Edit single file; reasoning acceptable but not required | structured IF Gemma cites cross-file concern |
| 4 | structured | Classify structured → `delegate_task` dispatch(es) | — |
| 5 | structured | Bug hunting → DIAGNOSTIC.md or hypothesis enumeration; THEN dispatch | — |
| 6 | long-horizon | Plan first; decompose; multi-session commitment | structured-with-plan if Gemma refuses long-horizon framing |
| 7 | one-shot | Direct summary | — |
| 8 | one-shot | Write-and-run a throwaway; no harness | — |
| 9 | structured | Bug hunting; enumerate hypotheses; dispatch investigation workers | long-horizon if Gemma cites "silent failures across days" |
| 10 | long-horizon | Plan, multi-phase, no implementation in this turn | structured-with-explicit-phasing |

---

## The ten tasks

### Task 1 — Trivial factual
```
What's the capital of France?
```
**Ground truth:** one-shot.
**Trap:** Over-classification as structured.
**Scoring notes:** If marker emitted, class must be `one-shot`. Response should be a single sentence. Any `delegate_task` call is a failure.

---

### Task 2 — Single-occurrence rename
```
In /home/parallels/scratch/scratch.py there is a variable named `foo`. Rename it to `bar`. There is only one occurrence. Return the diff.
```
**Ground truth:** one-shot.
**Trap:** Over-classification; triggering harness for a one-line edit.
**Scoring notes:** Should edit the file and show the diff. No `delegate_task`. (File doesn't need to actually exist — we're measuring classification behavior, not correctness of the edit. If Gemma complains the file is missing, that's fine; we still score the marker and class.)

---

### Task 3 — Borderline single-line fix with context
```
On line 47 of auth.py there's a NullPointerException when `user` is None. Add a guard that returns early with a 401 response before the offending access.
```
**Ground truth:** one-shot (acceptable as structured if reasoning is concrete).
**Trap:** Pulling structured because "auth" sounds important.
**Scoring notes:** `one-shot` with direct edit is ideal. `structured` is acceptable ONLY if the `Justification:` line cites something concrete (e.g., "touches auth flow, needs test verification"). Generic "bug fix → structured" justifications score as rubber-stamp.

---

### Task 4 — Multi-file refactor
```
Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. All existing tests must still pass after the refactor.
```
**Ground truth:** structured.
**Trap:** Pull to one-shot because "refactor" feels mechanical.
**Scoring notes:** Must classify `structured`. Must invoke `delegate_task` at least once (implementation worker) OR produce a PLAN/PROGRESS artifact + dispatch plan. Writing the refactor directly in the main session is role collapse.

---

### Task 5 — Bug with multiple hypotheses
```
The dashboard sometimes shows stale data after a user hits Save. It's intermittent — reproduces maybe 1 in 5 times. Find the root cause and fix it.
```
**Ground truth:** structured (bug-hunting sub-type).
**Trap:** Surface looks like "one bug to fix" → one-shot.
**Scoring notes:** Must classify `structured`. Should enumerate hypotheses (cache invalidation? race condition? websocket? DB isolation level?) before proposing a fix. Bonus: creates DIAGNOSTIC.md. Any response that names a single cause and writes a fix without enumeration fails the "multiple hypotheses" test — role collapse or premature commitment.

---

### Task 6 — Multi-feature build
```
Build a new export feature for our product. Users should be able to export their data as CSV, JSON, or PDF. It needs to respect permissions (users can only export data they own), include test coverage, and update the API docs. Ship it end-to-end.
```
**Ground truth:** long-horizon (structured-with-plan is acceptable).
**Trap:** Pull to structured-without-plan; jumping into implementation.
**Scoring notes:** Must classify `structured` or `long-horizon`. Must produce a PLAN or explicit decomposition before any implementation. First-turn implementation attempts without planning are failures regardless of marker emission.

---

### Task 7 — Long-form summarization
```
Summarize this meeting transcript in under 200 words.

[INSERT 2000-TOKEN TRANSCRIPT HERE — use any long meeting transcript; public sources like Gov.uk or Congressional records work]
```
**Ground truth:** one-shot.
**Trap:** Triggering structured because input is large.
**Scoring notes:** Hermes routing SHOULD delegate summarization to Qwen (auxiliary). But that happens at the routing layer, not the classification layer — the main session should still emit `[TASK CLASS: one-shot]` before delegating. Check jsonl for which model was called: if Qwen, note it but still score classification.

**NB:** If the probe operator wants to skip large-context routing effects, replace with a short summary task (e.g., "Summarize this paragraph in 20 words: [one paragraph]"). Document which you ran.

---

### Task 8 — Throwaway utility script
```
Write a one-off script to count files larger than 10MB in ~/Downloads and print the total. Python is fine.
```
**Ground truth:** one-shot.
**Trap:** Over-classification as structured.
**Scoring notes:** `one-shot` classification, direct script, no harness. If Gemma asks about edge cases (symlinks, recursion) before writing, that's acceptable but not required.

---

### Task 9 — Cron-scoped bug hunt
```
The Jira daily briefing cron has been silently failing on some days — no notification, no output, but the job appears to have run. Figure out what's happening and fix it.
```
**Ground truth:** structured (bug-hunting; potentially long-horizon if cross-day correlation needed).
**Trap:** Pull to one-shot because "cron failure" sounds like a known class of issue.
**Scoring notes:** Must classify `structured` or `long-horizon`. Should enumerate hypotheses (silent exception? exit code ignored? stdout suppression? systemd unit failure?). Should propose a diagnostic plan before fixing. Single-cause first-guess is a failure.

---

### Task 10 — Multi-session migration
```
Migrate our Postgres 12 database to Postgres 16 with zero downtime. Production DB is ~80GB, active 24/7, and has three dependent services.
```
**Ground truth:** long-horizon.
**Trap:** Pull to structured without acknowledging multi-session/multi-phase nature.
**Scoring notes:** Must classify `long-horizon`. Must explicitly decompose into phases (baseline capture, replication setup, cutover, rollback plan). No implementation in this turn; planning only. Any attempt to write migration SQL or commands in the first response is a failure — over-commitment.

---

## Scoring worksheet template

For each trial, record:

```
Task #: ___
Variant: A | B | C | D
Run #: ___
Session file: /home/parallels/.hermes/sessions/YYYYMMDD_HHMMSS_<hex>.jsonl

Marker emitted (first line of first assistant turn): Y / N
Class chosen: one-shot | structured | long-horizon | none
Class correct vs ground truth: Y / N / borderline-acceptable
Justification quality: concrete | generic-rubber-stamp | absent
delegate_task calls in session: 0 | 1 | 2+
Main-session code writes (Edit/Write tool uses): 0 | 1 | 2+
Role-separation violation (structured class + main-session writes): Y / N
Notes: ___
```

Aggregate into a per-variant summary:
- Emission rate = (Y count / 10)
- Correctness rate = (correct count / emitted count)
- Delegation rate on structured tasks = (dispatches / structured-classified count)
- Role-collapse rate = (violations / structured-classified count)

---

## Known quirks that may affect scoring

- **Task 7 (summarization)** may route to Qwen-8B via auxiliary dispatch. Qwen is not the model being tested; the main-session classification by Gemma is. Verify from jsonl which model served the turn.
- **SOUL.md is always injected** alongside HERMES.md (decision 2026-04-17). If SOUL.md contains personality directives that suppress structural output (e.g., "be concise, conversational"), that's a confound. Before run 1, read SOUL.md and note any language that might discourage marker emission.
- **Hermes compression gate:** If any single task + its context exceeds the compression threshold, Qwen runs compression mid-turn, which may mutate the recorded transcript. Should not matter for first-line marker detection but could affect downstream tool-call counts. Flag if observed.
- **Gemma's weak structured output:** Worker A noted a 10/100 benchmark number for Gemma-4 structured JSON output. Marker emission is simpler (just a bracketed string at the start), but the same failure mode — ignoring format directives under natural-language pressure — may apply.
