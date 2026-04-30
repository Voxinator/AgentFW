"""test_probe_r7_11.py — Tests for probe-r7.11-stage.sh / probe-r7.11-unstage.sh.

Strategy: build a mock VM-shape directory in a Python tempdir, run the bash
scripts against it via FIXTURE_ROOT env override, assert pre/post state.

The FIXTURE_ROOT abstraction in the bash scripts switches the SSH/scp
machinery to plain bash/cp against a local directory, so no VM access is
needed. CANONICAL_HERMES_MD / CANONICAL_RUN_AGENT env vars override the
canonical-md5 pre-flight check to match the fixture-generated content.

Run with: `python3 test_probe_r7_11.py`
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
STAGE = SCRIPT_DIR / "probe-r7.11-stage.sh"
UNSTAGE = SCRIPT_DIR / "probe-r7.11-unstage.sh"

# Real source files we expect on disk (Mac side). Used for import-rewrite test.
SRC_VERIFIED_STATE = SCRIPT_DIR / "verified_state.py"
SRC_VERIFY_PHASE = SCRIPT_DIR / "verify_phase.py"
SRC_VERIFY_PHASE_TOOL = SCRIPT_DIR / "verify_phase_tool.py"
SRC_HANDOFF_TOOLS = SCRIPT_DIR / "handoff_tools.py"
# r7.10 minimum-mechanism source — staged by Phase 4.5 (item 8 trial 1 fix).
SRC_WRITE_PLAN_MD = (
    SCRIPT_DIR.parent / "r7.10" / "write_plan_md.py.r7.10-min"
)


def md5_file(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def make_fixture(tmpdir: Path) -> dict:
    """Build a mock VM tree under tmpdir and return md5s of canonical files."""
    agent = tmpdir / ".hermes" / "hermes-agent"
    tools_dir = agent / "tools"
    tools_dir.mkdir(parents=True)

    # Stub HERMES.md and run_agent.py — content arbitrary; we record their md5s
    # and pass them to the script so pre-flight passes.
    hermes_md = agent / "HERMES.md"
    hermes_md.write_text("# fixture HERMES.md — not the real canonical\n")
    run_agent = agent / "run_agent.py"
    run_agent.write_text("# fixture run_agent.py\n")

    # Stub toolsets.py with the _HERMES_CORE_TOOLS list shape the patcher needs.
    toolsets_py = agent / "toolsets.py"
    toolsets_py.write_text(
        textwrap.dedent('''\
            """fixture toolsets.py."""

            _HERMES_CORE_TOOLS = [
                "web_search", "web_extract",
                "terminal", "process",
                "todo", "memory",
                "execute_code", "delegate_task", "delegate_worker",
            ]


            TOOLSETS = {
                "hermes-cli": {
                    "tools": _HERMES_CORE_TOOLS,
                },
            }
            ''')
    )

    # Stub model_tools.py with the explicit-import-list anchor.
    model_tools_py = agent / "model_tools.py"
    model_tools_py.write_text(
        textwrap.dedent('''\
            """fixture model_tools.py."""

            _TOOL_MODULES = [
                "tools.web_tools",
                "tools.terminal_tool",
                "tools.todo_tool",
                "tools.delegate_task",
                "tools.delegate_worker",
            ]
            ''')
    )

    # Empty tools/__init__.py so it's a package
    (tools_dir / "__init__.py").write_text("")
    # An existing tool to ensure we don't collide
    (tools_dir / "delegate_worker.py").write_text(
        "# fixture existing tool\n"
    )

    return {
        "hermes_md_md5": md5_file(hermes_md),
        "run_agent_md5": md5_file(run_agent),
        "toolsets_md5": md5_file(toolsets_py),
        "model_tools_md5": md5_file(model_tools_py),
        "agent_dir": agent,
    }


def run_script(script: Path, *args, fixture_root: Path,
               canonical_h: str, canonical_r: str,
               check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["FIXTURE_ROOT"] = str(fixture_root)
    env["CANONICAL_HERMES_MD"] = canonical_h
    env["CANONICAL_RUN_AGENT"] = canonical_r
    return subprocess.run(
        ["bash", str(script), *args],
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


class TestStageUnstage(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self.tmp.name)
        meta = make_fixture(self.tmpdir)
        self.canon_h = meta["hermes_md_md5"]
        self.canon_r = meta["run_agent_md5"]
        self.toolsets_md5_pre = meta["toolsets_md5"]
        self.model_tools_md5_pre = meta["model_tools_md5"]
        self.agent = meta["agent_dir"]

    def tearDown(self):
        self.tmp.cleanup()

    def _run_stage(self, *args, check=True):
        return run_script(
            STAGE, *args,
            fixture_root=self.tmpdir,
            canonical_h=self.canon_h,
            canonical_r=self.canon_r,
            check=check,
        )

    def _run_unstage(self, *args, check=True):
        return run_script(
            UNSTAGE, *args,
            fixture_root=self.tmpdir,
            canonical_h=self.canon_h,
            canonical_r=self.canon_r,
            check=check,
        )

    # ------------------------------------------------------------------
    # T1: stage on a clean fixture → expected files created, py_compile OK
    # ------------------------------------------------------------------
    def test_T1_stage_clean(self):
        result = self._run_stage("stage")
        self.assertEqual(result.returncode, 0,
                         msg=f"stage failed: {result.stderr}")
        # Lib dir + 5 files
        lib_dir = self.agent / "tools" / "r7_11_lib"
        self.assertTrue(lib_dir.is_dir(), "r7_11_lib/ not created")
        for name in ["__init__.py", "verified_state.py", "verify_phase.py",
                     "verify_phase_tool.py", "handoff_tools.py"]:
            self.assertTrue((lib_dir / name).is_file(),
                            f"missing {name}")
        # 3 shims
        for shim in ["r7_11_verify_phase.py", "r7_11_end_session.py",
                     "r7_11_escalate.py"]:
            self.assertTrue((self.agent / "tools" / shim).is_file(),
                            f"missing shim {shim}")
        # Backups
        self.assertTrue((self.agent / "toolsets.py.probe-r7.11-orig").is_file())
        self.assertTrue((self.agent / "model_tools.py.probe-r7.11-orig").is_file())
        # toolsets.py and model_tools.py modified
        self.assertNotEqual(md5_file(self.agent / "toolsets.py"),
                            self.toolsets_md5_pre,
                            "toolsets.py should have been patched")
        self.assertNotEqual(md5_file(self.agent / "model_tools.py"),
                            self.model_tools_md5_pre,
                            "model_tools.py should have been patched")
        # Manifest exists
        manifest = self.tmpdir / "tmp-r7.11-stage-md5s.txt"
        self.assertTrue(manifest.is_file(), f"md5 snapshot missing")
        # py_compile sanity: should be in result.stdout (no error)
        self.assertNotIn("py_compile failed", result.stdout + result.stderr)

    # ------------------------------------------------------------------
    # T2: stage twice — second fails fast (stale-backup pre-flight)
    # ------------------------------------------------------------------
    def test_T2_stage_twice_fails(self):
        self._run_stage("stage")
        # Snapshot post-first-stage state
        toolsets_md5_after_first = md5_file(self.agent / "toolsets.py")
        model_tools_md5_after_first = md5_file(self.agent / "model_tools.py")

        result = self._run_stage("stage", check=False)
        self.assertNotEqual(result.returncode, 0,
                            "second stage should fail with stale-backup error")
        self.assertIn("stale backup", result.stderr,
                      f"expected 'stale backup' in stderr, got: {result.stderr}")
        # Fixture unchanged from after-first-stage
        self.assertEqual(md5_file(self.agent / "toolsets.py"),
                         toolsets_md5_after_first)
        self.assertEqual(md5_file(self.agent / "model_tools.py"),
                         model_tools_md5_after_first)

    # ------------------------------------------------------------------
    # T3: unstage after stage → fixture restored byte-exact
    # ------------------------------------------------------------------
    def test_T3_unstage_restores(self):
        self._run_stage("stage")
        result = self._run_unstage()
        self.assertEqual(result.returncode, 0, msg=f"unstage failed: {result.stderr}")
        # toolsets.py + model_tools.py restored byte-exact
        self.assertEqual(md5_file(self.agent / "toolsets.py"),
                         self.toolsets_md5_pre,
                         "toolsets.py not restored byte-exact")
        self.assertEqual(md5_file(self.agent / "model_tools.py"),
                         self.model_tools_md5_pre,
                         "model_tools.py not restored byte-exact")
        # r7_11_lib gone
        self.assertFalse((self.agent / "tools" / "r7_11_lib").exists())
        # shims gone
        for shim in ["r7_11_verify_phase.py", "r7_11_end_session.py",
                     "r7_11_escalate.py"]:
            self.assertFalse((self.agent / "tools" / shim).exists(),
                             f"shim {shim} still present")
        # backups gone
        self.assertFalse((self.agent / "toolsets.py.probe-r7.11-orig").exists())
        self.assertFalse((self.agent / "model_tools.py.probe-r7.11-orig").exists())

    # ------------------------------------------------------------------
    # T4: stage + unstage + stage round-trip
    # ------------------------------------------------------------------
    def test_T4_round_trip(self):
        self._run_stage("stage")
        self._run_unstage()
        result = self._run_stage("stage")
        self.assertEqual(result.returncode, 0,
                         msg=f"second stage after unstage failed: {result.stderr}")
        # All artifacts present again
        lib_dir = self.agent / "tools" / "r7_11_lib"
        self.assertTrue((lib_dir / "verified_state.py").is_file())
        self.assertTrue((self.agent / "tools" / "r7_11_verify_phase.py").is_file())

    # ------------------------------------------------------------------
    # T5: failure injection — unstage from partial state restores cleanly.
    #
    # Simulate a mid-stage crash: backups exist + lib dir partially populated +
    # toolsets.py/model_tools.py NOT yet patched. The unstage path treats this
    # by restoring backups (which match canonical) and removing partial files.
    # ------------------------------------------------------------------
    def test_T5_partial_state_unstage(self):
        # Manually create a partial-stage state
        backup_t = self.agent / "toolsets.py.probe-r7.11-orig"
        backup_m = self.agent / "model_tools.py.probe-r7.11-orig"
        shutil.copy(self.agent / "toolsets.py", backup_t)
        shutil.copy(self.agent / "model_tools.py", backup_m)
        # Partial lib dir (only one file copied)
        partial_lib = self.agent / "tools" / "r7_11_lib"
        partial_lib.mkdir()
        (partial_lib / "verified_state.py").write_text("# partial")
        # No shims yet
        # toolsets.py + model_tools.py NOT yet patched — they match the backup

        result = self._run_unstage()
        self.assertEqual(result.returncode, 0,
                         msg=f"unstage from partial failed: {result.stderr}")
        self.assertFalse(partial_lib.exists(), "partial lib not cleaned up")
        self.assertFalse(backup_t.exists())
        self.assertFalse(backup_m.exists())
        self.assertEqual(md5_file(self.agent / "toolsets.py"),
                         self.toolsets_md5_pre)
        self.assertEqual(md5_file(self.agent / "model_tools.py"),
                         self.model_tools_md5_pre)

    # ------------------------------------------------------------------
    # T6: pre-flight check fires on stale backup
    # ------------------------------------------------------------------
    def test_T6_stale_backup_preflight(self):
        # Plant a stale backup
        stale = self.agent / "toolsets.py.probe-r7.11-orig"
        stale.write_text("# stale backup from a prior run")
        result = self._run_stage("stage", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale backup", result.stderr)

    # ------------------------------------------------------------------
    # T7: canonical-md5 mismatch in pre-flight
    # ------------------------------------------------------------------
    def test_T7_canonical_drift_preflight(self):
        # Tamper HERMES.md
        (self.agent / "HERMES.md").write_text("# tampered content")
        result = self._run_stage("stage", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical drift", result.stderr)

    # ------------------------------------------------------------------
    # T8: import rewrite logic
    # ------------------------------------------------------------------
    def test_T8_import_rewrite(self):
        sample = textwrap.dedent("""\
            import json
            import verified_state
            import verify_phase as vp_mod
            from verified_state import (
                AAA,
                BBB,
            )
            from verify_phase import PhaseInput
            # something else
            from datetime import datetime
            """)
        result = subprocess.run(
            ["bash", str(STAGE), "--rewrite-imports"],
            input=sample, capture_output=True, text=True, check=True,
        )
        out = result.stdout
        self.assertIn("from . import verified_state", out)
        self.assertIn("from . import verify_phase as vp_mod", out)
        self.assertIn("from .verified_state import", out)
        self.assertIn("from .verify_phase import PhaseInput", out)
        # Should NOT have rewritten the unrelated lines
        self.assertIn("import json", out)
        self.assertIn("from datetime import datetime", out)
        # Lines that were rewritten should NOT remain in their original form
        self.assertNotIn("\nimport verified_state\n", out)
        self.assertNotIn("\nimport verify_phase as vp_mod\n", out)

    # ------------------------------------------------------------------
    # T9 (bonus): unstage from canonical state is a no-op
    # ------------------------------------------------------------------
    def test_T9_unstage_clean_noop(self):
        result = self._run_unstage()
        self.assertEqual(result.returncode, 0,
                         msg=f"unstage on clean fixture should succeed: {result.stderr}")
        self.assertIn("nothing to unstage", result.stdout + result.stderr,
                      "expected no-op message")
        # Files still match canonical
        self.assertEqual(md5_file(self.agent / "toolsets.py"),
                         self.toolsets_md5_pre)

    # ------------------------------------------------------------------
    # T10 (bonus): rewrite produces py_compile-able verify_phase_tool.py
    # when run against the real source file (sibling siblings present)
    # ------------------------------------------------------------------
    def test_T10_rewritten_tool_compiles(self):
        with open(SRC_VERIFY_PHASE_TOOL) as f:
            original = f.read()
        result = subprocess.run(
            ["bash", str(STAGE), "--rewrite-imports"],
            input=original, capture_output=True, text=True, check=True,
        )
        rewritten = result.stdout
        # Place rewritten + the other lib files in a temp r7_11_lib pkg and
        # py_compile the rewritten file.
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "r7_11_lib"
            pkg.mkdir()
            (pkg / "__init__.py").write_text("")
            shutil.copy(SRC_VERIFIED_STATE, pkg / "verified_state.py")
            shutil.copy(SRC_VERIFY_PHASE, pkg / "verify_phase.py")
            (pkg / "verify_phase_tool.py").write_text(rewritten)
            # py_compile via subprocess for parity
            compile_result = subprocess.run(
                [sys.executable, "-m", "py_compile",
                 str(pkg / "verify_phase_tool.py")],
                capture_output=True, text=True,
            )
            self.assertEqual(compile_result.returncode, 0,
                             f"py_compile of rewritten file failed: "
                             f"{compile_result.stderr}")

    # ------------------------------------------------------------------
    # T11: stage includes write_plan_md.py (item 8 trial 1 staging-gap fix)
    # ------------------------------------------------------------------
    def test_T11_stage_includes_write_plan_md(self):
        result = self._run_stage("stage")
        self.assertEqual(result.returncode, 0,
                         msg=f"stage failed: {result.stderr}")
        wpm = self.agent / "tools" / "write_plan_md.py"
        self.assertTrue(wpm.is_file(),
                        "stage did not create tools/write_plan_md.py")
        # Non-trivial body: source is ~8KB (188 lines per HANDOFF-r7.10).
        self.assertGreater(wpm.stat().st_size, 500,
                           "write_plan_md.py is suspiciously small")
        # md5 matches the source file (Phase 4.5 is a straight copy).
        self.assertEqual(md5_file(wpm), md5_file(SRC_WRITE_PLAN_MD),
                         "staged write_plan_md.py md5 does not match source")
        # Valid Python (py_compile would have caught issues at stage-time too).
        compile_result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(wpm)],
            capture_output=True, text=True,
        )
        self.assertEqual(compile_result.returncode, 0,
                         f"staged write_plan_md.py does not py_compile: "
                         f"{compile_result.stderr}")

    # ------------------------------------------------------------------
    # T12: toolsets.py post-stage references "write_plan_md"
    # ------------------------------------------------------------------
    def test_T12_toolsets_lists_write_plan_md(self):
        self._run_stage("stage")
        toolsets_text = (self.agent / "toolsets.py").read_text()
        self.assertIn('"write_plan_md"', toolsets_text,
                      "toolsets.py missing write_plan_md after stage")
        # The other r7.11 names must still be present (single-insertion form).
        for name in ('"verify_phase"', '"end_session_for_handoff"',
                     '"escalate_to_operator"'):
            self.assertIn(name, toolsets_text,
                          f"toolsets.py missing {name} after stage")

    # ------------------------------------------------------------------
    # T13: model_tools.py post-stage imports "tools.write_plan_md"
    # ------------------------------------------------------------------
    def test_T13_model_tools_imports_write_plan_md(self):
        self._run_stage("stage")
        model_tools_text = (self.agent / "model_tools.py").read_text()
        self.assertIn('"tools.write_plan_md"', model_tools_text,
                      "model_tools.py missing tools.write_plan_md after stage")
        for imp in ('"tools.r7_11_verify_phase"',
                    '"tools.r7_11_end_session"',
                    '"tools.r7_11_escalate"'):
            self.assertIn(imp, model_tools_text,
                          f"model_tools.py missing {imp} after stage")

    # ------------------------------------------------------------------
    # T14: unstage removes write_plan_md and restores canonical baseline
    # ------------------------------------------------------------------
    def test_T14_unstage_removes_write_plan_md(self):
        self._run_stage("stage")
        wpm = self.agent / "tools" / "write_plan_md.py"
        self.assertTrue(wpm.is_file(), "precondition: write_plan_md staged")
        self._run_unstage()
        self.assertFalse(wpm.exists(),
                         "unstage did not remove tools/write_plan_md.py")
        # toolsets.py / model_tools.py back to canonical baseline (md5 match).
        self.assertEqual(md5_file(self.agent / "toolsets.py"),
                         self.toolsets_md5_pre,
                         "toolsets.py md5 not restored to canonical")
        self.assertEqual(md5_file(self.agent / "model_tools.py"),
                         self.model_tools_md5_pre,
                         "model_tools.py md5 not restored to canonical")

    # ------------------------------------------------------------------
    # T15: round-trip — stage, unstage, stage again is clean.
    # The post-second-stage write_plan_md md5 still matches source; toolsets
    # baseline at start matches baseline after first unstage.
    # ------------------------------------------------------------------
    def test_T15_round_trip_with_write_plan_md(self):
        self._run_stage("stage")
        self._run_unstage()
        # Snapshot baseline after first unstage — must match initial canonical.
        self.assertEqual(md5_file(self.agent / "toolsets.py"),
                         self.toolsets_md5_pre)
        self.assertEqual(md5_file(self.agent / "model_tools.py"),
                         self.model_tools_md5_pre)
        # Second stage works cleanly.
        result = self._run_stage("stage")
        self.assertEqual(result.returncode, 0,
                         msg=f"second stage failed: {result.stderr}")
        wpm = self.agent / "tools" / "write_plan_md.py"
        self.assertTrue(wpm.is_file())
        self.assertEqual(md5_file(wpm), md5_file(SRC_WRITE_PLAN_MD),
                         "second-stage write_plan_md md5 drift")

    # ------------------------------------------------------------------
    # T16: pre-flight refuses to overwrite an existing tools/write_plan_md.py
    # (Phase 4.5 belt-and-suspenders check). With no .probe-r7.11-orig
    # backups present, the stale-backup pre-flight wouldn't catch this case.
    # ------------------------------------------------------------------
    def test_T16_preflight_refuses_existing_write_plan_md(self):
        # Plant a pre-existing tools/write_plan_md.py (no backups → stale-
        # backup pre-flight passes; Phase 4.5 must be the gate that fires).
        existing = self.agent / "tools" / "write_plan_md.py"
        existing.write_text("# pre-existing — must not be overwritten\n")
        pre_md5 = md5_file(existing)
        result = self._run_stage("stage", check=False)
        self.assertNotEqual(result.returncode, 0,
                            "stage should refuse when write_plan_md.py exists")
        self.assertIn("write_plan_md.py already exists",
                      result.stderr + result.stdout,
                      f"expected 'already exists' guard, got "
                      f"stderr={result.stderr!r} stdout={result.stdout!r}")
        # Pre-existing file untouched.
        self.assertEqual(md5_file(existing), pre_md5,
                         "pre-existing write_plan_md.py was modified")


if __name__ == "__main__":
    unittest.main(verbosity=2)
