#!/usr/bin/env bash
# r7.8 Arm K batch 1 runner — 5 trials serial with HERMES_LOOP_DETECTOR=1.
# Adapted from /tmp/r7.8-t1-vet-runner.sh. Leaves staging intact at exit.
set -uo pipefail
cd /Users/briantaylor/Projects/AgentFW

# shellcheck disable=SC1091
source /tmp/r7.7-env.sh

# ARM K = vanilla (no overlay, no A1, no A2) + T1 loop detector ON.
unset HERMES_WORKER_OVERLAY
unset HERMES_CHILD_TOOLSET_RESTRICT
unset HERMES_WRITE_BEFORE_CLAIM_GATE
export ARM=A
export HERMES_LOOP_DETECTOR=1

export AGENT_DISPATCH_AVAILABLE=1
export OMLX_SWAP_MAX_GB=30
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export TIMEOUT_PER_TURN=1500

LOG_DIR="/tmp/r7.8-K-B1-logs"
mkdir -p "$LOG_DIR"

# Arm K batch 1 serial order:
#   1. T4-r1
#   2. T5-r1
#   3. T6-r1
#   4. T10-r1
#   5. T4-r2
declare -a TRIALS=("T4 1" "T5 1" "T6 1" "T10 1" "T4 2")

echo "trial_idx|task|run|start_ts|end_ts|wall_s|parent_sid|result|loop_detected|outcome_line"

IDX=0
for spec in "${TRIALS[@]}"; do
  IDX=$((IDX + 1))
  TASK=$(echo "$spec" | awk '{print $1}')
  RUN=$(echo "$spec" | awk '{print $2}')
  PROMPT_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
  export SOURCE_PREFIX="probe-r7.8-K-B1-${TASK}"
  LOG="${LOG_DIR}/${TASK}-run${RUN}.log"
  STDOUT="${LOG_DIR}/${TASK}-run${RUN}.stdout"

  START_EPOCH=$(date +%s)
  START_TS=$(date -u +%FT%TZ)

  TMPOUT=$(mktemp "/tmp/r7.8-K-B1-trial-${TASK}-run${RUN}.XXXXXX")
  ./probe-variantJ-wrapper.sh "$RUN" < "$PROMPT_FILE" > "$TMPOUT" 2>>"$LOG" &
  WPID=$!
  SECS=0
  LIMIT=1800
  while kill -0 "$WPID" 2>/dev/null; do
    sleep 10
    SECS=$((SECS + 10))
    if [[ $SECS -ge $LIMIT ]]; then
      echo "[K-B1-runner] 30-min wall cap hit; killing pid=$WPID" >> "$LOG"
      kill -9 "$WPID" 2>/dev/null || true
      break
    fi
  done
  wait "$WPID" 2>/dev/null
  cp "$TMPOUT" "$STDOUT"
  OUTCOME=$(grep -E "^OUTCOME" "$TMPOUT" | tail -1 || echo "OUTCOME run=${RUN} RESULT=NO_OUTCOME")
  rm -f "$TMPOUT"

  END_EPOCH=$(date +%s)
  END_TS=$(date -u +%FT%TZ)
  WALL=$((END_EPOCH - START_EPOCH))

  PARENT_SID=$(grep -oE 'session_id: [0-9]{8}_[0-9]{6}_[a-f0-9]+' "$LOG" | tail -1 | awk '{print $2}')
  [[ -z "$PARENT_SID" ]] && PARENT_SID="unknown"

  RESULT=$(echo "$OUTCOME" | grep -oE 'RESULT=[A-Z_]+' | head -1)
  [[ -z "$RESULT" ]] && RESULT="RESULT=UNKNOWN"

  LOOP_FIRED=$(grep -c "r7.8 loop detector" "$LOG" 2>/dev/null || echo 0)

  echo "${IDX}|${TASK}|${RUN}|${START_TS}|${END_TS}|${WALL}s|${PARENT_SID}|${RESULT}|loop_fired=${LOOP_FIRED}|${OUTCOME}"

  OMLX_HEALTH=$(./probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1 || echo "OMLX_HEALTH=UNKNOWN")
  TRIPWIRE=$(./probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^PREFLIGHT" | head -1 || echo "PREFLIGHT=UNKNOWN")
  echo "   -> ${OMLX_HEALTH} ${TRIPWIRE}" >&2

  if [[ "$TRIPWIRE" != "PREFLIGHT=PASS" ]]; then
    echo "HALT: tripwire drift detected after trial ${IDX}" >&2
    exit 2
  fi
done

echo "DONE: 5 trials complete"
