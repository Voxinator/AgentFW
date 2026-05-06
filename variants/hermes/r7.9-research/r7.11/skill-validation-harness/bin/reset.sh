#!/usr/bin/env bash
# reset.sh — restore a pristine scaffold from Brian's canonical tar and a
# fresh py3.11 .venv, ready for a Track A trial. Idempotent.
#
# Usage:
#   reset.sh <work-dir> [--baseline-tar PATH] [--keep-plan]
#
#   <work-dir>          per-trial scaffold root. Default Track A path:
#                       /tmp/r7.11-item8-scaffold (matches USER-PROMPT.md).
#   --baseline-tar PATH path to scaffold-baseline.tar.gz from Brian.
#                       Default: ~/Downloads/scaffold-baseline.tar.gz
#   --keep-plan         keep PLAN.md from the tar (for B-2b-subprocess arm
#                       only — Track A omits PLAN.md so the orchestrator
#                       authors its own per the skill's PHASE 0).
#
# Post-trial artifacts always stripped: .session-archive/,
# .session-end-signal.json, verified-state.json. Sentinel wipe matters —
# pre-flight 2b runs 1-2 (2026-05-03) confirmed stale .session-end-signal.json
# leaks into the next trial's behavior.
#
# Effect:
#   - rm -rf <work-dir>/* and <work-dir>/.* (full wipe)
#   - tar -xzf <baseline-tar> --strip-components=1 -C <work-dir>
#   - rm <work-dir>/{PLAN.md unless --keep-plan, .session-archive,
#                    .session-end-signal.json, verified-state.json}
#   - python3.11 -m venv <work-dir>/.venv
#   - pip install pytest fastapi httpx reportlab
#     (item-8 scaffold needs these; matches r7.11 trial-1 venv state)

set -euo pipefail

WORK=""
BASELINE_TAR="$HOME/Downloads/scaffold-baseline.tar.gz"
KEEP_PLAN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --baseline-tar) BASELINE_TAR="$2"; shift 2;;
    --keep-plan) KEEP_PLAN=1; shift;;
    -*) echo "unknown flag: $1" >&2; exit 2;;
    *) WORK="$1"; shift;;
  esac
done

[[ -z "$WORK" ]] && WORK="/tmp/r7.11-item8-scaffold"

PYTHON311="$(uv python find 3.11 2>/dev/null || command -v python3.11 || true)"
[[ -z "$PYTHON311" ]] && {
  echo "FATAL: python 3.11 not found. Run: uv python install 3.11" >&2
  exit 3
}

[[ -f "$BASELINE_TAR" ]] || {
  echo "FATAL: baseline tar not at $BASELINE_TAR" >&2
  exit 3
}

mkdir -p "$WORK"

# Full wipe — including dotfiles. We rely on the tar to restore everything.
# Use a subshell + find to avoid `rm -rf "$WORK"/* .*` glob hazards.
find "$WORK" -mindepth 1 -delete

tar -xzf "$BASELINE_TAR" --strip-components=1 -C "$WORK"

# Strip post-trial artifacts always.
rm -rf "$WORK/.session-archive"
rm -f  "$WORK/.session-end-signal.json"
rm -f  "$WORK/verified-state.json"

# Strip PLAN.md unless --keep-plan (B-2b-subprocess arm pre-stages PLAN.md;
# Track A and B-2a let the orchestrator author its own per skill PHASE 0).
if [[ "$KEEP_PLAN" -eq 0 ]]; then
  rm -f "$WORK/PLAN.md"
fi

"$PYTHON311" -m venv "$WORK/.venv"
"$WORK/.venv/bin/pip" install --quiet --upgrade pip
"$WORK/.venv/bin/pip" install --quiet pytest fastapi httpx reportlab

echo "reset OK: $WORK"
echo "  python:   $("$WORK/.venv/bin/python" --version 2>&1 | awk '{print $2}')"
echo "  baseline: $BASELINE_TAR ($(shasum -a 256 "$BASELINE_TAR" | awk '{print $1}' | cut -c1-12)…)"
echo "  PLAN.md:  $([[ -f "$WORK/PLAN.md" ]] && echo "present (--keep-plan)" || echo "stripped")"
