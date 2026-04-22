#!/usr/bin/env bash
# Run all remaining trials serially. Each trial runs to completion or 30-min cap.
# Per-trial: preflight gate -> run wrapper -> record line -> oMLX post-check.
# On DEGRADED: halt immediately, write halt marker, exit.
set -uo pipefail

ARTIFACT="/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-S8-armF-trials.md"
HALT_MARKER="/tmp/r7.7-S8-halt-marker"
RESULTS_APPEND="/tmp/r7.7-S8-armF-logs/records.tsv"
CHECKPOINT_INTERVAL=5

# Trial order: T4-run1, T5-run1, T6-run1, T10-run1, T4-run2, ...
# Trial 1 already done (T4-run1). Start from trial 2.
TRIALS=(
  # trial-n task run
  "2  T5  1"
  "3  T6  1"
  "4  T10 1"
  "5  T4  2"
  "6  T5  2"
  "7  T6  2"
  "8  T10 2"
  "9  T4  3"
  "10 T5  3"
  "11 T6  3"
  "12 T10 3"
  "13 T4  4"
  "14 T5  4"
  "15 T6  4"
  "16 T10 4"
  "17 T4  5"
  "18 T5  5"
  "19 T6  5"
  "20 T10 5"
)

append_record() {
  local rec="$1"
  # Parse fields by |
  IFS='|' read -r IDX TASK RUN START END WALL PSID CSID A2 STATUS OMLX TRIP <<< "$rec"
  local line="| $IDX | $TASK | $RUN | $START | $END | $WALL | $PSID | $CSID | $A2 | $STATUS |"
  # Find the row boundary (first row matching "| # |" after the header separator) and append after all existing rows.
  python3 <<PYEOF
path = "$ARTIFACT"
with open(path) as f: content = f.read()
line = "$line"
# Append after the last table row (last line starting with '| ' or before ## header that follows)
lines = content.splitlines()
out = []
inserted = False
# find the trial-records table boundary — table ends where a blank line or ## heading follows existing '| ' rows
table_end = -1
for i, l in enumerate(lines):
    if l.startswith('| ') and (i > 0) and ('Trial records' in '\n'.join(lines[:i]) or 'Parent session' in '\n'.join(lines[:i])):
        table_end = i
for i, l in enumerate(lines):
    out.append(l)
    if i == table_end and not inserted:
        out.append(line)
        inserted = True
if not inserted:
    # Fall back: append at end
    out.append(line)
with open(path, 'w') as f: f.write('\n'.join(out) + '\n')
PYEOF
}

append_checkpoint() {
  local idx="$1"
  local ts
  ts=$(date -u +%FT%TZ)
  python3 <<PYEOF
path = "$ARTIFACT"
with open(path, 'a') as f:
    f.write(f"\n<!-- progress checkpoint: completed ${idx}/20 at ${ts} -->\n")
PYEOF
}

record_halt() {
  local reason="$1"
  local next_trial="$2"
  local remaining="$3"
  {
    echo ""
    echo "## HALTED early"
    echo ""
    echo "- Halt BEFORE trial: ${next_trial}"
    echo "- Reason: ${reason}"
    echo "- Remaining trials: ${remaining}"
    echo "- Operator action: restart oMLX via Mac UI, then re-dispatch resumption worker"
  } >> "$ARTIFACT"
}

mkdir -p "$(dirname "$RESULTS_APPEND")"
: > "$RESULTS_APPEND"

for spec in "${TRIALS[@]}"; do
  read -r IDX TASK RUN <<< "$spec"

  # Preflight gate before every trial (including oMLX)
  source /tmp/r7.7-env.sh
  PF=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh 2>&1)
  PF_VERDICT=$(echo "$PF" | grep -E "^PREFLIGHT=" | head -1)
  if [[ "$PF_VERDICT" != "PREFLIGHT=PASS" ]]; then
    detail=$(echo "$PF_VERDICT" | grep -oE "detail=[^ ]*" || echo "detail=unknown")
    reason="preflight FAIL before trial ${IDX}: ${PF_VERDICT}"
    echo "$reason" >&2
    remaining=$(printf "T%s-run%s," $(echo "${TRIALS[@]:$((IDX-2))}" | tr ' ' '_' | sed 's/_\+/ /g' | awk '{for(i=1;i<=NF;i+=3) print $(i+1)"-run"$(i+2)}' | tr '\n' ',' | sed 's/,$//'))
    record_halt "$reason" "$IDX" "$remaining"
    touch "$HALT_MARKER"
    exit 0
  fi

  # Per-trial oMLX health check (idempotent with preflight but spec calls it out)
  OMLX_LINE=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1)
  if [[ "$OMLX_LINE" == OMLX_HEALTH=DEGRADED* ]]; then
    reason="oMLX DEGRADED before trial ${IDX}: ${OMLX_LINE}"
    echo "$reason" >&2
    remaining=$(printf "%s," $(for i in $(seq $((IDX-2)) $((${#TRIALS[@]}-1))); do read -r a b c <<< "${TRIALS[$i]}"; echo "${b}-run${c}"; done))
    record_halt "$reason" "$IDX" "$remaining"
    touch "$HALT_MARKER"
    exit 0
  fi

  echo "[$(date -u +%FT%TZ)] Starting trial ${IDX} (${TASK}-run${RUN})"
  REC=$(/tmp/r7.7-S8-prompts/run-trial.sh "$TASK" "$RUN" "$IDX" 2>> "/tmp/r7.7-S8-armF-logs/run-all.err")
  echo "$REC" >> "$RESULTS_APPEND"
  echo "[$(date -u +%FT%TZ)] Trial ${IDX} complete: $REC"

  append_record "$REC"

  # Inline checkpoint every 5 trials
  if (( IDX % CHECKPOINT_INTERVAL == 0 )); then
    append_checkpoint "$IDX"
  fi

  # Post-trial oMLX check → halt on DEGRADED
  POST_OMLX=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1)
  if [[ "$POST_OMLX" == OMLX_HEALTH=DEGRADED* ]]; then
    reason="oMLX DEGRADED after trial ${IDX}: ${POST_OMLX}"
    echo "$reason" >&2
    remaining=$(for i in $(seq $((IDX-1)) $((${#TRIALS[@]}-1))); do read -r a b c <<< "${TRIALS[$i]}"; echo "${b}-run${c}"; done | tr '\n' ',' | sed 's/,$//')
    record_halt "$reason" "$((IDX+1))" "$remaining"
    touch "$HALT_MARKER"
    exit 0
  fi
done

echo "[$(date -u +%FT%TZ)] All trials complete."

# Unstage all variants + final verification
echo "[$(date -u +%FT%TZ)] Beginning end-of-run unstage."
/tmp/r7.7-S8-prompts/unstage-all.sh > /tmp/r7.7-S8-armF-logs/unstage.out 2>&1 || echo "[ERR] unstage failed; see unstage.out"

# Append end-of-run block to artifact
{
  echo ""
  echo "## End-of-run"
  echo ""
  echo "- All trials complete: YES (run-all.sh exited cleanly)"
  UNST_STATUS=$(grep -E "STATE:|RESULT:" /tmp/r7.7-S8-armF-logs/unstage.out 2>/dev/null | grep -E "UNSTAGED|canonical" | wc -l | tr -d ' ')
  echo "- Variants unstaged (count canonical/UNSTAGED): ${UNST_STATUS}/6"
  FINAL_PF=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh 2>&1 | grep -E "^PREFLIGHT=" | head -1 || echo "PREFLIGHT=UNKNOWN")
  FINAL_TRIP=$(/Users/briantaylor/Projects/AgentFW/probe-preflight.sh --skip-omlx --skip-vm-idle 2>&1 | grep -E "^\[GATE: tripwire\]" | head -1 || echo "UNKNOWN")
  echo "- VM canonical / tripwire: ${FINAL_TRIP}"
  FINAL_OMLX=$(/Users/briantaylor/Projects/AgentFW/probe-omlx-health-check.sh 2>&1 | grep -E "^OMLX_HEALTH=" | head -1 || echo "OMLX_HEALTH=UNKNOWN")
  echo "- Final oMLX status: ${FINAL_OMLX}"
  echo "- Residue (.probe-*-orig): see /tmp/r7.7-S8-armF-logs/unstage.out for find results"
  echo ""
  echo "### Run log"
  echo "- run-all.out: /tmp/r7.7-S8-armF-logs/run-all.out"
  echo "- records.tsv: /tmp/r7.7-S8-armF-logs/records.tsv"
  echo "- unstage.out: /tmp/r7.7-S8-armF-logs/unstage.out"
  echo "- per-trial logs: /tmp/r7.7-S8-armF-logs/T{4,5,6,10}-run{1..5}.log"
} >> "$ARTIFACT"
