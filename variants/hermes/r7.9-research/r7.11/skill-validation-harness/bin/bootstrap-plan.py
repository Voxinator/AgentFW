#!/usr/bin/env python3
"""bootstrap-plan.py — author PLAN.md in a SEPARATE hermes session.

Mirrors r7.11's hermes_multi.py:_build_bootstrap_prompt (lines 1266-1294).
Key methodology point: USER-PROMPT.md content is INLINED into the prompt,
NOT read from disk by the session. This is load-bearing — the bootstrap
session never gets implicit scaffold-filesystem awareness, which is what
biases the orchestrator-skill toward fitting PLAN.md to existing stub
files.

Pre-flight 2b-subproc trial 1 (broken bootstrap, archived 2026-05-04)
established: a bootstrap that READS USER-PROMPT.md from disk reproduces
the same scaffold-anchored authoring failure as the orchestrator-skill.
The fix is to inline USER-PROMPT content so the session's only context
about the task is the prompt itself.

Usage:
  bootstrap-plan.py --scaffold-root PATH --log PATH \
                    [--timeout-seconds 300]

After successful exit, PLAN.md should exist at <scaffold-root>/PLAN.md.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time

# Mirrors r7.11 hermes_multi.py:_build_bootstrap_prompt (lines 1275-1293).
# Brief, no template, no scaffold-filesystem instructions. USER-PROMPT
# content is appended verbatim. Adapted: drop end_session_for_handoff
# (legacy bash-wrapper sentinel) — bootstrap exits naturally after
# write_plan_md returns.
BOOTSTRAP_PROMPT_TEMPLATE = """\
You are the parent agent in an r7.11 multi-session run.
This is the BOOTSTRAP SESSION (no PLAN.md exists yet).
Steps for this session:
  1. Classify the task and write PLAN.md via write_plan_md
     (or write_file fallback) using the OBJECTIVE/PATHS/ACCEPTANCE
     template — one '## Phase N: <title>' block per phase.
  2. Optionally seed a todo list mirroring the phases.
  3. After PLAN.md is on disk, your final message must be:
     PLAN.md authored.
Do NOT call delegate_task in this session; phase work begins
in the next session, after the wrapper reads your PLAN.md.

Active scaffold_root: {scaffold_root}

USER TASK PROMPT:
{user_prompt}
"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--scaffold-root", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--timeout-seconds", type=int, default=300)
    p.add_argument("--hermes-bin",
                   default=os.path.expanduser("~/Life-AI/hermes-agent/venv/bin/hermes"))
    p.add_argument("--model", default="gemma-4-26b-a4b-it-8bit")
    p.add_argument("--max-turns", type=int, default=8)
    args = p.parse_args()

    # Inline USER-PROMPT.md content into the bootstrap prompt — this is
    # load-bearing for r7.11 fidelity (see module docstring).
    user_prompt_path = os.path.join(args.scaffold_root, "USER-PROMPT.md")
    try:
        user_prompt = open(user_prompt_path).read().rstrip()
    except OSError as e:
        sys.stderr.write(f"FATAL: cannot read {user_prompt_path}: {e}\n")
        return 2

    prompt = BOOTSTRAP_PROMPT_TEMPLATE.format(
        scaffold_root=args.scaffold_root,
        user_prompt=user_prompt,
    )

    cmd = [
        args.hermes_bin, "chat", "-q", prompt,
        "-m", args.model,
        "--max-turns", str(args.max_turns),
    ]

    log_f = open(args.log, "a")
    log_f.write("=== bootstrap-plan ===\n")
    log_f.write(f"cmd: {shlex.join(cmd[:3])} <prompt-elided> {' '.join(cmd[4:])}\n")
    log_f.write(f"scaffold_root: {args.scaffold_root}\n")
    log_f.write(f"timeout_seconds: {args.timeout_seconds}\n")
    log_f.write(f"started_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    log_f.write(f"--- bootstrap prompt ({len(prompt)} chars) ---\n")
    log_f.write(prompt + "\n")
    log_f.write("---\n")
    log_f.flush()

    plan_path = os.path.join(args.scaffold_root, "PLAN.md")
    plan_existed_before = os.path.exists(plan_path)

    try:
        result = subprocess.run(
            cmd, stdout=log_f, stderr=subprocess.STDOUT,
            timeout=args.timeout_seconds,
        )
        ec = result.returncode
    except subprocess.TimeoutExpired:
        log_f.write(f"\n=== HALT: bootstrap timeout after {args.timeout_seconds}s ===\n")
        ec = 124
    except FileNotFoundError as e:
        log_f.write(f"\n=== bootstrap launch failed: {e} ===\n")
        ec = 125
    finally:
        log_f.write(f"\nended_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

    if ec == 0 and not os.path.exists(plan_path):
        log_f.write(f"\n=== bootstrap exited 0 but PLAN.md not at {plan_path} ===\n")
        ec = 126
    log_f.write(f"bootstrap_exit_code: {ec}\n")
    log_f.write(f"plan_existed_before: {plan_existed_before}\n")
    log_f.write(f"plan_present_after: {os.path.exists(plan_path)}\n")
    log_f.close()
    return ec


if __name__ == "__main__":
    sys.exit(main())
