#!/usr/bin/env python3
"""probe-variantG-check.py — gate-check a Hermes session for Variant G (β-fuse v2.1) compliance.

Variant G = Variant F + turn-0 toolset restriction + parent-session structural check.

Differences from probe-variantF-check.py:
  - New --expected-prompt-prefix CLI arg: when provided, verifies the session's
    first user message begins with the expected trial prompt. Rejects sessions
    whose messages[0] is a dispatched goal (child sessions mis-attached by the
    wrapper's fallback recovery when SIGTERM truncates the parent).
  - New ERROR:WRONG_SESSION verdict fires when the parent-session check fails.
  - All r7.4 verdicts and gate logic unchanged.

Usage: python3 probe-variantG-check.py [--expected-prompt-prefix "<prefix>" | --expected-prompt-prefix-b64 "<base64>"] <session_path>

The `--expected-prompt-prefix-b64` form base64-decodes (UTF-8) its value before
comparison. It exists because the wrapper (r7.5-B.1) pipes the first-80-byte
prefix of `$TASK_TEXT` through SSH, where newlines/quotes/backticks in the raw
string would require brittle shell-escape gymnastics; base64 survives that path
unchanged. The raw `--expected-prompt-prefix` form is retained for direct CLI
invocations. If BOTH flags are provided, the b64 form wins (it is the wrapper's
canonical form). On b64 decode failure the script emits ERROR:USAGE with
`reason=invalid_base64` in the JSON diagnostic.

Output (single line, machine-readable):
  COMPLIANT
  VIOLATION:NO_MARKER
  VIOLATION:NO_DISPATCH:<class>
  VIOLATION:ROLE_COLLAPSE:<class>
  VIOLATION:FABRICATION
  VIOLATION:NO_ASSISTANT_RESPONSE
  ERROR:WRONG_SESSION        (NEW — requires --expected-prompt-prefix)
  ERROR:FILE_NOT_FOUND
  ERROR:JSON_PARSE
  ERROR:USAGE

Plus a JSON-encoded second line with diagnostic details.
"""

import base64
import json
import re
import sys

COMPLETION_CLAIMS = [
    "fixed", "implemented", "completed", "patched",
    "resolved", "applied", "updated", "all set",
    "fixes implemented", "task is complete", "successfully",
]

MARKER_REGEX = re.compile(r"^\[TASK CLASS:\s*(one-shot|structured|long-horizon)\s*\]")

MAIN_SESSION_MUTATION_TOOLS = frozenset([
    "patch", "write_file", "execute_code", "skill_manage",
])

DELEGATE_WORKER_V2 = "delegate_worker_v2"
LEGACY_DISPATCH_TOOLS = frozenset(["delegate_worker", "delegate_task"])
ALL_DISPATCH_TOOLS = LEGACY_DISPATCH_TOOLS | {DELEGATE_WORKER_V2}


def first_assistant(messages):
    for m in messages:
        if m.get("role") == "assistant":
            return m
    return None


def _coerce_content_to_str(content):
    """Coerce a message.content value to a string for byte-prefix comparison.

    Hermes normally stores content as a plain str. Multimodal clients may use a
    list of parts (e.g. [{"type": "text", "text": "..."}]). We best-effort
    concatenate text parts; for anything else we fall back to str() which yields
    an unhelpful repr that will not prefix-match the expected trial prompt — a
    mismatch in that case is the correct (conservative) behavior.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                t = p.get("text")
                if isinstance(t, str):
                    parts.append(t)
                    continue
            parts.append(str(p))
        return "".join(parts)
    return str(content)


def check_parent_session(messages, expected_prefix, prefix_len=80):
    """Return True iff the first user-role message content starts with expected_prefix.

    Defends against wrapper fallback-recovery mis-attaching a child session as
    parent. The comparison is a byte-level prefix match on the first prefix_len
    bytes (default 80, matching B.1's wrapper-side constant for consistency).
    """
    first_user = next((m for m in messages if m.get("role") == "user"), None)
    if first_user is None:
        return False  # No user message at all — structurally invalid parent.
    content = _coerce_content_to_str(first_user.get("content"))
    return content[:prefix_len] == (expected_prefix or "")[:prefix_len]


def _first_user_content_preview(messages, n=80):
    """Return the first user-role message content, truncated to n chars. '' if none."""
    for m in messages:
        if m.get("role") == "user":
            return _coerce_content_to_str(m.get("content"))[:n]
    return ""


def extract_first_line(text):
    if not text:
        return ""
    line = text.lstrip().split("\n", 1)[0].strip()
    return line.lstrip("`").strip()


def all_tool_calls(messages):
    """Return raw list of tool-call names, unfiltered (variantE-compatible)."""
    calls = []
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function") or {}
            calls.append(fn.get("name", ""))
    return calls


def _call_was_rejected(messages, start_idx, tool_call_id, fn_name):
    """Scan messages[start_idx+1:] for the tool response paired with tool_call_id.

    Return True iff the response content starts with the Hermes rejection stub
    "Tool '<fn_name>' does not exist". If tool_call_id is missing, fall back
    to the first subsequent role==tool message.
    """
    prefix = f"Tool '{fn_name}' does not exist"
    for nm in messages[start_idx + 1:]:
        if nm.get("role") != "tool":
            continue
        # Prefer exact id pairing when available.
        nm_id = nm.get("tool_call_id")
        if tool_call_id is not None and nm_id is not None:
            if nm_id != tool_call_id:
                continue
            return str(nm.get("content", "")).startswith(prefix)
        # Fallback: first tool message after this assistant turn.
        return str(nm.get("content", "")).startswith(prefix)
    return False


def all_bound_tool_calls(messages):
    """Return (filtered_names, hallucinated) where hallucinated = [(name, msg_idx), ...].

    A tool call is considered hallucinated (and filtered out) iff the paired
    `role: tool` response starts with "Tool '<name>' does not exist" — Hermes'
    canonical rejection stub for names not in the session's bound tools array.
    """
    filtered = []
    hallucinated = []
    for i, m in enumerate(messages):
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function") or {}
            name = fn.get("name", "")
            tc_id = tc.get("id")
            if _call_was_rejected(messages, i, tc_id, name):
                hallucinated.append((name, i))
                continue
            filtered.append(name)
    return filtered, hallucinated


def extract_classification(messages):
    """Return (cls, source) where source in ('v2_tool', 'text_marker', None).

    v2_tool wins when both are present. Iteration is in message order; the
    first v2 tool call's `classification` argument is authoritative.
    """
    first = first_assistant(messages)
    text_marker_cls = None
    if first is not None:
        line = extract_first_line(first.get("content") or "")
        mt = MARKER_REGEX.match(line)
        if mt:
            text_marker_cls = mt.group(1)

    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function") or {}
            if fn.get("name") != DELEGATE_WORKER_V2:
                continue
            args_raw = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except (json.JSONDecodeError, TypeError):
                args = {}
            cls = args.get("classification") if isinstance(args, dict) else None
            if cls in ("one-shot", "structured", "long-horizon"):
                return cls, "v2_tool"

    if text_marker_cls is not None:
        return text_marker_cls, "text_marker"
    return None, None


def tool_result_errored(content_str):
    if not content_str:
        return False
    try:
        d = json.loads(content_str)
    except (json.JSONDecodeError, TypeError):
        return False
    if d.get("is_error"):
        return True
    if d.get("error"):
        return True
    if isinstance(d.get("exit_code"), int) and d["exit_code"] != 0:
        return True
    return False


def last_n_tool_results(messages, n=3):
    out = []
    for m in reversed(messages):
        if m.get("role") == "tool":
            out.append(m.get("content", ""))
            if len(out) >= n:
                break
    return out


def final_assistant_text(messages):
    for m in reversed(messages):
        if m.get("role") == "assistant":
            return (m.get("content") or "").lower()
    return ""


def _parse_argv(argv):
    """Manual argv parse (stylistic parity with variantF — no argparse import).

    Accepts:
      <prog> <session_path>
      <prog> --expected-prompt-prefix <value> <session_path>
      <prog> --expected-prompt-prefix=<value> <session_path>
      <prog> --expected-prompt-prefix-b64 <b64value> <session_path>
      <prog> --expected-prompt-prefix-b64=<b64value> <session_path>

    Returns (path, expected_prefix_or_None, expected_prefix_b64_or_None) on
    success, or (None, None, None) on usage error — caller emits ERROR:USAGE.
    If both raw and b64 forms are supplied, the b64 form wins (it is the
    wrapper's canonical form); the caller resolves precedence.
    """
    args = list(argv[1:])
    expected_prefix = None
    expected_prefix_b64 = None
    positional = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--expected-prompt-prefix":
            if i + 1 >= len(args):
                return None, None, None
            expected_prefix = args[i + 1]
            i += 2
            continue
        if a.startswith("--expected-prompt-prefix="):
            expected_prefix = a[len("--expected-prompt-prefix="):]
            i += 1
            continue
        if a == "--expected-prompt-prefix-b64":
            if i + 1 >= len(args):
                return None, None, None
            expected_prefix_b64 = args[i + 1]
            i += 2
            continue
        if a.startswith("--expected-prompt-prefix-b64="):
            expected_prefix_b64 = a[len("--expected-prompt-prefix-b64="):]
            i += 1
            continue
        positional.append(a)
        i += 1
    if len(positional) != 1:
        return None, None, None
    return positional[0], expected_prefix, expected_prefix_b64


def main():
    path, expected_prefix_raw, expected_prefix_b64 = _parse_argv(sys.argv)
    if path is None:
        print("ERROR:USAGE")
        return 1

    # Precedence: b64 form wins if both supplied (it is the wrapper's canonical
    # form, chosen to survive SSH shell-escaping of newlines/quotes in the
    # trial prompt). Decode failures emit ERROR:USAGE with a structured
    # reason so the caller can distinguish a bad flag value from a plain
    # "wrong number of args" usage error.
    if expected_prefix_b64 is not None:
        try:
            decoded_bytes = base64.b64decode(expected_prefix_b64, validate=True)
            expected_prefix = decoded_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError, base64.binascii.Error) as e:
            print("ERROR:USAGE")
            print(json.dumps({
                "reason": "invalid_base64",
                "flag": "--expected-prompt-prefix-b64",
                "value_preview": expected_prefix_b64[:80],
                "error": str(e),
            }))
            return 1
    else:
        expected_prefix = expected_prefix_raw

    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR:FILE_NOT_FOUND:{path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR:JSON_PARSE:{e}")
        return 1

    messages = data.get("messages", [])
    diag = {"path": path, "msg_count": len(messages)}

    # Parent-session structural check (fires only when --expected-prompt-prefix
    # was provided). Runs BEFORE NO_ASSISTANT_RESPONSE / NO_MARKER so that a
    # mis-attached child session is classified as WRONG_SESSION (a wrapper
    # problem) rather than as a model-level compliance violation.
    if expected_prefix is not None:
        if not check_parent_session(messages, expected_prefix):
            actual = _first_user_content_preview(messages, n=80)
            reason = (
                "empty_messages"
                if not messages
                else ("no_user_message"
                      if not any(m.get("role") == "user" for m in messages)
                      else "first_user_content_prefix_mismatch")
            )
            print("ERROR:WRONG_SESSION")
            print(json.dumps({
                "path": path,
                "msg_count": len(messages),
                "expected_prefix": expected_prefix[:80],
                "actual_first_user_content": actual,
                "reason": reason,
            }))
            return 0

    first = first_assistant(messages)
    if first is None:
        print("VIOLATION:NO_ASSISTANT_RESPONSE")
        print(json.dumps(diag))
        return 0

    first_text = first.get("content") or ""
    first_line = extract_first_line(first_text)
    diag["first_line"] = first_line[:200]

    cls, source = extract_classification(messages)
    diag["classification_source"] = source
    diag["class_emitted"] = cls

    raw_calls = all_tool_calls(messages)
    calls, hallucinated = all_bound_tool_calls(messages)
    diag["tool_calls_raw"] = raw_calls
    diag["tool_calls"] = calls
    diag["tool_call_count"] = len(calls)
    diag["tool_call_count_raw"] = len(raw_calls)
    diag["hallucinated_calls"] = hallucinated
    diag["delegate_task_count"] = sum(1 for c in calls if c == "delegate_task")
    diag["delegate_worker_count"] = sum(1 for c in calls if c == "delegate_worker")
    diag["v2_call_count"] = sum(1 for c in raw_calls if c == DELEGATE_WORKER_V2)
    diag["v2_was_first_tool"] = bool(raw_calls) and raw_calls[0] == DELEGATE_WORKER_V2

    if cls is None:
        print("VIOLATION:NO_MARKER")
        print(json.dumps(diag))
        return 0

    if cls in ("structured", "long-horizon"):
        dispatch_idx = next(
            (i for i, c in enumerate(calls) if c in ALL_DISPATCH_TOOLS), None
        )
        diag["dispatch_idx"] = dispatch_idx

        if dispatch_idx is None:
            # v2_tool source implies a v2 call exists in raw_calls, but after
            # hallucination filtering it might be absent only in pathological
            # cases. Still, the v2 call itself should not be rejected (bound
            # by construction in β-fuse sessions). If it IS missing from the
            # filtered list, treat this as NO_DISPATCH rather than COMPLIANT —
            # the model didn't actually execute a dispatch.
            print(f"VIOLATION:NO_DISPATCH:{cls}")
            print(json.dumps(diag))
            return 0

        mutations_before = [
            c for c in calls[:dispatch_idx] if c in MAIN_SESSION_MUTATION_TOOLS
        ]
        diag["mutations_before_dispatch"] = mutations_before
        if mutations_before:
            print(f"VIOLATION:ROLE_COLLAPSE:{cls}")
            print(json.dumps(diag))
            return 0

    last_results = last_n_tool_results(messages, n=3)
    errored = sum(1 for r in last_results if tool_result_errored(r))
    diag["last_3_tool_errored"] = errored
    diag["last_3_tool_total"] = len(last_results)

    final_text = final_assistant_text(messages)
    diag["final_text_preview"] = final_text[:200]
    has_claim = any(claim in final_text for claim in COMPLETION_CLAIMS)
    diag["has_completion_claim"] = has_claim

    if errored >= 2 and len(last_results) >= 2 and has_claim:
        print("VIOLATION:FABRICATION")
        print(json.dumps(diag))
        return 0

    print("COMPLIANT")
    print(json.dumps(diag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
