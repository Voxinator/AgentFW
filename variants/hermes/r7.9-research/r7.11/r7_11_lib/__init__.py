"""r7_11_lib — Hermes-side support package for r7.11 tools.

This package holds the four library modules that back the three new
r7.11 tools (verify_phase, end_session_for_handoff, escalate_to_operator):

  - verified_state.py     (verified-state.json read/write helpers)
  - verify_phase.py       (tier 1/2/3/3.5 verification engine)
  - verify_phase_tool.py  (Hermes-tool-shaped wrapper around verify_phase)
  - handoff_tools.py      (sentinel writers + tool metadata)

The package layout exists so the four library modules can live under
``~/.hermes/hermes-agent/tools/`` without being scanned as top-level
tool modules by ``model_tools.py`` (which uses an explicit import list,
not a directory scan, but extra defensiveness is cheap).

The three thin shims that actually self-register the tools live one level
up at ``tools/r7_11_verify_phase.py``, ``tools/r7_11_end_session.py``,
and ``tools/r7_11_escalate.py``. They import from this package via
``from tools.r7_11_lib import ...``.
"""
