#!/usr/bin/env bash
# probe-r7.11-unstage.sh — Reverse probe-r7.11-stage.sh.
#
# Order:
#   1. Pre-flight: backups exist for toolsets.py + model_tools.py.
#      If absent, fail loudly ("nothing to unstage" vs "partial" indistinguishable
#      from the absent side; we report whichever backup is missing).
#   2. Restore toolsets.py and model_tools.py from .probe-r7.11-orig.
#   3. Remove tools/r7_11_lib/ recursively.
#   4. Remove the three thin shims in tools/ + write_plan_md.py
#      (the r7.10 carry-forward staged alongside r7.11).
#   5. Remove the .probe-r7.11-orig backups.
#   6. py_compile sanity on toolsets.py + model_tools.py.
#   7. Verify canonical md5s for HERMES.md + run_agent.py.
#
# Idempotency: re-running unstage on an already-unstaged tree is a no-op.

set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-ubuntu-vm}"

# Canonical md5s (same defaults as stage; override via env for fixture tests).
CANONICAL_HERMES_MD="${CANONICAL_HERMES_MD:-0780c232a6cb52e13e432261f0d68ad9}"
CANONICAL_RUN_AGENT="${CANONICAL_RUN_AGENT:-94ad8712678df5e96b9f407446edf249}"

R_AGENT="${R_AGENT:-.hermes/hermes-agent}"
R_TOOLSETS="${R_AGENT}/toolsets.py"
R_MODEL_TOOLS="${R_AGENT}/model_tools.py"
R_LIB_DIR="${R_AGENT}/tools/r7_11_lib"
R_SHIM_VERIFY="${R_AGENT}/tools/r7_11_verify_phase.py"
R_SHIM_END="${R_AGENT}/tools/r7_11_end_session.py"
R_SHIM_ESCALATE="${R_AGENT}/tools/r7_11_escalate.py"
R_WRITE_PLAN_MD="${R_AGENT}/tools/write_plan_md.py"
BAK_SUFFIX=".probe-r7.11-orig"

FIXTURE_ROOT="${FIXTURE_ROOT:-}"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-r7.11-unstage] $*"; }

if [[ -n "$FIXTURE_ROOT" ]]; then
  R_AGENT="${FIXTURE_ROOT}/.hermes/hermes-agent"
  R_TOOLSETS="${R_AGENT}/toolsets.py"
  R_MODEL_TOOLS="${R_AGENT}/model_tools.py"
  R_LIB_DIR="${R_AGENT}/tools/r7_11_lib"
  R_SHIM_VERIFY="${R_AGENT}/tools/r7_11_verify_phase.py"
  R_SHIM_END="${R_AGENT}/tools/r7_11_end_session.py"
  R_SHIM_ESCALATE="${R_AGENT}/tools/r7_11_escalate.py"
  R_WRITE_PLAN_MD="${R_AGENT}/tools/write_plan_md.py"
  ssh_run() { bash -c "$*"; }
  remote_test_f() { [[ -f "$1" ]]; }
  remote_test_d() { [[ -d "$1" ]]; }
  md5_remote() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
else
  ssh_run() { ssh "$REMOTE_HOST" "$@"; }
  remote_test_f() { ssh "$REMOTE_HOST" "[ -f \"$1\" ]"; }
  remote_test_d() { ssh "$REMOTE_HOST" "[ -d \"$1\" ]"; }
  md5_remote() { ssh "$REMOTE_HOST" "md5sum \"$1\" 2>/dev/null | awk '{print \$1}'"; }
fi

cmd_unstage() {
  log "Unstaging r7.11 from ${REMOTE_HOST}${FIXTURE_ROOT:+ (fixture: $FIXTURE_ROOT)}..."

  # Pre-flight: at least one backup must exist; otherwise nothing to unstage.
  local have_t have_m
  if remote_test_f "${R_TOOLSETS}${BAK_SUFFIX}"; then have_t=1; else have_t=0; fi
  if remote_test_f "${R_MODEL_TOOLS}${BAK_SUFFIX}"; then have_m=1; else have_m=0; fi

  if [[ "$have_t" == 0 && "$have_m" == 0 ]]; then
    log "no backups found — nothing to unstage (already at canonical?)"
    # Still try to remove any orphaned shim/lib that survived; idempotent.
    ssh_run "rm -rf ${R_LIB_DIR}"
    ssh_run "rm -f ${R_SHIM_VERIFY} ${R_SHIM_END} ${R_SHIM_ESCALATE} ${R_WRITE_PLAN_MD}"
    log "orphan cleanup pass complete"
    verify_canonical_post
    return 0
  fi

  if [[ "$have_t" == 0 || "$have_m" == 0 ]]; then
    die "PARTIAL UNSTAGE STATE — only one of (toolsets.py, model_tools.py) has a ${BAK_SUFFIX} backup. Manual investigation required. toolsets.py-bak=$have_t, model_tools.py-bak=$have_m."
  fi

  # Phase 1: restore toolsets.py
  log "Phase 1: restore toolsets.py from ${BAK_SUFFIX}"
  ssh_run "mv ${R_TOOLSETS}${BAK_SUFFIX} ${R_TOOLSETS}"

  # Phase 2: restore model_tools.py
  log "Phase 2: restore model_tools.py from ${BAK_SUFFIX}"
  ssh_run "mv ${R_MODEL_TOOLS}${BAK_SUFFIX} ${R_MODEL_TOOLS}"

  # Phase 3: remove r7_11_lib/
  log "Phase 3: remove ${R_LIB_DIR}/ (and __pycache__)"
  ssh_run "rm -rf ${R_LIB_DIR}"

  # Phase 4: remove three shims + write_plan_md (r7.10 carry-forward)
  log "Phase 4: remove shim files + write_plan_md"
  ssh_run "rm -f ${R_SHIM_VERIFY} ${R_SHIM_END} ${R_SHIM_ESCALATE} ${R_WRITE_PLAN_MD}"

  # Phase 5: __pycache__ purge for safety (avoid stale .pyc shadows)
  ssh_run "rm -rf ${R_AGENT}/tools/__pycache__/r7_11_*.cpython-*.pyc 2>/dev/null || true"

  # Phase 6: py_compile sanity check on the two restored files.
  log "Phase 5: py_compile sanity check"
  ssh_run "python3 -m py_compile ${R_TOOLSETS} ${R_MODEL_TOOLS}" \
    || die "py_compile failed after restore — manual investigation required"

  verify_canonical_post

  log "UNSTAGE COMPLETE."
}

verify_canonical_post() {
  # Confirm canonical md5s for HERMES.md (or AGENTS.md on v0.12+) + run_agent.py
  # — these were never touched by r7.11 staging; if they diverge, something
  # else is wrong.
  local md_h md_r system_prompt_path
  system_prompt_path="${R_AGENT}/HERMES.md"
  if ! remote_test_f "$system_prompt_path"; then
    if remote_test_f "${R_AGENT}/AGENTS.md"; then
      system_prompt_path="${R_AGENT}/AGENTS.md"
    fi
  fi
  md_h=$(md5_remote "$system_prompt_path")
  md_r=$(md5_remote "${R_AGENT}/run_agent.py")
  if [[ "${R7_11_ALLOW_DRIFT:-0}" -eq 1 ]]; then
    [[ "$md_h" != "$CANONICAL_HERMES_MD" ]] && log "WARN: post-unstage drift on $(basename "$system_prompt_path") (md5=$md_h); proceeding because R7_11_ALLOW_DRIFT=1"
    [[ "$md_r" != "$CANONICAL_RUN_AGENT" ]] && log "WARN: post-unstage drift on run_agent.py (md5=$md_r); proceeding because R7_11_ALLOW_DRIFT=1"
    log "  canonical md5s checked (drift allowed)"
    return 0
  fi
  if [[ "$md_h" != "$CANONICAL_HERMES_MD" ]]; then
    die "post-unstage canonical drift: $(basename "$system_prompt_path") md5=$md_h expected=$CANONICAL_HERMES_MD. R7.11 unstage is complete but VM is NOT at canonical — something else modified it. Investigate."
  fi
  if [[ "$md_r" != "$CANONICAL_RUN_AGENT" ]]; then
    die "post-unstage canonical drift: run_agent.py md5=$md_r expected=$CANONICAL_RUN_AGENT. R7.11 unstage is complete but VM is NOT at canonical — something else modified it. Investigate."
  fi
  log "  canonical md5s OK ($(basename "$system_prompt_path"), run_agent.py)"
}

case "${1:-unstage}" in
  unstage|"") cmd_unstage ;;
  *) echo "Usage: $0 [unstage]" >&2; exit 2 ;;
esac
