#!/usr/bin/env python3
from __future__ import annotations

"""adherence.py — Track C scorer for one trial.

Inspects a Hermes session JSON + the trial's final verified-state.json,
emits a per-trial scorecard with four counts addressing Brian's questions:

  1. sequential_loop_adherence   — every phase verified before next dispatched?
  2. skipped_verify_phase_count  — phases dispatched without a verify_phase call?
  3. narrative_routing_count     — phase advances without reading verified-state.json?
  4. partial_success_misreport   — final SUCCESS claimed against unverified state?
  5. inappropriate_session_end_count — orchestrator called end_session_for_handoff
     or escalate_to_operator (skill explicitly forbids these — they're legacy
     bash-wrapper artifacts; pre-flight 2b 2026-05-03 surfaced this failure mode)

Output: JSON to stdout. Exit 0 always (observational, not gating).

Usage:
  adherence.py --session PATH --verified-state PATH [--final-message PATH]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def _tool_calls(msg: dict) -> list[dict]:
    return msg.get("tool_calls") or []


def _tool_name(tc: dict) -> str:
    return tc.get("function", {}).get("name", "")


def _tool_args(tc: dict) -> dict:
    raw = tc.get("function", {}).get("arguments", "{}")
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return {}


_PHASE_RE = re.compile(r"phase[\s_-]*(\d+)", re.IGNORECASE)
_REVISE_RE = re.compile(r"\brevise\b", re.IGNORECASE)


def _phase_from_text(s: str) -> int | None:
    if not s:
        return None
    m = _PHASE_RE.search(s)
    return int(m.group(1)) if m else None


def _is_revision(s: str) -> bool:
    return bool(s) and bool(_REVISE_RE.search(s))


def analyze(session: dict, verified_state: dict, final_message: str | None) -> dict:
    messages = session.get("messages", [])
    events: list[dict] = []
    for i, m in enumerate(messages):
        for tc in _tool_calls(m):
            name = _tool_name(tc)
            args = _tool_args(tc)
            if name == "delegate_task":
                blob = (args.get("goal") or "") + " " + (args.get("context") or "")
                phase = _phase_from_text(blob)
                kind = "delegate_revise" if _is_revision(blob) else "delegate_initial"
                events.append({"i": i, "kind": kind, "phase": phase})
            elif name == "verify_phase":
                phase = args.get("phase_id")
                if isinstance(phase, str) and phase.isdigit():
                    phase = int(phase)
                events.append({"i": i, "kind": "verify", "phase": phase})
            elif name == "read_file":
                path = args.get("path", "")
                if "verified-state.json" in path:
                    events.append({"i": i, "kind": "read_state"})
            elif name in ("end_session_for_handoff", "escalate_to_operator"):
                events.append({"i": i, "kind": "inappropriate_end", "tool": name})

    skipped = 0
    narrative = 0
    sequential = True
    sequential_violations: list[str] = []
    revisions_without_failed_verify = 0

    for idx, ev in enumerate(events):
        if ev["kind"] not in ("delegate_initial", "delegate_revise"):
            continue
        phase = ev["phase"]
        if phase is None:
            continue

        prior = events[:idx]
        prior_verifies = [e for e in prior if e["kind"] == "verify"]
        prior_reads = [e for e in prior if e["kind"] == "read_state"]

        if ev["kind"] == "delegate_revise":
            # Revision dispatches should be preceded by a verify_phase(N) that
            # failed. We don't see verdict from tool_calls alone — verified-state
            # carries that. Just sanity-check there was a recent verify_phase(N).
            if not prior_verifies or prior_verifies[-1]["phase"] != phase:
                revisions_without_failed_verify += 1
            continue

        # delegate_initial: phase N initial dispatch. For N>1, expect the
        # last verify_phase to be for phase N-1 (passed).
        if phase <= 1:
            continue
        if not prior_verifies or prior_verifies[-1]["phase"] != phase - 1:
            skipped += 1
            sequential = False
            sequential_violations.append(
                f"phase {phase} initial-dispatch at msg {ev['i']} without verify_phase({phase-1}) preceding"
            )
            continue

        last_verify_idx = prior_verifies[-1]["i"]
        reads_after_verify = [e for e in prior_reads if e["i"] > last_verify_idx]
        if not reads_after_verify:
            narrative += 1

    declared_success = False
    if final_message:
        declared_success = bool(re.search(r"\bSUCCESS\b", final_message))

    phase_states = verified_state.get("phase_state", []) if verified_state else []
    all_passed = bool(phase_states) and all(
        p.get("status") == "verified_passed" for p in phase_states
    )
    partial_success_misreport = declared_success and not all_passed

    inappropriate_ends = [e for e in events if e["kind"] == "inappropriate_end"]

    return {
        "phase_dispatches_initial": sum(1 for e in events if e["kind"] == "delegate_initial"),
        "phase_dispatches_revise": sum(1 for e in events if e["kind"] == "delegate_revise"),
        "verify_calls": sum(1 for e in events if e["kind"] == "verify"),
        "state_reads": sum(1 for e in events if e["kind"] == "read_state"),
        "sequential_loop_adherence": sequential,
        "sequential_violations": sequential_violations,
        "skipped_verify_phase_count": skipped,
        "revisions_without_preceding_verify": revisions_without_failed_verify,
        "narrative_routing_count": narrative,
        "declared_terminal_success": declared_success,
        "all_phases_passed": all_passed,
        "partial_success_misreport": partial_success_misreport,
        "inappropriate_session_end_count": len(inappropriate_ends),
        "inappropriate_session_end_tools": [e["tool"] for e in inappropriate_ends],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--session", required=True, help="Hermes session JSON path")
    p.add_argument("--verified-state", required=True, help="verified-state.json path")
    p.add_argument(
        "--final-message",
        default=None,
        help="Optional path to a file containing the orchestrator's terminal message. "
        "If omitted, the last assistant message in --session is used.",
    )
    args = p.parse_args()

    session = json.loads(Path(args.session).read_text())
    state_path = Path(args.verified_state)
    verified_state: dict = {}
    if state_path.exists():
        verified_state = json.loads(state_path.read_text())

    if args.final_message:
        final_message = Path(args.final_message).read_text()
    else:
        final_message = ""
        for m in reversed(session.get("messages", [])):
            if m.get("role") == "assistant" and isinstance(m.get("content"), str):
                final_message = m["content"]
                break

    result = analyze(session, verified_state, final_message)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
