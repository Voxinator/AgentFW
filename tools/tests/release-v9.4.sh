#!/usr/bin/env bash
# Deterministic release gate for the AgentFW v9.4 line (currently v9.4.0).
#
# AGENTFW_RELEASE_ROOT may point at a scratch copy for red-path probes (SKILL desync, stale
# metadata, laundered decision-table fixtures). AGENTFW_RELEASE_IDENTITY_ONLY=1 stops after the
# release-document checks; the normal contracted acceptance command sets neither variable and runs
# every deterministic suite below.
set -euo pipefail

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ROOT=${AGENTFW_RELEASE_ROOT:-$SCRIPT_ROOT}

fail() {
  printf 'release-v9.4.sh: FAIL: %s\n' "$*" >&2
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
    fail "$1 contains stale text that v9.4 must have removed: $2"
  fi
}

for required in \
  metadata.json README.md CHANGELOG.md DESIGN.md \
  RELEASE-NOTES-v9.4.0.md RELEASE-NOTES-v9.3.0.md RELEASE-NOTES-v9.2.0.md \
  CANDIDATES.md \
  policy/plan-critique.md policy/capability-contract.md \
  policy/model-dispatch.md policy/assurance-model.md \
  tools/validate-plan tools/validate-capability tools/check-skill-sync.py \
  tools/check-posture-invariants.py tools/check-liveness-invariants.py \
  tools/check-candidates.py \
  evaluation/fixtures/sleep-posture.json evaluation/fixtures/liveness-budget.json \
  evaluation/field-report-2026-07-31-drydock-scope-accretion.md \
  tools/fixtures/plan-good-15-necessity.md \
  tools/fixtures/plan-bad-15-missing-necessity.md \
  tools/fixtures/plan-bad-15-must-no-because.md \
  tools/fixtures/plan-bad-15-task-serves-fluff.md \
  tools/fixtures/plan-bad-14-carrying-15-field.md \
  profiles/chatgpt-projects.md \
  adapters/claude-code/INSTALL.md adapters/codex/INSTALL.md \
  adapters/claude-code/capability.yaml adapters/codex/capability.yaml \
  adapters/claude-code/agents/agentfw-plan-critic.md
do
  require_file "$required"
done

python3 - "$ROOT/metadata.json" <<'PY' \
  || fail "metadata.json must report version 9.4.0 and revision r9.4"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
assert data.get("version") == "9.4.0", data.get("version")
assert data.get("revision") == "r9.4", data.get("revision")
PY

# --- release identity, current-facing docs ---
# The kernels must self-identify the installed release — a model asked "what version
# are you running" answers from this line, so shipping without bumping it recreates
# the v9.3-misreport field bug (2026-07-31).
require_contains adapters/claude-code/CLAUDE-block.md 'Installed release: **AgentFW v9.4.0**'
require_contains adapters/codex/AGENTS.md 'Installed release: **AgentFW v9.4.0**'
require_contains README.md '**Status: v9.4.0, released 2026-07-31**'
require_contains README.md "## What's new in v9.4"
require_contains README.md 'tools/tests/release-v9.4.sh'
require_contains README.md '[the v9.4.0 release notes](RELEASE-NOTES-v9.4.0.md)'
require_contains profiles/chatgpt-projects.md 'Current release: **AgentFW v9.4.0**'
require_contains adapters/claude-code/INSTALL.md 'Current release: **AgentFW v9.4.0**'
require_contains adapters/codex/INSTALL.md 'Current release: **AgentFW v9.4.0**'
require_contains DESIGN.md '**Current-release note (v9.4.0):**'
require_contains DESIGN.md '| v9.4.0 | 2026-07-31 |'
require_contains CHANGELOG.md '## v9.4.0 (2026-07-31) — RELEASED'
require_contains CHANGELOG.md 'D-16 — operator-relaxed enforcement'
require_contains CHANGELOG.md 'D-2 — global liveness budget'
require_contains CHANGELOG.md 'D-19 — necessity tiers + C6 demote-duty'
require_contains CHANGELOG.md 'D-20 — operator digest'
require_contains RELEASE-NOTES-v9.4.0.md 'no behavioral-evaluation round was run for v9.4.0'
require_contains RELEASE-NOTES-v9.4.0.md 'lever, not a blocker'
require_contains RELEASE-NOTES-v9.4.0.md 'demoted to nice-to-have, not'

# --- D-16 operator relaxation: core rule + both adapters + both kernels ---
require_contains policy/capability-contract.md 'Operator relaxation is a lever, not missing substrate'
require_contains policy/capability-contract.md 'FLOOR-RELAXED'
require_contains adapters/claude-code/capability.yaml 'OPERATOR-RELAXED'
require_contains adapters/codex/capability.yaml 'OPERATOR-RELAXED'
require_contains adapters/claude-code/CLAUDE-block.md 'FLOOR-RELAXED'
require_contains adapters/codex/AGENTS.md 'FLOOR-RELAXED'
require_not_contains adapters/codex/capability.yaml 'sandbox_mode present and not "danger-full-access"'

# --- D-2 / D-18 liveness budget + scope freeze ---
require_contains policy/plan-critique.md 'Global liveness budget — per objective (D-2)'
require_contains policy/plan-critique.md 'LIVENESS-EXCEEDED'
require_contains policy/plan-critique.md 'Scope freeze after Layer 1'
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'Global liveness budget (D-2)'
require_contains adapters/codex/skills/agentfw/SKILL.md 'Global liveness budget (D-2)'

# --- D-19 schema 1.5 + C6 ---
require_contains policy/plan-critique.md '**schema 1.5 is the schema of record**'
require_contains policy/plan-critique.md 'Schema 1.5 necessity tiers (additive over 1.4):'
require_contains policy/plan-critique.md 'C6 necessity audit'
require_contains adapters/claude-code/agents/agentfw-plan-critic.md 'C6 Necessity audit'
require_contains adapters/claude-code/CLAUDE-block.md 'plan critique (C0–C6)'
require_contains adapters/codex/AGENTS.md 'plan critique (C0–C6)'
require_not_contains policy/plan-critique.md '**schema 1.4 is the schema of record**'

# --- D-20 operator digest ---
require_contains policy/plan-critique.md '## Operator digest'
require_contains policy/plan-critique.md 'speak-twice rule'
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'Operator digest & speak-twice (D-20)'
require_contains adapters/codex/skills/agentfw/SKILL.md 'Operator digest & speak-twice (D-20)'

printf 'release-v9.4.sh: PASS: release identity, current docs, D-16/D-2/D-18/D-19/D-20 policy + surfacing\n'

if [ "${AGENTFW_RELEASE_IDENTITY_ONLY:-0}" = 1 ]; then
  printf 'RELEASE_V9_4_IDENTITY_OK\n'
  exit 0
fi

# --- existing deterministic suites ---
( cd "$ROOT" && bash tools/tests/validate-plan.sh )
printf 'release-v9.4.sh: PASS: validator fixture harness (incl. schema 1.5)\n'
( cd "$ROOT" && bash tools/tests/install-roundtrip.sh )
printf 'release-v9.4.sh: PASS: installer roundtrip\n'
( cd "$ROOT" && bash tools/tests/check-links.sh )
printf 'release-v9.4.sh: PASS: relative links\n'

# --- the D-20 digest count oracle on the shipped 1.5 fixture ---
digest_output=$(python3 "$ROOT/tools/validate-plan" --digest \
  "$ROOT/tools/fixtures/plan-good-15-necessity.md") \
  || fail "--digest rejected the shipped 1.5 fixture"
printf '%s\n' "$digest_output" | grep -Fq \
  "digest: must=2 nice-to-have=2 (deferred 1) fluff=1 tasks=2" \
  || fail "--digest counts did not match the shipped 1.5 fixture"
printf 'release-v9.4.sh: PASS: digest count oracle\n'

# --- capability validation: 11 keys, via BOTH parser paths ---
python3 -c 'import yaml' \
  || fail "PyYAML is unavailable; cannot exercise both capability parser paths"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.4.sh: PASS: capability validation (11 keys, both parser paths)\n'

# --- machine-checked invariants (sleep floor-halt; liveness budget) ---
python3 "$ROOT/tools/check-skill-sync.py"
printf 'release-v9.4.sh: PASS: adapter SKILL sync\n'
python3 "$ROOT/tools/check-posture-invariants.py" --selftest
python3 "$ROOT/tools/check-posture-invariants.py" "$ROOT/evaluation/fixtures/sleep-posture.json"
printf 'release-v9.4.sh: PASS: sleep-posture floor-halt invariant\n'
python3 "$ROOT/tools/check-liveness-invariants.py" --selftest
python3 "$ROOT/tools/check-liveness-invariants.py" "$ROOT/evaluation/fixtures/liveness-budget.json"
printf 'release-v9.4.sh: PASS: liveness-budget invariant\n'
( cd "$ROOT" && python3 tools/check-candidates.py D-2 D-14 D-15 D-16 D-17 D-18 D-19 D-20 )
printf 'release-v9.4.sh: PASS: ledger completeness (D-2, D-14..D-20)\n'

# --- root release-document relative links (outside check-links.sh's normal scan) ---
python3 - "$ROOT" <<'PY' \
  || fail "a root release-document link is unresolved"
import pathlib
import re
import sys
root = pathlib.Path(sys.argv[1])
for relative in ("README.md", "CHANGELOG.md", "RELEASE-NOTES-v9.4.0.md"):
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
printf 'release-v9.4.sh: PASS: root release-document links\n'

printf 'RELEASE_V9_4_OK\n'
