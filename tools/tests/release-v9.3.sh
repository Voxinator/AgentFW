#!/usr/bin/env bash
# Deterministic release gate for the AgentFW v9.3 line (currently v9.3.0).
#
# AGENTFW_RELEASE_ROOT may point at a scratch copy for red-path probes (SKILL desync, stale
# metadata, laundered posture fixture). AGENTFW_RELEASE_IDENTITY_ONLY=1 stops after the
# release-document checks; the normal contracted acceptance command sets neither variable and runs
# every deterministic suite below.
set -euo pipefail

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ROOT=${AGENTFW_RELEASE_ROOT:-$SCRIPT_ROOT}

fail() {
  printf 'release-v9.3.sh: FAIL: %s\n' "$*" >&2
  exit 1
}

require_file() {
  [ -f "$ROOT/$1" ] || fail "missing required file: $1"
}

require_contains() {
  grep -Fq -- "$2" "$ROOT/$1" || fail "$1 is missing required text: $2"
}

require_not_contains() {
  if grep -Fq -- "$2" "$ROOT/$1"; then
    fail "$1 contains stale text that v9.3 must have removed: $2"
  fi
}

for required in \
  metadata.json README.md CHANGELOG.md DESIGN.md \
  RELEASE-NOTES-v9.3.0.md RELEASE-NOTES-v9.2.0.md \
  CANDIDATES.md PLAN-v9.3-sleep-adaptive.md \
  policy/model-dispatch.md policy/assurance-model.md policy/capability-contract.md \
  tools/validate-capability tools/check-skill-sync.py \
  tools/check-posture-invariants.py tools/check-candidates.py \
  evaluation/fixtures/sleep-posture.json evaluation/eval-v9.3-sleep-adaptive.md \
  profiles/chatgpt-projects.md \
  adapters/claude-code/INSTALL.md adapters/codex/INSTALL.md \
  adapters/claude-code/capability.yaml adapters/codex/capability.yaml
do
  require_file "$required"
done

python3 - "$ROOT/metadata.json" <<'PY' \
  || fail "metadata.json must report version 9.3.0 and revision r9.3"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
assert data.get("version") == "9.3.0", data.get("version")
assert data.get("revision") == "r9.3", data.get("revision")
PY

# --- release identity, current-facing docs ---
require_contains README.md '**Status: v9.3.0, released 2026-07-21**'
require_contains README.md "## What's new in v9.3"
require_contains README.md 'tools/tests/release-v9.3.sh'
require_contains README.md '[the v9.3.0 release notes](RELEASE-NOTES-v9.3.0.md)'
require_contains profiles/chatgpt-projects.md 'Current release: **AgentFW v9.3.0**'
require_contains adapters/claude-code/INSTALL.md 'Current release: **AgentFW v9.3.0**'
require_contains adapters/codex/INSTALL.md 'Current release: **AgentFW v9.3.0**'
require_contains DESIGN.md '**Current-release note (v9.3.0):**'
require_contains DESIGN.md '| v9.3.0 | 2026-07-21 |'
require_contains CHANGELOG.md '## v9.3.0 (2026-07-21) — RELEASED'
require_contains CHANGELOG.md 'D-14 — adaptive dispatch'
require_contains CHANGELOG.md 'D-15 — sleep mode'
require_contains RELEASE-NOTES-v9.3.0.md 'No behavioral-evaluation round was run for v9.3.0'
require_contains RELEASE-NOTES-v9.3.0.md 'economic escalation'
require_contains RELEASE-NOTES-v9.3.0.md 'never waivable'

# --- D-14 / D-15 policy + surfacing facts (reverting any is a release regression) ---
require_contains policy/model-dispatch.md 'The flagship cap'
require_contains policy/model-dispatch.md 'Verifier tier floor'
require_contains policy/model-dispatch.md 'Uniform / Mirror'
require_contains policy/assurance-model.md 'Unattended (sleep) posture'
require_contains policy/assurance-model.md 'SLEEP-HALT'
require_contains policy/assurance-model.md 'non-delegable'
require_contains policy/capability-contract.md 'model_selection'
require_contains adapters/claude-code/capability.yaml 'model_selection'
require_contains adapters/codex/capability.yaml 'model_selection'
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'AGENTFW-SYNC:v9.3'
require_contains adapters/codex/skills/agentfw/SKILL.md 'AGENTFW-SYNC:v9.3'

# --- partial-update trap: no stale key-count prose survives at 11 keys ---
require_not_contains policy/capability-contract.md 'The ten capability keys'
require_not_contains policy/capability-contract.md 'exactly the ten keys'
require_not_contains tools/validate-capability 'the 10 capability keys'
require_not_contains tools/validate-capability 'all 10 capability keys present'

printf 'release-v9.3.sh: PASS: release identity, current docs, D-14/D-15 policy + surfacing\n'

if [ "${AGENTFW_RELEASE_IDENTITY_ONLY:-0}" = 1 ]; then
  printf 'RELEASE_V9_3_IDENTITY_OK\n'
  exit 0
fi

# --- existing deterministic suites ---
( cd "$ROOT" && bash tools/tests/validate-plan.sh )
printf 'release-v9.3.sh: PASS: validator fixture harness\n'
( cd "$ROOT" && bash tools/tests/install-roundtrip.sh )
printf 'release-v9.3.sh: PASS: installer roundtrip\n'
( cd "$ROOT" && bash tools/tests/check-links.sh )
printf 'release-v9.3.sh: PASS: relative links\n'

# --- capability validation: 11 keys with ladder sub-fields, via BOTH parser paths ---
python3 -c 'import yaml' \
  || fail "PyYAML is unavailable; cannot exercise both capability parser paths"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.3.sh: PASS: capability validation (11 keys, both parser paths)\n'

# --- D-14/D-15 machine checks (each red-path probed in the release record) ---
python3 "$ROOT/tools/check-skill-sync.py"
printf 'release-v9.3.sh: PASS: adapter SKILL sync\n'
python3 "$ROOT/tools/check-posture-invariants.py" --selftest
python3 "$ROOT/tools/check-posture-invariants.py" "$ROOT/evaluation/fixtures/sleep-posture.json"
printf 'release-v9.3.sh: PASS: sleep-posture floor-halt invariant\n'
( cd "$ROOT" && python3 tools/check-candidates.py D-14 D-15 )
printf 'release-v9.3.sh: PASS: ledger completeness (D-14, D-15)\n'

# --- root release-document relative links (outside check-links.sh's normal scan) ---
python3 - "$ROOT" <<'PY' \
  || fail "a root release-document link is unresolved"
import pathlib
import re
import sys
root = pathlib.Path(sys.argv[1])
for relative in ("README.md", "CHANGELOG.md", "RELEASE-NOTES-v9.3.0.md"):
    source = root / relative
    text = source.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        candidate = source.parent / target
        root_candidate = root / target
        assert candidate.exists() or root_candidate.exists(), f"{relative} -> {target}"
PY
printf 'release-v9.3.sh: PASS: root release-document links\n'

printf 'RELEASE_V9_3_OK\n'
