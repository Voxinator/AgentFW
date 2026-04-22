#!/usr/bin/env bash
# judge-all.sh — Judge all 20 trials of one arm.
# Usage: judge-all.sh <arm>

set -uo pipefail
ARM="${1:?arm A or B}"
LOGDIR="/tmp/probe-r7.6-P1C-logs"
MATRIX="$LOGDIR/arm-${ARM}-matrix.txt"
TW_BASELINE="$LOGDIR/tripwire-baseline-arm${ARM}.json"
TW_POST="$LOGDIR/tripwire-post-arm${ARM}.json"
VERDICTS="$LOGDIR/arm-${ARM}-verdicts.txt"
JUDGE="$LOGDIR/judge-trial.py"

# Build tripwire JSONs from captured data
python3 - <<PYEOF
import re, json, os
path = "$LOGDIR/arm-${ARM}-tripwires.txt"
if not os.path.isfile(path):
    raise SystemExit(f"missing tripwire log: {path}")
text = open(path).read()
# Parse blocks. Baseline = first block; Post = last block.
blocks = re.split(r"===[^=\n]*===", text)
ts = re.findall(r"=== ([^=\n]*) ===", text)
def parse_block(blk):
    out = {}
    for line in blk.strip().split("\n"):
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            md5, p = parts
            if "HERMES.md" in p:
                out["HERMES.md"] = md5
            elif "SKILL.md" in p:
                out["SKILL.md"] = md5
            elif "jira-briefing.sh" in p:
                out["jira-briefing.sh"] = md5
    return out
# blocks[0] is pre-first-tag, blocks[1] = first block, blocks[-1] = last
baseline = parse_block(blocks[1]) if len(blocks) >= 2 else {}
post = parse_block(blocks[-1]) if len(blocks) >= 2 else {}
with open("$TW_BASELINE", "w") as f:
    json.dump(baseline, f)
with open("$TW_POST", "w") as f:
    json.dump(post, f)
print(f"  baseline: {baseline}")
print(f"  post: {post}")
PYEOF

: > "$VERDICTS"

judged=0
while IFS= read -r line; do
  tag=$(echo "$line" | grep -oE 'TAG=[^ ]+' | sed 's/TAG=//')
  task=$(echo "$line" | grep -oE 'TASK=[^ ]+' | sed 's/TASK=//')
  run=$(echo "$line" | grep -oE 'RUN=[^ ]+' | sed 's/RUN=//')
  parent_sid=$(echo "$line" | grep -oE 'PARENT_SID=[^ ]+' | sed 's/PARENT_SID=//')
  child_sid=$(echo "$line" | grep -oE 'CHILD_SID=[^ ]+' | sed 's/CHILD_SID=//')
  first_attempt=$(echo "$line" | grep -oE 'FIRST_ATTEMPT=[^ ]+' | sed 's/FIRST_ATTEMPT=//')

  judged=$((judged + 1))
  stdout_file="$LOGDIR/arm-${ARM}-trial-${judged}-judge.stdout.txt"
  python3 "$JUDGE" "$ARM" "$task" "$run" "$parent_sid" "$child_sid" "$TW_BASELINE" "$TW_POST" </dev/null > "$stdout_file" 2>&1 || true
  verdict=$(head -1 "$stdout_file" | grep -oE 'WORKER_QUALITY=[A-Z]+' | head -1)
  echo "TAG=$tag ${verdict:-WORKER_QUALITY=UNKNOWN} FIRST_ATTEMPT=$first_attempt" >> "$VERDICTS"
done < "$MATRIX"

echo ""
echo "Judged $judged trials for arm $ARM. Verdicts: $VERDICTS"
echo ""
echo "Aggregate:"
awk '{for(i=1;i<=NF;i++){if($i ~ /^WORKER_QUALITY=/){v=$i; sub("WORKER_QUALITY=","",v); counts[v]++}}} END {for(v in counts) printf "  %s: %d\n", v, counts[v]}' "$VERDICTS"
echo ""
awk '{for(i=1;i<=NF;i++){if($i ~ /^FIRST_ATTEMPT=/){v=$i; sub("FIRST_ATTEMPT=","",v); counts[v]++}}} END {for(v in counts) printf "  FIRST_ATTEMPT=%s: %d\n", v, counts[v]}' "$VERDICTS"
