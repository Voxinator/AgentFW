#!/usr/bin/env bash
# Deterministic release gate for the AgentFW v9.6 line (currently v9.6.0).
#
# AGENTFW_RELEASE_ROOT may point at a scratch copy for red-path probes.
# AGENTFW_RELEASE_IDENTITY_ONLY=1 stops after the release-document checks; the normal
# contracted acceptance command sets neither variable and runs every deterministic suite below.
set -euo pipefail

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ROOT=${AGENTFW_RELEASE_ROOT:-$SCRIPT_ROOT}

fail() {
  printf 'release-v9.6.sh: FAIL: %s\n' "$*" >&2
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
    fail "$1 contains stale text that v9.6 must have removed: $2"
  fi
}

for required in \
  metadata.json README.md CHANGELOG.md DESIGN.md \
  RELEASE-NOTES-v9.6.0.md RELEASE-NOTES-v9.5.0.md RELEASE-NOTES-v9.4.0.md \
  CANDIDATES.md PLAN-v9.6-operator-compass.md PLAN-v9.6-operator-compass.ledger.json \
  policy/plan-critique.md policy/acceptance-contract.md policy/recovery.md \
  policy/capability-contract.md policy/model-dispatch.md policy/assurance-model.md \
  tools/validate-plan tools/validate-capability tools/check-skill-sync.py \
  tools/check-posture-invariants.py tools/check-liveness-invariants.py \
  tools/check-delivery-invariants.py tools/check-reconcile-invariants.py \
  tools/check-candidates.py \
  evaluation/fixtures/sleep-posture.json evaluation/fixtures/liveness-budget.json \
  evaluation/fixtures/delivery-ledger.json evaluation/fixtures/reconcile.json \
  evaluation/field-report-2026-08-01-drydock-zero-delivery.md \
  tools/fixtures/plan-good-16-witness.md \
  profiles/chatgpt-projects.md \
  adapters/claude-code/INSTALL.md adapters/codex/INSTALL.md \
  adapters/claude-code/capability.yaml adapters/codex/capability.yaml \
  adapters/claude-code/agents/agentfw-plan-critic.md \
  adapters/claude-code/agents/agentfw-verifier.md
do
  require_file "$required"
done

python3 - "$ROOT/metadata.json" <<'PY' \
  || fail "metadata.json must report version 9.6.0 and revision r9.6"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
assert data.get("version") == "9.6.0", data.get("version")
assert data.get("revision") == "r9.6", data.get("revision")
PY

# --- release identity, current-facing docs ---
require_contains adapters/claude-code/CLAUDE-block.md 'Installed release: **AgentFW v9.6.0**'
require_contains adapters/codex/AGENTS.md 'Installed release: **AgentFW v9.6.0**'
require_contains README.md '**Status: v9.6.0, released 2026-08-01**'
require_contains README.md "## What's new in v9.6"
require_contains README.md 'tools/tests/release-v9.6.sh'
require_contains README.md '[the v9.6.0 release notes](RELEASE-NOTES-v9.6.0.md)'
require_contains profiles/chatgpt-projects.md 'Current release: **AgentFW v9.6.0**'
require_contains adapters/claude-code/INSTALL.md 'Current release: **AgentFW v9.6.0**'
require_contains adapters/codex/INSTALL.md 'Current release: **AgentFW v9.6.0**'
require_contains DESIGN.md '**Current-release note (v9.6.0):**'
require_contains DESIGN.md '| v9.6.0 | 2026-08-01 |'
require_contains CHANGELOG.md '## v9.6.0 (2026-08-01)'
require_contains CHANGELOG.md 'zero-dispatch tripwire'
require_contains RELEASE-NOTES-v9.6.0.md 'behavioral-evaluation round was run for v9.6.0'
require_contains RELEASE-NOTES-v9.6.0.md 'The gate caught and closed its own weak'
require_not_contains README.md '**Status: v9.5.0, released 2026-07-31**'
require_not_contains CHANGELOG.md '## v9.6.0 — UNRELEASED'

# --- operator-compass policy text on every surface ---
require_contains policy/plan-critique.md 'Delivery ledger, scoreboard & zero-dispatch tripwire (D-21)'
require_contains policy/plan-critique.md '[SCOREBOARD:'
require_contains policy/plan-critique.md 'root_objective'
require_contains policy/plan-critique.md 'reconcile first (D-25)'
require_contains policy/recovery.md 'Session-start reconciliation'
require_contains policy/recovery.md '[RECONCILE:'
require_contains policy/recovery.md 'check-reconcile-invariants.py'
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'SCOREBOARD'
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'RECONCILE'
require_contains adapters/codex/skills/agentfw/SKILL.md 'SCOREBOARD'
require_contains adapters/codex/skills/agentfw/SKILL.md 'RECONCILE'
require_contains adapters/claude-code/CLAUDE-block.md 'SCOREBOARD'
require_contains adapters/codex/AGENTS.md 'SCOREBOARD'

# --- retained v9.4/v9.5 surfaces (regression guard) ---
require_contains policy/plan-critique.md '**schema 1.6 is the schema of record**'
require_contains policy/acceptance-contract.md '**Whole-command-only evidence.**'
require_contains policy/capability-contract.md 'Operator relaxation is a lever, not missing substrate'
require_contains policy/plan-critique.md 'Global liveness budget — per objective (D-2)'
require_contains policy/plan-critique.md '## Operator digest'

printf 'release-v9.6.sh: PASS: release identity, current docs, operator-compass policy surfacing\n'

if [ "${AGENTFW_RELEASE_IDENTITY_ONLY:-0}" = 1 ]; then
  printf 'RELEASE_V9_6_IDENTITY_OK\n'
  exit 0
fi

# --- existing deterministic suites ---
( cd "$ROOT" && bash tools/tests/validate-plan.sh )
printf 'release-v9.6.sh: PASS: validator fixture harness\n'
( cd "$ROOT" && bash tools/tests/install-roundtrip.sh )
printf 'release-v9.6.sh: PASS: installer roundtrip\n'
( cd "$ROOT" && bash tools/tests/check-links.sh )
printf 'release-v9.6.sh: PASS: relative links\n'

# --- capability validation, both parser paths ---
python3 -c 'import yaml' \
  || fail "PyYAML is unavailable; cannot exercise both capability parser paths"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.6.sh: PASS: capability validation (both parser paths)\n'

# --- machine-checked invariants: sync, posture, liveness, delivery, reconcile ---
python3 "$ROOT/tools/check-skill-sync.py"
python3 "$ROOT/tools/check-posture-invariants.py" --selftest
python3 "$ROOT/tools/check-posture-invariants.py" "$ROOT/evaluation/fixtures/sleep-posture.json"
[ "$(python3 "$ROOT/tools/check-liveness-invariants.py" --selftest)" = "LIVENESS_SELFTEST_OK" ] \
  || fail "liveness selftest did not emit its exact signal"
python3 "$ROOT/tools/check-liveness-invariants.py" "$ROOT/evaluation/fixtures/liveness-budget.json"
grep -Fq 'sub_objective_inherits_root_counters' "$ROOT/evaluation/fixtures/liveness-budget.json" \
  || fail "liveness fixture lacks the D-22 inheritance case"
[ "$(python3 "$ROOT/tools/check-delivery-invariants.py" --selftest)" = "DELIVERY_SELFTEST_OK" ] \
  || fail "delivery selftest did not emit its exact signal"
python3 "$ROOT/tools/check-delivery-invariants.py" "$ROOT/evaluation/fixtures/delivery-ledger.json"
[ "$(python3 "$ROOT/tools/check-reconcile-invariants.py" --selftest)" = "RECONCILE_SELFTEST_OK" ] \
  || fail "reconcile selftest did not emit its exact signal"
python3 "$ROOT/tools/check-reconcile-invariants.py" "$ROOT/evaluation/fixtures/reconcile.json"
printf 'release-v9.6.sh: PASS: sync / posture / liveness / delivery / reconcile invariants\n'

# --- the build plan itself stays Layer-1 clean and its ledger validates against D-21 shape ---
python3 "$ROOT/tools/validate-plan" "$ROOT/PLAN-v9.6-operator-compass.md" >/dev/null \
  || fail "the v9.6 build plan no longer passes Layer 1"
python3 - "$ROOT" <<'PY' || fail "the v9.6 build ledger violates the D-21 ledger shape"
import json
import sys
root = sys.argv[1]
led = json.load(open(root + "/PLAN-v9.6-operator-compass.ledger.json", encoding="utf-8"))
for key in ("objective", "root_objective", "cycles", "layer2_passes",
            "workers_dispatched", "tasks_verified", "gate_events"):
    assert key in led, key
assert led["gate_events"] and all(e.get("runtime") for e in led["gate_events"])
PY
printf 'release-v9.6.sh: PASS: build plan Layer-1 + dogfood ledger shape\n'

# --- ledger completeness ---
( cd "$ROOT" && python3 tools/check-candidates.py D-2 D-14 D-15 D-16 D-17 D-18 D-19 D-20 \
    D-21 D-22 D-23 D-24 D-25 D-26 D-27 )
printf 'release-v9.6.sh: PASS: ledger completeness (D-2, D-14..D-27)\n'

# --- root release-document relative links ---
python3 - "$ROOT" <<'PY' \
  || fail "a root release-document link is unresolved"
import pathlib
import re
import sys
root = pathlib.Path(sys.argv[1])
for relative in ("README.md", "CHANGELOG.md", "RELEASE-NOTES-v9.6.0.md"):
    source = root / relative
    text = source.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        candidate = source.parent / target
        if not candidate.exists():
            print("unresolved link in %s: %s" % (relative, target))
            sys.exit(1)
PY
printf 'release-v9.6.sh: PASS: root release-document links\n'

printf 'RELEASE_V9_6_OK\n'
