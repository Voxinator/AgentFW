#!/usr/bin/env python3
"""probe-variantH-check.py — gate-check a Hermes session for Variant H (r7.6-P1A) compliance.

Variant H = Variant G + Gemma-MoE chat-template correctness:
  - Gemma parser prefix-tolerant fallback (inv-3 F3A'): see probe-variantH-stage.sh Change 1.
    Runtime-only effect on tool_call extraction; no check-side consequence.
  - Channel-marker content normalizer + empty-synthesis detection (inv-2 G1+G2):
    Runtime fix at run_agent.py:~8908-8936 routes channel-marker-only pollution
    to a synthetic "[child session exited with no synthesis — content was
    channel-marker pollution only]" trailer instead of back-patching. The
    check-side component (G2) detects the same pattern on child session JSONs
    and emits VIOLATION:EMPTY_SYNTHESIS.

Differences from probe-variantG-check.py:
  - New VIOLATION:EMPTY_SYNTHESIS verdict (inv-2 G2) fires on CHILD sessions
    whose terminal state is (a) last assistant content empty or channel-marker-
    only, OR (b) last assistant content is a Hermes back-patched "Calling the X
    tool..." stub AND any preceding assistant's content is empty / channel-
    marker polluted — AND the session's final assistant tool_calls do NOT
    contain delegate_* or write-type tools (which would indicate productive
    intent that merely got truncated).
  - Parent-session detection skips EMPTY_SYNTHESIS: if --expected-prompt-prefix
    is provided (wrapper-side parent verification), we are scoring a parent
    session and EMPTY_SYNTHESIS does not apply.
  - NEW VIOLATION:FABRICATION:NO_WRITE_TOOL verdict (P1-B) fires on CHILD
    sessions whose final assistant content claims to have written file(s) via
    past-tense write verb + file-path token (or a markdown "Files created:"
    block header) AND the session contains ZERO write-type tool calls AND
    ZERO delegate tool calls. Two detector call sites: (a) inside the
    cls-is-None branch BEFORE NO_MARKER (handles children without TASK CLASS
    markers); (b) AFTER existing FABRICATION, BEFORE COMPLIANT (handles any
    classified session). Existing FABRICATION (tool-errors+claim) wins on
    ties, preserving backward-compat labeling.
  - All r7.5 (Variant G) verdicts and gate logic unchanged.

Usage: python3 probe-variantH-check.py [--expected-prompt-prefix "<prefix>"
                                        | --expected-prompt-prefix-b64 "<base64>"]
                                       <session_path>

The `--expected-prompt-prefix-b64` form base64-decodes (UTF-8) its value before
comparison. When BOTH flags are provided, the b64 form wins.

Output (single line, machine-readable):
  COMPLIANT
  VIOLATION:NO_MARKER
  VIOLATION:NO_DISPATCH:<class>
  VIOLATION:ROLE_COLLAPSE:<class>
  VIOLATION:EMPTY_SYNTHESIS              (NEW — child sessions only; inv-2 G2)
  VIOLATION:FABRICATION
  VIOLATION:FABRICATION:NO_WRITE_TOOL    (NEW — child sessions only; P1-B)
  VIOLATION:NO_ASSISTANT_RESPONSE
  ERROR:WRONG_SESSION
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

# === P1-B FABRICATION:NO_WRITE_TOOL CONSTANTS + HELPERS (inserted by merge worker) ===
#
# Detects a fabrication-without-tool-error mode observed in r7.5 trials 18 and 20
# (T10 / long-horizon): the child emits a coherent-looking completion summary
# naming a file-path artifact it never actually wrote (the session contains zero
# write-type tool calls). This is a strict superset of the existing FABRICATION
# detector (which requires recent tool errors). Emits a distinct suffix so the
# two paths remain separable for downstream analysis.
#
# NOTE: P1-A's artifact placed ONLY the Anchor B (detector-location) placeholder.
# Anchor A (constants+helpers location) was missing; this block was added at the
# correct module-level position by the merge worker per P1-B's design intent.

# Write-type tool name allowlist (explicit) + prefix heuristic (defensive).
WRITE_TOOL_NAMES = frozenset({
    "write_file", "patch", "execute_code", "terminal", "skill_manage",
    "edit_file", "apply_diff",  # defensive: not currently bound, but future-proof
})

_WRITE_TOOL_PREFIXES = ("write_", "edit_", "patch_")


def is_write_tool(name):
    """True iff name is a known write-type tool or matches a write-like prefix."""
    if not name:
        return False
    if name in WRITE_TOOL_NAMES:
        return True
    return name.startswith(_WRITE_TOOL_PREFIXES)


# Completion-claim regex: past-tense write verb within 120 chars of a file-path token.
# Path token = absolute path (starts with '/' or '~/') OR a bare token with a known
# code/doc file extension. The 120-char window keeps the match tight enough that
# abstract claims ("I created a plan.") don't sweep in distant unrelated paths.
#
# P1-B' tightening (r7.6): the verb "updated" was REMOVED from the verb set
# after the merge-verifier caught a T02 false positive where "updated" appeared
# as a past-participle adjective ("the updated session management") inside an
# unchecked markdown todo item, within 120 chars of `tests/auth.test.ts`. The
# other past-tense verbs ("created", "wrote", "generated", "saved", "written")
# are far less prone to adjectival use. The campaign rule is "simpler is better,
# false positives are worse than false negatives"; r7.5 evidence contains zero
# "Updated X" fabrications (both true positives — trials 18 and 20 — fire via
# "Created" / "Generated" only), so removal costs no measurable recall.
COMPLETION_CLAIM_RE = re.compile(
    r"\b(created|wrote|generated|saved|written)\b.{0,120}?"
    r"(?:[~/][\w./-]+|[\w/-]+\.(?:md|py|sh|ts|js|yaml|yml|json|toml|txt|cfg|ini))",
    re.IGNORECASE | re.DOTALL,
)

# Markdown-aware "Files created:" / "Files modified:" block header.
# Matches leading whitespace + optional ** or __ bold wrappers on each side.
FILES_BLOCK_RE = re.compile(
    r"(?im)^\s*(?:\*{0,2}|_{0,2})\s*files?\s+"
    r"(?:created|modified|added|changed|written|generated):\s*(?:\*{0,2}|_{0,2})\s*$",
)


def final_assistant_text_raw(messages):
    """Return original-case content of the final assistant message, or ''."""
    for m in reversed(messages):
        if m.get("role") == "assistant":
            return m.get("content") or ""
    return ""


def extract_claimed_paths(text):
    """Return list of file-path-like tokens that appear within a completion claim.

    Uses COMPLETION_CLAIM_RE (anchored on a write verb + nearby path) and a
    secondary scan for tokens in the 300-char window following a FILES_BLOCK_RE
    header. Conservative: de-duplicates, caps at 10 paths (enough for diag).
    """
    paths = []
    # Primary: write-verb-proximate paths.
    for m in COMPLETION_CLAIM_RE.finditer(text):
        span = text[m.start(): m.end()]
        # Re-extract just the path-like suffix from the matched span.
        tail = re.search(
            r"(?:[~/][\w./-]+|[\w/-]+\.(?:md|py|sh|ts|js|yaml|yml|json|toml|txt|cfg|ini))",
            span,
        )
        if tail and tail.group(0) not in paths:
            paths.append(tail.group(0))
    # Secondary: files-block-followed tokens.
    for m in FILES_BLOCK_RE.finditer(text):
        window = text[m.end(): m.end() + 300]
        for pm in re.finditer(
            r"[`'\"]?((?:[~/][\w./-]+|[\w/-]+\.(?:md|py|sh|ts|js|yaml|yml|json|toml|txt|cfg|ini)))[`'\"]?",
            window,
        ):
            if pm.group(1) not in paths:
                paths.append(pm.group(1))
    return paths[:10]


def looks_like_child_session(messages):
    """Heuristic: parent sessions invoke delegate_worker_v2; children do not.

    Returns True iff the session contains ZERO delegate_worker_v2 / delegate_worker /
    delegate_task tool calls. This matches every r7.5 child session observed and
    zero of the r7.5 parent sessions observed. A parent that somehow reaches the
    NO_WRITE_TOOL condition is flagged separately (see main()).
    """
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function") or {}
            if fn.get("name") in ALL_DISPATCH_TOOLS:
                return False
    return True


def try_detect_fabrication_no_write_tool(messages, calls, diag):
    """Shared detection logic for FABRICATION:NO_WRITE_TOOL.

    Populates `diag` with write_tool_call_count, has_nowrite_completion_claim,
    and (when all conditions met) claimed_files + claim_sentence.
    Returns True iff the verdict should be emitted (caller prints and returns).
    False means either the claim didn't match, writes were present, or the
    session is not child-shaped.

    Called from TWO locations in main()'s cascade:
    1. Inside the `cls is None` branch BEFORE VIOLATION:NO_MARKER (children
       without TASK CLASS markers would otherwise short-circuit to NO_MARKER
       and miss this detection).
    2. AFTER the existing tool-error FABRICATION block, BEFORE COMPLIANT
       (for future-proofing: children that DO emit class markers, or
       parent-style sessions where the cascade reaches this far).
    """
    final_text_raw = final_assistant_text_raw(messages)
    claim_match = COMPLETION_CLAIM_RE.search(final_text_raw)
    files_block_match = FILES_BLOCK_RE.search(final_text_raw)
    has_nowrite_claim = bool(claim_match or files_block_match)
    write_tool_call_count = sum(1 for c in calls if is_write_tool(c))
    diag["write_tool_call_count"] = write_tool_call_count
    diag["has_nowrite_completion_claim"] = has_nowrite_claim

    if has_nowrite_claim and write_tool_call_count == 0:
        claimed_files = extract_claimed_paths(final_text_raw)
        diag["claimed_files"] = claimed_files
        anchor = claim_match or files_block_match
        start = max(0, anchor.start() - 40)
        diag["claim_sentence"] = final_text_raw[start: start + 200]
        if looks_like_child_session(messages):
            return True
        else:
            diag["note"] = "PARENT_FABRICATION_UNEXPECTED"
    return False

# === END P1-B helpers ===


# --- inv-2 G2 empty-synthesis detector constants --------------------------

# Harmony/Gemma channel-marker regex. Matches assistant content whose ENTIRE
# textual payload is chat-template channel-marker leakage. Accepts variants:
#   "<channel|>"                  (bare closer)
#   "thought\n<channel|>"         (thought-channel leak)
#   "<|channel>thought\n<channel|>"  (both bookends)
#   "<channel|>thought\n<channel|>"  (pair)
#   "<|channel|>"                 (pipe-pair form)
# Plus arbitrary whitespace. Kept intentionally narrow — if the content has any
# real prose alongside the markers, we do NOT call it polluted (that's a
# DIFFERENT failure mode — FABRICATION or COMPLIANT as appropriate).
_CHANNEL_MARKER_ONLY_REGEX = re.compile(
    r"^\s*(?:"
    r"(?:<\|?channel\|?>\s*)"
    r"|(?:thought\s*<\|?channel\|?>\s*)"
    r"|(?:<\|?channel\|?>\s*thought\s*<\|?channel\|?>\s*)"
    r"|(?:<\|channel\|>\s*thought\s*<channel\|>\s*)"
    r"|(?:<channel\|>\s*thought\s*<channel\|>\s*)"
    r")+\s*$",
    re.IGNORECASE | re.DOTALL,
)

# Hermes empty-follow-up back-patch stub. When the final assistant turn is
# content-empty and no structured fallback runs, Hermes (pre-G1) back-patches
# the penultimate tool-calling assistant's content to this string. Presence of
# this stub as the LAST assistant content indicates the session was truncated
# via the back-patch path — we then look PAST it at earlier assistants to
# decide if the underlying cause was channel-marker pollution.
_BACKPATCH_STUB_REGEX = re.compile(
    r"^Calling the .+? tools?\.\.\.$",
    re.DOTALL,
)

# Tool names considered "productive" — their presence as a final tool_call
# indicates the session was mid-productive-action at end (e.g. a delegate or
# write call was emitted but the wrapper's tool-result handler cut short).
# EMPTY_SYNTHESIS should NOT fire in this case because the failure is not
# "model produced nothing useful" but "pipeline cut a productive action short."
_PRODUCTIVE_FINAL_TOOLS = frozenset([
    "delegate_task", "delegate_worker", "delegate_worker_v2",
    "write_file", "patch", "execute_code", "skill_manage",
])


def _content_is_only_channel_markers(s):
    """Return True iff string is empty OR consists only of harmony/Gemma
    channel-marker tokens (with whitespace). Used by G2 detector to classify
    polluted assistant content without touching COMPLETION claims (which
    would be a different failure mode — FABRICATION).
    """
    if s is None:
        return True
    if not isinstance(s, str):
        s = str(s)
    if s.strip() == "":
        return True
    return bool(_CHANNEL_MARKER_ONLY_REGEX.match(s))


def _is_backpatch_stub(s):
    """Detect Hermes' empty-follow-up back-patch marker (pre-G1 sessions)."""
    if not isinstance(s, str):
        return False
    return bool(_BACKPATCH_STUB_REGEX.match(s.strip()))


def _last_assistant_and_chain(messages):
    """Return (last_assistant, assistants_in_order) pair.

    last_assistant is the final assistant message (or None).
    assistants_in_order is the full ordered list of assistant messages (may be empty).
    """
    assistants = [m for m in messages if m.get("role") == "assistant"]
    return (assistants[-1] if assistants else None), assistants


def _final_action_is_productive(last_asst):
    """Return True iff the last assistant's tool_calls contain at least one
    productive (delegate_* or write-type) tool. A productive final action means
    EMPTY_SYNTHESIS does NOT fire — the model had real intent.
    """
    if not last_asst:
        return False
    tcs = last_asst.get("tool_calls") or []
    for tc in tcs:
        if not isinstance(tc, dict):
            continue
        fn = (tc.get("function") or {}).get("name") or ""
        if fn in _PRODUCTIVE_FINAL_TOOLS:
            return True
    return False


def detect_empty_synthesis(messages):
    """Inv-2 G2 empty-synthesis detector (child sessions only).

    Returns (fires: bool, diag_fields: dict). diag_fields includes the raw
    content samples used in the decision so the caller can json.dumps them
    into the verdict output.

    Logic:
      1. If last assistant content is channel-marker-only (includes empty),
         AND final action is NOT productive → EMPTY_SYNTHESIS fires.
      2. If last assistant content matches the back-patch stub
         ("Calling the X tool..."), AND any preceding assistant's content is
         channel-marker-only, AND final action is NOT productive
         → EMPTY_SYNTHESIS fires.
      3. Otherwise does not fire.
    """
    last_asst, assistants = _last_assistant_and_chain(messages)
    diag = {
        "last_assistant_present": last_asst is not None,
        "assistant_count": len(assistants),
    }
    if last_asst is None:
        diag["reason"] = "no_assistant_messages"
        return False, diag  # No assistant at all → covered by NO_ASSISTANT_RESPONSE

    last_content = last_asst.get("content") or ""
    diag["last_content_preview"] = last_content[:200]
    diag["final_action_productive"] = _final_action_is_productive(last_asst)

    # Rule 1: direct channel-marker-only last assistant.
    if _content_is_only_channel_markers(last_content):
        diag["trigger"] = "direct_channel_marker_only"
        if diag["final_action_productive"]:
            diag["reason"] = "productive_final_action_suppresses"
            return False, diag
        return True, diag

    # Rule 2: back-patch stub AS last assistant content means Hermes' empty-
    # follow-up fallback fired. Dig into penultimate / earlier assistants to
    # see if any had channel-marker-only content (the ACTUAL pollution).
    if _is_backpatch_stub(last_content):
        diag["trigger"] = "backpatch_stub_detected"
        polluted_preceding = []
        for a in assistants[:-1]:
            ac = a.get("content") or ""
            if _content_is_only_channel_markers(ac):
                polluted_preceding.append(ac[:80])
        diag["polluted_preceding_count"] = len(polluted_preceding)
        diag["polluted_preceding_samples"] = polluted_preceding[:3]
        if polluted_preceding:
            if diag["final_action_productive"]:
                diag["reason"] = "productive_final_action_suppresses"
                return False, diag
            return True, diag

    diag["reason"] = "no_empty_synthesis_pattern"
    return False, diag


# --- end inv-2 G2 helpers -------------------------------------------------


def first_assistant(messages):
    for m in messages:
        if m.get("role") == "assistant":
            return m
    return None


def _coerce_content_to_str(content):
    """Coerce a message.content value to a string for byte-prefix comparison."""
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
    """Return True iff the first user-role message content starts with expected_prefix."""
    first_user = next((m for m in messages if m.get("role") == "user"), None)
    if first_user is None:
        return False
    content = _coerce_content_to_str(first_user.get("content"))
    return content[:prefix_len] == (expected_prefix or "")[:prefix_len]


def _first_user_content_preview(messages, n=80):
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
    calls = []
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function") or {}
            calls.append(fn.get("name", ""))
    return calls


def _call_was_rejected(messages, start_idx, tool_call_id, fn_name):
    prefix = f"Tool '{fn_name}' does not exist"
    for nm in messages[start_idx + 1:]:
        if nm.get("role") != "tool":
            continue
        nm_id = nm.get("tool_call_id")
        if tool_call_id is not None and nm_id is not None:
            if nm_id != tool_call_id:
                continue
            return str(nm.get("content", "")).startswith(prefix)
        return str(nm.get("content", "")).startswith(prefix)
    return False


def all_bound_tool_calls(messages):
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

    # Parent-session structural check (parent context only).
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

    # Child-context vs parent-context discrimination.
    # When --expected-prompt-prefix is PRESENT, we already verified this is a
    # parent session (via check_parent_session above). Skip EMPTY_SYNTHESIS.
    # When absent, the session could be a child OR a parent that wasn't
    # wrapper-launched. EMPTY_SYNTHESIS is structurally safe to run in either
    # case — parents never end in the child-session pattern (they emit clean
    # final prose after tool results). But we still gate it on cls == None
    # as a conservative belt-and-suspenders: parent sessions always emit a
    # TASK CLASS marker under variantG; children don't.
    is_parent_context = expected_prefix is not None

    if cls is None:
        # Parent sessions under variantG MUST emit a classification (via v2
        # tool call or text marker). Absent classification is NO_MARKER for
        # parent context. For child context, try EMPTY_SYNTHESIS first (it's
        # a more specific failure mode).
        if not is_parent_context:
            es_fires, es_diag = detect_empty_synthesis(messages)
            if es_fires:
                diag["empty_synthesis_diag"] = es_diag
                print("VIOLATION:EMPTY_SYNTHESIS")
                print(json.dumps(diag))
                return 0
            # Cascade coordination (merge worker): children without TASK CLASS
            # markers would otherwise short-circuit to VIOLATION:NO_MARKER and
            # miss the NO_WRITE_TOOL detector at Anchor B. Run the shared
            # detection helper here before NO_MARKER emit.
            if try_detect_fabrication_no_write_tool(messages, calls, diag):
                print("VIOLATION:FABRICATION:NO_WRITE_TOOL")
                print(json.dumps(diag))
                return 0
        print("VIOLATION:NO_MARKER")
        print(json.dumps(diag))
        return 0

    if cls in ("structured", "long-horizon"):
        dispatch_idx = next(
            (i for i, c in enumerate(calls) if c in ALL_DISPATCH_TOOLS), None
        )
        diag["dispatch_idx"] = dispatch_idx

        if dispatch_idx is None:
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

    # --- inv-2 G2: EMPTY_SYNTHESIS on child sessions ---
    # Placed between ROLE_COLLAPSE and FABRICATION per task spec. For child
    # sessions with classification emitted (e.g. via text marker), we still
    # want to catch the empty-synthesis terminal state.
    if not is_parent_context:
        es_fires, es_diag = detect_empty_synthesis(messages)
        if es_fires:
            diag["empty_synthesis_diag"] = es_diag
            print("VIOLATION:EMPTY_SYNTHESIS")
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

    # === P1-B FABRICATION:NO_WRITE_TOOL DETECTION (Anchor B) ===
    # Relocated by merge worker from P1-A's misplaced anchor (pre-FABRICATION)
    # to P1-B's intended semantic location: AFTER existing FABRICATION (so
    # tool-errors+claim wins on ties for backward-compat labeling) and BEFORE
    # COMPLIANT. For children without TASK CLASS markers, the SAME detector
    # also runs earlier in the cls-is-None branch (see cascade coordination
    # note above) to avoid being short-circuited by VIOLATION:NO_MARKER.
    if try_detect_fabrication_no_write_tool(messages, calls, diag):
        print("VIOLATION:FABRICATION:NO_WRITE_TOOL")
        print(json.dumps(diag))
        return 0
    # === END P1-B detector (Anchor B) ===

    print("COMPLIANT")
    print(json.dumps(diag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
