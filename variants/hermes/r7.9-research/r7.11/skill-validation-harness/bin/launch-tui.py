#!/usr/bin/env python3
"""launch-tui.py — drive `hermes chat --tui -s r7-11-orchestrate` under a pty.

Per Brian's call (option A): the operator's deployment path is the TUI, so
the campaign tests against the TUI, not in-process AIAgent. Stdlib pty
only — no pexpect dep.

Usage:
  launch-tui.py --scaffold-root PATH --prompt "..." --log PATH \
                [--timeout-seconds 5400] [--hermes-bin PATH] \
                [--skill r7-11-orchestrate] [--done-marker MARKER]...

Behavior:
  - Spawns hermes under a pty with the skill preloaded.
  - Waits HERMES_BOOT_DELAY seconds, types the prompt.
  - Reads pty output to --log until any --done-marker is seen, or timeout.
  - On done: 2s settle, then SIGTERM the process group, then exit 0.
  - On timeout: SIGTERM, exit 124 (matches `timeout(1)`).
  - On hermes crash (proc exits non-zero before any marker): exit that code.

Output:
  Raw pty bytes (ANSI included) to --log. Let analysis ANSI-strip later.
"""

from __future__ import annotations

import argparse
import errno
import os
import pty
import select
import signal
import subprocess
import sys
import time

DEFAULT_DONE_MARKERS = [b"r7.11 SUCCESS", b"r7.11 ESCALATE", b"r7.11 STOP"]
HERMES_BOOT_DELAY = 4.0
SETTLE_AFTER_DONE = 2.0
READ_CHUNK = 4096
SELECT_INTERVAL = 5.0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--scaffold-root", required=True)
    p.add_argument("--prompt", required=True, help="Text to send to hermes after boot")
    p.add_argument("--log", required=True, help="Path for raw pty output")
    p.add_argument("--timeout-seconds", type=int, default=5400)
    p.add_argument("--hermes-bin", default=os.path.expanduser("~/Life-AI/hermes-agent/venv/bin/hermes"))
    p.add_argument("--skill", default="r7-11-orchestrate")
    p.add_argument("--done-marker", action="append", default=None,
                   help="Repeatable. Default markers are r7.11 SUCCESS/ESCALATE/STOP.")
    p.add_argument("--model", default=None,
                   help="Optional --model to pass to hermes chat (uses config default if omitted)")
    args = p.parse_args()

    markers = [m.encode() for m in (args.done_marker or [])] or DEFAULT_DONE_MARKERS

    cmd = [args.hermes_bin, "chat", "--tui", "-s", args.skill]
    if args.model:
        cmd.extend(["-m", args.model])

    master_fd, slave_fd = pty.openpty()
    log_f = open(args.log, "wb")

    log_f.write(b"=== launch-tui ===\n")
    log_f.write(f"cmd: {cmd}\n".encode())
    log_f.write(f"scaffold_root: {args.scaffold_root}\n".encode())
    log_f.write(f"timeout_seconds: {args.timeout_seconds}\n".encode())
    log_f.write(f"started_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n".encode())
    log_f.write(b"---\n")
    log_f.flush()

    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
        start_new_session=True,
    )
    os.close(slave_fd)

    time.sleep(HERMES_BOOT_DELAY)
    if proc.poll() is not None:
        log_f.write(f"\n=== hermes exited during boot, code={proc.returncode} ===\n".encode())
        log_f.close()
        return proc.returncode or 1

    os.write(master_fd, args.prompt.encode() + b"\n")

    deadline = time.time() + args.timeout_seconds
    buf = b""
    matched_marker: bytes | None = None
    exit_code = 0
    try:
        while time.time() < deadline:
            timeout = min(SELECT_INTERVAL, deadline - time.time())
            rfds, _, _ = select.select([master_fd], [], [], timeout)
            if rfds:
                try:
                    data = os.read(master_fd, READ_CHUNK)
                except OSError as e:
                    if e.errno == errno.EIO:
                        break
                    raise
                if not data:
                    break
                log_f.write(data)
                log_f.flush()
                buf = (buf + data)[-65536:]
                for m in markers:
                    if m in buf:
                        matched_marker = m
                        break
                if matched_marker:
                    break
            if proc.poll() is not None:
                log_f.write(f"\n=== hermes exited, code={proc.returncode} ===\n".encode())
                exit_code = proc.returncode or 0
                break
        else:
            log_f.write(b"\n=== HALT: timeout ===\n")
            exit_code = 124

        if matched_marker:
            log_f.write(f"\n=== marker matched: {matched_marker.decode()} ===\n".encode())
            time.sleep(SETTLE_AFTER_DONE)
    finally:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                proc.wait()
        os.close(master_fd)
        log_f.write(f"\nended_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n".encode())
        log_f.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
