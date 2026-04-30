"""Tests for handoff_tools (r7.11 item 6a).

Runnable two ways:
  pytest test_handoff_tools.py -v
  python3 test_handoff_tools.py     (falls back to plain assertions)

Coverage (14 tests):
  - end_session_for_handoff (H1-H6).
  - escalate_to_operator    (E1-E5).
  - Cross-tool / shared     (S1-S3).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Allow `python3 test_handoff_tools.py` from any CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import handoff_tools as ht  # noqa: E402
from handoff_tools import (  # noqa: E402
    ESCALATE_REASON_VALUES,
    ESCALATE_TOOL_DESCRIPTION,
    ESCALATE_TOOL_NAME,
    ESCALATE_TOOL_PARAMETERS_SCHEMA,
    ESCALATE_TOOL_RETURNS_SCHEMA,
    END_SESSION_TOOL_DESCRIPTION,
    END_SESSION_TOOL_NAME,
    END_SESSION_TOOL_PARAMETERS_SCHEMA,
    END_SESSION_TOOL_RETURNS_SCHEMA,
    PARENT_INTENT_LOG_VALUES,
    SESSION_END_SENTINEL_NAME,
    SESSION_ESCALATE_SENTINEL_NAME,
    ToolError,
    end_session_for_handoff,
    escalate_to_operator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_ISO_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)


def _is_iso8601_z(s: str) -> bool:
    return bool(_ISO_Z_RE.match(s))


# ---------------------------------------------------------------------------
# end_session_for_handoff (H1-H6)
# ---------------------------------------------------------------------------


def test_H1_end_session_happy_path():
    with tempfile.TemporaryDirectory() as d:
        ack = end_session_for_handoff(
            scaffold_root=d,
            completed_phase=2,
            parent_intent_log="advance",
            parent_summary="phase 2 done",
        )
    assert ack["status"] == "session_end_sentinel_written"
    assert ack["sentinel_path"].endswith(SESSION_END_SENTINEL_NAME)
    assert isinstance(ack["session_id"], str) and ack["session_id"]


def test_H2_end_session_sentinel_json_content():
    with tempfile.TemporaryDirectory() as d:
        ack = end_session_for_handoff(
            scaffold_root=d,
            completed_phase=3,
            parent_intent_log="done",
            parent_summary="all phases complete",
            session_id="hermes-sess-abc",
        )
        with open(ack["sentinel_path"], "r", encoding="utf-8") as f:
            payload = json.load(f)
    assert payload["schema_version"] == "1.0"
    assert payload["kind"] == "session-end"
    assert _is_iso8601_z(payload["timestamp"]), payload["timestamp"]
    assert payload["session_id"] == "hermes-sess-abc"
    assert payload["completed_phase"] == 3
    assert payload["parent_intent_log"] == "done"
    assert payload["parent_summary"] == "all phases complete"
    # Required fields all present
    for key in (
        "schema_version",
        "kind",
        "timestamp",
        "session_id",
        "completed_phase",
        "parent_intent_log",
        "parent_summary",
    ):
        assert key in payload


def test_H3_end_session_relative_scaffold_root_rejected():
    raised = False
    try:
        end_session_for_handoff(scaffold_root="./foo")
    except ToolError as exc:
        raised = True
        assert "absolute" in str(exc).lower()
    assert raised


def test_H4_end_session_missing_scaffold_root_rejected():
    raised = False
    try:
        end_session_for_handoff(scaffold_root="/nonexistent/path/xyz-r711")
    except ToolError as exc:
        raised = True
        msg = str(exc).lower()
        assert "does not exist" in msg or "not a directory" in msg
    assert raised


def test_H5_end_session_double_call_raises():
    with tempfile.TemporaryDirectory() as d:
        end_session_for_handoff(scaffold_root=d, parent_summary="first")
        raised = False
        try:
            end_session_for_handoff(scaffold_root=d, parent_summary="second")
        except ToolError as exc:
            raised = True
            assert SESSION_END_SENTINEL_NAME in str(exc)
            assert "double-call" in str(exc).lower()
        assert raised


def test_H6_end_session_completed_phase_and_intent_log_none_accepted():
    """Bootstrap case: completed_phase=None and parent_intent_log=None
    are both accepted; sentinel reflects them as JSON null."""
    with tempfile.TemporaryDirectory() as d:
        ack = end_session_for_handoff(
            scaffold_root=d,
            completed_phase=None,
            parent_intent_log=None,
            parent_summary="bootstrap, nothing advanced yet",
        )
        with open(ack["sentinel_path"], "r", encoding="utf-8") as f:
            payload = json.load(f)
    assert payload["completed_phase"] is None
    assert payload["parent_intent_log"] is None


# ---------------------------------------------------------------------------
# escalate_to_operator (E1-E5)
# ---------------------------------------------------------------------------


def test_E1_escalate_happy_path():
    with tempfile.TemporaryDirectory() as d:
        ack = escalate_to_operator(
            scaffold_root=d,
            reason="verify_failed_after_max_revisions",
            message="phase 3 has failed 5 revisions",
        )
    assert ack["status"] == "escalate_sentinel_written"
    assert ack["sentinel_path"].endswith(SESSION_ESCALATE_SENTINEL_NAME)
    assert isinstance(ack["session_id"], str) and ack["session_id"]


def test_E2_escalate_sentinel_json_content():
    with tempfile.TemporaryDirectory() as d:
        ack = escalate_to_operator(
            scaffold_root=d,
            reason="ambiguous_requirements",
            message="PLAN.md phase 4 paths conflict with phase 2",
            session_id="hermes-sess-xyz",
        )
        with open(ack["sentinel_path"], "r", encoding="utf-8") as f:
            payload = json.load(f)
    assert payload["schema_version"] == "1.0"
    assert payload["kind"] == "session-escalate"
    assert _is_iso8601_z(payload["timestamp"]), payload["timestamp"]
    assert payload["session_id"] == "hermes-sess-xyz"
    assert payload["reason"] == "ambiguous_requirements"
    assert payload["message"] == "PLAN.md phase 4 paths conflict with phase 2"
    assert payload["suggested_action"] is None


def test_E3_escalate_invalid_reason_enum():
    with tempfile.TemporaryDirectory() as d:
        raised = False
        try:
            escalate_to_operator(
                scaffold_root=d,
                reason="bogus",
                message="hi",
            )
        except ToolError as exc:
            raised = True
            msg = str(exc)
            # Names at least one valid enum value
            assert "verify_failed_after_max_revisions" in msg
            assert "bogus" in msg
        assert raised


def test_E4_escalate_empty_message_rejected():
    with tempfile.TemporaryDirectory() as d:
        for bad_msg in ("", "   ", "\n\t  "):
            raised = False
            try:
                escalate_to_operator(
                    scaffold_root=d,
                    reason="other",
                    message=bad_msg,
                )
            except ToolError as exc:
                raised = True
                assert "non-empty" in str(exc).lower() or \
                       "must be" in str(exc).lower()
            assert raised, f"empty message {bad_msg!r} should raise"


def test_E5_escalate_double_call_raises():
    with tempfile.TemporaryDirectory() as d:
        escalate_to_operator(
            scaffold_root=d,
            reason="other",
            message="first call",
        )
        raised = False
        try:
            escalate_to_operator(
                scaffold_root=d,
                reason="other",
                message="second call",
            )
        except ToolError as exc:
            raised = True
            assert SESSION_ESCALATE_SENTINEL_NAME in str(exc)
            assert "double-call" in str(exc).lower()
        assert raised


# ---------------------------------------------------------------------------
# Cross-tool / shared (S1-S3)
# ---------------------------------------------------------------------------


def test_S1_session_id_synthesis():
    """session_id=None is resolved to 'tool-call-<digits>'; ack and
    sentinel agree on the synthesized value."""
    with tempfile.TemporaryDirectory() as d:
        ack = end_session_for_handoff(
            scaffold_root=d,
            session_id=None,
            parent_summary="synth check",
        )
        with open(ack["sentinel_path"], "r", encoding="utf-8") as f:
            payload = json.load(f)
    sid = ack["session_id"]
    assert sid.startswith("tool-call-"), sid
    suffix = sid[len("tool-call-"):]
    assert suffix.isdigit() and int(suffix) > 0, sid
    assert payload["session_id"] == sid


def test_S2_atomic_write_failure_no_leftovers():
    """If os.replace fails mid-flight, the sentinel is absent and no
    .tmp files are left in scaffold_root."""
    with tempfile.TemporaryDirectory() as d:
        real_replace = os.replace
        calls = {"n": 0}

        def boom(src, dst):
            calls["n"] += 1
            raise OSError("simulated mid-flight replace failure")

        os.replace = boom
        try:
            failed = False
            try:
                end_session_for_handoff(
                    scaffold_root=d, parent_summary="atomicity"
                )
            except OSError:
                failed = True
            assert failed, "atomic write should have propagated OSError"
            assert calls["n"] >= 1
        finally:
            os.replace = real_replace

        # Sentinel absent.
        assert not (Path(d) / SESSION_END_SENTINEL_NAME).exists()
        # No leftover temp files.
        leftover = list(Path(d).iterdir())
        assert leftover == [], f"unexpected leftovers: {leftover}"

        # And after restoring, a normal write still works.
        ack = end_session_for_handoff(
            scaffold_root=d, parent_summary="recovery"
        )
        assert (Path(d) / SESSION_END_SENTINEL_NAME).exists()
        assert ack["status"] == "session_end_sentinel_written"


def test_S3_tool_definition_constants_present_and_serializable():
    """Both tools expose NAME / DESCRIPTION / PARAMETERS_SCHEMA /
    RETURNS_SCHEMA. Descriptions teach the doctrine. Schemas
    round-trip through json.dumps."""
    # end_session_for_handoff
    assert END_SESSION_TOOL_NAME == "end_session_for_handoff"
    assert isinstance(END_SESSION_TOOL_DESCRIPTION, str)
    assert len(END_SESSION_TOOL_DESCRIPTION) > 200
    desc_lower = END_SESSION_TOOL_DESCRIPTION.lower()
    assert (
        "non-load-bearing" in desc_lower
        or "authoritative" in desc_lower
    ), "end_session description must teach doctrine"
    assert isinstance(END_SESSION_TOOL_PARAMETERS_SCHEMA, dict)
    assert END_SESSION_TOOL_PARAMETERS_SCHEMA.get("type") == "object"
    assert "scaffold_root" in END_SESSION_TOOL_PARAMETERS_SCHEMA["required"]
    assert (
        END_SESSION_TOOL_PARAMETERS_SCHEMA.get("additionalProperties") is False
    )
    assert "properties" in END_SESSION_TOOL_PARAMETERS_SCHEMA
    # parent_intent_log enum present
    intent_prop = (
        END_SESSION_TOOL_PARAMETERS_SCHEMA["properties"]["parent_intent_log"]
    )
    assert "enum" in intent_prop
    for v in PARENT_INTENT_LOG_VALUES:
        assert v in intent_prop["enum"]
    assert isinstance(END_SESSION_TOOL_RETURNS_SCHEMA, dict)
    assert "status" in END_SESSION_TOOL_RETURNS_SCHEMA["required"]

    # Round-trip both end_session schemas through json.dumps.
    json.dumps(END_SESSION_TOOL_PARAMETERS_SCHEMA)
    json.dumps(END_SESSION_TOOL_RETURNS_SCHEMA)

    # escalate_to_operator
    assert ESCALATE_TOOL_NAME == "escalate_to_operator"
    assert isinstance(ESCALATE_TOOL_DESCRIPTION, str)
    assert len(ESCALATE_TOOL_DESCRIPTION) > 200
    e_lower = ESCALATE_TOOL_DESCRIPTION.lower()
    assert (
        "do not" in e_lower or "not call" in e_lower or "sparingly" in e_lower
    ), "escalate description must teach when-not-to-call"
    assert isinstance(ESCALATE_TOOL_PARAMETERS_SCHEMA, dict)
    assert ESCALATE_TOOL_PARAMETERS_SCHEMA.get("type") == "object"
    for r in ("scaffold_root", "reason", "message"):
        assert r in ESCALATE_TOOL_PARAMETERS_SCHEMA["required"]
    assert (
        ESCALATE_TOOL_PARAMETERS_SCHEMA.get("additionalProperties") is False
    )
    reason_enum = (
        ESCALATE_TOOL_PARAMETERS_SCHEMA["properties"]["reason"]["enum"]
    )
    for v in ESCALATE_REASON_VALUES:
        assert v in reason_enum
    assert isinstance(ESCALATE_TOOL_RETURNS_SCHEMA, dict)
    assert "status" in ESCALATE_TOOL_RETURNS_SCHEMA["required"]

    json.dumps(ESCALATE_TOOL_PARAMETERS_SCHEMA)
    json.dumps(ESCALATE_TOOL_RETURNS_SCHEMA)


# ---------------------------------------------------------------------------
# Plain-script entry point
# ---------------------------------------------------------------------------


def _run_all():
    tests = [
        (n, fn) for n, fn in globals().items()
        if n.startswith("test_") and callable(fn)
    ]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failed.append((name, repr(exc)))
            print(f"FAIL  {name}: {exc!r}")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, repr(exc)))
            print(f"ERROR {name}: {exc!r}")
    print()
    print(f"{len(tests) - len(failed)}/{len(tests)} passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(_run_all())
