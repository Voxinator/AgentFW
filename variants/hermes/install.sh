#!/usr/bin/env bash
# install.sh — Automated installer for the Hermes variant of AgentFW (r7.11)
#
# Stages the r7.11 firmware (verified-state multi-session resumable
# architecture with execution-tier acceptance verification) onto a Hermes
# Agent installation on a remote VM. Idempotent, canonical-preserving via
# the .probe-r7.11-orig backup convention.
#
# USAGE
#   bash install.sh                    Default: pre-flight + tests + stage
#   bash install.sh --check            Pre-flight only (no mutation)
#   bash install.sh --uninstall        Restore canonical (unstage firmware)
#   bash install.sh --smoke            After install, run smoke-r7.11.sh
#                                      (requires OMLX_API_KEY in env)
#   bash install.sh --host=<alias>     Override default ssh alias (ubuntu-vm)
#   bash install.sh --skip-tests       Skip the 227-test local pre-stage check
#   bash install.sh --help             Print this header
#
# EXIT CODES
#   0  = success (or --check all gates pass)
#   1  = pre-flight failure (Mac side)
#   2  = pre-flight failure (VM side: canonical drift, missing Hermes, etc.)
#   3  = local test failure
#   4  = staging failure
#   5  = post-stage verification failure
#   6  = smoke test failure (only with --smoke)
#   10 = uninstall failure (only with --uninstall)
#   99 = usage error
#
# ENV OVERRIDES
#   HERMES_HOST            default "ubuntu-vm"; ssh alias for the VM
#   OMLX_API_KEY           required only with --smoke
#   R7_11_DIR              default <repo>/variants/hermes/r7.9-research/r7.11
#
# REQUIREMENTS
#   Mac side: this repo cloned; bash; ssh; python3
#   VM side: Hermes Agent installed at ~/.hermes/hermes-agent/ with
#            canonical md5s matching baseline (see DEPENDENCIES.md)

set -uo pipefail

# ---------------------------------------------------------------------------
# Defaults + arg parsing
# ---------------------------------------------------------------------------

MODE="install"
RUN_SMOKE=0
SKIP_TESTS=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_R7_11_DIR="${SCRIPT_DIR}/r7.9-research/r7.11"
R7_11_DIR="${R7_11_DIR:-$DEFAULT_R7_11_DIR}"
HERMES_HOST="${HERMES_HOST:-ubuntu-vm}"

print_help() {
  sed -n '2,33p' "${BASH_SOURCE[0]}" | sed 's|^# \?||'
}

for arg in "$@"; do
  case "$arg" in
    --check)        MODE="check" ;;
    --uninstall)    MODE="uninstall" ;;
    --smoke)        RUN_SMOKE=1 ;;
    --skip-tests)   SKIP_TESTS=1 ;;
    --host=*)       HERMES_HOST="${arg#--host=}" ;;
    --help|-h)      print_help; exit 0 ;;
    *) echo "ERROR: unknown arg: $arg (try --help)" >&2; exit 99 ;;
  esac
done

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

log()    { printf '[install] %s\n' "$*"; }
ok()     { printf '[install] \e[32mOK\e[0m  %s\n' "$*"; }
warn()   { printf '[install] \e[33mWARN\e[0m %s\n' "$*" >&2; }
fail()   { printf '[install] \e[31mFAIL\e[0m %s\n' "$*" >&2; }
header() { printf '\n[install] === %s ===\n' "$*"; }

# ---------------------------------------------------------------------------
# Canonical baseline md5s (post-cleanup, 2026-04-30)
# ---------------------------------------------------------------------------

readonly EXPECTED_HERMES_MD="0780c232a6cb52e13e432261f0d68ad9"
readonly EXPECTED_RUN_AGENT="94ad8712678df5e96b9f407446edf249"
readonly EXPECTED_TOOLSETS="5d126e7f1987468c0514cbc474ba12eb"
readonly EXPECTED_MODEL_TOOLS="10aaf53294ba39569844ebac7076e9c9"

# ---------------------------------------------------------------------------
# Phase 1: Mac-side pre-flight
# ---------------------------------------------------------------------------

mac_preflight() {
  header "Phase 1: Mac-side pre-flight"

  if ! command -v ssh >/dev/null 2>&1; then
    fail "ssh not found on PATH"; return 1
  fi
  ok "ssh available"

  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found on PATH"; return 1
  fi
  local pyver
  pyver=$(python3 --version 2>&1)
  ok "python3 available ($pyver)"

  if [[ ! -d "$R7_11_DIR" ]]; then
    fail "r7.11 directory not found: $R7_11_DIR"
    log "Hint: run from the AgentFW repo root, or set R7_11_DIR env var"
    return 1
  fi
  ok "r7.11 directory found: $R7_11_DIR"

  for f in probe-r7.11-stage.sh probe-r7.11-unstage.sh smoke-r7.11.sh \
           verify_phase.py verified_state.py verify_phase_tool.py \
           handoff_tools.py hermes_multi.py; do
    if [[ ! -f "$R7_11_DIR/$f" ]]; then
      fail "required file missing: $R7_11_DIR/$f"; return 1
    fi
  done
  ok "all required source files present"

  local wpm="${R7_11_DIR}/../r7.10/write_plan_md.py.r7.10-min"
  if [[ ! -f "$wpm" ]]; then
    fail "r7.10 carry-forward dependency missing: $wpm"; return 1
  fi
  ok "r7.10 write_plan_md.py.r7.10-min present"

  return 0
}

# ---------------------------------------------------------------------------
# Phase 2: VM-side pre-flight
# ---------------------------------------------------------------------------

vm_preflight() {
  header "Phase 2: VM-side pre-flight (host=$HERMES_HOST)"

  if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "$HERMES_HOST" true 2>/dev/null; then
    fail "cannot ssh to $HERMES_HOST (BatchMode; check ~/.ssh/config + key auth)"
    return 2
  fi
  ok "ssh to $HERMES_HOST works"

  if ! ssh "$HERMES_HOST" 'test -d ~/.hermes/hermes-agent' 2>/dev/null; then
    fail "Hermes not installed at ~/.hermes/hermes-agent on $HERMES_HOST"
    log "See DEPENDENCIES.md for Hermes Agent install requirements"
    return 2
  fi
  ok "Hermes installed at ~/.hermes/hermes-agent"

  local md5s drift=0
  md5s=$(ssh "$HERMES_HOST" 'md5sum ~/.hermes/hermes-agent/HERMES.md \
                                     ~/.hermes/hermes-agent/run_agent.py \
                                     ~/.hermes/hermes-agent/toolsets.py \
                                     ~/.hermes/hermes-agent/model_tools.py 2>&1' 2>/dev/null)
  check_md5() {
    local file="$1" expected="$2"
    local actual
    actual=$(echo "$md5s" | awk -v f="$file" '$2 ~ f {print $1}' | head -1)
    if [[ -z "$actual" ]]; then
      fail "  $file: not readable on VM"; drift=1
    elif [[ "$actual" != "$expected" ]]; then
      fail "  $file: md5 mismatch (expected $expected, got $actual)"; drift=1
    else
      ok "  $file md5 matches baseline"
    fi
  }
  check_md5 "HERMES.md"      "$EXPECTED_HERMES_MD"
  check_md5 "run_agent.py"   "$EXPECTED_RUN_AGENT"
  check_md5 "toolsets.py"    "$EXPECTED_TOOLSETS"
  check_md5 "model_tools.py" "$EXPECTED_MODEL_TOOLS"

  if [[ "$drift" -ne 0 ]]; then
    fail "VM canonical drift detected — refusing to stage"
    log "Either restore canonical Hermes install OR update baseline md5s in this script"
    return 2
  fi
  ok "VM canonical state matches baseline"

  local pyver
  pyver=$(ssh "$HERMES_HOST" '~/.hermes/hermes-agent/venv/bin/python --version' 2>/dev/null)
  if [[ "$pyver" != *"Python 3.11"* ]]; then
    warn "Hermes Python is '$pyver' — r7.11 was tested with Python 3.11.x"
    warn "Scaffold venvs MUST match Hermes' Python for ABI compatibility (F-6)"
  else
    ok "Hermes Python: $pyver"
  fi

  local stale
  stale=$(ssh "$HERMES_HOST" 'find ~/.hermes/hermes-agent -name "*.probe-r7.11-orig" 2>/dev/null | wc -l')
  if [[ "$stale" -gt 0 ]]; then
    warn "$stale stale .probe-r7.11-orig backup(s) detected on VM"
    warn "Run --uninstall first OR remove backups manually before re-staging"
    return 2
  fi
  ok "no stale .probe-r7.11-orig backups"

  if ssh "$HERMES_HOST" 'test -d ~/.hermes/hermes-agent/tools/r7_11_lib' 2>/dev/null; then
    warn "r7.11 firmware appears already staged"
    log "Use --uninstall to restore canonical, or remove staged files manually"
    return 2
  fi
  ok "no prior r7.11 staging detected"

  return 0
}

# ---------------------------------------------------------------------------
# Phase 3: Local test suite (verifies firmware integrity before staging)
# ---------------------------------------------------------------------------

run_local_tests() {
  header "Phase 3: Local test suite (227 tests)"

  if [[ "$SKIP_TESTS" -eq 1 ]]; then
    warn "skipped (--skip-tests)"
    return 0
  fi

  local fails=0
  for t in test_verified_state test_verify_phase test_verify_phase_tool \
           test_handoff_tools test_hermes_multi test_content_verify \
           test_probe_r7_11; do
    local out
    out=$(cd "$R7_11_DIR" && python3 "${t}.py" 2>&1 | tail -1)
    if echo "$out" | grep -qE 'passed|^OK'; then
      ok "  $t — $out"
    else
      fail "  $t — $out"
      fails=1
    fi
  done

  if [[ "$fails" -ne 0 ]]; then
    fail "test suite failed — refusing to stage broken firmware"
    return 3
  fi
  ok "all 7 test files passed (227 tests)"
  return 0
}

# ---------------------------------------------------------------------------
# Phase 4: Stage firmware
# ---------------------------------------------------------------------------

stage_firmware() {
  header "Phase 4: Stage firmware on $HERMES_HOST"
  if ! bash "$R7_11_DIR/probe-r7.11-stage.sh" stage 2>&1 | sed 's/^/  /'; then
    fail "staging script returned non-zero"
    return 4
  fi
  ok "stage complete"
  return 0
}

# ---------------------------------------------------------------------------
# Phase 5: Post-stage verification
# ---------------------------------------------------------------------------

verify_stage() {
  header "Phase 5: Post-stage verification"

  local missing=0
  for f in tools/r7_11_lib tools/r7_11_verify_phase.py \
           tools/r7_11_end_session.py tools/r7_11_escalate.py \
           tools/write_plan_md.py toolsets.py.probe-r7.11-orig \
           model_tools.py.probe-r7.11-orig; do
    if ssh "$HERMES_HOST" "test -e ~/.hermes/hermes-agent/$f" 2>/dev/null; then
      ok "  $f present"
    else
      fail "  $f missing"; missing=1
    fi
  done

  if [[ "$missing" -ne 0 ]]; then
    fail "post-stage verification failed — staged state is incomplete"
    log "Run --uninstall to restore canonical, then investigate"
    return 5
  fi

  local cur_hermes cur_run
  cur_hermes=$(ssh "$HERMES_HOST" 'md5sum ~/.hermes/hermes-agent/HERMES.md' 2>/dev/null | awk '{print $1}')
  cur_run=$(ssh "$HERMES_HOST" 'md5sum ~/.hermes/hermes-agent/run_agent.py' 2>/dev/null | awk '{print $1}')
  if [[ "$cur_hermes" != "$EXPECTED_HERMES_MD" ]] || [[ "$cur_run" != "$EXPECTED_RUN_AGENT" ]]; then
    fail "canonical tripwires mutated by staging — this should never happen"
    return 5
  fi
  ok "canonical tripwires (HERMES.md, run_agent.py) unchanged"
  return 0
}

# ---------------------------------------------------------------------------
# Phase 6: Optional smoke test
# ---------------------------------------------------------------------------

run_smoke() {
  header "Phase 6: Smoke test"

  if [[ -z "${OMLX_API_KEY:-}" ]]; then
    fail "OMLX_API_KEY not set in env — required for smoke test"
    return 6
  fi

  if ! bash "$R7_11_DIR/smoke-r7.11.sh" 2>&1 | sed 's/^/  /'; then
    fail "smoke test returned non-zero"
    return 6
  fi
  ok "smoke test passed"
  return 0
}

# ---------------------------------------------------------------------------
# Uninstall path
# ---------------------------------------------------------------------------

run_uninstall() {
  header "Uninstall: restore canonical via probe-r7.11-unstage.sh"
  if ! bash "$R7_11_DIR/probe-r7.11-unstage.sh" 2>&1 | sed 's/^/  /'; then
    fail "unstage script returned non-zero"
    return 10
  fi

  local cur_hermes cur_run
  cur_hermes=$(ssh "$HERMES_HOST" 'md5sum ~/.hermes/hermes-agent/HERMES.md' 2>/dev/null | awk '{print $1}')
  cur_run=$(ssh "$HERMES_HOST" 'md5sum ~/.hermes/hermes-agent/run_agent.py' 2>/dev/null | awk '{print $1}')
  if [[ "$cur_hermes" != "$EXPECTED_HERMES_MD" ]] || [[ "$cur_run" != "$EXPECTED_RUN_AGENT" ]]; then
    fail "canonical drift after unstage — investigate"
    return 10
  fi

  if ssh "$HERMES_HOST" 'test -d ~/.hermes/hermes-agent/tools/r7_11_lib \
                         || test -f ~/.hermes/hermes-agent/tools/write_plan_md.py' 2>/dev/null; then
    fail "r7.11 artifacts still present after unstage — investigate"
    return 10
  fi
  ok "uninstall complete; canonical state restored"
  return 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

case "$MODE" in
  uninstall)
    mac_preflight || exit $?
    vm_preflight_for_uninstall() {
      header "Phase 2: VM-side pre-flight (host=$HERMES_HOST)"
      ssh -o BatchMode=yes -o ConnectTimeout=10 "$HERMES_HOST" true 2>/dev/null \
        || { fail "cannot ssh to $HERMES_HOST"; return 2; }
      ok "ssh to $HERMES_HOST works"
      return 0
    }
    vm_preflight_for_uninstall || exit $?
    run_uninstall || exit $?
    log ""
    log "=== Hermes variant r7.11 firmware UNINSTALLED ==="
    log "Canonical Hermes Agent restored on $HERMES_HOST"
    exit 0
    ;;
  check)
    mac_preflight || exit $?
    vm_preflight  || exit $?
    if [[ "$SKIP_TESTS" -eq 0 ]]; then
      run_local_tests || exit $?
    fi
    log ""
    log "=== Pre-flight PASSED ==="
    log "Run without --check to perform the install."
    exit 0
    ;;
  install)
    mac_preflight || exit $?
    vm_preflight  || exit $?
    run_local_tests || exit $?
    stage_firmware  || exit $?
    verify_stage    || exit $?
    if [[ "$RUN_SMOKE" -eq 1 ]]; then
      run_smoke || exit $?
    fi
    log ""
    log "=== Hermes variant r7.11 firmware INSTALLED on $HERMES_HOST ==="
    log ""
    log "Next steps:"
    log "  1. Prepare a scaffold dir on the VM with USER-PROMPT.md +"
    log "     verify-config.json + a python3.11 .venv"
    log "     (see HOWTO-r7.11-multi.md §Prerequisites)"
    log "  2. Run a trial:"
    log "     ssh $HERMES_HOST \"cd /path/to/r7.11 && \\"
    log "       OMLX_API_KEY=... python3 hermes_multi.py run /path/to/scaffold/ \\"
    log "       --transport local\""
    log "  3. To uninstall: bash install.sh --uninstall"
    log ""
    log "Documentation:"
    log "  - INSTALL.md (this installer + manual procedure)"
    log "  - r7.9-research/r7.11/HOWTO-r7.11-stage.md (staging detail)"
    log "  - r7.9-research/r7.11/HOWTO-r7.11-multi.md (wrapper usage)"
    log "  - r7.9-research/r7.11/README.md (milestone tree overview)"
    log "  - r7.9-research/r7.11/HANDOFF-r7.11-current.md (campaign-close runbook)"
    exit 0
    ;;
  *)
    fail "unknown mode: $MODE"
    exit 99
    ;;
esac
