"""Tests for verify_phase module (r7.11 item 2).

Runnable two ways:
  pytest test_verify_phase.py -v
  python3 test_verify_phase.py     (falls back to plain assertions)

Tier-1 cases T1-T8, tier-2 cases T9-T18, mixed/corrective T19-T20, plus
a few extras. All tests build a fresh scaffold under a TemporaryDirectory.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Allow `python3 test_verify_phase.py` from any CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_phase import (  # noqa: E402
    PhaseInput,
    Tier,
    VerifyResult,
    verify_phase,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# A reusable Python body that easily clears tier-1 thresholds (>=50
# bytes, >=3 nonblank lines, not pure-docstring).
SUBSTANTIVE_BODY = (
    '"""substantive module."""\n'
    "import os\n"
    "VALUE = 42\n"
    "def f():\n"
    "    return VALUE\n"
)


# A body that ALSO clears tier 3 (no CAT1/CAT2 issues) — for tier-3.7
# tests that need passed=True after wiring analysis. `__all__` exempts
# all top-level defs from CAT1; `os` is referenced via os.environ so
# the import is used.
TIER3_CLEAN_BODY = (
    '"""tier-3-clean module."""\n'
    "import os\n"
    "VALUE = int(os.environ.get('R7_11_TEST_VAL', '42'))\n"
    "def helper():\n"
    "    return VALUE\n"
    "__all__ = ['VALUE', 'helper']\n"
)


# ---------------------------------------------------------------------------
# Tier 1
# ---------------------------------------------------------------------------


def test_T1_all_present_and_nontrivial():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        _write(root, "src/bar.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py", "src/bar.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is True, r
    assert r.tier_run == 1
    assert r.missing_paths == []
    assert r.corrective_dispatch == ""


def test_T2_one_file_missing():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py", "src/missing.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is False
    assert r.tier_run == 1
    assert "src/missing.py" in r.missing_paths
    assert "src/foo.py" not in r.missing_paths
    assert r.corrective_dispatch != ""


def test_T3_empty_file_treated_as_missing():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", "")
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is False
    assert any("src/foo.py" in m for m in r.missing_paths)


def test_T4_whitespace_only_file_fails():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", "   \n\n\t\n   \n")  # 4 blank lines
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is False
    assert any("src/foo.py" in m for m in r.missing_paths)


def test_T5_pure_docstring_stub_fails_with_note():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Triple-quoted docstring with extra blank lines so it clears
        # the byte+line thresholds — exposing the AST stub check.
        body = (
            '"""\n'
            "this module is intentionally a stub\n"
            "we will fill it in later\n"
            "but we want presence to fail\n"
            '"""\n'
        )
        _write(root, "src/foo.py", body)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is False
    assert any("docstring" in m or "stub" in m for m in r.missing_paths), r.missing_paths


def test_T6_custom_thresholds_pass_at_boundary():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Need ≥50 bytes AND ≥3 nonblank lines AND not pure-docstring stub.
        body = "import os\nimport sys\nimport json\n"  # 31 bytes
        # Pad to exactly 50 bytes:
        pad_needed = 50 - len(body.encode("utf-8"))
        body = body + ("# " + "x" * (pad_needed - 3) + "\n")  # +pad_needed bytes
        assert len(body.encode("utf-8")) == 50
        _write(root, "src/foo.py", body)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is True, r


def test_T7_custom_thresholds_fail_just_below():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        body = "import os\nimport sys\nimport json\n"
        pad_needed = 49 - len(body.encode("utf-8"))
        body = body + ("# " + "x" * (pad_needed - 3) + "\n")
        assert len(body.encode("utf-8")) == 49
        _write(root, "src/foo.py", body)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is False


def test_T8_non_python_file_with_substantive_content_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "PLAN.md",
            "# Plan\n\nPhase 1: do the thing.\nPhase 2: do another thing.\nPhase 3: finalize.\n",
        )
        phase = PhaseInput(id=1, paths=["PLAN.md"])
        r = verify_phase(phase, root, tier=1)
    assert r.passed is True, r


# ---------------------------------------------------------------------------
# Tier 2
# ---------------------------------------------------------------------------


def test_T9_clean_parse_clean_imports():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/foo.py",
            (
                '"""foo module."""\n'
                "import os\n"
                "import json\n"
                "VALUE = 42\n"
                "def f():\n"
                "    return os.getcwd()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True, r
    assert r.tier_run == 2
    assert r.integrity_issues == []
    assert r.corrective_dispatch == ""


def test_T10_syntax_error_caught():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/bad.py",
            (
                '"""bad module."""\n'
                "import os\n"
                "def f(:\n"  # syntax error
                "    return 1\n"
                "MORE = 2\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/bad.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is False
    assert r.tier_run == 2
    joined = " ".join(r.integrity_issues)
    assert "src/bad.py" in joined
    assert "SyntaxError" in joined
    # Line number must be present.
    assert any(":" in i and any(c.isdigit() for c in i) for i in r.integrity_issues)


def test_T11_NotImplementedError_in_test_file_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "tests/test_foo.py",
            (
                '"""tests for foo."""\n'
                "import os\n"
                "def test_x():\n"
                "    raise NotImplementedError\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["tests/test_foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True, r
    # No NotImplementedError flag for test files.
    assert all("NotImplementedError" not in i for i in r.integrity_issues)


def test_T12_NotImplementedError_in_non_test_file_fails():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/foo.py",
            (
                '"""foo module."""\n'
                "import os\n"
                "def f():\n"
                "    raise NotImplementedError\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is False
    assert any("NotImplementedError" in i for i in r.integrity_issues)
    assert any("src/foo.py" in i for i in r.integrity_issues)


def test_T13_unresolvable_import_fails():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/foo.py",
            (
                '"""foo."""\n'
                "import os\n"
                "from definitely_not_a_real_pkg_xyz_zzz import bar\n"
                "VALUE = 1\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        # No project_phases — nothing to defer to.
        r = verify_phase(phase, root, tier=2)
    assert r.passed is False
    assert any("unresolvable" in i for i in r.integrity_issues)
    assert any("definitely_not_a_real_pkg_xyz_zzz" in i for i in r.integrity_issues)


def test_T14_phase_awareness_saves_cross_phase_import():
    """Phase 1: src/a.py imports from src.b. Phase 2 declares src/b.py.
    Verifying phase 1 with project_phases passed → import deferred."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a."""\n'
                "import os\n"
                "from src.b import thing\n"
                "VALUE = 1\n"
            ),
        )
        # Note: src/b.py NOT written yet (it's phase 2's responsibility).
        phase1 = PhaseInput(id=1, paths=["src/a.py"])
        phase2 = PhaseInput(id=2, paths=["src/b.py"])
        r = verify_phase(
            phase1, root, tier=2, project_phases=[phase1, phase2]
        )
    assert r.passed is True, r
    assert r.integrity_issues == []


def test_T15_phase_awareness_does_not_save_truly_unknown():
    """Phase 1 imports src/c which is not declared by ANY phase → fails."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a."""\n'
                "import os\n"
                "from src.c import thing\n"
                "VALUE = 1\n"
            ),
        )
        phase1 = PhaseInput(id=1, paths=["src/a.py"])
        phase2 = PhaseInput(id=2, paths=["src/b.py"])  # b not c
        r = verify_phase(
            phase1, root, tier=2, project_phases=[phase1, phase2]
        )
    assert r.passed is False
    assert any("src.c" in i or "unresolvable" in i for i in r.integrity_issues)


def test_T16_re_export_pattern_passes_without_tracing_name():
    """from .b import x where src/a.py + src/b.py exist; we don't check
    whether x actually lives in b — that's tier 3."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/__init__.py",
            (
                '"""src top-level package init module."""\n'
                "VERSION = 1\n"
                'NAME = "src"\n'
                "ENABLED = True\n"
            ),
        )
        _write(
            root,
            "src/a.py",
            (
                '"""module a — re-export proxy."""\n'
                "import os\n"
                "from .b import some_symbol_we_dont_check\n"
                "VALUE = 1\n"
            ),
        )
        _write(
            root,
            "src/b.py",
            (
                '"""module b — provides symbols used by a."""\n'
                "import os\n"
                "OTHER_SYMBOL = 2\n"
                "ANOTHER = 3\n"
            ),
        )
        phase = PhaseInput(
            id=1,
            paths=["src/__init__.py", "src/a.py", "src/b.py"],
        )
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True, r
    assert r.integrity_issues == []


def test_T17_relative_import_within_same_phase():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/__init__.py",
            (
                '"""src top-level package init module."""\n'
                "N = 1\n"
                "M = 2\n"
                "K = 3\n"
            ),
        )
        _write(
            root,
            "src/foo/__init__.py",
            (
                '"""foo subpackage init module."""\n'
                "N = 1\n"
                "M = 2\n"
                "K = 3\n"
            ),
        )
        _write(
            root,
            "src/foo/bar.py",
            (
                '"""module bar — re-exports baz.quux."""\n'
                "import os\n"
                "from .baz import quux\n"
                "VALUE = 1\n"
            ),
        )
        _write(
            root,
            "src/foo/baz.py",
            (
                '"""module baz — provides quux."""\n'
                "import os\n"
                "quux = 1\n"
                "OTHER = 2\n"
            ),
        )
        phase = PhaseInput(
            id=1,
            paths=[
                "src/__init__.py",
                "src/foo/__init__.py",
                "src/foo/bar.py",
                "src/foo/baz.py",
            ],
        )
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True, r


def test_T18_stdlib_import_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/foo.py",
            (
                '"""foo."""\n'
                "import json\n"
                "import os\n"
                "import sys\n"
                "from pathlib import Path\n"
                "from collections.abc import Mapping\n"
                "VALUE = 1\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True, r


# ---------------------------------------------------------------------------
# Mixed / corrective_dispatch / API surface
# ---------------------------------------------------------------------------


def test_T19_tier3_no_longer_raises():
    """Tier 3 is implemented as of item 3. This test used to assert
    that tier=3 raised NotImplementedError; now we just confirm a
    VerifyResult comes back with tier_run==3."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_run == 3


def test_T19b_tier4_raises_NotImplementedError():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        try:
            verify_phase(phase, root, tier=4)
        except NotImplementedError as exc:
            assert "tier 4" in str(exc)
            assert "r7.12" in str(exc)
        else:
            raise AssertionError("expected NotImplementedError for tier=4")


def test_T20_corrective_dispatch_quality_on_tier1_failure():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(
            id=1,
            paths=["src/foo.py", "src/api/export.py", "src/export/csv.py"],
        )
        r = verify_phase(phase, root, tier=2)
    assert r.passed is False
    assert r.corrective_dispatch.startswith("Re-dispatch")
    assert "src/api/export.py" in r.corrective_dispatch
    assert "src/export/csv.py" in r.corrective_dispatch


def test_T20b_corrective_dispatch_quality_on_tier2_NotImpl():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/foo.py",
            (
                '"""foo."""\n'
                "import os\n"
                "def f():\n"
                "    raise NotImplementedError\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is False
    cd = r.corrective_dispatch
    assert cd.startswith("Re-dispatch")
    assert "src/foo.py" in cd
    assert "NotImplementedError" in cd or "real implementation" in cd


def test_T21_passed_True_has_empty_corrective_dispatch():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True
    assert r.corrective_dispatch == ""


def test_T22_persisted_to_is_None_in_module():
    """Module never sets persisted_to — the wrapper does."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
        # also tier-1 fail path
        phase2 = PhaseInput(id=1, paths=["does/not/exist.py"])
        r2 = verify_phase(phase2, root, tier=2)
    assert r.persisted_to is None
    assert r2.persisted_to is None


def test_T23_invalid_tier_raises_ValueError():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        try:
            verify_phase(phase, root, tier=7)
        except ValueError as exc:
            assert "7" in str(exc)
        else:
            raise AssertionError("expected ValueError for tier=7")


def test_T24_tier_enum_values():
    """Tier enum must declare 1=PRESENCE, 2=SYNTAX, 3=WIRING. Tier 3.5
    (RUNTIME_SMOKE) and tier 4 (SEMANTIC) are left for items 4 and r7.12
    respectively."""
    assert Tier.PRESENCE.value == 1
    assert Tier.SYNTAX.value == 2
    assert Tier.WIRING.value == 3
    names = {t.name for t in Tier}
    assert names == {"PRESENCE", "SYNTAX", "WIRING"}


def test_T25_phase_awareness_relative_import_cross_phase():
    """Phase 1: src/foo/a.py uses `from .b import x`; src/foo/b.py is
    phase 2's. Verifying phase 1 with project_phases → deferred."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/__init__.py",
            (
                '"""src top-level package init module."""\n'
                "N = 1\n"
                "M = 2\n"
                "K = 3\n"
            ),
        )
        _write(
            root,
            "src/foo/__init__.py",
            (
                '"""foo subpackage init module."""\n'
                "N = 1\n"
                "M = 2\n"
                "K = 3\n"
            ),
        )
        _write(
            root,
            "src/foo/a.py",
            (
                '"""module a — pulls x from sibling b."""\n'
                "import os\n"
                "from .b import x\n"
                "VALUE = 1\n"
            ),
        )
        # Note: src/foo/b.py NOT written.
        phase1 = PhaseInput(
            id=1,
            paths=["src/__init__.py", "src/foo/__init__.py", "src/foo/a.py"],
        )
        phase2 = PhaseInput(id=2, paths=["src/foo/b.py"])
        r = verify_phase(
            phase1, root, tier=2, project_phases=[phase1, phase2]
        )
    assert r.passed is True, r


# ===========================================================================
# Tier 3 (WIRING) — item 3 tests
# ===========================================================================
#
# Naming convention:
#   B*    backward-compat assertions (tier_3_hint defaults, enum, etc.)
#   C1.*  CAT1 — defined-but-never-referenced
#   C2.*  CAT2 — imported-but-never-used
#   C3.*  CAT3 — test references nonexistent symbols
#   C4.*  CAT4 — duplicate definitions
#   P*    phase-awareness reuse
#   D*    dynamic-dispatch detection (tier_3_hint)
#   CD*   corrective_dispatch quality
# ---------------------------------------------------------------------------


# Backward-compat ------------------------------------------------------------


def test_B1_tier2_invocation_still_no_hint_field_set():
    """Backward compat: tier=2 invocations leave tier_3_hint=None."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        r = verify_phase(phase, root, tier=2)
    assert r.passed is True
    assert r.tier_run == 2
    assert r.tier_3_hint is None


def test_B2_tier_WIRING_enum_value():
    assert Tier.WIRING.value == 3


def test_B3_tier4_still_raises():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/foo.py", SUBSTANTIVE_BODY)
        phase = PhaseInput(id=1, paths=["src/foo.py"])
        try:
            verify_phase(phase, root, tier=4)
        except NotImplementedError as exc:
            assert "tier 4" in str(exc)
        else:
            raise AssertionError("expected NotImplementedError for tier=4")


# CAT1 — defined-but-never-referenced ----------------------------------------


def test_C1_1_defined_referenced_in_other_phase_file_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""module a — defines helper used by b."""\n'
                "VAL = 1\n"
                "OTHER = 2\n"
                "def helper():\n"
                "    return VAL + OTHER\n"
            ),
        )
        _write(
            root,
            "src/b.py",
            (
                '"""module b — uses helper from a, exposes main."""\n'
                "from src.a import helper\n"
                "OUT = 0\n"
                "def main():\n"
                "    return helper()\n"
                'if __name__ == "__main__":\n'
                "    OUT = main()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py", "src/b.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_run == 3
    cat1 = [i for i in r.integrity_issues if "[CAT1" in i]
    # `helper` is referenced in src/b.py — must NOT be flagged.
    assert not any("`helper`" in i for i in cat1), r.integrity_issues


def test_C1_2_truly_unreferenced_function_flagged():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a."""\n'
                "VAL = 1\n"
                "def orphan():\n"
                "    return VAL\n"
                "def main():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py"])
        r = verify_phase(phase, root, tier=3)
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    assert any("`orphan`" in i for i in cat1)
    assert r.passed is False


def test_C1_3_class_used_vs_unused():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/used.py",
            (
                '"""defines and instantiates Foo."""\n'
                "class Foo:\n"
                "    def __init__(self):\n"
                "        self.x = 1\n"
                "INSTANCE = Foo()\n"
            ),
        )
        _write(
            root,
            "src/unused.py",
            (
                '"""defines OrphanClass that nobody uses."""\n'
                "class OrphanClass:\n"
                "    def __init__(self):\n"
                "        self.x = 1\n"
                "VAL = 1\n"
                "def keepalive():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/used.py", "src/unused.py"])
        r = verify_phase(phase, root, tier=3)
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    assert not any("`Foo`" in i for i in cat1)
    assert any("`OrphanClass`" in i for i in cat1)


def test_C1_4_router_allowlist_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/api/routes.py",
            (
                '"""API routes — `router` is consumed by FastAPI by name."""\n'
                "router = object()  # FastAPI APIRouter() in real code\n"
                "VAL = 1\n"
                "def helper():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/routes.py"])
        r = verify_phase(phase, root, tier=3)
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    # `router` is allow-listed; `helper` is unreferenced — flagged.
    assert not any("`router`" in i for i in cat1)


def test_C1_5_all_export_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/lib.py",
            (
                '"""lib — public_thing exported via __all__."""\n'
                '__all__ = ["public_thing"]\n'
                "def public_thing():\n"
                "    return 1\n"
                "PRIVATE = 2\n"
                "def _used():\n"
                "    return PRIVATE\n"
                "_REF = _used()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/lib.py"])
        r = verify_phase(phase, root, tier=3)
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    assert not any("`public_thing`" in i for i in cat1)


# CAT2 — imported-but-never-used ---------------------------------------------


def test_C2_1_used_import_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a — uses os."""\n'
                "import os\n"
                "VAL = 1\n"
                "def cwd():\n"
                "    return os.getcwd()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py"])
        r = verify_phase(phase, root, tier=3)
    cat2 = [i for i in r.integrity_issues if "[CAT2:imported-unused]" in i]
    assert cat2 == []


def test_C2_2_unused_import_flagged():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a — imports json but never uses it."""\n'
                "import os\n"
                "import json\n"
                "VAL = 1\n"
                "def cwd():\n"
                "    return os.getcwd()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py"])
        r = verify_phase(phase, root, tier=3)
    cat2 = [i for i in r.integrity_issues if "[CAT2:imported-unused]" in i]
    assert any("json" in i for i in cat2)
    assert not any("`os`" in i for i in cat2)


def test_C2_3_typecheck_only_import_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a — TYPE_CHECKING-gated import (not a runtime use)."""\n'
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from collections.abc import Mapping\n"
                "VAL = 1\n"
                "def f():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py"])
        r = verify_phase(phase, root, tier=3)
    cat2 = [i for i in r.integrity_issues if "[CAT2:imported-unused]" in i]
    assert not any("Mapping" in i for i in cat2)


def test_C2_4_all_reexport_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/_other.py",
            (
                '"""provides Helper."""\n'
                "class Helper:\n"
                "    def x(self):\n"
                "        return 1\n"
                "VAL = 1\n"
            ),
        )
        _write(
            root,
            "src/__init__.py",
            (
                '"""src package — re-exports Helper."""\n'
                "from src._other import Helper\n"
                '__all__ = ["Helper"]\n'
            ),
        )
        phase = PhaseInput(
            id=1, paths=["src/__init__.py", "src/_other.py"]
        )
        r = verify_phase(phase, root, tier=3)
    cat2 = [i for i in r.integrity_issues if "[CAT2:imported-unused]" in i]
    assert not any("Helper" in i for i in cat2)


# CAT3 — tests reference nonexistent symbols ---------------------------------


def test_C3_1_test_imports_existing_symbol_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a — defines do_thing."""\n'
                "VAL = 1\n"
                "def do_thing():\n"
                "    return VAL\n"
            ),
        )
        _write(
            root,
            "tests/test_a.py",
            (
                '"""tests for a."""\n'
                "from src.a import do_thing\n"
                "def test_x():\n"
                "    assert do_thing() == 1\n"
            ),
        )
        phase = PhaseInput(
            id=1, paths=["src/a.py", "tests/test_a.py"]
        )
        r = verify_phase(phase, root, tier=3)
    cat3 = [
        i for i in r.integrity_issues
        if "[CAT3:test-references-nonexistent]" in i
    ]
    assert cat3 == []


def test_C3_2_test_imports_nonexistent_symbol_flagged():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a — defines do_thing only."""\n'
                "VAL = 1\n"
                "def do_thing():\n"
                "    return VAL\n"
            ),
        )
        _write(
            root,
            "tests/test_a.py",
            (
                '"""tests for a — references missing do_other."""\n'
                "from src.a import do_thing, do_other\n"
                "def test_x():\n"
                "    assert do_thing() == 1\n"
                "def test_y():\n"
                "    assert do_other() == 1\n"
            ),
        )
        phase = PhaseInput(
            id=1, paths=["src/a.py", "tests/test_a.py"]
        )
        r = verify_phase(phase, root, tier=3)
    cat3 = [
        i for i in r.integrity_issues
        if "[CAT3:test-references-nonexistent]" in i
    ]
    assert any("do_other" in i for i in cat3), r.integrity_issues
    assert not any("do_thing" in i and "[CAT3" in i
                   for i in r.integrity_issues)


def test_C3_3_test_imports_cross_phase_not_on_disk_no_flag():
    """Phase 1 has the test; phase 2 (tolerated) declares the impl
    but the file isn't yet on disk. CAT3 must not flag — that's
    deferred."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "tests/test_pending.py",
            (
                '"""tests for pending impl (phase 2)."""\n'
                "from src.pending import some_symbol\n"
                "def test_x():\n"
                "    assert some_symbol() == 1\n"
            ),
        )
        # src/pending.py NOT written.
        phase1 = PhaseInput(id=1, paths=["tests/test_pending.py"])
        phase2 = PhaseInput(id=2, paths=["src/pending.py"])
        r = verify_phase(
            phase1, root, tier=3, project_phases=[phase1, phase2]
        )
    cat3 = [
        i for i in r.integrity_issues
        if "[CAT3:test-references-nonexistent]" in i
    ]
    assert cat3 == []


def test_C3_4_test_imports_stdlib_no_flag():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "tests/test_x.py",
            (
                '"""tests with stdlib imports."""\n'
                "from collections import OrderedDict\n"
                "def test_x():\n"
                "    assert OrderedDict() == OrderedDict()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["tests/test_x.py"])
        r = verify_phase(phase, root, tier=3)
    cat3 = [
        i for i in r.integrity_issues
        if "[CAT3:test-references-nonexistent]" in i
    ]
    assert cat3 == []


# CAT4 — duplicate definitions -----------------------------------------------


def test_C4_1_unique_definition_passes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a."""\n'
                "VAL = 1\n"
                "def helper():\n"
                "    return VAL\n"
            ),
        )
        _write(
            root,
            "src/b.py",
            (
                '"""b — uses helper."""\n'
                "from src.a import helper\n"
                "def main():\n"
                "    return helper()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py", "src/b.py"])
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    assert cat4 == []


def test_C4_2_duplicate_in_two_phaseN_files_flagged():
    """The n=10 r4 pattern, scaled down: PDFSerializer defined in
    pdf.py AND in formats_init.py. Tier-3 must surface this as a
    CAT4 violation."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/export/pdf.py",
            (
                '"""real PDF serializer."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, data):\n"
                "        return b\"%PDF-real\"\n"
                "VAL = 1\n"
            ),
        )
        _write(
            root,
            "src/export/formats_init.py",
            (
                '"""fake registration that shadows PDFSerializer."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, data):\n"
                "        return b\"%PDF-FAKE\"\n"
                "REG = PDFSerializer()\n"
            ),
        )
        phase = PhaseInput(
            id=1,
            paths=[
                "src/export/pdf.py",
                "src/export/formats_init.py",
            ],
        )
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    assert any("PDFSerializer" in i for i in cat4), r.integrity_issues
    assert r.passed is False


def test_C4_3_duplicate_across_phaseN_and_tolerated_phaseM_on_disk():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""phase-1 PDFSerializer."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, d):\n"
                "        return b\"a\"\n"
                "VAL = 1\n"
            ),
        )
        _write(
            root,
            "src/b.py",
            (
                '"""phase-2 PDFSerializer (already written)."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, d):\n"
                "        return b\"b\"\n"
                "VAL = 1\n"
            ),
        )
        phase1 = PhaseInput(id=1, paths=["src/a.py"])
        phase2 = PhaseInput(id=2, paths=["src/b.py"])
        r = verify_phase(
            phase1, root, tier=3, project_phases=[phase1, phase2]
        )
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    assert any("PDFSerializer" in i for i in cat4)


def test_C4_4_test_fixture_duplicates_allowed():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "tests/test_a.py",
            (
                '"""tests for a — defines local fixture."""\n'
                "def make_record():\n"
                "    return {\"id\": 1}\n"
                "def test_x():\n"
                "    assert make_record()[\"id\"] == 1\n"
            ),
        )
        _write(
            root,
            "tests/test_b.py",
            (
                '"""tests for b — defines its own fixture w/ same name."""\n'
                "def make_record():\n"
                "    return {\"id\": 2}\n"
                "def test_y():\n"
                "    assert make_record()[\"id\"] == 2\n"
            ),
        )
        phase = PhaseInput(
            id=1, paths=["tests/test_a.py", "tests/test_b.py"]
        )
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    assert not any("make_record" in i for i in cat4)


# CAT4 — orphan-collision detection (r7.11 F-9 mitigation, part B) -----------
#
# The motivating archetype: r7.11 item-8 trial-3 created
# `src/api/export_routes.py` (declared in phase 3) but did NOT modify
# the baseline stub `src/api/export.py`. Both files defined the same
# `router`, `MOCK_RECORDS`, and 3 endpoint functions. content_verify
# caught it (6 duplicate-symbol findings); tier-3 CAT4 did NOT, because
# CAT4 only inspected PLAN.md-declared paths. These tests cover the
# extension that walks `<scaffold_root>/{src,tests}` for orphan .py
# files and feeds them into CAT4's collision check.


def test_C4_5_orphan_with_colliding_symbol_fires():
    """An orphan baseline stub (`src/api/export.py`) defines `router`;
    phase 1 declares `src/api/main.py` also defining `router`. Tier 3
    must surface the orphan-collision finding mentioning both paths
    AND tagging the orphan with the 'orphan baseline stub' substring."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Orphan: not in any PLAN.md phase.
        _write(
            root,
            "src/api/export.py",
            (
                '"""baseline export stub — orphan."""\n'
                "router = object()\n"
                "MOCK_RECORDS = []\n"
            ),
        )
        # Own: phase 1 — defines `router` (collides) but NOT MOCK_RECORDS.
        _write(
            root,
            "src/api/main.py",
            (
                '"""phase-1 main router."""\n'
                "router = object()\n"
                "def make_app():\n"
                "    return router\n"
                "__all__ = ['router', 'make_app']\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/main.py"])
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    router_findings = [i for i in cat4 if "`router`" in i]
    assert router_findings, r.integrity_issues
    msg = router_findings[0]
    # Both files cited
    assert "src/api/main.py" in msg
    assert "src/api/export.py" in msg
    # Orphan tagged with the load-bearing substring
    assert "orphan baseline stub" in msg, msg
    # Remediation hint present
    assert "delete or empty the orphan" in msg or "modify the orphan" in msg
    # And the verification fails (orphan collision is a real wiring bug)
    assert r.passed is False


def test_C4_6_no_orphans_no_orphan_findings():
    """Scaffold has only PLAN.md-declared files — no orphan walk hits.
    CAT4 fires exactly as before (test C4_2's intra-phase duplicate
    must still flag, with NO 'orphan baseline stub' tag in the message
    since no orphan participated). Backward-compat check."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/export/pdf.py",
            (
                '"""real PDF serializer."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, data):\n"
                "        return b\"%PDF-real\"\n"
                "VAL = 1\n"
            ),
        )
        _write(
            root,
            "src/export/formats_init.py",
            (
                '"""fake registration that shadows PDFSerializer."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, data):\n"
                "        return b\"%PDF-FAKE\"\n"
                "REG = PDFSerializer()\n"
            ),
        )
        phase = PhaseInput(
            id=1,
            paths=["src/export/pdf.py", "src/export/formats_init.py"],
        )
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    pdf = [i for i in cat4 if "PDFSerializer" in i]
    assert pdf, r.integrity_issues
    # No orphan participated → no orphan tag in the message
    assert "orphan baseline stub" not in pdf[0], pdf[0]
    # And the original "runtime-shadowing risk" wording is preserved
    assert "runtime-shadowing risk" in pdf[0]


def test_C4_7_orphan_with_noncolliding_symbols_no_finding():
    """Orphan defines its own symbols that don't appear in phase-N.
    No collision → no flag. Confirms the additive nature of orphan
    discovery: presence of an orphan alone never fires."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/api/legacy.py",
            (
                '"""legacy helper — orphan, not declared anywhere."""\n'
                "def legacy_helper():\n"
                "    return 42\n"
                "LEGACY_CONST = 99\n"
            ),
        )
        _write(
            root,
            "src/api/main.py",
            (
                '"""phase-1 main."""\n'
                "def make_app():\n"
                "    return object()\n"
                "ROUTER = object()\n"
                "__all__ = ['make_app', 'ROUTER']\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/main.py"])
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    assert cat4 == [], cat4


def test_C4_8_test_only_orphan_collision_exempted():
    """Orphan in `tests/test_helpers.py` defines `make_record`; phase-N
    test in `tests/test_x.py` also defines `make_record`. All
    collision locations are test files → CAT4 test-fixture exception
    applies even when one participant is an orphan."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Orphan test file, not declared in any phase
        _write(
            root,
            "tests/test_helpers.py",
            (
                '"""orphan test helpers."""\n'
                "def make_record():\n"
                "    return {\"id\": 0}\n"
            ),
        )
        # Phase-N test file
        _write(
            root,
            "tests/test_x.py",
            (
                '"""phase-1 test — defines its own make_record."""\n'
                "def make_record():\n"
                "    return {\"id\": 1}\n"
                "def test_x():\n"
                "    assert make_record()[\"id\"] == 1\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["tests/test_x.py"])
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    assert not any("make_record" in i for i in cat4), cat4


def test_C4_9_multiple_orphans_only_colliding_pair_in_finding():
    """Three orphan files; only one shares a top-level symbol with
    phase-N. The CAT4 finding for that symbol must mention only the
    colliding orphan + the phase-N file, not the bystander orphans."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Colliding orphan — defines `router`
        _write(
            root,
            "src/api/export.py",
            (
                '"""colliding orphan."""\n'
                "router = object()\n"
            ),
        )
        # Bystander orphan A — defines unrelated symbols
        _write(
            root,
            "src/api/legacy.py",
            (
                '"""bystander A."""\n'
                "def legacy_a():\n"
                "    return 1\n"
            ),
        )
        # Bystander orphan B — defines unrelated symbols
        _write(
            root,
            "src/util/misc.py",
            (
                '"""bystander B."""\n'
                "def misc_b():\n"
                "    return 2\n"
                "MISC_CONST = 3\n"
            ),
        )
        # Phase-N file — collides with `router` only
        _write(
            root,
            "src/api/main.py",
            (
                '"""phase-1 main."""\n'
                "router = object()\n"
                "def make_app():\n"
                "    return router\n"
                "__all__ = ['router', 'make_app']\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/main.py"])
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    router_findings = [i for i in cat4 if "`router`" in i]
    assert len(router_findings) == 1, cat4
    msg = router_findings[0]
    # Colliding pair present
    assert "src/api/main.py" in msg
    assert "src/api/export.py" in msg
    # Bystander orphans NOT in this finding
    assert "src/api/legacy.py" not in msg, msg
    assert "src/util/misc.py" not in msg, msg
    # Bystander symbols never produce a CAT4 finding (no collision)
    assert not any("legacy_a" in i for i in cat4)
    assert not any("misc_b" in i for i in cat4)


def test_C4_10_orphan_under_excluded_subtree_ignored():
    """An orphan-shaped .py file under `.venv/` or `__pycache__/` must
    NOT be picked up by the orphan walker (would otherwise pull in
    third-party packages with arbitrary symbol collisions)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # A venv-vendored file that defines `router` — must be ignored
        _write(
            root,
            "src/.venv/lib/python3.x/site-packages/fastapi/routing.py",
            (
                '"""vendored fastapi — must be ignored."""\n'
                "router = object()\n"
            ),
        )
        # Bytecode cache shadow — must also be ignored
        _write(
            root,
            "src/__pycache__/cached.py",
            (
                '"""pyc-shadow — must be ignored."""\n'
                "router = object()\n"
            ),
        )
        # Phase-N file defining router (would collide if walker is sloppy)
        _write(
            root,
            "src/api/main.py",
            (
                '"""phase-1 main."""\n'
                "router = object()\n"
                "def make_app():\n"
                "    return router\n"
                "__all__ = ['router', 'make_app']\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/main.py"])
        r = verify_phase(phase, root, tier=3)
    cat4 = [i for i in r.integrity_issues if "[CAT4:duplicate-definition]" in i]
    # No collision should be reported — the .venv and __pycache__
    # entries don't count as orphans.
    assert not any("`router`" in i for i in cat4), cat4


# C4_11 through C4_15: heterogeneous-path coverage. Worker-2's original
# orphan-detection tests (C4_5 through C4_10) used homogeneous relative
# paths in declared_paths — matching the walker's relative-string output
# — so the absolute-vs-relative mismatch in real PLAN.md files (which
# typically use absolute paths) wasn't exercised. Trial 4 (2026-04-29)
# escalated when this bug surfaced: a parent declared
# `/tmp/r7.11-item8-scaffold/src/export/serializers.py` (absolute), the
# walker yielded `src/export/serializers.py` (relative), string equality
# failed, the file was misclassified as an orphan, and CAT4 then fired
# a self-collision the parent could not fix (the "duplicate" IS the
# declared file). These tests cover the heterogeneous-path matrix so
# the bug class doesn't regress.


def test_C4_11_absolute_declared_path_matches_relative_walker_yield():
    """THE TRIAL-4 CASE. PLAN.md declares an absolute path; walker
    yields the same file as a relative path. Normalization via
    Path.resolve() on both sides must canonicalize them to the same
    Path so the file is NOT misclassified as an orphan."""
    import verify_phase as vp_mod
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        serializers = _write(
            root,
            "src/export/serializers.py",
            (
                '"""phase-1 serializer."""\n'
                "def csv_serialize(records):\n"
                "    return \"\".join(str(r) for r in records)\n"
            ),
        )
        # declared_paths uses absolute path — exactly what real PLAN.md
        # files produce when the parent expands paths against scaffold_root.
        declared = {str(serializers.resolve())}
        orphans = vp_mod._discover_orphan_files(root, declared)
    # The declared file must NOT appear as an orphan.
    assert orphans == [], (
        f"declared file misclassified as orphan: "
        f"{[o.path_rel for o in orphans]}"
    )


def test_C4_12_relative_declared_path_matches_absolute_walker_resolution():
    """Symmetric inverse of C4_11. PLAN.md declares a relative path
    (older-style PLAN.md authoring); the walker resolves to the same
    canonical absolute path. No orphan-collision should fire."""
    import verify_phase as vp_mod
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/export/serializers.py",
            (
                '"""phase-1 serializer."""\n'
                "def csv_serialize(records):\n"
                "    return \"\".join(str(r) for r in records)\n"
            ),
        )
        # declared_paths is relative — the older PLAN.md style.
        declared = {"src/export/serializers.py"}
        orphans = vp_mod._discover_orphan_files(root, declared)
    assert orphans == [], (
        f"declared file misclassified as orphan: "
        f"{[o.path_rel for o in orphans]}"
    )


def test_C4_13_mixed_absolute_and_relative_declared_paths():
    """A single PLAN.md may declare some paths absolute and others
    relative (different phases authored at different times, or by
    different parents). Both flavors must normalize correctly so
    neither file is flagged as an orphan."""
    import verify_phase as vp_mod
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        foo = _write(
            root,
            "src/foo.py",
            (
                '"""phase-1 foo."""\n'
                "def helper():\n"
                "    return 1\n"
            ),
        )
        _write(
            root,
            "src/bar.py",
            (
                '"""phase-2 bar."""\n'
                "def helper2():\n"
                "    return 2\n"
            ),
        )
        # phase-1 absolute, phase-2 relative — heterogeneous union.
        declared = {str(foo.resolve()), "src/bar.py"}
        orphans = vp_mod._discover_orphan_files(root, declared)
    assert orphans == [], (
        f"heterogeneous declared paths produced false orphans: "
        f"{[o.path_rel for o in orphans]}"
    )


def test_C4_14_symlink_in_scaffold_resolves_to_declared_target():
    """Defensive: if the scaffold contains a symlink that points at a
    declared file, normalization via Path.resolve() must follow the
    link so both the link and the real file canonicalize to the same
    Path. The declared real file must not be classified as an orphan,
    and the symlink alias must not produce a spurious orphan-collision
    of the declared file's symbols against itself.

    Platform-dependence note: rglob's symlink-following behavior varies
    across Python versions. The load-bearing assertion is that the
    DECLARED file is not flagged as an orphan; whether the symlink
    alias is enumerated at all is secondary.
    """
    import os
    import verify_phase as vp_mod
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        real = _write(
            root,
            "src/real.py",
            (
                '"""phase-1 real."""\n'
                "def f():\n"
                "    return 1\n"
            ),
        )
        link = root / "src" / "link.py"
        try:
            os.symlink(real, link)
        except (OSError, NotImplementedError):
            # Platform without symlink support (rare on the dev macOS
            # target, but honor the spec's tolerance).
            return
        declared = {"src/real.py"}
        orphans = vp_mod._discover_orphan_files(root, declared)
    # The declared real file must not appear in the orphan list. If
    # rglob enumerates the symlink alias, its resolve() lands on the
    # same canonical path as `real` and is therefore also excluded.
    orphan_paths = [o.path_rel for o in orphans]
    assert "src/real.py" not in orphan_paths, (
        f"declared symlink target flagged as orphan: {orphan_paths}"
    )
    # And — critically for the trial-4 bug class — neither path should
    # produce a same-file collision pair.
    assert "src/link.py" not in orphan_paths or len(orphan_paths) <= 1, (
        f"symlink alias enumerated as separate orphan: {orphan_paths}"
    )


def test_C4_15_absolute_declared_path_outside_scaffold_no_crash():
    """Negative case: PLAN.md declares an absolute path outside
    `scaffold_root` (a stale path from a different scaffold, or a
    typo). Normalization must not crash; the walker simply finds no
    candidate matching the out-of-scaffold path. A scaffold-internal
    file that does NOT match anything declared remains a true orphan."""
    import verify_phase as vp_mod
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/foo.py",
            (
                '"""scaffold-internal — not declared anywhere."""\n'
                "def bar():\n"
                "    return 1\n"
            ),
        )
        # Declared path points outside scaffold_root entirely. Must
        # resolve without crashing; the walker won't visit it.
        declared = {"/some/other/place/external.py"}
        orphans = vp_mod._discover_orphan_files(root, declared)
    # src/foo.py is a true orphan (not declared anywhere under
    # scaffold_root) — the walker should still report it.
    orphan_paths = [o.path_rel for o in orphans]
    assert "src/foo.py" in orphan_paths, (
        f"true orphan missed when declared paths reference outside "
        f"scaffold_root: {orphan_paths}"
    )


# Phase-awareness reuse ------------------------------------------------------


def test_P1_phaseN_defines_phaseM_on_disk_references_passes():
    """Phase 1 defines `helper`; phase 2 (tolerated) is on disk and
    references `helper` — so CAT1 must NOT flag helper as unused."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/p1.py",
            (
                '"""phase-1 file."""\n'
                "VAL = 1\n"
                "def helper():\n"
                "    return VAL\n"
            ),
        )
        _write(
            root,
            "src/p2.py",
            (
                '"""phase-2 file (already on disk)."""\n'
                "from src.p1 import helper\n"
                "def main():\n"
                "    return helper()\n"
            ),
        )
        phase1 = PhaseInput(id=1, paths=["src/p1.py"])
        phase2 = PhaseInput(id=2, paths=["src/p2.py"])
        r = verify_phase(
            phase1, root, tier=3, project_phases=[phase1, phase2]
        )
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    assert not any("`helper`" in i for i in cat1)


def test_P2_phaseN_defines_phaseM_not_on_disk_conservative_pass():
    """Phase 2 not yet on disk — phase 1's helper must NOT be flagged
    as unused because the consumer hasn't been written yet."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/p1.py",
            (
                '"""phase-1 file."""\n'
                "VAL = 1\n"
                "def helper():\n"
                "    return VAL\n"
            ),
        )
        # src/p2.py NOT written yet.
        phase1 = PhaseInput(id=1, paths=["src/p1.py"])
        phase2 = PhaseInput(id=2, paths=["src/p2.py"])
        r = verify_phase(
            phase1, root, tier=3, project_phases=[phase1, phase2]
        )
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    # Conservative-by-default: don't flag.
    # NOTE: documented in TIER3-NOTES.md — current implementation flags
    # helper because we can't peek into a not-on-disk file. The test
    # below asserts the conservative variant: when ANY tolerated-phase
    # path is missing, we suppress CAT1 for phase-N's defined names.
    assert not any("`helper`" in i for i in cat1), (
        "Conservative rule: when a tolerated phase has files not yet "
        "on disk, CAT1 must not flag phase-N definitions; the consumer "
        "may reference them once written."
    )


def test_P3_tier2_deferral_no_redundant_tier3_issue():
    """Phase 1 imports a symbol from phase-2-not-yet-on-disk. Tier 2
    treats this as deferred (no integrity issue). Tier 3 must NOT then
    add a redundant CAT2 (or other) violation for the same import."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/p1.py",
            (
                '"""phase-1 importer of phase-2 helper."""\n'
                "from src.p2 import helper\n"
                "def main():\n"
                "    return helper()\n"
            ),
        )
        # src/p2.py NOT on disk.
        phase1 = PhaseInput(id=1, paths=["src/p1.py"])
        phase2 = PhaseInput(id=2, paths=["src/p2.py"])
        r = verify_phase(
            phase1, root, tier=3, project_phases=[phase1, phase2]
        )
    # `helper` IS used (called inside main), so CAT2 wouldn't flag it
    # anyway. But assert it explicitly.
    cat2 = [i for i in r.integrity_issues if "[CAT2:imported-unused]" in i]
    assert not any("helper" in i for i in cat2)
    # And no unresolvable-import noise from tier 2 either.
    assert not any("unresolvable" in i for i in r.integrity_issues)


# Dynamic-dispatch markers ---------------------------------------------------


def test_D1_no_dynamic_dispatch_no_hint():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/a.py",
            (
                '"""a — vanilla module."""\n'
                "import os\n"
                "VAL = 1\n"
                "def f():\n"
                "    return os.getcwd()\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/a.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_3_hint is None


def test_D2_importlib_import_module_sets_hint():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/loader.py",
            (
                '"""dynamic loader."""\n'
                "import importlib\n"
                "MODULE_NAME = \"src.formats_init\"\n"
                "def load():\n"
                "    return importlib.import_module(MODULE_NAME)\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/loader.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_3_hint is not None
    assert "tier 3.5" in r.tier_3_hint


def test_D3_dunder_import_sets_hint():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/loader.py",
            (
                '"""dunder-import loader."""\n'
                "VAL = 1\n"
                "def load():\n"
                "    return __import__(\"json\")\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/loader.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_3_hint is not None


def test_D4_getattr_on_imported_module_sets_hint():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/loader.py",
            (
                '"""dynamic-attr lookup."""\n'
                "import os\n"
                "def get_cwd_attr():\n"
                "    return getattr(os, \"getcwd\")\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/loader.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_3_hint is not None


# corrective_dispatch quality ------------------------------------------------


def test_CD1_cat4_dispatch_cites_files_and_symbol():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/export/pdf.py",
            (
                '"""real PDF serializer."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, d):\n"
                "        return b\"real\"\n"
                "VAL = 1\n"
            ),
        )
        _write(
            root,
            "src/export/formats_init.py",
            (
                '"""fake."""\n'
                "class PDFSerializer:\n"
                "    def serialize(self, d):\n"
                "        return b\"fake\"\n"
                "REG = PDFSerializer()\n"
            ),
        )
        phase = PhaseInput(
            id=1,
            paths=[
                "src/export/pdf.py",
                "src/export/formats_init.py",
            ],
        )
        r = verify_phase(phase, root, tier=3)
    cd = r.corrective_dispatch
    assert cd.startswith("Re-dispatch")
    assert "PDFSerializer" in cd
    assert "src/export/pdf.py" in cd
    assert "src/export/formats_init.py" in cd
    assert "CAT4:duplicate-definition" in cd


def test_CD2_mixed_cat1_and_cat2_dispatch_names_both():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/m.py",
            (
                '"""m — has unused import AND unused def."""\n'
                "import json\n"
                "VAL = 1\n"
                "def orphan():\n"
                "    return VAL\n"
                "def main():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(phase, root, tier=3)
    cd = r.corrective_dispatch
    assert "CAT1:defined-unused" in cd
    assert "CAT2:imported-unused" in cd
    assert "orphan" in cd
    assert "json" in cd


# ---------------------------------------------------------------------------
# Tier 3.5 — runtime smoke test (item 4)
# ---------------------------------------------------------------------------
#
# These tests exercise the opt-in subprocess-based verifier. Each test
# builds a scaffold and invokes verify_phase with
# `with_runtime_smoke_test=True`. The probe subprocess imports the
# declared modules and inspects registry-shaped objects.


# A clean substantive Python body that loads cleanly and contains no
# registry — used wherever tier 3.5 should run but find nothing. Built
# so all top-level definitions reference each other (no CAT1 unused).
_PLAIN_BODY = (
    '"""plain module."""\n'
    "VALUE = 42\n"
    "def f():\n"
    "    return VALUE\n"
    "def g():\n"
    "    return f()\n"
    "ENTRY = g()\n"
)


# A package __init__ that's big enough (>=50 bytes, >=3 nonblank lines)
# AND references all top-level names so tier 3 CAT1 doesn't flag them.
_PKG_INIT = (
    '"""pkg init."""\n'
    "_A = 1\n"
    "_B = 2\n"
    "_C = _A + _B\n"
    "PKG_TOTAL = _C\n"
)


# ---- Opt-in semantics (3 tests) ----


def test_S1_default_does_not_invoke_tier35():
    """with_runtime_smoke_test defaults to False; runtime_smoke_findings
    stays empty regardless of phase content. We verify by spying on
    the verify_phase module's subprocess reference."""
    import verify_phase as vp_mod
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", _PLAIN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        original_run = vp_mod.subprocess.run
        calls = []

        def _spy(*args, **kwargs):
            calls.append((args, kwargs))
            return original_run(*args, **kwargs)

        vp_mod.subprocess.run = _spy
        try:
            # tier=2 stays out of CAT1 territory — we're verifying the
            # opt-in gate, not tier-3 wiring strictness.
            r = verify_phase(phase, root, tier=2)
        finally:
            vp_mod.subprocess.run = original_run
    assert r.passed is True, r
    assert r.runtime_smoke_findings == []
    assert calls == [], "subprocess.run should not be called when opt-in is False"


def test_S2_tier1_failure_skips_tier35():
    """When tier 1 fails (missing path), tier 3.5 emits [SKIPPED] and
    `passed` is False from tier 1."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Don't create src/m.py. Phase declares it.
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(phase, root, tier=3, with_runtime_smoke_test=True)
    assert r.passed is False
    assert r.tier_run == 1
    assert r.runtime_smoke_findings, r.runtime_smoke_findings
    assert any(f.startswith("[SKIPPED]") for f in r.runtime_smoke_findings)


def test_S3_tier12_pass_no_dynamic_runs_tier35_with_checked():
    """Tier 1+2 pass, no dynamic content, tier 3.5 runs and produces
    [CHECKED] entries; passed=True."""
    body = (
        '"""m with registry."""\n'
        "class A:\n"
        "    pass\n"
        "REGISTRY = {'a': A}\n"
        "def use_it():\n"
        "    return REGISTRY['a']()\n"
    )
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/m.py", body)
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/m.py"])
        r = verify_phase(phase, root, tier=2, with_runtime_smoke_test=True)
    assert r.passed is True, r
    assert r.runtime_smoke_findings, "tier 3.5 should have produced findings"
    assert any(f.startswith("[CHECKED:") for f in r.runtime_smoke_findings)
    assert not any(f.startswith("[SHADOWING:") for f in r.runtime_smoke_findings)


# ---- n=10-r4 reproduction (the load-bearing test) — 2 tests ----


def _build_n10r4_scaffold(root: Path) -> None:
    """Build the n=10-r4 archetype: a real PDFSerializer in
    src/export/pdf.py, a fake PDFSerializer in src/export/formats_init.py
    that auto-registers via importlib at module-load time, and a
    registry in src/export/formats.py.

    This is the load-bearing failure pattern tier 3.5 exists to catch.
    """
    _write(root, "src/__init__.py", _PKG_INIT)
    _write(root, "src/export/__init__.py",
        '"""export pkg."""\n'
        'NAMES = []\n'
        'def list_names():\n'
        '    return NAMES\n'
        'TAG = list_names()\n'
    )
    # The real PDFSerializer (correct, what PLAN.md "intends").
    _write(root, "src/export/pdf.py",
        '"""real PDF serializer."""\n'
        'class PDFSerializer:\n'
        '    name = "real-pdf"\n'
        '    def serialize(self, data):\n'
        '        return b"REAL_PDF_BYTES"\n'
        'def get_real():\n'
        '    return PDFSerializer()\n'
    )
    # The fake — registered at runtime via importlib auto-load.
    _write(root, "src/export/formats_init.py",
        '"""fake auto-init that shadows pdf.PDFSerializer."""\n'
        'from src.export import formats as _f\n'
        'class PDFSerializer:\n'
        '    name = "fake-pdf"\n'
        '    def serialize(self, data):\n'
        '        return b"FAKE_PDF"\n'
        '_f._SERIALIZERS["pdf"] = PDFSerializer\n'
    )
    # The registry: declares _SERIALIZERS, then triggers the auto-init
    # via importlib.import_module (the n=10-r4 pattern verbatim).
    _write(root, "src/export/formats.py",
        '"""serializer registry."""\n'
        'import importlib\n'
        '_SERIALIZERS = {}\n'
        'def _bootstrap():\n'
        '    importlib.import_module("src.export.formats_init")\n'
        '_bootstrap()\n'
        'def get(key):\n'
        '    return _SERIALIZERS[key]\n'
    )


def test_SH1_n10_r4_shadowing_detected():
    """The n=10-r4 archetype: tier 3.5 must produce a [SHADOWING] entry
    naming the actual module (formats_init) as the runtime resolution
    when only `pdf.py` is declared in the phase."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_n10r4_scaffold(root)
        # The phase declares the real impl + the registry, NOT the
        # formats_init shadowing module.
        phase = PhaseInput(
            id=1,
            paths=[
                "src/__init__.py",
                "src/export/__init__.py",
                "src/export/pdf.py",
                "src/export/formats.py",
            ],
        )
        r = verify_phase(phase, root, tier=2, with_runtime_smoke_test=True)
    shadowing = [
        f for f in r.runtime_smoke_findings if f.startswith("[SHADOWING:")
    ]
    assert shadowing, (
        f"expected at least one [SHADOWING:...] entry, got: "
        f"{r.runtime_smoke_findings}"
    )
    # The shadowing entry must name formats_init as the actual module.
    joined = " ".join(shadowing)
    assert "formats_init" in joined, joined
    # And it must reference the registry / key 'pdf'.
    assert "_SERIALIZERS" in joined or "pdf" in joined, joined
    assert r.passed is False
    # corrective_dispatch should mention shadowing.
    assert "registry resolution" in r.corrective_dispatch.lower() or \
           "SHADOWING" in r.corrective_dispatch or \
           "shadow" in r.corrective_dispatch.lower(), r.corrective_dispatch


def test_SH2_n10_r4_with_tier3_both_fire():
    """Same n=10-r4 scaffold with tier=3. Tier 3.5 [SHADOWING] should
    fire AND tier 3 should also surface findings (CAT1 unused class
    PDFSerializer in pdf.py is one shape; tier 3.5 catches the runtime
    side). Defense-in-depth — both signals appear."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_n10r4_scaffold(root)
        phase = PhaseInput(
            id=1,
            paths=[
                "src/__init__.py",
                "src/export/__init__.py",
                "src/export/pdf.py",
                "src/export/formats.py",
            ],
        )
        r = verify_phase(phase, root, tier=3, with_runtime_smoke_test=True)
    # Tier 3.5 fired.
    assert any(
        f.startswith("[SHADOWING:") for f in r.runtime_smoke_findings
    ), r.runtime_smoke_findings
    # Tier 3 fired (some integrity_issue exists; at minimum the
    # PDFSerializer class in pdf.py is unreferenced from this phase's
    # files, since formats.py uses _SERIALIZERS not pdf.PDFSerializer).
    assert r.integrity_issues, "expected tier 3 to also produce issues"
    assert r.tier_run == 3
    assert r.passed is False


# ---- Sandbox / failure modes (5 tests) ----


def test_F1_subprocess_timeout():
    """Subprocess infinite-loops at import; tier 3.5 reports
    [INCONCLUSIVE:timeout]; passed unaffected by tier 3.5 alone."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/slow.py",
            '"""slow module."""\n'
            'import time\n'
            'def use_time():\n'
            '    return time\n'
            'while True:\n'
            '    pass\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/slow.py"])
        r = verify_phase(
            phase,
            root,
            tier=2,
            with_runtime_smoke_test=True,
            runtime_smoke_test_timeout=2,
        )
    assert any(
        f.startswith("[INCONCLUSIVE:timeout]")
        for f in r.runtime_smoke_findings
    ), r.runtime_smoke_findings
    # Tier 1+2 passed; passed should remain True (INCONCLUSIVE doesn't
    # flip the verdict).
    assert r.passed is True


def test_F2_subprocess_import_raises():
    """An imported module raises at import time. Probe records this as
    a per-module import error; verifier surfaces it as
    [INCONCLUSIVE:import-error]; passed unaffected."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/boom.py",
            '"""boom."""\n'
            'def use_msg():\n'
            '    return MSG\n'
            'MSG = "hi"\n'
            'raise RuntimeError("boom at import")\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/boom.py"])
        r = verify_phase(
            phase, root, tier=2, with_runtime_smoke_test=True
        )
    assert any(
        f.startswith("[INCONCLUSIVE:import-error]")
        for f in r.runtime_smoke_findings
    ), r.runtime_smoke_findings
    # tier 2 passed; tier 3.5 inconclusive doesn't flip passed.
    assert r.passed is True


def test_F3_malformed_subprocess_output():
    """Force malformed output by monkey-patching the probe-script string
    so the sentinel is missing. Verify [INCONCLUSIVE:malformed-output]
    surfaces and passed is unaffected."""
    import verify_phase as vp_mod
    original_probe = vp_mod._TIER35_PROBE_SCRIPT
    # Replace with a script that runs but prints nothing.
    vp_mod._TIER35_PROBE_SCRIPT = (
        "import sys\n"
        "sys.exit(0)\n"
    )
    try:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "src/__init__.py", _PKG_INIT)
            _write(root, "src/m.py", _PLAIN_BODY)
            phase = PhaseInput(
                id=1, paths=["src/__init__.py", "src/m.py"]
            )
            r = verify_phase(
                phase, root, tier=2, with_runtime_smoke_test=True
            )
    finally:
        vp_mod._TIER35_PROBE_SCRIPT = original_probe
    assert any(
        f.startswith("[INCONCLUSIVE:malformed-output]")
        for f in r.runtime_smoke_findings
    ), r.runtime_smoke_findings
    assert r.passed is True


def test_F4_configurable_timeout():
    """Pass runtime_smoke_test_timeout=2 and verify the timeout fires
    after ~2s rather than the default 10s."""
    import time
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/slow.py",
            '"""slow."""\n'
            'def use_time():\n'
            '    return None\n'
            'while True:\n'
            '    pass\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/slow.py"])
        t0 = time.monotonic()
        r = verify_phase(
            phase,
            root,
            tier=2,
            with_runtime_smoke_test=True,
            runtime_smoke_test_timeout=2,
        )
        elapsed = time.monotonic() - t0
    assert any(
        f.startswith("[INCONCLUSIVE:timeout]")
        for f in r.runtime_smoke_findings
    ), r.runtime_smoke_findings
    # Should finish within a reasonable margin of the 2s budget.
    assert elapsed < 8, f"timeout fired too late: {elapsed:.2f}s"


def test_F5_sandbox_does_not_inherit_env():
    """Set OMLX_API_KEY in the parent. The probe script reads
    os.environ.get('OMLX_API_KEY'); verify it does NOT see the parent's
    value. Achieved by writing a probe-script-side module that captures
    the env var into a module-level constant, then checking the
    [CHECKED:...] entries report "<not-found>"."""
    import os as _os
    original = _os.environ.get("OMLX_API_KEY")
    _os.environ["OMLX_API_KEY"] = "secret123-parent-only"
    try:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "src/__init__.py", _PKG_INIT)
            _write(root, "src/probe.py",
                '"""probe."""\n'
                'import os\n'
                'class _Capture:\n'
                '    val = os.environ.get("OMLX_API_KEY", "<not-found>")\n'
                'REGISTRY = {"capture": _Capture}\n'
                'def use_it():\n'
                '    return REGISTRY["capture"]\n'
            )
            phase = PhaseInput(
                id=1, paths=["src/__init__.py", "src/probe.py"]
            )
            r = verify_phase(
                phase, root, tier=2, with_runtime_smoke_test=True
            )
            # The class _Capture itself comes from src.probe (same phase),
            # so it'll be [CHECKED:entry-matches-declared]. We can't read
            # the captured val directly from outside the subprocess, but
            # we can write a second registry whose key reflects the val.
            #
            # Better approach: re-do the test by making the registry
            # KEY contain the captured value. Then [CHECKED] entry will
            # carry the key in its rendered string.
            pass
        # Stage 2: actually exercise the env-leak check via key encoding.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root, "src/__init__.py", _PKG_INIT)
            _write(root, "src/probe.py",
                '"""probe."""\n'
                'import os\n'
                'class C:\n'
                '    pass\n'
                '_VAL = os.environ.get("OMLX_API_KEY", "<not-found>")\n'
                'REGISTRY = {_VAL: C}\n'
                'def use_it():\n'
                '    return REGISTRY\n'
            )
            phase = PhaseInput(
                id=1, paths=["src/__init__.py", "src/probe.py"]
            )
            r = verify_phase(
                phase, root, tier=2, with_runtime_smoke_test=True
            )
        # The CHECKED entry's key field reflects the env-var capture.
        joined = " ".join(r.runtime_smoke_findings)
        assert "<not-found>" in joined, (
            f"sandbox leaked OMLX_API_KEY into subprocess; findings: "
            f"{r.runtime_smoke_findings}"
        )
        assert "secret123-parent-only" not in joined, joined
    finally:
        if original is None:
            _os.environ.pop("OMLX_API_KEY", None)
        else:
            _os.environ["OMLX_API_KEY"] = original


# ---- Registry detection (4 tests) ----


def test_R1_one_registry_clean_entries():
    """One dict registry, all entries from declared paths -> all
    [CHECKED]; no [SHADOWING]; passed=True."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/m.py",
            '"""m."""\n'
            'class Foo:\n'
            '    pass\n'
            'class Bar:\n'
            '    pass\n'
            'REGISTRY = {"foo": Foo, "bar": Bar}\n'
            'def use_it():\n'
            '    return REGISTRY\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/m.py"])
        r = verify_phase(
            phase, root, tier=2, with_runtime_smoke_test=True
        )
    checked = [
        f for f in r.runtime_smoke_findings if f.startswith("[CHECKED:")
    ]
    shadow = [
        f for f in r.runtime_smoke_findings if f.startswith("[SHADOWING:")
    ]
    assert checked, r.runtime_smoke_findings
    assert not shadow, r.runtime_smoke_findings
    assert r.passed is True


def test_R2_multiple_registries_all_clean():
    """Two registries in different files, all clean -> all reported."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/a.py",
            '"""a."""\n'
            'class A1:\n'
            '    pass\n'
            'HANDLERS = {"a": A1}\n'
            'def use_a():\n'
            '    return HANDLERS\n'
        )
        _write(root, "src/b.py",
            '"""b."""\n'
            'class B1:\n'
            '    pass\n'
            'SERIALIZERS = {"b": B1}\n'
            'def use_b():\n'
            '    return SERIALIZERS\n'
        )
        phase = PhaseInput(
            id=1, paths=["src/__init__.py", "src/a.py", "src/b.py"]
        )
        r = verify_phase(
            phase, root, tier=2, with_runtime_smoke_test=True
        )
    joined = " ".join(r.runtime_smoke_findings)
    assert "HANDLERS" in joined, joined
    assert "SERIALIZERS" in joined, joined
    shadow = [
        f for f in r.runtime_smoke_findings if f.startswith("[SHADOWING:")
    ]
    assert not shadow
    assert r.passed is True


def test_R3_class_based_registry_detected():
    """Duck-type detection: a class with `register` and `get` methods,
    instantiated at module level, gets detected."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/m.py",
            '"""m."""\n'
            'class Registry:\n'
            '    def __init__(self):\n'
            '        self._items = {}\n'
            '    def register(self, k, v):\n'
            '        self._items[k] = v\n'
            '    def get(self, k):\n'
            '        return self._items[k]\n'
            'class Plugin:\n'
            '    pass\n'
            'plugins = Registry()\n'
            'plugins.register("p1", Plugin)\n'
            'def use_it():\n'
            '    return plugins.get("p1")\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/m.py"])
        r = verify_phase(
            phase, root, tier=2, with_runtime_smoke_test=True
        )
    joined = " ".join(r.runtime_smoke_findings)
    # The duck-typed registry's name "plugins" should appear.
    assert "plugins" in joined, joined
    assert "Plugin" in joined, joined
    assert r.passed is True


def test_R4_obscure_name_registry_not_detected_no_false_positive():
    """A dict named with non-standard name (e.g. `lookup_table`) is NOT
    detected by the heuristic — documented limitation. The test asserts
    no false positive: passed=True, no spurious findings about it."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/m.py",
            '"""m."""\n'
            'class Foo:\n'
            '    pass\n'
            'lookup_table = {"foo": Foo}\n'  # non-standard name
            'def use_it():\n'
            '    return lookup_table\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/m.py"])
        r = verify_phase(
            phase, root, tier=2, with_runtime_smoke_test=True
        )
    joined = " ".join(r.runtime_smoke_findings)
    assert "lookup_table" not in joined, (
        f"obscure-name registry should NOT be detected: {joined}"
    )
    assert r.passed is True
    # Should report "no registries detected" or similar [CHECKED] note.
    assert any(
        f.startswith("[CHECKED:") for f in r.runtime_smoke_findings
    ), r.runtime_smoke_findings


# ---- Composability (2 tests) ----


def test_C1_tier3_and_tier35_both_run():
    """tier=3 AND with_runtime_smoke_test=True: both tiers run; both
    sets of findings appear."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _build_n10r4_scaffold(root)
        phase = PhaseInput(
            id=1,
            paths=[
                "src/__init__.py",
                "src/export/__init__.py",
                "src/export/pdf.py",
                "src/export/formats.py",
            ],
        )
        r = verify_phase(phase, root, tier=3, with_runtime_smoke_test=True)
    # tier 3 produced integrity_issues
    assert r.integrity_issues, "tier 3 should have produced issues"
    # tier 3.5 produced shadowing findings
    assert any(
        f.startswith("[SHADOWING:") for f in r.runtime_smoke_findings
    )
    # corrective_dispatch should mention both
    cd = r.corrective_dispatch
    assert "tier 3" in cd.lower() or "CAT" in cd
    assert "registry" in cd.lower() or "shadow" in cd.lower()


def test_C2_tier2_and_tier35_runs_tier3_does_not():
    """tier=2 AND with_runtime_smoke_test=True: tier 3.5 runs (only
    requires tier 1+2 pass); tier 3 does NOT run."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/m.py",
            '"""m."""\n'
            'class Foo:\n'
            '    pass\n'
            'REGISTRY = {"foo": Foo}\n'
            'def use_it():\n'
            '    return REGISTRY\n'
        )
        # Define a "dead" function. Tier 3 would flag it as CAT1; tier 2
        # would not.
        _write(root, "src/dead.py",
            '"""dead."""\n'
            'def never_called():\n'
            '    return 1\n'
            'def alone():\n'
            '    return 2\n'
            'def lonely():\n'
            '    return 3\n'
        )
        phase = PhaseInput(
            id=1, paths=["src/__init__.py", "src/m.py", "src/dead.py"]
        )
        r = verify_phase(
            phase, root, tier=2, with_runtime_smoke_test=True
        )
    # tier 3 NOT run: no [CATn:...] entries in integrity_issues
    cat_entries = [
        i for i in r.integrity_issues if i.startswith("[CAT")
    ]
    assert not cat_entries, f"tier 3 should not have run: {cat_entries}"
    assert r.tier_run == 2
    # tier 3.5 ran
    assert r.runtime_smoke_findings
    assert any(
        f.startswith("[CHECKED:") for f in r.runtime_smoke_findings
    )


# ---- tier_3_hint integration (2 tests) ----


def test_H1_dynamic_imports_tier3_hint_no_smoke():
    """Phase with dynamic imports, tier=3, with_runtime_smoke_test=False:
    tier_3_hint set; tier 3.5 NOT invoked."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/dyn.py",
            '"""dyn."""\n'
            'import importlib\n'
            'def loader():\n'
            '    return importlib.import_module("os")\n'
            'WIRED = loader()\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/dyn.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.tier_3_hint is not None
    assert r.runtime_smoke_findings == []


def test_H2_dynamic_imports_tier3_hint_with_smoke():
    """Same phase but with_runtime_smoke_test=True: tier_3_hint set AND
    tier 3.5 runs."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/__init__.py", _PKG_INIT)
        _write(root, "src/dyn.py",
            '"""dyn."""\n'
            'import importlib\n'
            'def loader():\n'
            '    return importlib.import_module("os")\n'
            'WIRED = loader()\n'
        )
        phase = PhaseInput(id=1, paths=["src/__init__.py", "src/dyn.py"])
        r = verify_phase(
            phase, root, tier=3, with_runtime_smoke_test=True
        )
    assert r.tier_3_hint is not None
    assert r.runtime_smoke_findings, r.runtime_smoke_findings


# ---------------------------------------------------------------------------
# cat1_extra_allow_list parameter (item 5 wrapper-config seam)
# ---------------------------------------------------------------------------


def test_X1_cat1_extra_allow_list_suppresses_flag():
    """ws_app is a public-API name picked up by string lookup. With it in
    cat1_extra_allow_list, CAT1 must NOT flag it as defined-unused."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/api/ws.py",
            (
                '"""ws — `ws_app` is consumed by the framework by name."""\n'
                "ws_app = object()  # framework picks this up by string\n"
                "VAL = 1\n"
                "def keepalive():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/ws.py"])
        r = verify_phase(
            phase, root, tier=3, cat1_extra_allow_list=["ws_app"]
        )
    cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
    assert not any("`ws_app`" in i for i in cat1), r.integrity_issues


def test_X2_cat1_without_extra_allow_list_flags_ws_app():
    """Without the extra allow-list, ws_app IS flagged — confirms the
    new param meaningfully gates behavior."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(
            root,
            "src/api/ws.py",
            (
                '"""ws — `ws_app` is unreferenced by AST."""\n'
                "ws_app = object()\n"
                "VAL = 1\n"
                "def keepalive():\n"
                "    return VAL\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/api/ws.py"])
        r_no = verify_phase(phase, root, tier=3)
        r_none = verify_phase(phase, root, tier=3, cat1_extra_allow_list=None)
    for r in (r_no, r_none):
        cat1 = [i for i in r.integrity_issues if "[CAT1:defined-unused]" in i]
        assert any("`ws_app`" in i for i in cat1), r.integrity_issues


# ---------------------------------------------------------------------------
# Tier 3.7 — acceptance-runner (r7.11 F-7 fix)
# ---------------------------------------------------------------------------


def test_A1_tier37_skipped_when_no_acceptance_command():
    """No acceptance_command declared -> acceptance_runner_findings is
    empty (silent no-op), passed unaffected."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(phase, root, tier=3)
    assert r.acceptance_runner_findings == [], r.acceptance_runner_findings
    assert r.passed is True, r


def test_A2_tier37_skipped_when_tier1_fails():
    """Tier 1 missing-paths -> tier 3.7 must NOT execute."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # No file written -> tier 1 fails
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="pytest tests/test_export.py",
        )
    assert r.passed is False
    # Skipped finding present, no actual execution attempted
    assert any("[SKIPPED]" in f for f in r.acceptance_runner_findings), r
    assert not any(
        "[ACCEPTANCE_" in f for f in r.acceptance_runner_findings
    )


def test_A3_tier37_skipped_when_tier2_fails():
    """Tier 1 passes, tier 2 fails (syntax error) -> tier 3.7 SKIPPED."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # Substantive enough to clear tier 1 (>=50 bytes, >=3 lines)
        # but syntactically broken so tier 2 fails.
        _write(
            root,
            "src/m.py",
            (
                '"""substantive but syntactically broken module."""\n'
                "import os\n"
                "VALUE = 42\n"
                "def broken(\n"
                "    # missing close paren and body\n"
            ),
        )
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="python3 -c 'import sys; sys.exit(0)'",
        )
    assert r.passed is False  # tier 2 broke
    assert any(
        "SyntaxError" in i for i in r.integrity_issues
    ), r.integrity_issues
    assert any("[SKIPPED]" in f for f in r.acceptance_runner_findings)


def test_A4_tier37_acceptance_passed_general_exit_zero():
    """Non-pytest command exiting 0 -> [ACCEPTANCE_PASSED]."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command='python3 -c "import sys; sys.exit(0)"',
        )
    assert r.passed is True, r
    assert any(
        f.startswith("[ACCEPTANCE_PASSED]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A5_tier37_acceptance_failed_general_nonzero():
    """Non-pytest command exiting nonzero -> [ACCEPTANCE_FAILED:N],
    passed=False, exit code preserved in prefix."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command='python3 -c "import sys; sys.exit(7)"',
        )
    assert r.passed is False, r
    assert any(
        f.startswith("[ACCEPTANCE_FAILED:7]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings
    # corrective_dispatch should mention the command
    assert "python3" in r.corrective_dispatch, r.corrective_dispatch


def test_A6_tier37_pytest_exit0_acceptance_passed():
    """First token simulating pytest, exit 0 -> [ACCEPTANCE_PASSED]."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        # Stub pytest binary that exits 0.
        pytest_stub = root / "pytest"
        pytest_stub.write_text(
            "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"
        )
        pytest_stub.chmod(0o755)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="./pytest tests/",
        )
    assert r.passed is True
    assert any(
        f.startswith("[ACCEPTANCE_PASSED]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A7_tier37_pytest_exit1_acceptance_failed_with_output():
    """pytest exit 1 -> [ACCEPTANCE_FAILED:1], stdout in
    corrective_dispatch."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        pytest_stub = root / "pytest"
        pytest_stub.write_text(
            "#!/usr/bin/env bash\n"
            "echo 'FAILED tests/test_x.py::test_thing - assert 1 == 2'\n"
            "exit 1\n",
            encoding="utf-8",
        )
        pytest_stub.chmod(0o755)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="./pytest tests/",
        )
    assert r.passed is False
    assert any(
        f.startswith("[ACCEPTANCE_FAILED:1]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings
    # The stdout failure marker should make it into the dispatch text
    assert "FAILED tests" in r.corrective_dispatch, r.corrective_dispatch


def test_A8_tier37_pytest_exit2_inconclusive_interrupted():
    """pytest exit 2 (interrupted) -> [INCONCLUSIVE:interrupted];
    does NOT set passed=False."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        pytest_stub = root / "pytest"
        pytest_stub.write_text(
            "#!/usr/bin/env bash\nexit 2\n", encoding="utf-8"
        )
        pytest_stub.chmod(0o755)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="./pytest tests/",
        )
    # tier 1-3 all clean AND inconclusive doesn't fail -> passed=True
    assert r.passed is True, r
    assert any(
        f.startswith("[INCONCLUSIVE:interrupted]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A9_tier37_pytest_exit5_environment_no_tests():
    """pytest exit 5 (no tests collected) -> [ENVIRONMENT:..]; sets
    passed=False (env-side blocker)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        pytest_stub = root / "pytest"
        pytest_stub.write_text(
            "#!/usr/bin/env bash\nexit 5\n", encoding="utf-8"
        )
        pytest_stub.chmod(0o755)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="./pytest tests/",
        )
    assert r.passed is False, r
    assert any(
        f.startswith("[ENVIRONMENT:no-tests-collected]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A10_tier37_command_not_found_environment():
    """A nonexistent binary -> [ENVIRONMENT:command-not-found:..],
    passed=False."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command=(
                "definitely-not-a-real-binary-r7-11 --foo"
            ),
        )
    assert r.passed is False
    assert any(
        "command-not-found" in f
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A11_tier37_timeout_environment():
    """A long-running command exceeding the timeout ->
    [ENVIRONMENT:timeout-after-..s], passed=False."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command='python3 -c "import time; time.sleep(5)"',
            acceptance_timeout_seconds=1,
        )
    assert r.passed is False
    assert any(
        "timeout-after-" in f
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A12_tier37_pythonpath_injection_uses_scaffold_venv():
    """When scaffold/.venv/lib/pythonX.Y/site-packages exists, the
    subprocess env's PYTHONPATH is augmented with that path. We mock
    subprocess.run to capture the env and assert."""
    import unittest.mock as um

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        # Create the .venv site-packages dir
        sp = root / ".venv" / "lib" / "python3.11" / "site-packages"
        sp.mkdir(parents=True)

        captured = {}

        def fake_run(argv, **kwargs):
            captured["env"] = kwargs.get("env")
            captured["cwd"] = kwargs.get("cwd")
            captured["argv"] = argv

            class _FakeProc:
                returncode = 0
                stdout = b""
                stderr = b""
            return _FakeProc()

        phase = PhaseInput(id=1, paths=["src/m.py"])
        with um.patch("verify_phase.subprocess.run", side_effect=fake_run):
            r = verify_phase(
                phase, root, tier=3,
                acceptance_command="echo hello",
            )
    env = captured["env"]
    assert env is not None
    assert "PYTHONPATH" in env, env
    assert str(sp) in env["PYTHONPATH"], env["PYTHONPATH"]
    # Must run in the scaffold root
    assert captured["cwd"] == str(root)
    # And we ran -> reported acceptance_passed
    assert any(
        f.startswith("[ACCEPTANCE_PASSED]")
        for f in r.acceptance_runner_findings
    ), r.acceptance_runner_findings


def test_A13_tier37_no_venv_pythonpath_untouched():
    """When scaffold has no .venv, PYTHONPATH is left as-is from
    os.environ.copy() (not mutated by tier 3.7)."""
    import os as _os
    import unittest.mock as um

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        # NO .venv created

        captured = {}

        def fake_run(argv, **kwargs):
            captured["env"] = kwargs.get("env")

            class _FakeProc:
                returncode = 0
                stdout = b""
                stderr = b""
            return _FakeProc()

        phase = PhaseInput(id=1, paths=["src/m.py"])
        original_pp = _os.environ.get("PYTHONPATH", "<<unset>>")
        with um.patch("verify_phase.subprocess.run", side_effect=fake_run):
            verify_phase(
                phase, root, tier=3,
                acceptance_command="echo hello",
            )
    env = captured["env"]
    # No augmentation: the env's PYTHONPATH equals whatever os.environ
    # already had (or absent if it wasn't set).
    if original_pp == "<<unset>>":
        assert "PYTHONPATH" not in env, (
            "PYTHONPATH should not be added when no .venv exists; "
            f"got {env.get('PYTHONPATH')!r}"
        )
    else:
        assert env.get("PYTHONPATH") == original_pp


def test_A14_tier37_stdout_truncation_bounded():
    """A command that produces ~5000 chars of stdout -> the
    corrective_dispatch text is bounded (~1500 chars combined for the
    truncated body, plus the wrapping prose). We check it's NOT 5000+."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        # Print 5000 chars of 'A' then exit 1 (acceptance_failed).
        pytest_stub = root / "pytest"
        pytest_stub.write_text(
            "#!/usr/bin/env bash\n"
            "python3 -c \"print('A' * 5000)\"\n"
            "exit 1\n",
            encoding="utf-8",
        )
        pytest_stub.chmod(0o755)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=3,
            acceptance_command="./pytest tests/",
        )
    assert r.passed is False
    # Find the ACCEPTANCE_FAILED finding
    failed = [
        f for f in r.acceptance_runner_findings
        if f.startswith("[ACCEPTANCE_FAILED:")
    ]
    assert failed
    # The entire finding body — not the wrapping prose — should be well
    # under the 5000-char raw output.
    assert len(failed[0]) < 3000, len(failed[0])
    # And corrective_dispatch shouldn't balloon either
    assert len(r.corrective_dispatch) < 4500, len(r.corrective_dispatch)


def test_A15_tier37_default_runs_when_acceptance_command_present():
    """No opt-in flag: tier 3.7 default-on when acceptance_command is
    declared. (Mirror of A4 but emphasizing the default-on contract.)"""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        # No with_runtime_smoke_test, no extra opt-in — just declare
        # acceptance_command. It should run.
        r = verify_phase(
            phase, root, tier=2,
            acceptance_command='python3 -c "import sys; sys.exit(0)"',
        )
    assert r.acceptance_runner_findings, "tier 3.7 should have run"
    assert any(
        f.startswith("[ACCEPTANCE_PASSED]")
        for f in r.acceptance_runner_findings
    )


def test_A16_tier37_tier2_branch_runs_acceptance_command():
    """At tier=2, with declared acceptance_command, tier 3.7 still
    runs (gate is tier1+tier2 passed, NOT tier=3 requested)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _write(root, "src/m.py", TIER3_CLEAN_BODY)
        phase = PhaseInput(id=1, paths=["src/m.py"])
        r = verify_phase(
            phase, root, tier=2,
            acceptance_command='python3 -c "import sys; sys.exit(1)"',
        )
    assert r.passed is False
    assert any(
        f.startswith("[ACCEPTANCE_FAILED:1]")
        for f in r.acceptance_runner_findings
    )


# ---------------------------------------------------------------------------
# Plain-script entry point
# ---------------------------------------------------------------------------


def _run_all():
    tests = [(n, fn) for n, fn in globals().items() if n.startswith("test_") and callable(fn)]
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
