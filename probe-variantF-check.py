#!/usr/bin/env python3
"""probe-variantF-check.py — gate-check a Hermes session for Variant F (β-fuse) compliance.

Variant F = Variant E's structure + Layer 3 β-fuse: classification is fused into
the `delegate_worker_v2` tool call. The v2 call IS the dispatch (for
structured/long-horizon) and IS the marker (for all classes).

Differences from probe-variantE-check.py:
  - Classification source is v2 tool-call args first, legacy text-marker fallback.
  - Hallucinated tool calls (those Hermes rejected with "Tool 'X' does not exist")
    are filtered from the analyzed tool-call sequence. This fixes the r7.3 probe
    labeling artifact where rejected `terminal` calls were counted as "first tool".
  - New diagnostics: classification_source, v2_call_count, v2_was_first_tool,
    hallucinated_calls.

Usage: python3 probe-variantF-check.py <session_path>
"""

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


def main():
    if len(sys.argv) != 2:
        print("ERROR:USAGE")
        return 1
    path = sys.argv[1]
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
