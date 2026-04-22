#!/usr/bin/env bash
# score.sh — Strict on-disk scoring of all sessions in outcomes.tsv
# Reads /tmp/r7.4-phase-d/outcomes.tsv, fetches each session_id's first tool call,
# writes /tmp/r7.4-phase-d/scored.tsv with columns:
#  task | model_tag | run | result | first_tool | classification | session_id | all_tools_json

set -uo pipefail

OUTCOMES=/tmp/r7.4-phase-d/outcomes.tsv
OUT=/tmp/r7.4-phase-d/scored.tsv
: > "$OUT"
echo -e "task\tmodel_tag\trun\tresult\tfirst_tool\tclassification\tsession_id\tall_tools" >> "$OUT"

while IFS=$'\t' read -r TASK MODEL_TAG RUN RAW; do
  [[ -z "$TASK" ]] && continue
  SID=$(echo "$RAW" | grep -oE 'final_session=[^ ]+' | head -1 | cut -d= -f2)
  RESULT=$(echo "$RAW" | grep -oE 'RESULT=[^ ]+' | head -1 | cut -d= -f2)
  if [[ -z "$SID" || "$SID" == "none" ]]; then
    printf "%s\t%s\t%s\t%s\tNONE\tNONE\t%s\tNONE\n" "$TASK" "$MODEL_TAG" "$RUN" "$RESULT" "${SID:-none}" >> "$OUT"
    continue
  fi
  JQ_OUT=$(ssh ubuntu-vm "jq -c '{ft:(.messages[1].tool_calls//[])[0].function.name, fa:((.messages[1].tool_calls//[])[0].function.arguments|fromjson?//null), all:[.messages[]|select(.role==\"assistant\")|(.tool_calls//[])[].function.name]}' /home/parallels/.hermes/sessions/session_${SID}.json 2>/dev/null" 2>/dev/null || echo '{}')
  FT=$(echo "$JQ_OUT" | jq -r '.ft // "NONE"')
  CLS=$(echo "$JQ_OUT" | jq -r '.fa.classification // "NONE"')
  ALL=$(echo "$JQ_OUT" | jq -c '.all // []')
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$TASK" "$MODEL_TAG" "$RUN" "$RESULT" "$FT" "$CLS" "$SID" "$ALL" >> "$OUT"
done < "$OUTCOMES"

cat "$OUT"
