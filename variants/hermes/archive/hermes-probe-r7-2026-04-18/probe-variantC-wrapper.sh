#!/usr/bin/env bash
# probe-variantC-wrapper.sh — Run a single probe trial through the Variant C runtime wrapper.
#
# Usage: probe-variantC-wrapper.sh <run_num> <task_prompt_text>
#   run_num: integer 1-10 used for --source tagging (probe-r7-varC-run<N>)
#   task_prompt_text: literal task text (use stdin OR pass as second arg)
#
# Reads task from stdin if "$2" is omitted.
#
# Behavior:
#   1. Invoke `hermes chat` on ubuntu-vm with the task.
#   2. Parse resulting session JSON via probe-variantC-check.py.
#   3. If gate violation, send a correction message via `hermes chat --resume`.
#   4. Loop up to MAX_RETRIES=3 attempts.
#   5. Print structured outcome line + chain log to stdout; capture full stdout to /tmp.
#
# Exit codes: 0 = trial finished (compliant or retry-exhausted); >0 = wrapper error.

set -euo pipefail

RUN_NUM="${1:?run_num required}"
TASK_TEXT="${2:-$(cat)}"
MAX_RETRIES=3
TIMEOUT_PER_TURN=300
SOURCE_TAG="probe-r7-varC-run${RUN_NUM}"
CHECK_REMOTE="/tmp/probe-variantC-check.py"
LOG_FILE="/tmp/varC-run${RUN_NUM}-wrapper.log"
STDOUT_FILE="/tmp/varC-run${RUN_NUM}-stdout.txt"

# --- helpers ---
log() {
  local msg="[varC run${RUN_NUM}] $*"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE"
}

ssh_run() {
  ssh ubuntu-vm "$@"
}

extract_session_id() {
  grep -oE 'session_id: [0-9]{8}_[0-9]{6}_[a-f0-9]+' "$1" | tail -1 | awk '{print $2}'
}

session_path_for() {
  local sid=$1
  echo "/home/parallels/.hermes/sessions/session_${sid}.json"
}

run_check() {
  local sid=$1
  ssh_run "python3 $CHECK_REMOTE $(session_path_for "$sid") 2>&1"
}

# --- correction messages by violation type ---
correction_for() {
  local v=$1
  case "$v" in
    VIOLATION:NO_MARKER)
      echo "Your response did not begin with the required \`[TASK CLASS: <class>]\` marker on the first line. HERMES.md mandates this as the first line of every response. Emit it now exactly as specified, followed by your \`Justification:\` line, then continue your work."
      ;;
    VIOLATION:NO_DISPATCH:structured)
      echo "You classified this task as \`structured\`. Per the role-separation rule in HERMES.md, the main session must NOT write implementation code directly for structured tasks — you must dispatch a worker via \`delegate_task(goal=..., context=...)\`. Either dispatch one now with a focused goal and the relevant context, or re-classify to \`one-shot\` with a justification explaining why no decomposition or independent verification is needed."
      ;;
    VIOLATION:NO_DISPATCH:long-horizon)
      echo "You classified this task as \`long-horizon\`. Per HERMES.md, long-horizon tasks require workers dispatched via \`delegate_task\`. Dispatch one now with a focused goal and the relevant context. Do not write implementation in the main session."
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
log "task: $(echo "$TASK_TEXT" | head -c 100)..."

# Stage check script on VM (idempotent — md5-compare to skip re-upload)
LOCAL_CHECK_MD5=$(md5 -q /Users/briantaylor/Projects/AgentFW/probe-variantC-check.py 2>/dev/null || md5sum /Users/briantaylor/Projects/AgentFW/probe-variantC-check.py | awk '{print $1}')
REMOTE_CHECK_MD5=$(ssh_run "md5sum $CHECK_REMOTE 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "")
if [[ "$LOCAL_CHECK_MD5" != "$REMOTE_CHECK_MD5" ]]; then
  log "uploading check script (md5 mismatch: local=$LOCAL_CHECK_MD5 remote=${REMOTE_CHECK_MD5:-none})"
  scp -q /Users/briantaylor/Projects/AgentFW/probe-variantC-check.py ubuntu-vm:$CHECK_REMOTE
fi

# --- attempt 0: initial invocation ---
ATTEMPT=0
log "attempt $ATTEMPT: initial invocation"
TURN_OUT=$(mktemp /tmp/varC-r${RUN_NUM}-a${ATTEMPT}.XXXXXX)
trap "rm -f /tmp/varC-r${RUN_NUM}-a*.* 2>/dev/null" EXIT

set +e
ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat -Q --max-turns 20 --checkpoints -q \"\$P\" --source $SOURCE_TAG" <<< "$TASK_TEXT" > "$TURN_OUT" 2>&1
RC=$?
set -e
cat "$TURN_OUT" >> "$STDOUT_FILE"
echo "---ATTEMPT $ATTEMPT END (rc=$RC)---" >> "$STDOUT_FILE"

SESSION_ID=$(extract_session_id "$TURN_OUT" || true)
if [[ -z "$SESSION_ID" ]]; then
  log "ERROR: no session_id captured from initial invocation (rc=$RC)"
  log "see $TURN_OUT for raw output"
  echo "OUTCOME run=$RUN_NUM ERROR=NO_SESSION_ID attempts=1 final_session=none"
  exit 0
fi
log "session_id captured: $SESSION_ID"

CHAIN="A0:rc=$RC"

# --- gate check + retry loop ---
while [[ $ATTEMPT -le $MAX_RETRIES ]]; do
  CHECK_OUT=$(run_check "$SESSION_ID" || echo "ERROR:CHECK_FAILED")
  VERDICT=$(echo "$CHECK_OUT" | head -1 | tr -d '\r')
  log "attempt $ATTEMPT verdict: $VERDICT"
  CHAIN="$CHAIN | A$ATTEMPT:$VERDICT"

  if [[ "$VERDICT" == "COMPLIANT" ]]; then
    log "COMPLIANT after attempt $ATTEMPT"
    echo "OUTCOME run=$RUN_NUM RESULT=COMPLIANT attempts=$((ATTEMPT+1)) final_session=$SESSION_ID chain=\"$CHAIN\""
    exit 0
  fi

  if [[ "$VERDICT" == ERROR:* ]]; then
    log "wrapper check error: $VERDICT"
    echo "OUTCOME run=$RUN_NUM RESULT=WRAPPER_ERROR detail=$VERDICT attempts=$((ATTEMPT+1)) final_session=$SESSION_ID chain=\"$CHAIN\""
    exit 0
  fi

  if [[ $ATTEMPT -ge $MAX_RETRIES ]]; then
    log "retry budget exhausted after attempt $ATTEMPT"
    echo "OUTCOME run=$RUN_NUM RESULT=RETRY_EXHAUSTED last_violation=$VERDICT attempts=$((ATTEMPT+1)) final_session=$SESSION_ID chain=\"$CHAIN\""
    exit 0
  fi

  ATTEMPT=$((ATTEMPT + 1))
  CORRECTION=$(correction_for "$VERDICT")
  log "attempt $ATTEMPT: sending correction for $VERDICT"
  TURN_OUT=$(mktemp /tmp/varC-r${RUN_NUM}-a${ATTEMPT}.XXXXXX)

  set +e
  ssh_run "P=\$(cat); cd ~/.hermes/hermes-agent && timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat --resume $SESSION_ID -Q --max-turns 20 -q \"\$P\" --source $SOURCE_TAG" <<< "$CORRECTION" > "$TURN_OUT" 2>&1
  RC=$?
  set -e
  cat "$TURN_OUT" >> "$STDOUT_FILE"
  echo "---ATTEMPT $ATTEMPT (correction for $VERDICT) END (rc=$RC)---" >> "$STDOUT_FILE"
  CHAIN="$CHAIN | A${ATTEMPT}_correct:rc=$RC"
done

log "loop exited unexpectedly"
echo "OUTCOME run=$RUN_NUM RESULT=UNEXPECTED_LOOP_EXIT attempts=$((ATTEMPT+1)) final_session=$SESSION_ID chain=\"$CHAIN\""
exit 0
