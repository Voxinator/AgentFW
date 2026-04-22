#!/usr/bin/env bash
# run one S8 Arm F trial; print a parseable record line on stdout
set -uo pipefail
TASK="${1:?TASK required}"       # T4|T5|T6|T10
RUN="${2:?RUN num required}"     # 1..5
TRIAL_IDX="${3:?TRIAL_IDX required}"  # 1..20 for the record
PROMPT_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
LOG_DIR="/tmp/r7.7-S8-armF-logs"
mkdir -p "$LOG_DIR"
TS=$(date +%Y%m%d_%H%M%S)
LOG="${LOG_DIR}/${TASK}-run${RUN}.log"

# shellcheck disable=SC1091
source /tmp/r7.7-env.sh
export HERMES_WORKER_OVERLAY=1
export HERMES_CHILD_TOOLSET_RESTRICT=1
export HERMES_WRITE_BEFORE_CLAIM_GATE=1
export AGENT_DISPATCH_AVAILABLE=1
export OMLX_SWAP_MAX_GB=5.5
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export SOURCE_PREFIX="probe-r7.7-S8-armF-${TASK}"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export ARM=B  # enable overlay path
export TIMEOUT_PER_TURN=1500

START_EPOCH=$(date +%s)
START_TS=$(date -u +%FT%TZ)

# Run the trial (cap wall-clock at 30 min = 1800s) — no macOS timeout binary, so background+kill.
TMPOUT=$(mktemp "/tmp/r7.7-S8-trial-${TASK}-run${RUN}.XXXXXX")
/Users/briantaylor/Projects/AgentFW/probe-variantJ-wrapper.sh "$RUN" < "$PROMPT_FILE" > "$TMPOUT" 2>>"$LOG" &
WRAPPER_PID=$!
SECS=0
LIMIT=1800
while kill -0 "$WRAPPER_PID" 2>/dev/null; do
  sleep 5
  SECS=$((SECS + 5))
  if [[ $SECS -ge $LIMIT ]]; then
    echo "[run-trial] 30-min wall-clock cap hit; killing wrapper pid=$WRAPPER_PID" >> "$LOG"
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

# Capture the OUTCOME line (last non-empty line)
OUTCOME=$(echo "$OUTCOME_RAW" | grep -E "^OUTCOME" | tail -1)
if [[ -z "$OUTCOME" ]]; then
  OUTCOME="OUTCOME run=${RUN} RESULT=NO_OUTCOME_LINE final_session=none"
fi
echo "$OUTCOME" >> "$LOG"

# Parse parent session id
PARENT_SID=$(echo "$OUTCOME" | grep -oE "final_session=[^ ]+" | cut -d= -f2 | head -1)
[[ -z "$PARENT_SID" || "$PARENT_SID" == "none" ]] && PARENT_SID="MISSING"

# Find child session(s) + a2_gate_outcome
CHILD_SIDS="none"
A2_GATE="none"
if [[ "$PARENT_SID" != "MISSING" ]]; then
  PSID_JSON="/home/parallels/.hermes/sessions/session_${PARENT_SID}.json"
  # Parse a2_gate_outcome from parent JSON (one-line grep is robust across quoting)
  A2_GATE=$(ssh ubuntu-vm "grep -oE 'a2_gate_outcome[^,}]*' ${PSID_JSON} 2>/dev/null | grep -oE '\"[A-Z_]+\"' | tr -d '\"' | sort -u | tr '\n' ','" 2>/dev/null | sed 's/,$//')
  [[ -z "$A2_GATE" ]] && A2_GATE="none"
  # Child sessions: find session files modified within 2min of parent-start, not the parent, and whose messages[0].content does NOT match TASK_TEXT prefix (child goal differs from parent task text when classification is structured/long-horizon — and matches when goal==task)
  # Simpler: use parent's delegate_worker_v2 tool_result contents to extract child_session_id (Hermes returns session id in the result). Fallback: any session modified within start+20min window that's not the parent.
  # Use trial-window approach: session files created after trial START, excluding parent, with non-trivial message count
  CHILD_SIDS=$(ssh ubuntu-vm "python3 -c \"
import json, os, glob, re, time
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
    # Child sessions are spawned by delegate_worker_v2; their first-user content is the 'goal' passed by parent. We accept any non-parent session whose mtime is within the trial window.
    out.append(sid)
  print(','.join(out))
except Exception as e:
  print('')
\"" 2>/dev/null)
  [[ -z "$CHILD_SIDS" ]] && CHILD_SIDS="none"
fi

# Determine status
RESULT_STATUS="PASS"
if echo "$OUTCOME" | grep -q "RESULT=TIMEOUT_30MIN"; then RESULT_STATUS="TIMEOUT"
elif echo "$OUTCOME" | grep -q "RESULT=ERROR\|RESULT=WRAPPER_ERROR\|RESULT=UNEXPECTED_LOOP_EXIT\|RESULT=NO_OUTCOME_LINE"; then RESULT_STATUS="ERROR"
elif echo "$OUTCOME" | grep -q "RESULT=RETRY_EXHAUSTED"; then RESULT_STATUS="RETRY_EXHAUSTED"
elif echo "$OUTCOME" | grep -q "RESULT=COMPLIANT"; then RESULT_STATUS="PASS"
fi

# Post-trial oMLX health check
OMLX_HEALTH=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1 || echo "OMLX_HEALTH=UNKNOWN")

# Post-trial tripwire check
TRIPWIRE_STATUS=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^PREFLIGHT" | head -1 || echo "PREFLIGHT=UNKNOWN")

printf '%s|%s|%s|%s|%s|%ss|%s|%s|%s|%s|%s|%s\n' \
  "$TRIAL_IDX" "$TASK" "$RUN" "$START_TS" "$END_TS" "$WALL" \
  "$PARENT_SID" "$CHILD_SIDS" "$A2_GATE" "$RESULT_STATUS" "$OMLX_HEALTH" "$TRIPWIRE_STATUS"
