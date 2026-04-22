#!/usr/bin/env bash
# r7.8 P3a C1 vet — vanilla Arm A trial runner (NO overlay, NO restrict, NO gate)
# Only C1's parser fix is in play.
set -uo pipefail
TASK="${1:?TASK required}"
RUN="${2:?RUN required}"
TRIAL_IDX="${3:?TRIAL_IDX required}"
PROMPT_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
LOG_DIR="/tmp/r7.8-P3a-C1-logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/${TASK}-run${RUN}.log"

# shellcheck disable=SC1091
source /tmp/r7.7-env.sh
# Explicitly UNSET HWO/restrict/gate — vanilla Arm A
unset HERMES_WORKER_OVERLAY
unset HERMES_CHILD_TOOLSET_RESTRICT
unset HERMES_WRITE_BEFORE_CLAIM_GATE
export AGENT_DISPATCH_AVAILABLE=1
export OMLX_SWAP_MAX_GB=30
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export SOURCE_PREFIX="probe-r7.8-P3a-C1-${TASK}"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export ARM=A
export TIMEOUT_PER_TURN=1500

START_EPOCH=$(date +%s)
TMPOUT=$(mktemp "/tmp/r7.8-P3a-trial-${TASK}-run${RUN}.XXXXXX")

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
WALL=$((END_EPOCH - START_EPOCH))

OUTCOME=$(echo -e "$OUTCOME_RAW" | grep -E "^OUTCOME" | tail -1)
if [[ -z "$OUTCOME" ]]; then
  OUTCOME="OUTCOME run=${RUN} RESULT=NO_OUTCOME_LINE final_session=none"
fi
echo "$OUTCOME" >> "$LOG"
echo "[TRIAL_RECORD] task=$TASK run=$RUN idx=$TRIAL_IDX wall=${WALL}s rc=$RC"
echo "  $OUTCOME"
echo "$OUTCOME_RAW" | tail -5
