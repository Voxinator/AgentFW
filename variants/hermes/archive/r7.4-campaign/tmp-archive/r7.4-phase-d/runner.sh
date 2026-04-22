#!/usr/bin/env bash
# runner.sh — drive a batch of probe trials sequentially.
# Usage: runner.sh <task> <model_tag> <model_id> <start_run_num> <count> <source_prefix>
# Appends one-line OUTCOME records to /tmp/r7.4-phase-d/outcomes.tsv

set -uo pipefail

TASK="$1"       # T1, T2, T4, T5, T6, T8, T10
MODEL_TAG="$2"  # dense | moe
MODEL_ID="$3"   # gemma-4-31b-it-4bit | gemma-4-26b-a4b-it-mlx-8bit
START="$4"
COUNT="$5"
PREFIX="$6"

OUTFILE=/tmp/r7.4-phase-d/outcomes.tsv
touch "$OUTFILE"

TASK_TEXT=$(/tmp/r7.4-phase-d/tasks.sh "$TASK")

for i in $(seq 1 "$COUNT"); do
  RUN=$((START + i - 1))
  TS=$(date +%H:%M:%S)
  echo "[$TS] Starting trial RUN=$RUN TASK=$TASK MODEL=$MODEL_TAG PREFIX=$PREFIX"
  RAW=$(MODEL="$MODEL_ID" \
    SOURCE_PREFIX="$PREFIX" \
    TOOLSETS=delegation,todo,clarify,file_readonly \
    TIMEOUT_PER_TURN=900 \
    /Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh "$RUN" <<< "$TASK_TEXT" 2>&1)
  OUTCOME_LINE=$(echo "$RAW" | grep '^OUTCOME' | tail -1)
  if [[ -z "$OUTCOME_LINE" ]]; then
    OUTCOME_LINE="OUTCOME run=$RUN MODEL=$MODEL_ID RESULT=WRAPPER_NO_OUTPUT"
  fi
  printf "%s\t%s\t%s\t%s\n" "$TASK" "$MODEL_TAG" "$RUN" "$OUTCOME_LINE" >> "$OUTFILE"
  TS=$(date +%H:%M:%S)
  echo "[$TS] Done RUN=$RUN: $OUTCOME_LINE"
done
