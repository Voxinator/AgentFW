#!/usr/bin/env bash
# build-matrix.sh — Read outcomes for an arm, discover child sessions, invoke
# judges, and emit aggregate data to /tmp/probe-r7.6-P1C-logs/arm-<arm>-matrix.txt

set -euo pipefail
ARM="${1:?arm A or B required}"
LOGDIR="/tmp/probe-r7.6-P1C-logs"
OUTCOMES="$LOGDIR/arm-${ARM}-outcomes.txt"
MATRIX="$LOGDIR/arm-${ARM}-matrix.txt"
JUDGE="/tmp/probe-r7.6-P1C-logs/judge-trial.py"

: > "$MATRIX"

# Capture tripwire baselines + posts (simple — one shared baseline file per arm)
BASELINE_JSON="$LOGDIR/tripwire-baseline-arm${ARM}.json"
POST_JSON="$LOGDIR/tripwire-post-arm${ARM}.json"

# Parse OUTCOMEs from run-arm.sh output (we already tagged with TRIAL=...)
grep -E "^TRIAL=arm${ARM}" "$OUTCOMES" > "$LOGDIR/arm-${ARM}-trials.raw"

# For each outcome line, extract: task, run, parent_sid, first_attempt_pass
while IFS= read -r line; do
  # line format: TRIAL=armA-T4-run1-g1 OUTCOME run=1 MODEL=... RESULT=COMPLIANT attempts=1 elapsed=33s final_session=ID chain=...
  tag=$(echo "$line" | grep -oE 'TRIAL=[^ ]+' | head -1 | sed 's/TRIAL=//')
  task=$(echo "$tag" | grep -oE 'T[0-9]+' | head -1)
  run=$(echo "$tag" | grep -oE 'run[0-9]+' | head -1 | sed 's/run//')
  parent_sid=$(echo "$line" | grep -oE 'final_session=[^ ]+' | head -1 | sed 's/final_session=//')
  result=$(echo "$line" | grep -oE 'RESULT=[A-Z_]+' | head -1 | sed 's/RESULT=//')
  attempts=$(echo "$line" | grep -oE 'attempts=[0-9]+' | head -1 | sed 's/attempts=//')
  first_attempt_pass=$([[ "$result" == "COMPLIANT" && "$attempts" == "1" ]] && echo "PASS" || echo "FAIL")

  # Discover child session id — the one spawned from parent by delegate_worker_v2
  # Strategy: child session's message[0].content prefix matches parent's v2 call's goal arg
  # Simpler: sessions created between parent session_start and (parent session_start + 5s)
  # with messages[0].role=user and NOT matching the task prompt (matches the goal instead).
  # Use jq to extract parent's v2 goal, then find child whose messages[0].content matches.
  parent_path="/home/parallels/.hermes/sessions/session_${parent_sid}.json"
  child_sid=$(ssh -n ubuntu-vm "python3 <<PYEOF
import json, os, glob
try:
    with open('$parent_path') as f:
        p = json.load(f)
    # Find v2 tool call's goal arg
    goal = None
    for m in p.get('messages', []):
        if m.get('role') != 'assistant':
            continue
        for tc in (m.get('tool_calls') or []):
            fn = tc.get('function') or {}
            if fn.get('name') in ('delegate_worker_v2', 'delegate_worker', 'delegate_task'):
                args = fn.get('arguments') or '{}'
                try:
                    a = json.loads(args) if isinstance(args, str) else args
                    goal = a.get('goal') or ''
                    if goal:
                        break
                except Exception:
                    pass
        if goal:
            break
    if not goal:
        print('NO_GOAL')
    else:
        prefix = goal[:80]
        # Parent's session_id is the filename minus 'session_' and '.json'.
        # Session IDs are 'YYYYMMDD_HHMMSS_<hex>' — lexically sortable AND
        # time-ordered. So: pick children whose filename sorts AFTER parent's.
        parent_sid_local = '$parent_sid'
        parent_fname = 'session_' + parent_sid_local + '.json'
        candidates = []
        for sp in sorted(glob.glob('/home/parallels/.hermes/sessions/session_*.json')):
            sp_base = os.path.basename(sp)
            if sp_base <= parent_fname:
                continue  # older or same
            try:
                with open(sp) as f:
                    c = json.load(f)
                msgs = c.get('messages', [])
                if not msgs:
                    continue
                first = msgs[0]
                if first.get('role') != 'user':
                    continue
                content = first.get('content') or ''
                if isinstance(content, list):
                    content = ''.join(x.get('text','') if isinstance(x,dict) else str(x) for x in content)
                if content[:80] == prefix:
                    sid = sp_base.replace('session_','').replace('.json','')
                    candidates.append(sid)
                    # First match in sorted order IS the closest-in-time.
                    break
            except Exception:
                continue
        if candidates:
            print(candidates[0])
        else:
            print('NOT_FOUND')
except Exception as e:
    print(f'ERROR:{e}')
PYEOF
" 2>/dev/null || echo "ERROR:ssh")

  child_sid=$(echo "$child_sid" | tr -d '\r' | head -1)

  # Record
  echo "TAG=$tag TASK=$task RUN=$run PARENT_SID=$parent_sid CHILD_SID=$child_sid FIRST_ATTEMPT=$first_attempt_pass RESULT=$result ATTEMPTS=$attempts" >> "$MATRIX"
done < "$LOGDIR/arm-${ARM}-trials.raw"

echo "Matrix built: $MATRIX"
wc -l "$MATRIX"
