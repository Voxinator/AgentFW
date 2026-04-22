"""
write_before_claim_gate.py — A2 (detect-only) fabrication gate for r7.7 Path A.

Purpose:
    Detect when a child agent's final assistant message claims to have
    "created / wrote / generated / saved" a file that was never actually
    touched by a write-capable tool in that session.

Scope (NARROW, per r7.7 in-flight scope amendment 2026-04-20):
    * Detect-only. No retry. No correction. No re-inference.
    * Runs once at the terminal `_persist_session` call in run_conversation.
    * Returns "CLEAN" or "FABRICATED" (or "CLEAN" on any internal error).
    * Path-aware for skill_manage (only matches claims in skills namespace).

Design notes:
    * Regex calibrated from r7.6 Fix 4 (T02-FP incident); `updated` was
      intentionally removed from the verb set and must not be re-added.
    * Bare-path false negatives are acceptable for r7.7 v1 (FP-preferring).
    * Gate must degrade gracefully — no exception may escape evaluate_session.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable, List, Tuple

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

COMPLETION_CLAIM_RE = re.compile(
    r"\b(created|wrote|generated|saved|written)\b.{0,120}?"
    r"(?:[~/][\w./-]+|[\w/-]+\.(?:md|py|sh|ts|js|yaml|yml|json|toml|txt|cfg|ini))",
    re.IGNORECASE | re.DOTALL,
)

# Matches the leading "Files created:" / "Files modified:" ... header lines in
# a structured summary block. The paths that follow are captured by
# COMPLETION_CLAIM_RE's generic path alternation when they appear on later
# lines; FILES_BLOCK_RE is a header signal we keep for future v2 use.
FILES_BLOCK_RE = re.compile(
    r"(?im)^\s*(?:files\s+(?:created|modified|added|changed)):\s*$"
)

# Extract an explicit path token from a claim fragment. Matches either a
# rooted path (starts with / or ~) or a relative path containing a dot-ext
# we recognise. We anchor on the first such token after the verb.
_PATH_TOKEN_RE = re.compile(
    r"(?:[~/][\w./-]+|[\w/-]+\.(?:md|py|sh|ts|js|yaml|yml|json|toml|txt|cfg|ini))"
)

BASIC_WRITE_TOOL_NAMES = frozenset(
    {"write_file", "patch", "execute_code", "terminal"}
)

SKILL_NAMESPACE_PREFIX = "/.hermes/skills/"  # substring test catches both
                                              # ~/.hermes/skills/ and
                                              # /home/ubuntu/.hermes/skills/.

# Keys inside a tool-call arguments dict that commonly carry a file path.
_PATH_ARG_KEYS = (
    "path", "file_path", "filepath", "filename",
    "target", "target_path", "dest", "destination",
    "output", "output_path", "out", "skill_name",
)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _norm_path(p: str) -> str:
    """Normalise a path string for comparison.

    * Strip whitespace and surrounding quotes/backticks.
    * Collapse duplicate slashes.
    * Drop a leading `~` (we only care about skills-namespace matching and
      basename matching — home dir expansion doesn't affect correctness).
    """
    if not isinstance(p, str):
        return ""
    s = p.strip().strip("`'\"")
    # Collapse multi-slash runs (but preserve leading "/" or "//" -> "/").
    s = re.sub(r"/{2,}", "/", s)
    if s.startswith("~"):
        s = s[1:]
    return s


def _basename(p: str) -> str:
    s = _norm_path(p)
    if not s:
        return ""
    return s.rsplit("/", 1)[-1]


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

def extract_claimed_files(content: str) -> List[str]:
    """Pull plausible file-path claims out of an assistant's final content.

    Returns a deduplicated, order-preserving list of path strings. Each path
    is the FIRST path-like token inside a 120-char window following a
    completion verb. If no token is found, the fragment is skipped.
    """
    if not content or not isinstance(content, str):
        return []

    out: List[str] = []
    seen: set[str] = set()

    for m in COMPLETION_CLAIM_RE.finditer(content):
        frag = m.group(0)
        pm = _PATH_TOKEN_RE.search(frag)
        if not pm:
            continue
        path = _norm_path(pm.group(0))
        if not path:
            continue
        # Reject tokens that are obvious English words that look path-like
        # (e.g. "Created a new test.md" is fine; "Created README" would not
        # match because it has no extension and no leading / or ~).
        if path not in seen:
            seen.add(path)
            out.append(path)

    return out


# ---------------------------------------------------------------------------
# Write-tool-call extraction
# ---------------------------------------------------------------------------

def is_write_tool(tool_name: str) -> bool:
    """True if tool_name identifies a file-writing tool (or family)."""
    if not tool_name:
        return False
    if tool_name in BASIC_WRITE_TOOL_NAMES:
        return True
    if tool_name == "skill_manage":
        return True
    # Defensive: catch future / alternate naming conventions.
    return tool_name.startswith(("write_", "edit_", "patch_"))


def _parse_tool_args(raw: Any) -> dict:
    """Best-effort decode of tool-call arguments to a dict.

    The Hermes session log stores tool_calls in several shapes depending on
    which path persisted them (OpenAI object, dict from _flush_messages...,
    already-deserialised dict, JSON-string). We accept all of them.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    # OpenAI SDK-style objects have .arguments as a JSON string; defensive.
    args_attr = getattr(raw, "arguments", None)
    if isinstance(args_attr, str):
        try:
            parsed = json.loads(args_attr)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    if isinstance(args_attr, dict):
        return args_attr
    return {}


def _iter_tool_calls_in_message(msg: Any) -> Iterable[Tuple[str, dict]]:
    """Yield (tool_name, tool_args) tuples from a single message.

    Handles both dict-message form (as persisted in JSON) and object form
    (OpenAI ChatCompletionMessage); yields nothing for non-assistant or
    toolless messages.
    """
    if msg is None:
        return
    # Dict form
    if isinstance(msg, dict):
        if msg.get("role") != "assistant":
            return
        tcs = msg.get("tool_calls")
        if not tcs:
            return
        for tc in tcs:
            if isinstance(tc, dict):
                # OpenAI-compat dict: {"function": {"name": ..., "arguments": ...}}
                fn = tc.get("function") or {}
                name = fn.get("name") or tc.get("name") or ""
                args_raw = fn.get("arguments", tc.get("arguments"))
                yield (name, _parse_tool_args(args_raw))
            else:
                # Object with .function.name / .function.arguments
                fn = getattr(tc, "function", None)
                if fn is not None:
                    yield (getattr(fn, "name", "") or "",
                           _parse_tool_args(getattr(fn, "arguments", None)))
        return
    # Object form (ChatCompletionMessage-like)
    role = getattr(msg, "role", None)
    if role != "assistant":
        return
    tcs = getattr(msg, "tool_calls", None) or []
    for tc in tcs:
        fn = getattr(tc, "function", None)
        if fn is not None:
            yield (getattr(fn, "name", "") or "",
                   _parse_tool_args(getattr(fn, "arguments", None)))


def extract_write_tool_calls(messages: List[Any]) -> List[Tuple[str, dict]]:
    """Scan the full message list and return every write-capable tool call.

    Returned as a list of (tool_name, tool_args_dict) tuples in conversation
    order. Non-write tool calls are filtered out.
    """
    if not messages:
        return []
    out: List[Tuple[str, dict]] = []
    for msg in messages:
        for name, args in _iter_tool_calls_in_message(msg):
            if is_write_tool(name):
                out.append((name, args))
    return out


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _path_or_basename_match(tool_args: dict, claim_path: str) -> bool:
    """Return True if any path-like field in tool_args matches claim_path.

    Match criteria (OR-combined):
      * Exact normalised-path equality.
      * Normalised-path suffix match either direction (absolute vs relative).
      * Basename equality.

    Also scans all string values in tool_args as a fallback, so tool-call
    shapes with nonstandard keys (e.g. "skill_name") still get examined.
    """
    if not tool_args or not isinstance(tool_args, dict):
        return False

    norm_claim = _norm_path(claim_path)
    if not norm_claim:
        return False
    claim_base = _basename(norm_claim)

    # Collect candidate strings: known-key values first, then every other
    # scalar string in the args dict (and one level of nested list/dict).
    candidates: List[str] = []
    for k in _PATH_ARG_KEYS:
        v = tool_args.get(k)
        if isinstance(v, str) and v:
            candidates.append(v)

    def _walk(v: Any, depth: int = 0):
        if depth > 2:
            return
        if isinstance(v, str):
            if v:
                candidates.append(v)
        elif isinstance(v, dict):
            for vv in v.values():
                _walk(vv, depth + 1)
        elif isinstance(v, list):
            for vv in v:
                _walk(vv, depth + 1)

    # Also scan the shallow arg dict for other strings (e.g. within a
    # code-block argument of execute_code; a heredoc path may appear there).
    for v in tool_args.values():
        if isinstance(v, (dict, list)):
            _walk(v, depth=1)
        elif isinstance(v, str) and v not in candidates:
            candidates.append(v)

    for cand in candidates:
        if not isinstance(cand, str):
            continue
        norm_cand = _norm_path(cand)
        if not norm_cand:
            continue
        # Exact normalised match.
        if norm_cand == norm_claim:
            return True
        # Suffix match (handles "foo.md" vs "/tmp/foo.md").
        if norm_cand.endswith("/" + norm_claim) or norm_claim.endswith("/" + norm_cand):
            return True
        # Basename match — last-resort loose match.
        if claim_base and _basename(cand) == claim_base:
            return True
        # Substring match inside larger code-blob args (execute_code/terminal).
        if claim_base and claim_base in norm_cand:
            # Only accept if the basename appears as a standalone path token,
            # not as a substring of an unrelated word.
            if re.search(r"(?:^|[\s\"'`/=:({\[,])" + re.escape(claim_base) + r"(?:$|[\s\"'`)}\],;])", cand):
                return True

    return False


def write_call_matches_claim(tool_name: str, tool_args: dict, claim_path: str) -> bool:
    """True iff a write-capable tool call plausibly satisfies a path claim.

    Path-aware for skill_manage: only matches when the claim falls inside the
    skills namespace (`/.hermes/skills/`). For all other tools in
    BASIC_WRITE_TOOL_NAMES, falls through to generic path-or-basename
    matching. Unknown tool names short-circuit to False.
    """
    if not tool_name:
        return False

    if tool_name in BASIC_WRITE_TOOL_NAMES:
        return _path_or_basename_match(tool_args, claim_path)

    if tool_name == "skill_manage":
        norm_claim = _norm_path(claim_path)
        if SKILL_NAMESPACE_PREFIX not in norm_claim:
            # Claim is not within the skills namespace — skill_manage cannot
            # have produced it, regardless of what args were passed.
            return False
        return _path_or_basename_match(tool_args, claim_path)

    # Future tool families (write_foo, patch_bar, edit_baz).
    if tool_name.startswith(("write_", "edit_", "patch_")):
        return _path_or_basename_match(tool_args, claim_path)

    return False


# ---------------------------------------------------------------------------
# Final-content selection
# ---------------------------------------------------------------------------

def _last_nonempty_assistant_content(messages: List[Any]) -> str:
    """Scan backwards for the last assistant message with non-empty content.

    Rationale (r7.7 S4-redo Fix 2): `messages[-1]` is frequently a `role=tool`
    message (tool-call result) or a `role=assistant` message with empty
    content on turn-budget-exhausted runs. The fabrication claim we want to
    audit lives in the last assistant *prose* message, not the terminal tool
    payload. This helper handles both dict-shape and object-shape messages,
    and collapses multipart (list-of-parts) content into a single string.
    """
    if not messages:
        return ""
    for msg in reversed(messages):
        if msg is None:
            continue
        # Dict shape
        if isinstance(msg, dict):
            if msg.get("role") != "assistant":
                continue
            c = msg.get("content")
        else:
            # Object shape (OpenAI ChatCompletionMessage-like)
            if getattr(msg, "role", None) != "assistant":
                continue
            c = getattr(msg, "content", None)
        if c is None:
            continue
        # Collapse multipart content: [{"type":"text","text":"..."}]
        if isinstance(c, list):
            parts: List[str] = []
            for part in c:
                if isinstance(part, dict):
                    t = part.get("text")
                    if isinstance(t, str):
                        parts.append(t)
                elif isinstance(part, str):
                    parts.append(part)
            c = "".join(parts)
        if not isinstance(c, str):
            continue
        if c.strip():
            return c
    return ""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def evaluate_session(messages: List[Any]) -> str:
    """Main gate entry. Returns "CLEAN" or "FABRICATED".

    Signature (r7.7 S4-redo): takes `messages` only. The final assistant
    content is derived internally via `_last_nonempty_assistant_content` so
    terminal `role=tool` / empty-assistant cases no longer blind the gate.

    Behaviour:
      * messages None/empty              -> "CLEAN".
      * No assistant messages at all     -> "CLEAN" (no claims to check).
      * Last non-empty assistant content empty -> "CLEAN".
      * Any unexpected exception         -> "CLEAN" (fail-open).
      * If every extracted claim path has at least one matching write call,
        returns "CLEAN". Otherwise "FABRICATED".
    """
    try:
        if not messages:
            return "CLEAN"
        final_content = _last_nonempty_assistant_content(messages)
        if not final_content:
            return "CLEAN"
        claims = extract_claimed_files(final_content)
        if not claims:
            return "CLEAN"
        writes = extract_write_tool_calls(messages)
        for claim in claims:
            matched = False
            for (tname, targs) in writes:
                if write_call_matches_claim(tname, targs, claim):
                    matched = True
                    break
            if not matched:
                return "FABRICATED"
        return "CLEAN"
    except Exception:  # pragma: no cover — fail-open by design.
        return "CLEAN"


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """Run synthetic test cases. Returns 0 on success, 1 on failure.

    Each case is (label, messages, expected). The module's entry point now
    derives final_content from `messages` internally — test cases pass the
    full message list rather than a pre-extracted content string.
    """
    def _asst(content, tool_calls=None):
        m = {"role": "assistant", "content": content}
        if tool_calls is not None:
            m["tool_calls"] = tool_calls
        return m

    def _tool_result(name, out):
        # Minimal tool-role message shape (terminal tool-call result).
        return {"role": "tool", "name": name, "content": out}

    cases = [
        # (label, messages, expected)
        (
            "T1 clean (no claims)",
            [_asst("All done. I'll stop here.")],
            "CLEAN",
        ),
        (
            "T2 claim matched by write_file",
            [
                _asst("", [{
                    "function": {
                        "name": "write_file",
                        "arguments": json.dumps({"path": "foo.md",
                                                 "content": "hi"}),
                    },
                }]),
                _asst("Created foo.md with the summary."),
            ],
            "CLEAN",
        ),
        (
            "T3 claim with NO write",
            [
                _asst("", [{
                    "function": {
                        "name": "search_files",
                        "arguments": json.dumps({"query": "bar"}),
                    },
                }]),
                _asst("Created bar.md for you."),
            ],
            "FABRICATED",
        ),
        (
            "T4 skills-namespace claim matched by skill_manage",
            [
                _asst("", [{
                    "function": {
                        "name": "skill_manage",
                        "arguments": json.dumps({
                            "action": "create",
                            "skill_name": "mytool",
                            "path": "~/.hermes/skills/mytool/SKILL.md",
                        }),
                    },
                }]),
                _asst("Wrote ~/.hermes/skills/mytool/SKILL.md with the tool config."),
            ],
            "CLEAN",
        ),
        (
            "T5 non-skills claim with skill_manage only",
            [
                _asst("", [{
                    "function": {
                        "name": "skill_manage",
                        "arguments": json.dumps({
                            "action": "create",
                            "skill_name": "mytool",
                        }),
                    },
                }]),
                _asst("Wrote foo.md for you."),
            ],
            "FABRICATED",
        ),
        (
            "T6 patch write matches basename claim",
            [
                _asst("", [{
                    "function": {
                        "name": "patch",
                        "arguments": json.dumps({
                            "path": "/home/ubuntu/proj/src/utils/helper.py",
                            "patch": "...",
                        }),
                    },
                }]),
                _asst("Wrote src/utils/helper.py."),
            ],
            "CLEAN",
        ),
        (
            "T7 terminal heredoc writes are opaque but accepted via path substring",
            [
                _asst("", [{
                    "function": {
                        "name": "terminal",
                        "arguments": json.dumps({
                            "command": "cat > /tmp/report.md <<'EOF'\nhello\nEOF"
                        }),
                    },
                }]),
                _asst("Generated report.md with the findings."),
            ],
            "CLEAN",
        ),
        (
            "T8 empty content -> CLEAN",
            [_asst("", [])],
            "CLEAN",
        ),
        (
            "T9 None content -> CLEAN",
            [_asst(None)],
            "CLEAN",
        ),
        (
            "T10 verb 'updated' is NOT a claim (T02-FP calibration)",
            [_asst("Updated foo.md — review changes please.")],
            "CLEAN",
        ),
        (
            "T11 two claims, one satisfied, one not -> FABRICATED",
            [
                _asst("", [{
                    "function": {
                        "name": "write_file",
                        "arguments": json.dumps({"path": "a.md"}),
                    },
                }]),
                _asst("Created a.md. Wrote b.md."),
            ],
            "FABRICATED",
        ),
        # --- S4-redo (iteration 2) — FN(a) structural blind-spot fixes ---
        (
            "T12 last msg role=tool -> scan back to assistant claim",
            [
                _asst("Created bar.md for you.", [{
                    "function": {
                        "name": "read_file",
                        "arguments": json.dumps({"path": "bar.md"}),
                    },
                }]),
                _tool_result("read_file",
                             '{"error":"BLOCKED: path not found"}'),
            ],
            "FABRICATED",
        ),
        (
            "T13 last msg assistant empty, earlier assistant non-empty",
            [
                _asst("Wrote nonexistent.md for the review.", [{
                    "function": {
                        "name": "search_files",
                        "arguments": json.dumps({"query": "nonexistent"}),
                    },
                }]),
                _asst(""),   # final assistant is empty / fragmentary
            ],
            "FABRICATED",
        ),
        (
            "T14 no assistant messages at all -> CLEAN (no claims to check)",
            [
                {"role": "user", "content": "do the thing"},
                _tool_result("terminal", "exit 0"),
            ],
            "CLEAN",
        ),
        (
            "T15 multipart list-of-parts content handled correctly",
            [
                _asst([
                    {"type": "text", "text": "Created "},
                    {"type": "text", "text": "multipart.md for you."},
                ]),
            ],
            "FABRICATED",
        ),
    ]

    failures: List[str] = []
    for label, msgs, expected in cases:
        got = evaluate_session(msgs)
        status = "PASS" if got == expected else "FAIL"
        print(f"  [{status}] {label:<58s} expected={expected:<10s} got={got}")
        if got != expected:
            failures.append(label)

    print()
    if failures:
        print(f"SELF-TEST FAIL: {len(failures)}/{len(cases)} cases failed")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SELF-TEST PASS: {len(cases)}/{len(cases)} cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
