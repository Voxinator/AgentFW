#!/usr/bin/env bash
# Arm K' runner — vanilla Arm A ablation (F+G+H only, no HWO, no A1, no A2, no T1).
set -uo pipefail
TASK="${1:?TASK required}"
RUN="${2:?RUN num required}"
TRIAL_IDX="${3:?TRIAL_IDX required}"
PROMPT_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
LOG_DIR="/tmp/r7.8-KP-B2-logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/${TASK}-run${RUN}.log"

# shellcheck disable=SC1091
source /tmp/r7.7-env.sh
# Arm K': Explicitly unset every feature flag — F+G+H staging remains (VM-side patches)
unset HERMES_WORKER_OVERLAY
unset HERMES_CHILD_TOOLSET_RESTRICT
unset HERMES_WRITE_BEFORE_CLAIM_GATE
unset HERMES_LOOP_DETECTOR
export AGENT_DISPATCH_AVAILABLE=1
export OMLX_SWAP_MAX_GB=30
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export SOURCE_PREFIX="probe-r7.8-KP-B2-${TASK}"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export ARM=A  # HWO prefix OFF in wrapper
export TIMEOUT_PER_TURN=1500

START_EPOCH=$(date +%s)
START_TS=$(date -u +%FT%TZ)

TMPOUT=$(mktemp "/tmp/r7.8-KP-B2-${TASK}-run${RUN}.XXXXXX")
/Users/briantaylor/Projects/AgentFW/probe-variantJ-wrapper.sh "$RUN" < "$PROMPT_FILE" > "$TMPOUT" 2>>"$LOG" &
WRAPPER_PID=$!
SECS=0
LIMIT=1800
while kill -0 "$WRAPPER_PID" 2>/dev/null; do
  sleep 5
  SECS=$((SECS + 5))
  if [[ $SECS -ge $LIMIT ]]; then
    echo "[run-trial-armKp] 30-min wall-clock cap hit; killing wrapper pid=$WRAPPER_PID" >> "$LOG"
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

# Max consecutive identical tool calls — compute across parent + children
MAX_CONSEC=0
if [[ "$PARENT_SID" != "MISSING" ]]; then
  ALL_SIDS="$PARENT_SID"
  if [[ "$CHILD_SIDS" != "none" ]]; then
    ALL_SIDS="$PARENT_SID,$CHILD_SIDS"
  fi
  MAX_CONSEC=$(ssh ubuntu-vm "python3 -c \"
import json, os
sids = '${ALL_SIDS}'.split(',')
overall = 0
for sid in sids:
  p = '/home/parallels/.hermes/sessions/session_' + sid + '.json'
  if not os.path.exists(p): continue
  try:
    with open(p) as f: d = json.load(f)
  except Exception: continue
  msgs = d.get('messages', [])
  prev_sig = None
  run = 0
  best = 0
  for m in msgs:
    tc = m.get('tool_calls') or []
    if not tc:
      prev_sig = None; run = 0; continue
    # Signature: tool name + arg JSON
    sig_parts = []
    for c in tc:
      fn = c.get('function', {}) if isinstance(c, dict) else {}
      name = fn.get('name', '')
      args = fn.get('arguments', '')
      sig_parts.append(name + '|' + str(args))
    sig = '\\n'.join(sig_parts)
    if sig == prev_sig:
      run += 1
    else:
      run = 1; prev_sig = sig
    if run > best: best = run
  if best > overall: overall = best
print(overall)
\"" 2>/dev/null)
  [[ -z "$MAX_CONSEC" ]] && MAX_CONSEC=0
fi

RESULT_STATUS="PASS"
if echo "$OUTCOME" | grep -q "RESULT=TIMEOUT_30MIN"; then RESULT_STATUS="TIMEOUT"
elif echo "$OUTCOME" | grep -q "RESULT=ERROR\|RESULT=WRAPPER_ERROR\|RESULT=UNEXPECTED_LOOP_EXIT\|RESULT=NO_OUTCOME_LINE"; then RESULT_STATUS="ERROR"
elif echo "$OUTCOME" | grep -q "RESULT=RETRY_EXHAUSTED"; then RESULT_STATUS="RETRY_EXHAUSTED"
elif echo "$OUTCOME" | grep -q "RESULT=COMPLIANT"; then RESULT_STATUS="PASS"
fi

OMLX_HEALTH=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1 || echo "OMLX_HEALTH=UNKNOWN")

TRIPWIRE_STATUS=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^PREFLIGHT" | head -1 || echo "PREFLIGHT=UNKNOWN")

printf '%s|%s|%s|%s|%s|%ss|%s|%s|%s|%s|%s|%s\n' \
  "$TRIAL_IDX" "$TASK" "$RUN" "$START_TS" "$END_TS" "$WALL" \
  "$PARENT_SID" "$CHILD_SIDS" "$MAX_CONSEC" "$RESULT_STATUS" "$OMLX_HEALTH" "$TRIPWIRE_STATUS"
