"""verify_phase_tool — Hermes-tool-shaped wrapper around verify_phase.

Item 5 of the r7.11 implementation order. This module is the bridge
between the parent agent (which will eventually call this tool via
Hermes) and the standalone analyzers in `verify_phase.py` + the
state machine in `verified_state.py`.

Per DESIGN-r7.11-architecture.md §3, the wrapper:

  1. Reads `verify-config.json` (operator-supplied; all fields optional).
  2. Reads `PLAN.md` to extract phase paths (the wrapper bridges the
     PLAN.md text format to `PhaseInput` data).
  3. Constructs `project_phases` from PLAN.md for phase-awareness.
  4. Calls `verify_phase.verify_phase()` with config-resolved args.
  5. Persists the verdict to `verified-state.json` via
     `verified_state.record_verdict` + `save`.
  6. Returns a dict matching §3's `verify_phase` returns schema.

Item 5 is **tool definition only**. Item 6 owns the actual Hermes
registration (which imports `TOOL_NAME`, `TOOL_DESCRIPTION`,
`TOOL_PARAMETERS_SCHEMA`, and `TOOL_RETURNS_SCHEMA` from this
module verbatim). No Hermes-layer code lives here.

Stdlib only. Errors:
  ConfigError(ValueError) — verify-config.json malformed / version-mismatch.
  ToolError(Exception)    — operational failure (PLAN.md missing, phase_id
                            unknown, scaffold_root missing, etc.).
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import verified_state
import verify_phase as vp_mod
from verified_state import (
    PhaseSpec,
    bootstrap,
    load,
    record_verdict,
    save,
)
from verify_phase import PhaseInput, VerifyResult


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ConfigError(ValueError):
    """verify-config.json is malformed, version-mismatched, or violates
    schema. Raised before any verification work runs; the wrapper
    substrate (item 7) is expected to fail-fast on this."""


class ToolError(Exception):
    """Operational failure: PLAN.md missing/unparseable, phase_id not
    in PLAN.md, scaffold_root doesn't exist, etc."""


# ---------------------------------------------------------------------------
# Resolved config
# ---------------------------------------------------------------------------


CONFIG_SCHEMA_VERSION = "1.0"


@dataclass
class VerifyConfig:
    """Resolved verify-config.json with defaults filled in.

    Fields mirror the operator-approved schema in VERIFY-CONFIG-SCHEMA.md.
    Defaults match `verify_phase.verify_phase`'s built-in defaults so
    `VerifyConfig()` is equivalent to "no config file present".
    """

    cat1_extra_allow_list: List[str] = field(default_factory=list)
    presence_min_bytes: int = 50
    presence_min_nonblank_lines: int = 3
    runtime_smoke_test_timeout: int = 10
    runtime_smoke_test_default: bool = False
    # Tier 3.7 acceptance-runner subprocess timeout, in seconds. Default
    # 120 — generous enough for a normal test suite, low enough that a
    # truly stuck command surfaces an [ENVIRONMENT:timeout-after-...]
    # finding before the wrapper's outer phase wall-clock budget is
    # consumed. Operator-tunable per scaffold via verify-config.json.
    acceptance_timeout_seconds: int = 120


# ---------------------------------------------------------------------------
# Plan parsing
# ---------------------------------------------------------------------------


@dataclass
class PhaseSpecWithPaths:
    """One phase block from PLAN.md, including its declared paths.

    `paths_empty` is True when the `Paths:` line was present but blank
    (the parser tolerates this; the tool callable can decide whether
    such a phase is verifiable). `id` and `paths` are populated from
    the parsed text; `title` is the trailing text on the `## Phase N:`
    header line (may be empty).

    `acceptance_command` (added for r7.11 F-7 fix): the operator's
    declared command string for tier 3.7. None when the phase block
    omitted the field OR when the field's value was blank (treated
    identically — the field's PRESENCE with content is the opt-in for
    tier 3.7).
    """

    id: int
    title: str
    paths: List[str]
    paths_empty: bool = False
    acceptance_command: Optional[str] = None


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def _format_json_error(path: Path, exc: json.JSONDecodeError) -> str:
    return (
        f"verify-config.json at {path}: invalid JSON "
        f"(line {exc.lineno}, col {exc.colno}): {exc.msg}"
    )


def load_verify_config(
    path: Optional[Union[str, Path]],
) -> VerifyConfig:
    """Load verify-config.json from `path`, returning a resolved
    VerifyConfig with defaults filled in.

    Returns defaults when `path is None` OR the file does not exist
    (the config is optional). Raises ConfigError on parse error,
    version mismatch, or schema violation. Unknown extra keys are
    tolerated for forward-compat (note logged via stderr-like, but no
    raise).
    """
    if path is None:
        return VerifyConfig()
    p = Path(path)
    if not p.exists():
        return VerifyConfig()
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(
            f"verify-config.json at {p}: unreadable ({exc})"
        ) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(_format_json_error(p, exc)) from exc

    if not isinstance(data, dict):
        raise ConfigError(
            f"verify-config.json at {p}: top-level must be an object, "
            f"got {type(data).__name__}"
        )

    schema_version = data.get("schema_version")
    if schema_version is None:
        raise ConfigError(
            f"verify-config.json at {p}: missing required field "
            f"'schema_version' (expected {CONFIG_SCHEMA_VERSION!r})"
        )
    if schema_version != CONFIG_SCHEMA_VERSION:
        raise ConfigError(
            f"verify-config.json at {p}: unsupported schema_version "
            f"{schema_version!r}; expected {CONFIG_SCHEMA_VERSION!r}"
        )

    section = data.get("verify_phase", {})
    if not isinstance(section, dict):
        raise ConfigError(
            f"verify-config.json at {p}: 'verify_phase' must be an "
            f"object, got {type(section).__name__}"
        )

    cfg = VerifyConfig()

    if "cat1_extra_allow_list" in section:
        v = section["cat1_extra_allow_list"]
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise ConfigError(
                f"verify-config.json at {p}: "
                "'verify_phase.cat1_extra_allow_list' must be a list of "
                "strings"
            )
        cfg.cat1_extra_allow_list = list(v)

    for int_key in (
        "presence_min_bytes",
        "presence_min_nonblank_lines",
        "runtime_smoke_test_timeout",
        "acceptance_timeout_seconds",
    ):
        if int_key in section:
            v = section[int_key]
            if not isinstance(v, int) or isinstance(v, bool):
                raise ConfigError(
                    f"verify-config.json at {p}: "
                    f"'verify_phase.{int_key}' must be an integer"
                )
            setattr(cfg, int_key, v)

    if "runtime_smoke_test_default" in section:
        v = section["runtime_smoke_test_default"]
        if not isinstance(v, bool):
            raise ConfigError(
                f"verify-config.json at {p}: "
                "'verify_phase.runtime_smoke_test_default' must be a bool"
            )
        cfg.runtime_smoke_test_default = v

    # Forward-compat: unknown extra keys at top level OR inside verify_phase
    # are tolerated. We don't raise; we don't log loudly either, to keep
    # the substrate quiet.

    return cfg


# ---------------------------------------------------------------------------
# PLAN.md parser
# ---------------------------------------------------------------------------


_PHASE_HEADER_RE = re.compile(
    r"^##\s+Phase\s+(\d+)\s*:?\s*(.*?)\s*$",
    re.IGNORECASE,
)


def parse_plan_md(path: Union[str, Path]) -> List[PhaseSpecWithPaths]:
    """Parse PLAN.md per §4 format. Returns one entry per `## Phase N:`
    block.

    Strict requirements per block:
      - The phase header line MUST match `## Phase N: <title>` where N
        is an integer (case-insensitive on "Phase"; trailing colon
        optional; title may be empty).
      - The block MUST contain a `Paths:` line. Empty paths-line is
        tolerated (paths_empty=True) but the absence of any Paths line
        is a hard error.

    Tolerated:
      - Extra whitespace around colons / paths.
      - Missing optional fields (Acceptance Criteria, Acceptance
        Command, Size estimate, Objective).
      - Lines outside any phase block (treated as preamble).
      - Trailing content on the Paths line.

    Optional `Acceptance Command:` field per phase (r7.11 F-7 fix):
      - Bullet/dash prefix tolerated (`- Acceptance Command:` or bare).
      - Case-insensitive on the label.
      - Trailing whitespace stripped.
      - Absent OR present-but-blank both yield `acceptance_command=None`
        on the returned PhaseSpecWithPaths (the operator opted out by
        omission OR by leaving it blank — same effect, parser doesn't
        raise on either).
      - Distinct from `Acceptance Criteria:` — the latter is freeform
        prose for human readers; this is a runnable shell command for
        tier 3.7. We match `acceptance command` specifically (with the
        space) so the longer prose label doesn't accidentally hit.

    Raises ToolError on missing file, unparseable header, or missing
    Paths line within a phase block. Error messages name the file and
    offending block.
    """
    p = Path(path)
    if not p.exists():
        raise ToolError(f"PLAN.md not found at {p}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"PLAN.md at {p}: unreadable ({exc})") from exc

    lines = text.splitlines()

    # Identify phase header line indices.
    headers: List[tuple] = []  # (idx, lineno_1based, phase_id, title)
    for i, raw in enumerate(lines):
        m = _PHASE_HEADER_RE.match(raw)
        if m:
            try:
                pid = int(m.group(1))
            except ValueError:
                raise ToolError(
                    f"PLAN.md at {p}, line {i + 1}: phase id "
                    f"{m.group(1)!r} is not an integer"
                )
            headers.append((i, i + 1, pid, m.group(2).strip()))

    if not headers:
        raise ToolError(
            f"PLAN.md at {p}: no '## Phase N: <title>' header found"
        )

    phases: List[PhaseSpecWithPaths] = []
    for j, (start_idx, header_lineno, pid, title) in enumerate(headers):
        end_idx = headers[j + 1][0] if j + 1 < len(headers) else len(lines)
        block = lines[start_idx + 1: end_idx]

        paths_line: Optional[str] = None
        acceptance_command_value: Optional[str] = None
        for bl in block:
            stripped = bl.strip()
            # Match "Paths:" or "paths:" (case-insensitive), tolerant of
            # bullet prefixes like "- Paths:".
            low = stripped.lstrip("-* \t").lower()
            if paths_line is None and low.startswith("paths:"):
                # Extract everything after the first ':'
                idx = stripped.lower().find("paths:")
                paths_line = stripped[idx + len("paths:"):].strip()
                # Don't break — keep walking so we can also pick up
                # acceptance_command if present elsewhere in the block.
                continue
            # Acceptance Command: <command>. Match "acceptance command:"
            # (with the space) to avoid false-matching the longer
            # "Acceptance Criteria:" label. Case-insensitive.
            if (
                acceptance_command_value is None
                and low.startswith("acceptance command:")
            ):
                idx = stripped.lower().find("acceptance command:")
                acceptance_command_value = stripped[
                    idx + len("acceptance command:"):
                ].strip()
                continue

        if paths_line is None:
            raise ToolError(
                f"PLAN.md at {p}: phase block 'Phase {pid}' "
                f"(line {header_lineno}) is missing a 'Paths:' line"
            )

        # Treat present-but-blank acceptance_command as absent. The
        # operator's intent is "no acceptance check" either way.
        normalized_acceptance: Optional[str] = (
            acceptance_command_value
            if acceptance_command_value
            else None
        )

        if paths_line == "":
            phases.append(
                PhaseSpecWithPaths(
                    id=pid,
                    title=title,
                    paths=[],
                    paths_empty=True,
                    acceptance_command=normalized_acceptance,
                )
            )
            continue

        raw_parts = paths_line.split(",")
        cleaned = [s.strip() for s in raw_parts if s.strip()]
        phases.append(
            PhaseSpecWithPaths(
                id=pid,
                title=title,
                paths=cleaned,
                paths_empty=False,
                acceptance_command=normalized_acceptance,
            )
        )

    return phases


# ---------------------------------------------------------------------------
# Tool callable
# ---------------------------------------------------------------------------


def _result_to_dict(result: VerifyResult, persisted_to: str) -> Dict[str, Any]:
    """Serialize VerifyResult to the §3 returns schema. Enums (none in
    VerifyResult; tier_run is already int) are left as-is. `persisted_to`
    is set by the wrapper (this function) — verify_phase itself does
    not write the file."""
    return {
        "passed": bool(result.passed),
        "tier_run": int(result.tier_run),
        "missing_paths": list(result.missing_paths),
        "integrity_issues": list(result.integrity_issues),
        "runtime_smoke_findings": list(result.runtime_smoke_findings),
        "acceptance_runner_findings": list(result.acceptance_runner_findings),
        "semantic_concerns": list(result.semantic_concerns),
        "tier_3_hint": result.tier_3_hint,
        "corrective_dispatch": result.corrective_dispatch or "",
        "persisted_to": persisted_to,
    }


def _synthetic_session_id() -> str:
    return f"tool-call-{int(time.time())}"


def verify_phase_tool(
    phase_id: int,
    *,
    scaffold_root: Union[str, Path],
    tier: int = 3,
    with_runtime_smoke_test: Optional[bool] = None,
    verify_config_path: Optional[Union[str, Path]] = None,
    plan_md_path: Optional[Union[str, Path]] = None,
    verified_state_path: Optional[Union[str, Path]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify a single phase end-to-end.

    Item 6's Hermes registration will call this function with
    `session_id` injected from the live Hermes session_id; for now,
    `session_id=None` synthesizes one. All other parameters are the
    wrapper's tool surface per §3.

    Behavior:
      1. Load verify-config.json (defaults if absent).
      2. Parse PLAN.md.
      3. Load (or bootstrap) verified-state.json.
      4. Find the requested phase_id in PLAN.md.
      5. Build PhaseInput + project_phases for phase-awareness.
      6. Resolve with_runtime_smoke_test (param > config default).
      7. Call verify_phase.verify_phase(...).
      8. Record verdict via verified_state.record_verdict + save.
      9. Return a dict matching §3's returns schema.

    Raises:
      ConfigError on malformed verify-config.json.
      ToolError on missing PLAN.md, missing scaffold_root, unknown
        phase_id, or other operational failures.
      NotImplementedError if tier=4 (deferred to r7.12).
    """
    if not isinstance(phase_id, int):
        raise ToolError(f"phase_id must be int, got {type(phase_id).__name__}")

    scaffold = Path(scaffold_root)
    if not scaffold.exists():
        raise ToolError(
            f"scaffold_root does not exist: {scaffold}"
        )
    if not scaffold.is_dir():
        raise ToolError(
            f"scaffold_root is not a directory: {scaffold}"
        )

    cfg_path = (
        Path(verify_config_path)
        if verify_config_path is not None
        else scaffold / "verify-config.json"
    )
    plan_path = (
        Path(plan_md_path)
        if plan_md_path is not None
        else scaffold / "PLAN.md"
    )
    state_path = (
        Path(verified_state_path)
        if verified_state_path is not None
        else scaffold / "verified-state.json"
    )

    cfg = load_verify_config(cfg_path)
    phases = parse_plan_md(plan_path)

    # ---- Load or bootstrap verified-state.json ----
    if state_path.exists():
        try:
            state = load(state_path)
        except verified_state.SchemaError as exc:
            raise ToolError(
                f"verified-state.json at {state_path} invalid: {exc}"
            ) from exc
    else:
        spec_phases = [
            PhaseSpec(id=p.id, title=p.title) for p in phases
        ]
        state = bootstrap(
            scaffold_root=str(scaffold),
            plan_md_path=str(plan_path),
            phases=spec_phases,
        )
        save(state, state_path)

    # ---- Verify phase_id is in spec ----
    target: Optional[PhaseSpecWithPaths] = next(
        (p for p in phases if p.id == phase_id), None
    )
    if target is None:
        known_ids = sorted(p.id for p in phases)
        raise ToolError(
            f"phase_id={phase_id} not present in PLAN.md "
            f"(known phases: {known_ids})"
        )
    spec_ids = {p.id for p in state.spec.phases}
    if phase_id not in spec_ids:
        raise ToolError(
            f"phase_id={phase_id} present in PLAN.md but not in "
            f"verified-state.json spec (known: {sorted(spec_ids)}); "
            "scaffold may be in inconsistent state"
        )

    # ---- Build PhaseInput + project_phases ----
    phase_input = PhaseInput(id=target.id, paths=list(target.paths))
    project_phases = [
        PhaseInput(id=p.id, paths=list(p.paths)) for p in phases
    ]

    # ---- Resolve with_runtime_smoke_test ----
    if with_runtime_smoke_test is None:
        smoke = cfg.runtime_smoke_test_default
    else:
        smoke = bool(with_runtime_smoke_test)

    # ---- Run verify_phase ----
    result = vp_mod.verify_phase(
        phase_input,
        scaffold,
        tier=tier,
        presence_min_bytes=cfg.presence_min_bytes,
        presence_min_nonblank_lines=cfg.presence_min_nonblank_lines,
        project_phases=project_phases,
        with_runtime_smoke_test=smoke,
        runtime_smoke_test_timeout=cfg.runtime_smoke_test_timeout,
        cat1_extra_allow_list=list(cfg.cat1_extra_allow_list),
        acceptance_command=target.acceptance_command,
        acceptance_timeout_seconds=cfg.acceptance_timeout_seconds,
    )

    # ---- Persist verdict ----
    sid = session_id if session_id else _synthetic_session_id()

    new_state = record_verdict(
        state=state,
        phase_id=phase_id,
        passed=result.passed,
        session_id=sid,
        tier_run=result.tier_run,
        missing_paths=result.missing_paths,
        integrity_issues=result.integrity_issues,
        runtime_smoke_findings=result.runtime_smoke_findings,
        acceptance_runner_findings=result.acceptance_runner_findings,
        semantic_concerns=result.semantic_concerns,
        corrective_dispatch=result.corrective_dispatch or None,
    )
    save(new_state, state_path)

    return _result_to_dict(result, persisted_to=str(state_path))


# ---------------------------------------------------------------------------
# Hermes tool definition (paste-ready for item 6)
# ---------------------------------------------------------------------------


TOOL_NAME = "verify_phase"


TOOL_DESCRIPTION = (
    "Verify a phase's deliverables against PLAN.md and persist the "
    "verdict to verified-state.json (the wrapper's machine-authoritative "
    "source of truth). Trust this tool's structured output, not your "
    "own narrative.\n"
    "\n"
    "Tiers (cumulative, deterministic for 1-3.5):\n"
    "  1 PRESENCE — declared paths exist with non-trivial bodies.\n"
    "  2 SYNTAX  — Python files parse; no `raise NotImplementedError` in\n"
    "              non-test code; imports resolve.\n"
    "  3 WIRING  — defined symbols are referenced; tests reference real\n"
    "              implementations; no duplicate definitions; default tier.\n"
    "  3.5 RUNTIME SMOKE TEST — opt-in via `with_runtime_smoke_test=true`.\n"
    "       Imports the phase's modules in a sandboxed subprocess and "
    "inspects\n"
    "       runtime registry state. Catches importlib-shadowing patterns\n"
    "       AST analysis cannot resolve. Recommended when PLAN.md declares\n"
    "       modules with import-time side effects (registries, plugin\n"
    "       loaders, monkey-patches).\n"
    "  3.7 ACCEPTANCE RUNNER — implicit when PLAN.md declares `Acceptance\n"
    "       Command:` for the phase. Runs that command as a subprocess in\n"
    "       scaffold_root with the scaffold .venv on PYTHONPATH; classifies\n"
    "       the exit code (pytest-aware) into ACCEPTANCE_PASSED /\n"
    "       ACCEPTANCE_FAILED:N / ENVIRONMENT:.. / INCONCLUSIVE:.. and\n"
    "       captures truncated stdout+stderr into corrective_dispatch on\n"
    "       failure. Gated by tier 1 + tier 2 (no point running an\n"
    "       acceptance command on broken syntax).\n"
    "  4 SEMANTIC — deferred to r7.12; not callable.\n"
    "\n"
    "On passed=false, the result includes `corrective_dispatch` — a\n"
    "complete, paste-ready re-dispatch goal following OBJECTIVE/PATHS/\n"
    "ACCEPTANCE. Worked examples of the shape:\n"
    "  - n=10 r4 / PDF importlib-shadowing:\n"
    "    \"Re-dispatch with explicit focus on src/export/pdf.py "
    "PDFSerializer\n"
    "    registration. The duplicate registration in formats_init.py is\n"
    "    shadowing the real serializer at runtime; either remove\n"
    "    formats_init.py or update PDFSerializer registration order so the\n"
    "    reportlab-based class wins.\"\n"
    "  - n=5 r5 / unwired serializers:\n"
    "    \"Re-dispatch with explicit focus on src/api/export.py imports.\n"
    "    Endpoints currently inline serialization; they should import\n"
    "    serialize_to_csv / serialize_to_json / serialize_to_pdf from\n"
    "    src/export/ and call those functions instead of inlining.\"\n"
    "\n"
    "Re-dispatch via delegate_worker with the corrective_dispatch text\n"
    "as the goal. The wrapper reads verified-state.json (not your\n"
    "narrative summary) to decide what happens next."
)


TOOL_PARAMETERS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "phase_id": {
            "type": "integer",
            "description": (
                "Phase number from PLAN.md to verify."
            ),
        },
        "tier": {
            "type": "integer",
            "enum": [1, 2, 3, 4],
            "default": 3,
            "description": (
                "Verification tier. 1=presence, 2=syntax, 3=wiring (default),"
                " 4=semantic (deferred to r7.12). Tiers are cumulative; "
                "tier=N runs 1..N."
            ),
        },
        "with_runtime_smoke_test": {
            "type": ["boolean", "null"],
            "default": None,
            "description": (
                "Opt-in sub-tier 3.5 runtime smoke test. Imports the "
                "phase's PLAN.md modules in a sandboxed subprocess and "
                "inspects registry contents. Catches importlib-shadowing "
                "patterns AST analysis cannot resolve. When null, falls "
                "back to verify-config.json's runtime_smoke_test_default."
            ),
        },
        "scaffold_root": {
            "type": "string",
            "description": (
                "Absolute path to the project root containing PLAN.md "
                "and verified-state.json."
            ),
        },
        "verify_config_path": {
            "type": ["string", "null"],
            "default": None,
            "description": (
                "Optional path to verify-config.json. Defaults to "
                "<scaffold_root>/verify-config.json."
            ),
        },
        "plan_md_path": {
            "type": ["string", "null"],
            "default": None,
            "description": (
                "Optional path to PLAN.md. Defaults to "
                "<scaffold_root>/PLAN.md."
            ),
        },
        "verified_state_path": {
            "type": ["string", "null"],
            "default": None,
            "description": (
                "Optional path to verified-state.json. Defaults to "
                "<scaffold_root>/verified-state.json."
            ),
        },
    },
    "required": ["phase_id", "scaffold_root"],
    "additionalProperties": False,
}


TOOL_RETURNS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "passed": {
            "type": "boolean",
            "description": "Overall verdict for this phase.",
        },
        "tier_run": {
            "type": "integer",
            "description": (
                "The integer tier that produced the verdict. Tier 3.5 "
                "findings are surfaced via runtime_smoke_findings; "
                "tier_run remains the integer tier."
            ),
        },
        "missing_paths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files PLAN.md declared but that don't exist or are stub-trivial.",
        },
        "integrity_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Tier 2 (syntax/import) and tier 3 (wiring) findings. "
                "Tier-3 entries are prefixed [CAT1:..]/[CAT2:..]/"
                "[CAT3:..]/[CAT4:..]."
            ),
        },
        "runtime_smoke_findings": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Sub-tier 3.5 findings, prefixed "
                "[SHADOWING:..]/[CHECKED:..]/[INCONCLUSIVE:..]/[SKIPPED]. "
                "Only [SHADOWING:..] sets passed=false."
            ),
        },
        "acceptance_runner_findings": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Sub-tier 3.7 (acceptance-runner) findings, prefixed "
                "[ACCEPTANCE_PASSED]/[ACCEPTANCE_FAILED:N]/"
                "[ENVIRONMENT:..]/[INCONCLUSIVE:..]/[SKIPPED]. "
                "[ACCEPTANCE_FAILED:..] and [ENVIRONMENT:..] set "
                "passed=false. Empty when PLAN.md did not declare an "
                "Acceptance Command for this phase."
            ),
        },
        "semantic_concerns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tier 4 only; empty in this build.",
        },
        "tier_3_hint": {
            "type": ["string", "null"],
            "description": (
                "Set when tier 3 detected dynamic-dispatch markers "
                "(importlib.import_module, exec/eval, etc.); recommends "
                "calling again with with_runtime_smoke_test=true."
            ),
        },
        "corrective_dispatch": {
            "type": "string",
            "description": (
                "Paste-ready re-dispatch goal when passed=false. Empty "
                "string when passed=true."
            ),
        },
        "persisted_to": {
            "type": "string",
            "description": "Absolute path to verified-state.json.",
        },
    },
    "required": [
        "passed",
        "tier_run",
        "missing_paths",
        "integrity_issues",
        "runtime_smoke_findings",
        "acceptance_runner_findings",
        "semantic_concerns",
        "tier_3_hint",
        "corrective_dispatch",
        "persisted_to",
    ],
}


__all__ = [
    "ConfigError",
    "ToolError",
    "VerifyConfig",
    "PhaseSpecWithPaths",
    "load_verify_config",
    "parse_plan_md",
    "verify_phase_tool",
    "TOOL_NAME",
    "TOOL_DESCRIPTION",
    "TOOL_PARAMETERS_SCHEMA",
    "TOOL_RETURNS_SCHEMA",
    "CONFIG_SCHEMA_VERSION",
]
