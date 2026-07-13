#!/usr/bin/env bash
# run-codex-cell.sh — AgentFW r9 eval harness: one codex eval cell with a WORKING two-turn resume.
#
# Fixes the 2026-07-13 Phase-2 failure: sandbox flags valid on `codex exec` (-s/-C) were passed to
# `codex exec resume`, which rejects them ("error: unexpected argument '-s' found" — see
# evaluation/transcripts-2026-07-13/gt4-codex.md). On resume, sandbox/config are expressed ONLY as
# `-c key=value` overrides (verified against `codex exec resume --help`, codex-cli 0.144.1):
#
#   turn 1:  codex exec  --skip-git-repo-check -s workspace-write -C <fixture> -c mcp_servers={} <prompt>
#   turn 2:  codex exec resume --skip-git-repo-check -c mcp_servers={} \
#                -c sandbox_mode="workspace-write" <SESSION_ID> <prompt>
#
# Usage:
#   run-codex-cell.sh --selftest-two-turn
#   run-codex-cell.sh --gt <id> --prompt-file <file> [--phase2-file <file>] [--seed-dir <dir>]
#                     [--out <transcript.md>] [--timeout <secs>] [--low-effort]
#
# Per-GT flow: hermetic mktemp fixture laid out per adapters/codex/INSTALL.md (marker-wrapped
# AGENTS.md block at fixture root; repo-scope .agents/skills/agentfw/ with SKILL.md + policy/ +
# tools/validate-plan + capability.yaml), optionally seeded from --seed-dir. Turn 1 runs the GT
# prompt; the session_id is extracted and its rollout file under ~/.codex/sessions verified; turn 2
# injects the Phase-2 prompt via `codex exec resume`. `PHASE2-DELIVERED: <n> bytes` is emitted into
# the transcript HEADER only when second-turn model output is non-empty. The transcript is
# sanitized (/Users/<name> -> /Users/USER, MCP-connection noise stripped) and the script REFUSES
# (nonzero exit, no transcript emitted) if the sanitized transcript would still fail the hygiene
# sweep: rmcp::transport|AuthRequired|www_authenticate|\.well-known/oauth|/Users/[a-z]
set -u -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HARNESS_DIR="$REPO_ROOT/evaluation/harness"
ADAPTER_DIR="$REPO_ROOT/adapters/codex"
HYGIENE_RE='rmcp::transport|AuthRequired|www_authenticate|\.well-known/oauth|/Users/[a-z]'

die() { echo "run-codex-cell: ERROR: $*" >&2; exit 1; }

# --- args -------------------------------------------------------------------
SELFTEST=0
GT_ID=""
PROMPT_FILE=""
PHASE2_FILE=""
SEED_DIR=""
OUT_FILE=""
TURN_TIMEOUT=1800
LOW_EFFORT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --selftest-two-turn) SELFTEST=1; shift ;;
    --gt)          GT_ID="$2"; shift 2 ;;
    --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
    --phase2-file) PHASE2_FILE="$2"; shift 2 ;;
    --seed-dir)    SEED_DIR="$2"; shift 2 ;;
    --out)         OUT_FILE="$2"; shift 2 ;;
    --timeout)     TURN_TIMEOUT="$2"; shift 2 ;;
    --low-effort)  LOW_EFFORT=1; shift ;;
    -h|--help)     sed -n '2,22p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ "$SELFTEST" -eq 1 ]; then
  GT_ID="gt0-selftest"
  OUT_FILE="$HARNESS_DIR/selftest-out/gt0-selftest-codex.md"
  TURN_TIMEOUT=300
  LOW_EFFORT=1
  PROMPT_TEXT="Reply with the single word READY"
  PHASE2_TEXT="Reply with exactly PHASE2-ACK"
else
  [ -n "$GT_ID" ] || die "--gt <id> is required (or use --selftest-two-turn)"
  [ -n "$PROMPT_FILE" ] && [ -f "$PROMPT_FILE" ] || die "--prompt-file <file> is required and must exist"
  PROMPT_TEXT="$(cat "$PROMPT_FILE")"
  PHASE2_TEXT=""
  if [ -n "$PHASE2_FILE" ]; then
    [ -f "$PHASE2_FILE" ] || die "--phase2-file does not exist: $PHASE2_FILE"
    PHASE2_TEXT="$(cat "$PHASE2_FILE")"
  fi
  [ -n "$OUT_FILE" ] || OUT_FILE="$HARNESS_DIR/out/${GT_ID}-codex.md"
fi
[ -z "$SEED_DIR" ] || [ -d "$SEED_DIR" ] || die "--seed-dir does not exist: $SEED_DIR"

command -v codex >/dev/null 2>&1 || die "codex CLI not found on PATH"
CODEX_VERSION="$(codex --version 2>/dev/null | head -1)"

# --- shell-level timeout (macOS ships no coreutils timeout; perl alarm is the guard) ----------
# alarm(2) survives exec, so the exec'd codex gets SIGALRM at the deadline -> exit 142 (128+14).
with_timeout() { # with_timeout <secs> <cmd...>
  perl -e 'alarm shift; exec @ARGV or exit 127;' "$@"
}
TIMEOUT_EXIT=142

# --- fixture: hermetic mktemp dir laid out per adapters/codex/INSTALL.md ----------------------
FIXTURE="$(mktemp -d)" || die "mktemp failed"
WORK="$(mktemp -d)"    || die "mktemp failed"

if [ -n "$SEED_DIR" ]; then
  cp -R "$SEED_DIR"/. "$FIXTURE"/ || die "seeding fixture from $SEED_DIR failed"
fi

# 1. Marker-wrapped bootloader block at the fixture (repo) root.
{
  echo '<!-- AGENTFW:BEGIN r9 -->'
  cat "$ADAPTER_DIR/AGENTS.md"
  echo '<!-- AGENTFW:END r9 -->'
} > "$FIXTURE/AGENTS.md"

# 2. Repo-scope skill: .agents/skills/agentfw/ with SKILL.md + policy copy + validator + capability contract.
SKILL_DST="$FIXTURE/.agents/skills/agentfw"
mkdir -p "$SKILL_DST/tools"
cp "$ADAPTER_DIR/skills/agentfw/SKILL.md" "$SKILL_DST/SKILL.md"
cp -R "$REPO_ROOT/policy" "$SKILL_DST/policy"
cp "$REPO_ROOT/tools/validate-plan" "$SKILL_DST/tools/validate-plan"
chmod +x "$SKILL_DST/tools/validate-plan"
cp "$ADAPTER_DIR/capability.yaml" "$SKILL_DST/capability.yaml"

# 3. Fresh git repo (matches the 2026-07-13 fixture pattern).
git -C "$FIXTURE" init -q
git -C "$FIXTURE" add -A
git -C "$FIXTURE" -c user.name='agentfw-eval' -c user.email='eval@localhost' commit -qm 'eval fixture' >/dev/null 2>&1 || true

EFFORT_ARGS=()
[ "$LOW_EFFORT" -eq 1 ] && EFFORT_ARGS=(-c 'model_reasoning_effort="low"')

# --- turn 1: codex exec (sandbox confined to the fixture dir; -s/-C are valid HERE) -----------
T1_LOG="$WORK/turn1.log"
T1_MSG="$WORK/turn1-last-message.txt"
( cd "$FIXTURE" && with_timeout "$TURN_TIMEOUT" \
    codex exec --skip-git-repo-check -s workspace-write -C "$FIXTURE" \
      -c 'mcp_servers={}' "${EFFORT_ARGS[@]}" \
      -o "$T1_MSG" "$PROMPT_TEXT" </dev/null ) >"$T1_LOG" 2>&1
T1_EXIT=$?
[ "$T1_EXIT" -eq "$TIMEOUT_EXIT" ] && echo "run-codex-cell: turn 1 hit the ${TURN_TIMEOUT}s kill window" >&2

SESSION_ID="$(grep -Eio 'session[ _]id:?[[:space:]]+[0-9a-f-]{36}' "$T1_LOG" | grep -Eo '[0-9a-f-]{36}' | head -1)"
if [ -z "$SESSION_ID" ]; then
  echo "run-codex-cell: turn 1 produced no session id (exit $T1_EXIT). Output follows:" >&2
  cat "$T1_LOG" >&2
  exit 1
fi
[ "$T1_EXIT" -eq 0 ] || { echo "run-codex-cell: turn 1 exit $T1_EXIT. Output follows:" >&2; cat "$T1_LOG" >&2; exit 1; }

# --- rollout verification: a session file for this id must exist under ~/.codex/sessions ------
ROLLOUT="$(find "$HOME/.codex/sessions" -type f -name "*${SESSION_ID}*" 2>/dev/null | head -1)"
if [ -n "$ROLLOUT" ]; then
  ROLLOUT_STATUS="verified-present (${ROLLOUT})"
else
  ROLLOUT_STATUS="NOT FOUND"
  echo "run-codex-cell: WARNING: no rollout file for session $SESSION_ID under ~/.codex/sessions" >&2
fi

# --- turn 2: codex exec resume — ONLY -c overrides; NEVER -s/-C (resume rejects them) ---------
T2_LOG="$WORK/turn2.log"
T2_MSG="$WORK/turn2-last-message.txt"
T2_EXIT=""
PHASE2_BYTES=0
if [ -n "$PHASE2_TEXT" ]; then
  ( cd "$FIXTURE" && with_timeout "$TURN_TIMEOUT" \
      codex exec resume --skip-git-repo-check \
        -c 'mcp_servers={}' -c 'sandbox_mode="workspace-write"' "${EFFORT_ARGS[@]}" \
        -o "$T2_MSG" "$SESSION_ID" "$PHASE2_TEXT" </dev/null ) >"$T2_LOG" 2>&1
  T2_EXIT=$?
  [ "$T2_EXIT" -eq "$TIMEOUT_EXIT" ] && echo "run-codex-cell: turn 2 hit the ${TURN_TIMEOUT}s kill window" >&2
  if [ -s "$T2_MSG" ]; then
    PHASE2_BYTES=$(wc -c < "$T2_MSG" | tr -d ' ')
  fi
fi

# --- assemble + sanitize ----------------------------------------------------------------------
sanitize() { # operator identity out; MCP-connection error noise stripped
  sed -E -e '/rmcp::transport/d' \
         -e '/ERROR:? +MCP client/d' \
         -e 's#/Users/[a-z][a-zA-Z0-9._-]*#/Users/USER#g'
}

RAW="$WORK/transcript.raw.md"
{
  echo "<!-- generated by evaluation/harness/run-codex-cell.sh $(date -u +%Y-%m-%dT%H:%M:%SZ) -->"
  echo "# ${GT_ID} — codex cell"
  echo "codex_cli: ${CODEX_VERSION}"
  echo "fixture: ${FIXTURE}"
  echo "session_id: ${SESSION_ID}"
  echo "rollout_file: ${ROLLOUT_STATUS}"
  echo "turn1_exit: ${T1_EXIT}"
  if [ -n "$PHASE2_TEXT" ]; then
    echo "turn2_exit: ${T2_EXIT}"
    if [ "$PHASE2_BYTES" -gt 0 ]; then
      echo "PHASE2-DELIVERED: ${PHASE2_BYTES} bytes"
    fi
  fi
  echo
  echo "===== PHASE 1 (codex exec) ====="
  echo
  cat "$T1_LOG"
  if [ -n "$PHASE2_TEXT" ]; then
    echo
    echo "===== PHASE 2 (codex exec resume ${SESSION_ID}) ====="
    echo
    echo "injected prompt: ${PHASE2_TEXT}"
    echo
    cat "$T2_LOG"
  fi
} > "$RAW"

SANITIZED="$WORK/transcript.md"
sanitize < "$RAW" > "$SANITIZED"

# --- hygiene gate: REFUSE (no transcript, nonzero exit) if the sweep still matches ------------
if grep -qE "$HYGIENE_RE" "$SANITIZED"; then
  echo "run-codex-cell: REFUSED — sanitized transcript still fails the hygiene sweep; no transcript emitted." >&2
  echo "matching lines:" >&2
  grep -nE "$HYGIENE_RE" "$SANITIZED" | head -20 >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT_FILE")"
cp "$SANITIZED" "$OUT_FILE"
echo "run-codex-cell: transcript -> $OUT_FILE (session_id: $SESSION_ID)"

# --- phase-2 delivery is the contract: fail loudly when it did not happen --------------------
if [ -n "$PHASE2_TEXT" ]; then
  if [ "$PHASE2_BYTES" -eq 0 ]; then
    echo "run-codex-cell: FAIL — Phase-2 second-turn model output is empty (exit ${T2_EXIT}); transcript kept as evidence." >&2
    exit 1
  fi
  if [ "$T2_EXIT" -ne 0 ]; then
    echo "run-codex-cell: FAIL — turn 2 exited ${T2_EXIT}; transcript kept as evidence." >&2
    exit 1
  fi
fi
exit 0
