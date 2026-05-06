#!/usr/bin/env bash
# score.sh — invoke content_verify.py against a scaffold and emit a
# campaign-shaped JSON verdict.
#
# RC scoring (per Brian, 2026-05-03):
#   Strict completion = (content_verify strict_passed) AND
#                       (every verified-state.json phase status == verified_passed)
#   Charitable        = (content_verify charitable_passed) AND
#                       (every phase verified_passed)
# Rationale: a trial where the orchestrator terminates before all phases
# verify_passed factually doesn't have all phases verified — under r7.11's
# rubric that trial fails strict by definition. Treating it as observational-
# only would hide architectural failures in adherence noise.
#
# Usage:
#   score.sh <scaffold-root> [<plan-md-path>]
# Output (stdout, JSON):
#   {
#     "strict_passed": bool,           # campaign verdict (combines content_verify + state)
#     "charitable_passed": bool,
#     "content_verify_strict": bool,   # raw from content_verify.py
#     "content_verify_charitable": bool,
#     "all_phases_verified_passed": bool,
#     "phases_pending_or_failed": [int],
#     "findings": [...],
#     "campaign_findings": [str]       # added by this wrapper, not by content_verify
#   }
# Exit code: 0 if campaign strict_passed, 1 otherwise.

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <scaffold-root> [<plan-md-path>]" >&2
  exit 2
fi

SCAFFOLD="$1"
PLAN_ARG=""
if [[ $# -eq 2 ]]; then
  PLAN_ARG="--plan-md $2"
fi

HARNESS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTENT_VERIFY="$HARNESS/../content_verify.py"

if [[ ! -f "$CONTENT_VERIFY" ]]; then
  echo "FATAL: content_verify.py not at $CONTENT_VERIFY" >&2
  exit 3
fi

PY="$SCAFFOLD/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3.11 || command -v python3)"

CV_OUT=$(mktemp)
trap 'rm -f "$CV_OUT"' EXIT

# content_verify.py exits 0 on strict_passed, 1 otherwise; we don't propagate
# its exit directly because the campaign verdict combines both signals.
"$PY" "$CONTENT_VERIFY" "$SCAFFOLD" $PLAN_ARG --json > "$CV_OUT" || true

STATE_FILE="$SCAFFOLD/verified-state.json"

python3 - "$CV_OUT" "$STATE_FILE" <<'PYTHON'
import json, sys

cv_path, state_path = sys.argv[1:]

cv = json.load(open(cv_path))
content_strict = bool(cv.get("strict_passed"))
content_charitable = bool(cv.get("charitable_passed"))

campaign_findings = []
all_passed = True
pending_or_failed = []

try:
    with open(state_path) as f:
        state = json.load(f)
    phase_state = state.get("phase_state", []) or []
    if not phase_state:
        all_passed = False
        campaign_findings.append(
            "[ORCHESTRATOR_TERMINATED_EARLY] verified-state.json has no phase_state — "
            "orchestrator never reached PHASE LOOP step B; "
            "campaign-strict and campaign-charitable forced False."
        )
    else:
        for ps in phase_state:
            status = ps.get("status")
            if status != "verified_passed":
                all_passed = False
                pending_or_failed.append(ps.get("id"))
        if pending_or_failed:
            campaign_findings.append(
                f"[ORCHESTRATOR_TERMINATED_EARLY] phases {pending_or_failed} not verified_passed; "
                f"campaign-strict and campaign-charitable forced False regardless of content_verify verdict."
            )
except FileNotFoundError:
    all_passed = False
    campaign_findings.append(
        f"[ORCHESTRATOR_TERMINATED_EARLY] verified-state.json missing at {state_path}; "
        f"orchestrator never invoked verify_phase; campaign-strict and campaign-charitable forced False."
    )
except json.JSONDecodeError as e:
    all_passed = False
    campaign_findings.append(
        f"[VERIFIED_STATE_CORRUPT] verified-state.json failed to parse: {e}; "
        f"campaign-strict and campaign-charitable forced False."
    )

strict_passed = content_strict and all_passed
charitable_passed = content_charitable and all_passed

out = {
    "strict_passed": strict_passed,
    "charitable_passed": charitable_passed,
    "content_verify_strict": content_strict,
    "content_verify_charitable": content_charitable,
    "all_phases_verified_passed": all_passed,
    "phases_pending_or_failed": pending_or_failed,
    "campaign_findings": campaign_findings,
    "findings": cv.get("findings", []),
    "files_inspected": cv.get("files_inspected", []),
}
json.dump(out, sys.stdout, indent=2)
sys.stdout.write("\n")
sys.exit(0 if strict_passed else 1)
PYTHON
