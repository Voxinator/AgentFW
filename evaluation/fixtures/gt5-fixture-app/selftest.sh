#!/usr/bin/env bash
# End-to-end self-test of the fixture lifecycle, run entirely inside a
# throwaway mktemp copy of this project (the committed tree is never mutated):
#   1. tests are green on the pristine copy
#   2. deleting tests/fixtures/ makes the tests fail
#   3. tools/generate_fixtures.py restores the tests to green
#   4. two independent regenerations are byte-identical
# Log: selftest-last.log (next to this script). Exit 0 only if all steps pass.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$ROOT/selftest-last.log"
: > "$LOG"

log() { printf '%s\n' "$*" | tee -a "$LOG"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
APP="$TMP/app"
mkdir -p "$APP"
# Copy the project into the sandbox (skip the log so the copy is pristine).
(cd "$ROOT" && tar -cf - --exclude='selftest-last.log' .) | (cd "$APP" && tar -xf -)

fail() { log "SELFTEST: FAILED — $*"; exit 1; }

log "== selftest in mktemp copy: $APP =="

# Step 1: tests green on the pristine copy.
log "-- step 1: baseline test run --"
if bash "$APP/run-tests.sh" >>"$LOG" 2>&1; then
  log "BASELINE TESTS: GREEN"
else
  fail "baseline tests did not pass"
fi

# Step 2: delete the fixtures; tests must fail.
log "-- step 2: rm -rf tests/fixtures --"
rm -rf "$APP/tests/fixtures"
if bash "$APP/run-tests.sh" >>"$LOG" 2>&1; then
  fail "tests still pass with tests/fixtures deleted — fixtures are not load-bearing"
else
  log "DELETION BREAKS TESTS: CONFIRMED"
fi

# Step 3: regenerate from the schema; tests must be green again.
log "-- step 3: regenerate fixtures --"
python3 "$APP/tools/generate_fixtures.py" >>"$LOG" 2>&1 || fail "generator exited non-zero"
if bash "$APP/run-tests.sh" >>"$LOG" 2>&1; then
  log "REGENERATION RESTORES TESTS: CONFIRMED"
else
  fail "tests still failing after regeneration"
fi

# Step 4: regeneration is byte-deterministic.
log "-- step 4: determinism check --"
python3 "$APP/tools/generate_fixtures.py" "$TMP/gen-a" >>"$LOG" 2>&1 || fail "determinism run A exited non-zero"
python3 "$APP/tools/generate_fixtures.py" "$TMP/gen-b" >>"$LOG" 2>&1 || fail "determinism run B exited non-zero"
if diff -r "$TMP/gen-a" "$TMP/gen-b" >>"$LOG" 2>&1; then
  log "REGEN DETERMINISTIC: CONFIRMED"
else
  fail "two consecutive regenerations differ byte-wise"
fi
# The regenerated set must also byte-match what the sandbox tests just ran on.
if diff -r "$TMP/gen-a" "$APP/tests/fixtures" >>"$LOG" 2>&1; then
  log "REGEN MATCHES LIVE FIXTURES: CONFIRMED"
else
  fail "regenerated fixtures differ from the set the tests ran against"
fi

log "SELFTEST: ALL STEPS PASSED"
exit 0
