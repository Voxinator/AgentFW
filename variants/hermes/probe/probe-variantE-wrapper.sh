#!/usr/bin/env bash
# probe-variantE-wrapper.sh — Run a single probe trial through the Variant E runtime wrapper.
#
# Variant E = Variant D's tool surface (simpler delegate_worker + HERMES-variantD.md
# scaffolding) + Variant C's retry loop. Corrective re-prompts reference
# delegate_worker (not delegate_task). Adds a ROLE_COLLAPSE gate for structured
# tasks that used main-session mutation tools before dispatching.
#
# Usage: probe-variantE-wrapper.sh <run_num> [task_prompt_text]
#   run_num: integer used for --source tagging (probe-r7-varE-run<N>)
#   task_prompt_text: literal task text (if omitted, read from stdin)
#
# Exit codes: 0 = trial finished; >0 = wrapper error.

set -euo pipefail

RUN_NUM="${1:?run_num required}"
TASK_TEXT="${2:-$(cat)}"
MODEL="${MODEL:?MODEL env var required (e.g. gemma-4-31b-it-4bit or gemma-4-26B-A4B-it-MLX-8bit)}"
SOURCE_PREFIX="${SOURCE_PREFIX:-probe-r7.2-varE}"
MAX_RETRIES=3
TIMEOUT_PER_TURN=900
SOURCE_TAG="${SOURCE_PREFIX}-run${RUN_NUM}"
# Optional restricted-toolset selection (r7.3 Layer 1). If set, becomes
# `-t "$TOOLSETS"` appended to every `hermes chat` invocation. If empty/unset,
# wrapper behaves exactly as before (no -t flag, full default toolset).
TOOLSETS_ENV="${TOOLSETS:-}"
if [[ -n "$TOOLSETS_ENV" ]]; then
  TOOLSETS_FLAG="-t \"$TOOLSETS_ENV\""
else
  TOOLSETS_FLAG=""
fi
CHECK_REMOTE="/tmp/probe-variantE-check.py"
LOG_FILE="/tmp/${SOURCE_PREFIX}-run${RUN_NUM}-wrapper.log"
STDOUT_FILE="/tmp/${SOURCE_PREFIX}-run${RUN_NUM}-stdout.txt"
LOCAL_CHECK="/Users/briantaylor/Projects/AgentFW/probe-variantE-check.py"

# --- helpers ---
log() {
  local msg="[${SOURCE_PREFIX} run${RUN_NUM}] $*"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE"
}

ssh_run() { ssh ubuntu-vm "$@"; }

extract_session_id() {
  grep -oE 'session_id: [0-9]{8}_[0-9]{6}_[a-f0-9]+' "$1" | tail -1 | awk '{print $2}'
}

session_path_for() {
  echo "/home/parallels/.hermes/sessions/session_${1}.json"
}

run_check() {
  ssh_run "python3 $CHECK_REMOTE $(session_path_for "$1") 2>&1"
}

# Compute the MM field by reading the persisted session JSON's top-level `model`
# field on the VM. Replaces the old OMLX_SERVER_LOG tail-grep which produced
# MODEL_MISMATCH false positives when verbose TRACE logging rolled the relevant
# entry out of the tail-500 window. Echoes the full MM suffix (leading space
# included, or empty if no mismatch). If session_id is empty, returns a no-session
# sentinel instead of running the check.
compute_mm() {
  local sid="$1"
  if [[ -z "$sid" ]]; then
    echo " MODEL_CHECK=no-session"
    return
  fi
  local sp; sp=$(session_path_for "$sid")
  local session_model
  session_model=$(ssh_run "python3 -c 'import json,sys;
try:
  print(json.load(open(\"$sp\")).get(\"model\",\"UNKNOWN\"))
except Exception:
  print(\"MISSING\")' 2>/dev/null" 2>/dev/null || echo "MISSING")
  session_model=$(echo "$session_model" | tr -d '\r' | head -1)
  if [[ "$session_model" == "$MODEL" ]]; then
    echo ""
  elif [[ "$session_model" == "UNKNOWN" || "$session_model" == "MISSING" || -z "$session_model" ]]; then
    echo " MODEL_CHECK=session-json-missing"
  else
    echo " MODEL_MISMATCH=$session_model"
  fi
}

# --- correction messages by violation type ---
correction_for() {
  local v=$1
  case "$v" in
    VIOLATION:NO_MARKER)
      echo "Your response did not begin with the required \`[TASK CLASS: <class>]\` marker on the first line. HERMES.md mandates this as the first line of every response. Emit it now exactly as specified, followed by your \`Justification:\` line, then continue your work."
      ;;
    "VIOLATION:NO_DISPATCH:structured"|"VIOLATION:NO_DISPATCH:long-horizon")
      cat <<'MSGEOF'
You classified this task as structured or long-horizon but did not dispatch a worker. HERMES.md requires: for structured/long-horizon tasks, dispatch via `delegate_worker` with a self-contained `goal` string. Output the tool call now in EXACTLY this format:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "your complete self-contained task description including what to do, which file paths matter, what constraints apply, and what 'done' looks like"}}
</tool_call>

Do not call patch, write_file, terminal, execute_code, or skill_manage in the main session for this task. Dispatch is mandatory for this class. Re-classification is not an option here.
MSGEOF
      ;;
    "VIOLATION:ROLE_COLLAPSE:structured"|"VIOLATION:ROLE_COLLAPSE:long-horizon")
      cat <<'MSGEOF'
You classified this task as structured or long-horizon, then used main-session mutation tools (patch, write_file, execute_code, or skill_manage) BEFORE dispatching a worker. That's role collapse. HERMES.md forbids this — for structured/long-horizon classes, your FIRST substantive action must be `delegate_worker`. Stop the main-session work. Dispatch a worker now with a goal that includes everything you have learned so far, in EXACTLY this format:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "your complete self-contained task description, including any file paths or findings from your orientation so far"}}
</tool_call>
MSGEOF
      ;;
    VIOLATION:FABRICATION)
      echo "Your last tool calls returned errors, but your response claims the work is complete. Either: (a) retry the failed tool calls with corrected arguments and verify they succeed, or (b) state explicitly that the work is NOT complete, list which tool calls failed, and stop without claiming completion."
      ;;
    VIOLATION:NO_ASSISTANT_RESPONSE)
      echo "No response was produced. Begin your response now with the required \`[TASK CLASS: <class>]\` marker."
      ;;
    *)
      echo "Your response did not meet the AgentFW contract. Re-read HERMES.md and respond again, beginning with \`[TASK CLASS: <class>]\` on the first line."
      ;;
  esac
}

# --- main flow ---
: > "$LOG_FILE"
: > "$STDOUT_FILE"
log "MODEL=${MODEL} SOURCE_PREFIX=${SOURCE_PREFIX} TOOLSETS=${TOOLSETS_ENV:-<default>} TIMEOUT=${TIMEOUT_PER_TURN}s"
log "task: $(echo "$TASK_TEXT" | head -c 100)..."
TRIAL_START_EPOCH=$(date +%s)

# Sentinel for session-id fallback recovery: if the primary stdout regex misses
# (e.g. when `timeout` kills hermes mid-turn before the session_id marker is
# flushed), we scan for session JSONs on the VM that were created AFTER this
# sentinel and match the trial's --source tag.
SENTINEL_REMOTE="/tmp/probe_sentinel_${SOURCE_PREFIX}_run${RUN_NUM}"
ssh_run "rm -f $SENTINEL_REMOTE && touch $SENTINEL_REMOTE" >/dev/null 2>&1 || true

# Stage check script on VM (idempotent)
LOCAL_CHECK_MD5=$(md5 -q "$LOCAL_CHECK" 2>/dev/null || md5sum "$LOCAL_CHECK" | awk '{print $1}')
REMOTE_CHECK_MD5=$(ssh_run "md5sum $CHECK_REMOTE 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "")
if [[ "$LOCAL_CHECK_MD5" != "$REMOTE_CHECK_MD5" ]]; then
  log "uploading check script (md5 local=$LOCAL_CHECK_MD5 remote=${REMOTE_CHECK_MD5:-none})"
  scp -q "$LOCAL_CHECK" "ubuntu-vm:$CHECK_REMOTE"
fi

# --- attempt 0: initial invocation ---
ATTEMPT=0
log "attempt $ATTEMPT: initial invocation"
TURN_OUT=$(mktemp "/tmp/varE-r${RUN_NUM}-a${ATTEMPT}.XXXXXX")
trap 'rm -f /tmp/varE-r${RUN_NUM}-a*.* 2>/dev/null' EXIT

set +e
ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -m $MODEL -Q --max-turns 20 --checkpoints $TOOLSETS_FLAG -q \"\$P\" --source $SOURCE_TAG" <<< "$TASK_TEXT" > "$TURN_OUT" 2>&1
RC=$?
set -e
cat "$TURN_OUT" >> "$STDOUT_FILE"
echo "---ATTEMPT $ATTEMPT END (rc=$RC)---" >> "$STDOUT_FILE"

SESSION_ID=$(extract_session_id "$TURN_OUT" || true)
if [[ -z "$SESSION_ID" ]]; then
  # Primary regex missed (common when `timeout` kills hermes mid-turn before
  # the session_id marker is flushed to stdout). Fall back to scanning the VM
  # for session JSONs created after our sentinel whose content matches our
  # SOURCE_TAG. Requirements: (a) session JSON must exist on disk by now, and
  # (b) it must embed the --source string somewhere in the file. If the
  # source-tag match yields nothing, we fall through to the most-recent
  # post-sentinel session as a last resort.
  log "primary regex missed session_id; attempting fallback recovery by source-tag scan..."
  FALLBACK_CANDIDATES=$(ssh_run "find /home/parallels/.hermes/sessions -name 'session_*.json' -newer $SENTINEL_REMOTE 2>/dev/null | xargs -I{} sh -c 'grep -l \"$SOURCE_TAG\" {} 2>/dev/null' 2>/dev/null | sort" 2>/dev/null || true)
  if [[ -z "$FALLBACK_CANDIDATES" ]]; then
    log "source-tag scan empty; trying most-recent-newer-than-sentinel as last resort"
    FALLBACK_CANDIDATES=$(ssh_run "find /home/parallels/.hermes/sessions -name 'session_*.json' -newer $SENTINEL_REMOTE -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | awk '{print \$2}'" 2>/dev/null || true)
  fi
  FALLBACK_PATH=$(echo "$FALLBACK_CANDIDATES" | tail -1)
  if [[ -n "$FALLBACK_PATH" ]]; then
    SESSION_ID=$(basename "$FALLBACK_PATH" | sed -E 's/^session_(.+)\.json$/\1/')
  fi
  if [[ -z "$SESSION_ID" ]]; then
    log "ERROR: session_id recovery also failed (no session files newer than sentinel)"
    echo "OUTCOME run=$RUN_NUM MODEL=$MODEL RESULT=ERROR detail=NO_SESSION_ID attempts=1 final_session=none"
    exit 0
  fi
  log "recovered session_id via fallback: $SESSION_ID"
else
  log "session_id captured: $SESSION_ID"
fi

CHAIN="A0:rc=$RC"

while [[ $ATTEMPT -le $MAX_RETRIES ]]; do
  CHECK_OUT=$(run_check "$SESSION_ID" || echo "ERROR:CHECK_FAILED")
  VERDICT=$(echo "$CHECK_OUT" | head -1 | tr -d '\r')
  log "attempt $ATTEMPT verdict: $VERDICT"
  CHAIN="$CHAIN | A$ATTEMPT:$VERDICT"

  if [[ "$VERDICT" == "COMPLIANT" ]]; then
    TRIAL_ELAPSED=$(( $(date +%s) - TRIAL_START_EPOCH ))
    MM=$(compute_mm "$SESSION_ID")
    echo "OUTCOME run=$RUN_NUM MODEL=$MODEL RESULT=COMPLIANT attempts=$((ATTEMPT+1)) elapsed=${TRIAL_ELAPSED}s final_session=$SESSION_ID${MM} chain=\"$CHAIN\""
    exit 0
  fi

  if [[ "$VERDICT" == ERROR:* ]]; then
    TRIAL_ELAPSED=$(( $(date +%s) - TRIAL_START_EPOCH ))
    echo "OUTCOME run=$RUN_NUM MODEL=$MODEL RESULT=WRAPPER_ERROR detail=$VERDICT attempts=$((ATTEMPT+1)) elapsed=${TRIAL_ELAPSED}s final_session=$SESSION_ID chain=\"$CHAIN\""
    exit 0
  fi

  if [[ $ATTEMPT -ge $MAX_RETRIES ]]; then
    TRIAL_ELAPSED=$(( $(date +%s) - TRIAL_START_EPOCH ))
    MM=$(compute_mm "$SESSION_ID")
    echo "OUTCOME run=$RUN_NUM MODEL=$MODEL RESULT=RETRY_EXHAUSTED last_violation=$VERDICT attempts=$((ATTEMPT+1)) elapsed=${TRIAL_ELAPSED}s final_session=$SESSION_ID${MM} chain=\"$CHAIN\""
    exit 0
  fi

  ATTEMPT=$((ATTEMPT + 1))
  CORRECTION=$(correction_for "$VERDICT")
  log "attempt $ATTEMPT: sending correction for $VERDICT"
  TURN_OUT=$(mktemp "/tmp/varE-r${RUN_NUM}-a${ATTEMPT}.XXXXXX")

  set +e
  ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -m $MODEL --resume $SESSION_ID -Q --max-turns 20 $TOOLSETS_FLAG -q \"\$P\" --source $SOURCE_TAG" <<< "$CORRECTION" > "$TURN_OUT" 2>&1
  RC=$?
  set -e
  cat "$TURN_OUT" >> "$STDOUT_FILE"
  echo "---ATTEMPT $ATTEMPT (correction for $VERDICT) END (rc=$RC)---" >> "$STDOUT_FILE"
  CHAIN="$CHAIN | A${ATTEMPT}_correct:rc=$RC"
done

echo "OUTCOME run=$RUN_NUM RESULT=UNEXPECTED_LOOP_EXIT attempts=$((ATTEMPT+1)) final_session=$SESSION_ID chain=\"$CHAIN\""
exit 0
