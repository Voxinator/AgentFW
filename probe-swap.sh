#!/usr/bin/env bash
# probe-swap.sh — Stage, swap in, and swap out the Variant B HERMES.md on ubuntu-vm.
#
# USAGE:
#   ./probe-swap.sh stage      # Copy HERMES-variantB.md to VM, backup canonical, verify md5s
#   ./probe-swap.sh swap-in    # Replace live HERMES.md with Variant B (run this before Variant B probe trials)
#   ./probe-swap.sh swap-out   # Restore canonical HERMES.md (run immediately after Variant B trials)
#   ./probe-swap.sh status     # Report what's currently live on the VM and checksum match state
#
# SAFETY: Any md5 mismatch aborts with non-zero exit. Swap-out verifies canonical is restored
# before declaring success. Backup file remains on the VM after swap-out for paranoia.
#
# All operations are reversible. The only mutation is to ~/.hermes/hermes-agent/HERMES.md.
# Nothing in core/, references/, playbooks/, templates/, or other variants is touched.

set -euo pipefail

# --- config ---
LOCAL_VARIANT_B="/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantB.md"
LOCAL_CANONICAL="/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES.md"
REMOTE_HOST="ubuntu-vm"
REMOTE_DIR="~/.hermes/hermes-agent"
REMOTE_LIVE="${REMOTE_DIR}/HERMES.md"
REMOTE_VARIANT_B="${REMOTE_DIR}/HERMES-variantB.md"
REMOTE_BACKUP="${REMOTE_DIR}/HERMES-canonical-backup.md"

CANONICAL_MD5="0780c232a6cb52e13e432261f0d68ad9"

# --- helpers ---
die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-swap] $*"; }

md5_local() { md5 -q "$1" 2>/dev/null || md5sum "$1" | awk '{print $1}'; }
md5_remote() { ssh "$REMOTE_HOST" "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }

expect_md5() {
  local path=$1 expected=$2 label=$3
  local actual
  actual=$(md5_remote "$path")
  [[ "$actual" == "$expected" ]] || die "$label md5 mismatch: got '$actual', expected '$expected' (path: $path)"
}

# --- preflight: verify local files exist and canonical matches expected md5 ---
[[ -f "$LOCAL_VARIANT_B" ]]   || die "missing local file: $LOCAL_VARIANT_B"
[[ -f "$LOCAL_CANONICAL" ]]   || die "missing local file: $LOCAL_CANONICAL"

LOCAL_VARIANT_B_MD5=$(md5_local "$LOCAL_VARIANT_B")
LOCAL_CANONICAL_MD5=$(md5_local "$LOCAL_CANONICAL")

[[ "$LOCAL_CANONICAL_MD5" == "$CANONICAL_MD5" ]] || die \
  "local canonical HERMES.md md5 '$LOCAL_CANONICAL_MD5' != pinned '$CANONICAL_MD5' — did the canonical drift?"

# --- subcommands ---
cmd_stage() {
  log "Staging Variant B onto $REMOTE_HOST..."

  # 1. Confirm live HERMES.md on the VM matches canonical (i.e. nothing else has drifted it).
  log "Verifying live HERMES.md on VM matches canonical..."
  expect_md5 "$REMOTE_LIVE" "$CANONICAL_MD5" "live HERMES.md"

  # 2. Backup live HERMES.md to HERMES-canonical-backup.md on the VM (idempotent).
  log "Backing up live HERMES.md → HERMES-canonical-backup.md (on VM)..."
  ssh "$REMOTE_HOST" "cp -f $REMOTE_LIVE $REMOTE_BACKUP"
  expect_md5 "$REMOTE_BACKUP" "$CANONICAL_MD5" "remote backup"

  # 3. Copy Variant B from local project to VM.
  log "Copying $LOCAL_VARIANT_B → $REMOTE_HOST:$REMOTE_VARIANT_B..."
  scp -q "$LOCAL_VARIANT_B" "$REMOTE_HOST:$REMOTE_VARIANT_B"
  expect_md5 "$REMOTE_VARIANT_B" "$LOCAL_VARIANT_B_MD5" "remote Variant B after scp"

  log "STAGE COMPLETE."
  log "  live HERMES.md: md5 $CANONICAL_MD5 (unchanged, canonical)"
  log "  backup        : md5 $CANONICAL_MD5 (matches canonical)"
  log "  Variant B     : md5 $LOCAL_VARIANT_B_MD5 (on VM, not yet swapped in)"
  log "Next: ./probe-swap.sh swap-in"
}

cmd_swap_in() {
  log "Swapping Variant B into live HERMES.md..."

  # Safety checks: confirm Variant B is staged and canonical is backed up.
  local staged_md5 backup_md5 live_md5
  staged_md5=$(md5_remote "$REMOTE_VARIANT_B")
  backup_md5=$(md5_remote "$REMOTE_BACKUP")
  live_md5=$(md5_remote "$REMOTE_LIVE")

  [[ -n "$staged_md5" ]] || die "Variant B not staged on VM — run './probe-swap.sh stage' first"
  [[ "$staged_md5" == "$LOCAL_VARIANT_B_MD5" ]] || die "staged Variant B md5 drift (got $staged_md5, expected $LOCAL_VARIANT_B_MD5)"
  [[ "$backup_md5" == "$CANONICAL_MD5" ]] || die "backup md5 mismatch (got $backup_md5, expected $CANONICAL_MD5) — refusing to swap"

  # Idempotency: if live is already Variant B, exit cleanly.
  if [[ "$live_md5" == "$LOCAL_VARIANT_B_MD5" ]]; then
    log "live HERMES.md already IS Variant B (md5 $live_md5) — no-op"
    return 0
  fi

  [[ "$live_md5" == "$CANONICAL_MD5" ]] || die "live HERMES.md is neither canonical nor Variant B (md5 $live_md5) — refusing to overwrite unknown state"

  ssh "$REMOTE_HOST" "cp -f $REMOTE_VARIANT_B $REMOTE_LIVE"
  expect_md5 "$REMOTE_LIVE" "$LOCAL_VARIANT_B_MD5" "live after swap-in"

  log "SWAP-IN COMPLETE."
  log "  live HERMES.md = Variant B (md5 $LOCAL_VARIANT_B_MD5)"
  log "  canonical backed up at: $REMOTE_BACKUP"
  log "Run your 10 Variant B probe trials now."
  log "When done: ./probe-swap.sh swap-out"
}

cmd_swap_out() {
  log "Restoring canonical HERMES.md from backup..."

  local backup_md5 live_md5
  backup_md5=$(md5_remote "$REMOTE_BACKUP")
  live_md5=$(md5_remote "$REMOTE_LIVE")

  [[ "$backup_md5" == "$CANONICAL_MD5" ]] || die "backup md5 mismatch (got $backup_md5, expected $CANONICAL_MD5) — cannot safely restore"

  # Idempotency: if live is already canonical, exit cleanly.
  if [[ "$live_md5" == "$CANONICAL_MD5" ]]; then
    log "live HERMES.md already IS canonical (md5 $live_md5) — no-op"
    return 0
  fi

  ssh "$REMOTE_HOST" "cp -f $REMOTE_BACKUP $REMOTE_LIVE"
  expect_md5 "$REMOTE_LIVE" "$CANONICAL_MD5" "live after swap-out"

  log "SWAP-OUT COMPLETE."
  log "  live HERMES.md = canonical (md5 $CANONICAL_MD5)"
  log "  backup retained at: $REMOTE_BACKUP (leave in place for a few days in case of re-runs)"
  log "Production Hermes is back on canonical HERMES.md."
}

cmd_status() {
  log "Current state on $REMOTE_HOST:"
  local live_md5 variant_md5 backup_md5
  live_md5=$(md5_remote "$REMOTE_LIVE")
  variant_md5=$(md5_remote "$REMOTE_VARIANT_B")
  backup_md5=$(md5_remote "$REMOTE_BACKUP")

  local live_state="unknown"
  case "$live_md5" in
    "$CANONICAL_MD5")       live_state="CANONICAL" ;;
    "$LOCAL_VARIANT_B_MD5") live_state="VARIANT B" ;;
    "")                     live_state="MISSING" ;;
    *)                      live_state="UNKNOWN md5" ;;
  esac

  printf "  live HERMES.md : %-32s %s\n" "$live_md5" "[$live_state]"
  printf "  Variant B      : %-32s %s\n" "${variant_md5:-<not staged>}" "$([[ "$variant_md5" == "$LOCAL_VARIANT_B_MD5" ]] && echo '[matches local]' || echo '[drifted or missing]')"
  printf "  backup         : %-32s %s\n" "${backup_md5:-<no backup>}" "$([[ "$backup_md5" == "$CANONICAL_MD5" ]] && echo '[matches canonical]' || echo '[NOT canonical]')"
}

# --- dispatch ---
case "${1:-}" in
  stage)    cmd_stage ;;
  swap-in)  cmd_swap_in ;;
  swap-out) cmd_swap_out ;;
  status)   cmd_status ;;
  "")       die "usage: $0 {stage|swap-in|swap-out|status}" ;;
  *)        die "unknown subcommand: $1 (use: stage | swap-in | swap-out | status)" ;;
esac
