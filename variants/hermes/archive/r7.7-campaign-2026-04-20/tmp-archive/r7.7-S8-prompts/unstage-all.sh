#!/usr/bin/env bash
# Unstage all 6 variants in reverse order: J-A2, J-A1, I, H, G, F.
# Report per-variant status and final canonical verification.
set -uo pipefail
source /tmp/r7.7-env.sh

ORDER=("J-A2" "J-A1" "I" "H" "G" "F")
RESULT=()
for v in "${ORDER[@]}"; do
  echo "=== Unstaging variant$v ==="
  /Users/briantaylor/Projects/AgentFW/probe-variant${v}-stage.sh unstage 2>&1 | tail -5
  echo ""
done

echo "=== Final status after unstage ==="
for v in "${ORDER[@]}"; do
  STATE=$(/Users/briantaylor/Projects/AgentFW/probe-variant${v}-stage.sh status 2>&1 | grep -E "STATE|RESULT" | tail -1)
  echo "variant$v: $STATE"
done

echo ""
echo "=== Tripwire / preflight verification ==="
/Users/briantaylor/Projects/AgentFW/probe-preflight.sh 2>&1 | tail -10

echo ""
echo "=== Residue check (.probe-*-orig files) ==="
ssh ubuntu-vm "find ~/.hermes/hermes-agent ~/.hermes/skills -name '*.probe-*-orig' 2>/dev/null | head -20; echo 'end-residue'"
