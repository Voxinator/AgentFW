#!/usr/bin/env bash
# Usage: run-trial.sh <task> <run> <source_prefix>
set -u
TASK="$1"   # T4, T5, T6, T10
RUN="$2"    # 2, 1, 3 etc
SRC_PREFIX="$3"  # probe-r7.7-S8-F-B1-T4-run2 etc

source /tmp/r7.7-env.sh
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export SOURCE_PREFIX="$SRC_PREFIX"
export HERMES_WORKER_OVERLAY=1
export HERMES_CHILD_TOOLSET_RESTRICT=1
export HERMES_WRITE_BEFORE_CLAIM_GATE=1
export TIMEOUT_PER_TURN=1500

TASK_FILE="/tmp/r7.7-S8-prompts/${TASK}.txt"
STDOUT_FILE="/tmp/${SRC_PREFIX}-runner.stdout"
STDERR_FILE="/tmp/${SRC_PREFIX}-runner.stderr"

echo "START=$(date -Iseconds)"
# Run wrapper, read prompt from stdin
/Users/briantaylor/Projects/AgentFW/probe-variantJ-wrapper.sh "$RUN" < "$TASK_FILE" > "$STDOUT_FILE" 2> "$STDERR_FILE" &
WPID=$!

# Local watchdog: kill if exceeds 1700s (slightly > TIMEOUT_PER_TURN + buffer)
MAX_WALL=1700
elapsed=0
while kill -0 $WPID 2>/dev/null; do
  sleep 10
  elapsed=$((elapsed + 10))
  if [ $elapsed -ge $MAX_WALL ]; then
    echo "LOCAL_WATCHDOG_KILL at ${elapsed}s"
    kill -TERM $WPID 2>/dev/null
    sleep 5
    kill -KILL $WPID 2>/dev/null
    echo "END=$(date -Iseconds)"
    echo "RC=TIMEOUT_LOCAL"
    exit 124
  fi
done
wait $WPID
RC=$?
echo "END=$(date -Iseconds)"
echo "RC=$RC"
exit $RC
