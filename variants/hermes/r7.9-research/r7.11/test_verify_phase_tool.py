"""Tests for verify_phase_tool (r7.11 item 5).

Runnable two ways:
  pytest test_verify_phase_tool.py -v
  python3 test_verify_phase_tool.py     (falls back to plain assertions)

Coverage:
  - Config loader (5 tests, C1-C6).
  - PLAN.md parser (4 tests, P1-P4).
  - Tool callable end-to-end (5 tests, T1-T5).
  - Backward-compat smoke (B1).
  - Plus 2 extras (E1-E2): tool definition surface; enum/serialization shape.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Allow `python3 test_verify_phase_tool.py` from any CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_phase_tool as vpt  # noqa: E402
from verify_phase_tool import (  # noqa: E402
    CONFIG_SCHEMA_VERSION,
    ConfigError,
    PhaseSpecWithPaths,
    ToolError,
    VerifyConfig,
    load_verify_config,
    parse_plan_md,
    verify_phase_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SUBSTANTIVE_BODY = (
    '"""substantive module."""\n'
    "import os\n"
    "VALUE = 42\n"
    "def f():\n"
    "    return VALUE\n"
)


_GOOD_PLAN = """\
# Project plan

Some preamble text. Ignored by parser.

## Phase 1: Core serializers
Objective: implement CSV / JSON serializers.
Paths: src/export/csv.py, src/export/json.py
Acceptance Criteria:
  - both serializers emit valid output
Size estimate: medium

## Phase 2: API + permissions
Objective: wire the API endpoints to the serializers.
Paths:   src/api/export.py ,  src/auth/permissions.py
Acceptance Criteria: endpoints call serializers; auth enforced
Size estimate: medium

## Phase 3: Tests + docs
Objective: integration tests + README.
Paths: tests/test_export.py
Size estimate: small
"""


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _write_config(root: Path, body: str | dict, name: str = "verify-config.json") -> Path:
    p = root / name
    if isinstance(body, dict):
        body = json.dumps(body, indent=2)
    p.write_text(body, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Config loader (C1-C6)
# ---------------------------------------------------------------------------


def test_C1_absent_path_returns_defaults():
    cfg = load_verify_config(None)
    assert isinstance(cfg, VerifyConfig)
    assert cfg.cat1_extra_allow_list == []
    assert cfg.presence_min_bytes == 50
    assert cfg.presence_min_nonblank_lines == 3
    assert cfg.runtime_smoke_test_timeout == 10
    assert cfg.runtime_smoke_test_default is False


def test_C2_absent_file_at_path_returns_defaults():
    with tempfile.TemporaryDirectory() as d:
        cfg = load_verify_config(Path(d) / "does-not-exist.json")
    assert cfg == VerifyConfig()


def test_C3_full_valid_file_returns_all_values():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {
                    "cat1_extra_allow_list": ["router", "app", "ws_app"],
                    "presence_min_bytes": 100,
                    "presence_min_nonblank_lines": 5,
                    "runtime_smoke_test_timeout": 15,
                    "runtime_smoke_test_default": True,
                },
            },
        )
        cfg = load_verify_config(path)
    assert cfg.cat1_extra_allow_list == ["router", "app", "ws_app"]
    assert cfg.presence_min_bytes == 100
    assert cfg.presence_min_nonblank_lines == 5
    assert cfg.runtime_smoke_test_timeout == 15
    assert cfg.runtime_smoke_test_default is True


def test_C4_partial_file_fills_in_defaults():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {
                    "cat1_extra_allow_list": ["ws_app"],
                },
            },
        )
        cfg = load_verify_config(path)
    assert cfg.cat1_extra_allow_list == ["ws_app"]
    # Defaults preserved for everything else.
    assert cfg.presence_min_bytes == 50
    assert cfg.presence_min_nonblank_lines == 3
    assert cfg.runtime_smoke_test_timeout == 10
    assert cfg.runtime_smoke_test_default is False


def test_C5_malformed_json_raises_with_line_col():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Malformed JSON: trailing comma on line 3 (or similar).
        path = _write_config(
            root,
            '{\n  "schema_version": "1.0",\n  "verify_phase": {,}\n}\n',
        )
        try:
            load_verify_config(path)
        except ConfigError as exc:
            msg = str(exc)
            assert "line" in msg.lower(), msg
            # message should include some line number
            assert any(c.isdigit() for c in msg), msg
        else:
            raise AssertionError("expected ConfigError on malformed JSON")


def test_C7_acceptance_timeout_seconds_default_and_override():
    """acceptance_timeout_seconds defaults to 120; explicit value is
    parsed; non-int (incl. bool) raises ConfigError."""
    # Default
    assert load_verify_config(None).acceptance_timeout_seconds == 120

    # Explicit override
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {"acceptance_timeout_seconds": 30},
            },
        )
        cfg = load_verify_config(path)
    assert cfg.acceptance_timeout_seconds == 30
    # Other fields keep defaults
    assert cfg.runtime_smoke_test_timeout == 10

    # Bool rejected (bool is int in Python; we explicitly disallow)
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {"acceptance_timeout_seconds": True},
            },
        )
        try:
            load_verify_config(path)
        except ConfigError as exc:
            assert "acceptance_timeout_seconds" in str(exc)
        else:
            raise AssertionError(
                "expected ConfigError on bool acceptance_timeout_seconds"
            )


def test_C6_schema_version_mismatch_raises():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = _write_config(
            root,
            {
                "schema_version": "9.9",
                "verify_phase": {},
            },
        )
        try:
            load_verify_config(path)
        except ConfigError as exc:
            msg = str(exc)
            assert "9.9" in msg
            assert "1.0" in msg
        else:
            raise AssertionError("expected ConfigError on schema version mismatch")


# ---------------------------------------------------------------------------
# PLAN.md parser (P1-P4)
# ---------------------------------------------------------------------------


def test_P1_well_formed_multiphase_plan():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(_GOOD_PLAN, encoding="utf-8")
        phases = parse_plan_md(path)
    assert len(phases) == 3
    assert [p.id for p in phases] == [1, 2, 3]
    assert phases[0].title.startswith("Core serializers")
    assert phases[0].paths == ["src/export/csv.py", "src/export/json.py"]
    # Paths line with extra whitespace stripped properly.
    assert phases[1].paths == [
        "src/api/export.py",
        "src/auth/permissions.py",
    ]
    assert phases[2].paths == ["tests/test_export.py"]
    assert all(not p.paths_empty for p in phases)


def test_P2_missing_plan_md_raises_tool_error():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        try:
            parse_plan_md(root / "PLAN.md")
        except ToolError as exc:
            assert "PLAN.md" in str(exc)
            assert str(root) in str(exc)
        else:
            raise AssertionError("expected ToolError on missing PLAN.md")


def test_P3_phase_block_missing_paths_raises():
    bad = """\
## Phase 1: First
Objective: do something
Acceptance Criteria: works

## Phase 2: Second
Paths: src/b.py
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(bad, encoding="utf-8")
        try:
            parse_plan_md(path)
        except ToolError as exc:
            msg = str(exc)
            assert "Phase 1" in msg, msg
            assert "Paths" in msg, msg
        else:
            raise AssertionError("expected ToolError on missing Paths line")


def test_P4_paths_with_whitespace_get_stripped():
    p_text = """\
## Phase 1: T1
Paths:    src/a.py ,    src/sub/b.py   ,src/c.py
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(p_text, encoding="utf-8")
        phases = parse_plan_md(path)
    assert len(phases) == 1
    assert phases[0].paths == ["src/a.py", "src/sub/b.py", "src/c.py"]


def test_P6_acceptance_command_parsed():
    """Acceptance Command: <cmd> populates PhaseSpecWithPaths.acceptance_command."""
    text = """\
## Phase 1: Core
Paths: src/m.py
Acceptance Command: pytest tests/test_export.py

## Phase 2: API
Paths: src/api.py
- Acceptance Command:   python -m pytest tests/

## Phase 3: Plain
Paths: src/n.py
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(text, encoding="utf-8")
        phases = parse_plan_md(path)
    assert len(phases) == 3
    assert phases[0].acceptance_command == "pytest tests/test_export.py"
    # Bullet prefix tolerated; trailing whitespace stripped.
    assert phases[1].acceptance_command == "python -m pytest tests/"
    # Phase 3 omitted -> None
    assert phases[2].acceptance_command is None


def test_P7_acceptance_command_blank_treated_as_absent():
    """Present-but-blank Acceptance Command: should yield None (same
    as absent), not the empty string."""
    text = """\
## Phase 1: Core
Paths: src/m.py
Acceptance Command:

## Phase 2: API
Paths: src/api.py
acceptance command:
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(text, encoding="utf-8")
        phases = parse_plan_md(path)
    assert phases[0].acceptance_command is None
    assert phases[1].acceptance_command is None


def test_P8_acceptance_command_does_not_match_acceptance_criteria():
    """The longer prose label `Acceptance Criteria:` must NOT be picked
    up as `Acceptance Command:` (regression guard for the substring
    match)."""
    text = """\
## Phase 1: Core
Paths: src/m.py
Acceptance Criteria: things should work nicely
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(text, encoding="utf-8")
        phases = parse_plan_md(path)
    assert phases[0].acceptance_command is None


def test_P9_legacy_plan_md_no_acceptance_command_field_unchanged():
    """A PLAN.md with no Acceptance Command field anywhere parses
    EXACTLY as before — full backward compatibility."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(_GOOD_PLAN, encoding="utf-8")
        phases = parse_plan_md(path)
    # Same shape as test_P1, plus None for the new field.
    assert all(p.acceptance_command is None for p in phases)


def test_P5_empty_paths_line_tolerated():
    """Bonus: empty Paths line is allowed but flagged via paths_empty."""
    p_text = """\
## Phase 1: T1
Paths:
Objective: TBD

## Phase 2: T2
Paths: src/b.py
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = root / "PLAN.md"
        path.write_text(p_text, encoding="utf-8")
        phases = parse_plan_md(path)
    assert len(phases) == 2
    assert phases[0].paths == []
    assert phases[0].paths_empty is True
    assert phases[1].paths_empty is False


# ---------------------------------------------------------------------------
# Tool callable end-to-end (T1-T5)
# ---------------------------------------------------------------------------


def _build_clean_2phase_scaffold(root: Path, with_config: bool = True) -> None:
    """Build a 2-phase scaffold with files clean enough to pass tier 2.

    Phase 1: src/m.py
    Phase 2: src/n.py (imports from src.m)
    """
    plan = """\
## Phase 1: Core
Paths: src/__init__.py, src/m.py

## Phase 2: Wiring
Paths: src/n.py
"""
    (root / "PLAN.md").write_text(plan, encoding="utf-8")
    _write(
        root, "src/__init__.py",
        '"""package init."""\nVERSION = "1.0"\nNAME = "scaffold-test"\nDEFAULT_LIMIT = 100\n',
    )
    _write(
        root,
        "src/m.py",
        '"""m."""\nVALUE = 1\ndef get_value():\n    return VALUE\n',
    )
    _write(
        root,
        "src/n.py",
        '"""n."""\nfrom src.m import get_value\n'
        'def proxy():\n    return get_value()\nUSE = proxy()\n',
    )
    if with_config:
        _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {},
            },
        )


def test_T1_happy_path_tier2_persists_state():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_clean_2phase_scaffold(root)
        out = verify_phase_tool(
            phase_id=1, tier=2, scaffold_root=root
        )
        expected_keys = {
            "passed", "tier_run", "missing_paths", "integrity_issues",
            "runtime_smoke_findings", "acceptance_runner_findings",
            "semantic_concerns", "tier_3_hint", "corrective_dispatch",
            "persisted_to",
        }
        assert set(out.keys()) == expected_keys, out
        assert out["passed"] is True, out
        assert out["tier_run"] == 2
        assert out["persisted_to"].endswith("verified-state.json")
        # Re-load file to confirm persistence (inside the temp scope).
        state_path = Path(out["persisted_to"])
        assert state_path.exists(), out
        data = json.loads(state_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        phase_state = data["phase_state"]
        p1_entry = next(p for p in phase_state if p["id"] == 1)
        assert p1_entry["status"] == "verified_passed"
        assert p1_entry["tier_run"] == 2


def test_T2_tier3_cat1_extra_allow_list_from_config():
    """ws_app declared but unreferenced. With cat1_extra_allow_list=['ws_app']
    in config -> passes. Without -> CAT1 flagged."""
    plan = """\
## Phase 1: API
Paths: src/__init__.py, src/api.py
"""
    body = (
        '"""api — ws_app picked up by framework string lookup."""\n'
        "ws_app = object()\n"
        "VAL = 1\n"
        "def helper():\n"
        "    return VAL\n"
    )
    # Case A: with extra allow-list
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "PLAN.md").write_text(plan, encoding="utf-8")
        _write(
            root, "src/__init__.py",
            '"""package init for tests."""\n'
            "VERSION = '1.0'\n"
            "NAME = 'scaffold'\n"
            "DEFAULT_LIMIT = 100\n",
        )
        _write(root, "src/api.py", body)
        _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {
                    "cat1_extra_allow_list": ["ws_app"],
                },
            },
        )
        out = verify_phase_tool(phase_id=1, tier=3, scaffold_root=root)
    cat1 = [
        i for i in out["integrity_issues"] if "[CAT1:defined-unused]" in i
    ]
    assert not any("`ws_app`" in i for i in cat1), out["integrity_issues"]

    # Case B: without it — ws_app IS flagged
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "PLAN.md").write_text(plan, encoding="utf-8")
        _write(
            root, "src/__init__.py",
            '"""package init for tests."""\n'
            "VERSION = '1.0'\n"
            "NAME = 'scaffold'\n"
            "DEFAULT_LIMIT = 100\n",
        )
        _write(root, "src/api.py", body)
        # No config file -> default cat1_extra_allow_list = []
        out = verify_phase_tool(phase_id=1, tier=3, scaffold_root=root)
    cat1 = [
        i for i in out["integrity_issues"] if "[CAT1:defined-unused]" in i
    ]
    assert any("`ws_app`" in i for i in cat1), out["integrity_issues"]


def test_T3_runtime_smoke_test_default_from_config():
    """runtime_smoke_test_default=true in config; no explicit param -> 3.5 runs."""
    plan = """\
## Phase 1: Core
Paths: src/__init__.py, src/m.py
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "PLAN.md").write_text(plan, encoding="utf-8")
        _write(
            root, "src/__init__.py",
            '"""package init for tests."""\n'
            "VERSION = '1.0'\n"
            "NAME = 'scaffold'\n"
            "DEFAULT_LIMIT = 100\n",
        )
        _write(
            root,
            "src/m.py",
            (
                '"""m with registry."""\n'
                "class A:\n"
                "    pass\n"
                "REGISTRY = {'a': A}\n"
                "def use_it():\n"
                "    return REGISTRY['a']()\n"
            ),
        )
        _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {
                    "runtime_smoke_test_default": True,
                },
            },
        )
        out = verify_phase_tool(phase_id=1, tier=2, scaffold_root=root)
    # Tier 3.5 should have run -> findings non-empty
    assert out["runtime_smoke_findings"], out
    # Subset must include [CHECKED:..] (clean registry case)
    assert any(
        f.startswith("[CHECKED:") for f in out["runtime_smoke_findings"]
    )


def test_T4_bootstrap_on_first_call():
    """Scaffold has PLAN.md + files but no verified-state.json -> wrapper
    bootstraps it before verification."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_clean_2phase_scaffold(root)
        state_path = root / "verified-state.json"
        assert not state_path.exists(), "precondition: state file absent"
        out = verify_phase_tool(phase_id=1, tier=2, scaffold_root=root)
        assert state_path.exists()
        data = json.loads(state_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        # Spec phases reflect PLAN.md
        spec_ids = [p["id"] for p in data["spec"]["phases"]]
        assert spec_ids == [1, 2]
        # Phase 1 verified_passed; phase 2 still pending
        ps = {p["id"]: p for p in data["phase_state"]}
        assert ps[1]["status"] == "verified_passed"
        assert ps[2]["status"] == "pending"
        assert out["passed"] is True


def test_T5_missing_scaffold_root_raises():
    bad = Path(tempfile.gettempdir()) / "definitely-not-a-real-scaffold-vpt"
    if bad.exists():
        # Defensive: clean up if a prior run left it.
        import shutil
        shutil.rmtree(bad)
    try:
        verify_phase_tool(phase_id=1, scaffold_root=bad)
    except ToolError as exc:
        assert "scaffold_root" in str(exc) or str(bad) in str(exc)
    else:
        raise AssertionError("expected ToolError on missing scaffold_root")


def test_T6_unknown_phase_id_raises():
    """Bonus: phase_id not in PLAN.md -> ToolError."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_clean_2phase_scaffold(root)
        try:
            verify_phase_tool(phase_id=99, tier=2, scaffold_root=root)
        except ToolError as exc:
            assert "99" in str(exc)
        else:
            raise AssertionError("expected ToolError on unknown phase_id")


def test_T7_explicit_smoke_param_overrides_config():
    """Explicit with_runtime_smoke_test=False overrides config True."""
    plan = """\
## Phase 1: Core
Paths: src/__init__.py, src/m.py
"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "PLAN.md").write_text(plan, encoding="utf-8")
        _write(
            root, "src/__init__.py",
            '"""package init for tests."""\n'
            "VERSION = '1.0'\n"
            "NAME = 'scaffold'\n"
            "DEFAULT_LIMIT = 100\n",
        )
        _write(
            root,
            "src/m.py",
            (
                '"""m."""\nclass A:\n    pass\n'
                "REGISTRY = {'a': A}\n"
                "def use_it():\n    return REGISTRY['a']()\n"
            ),
        )
        _write_config(
            root,
            {
                "schema_version": "1.0",
                "verify_phase": {"runtime_smoke_test_default": True},
            },
        )
        out = verify_phase_tool(
            phase_id=1, tier=2,
            with_runtime_smoke_test=False,
            scaffold_root=root,
        )
    # Smoke should NOT have run despite config default=True.
    assert out["runtime_smoke_findings"] == [], out


# ---------------------------------------------------------------------------
# Backward compat smoke (B1)
# ---------------------------------------------------------------------------


def test_B1_existing_verify_phase_tests_still_pass():
    """Run the pre-existing test_verify_phase.py file in-process to confirm
    the additive edit didn't regress 74 existing tests. The 2 new tests for
    cat1_extra_allow_list bring the total to 76."""
    import importlib
    import importlib.util as iutil

    here = Path(__file__).resolve().parent
    spec = iutil.spec_from_file_location(
        "test_verify_phase_module", here / "test_verify_phase.py"
    )
    mod = iutil.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tests = [
        (n, fn) for n, fn in vars(mod).items()
        if n.startswith("test_") and callable(fn)
    ]
    failures = []
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, repr(exc)))
    assert not failures, f"verify_phase tests regressed: {failures}"
    assert len(tests) >= 76, f"expected >=76 tests, got {len(tests)}"


# ---------------------------------------------------------------------------
# Tool definition surface (E1-E2)
# ---------------------------------------------------------------------------


def test_E1_tool_definition_constants_exposed():
    assert vpt.TOOL_NAME == "verify_phase"
    assert isinstance(vpt.TOOL_DESCRIPTION, str)
    assert len(vpt.TOOL_DESCRIPTION) >= 200, "description should be substantive"
    assert "corrective_dispatch" in vpt.TOOL_DESCRIPTION
    assert "verified-state.json" in vpt.TOOL_DESCRIPTION
    assert isinstance(vpt.TOOL_PARAMETERS_SCHEMA, dict)
    assert vpt.TOOL_PARAMETERS_SCHEMA["type"] == "object"
    assert "phase_id" in vpt.TOOL_PARAMETERS_SCHEMA["properties"]
    assert "scaffold_root" in vpt.TOOL_PARAMETERS_SCHEMA["properties"]
    assert isinstance(vpt.TOOL_RETURNS_SCHEMA, dict)
    for k in (
        "passed", "tier_run", "missing_paths", "integrity_issues",
        "runtime_smoke_findings", "semantic_concerns",
        "tier_3_hint", "corrective_dispatch", "persisted_to",
    ):
        assert k in vpt.TOOL_RETURNS_SCHEMA["properties"], k


def test_E2_returned_dict_is_json_serializable():
    """The wrapper's dict result must be JSON-serializable (this is what
    Hermes will pass back as a tool result)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_clean_2phase_scaffold(root)
        out = verify_phase_tool(phase_id=1, tier=2, scaffold_root=root)
    blob = json.dumps(out)  # raises if non-serializable
    assert "passed" in blob


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
