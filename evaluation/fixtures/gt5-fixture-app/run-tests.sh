#!/usr/bin/env bash
# Run the test suite. Works from any working directory; offline; stdlib only.
set -u
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -m unittest discover -s tests -t . -v
