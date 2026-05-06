#!/usr/bin/env python3
"""launch-q.py — invoke `hermes chat -q ...` with a wall-clock timeout.

`gtimeout`/`timeout` aren't always available on Mac. Stdlib subprocess.run
handles the deadline. Mirrors the launch shape `hermes_multi.py:354` used at
r7.11 item 9.

Usage:
  launch-q.py --scaffold-root PATH --prompt "..." --log PATH \
              [--timeout-seconds 5400] [--hermes-bin PATH] \
              [--skill r7-11-orchestrate] [--model gemma-4-26b-a4b-it-8bit] \
              [--max-turns 40]

Exit code:
  - whatever hermes chat -q returns
  - 124 if the wall-clock timeout fires
  - 125 on subprocess launch failure
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--scaffold-root", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--timeout-seconds", type=int, default=5400)
    p.add_argument("--hermes-bin",
                   default=os.path.expanduser("~/Life-AI/hermes-agent/venv/bin/hermes"))
    p.add_argument("--skill", default="r7-11-orchestrate")
    p.add_argument("--model", default="gemma-4-26b-a4b-it-8bit")
    p.add_argument("--max-turns", type=int, default=40)
    args = p.parse_args()

    cmd = [
        args.hermes_bin, "chat", "-q", args.prompt,
        "-s", args.skill, "-m", args.model,
        "--max-turns", str(args.max_turns),
    ]

    log_f = open(args.log, "a")
    log_f.write("=== launch-q ===\n")
    log_f.write(f"cmd: {shlex.join(cmd)}\n")
    log_f.write(f"scaffold_root: {args.scaffold_root}\n")
    log_f.write(f"timeout_seconds: {args.timeout_seconds}\n")
    log_f.write(f"started_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    log_f.write("---\n")
    log_f.flush()

    try:
        result = subprocess.run(
            cmd, stdout=log_f, stderr=subprocess.STDOUT,
            timeout=args.timeout_seconds,
        )
        ec = result.returncode
    except subprocess.TimeoutExpired:
        log_f.write(f"\n=== HALT: timeout after {args.timeout_seconds}s ===\n")
        ec = 124
    except FileNotFoundError as e:
        log_f.write(f"\n=== launch failed: {e} ===\n")
        ec = 125
    finally:
        log_f.write(f"\nended_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        log_f.write(f"launch_exit_code: {ec}\n")
        log_f.close()
    return ec


if __name__ == "__main__":
    sys.exit(main())
