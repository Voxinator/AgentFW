#!/usr/bin/env bash
# probe-preflight.sh — Pre-flight gate for r7.6 probe orchestration.
#
# Implements Fix 5 (r7.6-P1C rev 2 plan §7.2a). Runs BEFORE any probe trial
# or judge dispatch. Aborts with a specific exit code when any gate fails,
# so the caller can distinguish methodology-blocking failures (no Agent
# dispatch) from environmental (VM busy, oMLX swap) or state-drift failures
# (tripwire md5 mismatch).
#
# USAGE
#   probe-preflight.sh [--skip-omlx] [--skip-tripwire] [--skip-vm-idle] [--help|-h]
#
# There is NO --skip-agent flag. The Agent-dispatch gate is the load-bearing
# methodology check (plan §7.6). If the invoking session lacks Agent/Task
# dispatch, the ship-judge path does not exist and the probe campaign cannot
# be calibrated per CALIBRATION-r7.6-judge-protocol.md. Running probes
# without it would reproduce the r7.5-F.2 / r7.6-P1C methodology regression.
#
# OUTPUT
#   stderr: per-gate PASS / FAIL lines (human readable).
#   stdout: single-line verdict (PREFLIGHT=PASS | PREFLIGHT=FAIL detail=<gate>).
#
# EXIT CODES
#   0 = all enabled gates pass
#   1 = agent_dispatch FAIL (not bypassable)
#   2 = oMLX FAIL
#   3 = tripwire FAIL
#   4 = VM busy (hermes chat running)
#   5 = usage error
#
# ENV OVERRIDES
#   AGENT_DISPATCH_AVAILABLE    must be "1" — set by the orchestrating
#                               harness layer (Claude Code session) when its
#                               tool scope exposes a Task/Agent dispatcher.
#                               No other way to probe this from a bash script.
#   OMLX_SWAP_MAX_GB            default 5.5 (operator current override;
#                               base oMLX check default is 5.0).
#   OMLX_URL, OMLX_API_KEY, OMLX_MEM_FREE_MIN_GB, OMLX_ACTIVE_SESSIONS_MAX
#                               forwarded to probe-omlx-health-check.sh.
#   SSH_TARGET                  default "ubuntu-vm".
#   TRIPWIRE_HERMES_MD5         override expected HERMES.md md5.
#   TRIPWIRE_SKILL_MD5          override expected SKILL.md md5.
#   TRIPWIRE_JIRA_MD5           override expected jira-briefing.sh md5.
#   TRIPWIRE_USE_DASHBOARD_MD5  override expected useDashboard.ts md5.
#
# DESIGN NOTE — Agent-dispatch probe
#   A bash script cannot directly introspect the invoking Claude session's
#   available tools. The practical approach chosen here is an environment-
#   variable contract: the harness layer that spawns the probe sets
#   AGENT_DISPATCH_AVAILABLE=1 when (and only when) it knows its tool scope
#   exposes the Task tool. This shifts the responsibility for truthful
#   reporting to the caller, but the contract is explicit and auditable —
#   any probe run produces a stdout verdict line containing the agent_dispatch
#   gate result. False positives are detectable post-hoc by checking that
#   fresh-judge artifacts exist for the run.

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

# ---- Defaults ---------------------------------------------------------------
: "${SSH_TARGET:=ubuntu-vm}"
: "${OMLX_SWAP_MAX_GB:=5.5}"
export OMLX_SWAP_MAX_GB

: "${TRIPWIRE_HERMES_MD5:=0780c232a6cb52e13e432261f0d68ad9}"
: "${TRIPWIRE_SKILL_MD5:=fb1a5a5208a6cf2fcb8252aac10397eb}"
: "${TRIPWIRE_JIRA_MD5:=a1dce6e989527686124d0860830627c9}"
: "${TRIPWIRE_USE_DASHBOARD_MD5:=5503ee1c2ef7d635a020eea275e41239}"

SKIP_OMLX=0
SKIP_TRIPWIRE=0
SKIP_VM_IDLE=0

usage() {
    cat <<EOF
$SCRIPT_NAME — r7.6 probe pre-flight gate

Usage:
  $SCRIPT_NAME [--skip-omlx] [--skip-tripwire] [--skip-vm-idle]
  $SCRIPT_NAME --help | -h

Gates (in order):
  1. agent_dispatch  — AGENT_DISPATCH_AVAILABLE=1 in env (NOT bypassable)
  2. omlx            — probe-omlx-health-check.sh (CLEAN)
  3. tripwire        — VM canonical md5s
  4. vm_idle         — no 'hermes chat' process on VM (gateway OK)

Exit codes:
  0 pass, 1 agent_dispatch, 2 omlx, 3 tripwire, 4 vm_busy, 5 usage
EOF
}

# ---- Argument parsing -------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --skip-omlx)     SKIP_OMLX=1 ;;
        --skip-tripwire) SKIP_TRIPWIRE=1 ;;
        --skip-vm-idle)  SKIP_VM_IDLE=1 ;;
        --help|-h)       usage; exit 0 ;;
        *)
            echo "ERROR: unknown argument '$1'" >&2
            usage >&2
            exit 5
            ;;
    esac
    shift
done

# ---- Per-gate log helpers ---------------------------------------------------
gate_pass() { echo "[GATE: $1] PASS${2:+ $2}" >&2; }
gate_fail() { echo "[GATE: $1] FAIL: $2" >&2; }
gate_skip() { echo "[GATE: $1] SKIPPED (--skip flag)" >&2; }

# ---- Gate 1: agent_dispatch (NOT bypassable) --------------------------------
# This is the load-bearing gate. Without Agent dispatch the ship-judge
# methodology collapses into orchestrator-in-process judging, which
# CALIBRATION-r7.6-judge-protocol.md designates as a documented fallback,
# not the primary path.
if [ "${AGENT_DISPATCH_AVAILABLE:-0}" = "1" ]; then
    gate_pass "agent_dispatch" "(AGENT_DISPATCH_AVAILABLE=1)"
else
    gate_fail "agent_dispatch" \
        "AGENT_DISPATCH_AVAILABLE is not '1' — invoking harness must declare Task/Agent tool availability. See plan §7.6: no --skip flag exists for this gate."
    echo "PREFLIGHT=FAIL detail=agent_dispatch"
    exit 1
fi

# ---- Gate 2: oMLX health ----------------------------------------------------
if [ "$SKIP_OMLX" -eq 1 ]; then
    gate_skip "omlx"
else
    SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
    OMLX_CHECK="$SCRIPT_DIR/probe-omlx-health-check.sh"
    if [ ! -x "$OMLX_CHECK" ]; then
        gate_fail "omlx" "helper script missing or not executable: $OMLX_CHECK"
        echo "PREFLIGHT=FAIL detail=omlx"
        exit 2
    fi
    # Capture the single-line verdict (stdout) while letting human-readable
    # detail flow to our stderr for the operator. Disarm -e with `|| omlx_rc=$?`.
    omlx_rc=0
    omlx_verdict="$("$OMLX_CHECK")" || omlx_rc=$?
    if [ "$omlx_rc" -eq 0 ]; then
        gate_pass "omlx" "($omlx_verdict)"
    else
        gate_fail "omlx" "$omlx_verdict"
        echo "PREFLIGHT=FAIL detail=omlx"
        exit 2
    fi
fi

# ---- Gate 3: VM tripwire canonical state -----------------------------------
if [ "$SKIP_TRIPWIRE" -eq 1 ]; then
    gate_skip "tripwire"
else
    # Single SSH round-trip for all four files. Output format:
    #   <md5>  <path>
    # One per line. Parse, compare, report first mismatch.
    tripwire_cmd='md5sum \
        ~/.hermes/hermes-agent/HERMES.md \
        ~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md \
        ~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh \
        /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts'

    if ! tripwire_out="$(ssh -o ConnectTimeout=10 "$SSH_TARGET" "$tripwire_cmd" 2>&1)"; then
        gate_fail "tripwire" "ssh/md5sum failed: $(printf '%s' "$tripwire_out" | head -1)"
        echo "PREFLIGHT=FAIL detail=tripwire"
        exit 3
    fi

    # Extract md5 per file by path substring match (BSD/GNU md5sum compatible).
    extract_md5() {
        printf '%s\n' "$tripwire_out" | awk -v pat="$1" '$0 ~ pat { print $1; exit }'
    }
    got_hermes="$(extract_md5 'HERMES\.md$')"
    got_skill="$(extract_md5 'SKILL\.md$')"
    got_jira="$(extract_md5 'jira-briefing\.sh$')"
    got_dash="$(extract_md5 'useDashboard\.ts$')"

    first_bad=""
    declare -a bad_list=()
    if [ "$got_hermes" != "$TRIPWIRE_HERMES_MD5" ]; then
        bad_list+=("HERMES.md expected=$TRIPWIRE_HERMES_MD5 got=${got_hermes:-MISSING}")
        first_bad="${first_bad:-HERMES.md}"
    fi
    if [ "$got_skill" != "$TRIPWIRE_SKILL_MD5" ]; then
        bad_list+=("SKILL.md expected=$TRIPWIRE_SKILL_MD5 got=${got_skill:-MISSING}")
        first_bad="${first_bad:-SKILL.md}"
    fi
    if [ "$got_jira" != "$TRIPWIRE_JIRA_MD5" ]; then
        bad_list+=("jira-briefing.sh expected=$TRIPWIRE_JIRA_MD5 got=${got_jira:-MISSING}")
        first_bad="${first_bad:-jira-briefing.sh}"
    fi
    if [ "$got_dash" != "$TRIPWIRE_USE_DASHBOARD_MD5" ]; then
        bad_list+=("useDashboard.ts expected=$TRIPWIRE_USE_DASHBOARD_MD5 got=${got_dash:-MISSING}")
        first_bad="${first_bad:-useDashboard.ts}"
    fi

    if [ "${#bad_list[@]}" -eq 0 ]; then
        gate_pass "tripwire" "(all 4 canonical)"
    else
        for b in "${bad_list[@]}"; do
            echo "  tripwire-mismatch: $b" >&2
        done
        gate_fail "tripwire" "first mismatch: $first_bad"
        echo "PREFLIGHT=FAIL detail=tripwire"
        exit 3
    fi
fi

# ---- Gate 4: VM idle (no hermes chat running) -------------------------------
# The gateway process ("python -m hermes_cli.main gateway run --replace") is
# a long-running background service and is expected to be present. Only
# "hermes chat" indicates an actively running probe trial we'd conflict with.
if [ "$SKIP_VM_IDLE" -eq 1 ]; then
    gate_skip "vm_idle"
else
    # Pattern uses a character class so pgrep's own argv does NOT match its own
    # pattern — [h]ermes never contains the literal "[h]ermes" but does match
    # strings starting with "h". This is the idiomatic pgrep self-exclusion.
    if ! busy_out="$(ssh -o ConnectTimeout=10 "$SSH_TARGET" 'pgrep -af "[h]ermes chat" || true' 2>&1)"; then
        gate_fail "vm_idle" "ssh failed: $(printf '%s' "$busy_out" | head -1)"
        echo "PREFLIGHT=FAIL detail=vm_idle"
        exit 4
    fi
    if [ -n "$(printf '%s' "$busy_out" | tr -d '[:space:]')" ]; then
        echo "  vm_busy_procs:" >&2
        printf '    %s\n' "$busy_out" >&2
        gate_fail "vm_idle" "active 'hermes chat' process on VM"
        echo "PREFLIGHT=FAIL detail=vm_idle"
        exit 4
    fi
    gate_pass "vm_idle" "(no hermes chat)"
fi

# ---- All gates cleared ------------------------------------------------------
echo "PREFLIGHT=PASS"
exit 0
