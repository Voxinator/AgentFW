#!/usr/bin/env bash
# Run the offline test suite. Works from any cwd.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m unittest discover -s tests -t . -v
