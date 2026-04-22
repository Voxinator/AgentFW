#!/usr/bin/env bash
# probe-variantJ-A1-stage.sh — Stage/unstage the A1 (child toolset restriction)
# patch to delegate_worker_v2.py on ubuntu-vm.
#
# USAGE:
#   ./probe-variantJ-A1-stage.sh stage      # backup existing delegate_worker_v2.py to .probe-r7.7-orig, scp local copy
#   ./probe-variantJ-A1-stage.sh unstage    # restore .probe-r7.7-orig backup
#   ./probe-variantJ-A1-stage.sh status     # show md5 state and overall STAGED / UNSTAGED / PARTIAL
#
# DEPENDENCY CHAIN (variantJ-A1 stacks on top):
#   * variantD:   stages delegate_worker v1               (backup: .probe-d-orig)
#   * variantF:   stages delegate_worker_v2 (β-fuse)       (backup: .probe-r7.4-orig)
#   * variantG/H/I: later β-fuse refinements
#   * variantJ-A1 (THIS SCRIPT): overlays A1 child toolset restriction on top
#                                 of the variantF-staged delegate_worker_v2.py
#                                 (backup: .probe-r7.7-orig)
#
# PRECONDITION:
#   variantF MUST be staged first. This script verifies the VM has a
#   delegate_worker_v2.py at ~/.hermes/hermes-agent/tools/ before touching
#   it; if missing, aborts with a clear error pointing at probe-variantF-stage.sh.
#
# SAFETY:
#   * Idempotent: re-running `stage` when local md5 matches remote is a no-op.
#   * Backup uses `.probe-r7.7-orig` suffix (distinct from variantF's
#     `.probe-r7.4-orig` so the two chains coexist cleanly).
#   * Backup is created ONLY if it does not already exist — preserves the
#     pre-A1 state across repeated stage/unstage cycles.
#   * set -euo pipefail: aborts on mid-stage failure.
#   * Runtime behavior is env-gated by HERMES_CHILD_TOOLSET_RESTRICT=1; staging
#     this file without setting the env var is a pure no-op for running
#     agents. A/B probes toggle the env, not the staged file.

set -euo pipefail

LOCAL_TOOL="/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py"
REMOTE_HOST="ubuntu-vm"
REMOTE_TOOL="\$HOME/.hermes/hermes-agent/tools/delegate_worker_v2.py"
REMOTE_TOOL_PATH_LITERAL="~/.hermes/hermes-agent/tools/delegate_worker_v2.py"
BAK_SUFFIX=".probe-r7.7-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantJ-A1-stage] $*"; }

ssh_run() { ssh "$REMOTE_HOST" "$@"; }

md5_remote() {
  # $1 is an unquoted path string; must pass it to a shell on the VM that will
  # expand $HOME. We already reference via $HOME in REMOTE_TOOL.
  ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true
}
md5_local() { md5 -q "$1" 2>/dev/null; }

# --- preflight ---
[[ -f "$LOCAL_TOOL" ]] || die "missing local tool: $LOCAL_TOOL"

cmd_stage() {
  log "Staging Variant J-A1 (child toolset restriction overlay on β-fuse delegate_worker_v2)..."

  # Precondition: variantF must have staged delegate_worker_v2.py on the VM.
  local have_v2
  have_v2=$(ssh_run "[[ -f $REMOTE_TOOL ]] && echo yes || echo no")
  if [[ "$have_v2" != "yes" ]]; then
    die "VM has no $REMOTE_TOOL_PATH_LITERAL — stage variantF first (probe-variantF-stage.sh stage)"
  fi

  local local_md5 remote_md5
  local_md5=$(md5_local "$LOCAL_TOOL")
  remote_md5=$(md5_remote "$REMOTE_TOOL")
  log "  local  delegate_worker_v2.py md5: $local_md5"
  log "  remote delegate_worker_v2.py md5: ${remote_md5:-<absent>}"

  # Idempotent no-op: local and remote md5s already match.
  if [[ "$remote_md5" == "$local_md5" ]]; then
    log "  already staged (local == remote md5); no-op"
    # Still create a backup if somehow missing (defensive).
    ssh_run "[[ -f ${REMOTE_TOOL}${BAK_SUFFIX} ]] || cp $REMOTE_TOOL ${REMOTE_TOOL}${BAK_SUFFIX}"
    log "STAGE COMPLETE (idempotent no-op)."
    return 0
  fi

  # Create backup of the existing VM copy ONLY if not already present.
  # If a prior A1 stage ran and was then manually muddled, we preserve the
  # earliest pre-A1 state rather than overwrite the backup.
  ssh_run "[[ -f ${REMOTE_TOOL}${BAK_SUFFIX} ]] || cp $REMOTE_TOOL ${REMOTE_TOOL}${BAK_SUFFIX}"
  log "  backup at ${REMOTE_TOOL_PATH_LITERAL}${BAK_SUFFIX} (created if absent; preserved if present)"

  # scp the updated file
  log "  uploading $LOCAL_TOOL -> $REMOTE_HOST:$REMOTE_TOOL_PATH_LITERAL"
  scp -q "$LOCAL_TOOL" "${REMOTE_HOST}:${REMOTE_TOOL_PATH_LITERAL}"

  # Verify upload
  remote_md5=$(md5_remote "$REMOTE_TOOL")
  if [[ "$remote_md5" != "$local_md5" ]]; then
    die "upload verify failed; md5 mismatch (local=$local_md5 remote=$remote_md5)"
  fi
  log "  upload verified (remote md5 $remote_md5)"

  log ""
  log "STAGE COMPLETE."
  log "  A1 overlay active at file level; runtime behavior still gated by"
  log "  HERMES_CHILD_TOOLSET_RESTRICT=1 — export it before starting Hermes to"
  log "  enable child toolset restriction. Unset/other = r7.5 behavior."
}

cmd_unstage() {
  log "Unstaging Variant J-A1 (restoring .probe-r7.7-orig backup)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent/tools

if [[ -f delegate_worker_v2.py.probe-r7.7-orig ]]; then
  cp delegate_worker_v2.py.probe-r7.7-orig delegate_worker_v2.py
  echo "  delegate_worker_v2.py restored from .probe-r7.7-orig"
else
  echo "  delegate_worker_v2.py.probe-r7.7-orig: no backup found — nothing to do (already unstaged?)"
fi
REMOTE_SCRIPT

  log "UNSTAGE COMPLETE."
  log "  variantF-staged delegate_worker_v2.py is back in place; A1 is off."
}

cmd_status() {
  log "Current Variant J-A1 state on $REMOTE_HOST:"

  local local_md5 remote_md5 backup_md5 backup_present
  local_md5=$(md5_local "$LOCAL_TOOL" 2>/dev/null || echo "<local missing>")
  remote_md5=$(md5_remote "$REMOTE_TOOL")
  backup_present=$(ssh_run "[[ -f ${REMOTE_TOOL}${BAK_SUFFIX} ]] && echo yes || echo no")
  if [[ "$backup_present" == "yes" ]]; then
    backup_md5=$(md5_remote "${REMOTE_TOOL}${BAK_SUFFIX}")
  else
    backup_md5="<absent>"
  fi

  printf "  local   delegate_worker_v2.py md5:                 %s\n" "$local_md5"
  printf "  remote  delegate_worker_v2.py md5:                 %s\n" "${remote_md5:-<absent>}"
  printf "  backup  delegate_worker_v2.py.probe-r7.7-orig:     %s (md5: %s)\n" "$backup_present" "$backup_md5"

  if [[ -z "${remote_md5:-}" ]]; then
    echo "  STATE: PARTIAL — remote delegate_worker_v2.py absent; stage variantF first"
    return 0
  fi

  if [[ "$remote_md5" == "$local_md5" && "$backup_present" == "yes" ]]; then
    echo "  STATE: STAGED (r7.7 Variant J-A1 active at file level)"
    echo "         runtime gate: export HERMES_CHILD_TOOLSET_RESTRICT=1 to activate"
  elif [[ "$backup_present" == "no" && "$remote_md5" != "$local_md5" ]]; then
    echo "  STATE: UNSTAGED (remote is pre-A1 or some other variant; no A1 backup present)"
  elif [[ "$backup_present" == "yes" && "$remote_md5" != "$local_md5" ]]; then
    echo "  STATE: PARTIAL — backup present but remote md5 differs from local;"
    echo "         either stage was interrupted or remote was modified out-of-band. Investigate."
  else
    echo "  STATE: PARTIAL — unexpected combination; investigate"
  fi
}

case "${1:-}" in
  stage)    cmd_stage ;;
  unstage)  cmd_unstage ;;
  status)   cmd_status ;;
  verify)   cmd_status ;;  # alias
  "")       die "usage: $0 {stage|unstage|status}" ;;
  *)        die "unknown subcommand: $1" ;;
esac
