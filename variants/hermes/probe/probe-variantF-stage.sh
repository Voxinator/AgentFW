#!/usr/bin/env bash
# probe-variantF-stage.sh — Stage/unstage the delegate_worker_v2 (β-fuse) tool
# side-by-side with existing delegate_worker on ubuntu-vm.
#
# USAGE:
#   ./probe-variantF-stage.sh stage      # copy delegate_worker_v2.py, patch toolsets.py + model_tools.py + run_agent.py (backups .probe-r7.4-orig)
#   ./probe-variantF-stage.sh unstage    # restore .probe-r7.4-orig backups, remove v2 tool file
#   ./probe-variantF-stage.sh status     # show md5 state of all patched files
#
# SAFETY:
#   * Patches are idempotent (check before insert).
#   * Backups use `.probe-r7.4-orig` suffix (distinct from r7's `.probe-d-orig`).
#   * Leaves delegate_worker (v1) fully functional — side-by-side migration.
#   * Aborts on mid-stage failure; requires manual recovery if aborted (does NOT
#     auto-rollback partial state, because rollback logic in a failure handler
#     has its own failure modes).
#
# Relationship to probe-variantD-stage.sh:
#   * variantD stages delegate_worker (v1) with .probe-d-orig backups.
#   * variantF stages delegate_worker_v2 on TOP of variantD-staged state.
#   * Both backup chains coexist: .probe-d-orig is the pre-r7 baseline,
#     .probe-r7.4-orig is the pre-r7.4 state (v1 already staged).

set -euo pipefail

LOCAL_TOOL="/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py"
REMOTE_HOST="ubuntu-vm"
REMOTE_TOOL="~/.hermes/hermes-agent/tools/delegate_worker_v2.py"
REMOTE_TOOLSETS="~/.hermes/hermes-agent/toolsets.py"
REMOTE_MODELTOOLS="~/.hermes/hermes-agent/model_tools.py"
REMOTE_RUNAGENT="~/.hermes/hermes-agent/run_agent.py"
BAK_SUFFIX=".probe-r7.4-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantF-stage] $*"; }

ssh_run() { ssh "$REMOTE_HOST" "$@"; }

md5_remote() { ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }
md5_local() { md5 -q "$1" 2>/dev/null; }

# --- preflight ---
[[ -f "$LOCAL_TOOL" ]] || die "missing local tool: $LOCAL_TOOL"

cmd_stage() {
  log "Staging Variant F (β-fuse delegate_worker_v2 — side-by-side with v1)..."

  local local_md5 remote_md5
  local_md5=$(md5_local "$LOCAL_TOOL")
  log "  local delegate_worker_v2.py md5: $local_md5"

  # 1. Copy tool file to VM (idempotent via md5 compare)
  remote_md5=$(md5_remote "$REMOTE_TOOL")
  if [[ "$remote_md5" == "$local_md5" ]]; then
    log "  delegate_worker_v2.py: already uploaded (md5 match, skip)"
  else
    log "  uploading delegate_worker_v2.py..."
    scp -q "$LOCAL_TOOL" "$REMOTE_HOST:$REMOTE_TOOL"
    remote_md5=$(md5_remote "$REMOTE_TOOL")
    [[ "$remote_md5" == "$local_md5" ]] || die "upload failed; md5 mismatch (local=$local_md5 remote=$remote_md5)"
    log "  delegate_worker_v2.py uploaded (md5 $remote_md5)"
  fi

  # 2. Patch toolsets.py — 4 distinct insertion points:
  #    (a) _HERMES_CORE_TOOLS at ~L56: '..."delegate_task", "delegate_worker",' -> add ', "delegate_worker_v2"'
  #    (b) delegation toolset at ~L199: '"tools": ["delegate_task", "delegate_worker"]' -> add ', "delegate_worker_v2"'
  #    (c) hermes-default-server-like block at ~L254: same pattern as (a)
  #    (d) hermes-api-server block at ~L282: same pattern as (a)
  log "Patching toolsets.py..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

# Idempotency check: if delegate_worker_v2 already present, skip
if grep -q '"delegate_worker_v2"' toolsets.py; then
  echo "  toolsets.py: already patched (idempotent no-op)"
  exit 0
fi

# Backup (separate from .probe-d-orig so r7 backup chain is preserved)
[[ -f toolsets.py.probe-r7.4-orig ]] || cp toolsets.py toolsets.py.probe-r7.4-orig

# Three insertion points of the pattern: "execute_code", "delegate_task", "delegate_worker",
# Insert ', "delegate_worker_v2"' after "delegate_worker" in each.
sed -i 's/"execute_code", "delegate_task", "delegate_worker",/"execute_code", "delegate_task", "delegate_worker", "delegate_worker_v2",/g' toolsets.py

# Delegation toolset array: "tools": ["delegate_task", "delegate_worker"]
sed -i 's/"tools": \["delegate_task", "delegate_worker"\]/"tools": ["delegate_task", "delegate_worker", "delegate_worker_v2"]/' toolsets.py

# Verify we got all 4 insertion points
count=$(grep -c '"delegate_worker_v2"' toolsets.py)
echo "  toolsets.py: inserted $count delegate_worker_v2 references (expect 4)"
if [[ $count -ne 4 ]]; then
  echo "ERROR: expected exactly 4 references, got $count — sed pattern may have missed an insertion point"
  exit 1
fi
REMOTE_SCRIPT

  # 3. Patch model_tools.py — add import of tools.delegate_worker_v2 after tools.delegate_worker
  log "Patching model_tools.py..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if grep -q '"tools.delegate_worker_v2"' model_tools.py; then
  echo "  model_tools.py: already patched (idempotent no-op)"
  exit 0
fi

[[ -f model_tools.py.probe-r7.4-orig ]] || cp model_tools.py model_tools.py.probe-r7.4-orig

# Match the existing '"tools.delegate_worker",' line and insert the v2 import after it.
# Use sed with a literal substitution that doubles the line.
sed -i 's|"tools.delegate_worker",|"tools.delegate_worker",\n        "tools.delegate_worker_v2",|' model_tools.py

count=$(grep -c '"tools.delegate_worker_v2"' model_tools.py)
echo "  model_tools.py: inserted $count v2 import reference (expect 1)"
if [[ $count -ne 1 ]]; then
  echo "ERROR: expected exactly 1 reference, got $count"
  exit 1
fi
REMOTE_SCRIPT

  # 4. Patch run_agent.py — add elif branches for delegate_worker_v2 at both dispatch sites.
  #
  # Why this patch IS required (despite registry-based fallback):
  #   run_agent.py's dispatch sites (`_execute_tool_call` and
  #   `_execute_tool_calls_concurrent`) special-case delegate_task/delegate_worker
  #   BEFORE falling through to handle_function_call. These branches directly
  #   call delegate_task(goal=..., parent_agent=self), bypassing the registry.
  #   If we let delegate_worker_v2 fall through to the generic path, the registry
  #   handler would be invoked via handle_function_call, but that path does NOT
  #   pass parent_agent=self — so v2's structured/long-horizon path (which needs
  #   parent_agent to spawn children) would break.
  #
  # Solution: insert a dedicated elif branch for delegate_worker_v2 that invokes
  # the v2 handler with parent_agent=self. The v2 handler itself decides whether
  # to short-circuit (one-shot) or spawn (structured/long-horizon).
  log "Patching run_agent.py (adding delegate_worker_v2 dispatch branches)..."
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if grep -q 'function_name == "delegate_worker_v2"' run_agent.py; then
  echo "  run_agent.py: already patched (idempotent no-op)"
  exit 0
fi

[[ -f run_agent.py.probe-r7.4-orig ]] || cp run_agent.py run_agent.py.probe-r7.4-orig

# We'll use a Python script to do the multi-line insertion — sed's multi-line
# insert is brittle and this gives us exact control.
python3 - <<'PYEOF'
import io, re

path = "run_agent.py"
with open(path, "r") as f:
    src = f.read()

# We use newline-anchored markers so the 8-space pattern isn't a substring
# of the 12-space pattern. Each marker starts AT a newline so substring
# matching is unambiguous.
#
# Site 1 — the synchronous dispatch path (~L6009). Indent: 8 spaces.
#          Pattern returns directly.
site1_marker = '\n        elif function_name in ("delegate_task", "delegate_worker"):'
site1_insert = (
    '\n        elif function_name == "delegate_worker_v2":'
    '\n            from tools.delegate_worker_v2 import delegate_worker_v2 as _dw2'
    '\n            return _dw2('
    '\n                classification=function_args.get("classification"),'
    '\n                justification=function_args.get("justification"),'
    '\n                goal=function_args.get("goal"),'
    '\n                parent_agent=self,'
    '\n            )'
)

# Site 2 — the concurrent dispatch path (~L6386). Indent: 12 spaces.
#          Pattern assigns function_result, no return.
site2_marker = '\n            elif function_name in ("delegate_task", "delegate_worker"):'
site2_insert = (
    '\n            elif function_name == "delegate_worker_v2":'
    '\n                from tools.delegate_worker_v2 import delegate_worker_v2 as _dw2'
    '\n                function_result = _dw2('
    '\n                    classification=function_args.get("classification"),'
    '\n                    justification=function_args.get("justification"),'
    '\n                    goal=function_args.get("goal"),'
    '\n                    parent_agent=self,'
    '\n                )'
    '\n                tool_duration = time.time() - tool_start_time'
    '\n                if self.quiet_mode:'
    '\n                    self._vprint(f"  {_get_cute_tool_message_impl(\'delegate_worker_v2\', function_args, tool_duration, result=function_result)}")'
)

# Count sites for sanity — exactly one of each.
s1_count = src.count(site1_marker)
s2_count = src.count(site2_marker)

if s1_count != 1 or s2_count != 1:
    print(f"ERROR: expected exactly 1 match for each site, got site1={s1_count} site2={s2_count}")
    raise SystemExit(1)

# Insert the v2 branch BEFORE each existing elif — the v2 branch ends with the
# newline-less insert, which is followed by the marker (which starts with \n).
new_src = src.replace(
    site1_marker,
    site1_insert + site1_marker,
    1,
)
new_src = new_src.replace(
    site2_marker,
    site2_insert + site2_marker,
    1,
)

# Verify insertion actually happened
if 'function_name == "delegate_worker_v2"' not in new_src:
    print("ERROR: v2 marker not present after replace; aborting")
    raise SystemExit(1)
v2_count = new_src.count('function_name == "delegate_worker_v2"')
if v2_count != 2:
    print(f"ERROR: expected 2 v2 branches after insert, got {v2_count}")
    raise SystemExit(1)

with open(path, "w") as f:
    f.write(new_src)

print(f"  run_agent.py: inserted 2 delegate_worker_v2 dispatch branches")
PYEOF
REMOTE_SCRIPT

  log ""
  log "STAGE COMPLETE."
  log "  delegate_worker_v2.py on VM: md5 $remote_md5"
  log "  *.probe-r7.4-orig backups in place for toolsets.py, model_tools.py, run_agent.py"
  log "  v1 delegate_worker remains fully functional (side-by-side)"
}

cmd_unstage() {
  log "Unstaging Variant F (restoring .probe-r7.4-orig backups, removing v2 tool)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if [[ -f toolsets.py.probe-r7.4-orig ]]; then
  cp toolsets.py.probe-r7.4-orig toolsets.py
  echo "  toolsets.py restored from .probe-r7.4-orig"
else
  echo "  toolsets.py: no r7.4 backup found — skipping (already unstaged?)"
fi

if [[ -f model_tools.py.probe-r7.4-orig ]]; then
  cp model_tools.py.probe-r7.4-orig model_tools.py
  echo "  model_tools.py restored from .probe-r7.4-orig"
else
  echo "  model_tools.py: no r7.4 backup found — skipping"
fi

if [[ -f run_agent.py.probe-r7.4-orig ]]; then
  cp run_agent.py.probe-r7.4-orig run_agent.py
  echo "  run_agent.py restored from .probe-r7.4-orig"
else
  echo "  run_agent.py: no r7.4 backup found — skipping"
fi

if [[ -f tools/delegate_worker_v2.py ]]; then
  mv tools/delegate_worker_v2.py /tmp/delegate_worker_v2.py.probe-r7.4-removed
  echo "  tools/delegate_worker_v2.py moved to /tmp/delegate_worker_v2.py.probe-r7.4-removed"
else
  echo "  tools/delegate_worker_v2.py: not present — skipping"
fi

# Verify no stray v2 references remain
stray=$(grep -l 'delegate_worker_v2' toolsets.py model_tools.py run_agent.py 2>/dev/null || true)
if [[ -n "$stray" ]]; then
  echo "WARNING: v2 references still present in: $stray"
  echo "         .probe-r7.4-orig backups may be stale; investigate before next stage."
  exit 1
fi
echo "  verified: no stray delegate_worker_v2 references in patched files"
REMOTE_SCRIPT

  log "UNSTAGE COMPLETE."
}

cmd_status() {
  log "Current Variant F state on $REMOTE_HOST:"

  local local_md5 remote_v2_md5 toolsets_v2_refs model_v2_refs runagent_v2_refs
  local toolsets_bak model_bak runagent_bak hermes_md5

  local_md5=$(md5_local "$LOCAL_TOOL" 2>/dev/null || echo "<local missing>")
  remote_v2_md5=$(md5_remote "$REMOTE_TOOL")
  # grep -c exits 1 when there are 0 matches but still prints "0", so || echo 0
  # double-prints. Use `|| true` on the remote side instead.
  toolsets_v2_refs=$(ssh_run "grep -c '\"delegate_worker_v2\"' $REMOTE_TOOLSETS 2>/dev/null || true" | head -1)
  model_v2_refs=$(ssh_run "grep -c 'tools.delegate_worker_v2' $REMOTE_MODELTOOLS 2>/dev/null || true" | head -1)
  runagent_v2_refs=$(ssh_run "grep -c 'delegate_worker_v2' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  toolsets_v2_refs=${toolsets_v2_refs:-0}
  model_v2_refs=${model_v2_refs:-0}
  runagent_v2_refs=${runagent_v2_refs:-0}
  toolsets_bak=$(ssh_run "[[ -f ~/.hermes/hermes-agent/toolsets.py.probe-r7.4-orig ]] && echo yes || echo no")
  model_bak=$(ssh_run "[[ -f ~/.hermes/hermes-agent/model_tools.py.probe-r7.4-orig ]] && echo yes || echo no")
  runagent_bak=$(ssh_run "[[ -f ~/.hermes/hermes-agent/run_agent.py.probe-r7.4-orig ]] && echo yes || echo no")
  hermes_md5=$(md5_remote "~/.hermes/hermes-agent/HERMES.md")

  printf "  local   delegate_worker_v2.py md5:           %s\n" "$local_md5"
  printf "  remote  delegate_worker_v2.py md5:           %s\n" "${remote_v2_md5:-<absent>}"
  printf "  toolsets.py  delegate_worker_v2 refs:        %s (expect 4 when staged, 0 when canonical)\n" "$toolsets_v2_refs"
  printf "  model_tools.py delegate_worker_v2 refs:      %s (expect 1 when staged, 0 when canonical)\n" "$model_v2_refs"
  printf "  run_agent.py delegate_worker_v2 refs:        %s (expect 5 when staged, 0 when canonical)\n" "$runagent_v2_refs"
  printf "  toolsets.py.probe-r7.4-orig backup present:  %s\n" "$toolsets_bak"
  printf "  model_tools.py.probe-r7.4-orig backup present: %s\n" "$model_bak"
  printf "  run_agent.py.probe-r7.4-orig backup present: %s\n" "$runagent_bak"
  printf "  HERMES.md md5 (canonical expected 0780c232a6cb52e13e432261f0d68ad9): %s\n" "${hermes_md5:-<absent>}"

  if [[ -n "$remote_v2_md5" && "$toolsets_v2_refs" -eq 4 && "$model_v2_refs" -eq 1 && "$runagent_v2_refs" -eq 5 ]]; then
    echo "  STATE: STAGED (r7.4 Variant F)"
  elif [[ -z "$remote_v2_md5" && "$toolsets_v2_refs" -eq 0 && "$model_v2_refs" -eq 0 && "$runagent_v2_refs" -eq 0 ]]; then
    echo "  STATE: UNSTAGED (clean, canonical)"
  else
    echo "  STATE: PARTIAL — investigate before running probe or returning control"
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
