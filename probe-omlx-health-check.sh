#!/usr/bin/env bash
# probe-omlx-health-check.sh — Report oMLX/Mac-host health as single-line verdict.
# Run between probe-trial batches to detect state drift that contaminates results
# (e.g. accumulated orphaned oMLX sessions eating RAM, swap pressure, or stalled
# generations). Read-only diagnostic — does NOT restart oMLX or modify state.
#
# Usage:
#   probe-omlx-health-check.sh
#
# Output (line 1, machine-parseable):
#   OMLX_HEALTH=CLEAN
#   OMLX_HEALTH=DEGRADED detail=<breach_list>
#
# Exit codes: 0=CLEAN, 1=DEGRADED, 2=ERROR
#
# Env var thresholds:
#   OMLX_MEM_FREE_MIN_GB (default 20)
#   OMLX_SWAP_MAX_GB (default 5)
#   OMLX_ACTIVE_SESSIONS_MAX (default 1)
#   OMLX_URL (default http://localhost:8000)
#   OMLX_API_KEY (optional) — when set, enables authenticated /v1/* queries
#     for active session count. Without it, omlx_active_sessions=unknown.

set -euo pipefail

# ---- Thresholds (env-overridable) -------------------------------------------
OMLX_MEM_FREE_MIN_GB="${OMLX_MEM_FREE_MIN_GB:-20}"
OMLX_SWAP_MAX_GB="${OMLX_SWAP_MAX_GB:-5}"
OMLX_ACTIVE_SESSIONS_MAX="${OMLX_ACTIVE_SESSIONS_MAX:-1}"
OMLX_URL="${OMLX_URL:-http://localhost:8000}"
: "${OMLX_API_KEY:=}"  # optional — when set, used for authenticated endpoint queries

# Build curl auth header flag conditionally. Array stays empty when key absent,
# so expansion of "${AUTH_HEADER[@]}" in curl calls contributes no arguments.
# The key value itself never appears in script output — only in the header.
declare -a AUTH_HEADER=()
if [[ -n "$OMLX_API_KEY" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer $OMLX_API_KEY")
fi

# ---- Helpers ----------------------------------------------------------------
# Portable floating-point compare: returns 0 if $1 > $2, else 1. Uses awk (BSD-safe).
fgt() { awk -v a="$1" -v b="$2" 'BEGIN { exit !(a+0 > b+0) }'; }
flt() { awk -v a="$1" -v b="$2" 'BEGIN { exit !(a+0 < b+0) }'; }

# Format a float to 1 decimal place (BSD awk safe).
fmt1() { awk -v v="$1" 'BEGIN { printf "%.1f", v+0 }'; }

# ---- Check 1: Free memory (Mac) ---------------------------------------------
# vm_stat reports pages; multiply (free + inactive) * page_size to get "available"
# memory the kernel can hand out without forcing swap. This is the standard
# approximation on macOS for "usable free RAM" since inactive is reclaimable.
check_mem() {
    local vmstat_out page_size_bytes pages_free pages_inactive free_bytes free_gb
    if ! vmstat_out="$(vm_stat 2>/dev/null)"; then
        echo "ERROR: vm_stat failed" >&2
        return 1
    fi
    # "Mach Virtual Memory Statistics: (page size of 16384 bytes)"
    page_size_bytes="$(printf '%s\n' "$vmstat_out" | awk '/page size of/ { for (i=1;i<=NF;i++) if ($i ~ /^[0-9]+$/) { print $i; exit } }')"
    pages_free="$(printf '%s\n' "$vmstat_out" | awk -F'[ .]+' '/^Pages free:/ { print $3 }')"
    pages_inactive="$(printf '%s\n' "$vmstat_out" | awk -F'[ .]+' '/^Pages inactive:/ { print $3 }')"
    if [ -z "${page_size_bytes:-}" ] || [ -z "${pages_free:-}" ] || [ -z "${pages_inactive:-}" ]; then
        echo "ERROR: could not parse vm_stat output" >&2
        return 1
    fi
    free_bytes="$(awk -v pf="$pages_free" -v pi="$pages_inactive" -v ps="$page_size_bytes" 'BEGIN { print (pf+pi)*ps }')"
    free_gb="$(awk -v b="$free_bytes" 'BEGIN { printf "%.2f", b/(1024*1024*1024) }')"
    printf '%s' "$free_gb"
}

# ---- Check 2: Swap usage (Mac) ----------------------------------------------
# sysctl vm.swapusage -> "vm.swapusage: total = 5120.00M  used = 4101.88M  free = 1018.12M  (encrypted)"
# Parse "used" field; convert unit (M or G) to GB.
check_swap() {
    local line used_raw used_val used_unit used_gb
    if ! line="$(sysctl -n vm.swapusage 2>/dev/null)"; then
        echo "ERROR: sysctl vm.swapusage failed" >&2
        return 1
    fi
    used_raw="$(printf '%s\n' "$line" | awk '{ for (i=1;i<=NF;i++) if ($i=="used") { print $(i+2); exit } }')"
    if [ -z "${used_raw:-}" ]; then
        echo "ERROR: could not parse swapusage: $line" >&2
        return 1
    fi
    # Strip trailing unit letter; keep numeric value and unit separately.
    used_val="$(printf '%s' "$used_raw" | awk '{ sub(/[A-Za-z]$/,""); print }')"
    used_unit="$(printf '%s' "$used_raw" | awk '{ print substr($0,length($0)) }')"
    case "$used_unit" in
        K|k) used_gb="$(awk -v v="$used_val" 'BEGIN { printf "%.2f", v/(1024*1024) }')" ;;
        M|m) used_gb="$(awk -v v="$used_val" 'BEGIN { printf "%.2f", v/1024 }')" ;;
        G|g) used_gb="$(awk -v v="$used_val" 'BEGIN { printf "%.2f", v+0 }')" ;;
        *)   used_gb="$(awk -v v="$used_val" 'BEGIN { printf "%.2f", v/(1024*1024*1024) }')" ;;  # assume bytes
    esac
    printf '%s' "$used_gb"
}

# ---- Check 3: oMLX active generation sessions -------------------------------
# Strategy:
#   1. Hit /health (no auth) — always works if oMLX is up. Gives `loaded_count`
#      (models loaded into memory) as a weak proxy.
#   2. When OMLX_API_KEY is set, hit /api/status (auth'd) which returns
#      `active_requests` (currently-generating) and `waiting_requests` (queued).
#      Discovered endpoint 2026-04-19 (oMLX 0.3.6). Other candidates tried:
#        /v1/models (404 for session count — just lists models)
#        /metrics, /v1/metrics, /v1/sessions, /stats, /v1/status, /v1/requests,
#        /v1/engines, /v1/engine_pool, /v1/admin, /admin/sessions, /active,
#        /sessions — all 404 or not session-count bearing.
#      Only /api/status exposes per-server active/waiting counts cleanly.
#      JSON path used: .active_requests
#   3. When key absent OR auth fails OR parse fails, fall back to "unknown"
#      (not an error) per spec. The count signal does not degrade the verdict
#      unless it's a real integer > OMLX_ACTIVE_SESSIONS_MAX.
# Writes two globals: OMLX_SESSIONS (count or "unknown") and OMLX_LOADED_COUNT.
check_omlx_sessions() {
    local health_body http_code status_code status_body active
    # -m 3 = 3s timeout so we stay under the <5s budget even if oMLX hangs.
    # Use `|| true` + empty-check to disarm pipefail if curl fails (e.g. exit 7 = no connection).
    http_code="$(curl -s -m 3 -o /tmp/omlx_health.$$ -w '%{http_code}' "$OMLX_URL/health" 2>/dev/null || true)"
    if [ -z "$http_code" ] || ! printf '%s' "$http_code" | grep -qE '^[0-9]+$'; then
        http_code="000"
    fi
    if [ "$http_code" != "200" ]; then
        rm -f /tmp/omlx_health.$$
        OMLX_REACHABLE=0
        OMLX_SESSIONS="unknown"
        OMLX_LOADED_COUNT="unknown"
        OMLX_HEALTH_NOTE="oMLX unreachable (http=$http_code)"
        return 0
    fi
    health_body="$(cat /tmp/omlx_health.$$)"
    rm -f /tmp/omlx_health.$$
    OMLX_REACHABLE=1
    OMLX_HEALTH_NOTE=""

    # Parse loaded_count from /health JSON. Prefer jq; fall back to grep/awk.
    if command -v jq >/dev/null 2>&1; then
        OMLX_LOADED_COUNT="$(printf '%s' "$health_body" | jq -r '.engine_pool.loaded_count // "unknown"' 2>/dev/null || echo "unknown")"
    else
        # Crude fallback: extract integer after "loaded_count":
        OMLX_LOADED_COUNT="$(printf '%s' "$health_body" | awk 'match($0,/"loaded_count"[[:space:]]*:[[:space:]]*[0-9]+/) { s=substr($0,RSTART,RLENGTH); sub(/.*:[[:space:]]*/,"",s); print s; exit }')"
        [ -z "$OMLX_LOADED_COUNT" ] && OMLX_LOADED_COUNT="unknown"
    fi

    # Default: unknown. Overridden below iff auth key set AND /api/status parses.
    OMLX_SESSIONS="unknown"

    if [ -z "$OMLX_API_KEY" ]; then
        return 0
    fi

    # Auth'd /api/status probe. NOTE: AUTH_HEADER array carries the bearer header
    # — it's never printed, and curl's URL line doesn't contain the key.
    status_code="$(curl -s -m 3 -o /tmp/omlx_status.$$ -w '%{http_code}' "${AUTH_HEADER[@]}" "$OMLX_URL/api/status" 2>/dev/null || true)"
    if [ -z "$status_code" ] || ! printf '%s' "$status_code" | grep -qE '^[0-9]+$'; then
        status_code="000"
    fi
    if [ "$status_code" != "200" ]; then
        rm -f /tmp/omlx_status.$$
        # Do NOT include the HTTP code's body (may echo key in error?) — just code.
        OMLX_HEALTH_NOTE="auth status probe http=$status_code"
        return 0
    fi
    status_body="$(cat /tmp/omlx_status.$$)"
    rm -f /tmp/omlx_status.$$

    if command -v jq >/dev/null 2>&1; then
        active="$(printf '%s' "$status_body" | jq -r '.active_requests // "unknown"' 2>/dev/null || echo "unknown")"
    else
        active="$(printf '%s' "$status_body" | awk 'match($0,/"active_requests"[[:space:]]*:[[:space:]]*[0-9]+/) { s=substr($0,RSTART,RLENGTH); sub(/.*:[[:space:]]*/,"",s); print s; exit }')"
        [ -z "$active" ] && active="unknown"
    fi
    # Guard: only accept pure-integer results; otherwise leave as "unknown".
    if printf '%s' "$active" | grep -qE '^[0-9]+$'; then
        OMLX_SESSIONS="$active"
    fi
}

# ---- Main -------------------------------------------------------------------
breaches=()
report_lines=()

# Memory check
if mem_gb="$(check_mem)"; then
    if flt "$mem_gb" "$OMLX_MEM_FREE_MIN_GB"; then
        breaches+=("mem_low")
    fi
    report_lines+=("  free_mem_gb=$(fmt1 "$mem_gb") (threshold >=${OMLX_MEM_FREE_MIN_GB})")
else
    report_lines+=("  free_mem_gb=ERROR")
    printf 'OMLX_HEALTH=ERROR detail=mem_check_failed\n'
    printf '%s\n' "${report_lines[@]}" >&2
    exit 2
fi

# Swap check
if swap_gb="$(check_swap)"; then
    if fgt "$swap_gb" "$OMLX_SWAP_MAX_GB"; then
        breaches+=("swap_high")
    fi
    report_lines+=("  swap_used_gb=$(fmt1 "$swap_gb") (threshold <=${OMLX_SWAP_MAX_GB})")
else
    report_lines+=("  swap_used_gb=ERROR")
    printf 'OMLX_HEALTH=ERROR detail=swap_check_failed\n'
    printf '%s\n' "${report_lines[@]}" >&2
    exit 2
fi

# oMLX session check (advisory — does not degrade on its own per spec)
check_omlx_sessions
if [ "$OMLX_SESSIONS" = "unknown" ]; then
    note="omlx_active_sessions=unknown"
    [ -n "$OMLX_HEALTH_NOTE" ] && note="$note ($OMLX_HEALTH_NOTE)"
    report_lines+=("  $note")
else
    # Reserved path: if a future revision can count active sessions, degrade here.
    if [ "$OMLX_SESSIONS" -gt "$OMLX_ACTIVE_SESSIONS_MAX" ] 2>/dev/null; then
        breaches+=("too_many_sessions")
    fi
    report_lines+=("  omlx_active_sessions=${OMLX_SESSIONS} (threshold <=${OMLX_ACTIVE_SESSIONS_MAX})")
fi
report_lines+=("  omlx_loaded_count=${OMLX_LOADED_COUNT} (advisory)")

# Verdict
if [ "${#breaches[@]}" -eq 0 ]; then
    printf 'OMLX_HEALTH=CLEAN\n'
    printf '%s\n' "${report_lines[@]}" >&2
    exit 0
else
    detail="$(IFS=,; echo "${breaches[*]}")"
    printf 'OMLX_HEALTH=DEGRADED detail=%s\n' "$detail"
    printf '%s\n' "${report_lines[@]}" >&2
    exit 1
fi
