# ARTIFACT — Drift Investigation, Worker ε (session-level forensic diff)

**Worker:** ε.
**Date:** 2026-04-17 / 2026-04-18 (r7 at 01:24 / 01:17 UTC+? session_start timestamps; r7.2 v2 at 14:11 / 14:18).
**Mode:** READ-ONLY; all extraction via `ssh ubuntu-vm python3 -c '...'`. No sessions modified.
**Goal:** At the session-JSON level, what is different between a r7 trial that dispatched vs a r7.2 v2 trial that role-collapsed on the same task text?

---

## 1. Session identification

Two same-task pairs were located:

**Task 5 — dashboard stale data (structured):**
- r7 reference: `/home/parallels/.hermes/sessions/session_20260418_012437_fce8fb.json` — Variant E Trial 5 parent. Per ARTIFACT-probe-variantE-trials.md, Trial 5 runtime dispatched (worker session `012749_58db0e` exists) but the parent was SIGTERM-truncated by the 300s wrapper while mid-`delegate_worker`. Of the four r7 structured-trial candidates, this is the ONLY r7 parent session run against the exact same task text as r7.2 v2 T5. Caveat: its persisted-on-disk state ends mid-investigation at message 23 (the stdout-visible `delegate_worker` call never landed on disk).
- r7.2 v2 reference: `/home/parallels/.hermes/sessions/session_20260418_141857_848189.json` — Trial 5 today, role-collapsed.

**Task 4 — auth refactor (structured):**
- r7 reference: `/home/parallels/.hermes/sessions/session_20260418_010641_d07074.json` — Variant E Trial 4 Smoke 2 (A0 attempt — NO_DISPATCH, 4-attempt retry chain eventually rescued this on A3; this is the first-attempt session on-disk for r7). Selected because no other r7 parent session on disk used the canonical Task 4 prompt.
- r7.2 v2 reference: `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json` — Trial 4 today, dispatched first-attempt (confirmed).

First-user-message text is byte-identical per pair (checked).

---

## 2. Top-level field diff

| Field | r7_T5 (012437) | r72_T5 (141857) | match? |
|---|---|---|---|
| `session_id` | 20260418_012437_fce8fb | 20260418_141857_848189 | expected-diff |
| `model` | gemma-4-31b-it-4bit | gemma-4-31b-it-4bit | **YES** |
| `base_url` | http://10.211.55.2:8000/v1 | http://10.211.55.2:8000/v1 | **YES** |
| `platform` | cli | cli | **YES** |
| `session_start` | 2026-04-18T01:24:37 | 2026-04-18T14:18:57 | expected-diff |
| `tools` count | 29 | 29 | **YES** |
| tool names (set) | `browser_*(10)`, `clarify`, `cronjob`, `delegate_task`, `delegate_worker`, `execute_code`, `memory`, `patch`, `process`, `read_file`, `search_files`, `session_search`, `skill_manage`, `skill_view`, `skills_list`, `terminal`, `text_to_speech`, `todo`, `vision_analyze`, `write_file` | identical set | **YES** |
| `system_prompt` length | 36165 | 36165 | **YES** |
| `message_count` | 23 | 13 | diff (outcome) |

| Field | r7_T4 (010641) | r72_T4 (141126) | match? |
|---|---|---|---|
| `model` | gemma-4-31b-it-4bit | gemma-4-31b-it-4bit | **YES** |
| `base_url` | http://10.211.55.2:8000/v1 | http://10.211.55.2:8000/v1 | **YES** |
| `platform` | cli | cli | **YES** |
| `tools` count | 29 | 29 | **YES** |
| tool names | identical set | identical set | **YES** |
| `system_prompt` length | 36165 | 36165 | **YES** |
| `message_count` | 12 | 10 | diff (outcome) |

Model/endpoint/platform/tool-set is identical across all four. No tool was added, removed, or renamed between r7 and r7.2. System-prompt length is byte-identical (36165 in all four) — suggestive of identical HERMES.md content.

---

## 3. System prompt byte-diff

md5 per session:
- r7_T4  `ff0d0819ddf5875aabc904177789d3c4`
- r7_T5  `31dc11f434b9dff84dd1860e25d0ed0a`
- r72_T4 `c94dd12c14934d6623f6070edbbc6473`
- r72_T5 `bee8added04a716b0c5be10b0e2d5604`

All four differ — but `difflib.unified_diff` at the line level shows a **single** changed line (line 461) per pair:

```
--- r7_T5 (01:24)
+++ r72_T5 (14:18)
@@ -461,3 +461,3 @@
-Conversation started: Saturday, April 18, 2026 01:24 AM
+Conversation started: Saturday, April 18, 2026 02:18 PM
 Model: gemma-4-31b-it-4bit
```

The same one-line delta (timestamp header only) is the only difference for all three pairs I diffed:
- r7_T5 vs r72_T5 → 1 line, timestamp only
- r7_T4 vs r72_T4 → 1 line, timestamp only
- r7_T4 vs r7_T5  → 1 line, timestamp only (same night, 18 min apart)
- r72_T4 vs r72_T5 → 1 line, timestamp only (same session, 7 min apart)

**Verdict: the system prompt is functionally byte-identical across r7 and r7.2 v2.** HERMES.md did not drift. The only runtime-injected variance is the wall-clock timestamp, which Hermes injects on each session start.

This rules out "HERMES.md was edited between runs" as a cause.

---

## 4. Tool schema diff — `delegate_worker`

The `delegate_worker` schema is **byte-identical across all four sessions** (sorted-JSON md5 `5bbcf945d9bf5ce7b2d716622ac7ecca`, length 1040).

Verbatim (from r72_T4, matches r7_T5 byte-for-byte):

```json
{
  "type": "function",
  "function": {
    "name": "delegate_worker",
    "description": "Spawn ONE worker subagent to complete a task in an isolated, fresh context. The worker has its own conversation, terminal, and toolset; only the final summary is returned to you.\n\nALWAYS USE THIS TOOL when the task class is `structured` or `long-horizon`. Do NOT call patch, write_file, terminal, execute_code, or skill_manage directly from the main session for such tasks — dispatch to a worker via this tool instead.\n\nPass everything the worker needs in the single `goal` argument — the worker has no memory of your conversation. Include: what to do, which files matter, what constraints apply, and what 'done' looks like. Be specific and self-contained.",
    "parameters": {
      "type": "object",
      "properties": {
        "goal": {
          "type": "string",
          "description": "Self-contained task description for the worker. Include all necessary context: file paths, constraints, success criteria. The worker knows nothing about your conversation."
        }
      },
      "required": ["goal"]
    }
  }
}
```

**Verdict: tool surface is byte-identical.** The registered schema has not changed between r7 and r7.2 v2.

---

## 5. First assistant message diff

All four first-assistant messages emit the mandatory `[TASK CLASS: structured]` marker in the first line with a plausible justification paragraph. `reasoning_content` is empty in all four (Gemma doesn't emit a reasoning channel). `finish_reason` on first-asst: `None` (r7_T4) / `tool_calls` (r7_T5, r72_T4, r72_T5).

**Task 5 pair (same user prompt, same marker structure):**

```
r7_T5 (dispatched at runtime, session truncated):
[TASK CLASS: structured]
Justification: The task involves debugging an intermittent race condition or caching issue across multiple files (frontend state vs. backend persistence) and requires a separate verification step to ensure the fix is robust.

I'll start by investigating the current data flow between the Save action and the dashboard refresh.
  → tool_call[0]: terminal(find /media/psf/Projects/chief-of-staff-dashboard -maxdepth 3 -type d)
```

```
r72_T5 (role-collapsed, never dispatched):
[TASK CLASS: structured]
Justification: This is an intermittent race condition involving state synchronization between a frontend (React/Vite) and a backend/API, requiring hypothesis testing and verification.

I'll start by orienting myself with the current dashboard codebase to understand how the "Save" operation and data fetching are implemented.
  → tool_call[0]: terminal(ls -R /media/psf/Projects/chief-of-staff-dashboard/src)
```

Both say essentially: `[marker]` + `I'll start by [investigating/orienting]` + `→ terminal(...)`. The first tool in BOTH Task 5 sessions is `terminal` — **the r7_T5 parent did NOT dispatch first either**. Per ARTIFACT-probe-variantE-trials.md §2, r7_T5 is listed as "persisted session shows NO_DISPATCH" with a `[terminal, search_files, search_files, read_file, search_files×5, read_file, read_file]` tool sequence — identical failure mode to r72_T5.

**Task 4 pair:**

```
r7_T4 (NO_DISPATCH A0, rescued on A3):
[TASK CLASS: structured]
Justification: The task requires modifying three separate files and necessitates a verification step (running tests) to ensure no regressions.

I will now orient myself by inspecting the current implementation of the auth module and the new session store.
  → tool_call[0]: terminal(ls -R src/auth tests/auth.test.ts)
```

```
r72_T4 (DISPATCHED first-attempt):
[TASK CLASS: structured]
Justification: The task requires modifying three separate files and verifying the results against an existing test suite, necessitating a structured plan and verification loop.

I'll start by orienting myself with the current implementation of the auth module and the new session store.
  → tool_call[0]: delegate_worker(goal="Analyze the current implementation of src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts...")
```

The marker text is essentially interchangeable between the two. The preamble phrasing is near-identical ("orient myself by/with… current implementation"). **The only session-JSON-visible difference that predicts dispatch-vs-collapse is the tool-call choice itself.** Gemma commits to either `delegate_worker` or `terminal` in the very first action.

---

## 6. Tool-call sequence diff

### Task 5 pair

**r7_T5 (23 msgs, parent truncated during actual runtime dispatch):**
```
[0] USER  dashboard stale-data prompt
[1] ASST  terminal(find … -maxdepth 3 -type d)
[3] ASST  search_files(pattern="save", target="content")
[5] ASST  search_files(pattern="save", target="content", path=/media/psf/…)
[7] ASST  read_file(/media/psf/…/TaskDetailPanel.tsx)
[9] ASST  search_files(pattern="onUpdate")
[11] ASST search_files(pattern="TaskDetailPanel", files)
[13] ASST search_files(pattern="TaskDetailPanel", content)
[15] ASST search_files(pattern="TaskDetailPanel", files, path=.../src)
[17] ASST search_files(pattern="TaskDetailPanel", content, path=.../src)
[19] ASST read_file(App.tsx)
[21] ASST read_file(useDashboard.ts)
  -- session truncated here; stdout confirms a `delegate_worker` fire happened AFTER msg 22, but it never landed on disk before SIGTERM
```

**r72_T5 (13 msgs, role-collapsed, no truncation — clean termination):**
```
[0] USER  dashboard stale-data prompt
[1] ASST  terminal(ls -R /media/psf/Projects/chief-of-staff-dashboard/src)
[3] ASST  read_file(lib/api.ts)
[5] ASST  read_file(components/tasks/TaskForm.tsx)
[7] ASST  read_file(hooks/useDashboard.ts)
[9] ASST  read_file(components/tasks/TaskDetailPanel.tsx)
[11] ASST read_file(App.tsx)
[12] TOOL
  -- run ended (hit budget/turn limit), last finish_reason=tool_calls with empty content
```

Both sessions' early-message patterns are the same failure mode: orient-with-terminal → widen-with-search/read_file → accumulate context in main session instead of dispatching. The r7_T5 session happens to have 10 more messages before being truncated, but NONE of those 22 on-disk messages is a `delegate_worker` call.

### Task 4 pair

**r7_T4 Smoke 2 (12 msgs, NO_DISPATCH on A0, dispatched later on A3 via a separate session):**
```
[0] USER  auth refactor prompt
[1] ASST  terminal(ls -R src/auth tests/auth.test.ts)         -- fails, no such dir
[3] ASST  search_files(session.ts) + search_files(middleware.ts) + search_files(auth.test.ts)   (parallel)
[7] ASST  text only: "Cannot find files, asks user for guidance" (finish=stop)
[8] USER  structural nudge: "You classified structured but did not dispatch…"
[9] ASST  delegate_worker(goal="Refactor auth module…")   ← retry nudge worked
[10] TOOL result
[11] ASST text final (finish=stop, content_len=395)
```

**r72_T4 (10 msgs, DISPATCHED first-attempt):**
```
[0] USER  auth refactor prompt
[1] ASST  delegate_worker(goal="Analyze the current implementation of src/auth/session.ts…")  ← IMMEDIATE dispatch
[2] TOOL  worker result
[3] ASST  search_files(session)   ← main session DID try to verify on its own after worker returned "can't find"
[5] ASST  search_files(auth)
[7] ASST  terminal(find . -maxdepth 4 -name "*auth*" -o -name "*session*")
[9] ASST  text final (finish=stop, "Could you double-check the paths?")
```

r72_T4 is the ONLY session of the four where the **first** tool call is `delegate_worker`. In the other three it is `terminal`.

---

## 7. Behavioral signal — the dispositive observation

**There is no detectable session-JSON-level difference that predicts dispatch vs collapse.** Specifically:

1. `model`, `base_url`, `platform`, `tools` (29 tools, identical set, identical `delegate_worker` schema byte-for-byte) — all identical.
2. `system_prompt` — byte-identical except a single timestamp-header line. No drift in HERMES.md content.
3. First-assistant `content` — the `[TASK CLASS: structured]` marker, the justification paragraph, and the "I'll start by orienting myself with..." preamble are stylistically interchangeable between dispatched and collapsed sessions.
4. `reasoning_content` — empty in all four; Gemma does not expose internal reasoning.
5. `finish_reason` on first-asst — `tool_calls` in three of four, `None` in the Smoke-2 A0 (which also happens to be a collapse).

The only predictive difference is **which tool Gemma emits at `tool_calls[0]`**:
- Dispatched → `delegate_worker`
- Collapsed → `terminal` (followed by search_files / read_file chains)

This choice appears to be a pure generation-sampling event. By the time the first tool call lands in the session JSON, the path is already fixed. There is no upstream signal in the prompt, tool surface, or prior messages that changed between the "dispatched" and "collapsed" runs. Given identical inputs and identical tool surface, the outcome is gated on whatever Gemma decodes for the function-calling token at the start of its first tool-use turn.

This matches what the r7 probe already observed:
- Variant D (r7, `delegate_worker` scaffolded, no retry) dispatched 2/5 (40%) on the same prompts.
- Variant E (r7, scaffolded + retry) persisted-session dispatch was 3/5 (60%).
- r7.2 v2 (today) is 1–2/5 (~20–40%).

The 40–60% range brackets an inherently stochastic event, and today's 20–40% is a sample-size fluctuation around the same underlying mean — not a new regression.

Critically: **the r7 Task 5 parent session I compared against actually shows the SAME NO_DISPATCH failure mode on disk as r7.2 v2 Task 5.** The only reason Trial 5 is counted as "dispatched" in the r7 probe is that the stdout captured a `delegate_worker` fire that happened AFTER the session JSON I examined was truncated by SIGTERM. Session-JSON-persisted dispatch is actually no better in r7 than in r7.2 on this specific task.

---

## 8. Ranked hypotheses

### H1 — Stochastic sampling variance; no drift. (MOST PLAUSIBLE)
**Evidence:**
- System prompt byte-identical (modulo timestamp).
- Tool surface (29 tools, `delegate_worker` schema) byte-identical.
- Model ID identical (`gemma-4-31b-it-4bit`).
- First-assistant content/marker structure is interchangeable between dispatched and collapsed sessions.
- The ONLY session-level difference that predicts outcome is `tool_calls[0].name`, which is the very thing we're trying to explain.
- r7's sample-size was 5 structured trials per variant; 3/5 vs 2/5 vs 1/5 are all within binomial noise for a Bernoulli process with p≈0.3–0.5.
- r7_T5's on-disk session shows IDENTICAL failure mode to r72_T5 (terminal-first, read_file chain, never dispatches). Only stdout logging and session-JSON-truncation accounting makes r7_T5 look like a "win" in the scoreboard.

**What this hypothesis implies:** there is no drift to fix. The observed 1/5 → 3/5 → 1/5 swing across runs is sample-size noise on a stochastic dispatch decision, not a regression in the harness.

### H2 — Upstream model-server difference (sampling params, quantization, or softmax temperature) not visible in the session JSON.
**Evidence:**
- Session JSON records no `temperature`, `top_p`, `top_k`, or `max_tokens` used for the assistant call. These live in the client/oMLX config.
- If oMLX or Hermes client changed a sampling parameter between r7 and r7.2 runs, the resulting distribution over first-tool choice could shift.
- Worker α is investigating oMLX-side; worker δ is investigating sampling. If either finds a param drift, it would explain the rate change without needing to invoke randomness.

**Counter-evidence:** session-JSON byte-identity of `system_prompt` and `tools` is consistent with "client request shape unchanged." If a temperature or `tools` serialization changed, we'd expect to see it here. My evidence says client→server payload is identical modulo timestamp.

### H3 — Task-5-specific prompt pathology (terminal-first bias on "dashboard" tasks)
**Evidence:**
- Of the 4 sessions inspected, the only `delegate_worker`-first session is Task 4 (auth refactor).
- Both Task 5 (dashboard) sessions — r7 and r7.2 — start with `terminal`.
- "The dashboard sometimes shows stale data…" may prime the model toward a find/grep orientation pattern more strongly than the auth-refactor prompt does.
- This is consistent with r7 probe finding that Task 5 is repeatedly the hardest dispatch case across variants.

**Counter-evidence:** explains per-task variance but not per-run variance. Doesn't account for r7 Trial 5 (Variant D, same task) dispatching immediately on that run.

### H4 — Context/memory poisoning across sessions (unlikely, worker γ domain)
**Evidence for:** None in session JSON — each session is initialized fresh with the same system prompt.
**Evidence against:** No memory or session_search tools are active in any of the four first-asst tool_calls. The model has no access to cross-session state at turn 1.

### H5 — HERMES.md content drift (RULED OUT)
system_prompt is byte-identical across runs modulo one timestamp line. HERMES.md has not been edited between r7 (01:24) and r7.2 v2 (14:18).

---

## 9. Proposed experiments

1. **Tight A/B against the stochastic hypothesis.** Run the same Task 5 prompt 20 times back-to-back today (no HERMES.md swap, no config change). If dispatch rate ≈ 30–50%, H1 is confirmed — there is no regression to fix, only a sample-size problem. Worker δ's sampling work should cover this.

2. **Pin `temperature` to 0** (or the lowest oMLX permits) for one run of 5 structured trials. If dispatch rate jumps deterministically one way or the other (either 0/5 or 5/5), it confirms the outcome is driven by logits near the decision boundary rather than by prompt/tool content. If it stays mid-range, something else is in play.

3. **Replay identical session seeding.** Capture a session that dispatched first-attempt (r72_T4, `141126_4fe2e2.json`) and replay its exact first-asst request payload (system_prompt + user msg + tools) through the oMLX endpoint 20 times. Count `tool_calls[0].name`. This isolates model-server variance from Hermes client variance.

4. **Instrument sampling params in session JSON.** Add `request_params` (temperature, top_p, seed if any) to the persisted session. Next time we see a drift claim, this diff will be conclusive in seconds instead of taking a forensic pass.

5. **Task-5-specific probe.** Rerun Task 5 only, 10x, and score `tool_calls[0]`. If it's consistently `terminal`, the prompt has a strong terminal-first bias that scaffolding alone cannot fix — the fix is prompt-engineering on HERMES.md to demote `terminal` as first-action for structured tasks (the description already says "Do NOT call … terminal … directly from main session" but `terminal` is not listed explicitly in the delegate_worker description's forbid-list as strongly as patch/write_file/execute_code/skill_manage). Worth tightening that wording.

---

## Appendix — session paths (absolute)

- `/home/parallels/.hermes/sessions/session_20260418_010641_d07074.json` — r7 Variant E Trial 4 Smoke 2 (A0 NO_DISPATCH)
- `/home/parallels/.hermes/sessions/session_20260418_012437_fce8fb.json` — r7 Variant E Trial 5 (parent truncated; on-disk shows NO_DISPATCH, stdout shows dispatch fired post-truncation)
- `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json` — r7.2 v2 Trial 4 (DISPATCHED first-attempt)
- `/home/parallels/.hermes/sessions/session_20260418_141857_848189.json` — r7.2 v2 Trial 5 (role-collapsed, clean termination)

Supporting artifact:
- `/Users/briantaylor/Projects/AgentFW/archive/hermes-probe-r7-2026-04-18/ARTIFACT-probe-variantE-trials.md`
- `/Users/briantaylor/Projects/AgentFW/archive/hermes-probe-r7-2026-04-18/ARTIFACT-probe-variantD-trials.md`
