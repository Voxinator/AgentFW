#!/usr/bin/env bash
# probe-r7.3-l12-driver.sh — Sequential L1+L2 stacked probe driver.
# Runs 30 trials (3 tasks × 5 trials × 2 models) + 4 one-shot regression checks.
# Designed to run in background via Bash run_in_background=true.
# Appends OUTCOME lines to /tmp/probe-r7.3-l12-OUTCOMES.txt.
# Tripwire-checks after each trial; halts on tripwire drift.

set -uo pipefail

WRAPPER=/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh
OUT=/tmp/probe-r7.3-l12-OUTCOMES.txt
TOOLSETS_VAL="delegation,todo,clarify,file_readonly"

# Tripwire baselines
TW_USEDASH="5503ee1c2ef7d635a020eea275e41239"
TW_JIRABRIEFING="a1dce6e989527686124d0860830627c9"
TW_SKILLMD="fb1a5a5208a6cf2fcb8252aac10397eb"

# Tasks (verbatim from probe-tasks.md). Numbering matches global probe-tasks scheme.
read -r -d '' TASK_4 <<'EOT' || true
Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts. All existing tests must still pass after the refactor.
EOT

read -r -d '' TASK_6 <<'EOT' || true
Build a new export feature for our product. Users should be able to export their data as CSV, JSON, or PDF. It needs to respect permissions (users can only export data they own), include test coverage, and update the API docs. Ship it end-to-end.
EOT

read -r -d '' TASK_9 <<'EOT' || true
The Jira daily briefing cron has been silently failing on some days — no notification, no output, but the job appears to have run. Figure out what's happening and fix it.
EOT

# One-shot regression spot-check tasks
read -r -d '' TASK_1 <<'EOT' || true
What's the capital of France?
EOT

read -r -d '' TASK_8 <<'EOT' || true
Write a one-off script to count files larger than 10MB in ~/Downloads and print the total. Python is fine.
EOT

# Initialize output
echo "=== probe-r7.3-l12 driver starting at $(date '+%Y-%m-%d %H:%M:%S') ===" > "$OUT"
echo "Wrapper: $WRAPPER" >> "$OUT"
echo "Toolsets: $TOOLSETS_VAL" >> "$OUT"
echo "HERMES.md md5 (live on VM): $(ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md | awk "{print \$1}"')" >> "$OUT"
echo "Tripwire baselines: useDash=$TW_USEDASH jira=$TW_JIRABRIEFING skill=$TW_SKILLMD" >> "$OUT"
echo "" >> "$OUT"

run_trial () {
  local model=$1
  local source_prefix=$2
  local run_num=$3
  local task_id=$4
  local task_text=$5

  local tw=$(ssh ubuntu-vm "md5sum /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md 2>&1" | awk '{print $1}' | tr '\n' ',')

  echo "" >> "$OUT"
  echo "=== [$(date '+%H:%M:%S')] $source_prefix run$run_num task=T$task_id tw=$tw ===" >> "$OUT"

  MODEL="$model" SOURCE_PREFIX="$source_prefix" TOOLSETS="$TOOLSETS_VAL" \
    "$WRAPPER" "$run_num" "$task_text" >> "$OUT" 2>&1

  local tw_after=$(ssh ubuntu-vm "md5sum /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md 2>&1" | awk '{print $1}' | tr '\n' ',')
  if [[ "$tw" != "$tw_after" ]]; then
    echo "!!! TRIPWIRE DRIFT after $source_prefix run$run_num: before=$tw after=$tw_after !!!" >> "$OUT"
  fi
}

# Dense leg: T4 runs 1-5, T6 runs 6-10, T9 runs 11-15
for run in 1 2 3 4 5; do run_trial "gemma-4-31b-it-4bit" "probe-r7.3-l12-dense" "$run" "4" "$TASK_4"; done
for run in 6 7 8 9 10; do run_trial "gemma-4-31b-it-4bit" "probe-r7.3-l12-dense" "$run" "6" "$TASK_6"; done
for run in 11 12 13 14 15; do run_trial "gemma-4-31b-it-4bit" "probe-r7.3-l12-dense" "$run" "9" "$TASK_9"; done

# MoE leg: same pattern
for run in 1 2 3 4 5; do run_trial "gemma-4-26B-A4B-it-MLX-8bit" "probe-r7.3-l12-moe" "$run" "4" "$TASK_4"; done
for run in 6 7 8 9 10; do run_trial "gemma-4-26B-A4B-it-MLX-8bit" "probe-r7.3-l12-moe" "$run" "6" "$TASK_6"; done
for run in 11 12 13 14 15; do run_trial "gemma-4-26B-A4B-it-MLX-8bit" "probe-r7.3-l12-moe" "$run" "9" "$TASK_9"; done

# One-shot regression spot-checks
for model_label in "gemma-4-31b-it-4bit:dense" "gemma-4-26B-A4B-it-MLX-8bit:moe"; do
  model="${model_label%%:*}"
  label="${model_label##*:}"
  run_trial "$model" "probe-r7.3-l12-oneshot-$label" "1" "1" "$TASK_1"
  run_trial "$model" "probe-r7.3-l12-oneshot-$label" "8" "8" "$TASK_8"
done

echo "" >> "$OUT"
echo "=== probe-r7.3-l12 driver completed at $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$OUT"
