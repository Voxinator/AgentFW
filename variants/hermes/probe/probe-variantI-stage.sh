#!/usr/bin/env bash
# probe-variantI-stage.sh — Stage/unstage the r7.6-P1C HERMES-WORKER.md
# child-session scaffold overlay on top of Variants H / G / F / D.
#
# Design rationale for forking (vs. extending probe-variantH-stage.sh):
#   - variantH's scope is mechanical runtime fixes (gemma_parser prefix-tolerance
#     + channel-marker pollution routing) with no file-copy component.
#   - variantI's scope is a NEW teaching doc (HERMES-WORKER.md) injected into
#     child-agent system prompts — a behavioral overlay, not a runtime patch.
#   - Keeping them in separate stage scripts lets us A/B probe Arm A
#     (variantH staged alone = mechanical fixes only) vs Arm B (variantH + I =
#     mechanical + scaffold) without a mid-run env-var flip.
#
# USAGE:
#   ./probe-variantI-stage.sh stage     # install delegate_tool.py patch + scp HERMES-WORKER.md
#   ./probe-variantI-stage.sh unstage   # restore .probe-r7.6-worker-orig backup + remove HERMES-WORKER.md
#   ./probe-variantI-stage.sh status    # show marker counts + backup + file presence
#
# WHAT THIS PATCHES:
#   ~/.hermes/hermes-agent/tools/delegate_tool.py::_build_child_system_prompt
#     - Adds a prepend step at the TOP of the function: when env var
#       HERMES_WORKER_OVERLAY is set (1|true|yes, case-insensitive), read
#       ~/.hermes/hermes-agent/HERMES-WORKER.md and prepend it to the system
#       prompt. Slot-1 / highest-attention per P1-C design.
#     - When env var is unset or file is missing, silent fallback to base
#       system prompt (no behavior change from canonical).
#   ~/.hermes/hermes-agent/HERMES-WORKER.md
#     - Uploaded from Mac-side /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-WORKER.md
#
# SAFETY:
#   * Idempotent — guarded by `_r76_worker_overlay` marker.
#   * Backup: .probe-r7.6-worker-orig (does not collide with r7.5/r7.4/r7.6 backups).
#   * py_compile sanity-check after patch.
#   * The env-var gate means: even when staged, if HERMES_WORKER_OVERLAY is unset
#     at runtime, child prompts are identical to canonical. Staging is safe.
#   * Canonical HERMES.md on VM must remain untouched — this script does NOT
#     swap HERMES.md (that's the parent system prompt, a separate concern).

set -euo pipefail

REMOTE_HOST="ubuntu-vm"
REMOTE_DELEGATE_TOOL="~/.hermes/hermes-agent/tools/delegate_tool.py"
REMOTE_WORKER_DOC="~/.hermes/hermes-agent/HERMES-WORKER.md"
LOCAL_WORKER_DOC="/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-WORKER.md"
BAK_SUFFIX=".probe-r7.6-worker-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantI-stage] $*"; }
ssh_run() { ssh "$REMOTE_HOST" "$@"; }
md5_remote() { ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }

cmd_stage() {
  log "Staging Variant I (r7.6-P1C HERMES-WORKER.md child-session overlay)..."

  # --- Step 1: Upload HERMES-WORKER.md to VM ---
  [[ -f "$LOCAL_WORKER_DOC" ]] || die "Local HERMES-WORKER.md not found: $LOCAL_WORKER_DOC"
  local_md5=$(md5 -q "$LOCAL_WORKER_DOC" 2>/dev/null || md5sum "$LOCAL_WORKER_DOC" | awk '{print $1}')
  remote_md5=$(md5_remote "$REMOTE_WORKER_DOC")
  if [[ "$local_md5" == "$remote_md5" && -n "$remote_md5" ]]; then
    log "  HERMES-WORKER.md: already uploaded (md5 match)"
  else
    log "  uploading HERMES-WORKER.md (local=$local_md5 remote=${remote_md5:-none})"
    scp -q "$LOCAL_WORKER_DOC" "$REMOTE_HOST:$REMOTE_WORKER_DOC"
  fi

  # --- Step 2: Patch delegate_tool.py ---
  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if grep -q '_r76_worker_overlay' tools/delegate_tool.py; then
  echo "  delegate_tool.py: already patched (idempotent no-op)"
else
  [[ -f tools/delegate_tool.py.probe-r7.6-worker-orig ]] \
    || cp tools/delegate_tool.py tools/delegate_tool.py.probe-r7.6-worker-orig

python3 - <<'PYEOF'
import sys

path = "tools/delegate_tool.py"
with open(path, "r") as f:
    src = f.read()

# Anchor: the first line INSIDE _build_child_system_prompt, which is:
#     parts = [
#         "You are a focused subagent working on a specific delegated task.",
# We insert our overlay logic BEFORE the `parts = [` so that the returned prompt
# is worker_doc + "\n\n---\n\n" + base_prompt when the env var is set.
#
# Concretely we replace:
#     """Build a focused system prompt for a child agent."""
#     parts = [
# With a version that reads HERMES-WORKER.md (when gated), builds the base
# prompt exactly as before, and prepends the overlay.

anchor = (
    '    """Build a focused system prompt for a child agent."""\n'
    '    parts = [\n'
)
replacement = (
    '    """Build a focused system prompt for a child agent.\n'
    '\n'
    '    r7.6-P1C HERMES-WORKER.md overlay: when env var HERMES_WORKER_OVERLAY\n'
    '    is set to 1/true/yes (case-insensitive), prepend the contents of\n'
    '    ~/.hermes/hermes-agent/HERMES-WORKER.md to the returned prompt. This\n'
    '    gives every child session a behavioral scaffolding overlay before any\n'
    '    goal/context text. When unset or file missing, silent fallback to base.\n'
    '    """\n'
    '    # --- r7.6-P1C _r76_worker_overlay ---\n'
    '    _r76_worker_doc = ""\n'
    '    if os.environ.get("HERMES_WORKER_OVERLAY", "").lower() in ("1", "true", "yes"):\n'
    '        _r76_worker_doc_path = os.path.expanduser("~/.hermes/hermes-agent/HERMES-WORKER.md")\n'
    '        try:\n'
    '            with open(_r76_worker_doc_path, "r") as _r76_fh:\n'
    '                _r76_worker_doc = _r76_fh.read()\n'
    '        except (FileNotFoundError, OSError):\n'
    '            _r76_worker_doc = ""\n'
    '    # --- end r7.6-P1C overlay read ---\n'
    '    parts = [\n'
)
if src.count(anchor) != 1:
    print(f"ERROR: _build_child_system_prompt anchor not unique (count={src.count(anchor)})")
    sys.exit(1)
src = src.replace(anchor, replacement, 1)

# Next: patch the return statement so the overlay actually prepends. The current
# function ends with:
#     return "\n".join(parts)
# We change it to:
#     _r76_base = "\n".join(parts)
#     if _r76_worker_doc:
#         return _r76_worker_doc + "\n\n---\n\n" + _r76_base
#     return _r76_base
#
# Need to anchor on a unique substring of the end — the return statement plus the
# signature of the NEXT function. The preceding function body has ONE return
# statement at its end.

return_anchor = (
    '        "Be thorough but concise -- your response is returned to the "\n'
    '        "parent agent as a summary."\n'
    '    )\n'
    '    return "\\n".join(parts)\n'
)
return_replacement = (
    '        "Be thorough but concise -- your response is returned to the "\n'
    '        "parent agent as a summary."\n'
    '    )\n'
    '    # --- r7.6-P1C _r76_worker_overlay prepend ---\n'
    '    _r76_base_prompt = "\\n".join(parts)\n'
    '    if _r76_worker_doc:\n'
    '        return _r76_worker_doc + "\\n\\n---\\n\\n" + _r76_base_prompt\n'
    '    return _r76_base_prompt\n'
    '    # --- end r7.6-P1C overlay return ---\n'
)
if src.count(return_anchor) != 1:
    print(f"ERROR: _build_child_system_prompt return anchor not unique "
          f"(count={src.count(return_anchor)})")
    sys.exit(1)
src = src.replace(return_anchor, return_replacement, 1)

# Sanity: `os` must be imported. delegate_tool.py already imports os at the top;
# we saw `os.getenv` and `os.path.abspath` in _resolve_workspace_hint below the
# function we're patching. So os is in scope. We verify:
if "import os" not in src and "from os " not in src:
    # Fallback: prepend `import os`
    src = "import os\n" + src

marker_count = src.count("_r76_worker_overlay")
# Expect: 2 (two guard-comment block headers — one in the read block at top,
# one in the prepend block at bottom).
if marker_count < 2:
    print(f"ERROR: expected >=2 _r76_worker_overlay marker hits, got {marker_count}")
    sys.exit(1)

with open(path, "w") as f:
    f.write(src)
print(f"  delegate_tool.py: applied HERMES-WORKER.md overlay prepend ({marker_count} marker hits)")
PYEOF
fi

# Syntax sanity
python3 -m py_compile tools/delegate_tool.py && echo "  tools/delegate_tool.py: py_compile OK"
REMOTE_SCRIPT

  log ""
  log "STAGE COMPLETE."
  log "  delegate_tool.py.probe-r7.6-worker-orig backup in place"
  log "  HERMES-WORKER.md uploaded to ~/.hermes/hermes-agent/HERMES-WORKER.md"
  log "  Overlay gated by env var HERMES_WORKER_OVERLAY=1 (or true/yes)"
  log "  Set that env var in the wrapper's ssh invocation to activate for a probe arm"
}

cmd_unstage() {
  log "Unstaging Variant I (restoring delegate_tool.py backup + removing HERMES-WORKER.md)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if [[ -f tools/delegate_tool.py.probe-r7.6-worker-orig ]]; then
  cp tools/delegate_tool.py.probe-r7.6-worker-orig tools/delegate_tool.py
  echo "  delegate_tool.py restored from .probe-r7.6-worker-orig"
else
  echo "  delegate_tool.py: no r7.6-worker backup found — skipping (already unstaged?)"
fi

# Verify no stray markers remain.
stray=$(grep -c '_r76_worker_overlay' tools/delegate_tool.py 2>/dev/null || true)
if [[ "${stray:-0}" -ne 0 ]]; then
  echo "WARNING: _r76_worker_overlay markers still present ($stray) — investigate"
  exit 1
fi
echo "  verified: no stray _r76_worker_overlay markers in delegate_tool.py"

# Optionally remove the uploaded HERMES-WORKER.md. It's harmless to leave in
# place (only activated by env var gate), but cleanliness matters for canonical.
if [[ -f HERMES-WORKER.md ]]; then
  rm HERMES-WORKER.md
  echo "  HERMES-WORKER.md removed from ~/.hermes/hermes-agent/"
fi
REMOTE_SCRIPT

  log "UNSTAGE COMPLETE."
}

cmd_status() {
  log "Current Variant I state on $REMOTE_HOST:"

  local marker_hits bak_present worker_doc_present worker_doc_md5 delegate_md5

  marker_hits=$(ssh_run "grep -c '_r76_worker_overlay' $REMOTE_DELEGATE_TOOL 2>/dev/null || true" | head -1)
  marker_hits=${marker_hits:-0}
  bak_present=$(ssh_run "[[ -f ~/.hermes/hermes-agent/tools/delegate_tool.py.probe-r7.6-worker-orig ]] && echo yes || echo no")
  worker_doc_present=$(ssh_run "[[ -f $REMOTE_WORKER_DOC ]] && echo yes || echo no")
  worker_doc_md5=$(md5_remote "$REMOTE_WORKER_DOC")
  delegate_md5=$(md5_remote "$REMOTE_DELEGATE_TOOL")

  printf "  delegate_tool.py _r76_worker_overlay hits:   %s (expect >=2 staged, 0 canonical)\n" "$marker_hits"
  printf "  delegate_tool.py.probe-r7.6-worker-orig bak: %s\n" "$bak_present"
  printf "  HERMES-WORKER.md present on VM:              %s\n" "$worker_doc_present"
  printf "  HERMES-WORKER.md md5:                        %s\n" "${worker_doc_md5:-<absent>}"
  printf "  delegate_tool.py md5:                        %s\n" "${delegate_md5:-<absent>}"

  if [[ "$marker_hits" -ge 2 && "$worker_doc_present" == "yes" ]]; then
    echo "  STATE: STAGED (r7.6-P1C Variant I)"
  elif [[ "$marker_hits" -eq 0 && "$worker_doc_present" == "no" ]]; then
    echo "  STATE: VARIANT-I UNSTAGED"
  else
    echo "  STATE: PARTIAL — investigate before probe"
  fi
}

case "${1:-}" in
  stage)    cmd_stage ;;
  unstage)  cmd_unstage ;;
  status)   cmd_status ;;
  verify)   cmd_status ;;
  "")       die "usage: $0 {stage|unstage|status}" ;;
  *)        die "unknown subcommand: $1" ;;
esac
