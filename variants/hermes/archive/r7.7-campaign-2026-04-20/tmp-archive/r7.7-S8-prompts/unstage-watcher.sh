#!/usr/bin/env bash
# Idle watcher: waits for run-all to complete (either by record count or process exit),
# then unstages all variants and appends end-of-run block to artifact.
# Safe to run in the background detached from Claude session.
set -uo pipefail

ARTIFACT="/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-S8-armF-trials.md"
RECS="/tmp/r7.7-S8-armF-logs/records.tsv"
HALT="/tmp/r7.7-S8-halt-marker"
RUNALL_PID=77197

while true; do
  # Exit conditions: (a) halt marker, (b) run-all pid gone, (c) records.tsv has >=19 lines (19 appends = trials 2-20)
  if [[ -f "$HALT" ]]; then
    echo "[$(date -u +%FT%TZ)] HALT marker observed; proceeding to unstage"
    break
  fi
  if ! ps -p "$RUNALL_PID" > /dev/null 2>&1; then
    echo "[$(date -u +%FT%TZ)] run-all pid $RUNALL_PID has exited; proceeding to unstage"
    break
  fi
  RECS_LINES=$(wc -l < "$RECS" 2>/dev/null || echo 0)
  if [[ "$RECS_LINES" -ge 19 ]]; then
    echo "[$(date -u +%FT%TZ)] records.tsv has $RECS_LINES lines (>=19); proceeding to unstage (allowing 90s for final trial append)"
    sleep 90
    break
  fi
  sleep 60
done

echo "[$(date -u +%FT%TZ)] Beginning unstage"
/tmp/r7.7-S8-prompts/unstage-all.sh > /tmp/r7.7-S8-armF-logs/unstage.out 2>&1 || echo "[ERR] unstage-all failed"

# Append end-of-run block
{
  echo ""
  echo "## End-of-run"
  echo ""
  ALL_RECS=$(wc -l < "$RECS" 2>/dev/null || echo 0)
  echo "- Trials completed (record count): ${ALL_RECS}/19 (trial 1 was appended separately; total 1 + ${ALL_RECS})"
  UNST_STATUS=$(grep -cE "STATE:.*UNSTAGED|STATE:.*canonical|RESULT:.*UNSTAGED" /tmp/r7.7-S8-armF-logs/unstage.out 2>/dev/null || echo 0)
  echo "- Variants unstaged (count matching UNSTAGED/canonical heuristic): ${UNST_STATUS}/6"
  FINAL_PF=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh 2>&1 | grep -E "^PREFLIGHT=" | head -1 || echo "PREFLIGHT=UNKNOWN")
  echo "- Final preflight: ${FINAL_PF}"
  TRIP_GATE=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^\[GATE: tripwire\]" | head -1 || echo "UNKNOWN")
  echo "- Tripwire gate: ${TRIP_GATE}"
  FINAL_OMLX=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1 || echo "OMLX_HEALTH=UNKNOWN")
  echo "- Final oMLX status: ${FINAL_OMLX}"
  RES_LINE=$(grep -c "probe-.*-orig" /tmp/r7.7-S8-armF-logs/unstage.out 2>/dev/null || echo 0)
  echo "- Residue (.probe-*-orig files remaining on VM, from unstage-all scan): ${RES_LINE} (0 desired)"
  echo ""
  echo "### Run log pointers"
  echo "- run-all log: /tmp/r7.7-S8-armF-logs/run-all.out"
  echo "- records TSV: /tmp/r7.7-S8-armF-logs/records.tsv"
  echo "- unstage log: /tmp/r7.7-S8-armF-logs/unstage.out"
  echo "- per-trial wrapper logs: /tmp/probe-r7.7-S8-armF-*-run*-wrapper.log, /tmp/probe-r7.7-S8-armF-*-run*-stdout.txt"
  echo ""
  echo "### Judge dispatch pointers"
  echo "- All parent/child session JSONs live on VM at /home/parallels/.hermes/sessions/session_<id>.json"
  echo "- Trial records table above provides parent + child session IDs per trial"
  echo "- Canonical goal prompts: /tmp/r7.7-S8-prompts/T{4,5,6,10}.txt (local Mac) or regenerated from trial record Wall column"
} >> "$ARTIFACT"

echo "[$(date -u +%FT%TZ)] Unstage watcher complete"
