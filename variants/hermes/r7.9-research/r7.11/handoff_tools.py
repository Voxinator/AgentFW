"""handoff_tools — Hermes-tool definitions for session handoff signals.

Item 6a of the r7.11 implementation order. Provides two tool callables
that the parent agent invokes during a Hermes session to signal the
wrapper substrate (item 7) that the session should end:

  * end_session_for_handoff — work for this session is complete; the
    wrapper should kill the Hermes process and (if applicable) start
    the next session.
  * escalate_to_operator — the multi-session run needs human review;
    the wrapper should pause and surface the message.

Both tools write a sentinel JSON file to the scaffold root. The
sentinels are HANDOFF TRIGGERS, NOT AUTHORITATIVE STATE. Authority for
phase state remains in `verified-state.json` (written by verify_phase
via items 1+5). Sentinels carry metadata for wrapper debugging /
logging only — when the wrapper sees a sentinel it kills Hermes, then
reads `verified-state.json` to decide what happens next.

Per DESIGN-r7.11-architecture.md §6 F2 ("parent fabrication
mitigation — wrapper-as-source-of-truth"), the parent's
`parent_intent_log` field is NON-LOAD-BEARING: a parent that lies in
its narrative cannot corrupt the verdict, because the wrapper does
not consult the narrative.

Item 6a is **tool definition only**. Item 6b owns the actual VM
staging + smoke; item 7 (wrapper substrate) reads and acts on the
sentinel files. No Hermes-layer code lives here.

This module re-defines `ToolError` rather than importing from
`verify_phase_tool`; this is intentional — duplicating the small
exception class across tool modules keeps each independently
importable, and the planner-worker dispatch shape (each tool can be
swapped or staged in isolation) is preserved. The two ToolError
classes are not interchangeable across modules.

Stdlib only.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ToolError(Exception):
    """Operational failure for handoff sentinel writers.

    Raised when the scaffold_root is missing/relative, when validation
    of a parameter fails, or when a double-call would overwrite an
    existing sentinel.
    """


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SENTINEL_SCHEMA_VERSION = "1.0"
SESSION_END_SENTINEL_NAME = ".session-end-signal.json"
SESSION_ESCALATE_SENTINEL_NAME = ".session-escalate-signal.json"

PARENT_INTENT_LOG_VALUES = ("advance", "done", "escalate")
ESCALATE_REASON_VALUES = (
    "verify_failed_after_max_revisions",
    "ambiguous_requirements",
    "external_dependency",
    "other",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """Return current time as ISO 8601 UTC with trailing 'Z'."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _synthetic_session_id() -> str:
    """Synthesize a session_id for direct callers.

    Item 7 (wrapper substrate) will inject the real Hermes session_id
    via the `session_id` keyword. This is the same plumbing seam used
    by verify_phase_tool._synthetic_session_id.
    """
    return f"tool-call-{int(time.time())}"


def _validate_scaffold_root(scaffold_root: Union[str, Path]) -> Path:
    """Normalize scaffold_root to Path; reject relative or non-directory.

    Returns the resolved Path on success. Raises ToolError otherwise.
    """
    p = Path(scaffold_root)
    if not p.is_absolute():
        raise ToolError(
            f"scaffold_root must be absolute path; got: {scaffold_root!r}"
        )
    if not p.exists() or not p.is_dir():
        raise ToolError(
            f"scaffold_root does not exist or is not a directory: "
            f"{scaffold_root!r}"
        )
    return p


def _atomic_write_json(target: Path, payload: Dict[str, Any]) -> None:
    """Write `payload` as pretty-printed JSON to `target` atomically.

    Mirrors verified_state.save's pattern: write to a NamedTemporaryFile
    in the same directory, fsync, os.replace onto target. Cleans up
    temp on any failure.
    """
    target_dir = target.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    body = json.dumps(payload, indent=2, sort_keys=False)

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(target_dir),
        prefix=target.name + ".",
        suffix=".tmp",
        delete=False,
    )
    tmp_path = Path(tmp.name)
    try:
        try:
            tmp.write(body)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(str(tmp_path), str(target))
    except BaseException:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# end_session_for_handoff
# ---------------------------------------------------------------------------


def end_session_for_handoff(
    *,
    scaffold_root: Union[str, Path],
    completed_phase: Optional[int] = None,
    parent_intent_log: Optional[str] = None,
    parent_summary: str = "",
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write the session-end sentinel to the scaffold root.

    Behavior (per design §3, §6 F2):
      1. Validate scaffold_root (absolute + existing directory).
      2. Validate parent_intent_log (None or one of advance/done/escalate).
         This field is non-load-bearing — the wrapper logs it but does
         NOT base routing on it; verified-state.json is authoritative.
      3. Validate completed_phase (None or non-negative int). Bootstrap
         sessions can pass None (no phase completed yet).
      4. Resolve session_id (synth fallback for direct callers).
      5. Refuse to overwrite an existing sentinel — double-call detection.
      6. Atomically write `<scaffold_root>/.session-end-signal.json`.
      7. Return ack dict { status, sentinel_path, session_id }.

    Raises ToolError on any validation failure or double-call.
    """
    root = _validate_scaffold_root(scaffold_root)

    if parent_intent_log is not None:
        if parent_intent_log not in PARENT_INTENT_LOG_VALUES:
            raise ToolError(
                f"parent_intent_log must be one of "
                f"{list(PARENT_INTENT_LOG_VALUES)} or null; got "
                f"{parent_intent_log!r}"
            )

    if completed_phase is not None:
        if (
            not isinstance(completed_phase, int)
            or isinstance(completed_phase, bool)
            or completed_phase < 0
        ):
            raise ToolError(
                f"completed_phase must be a non-negative int or null; got "
                f"{completed_phase!r}"
            )

    if not isinstance(parent_summary, str):
        raise ToolError(
            f"parent_summary must be a string; got "
            f"{type(parent_summary).__name__}"
        )

    sid = session_id if session_id else _synthetic_session_id()
    sentinel_path = root / SESSION_END_SENTINEL_NAME

    if sentinel_path.exists():
        raise ToolError(
            f"session-end sentinel already exists at {sentinel_path}; "
            f"double-call detected"
        )

    payload = {
        "schema_version": SENTINEL_SCHEMA_VERSION,
        "kind": "session-end",
        "timestamp": _utc_now_iso(),
        "session_id": sid,
        "completed_phase": completed_phase,
        "parent_intent_log": parent_intent_log,
        "parent_summary": parent_summary,
    }

    _atomic_write_json(sentinel_path, payload)

    return {
        "status": "session_end_sentinel_written",
        "sentinel_path": str(sentinel_path),
        "session_id": sid,
    }


# ---------------------------------------------------------------------------
# escalate_to_operator
# ---------------------------------------------------------------------------


def escalate_to_operator(
    *,
    scaffold_root: Union[str, Path],
    reason: str,
    message: str,
    suggested_action: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write the escalate sentinel to pause the multi-session run.

    Behavior:
      1. Validate scaffold_root (absolute + existing directory).
      2. Validate reason against the enum.
      3. Validate message (non-empty after strip).
      4. Resolve session_id (synth fallback).
      5. Refuse to overwrite an existing sentinel.
      6. Atomically write
         `<scaffold_root>/.session-escalate-signal.json`.
      7. Return ack dict { status, sentinel_path, session_id }.

    Raises ToolError on any validation failure or double-call.
    """
    root = _validate_scaffold_root(scaffold_root)

    if not isinstance(reason, str) or reason not in ESCALATE_REASON_VALUES:
        raise ToolError(
            f"reason must be one of {list(ESCALATE_REASON_VALUES)}; got "
            f"{reason!r}"
        )

    if not isinstance(message, str):
        raise ToolError(
            f"message must be a string; got {type(message).__name__}"
        )
    if message.strip() == "":
        raise ToolError("message must be a non-empty string (after strip)")

    if suggested_action is not None and not isinstance(suggested_action, str):
        raise ToolError(
            f"suggested_action must be a string or null; got "
            f"{type(suggested_action).__name__}"
        )

    sid = session_id if session_id else _synthetic_session_id()
    sentinel_path = root / SESSION_ESCALATE_SENTINEL_NAME

    if sentinel_path.exists():
        raise ToolError(
            f"escalate sentinel already exists at {sentinel_path}; "
            f"double-call detected"
        )

    payload = {
        "schema_version": SENTINEL_SCHEMA_VERSION,
        "kind": "session-escalate",
        "timestamp": _utc_now_iso(),
        "session_id": sid,
        "reason": reason,
        "message": message,
        "suggested_action": suggested_action,
    }

    _atomic_write_json(sentinel_path, payload)

    return {
        "status": "escalate_sentinel_written",
        "sentinel_path": str(sentinel_path),
        "session_id": sid,
    }


# ---------------------------------------------------------------------------
# Hermes tool definition: end_session_for_handoff (paste-ready for item 6b)
# ---------------------------------------------------------------------------


END_SESSION_TOOL_NAME = "end_session_for_handoff"


END_SESSION_TOOL_DESCRIPTION = (
    "Signal the wrapper that this Hermes session's work is complete and "
    "the next session (if any) should resume. Calling this tool writes a "
    "sentinel file to the scaffold root; the wrapper substrate polls for "
    "the sentinel, kills this Hermes process, and decides the next "
    "action.\n"
    "\n"
    "CRITICAL DOCTRINE — read carefully:\n"
    "  The wrapper reads `verified-state.json` for AUTHORITATIVE phase "
    "state, NOT your `parent_intent_log` field. Your `parent_intent_log` "
    "is logged for debugging only — it is non-load-bearing. If your "
    "narrative claims phase 2 passed but verified-state.json says phase "
    "2 failed, the wrapper trusts verified-state.json and ignores you.\n"
    "  PLAN.md updates you write are likewise informational. The JSON "
    "verdict file written by `verify_phase` is the only authoritative "
    "source of truth.\n"
    "\n"
    "STANDARD PATTERN — one phase per session:\n"
    "  After a phase verifies passed, the standard pattern is to call "
    "end_session_for_handoff so the wrapper starts the next phase in "
    "fresh context. This preserves verification independence across "
    "phases (each phase's verification is unbiased by the prior phase's "
    "narrative). Batching multiple phases into one session is allowed "
    "but reduces the multi-session architecture's value — the wrapper's "
    "isolation between phases is the mechanism that keeps synthesis "
    "tethered to verified state.\n"
    "\n"
    "When to call:\n"
    "  - The current phase verified passed (`verify_phase` returned "
    "    passed=true and verified-state.json reflects it). Start the "
    "    next phase in a fresh session via this tool — DON'T continue "
    "    inline.\n"
    "  - All phases for this session are complete (passed=true verdicts "
    "    persisted via verify_phase).\n"
    "  - You have no further productive work this session and want the "
    "    wrapper to advance / hand off / finish.\n"
    "\n"
    "When NOT to call:\n"
    "  - A verify_phase call returned passed=false. Re-dispatch the "
    "    worker first; do not end the session on a failed verdict unless "
    "    you have hit the revision cap (in which case use "
    "    escalate_to_operator).\n"
    "  - You are mid-task. Finish the task, run verify_phase, then end.\n"
    "\n"
    "Calling this tool twice in the same session is an error (the "
    "sentinel file already exists). Call it exactly once at end-of-"
    "session."
)


END_SESSION_TOOL_PARAMETERS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "scaffold_root": {
            "type": "string",
            "description": (
                "Absolute path to the project scaffold root. Sentinel "
                "is written to <scaffold_root>/.session-end-signal.json."
            ),
        },
        "completed_phase": {
            "type": ["integer", "null"],
            "default": None,
            "description": (
                "Highest phase id completed in this session. None / null "
                "is acceptable for bootstrap sessions where no phase "
                "advanced. NON-LOAD-BEARING — the wrapper consults "
                "verified-state.json for authoritative phase state; "
                "this field is metadata for logging only."
            ),
        },
        "parent_intent_log": {
            "type": ["string", "null"],
            "enum": ["advance", "done", "escalate", None],
            "default": None,
            "description": (
                "Parent's narrative summary of intent: 'advance' (next "
                "phase pending), 'done' (project complete), 'escalate' "
                "(needs operator). NON-LOAD-BEARING — logged for "
                "debugging; the wrapper does NOT route on this field."
            ),
        },
        "parent_summary": {
            "type": "string",
            "default": "",
            "description": (
                "Free-text summary of what was done this session. "
                "Logged for operator inspection; non-load-bearing."
            ),
        },
    },
    "required": ["scaffold_root"],
    "additionalProperties": False,
}


END_SESSION_TOOL_RETURNS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "description": "Always 'session_end_sentinel_written' on success.",
        },
        "sentinel_path": {
            "type": "string",
            "description": (
                "Absolute path to the sentinel file that was written."
            ),
        },
        "session_id": {
            "type": "string",
            "description": (
                "Resolved session_id (caller-provided or synthesized)."
            ),
        },
    },
    "required": ["status", "sentinel_path", "session_id"],
}


# ---------------------------------------------------------------------------
# Hermes tool definition: escalate_to_operator (paste-ready for item 6b)
# ---------------------------------------------------------------------------


ESCALATE_TOOL_NAME = "escalate_to_operator"


ESCALATE_TOOL_DESCRIPTION = (
    "Pause the multi-session run for operator review. Calling this tool "
    "writes a sentinel file to the scaffold root; the wrapper substrate "
    "kills this Hermes process and surfaces the message to the human "
    "operator. State (verified-state.json, PLAN.md, scaffold files) is "
    "preserved; the operator can inspect everything and resume by "
    "re-launching the wrapper.\n"
    "\n"
    "WHEN TO CALL — this is a high-cost action; use it sparingly:\n"
    "  - revision_count has hit the configured maximum and verify_phase "
    "    is still returning passed=false.\n"
    "  - The situation requires human input that the verify tool cannot "
    "    provide (ambiguous requirements, external blocker, etc.).\n"
    "  - You detect a contradiction between PLAN.md and the work that "
    "    you cannot resolve.\n"
    "\n"
    "WHEN NOT TO CALL — DO NOT use this for routine verification "
    "failures. A single passed=false verdict is normal and recoverable: "
    "re-dispatch the worker with the corrective_dispatch text and try "
    "again. Only escalate when the revise loop has been exhausted or "
    "the situation is structurally unrecoverable from inside the "
    "session.\n"
    "\n"
    "Authority and state preservation:\n"
    "  - verified-state.json is unchanged by this tool — it remains the "
    "    authoritative source of phase state.\n"
    "  - The operator can inspect verified-state.json + PLAN.md + the "
    "    scaffold and decide whether to resume, edit, or abandon.\n"
    "  - Calling this tool twice in the same session is an error."
)


ESCALATE_TOOL_PARAMETERS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "scaffold_root": {
            "type": "string",
            "description": (
                "Absolute path to the project scaffold root. Sentinel "
                "is written to "
                "<scaffold_root>/.session-escalate-signal.json."
            ),
        },
        "reason": {
            "type": "string",
            "enum": list(ESCALATE_REASON_VALUES),
            "description": (
                "Categorical reason. 'verify_failed_after_max_revisions' "
                "is the most common; 'other' is a free-form fallback."
            ),
        },
        "message": {
            "type": "string",
            "description": (
                "Operator-facing message explaining the situation. "
                "Required and must be non-empty."
            ),
        },
        "suggested_action": {
            "type": ["string", "null"],
            "default": None,
            "description": (
                "Optional hint to the operator about what to do next "
                "(e.g. 'revise PLAN.md phase 3 paths' or 'check the "
                "external API key in verify-config.json')."
            ),
        },
    },
    "required": ["scaffold_root", "reason", "message"],
    "additionalProperties": False,
}


ESCALATE_TOOL_RETURNS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "description": "Always 'escalate_sentinel_written' on success.",
        },
        "sentinel_path": {
            "type": "string",
            "description": "Absolute path to the sentinel file written.",
        },
        "session_id": {
            "type": "string",
            "description": (
                "Resolved session_id (caller-provided or synthesized)."
            ),
        },
    },
    "required": ["status", "sentinel_path", "session_id"],
}


__all__ = [
    "ToolError",
    "SENTINEL_SCHEMA_VERSION",
    "SESSION_END_SENTINEL_NAME",
    "SESSION_ESCALATE_SENTINEL_NAME",
    "PARENT_INTENT_LOG_VALUES",
    "ESCALATE_REASON_VALUES",
    "end_session_for_handoff",
    "escalate_to_operator",
    "END_SESSION_TOOL_NAME",
    "END_SESSION_TOOL_DESCRIPTION",
    "END_SESSION_TOOL_PARAMETERS_SCHEMA",
    "END_SESSION_TOOL_RETURNS_SCHEMA",
    "ESCALATE_TOOL_NAME",
    "ESCALATE_TOOL_DESCRIPTION",
    "ESCALATE_TOOL_PARAMETERS_SCHEMA",
    "ESCALATE_TOOL_RETURNS_SCHEMA",
]
