"""Tests for hermes_multi (r7.11 item 7 — wrapper substrate).

Runnable two ways:
  pytest test_hermes_multi.py -v
  python3 test_hermes_multi.py     (falls back to plain assertions)

Coverage (T1–T16 per brief + invariant test + T18–T22 bootstrap-mode +
T23–T25 LocalProcessTransport):
  T1  3-phase advance through to success
  T2  Phase fails, parent revises, passes
  T3  Parent escalates explicitly
  T4  Phase fails N+1 times, wrapper escalates
  T5  Hermes crashes mid-phase
  T6  Phase exceeds wall-clock (timeout)
  T7  Hermes exits clean (0) but no sentinel (anomalous_exit)
  T8  anomalous_exit_count > max → escalate
  T9  hermes-multi resume after escalate-pause
  T10 Wrapper-internal error (transport raises)
  T11 Malformed verify-config.json
  T12 hermes-multi status after a run
  T13 Sentinel grace timer (sentinel fires, hermes still running)
  T14 Manifest atomicity (os.replace failure)
  T15 Bootstrap state-file on first run (PLAN.md present, no verified-state)
  T16 Both end + escalate sentinels (anomaly)
  Inv Wrapper does not mutate verified-state.json during a session
  T18 Bootstrap session writes PLAN.md, run continues phase-by-phase
  T19 Bootstrap ends but PLAN.md not written → bootstrap_failed_no_plan
  T20 Bootstrap writes unparseable PLAN.md → bootstrap_failed_unparseable_plan
  T21 PLAN.md present at run-start → bootstrap session skipped (regression)
  T22 Neither PLAN.md nor USER-PROMPT.md → exit 4 (config error)
  T23 LocalProcessTransport file operations (Path-based)
  T24 LocalProcessTransport.launch_hermes returns Popen with env + cwd honored
  T25 Wrapper end-to-end via LocalProcessTransport + fake binary

Tests T1–T22 use LocalFsTransport + FakePopen against tempdir scaffolds.
T23–T25 exercise LocalProcessTransport with real subprocesses (fake
binary), but no real ssh, no real Hermes.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from unittest import mock

# Allow `python3 test_hermes_multi.py` from any CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hermes_multi as hm  # noqa: E402
import verified_state as vs  # noqa: E402
from handoff_tools import (  # noqa: E402
    SESSION_END_SENTINEL_NAME,
    SESSION_ESCALATE_SENTINEL_NAME,
)


# ---------------------------------------------------------------------------
# FakePopen — the load-bearing testability seam.
# ---------------------------------------------------------------------------


class FakePopen:
    """Stand-in for subprocess.Popen in tests.

    Configurable behavior:
      - exit_code: int returned by poll()/wait() once exit_after has elapsed
      - exit_after: seconds after construction at which the fake exits
      - sentinel_action: callable(scaffold_root) invoked at sentinel_at seconds
                         (typically writes an end or escalate sentinel)
      - sentinel_at: seconds after construction at which sentinel_action runs

    All timing references are real wall-clock seconds; tests use sub-second
    values (0.05–0.5) for fast execution.
    """

    def __init__(
        self,
        scaffold_root: str,
        *,
        exit_code: int = 0,
        exit_after: float = 0.5,
        sentinel_action: Optional[Callable[[str], None]] = None,
        sentinel_at: float = 0.05,
    ):
        self.scaffold_root = scaffold_root
        self._exit_code = exit_code
        self._exit_after = exit_after
        self._sentinel_action = sentinel_action
        self._sentinel_at = sentinel_at
        self._t0 = time.time()
        self._sentinel_done = False
        # `pid=-1` ensures Wrapper._terminate_popen's os.getpgid raises
        # ProcessLookupError, which is caught; popen.terminate() runs in
        # fallback (no real PID is touched).
        self.pid = -1
        self._terminated = False
        self._killed = False
        self._returncode: Optional[int] = None

    def _maybe_run_sentinel(self) -> None:
        if (
            not self._sentinel_done
            and self._sentinel_action is not None
            and time.time() - self._t0 >= self._sentinel_at
        ):
            try:
                self._sentinel_action(self.scaffold_root)
            except Exception:
                pass
            self._sentinel_done = True

    def poll(self) -> Optional[int]:
        self._maybe_run_sentinel()
        if self._returncode is not None:
            return self._returncode
        if time.time() - self._t0 >= self._exit_after:
            self._returncode = self._exit_code
            return self._returncode
        return None

    def wait(self, timeout: Optional[float] = None) -> int:
        deadline = time.time() + (timeout if timeout is not None else 1e9)
        while time.time() < deadline:
            r = self.poll()
            if r is not None:
                return r
            time.sleep(0.01)
        import subprocess
        raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout)

    def terminate(self) -> None:
        self._terminated = True
        # On termination, declare a real returncode so wait() can drain.
        self._returncode = (
            self._exit_code if self._exit_code != 0 else 143
        )

    def kill(self) -> None:
        self._killed = True
        self._returncode = -9


# ---------------------------------------------------------------------------
# Sentinel-action helpers
# ---------------------------------------------------------------------------


def _write_end_sentinel(scaffold: str) -> None:
    p = Path(scaffold) / SESSION_END_SENTINEL_NAME
    p.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "session-end",
                "timestamp": "2026-04-27T00:00:00Z",
                "session_id": "test-sid",
                "completed_phase": None,
                "parent_intent_log": None,
                "parent_summary": "",
            }
        ),
        encoding="utf-8",
    )


def _write_escalate_sentinel(scaffold: str) -> None:
    p = Path(scaffold) / SESSION_ESCALATE_SENTINEL_NAME
    p.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "session-escalate",
                "timestamp": "2026-04-27T00:00:00Z",
                "session_id": "test-sid",
                "reason": "other",
                "message": "test escalate",
                "suggested_action": None,
            }
        ),
        encoding="utf-8",
    )


def _write_both_sentinels(scaffold: str) -> None:
    _write_end_sentinel(scaffold)
    _write_escalate_sentinel(scaffold)


# ---------------------------------------------------------------------------
# Scaffold factory
# ---------------------------------------------------------------------------


def _build_scaffold(
    tmpdir: str,
    *,
    n_phases: int = 1,
    max_revisions: int = 3,
    bootstrap_state: bool = True,
    config_overrides: Optional[Dict[str, Any]] = None,
    bad_config: bool = False,
) -> Path:
    scaffold = Path(tmpdir)
    scaffold.mkdir(parents=True, exist_ok=True)

    plan_lines = []
    for i in range(1, n_phases + 1):
        plan_lines.append(f"## Phase {i}: phase-{i}-title")
        plan_lines.append(f"Paths: src/p{i}.py")
        plan_lines.append("")
    (scaffold / "PLAN.md").write_text("\n".join(plan_lines), encoding="utf-8")

    if bad_config:
        (scaffold / "verify-config.json").write_text(
            "{not valid json", encoding="utf-8"
        )
    else:
        wrapper_section = {
            "phase_max_wall_clock_seconds": 10,
            "sentinel_grace_seconds": 1,
            "poll_interval_seconds": 0.05,
            "max_anomalous_exits": 3,
            "model": "test-model",
            "max_turns_per_phase": 5,
            "remote_host": "localhost",
        }
        if config_overrides:
            wrapper_section.update(config_overrides)
        cfg = {
            "schema_version": "1.0",
            "verify_phase": {},
            "wrapper": wrapper_section,
        }
        (scaffold / "verify-config.json").write_text(
            json.dumps(cfg), encoding="utf-8"
        )

    if bootstrap_state:
        phases = [vs.PhaseSpec(id=i, title=f"phase-{i}-title")
                  for i in range(1, n_phases + 1)]
        state = vs.bootstrap(
            scaffold_root=str(scaffold),
            plan_md_path=str(scaffold / "PLAN.md"),
            phases=phases,
            max_revisions=max_revisions,
        )
        vs.save(state, scaffold / "verified-state.json")
    return scaffold


def _make_wrapper(
    scaffold: Path,
    factory: Callable[..., FakePopen],
    *,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> hm.Wrapper:
    cfg_path = scaffold / "verify-config.json"
    cfg = hm.load_wrapper_config(cfg_path if cfg_path.exists() else None)
    if config_overrides:
        for k, v in config_overrides.items():
            setattr(cfg, k, v)
    transport = hm.LocalFsTransport(hermes_factory=factory)
    return hm.Wrapper(
        scaffold_root=scaffold,
        transport=transport,
        wrapper_config=cfg,
    )


def _read_manifest(scaffold: Path) -> Dict[str, Any]:
    p = scaffold / ".session-archive" / "manifest.json"
    if not p.exists():
        return {"entries": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_phase_passed(
    scaffold: Path, phase_id: int, *, max_revisions: int = 3
) -> None:
    state = vs.load(scaffold / "verified-state.json")
    new_state = vs.record_verdict(
        state=state,
        phase_id=phase_id,
        passed=True,
        session_id=f"sid-phase-{phase_id}",
        tier_run=3,
        missing_paths=[],
        integrity_issues=[],
    )
    vs.save(new_state, scaffold / "verified-state.json")


def _write_phase_failed(
    scaffold: Path,
    phase_id: int,
    *,
    corrective: str = "fix it",
) -> None:
    state = vs.load(scaffold / "verified-state.json")
    new_state = vs.record_verdict(
        state=state,
        phase_id=phase_id,
        passed=False,
        session_id=f"sid-phase-{phase_id}-fail",
        tier_run=3,
        missing_paths=["src/missing.py"],
        integrity_issues=[],
        corrective_dispatch=corrective,
    )
    vs.save(new_state, scaffold / "verified-state.json")


# ---------------------------------------------------------------------------
# T1. Happy path: 3-phase advance through to success.
# ---------------------------------------------------------------------------


def test_T1_three_phase_advance_to_success():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=3)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)
            state = vs.load(sroot / "verified-state.json")
            active = next(
                (e.id for e in state.phase_state
                 if e.status != vs.PhaseStatus.VERIFIED_PASSED),
                None,
            )

            def action(s):
                if active is not None:
                    _write_phase_passed(Path(s), active)
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_SUCCESS, f"expected 0, got {rc}"
        manifest = _read_manifest(scaffold)
        decisions = [e.get("wrapper_decision") for e in manifest["entries"]
                     if e.get("attempt", 0) > 0]
        assert decisions == [
            hm.DECISION_ADVANCE, hm.DECISION_ADVANCE, hm.DECISION_SUCCESS
        ], f"unexpected decision sequence {decisions}"


# ---------------------------------------------------------------------------
# T2. Phase fails, parent revises, then passes.
# ---------------------------------------------------------------------------


def test_T2_phase_fails_then_revises_passes():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)
        attempts = {"n": 0}

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)
            attempts["n"] += 1
            n = attempts["n"]

            def action(s):
                if n == 1:
                    _write_phase_failed(Path(s), 1, corrective="re-dispatch p1")
                else:
                    _write_phase_passed(Path(s), 1)
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_SUCCESS, f"expected 0, got {rc}"
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert len(session_entries) == 2, (
            f"expected 2 session entries, got {len(session_entries)}"
        )
        assert session_entries[0]["wrapper_decision"] == hm.DECISION_REVISE
        assert session_entries[1]["wrapper_decision"] == hm.DECISION_SUCCESS


# ---------------------------------------------------------------------------
# T3. Parent escalates explicitly.
# ---------------------------------------------------------------------------


def test_T3_parent_escalates_explicitly():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=2)
        snapshot_before = (scaffold / "verified-state.json").read_text(
            encoding="utf-8"
        )

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                _write_escalate_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE, f"expected 2, got {rc}"
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert len(session_entries) == 1
        e = session_entries[0]
        assert e["exit_reason"] == hm.EXIT_REASON_ESCALATE
        assert e["wrapper_decision"] == hm.DECISION_ESCALATE
        after = (scaffold / "verified-state.json").read_text(encoding="utf-8")
        assert after == snapshot_before, "wrapper modified verified-state.json"


# ---------------------------------------------------------------------------
# T4. Phase fails repeatedly → escalate.
# ---------------------------------------------------------------------------


def test_T4_phase_fails_repeatedly_escalates():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1, max_revisions=2)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                _write_phase_failed(Path(s), 1, corrective="try again")
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE, f"expected 2, got {rc}"
        state = vs.load(scaffold / "verified-state.json")
        p1 = next(e for e in state.phase_state if e.id == 1)
        assert p1.revision_count >= 2


# ---------------------------------------------------------------------------
# T5. Hermes crashes mid-phase (non-zero exit, no sentinel).
# ---------------------------------------------------------------------------


def test_T5_hermes_crash_counted_as_anomalous():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            return FakePopen(str(scaffold_root), exit_code=42,
                             exit_after=0.1, sentinel_action=None)

        wrapper = _make_wrapper(scaffold, factory,
                                config_overrides={"max_anomalous_exits": 0})
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert any(e["exit_reason"] == hm.EXIT_REASON_CRASH
                   for e in session_entries)
        state = vs.load(scaffold / "verified-state.json")
        assert state.phase_state[0].status == vs.PhaseStatus.PENDING


# ---------------------------------------------------------------------------
# T6. Phase exceeds wall-clock → timeout.
# ---------------------------------------------------------------------------


def test_T6_timeout_kills_hermes():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            return FakePopen(str(scaffold_root), exit_code=0,
                             exit_after=999.0, sentinel_action=None)

        wrapper = _make_wrapper(
            scaffold, factory,
            config_overrides={
                "phase_max_wall_clock_seconds": 1,
                "max_anomalous_exits": 0,
            },
        )
        t0 = time.time()
        rc = wrapper.run()
        elapsed = time.time() - t0
        assert rc == hm.EXIT_ESCALATE
        assert elapsed < 10.0, f"timeout took too long: {elapsed:.1f}s"
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert any(e["exit_reason"] == hm.EXIT_REASON_TIMEOUT
                   for e in session_entries), (
            "no timeout entry; reasons: "
            f"{[e['exit_reason'] for e in session_entries]}"
        )


# ---------------------------------------------------------------------------
# T7. Hermes exits clean (0) with no sentinel → anomalous_exit.
# ---------------------------------------------------------------------------


def test_T7_clean_exit_no_sentinel_anomalous():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            return FakePopen(str(scaffold_root), exit_code=0,
                             exit_after=0.1, sentinel_action=None)

        wrapper = _make_wrapper(scaffold, factory,
                                config_overrides={"max_anomalous_exits": 0})
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert any(e["exit_reason"] == hm.EXIT_REASON_ANOMALOUS
                   for e in session_entries), (
            "no anomalous_exit entry; reasons: "
            f"{[e['exit_reason'] for e in session_entries]}"
        )


# ---------------------------------------------------------------------------
# T8. anomalous_exit_count > max_anomalous_exits → escalate.
# ---------------------------------------------------------------------------


def test_T8_anomalous_exit_threshold_escalates():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            return FakePopen(str(scaffold_root), exit_code=0,
                             exit_after=0.1, sentinel_action=None)

        wrapper = _make_wrapper(scaffold, factory,
                                config_overrides={"max_anomalous_exits": 2})
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        # Need anomalous_exit_count > 2, so at least 3 anomalous sessions.
        assert len(session_entries) >= 3, (
            f"expected >=3 sessions before escalate, got {len(session_entries)}"
        )


# ---------------------------------------------------------------------------
# T9. hermes-multi resume after escalate-pause.
# ---------------------------------------------------------------------------


def test_T9_resume_after_escalate_pause():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory_1(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.3,
                sentinel_action=_write_escalate_sentinel, sentinel_at=0.05,
            )

        wrapper_1 = _make_wrapper(scaffold, factory_1)
        rc_1 = wrapper_1.run()
        assert rc_1 == hm.EXIT_ESCALATE

        def factory_2(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                _write_phase_passed(Path(s), 1)
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.3,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper_2 = _make_wrapper(scaffold, factory_2)
        rc_2 = wrapper_2.resume()
        assert rc_2 == hm.EXIT_SUCCESS, f"resume expected 0, got {rc_2}"


# ---------------------------------------------------------------------------
# T10. Wrapper-internal error: transport raises mid-run.
# ---------------------------------------------------------------------------


def test_T10_wrapper_internal_error_exits_3():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def bad_factory(**kwargs):
            raise OSError("simulated transport failure")

        wrapper = _make_wrapper(scaffold, bad_factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_WRAPPER_ERROR, f"expected 3, got {rc}"
        manifest = _read_manifest(scaffold)
        assert any(e.get("wrapper_decision") == hm.DECISION_WRAPPER_ERROR
                   for e in manifest["entries"]), (
            "no wrapper_error entry in manifest"
        )


# ---------------------------------------------------------------------------
# T11. Malformed verify-config.json → exit 4.
# ---------------------------------------------------------------------------


def test_T11_malformed_config_exits_4():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1, bad_config=True)
        try:
            hm.load_wrapper_config(scaffold / "verify-config.json")
            raise AssertionError("expected ConfigError")
        except hm.ConfigError:
            pass
        rc = hm.main(["run", str(scaffold)])
        assert rc == hm.EXIT_CONFIG_ERROR, f"expected 4, got {rc}"


# ---------------------------------------------------------------------------
# T12. status subcommand prints summary.
# ---------------------------------------------------------------------------


def test_T12_status_after_run():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                _write_phase_passed(Path(s), 1)
                _write_end_sentinel(s)
            return FakePopen(str(sroot), exit_code=0, exit_after=0.3,
                             sentinel_action=action, sentinel_at=0.05)

        wrapper = _make_wrapper(scaffold, factory)
        wrapper.run()

        from io import StringIO
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = hm._cmd_status(scaffold)
        finally:
            sys.stdout = old
        out = buf.getvalue()
        assert rc == hm.EXIT_SUCCESS
        assert "verified-state.json:" in out
        assert "manifest entries:" in out
        assert "scaffold_root:" in out


# ---------------------------------------------------------------------------
# T13. Sentinel grace timer: sentinel fires, hermes still running → SIGTERM.
# ---------------------------------------------------------------------------


def test_T13_sentinel_grace_then_kill():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                _write_phase_passed(Path(s), 1)
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=999.0,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(
            scaffold, factory,
            config_overrides={
                "sentinel_grace_seconds": 1,
                "phase_max_wall_clock_seconds": 30,
            },
        )
        t0 = time.time()
        rc = wrapper.run()
        elapsed = time.time() - t0
        assert rc == hm.EXIT_SUCCESS, f"expected 0, got {rc}"
        assert elapsed < 10.0, f"grace path too slow: {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# T14. Manifest atomicity under os.replace failure.
# ---------------------------------------------------------------------------


def test_T14_manifest_atomicity_on_replace_failure():
    with tempfile.TemporaryDirectory() as d:
        scaffold = Path(d)
        archive = scaffold / ".session-archive"
        archive.mkdir(parents=True, exist_ok=True)
        manifest_path = archive / "manifest.json"
        manifest_path.write_text(
            json.dumps({"schema_version": "1.0", "entries": []}),
            encoding="utf-8",
        )
        before = manifest_path.read_text(encoding="utf-8")

        target_name = manifest_path.name

        def fake_replace(src, dst):
            if Path(dst).name == target_name:
                raise OSError("simulated replace failure")
            # Fallback to real os.replace for other callers (none expected).
            os.replace.__wrapped__(src, dst)  # pragma: no cover

        raised = False
        with mock.patch("hermes_multi.os.replace", side_effect=fake_replace):
            try:
                hm._atomic_write_json(manifest_path,
                                      {"schema_version": "1.0",
                                       "entries": [{"x": 1}]})
            except OSError:
                raised = True
        assert raised, "atomic write should have raised"
        after = manifest_path.read_text(encoding="utf-8")
        assert after == before, "manifest was modified despite replace failure"
        leftovers = [p for p in archive.iterdir()
                     if p.name.startswith(target_name + ".")
                     and p.suffix == ".tmp"]
        assert not leftovers, f"leftover temp files: {leftovers}"


# ---------------------------------------------------------------------------
# T15. Bootstrap on first run (no verified-state.json present).
# ---------------------------------------------------------------------------


def test_T15_bootstrap_on_first_run():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=2, bootstrap_state=False)
        assert not (scaffold / "verified-state.json").exists()

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)
            state = vs.load(sroot / "verified-state.json")
            active = next(
                (e.id for e in state.phase_state
                 if e.status != vs.PhaseStatus.VERIFIED_PASSED),
                None,
            )

            def action(s):
                if active is not None:
                    _write_phase_passed(Path(s), active)
                _write_end_sentinel(s)
            return FakePopen(str(sroot), exit_code=0, exit_after=0.3,
                             sentinel_action=action, sentinel_at=0.05)

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_SUCCESS
        state = vs.load(scaffold / "verified-state.json")
        assert len(state.phase_state) == 2
        assert all(p.status == vs.PhaseStatus.VERIFIED_PASSED
                   for p in state.phase_state)


# ---------------------------------------------------------------------------
# T16. Both end + escalate sentinels written → escalate (priority).
# ---------------------------------------------------------------------------


def test_T16_both_sentinels_treated_as_escalate():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)
            return FakePopen(str(sroot), exit_code=0, exit_after=0.3,
                             sentinel_action=_write_both_sentinels,
                             sentinel_at=0.05)

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE, f"expected 2, got {rc}"
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert len(session_entries) == 1
        e = session_entries[0]
        assert e["sentinel_kind"] == "both", (
            f"got sentinel_kind={e['sentinel_kind']!r}"
        )
        assert e["exit_reason"] == hm.EXIT_REASON_ESCALATE
        assert e["wrapper_decision"] == hm.DECISION_ESCALATE


# ---------------------------------------------------------------------------
# Invariant: wrapper does not mutate verified-state.json during a session.
# ---------------------------------------------------------------------------


def test_invariant_wrapper_does_not_mutate_verified_state_during_session():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=1)
        before = (scaffold / "verified-state.json").read_text(encoding="utf-8")

        def factory(*, scaffold_root, **kwargs):
            return FakePopen(str(scaffold_root), exit_code=0,
                             exit_after=0.1, sentinel_action=None)

        wrapper = _make_wrapper(scaffold, factory,
                                config_overrides={"max_anomalous_exits": 0})
        wrapper.run()
        after = (scaffold / "verified-state.json").read_text(encoding="utf-8")
        # When verify_phase did not run, the wrapper must not have touched
        # the state file.
        assert after == before, (
            "wrapper mutated verified-state.json during anomalous-exit session"
        )


# ---------------------------------------------------------------------------
# Bootstrap-mode helpers
# ---------------------------------------------------------------------------


def _build_bootstrap_scaffold(
    tmpdir: str,
    *,
    user_prompt: str = "Build an export feature with CSV/JSON/PDF.",
    include_user_prompt: bool = True,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Path:
    """Build a scaffold for bootstrap-mode tests.

    Mirrors `_build_scaffold` but omits PLAN.md + verified-state.json
    (those are bootstrap session outputs / post-bootstrap seeds).
    Optionally writes USER-PROMPT.md.
    """
    scaffold = Path(tmpdir)
    scaffold.mkdir(parents=True, exist_ok=True)
    if include_user_prompt:
        (scaffold / "USER-PROMPT.md").write_text(user_prompt, encoding="utf-8")
    wrapper_section = {
        "phase_max_wall_clock_seconds": 10,
        "sentinel_grace_seconds": 1,
        "poll_interval_seconds": 0.05,
        "max_anomalous_exits": 3,
        "model": "test-model",
        "max_turns_per_phase": 5,
        "remote_host": "localhost",
    }
    if config_overrides:
        wrapper_section.update(config_overrides)
    (scaffold / "verify-config.json").write_text(
        json.dumps({"schema_version": "1.0",
                    "verify_phase": {},
                    "wrapper": wrapper_section}),
        encoding="utf-8",
    )
    return scaffold


def _make_plan_md_text(n_phases: int = 2) -> str:
    lines = []
    for i in range(1, n_phases + 1):
        lines.append(f"## Phase {i}: bootstrap-phase-{i}")
        lines.append(f"Paths: src/p{i}.py")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# T18. Bootstrap success → PLAN.md written; phase loop completes.
# ---------------------------------------------------------------------------


def test_T18_bootstrap_success_then_phase_loop():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_bootstrap_scaffold(d)
        # Pre-conditions: PLAN.md absent, USER-PROMPT.md present.
        assert not (scaffold / "PLAN.md").exists()
        assert (scaffold / "USER-PROMPT.md").exists()
        assert not (scaffold / "verified-state.json").exists()

        call_count = {"n": 0}

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)
            call_count["n"] += 1
            n = call_count["n"]

            if n == 1:
                # Bootstrap session: write PLAN.md (2 phases) + end-sentinel.
                def action(s):
                    (Path(s) / "PLAN.md").write_text(
                        _make_plan_md_text(2), encoding="utf-8"
                    )
                    _write_end_sentinel(s)
                return FakePopen(
                    str(sroot), exit_code=0, exit_after=0.4,
                    sentinel_action=action, sentinel_at=0.05,
                )

            # Phase sessions: state has been seeded between sessions.
            state = vs.load(sroot / "verified-state.json")
            active = next(
                (e.id for e in state.phase_state
                 if e.status != vs.PhaseStatus.VERIFIED_PASSED),
                None,
            )

            def action(s):
                if active is not None:
                    _write_phase_passed(Path(s), active)
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_SUCCESS, f"expected 0, got {rc}"

        manifest = _read_manifest(scaffold)
        entries = manifest["entries"]

        # Bootstrap entry: phase_id is null, session_kind=bootstrap.
        bootstrap_entries = [e for e in entries
                             if e.get("session_kind") == "bootstrap"]
        assert len(bootstrap_entries) == 1, (
            f"expected exactly 1 bootstrap entry, got {len(bootstrap_entries)}"
        )
        be = bootstrap_entries[0]
        assert be["phase_id"] is None, f"phase_id should be null, got {be['phase_id']!r}"
        assert be["wrapper_decision"] == hm.DECISION_ADVANCE
        assert be["exit_reason"] == hm.EXIT_REASON_END
        assert "pre-bootstrap" in be["verify_state_snapshot"], be["verify_state_snapshot"]

        # Phase entries: 2 phases, both with attempt>0.
        session_entries = [e for e in entries if e.get("attempt", 0) > 0
                           and e.get("session_kind") != "bootstrap"]
        decisions = [e.get("wrapper_decision") for e in session_entries]
        assert decisions == [hm.DECISION_ADVANCE, hm.DECISION_SUCCESS], (
            f"unexpected phase decisions: {decisions}"
        )

        # Final: PLAN.md exists, verified-state seeded, all phases passed.
        assert (scaffold / "PLAN.md").exists()
        final_state = vs.load(scaffold / "verified-state.json")
        assert all(p.status == vs.PhaseStatus.VERIFIED_PASSED
                   for p in final_state.phase_state)


# ---------------------------------------------------------------------------
# T19. Bootstrap end-sentinel fires but PLAN.md never written.
# ---------------------------------------------------------------------------


def test_T19_bootstrap_no_plan_escalates():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_bootstrap_scaffold(d)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                # Parent claims completion via end-sentinel but never writes
                # PLAN.md. This is the bootstrap-shape fabrication failure.
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE, f"expected 2, got {rc}"
        assert not (scaffold / "PLAN.md").exists()
        # verified-state.json must NOT be created when bootstrap fails.
        assert not (scaffold / "verified-state.json").exists()

        manifest = _read_manifest(scaffold)
        bootstrap_entries = [e for e in manifest["entries"]
                             if e.get("session_kind") == "bootstrap"]
        assert len(bootstrap_entries) == 1
        be = bootstrap_entries[0]
        assert be["phase_id"] is None
        assert be["wrapper_decision"] == hm.DECISION_ESCALATE
        assert be.get("reason") == hm.BOOTSTRAP_FAILED_NO_PLAN, (
            f"expected reason={hm.BOOTSTRAP_FAILED_NO_PLAN!r}, "
            f"got {be.get('reason')!r}"
        )


# ---------------------------------------------------------------------------
# T20. Bootstrap writes PLAN.md but it has no parseable phase headers.
# ---------------------------------------------------------------------------


def test_T20_bootstrap_unparseable_plan_escalates():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_bootstrap_scaffold(d)

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                # Empty/no-headers PLAN.md → parse_plan_md raises ToolError.
                (Path(s) / "PLAN.md").write_text(
                    "# Random notes\n\n(no phase blocks here)\n",
                    encoding="utf-8",
                )
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.4,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_ESCALATE, f"expected 2, got {rc}"
        # PLAN.md got written by parent but is unusable.
        assert (scaffold / "PLAN.md").exists()
        # verified-state.json must NOT be created on parse-failure path.
        assert not (scaffold / "verified-state.json").exists()

        manifest = _read_manifest(scaffold)
        bootstrap_entries = [e for e in manifest["entries"]
                             if e.get("session_kind") == "bootstrap"]
        assert len(bootstrap_entries) == 1
        be = bootstrap_entries[0]
        assert be["phase_id"] is None
        assert be["wrapper_decision"] == hm.DECISION_ESCALATE
        # Reason starts with the unparseable code; the parser's message is
        # appended after a colon.
        reason = be.get("reason", "")
        assert reason.startswith(hm.BOOTSTRAP_FAILED_UNPARSEABLE_PLAN), (
            f"expected reason starting with "
            f"{hm.BOOTSTRAP_FAILED_UNPARSEABLE_PLAN!r}, got {reason!r}"
        )


# ---------------------------------------------------------------------------
# T21. Regression: PLAN.md present at run-start → bootstrap is skipped.
# ---------------------------------------------------------------------------


def test_T21_existing_plan_md_skips_bootstrap():
    with tempfile.TemporaryDirectory() as d:
        # Use the existing scaffold builder: PLAN.md AND verified-state.json
        # are both present.
        scaffold = _build_scaffold(d, n_phases=1)
        # Sanity: USER-PROMPT.md is NOT present (existing flow has no need).
        assert not (scaffold / "USER-PROMPT.md").exists()

        def factory(*, scaffold_root, **kwargs):
            sroot = Path(scaffold_root)

            def action(s):
                _write_phase_passed(Path(s), 1)
                _write_end_sentinel(s)
            return FakePopen(
                str(sroot), exit_code=0, exit_after=0.3,
                sentinel_action=action, sentinel_at=0.05,
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_SUCCESS

        manifest = _read_manifest(scaffold)
        # Confirm: zero bootstrap entries — wrapper never launched bootstrap.
        bootstrap_entries = [e for e in manifest["entries"]
                             if e.get("session_kind") == "bootstrap"]
        assert len(bootstrap_entries) == 0, (
            f"expected no bootstrap entries on existing-PLAN.md path, "
            f"got {len(bootstrap_entries)}"
        )
        # And exactly one phase-1 entry with success.
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        assert len(session_entries) == 1
        assert session_entries[0]["phase_id"] == 1
        assert session_entries[0]["wrapper_decision"] == hm.DECISION_SUCCESS


# ---------------------------------------------------------------------------
# T22. No PLAN.md, no USER-PROMPT.md → exit 4 (config error). No launch.
# ---------------------------------------------------------------------------


def test_T22_missing_user_prompt_exits_config_error():
    with tempfile.TemporaryDirectory() as d:
        # Bootstrap-shaped scaffold but WITHOUT USER-PROMPT.md.
        scaffold = _build_bootstrap_scaffold(d, include_user_prompt=False)
        assert not (scaffold / "PLAN.md").exists()
        assert not (scaffold / "USER-PROMPT.md").exists()

        launches = {"n": 0}

        def factory(**kwargs):
            launches["n"] += 1
            raise AssertionError(
                "wrapper must NOT launch Hermes when both PLAN.md and "
                "USER-PROMPT.md are absent"
            )

        wrapper = _make_wrapper(scaffold, factory)
        rc = wrapper.run()
        assert rc == hm.EXIT_CONFIG_ERROR, f"expected 4, got {rc}"
        assert launches["n"] == 0, "no Hermes launch should have occurred"
        # No scaffold mutation.
        assert not (scaffold / "PLAN.md").exists()
        assert not (scaffold / "verified-state.json").exists()


# ---------------------------------------------------------------------------
# T23. LocalProcessTransport file operations.
# ---------------------------------------------------------------------------


def test_T23_local_process_transport_file_ops():
    with tempfile.TemporaryDirectory() as d:
        scaffold = Path(d)
        transport = hm.LocalProcessTransport()

        # write_file → file present + correct content.
        f1 = scaffold / "f1.txt"
        transport.write_file(str(f1), "hello\nworld\n")
        assert f1.exists()
        assert f1.read_text(encoding="utf-8") == "hello\nworld\n"

        # read_file roundtrip.
        assert transport.read_file(str(f1)) == "hello\nworld\n"

        # file_exists positive.
        assert transport.file_exists(str(f1)) is True

        # write_file creates parent dirs.
        f2 = scaffold / "nested" / "subdir" / "f2.txt"
        transport.write_file(str(f2), "deep")
        assert f2.exists() and f2.read_text(encoding="utf-8") == "deep"

        # list_dir → sorted basenames.
        listing = transport.list_dir(str(scaffold))
        assert "f1.txt" in listing
        assert "nested" in listing
        assert listing == sorted(listing)

        # remove_file → gone.
        transport.remove_file(str(f1))
        assert not f1.exists()
        assert transport.file_exists(str(f1)) is False

        # remove_file on missing path is a no-op.
        transport.remove_file(str(scaffold / "does-not-exist"))

        # list_dir on missing path → [].
        assert transport.list_dir(str(scaffold / "no-such")) == []


# ---------------------------------------------------------------------------
# T24. LocalProcessTransport.launch_hermes via fake binary.
# ---------------------------------------------------------------------------


def test_T24_local_process_transport_launch_hermes():
    """launch_hermes Popens a real subprocess with env + cwd honored."""
    import subprocess as _sp

    with tempfile.TemporaryDirectory() as d:
        scaffold = Path(d)

        # Fake binary: a Python script that echoes argv + an env var to
        # stdout, then exits 0. Marked executable.
        fake_bin = scaffold / "fake-hermes"
        fake_bin.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "print('argv=' + repr(sys.argv))\n"
            "print('OMLX_API_KEY=' + os.environ.get('OMLX_API_KEY', ''))\n"
            "print('cwd=' + os.getcwd())\n"
            "sys.exit(0)\n",
            encoding="utf-8",
        )
        os.chmod(fake_bin, 0o755)

        # cwd target: a separate dir we can identify.
        fake_cwd = scaffold / "hermes-home"
        fake_cwd.mkdir()

        transport = hm.LocalProcessTransport(
            hermes_path=str(fake_bin),
            hermes_cwd=str(fake_cwd),
        )

        stdout_path = str(scaffold / "fake.stdout")
        stderr_path = str(scaffold / "fake.stderr")

        popen = transport.launch_hermes(
            scaffold_root=str(scaffold),
            source_tag="t24-source",
            prompt="test prompt",
            model="test-model",
            max_turns=5,
            omlx_api_key="t24-secret",
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )

        # Returns a Popen.
        assert isinstance(popen, _sp.Popen)

        # Process drains promptly.
        rc = popen.wait(timeout=10.0)
        assert rc == 0, f"fake binary exited {rc}"

        out = Path(stdout_path).read_text(encoding="utf-8")
        # cwd was honored. macOS /var → /private/var symlink, so compare
        # via realpath rather than literal substring.
        cwd_line = next(
            (line[len("cwd="):] for line in out.splitlines()
             if line.startswith("cwd=")),
            None,
        )
        assert cwd_line is not None, out
        assert os.path.realpath(cwd_line) == os.path.realpath(str(fake_cwd)), (
            f"cwd_line={cwd_line!r} fake_cwd={fake_cwd!r}"
        )
        # OMLX_API_KEY was passed through env.
        assert "OMLX_API_KEY=t24-secret" in out, out
        # argv contains hermes-style flags + the prompt + source tag.
        assert "'chat'" in out, out
        assert "'-q'" in out and "'test prompt'" in out, out
        assert "'-m'" in out and "'test-model'" in out, out
        assert "'--source'" in out and "'t24-source'" in out, out
        assert "'--max-turns'" in out and "'5'" in out, out


# ---------------------------------------------------------------------------
# T25. End-to-end happy path through LocalProcessTransport with a fake binary.
# ---------------------------------------------------------------------------


def _write_fake_hermes_binary_for_e2e(scaffold: Path) -> Path:
    """Write a small Python "hermes" script that drives the test scenario.

    On each invocation it:
      1. parses argv to find --source <scaffold_root>
      2. reads verified-state.json from that scaffold
      3. records a passed verdict for the active phase via verified_state
      4. drops a session-end sentinel
      5. exits 0

    This is the LocalProcessTransport analog of T1's FakePopen factory.
    """
    bin_path = scaffold / "fake-hermes-e2e"
    repo_dir = str(Path(__file__).resolve().parent)
    body = f"""#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, {repo_dir!r})
import verified_state as vs
from handoff_tools import (
    SESSION_END_SENTINEL_NAME,
)

argv = sys.argv
src_idx = argv.index('--source') if '--source' in argv else -1
if src_idx == -1 or src_idx + 1 >= len(argv):
    print('FAKE-HERMES: missing --source', file=sys.stderr)
    sys.exit(2)
scaffold_root = argv[src_idx + 1]
vs_path = os.path.join(scaffold_root, 'verified-state.json')
state = vs.load(vs_path)
active = None
for entry in state.phase_state:
    if entry.status != vs.PhaseStatus.VERIFIED_PASSED:
        active = entry.id
        break
if active is None:
    print('FAKE-HERMES: no active phase', file=sys.stderr)
    sys.exit(0)

new_state = vs.record_verdict(
    state=state,
    phase_id=active,
    passed=True,
    session_id='t25-sid-' + str(active),
    tier_run=3,
    missing_paths=[],
    integrity_issues=[],
)
vs.save(new_state, vs_path)

sentinel_path = os.path.join(scaffold_root, SESSION_END_SENTINEL_NAME)
with open(sentinel_path, 'w', encoding='utf-8') as f:
    json.dump({{
        'schema_version': '1.0',
        'kind': 'session-end',
        'timestamp': '2026-04-27T00:00:00Z',
        'session_id': 't25-sid-' + str(active),
        'completed_phase': active,
        'parent_intent_log': None,
        'parent_summary': '',
    }}, f)

print('FAKE-HERMES: phase', active, 'passed')
sys.exit(0)
"""
    bin_path.write_text(body, encoding="utf-8")
    os.chmod(bin_path, 0o755)
    return bin_path


def test_T25_wrapper_end_to_end_with_local_process_transport():
    with tempfile.TemporaryDirectory() as d:
        scaffold = _build_scaffold(d, n_phases=2)

        # Fake binary writes verdicts + sentinel for the active phase.
        fake_bin = _write_fake_hermes_binary_for_e2e(scaffold)

        # cwd doesn't matter for the fake binary; reuse scaffold.
        transport = hm.LocalProcessTransport(
            hermes_path=str(fake_bin),
            hermes_cwd=str(scaffold),
        )

        cfg_path = scaffold / "verify-config.json"
        cfg = hm.load_wrapper_config(cfg_path if cfg_path.exists() else None)
        # Tighten timing for fast test.
        cfg.poll_interval_seconds = 0.05
        cfg.sentinel_grace_seconds = 1
        cfg.phase_max_wall_clock_seconds = 30

        wrapper = hm.Wrapper(
            scaffold_root=scaffold,
            transport=transport,
            wrapper_config=cfg,
        )

        rc = wrapper.run()
        assert rc == hm.EXIT_SUCCESS, f"expected 0, got {rc}"

        # verified-state.json: both phases passed.
        final_state = vs.load(scaffold / "verified-state.json")
        assert all(p.status == vs.PhaseStatus.VERIFIED_PASSED
                   for p in final_state.phase_state)

        # manifest captured both attempts plus terminal SUCCESS.
        manifest = _read_manifest(scaffold)
        session_entries = [e for e in manifest["entries"]
                           if e.get("attempt", 0) > 0]
        decisions = [e.get("wrapper_decision") for e in session_entries]
        assert decisions == [hm.DECISION_ADVANCE, hm.DECISION_SUCCESS], (
            f"unexpected decisions: {decisions}"
        )
        # Stdout log was written by the fake binary.
        archive = scaffold / ".session-archive"
        stdout_logs = list(archive.glob("phase-*-attempt-*.stdout.log"))
        assert stdout_logs, "no per-attempt stdout logs archived"
        joined = "\n".join(p.read_text(encoding="utf-8") for p in stdout_logs)
        assert "FAKE-HERMES: phase 1 passed" in joined, joined
        assert "FAKE-HERMES: phase 2 passed" in joined, joined


# ---------------------------------------------------------------------------
# T26. LocalProcessTransport.launch_hermes injects scaffold venv site-packages
# into PYTHONPATH (B1 fix for tier-2 import resolution gap).
# ---------------------------------------------------------------------------


def _write_pythonpath_echo_binary(scaffold: Path) -> Path:
    """Fake hermes binary that echoes PYTHONPATH to stdout, then exits 0."""
    fake_bin = scaffold / "fake-hermes-pp"
    fake_bin.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "print('PYTHONPATH=' + os.environ.get('PYTHONPATH', ''))\n"
        "print('HAS_PYTHONPATH=' + ('1' if 'PYTHONPATH' in os.environ else '0'))\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    os.chmod(fake_bin, 0o755)
    return fake_bin


def _launch_and_read(transport, scaffold: Path, stdout_name: str) -> str:
    stdout_path = str(scaffold / stdout_name)
    stderr_path = str(scaffold / (stdout_name + ".err"))
    popen = transport.launch_hermes(
        scaffold_root=str(scaffold),
        source_tag="t26-source",
        prompt="test prompt",
        model="test-model",
        max_turns=1,
        omlx_api_key=None,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    rc = popen.wait(timeout=10.0)
    assert rc == 0, f"fake binary exited {rc}"
    return Path(stdout_path).read_text(encoding="utf-8")


def test_T26_local_process_transport_pythonpath_injection():
    """launch_hermes prepends scaffold/.venv site-packages to PYTHONPATH."""
    import unittest.mock as _mock

    # --- Case 1: injection happens when scaffold/.venv site-packages exists.
    with tempfile.TemporaryDirectory() as d:
        scaffold = Path(d)
        site_packages = scaffold / ".venv" / "lib" / "python3.12" / "site-packages"
        site_packages.mkdir(parents=True)

        fake_bin = _write_pythonpath_echo_binary(scaffold)
        fake_cwd = scaffold / "hermes-home"
        fake_cwd.mkdir()
        transport = hm.LocalProcessTransport(
            hermes_path=str(fake_bin),
            hermes_cwd=str(fake_cwd),
        )

        # Ensure parent has no PYTHONPATH for the cleanest assertion.
        with _mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PYTHONPATH", None)
            out = _launch_and_read(transport, scaffold, "case1.stdout")

        pp_line = next(
            (line[len("PYTHONPATH="):] for line in out.splitlines()
             if line.startswith("PYTHONPATH=")),
            None,
        )
        assert pp_line is not None, out
        assert str(site_packages) in pp_line, (
            f"expected {site_packages} in PYTHONPATH, got {pp_line!r}"
        )
        # No trailing colon when there was no preexisting PYTHONPATH.
        assert pp_line == str(site_packages), (
            f"expected exact match (no trailing :), got {pp_line!r}"
        )

    # --- Case 2: no-op when scaffold/.venv is absent.
    with tempfile.TemporaryDirectory() as d:
        scaffold = Path(d)
        # Deliberately do NOT create .venv/.
        fake_bin = _write_pythonpath_echo_binary(scaffold)
        fake_cwd = scaffold / "hermes-home"
        fake_cwd.mkdir()
        transport = hm.LocalProcessTransport(
            hermes_path=str(fake_bin),
            hermes_cwd=str(fake_cwd),
        )

        # Snapshot whatever the test-runner currently has for PYTHONPATH.
        runner_pp = os.environ.get("PYTHONPATH", None)

        out = _launch_and_read(transport, scaffold, "case2.stdout")
        pp_line = next(
            (line[len("PYTHONPATH="):] for line in out.splitlines()
             if line.startswith("PYTHONPATH=")),
            None,
        )
        has_pp_line = next(
            (line[len("HAS_PYTHONPATH="):] for line in out.splitlines()
             if line.startswith("HAS_PYTHONPATH=")),
            None,
        )
        assert pp_line is not None, out
        assert has_pp_line is not None, out
        if runner_pp is None:
            # Parent had no PYTHONPATH; child should also lack it.
            assert has_pp_line == "0", (
                f"expected unset PYTHONPATH; got HAS={has_pp_line} VAL={pp_line!r}"
            )
        else:
            # Parent had one; child should see it unchanged.
            assert pp_line == runner_pp, (
                f"expected unchanged PYTHONPATH={runner_pp!r}, got {pp_line!r}"
            )

    # --- Case 3: prepend to an existing PYTHONPATH.
    with tempfile.TemporaryDirectory() as d:
        scaffold = Path(d)
        site_packages = scaffold / ".venv" / "lib" / "python3.10" / "site-packages"
        site_packages.mkdir(parents=True)

        fake_bin = _write_pythonpath_echo_binary(scaffold)
        fake_cwd = scaffold / "hermes-home"
        fake_cwd.mkdir()
        transport = hm.LocalProcessTransport(
            hermes_path=str(fake_bin),
            hermes_cwd=str(fake_cwd),
        )

        preexisting = "/some/preexisting/path"
        with _mock.patch.dict(
            os.environ, {"PYTHONPATH": preexisting}, clear=False
        ):
            out = _launch_and_read(transport, scaffold, "case3.stdout")

        pp_line = next(
            (line[len("PYTHONPATH="):] for line in out.splitlines()
             if line.startswith("PYTHONPATH=")),
            None,
        )
        assert pp_line is not None, out
        expected = f"{site_packages}:{preexisting}"
        assert pp_line == expected, (
            f"expected {expected!r}, got {pp_line!r}"
        )


# ---------------------------------------------------------------------------
# Plain-script entry point.
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
            import traceback
            failed.append((name, repr(exc)))
            print(f"ERROR {name}: {exc!r}")
            traceback.print_exc()
    print()
    print(f"{len(tests) - len(failed)}/{len(tests)} passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(_run_all())
