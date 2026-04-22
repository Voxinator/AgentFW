# ARTIFACT — Drift Step A Re-tally (r7 vs r7.2 v2, strict persisted-JSON criterion)

**Worker:** Step-A re-tally worker (read-only).
**Date:** 2026-04-17.
**Scope:** Re-tally r7 Variant E structured/long-horizon trials (Tasks 4, 5, 6, 9, 10) and r7.2 dense v2 structured/long-horizon trials (same tasks) under a strict on-disk-session-JSON criterion, to determine whether r7's claimed "3/5 first-attempt, 4/5 final" dispatch rate was a bookkeeping artifact of the wrapper's stdout-based detection counting SIGTERM-truncated dispatches that never persisted.

---

## 1. Method

### Strict criterion

For each trial's parent session JSON at `/home/parallels/.hermes/sessions/session_<id>.json`:

- **Strict first-attempt dispatch:** extract the first assistant message; read `tool_calls[0].function.name`. If the value is `delegate_worker` or `delegate_task`, count as dispatched-first-attempt. Anything else (including `terminal`, `read_file`, `search_files`, `patch`, `todo`, `cronjob`, `skill_view`, or an assistant message with no `tool_calls`) does **not** count.
- **Strict final dispatch:** scan every assistant message in the persisted session; if any assistant message has a `tool_calls` entry whose `function.name` is `delegate_worker` or `delegate_task`, count as dispatched-final. Otherwise does not count.

This is strictly a persisted-JSON measurement. Stdout markers such as `🔀 preparing delegate_worker…` are explicitly ignored — the whole point of the re-tally is to set aside the stdout-based wrapper bookkeeping and look only at what survived to disk.

### Session identification strategy

**r7 Variant E:** sessions are listed by SHA-suffix in `/Users/briantaylor/Projects/AgentFW/archive/hermes-probe-r7-2026-04-18/ARTIFACT-probe-variantE-trials.md` §7 "Raw scoring inputs." I used the session IDs there directly and confirmed each one is the parent (not a worker) by inspecting the first user message — parents carry the original probe-tasks.md prompt wording; workers carry the delegated goal string.

**r7.2 v2:** sessions are listed in `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense-v2.md` §Run log and §Session ownership table. Trial 5's wrapper recovered the wrong (child) session; the artifact identifies `20260418_141857_848189` as the actual parent, so I used that — but I also sanity-checked the recovered-child `_142132_505637`. Both agree on no delegate_* call.

### Tooling

Sessions copied locally from `parallels@ubuntu-vm:/home/parallels/.hermes/sessions/` via scp. Tally script: `/tmp/drift-step-a/tally.py` — pure JSON parser, no heuristics, no stdout parsing.

---

## 2. Session identification per r7 trial

| Task | Class (truth) | Parent session | On-disk? | How found |
|------|---------------|----------------|----------|-----------|
| 4 | structured | `session_20260418_010641_d07074.json` | yes (95 KB) | r7 artifact §7 |
| 5 | structured | `session_20260418_012437_fce8fb.json` | yes (184 KB — truncated mid-turn) | r7 artifact §7 |
| 6 | long-horizon | `session_20260418_013007_190a6c.json` | yes (180 KB — truncated mid-turn) | r7 artifact §7 |
| 9 | structured | `session_20260418_013709_8c521e.json` | yes (123 KB) | r7 artifact §7 |
| 10 | long-horizon | **NOT ON DISK** | **no** | r7 artifact §7 says "parent JSON not persisted." Confirmed: `ls /home/parallels/.hermes/sessions/ \| grep 20260418_014` returns only `session_20260418_014050_509ee2.json`, which is the **worker** session (first user message is the Postgres-discovery delegated goal, not the task-10 prompt). |

Trial 10's missing parent is itself load-bearing: it means the wrapper's stdout-detected dispatch for Trial 10 cannot be reconciled against on-disk state at all. Under the strict criterion, "no parent on disk" must count as NOT-dispatched (we have no evidence of a persisted delegate_* call on the parent session because the parent session does not exist).

---

## 3. Strict r7 table (r7 Variant E structured/long-horizon, Tasks 4/5/6/9/10)

| Task | Class | r7 session | First-tool-call in parent | First-attempt dispatch (strict) | delegate_* count anywhere in session | Final dispatch (strict) | Original r7 artifact scoring |
|------|-------|-----------|---------------------------|----------------------------------|---------------------------------------|-------------------------|--------------------------------|
| 4 | structured | `010641_d07074` | `terminal` | **NO** | 1 (`delegate_worker` at assistant turn 3, after A3 retry) | **YES** | first-attempt NO, final YES (rescued A3) — matches |
| 5 | structured | `012437_fce8fb` | `terminal` | **NO** | 0 | **NO** | first-attempt runtime "YES" (stdout), persisted NO — r7 artifact already acknowledged persisted=0 |
| 6 | long-horizon | `013007_190a6c` | `terminal` | **NO** | 0 | **NO** | first-attempt runtime "YES" (stdout), persisted NO — same as Trial 5 |
| 9 | structured | `013709_8c521e` | `cronjob` | **NO** | 0 | **NO** | first-attempt NO, final NO (retry exhausted) — matches |
| 10 | long-horizon | **parent absent** | n/a | **NO** (no parent session exists) | n/a (parent absent) | **NO** (no parent session exists) | first-attempt runtime "YES" (stdout + worker session), persisted n/a — the runtime YES is what's at issue here |

**Strict tally:**
- First-attempt dispatch on structured/LH: **0/5** (vs r7 claimed 3/5 under runtime-truth method)
- Final dispatch on structured/LH: **1/5** (vs r7 claimed 4/5 under runtime-truth method) — only Trial 4 has a persisted delegate_* call

---

## 4. Strict r7.2 v2 table (sanity check, same 5 tasks)

| Task | Class | r7.2 v2 session | First-tool-call in parent | First-attempt dispatch (strict) | delegate_* count anywhere in session | Final dispatch (strict) | Reported in r7.2 v2 artifact |
|------|-------|-----------------|---------------------------|----------------------------------|---------------------------------------|-------------------------|-------------------------------|
| 4 | structured | `141126_4fe2e2` | `delegate_worker` | **YES** | 1 | **YES** | COMPLIANT, first-call delegate_worker — matches |
| 5 | structured | `141857_848189` (actual parent) | `terminal` | **NO** | 0 | **NO** | RETRY_EXHAUSTED NO_DISPATCH — matches |
| 6 | long-horizon | `143639_c0e074` | `terminal` | **NO** | 0 | **NO** | RETRY_EXHAUSTED NO_DISPATCH, write_file before dispatch — matches |
| 9 | structured | `145925_118829` | `cronjob` | **NO** | 0 | **NO** | RETRY_EXHAUSTED NO_DISPATCH, skill_manage before dispatch — matches |
| 10 | long-horizon | `150708_06e953` | `search_files` | **NO** | 2 (`delegate_worker`×2 at later turns, after A1 correction) | **YES** | COMPLIANT after A1 correction — matches |

**Strict tally (r7.2 v2):**
- First-attempt: **1/5** (Trial 4 only) — **matches reported 1/5**
- Final: **2/5** (Trials 4, 10) — **matches reported 2/5**

The r7.2 v2 sanity check passes cleanly. This validates the strict criterion is internally consistent and that the r7.2 v2 artifact scored itself honestly against the persisted-JSON measurement.

---

## 5. Headline numbers

| Measurement | r7 (claimed) | r7 (strict, this re-tally) | r7.2 v2 (reported) | r7.2 v2 (strict, this re-tally) |
|-------------|--------------|----------------------------|--------------------|---------------------------------|
| First-attempt dispatch on structured/LH | 3/5 (60%) | **0/5 (0%)** | 1/5 (20%) | 1/5 (20%) — matches |
| Final dispatch on structured/LH | 4/5 (80%) | **1/5 (20%)** | 2/5 (40%) | 2/5 (40%) — matches |

Under the strict criterion, r7 scored **worse** than r7.2 v2, not better. The "3/5 first-attempt" claim rests entirely on (a) stdout markers (`🔀 preparing delegate_worker…`) for Trials 5, 6, and 10, and (b) the existence of worker-session JSONs with the delegated goal as their first user message. Neither of those is a persisted delegate_* tool call on the parent session. Three of those three "runtime dispatches" were SIGTERM'd before the parent could flush, and one (Trial 10) lost the entire parent session.

The r7 artifact is internally honest about this — §5 Anomaly A explicitly states "Persisted-dispatch rate (what the check script sees): 1/5 = 20%" and warns the persisted measurement understates runtime behavior. The r7 headline rolled up under "runtime-truth," which credits stdout + worker-session existence as dispatch evidence. Under strict persisted-JSON measurement (the r7.2 v2 method), the gap flips.

---

## 6. Verdict

**CONFIRMED ARTIFACT.**

r7 strict first-attempt = **0/5**, which is ≤ 2/5 and in fact **lower than r7.2 v2's 1/5**. The hypothesis that r7's claimed 3/5 first-attempt was a wrapper-SIGTERM bookkeeping artifact is confirmed — decisively. When measured with the same strict persisted-JSON criterion used for r7.2 v2, r7 does not outperform r7.2; it underperforms it.

Specifically:
- All three of r7's "first-attempt runtime dispatches" (Trials 5, 6, 10) have **zero** delegate_* tool calls in their persisted parent sessions. Trial 10 has no parent session at all.
- The only strict-counted dispatch on r7 is Trial 4, which required three NO_DISPATCH retries before landing. Under the strict first-attempt criterion, even that one doesn't count toward first-attempt — its first tool was `terminal`.
- r7.2 v2's Trial 4, by contrast, had `delegate_worker` as the literal first tool call — a cleaner first-attempt dispatch than anything r7 persisted on disk.

The "drift" between r7 (claimed 3/5) and r7.2 v2 (measured 1/5) is not a real behavioral regression. It is a measurement-method discrepancy: r7's wrapper counted stdout-emitted but SIGTERM-truncated dispatches; r7.2 v2's strict measurement did not. Under a common strict metric, both runs look similar (r7.2 v2 is actually 1 trial better first-attempt and 1 trial better final).

**No cache-flush experiment is needed.** The perceived drift dissolves once the measurement is harmonized.

---

## 7. Implications for documentation

These files contain text that becomes misleading once the artifact above is taken as ground truth. I did not modify them — parent decides timing and exact wording.

### `/Users/briantaylor/Projects/AgentFW/archive/hermes-probe-r7-2026-04-18/ARTIFACT-probe-variantE-trials.md`

- §5 headline table, rows "First-attempt runtime dispatch on structured/long-horizon: 3/5 = 60%" and "Final runtime dispatch (after retries): 4/5 = 80%" — these rely on the "runtime-truth" measurement (stdout + worker-session existence). Under strict persisted-JSON measurement they are 0/5 and 1/5. Recommend keeping the runtime-truth rows but **adding** a persisted-strict row and an explicit note that cross-run comparisons with r7.2+ must use the strict method.
- §8 Closing observations #1 "Variant E's first-attempt dispatch rate improved over Variant D (60% vs 40%) under runtime-truth measurement" — this comparison is only valid within the runtime-truth framework. Needs a footnote that under persisted-strict, the same row flips.
- §8 Closing observation #8 "Recommendation for scoring this variant: Judge against the runtime-truth table (§7 "Runtime-truth measurement"), not the persisted-session table" — this recommendation should be **reversed** now that r7.2+ uses persisted-strict scoring. Otherwise r7 and r7.2 are being graded on incompatible rubrics and any cross-run comparison is meaningless.

### `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense-v2.md`

- Any sentence implying r7 had a real 3/5 first-attempt that r7.2 v2 regressed from should be softened. The correct framing: r7.2 v2 did not regress from r7; r7's earlier number was an artifact of looser scoring. Left as-is, readers may believe there is a real tuning regression where there is none.

### `/Users/briantaylor/Projects/AgentFW/PLAN-r7-opus47-tuning.md` and `PLAN-r7.md` (if applicable)

- Any "next steps" item proposing a cache-flush experiment or r7.2 regression investigation motivated by the apparent drift should be deprioritized or rewritten. The drift is not real.

### NEXT-STEPS (if such a file exists)

- I did not locate a top-level NEXT-STEPS.md or PROBE-RESULTS-r7.md by name in the listings I ran, so I cannot speak to specific text there. If those files do exist and repeat the 3/5 / 4/5 framing, they need the same correction.

---

## Appendix A — Raw strict-tally output

```
=== r7 ===
session_20260418_010641_d07074.json (Trial 4)
  assistant messages: 5
  first tool call:    terminal
  first is delegate:  False
  any delegate call:  True
  total tool calls:   5
  tool sequence: [terminal, search_files, search_files, search_files, delegate_worker]

session_20260418_012437_fce8fb.json (Trial 5)
  assistant messages: 11
  first tool call:    terminal
  first is delegate:  False
  any delegate call:  False
  total tool calls:   11
  tool sequence: [terminal, search_files, search_files, read_file, search_files×5, read_file, read_file]

session_20260418_013007_190a6c.json (Trial 6)
  assistant messages: 6
  first tool call:    terminal
  first is delegate:  False
  any delegate call:  False
  total tool calls:   6
  tool sequence: [terminal, search_files, todo, search_files, read_file, read_file]

session_20260418_013709_8c521e.json (Trial 9)
  assistant messages: 11
  first tool call:    cronjob
  first is delegate:  False
  any delegate call:  False
  total tool calls:   7
  tool sequence: [cronjob, skill_view, terminal, read_file, terminal, terminal, terminal]

(Trial 10 parent: not on disk)

=== r7.2 v2 ===
session_20260418_141126_4fe2e2.json (Trial 4)
  assistant messages: 5
  first tool call:    delegate_worker
  first is delegate:  True
  any delegate call:  True
  total tool calls:   4
  tool sequence: [delegate_worker, search_files, search_files, terminal]

session_20260418_141857_848189.json (Trial 5 actual parent)
  assistant messages: 6
  first tool call:    terminal
  first is delegate:  False
  any delegate call:  False
  total tool calls:   6
  tool sequence: [terminal, read_file×5]

session_20260418_142132_505637.json (Trial 5 wrapper-recovered child)
  assistant messages: 8
  first tool call:    todo
  first is delegate:  False
  any delegate call:  False
  total tool calls:   13
  tool sequence: [todo, read_file×2, search_files×2, terminal×7]

session_20260418_143639_c0e074.json (Trial 6)
  assistant messages: 8
  first tool call:    terminal
  first is delegate:  False
  any delegate call:  False
  total tool calls:   8
  tool sequence: [terminal, search_files, read_file×2, todo, read_file, todo, write_file]

session_20260418_145925_118829.json (Trial 9)
  assistant messages: 16
  first tool call:    cronjob
  first is delegate:  False
  any delegate call:  False
  total tool calls:   12
  tool sequence: [cronjob, skill_view, terminal×7, skill_manage, cronjob×2]

session_20260418_150708_06e953.json (Trial 10)
  assistant messages: 8
  first tool call:    search_files
  first is delegate:  False
  any delegate call:  True
  total tool calls:   6
  tool sequence: [search_files×2, terminal×2, delegate_worker×2]
```

Tally script: `/tmp/drift-step-a/tally.py` (ephemeral; re-runnable by scp'ing session JSONs back and rerunning).
