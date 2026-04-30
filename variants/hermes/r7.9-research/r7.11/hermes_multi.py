#!/usr/bin/env python3
"""hermes_multi — wrapper substrate for r7.11 multi-session Hermes runs.

Item 7 of the r7.11 implementation order. Operator-facing tool that
drives a multi-session Hermes run with verification gates between
phases. Pure stdlib; runs on the operator's Mac; drives Hermes via ssh
on the build VM.

The wrapper is INTENTIONALLY DUMB:
  * It does NOT modify Hermes, the VM canonical, or PLAN.md.
  * It does NOT make agentic decisions. Routing is determined by
    `verified-state.json` (machine-authoritative) and sentinel-file
    triggers.
  * It does NOT write to `verified-state.json` — that's `verify_phase`'s
    job inside the Hermes session. The wrapper is read-only on that
    file. (Search for `_VS_WRITE_FORBIDDEN_INVARIANT` in this module.)

Per DESIGN-r7.11-architecture.md §5: ~200 lines of substrate; reads
state, polls sentinels, re-launches Hermes. This file is bigger than
that target only because it carries (a) full transport abstraction for
testability and (b) atomic manifest writes — both of which the original
budget didn't include but which the smoke trials proved necessary.

Subcommands:
  hermes-multi run <scaffold_root>      — initial run (or resume if state exists)
  hermes-multi resume <scaffold_root>   — resume after escalate-pause
  hermes-multi status <scaffold_root>   — read-only diagnostic

Exit codes (per design §SC-10):
  0  success — all phases verified_passed
  1  generic failure (POSIX; rarely emitted)
  2  escalate-pause — operator action expected
  3  wrapper-internal error (file IO, ssh, parse)
  4  configuration error (verify-config.json malformed)
  5  canonical drift (RESERVED for future use)
  130 SIGINT (operator Ctrl-C)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

# Item-1 / item-5 / item-6a imports — read-only consumers.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verified_state as vs_mod  # noqa: E402
from verified_state import (  # noqa: E402
    Decision,
    DecisionAction,
    PhaseSpec,
    PhaseStatus,
    VerifiedState,
)
from handoff_tools import (  # noqa: E402
    SESSION_END_SENTINEL_NAME,
    SESSION_ESCALATE_SENTINEL_NAME,
)
from verify_phase_tool import (  # noqa: E402
    ConfigError as VPConfigError,
    ToolError as VPToolError,
    parse_plan_md,
)


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


EXIT_SUCCESS = 0
EXIT_GENERIC_FAILURE = 1
EXIT_ESCALATE = 2
EXIT_WRAPPER_ERROR = 3
EXIT_CONFIG_ERROR = 4
EXIT_CANONICAL_DRIFT = 5  # RESERVED
EXIT_SIGINT = 130


# ---------------------------------------------------------------------------
# Wrapper-side errors
# ---------------------------------------------------------------------------


class WrapperError(Exception):
    """Generic wrapper-internal failure (file IO, ssh, etc.). Maps to exit 3."""


class ConfigError(ValueError):
    """Wrapper-side config error. Maps to exit 4."""


# ---------------------------------------------------------------------------
# Wrapper config
# ---------------------------------------------------------------------------


@dataclass
class WrapperConfig:
    phase_max_wall_clock_seconds: int = 3600
    sentinel_grace_seconds: int = 30
    poll_interval_seconds: float = 1.0
    max_anomalous_exits: int = 3
    model: str = "gemma-4-26B-A4B-it-MLX-8bit"
    max_turns_per_phase: int = 40
    remote_host: str = "ubuntu-vm"


def load_wrapper_config(verify_config_path: Optional[Path]) -> WrapperConfig:
    """Read the `wrapper` section of verify-config.json. Defaults if missing."""
    if verify_config_path is None or not verify_config_path.exists():
        return WrapperConfig()
    try:
        raw = verify_config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"verify-config.json unreadable: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"verify-config.json invalid JSON (line {exc.lineno}): {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise ConfigError("verify-config.json top-level must be an object")
    section = data.get("wrapper", {})
    if not isinstance(section, dict):
        raise ConfigError("verify-config.json 'wrapper' must be an object")
    cfg = WrapperConfig()

    def _set_int(key: str) -> None:
        if key in section:
            v = section[key]
            if not isinstance(v, int) or isinstance(v, bool):
                raise ConfigError(f"wrapper.{key} must be int")
            setattr(cfg, key, v)

    def _set_str(key: str) -> None:
        if key in section:
            v = section[key]
            if not isinstance(v, str):
                raise ConfigError(f"wrapper.{key} must be string")
            setattr(cfg, key, v)

    _set_int("phase_max_wall_clock_seconds")
    _set_int("sentinel_grace_seconds")
    _set_int("max_anomalous_exits")
    _set_int("max_turns_per_phase")
    _set_str("model")
    _set_str("remote_host")
    if "poll_interval_seconds" in section:
        v = section["poll_interval_seconds"]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ConfigError("wrapper.poll_interval_seconds must be number")
        cfg.poll_interval_seconds = float(v)
    return cfg


# ---------------------------------------------------------------------------
# Transport abstraction (testability seam, SC-1)
# ---------------------------------------------------------------------------


class Transport(Protocol):
    def file_exists(self, path: str) -> bool: ...
    def read_file(self, path: str) -> str: ...
    def write_file(self, path: str, content: str) -> None: ...
    def remove_file(self, path: str) -> None: ...
    def list_dir(self, path: str) -> List[str]: ...
    def launch_hermes(
        self,
        *,
        scaffold_root: str,
        source_tag: str,
        prompt: str,
        model: str,
        max_turns: int,
        omlx_api_key: Optional[str],
        stdout_path: str,
        stderr_path: str,
        resume_session_id: Optional[str] = None,
    ) -> "subprocess.Popen": ...
    def find_recent_session_json(
        self, source_tag: str, since_epoch: float
    ) -> Optional[str]: ...
    def copy_to_local(self, remote_path: str, local_path: str) -> None: ...


class LocalFsTransport:
    """Test transport — backs onto the local filesystem.

    The `launch_hermes` implementation delegates to a caller-supplied
    factory. Tests construct one with a custom factory that returns a
    `FakePopen` (see test file). Production never instantiates this
    transport.
    """

    def __init__(self, hermes_factory=None):
        self._hermes_factory = hermes_factory

    def file_exists(self, path: str) -> bool:
        return Path(path).exists()

    def read_file(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def remove_file(self, path: str) -> None:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass

    def list_dir(self, path: str) -> List[str]:
        p = Path(path)
        if not p.exists():
            return []
        return sorted(os.listdir(p))

    def launch_hermes(self, **kwargs) -> "subprocess.Popen":
        if self._hermes_factory is None:
            raise WrapperError(
                "LocalFsTransport.launch_hermes called without a factory; "
                "test setup error"
            )
        return self._hermes_factory(**kwargs)

    def find_recent_session_json(
        self, source_tag: str, since_epoch: float
    ) -> Optional[str]:
        # Tests stash a hint file at `<scaffold>/.test-session-json`.
        # In production we'd query ~/.hermes/sessions on the VM.
        # source_tag is the scaffold_root in tests.
        hint = Path(source_tag) / ".test-session-json"
        if hint.exists():
            try:
                p = hint.read_text(encoding="utf-8").strip()
                if p and Path(p).exists():
                    return p
            except OSError:
                return None
        return None

    def copy_to_local(self, remote_path: str, local_path: str) -> None:
        rp = Path(remote_path)
        lp = Path(local_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        if rp.exists():
            shutil.copy2(rp, lp)


class SshTransport:
    """Production transport — drives Hermes on a remote VM via ssh.

    Operations are read-mostly. We shell out to `ssh <host> <cmd>` for
    file ops; for `launch_hermes` we Popen `ssh -t <host> bash -lc
    'hermes chat ...'` so SIGTERM on the local side kills the remote
    process tree (controlled by `start_new_session=True`).

    NOTE: the wrapper test suite does NOT exercise SshTransport directly;
    coverage of ssh paths is the operator runbook's smoke responsibility.
    The seam is sufficient to keep the state machine code testable.
    """

    def __init__(self, host: str):
        self.host = host

    def _ssh_run(self, cmd: str, check: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["ssh", self.host, cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if check and result.returncode != 0:
            raise WrapperError(
                f"ssh {self.host} {cmd!r} failed (exit {result.returncode}): "
                f"{result.stderr.strip()}"
            )
        return result

    def file_exists(self, path: str) -> bool:
        r = self._ssh_run(f"test -e {shlex.quote(path)} && echo Y || echo N", check=False)
        return r.stdout.strip() == "Y"

    def read_file(self, path: str) -> str:
        r = self._ssh_run(f"cat {shlex.quote(path)}")
        return r.stdout

    def write_file(self, path: str, content: str) -> None:
        # Use a heredoc-style upload via stdin to avoid quoting issues.
        proc = subprocess.run(
            ["ssh", self.host, f"cat > {shlex.quote(path)}"],
            input=content,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            raise WrapperError(
                f"ssh write_file failed for {path}: {proc.stderr.strip()}"
            )

    def remove_file(self, path: str) -> None:
        self._ssh_run(f"rm -f {shlex.quote(path)}", check=False)

    def list_dir(self, path: str) -> List[str]:
        r = self._ssh_run(
            f"ls -1 {shlex.quote(path)} 2>/dev/null || true", check=False
        )
        return [s for s in r.stdout.splitlines() if s]

    def launch_hermes(
        self,
        *,
        scaffold_root: str,
        source_tag: str,
        prompt: str,
        model: str,
        max_turns: int,
        omlx_api_key: Optional[str],
        stdout_path: str,
        stderr_path: str,
        resume_session_id: Optional[str] = None,
    ) -> "subprocess.Popen":
        env_part = ""
        if omlx_api_key:
            env_part = f"OMLX_API_KEY={shlex.quote(omlx_api_key)} "
        resume_part = (
            f"--resume {shlex.quote(resume_session_id)} "
            if resume_session_id
            else ""
        )
        remote_cmd = (
            f"{env_part}hermes chat "
            f"{resume_part}"
            f"--model {shlex.quote(model)} "
            f"--max-turns {int(max_turns)} "
            f"-q {shlex.quote(prompt)}"
        )
        out_f = open(stdout_path, "wb")
        err_f = open(stderr_path, "wb")
        return subprocess.Popen(
            ["ssh", "-tt", self.host, f"bash -lc {shlex.quote(remote_cmd)}"],
            stdout=out_f,
            stderr=err_f,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    def find_recent_session_json(
        self, source_tag: str, since_epoch: float
    ) -> Optional[str]:
        # Look in ~/.hermes/sessions for a JSON modified after since_epoch.
        # F-1: SQLite is regressed; we rely on JSON mtime.
        cmd = (
            "ls -1t ~/.hermes/sessions/session_*.json 2>/dev/null | head -5"
        )
        r = self._ssh_run(cmd, check=False)
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            stat = self._ssh_run(
                f"stat -c %Y {shlex.quote(line)} 2>/dev/null || echo 0",
                check=False,
            )
            try:
                mtime = int(stat.stdout.strip())
            except ValueError:
                continue
            if mtime >= int(since_epoch):
                return line
        return None

    def copy_to_local(self, remote_path: str, local_path: str) -> None:
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["scp", "-q", f"{self.host}:{remote_path}", local_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            # Non-fatal: log only.
            logging.getLogger("hermes_multi").warning(
                "scp %s -> %s failed: %s",
                remote_path,
                local_path,
                proc.stderr.strip(),
            )


class LocalProcessTransport:
    """Production transport — drives Hermes as a local subprocess.

    Use case: operator ssh's into the build VM and runs the wrapper there,
    so scaffold + Hermes are both VM-local. Avoids the SshTransport path-
    mismatch problem (Mac and VM disagreeing on the scaffold path string)
    and the ssh-to-self overhead.

    All file ops are direct local Path operations. ``launch_hermes`` Popens
    the Hermes binary directly with ``cwd=hermes_cwd`` (matching the prior
    probe pattern: ``cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat ...``).
    """

    def __init__(
        self,
        hermes_path: Optional[Any] = None,
        hermes_cwd: Optional[Any] = None,
    ):
        # Default hermes_path: ~/.hermes/hermes-agent/venv/bin/hermes
        # Default hermes_cwd: ~/.hermes/hermes-agent
        self.hermes_path = (
            Path(hermes_path)
            if hermes_path is not None
            else Path.home() / ".hermes" / "hermes-agent" / "venv" / "bin" / "hermes"
        )
        self.hermes_cwd = (
            Path(hermes_cwd)
            if hermes_cwd is not None
            else Path.home() / ".hermes" / "hermes-agent"
        )

    def file_exists(self, path: str) -> bool:
        return Path(path).exists()

    def read_file(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def remove_file(self, path: str) -> None:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass

    def list_dir(self, path: str) -> List[str]:
        p = Path(path)
        if not p.exists():
            return []
        return sorted(os.listdir(p))

    def launch_hermes(
        self,
        *,
        scaffold_root: str,
        source_tag: str,
        prompt: str,
        model: str,
        max_turns: int,
        omlx_api_key: Optional[str],
        stdout_path: str,
        stderr_path: str,
        resume_session_id: Optional[str] = None,
        toolset: str = "hermes-cli",
        timeout_seconds: Optional[int] = None,
    ) -> "subprocess.Popen":
        cmd: List[str] = [
            str(self.hermes_path),
            "chat",
            "-m", model,
            "-Q",
            "--max-turns", str(int(max_turns)),
            "-t", toolset,
            "--source", source_tag,
            "-q", prompt,
        ]
        if resume_session_id:
            cmd.extend(["--resume", str(resume_session_id)])

        env = os.environ.copy()
        if omlx_api_key:
            env["OMLX_API_KEY"] = omlx_api_key

        scaffold_venv = Path(scaffold_root) / ".venv"
        if scaffold_venv.is_dir():
            site_packages = next(
                (scaffold_venv / "lib").glob("python*/site-packages"),
                None,
            )
            if site_packages is not None:
                existing = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = (
                    f"{site_packages}:{existing}" if existing else str(site_packages)
                )

        # Open log files in binary mode for parity with SshTransport.
        out_f = open(stdout_path, "wb")
        err_f = open(stderr_path, "wb")

        return subprocess.Popen(
            cmd,
            cwd=str(self.hermes_cwd),
            env=env,
            stdout=out_f,
            stderr=err_f,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    def find_recent_session_json(
        self, source_tag: str, since_epoch: float
    ) -> Optional[str]:
        """Find the most-recent session_*.json under ~/.hermes/sessions.

        Per F-1 (SQLite session DB regression), we cannot rely on a DB
        lookup. Strategy: prefer JSON files whose ``source`` field matches
        ``source_tag`` AND mtime >= since_epoch; fall back to the newest
        JSON with mtime >= since_epoch (mirrors smoke-harness behavior).
        """
        sessions_dir = Path.home() / ".hermes" / "sessions"
        if not sessions_dir.exists():
            return None
        candidates_by_source: List[tuple] = []
        candidates_by_mtime: List[tuple] = []
        try:
            iterator = sessions_dir.glob("session_*.json")
        except OSError:
            return None
        for path in iterator:
            try:
                mt = path.stat().st_mtime
            except OSError:
                continue
            if mt < since_epoch:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                # Still a candidate by mtime if unreadable JSON.
                candidates_by_mtime.append((mt, str(path)))
                continue
            if isinstance(data, dict) and data.get("source") == source_tag:
                candidates_by_source.append((mt, str(path)))
            else:
                candidates_by_mtime.append((mt, str(path)))
        if candidates_by_source:
            candidates_by_source.sort(reverse=True)
            return candidates_by_source[0][1]
        if candidates_by_mtime:
            candidates_by_mtime.sort(reverse=True)
            return candidates_by_mtime[0][1]
        return None

    def copy_to_local(self, remote_path: str, local_path: str) -> None:
        rp = Path(remote_path)
        lp = Path(local_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        if rp.exists():
            shutil.copy2(rp, lp)


# ---------------------------------------------------------------------------
# State machine states
# ---------------------------------------------------------------------------


class WrapperState(str, Enum):
    INITIAL = "INITIAL"
    BOOTSTRAPPING = "BOOTSTRAPPING"
    LAUNCHING = "LAUNCHING"
    RUNNING = "RUNNING"
    SENTINEL_DETECTED = "SENTINEL_DETECTED"
    HERMES_EXITED = "HERMES_EXITED"
    ARCHIVING = "ARCHIVING"
    DECIDING = "DECIDING"
    COMPLETE = "COMPLETE"
    ESCALATING = "ESCALATING"
    WRAPPER_ERROR = "WRAPPER_ERROR"


# Exit-reason categories used in manifest entries.
EXIT_REASON_END = "end"
EXIT_REASON_ESCALATE = "escalate"
EXIT_REASON_TIMEOUT = "timeout"
EXIT_REASON_CRASH = "crash"
EXIT_REASON_ANOMALOUS = "anomalous_exit"

# Bootstrap-mode escalation reason codes (parent failed to produce a usable
# PLAN.md from USER-PROMPT.md). Surfaced via stderr + manifest reason field.
BOOTSTRAP_FAILED_NO_PLAN = "bootstrap_failed_no_plan"
BOOTSTRAP_FAILED_UNPARSEABLE_PLAN = "bootstrap_failed_unparseable_plan"
BOOTSTRAP_FAILED_ANOMALOUS_EXIT = "bootstrap_failed_anomalous_exit"

# wrapper_decision values in manifest entries.
DECISION_ADVANCE = "advance"
DECISION_REVISE = "revise"
DECISION_ESCALATE = "escalate"
DECISION_SUCCESS = "success"
DECISION_WRAPPER_ERROR = "wrapper_error"


# ---------------------------------------------------------------------------
# Sentinel polling thread
# ---------------------------------------------------------------------------


@dataclass
class SentinelPollResult:
    end_seen: bool = False
    escalate_seen: bool = False


class SentinelPoller:
    """Background thread polling for sentinel files via Transport."""

    def __init__(
        self,
        transport: Transport,
        scaffold_root: str,
        interval: float,
        stop_event: threading.Event,
        detected_event: threading.Event,
        result: SentinelPollResult,
    ):
        self.transport = transport
        self.scaffold_root = scaffold_root
        self.interval = interval
        self._stop = stop_event
        self._detected = detected_event
        self._result = result
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def join(self, timeout: Optional[float] = None) -> None:
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        end_path = str(Path(self.scaffold_root) / SESSION_END_SENTINEL_NAME)
        esc_path = str(Path(self.scaffold_root) / SESSION_ESCALATE_SENTINEL_NAME)
        while not self._stop.is_set():
            try:
                end_present = self.transport.file_exists(end_path)
                esc_present = self.transport.file_exists(esc_path)
            except Exception:
                # Transient transport failures are tolerated; we'll retry.
                end_present = False
                esc_present = False
            if end_present:
                self._result.end_seen = True
            if esc_present:
                self._result.escalate_seen = True
            if end_present or esc_present:
                self._detected.set()
                # Keep observing in case the second one shows up too.
            self._stop.wait(self.interval)


# ---------------------------------------------------------------------------
# Wrapper core
# ---------------------------------------------------------------------------


@dataclass
class PhaseRunOutcome:
    """Outcome of a single Hermes session run."""

    exit_reason: str
    exit_code: int
    sentinel_kind: Optional[str]
    hermes_session_id: Optional[str]
    archived_session_path: Optional[str]
    wall_clock_seconds: int


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_write_json(target: Path, payload: Any) -> None:
    """Write `payload` as pretty JSON to `target` atomically.

    Mirrors verified_state.save's pattern.
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


def _verify_state_snapshot(state: VerifiedState) -> str:
    """Build the human-readable snapshot string for manifest entries."""
    parts = []
    for entry in state.phase_state:
        if entry.status == PhaseStatus.VERIFIED_PASSED:
            parts.append(
                f"phase {entry.id} verified_passed "
                f"(tier_run={entry.tier_run}, revision_count={entry.revision_count})"
            )
        elif entry.status == PhaseStatus.VERIFIED_FAILED:
            parts.append(
                f"phase {entry.id} verified_failed "
                f"(revision_count={entry.revision_count}/{entry.max_revisions})"
            )
        else:
            parts.append(f"phase {entry.id} {entry.status.value}")
    return "; ".join(parts) if parts else "no phases"


class Wrapper:
    """Multi-session Hermes orchestrator. Read-only on verified-state.json."""

    # Searchable invariant: the wrapper MUST NEVER write verified-state.json.
    # All modifications happen via verify_phase inside a Hermes session.
    _VS_WRITE_FORBIDDEN_INVARIANT = (
        "wrapper.run() / wrapper.resume() / wrapper._archive_session() "
        "MUST NOT call verified_state.save() or write verified-state.json. "
        "The wrapper is read-only on that file. revision_count is bumped "
        "by verify_phase via record_verdict; anomalous_exit_count is "
        "wrapper-side state held in self._anomalous_exit_count."
    )

    def __init__(
        self,
        *,
        scaffold_root: Path,
        transport: Transport,
        wrapper_config: WrapperConfig,
        omlx_api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.scaffold_root = Path(scaffold_root)
        self.transport = transport
        self.cfg = wrapper_config
        self.omlx_api_key = omlx_api_key
        self.log = logger or logging.getLogger("hermes_multi")
        self._anomalous_exit_count = 0
        self._sigint_received = False
        self._current_popen: Optional[subprocess.Popen] = None
        self._archive_dir = self.scaffold_root / ".session-archive"
        self._manifest_path = self._archive_dir / "manifest.json"
        self._wrapper_log_path = self._archive_dir / "wrapper.log"
        # Persistent session-id used for `--resume` chains.
        # First session creates it; subsequent sessions reuse it.
        self._hermes_session_id: Optional[str] = None
        self._attempt_counters: Dict[int, int] = {}
        # 0-arg state-snapshot path used by status command + tests.
        self._verified_state_path = self.scaffold_root / "verified-state.json"

    # ---- logging -----------------------------------------------------

    def _log_state(self, state: WrapperState, detail: str = "") -> None:
        ts = _utc_now_iso()
        line = f"{ts} {state.value} {detail}".rstrip() + "\n"
        try:
            self._archive_dir.mkdir(parents=True, exist_ok=True)
            with open(self._wrapper_log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass
        self.log.info("%s %s", state.value, detail)

    # ---- bootstrap / state load -------------------------------------

    def _load_verified_state(self) -> VerifiedState:
        try:
            return vs_mod.load(self._verified_state_path)
        except FileNotFoundError as exc:
            raise WrapperError(
                f"verified-state.json not found at "
                f"{self._verified_state_path}; run bootstrap first"
            ) from exc

    def _maybe_run_bootstrap(self) -> Optional[int]:
        """If PLAN.md is missing, drive the bootstrap session. Returns:

        - ``None`` if PLAN.md is already present (skip bootstrap; caller
          proceeds to the existing flow). This is the regression-safe
          path: previously-bootstrapped scaffolds behave exactly as before.
        - An exit code (``EXIT_CONFIG_ERROR`` or ``EXIT_ESCALATE``) if the
          wrapper must terminate before entering the phase loop.

        Per the brief and design §2: anomalous-exit policy for bootstrap
        is FAIL-FAST. A single attempt; if Hermes exits without producing
        a parseable PLAN.md, escalate. Bootstrap loops aren't useful — if
        the parent can't author PLAN.md once, retry without operator
        intervention won't help.
        """
        plan_path = self.scaffold_root / "PLAN.md"
        if plan_path.exists():
            return None  # regression-safe: existing PLAN.md → skip bootstrap

        user_prompt_path = self.scaffold_root / "USER-PROMPT.md"
        if not user_prompt_path.exists():
            msg = (
                "neither PLAN.md nor USER-PROMPT.md present in "
                f"{self.scaffold_root}; cannot bootstrap"
            )
            self._log_state(WrapperState.WRAPPER_ERROR, msg)
            print(f"hermes-multi: config error: {msg}", file=sys.stderr)
            return EXIT_CONFIG_ERROR

        outcome = self._run_bootstrap_session(user_prompt_path)
        self._log_state(
            WrapperState.HERMES_EXITED,
            f"bootstrap exit_reason={outcome.exit_reason} "
            f"exit_code={outcome.exit_code} sentinel={outcome.sentinel_kind} "
            f"wall={outcome.wall_clock_seconds}s",
        )

        # Determine next action. Sentinel-escalate from bootstrap → escalate.
        if outcome.sentinel_kind in ("escalate-signal", "both"):
            entry = self._build_bootstrap_manifest_entry(
                outcome,
                wrapper_decision=DECISION_ESCALATE,
                reason="parent_called_escalate_during_bootstrap",
            )
            self._append_manifest_entry(entry)
            print(
                "hermes-multi: ESCALATE — parent called escalate_to_operator "
                f"during bootstrap (sentinel={outcome.sentinel_kind})",
                file=sys.stderr,
            )
            return EXIT_ESCALATE

        # Anomalous bootstrap exit (timeout/crash/clean-no-sentinel).
        # FAIL-FAST policy: single attempt, escalate on failure.
        if outcome.exit_reason in (
            EXIT_REASON_CRASH,
            EXIT_REASON_TIMEOUT,
            EXIT_REASON_ANOMALOUS,
        ):
            self._anomalous_exit_count += 1
            entry = self._build_bootstrap_manifest_entry(
                outcome,
                wrapper_decision=DECISION_ESCALATE,
                reason=BOOTSTRAP_FAILED_ANOMALOUS_EXIT,
            )
            self._append_manifest_entry(entry)
            print(
                "hermes-multi: ESCALATE — bootstrap session exited "
                f"anomalously (exit_reason={outcome.exit_reason}); "
                "fail-fast policy",
                file=sys.stderr,
            )
            return EXIT_ESCALATE

        # End-sentinel fired. Verify PLAN.md exists + parses.
        plan_path = self.scaffold_root / "PLAN.md"
        if not plan_path.exists():
            entry = self._build_bootstrap_manifest_entry(
                outcome,
                wrapper_decision=DECISION_ESCALATE,
                reason=BOOTSTRAP_FAILED_NO_PLAN,
            )
            self._append_manifest_entry(entry)
            print(
                "hermes-multi: ESCALATE — bootstrap session ended but "
                "PLAN.md was not written "
                f"(reason={BOOTSTRAP_FAILED_NO_PLAN})",
                file=sys.stderr,
            )
            return EXIT_ESCALATE

        try:
            phases = parse_plan_md(plan_path)
            if not phases:
                raise VPToolError("PLAN.md parsed but contained zero phases")
        except VPToolError as exc:
            entry = self._build_bootstrap_manifest_entry(
                outcome,
                wrapper_decision=DECISION_ESCALATE,
                reason=f"{BOOTSTRAP_FAILED_UNPARSEABLE_PLAN}: {exc}",
            )
            self._append_manifest_entry(entry)
            print(
                "hermes-multi: ESCALATE — bootstrap session wrote PLAN.md "
                f"but it is unparseable: {exc} "
                f"(reason={BOOTSTRAP_FAILED_UNPARSEABLE_PLAN})",
                file=sys.stderr,
            )
            return EXIT_ESCALATE

        # Bootstrap success. Record manifest entry and let caller proceed
        # to _bootstrap_state_if_needed (which seeds verified-state.json
        # from the new PLAN.md) and then into the phase loop.
        entry = self._build_bootstrap_manifest_entry(
            outcome,
            wrapper_decision=DECISION_ADVANCE,
        )
        self._append_manifest_entry(entry)
        self._log_state(
            WrapperState.BOOTSTRAPPING,
            f"bootstrap succeeded; PLAN.md has {len(phases)} phases",
        )
        return None

    def _bootstrap_state_if_needed(self, fresh: bool = False) -> None:
        """Create initial verified-state.json from PLAN.md if absent.

        This is the ONLY case where the wrapper is permitted to write
        verified-state.json — the very first call before any Hermes
        session has run. After this initial bootstrap, the wrapper is
        read-only on the file.
        """
        plan_path = self.scaffold_root / "PLAN.md"
        if not plan_path.exists():
            raise WrapperError(f"PLAN.md not found at {plan_path}")
        if self._verified_state_path.exists() and not fresh:
            return
        try:
            phases_with_paths = parse_plan_md(plan_path)
        except VPToolError as exc:
            raise WrapperError(f"PLAN.md parse failed: {exc}") from exc
        phases = [
            PhaseSpec(id=p.id, title=p.title) for p in phases_with_paths
        ]
        state = vs_mod.bootstrap(
            scaffold_root=str(self.scaffold_root),
            plan_md_path=str(plan_path),
            phases=phases,
        )
        vs_mod.save(state, self._verified_state_path)
        self._log_state(
            WrapperState.INITIAL,
            f"bootstrapped verified-state.json with {len(phases)} phases",
        )

    # ---- session management -----------------------------------------

    def _clear_sentinels(self) -> None:
        for name in (SESSION_END_SENTINEL_NAME, SESSION_ESCALATE_SENTINEL_NAME):
            self.transport.remove_file(str(self.scaffold_root / name))

    def _next_attempt(self, phase_id: int) -> int:
        n = self._attempt_counters.get(phase_id, 0) + 1
        self._attempt_counters[phase_id] = n
        return n

    def _build_prompt(
        self,
        decision: Decision,
        state: VerifiedState,
        attempt: int,
        is_resume: bool,
    ) -> str:
        """Construct the resume-orientation prompt per §4.B Addendum A2."""
        lines = [
            "You are the parent agent in an r7.11 multi-session Hermes run.",
            "On every (re)start, perform these orientation steps:",
            "  1. read_file PLAN.md",
            f"  2. read_file {self._verified_state_path}",
            "  3. Identify the next pending or revision-needed phase.",
            "  4. Reconstitute the todo list from verified-state.json (one entry per phase).",
            "  5. Dispatch via delegate_worker; on revise, prepend corrective_dispatch.",
            "When you finish (or hit the revision cap), call end_session_for_handoff",
            "or escalate_to_operator. The wrapper trusts verified-state.json only.",
            "",
            f"Active scaffold_root: {self.scaffold_root}",
            f"Active phase: {decision.phase_id} ({decision.action.value})",
            f"Wrapper attempt #: {attempt}",
        ]
        if decision.action == DecisionAction.REVISE:
            entry = next(
                (e for e in state.phase_state if e.id == decision.phase_id),
                None,
            )
            if entry and entry.corrective_dispatch:
                lines.append("")
                lines.append("Corrective guidance from prior verify_phase:")
                lines.append(entry.corrective_dispatch)
        return "\n".join(lines)

    def _run_one_session(
        self,
        decision: Decision,
        state: VerifiedState,
    ) -> PhaseRunOutcome:
        """Launch Hermes, poll for sentinel + exit, return outcome."""
        phase_id = decision.phase_id or 0
        attempt = self._next_attempt(phase_id)
        is_resume = self._hermes_session_id is not None

        # Snapshot prior session JSON before re-launch (Addendum A3).
        if is_resume and self._hermes_session_id:
            try:
                self._snapshot_prior_session_json(phase_id, attempt)
            except Exception as exc:
                self.log.warning("session-json snapshot failed: %s", exc)

        prompt = self._build_prompt(decision, state, attempt, is_resume)
        archive_basename = f"phase-{phase_id}-attempt-{attempt}"
        return self._run_session_core(
            prompt=prompt,
            phase_id=phase_id,
            attempt=attempt,
            is_resume=is_resume,
            archive_basename=archive_basename,
            launch_state_detail=(
                f"phase={phase_id} attempt={attempt} resume={is_resume}"
            ),
        )

    def _run_session_core(
        self,
        *,
        prompt: str,
        phase_id: int,
        attempt: int,
        is_resume: bool,
        archive_basename: str,
        launch_state_detail: str,
    ) -> PhaseRunOutcome:
        """Shared launch-poll-archive machinery for phase + bootstrap sessions.

        Used by both ``_run_one_session`` (phase sessions) and
        ``_run_bootstrap_session`` (bootstrap session that writes PLAN.md).
        Bootstrap callers pass ``phase_id=0`` and an ``archive_basename`` of
        the form ``bootstrap-attempt-<M>``; phase callers pass the active
        phase id and ``phase-<N>-attempt-<M>``.
        """
        # Clear stale sentinels BEFORE launch.
        self._clear_sentinels()

        self._archive_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = str(self._archive_dir / f"{archive_basename}.stdout.log")
        stderr_path = str(self._archive_dir / f"{archive_basename}.stderr.log")

        self._log_state(WrapperState.LAUNCHING, launch_state_detail)

        launch_t0 = time.time()
        try:
            popen = self.transport.launch_hermes(
                scaffold_root=str(self.scaffold_root),
                source_tag=str(self.scaffold_root),
                prompt=prompt,
                model=self.cfg.model,
                max_turns=self.cfg.max_turns_per_phase,
                omlx_api_key=self.omlx_api_key,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                resume_session_id=self._hermes_session_id,
            )
        except Exception as exc:
            raise WrapperError(f"launch_hermes failed: {exc}") from exc

        self._current_popen = popen

        stop_event = threading.Event()
        detected_event = threading.Event()
        poll_result = SentinelPollResult()
        poller = SentinelPoller(
            transport=self.transport,
            scaffold_root=str(self.scaffold_root),
            interval=self.cfg.poll_interval_seconds,
            stop_event=stop_event,
            detected_event=detected_event,
            result=poll_result,
        )
        poller.start()

        deadline = launch_t0 + self.cfg.phase_max_wall_clock_seconds
        sentinel_fired_at: Optional[float] = None

        # Main wait loop.
        try:
            while True:
                if self._sigint_received:
                    break
                if popen.poll() is not None:
                    break
                if detected_event.is_set() and sentinel_fired_at is None:
                    sentinel_fired_at = time.time()
                    self._log_state(
                        WrapperState.SENTINEL_DETECTED,
                        f"phase={phase_id} attempt={attempt}",
                    )
                if sentinel_fired_at is not None:
                    grace_deadline = (
                        sentinel_fired_at + self.cfg.sentinel_grace_seconds
                    )
                    if time.time() >= grace_deadline:
                        self._terminate_popen(popen)
                        break
                if time.time() >= deadline:
                    self._terminate_popen(popen)
                    break
                time.sleep(0.1)
        finally:
            stop_event.set()
            poller.join(timeout=2.0)

        # Drain — wait for popen to exit with a small ceiling.
        try:
            exit_code = popen.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            try:
                popen.kill()
            except Exception:
                pass
            try:
                exit_code = popen.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                exit_code = -1
        self._current_popen = None

        wall = int(time.time() - launch_t0)

        # Final snapshot of sentinel state (post-exit, in case race).
        try:
            end_present = self.transport.file_exists(
                str(self.scaffold_root / SESSION_END_SENTINEL_NAME)
            )
            esc_present = self.transport.file_exists(
                str(self.scaffold_root / SESSION_ESCALATE_SENTINEL_NAME)
            )
        except Exception:
            end_present = poll_result.end_seen
            esc_present = poll_result.escalate_seen

        sentinel_kind: Optional[str] = None
        if end_present and esc_present:
            sentinel_kind = "both"  # T16: anomaly. Treated as escalate.
        elif esc_present:
            sentinel_kind = "escalate-signal"
        elif end_present:
            sentinel_kind = "end-signal"

        # Classify exit reason.
        if esc_present:
            exit_reason = EXIT_REASON_ESCALATE
        elif end_present:
            exit_reason = EXIT_REASON_END
        elif time.time() >= deadline and not (end_present or esc_present):
            exit_reason = EXIT_REASON_TIMEOUT
        elif exit_code != 0:
            exit_reason = EXIT_REASON_CRASH
        else:
            exit_reason = EXIT_REASON_ANOMALOUS

        # Capture session JSON for archive (mtime fallback per F-1).
        archived_path = None
        hermes_session_id = self._hermes_session_id
        try:
            sj_path = self.transport.find_recent_session_json(
                source_tag=str(self.scaffold_root),
                since_epoch=launch_t0,
            )
            if sj_path:
                local_archive = (
                    self._archive_dir
                    / f"{archive_basename}-{exit_reason}.json"
                )
                self.transport.copy_to_local(sj_path, str(local_archive))
                archived_path = str(local_archive)
                # Try to extract session_id.
                try:
                    raw = local_archive.read_text(encoding="utf-8")
                    obj = json.loads(raw)
                    sid = obj.get("session_id") or obj.get("id")
                    if isinstance(sid, str) and sid:
                        hermes_session_id = sid
                        if self._hermes_session_id is None:
                            self._hermes_session_id = sid
                except Exception:
                    pass
        except Exception as exc:
            self.log.warning("session-json archive failed: %s", exc)

        return PhaseRunOutcome(
            exit_reason=exit_reason,
            exit_code=exit_code if exit_code is not None else -1,
            sentinel_kind=sentinel_kind,
            hermes_session_id=hermes_session_id,
            archived_session_path=archived_path,
            wall_clock_seconds=wall,
        )

    # ---- bootstrap session (writes PLAN.md from USER-PROMPT.md) -----

    # Sentinel phase id for bootstrap-mode bookkeeping (manifest entries
    # serialize this as JSON ``null``; the int form is used internally for
    # ``_attempt_counters`` keying and archive-basename construction).
    _BOOTSTRAP_PHASE_KEY = 0

    def _run_bootstrap_session(self, user_prompt_path: Path) -> PhaseRunOutcome:
        """Drive the parent's first session to write PLAN.md.

        Reads USER-PROMPT.md, prepends a short header instructing the parent
        to call ``write_plan_md`` (or ``write_file`` fallback) and then
        ``end_session_for_handoff``, launches Hermes, and returns the outcome.
        Caller (``run()``) verifies PLAN.md presence + parseability and
        decides whether to escalate or proceed into the phase loop.

        Per design §2 (BOOTSTRAP SESSION) + §4 (PLAN.md authored here).
        Reuses ``_run_session_core`` for launch/poll/archive symmetry with
        phase sessions; the only differences are prompt source, archive
        basename ("bootstrap-attempt-<M>"), and ``phase_id`` (0 internally,
        serialized as null in the manifest).
        """
        try:
            user_prompt = user_prompt_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise WrapperError(
                f"USER-PROMPT.md unreadable: {exc}"
            ) from exc
        attempt = self._next_attempt(self._BOOTSTRAP_PHASE_KEY)
        prompt = self._build_bootstrap_prompt(user_prompt, attempt)
        archive_basename = f"bootstrap-attempt-{attempt}"
        self._log_state(
            WrapperState.BOOTSTRAPPING,
            f"attempt={attempt} (writing PLAN.md from USER-PROMPT.md)",
        )
        return self._run_session_core(
            prompt=prompt,
            phase_id=self._BOOTSTRAP_PHASE_KEY,
            attempt=attempt,
            is_resume=False,
            archive_basename=archive_basename,
            launch_state_detail=f"bootstrap attempt={attempt}",
        )

    def _build_bootstrap_prompt(self, user_prompt: str, attempt: int) -> str:
        """Construct the bootstrap-session prompt.

        Wraps the operator's USER-PROMPT.md content with the orientation
        header the design's BOOTSTRAP SESSION block requires: classify,
        write PLAN.md, then end_session_for_handoff. The wrapper trusts only
        the on-disk PLAN.md (and post-bootstrap, verified-state.json); the
        parent's narrative is non-load-bearing.
        """
        lines = [
            "You are the parent agent in an r7.11 multi-session Hermes run.",
            "This is the BOOTSTRAP SESSION (no PLAN.md exists yet).",
            "Steps for this session:",
            "  1. Classify the task (β-fuse) and write PLAN.md via write_plan_md",
            "     (or write_file fallback) using the OBJECTIVE/PATHS/ACCEPTANCE",
            "     template — one '## Phase N: <title>' block per phase.",
            "  2. Optionally seed a todo list mirroring the phases.",
            "  3. Call end_session_for_handoff (completed_phase=null) when",
            "     PLAN.md is on disk; the wrapper will then resume per-phase.",
            "Do NOT call delegate_worker in this session; phase work begins",
            "in the next session, after the wrapper reads your PLAN.md.",
            "",
            f"Active scaffold_root: {self.scaffold_root}",
            f"Bootstrap attempt #: {attempt}",
            "",
            "USER TASK PROMPT:",
            user_prompt.rstrip(),
        ]
        return "\n".join(lines)

    def _build_bootstrap_manifest_entry(
        self,
        outcome: PhaseRunOutcome,
        wrapper_decision: str,
        *,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a manifest entry for a bootstrap session.

        ``phase_id`` is serialized as JSON ``null`` (the bootstrap session is
        not a phase). Internally we key ``_attempt_counters`` on
        ``_BOOTSTRAP_PHASE_KEY``; that's a wrapper-private detail.
        ``verify_state_snapshot`` reflects pre-/post-bootstrap state of the
        verified-state.json file; bootstrap itself does not write that file
        (see ``_VS_WRITE_FORBIDDEN_INVARIANT``).
        """
        attempt = self._attempt_counters.get(self._BOOTSTRAP_PHASE_KEY, 1)
        if self._verified_state_path.exists():
            try:
                snap = _verify_state_snapshot(
                    vs_mod.load(self._verified_state_path)
                )
            except Exception:
                snap = "bootstrap (verified-state.json present, parse failed)"
        else:
            snap = "pre-bootstrap (no verified-state.json)"
        entry: Dict[str, Any] = {
            "archived_at": _utc_now_iso(),
            "phase_id": None,
            "attempt": attempt,
            "exit_reason": outcome.exit_reason,
            "hermes_session_id": outcome.hermes_session_id,
            "sentinel_kind": outcome.sentinel_kind,
            "exit_code": outcome.exit_code,
            "wall_clock_seconds": outcome.wall_clock_seconds,
            "wrapper_decision": wrapper_decision,
            "verify_state_snapshot": snap,
            "prior_phase_id": None,
            "session_kind": "bootstrap",
        }
        if reason:
            entry["reason"] = reason
        return entry

    def _terminate_popen(self, popen: subprocess.Popen) -> None:
        """SIGTERM the process group; SIGKILL after 5s if still up."""
        try:
            pgid = os.getpgid(popen.pid)
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                popen.terminate()
            except Exception:
                pass
        # Wait briefly.
        for _ in range(50):  # 5s @ 100ms
            if popen.poll() is not None:
                return
            time.sleep(0.1)
        try:
            pgid = os.getpgid(popen.pid)
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                popen.kill()
            except Exception:
                pass

    def _snapshot_prior_session_json(self, phase_id: int, attempt: int) -> None:
        """Per Addendum A3: snapshot the live session JSON before --resume
        overwrites it. Best-effort; failures are warnings."""
        if not self._hermes_session_id:
            return
        # In production, the JSON lives at ~/.hermes/sessions/session_<id>.json
        # on the VM. We don't know the exact path without ssh; skip in test
        # transport (LocalFsTransport handles via `.test-session-json` hint).
        # The find_recent_session_json call after the run handles the archive.
        return

    # ---- manifest ---------------------------------------------------

    def _read_manifest(self) -> Dict[str, Any]:
        if not self._manifest_path.exists():
            return {"schema_version": "1.0", "entries": []}
        try:
            return json.loads(
                self._manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return {"schema_version": "1.0", "entries": []}

    def _append_manifest_entry(self, entry: Dict[str, Any]) -> None:
        current = self._read_manifest()
        current.setdefault("entries", []).append(entry)
        _atomic_write_json(self._manifest_path, current)

    def _build_manifest_entry(
        self,
        outcome: PhaseRunOutcome,
        decision_for_entry: Decision,
        wrapper_decision: str,
        state_at_archive: VerifiedState,
        prior_phase_id: Optional[int],
    ) -> Dict[str, Any]:
        phase_id = decision_for_entry.phase_id or 0
        attempt = self._attempt_counters.get(phase_id, 1)
        return {
            "archived_at": _utc_now_iso(),
            "phase_id": phase_id,
            "attempt": attempt,
            "exit_reason": outcome.exit_reason,
            "hermes_session_id": outcome.hermes_session_id,
            "sentinel_kind": outcome.sentinel_kind,
            "exit_code": outcome.exit_code,
            "wall_clock_seconds": outcome.wall_clock_seconds,
            "wrapper_decision": wrapper_decision,
            "verify_state_snapshot": _verify_state_snapshot(state_at_archive),
            "prior_phase_id": prior_phase_id,
        }

    # ---- decision ---------------------------------------------------

    def _decide(
        self, state: VerifiedState, sentinel_kind: Optional[str]
    ) -> Decision:
        """Wrapper-side decision logic per SC-5 (corrected case-3)."""
        # Escalate sentinel always wins.
        if sentinel_kind in ("escalate-signal", "both"):
            return Decision(
                action=DecisionAction.ESCALATE,
                phase_id=self._active_phase_id(state),
                reason="parent_called_escalate",
            )
        # Anomalous-exit threshold.
        if self._anomalous_exit_count > self.cfg.max_anomalous_exits:
            return Decision(
                action=DecisionAction.ESCALATE,
                phase_id=self._active_phase_id(state),
                reason="repeated_anomalous_exits",
            )
        return vs_mod.decide(state)

    def _active_phase_id(self, state: VerifiedState) -> Optional[int]:
        for entry in state.phase_state:
            if entry.status != PhaseStatus.VERIFIED_PASSED:
                return entry.id
        return None

    # ---- main run loop ---------------------------------------------

    def run(self, *, fresh: bool = False) -> int:
        """Drive the state machine through all phases. Returns exit code.

        Bootstrap-mode (per DESIGN-r7.11-architecture.md §2 BOOTSTRAP
        SESSION block): if PLAN.md is absent at run-start, the wrapper
        reads USER-PROMPT.md and drives a single bootstrap session whose
        job is to write PLAN.md. The wrapper does NOT touch
        verified-state.json during bootstrap; that's seeded post-bootstrap
        by ``_bootstrap_state_if_needed`` once a parseable PLAN.md exists.
        """
        self._install_sigint_handler()
        try:
            self._archive_dir.mkdir(parents=True, exist_ok=True)
            bootstrap_rc = self._maybe_run_bootstrap()
            if bootstrap_rc is not None:
                return bootstrap_rc
            self._bootstrap_state_if_needed(fresh=fresh)
            return self._main_loop()
        except ConfigError as exc:
            self._log_state(
                WrapperState.WRAPPER_ERROR, f"config error: {exc}"
            )
            print(f"hermes-multi: config error: {exc}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        except VPConfigError as exc:
            print(f"hermes-multi: verify-config error: {exc}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        except WrapperError as exc:
            self._log_state(
                WrapperState.WRAPPER_ERROR, f"wrapper error: {exc}"
            )
            self._record_wrapper_error(str(exc))
            print(f"hermes-multi: wrapper error: {exc}", file=sys.stderr)
            return EXIT_WRAPPER_ERROR
        except KeyboardInterrupt:
            self._handle_sigint_during_run()
            return EXIT_SIGINT

    def resume(self) -> int:
        """Resume after escalate-pause. Operator presumably investigated."""
        self._install_sigint_handler()
        try:
            self._archive_dir.mkdir(parents=True, exist_ok=True)
            if not self._verified_state_path.exists():
                raise WrapperError(
                    "cannot resume: verified-state.json missing; run "
                    "`hermes-multi run <scaffold>` first"
                )
            # Clear any lingering escalate sentinel (operator finished review).
            esc_path = (
                self.scaffold_root / SESSION_ESCALATE_SENTINEL_NAME
            )
            if esc_path.exists():
                self.transport.remove_file(str(esc_path))
            return self._main_loop()
        except ConfigError as exc:
            print(f"hermes-multi: config error: {exc}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        except WrapperError as exc:
            self._record_wrapper_error(str(exc))
            print(f"hermes-multi: wrapper error: {exc}", file=sys.stderr)
            return EXIT_WRAPPER_ERROR
        except KeyboardInterrupt:
            self._handle_sigint_during_run()
            return EXIT_SIGINT

    def _main_loop(self) -> int:
        # Hard ceiling on iterations; defends against pathological loops
        # the explicit decide() logic missed.
        max_iterations = 1000
        for _ in range(max_iterations):
            if self._sigint_received:
                return EXIT_SIGINT
            try:
                state = self._load_verified_state()
            except WrapperError:
                raise

            decision = vs_mod.decide(state)
            self._log_state(
                WrapperState.DECIDING,
                f"action={decision.action.value} phase={decision.phase_id} "
                f"reason={decision.reason}",
            )

            # Anomalous threshold check (independent of state.decide()).
            if self._anomalous_exit_count > self.cfg.max_anomalous_exits:
                self._record_terminal(
                    state,
                    decision_action=DECISION_ESCALATE,
                    reason="repeated_anomalous_exits",
                )
                print(
                    "hermes-multi: ESCALATE — "
                    f"anomalous_exit_count={self._anomalous_exit_count} "
                    f"exceeds max={self.cfg.max_anomalous_exits}",
                    file=sys.stderr,
                )
                return EXIT_ESCALATE

            if decision.action == DecisionAction.COMPLETE:
                self._log_state(WrapperState.COMPLETE, "all phases passed")
                self._record_terminal(
                    state,
                    decision_action=DECISION_SUCCESS,
                    reason="all phases verified",
                )
                print("hermes-multi: SUCCESS — all phases verified_passed")
                return EXIT_SUCCESS

            if decision.action == DecisionAction.ESCALATE:
                self._log_state(
                    WrapperState.ESCALATING,
                    f"phase={decision.phase_id} reason={decision.reason}",
                )
                self._record_terminal(
                    state,
                    decision_action=DECISION_ESCALATE,
                    reason=decision.reason,
                    prior_phase_id=decision.phase_id,
                )
                print(
                    f"hermes-multi: ESCALATE — phase={decision.phase_id} "
                    f"reason={decision.reason}",
                    file=sys.stderr,
                )
                return EXIT_ESCALATE

            # ADVANCE or REVISE → run a session.
            prior_phase_id = (
                decision.phase_id
                if decision.action == DecisionAction.REVISE
                else None
            )
            outcome = self._run_one_session(decision, state)
            self._log_state(
                WrapperState.HERMES_EXITED,
                f"exit_reason={outcome.exit_reason} "
                f"exit_code={outcome.exit_code} "
                f"sentinel={outcome.sentinel_kind} "
                f"wall={outcome.wall_clock_seconds}s",
            )

            # Update anomalous counter.
            if outcome.exit_reason in (
                EXIT_REASON_CRASH,
                EXIT_REASON_TIMEOUT,
                EXIT_REASON_ANOMALOUS,
            ):
                self._anomalous_exit_count += 1

            # Re-load state (verify_phase may have modified it).
            try:
                state_after = self._load_verified_state()
            except WrapperError:
                raise

            # Decide next action; this becomes the wrapper_decision tag.
            next_decision = self._decide(
                state_after, sentinel_kind=outcome.sentinel_kind
            )
            wrapper_decision_tag = self._decision_to_tag(next_decision)

            # ARCHIVING: append manifest entry.
            self._log_state(
                WrapperState.ARCHIVING,
                f"writing manifest entry for phase={decision.phase_id}",
            )
            entry = self._build_manifest_entry(
                outcome=outcome,
                decision_for_entry=decision,
                wrapper_decision=wrapper_decision_tag,
                state_at_archive=state_after,
                prior_phase_id=prior_phase_id,
            )
            self._append_manifest_entry(entry)

            # Check: was this an escalate-via-sentinel? terminate.
            if outcome.sentinel_kind in ("escalate-signal", "both"):
                self._log_state(
                    WrapperState.ESCALATING,
                    f"parent called escalate; sentinel={outcome.sentinel_kind}",
                )
                print(
                    "hermes-multi: ESCALATE — parent called "
                    f"escalate_to_operator (sentinel={outcome.sentinel_kind})",
                    file=sys.stderr,
                )
                return EXIT_ESCALATE

            # Otherwise loop with fresh decision.

        # Hit the iteration ceiling.
        raise WrapperError(
            f"main loop exceeded {max_iterations} iterations; aborting"
        )

    @staticmethod
    def _decision_to_tag(d: Decision) -> str:
        return {
            DecisionAction.ADVANCE: DECISION_ADVANCE,
            DecisionAction.REVISE: DECISION_REVISE,
            DecisionAction.ESCALATE: DECISION_ESCALATE,
            DecisionAction.COMPLETE: DECISION_SUCCESS,
        }[d.action]

    def _record_terminal(
        self,
        state: VerifiedState,
        *,
        decision_action: str,
        reason: str,
        prior_phase_id: Optional[int] = None,
    ) -> None:
        """Write a terminal manifest entry (no session ran)."""
        active = self._active_phase_id(state)
        entry = {
            "archived_at": _utc_now_iso(),
            "phase_id": active or 0,
            "attempt": 0,
            "exit_reason": "terminal",
            "hermes_session_id": None,
            "sentinel_kind": None,
            "exit_code": 0,
            "wall_clock_seconds": 0,
            "wrapper_decision": decision_action,
            "verify_state_snapshot": _verify_state_snapshot(state),
            "prior_phase_id": prior_phase_id,
            "reason": reason,
        }
        try:
            self._append_manifest_entry(entry)
        except Exception as exc:
            self.log.warning("terminal manifest write failed: %s", exc)

    def _record_wrapper_error(self, msg: str) -> None:
        try:
            state = self._load_verified_state()
            snap = _verify_state_snapshot(state)
        except Exception:
            snap = "verified-state unavailable"
        entry = {
            "archived_at": _utc_now_iso(),
            "phase_id": 0,
            "attempt": 0,
            "exit_reason": "wrapper_error",
            "hermes_session_id": None,
            "sentinel_kind": None,
            "exit_code": 0,
            "wall_clock_seconds": 0,
            "wrapper_decision": DECISION_WRAPPER_ERROR,
            "verify_state_snapshot": snap,
            "prior_phase_id": None,
            "error_message": msg,
        }
        try:
            self._append_manifest_entry(entry)
        except Exception:
            pass

    # ---- signals ----------------------------------------------------

    def _install_sigint_handler(self) -> None:
        def handler(signum, frame):
            self._sigint_received = True
            if self._current_popen is not None:
                try:
                    self._terminate_popen(self._current_popen)
                except Exception:
                    pass
        try:
            signal.signal(signal.SIGINT, handler)
        except ValueError:
            # Not in main thread (e.g., tests). Skip handler install.
            pass

    def _handle_sigint_during_run(self) -> None:
        entry = {
            "archived_at": _utc_now_iso(),
            "phase_id": 0,
            "attempt": 0,
            "exit_reason": "sigint",
            "hermes_session_id": None,
            "sentinel_kind": None,
            "exit_code": 130,
            "wall_clock_seconds": 0,
            "wrapper_decision": "wrapper_error",
            "verify_state_snapshot": "wrapper interrupted by SIGINT",
            "prior_phase_id": None,
        }
        try:
            self._append_manifest_entry(entry)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hermes-multi",
        description=(
            "Multi-session Hermes wrapper with verification gates. "
            "Reads PLAN.md + verified-state.json from <scaffold_root>; "
            "drives Hermes phase-by-phase; routes via verified-state.json. "
            "Bootstrap mode: if PLAN.md is absent at run-start, the wrapper "
            "reads USER-PROMPT.md and drives a single bootstrap session to "
            "author PLAN.md before entering the phase loop. Missing both "
            "files -> exit 4 (config error)."
        ),
    )
    sub = p.add_subparsers(dest="command", required=True)

    transport_help = (
        "transport for driving Hermes: 'ssh' (default; wrapper on Mac, "
        "Hermes on remote VM) or 'local' (wrapper and Hermes on the same "
        "host; no ssh, direct subprocess.Popen). 'local' is incompatible "
        "with --remote-host."
    )

    p_run = sub.add_parser("run", help="initial run (or pick up where you left off)")
    p_run.add_argument("scaffold_root", type=str)
    p_run.add_argument("--fresh", action="store_true",
                       help="reset verified-state.json from PLAN.md before running")
    p_run.add_argument("--remote-host", type=str, default=None,
                       help="override wrapper.remote_host from verify-config.json")
    p_run.add_argument("--transport", choices=["ssh", "local"], default="ssh",
                       help=transport_help)

    p_resume = sub.add_parser("resume", help="resume after escalate-pause")
    p_resume.add_argument("scaffold_root", type=str)
    p_resume.add_argument("--remote-host", type=str, default=None)
    p_resume.add_argument("--transport", choices=["ssh", "local"], default="ssh",
                          help=transport_help)

    p_status = sub.add_parser("status", help="read-only diagnostic")
    p_status.add_argument("scaffold_root", type=str)
    return p


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _cmd_status(scaffold_root: Path) -> int:
    if not scaffold_root.exists() or not scaffold_root.is_dir():
        print(
            f"hermes-multi status: scaffold_root not found: {scaffold_root}",
            file=sys.stderr,
        )
        return EXIT_WRAPPER_ERROR
    vs_path = scaffold_root / "verified-state.json"
    print(f"scaffold_root: {scaffold_root}")
    if vs_path.exists():
        try:
            state = vs_mod.load(vs_path)
            print(f"verified-state.json: {_verify_state_snapshot(state)}")
        except Exception as exc:
            print(f"verified-state.json: parse error: {exc}")
    else:
        print("verified-state.json: <absent — not bootstrapped>")
    end_p = scaffold_root / SESSION_END_SENTINEL_NAME
    esc_p = scaffold_root / SESSION_ESCALATE_SENTINEL_NAME
    print(f"session-end sentinel: {'present' if end_p.exists() else 'absent'}")
    print(f"session-escalate sentinel: {'present' if esc_p.exists() else 'absent'}")
    manifest = scaffold_root / ".session-archive" / "manifest.json"
    if manifest.exists():
        try:
            obj = json.loads(manifest.read_text(encoding="utf-8"))
            entries = obj.get("entries", [])
            print(f"manifest entries: {len(entries)}")
            if entries:
                last = entries[-1]
                print(
                    f"last entry: phase={last.get('phase_id')} "
                    f"attempt={last.get('attempt')} "
                    f"exit_reason={last.get('exit_reason')} "
                    f"wrapper_decision={last.get('wrapper_decision')}"
                )
        except Exception as exc:
            print(f"manifest: parse error: {exc}")
    else:
        print("manifest: <absent>")
    return EXIT_SUCCESS


def _construct_transport(args, cfg: WrapperConfig) -> Transport:
    """Build the Transport per --transport flag and CLI args.

    Defaults to SshTransport(cfg.remote_host). When --transport local is
    set, returns a LocalProcessTransport; --remote-host is mutually
    exclusive with --transport local (exits 4 on conflict).
    """
    transport_kind = getattr(args, "transport", "ssh") or "ssh"
    if transport_kind == "local":
        if getattr(args, "remote_host", None):
            print(
                "hermes-multi: error: --transport local is incompatible "
                "with --remote-host",
                file=sys.stderr,
            )
            sys.exit(EXIT_CONFIG_ERROR)
        return LocalProcessTransport()
    # ssh path (default; preserves backward compat).
    host = getattr(args, "remote_host", None) or cfg.remote_host
    return SshTransport(host)


def _make_wrapper(args, transport: Optional[Transport] = None) -> Wrapper:
    scaffold_root = Path(args.scaffold_root).resolve()
    if not scaffold_root.exists():
        raise WrapperError(f"scaffold_root not found: {scaffold_root}")
    verify_config_path = scaffold_root / "verify-config.json"
    cfg = load_wrapper_config(
        verify_config_path if verify_config_path.exists() else None
    )
    if getattr(args, "remote_host", None):
        cfg.remote_host = args.remote_host
    if transport is None:
        transport = _construct_transport(args, cfg)
    omlx_key = os.environ.get("OMLX_API_KEY")
    return Wrapper(
        scaffold_root=scaffold_root,
        transport=transport,
        wrapper_config=cfg,
        omlx_api_key=omlx_key,
    )


def main(argv: Optional[List[str]] = None) -> int:
    _setup_logging()
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.command == "status":
        return _cmd_status(Path(args.scaffold_root).resolve())
    try:
        wrapper = _make_wrapper(args)
    except ConfigError as exc:
        print(f"hermes-multi: config error: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except WrapperError as exc:
        print(f"hermes-multi: wrapper error: {exc}", file=sys.stderr)
        return EXIT_WRAPPER_ERROR
    if args.command == "run":
        return wrapper.run(fresh=getattr(args, "fresh", False))
    if args.command == "resume":
        return wrapper.resume()
    parser.error(f"unknown command: {args.command}")
    return EXIT_GENERIC_FAILURE


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "EXIT_SUCCESS",
    "EXIT_GENERIC_FAILURE",
    "EXIT_ESCALATE",
    "EXIT_WRAPPER_ERROR",
    "EXIT_CONFIG_ERROR",
    "EXIT_CANONICAL_DRIFT",
    "EXIT_SIGINT",
    "WrapperError",
    "ConfigError",
    "WrapperConfig",
    "load_wrapper_config",
    "Transport",
    "LocalFsTransport",
    "SshTransport",
    "LocalProcessTransport",
    "WrapperState",
    "EXIT_REASON_END",
    "EXIT_REASON_ESCALATE",
    "EXIT_REASON_TIMEOUT",
    "EXIT_REASON_CRASH",
    "EXIT_REASON_ANOMALOUS",
    "BOOTSTRAP_FAILED_NO_PLAN",
    "BOOTSTRAP_FAILED_UNPARSEABLE_PLAN",
    "BOOTSTRAP_FAILED_ANOMALOUS_EXIT",
    "DECISION_ADVANCE",
    "DECISION_REVISE",
    "DECISION_ESCALATE",
    "DECISION_SUCCESS",
    "DECISION_WRAPPER_ERROR",
    "Wrapper",
    "PhaseRunOutcome",
    "main",
]
