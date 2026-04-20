# ARTIFACT — r7.5 Workstream B.2 Implementation Notes

**Worker:** B.2 (Tier 2 check-script hardening)
**Target file:** `/Users/briantaylor/Projects/AgentFW/probe-variantG-check.py`
**Date:** 2026-04-19
**Coordinating with:** B.1 (wrapper-side `--expected-prompt-prefix` pass-through, `ERROR:WRONG_SESSION` handling)

---

## Summary

Added a structural parent-session gate to `probe-variantG-check.py`. When invoked with `--expected-prompt-prefix "<text>"`, the script verifies that the session's first user-role message content begins with `<text>` on a byte-level prefix match (first 80 bytes). A mismatch emits a new `ERROR:WRONG_SESSION` verdict (plus a diagnostic JSON line with `expected_prefix`, `actual_first_user_content`, `reason`). All existing verdicts and gate logic are preserved verbatim. The new check runs BEFORE the `NO_ASSISTANT_RESPONSE` / `NO_MARKER` gates so a mis-attached child session is correctly classified as a wrapper problem, not a model-level compliance violation.

---

## File hashes

| Stage | MD5 | Lines |
|---|---|---|
| Before edit (Worker A.1's variantG baseline) | `12f27a10c789bb58f9f5cb841f3b3d63` | 284 |
| After edit (this worker)                    | `b9b5944dde12ff8f698c8a6be10913fb` | 393 |

Line-count delta: **+109**.

---

## Line ranges touched

| Range (post-edit) | Purpose |
|---|---|
| 1–29 | Module docstring replaced to document new flag, new verdict, full usage line, and the full verdict enumeration. |
| 56–100 | New helpers `_coerce_content_to_str`, `check_parent_session`, `_first_user_content_preview` inserted between `first_assistant` and `extract_first_line`. |
| 239–271 | New `_parse_argv` helper inserted between `final_assistant_text` and `main`. |
| 275–278 | `main()` header switched from positional-only `sys.argv` handling to `_parse_argv` dispatch. |
| 292–315 | New early-gate block that runs the parent-session check and emits `ERROR:WRONG_SESSION` on failure (before `first_assistant` / `NO_MARKER` paths). |

No lines were removed from the prior verdict/gate logic; no existing verdict strings were altered.

---

## Unified diff (vs. `probe-variantF-check.py` — also ≈ vs the pre-edit variantG baseline which was a clean F copy with only header differences)

```diff
--- /Users/briantaylor/Projects/AgentFW/probe-variantF-check.py	2026-04-19 12:43:02
+++ /Users/briantaylor/Projects/AgentFW/probe-variantG-check.py	2026-04-19 17:23:11
@@ -1,19 +1,31 @@
 #!/usr/bin/env python3
-"""probe-variantF-check.py — gate-check a Hermes session for Variant F (β-fuse) compliance.
+"""probe-variantG-check.py — gate-check a Hermes session for Variant G (β-fuse v2.1) compliance.

-Variant F = Variant E's structure + Layer 3 β-fuse: classification is fused into
-the `delegate_worker_v2` tool call. The v2 call IS the dispatch (for
-structured/long-horizon) and IS the marker (for all classes).
+Variant G = Variant F + turn-0 toolset restriction + parent-session structural check.

-Differences from probe-variantE-check.py:
-  - Classification source is v2 tool-call args first, legacy text-marker fallback.
-  - Hallucinated tool calls (those Hermes rejected with "Tool 'X' does not exist")
-    are filtered from the analyzed tool-call sequence. This fixes the r7.3 probe
-    labeling artifact where rejected `terminal` calls were counted as "first tool".
-  - New diagnostics: classification_source, v2_call_count, v2_was_first_tool,
-    hallucinated_calls.
+Differences from probe-variantF-check.py:
+  - New --expected-prompt-prefix CLI arg: when provided, verifies the session's
+    first user message begins with the expected trial prompt. Rejects sessions
+    whose messages[0] is a dispatched goal (child sessions mis-attached by the
+    wrapper's fallback recovery when SIGTERM truncates the parent).
+  - New ERROR:WRONG_SESSION verdict fires when the parent-session check fails.
+  - All r7.4 verdicts and gate logic unchanged.

-Usage: python3 probe-variantF-check.py <session_path>
+Usage: python3 probe-variantG-check.py [--expected-prompt-prefix "<prefix>"] <session_path>
+
+Output (single line, machine-readable):
+  COMPLIANT
+  VIOLATION:NO_MARKER
+  VIOLATION:NO_DISPATCH:<class>
+  VIOLATION:ROLE_COLLAPSE:<class>
+  VIOLATION:FABRICATION
+  VIOLATION:NO_ASSISTANT_RESPONSE
+  ERROR:WRONG_SESSION        (NEW — requires --expected-prompt-prefix)
+  ERROR:FILE_NOT_FOUND
+  ERROR:JSON_PARSE
+  ERROR:USAGE
+
+Plus a JSON-encoded second line with diagnostic details.
 """

 import json
@@ -42,8 +54,56 @@
         if m.get("role") == "assistant":
             return m
     return None
+
+
+def _coerce_content_to_str(content):
+    """Coerce a message.content value to a string for byte-prefix comparison.
+
+    Hermes normally stores content as a plain str. Multimodal clients may use a
+    list of parts (e.g. [{"type": "text", "text": "..."}]). We best-effort
+    concatenate text parts; for anything else we fall back to str() which yields
+    an unhelpful repr that will not prefix-match the expected trial prompt — a
+    mismatch in that case is the correct (conservative) behavior.
+    """
+    if content is None:
+        return ""
+    if isinstance(content, str):
+        return content
+    if isinstance(content, list):
+        parts = []
+        for p in content:
+            if isinstance(p, dict):
+                t = p.get("text")
+                if isinstance(t, str):
+                    parts.append(t)
+                    continue
+            parts.append(str(p))
+        return "".join(parts)
+    return str(content)
+
+
+def check_parent_session(messages, expected_prefix, prefix_len=80):
+    """Return True iff the first user-role message content starts with expected_prefix.
+
+    Defends against wrapper fallback-recovery mis-attaching a child session as
+    parent. The comparison is a byte-level prefix match on the first prefix_len
+    bytes (default 80, matching B.1's wrapper-side constant for consistency).
+    """
+    first_user = next((m for m in messages if m.get("role") == "user"), None)
+    if first_user is None:
+        return False  # No user message at all — structurally invalid parent.
+    content = _coerce_content_to_str(first_user.get("content"))
+    return content[:prefix_len] == (expected_prefix or "")[:prefix_len]


+def _first_user_content_preview(messages, n=80):
+    """Return the first user-role message content, truncated to n chars. '' if none."""
+    for m in messages:
+        if m.get("role") == "user":
+            return _coerce_content_to_str(m.get("content"))[:n]
+    return ""
+
+
 def extract_first_line(text):
     if not text:
         return ""
@@ -174,13 +234,47 @@
         if m.get("role") == "assistant":
             return (m.get("content") or "").lower()
     return ""
+
+
+def _parse_argv(argv):
+    """Manual argv parse (stylistic parity with variantF — no argparse import).
+
+    Accepts:
+      <prog> <session_path>
+      <prog> --expected-prompt-prefix <value> <session_path>
+      <prog> --expected-prompt-prefix=<value> <session_path>
+
+    Returns (path, expected_prefix_or_None) on success, or (None, None) on
+    usage error — caller emits ERROR:USAGE.
+    """
+    args = list(argv[1:])
+    expected_prefix = None
+    positional = []
+    i = 0
+    while i < len(args):
+        a = args[i]
+        if a == "--expected-prompt-prefix":
+            if i + 1 >= len(args):
+                return None, None
+            expected_prefix = args[i + 1]
+            i += 2
+            continue
+        if a.startswith("--expected-prompt-prefix="):
+            expected_prefix = a[len("--expected-prompt-prefix="):]
+            i += 1
+            continue
+        positional.append(a)
+        i += 1
+    if len(positional) != 1:
+        return None, None
+    return positional[0], expected_prefix


 def main():
-    if len(sys.argv) != 2:
+    path, expected_prefix = _parse_argv(sys.argv)
+    if path is None:
         print("ERROR:USAGE")
         return 1
-    path = sys.argv[1]
     try:
         with open(path) as f:
             data = json.load(f)
@@ -194,6 +288,30 @@
     messages = data.get("messages", [])
     diag = {"path": path, "msg_count": len(messages)}

+    # Parent-session structural check (fires only when --expected-prompt-prefix
+    # was provided). Runs BEFORE NO_ASSISTANT_RESPONSE / NO_MARKER so that a
+    # mis-attached child session is classified as WRONG_SESSION (a wrapper
+    # problem) rather than as a model-level compliance violation.
+    if expected_prefix is not None:
+        if not check_parent_session(messages, expected_prefix):
+            actual = _first_user_content_preview(messages, n=80)
+            reason = (
+                "empty_messages"
+                if not messages
+                else ("no_user_message"
+                      if not any(m.get("role") == "user" for m in messages)
+                      else "first_user_content_prefix_mismatch")
+            )
+            print("ERROR:WRONG_SESSION")
+            print(json.dumps({
+                "path": path,
+                "msg_count": len(messages),
+                "expected_prefix": expected_prefix[:80],
+                "actual_first_user_content": actual,
+                "reason": reason,
+            }))
+            return 0
+
     first = first_assistant(messages)
     if first is None:
         print("VIOLATION:NO_ASSISTANT_RESPONSE")
```

---

## Design choices

### argparse vs manual argv parsing

**Chose: manual argv parsing.**

- variantF (the r7.4 baseline) uses `len(sys.argv) != 2` with direct indexing. variantE and earlier do the same. Introducing `argparse` for a single optional flag breaks stylistic consistency with the rest of the probe-variant* family.
- The new `_parse_argv` helper is ~20 lines, self-contained, and supports both `--expected-prompt-prefix VALUE` and `--expected-prompt-prefix=VALUE` forms to be flexible for whatever quoting convention B.1 settles on in the wrapper.
- If argparse were later wanted (for e.g. `--help`, mutually exclusive flags), migration is a local refactor that doesn't touch the verdict logic.

### `prefix_len = 80`

Matches the constant B.1 is adopting on the wrapper side (per the task spec). 80 bytes is:
- long enough to distinguish the trial prompts (the three core trials — P1 math, P2 dashboard, P3 debug — differ within the first ~30 chars, so 80 is comfortably redundant).
- short enough to tolerate minor trailing whitespace / newline differences without a strict-equality false negative.
- cheap to compare on every session read (O(1) byte slice).

### Empty-messages edge case → `ERROR:WRONG_SESSION`

When `messages` is empty OR contains no user-role entry, `check_parent_session` returns `False` and we emit `ERROR:WRONG_SESSION` with a `reason` distinguishing `empty_messages` vs `no_user_message` vs `first_user_content_prefix_mismatch`. Rationale:

- The caller (B.1 wrapper) sets `--expected-prompt-prefix` only when it believes it's looking at a parent session. If messages are empty or lack a user turn, the session is structurally not a parent — `WRONG_SESSION` correctly signals "wrapper picked the wrong file" rather than `NO_ASSISTANT_RESPONSE` (which would signal "model failed to respond to a valid prompt").
- Folding into `WRONG_SESSION` keeps the new verdict the sole indicator of a wrapper-level attribution bug and lets the existing `NO_ASSISTANT_RESPONSE` path continue to flag real model failures in non-flagged invocations.
- The `reason` field in the diag JSON gives the wrapper/operator the detail needed to distinguish the three sub-cases without exploding the verdict enum.

### Content coercion

`_coerce_content_to_str` handles:
- `None` → `""` (non-match against any non-empty prefix, as intended).
- `str` → passthrough.
- `list` (multimodal parts like `[{"type":"text","text":"..."}]`) → concatenate `text` fields.
- Anything else → `str()` fallback, which produces a repr that won't prefix-match; a mismatch is the conservative default.

This preserves Hermes' usual plain-string case as a literal byte match and keeps the check from crashing on unusual message shapes.

### Byte-level comparison

Per task spec, the comparison is a plain Python slice equality (`content[:80] == expected[:80]`). Python strings are unicode-normalized-as-is — the wrapper passes `$TASK_TEXT` unchanged, and Hermes stores what it receives. If a future refactor introduces unicode normalization somewhere in the pipeline, this will fail deterministically with `first_user_content_prefix_mismatch` and surface as `ERROR:WRONG_SESSION`, which is better than silently accepting a normalized mismatch.

---

## Smoke test outputs

Verification tool: `python3 -m py_compile` → silent (OK).

**Test 1 — no flag, synthetic COMPLIANT session:**
```
COMPLIANT
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "first_line": "", "classification_source": "v2_tool", "class_emitted": "one-shot", "tool_calls_raw": ["delegate_worker_v2"], "tool_calls": ["delegate_worker_v2"], "tool_call_count": 1, "tool_call_count_raw": 1, "hallucinated_calls": [], "delegate_task_count": 0, "delegate_worker_count": 0, "v2_call_count": 1, "v2_was_first_tool": true, "last_3_tool_errored": 0, "last_3_tool_total": 0, "final_text_preview": "", "has_completion_claim": false}
```
**Expected:** COMPLIANT. **Got:** COMPLIANT. Baseline parity confirmed — when the flag is absent, the new code path is inert.

**Test 2 — matching expected prefix:**
```
COMPLIANT
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "first_line": "", "classification_source": "v2_tool", "class_emitted": "one-shot", "tool_calls_raw": ["delegate_worker_v2"], "tool_calls": ["delegate_worker_v2"], "tool_call_count": 1, "tool_call_count_raw": 1, "hallucinated_calls": [], "delegate_task_count": 0, "delegate_worker_count": 0, "v2_call_count": 1, "v2_was_first_tool": true, "last_3_tool_errored": 0, "last_3_tool_total": 0, "final_text_preview": "", "has_completion_claim": false}
```
**Expected:** COMPLIANT. **Got:** COMPLIANT. Check passes, falls through to the normal gate pipeline.

**Test 3 — mismatching expected prefix (simulated mis-attached child):**
```
ERROR:WRONG_SESSION
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "expected_prefix": "The dashboard sometimes shows stale data after a user hits Save. It's intermitte", "actual_first_user_content": "What is 2+2? Answer in one sentence.", "reason": "first_user_content_prefix_mismatch"}
```
**Expected:** ERROR:WRONG_SESSION. **Got:** ERROR:WRONG_SESSION. Diag JSON includes the truncated expected prefix (80 chars), actual content preview, and the `first_user_content_prefix_mismatch` reason.

**Test 4 — empty messages with flag:**
```
ERROR:WRONG_SESSION
{"path": "/tmp/test-session-empty.json", "msg_count": 0, "expected_prefix": "X", "actual_first_user_content": "", "reason": "empty_messages"}
```
**Expected:** ERROR:WRONG_SESSION or VIOLATION:NO_ASSISTANT_RESPONSE (impl choice). **Got:** ERROR:WRONG_SESSION with `reason=empty_messages` — matches the design choice documented above (fold into WRONG_SESSION; reserve NO_ASSISTANT_RESPONSE for non-flagged invocations).

All 4 tests green.

---

## Coordination status with B.1

- **Flag name:** `--expected-prompt-prefix` (exact string).
- **Flag value format:** a raw string; typically the trial prompt text (`$TASK_TEXT`). Both space-separated (`--expected-prompt-prefix "text"`) and `=`-joined (`--expected-prompt-prefix=text`) forms accepted.
- **Prefix length constant:** 80 bytes (agreed with B.1 task spec — keep identical on both sides).
- **Byte path:** wrapper passes `$TASK_TEXT` unchanged; check.py does a plain Python string slice comparison. No normalization on either side.
- **New verdict B.1 must handle:** `ERROR:WRONG_SESSION` on line 1; line 2 is a JSON object with keys `path`, `msg_count`, `expected_prefix`, `actual_first_user_content`, `reason`. `reason` ∈ {`empty_messages`, `no_user_message`, `first_user_content_prefix_mismatch`}.
- **Existing verdicts unchanged:** B.1 does not need to touch its existing verdict-handling switch for COMPLIANT/VIOLATION:*/ERROR:FILE_NOT_FOUND/ERROR:JSON_PARSE/ERROR:USAGE.

---

## What would disprove this design

Scenarios under which the Tier 2 check would be shown to be wrong or insufficient:

1. **Bytes-differ / prefix-still-matches collision.** A child session whose first user message happens to start with the same 80-byte prefix as the trial prompt (e.g. if a worker dispatch prompt were crafted to literally embed the trial text as its preamble) would pass the check and be mis-classified as parent. Mitigation only if probed: increase `prefix_len` toward the full prompt text, or add a structural tool-shape check (e.g. child sessions dispatched via `delegate_worker_v2` contain a specific top-level user format distinct from a trial prompt).

2. **Wrapper passes the wrong prefix.** If B.1's wrapper interpolates a stale or wrong `$TASK_TEXT`, every valid parent would be flagged `WRONG_SESSION` — a Tier-2 false positive. Detectable by: first-run smoke trial after B.1 lands showing 100% WRONG_SESSION instead of 0%.

3. **Unicode / encoding drift.** If the wrapper ever writes `$TASK_TEXT` in a different encoding from what Hermes persists, the byte slices diverge and every session fails. Would show as a universal WRONG_SESSION on an otherwise-compliant sample. Mitigation: normalize to NFC on both sides (deferred; fail-loud today).

4. **Content stored as non-string / non-text-list.** A future Hermes change that stores user content as, say, a dict with a nested `text` key would pass through `_coerce_content_to_str`'s fallback `str()` path and always mis-match. Would show as a universal WRONG_SESSION.

5. **Session file still being written.** Current code inherits `json.JSONDecodeError → ERROR:JSON_PARSE`. If the wrapper races to probe a half-written file, the probe reports `JSON_PARSE`, not `WRONG_SESSION`. This is correct but worth noting: `WRONG_SESSION` only fires when the file is well-formed JSON with an array at `messages`.

6. **User message at a non-initial index IS the trial prompt.** If Hermes ever inserts a pre-trial user turn (e.g. a system-prompt-as-user), the first-user iteration picks that up instead of the trial prompt and flags `WRONG_SESSION`. We iterate `m.get("role") == "user"` in order; the first one wins. This matches the current Hermes persistence format (trial prompt == messages[0] or messages[1] when preceded by a system message). Any future harness change that injects a pre-trial synthetic user turn would need this check updated.

If smoke deployment with B.1 shows `WRONG_SESSION` firing on a clearly-valid parent (case 2 or 3), the bug is in the wrapper-side flag pass-through or encoding, not in this check — the first diagnostic is to eyeball the emitted `actual_first_user_content` vs `expected_prefix` fields on the offending session.

---

## Reconciliation with B.1 (base64 flag)

**Date:** 2026-04-19 (post-B.1, post-B.2 coordination fix)
**Scope:** Add `--expected-prompt-prefix-b64` to `probe-variantG-check.py` so it consumes the wrapper's canonical b64 form, without dropping raw-string support for direct CLI use.

### Why b64 was added

B.1 landed with the wrapper sending `--expected-prompt-prefix-b64 <base64>` through SSH. B.2 (this script) had only `--expected-prompt-prefix <raw>`. Both choices were defensible in isolation but the wrapper's decision is the right one for SSH robustness: `$TASK_TEXT` can contain newlines, single quotes, double quotes, and backticks, each of which would require brittle shell-escape gymnastics when interpolated into an `ssh_run` command. Base64 survives that path unchanged. See `probe-variantG-wrapper.sh` lines 68–78 and 174 for B.1's encoding site.

Rather than revert B.1, this reconciliation teaches check.py the b64 form. The raw form is retained unchanged for direct CLI invocations (smoke tests, humans debugging session files, anything that isn't going through SSH).

### Precedence rule

If BOTH `--expected-prompt-prefix` and `--expected-prompt-prefix-b64` are passed on the same invocation, the **b64 form wins**. Rationale: the b64 form is the wrapper's canonical form, so any conflict most plausibly originates from a caller that is experimenting with flag injection on top of an already-wrapper-driven invocation — in which case the wrapper's value should be authoritative. Documented in both the module docstring and the `_parse_argv` docstring. No error or warning is emitted on the dual-flag case (quiet precedence).

### Failure handling

On b64 decode failure (non-base64 characters, truncated input, non-UTF-8 decoded bytes), the script emits `ERROR:USAGE` with a JSON diagnostic line containing `reason=invalid_base64`, the flag name, a truncated preview of the offending value, and the underlying error string. This keeps the existing `ERROR:USAGE` verdict as the sole usage-error channel (no new verdict needed) while giving the wrapper enough detail to distinguish "bad flag value" from "wrong number of args."

### Implementation notes

- `_parse_argv` return shape changed from `(path, prefix)` to `(path, raw_prefix, b64_prefix)`. Decode and precedence resolution live in `main()` because `main()` already owns diagnostic JSON emission — keeping the b64 decode there means the `ERROR:USAGE` + reason JSON pattern is consistent with the rest of the error paths.
- Added `import base64` at module top (alongside `import json`). `base64.binascii.Error` is caught explicitly in addition to `ValueError` / `UnicodeDecodeError` because `b64decode(..., validate=True)` can raise either depending on the CPython version.
- Used `validate=True` on `b64decode` — without it, CPython silently discards non-base64 characters and happily decodes garbage, which would let a malformed wrapper argument slip through as a silent prefix mismatch.
- Docstring updated to document both flags, the precedence rule, and the `invalid_base64` diagnostic.
- No changes to any verdict string. No changes to the parent-session check helper. No changes to the existing raw-flag behavior for any of the original 4 smoke tests.

### Smoke test outputs (7 total — 3 original still passing + 4 new)

Verification tool: `python3 -m py_compile /Users/briantaylor/Projects/AgentFW/probe-variantG-check.py` → silent (OK).

**Test 1 — no flag, synthetic session → COMPLIANT.** Output matches the pre-reconciliation Test 1 byte-for-byte (baseline parity preserved).

**Test 2 — raw flag match, same session → COMPLIANT.** Output matches pre-reconciliation Test 2 byte-for-byte.

**Test 3 — raw flag mismatch → ERROR:WRONG_SESSION:**
```
ERROR:WRONG_SESSION
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "expected_prefix": "The dashboard sometimes shows stale data", "actual_first_user_content": "What is 2+2? Answer in one sentence.", "reason": "first_user_content_prefix_mismatch"}
```
Matches pre-reconciliation Test 3.

**Test 4 — b64 flag match (new):**
```
COMPLIANT
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "first_line": "", "classification_source": "v2_tool", "class_emitted": "one-shot", "tool_calls_raw": ["delegate_worker_v2"], "tool_calls": ["delegate_worker_v2"], "tool_call_count": 1, "tool_call_count_raw": 1, "hallucinated_calls": [], "delegate_task_count": 0, "delegate_worker_count": 0, "v2_call_count": 1, "v2_was_first_tool": true, "last_3_tool_errored": 0, "last_3_tool_total": 0, "final_text_preview": "", "has_completion_claim": false}
```
b64 input: `base64('What is 2+2? Answer in one sentence.')`. Decoded, matched the first user message prefix, fell through to the normal COMPLIANT path. Output byte-identical to Test 1 / Test 2 (confirms the b64 path and raw path converge to the same downstream logic once `expected_prefix` is resolved).

**Test 5 — b64 flag mismatch (new):**
```
ERROR:WRONG_SESSION
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "expected_prefix": "The dashboard sometimes shows stale data", "actual_first_user_content": "What is 2+2? Answer in one sentence.", "reason": "first_user_content_prefix_mismatch"}
```
b64 input: `base64('The dashboard sometimes shows stale data')`. Decoded, compared, mismatch, emitted `ERROR:WRONG_SESSION` with the decoded prefix visible in `expected_prefix`. Output byte-identical to Test 3 (same decoded string → same diagnostic).

**Test 6 — invalid b64 (new):**
```
ERROR:USAGE
{"reason": "invalid_base64", "flag": "--expected-prompt-prefix-b64", "value_preview": "not-valid-base64-!!!", "error": "Non-base64 digit found"}
```
b64 input: literal string `not-valid-base64-!!!` (contains `!` which is not in the base64 alphabet). `validate=True` caused `binascii.Error: Non-base64 digit found`; caught and surfaced as `ERROR:USAGE` with `reason=invalid_base64`.

**Test 7 — b64 with embedded newline (stress-test the whole reason for b64, new):**
```
ERROR:WRONG_SESSION
{"path": "/tmp/test-session-parent.json", "msg_count": 2, "expected_prefix": "Line 1\nLine 2", "actual_first_user_content": "What is 2+2? Answer in one sentence.", "reason": "first_user_content_prefix_mismatch"}
```
b64 input: `base64('Line 1\nLine 2')`. The decoded `expected_prefix` in the diagnostic JSON shows `"Line 1\nLine 2"` — the embedded newline survived the round-trip intact, which is the exact scenario raw-string SSH passing would mangle. Test 7 confirms the b64 channel preserves the bytes the wrapper intended to send. Verdict is `ERROR:WRONG_SESSION` because the test session's first user content isn't `Line 1\n...`, which is the expected outcome for a mismatch (the newline preservation is a property of the `expected_prefix` field, not the match result).

All 7 tests match expected outcomes. The original 4 (Tests 1–3 here + the original Test 4 "empty messages" case in the pre-reconciliation section above) are unchanged.

### File hashes

| Stage | MD5 |
|---|---|
| Pre-reconciliation (B.2 original) | `b9b5944dde12ff8f698c8a6be10913fb` |
| Post-reconciliation (this edit)   | `e1edfd538bd4a384595ef9c8da2dcff1` |

### Coordination state after reconciliation

- **Wrapper (B.1):** unchanged. Sends `--expected-prompt-prefix-b64 $EXPECTED_PREFIX_B64`. No further action required.
- **Check (B.2):** accepts both `--expected-prompt-prefix` (raw) and `--expected-prompt-prefix-b64` (base64 UTF-8), with b64 taking precedence if both are set. `ERROR:WRONG_SESSION` behavior is unchanged from B.2's original implementation — only the input path to `expected_prefix` has been widened.
- **Downstream verdict handlers (B.1's verdict loop):** no new verdicts. `ERROR:USAGE` is the same one it already handles, just with a richer JSON body when `reason=invalid_base64` is present. If the wrapper wants to surface invalid-b64 specifically (vs generic usage errors), it can now do so by parsing the second-line JSON for `reason=="invalid_base64"`.
