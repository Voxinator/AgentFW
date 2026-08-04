#!/usr/bin/env bash
# Deterministic release gate for the AgentFW v9.7 line (currently v9.7.0).
#
# AGENTFW_RELEASE_ROOT may point at a scratch copy for red-path probes.
# AGENTFW_RELEASE_IDENTITY_ONLY=1 stops after the release-identity checks; the normal
# contracted acceptance command sets neither variable and runs every deterministic suite below.
set -euo pipefail

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ROOT=${AGENTFW_RELEASE_ROOT:-$SCRIPT_ROOT}

fail() {
  printf 'release-v9.7.sh: FAIL: %s\n' "$*" >&2
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
    fail "$1 contains stale text that v9.7 must have removed: $2"
  fi
}

for required in \
  metadata.json CHANGELOG.md CANDIDATES.md \
  RELEASE-NOTES-v9.7.0.md \
  PLAN-v9.6-operator-compass.md \
  policy/plan-critique.md policy/acceptance-contract.md \
  tools/validate-plan tools/validate-capability tools/check-skill-sync.py \
  tools/check-candidates.py tools/check-reapproach-invariants.py \
  tools/tests/validate-plan.sh tools/tests/install-roundtrip.sh tools/tests/check-links.sh \
  evaluation/fixtures/reapproach-fork.json \
  adapters/claude-code/CLAUDE-block.md adapters/codex/AGENTS.md \
  adapters/claude-code/INSTALL.md adapters/codex/INSTALL.md \
  adapters/claude-code/capability.yaml adapters/codex/capability.yaml \
  adapters/claude-code/skills/agentfw/SKILL.md adapters/codex/skills/agentfw/SKILL.md \
  adapters/claude-code/agents/agentfw-verifier.md \
  adapters/claude-code/agents/agentfw-plan-critic.md
do
  require_file "$required"
done

# --- release identity: metadata.json + the four adapter surfaces (D-28..D-36 hardening) ---
# A kernel bootloader that misreports its own release is the specific failure this block exists
# to prevent (v9.7 build learned this the hard way — see field report on schema-1.6 drift).
python3 - "$ROOT/metadata.json" <<'PY' \
  || fail "metadata.json must report version 9.7.0 and revision r9.7"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
assert data.get("version") == "9.7.0", data.get("version")
assert data.get("revision") == "r9.7", data.get("revision")
PY

require_contains adapters/claude-code/CLAUDE-block.md 'Installed release: **AgentFW v9.7.0**'
require_contains adapters/codex/AGENTS.md 'Installed release: **AgentFW v9.7.0**'
require_contains adapters/claude-code/INSTALL.md 'Current release: **AgentFW v9.7.0**'
require_contains adapters/codex/INSTALL.md 'Current release: **AgentFW v9.7.0**'

printf 'release-v9.7.sh: PASS: release identity (metadata.json + four adapter surfaces report v9.7.0)\n'

if [ "${AGENTFW_RELEASE_IDENTITY_ONLY:-0}" = 1 ]; then
  printf 'RELEASE_V9_7_IDENTITY_OK\n'
  exit 0
fi

# --- no adapter surface retains the demoted schema-1.6 plan-time witness-tree duty ---
# policy/plan-critique.md and policy/acceptance-contract.md legitimately retain the phrase as
# historical schema-1.6 documentation and are deliberately NOT asserted against here.
for surface in \
  adapters/claude-code/skills/agentfw/SKILL.md \
  adapters/codex/skills/agentfw/SKILL.md \
  adapters/claude-code/CLAUDE-block.md \
  adapters/codex/AGENTS.md \
  adapters/claude-code/agents/agentfw-verifier.md \
  adapters/claude-code/agents/agentfw-plan-critic.md
do
  require_not_contains "$surface" 'planner-authored witness tree'
done

printf 'release-v9.7.sh: PASS: no adapter surface retains the demoted witness-tree duty\n'

# --- existing deterministic suites ---
( cd "$ROOT" && bash tools/tests/validate-plan.sh )
printf 'release-v9.7.sh: PASS: validator fixture harness\n'
( cd "$ROOT" && bash tools/tests/install-roundtrip.sh )
printf 'release-v9.7.sh: PASS: installer roundtrip\n'
( cd "$ROOT" && bash tools/tests/check-links.sh )
printf 'release-v9.7.sh: PASS: relative links\n'

# --- capability validation, both parser paths ---
python3 -c 'import yaml' \
  || fail "PyYAML is unavailable; cannot exercise both capability parser paths"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.7.sh: PASS: capability validation (both parser paths)\n'

# --- cross-adapter skill sync ---
python3 "$ROOT/tools/check-skill-sync.py"
printf 'release-v9.7.sh: PASS: cross-adapter skill sync (byte-identical AGENTFW-SYNC block)\n'

# --- schema-1.6 back-compatibility: the shipped v9.6 build plan still validates under 1.7 tooling ---
python3 "$ROOT/tools/validate-plan" "$ROOT/PLAN-v9.6-operator-compass.md" >/dev/null \
  || fail "the v9.6 build plan no longer validates — schema-1.6 back-compatibility regressed"
printf 'release-v9.7.sh: PASS: schema-1.6 back-compatibility (PLAN-v9.6-operator-compass.md)\n'

# --- re-approach fork invariants: exact selftest signal, then the shipped fixture validates ---
[ "$(python3 "$ROOT/tools/check-reapproach-invariants.py" --selftest)" = "REAPPROACH_SELFTEST_OK" ] \
  || fail "re-approach selftest did not emit its exact signal"
python3 "$ROOT/tools/check-reapproach-invariants.py" "$ROOT/evaluation/fixtures/reapproach-fork.json"
printf 'release-v9.7.sh: PASS: re-approach fork invariants (selftest + shipped fixture)\n'

# --- ledger completeness: Falsifier required for the D-28..D-36 tier, absent for the pre-D-28 tier ---
# Both directions are asserted so a future change that makes Falsifier unconditionally required
# again (breaking pre-D-28 entries) is caught here, not discovered downstream.
( cd "$ROOT" && python3 tools/check-candidates.py --require-falsifier \
    D-28 D-29 D-30 D-31 D-32 D-33 D-34 D-35 D-36 )
( cd "$ROOT" && python3 tools/check-candidates.py \
    D-2 D-14 D-15 D-16 D-17 D-18 D-19 D-20 D-21 D-22 )
printf 'release-v9.7.sh: PASS: ledger completeness, both Falsifier-required and bare forms\n'

# --- release documents exist and carry the v9.7.0 heading ---
# Pinned to a line-start heading (not a bare substring grep) so a reference to "v9.7.0" inside
# prose, a link target, or a different heading level cannot satisfy this check.
grep -Eq '^## v9\.7\.0' "$ROOT/CHANGELOG.md" \
  || fail "CHANGELOG.md is missing a '## v9.7.0' section heading"
python3 - "$ROOT/RELEASE-NOTES-v9.7.0.md" <<'PY' \
  || fail "RELEASE-NOTES-v9.7.0.md must exist and be non-empty"
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    text = fh.read()
assert text.strip(), "RELEASE-NOTES-v9.7.0.md is empty"
PY
printf 'release-v9.7.sh: PASS: release documents (CHANGELOG.md v9.7.0 heading, non-empty release notes)\n'

# --- front-door documents: README.md and DESIGN.md updated to v9.7.0 ---
# Whole distinctive lines pinned, not bare "9.7.0" substrings — that token recurs throughout both
# documents, so a bare grep would be satisfied by any incidental mention.
require_contains README.md '**Status: v9.7.0, released 2026-08-04**'
require_contains README.md "## What's new in v9.7"
require_contains README.md 'tools/tests/release-v9.7.sh'
require_contains DESIGN.md '**Current-release note (v9.7.0):**'
require_contains DESIGN.md '| v9.7.0 | 2026-08-04 |'
printf 'release-v9.7.sh: PASS: front-door documents (README.md + DESIGN.md report v9.7.0)\n'

printf 'RELEASE_V9_7_OK\n'
