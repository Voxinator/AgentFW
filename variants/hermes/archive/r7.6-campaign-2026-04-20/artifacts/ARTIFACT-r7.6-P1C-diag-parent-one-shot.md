# ARTIFACT — r7.6-P1C diag: parent one-shot-no-goal on retry

**Scope:** Read-only diagnostic. Fix 4 of PLAN-r7.6-P1C-fixes-implementation.md rev-2 §6.3.
**Date:** 2026-04-19
**Author:** Fix 4 diagnostic worker (sub-agent)

---

## TL;DR

**Root cause: H4B (wrapper correction framing) is the dominant cause, with H4A (variantF spec silence on retry) as an amplifier. H4C (schema) is not causal — the schema is behaving as specified.**

The wrapper's `correction_for()` function emits correction messages that stand alone as "protocol correction" prose and **never re-inject the original `$TASK_TEXT`**. On a retry that opens with a correction message, the model legitimately reads the correction as the current user turn, classifies it as `one-shot` (a meta-correction with no file work is, in fact, one-shot under the §"one-shot" criteria of HERMES-variantF.md), and returns — producing LOST because no child is spawned. The original structured task is forgotten by the post-correction turn.

**Additional finding that affects the diag scope:** Only **2 of the 3** trials named in the brief are in the one-shot-no-goal failure class. **T6-run4 (`session_20260419_221749_e5e803`) is retry-exhausted on VIOLATION:NO_MARKER, not one-shot-no-goal.** It matches a DIFFERENT failure mode (orient-first drift on long-horizon task under 900s timeout) and requires a separate analysis. The plan's §6.1 enumerates three trials; the probe-results per-trial table (line 194) and §"Incidents 3" (line 131) list only T4-run3 + T5-run4 as one-shot-no-goal. This artifact flags the inconsistency but focuses the fix on the confirmed two-trial pattern.

---

## Evidence inventory

**Files inspected (md5 for reproducibility):**

| File | md5 | Purpose |
|------|-----|---------|
| `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh` | `95cef027235f1a4716878640796c016f` | Arm B wrapper; correction_for() at lines 108-150 |
| `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh` | `6958c8bbc3567d1d221e04e5706ecee9` | Sibling wrapper with symmetric correction_for() at lines 112-152 |
| `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md` | `01c0e77bb2a6e753a8ea9063784a25e0` | β-fuse spec read by parent agent |
| `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py` | `d31876fe987331a26c8640202334fd46` | v2 schema + handler |

**VM sessions inspected:**

| Trial | Parent SID | Task | Wrapper outcome | Session len |
|-------|-----------|------|------------------|-------------|
| armB-T4-run3 | `20260419_212256_d885e6` | T4 (structured) | COMPLIANT after 3 attempts, chain: `A0:rc=124 \| A0:VIOLATION:EMPTY_SYNTHESIS \| A1_correct:rc=0 \| A1:VIOLATION:EMPTY_SYNTHESIS \| A2_correct:rc=0 \| A2:COMPLIANT` | 8 msgs |
| armB-T5-run4 | `20260419_214432_52b6a8` | T5 (structured) | COMPLIANT after 3 attempts, chain: `A0:rc=124 \| A0:VIOLATION:EMPTY_SYNTHESIS \| A1_correct:rc=0 \| A1:VIOLATION:EMPTY_SYNTHESIS \| A2_correct:rc=0 \| A2:COMPLIANT` | 10 msgs |
| armB-T6-run4 | `20260419_221749_e5e803` | T6 (long-horizon) | RETRY_EXHAUSTED on NO_MARKER (4 attempts), chain: `A0:rc=124 \| A0:VIOLATION:NO_MARKER \| ... \| A3:VIOLATION:NO_MARKER` | 35 msgs | **Different failure mode** |

`rc=124` = 900s SIGTERM on initial invocation. All three had wrappers compute session_id via the "most-recent-newer-than-sentinel" last-resort fallback (line 190 in variantI-wrapper.sh), i.e., primary regex failed because the SIGTERM-killed invocation never emitted a `session_id:` line to stdout.

---

## Per-session evidence

### Trial 1 — armB-T4-run3 (`20260419_212256_d885e6`)

**Wrapper log** (`/tmp/probe-r7.6-P1C-logs/arm-B-T4-run3.out` line 1-12):
```
[probe-r7.6-armB-T4-moe run3] task: Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts...
[probe-r7.6-armB-T4-moe run3] attempt 0: initial invocation (ARM=B)
[probe-r7.6-armB-T4-moe run3] primary regex missed session_id; attempting fallback recovery by source-tag scan...
[probe-r7.6-armB-T4-moe run3] source-tag scan empty; trying most-recent-newer-than-sentinel as last resort
[probe-r7.6-armB-T4-moe run3] recovered session_id via fallback: 20260419_212256_d885e6
[probe-r7.6-armB-T4-moe run3] attempt 0 verdict: VIOLATION:EMPTY_SYNTHESIS
[probe-r7.6-armB-T4-moe run3] attempt 1: sending correction for VIOLATION:EMPTY_SYNTHESIS (ARM=B)
...
OUTCOME run=3 ... RESULT=COMPLIANT attempts=3 elapsed=911s final_session=20260419_212256_d885e6 chain="A0:rc=124 | A0:VIOLATION:EMPTY_SYNTHESIS | A1_correct:rc=0 | A1:VIOLATION:EMPTY_SYNTHESIS | A2_correct:rc=0 | A2:COMPLIANT"
```

**Session message chain** (session `20260419_212256_d885e6.json` idx 0..7):

| idx | role | content | tool_calls |
|-----|------|---------|-----------|
| 0 | user | **"Your response did not meet the AgentFW β-fuse contract. Re-read HERMES.md and respond again, beginning with a `delegate_worker_v2` tool call..."** | — |
| 1 | assistant | (empty) | `delegate_worker_v2(classification="one-shot", justification="The user is correcting a protocol violation regarding the initial tool call requirement; this is a purely informational/corrective response with no file modifications.")` — **no goal** |
| 2 | tool | `Error executing tool: ... unhashable type: 'slice'` | — |
| 3 | assistant | `I apologize, Brian. It looks like I hit a technical snag with the delegate_worker_v2 tool...` | — |
| 4 | user | (wrapper correction, identical default-branch text to idx 0) | — |
| 5 | assistant | (empty) | `delegate_worker_v2(classification="one-shot", justification="The user is providing a corrective instruction regarding the AgentFW protocol; this response is a meta-discussion/correction involving no file modifications or sub-tasks.")` — **no goal** |
| 6 | tool | `Error executing tool: ... unhashable type: 'slice'` | — |
| 7 | assistant | `I apologize, Brian. I am attempting to follow the β-fuse contract by leading with the delegate_worker_v2 tool call, but the tool itself is currently returning a technical error...` | — |

**Key observations:**
- The session.json's **first message is the wrapper correction, not the original task**. The SIGTERM-killed initial invocation wrote zero assistant turns to the session (explaining the "primary regex missed session_id" in the wrapper log — there was no emitted `session_id: ...` line to grep). The session file was created by the --resume leg.
- Under wrapper semantics, `A0:VIOLATION:EMPTY_SYNTHESIS` means the check script saw no final synthesis assistant turn in the session at attempt-0 inspection time. The attempt-0 verdict used a session that contained ONLY the correction turn + assistant tool_call — the check called this "empty synthesis" because the assistant had an error-result, not a final synthesized answer.
- The model's `justification` strings explicitly reference the correction as the task: *"The user is correcting a protocol violation"* (idx 1) and *"The user is providing a corrective instruction regarding the AgentFW protocol"* (idx 5). The original task (refactor auth module) is **never mentioned** anywhere in the session. The model does not have it in scope because it never saw it (the initial-invocation prompt was SIGTERM'd before anything persisted).
- `A2:COMPLIANT` verdict was reached on attempt 2 because the check script found BOTH `delegate_worker_v2` tool_calls and no further violations — structurally COMPLIANT under the β-fuse contract, but LOST from the worker-quality perspective because **no goal was provided, so no child spawned**.

### Trial 2 — armB-T5-run4 (`20260419_214432_52b6a8`)

Identical structural pattern to trial 1.

**Session idx 0** (first user message, via `jq ".messages[0].content"`):
```
"Your response did not meet the AgentFW β-fuse contract. Re-read HERMES.md and respond again, beginning with a `delegate_worker_v2` tool call that records your classification, justification, and (for structured/long-horizon) goal."
```

**Session idx 1** (first assistant tool call):
```
{"classification": "one-shot", "justification": "The user is providing a direct corrective instruction regarding protocol compliance; no files are being modified and it is a purely informational/meta-conversational response."}
```

**Session idx 3** (second assistant, AFTER seeing slice-error tool return):
```
tool_call: delegate_worker_v2(classification="one-shot", justification="Retrying the protocol correction after a tool execution error to ensure compliance with the β-fuse contract.")
```

**Session idx 7** (third assistant after second correction):
```
{"classification": "one-shot", "justification": "The user is issuing a protocol correction. No files are being modified and no complex work is required beyond acknowledging the instruction and addressing the error."}
```

Three `delegate_worker_v2` calls, all one-shot, all without `goal`, all rationalized against "the user's correction" rather than the original T5 stale-dashboard bug-hunt task. The original task prompt never appears in the session.

### Trial 3 — armB-T6-run4 (`20260419_221749_e5e803`) — **DIFFERENT FAILURE MODE**

This trial does NOT match the one-shot-no-goal pattern. Evidence:

**Session idx 0** (first user message, full content):
```
"Implement a multi-format export feature (CSV, JSON, PDF) with permission enforcement and documentation updates. \n\nPhase 1: Discovery & Design\n1. Explore the codebase to identify the data layer and existing API patterns. ... Deliverable for this phase: export-feature/PLAN.md and export-feature/PROGRESS.md."
```
The ORIGINAL T6 task text is present (not a wrapper correction). So the session_id extraction on attempt-0 may have succeeded differently, OR the initial invocation did persist the prompt before SIGTERM.

**All assistant tool calls across 35 messages — zero `delegate_worker_v2` invocations.** The model dispatched directly: `search_files("*", target="files")` (idx 1), `search_files("*api*", ...)` (idx 3), `search_files("*permission*", ...)` (idx 5), `read_file("./acp_adapter/permissions.py")` (idx 7), `read_file("./gateway/platforms/api_server.py")` (idx 9), `search_files("*db*", ...)` (idx 11), ... continuing through idx 29 with `todo(...)`. Repeated `<channel|>` leakage in assistant content (e.g., idx 3, 5, 13, etc.).

**This is VIOLATION:NO_MARKER, not EMPTY_SYNTHESIS.** The model went straight into orient-first drift — a failure mode explicitly named in HERMES-variantF.md §"Classification pressure" as pattern #3 ("Orient-First Drift"). Under the β-fuse contract, the first tool call MUST be `delegate_worker_v2`; here the first (and every) tool call is something else. The NO_MARKER branch of `correction_for()` was invoked four times, never succeeding.

**Planner-brief inconsistency:** PLAN §6.1 and §6.3 list T6-run4 alongside T4-run3 and T5-run4 as one-shot-no-goal cases. The probe-results artifact per-trial table at line 194 and "Incidents" §3 at line 131 list only T4-run3 + T5-run4 as one-shot-no-goal, and separately call out T6-run4 as "retry-exhausted on NO_MARKER." The probe-results artifact is correct. Fix 4 should focus on the 2-trial one-shot-no-goal pattern; T6-run4 is an orthogonal issue related to NO_MARKER handling on long-horizon timeouts.

---

## Wrapper-correction text inspection (authoritative)

`probe-variantI-wrapper.sh::correction_for()` at lines 108-150. Six branches:

| Verdict | Branch | Re-injects `$TASK_TEXT`? |
|---------|--------|---------------------------|
| `VIOLATION:NO_MARKER` | lines 111-118 | **NO** — emits format template only |
| `VIOLATION:NO_DISPATCH:structured\|long-horizon` | lines 120-129 | **NO** |
| `VIOLATION:ROLE_COLLAPSE:structured\|long-horizon` | lines 131-138 | **NO** |
| `VIOLATION:FABRICATION` | lines 140-142 | **NO** |
| `VIOLATION:NO_ASSISTANT_RESPONSE` | lines 143-144 | **NO** |
| `*)` (default) | lines 146-148 | **NO** — emits: "Your response did not meet the AgentFW β-fuse contract. Re-read HERMES.md and respond again..." |

**No branch handles `VIOLATION:EMPTY_SYNTHESIS` specifically** — it falls through to the `*)` default. This is the exact path hit by T4-run3 and T5-run4.

**Not one correction re-injects the original task.** The wrapper assumes Hermes session-state preserves the original prompt across --resume, but in the SIGTERM-killed-before-persistence scenario, the original prompt was never written to the session file. From the model's post-correction turn perspective, the *only* visible user turn is the correction.

`probe-variantH-wrapper.sh::correction_for()` at lines 112-152 is **structurally identical** (same six branches, same default fall-through, no `$TASK_TEXT` re-injection anywhere). Fix 4 will need symmetric treatment on both wrappers to avoid drift.

---

## HERMES-variantF.md retry-guidance inspection

Grep for retry-related vocabulary (`retry|correction|continue|original|resume|preserve`, case-insensitive):

- **Line 100** — only hit, in the "Judge" paragraph: *"Evaluates completed work against verification criteria from a fresh context... Determines accept, revise, or restart."* Unrelated to parent-retry classification.
- **Line 142** — worker-dispatch example goal contains "continues to run until done"-style phrasing; unrelated.

**There is no text in HERMES-variantF.md that instructs the model to preserve original classification across retries.** The Classification Gate (§"CRITICAL: First-Tool-Call Contract") treats every task as a first impression. §"Classification pressure" enumerates 5 failure modes but none cover "retry after prior-session-killed."

The model's behavior on T4-run3 and T5-run4 is, in fact, **internally consistent** with variantF's rules: the visible user turn is "Re-read HERMES.md and respond again, beginning with a `delegate_worker_v2` tool call..." — classifying that as one-shot (no files, no sub-components) is defensible. The spec never tells the model "if this correction is about a retry, reconstruct the original task." H4A is a real gap.

---

## Schema inspection — `delegate_worker_v2.py`

Per `delegate_worker_v2.py` lines 59-94 (`DELEGATE_WORKER_V2_SCHEMA`):

```json
"required": ["classification", "justification"]
```

`goal` is listed in properties (line 82-91) but **not in `required`**. Goal's description says: *"REQUIRED for structured and long-horizon. ... OPTIONAL for one-shot (ignored if provided)."*

Handler at lines 98-148:
- Enum-validates `classification` (line 102-103).
- Length-validates `justification` ≥30 chars (lines 106-109).
- For `classification="one-shot"`, returns `{"ok": True, "classified": "one-shot", "message": "Classified as one-shot. Proceed in the main session. ..."}` — **no child spawn, no goal requirement** (lines 114-124). This is the handler's **specified** behavior per the module docstring line 20: "one-shot → returns immediately; model continues in main session."
- For structured/long-horizon, `goal` is required at handler level (lines 126-135) and `delegate_task()` is called.

**Interpretation for H4C:** the schema is doing exactly what it was designed to do. One-shot + no goal is a valid, documented path. From the wrapper's perspective, a one-shot response produces a COMPLIANT verdict (structurally), which is what attempt-2 returned on trials 1 and 2. The LOST classification happens downstream in the judge, which correctly flags "no child to judge." The schema is NOT the causal root — tightening it to require `goal` for one-shot would regress legitimate one-shot answers (e.g., T1/T2/T8 which pass under one-shot-no-goal).

**Side-finding unrelated to H4A/B/C:** messages 2 and 6 in T4-run3 show `Error executing tool: ... unhashable type: 'slice'`. This is an oMLX infrastructure error in the handler's downstream layer, reported by the probe-results artifact §"Incidents 3" as a possibly-transient bug. Not causal for the classification itself (the tool_call args were already recorded in the session BEFORE the error hit) but noteworthy.

---

## Hypothesis weighting

### H4A — HERMES-variantF.md lacks retry-classification guidance

- **Supporting:** grep finds zero retry-relevant clauses in variantF.md. The Classification Gate treats every user turn as an independent task. Under strict variantF rules, classifying the correction message as one-shot is defensible.
- **Disconfirming:** if the correction re-injected the original task text, the model would classify on the injected text, not on the correction framing. So H4A is amplifying, not causal in isolation.
- **Probability this is the sole cause:** ~10%.
- **Probability this is a contributing factor:** ~75%.

### H4B — Wrapper correction framing doesn't re-inject original task

- **Supporting:** session idx 0 on T4-run3 and T5-run4 is the correction text verbatim, and NOWHERE in either session does the original task appear. The model cannot classify based on context it cannot see. Model justifications explicitly reference "the user is correcting a protocol violation" — demonstrating the model's world-model IS the correction. Fix at this layer (re-inject `$TASK_TEXT` in every correction branch) directly prevents the failure.
- **Disconfirming:** T6-run4 had the original task present in idx 0 and STILL failed (NO_MARKER drift), showing that H4B alone doesn't capture all parent failures. But within the one-shot-no-goal failure class, H4B is necessary and probably sufficient.
- **Probability this is the dominant cause of the one-shot-no-goal LOST trials:** ~80%.

### H4C — Schema allows one-shot without goal silently

- **Supporting:** nothing — this is a descriptive statement about the schema but not a causal failure mode.
- **Disconfirming:** schema is behaving as specified. Tightening it would regress legitimate one-shots (T1/T2/T8 which currently PASS under one-shot-no-goal) without addressing the underlying issue that the model is classifying the WRONG TEXT.
- **Probability this is causal:** ~5%. The schema is the structural backstop that allows the LOST outcome to manifest, but it is not the reason the model made the wrong classification choice.

**Verdict:** H4B (80%) >> H4A (10% sole / 75% contributing) >> H4C (5%). Primary fix target: the wrapper. Secondary fix: a short variantF.md clause. No schema change.

---

## Recommended fix

**Primary — P0:** Edit `probe-variantI-wrapper.sh::correction_for()` to re-inject `$TASK_TEXT` in EVERY correction branch, with a clear prefix framing the retry as a continuation. Additionally, **add an explicit branch for `VIOLATION:EMPTY_SYNTHESIS`** so it no longer falls through to the generic default. Apply symmetric edits to `probe-variantH-wrapper.sh` to avoid drift (per plan §6.4, "handle in same PR to avoid drift").

**Secondary — add-on:** ~5-line clause in HERMES-variantF.md §"Classification pressure — named failure modes" (after pattern #5) teaching the model: "If a user turn reads as a protocol correction referencing 'Re-read HERMES.md', check whether an original task text is present in the same turn. If so, classify based on the original task, not the correction framing. If not, ask for the original task via a `clarify` call rather than classifying the correction itself."

**No schema change.** H4C is not causal.

### Affected files

1. `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh` — PRIMARY
2. `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh` — SYMMETRIC (same diff shape)
3. `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md` — OPTIONAL add-on

Implementation worker scope (per plan §6.4): "If H4B dominant: edit `probe-variantI-wrapper.sh::correction_for()` to re-inject the original task text in corrections. Worker scope: wrapper only. Also update `probe-variantH-wrapper.sh` symmetrically." Picks branch #2 of plan §6.4 decision tree.

### Approximate diff (probe-variantI-wrapper.sh; ~15 lines net new)

```diff
 correction_for() {
   local v=$1
+  # Retry-safe prefix: re-inject the original TASK_TEXT so the model sees the
+  # task it was originally asked to solve, not just the correction framing.
+  # Fixes the one-shot-no-goal cascade observed in armB-T4-run3 / armB-T5-run4
+  # where the SIGTERM-killed attempt-0 left an empty session and the model
+  # classified the subsequent correction message as a standalone one-shot.
+  local ORIG_PREAMBLE
+  ORIG_PREAMBLE=$(cat <<EOF
+This is a RETRY of your original task. The initial attempt did not satisfy the β-fuse contract. Your ORIGINAL task (unchanged) is:
+
+--- BEGIN ORIGINAL TASK ---
+${TASK_TEXT}
+--- END ORIGINAL TASK ---
+
+Preserve your original classification for this task. Below is the specific protocol issue you must address before proceeding:
+EOF
+)
   case "$v" in
     VIOLATION:NO_MARKER)
-      cat <<'MSGEOF'
+      {
+        echo "$ORIG_PREAMBLE"
+        echo
+        cat <<'MSGEOF'
 Your first tool call was not `delegate_worker_v2`. Under the AgentFW β-fuse contract, every task must begin with a `delegate_worker_v2` tool call that records your classification. Emit the tool call now in EXACTLY this format:

 <tool_call>
 {"name": "delegate_worker_v2", "arguments": {"classification": "<one-shot|structured|long-horizon>", "justification": "<reason, ≥30 chars>", "goal": "<if structured/long-horizon, self-contained task spawn>"}}
 </tool_call>
 MSGEOF
+      }
       ;;
     # ... same pattern for NO_DISPATCH, ROLE_COLLAPSE, FABRICATION, NO_ASSISTANT_RESPONSE ...
+    "VIOLATION:EMPTY_SYNTHESIS")
+      {
+        echo "$ORIG_PREAMBLE"
+        echo
+        cat <<'MSGEOF'
+Your previous attempt ended without producing a final synthesis/answer turn. Re-engage the original task above. Begin with a `delegate_worker_v2` tool call that preserves your original classification and (for structured/long-horizon) includes a self-contained `goal` re-stating the original task.
+MSGEOF
+      }
+      ;;
     *)
-      echo "Your response did not meet the AgentFW β-fuse contract. Re-read HERMES.md and respond again, beginning with a \`delegate_worker_v2\` tool call that records your classification, justification, and (for structured/long-horizon) goal."
+      {
+        echo "$ORIG_PREAMBLE"
+        echo
+        echo "Your response did not meet the AgentFW β-fuse contract. Re-read HERMES.md and respond again, beginning with a \`delegate_worker_v2\` tool call that records your classification, justification, and (for structured/long-horizon) goal."
+      }
       ;;
   esac
 }
```

Apply analogous edit to `probe-variantH-wrapper.sh` (symmetric; `correction_for()` starts line 112 there). Total LOC: ~20-25 lines added across two files; zero lines deleted except for the single-echo rewrite in the `*)` default.

---

## Falsifiability

**H4B falsifier:** After the fix lands, run an artificial retry probe that simulates SIGTERM-before-persistence on Arm B T4 and T5 (the plan §6.5 "5-trial smoke"). Expected post-fix behavior:
- The retry attempts see the `--- BEGIN ORIGINAL TASK ---` block in the correction message.
- The model classifies based on the original task (structured, with a goal) — NOT as one-shot.
- `delegate_worker_v2` call carries `goal="..."` matching the original T4/T5 task brief.
- No LOST outcomes on the 5 smoke trials.

**If post-fix the model STILL classifies these retries as one-shot-no-goal**, then H4B is wrong (the correction-framing was not causal) and H4A was dominant after all — the fix would then need to move to HERMES-variantF.md (plan §6.4 branch #1).

**Specific disconfirmer for H4B:** observe post-fix `justification` strings. If they reference the retry framing ("user is correcting me") rather than the original task properties ("refactor auth module touches three files"), the prefix injection did not land in the model's attention and H4B's premise was wrong.

**Upper-bound falsifier:** if, on a clean run (no retry path), Arm B produces a fresh one-shot-no-goal LOST that was NOT preceded by a SIGTERM cascade, H4B is inadequate — a different causal chain exists. Planner should track this across the S10 validation probe.

---

## Summary table

| Question | Answer |
|----------|--------|
| What is the root cause? | Wrapper's `correction_for()` does not re-inject `$TASK_TEXT`; SIGTERM-before-persistence leaves a session whose only visible user turn is the correction framing, which the model legitimately classifies as one-shot-no-goal. |
| Winning hypothesis? | **H4B** (probability ~80%), with H4A as contributing factor (~75% contribution when layered on H4B's gap). |
| Files affected? | `probe-variantI-wrapper.sh` (primary), `probe-variantH-wrapper.sh` (symmetric), optional ~5-line add in `HERMES-variantF.md`. |
| Schema change needed? | **No.** H4C is not causal; schema is behaving as specified. |
| How many trials actually match the hypothesis class? | **2 of 3** named in plan §6.1 — T4-run3 and T5-run4. T6-run4 is a different failure (NO_MARKER retry-exhaustion on long-horizon timeout). Planner should update §6.1 to reflect probe-results artifact's accurate count (2). |
| Estimated implementation effort? | **S (small)**. ~20-25 LOC across two files + optional 5 LOC in variantF.md. |
