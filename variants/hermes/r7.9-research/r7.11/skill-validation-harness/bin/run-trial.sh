#!/usr/bin/env bash
# run-trial.sh — drive one Hermes/skill trial against a fresh scaffold,
# archive the result in r7.11 item-9 shape.
#
# Usage:
#   run-trial.sh --trial N \
#                [--track A|B-2a|B-2b-orch|B-2b-subproc|B-2c] \
#                [--baseline-tar PATH] \
#                [--timeout SECONDS] [--dry-run] [--prior-medians PATH]
#
# USER-PROMPT.md and verify-config.json are restored from the canonical
# baseline tar (default: ~/Downloads/scaffold-baseline.tar.gz). Track A
# uses /tmp/r7.11-item8-scaffold as the work dir to match USER-PROMPT.md
# exactly (which references that path). Post-trial state is archived into
# archives/trial-${TRACK}-${TRIAL}/scaffold-work/.
#
# Per Brian (2026-05-03):
#   - Launch method: hermes chat -q via launch-q.py (matches r7.11 item 9)
#   - Halt-and-flag: trial-1 always halts for operator review;
#     trials 2-5 halt-on-anomaly with concrete checks
#   - Wallclock default 5400s (90 min) for trial 1
#   - reset.sh strips PLAN.md unless --keep-plan; Track A lets the
#     orchestrator author its own per skill PHASE 0.
#   - B-2b-subproc passes --keep-plan via reset (uses bootstrap-authored PLAN).
#
# --dry-run: skips the LLM launch entirely, runs everything else
# (reset, manifest, archive empty trajectory, score empty scaffold,
# adherence on empty session) to validate harness pipeline cheaply.

set -euo pipefail

TRIAL=""
TRACK="A"
TIMEOUT_SECONDS=5400
DRY_RUN=0
PRIOR_MEDIANS=""
ORCHESTRATOR_PROMPT_TEMPLATE='Run r7.11 against {scaffold_root}.'
BASELINE_TAR="$HOME/Downloads/scaffold-baseline.tar.gz"
WORK_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --trial) TRIAL="$2"; shift 2;;
    --track) TRACK="$2"; shift 2;;
    --timeout) TIMEOUT_SECONDS="$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    --prior-medians) PRIOR_MEDIANS="$2"; shift 2;;
    --orchestrator-prompt) ORCHESTRATOR_PROMPT_TEMPLATE="$2"; shift 2;;
    --baseline-tar) BASELINE_TAR="$2"; shift 2;;
    --work-dir) WORK_OVERRIDE="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

[[ -z "$TRIAL" ]] && { echo "usage: $0 --trial N [--track A|B-2a|...]" >&2; exit 2; }

HARNESS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_ROOT="$HARNESS/archives/trial-${TRACK}-${TRIAL}"
# Work dir = the scaffold path the orchestrator interacts with. Track A
# pins it to /tmp/r7.11-item8-scaffold so USER-PROMPT.md's hardcoded path
# matches reality. Override per call with --work-dir.
WORK="${WORK_OVERRIDE:-/tmp/r7.11-item8-scaffold}"
LOG="$ARCHIVE_ROOT/tui.log"
MANIFEST="$ARCHIVE_ROOT/manifest.json"
SCORE_OUT="$ARCHIVE_ROOT/score.json"
ADHERENCE_OUT="$ARCHIVE_ROOT/adherence.json"
SKILL_DIR="$HOME/.hermes/skills/autonomous-ai-agents/r7-11-orchestrate"
CONTENT_VERIFY="$(cd "$HARNESS/.." && pwd)/content_verify.py"
HERMES_AGENT_DIR="$HOME/Life-AI/hermes-agent"
AGENTFW_DIR="$HOME/Life-AI/AgentFW"

mkdir -p "$ARCHIVE_ROOT"

# --- 1. reset scaffold from canonical tar -----------------------------------
# Track A and B-2b-subproc both start with NO PLAN.md (Track A's orchestrator
# authors via PHASE 0; B-2b-subproc has bootstrap-child author it in step 1.5
# below). B-2b-orch is the same as Track A (covered by trials A-{1..5}).
RESET_FLAGS=("$WORK" "--baseline-tar" "$BASELINE_TAR")
echo "[run-trial] reset ${WORK} (track=${TRACK}) ..."
"$HARNESS/bin/reset.sh" "${RESET_FLAGS[@]}"

# --- 2. apply Track-B overlays (broken impls, pre-staged PLAN, etc) ---------
sha() { shasum -a 256 "$1" | awk '{print $1}'; }

case "$TRACK" in
  B-2a)
    OVERLAY="$HARNESS/track-b-scaffolds/2a-content-type/overlay"
    if [[ -d "$OVERLAY" ]]; then
      echo "[run-trial] applying 2a overlay (broken /api/export.json + weak tests + pre-staged PLAN.md)"
      cp -R "$OVERLAY"/. "$WORK/"
      pre_staged_sha=$(sha "$WORK/src/api/export.py")
      echo "[run-trial] pre_staged_sha src/api/export.py = $pre_staged_sha"
    fi
    ;;
  B-2b-orch|B-2b-subproc)
    OVERLAY="$HARNESS/track-b-scaffolds/2b-bootstrap-child/overlay"
    [[ -d "$OVERLAY" ]] && cp -R "$OVERLAY"/. "$WORK/"
    ;;
esac

# --- 2.5. B-2b-subproc: bootstrap-child authors PLAN.md ---------------------
if [[ "$TRACK" == "B-2b-subproc" && "$DRY_RUN" != "1" ]]; then
  echo "[run-trial] bootstrap-plan (subprocess hermes session, no skill) ..."
  set +e
  python3 "$HARNESS/bin/bootstrap-plan.py" \
    --scaffold-root "$WORK" \
    --log "$LOG" \
    --timeout-seconds 300 \
    --hermes-bin "${HERMES_BIN:-$HOME/Life-AI/hermes-agent/venv/bin/hermes}" \
    --model "${MODEL:-gemma-4-26b-a4b-it-8bit}"
  bootstrap_ec=$?
  set -e
  if [[ "$bootstrap_ec" != "0" ]]; then
    echo "[run-trial] HALT: bootstrap-plan failed (ec=$bootstrap_ec); cannot run skill arm without PLAN.md"
    echo "  inspect $LOG for bootstrap session output"
    exit "$bootstrap_ec"
  fi
  bootstrap_plan_sha=$(sha "$WORK/PLAN.md")
  echo "[run-trial] bootstrap-authored PLAN.md sha=$bootstrap_plan_sha"
fi

# --- 3. seed manifest --------------------------------------------------------
agentfw_commit=$(cd "$AGENTFW_DIR" && git rev-parse HEAD 2>/dev/null || echo "unknown")
agentfw_branch=$(cd "$AGENTFW_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
python_version=$("$WORK/.venv/bin/python" --version 2>&1 | awk '{print $2}')
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
started_epoch=$(date +%s)
USER_PROMPT_PATH="$WORK/USER-PROMPT.md"
VERIFY_CONFIG_PATH="$WORK/verify-config.json"

python3 - "$MANIFEST" "$HARNESS/manifest-template.json" \
  "$TRACK" "trial-${TRIAL}" "$started" "$WORK" \
  "$SKILL_DIR" "$(sha "$SKILL_DIR/SKILL.md")" \
  "$HERMES_AGENT_DIR" "$agentfw_branch" "$agentfw_commit" \
  "$python_version" \
  "$CONTENT_VERIFY" "$(sha "$CONTENT_VERIFY")" \
  "$USER_PROMPT_PATH" "$(sha "$USER_PROMPT_PATH")" "$VERIFY_CONFIG_PATH" \
  "$BASELINE_TAR" "$(sha "$BASELINE_TAR")" <<'PYTHON'
import json, sys
out, tmpl, *vals = sys.argv[1:]
keys = ["TRACK_PLACEHOLDER","TRIAL_ID_PLACEHOLDER","ISO8601_PLACEHOLDER",
        "WORK_DIR_PLACEHOLDER","SKILL_PATH_PLACEHOLDER","SKILL_SHA_PLACEHOLDER",
        "HERMES_AGENT_PLACEHOLDER","AGENTFW_BRANCH_PLACEHOLDER","AGENTFW_COMMIT_PLACEHOLDER",
        "PYTHON_VERSION_PLACEHOLDER","CONTENT_VERIFY_PATH_PLACEHOLDER",
        "CONTENT_VERIFY_SHA_PLACEHOLDER","USER_PROMPT_PATH_PLACEHOLDER",
        "USER_PROMPT_SHA_PLACEHOLDER","VERIFY_CONFIG_PATH_PLACEHOLDER",
        "BASELINE_TAR_PLACEHOLDER","BASELINE_TAR_SHA_PLACEHOLDER"]
text = open(tmpl).read()
for k, v in zip(keys, vals):
    text = text.replace(k, v)
text = text.replace("BASELINE_REV_PLACEHOLDER", "Brian's scaffold-baseline.tar.gz")
open(out, "w").write(text)
PYTHON

# --- 4. launch ---------------------------------------------------------------
# Method: hermes chat -q (matches hermes_multi.py:354's launch shape used at
# r7.11 item 9 — apples-to-apples with REPORT-r7.11-item9-n5.md scoring).
# launch-tui.py stays in bin/ as fallback if pure-TUI replay is ever wanted.
sessions_before=$(ls -1t "$HOME/.hermes/sessions"/session_*.json 2>/dev/null | head -1 || echo "")
# For B-2b-subproc, override the orchestrator prompt to tell the skill that
# PLAN.md is already authored — start from PHASE LOOP step 1, don't call
# write_plan_md. (Pre-flight 2b confirmed the skill silently overwrites
# pre-staged PLAN.md without explicit guidance — outcome (c).)
if [[ "$TRACK" == "B-2b-subproc" ]]; then
  ORCHESTRATOR_PROMPT_TEMPLATE='Run r7.11 against {scaffold_root}. PLAN.md already exists at {scaffold_root}/PLAN.md and was authored by a prior session. Read it and start from PHASE LOOP step 1. Do NOT call write_plan_md or write_file to author or modify PLAN.md.'
fi

# Tier-4 probe (Brian's r7.12 design test): adds a whole-scaffold content_verify
# gate at PHASE FINAL. Tests whether the orchestrator can recover from
# cross-phase wiring findings or just escalates against the new gate.
# Operator-prompt override only — no SKILL.md modifications.
if [[ "$TRACK" == "A-tier4" ]]; then
  ORCHESTRATOR_PROMPT_TEMPLATE="Run r7.11 against {scaffold_root}.

ADDITIONAL REQUIREMENT — TIER-4 PHASE FINAL GATE:

After every phase in PLAN.md has reached verified_passed in verified-state.json, you MUST run a whole-scaffold tier-4 check BEFORE emitting r7.11 SUCCESS:

1. Invoke via terminal tool: python3 ${CONTENT_VERIFY} {scaffold_root} --json
2. If the script exits 0 (no HIGH findings), emit r7.11 SUCCESS as usual.
3. If the script exits 1, parse its JSON stdout — the 'findings' array contains HIGH-severity cross-file wiring issues that per-phase verify_phase did not catch. For each such finding, dispatch ONE corrective worker via delegate_task with the finding details as context. After the worker completes, re-run verify_phase on the affected phase, then re-run the tier-4 check.
4. Maximum 3 tier-4 revision rounds. If still failing, emit r7.11 ESCALATE with the unresolved tier-4 findings."
  MAX_TURNS="${MAX_TURNS_OVERRIDE:-60}"
fi

prompt_text="${ORCHESTRATOR_PROMPT_TEMPLATE//\{scaffold_root\}/$WORK}"
HERMES_BIN="${HERMES_BIN:-$HOME/Life-AI/hermes-agent/venv/bin/hermes}"
MODEL="${MODEL:-gemma-4-26b-a4b-it-8bit}"
MAX_TURNS="${MAX_TURNS:-40}"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[run-trial] DRY RUN — skipping hermes chat"
  {
    echo "=== run-trial dry-run ==="
    echo "would launch: $HERMES_BIN chat -q '$prompt_text' -s r7-11-orchestrate -m $MODEL --max-turns $MAX_TURNS"
  } > "$LOG"
  launch_ec=0
else
  echo "[run-trial] launch-q (timeout ${TIMEOUT_SECONDS}s, model=$MODEL, max-turns=$MAX_TURNS) ..."
  set +e
  python3 "$HARNESS/bin/launch-q.py" \
    --scaffold-root "$WORK" \
    --prompt "$prompt_text" \
    --log "$LOG" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --hermes-bin "$HERMES_BIN" \
    --model "$MODEL" \
    --max-turns "$MAX_TURNS"
  launch_ec=$?
  set -e
  if [[ "$launch_ec" == "124" ]]; then
    echo "[run-trial] HALT: hermes chat -q exceeded ${TIMEOUT_SECONDS}s wall-clock"
  fi
fi

ended_epoch=$(date +%s)
wallclock=$((ended_epoch - started_epoch))

# --- 5. archive ------------------------------------------------------------
echo "[run-trial] archive ..."

# 2a-specific: did the worker preserve the broken impl byte-for-byte?
if [[ "$TRACK" == "B-2a" && -f "$WORK/src/api/export.py" ]]; then
  final_sha=$(sha "$WORK/src/api/export.py")
  if [[ -n "${pre_staged_sha:-}" && "$pre_staged_sha" != "$final_sha" ]]; then
    echo "[run-trial] WORKER-CONTEXT-FAILURE: src/api/export.py modified during trial"
    echo "  pre_staged_sha=$pre_staged_sha"
    echo "  final_sha=$final_sha"
    worker_context_failure=true
  else
    worker_context_failure=false
  fi
fi

tar -cf "$ARCHIVE_ROOT/scaffold.tar" -C "$WORK" . 2>/dev/null || true

# Also archive a directory copy for human inspection (per Brian's archive shape:
# scaffold tar + .session-archive/ + verified-state.json + manifest.json + log).
mkdir -p "$ARCHIVE_ROOT/scaffold-work"
rsync -a --exclude='.venv/' "$WORK/" "$ARCHIVE_ROOT/scaffold-work/" 2>/dev/null || \
  cp -R "$WORK/" "$ARCHIVE_ROOT/scaffold-work/"

session_json=""
if [[ "$DRY_RUN" != "1" ]]; then
  # Pick the ORCHESTRATOR session, not the latest worker. Orchestrator's
  # first user message starts with "Run r7.11"; workers' first messages are
  # the "Implement phase N" / "Revise phase N" delegate-task prompts.
  # ls -1tr is oldest-first; we want the first orchestrator-shaped session
  # newer than the manifest.
  orch=""
  for s in $(find "$HOME/.hermes/sessions" -name "session_*.json" -newer "$MANIFEST" 2>/dev/null | sort); do
    if python3 -c "
import json, sys
try:
    d = json.load(open('$s'))
    msgs = d.get('messages', [])
    sys.exit(0 if msgs and (msgs[0].get('content') or '').startswith('Run r7.11') else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
      orch="$s"
      break
    fi
  done
  if [[ -n "$orch" ]]; then
    cp "$orch" "$ARCHIVE_ROOT/session.json"
    session_json="$ARCHIVE_ROOT/session.json"
  fi
fi

cp "$WORK/verified-state.json" "$ARCHIVE_ROOT/verified-state.json" 2>/dev/null || \
  echo '{}' > "$ARCHIVE_ROOT/verified-state.json"

# --- 6. score --------------------------------------------------------------
echo "[run-trial] score ..."
score_ec=0
set +e
"$HARNESS/bin/score.sh" "$WORK" > "$SCORE_OUT" 2>"$ARCHIVE_ROOT/score.stderr"
score_ec=$?
set -e

# --- 7. adherence ----------------------------------------------------------
adherence_ec=0
if [[ -n "$session_json" && -f "$session_json" ]]; then
  echo "[run-trial] adherence ..."
  set +e
  python3 "$HARNESS/bin/adherence.py" \
    --session "$session_json" \
    --verified-state "$ARCHIVE_ROOT/verified-state.json" \
    > "$ADHERENCE_OUT" 2>"$ARCHIVE_ROOT/adherence.stderr"
  adherence_ec=$?
  set -e
else
  echo '{"note": "no session.json captured (dry-run or session-archive miss)"}' > "$ADHERENCE_OUT"
fi

# --- 8. finalize manifest --------------------------------------------------
ended=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - "$MANIFEST" "$ended" "$wallclock" "$launch_ec" "$score_ec" "$adherence_ec" "$SCORE_OUT" \
  "${pre_staged_sha:-}" "${final_sha:-}" "${worker_context_failure:-}" "$TRACK" <<'PYTHON'
import json, sys, os
m_path, ended, wc, lec, sec, aec, score_path, pre_sha, fin_sha, wcf, track = sys.argv[1:]
m = json.load(open(m_path))
m["ended_at"] = ended
m["outcome"]["wallclock_seconds"] = int(wc)
m["outcome"]["launch_exit_code"] = int(lec)
m["outcome"]["score_exit_code"] = int(sec)
m["outcome"]["adherence_exit_code"] = int(aec)
if os.path.exists(score_path):
    try:
        s = json.load(open(score_path))
        m["outcome"]["verifier_strict"] = bool(s.get("strict_passed"))
        m["outcome"]["verifier_charitable"] = bool(s.get("charitable_passed"))
    except Exception:
        pass
if track == "B-2a":
    m["outcome"]["pre_staged_sha256"] = pre_sha or None
    m["outcome"]["final_sha256"] = fin_sha or None
    m["outcome"]["worker_context_failure"] = (wcf == "true")
json.dump(m, open(m_path, "w"), indent=2)
PYTHON

# --- 9. halt-and-flag policy -----------------------------------------------
echo
echo "=========================================="
echo "[run-trial] trial ${TRACK}-${TRIAL} complete in ${wallclock}s"
echo "  launch_ec=$launch_ec  score_ec=$score_ec  adherence_ec=$adherence_ec"
echo "  archive: $ARCHIVE_ROOT"
echo "=========================================="

# Trial 1 always halts for operator review (Brian's policy).
if [[ "$TRIAL" == "1" ]]; then
  echo
  echo "HALT: trial 1 complete — operator review required before trials 2-5."
  echo "  inspect $SCORE_OUT, $ADHERENCE_OUT, $LOG, $MANIFEST"
  echo "  then re-run trial 2 with --prior-medians <path-to-aggregate-from-trial-1>"
  exit 0
fi

# Trials 2-5: halt-on-anomaly per Brian's checklist.
halt_reason=""
if [[ "$score_ec" != "0" && "$score_ec" != "1" ]]; then
  halt_reason="score script crashed (ec=$score_ec)"
fi
if [[ -n "$PRIOR_MEDIANS" && -f "$PRIOR_MEDIANS" ]]; then
  median=$(python3 -c "import json; print(int(json.load(open('$PRIOR_MEDIANS'))['median_wallclock_seconds']))" 2>/dev/null || echo 0)
  if [[ "$median" -gt 0 ]] && (( wallclock > median * 2 )); then
    halt_reason="wallclock $wallclock > 2× prior-median $median (degeneracy)"
  fi
fi
if [[ -f "$ARCHIVE_ROOT/score.stderr" && -s "$ARCHIVE_ROOT/score.stderr" ]]; then
  if grep -qiE "Traceback|Error" "$ARCHIVE_ROOT/score.stderr"; then
    halt_reason="verifier raised exception instead of returning verdict"
  fi
fi

if [[ -n "$halt_reason" ]]; then
  python3 -c "
import json, sys
m = json.load(open('$MANIFEST'))
m['outcome']['halt_reason'] = '$halt_reason'
json.dump(m, open('$MANIFEST', 'w'), indent=2)
"
  echo
  echo "HALT-ON-ANOMALY: $halt_reason"
  echo "  recorded in manifest; investigate before next trial."
  exit 1
fi

if [[ "$TRIAL" =~ ^[0-9]+$ ]]; then
  echo "[run-trial] no anomaly detected; safe to continue to trial $((TRIAL+1))."
else
  echo "[run-trial] no anomaly detected (non-numeric trial id: $TRIAL)."
fi
exit 0
