[TASK CLASS: structured]
Justification: Multi-file read-only diagnostic with explicit verification deliverable, cross-source evidence chain, and recommendation section.

# ARTIFACT — r7.6-P1C Arm B EMPTY_SYNTHESIS diagnostic

**Author:** diag worker, fresh context, READ-ONLY scope.
**Date:** 2026-04-19, mid-probe (Arm B still running at T5-run5 at analysis time).
**Subjects:** armB-T4-run3 and armB-T5-run4 — two Arm B trials that SIGTERM'd at 900s, fallback-recovered a session, cycled through two EMPTY_SYNTHESIS verdicts, then finally flipped COMPLIANT at A2 with elapsed≈911-914s.

---

## 1. Root cause (one paragraph with citation)

**Same SIGTERM / parent-session-loss / mis-attachment cascade that r7.4 Phase D documented in `ARTIFACT-r7.4-phase-d-dense-results.md` lines 22-23 — but the regression is introduced by the Arm B wrapper fork.** The r7.5-B1 anti-child-attachment content-match check (which lives in `probe-variantH-wrapper.sh` lines 200-295) was DROPPED when `probe-variantI-wrapper.sh` was forked from `probe-variantF-wrapper.sh` (not from variantH) to add the `HERMES_WORKER_OVERLAY=1` env injection. Arm B runs `probe-variantI-wrapper.sh` (`/tmp/probe-r7.6-P1C-logs/run-arm.sh` line 18: `WRAPPER="/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh"`), which falls back to the legacy "most-recent-newer-than-sentinel" scan with NO prefix-match guard (`probe-variantI-wrapper.sh` lines 177-185). Because SIGTERM at 900s does not run Hermes' atexit-based session save, the legitimate parent session is orphaned. The fallback picks up some OTHER session file created during the same window — in both incidents, a spuriously-created "retry parent" session (`20260419_212256_d885e6` and `20260419_214432_52b6a8`) with channel-marker pollution and no real prompt content. The check script (variantH) correctly emits `VIOLATION:EMPTY_SYNTHESIS` against that polluted state (`probe-variantH-check.py` lines 280-386, `detect_empty_synthesis`). Correction turns A1/A2 then `--resume` into the recovered-but-empty file (stdout line 30 of `probe-r7.6-armB-T4-moe-run3-stdout.txt`: `"Session 20260419_212256_d885e6 found but has no messages. Starting fresh."`), which silently starts a fresh session under the same session-id, and the model then makes two `delegate_worker_v2` calls that succeed in shape even as they return an API error (`unhashable type: 'slice'`), so by A2 the check sees a v2 tool call with `classification="one-shot"` and non-empty apology prose, and returns COMPLIANT — a false COMPLIANT on a session that never dispatched the real task.

---

## 2. Is fallback mis-attaching? (explicit YES/NO)

**YES — but with a new twist.** This is the same Phase D bug, with a new flavor.

Evidence — the LEGITIMATE parent for armB-T4-run3 exists:

- Session `20260419_210911_3d6b66` (msg_count=3, dispatched at run3 start time ~21:09):
  - `messages[0].content[:200]`: `'Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. All existing tests must still pass after the refactor.'` — THIS IS THE TRIAL PROMPT.
  - `messages[1].role=assistant, content_len=0, tool_calls=['delegate_worker_v2']` with `classification='structured', goal='Refactor the auth module...'`
  - No further assistant messages (SIGTERM at 900s killed it before synthesis).

The session the wrapper actually recovered:

- Session `20260419_212256_d885e6` (msg_count=8 NOW, was polluted-partial at A0 check time):
  - `messages[0].content[:200]`: `'Your response did not meet the AgentFW β-fuse contract. Re-read HERMES.md and respond again, beginning with a \`delegate_worker_v2\` tool call...'` — THIS IS THE DEFAULT CORRECTION MESSAGE (from `probe-variantI-wrapper.sh` line 138, the `*)` fall-through branch of `correction_for`). It is NOT the trial prompt, NOT a delegated goal, and NOT even a child session in the traditional sense — it's a **fresh session created by hermes when A1's `--resume` opened an empty stub file**.

Same result for T5-run4: legitimate parent unknown to wrapper; recovered session `20260419_214432_52b6a8` has `messages[0]` = the default correction template.

**So this is worse than Phase D's flavor.** Phase D picked up the CHILD session (which at least contained the dispatched goal). P1C picks up a session whose content is the WRAPPER'S OWN CORRECTION MESSAGE — meaning the fallback is effectively picking up a session that was created in response to its own earlier pick-up. A second-order pathology.

**Why Arm A doesn't hit this:** Arm A trials never SIGTERM because the overlay is inactive → children complete faster → parent never dies (all Arm A T4/T5 elapsed 30-111s; all Arm B timeouts happen when elapsed hits 900s). See §5.

---

## 3. EMPTY_SYNTHESIS verdict mechanics

**Source:** `probe-variantH-check.py` is the active check script (per `probe-variantI-wrapper.sh` line 37-38: `CHECK_REMOTE="/tmp/probe-variantH-check.py"`). The check on the VM has md5 `9fea7cbe5862da92b0fdc94e43fec563` (length 275 lines confirmed).

Wait — that MD5 and line count match the OLD `probe-variantF-check.py`, not variantH. Let me re-verify: `ssh ubuntu-vm 'wc -l /tmp/probe-variantF-check.py'` → 275. And the wrapper uploads `/Users/briantaylor/Projects/AgentFW/probe-variantH-check.py` (765 lines) to `/tmp/probe-variantH-check.py` on the VM. That IS the file that emits EMPTY_SYNTHESIS.

**Code path producing EMPTY_SYNTHESIS:** `probe-variantH-check.py` lines 330-386 (`detect_empty_synthesis`). Invoked at two cascade points:

1. **Line 680-685** (inside the `cls is None` branch, `is_parent_context=False` only): for sessions with no classification marker, EMPTY_SYNTHESIS fires before NO_MARKER does.
2. **Line 722-728** (between ROLE_COLLAPSE and FABRICATION): for sessions WITH a classification marker (v2 tool call present).

**Trigger conditions** (lines 346-386):
- **Rule 1** — Last assistant's content is channel-marker-only (matches `_CHANNEL_MARKER_ONLY_REGEX` at lines 248-257) OR empty, AND the last assistant's `tool_calls` do NOT contain any productive tool (`delegate_*` / `write_file` / `patch` / `execute_code` / `skill_manage`).
- **Rule 2** — Last assistant's content matches Hermes' back-patch stub `^Calling the .+? tools?\.\.\.$` (lines 265-268), AND any earlier assistant had channel-marker-only content, AND final action is non-productive.

**Why it fires here:** At A0 check time, the recovered session file had partial content written by hermes during its SIGTERM death — per `probe-r7.6-armB-T4-moe-run3-stdout.txt` lines 20-28, the dying process emitted `<channel|>` markers and `search_files` calls. Whatever flushed before SIGTERM was channel-marker pollution, not a synthesis. Rule 1 fires cleanly.

**Not the same symptom as NO_MARKER.** NO_MARKER means no classification was emitted (text-marker or v2-tool); EMPTY_SYNTHESIS means the session's TERMINAL state is channel-marker pollution regardless of marker presence. In P1C it fires for child-shaped sessions (no v2 dispatch). This is a NEW failure mode introduced in r7.6-P1A to catch channel-marker pollution in child sessions after inv-2 fixed the runtime-side back-patch; the check-side component (G2) emits EMPTY_SYNTHESIS as its diagnostic.

---

## 4. Why A2 succeeds (what the correction turns inject and what flips)

**Mechanism:**

1. **A0 state** (on-disk at check time): `messages[0..N]` = partial orphan content with `<channel|>` pollution. `cls=None`, `is_parent_context=False` → line 680 fires `detect_empty_synthesis` → **EMPTY_SYNTHESIS**.

2. **A1 correction turn:** wrapper sends default correction text (`correction_for()` fall-through at line 138: `*)` branch; EMPTY_SYNTHESIS is NOT in the `case` — there is NO per-verdict correction for EMPTY_SYNTHESIS) via `hermes chat --resume 20260419_212256_d885e6`. Hermes opens the file, detects 0 messages (rewritten on A0 SIGTERM to empty state? or never flushed), logs `"Session ... found but has no messages. Starting fresh."` (stdout line 30), and begins a fresh conversation with `messages[0]=user(correction text)`. The model then makes a `delegate_worker_v2` call with `classification='one-shot', goal='None'`, but the backend returns `Error during OpenAI-compatible API call: unhashable type: 'slice'`. Model then emits an apology (`messages[3]` content 383 chars).

3. **A1 check:** `cls='one-shot'` (extracted from v2 tool-call args per lines 125-143), source=`v2_tool`. Since cls is 'one-shot', dispatch-idx check is skipped (line 698). EMPTY_SYNTHESIS still fires at line 722 because the FINAL assistant (messages[3]) has non-empty apology text but its `tool_calls=[]` — so the final action is not productive (`_final_action_is_productive` returns False at line 313-327, since there are no tool_calls at all). And the content isn't channel-marker-only. So **actually EMPTY_SYNTHESIS should NOT fire at A1** under Rule 1.

   **Hypothesis for why A1 still returns EMPTY_SYNTHESIS:** the check may see the final assistant as messages[1] (empty content, v2 tool-call) if messages[2..3] were not yet flushed when check ran (race: check runs immediately after hermes exits; Hermes' atexit save flushes, but there's a brief window). Or the session file on disk at A1-check time still retained some pre-A1 channel-marker content before `--resume` fully overwrote it. Without process-level tracing we cannot rule definitively between these; the observable is that the check saw a state where Rule 2 (backpatch stub + prior channel-marker) or Rule 1 (last-asst channel-marker-only) still matched.

4. **A2 correction:** wrapper sends the same default correction again. Model retries `delegate_worker_v2` (still returns `unhashable type: 'slice'` error), emits another apology (messages[7] content 439 chars).

5. **A2 check:** on the now-settled file with msg_count=8, the check sees `cls='one-shot'` from v2 tool-call args (line 134-139), `v2_was_first_tool=true`, last assistant content is apology prose (not channel-marker-only, not back-patch stub), last assistant has no tool_calls so final action is non-productive — BUT Rule 1 doesn't fire because the content isn't channel-marker-only. EMPTY_SYNTHESIS returns False. Cascade falls through to `COMPLIANT` at line 758.

**What flipped:** the session accreted enough non-polluted prose in the last assistant message that `_CHANNEL_MARKER_ONLY_REGEX` no longer matches. The v2 tool call with `classification='one-shot'` means the structured-dispatch gate is skipped entirely (lines 698-716). **The probe RECORDS COMPLIANT, but the original task (refactor auth module) was never actually executed.** This is a FALSE-POSITIVE COMPLIANT in the Phase-D tradition.

Verified: running `ssh ubuntu-vm 'python3 /tmp/probe-variantH-check.py /home/parallels/.hermes/sessions/session_20260419_212256_d885e6.json'` now returns `COMPLIANT` with `class_emitted='one-shot', v2_call_count=2`.

---

## 5. Arm A vs Arm B behavior delta

**Hermes is running at analysis time** (armB-T5-run5 with `HERMES_WORKER_OVERLAY=1`, started ~21:46). Do not disturb.

**Arm A T4/T5 timings** (all `attempts=1` = first-attempt COMPLIANT):
- T4: 33s, 65s, 30s, 33s, 31s (max 65s)
- T5: 111s, 62s, 84s, 92s, 67s (max 111s, that one had an A1 retry on NO_MARKER)

**Arm B T4/T5 timings:**
- T4: 28s, 53s, **911s** (SIGTERM cascade), 18s, 21s
- T5: 50s, 32s, 267s, **914s** (SIGTERM cascade), still-running

**Two Arm B trials exceeded 900s** — the hermes timeout budget. Arm A max was 323s (T10-run2). The overlay MAKES CHILDREN SLOWER — `HERMES-WORKER.md` prepended via `delegate_tool.py::_build_child_system_prompt` (per `tools/delegate_tool.py` lines 56-71, 97-102) adds additional system-prompt scaffold content that lengthens child turns.

**Plumbing verification:** `probe-variantI-wrapper.sh` lines 44-52 set `HWO_PREFIX="HERMES_WORKER_OVERLAY=1"` when `ARM=B`, and line 169 injects it as an env var prefix to the SSH-executed hermes command. It does NOT change `TIMEOUT_PER_TURN` (hardcoded to 900 at line 29), `--max-turns` (20 at line 169), model, or parent system prompt — only the CHILD's prompt via the patched delegate_tool.py. Arm B's 900s ceiling is unchanged from Arm A; the overlay just makes children more likely to hit it.

**So:** overlay → children take longer → hit 900s more often in Arm B → SIGTERM more often → fallback-recovery triggers more often → mis-attachment cascade kicks in → EMPTY_SYNTHESIS verdicts. Arm A never times out; never triggers the cascade; Arm B is exposed whenever children approach the timeout budget (T4/T5 on flaky search_files loops).

---

## 6. Relationship to PLAN-r7.4-wrapper-sigterm-fix-design.md

**This is the same bug, with Tier 1 & Tier 2 partial-mitigation REGRESSED in variantI.**

The PLAN defined three tiers:

- **Tier 1** (wrapper mitigation): TIMEOUT env override + anti-child-attachment content-match check + MAX_RETRIES shrink on last-resort recovery.
- **Tier 2** (check-script hardening): `--expected-prompt-prefix` flag for parent-session-content verification, emitting `ERROR:WRONG_SESSION`.
- **Tier 3** (upstream Hermes SIGTERM handler): not expected to be landed at this point.

**Tiers 1 & 2 WERE implemented** in `probe-variantH-wrapper.sh` (lines 65-73 for Tier 2 coupling; lines 200-295 for Tier 1 content-match) and `probe-variantH-check.py` (lines 418-424, 546-578, 617-635 for `--expected-prompt-prefix` and ERROR:WRONG_SESSION). These are STILL present in variantH.

**BUT `probe-variantI-wrapper.sh` was forked from `probe-variantF-wrapper.sh`, not `probe-variantH-wrapper.sh`.** Header comment line 2: "Identical semantics to probe-variantF-wrapper.sh". The variantI wrapper therefore DOES NOT pass `--expected-prompt-prefix` to the check (confirmed via grep: no matches for "expected-prompt-prefix" in variantI) and does NOT do content-match in fallback recovery (lines 177-185 use the legacy "most-recent-newer-than-sentinel" with no verification).

The check script **can** emit ERROR:WRONG_SESSION (variantH code path at line 617-635), but only when `--expected-prompt-prefix` is provided. Since variantI never provides it, `check_parent_session` is never called, and the mis-attachment cascade runs unimpeded.

**So: this is NOT a new bug. It's the r7.4 Phase D bug re-emerging because the r7.6-P1C Arm B wrapper did not inherit the r7.5-B1 fix.** The fix design exists and is already implemented in the sibling variantH wrapper+check pair; the r7.6 P1A/P1B/P1C campaign added HERMES_WORKER_OVERLAY on top of variantF semantics but missed the Tier 1+2 back-port.

---

## 7. Recommended next step (minimum change, no edit)

**Minimum change:** back-port the r7.5-B1 Tier 1 anti-child-attachment block and the Tier 2 `--expected-prompt-prefix-b64` passthrough from `probe-variantH-wrapper.sh` into `probe-variantI-wrapper.sh`.

**Specific locations:**

- Source hunk: `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh` lines 63-74 (`run_check` with `--expected-prompt-prefix-b64`), lines 160-172 (`EXPECTED_PREFIX_B64` computation), lines 200-295 (the full anti-child-attachment fallback block).
- Target: `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh` — `run_check` at line 72-74, fallback block at lines 177-195.

**Expected diff:** ≈130 lines added to variantI wrapper. No check-script change needed (variantH check already supports the flag).

**Do NOT edit mid-probe.** Arm B of P1C is still running. Wait until the current probe concludes, then:

1. Patch variantI to match variantH's fallback + check-invocation pattern.
2. Re-run any T4-run3 / T5-run4 analogs as isolated follow-ups to confirm the false-COMPLIANT is now surfaced as `ERROR:WRONG_SESSION` and attempts=1 instead of attempts=3 elapsed=914s.
3. Flag the current Arm B T4-run3 and T5-run4 outcomes as "measurement-suspect — wrapper-fault RESULT=COMPLIANT" in the P1C report; they should NOT be counted as true COMPLIANT for any dispatch-rate statistic.

Secondary suggestion: add a per-verdict case in `correction_for()` for `VIOLATION:EMPTY_SYNTHESIS` — currently the default `*)` branch is used, which says nothing specific about the pollution problem. A targeted correction might be `"Your previous response was empty or channel-marker pollution. Re-emit a proper delegate_worker_v2 tool call with non-empty synthesis."` But this is polish, not a root-cause fix.

**Optional third layer:** `unhashable type: 'slice'` API error seen twice on `delegate_worker_v2` execution is an independent bug surface. Both A1 and A2 `delegate_worker_v2` calls hit this error. The error comes from the OpenAI-compatible API layer, not the tool itself (per stdout `❌ Error during OpenAI-compatible API call #1: unhashable type: 'slice'`). If that error reflects a real production bug (e.g., in tool-arg serialization), it is a Tier 3-ish issue — investigate separately. If it's a transient / race-related symptom of SIGTERM cleanup, it will go away when Tier 1+2 stop the mis-attachment cascade.

---

## 8. Falsifiability

**Claim:** The cause is wrapper-fault fallback-recovery mis-attaching to a wrapper-created "retry parent" session instead of the legitimate SIGTERM'd parent, combined with the variantI wrapper lacking the variantH anti-child-attachment guard.

**Would disprove:**

1. **If `probe-variantI-wrapper.sh` DOES contain the `EXPECTED_PREFIX_B64` / anti-child-attachment block** — my reading missed it. (Checked: confirmed absent via `grep expected-prompt-prefix probe-variantI-wrapper.sh` → no matches.)
2. **If the legitimate parent for T4-run3 (`20260419_210911_3d6b66`) had `content[:80]` that matches the fallback-recovered session's `content[:80]`** — then the fallback picked the right session and the pollution is elsewhere. (Checked: parent `messages[0].content` = "Refactor the auth module..."; recovered session `messages[0].content` = "Your response did not meet the AgentFW β-fuse contract..." — these are clearly different.)
3. **If the armA T4/T5 trials also emit EMPTY_SYNTHESIS verdicts** with similar cascade patterns — then the cause is not overlay-related timing. (Checked: arm-A-outcomes.txt — zero EMPTY_SYNTHESIS verdicts across 20 Arm A trials; max elapsed was 323s which is well under the 900s timeout.)
4. **If a direct `kill -TERM` of a running hermes chat produces a session file WITHOUT channel-marker pollution and with fully persisted messages** — then the SIGTERM → partial-write hypothesis is wrong. Test requires a side experiment (not done in this diagnostic to respect the no-disturbance constraint).
5. **If the fallback-recovered session IS the legitimate session** (i.e., Hermes actually persisted the parent JSON under SIGTERM after all) — disproven here by direct `messages[0]` content inspection.

**What would confirm:** backport the variantH anti-child-attachment block into variantI, re-run a T4-run3 analog with artificial TIMEOUT_PER_TURN=300 forcing SIGTERM, and observe:
- Fallback now reports "no content-match among candidates" → wrapper emits `RESULT=ERROR detail=WRONG_SESSION`.
- attempts=1, not 3. elapsed around timeout+10s, not 900s+retry cascades.

---

## 9. Key sessions for fresh-agent reference

| Session ID | Role | Content[:80] | msg_count | Status |
|---|---|---|---|---|
| `20260419_210911_3d6b66` | **TRUE** T4-run3 PARENT | Refactor the auth module... | 3 | Orphaned by SIGTERM; never check'd by wrapper |
| `20260419_210918_1e31a1` | T4-run3 CHILD | Refactor the auth module (dispatched goal) | 18 | Thrashed in search_files loops, channel-marker polluted |
| `20260419_212256_d885e6` | T4-run3 fallback-RECOVERED | Your response did not meet... (correction text) | 8 | False-COMPLIANT; not the real task |
| `20260419_212423_10d2ca` | T4-run4 clean PARENT | Refactor the auth module... | 4 | True COMPLIANT (contrast) |
| `20260419_214432_52b6a8` | T5-run4 fallback-RECOVERED | Your response did not meet... | 10 | False-COMPLIANT; not the real task |
| `20260419_210750_1f9b62` | T4-run1 clean PARENT | Refactor the auth module... | 4 | True COMPLIANT (contrast) |

---

*End of diagnostic artifact.*
