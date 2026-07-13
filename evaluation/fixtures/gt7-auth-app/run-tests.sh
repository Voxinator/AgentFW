#!/usr/bin/env bash
# Run the test suite. Works from any directory; no dependencies beyond Node.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec node --test "tests/**/*.test.js"
