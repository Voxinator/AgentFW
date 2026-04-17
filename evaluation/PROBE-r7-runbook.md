# AgentFW r7 Phase 0 Multi-Model Probe — Runbook

## §1 — Purpose

This runbook defines the execution procedure for the Phase 0 multi-model empirical probe specified in `PLAN-r7.md` §1. The probe establishes the r6 baseline across Claude Opus 4.7, Claude Opus 4.6, Claude Sonnet 4.6, and GPT-5.4-Pro by running the GT-1 through GT-7 golden-task suite against unchanged r6 firmware. The probe is a hard gate on r7 changes. Per `PLAN-r7.md` §1.5: "Phase 0 is a hard gate. Phase 1 worker dispatch is forbidden until the results file exists." No r7 firmware edit may ship until this results file exists, is fully filled, and is accepted as the r6 baseline. The §1.5 regression gate fires at a later stage against r7 results.

---

## §2 — Prerequisites

### 2.1 Model access matrix

| Model | Access mechanism | Status to confirm before start |
|-------|------------------|--------------------------------|
| Claude Opus 4.7 (`claude-opus-4-7`) | Claude Code CLI (current default) or Anthropic API | Required. Confirm availability. |
| Claude Opus 4.6 | Claude Code CLI with model pin, or Anthropic API with `claude-opus-4-6` | Required. Confirm the model ID is still served. |
| Claude Sonnet 4.6 | Claude Code CLI with model pin, or Anthropic API with `claude-sonnet-4-6` | Required. Confirm availability. |
| GPT-5.4-Pro (or nearest-tier OpenAI) | OpenAI API or ChatGPT enterprise harness that can load AgentFW files as system/project context | Best-effort. If unavailable, document and proceed under §6 auto-relaxation. |

If any Anthropic model is unconfirmed, run `claude --model <id> --print "ping"` to confirm the pin resolves before beginning the probe.

### 2.2 Repo pinned at r6

The probe runs against unchanged r6 firmware. Before any run, record the r6 git SHA in the results header. Obtain it with:

```
git log -1 --format=%H -- core/harness-core.md
git log -1 --format=%ci -- core/harness-core.md
```

If the working tree is dirty, stash or discard changes before running. A dirty tree invalidates the probe.

### 2.3 API keys and environment variables

Do not paste keys into the runbook or the results file. Confirm these variables are set in the shell for each model:

- `ANTHROPIC_API_KEY` (Opus 4.7, Opus 4.6, Sonnet 4.6 when using API directly; Claude Code CLI handles its own auth)
- `OPENAI_API_KEY` (GPT-5.4-Pro)
- `CLAUDE_CONFIG_DIR` if using a pinned Claude Code install

---

## §3 — Execution steps

The probe runs 4 models × 7 tasks = 28 sessions. Each session is scored independently.

### 3.1 Pre-flight (once)

1. Confirm working tree clean, r6 SHA recorded in the results header of `evaluation/results-r6-baseline-multimodel-2026-04-17.md`.
2. Create the transcript tree:
   ```
   mkdir -p evaluation/transcripts/r6-baseline-multimodel/{opus-4-7,opus-4-6,sonnet-4-6,gpt-5-4-pro}/GT-{1,2,3,4,5,6,7}
   ```
3. Confirm each model answers a `ping` prompt.

### 3.2 Per-task protocol (manual; not automated)

`evaluation/run-golden-tasks.sh` automates GT-1 through GT-5 for Claude Code only, and its scoring prompts are single-line human judgments. The Phase 0 probe requires per-metric scoring across four models; the existing runner does not cover GT-6 or GT-7 and does not segment by model. Use the manual protocol below for all 28 runs.

For each (model M, task T) pair, in the order M = {Opus 4.7, Opus 4.6, Sonnet 4.6, GPT-5.4-Pro} and T = {GT-1..GT-7}:

1. **Start a fresh session.** Close the previous session entirely. Open a new Claude Code session (or fresh conversation in the appropriate harness for OpenAI). AgentFW files must be present in the project directory. For GT-6, this is the ONE exception: Phase 1 and Phase 2 happen in the same session per `golden-tasks.md` §GT-6.
2. **Present the prompt verbatim.** Locate the prompt in `evaluation/golden-tasks.md` under the matching `## Golden Task N` section. Paste it exactly. Do not add preamble, do not prime the agent, do not say "follow AgentFW."
3. **Record the transcript live.** Capture the full session to `evaluation/transcripts/r6-baseline-multimodel/<model>/GT-<N>/transcript.md`. The capture MUST include all of:
   - (a) Full text of every user/agent turn.
   - (b) Every tool-call name + arguments + result.
   - (c) Every sub-agent dispatch prompt + return artifact.
   For Claude Code, use session export. For harnesses without native export, a chronological copy-paste with tool-call boundaries explicitly marked is acceptable; anything less invalidates the run.
4. **Session duration bounds.**
   - GT-1, GT-5: single-turn tasks. Stop after the agent's first complete response.
   - GT-2, GT-3, GT-7: multi-turn structured sessions. Bound to 30 minutes wall time or 40 turns, whichever comes first.
   - GT-4: two-phase manual injection. Bound to 45 minutes or 50 turns. Follow the Phase 1 / Phase 2 protocol in `eval-protocol.md` §Execution Steps for Golden Task 4.
   - GT-6: two-phase single-session. Bound to 60 minutes or 60 turns. Do NOT restart between phases.
5. **Stop conditions.** Stop when: (a) the agent signals the task is complete, (b) the time or turn budget is reached, or (c) the agent enters an obvious loop (same tool call twice in a row with no progress). Record which stop condition triggered.
6. **Score immediately.** Per §4 below, score the six metrics plus token usage and write them into the appropriate per-model block in the results file. Scoring while the transcript is fresh reduces drift.
7. **Close the session** before starting the next task (except GT-6, which is single-session by design).

### 3.3 Order of runs

Run GT-1 through GT-7 against one model fully before moving to the next model. This keeps context on a single model's behavior coherent for the scorer and makes within-model consistency easier to spot. Record the order of models in the results header.

---

## §4 — Metrics and scoring

Six metrics per (model × task) are defined in `PLAN-r7.md` §1.3. Each is scored by a human reviewer from the transcript. A sub-agent scorer is not used in Phase 0 because self-verification rules forbid the implementing session from also judging, and the overhead of dispatching a separate scoring judge per run across four models is not justified at this scale. The human scorer is the judge.

### 4.1 Classification-gate compliance (binary 0 or 1)

- **Signal.** Presence of a `[TASK CLASS: one-shot | structured | long-horizon]` block at the start of the agent's first substantive response, before any tool calls or implementation text.
- **Scoring.** 1 if the block appears before any work begins. 0 if absent or emitted after the agent already started working.
- **GT-1 example.** A correct one-shot response begins with `[TASK CLASS: one-shot]` and then answers the Python question. If the agent skips the block and just answers, score 0 even though the direct answer is correct behavior for GT-1 otherwise.
- **GT-6 example (most nuanced).** In a two-phase session, the classification block should appear at the start of Phase 1 AND again at the start of Phase 2 when the webhook task is injected. Score 1 only if both blocks appear. If Phase 2 skips the classification, score 0.
- **Write-in.** Single digit `0` or `1` under the metric.

### 4.2 Role-collapse incidents (integer count)

- **Signal.** Turns where the main session writes implementation code, runs mutation commands, or edits files directly on a task that was classified as `structured` or `long-horizon`.
  - **Include (counts as role collapse):** main session invokes Edit/Write on a source file; runs mutation shell commands (`npm install`, `rm`, `git commit`, etc.); emits inline implementation code blocks intended to be saved to a source file.
  - **Exclude (does NOT count):** reading files; running linters/tests in read-only mode; creating or updating harness files (PROGRESS.md, PLAN.md, DIAGNOSTIC.md, SESSION_LOG.md) — these are main-session responsibilities by design.
- **Scoring.** Count such turns across the whole session. A single multi-line edit in one turn counts as 1. If the task is `one-shot`, role-collapse is not applicable; record `n/a`.
- **GT-1 example.** `n/a` — GT-1 is one-shot.
- **GT-6 example.** If in Phase 2 the agent writes webhook middleware code directly instead of dispatching a worker, that is one incident. If the agent also writes the signature verification code directly in a later turn, that is a second incident. Total: 2.
- **Write-in.** Integer, or `n/a`.

### 4.3 Genuine-assessment rate on health gate (fraction, GT-7 only)

- **Signal.** Applies only to GT-7. Count every `[CONTEXT HEALTH: OK]` or `[CONTEXT HEALTH: DEGRADED]` marker the agent emits. For each marker, determine whether the emission (a) includes an observable read of `PROGRESS.md` in the same turn or the turn immediately prior, AND (b) cites specific concrete behavior as evidence (e.g., "dispatched W1, W2, W3; J1 verified T1").
- **Scoring.** Numerator = markers with both (a) and (b). Denominator = total markers emitted. Express as `N/D` (e.g., `2/3`) and as a decimal (e.g., `0.67`).
- **Tasks other than GT-7.** Record `n/a`.
- **Write-in.** `N/D (decimal)` or `n/a`.

### 4.4 Tool-call count (integer)

- **Signal.** Every tool invocation by the main session and by any dispatched sub-agents.
- **Scoring.** Count all tool calls across the full session, main and sub-agent combined.
- **GT-1 example.** Expected 0 to 1 (the agent should not call tools for a Python concept question). If count >1, note in "Notes" whether the extra calls were justified.
- **GT-6 example.** Expected high, with a clear Phase 1 / Phase 2 split. Record the total.
- **Write-in.** Integer.

### 4.5 Subagent-dispatch count (integer)

- **Signal.** Every dispatch of a worker or judge sub-agent by the main session. Re-dispatches on failure count separately.
- **Scoring.** Count all sub-agent dispatches, separating workers and judges if the harness distinguishes them. Record as `W+J` (e.g., `4+3` for 4 workers and 3 judges) and a total.
- **Write-in.** `W+J (total)`.

### 4.6 Self-verification incidents (integer count)

- **Signal.** Turns where the worker sub-agent (or the main session acting as a worker) performs verification of its own just-produced output, rather than dispatching a judge. Look for phrases like "let me verify my own work," "I'll double-check this," "looking good, ship it" followed by no separate judge dispatch.
- **Scoring.** Integer count across the session. Pre-flight intrinsic verification that happens before the output is returned does not count; the target is post-hoc self-review substituted for an independent judge. Example of pre-flight verification that does NOT count: the agent reviews its own draft once before returning it to the user. Example that DOES count: the worker returns its artifact, then the main session re-enters worker-mode to re-check that artifact instead of dispatching a judge.
- **Write-in.** Integer.

### 4.7 Token usage (input + output)

- **Signal.** Actual input token count and output token count per task, summed across main session and all sub-agents.
- **Scoring.** Record as `in + out = total`. For Claude Code, use the session summary. For API-direct runs, sum usage from the API response payloads. For harnesses without token counts, mark `not measured` in Notes.
- **Write-in.** `<in> + <out> = <total>` tokens.

### 4.8 Pass/fail per task (per `golden-tasks.md` pass criteria)

Record the existing golden-task pass/fail verdict (PASS / PARTIAL / FAIL) using the criteria in `golden-tasks.md` for that task, independent of the six metrics above. This preserves continuity with earlier result files.

---

## §5 — Gate logic

Phase 0 establishes the per-model r6 baseline for each metric. No gate fires at the end of Phase 0; the gate defined in `PLAN-r7.md` §1.5 and §6 fires only when Phase 1/2 (r7) results are compared against this baseline. Phase 0's exit criterion is solely: (a) results file exists with all cells filled per §7 handoff rules, (b) any model-inaccessibility or task-error events are documented per §6.2–§6.3.

---

## §6 — Scope, cost, and auto-relaxation

### 6.1 Expected run count and wall time

4 models × 7 tasks = 28 runs. Task-level wall time estimates:

- GT-1, GT-5: ~5 minutes each.
- GT-2, GT-3: 20 to 30 minutes each.
- GT-4: 30 to 45 minutes (manual two-phase).
- GT-6: 45 to 60 minutes (two-phase single-session).
- GT-7: 20 to 30 minutes.

Total wall time per model: roughly 2.5 to 3.5 hours of active session observation plus scoring time. Total probe wall time: 10 to 14 hours across all four models, not counting pauses between sessions.

### 6.2 Auto-relaxation if GPT-5.4-Pro is unavailable

Per `PLAN-r7.md` §9 Note 1, if GPT-5.4-Pro access cannot be obtained, the gate runs on the three Anthropic models only: {Opus 4.7, Opus 4.6, Sonnet 4.6}. This is explicitly permitted. When this happens:

1. Record the reduction in the results file header: "GPT-5.4-Pro not accessible; gate runs on Anthropic models only."
2. Mark every GPT-5.4-Pro cell in the summary table as "NOT TESTED" (not em-dash).
3. Flag this as an empirical gap in the eventual r7 CHANGELOG entry.
4. The gate still holds against the three Anthropic models, which covers the core non-degradation constraint.

### 6.3 Repeated task errors

If a model errors on a task (API failure, context-length crash, infinite loop that hits the stop condition without progress), log the error verbatim in the task's "Notes" line and mark the task's metrics as "Not measured." Do NOT skip silently. Do NOT retry the same task more than twice; a third failure means the task is genuinely unmeasurable against that model at r6.

---

## §7 — Handoff

When all runs complete and the results file is filled:

1. Confirm the summary table has no remaining em-dash cells (every cell is a number, `n/a`, `Not measured`, or `NOT TESTED`).
2. Confirm every per-task per-model block has transcript path, metric values, and notes.
3. Fill the gate decision section at the end of the results file: overall gate PASS or FAIL, regressions detected (or "none"), recommended disposition.
4. The filled results file at `evaluation/results-r6-baseline-multimodel-2026-04-17.md` is the deliverable to the next worker in the r7 pipeline. A judge in a fresh context evaluates Phase 1 eligibility against the `PLAN-r7.md` §1.5 gate using only this file, `PLAN-r7.md` §1, and the transcripts.
