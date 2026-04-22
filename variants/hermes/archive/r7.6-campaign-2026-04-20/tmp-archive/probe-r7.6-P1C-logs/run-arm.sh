#!/usr/bin/env bash
# run-arm.sh — Orchestrator for one arm (A or B) of the r7.6-P1C probe matrix.
# Runs 20 sequential trials: T4x5, T5x5, T6x5, T10x5.
# Writes outcome lines to /tmp/probe-r7.6-P1C-logs/arm-<arm>-outcomes.txt
# After each task batch (5 trials) captures tripwire md5s.

set -euo pipefail

# Fix 5 pre-flight gate — added 2026-04-19 per PLAN-r7.6-P1C-fixes-implementation.md §7.
# Gates: agent_dispatch (env-contract), oMLX health, VM tripwires, VM idle.
# agent_dispatch has no --skip override; the invoking harness must export
# AGENT_DISPATCH_AVAILABLE=1 when its tool scope exposes Agent/Task dispatch.
: "${PREFLIGHT_PATH:=/Users/briantaylor/Projects/AgentFW/probe-preflight.sh}"
if [ ! -x "$PREFLIGHT_PATH" ]; then
  echo "PREFLIGHT missing at $PREFLIGHT_PATH — aborting run-arm.sh" >&2
  exit 1
fi
"$PREFLIGHT_PATH" || {
  echo "PREFLIGHT FAILED — aborting run-arm.sh" >&2
  exit 1
}

ARM="${ARM:-A}"                # A or B
export ARM
export MODEL="gemma-4-26B-A4B-it-MLX-8bit"
export TOOLSETS="delegation,todo,clarify,file_readonly"
export SOURCE_PREFIX="probe-r7.6-arm${ARM}"

LOGDIR="/tmp/probe-r7.6-P1C-logs"
OUTCOMES="$LOGDIR/arm-${ARM}-outcomes.txt"
TRIPWIRE_LOG="$LOGDIR/arm-${ARM}-tripwires.txt"
WRAPPER="/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh"

: > "$OUTCOMES"
: > "$TRIPWIRE_LOG"

mkdir -p "$LOGDIR"

capture_tripwires() {
  local tag="$1"
  echo "=== $tag $(date -Iseconds) ===" >> "$TRIPWIRE_LOG"
  ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md ~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md ~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh' 2>&1 >> "$TRIPWIRE_LOG"
  echo "" >> "$TRIPWIRE_LOG"
}

run_task_batch() {
  local task_id="$1"
  local prompt_file="$LOGDIR/task-${task_id}.txt"
  local prompt; prompt=$(cat "$prompt_file")
  for run in 1 2 3 4 5; do
    local global_run_num
    # global run number = task index (T4=0, T5=1, T6=2, T10=3) * 5 + run offset
    case "$task_id" in
      T4)  global_run_num=$((0*5 + run)) ;;
      T5)  global_run_num=$((1*5 + run)) ;;
      T6)  global_run_num=$((2*5 + run)) ;;
      T10) global_run_num=$((3*5 + run)) ;;
    esac
    local tag="arm${ARM}-${task_id}-run${run}-g${global_run_num}"
    local t_start; t_start=$(date +%s)
    echo "[orch] ----- $tag start -----" | tee -a "$OUTCOMES"

    # Per-trial SOURCE_PREFIX so session tagging is unambiguous
    SOURCE_PREFIX="probe-r7.6-arm${ARM}-${task_id}-moe" \
      "$WRAPPER" "$run" "$prompt" 2>&1 | tee -a "$LOGDIR/arm-${ARM}-${task_id}-run${run}.out"

    # Extract the OUTCOME line from the per-trial output
    grep -E '^OUTCOME ' "$LOGDIR/arm-${ARM}-${task_id}-run${run}.out" | tail -1 \
      | sed "s|^|TRIAL=${tag} |" >> "$OUTCOMES" || true

    local t_end; t_end=$(date +%s)
    local elapsed=$((t_end - t_start))
    echo "[orch] ----- $tag end elapsed=${elapsed}s -----" | tee -a "$OUTCOMES"
  done
  capture_tripwires "after-${task_id}-batch"
}

capture_tripwires "baseline-pre-arm${ARM}"
for task in T4 T5 T6 T10; do
  run_task_batch "$task"
done
capture_tripwires "final-post-arm${ARM}"

echo "[orch] arm ${ARM} complete. Outcomes: $OUTCOMES"
