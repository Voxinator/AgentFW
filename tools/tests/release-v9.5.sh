#!/usr/bin/env bash
# Deterministic release gate for the AgentFW v9.5 line (currently v9.5.0).
#
# AGENTFW_RELEASE_ROOT may point at a scratch copy for red-path probes (stale metadata,
# reverted schema-of-record, missing witness fixtures). AGENTFW_RELEASE_IDENTITY_ONLY=1 stops
# after the release-document checks; the normal contracted acceptance command sets neither
# variable and runs every deterministic suite below.
set -euo pipefail

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ROOT=${AGENTFW_RELEASE_ROOT:-$SCRIPT_ROOT}

fail() {
  printf 'release-v9.5.sh: FAIL: %s\n' "$*" >&2
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
    fail "$1 contains stale text that v9.5 must have removed: $2"
  fi
}

for required in \
  metadata.json README.md CHANGELOG.md DESIGN.md \
  RELEASE-NOTES-v9.5.0.md RELEASE-NOTES-v9.4.0.md RELEASE-NOTES-v9.3.0.md \
  CANDIDATES.md \
  policy/plan-critique.md policy/acceptance-contract.md \
  policy/capability-contract.md policy/model-dispatch.md policy/assurance-model.md \
  tools/validate-plan tools/validate-capability tools/check-skill-sync.py \
  tools/check-posture-invariants.py tools/check-liveness-invariants.py \
  tools/check-candidates.py \
  evaluation/fixtures/sleep-posture.json evaluation/fixtures/liveness-budget.json \
  tools/fixtures/plan-good-16-witness.md \
  tools/fixtures/plan-bad-16-missing-witness.md \
  tools/fixtures/plan-bad-16-round3-contradiction.md \
  tools/fixtures/plan-bad-16-digest-mismatch.md \
  tools/fixtures/plan-bad-16-witness-shape.md \
  tools/fixtures/plan-bad-15-carrying-16-field.md \
  evaluation/evidence/witness-pair-upgrade-2026-07-31/byte-identical-NOTE.md \
  profiles/chatgpt-projects.md \
  adapters/claude-code/INSTALL.md adapters/codex/INSTALL.md \
  adapters/claude-code/capability.yaml adapters/codex/capability.yaml \
  adapters/claude-code/agents/agentfw-plan-critic.md \
  adapters/claude-code/agents/agentfw-verifier.md
do
  require_file "$required"
done

python3 - "$ROOT/metadata.json" <<'PY' \
  || fail "metadata.json must report version 9.5.0 and revision r9.5"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
assert data.get("version") == "9.5.0", data.get("version")
assert data.get("revision") == "r9.5", data.get("revision")
PY

# --- release identity, current-facing docs ---
# The kernels must self-identify the installed release — a model asked "what version
# are you running" answers from this line (v9.3-misreport field bug, 2026-07-31).
require_contains adapters/claude-code/CLAUDE-block.md 'Installed release: **AgentFW v9.5.0**'
require_contains adapters/codex/AGENTS.md 'Installed release: **AgentFW v9.5.0**'
require_contains README.md '**Status: v9.5.0, released 2026-07-31**'
require_contains README.md "## What's new in v9.5"
require_contains README.md 'tools/tests/release-v9.5.sh'
require_contains README.md '[the v9.5.0 release notes](RELEASE-NOTES-v9.5.0.md)'
require_contains profiles/chatgpt-projects.md 'Current release: **AgentFW v9.5.0**'
require_contains adapters/claude-code/INSTALL.md 'Current release: **AgentFW v9.5.0**'
require_contains adapters/codex/INSTALL.md 'Current release: **AgentFW v9.5.0**'
require_contains DESIGN.md '**Current-release note (v9.5.0):**'
require_contains DESIGN.md '| v9.5.0 | 2026-07-31 |'
require_contains CHANGELOG.md '## v9.5.0 (2026-07-31)'
require_contains CHANGELOG.md 'Witness pair'
require_contains CHANGELOG.md 'Whole-command-only evidence'
require_contains RELEASE-NOTES-v9.5.0.md 'no behavioral-evaluation round was run for v9.5.0'
require_contains RELEASE-NOTES-v9.5.0.md 'this command CAN pass'
require_contains RELEASE-NOTES-v9.5.0.md 'rejected at plan time'

# --- witness pair: schema of record + policy text on every surface ---
require_contains policy/plan-critique.md '**schema 1.6 is the schema of record**'
require_contains policy/plan-critique.md '**Schema 1.6 witness pair (additive over 1.5):**'
require_contains policy/plan-critique.md '**Witness pair replaces the temporal split (1.6):**'
require_contains policy/plan-critique.md '`witness` covers every schema-1.6 `witness_pair` defect'
require_contains policy/acceptance-contract.md '### The witness pair (schema 1.6) — prove the command CAN pass, at plan time'
require_contains policy/acceptance-contract.md '**Whole-command-only evidence.**'
require_contains policy/acceptance-contract.md 'A witness tree that an EMPTY implementation would also satisfy is void'
require_contains policy/acceptance-contract.md '`"1.6"` is the schema of record'
require_not_contains policy/plan-critique.md '**schema 1.5 is the schema of record**'
require_not_contains policy/acceptance-contract.md '`"1.4"` is the schema of record'

# --- red-path duty untouched (the pair extends, never weakens) ---
require_contains policy/plan-critique.md '**Schema 1.3 red-path execution duty:**'
require_contains policy/plan-critique.md 'contract producer MUST execute every proposed `acceptance_command`'
require_contains policy/plan-critique.md 'it never weakens or replaces it'

# --- judge prompts carry the C2/verifier witness duties ---
require_contains adapters/claude-code/agents/agentfw-plan-critic.md 'MUST reject a green witness whose tree still passes with'
require_contains adapters/claude-code/agents/agentfw-plan-critic.md 'the deliverables stubbed to nothing'
require_contains adapters/claude-code/agents/agentfw-verifier.md '**Whole-command-only evidence (schema 1.6).**'

# --- both adapter SKILLs surface schema 1.6 + the witness pair ---
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'Schema `"1.6"` is the schema of record'
require_contains adapters/claude-code/skills/agentfw/SKILL.md 'witness pair'
require_contains adapters/codex/skills/agentfw/SKILL.md 'Schema `"1.6"` is the schema of record'
require_contains adapters/codex/skills/agentfw/SKILL.md 'witness pair'

# --- retained v9.4 surfaces (regression guard) ---
require_contains policy/capability-contract.md 'Operator relaxation is a lever, not missing substrate'
require_contains policy/plan-critique.md 'Global liveness budget — per objective (D-2)'
require_contains policy/plan-critique.md '## Operator digest'
require_contains policy/plan-critique.md 'Schema 1.5 necessity tiers (additive over 1.4):'

printf 'release-v9.5.sh: PASS: release identity, current docs, witness-pair policy + surfacing\n'

if [ "${AGENTFW_RELEASE_IDENTITY_ONLY:-0}" = 1 ]; then
  printf 'RELEASE_V9_5_IDENTITY_OK\n'
  exit 0
fi

# --- existing deterministic suites ---
( cd "$ROOT" && bash tools/tests/validate-plan.sh )
printf 'release-v9.5.sh: PASS: validator fixture harness (incl. schema 1.6 witness fixtures)\n'
( cd "$ROOT" && bash tools/tests/install-roundtrip.sh )
printf 'release-v9.5.sh: PASS: installer roundtrip\n'
( cd "$ROOT" && bash tools/tests/check-links.sh )
printf 'release-v9.5.sh: PASS: relative links\n'

# --- digest count oracle on BOTH shipped necessity fixtures (1.5 and 1.6) ---
for fixture in tools/fixtures/plan-good-15-necessity.md \
               tools/fixtures/plan-good-16-witness.md; do
  digest_output=$(python3 "$ROOT/tools/validate-plan" --digest "$ROOT/$fixture") \
    || fail "--digest rejected the shipped fixture $fixture"
  printf '%s\n' "$digest_output" | grep -Fq \
    "digest: must=2 nice-to-have=2 (deferred 1) fluff=1 tasks=2" \
    || fail "--digest counts did not match the shipped fixture $fixture"
done
printf 'release-v9.5.sh: PASS: digest count oracle (1.5 + 1.6 fixtures)\n'

# --- the witness red paths go red with the stable keyword ---
for fixture in plan-bad-16-missing-witness plan-bad-16-round3-contradiction \
               plan-bad-16-digest-mismatch plan-bad-16-witness-shape; do
  if output=$(python3 "$ROOT/tools/validate-plan" \
      "$ROOT/tools/fixtures/$fixture.md" 2>&1); then
    fail "witness fixture $fixture unexpectedly passed: $output"
  fi
  printf '%s\n' "$output" | grep -Fq "witness" \
    || fail "witness fixture $fixture rejection lacks the stable keyword: $output"
done
printf 'release-v9.5.sh: PASS: witness red paths (missing/contradiction/forgery/shape)\n'

# --- capability validation: 11 keys, via BOTH parser paths ---
python3 -c 'import yaml' \
  || fail "PyYAML is unavailable; cannot exercise both capability parser paths"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/claude-code/capability.yaml"
python3 -S "$ROOT/tools/validate-capability" "$ROOT/adapters/codex/capability.yaml"
printf 'release-v9.5.sh: PASS: capability validation (11 keys, both parser paths)\n'

# --- machine-checked invariants (adapter sync; sleep floor-halt; liveness budget) ---
python3 "$ROOT/tools/check-skill-sync.py"
printf 'release-v9.5.sh: PASS: adapter SKILL sync\n'
python3 "$ROOT/tools/check-posture-invariants.py" --selftest
python3 "$ROOT/tools/check-posture-invariants.py" "$ROOT/evaluation/fixtures/sleep-posture.json"
printf 'release-v9.5.sh: PASS: sleep-posture floor-halt invariant\n'
python3 "$ROOT/tools/check-liveness-invariants.py" --selftest
python3 "$ROOT/tools/check-liveness-invariants.py" "$ROOT/evaluation/fixtures/liveness-budget.json"
printf 'release-v9.5.sh: PASS: liveness-budget invariant\n'
( cd "$ROOT" && python3 tools/check-candidates.py D-2 D-14 D-15 D-16 D-17 D-18 D-19 D-20 )
printf 'release-v9.5.sh: PASS: ledger completeness (D-2, D-14..D-20)\n'

# --- root release-document relative links (outside check-links.sh's normal scan) ---
python3 - "$ROOT" <<'PY' \
  || fail "a root release-document link is unresolved"
import pathlib
import re
import sys
root = pathlib.Path(sys.argv[1])
for relative in ("README.md", "CHANGELOG.md", "RELEASE-NOTES-v9.5.0.md"):
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
printf 'release-v9.5.sh: PASS: root release-document links\n'

printf 'RELEASE_V9_5_OK\n'
