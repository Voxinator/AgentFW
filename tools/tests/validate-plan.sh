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
expect_policy_text "$PLAN_POLICY" 'mode — `"1.1"`, `"1.2"`, `"1.3"`, `"1.4"`, `"1.5"`, or `"1.6"`'
expect_policy_text "$PLAN_POLICY" '**schema 1.6 is the schema of record**'
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

# Schema 1.4 overrides ledger: additive positives and hostile shapes.
expect_pass "$FIXTURES/plan-good-14-overrides.md" "known-command-shape lint"
expect_pass "$FIXTURES/plan-good-14-no-overrides.md" "known-command-shape lint"
expect_fail "$FIXTURES/plan-bad-14-override-shape.md" override
expect_fail "$FIXTURES/plan-bad-14-override-nonarray.md" override
expect_fail "$FIXTURES/plan-bad-13-carrying-14-field.md" version
expect_policy_text "$PLAN_POLICY" '**Schema 1.4 overrides ledger (additive over 1.3):**'

# Schema 1.5 necessity tiers (D-19): positives, scope note, digest counts,
# and hostile shapes.
expect_pass "$FIXTURES/plan-good-15-necessity.md" "known-command-shape lint"
expect_pass "$FIXTURES/plan-good-15-necessity.md" \
  "scope note: task T2 serves only nice-to-have requirements"
expect_fail "$FIXTURES/plan-bad-15-missing-necessity.md" "missing necessity"
expect_fail "$FIXTURES/plan-bad-15-must-no-because.md" \
  "necessity justification missing"
expect_fail "$FIXTURES/plan-bad-15-task-serves-fluff.md" \
  "requirement inflation"
expect_fail "$FIXTURES/plan-bad-14-carrying-15-field.md" "schema-1.5"
digest_output=$(python3 "$VALIDATOR" --digest \
  "$FIXTURES/plan-good-15-necessity.md" 2>&1) \
  || fail "--digest rejected the good 1.5 fixture: $digest_output"
[[ $digest_output == *"digest: must=2 nice-to-have=2 (deferred 1) fluff=1 tasks=2"* ]] \
  || fail "--digest counts did not match the 1.5 fixture; got: $digest_output"
expect_policy_text "$PLAN_POLICY" \
  '**Schema 1.5 necessity tiers (additive over 1.4):**'
expect_policy_text "$PLAN_POLICY" 'C6 necessity audit'
expect_policy_text "$PLAN_POLICY" '## Operator digest'

# Schema 1.6 witness pair: positives, whole-command digest matching, the
# round-3 impossible-command regression, and hostile shapes.
CRITIC="$ROOT/adapters/claude-code/agents/agentfw-plan-critic.md"
VERIFIER_PROMPT="$ROOT/adapters/claude-code/agents/agentfw-verifier.md"
expect_pass "$FIXTURES/plan-good-16-witness.md" "witness pair"
digest16_output=$(python3 "$VALIDATOR" --digest \
  "$FIXTURES/plan-good-16-witness.md" 2>&1) \
  || fail "--digest rejected the good 1.6 fixture: $digest16_output"
[[ $digest16_output == *"digest: must=2 nice-to-have=2 (deferred 1) fluff=1 tasks=2"* ]] \
  || fail "--digest counts did not match the 1.6 fixture; got: $digest16_output"
expect_fail "$FIXTURES/plan-bad-16-missing-witness.md" "missing witness pair"
expect_fail "$FIXTURES/plan-bad-16-round3-contradiction.md" \
  "never been shown able to pass"
expect_fail "$FIXTURES/plan-bad-16-round3-contradiction.md" \
  "rejected at plan time (witness exit code)"
expect_fail "$FIXTURES/plan-bad-16-digest-mismatch.md" \
  "witness digest mismatch"
expect_fail "$FIXTURES/plan-bad-16-witness-shape.md" \
  "exactly the keys 'red' and 'green'"
expect_fail "$FIXTURES/plan-bad-16-witness-shape.md" \
  "'exit_code' must be a JSON integer"
expect_fail "$FIXTURES/plan-bad-15-carrying-16-field.md" "schema-1.6 field"
expect_policy_text "$ACCEPTANCE_POLICY" \
  '### The witness pair (schema 1.6) — prove the command CAN pass, at plan time'
expect_policy_text "$ACCEPTANCE_POLICY" '**Whole-command-only evidence.**'
expect_policy_text "$ACCEPTANCE_POLICY" \
  'A witness tree that an EMPTY implementation would also satisfy is void'
expect_policy_text "$PLAN_POLICY" \
  '**Schema 1.6 witness pair (additive over 1.5):**'
expect_policy_text "$PLAN_POLICY" \
  '`witness` covers every schema-1.6 `witness_pair` defect'
expect_policy_text "$PLAN_POLICY" \
  '**Witness pair replaces the temporal split (1.6):**'
expect_policy_text "$PLAN_POLICY" 'it never weakens or replaces it'
# The C2 stub-tree rejection duty must live in the judge prompt, or judges
# will not act on it (the D-level fixture for the judge instruction).
expect_policy_text "$CRITIC" \
  'MUST reject a green witness whose tree still passes with'
expect_policy_text "$CRITIC" 'the deliverables stubbed to nothing'
expect_policy_text "$VERIFIER_PROMPT" '**Whole-command-only evidence (schema 1.6).**'

printf 'validate-plan.sh: ALL CHECKS PASSED\n'
