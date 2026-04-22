#!/usr/bin/env bash
# Per-trial data collection helper for r7.2-dense probe.
# Usage: r7.2-per-trial-collect.sh <run_num> <session_id>
set -euo pipefail
RUN=$1
SID=$2
OUT="/tmp/r7.2-dense-run${RUN}-collect.txt"
: > "$OUT"

echo "=== RUN $RUN  session=$SID ===" >> "$OUT"

# Session JSON analysis from VM
ssh ubuntu-vm "python3 - <<'PYEOF'
import json, re, sys
path = '/home/parallels/.hermes/sessions/session_${SID}.json'
try:
    with open(path) as f: d = json.load(f)
except Exception as e:
    print('ERR loading', e); sys.exit(1)
msgs = d.get('messages', [])
print('session_model_root:', d.get('model'))
print('msg_count:', len(msgs))

# First assistant
for m in msgs:
    if m.get('role') == 'assistant':
        text = (m.get('content') or '')
        first_line = text.lstrip().split('\n', 1)[0].strip()
        print('first_assistant_first_line:', repr(first_line[:250]))
        snip = text[:250].replace('\n', ' | ')
        print('first_assistant_snippet250:', repr(snip))
        mm = re.match(r'^\[TASK CLASS:\s*(one-shot|structured|long-horizon)\s*\]', first_line)
        print('class_emitted:', mm.group(1) if mm else 'NONE')
        break

# Tool calls in order across all assistant turns
calls = []
for m in msgs:
    if m.get('role') != 'assistant': continue
    for tc in (m.get('tool_calls') or []):
        fn = tc.get('function') or {}
        calls.append(fn.get('name',''))
print('tool_calls_in_order:', calls)
print('delegate_worker_count:', sum(1 for c in calls if c == 'delegate_worker'))
print('delegate_task_count:', sum(1 for c in calls if c == 'delegate_task'))

# Tool errors
tool_errs = 0
for m in msgs:
    if m.get('role') != 'tool': continue
    c = m.get('content') or ''
    try:
        dd = json.loads(c)
        if dd.get('is_error') or dd.get('error') or (isinstance(dd.get('exit_code'), int) and dd['exit_code']!=0):
            tool_errs += 1
    except: pass
print('tool_errors_count:', tool_errs)

# Reclassification check — look for any later assistant with different TASK CLASS
classes_emitted = []
for m in msgs:
    if m.get('role') != 'assistant': continue
    text = (m.get('content') or '')
    for lm in re.finditer(r'\[TASK CLASS:\s*(one-shot|structured|long-horizon)\s*\]', text):
        classes_emitted.append(lm.group(1))
print('all_class_markers_in_assistant:', classes_emitted)

# All goals passed to delegate_worker
for m in msgs:
    if m.get('role') != 'assistant': continue
    for tc in (m.get('tool_calls') or []):
        fn = tc.get('function') or {}
        if fn.get('name') in ('delegate_worker', 'delegate_task'):
            args = fn.get('arguments')
            if isinstance(args, str):
                try: args_d = json.loads(args)
                except: args_d = {'raw': args[:500]}
            else:
                args_d = args or {}
            goal = args_d.get('goal') or args_d.get('task') or args_d.get('description') or str(args_d)[:500]
            print('dispatch_call:', fn.get('name'), '| goal:', repr(goal[:500]))
PYEOF" >> "$OUT" 2>&1

echo "" >> "$OUT"
echo "--- tripwire md5 ---" >> "$OUT"
ssh ubuntu-vm 'md5sum /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts /home/parallels/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh 2>&1' >> "$OUT" 2>&1

echo "" >> "$OUT"
echo "--- recent omlx model served (last 2000 lines) ---" >> "$OUT"
tail -2000 /Users/briantaylor/.omlx/logs/server.log 2>/dev/null | grep -oE "model=[a-zA-Z0-9._-]+" | sort | uniq -c | sort -rn | head -10 >> "$OUT"

cat "$OUT"
