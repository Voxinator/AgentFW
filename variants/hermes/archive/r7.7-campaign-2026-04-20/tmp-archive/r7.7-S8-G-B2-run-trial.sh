#!/usr/bin/env bash
# Arm G runner — A1-only ablation. HWO off, A2 off, A1 on.
set -uo pipefail
TASK="${1:?TASK required}"
RUN="${2:?RUN num required}"
TRIAL_IDX="${3:?TRIAL_IDX required}"
PROMPT_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
LOG_DIR="/tmp/r7.7-S8-armG-B2-logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/${TASK}-run${RUN}.log"

# shellcheck disable=SC1091
source /tmp/r7.7-env.sh
# Arm G: A1 ON, HWO OFF, A2 OFF
export HERMES_CHILD_TOOLSET_RESTRICT=1
export HERMES_WORKER_OVERLAY=0
export HERMES_WRITE_BEFORE_CLAIM_GATE=0
unset HERMES_WORKER_OVERLAY HERMES_WRITE_BEFORE_CLAIM_GATE
export HERMES_CHILD_TOOLSET_RESTRICT=1
export AGENT_DISPATCH_AVAILABLE=1
export OMLX_SWAP_MAX_GB=30
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export SOURCE_PREFIX="probe-r7.7-S8-armG-${TASK}"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export ARM=A  # HWO prefix off in wrapper (ARM=B would enable HWO)
export TIMEOUT_PER_TURN=1500

START_EPOCH=$(date +%s)
START_TS=$(date -u +%FT%TZ)

TMPOUT=$(mktemp "/tmp/r7.7-S8-armG-${TASK}-run${RUN}.XXXXXX")
/Users/briantaylor/Projects/AgentFW/probe-variantJ-wrapper.sh "$RUN" < "$PROMPT_FILE" > "$TMPOUT" 2>>"$LOG" &
WRAPPER_PID=$!
SECS=0
LIMIT=1800
while kill -0 "$WRAPPER_PID" 2>/dev/null; do
  sleep 5
  SECS=$((SECS + 5))
  if [[ $SECS -ge $LIMIT ]]; then
    echo "[run-trial-armG] 30-min wall-clock cap hit; killing wrapper pid=$WRAPPER_PID" >> "$LOG"
    kill -9 "$WRAPPER_PID" 2>/dev/null || true
    break
  fi
done
wait "$WRAPPER_PID" 2>/dev/null
RC=$?
OUTCOME_RAW=$(cat "$TMPOUT")
if [[ $SECS -ge $LIMIT ]]; then
  OUTCOME_RAW="${OUTCOME_RAW}
OUTCOME run=${RUN} RESULT=TIMEOUT_30MIN final_session=none"
fi
rm -f "$TMPOUT"
END_EPOCH=$(date +%s)
END_TS=$(date -u +%FT%TZ)
WALL=$((END_EPOCH - START_EPOCH))

OUTCOME=$(echo "$OUTCOME_RAW" | grep -E "^OUTCOME" | tail -1)
if [[ -z "$OUTCOME" ]]; then
  OUTCOME="OUTCOME run=${RUN} RESULT=NO_OUTCOME_LINE final_session=none"
fi
echo "$OUTCOME" >> "$LOG"

PARENT_SID=$(echo "$OUTCOME" | grep -oE "final_session=[^ ]+" | cut -d= -f2 | head -1)
[[ -z "$PARENT_SID" || "$PARENT_SID" == "none" ]] && PARENT_SID="MISSING"

CHILD_SIDS="none"
if [[ "$PARENT_SID" != "MISSING" ]]; then
  CHILD_SIDS=$(ssh ubuntu-vm "python3 -c \"
import json, os, glob, time
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

RESULT_STATUS="PASS"
if echo "$OUTCOME" | grep -q "RESULT=TIMEOUT_30MIN"; then RESULT_STATUS="TIMEOUT"
elif echo "$OUTCOME" | grep -q "RESULT=ERROR\|RESULT=WRAPPER_ERROR\|RESULT=UNEXPECTED_LOOP_EXIT\|RESULT=NO_OUTCOME_LINE"; then RESULT_STATUS="ERROR"
elif echo "$OUTCOME" | grep -q "RESULT=RETRY_EXHAUSTED"; then RESULT_STATUS="RETRY_EXHAUSTED"
elif echo "$OUTCOME" | grep -q "RESULT=COMPLIANT"; then RESULT_STATUS="PASS"
fi

OMLX_HEALTH=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1 || echo "OMLX_HEALTH=UNKNOWN")

TRIPWIRE_STATUS=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^PREFLIGHT" | head -1 || echo "PREFLIGHT=UNKNOWN")

printf '%s|%s|%s|%s|%s|%ss|%s|%s|%s|%s|%s\n' \
  "$TRIAL_IDX" "$TASK" "$RUN" "$START_TS" "$END_TS" "$WALL" \
  "$PARENT_SID" "$CHILD_SIDS" "$RESULT_STATUS" "$OMLX_HEALTH" "$TRIPWIRE_STATUS"
