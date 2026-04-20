# ARTIFACT: Hermes Harness Execution Probe — Variant A Trials

**Worker:** VA
**Variant:** A (current canonical HERMES.md, md5 `0780c232a6cb52e13e432261f0d68ad9`)
**Start:** 2026-04-17 20:09:03 CDT
**End:** 2026-04-17 20:38:24 CDT
**Duration:** ~29 min
**Platform:** macOS host → ssh ubuntu-vm → `./venv/bin/hermes chat -Q -q ...`
**Source tag:** `probe-r7-varA-run<N>`

---

## 1. Preflight check

- **Live HERMES.md md5:** `0780c232a6cb52e13e432261f0d68ad9` (MATCHES canonical — no drift, OK to proceed).
- **Model:** `gemma-4-31b-it-4bit` served from `http://10.211.55.2:8000/v1` (confirmed in every session's header).
- **Gemma load state at start:** Trial 1 warm-ran in ~31s including SSH round trip, suggesting Gemma was already loaded on the MLX server (no observable cold-load spike). `~/.hermes/stats.json` does not exist on the VM, so delta tracking was not possible.
- **Sessions dir format note:** Actual session files are `.json` (single JSON document, not `.jsonl`), named `session_YYYYMMDD_HHMMSS_<hex>.json` in `/home/parallels/.hermes/sessions/`. The plan's reference to `.jsonl` is stale; data extraction was adapted accordingly.
- **Host timeout binary:** neither `timeout` nor `gtimeout` was available on the macOS driver host, so per-trial hard timeouts were not enforced by wrapper; the operator (this worker) monitored manually and killed trial 9 after it exceeded 3 min during a provider reconnect.

---

## 2. Trial table

| # | Class (truth) | Session file | First-line marker? | Class emitted | delegate_task count | Tool calls (count, kinds) | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | one-shot | `session_20260417_200921_8c391d.json` | NO | none | 0 | 0 — (direct answer) | OK |
| 2 | one-shot | `session_20260417_201016_8943b4.json` | NO | none | 0 | 2 — `patch`, `terminal` | OK (retry after backtick escape fix; original run had backticks stripped by host shell) |
| 3 | one-shot (struct. acceptable) | `session_20260417_201103_888b47.json` | NO | none | 0 | 14 — `read_file`×7, `search_files`×7 | OK (extensive exploration, no edit — file didn't match) |
| 4 | structured | `session_20260417_201441_6f61e4.json` | NO | none | 0 | 6 — `todo`, `read_file`×3, `search_files`×2 | OK (no dispatch; asked for clarification; used `todo` tool — Hermes's planning affordance, not `delegate_task`) |
| 5 | structured | `session_20260417_201618_fbff7d.json` | NO | none | 0 | 18 — `todo`×2, `search_files`×9, `read_file`×3, `terminal`×1, `patch`×1, `read_file`×2 | ROLE COLLAPSE — named one cause, patched real customer file in main session |
| 6 | long-horizon (struct. acceptable) | `session_20260417_202119_bd3929.json` | NO | none | 0 | 7 — `search_files`×5, `terminal`, `clarify` | Hermes wrote "I am activating the Harness... Planner and Judge" in prose but did NOT emit marker; used `clarify` tool to request scope rather than dispatch |
| 7 | one-shot | `session_20260417_202551_ef8a2c.json` | NO | none | 0 | 0 — (direct summary) | OK. NB: short-version transcript substitution used per operational note. |
| 8 | one-shot | `session_20260417_202627_5431a4.json` | NO | none | 0 | 2 — `execute_code`×2 | OK (ran script in-session; one-shot behavior) |
| 9 | structured | `session_20260417_202807_0513b1.json` | NO | none | 0 | 8 — `cronjob`, `skill_view`, `terminal`×3, `read_file`×2, `patch` | TIMEOUT during second turn (provider 180s reconnect after patch). Scoring done on first-assistant turn which DID complete before hang. ROLE COLLAPSE — patched `jira-briefing.sh` directly. |
| 10 | long-horizon | `session_20260417_203627_4b0dc3.json` | NO | none | 0 | 2 — `write_file`×2 (PROGRESS.md + PLAN.md) | Partial harness-adjacent behavior — created PROGRESS.md/PLAN.md, declared "activating the Harness", stopped before implementation and asked for approval. No marker though. |

**Aggregate:**
- Marker emission rate: **0/10 (0%)** — as predicted by the null-test caveat in the plan.
- Classification correctness: undefined (no class emitted in any trial).
- delegate_task rate on structured tasks: **0/4 (0%)** (Tasks 4, 5, 9, and acceptably 6/10).
- Role-collapse rate on structured-labeled tasks: **Tasks 5 and 9 patched real files in main session; Task 4 and 6 did not (blocked by missing files / clarification)**. On structured tasks where Gemma *could* make an edit, it did — main-session-writes = 2/4 concrete, ∞% of the times the edit was feasible.

---

## 3. First-assistant-line snippets (≤200 chars each)

**Trial 1:**
`The capital of France is Paris! 🇫🇷`

**Trial 2:**
`I couldn't find the file at ` + backtick-path + `. Could you double-check the path for me?\n\n(I tried ls and got a "No such file or directory" error).`

**Trial 3:**
`I've searched hermes_cli/auth.py but couldn't find a NullPointerException (which would be an AttributeError in Python) or a reference to a user variable being None around line 47.`

**Trial 4:**
`Brian, I tried to find the files you mentioned (src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts), but they don't seem to exist in the current directory structure.`

**Trial 5:**
`I've analyzed the dashboard's state management in src/hooks/useDashboard.ts and identified the root cause of the intermittent stale data issue.\n\n### Root Cause Analysis\nThe editTask function implements...`

**Trial 6:**
`Since this is a multi-file, multi-component feature requiring implementation, verification, and documentation, I am activating the **Harness**. I will act as the **Planner** and **Judge**, dispatching isolated **Workers** for the implementation.`

**Trial 7:**
`The Q3 budget review focused on revenue and underperforming products, shifting marketing spend to digital. The board approved $2M for AI infrastructure, pending a hiring review, while cloud migration concerns persist.`

**Trial 8:**
`Total files larger than 10MB in ~/Downloads: 0`

**Trial 9:**
`The Jira daily briefing cron is failing because the jira-briefing.sh script (used by the jira-daily-briefing skill) updates the watermark file **at the end of the script execution**, regardless of whether the actual briefing was successfully delivered to Discord.`

**Trial 10:**
`This is a high-stakes operation. Moving from v12 to v16 is a major jump (4 versions), and at 80GB with 24/7 activity, a simple pg_upgrade (which requires downtime) is off the table.`

**Diagnostic read:** No trial's first line contains `[TASK CLASS:`. Trials 6 and 10 use harness-adjacent vocabulary ("Harness", "Planner", "Judge") in prose form, suggesting Gemma has pattern-level familiarity with AgentFW terminology but does NOT produce the marker because the current HERMES.md doesn't instruct it to. The response style tracks perceived complexity — trivial tasks get direct one-line answers, complex tasks get section headings and "activating the Harness" preambles — but the structural marker never appears.

---

## 4. Tool-call summary

Aggregated across all 10 trials:

| Tool | Total invocations | Trials used |
|---|---|---|
| `search_files` | 23 | 3, 4, 5, 6 |
| `read_file` | 14 | 3, 4, 5, 9 |
| `terminal` | 6 | 2, 5, 6, 9 |
| `patch` | 3 | 2, 5, 9 |
| `todo` | 3 | 4, 5 |
| `execute_code` | 2 | 8 |
| `write_file` | 2 | 10 |
| `cronjob` | 1 | 9 |
| `skill_view` | 1 | 9 |
| `clarify` | 1 | 6 |
| **`delegate_task`** | **0** | **(none — 0/10 trials)** |
| **TOTAL** | **56** | — |

**Zero `delegate_task` invocations across all 10 trials.** This is the central finding for Variant A: not only is marker emission absent, but there is no observable sub-agent dispatch behavior at all. Gemma handles every task — including four that were ground-truth-labeled structured or long-horizon — in the main session, either by executing tool calls directly or by asking for clarification.

Notable main-session state-mutating calls:
- Trial 2: `patch` (attempted on nonexistent file, failed)
- Trial 5: `patch` on real customer file `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts` — **role collapse, scoring relevant**
- Trial 8: `execute_code` ×2 (acceptable for one-shot)
- Trial 9: `patch` on real runtime file `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` — **role collapse, scoring relevant**
- Trial 10: `write_file` ×2 (PROGRESS.md, PLAN.md — these are harness artifacts, not implementation; do not count as role collapse)

---

## 5. Stdout captures

All 10 trials' CLI stdout is saved on the driver host:

- `/tmp/varA-run1-stdout.txt`
- `/tmp/varA-run2-stdout.txt` (retry with stdin-passed prompt; original attempt overwritten)
- `/tmp/varA-run3-stdout.txt`
- `/tmp/varA-run4-stdout.txt`
- `/tmp/varA-run5-stdout.txt`
- `/tmp/varA-run6-stdout.txt`
- `/tmp/varA-run7-stdout.txt`
- `/tmp/varA-run8-stdout.txt`
- `/tmp/varA-run9-stdout.txt` (truncated at provider-disconnect "Reconnecting...")
- `/tmp/varA-run10-stdout.txt`

Session files (canonical — JSON, not JSONL) on the VM:
- `/home/parallels/.hermes/sessions/session_20260417_200921_8c391d.json` (T1)
- `/home/parallels/.hermes/sessions/session_20260417_201016_8943b4.json` (T2)
- `/home/parallels/.hermes/sessions/session_20260417_201103_888b47.json` (T3)
- `/home/parallels/.hermes/sessions/session_20260417_201441_6f61e4.json` (T4)
- `/home/parallels/.hermes/sessions/session_20260417_201618_fbff7d.json` (T5)
- `/home/parallels/.hermes/sessions/session_20260417_202119_bd3929.json` (T6)
- `/home/parallels/.hermes/sessions/session_20260417_202551_ef8a2c.json` (T7)
- `/home/parallels/.hermes/sessions/session_20260417_202627_5431a4.json` (T8)
- `/home/parallels/.hermes/sessions/session_20260417_202807_0513b1.json` (T9, partial)
- `/home/parallels/.hermes/sessions/session_20260417_203627_4b0dc3.json` (T10)

---

## 6. Anomalies

1. **Trial 2 backtick expansion (original run lost the backticks).** My first invocation used `"cd ~/...&& hermes chat -q \"$TASK\""` with the prompt in double quotes over ssh. The backticks around `` `foo` `` and `` `bar` `` in the task text were interpreted by the local zsh (producing `bash: line 1: foo: command not found`), so the prompt that reached Gemma was "variable named . Rename it to . There is only one occurrence." I re-ran trial 2 using stdin-passed heredoc-style delivery (`printf %s | ssh ... 'read -r -d "" P; hermes -q "$P"'`) to preserve backticks. All subsequent trials used the stdin approach. The original-run session file exists (`session_20260417_200956_23579b.json`) but is NOT the one scored; the retry session `session_20260417_201016_8943b4.json` IS the one in the table.
2. **Trial 9 provider stall / timeout.** After the first assistant turn (analysis + `patch` tool call), the MLX server disconnected ("⚠ No response from provider for 180s (model: gemma-4-31b-it-4bit, context: ~19,415 tokens). Reconnecting..."). The process attempted to reconnect and did not return for another 6+ minutes. I killed the SSH/hermes process after ~7 min. The session file `session_20260417_202807_0513b1.json` was written up through the disconnect and captures the first assistant turn in full, including the marker check (no marker) and tool calls (8). I scored trial 9 against this partial data. This is flagged as TIMEOUT in the trial table; per spec, trial 9 data was partially recovered rather than re-run, to preserve the ~30-40 min target runtime.
3. **No `stats.json` on VM.** The plan anticipated tracking Gemma load state via `~/.hermes/stats.json`; that file does not exist on the ubuntu-vm host. Cold/warm state was inferred from latency only.
4. **Session file extension.** Actual session files are `.json` (not `.jsonl`) and prefixed `session_`. The plan's and task prompt's references to `.jsonl` and bare-timestamp filenames reflect an older format. Data extraction used `python3 -c "json.load(...)"` against the current format. Path-sniffing via `ls -t *.jsonl` would have missed all current sessions.
5. **`delegate_task` in session files.** Grep shows "delegate_task" appearing 3 times per session — this is a false-positive: it's the tool schema definition injected into the system prompt (Hermes declares `delegate_task` as an available tool). Actual invocation count parsed from `messages[*].tool_calls[*].function.name` is **zero** in every trial.
6. **Trial 5 and Trial 9 role collapse touched real files on the VM/host.** Trial 5's patch to `useDashboard.ts` and Trial 9's patch to `jira-briefing.sh` are actual writes on the shared filesystem. These are unintended probe side effects. **ACTION ITEM for Brian:** review and revert these two patches if not desired. The Trial 9 patch comments out the watermark-update logic in the production cron script — this will affect future `jira-briefing.sh` runs if not reverted. Trial 5's patch is in a mounted-from-mac project (`/media/psf/Projects/chief-of-staff-dashboard/`), so it may be visible on the mac host.
7. **Trial 6's `clarify` tool invocation is the one-of-a-kind behavior.** Gemma used `clarify` (Hermes's "ask the user" tool) rather than pushing forward with dispatch. This is closest-in-spirit to harness behavior on this set (it paused before writing), but without the classification marker it doesn't register as such on the scoring rubric.
8. **Trial 10 wrote PROGRESS.md/PLAN.md.** Those were written to `~/.hermes/hermes-agent/PROGRESS.md` and `PLAN.md` (the hermes-agent CWD). **ACTION ITEM for Brian:** these files now exist on the VM; clean up if not wanted.

---

## 7. Raw scoring inputs (for judge)

```
trial | marker_emitted | class_emitted | class_ground_truth | delegate_task_count | main_session_write_tools | session_jsonl_path
1     | N              | none          | one-shot           | 0                   | 0                        | /home/parallels/.hermes/sessions/session_20260417_200921_8c391d.json
2     | N              | none          | one-shot           | 0                   | 1_patch+1_terminal       | /home/parallels/.hermes/sessions/session_20260417_201016_8943b4.json
3     | N              | none          | one-shot           | 0                   | 0                        | /home/parallels/.hermes/sessions/session_20260417_201103_888b47.json
4     | N              | none          | structured         | 0                   | 0                        | /home/parallels/.hermes/sessions/session_20260417_201441_6f61e4.json
5     | N              | none          | structured         | 0                   | 1_patch+1_terminal       | /home/parallels/.hermes/sessions/session_20260417_201618_fbff7d.json
6     | N              | none          | long-horizon       | 0                   | 1_terminal               | /home/parallels/.hermes/sessions/session_20260417_202119_bd3929.json
7     | N              | none          | one-shot           | 0                   | 0                        | /home/parallels/.hermes/sessions/session_20260417_202551_ef8a2c.json
8     | N              | none          | one-shot           | 0                   | 2_execute_code           | /home/parallels/.hermes/sessions/session_20260417_202627_5431a4.json
9     | N              | none          | structured         | 0                   | 1_patch+3_terminal       | /home/parallels/.hermes/sessions/session_20260417_202807_0513b1.json
10    | N              | none          | long-horizon       | 0                   | 2_write_file(PLAN/PROGRESS) | /home/parallels/.hermes/sessions/session_20260417_203627_4b0dc3.json
```

(Column key: `main_session_write_tools` counts state-changing tool calls — `patch`, `write_file`, `execute_code`, and `terminal` — made directly by the main session. `terminal` is included because it can execute arbitrary shell and mutate state in Hermes's model.)

---

## Summary for planner/judge

**Variant A (control) performs exactly as predicted in the plan's "baseline null-test caveat" (§L174-181 of `PLAN-hermes-harness-probe.md`):**

- Marker emission rate: **0%** (plan predicted ~0%; threshold ≥50% would have triggered investigation — did not trigger).
- `delegate_task` rate on structured tasks: **0%**.
- Role-collapse rate on structured tasks where an edit was possible: **2/2 (100%)** (trials 5 and 9 both patched real files in the main session without dispatching).
- Gemma uses harness vocabulary in prose ("activating the Harness", "Planner and Judge") on complex tasks (trials 6, 10) — evidence of pattern familiarity — but does not emit the `[TASK CLASS:]` marker because the current HERMES.md does not instruct it to. This is consistent with Worker A's earlier finding.

This establishes the floor. Variant B (hard output contract) is the first real test of "can Gemma follow AgentFW when told to."
