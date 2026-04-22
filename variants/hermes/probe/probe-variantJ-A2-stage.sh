#!/usr/bin/env bash
# probe-variantJ-A2-stage.sh — Stage/unstage the r7.7 A2 write-before-claim
# (detect-only) fabrication gate on ubuntu-vm.
#
# USAGE:
#   ./probe-variantJ-A2-stage.sh stage      # deploy gate module + patch run_agent.py
#   ./probe-variantJ-A2-stage.sh unstage    # restore run_agent.py backup + remove gate module
#   ./probe-variantJ-A2-stage.sh status     # STAGED / UNSTAGED / PARTIAL
#
# SCOPE (narrow, per r7.7 operator-confirmed 2026-04-20):
#   * Detect-only gate; runs ONCE at the terminal `_persist_session` call.
#   * Populates `self._a2_gate_outcome` ("CLEAN" | "FABRICATED" | "ERROR"),
#     which _save_session_log emits as a top-level `a2_gate_outcome` field
#     in the session JSON.
#   * Enabled at runtime via env var `HERMES_WRITE_BEFORE_CLAIM_GATE=1`.
#   * No retry, no correction, no re-inference.
#
# SAFETY:
#   * Backup suffix `.probe-r7.7-orig` (distinct from r7.4's `.probe-r7.4-orig`
#     and r7's `.probe-d-orig`).
#   * Idempotent: re-running `stage` is a no-op if already staged
#     (md5-compared files, grep-gated patch insertions).
#   * Fails fast on unexpected state; does NOT auto-rollback partial stage.
#
# DOES NOT:
#   * Commit, push, or open any PR.
#   * Enable the gate env var automatically (operator must set
#     `export HERMES_WRITE_BEFORE_CLAIM_GATE=1` in probe runner env).

set -euo pipefail

LOCAL_GATE="/Users/briantaylor/Projects/AgentFW/variants/hermes/write_before_claim_gate.py"
REMOTE_HOST="ubuntu-vm"
BAK_SUFFIX=".probe-r7.7-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantJ-A2-stage] $*"; }

ssh_run() { ssh "$REMOTE_HOST" "$@"; }

md5_remote() { ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }
md5_local()  { md5 -q "$1" 2>/dev/null; }

# --- preflight ---
[[ -f "$LOCAL_GATE" ]] || die "missing local gate: $LOCAL_GATE"

# Pre-resolve the remote home so scp destinations are fully-qualified paths.
# scp does NOT shell-expand `$HOME` / `~` on the remote destination (it treats
# the path literally), so we must substitute a real absolute path ourselves.
# ssh_run contexts (where the remote login shell evaluates the command) still
# work with `$HOME`/`~`, but this script now uses the resolved constants for
# consistency.
REMOTE_HOME=$(ssh "$REMOTE_HOST" 'echo $HOME' 2>/dev/null | tr -d '\r' | head -1)
[[ -n "$REMOTE_HOME" ]] || die "could not resolve \$HOME on $REMOTE_HOST"
REMOTE_GATE_DIR="$REMOTE_HOME/.hermes/hermes-agent/agent"
REMOTE_GATE="$REMOTE_HOME/.hermes/hermes-agent/agent/write_before_claim_gate.py"
REMOTE_RUNAGENT="$REMOTE_HOME/.hermes/hermes-agent/run_agent.py"

# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------

cmd_stage() {
  log "Staging Variant J A2 (write-before-claim detect-only gate)..."

  local local_md5 remote_md5
  local_md5=$(md5_local "$LOCAL_GATE")
  log "  local write_before_claim_gate.py md5: $local_md5"

  # 1. Ensure remote gate dir exists, then copy module (idempotent).
  ssh_run "mkdir -p $REMOTE_GATE_DIR && touch $REMOTE_GATE_DIR/__init__.py" \
    || die "could not create remote gate dir"
  remote_md5=$(md5_remote "$REMOTE_GATE")
  if [[ "$remote_md5" == "$local_md5" ]]; then
    log "  write_before_claim_gate.py: already uploaded (md5 match, skip)"
  else
    log "  uploading write_before_claim_gate.py..."
    scp -q "$LOCAL_GATE" "$REMOTE_HOST:$REMOTE_GATE"
    remote_md5=$(md5_remote "$REMOTE_GATE")
    [[ "$remote_md5" == "$local_md5" ]] \
      || die "upload failed; md5 mismatch (local=$local_md5 remote=$remote_md5)"
    log "  write_before_claim_gate.py uploaded (md5 $remote_md5)"
  fi

  # 2. Patch run_agent.py — two anchored edits:
  #    (a) Insert gate invocation just before terminal `_persist_session`.
  #    (b) Add `a2_gate_outcome` field to `_save_session_log`'s entry dict.
  log "Patching run_agent.py..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd "$HOME/.hermes/hermes-agent"

RUNAGENT="run_agent.py"
BAK_SUFFIX=".probe-r7.7-orig"

# Backup (only if not already backed up; never overwrite existing backup).
if [[ ! -f "${RUNAGENT}${BAK_SUFFIX}" ]]; then
  cp -p "$RUNAGENT" "${RUNAGENT}${BAK_SUFFIX}"
  echo "  backed up run_agent.py -> ${RUNAGENT}${BAK_SUFFIX}"
else
  echo "  backup already exists: ${RUNAGENT}${BAK_SUFFIX} (leave it)"
fi

# --- Patch (a): insert A2 gate invocation before terminal _persist_session ---
# Anchor: the unique comment on the line immediately preceding the call.
ANCHOR_A='# Persist session to both JSON log and SQLite'
if grep -q '_a2_gate_outcome = _a2_evaluate' "$RUNAGENT"; then
  echo "  patch (a) already present — skip"
else
  # Use python to do the insertion (awk/sed are fragile with Python indent).
  python3 - "$RUNAGENT" <<'PY'
import io, sys, re
path = sys.argv[1]
src = open(path, "r", encoding="utf-8").read()
anchor = "        # Persist session to both JSON log and SQLite\n" \
        "        self._persist_session(messages, conversation_history)\n"
if anchor not in src:
    # Emit explicit error so the outer shell script sees it.
    sys.stderr.write("ANCHOR_NOT_FOUND: terminal _persist_session block\n")
    sys.exit(2)
replacement = (
    "        # A2 write-before-claim gate (r7.7 narrow, detect-only).\n"
    "        # Populates self._a2_gate_outcome; _save_session_log emits it.\n"
    "        # S4-redo (2026-04-20): gate derives final_content internally\n"
    "        # via _last_nonempty_assistant_content; pass only `messages`.\n"
    "        try:\n"
    "            if os.environ.get(\"HERMES_WRITE_BEFORE_CLAIM_GATE\") == \"1\":\n"
    "                from agent.write_before_claim_gate import evaluate_session as _a2_evaluate\n"
    "                self._a2_gate_outcome = _a2_evaluate(messages)\n"
    "        except Exception as _a2_err:\n"
    "            self._a2_gate_outcome = \"ERROR\"\n"
    + anchor
)
# Use count=1 to patch only the TERMINAL occurrence (the one matching the
# preceding comment). The anchor comment is unique in the file.
new = src.replace(anchor, replacement, 1)
if new == src:
    sys.stderr.write("PATCH_A_NOOP: replacement did not change source\n")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(new)
print("  patch (a) applied — gate invocation inserted")
PY
fi

# --- Patch (b): add a2_gate_outcome to _save_session_log's entry dict ---
# Anchor: the unique line in _save_session_log that opens the entry dict.
if grep -q '"a2_gate_outcome":' "$RUNAGENT"; then
  echo "  patch (b) already present — skip"
else
  python3 - "$RUNAGENT" <<'PY'
import sys
path = sys.argv[1]
src = open(path, "r", encoding="utf-8").read()
anchor = '                "message_count": len(cleaned),\n' \
         '                "messages": cleaned,\n' \
         '            }\n'
if anchor not in src:
    sys.stderr.write("ANCHOR_NOT_FOUND: entry dict tail\n")
    sys.exit(2)
replacement = (
    '                "message_count": len(cleaned),\n'
    '                "messages": cleaned,\n'
    '                "a2_gate_outcome": getattr(self, "_a2_gate_outcome", None),\n'
    '            }\n'
)
new = src.replace(anchor, replacement, 1)
if new == src:
    sys.stderr.write("PATCH_B_NOOP\n")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(new)
print("  patch (b) applied — a2_gate_outcome added to session log entry")
PY
fi

# --- Syntax check on patched run_agent.py ---
python3 -c "import ast,sys; ast.parse(open('$RUNAGENT','r',encoding='utf-8').read()); print('  patched run_agent.py: syntax OK')"
REMOTE_SCRIPT

  log "Stage complete."
  log "  NOTE: gate is GATED by env HERMES_WRITE_BEFORE_CLAIM_GATE=1"
  log "  Set that env in the probe runner to activate; leave unset for baseline."
}

# ---------------------------------------------------------------------------
# Unstage
# ---------------------------------------------------------------------------

cmd_unstage() {
  log "Unstaging Variant J A2..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd "$HOME/.hermes/hermes-agent"

RUNAGENT="run_agent.py"
BAK_SUFFIX=".probe-r7.7-orig"
GATE="$HOME/.hermes/hermes-agent/agent/write_before_claim_gate.py"

if [[ -f "${RUNAGENT}${BAK_SUFFIX}" ]]; then
  cp -p "${RUNAGENT}${BAK_SUFFIX}" "$RUNAGENT"
  rm -f "${RUNAGENT}${BAK_SUFFIX}"
  echo "  restored run_agent.py from backup"
else
  echo "  no backup found — run_agent.py left as-is"
fi

if [[ -f "$GATE" ]]; then
  rm -f "$GATE"
  echo "  removed $GATE"
fi

# Syntax check after restore.
python3 -c "import ast; ast.parse(open('$RUNAGENT','r',encoding='utf-8').read()); print('  restored run_agent.py: syntax OK')"
REMOTE_SCRIPT
  log "Unstage complete."
}

# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

cmd_status() {
  log "Status check..."
  local local_md5 remote_md5 bak_present import_present patch_b_present
  local_md5=$(md5_local "$LOCAL_GATE")

  remote_md5=$(md5_remote "$REMOTE_GATE")
  bak_present=$(ssh_run "[[ -f \"$REMOTE_RUNAGENT$BAK_SUFFIX\" ]] && echo YES || echo NO")
  # Clean integer counts: `grep -c PAT FILE || true` yields a single integer
  # (or empty string when the file is unreadable). Default empty to 0.
  import_present=$(ssh_run "grep -c '_a2_gate_outcome = _a2_evaluate' \"$REMOTE_RUNAGENT\" 2>/dev/null || true")
  patch_b_present=$(ssh_run "grep -c '\"a2_gate_outcome\":' \"$REMOTE_RUNAGENT\" 2>/dev/null || true")
  import_present=${import_present:-0}
  patch_b_present=${patch_b_present:-0}

  echo "  local gate md5:      $local_md5"
  echo "  remote gate md5:     ${remote_md5:-<absent>}"
  echo "  run_agent.py backup: $bak_present"
  echo "  patch (a) count:     $import_present"
  echo "  patch (b) count:     $patch_b_present"

  local md5_ok="NO" a_ok="NO" b_ok="NO" bak_ok="NO"
  [[ "$remote_md5" == "$local_md5" ]] && md5_ok="YES"
  [[ "$import_present" =~ ^[0-9]+$ ]] && [[ "$import_present" -ge 1 ]] && a_ok="YES"
  [[ "$patch_b_present" =~ ^[0-9]+$ ]] && [[ "$patch_b_present" -ge 1 ]] && b_ok="YES"
  [[ "$bak_present" == "YES" ]] && bak_ok="YES"

  if [[ "$md5_ok" == "YES" && "$a_ok" == "YES" && "$b_ok" == "YES" && "$bak_ok" == "YES" ]]; then
    echo "  RESULT: STAGED"
  elif [[ "$md5_ok" == "NO" && "$a_ok" == "NO" && "$b_ok" == "NO" && "$bak_ok" == "NO" ]]; then
    echo "  RESULT: UNSTAGED"
  else
    echo "  RESULT: PARTIAL (inconsistent state — inspect above)"
  fi
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

main() {
  [[ $# -ge 1 ]] || die "usage: $0 {stage|unstage|status}"
  case "$1" in
    stage)   cmd_stage ;;
    unstage) cmd_unstage ;;
    status)  cmd_status ;;
    *) die "unknown command: $1 (expected stage|unstage|status)" ;;
  esac
}

main "$@"
