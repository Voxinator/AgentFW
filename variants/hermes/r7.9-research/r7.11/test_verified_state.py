"""Tests for verified_state module (r7.11 item 1).

Runnable two ways:
  pytest test_verified_state.py -v
  python3 test_verified_state.py     (falls back to plain assertions)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Allow `python3 test_verified_state.py` from any CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verified_state as vs
from verified_state import (
    Decision,
    DecisionAction,
    IntegrityError,
    PhaseSpec,
    PhaseStatus,
    SchemaError,
    bootstrap,
    decide,
    from_dict,
    load,
    record_verdict,
    save,
    to_dict,
)


# ---------------------------------------------------------------------------
# Fixtures (lightweight; no pytest dependency)
# ---------------------------------------------------------------------------

def _phases3():
    return [
        PhaseSpec(id=1, title="Core serializers"),
        PhaseSpec(id=2, title="API + permissions"),
        PhaseSpec(id=3, title="Tests + docs"),
    ]


def _bootstrap_default(max_revisions: int = 3):
    return bootstrap(
        scaffold_root="/tmp/probe-scaffold",
        plan_md_path="/tmp/probe-scaffold/PLAN.md",
        phases=_phases3(),
        max_revisions=max_revisions,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bootstrap_pending():
    s = _bootstrap_default(max_revisions=5)
    assert s.schema_version == "1.0"
    assert len(s.phase_state) == 3
    for e in s.phase_state:
        assert e.status == PhaseStatus.PENDING
        assert e.revision_count == 0
        assert e.max_revisions == 5
        assert e.tier_run is None
        assert e.verified_at is None
        assert e.missing_paths == []
        assert e.integrity_issues == []
    assert s.history == []
    assert s.spec.scaffold_root == "/tmp/probe-scaffold"


def test_save_load_roundtrip():
    s = _bootstrap_default()
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "verified-state.json"
        save(s, path)
        s2 = load(path)
    assert to_dict(s) == to_dict(s2)


def test_saved_file_is_valid_json():
    s = _bootstrap_default()
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "verified-state.json"
        save(s, path)
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    assert parsed["schema_version"] == "1.0"
    assert "spec" in parsed and "phase_state" in parsed and "history" in parsed
    assert isinstance(parsed["phase_state"], list)
    assert len(parsed["phase_state"]) == 3


def test_atomic_write_failure_preserves_target_and_cleans_temp(monkeypatch=None):
    """If os.replace fails mid-flight, target stays intact and temp is removed."""
    s1 = _bootstrap_default()
    s2 = record_verdict(s1, phase_id=1, passed=True, session_id="sess1", tier_run=2)

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "verified-state.json"
        # First write a known-good baseline.
        save(s1, path)
        baseline_bytes = path.read_bytes()

        # Now monkeypatch os.replace to simulate failure.
        real_replace = os.replace
        calls = {"n": 0}

        def boom(src, dst):
            calls["n"] += 1
            raise OSError("simulated mid-flight replace failure")

        os.replace = boom
        try:
            failed = False
            try:
                save(s2, path)
            except OSError:
                failed = True
            assert failed, "save() should have propagated the OSError"
        finally:
            os.replace = real_replace

        # Target unchanged.
        assert path.read_bytes() == baseline_bytes

        # No leftover temp files in the directory.
        leftover = [
            p for p in Path(d).iterdir() if p.name != "verified-state.json"
        ]
        assert leftover == [], f"unexpected leftover temp files: {leftover}"

        # And we can still load the original.
        loaded = load(path)
        assert to_dict(loaded) == to_dict(s1)


def test_record_verdict_passing():
    s = _bootstrap_default()
    s2 = record_verdict(
        s,
        phase_id=1,
        passed=True,
        session_id="sess-pass-001",
        tier_run=3,
    )
    e = next(e for e in s2.phase_state if e.id == 1)
    assert e.status == PhaseStatus.VERIFIED_PASSED
    assert e.tier_run == 3
    assert e.session_id == "sess-pass-001"
    assert e.verified_at is not None
    assert e.verified_at.endswith("Z")
    assert e.revision_count == 0
    assert len(s2.history) == 1
    assert s2.history[0].verdict == "passed"
    assert s2.history[0].phase_id == 1
    assert s2.history[0].session_id == "sess-pass-001"


def test_record_verdict_failing():
    s = _bootstrap_default()
    s2 = record_verdict(
        s,
        phase_id=2,
        passed=False,
        session_id="sess-fail-001",
        tier_run=3,
        missing_paths=["src/api/export.py"],
        integrity_issues=["src/auth/permissions.py imported but never invoked"],
        corrective_dispatch="Re-dispatch with explicit focus on src/api/export.py",
    )
    e = next(e for e in s2.phase_state if e.id == 2)
    assert e.status == PhaseStatus.VERIFIED_FAILED
    assert e.revision_count == 1
    assert e.missing_paths == ["src/api/export.py"]
    assert e.integrity_issues == ["src/auth/permissions.py imported but never invoked"]
    assert e.corrective_dispatch == "Re-dispatch with explicit focus on src/api/export.py"
    assert s2.history[-1].verdict == "failed"
    assert s2.history[-1].phase_id == 2


def test_record_verdict_immutability():
    s = _bootstrap_default()
    s_dict_before = to_dict(s)
    s2 = record_verdict(s, phase_id=1, passed=False, session_id="x", tier_run=2)
    # Original state object unchanged.
    assert to_dict(s) == s_dict_before
    # Returned object is a new instance with new content.
    assert s is not s2
    assert to_dict(s2) != s_dict_before


def test_decide_all_pending_returns_advance_first():
    s = _bootstrap_default()
    d = decide(s)
    assert d.action == DecisionAction.ADVANCE
    assert d.phase_id == 1


def test_decide_first_passed_returns_advance_second():
    s = _bootstrap_default()
    s = record_verdict(s, phase_id=1, passed=True, session_id="s", tier_run=2)
    d = decide(s)
    assert d.action == DecisionAction.ADVANCE
    assert d.phase_id == 2


def test_decide_first_failed_revisions_available_returns_revise():
    s = _bootstrap_default(max_revisions=3)
    s = record_verdict(s, phase_id=1, passed=False, session_id="s", tier_run=2)
    d = decide(s)
    assert d.action == DecisionAction.REVISE
    assert d.phase_id == 1


def test_decide_first_failed_max_revisions_returns_escalate():
    s = _bootstrap_default(max_revisions=2)
    s = record_verdict(s, phase_id=1, passed=False, session_id="s1", tier_run=2)
    s = record_verdict(s, phase_id=1, passed=False, session_id="s2", tier_run=2)
    # revision_count should now be 2 == max_revisions
    e = next(e for e in s.phase_state if e.id == 1)
    assert e.revision_count == 2
    d = decide(s)
    assert d.action == DecisionAction.ESCALATE
    assert d.phase_id == 1
    assert "max revisions" in d.reason


def test_decide_all_passed_returns_complete():
    s = _bootstrap_default()
    for pid in (1, 2, 3):
        s = record_verdict(s, phase_id=pid, passed=True, session_id=f"s{pid}", tier_run=2)
    d = decide(s)
    assert d.action == DecisionAction.COMPLETE
    assert d.phase_id is None


def test_decide_sequential_discipline_failed_blocks_pending():
    """Phase 1 failed (max revisions hit) AND phase 2 pending → ESCALATE on 1, NOT ADVANCE on 2."""
    s = _bootstrap_default(max_revisions=1)
    s = record_verdict(s, phase_id=1, passed=False, session_id="s1", tier_run=2)
    # revision_count=1, max=1 → exhausted
    d = decide(s)
    assert d.action == DecisionAction.ESCALATE
    assert d.phase_id == 1


def test_load_rejects_bad_schema_version():
    s = _bootstrap_default()
    d = to_dict(s)
    d["schema_version"] = "2.0"
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        try:
            load(path)
        except SchemaError as exc:
            assert "schema_version" in str(exc) or "2.0" in str(exc)
        else:
            raise AssertionError("expected SchemaError")

    # Missing schema_version
    d2 = to_dict(s)
    d2.pop("schema_version")
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d2), encoding="utf-8")
        try:
            load(path)
        except SchemaError:
            pass
        else:
            raise AssertionError("expected SchemaError on missing schema_version")


def test_load_rejects_missing_phase_state():
    s = _bootstrap_default()
    d = to_dict(s)
    d.pop("phase_state")
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        try:
            load(path)
        except SchemaError as exc:
            assert "phase_state" in str(exc)
        else:
            raise AssertionError("expected SchemaError")


def test_load_rejects_invalid_status_enum():
    s = _bootstrap_default()
    d = to_dict(s)
    d["phase_state"][0]["status"] = "bogus"
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        try:
            load(path)
        except SchemaError as exc:
            assert "bogus" in str(exc) or "status" in str(exc)
        else:
            raise AssertionError("expected SchemaError")


def test_load_rejects_phase_id_not_in_spec():
    s = _bootstrap_default()
    d = to_dict(s)
    d["phase_state"][0]["id"] = 999
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        try:
            load(path)
        except SchemaError as exc:
            assert "999" in str(exc) or "spec.phases" in str(exc)
        else:
            raise AssertionError("expected SchemaError")


def test_record_verdict_unknown_phase_raises_integrity_error():
    s = _bootstrap_default()
    try:
        record_verdict(s, phase_id=42, passed=True, session_id="x", tier_run=2)
    except IntegrityError as exc:
        assert "42" in str(exc)
    else:
        raise AssertionError("expected IntegrityError")


def test_load_tolerates_unknown_extra_fields_forward_compat():
    """Validation policy: unknown extra fields tolerated for forward-compat."""
    s = _bootstrap_default()
    d = to_dict(s)
    d["future_field"] = {"foo": "bar"}
    d["phase_state"][0]["future_per_phase"] = 123
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        loaded = load(path)  # should NOT raise
        assert loaded.schema_version == "1.0"


def test_record_verdict_persists_acceptance_runner_findings():
    """r7.11 F-7 fix: record_verdict accepts and persists
    acceptance_runner_findings; default is empty list."""
    s = _bootstrap_default()
    findings = [
        "[ACCEPTANCE_FAILED:1] stdout (truncated):\nFAILED tests/x.py",
    ]
    new_state = record_verdict(
        s,
        phase_id=2,
        passed=False,
        session_id="sess-7",
        tier_run=3,
        acceptance_runner_findings=findings,
    )
    e2 = next(e for e in new_state.phase_state if e.id == 2)
    assert e2.acceptance_runner_findings == findings

    # Roundtrip through to_dict/from_dict preserves it
    d = to_dict(new_state)
    e2_d = next(e for e in d["phase_state"] if e["id"] == 2)
    assert e2_d["acceptance_runner_findings"] == findings
    parsed = from_dict(d)
    e2_p = next(e for e in parsed.phase_state if e.id == 2)
    assert e2_p.acceptance_runner_findings == findings

    # Untouched phases default to []
    e1 = next(e for e in new_state.phase_state if e.id == 1)
    assert e1.acceptance_runner_findings == []


def test_load_legacy_state_without_acceptance_runner_findings_field():
    """A pre-r7.11-F7 state file (no acceptance_runner_findings key on
    phase_state entries) loads successfully and defaults to empty list
    — backward compatibility with persisted state from prior versions."""
    s = _bootstrap_default()
    d = to_dict(s)
    # Strip the new field as a pre-F7 file would not have it
    for entry in d["phase_state"]:
        del entry["acceptance_runner_findings"]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "v.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        loaded = load(path)
    for entry in loaded.phase_state:
        assert entry.acceptance_runner_findings == []


# ---------------------------------------------------------------------------
# Plain-script entry point (no pytest required)
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
