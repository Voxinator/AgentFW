#!/usr/bin/env bash
# r7.8 P3b S1 vet — single-trial runner
# Vanilla Arm A (F+G+H, no A1/A2/HWO) with S1 sampler tune applied server-side.
set -uo pipefail

TASK="${1:?TASK}"     # T4|T5|T6|T10
RUN="${2:?RUN}"
IDX="${3:?IDX}"

PROMPT_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
LOG_DIR="/tmp/r7.8-P3b-S1-logs"
mkdir -p "$LOG_DIR"

LOG="${LOG_DIR}/${TASK}-run${RUN}.log"

# shellcheck disable=SC1091
source /tmp/r7.7-env.sh
# Vanilla Arm A: no A1/A2/HWO overlays
unset HERMES_WORKER_OVERLAY
unset HERMES_CHILD_TOOLSET_RESTRICT
unset HERMES_WRITE_BEFORE_CLAIM_GATE
unset ARM
export AGENT_DISPATCH_AVAILABLE=1
export OMLX_SWAP_MAX_GB=30
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export SOURCE_PREFIX="probe-r7.8-P3b-S1-${TASK}"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export TIMEOUT_PER_TURN=1500

START_EPOCH=$(date +%s)
START_TS=$(date -u +%FT%TZ)

TMPOUT=$(mktemp "/tmp/r7.8-P3b-S1-${TASK}-run${RUN}.XXXXXX")
/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh "$RUN" < "$PROMPT_FILE" > "$TMPOUT" 2>>"$LOG" &
WRAPPER_PID=$!
SECS=0
LIMIT=1800
while kill -0 "$WRAPPER_PID" 2>/dev/null; do
  sleep 5
  SECS=$((SECS + 5))
  if [[ $SECS -ge $LIMIT ]]; then
    echo "[run-trial] 30-min cap; kill" >> "$LOG"
    kill -9 "$WRAPPER_PID" 2>/dev/null || true
    break
  fi
done
wait "$WRAPPER_PID" 2>/dev/null
RC=$?
OUTCOME_RAW=$(cat "$TMPOUT")
if [[ $SECS -ge $LIMIT ]]; then
  OUTCOME_RAW="${OUTCOME_RAW}\nOUTCOME run=${RUN} RESULT=TIMEOUT_30MIN final_session=none"
fi
rm -f "$TMPOUT"
END_EPOCH=$(date +%s)
END_TS=$(date -u +%FT%TZ)
WALL=$((END_EPOCH - START_EPOCH))

OUTCOME=$(echo "$OUTCOME_RAW" | grep -E "^OUTCOME" | tail -1)
[[ -z "$OUTCOME" ]] && OUTCOME="OUTCOME run=${RUN} RESULT=NO_OUTCOME_LINE final_session=none"
echo "$OUTCOME" >> "$LOG"

PARENT_SID=$(echo "$OUTCOME" | grep -oE "final_session=[^ ]+" | cut -d= -f2 | head -1)
[[ -z "$PARENT_SID" || "$PARENT_SID" == "none" ]] && PARENT_SID="MISSING"

CHILD_SIDS="none"
if [[ "$PARENT_SID" != "MISSING" ]]; then
  CHILD_SIDS=$(ssh ubuntu-vm "python3 -c \"
import json, os, glob
try:
  start = ${START_EPOCH}
  sdir = '/home/parallels/.hermes/sessions'
  out = []
  for path in sorted(glob.glob(os.path.join(sdir, 'session_*.json')), key=lambda p: os.path.getmtime(p)):
    sid = os.path.basename(path)[len('session_'):-len('.json')]
    if sid == '${PARENT_SID}': continue
    try:
      ctime = os.path.getmtime(path)
      if ctime < start - 5: continue
    except Exception: continue
    try:
      with open(path) as f: d = json.load(f)
    except Exception: continue
    msgs = d.get('messages', [])
    if len(msgs) < 2: continue
    out.append(sid)
  print(','.join(out))
except Exception as e:
  print('')
\"" 2>/dev/null)
  [[ -z "$CHILD_SIDS" ]] && CHILD_SIDS="none"
fi

RESULT_STATUS="UNKNOWN"
if echo "$OUTCOME" | grep -q "RESULT=TIMEOUT_30MIN"; then RESULT_STATUS="TIMEOUT"
elif echo "$OUTCOME" | grep -q "RESULT=ERROR\|RESULT=WRAPPER_ERROR\|RESULT=UNEXPECTED_LOOP_EXIT\|RESULT=NO_OUTCOME_LINE"; then RESULT_STATUS="ERROR"
elif echo "$OUTCOME" | grep -q "RESULT=RETRY_EXHAUSTED"; then RESULT_STATUS="RETRY_EXHAUSTED"
elif echo "$OUTCOME" | grep -q "RESULT=COMPLIANT"; then RESULT_STATUS="PASS"
elif echo "$OUTCOME" | grep -q "RESULT=FAIL"; then RESULT_STATUS="FAIL"
fi

TRIPWIRE_STATUS=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^PREFLIGHT" | head -1 || echo "PREFLIGHT=UNKNOWN")

printf '%s|%s|%s|%s|%s|%ss|%s|%s|%s|%s\n' \
  "$IDX" "$TASK" "$RUN" "$START_TS" "$END_TS" "$WALL" \
  "$PARENT_SID" "$CHILD_SIDS" "$RESULT_STATUS" "$TRIPWIRE_STATUS"
