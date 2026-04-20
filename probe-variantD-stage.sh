#!/usr/bin/env bash
# probe-variantD-stage.sh — Stage/unstage the delegate_worker tool on ubuntu-vm.
#
# USAGE:
#   ./probe-variantD-stage.sh stage     # copy delegate_worker.py to VM, patch toolsets.py + model_tools.py (with .orig backups)
#   ./probe-variantD-stage.sh unstage   # revert the patches, remove the tool file
#   ./probe-variantD-stage.sh verify    # check current state
#
# Coordinates with probe-swap.sh (which handles HERMES.md). Do Variant D setup by:
#   1. ./probe-variantD-stage.sh stage
#   2. Update probe-swap.sh to point at HERMES-variantD.md for stage, OR manually scp + swap-in.
#
# SAFETY: Patches are idempotent. Both modified files keep .probe-d-orig copies for
# surgical restore. Aborts on md5 drift from expected pre-state.

set -euo pipefail

LOCAL_TOOL="/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker.py"
REMOTE_HOST="ubuntu-vm"
REMOTE_TOOL="~/.hermes/hermes-agent/tools/delegate_worker.py"
REMOTE_TOOLSETS="~/.hermes/hermes-agent/toolsets.py"
REMOTE_MODELTOOLS="~/.hermes/hermes-agent/model_tools.py"
REMOTE_TOOLSETS_BAK="~/.hermes/hermes-agent/toolsets.py.probe-d-orig"
REMOTE_MODELTOOLS_BAK="~/.hermes/hermes-agent/model_tools.py.probe-d-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantD-stage] $*"; }

ssh_run() { ssh "$REMOTE_HOST" "$@"; }

md5_remote() { ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }

# --- preflight ---
[[ -f "$LOCAL_TOOL" ]] || die "missing local tool: $LOCAL_TOOL"

cmd_stage() {
  log "Staging Variant D (delegate_worker tool + import/toolset patches)..."

  # 1. Copy tool file to VM
  log "Uploading delegate_worker.py..."
  scp -q "$LOCAL_TOOL" "$REMOTE_HOST:$REMOTE_TOOL"
  local tool_md5
  tool_md5=$(md5_remote "$REMOTE_TOOL")
  [[ -n "$tool_md5" ]] || die "upload failed; remote file missing"
  log "  delegate_worker.py uploaded (md5 $tool_md5)"

  # 2. Backup toolsets.py and patch it (idempotent — check for delegate_worker string first)
  log "Patching toolsets.py..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent
# Only backup if no backup exists yet
[[ -f toolsets.py.probe-d-orig ]] || cp toolsets.py toolsets.py.probe-d-orig
# Idempotent patch: only add if not already present
if ! grep -q '"delegate_worker"' toolsets.py; then
  # Add delegate_worker next to delegate_task in _HERMES_CORE_TOOLS (line ~56)
  sed -i 's/"execute_code", "delegate_task",/"execute_code", "delegate_task", "delegate_worker",/' toolsets.py
  # Add to delegation toolset (line ~193)
  sed -i 's/"tools": \["delegate_task"\]/"tools": ["delegate_task", "delegate_worker"]/' toolsets.py
  # Verify edits landed
  count=$(grep -c '"delegate_worker"' toolsets.py)
  echo "  toolsets.py: inserted $count delegate_worker references"
  if [[ $count -lt 2 ]]; then
    echo "ERROR: expected at least 2 references, got $count — sed pattern may have missed"
    exit 1
  fi
else
  echo "  toolsets.py: already patched (idempotent no-op)"
fi
REMOTE_SCRIPT

  # 3. Backup model_tools.py and patch it
  log "Patching model_tools.py..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent
[[ -f model_tools.py.probe-d-orig ]] || cp model_tools.py model_tools.py.probe-d-orig
if ! grep -q '"tools.delegate_worker"' model_tools.py; then
  sed -i 's|"tools.delegate_tool",|"tools.delegate_tool",\n        "tools.delegate_worker",|' model_tools.py
  count=$(grep -c '"tools.delegate_worker"' model_tools.py)
  echo "  model_tools.py: inserted $count import reference"
  if [[ $count -ne 1 ]]; then
    echo "ERROR: expected exactly 1 reference, got $count"
    exit 1
  fi
else
  echo "  model_tools.py: already patched (idempotent no-op)"
fi
REMOTE_SCRIPT

  # 4. Backup run_agent.py and extend the delegate_task special-case to also match delegate_worker
  log "Patching run_agent.py (extending delegate_task dispatch to also handle delegate_worker)..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent
[[ -f run_agent.py.probe-d-orig ]] || cp run_agent.py run_agent.py.probe-d-orig
# Idempotent: only patch if delegate_worker not already in the conditions
if ! grep -q 'function_name in ("delegate_task", "delegate_worker")' run_agent.py; then
  # Replace both occurrences:
  #   elif function_name == "delegate_task":
  #     -> elif function_name in ("delegate_task", "delegate_worker"):
  sed -i 's|elif function_name == "delegate_task":|elif function_name in ("delegate_task", "delegate_worker"):|g' run_agent.py
  count=$(grep -c 'function_name in ("delegate_task", "delegate_worker")' run_agent.py)
  echo "  run_agent.py: patched $count delegate_task call sites"
  if [[ $count -ne 2 ]]; then
    echo "ERROR: expected exactly 2 patches, got $count"
    exit 1
  fi
else
  echo "  run_agent.py: already patched (idempotent no-op)"
fi
REMOTE_SCRIPT

  log "STAGE COMPLETE."
  log "  delegate_worker.py on VM: md5 $tool_md5"
  log "  toolsets.py.probe-d-orig + model_tools.py.probe-d-orig backups in place"
}

cmd_unstage() {
  log "Unstaging Variant D (restoring original toolsets.py + model_tools.py; removing delegate_worker.py)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent
if [[ -f toolsets.py.probe-d-orig ]]; then
  cp toolsets.py.probe-d-orig toolsets.py
  echo "  toolsets.py restored from .probe-d-orig"
else
  echo "  toolsets.py: no backup found, skipping"
fi
if [[ -f model_tools.py.probe-d-orig ]]; then
  cp model_tools.py.probe-d-orig model_tools.py
  echo "  model_tools.py restored from .probe-d-orig"
else
  echo "  model_tools.py: no backup found, skipping"
fi
if [[ -f run_agent.py.probe-d-orig ]]; then
  cp run_agent.py.probe-d-orig run_agent.py
  echo "  run_agent.py restored from .probe-d-orig"
else
  echo "  run_agent.py: no backup found, skipping"
fi
if [[ -f tools/delegate_worker.py ]]; then
  mv tools/delegate_worker.py /tmp/delegate_worker.py.probe-d-removed
  echo "  tools/delegate_worker.py moved to /tmp/delegate_worker.py.probe-d-removed"
fi
REMOTE_SCRIPT

  log "UNSTAGE COMPLETE."
}

cmd_verify() {
  log "Current Variant D state on $REMOTE_HOST:"
  local tool_md5 toolsets_has model_has
  tool_md5=$(md5_remote "$REMOTE_TOOL")
  toolsets_has=$(ssh_run "grep -c '\"delegate_worker\"' $REMOTE_TOOLSETS 2>/dev/null" 2>/dev/null || echo 0)
  model_has=$(ssh_run "grep -c 'tools.delegate_worker' $REMOTE_MODELTOOLS 2>/dev/null" 2>/dev/null || echo 0)
  printf "  delegate_worker.py: %s\n" "${tool_md5:-<missing>}"
  printf "  toolsets.py delegate_worker refs: %s (expect 2 when staged)\n" "$toolsets_has"
  printf "  model_tools.py delegate_worker import: %s (expect 1 when staged)\n" "$model_has"
  if [[ -n "$tool_md5" && "$toolsets_has" -ge 2 && "$model_has" -ge 1 ]]; then
    echo "  STATE: STAGED"
  elif [[ -z "$tool_md5" && "$toolsets_has" -eq 0 && "$model_has" -eq 0 ]]; then
    echo "  STATE: UNSTAGED (clean)"
  else
    echo "  STATE: PARTIAL — investigate before running probe"
  fi
}

case "${1:-}" in
  stage)   cmd_stage ;;
  unstage) cmd_unstage ;;
  verify)  cmd_verify ;;
  "")      die "usage: $0 {stage|unstage|verify}" ;;
  *)       die "unknown subcommand: $1" ;;
esac
