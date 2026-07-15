#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
VALIDATOR="$ROOT/tools/validate-plan"
FIXTURES="$ROOT/tools/fixtures"
PLAN_POLICY="$ROOT/policy/plan-critique.md"
ACCEPTANCE_POLICY="$ROOT/policy/acceptance-contract.md"

fail() {
  printf 'validate-plan.sh: FAIL: %s\n' "$*" >&2
  exit 1
}

expect_pass() {
  local path=$1
  local needle=${2:-PASS:}
  local output
  output=$(python3 "$VALIDATOR" "$path" 2>&1) \
    || fail "expected PASS for $path; got: $output"
  [[ $output == *"$needle"* ]] \
    || fail "PASS output for $path did not contain: $needle"
}

expect_fail() {
  local path=$1
  local needle=${2:-FAIL:}
  local output
  if output=$(python3 "$VALIDATOR" "$path" 2>&1); then
    fail "expected rejection for $path; got: $output"
  fi
  [[ $output == *"$needle"* ]] \
    || fail "rejection for $path did not contain '$needle'; got: $output"
}

expect_policy_text() {
  local path=$1
  local needle=$2
  grep -Fq -- "$needle" "$path" \
    || fail "$path is missing required policy text: $needle"
}

# Compatibility positives: representative 1.1 and 1.2 plans remain valid.
expect_pass "$FIXTURES/plan-good.md" "review floor (advisory, 1.1):"
expect_pass "$FIXTURES/plan-good-single-review.md" "review tier: single"
expect_pass "$FIXTURES/plan-good-dual-review.md" "review tier: dual"

# Schema 1.3 positive, including both shipped adapter examples.
expect_pass "$FIXTURES/plan-good-13-mutation.md" "known-command-shape lint"
expect_pass "$ROOT/adapters/claude-code/skills/agentfw/SKILL.md" "review tier: dual"
expect_pass "$ROOT/adapters/codex/skills/agentfw/SKILL.md" "review tier: dual"

# Every hostile plan fixture must be rejected under default validation.
for fixture in "$FIXTURES"/plan-bad-*.md; do
  expect_fail "$fixture"
done

# Legacy provenance remains available only through the explicit flag.
legacy_output=$(python3 "$VALIDATOR" --legacy \
  "$FIXTURES/plan-bad-legacy-version.md" 2>&1) \
  || fail "--legacy rejected the historical v1 fixture: $legacy_output"
[[ $legacy_output == *"PASS:"* ]] \
  || fail "--legacy output did not report PASS"

# New mutation-contract rules, each tied to its hostile fixture.
expect_fail "$FIXTURES/plan-bad-13-seam-missing-mutations.md" \
  "requires non-empty 'mutation_probes'"
expect_fail "$FIXTURES/plan-bad-13-empty-mutations.md" \
  "empty mutation contract"
expect_fail "$FIXTURES/plan-bad-13-a3-missing-mutations.md" \
  "every A3/A4 contract"
expect_fail "$FIXTURES/plan-bad-13-mutation-not-array.md" \
  "must be a JSON array"
expect_fail "$FIXTURES/plan-bad-13-mutation-shapes.md" \
  "mutation probe #0 must be an object"
expect_fail "$FIXTURES/plan-bad-13-mutation-shapes.md" \
  "field 'mutation' must be a non-empty string"
expect_fail "$FIXTURES/plan-bad-13-mutation-shapes.md" \
  "field 'expected' must equal \"red\""
expect_fail "$FIXTURES/plan-bad-13-mutation-shapes.md" \
  "exactly the keys 'mutation' and 'expected'"
expect_fail "$FIXTURES/plan-bad-12-carrying-13-field.md" \
  "schema-1.3 field"

# New known-weak command shapes.
expect_fail "$FIXTURES/plan-bad-13-pipe-before-gate.md" \
  "pipe operator appears before a gating &&"
expect_fail "$FIXTURES/plan-bad-13-unguarded-signal.md" \
  "not exit-code gated"
expect_fail "$FIXTURES/plan-bad-13-nonterminal-signal.md" \
  "is not terminal"

# Both policy surfaces stay synchronized with schema 1.3 and validator behavior.
expect_policy_text "$ACCEPTANCE_POLICY" 'Schema `"1.3"` is ADDITIVE over 1.2'
expect_policy_text "$ACCEPTANCE_POLICY" 'Producer red-path self-probe'
expect_policy_text "$ACCEPTANCE_POLICY" 'executes every probe independently'
expect_policy_text "$ACCEPTANCE_POLICY" 'success signal is emitted'

# Regression guards for policy/plan-critique.md: reverting the schema of
# record, dropping mutation contracts, or dropping any known weak command
# shape must make this harness fail even when all fixtures still pass.
expect_policy_text "$PLAN_POLICY" 'mode — `"1.1"`, `"1.2"`, or `"1.3"`'
expect_policy_text "$PLAN_POLICY" '**schema 1.3 is the schema of record**'
expect_policy_text "$PLAN_POLICY" \
  '**Schema 1.3 mutation probes + known command-shape lint (additive over 1.2):**'
expect_policy_text "$PLAN_POLICY" \
  'A non-empty `mutation_probes` array is REQUIRED for'
expect_policy_text "$PLAN_POLICY" \
  'every `integration_seam: true` contract and every contract at assurance A3/A4'
expect_policy_text "$PLAN_POLICY" \
  'objects containing exactly `mutation` (a non-empty string) and'
expect_policy_text "$PLAN_POLICY" \
  '`expected` (the literal string `"red"`)'
expect_policy_text "$PLAN_POLICY" \
  'A `"1.1"` or `"1.2"` block'
expect_policy_text "$PLAN_POLICY" \
  'carrying `mutation_probes` is rejected with a diagnostic naming schema 1.3'
expect_policy_text "$PLAN_POLICY" 'a pipe operator before a gating `&&`'
expect_policy_text "$PLAN_POLICY" \
  'an expected-signal `echo` that is not immediately preceded by `&&`'
expect_policy_text "$PLAN_POLICY" \
  'an expected-signal `echo` followed by another'
expect_policy_text "$PLAN_POLICY" '**Schema 1.3 red-path execution duty:**'
expect_policy_text "$PLAN_POLICY" \
  'contract producer MUST execute every proposed `acceptance_command`'
expect_policy_text "$PLAN_POLICY" \
  'verifier at the contract'
expect_policy_text "$PLAN_POLICY" \
  'independently executes every probe on fresh scratch copies'
expect_policy_text "$PLAN_POLICY" \
  '`failure_surface`, `mutation`, `command`, `version`'
expect_policy_text "$PLAN_POLICY" \
  '`mutation` covers every schema-1.3 `mutation_probes` presence and shape defect'
expect_policy_text "$PLAN_POLICY" \
  '`command` covers the three schema-1.3 weak acceptance-command shapes'

printf 'validate-plan.sh: ALL CHECKS PASSED\n'
