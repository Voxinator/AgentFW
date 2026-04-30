#!/usr/bin/env bash
# smoke-r7.11.sh — Single-trial smoke harness for r7.11.
#
# Pre-condition: probe-r7.11-stage.sh stage was run successfully and is
# currently active.
#
# What this does:
#   1. Builds a minimal /tmp/r7.11-smoke-scaffold/ on the VM (PLAN.md +
#      src/foo.py + verify-config.json). Real, parseable Python — NOT stubs.
#   2. Source OMLX_API_KEY from local env (operator's local-dev key).
#   3. Launches `hermes chat` with a prompt asking the parent to call
#      verify_phase + end_session_for_handoff.
#   4. Captures stdout, stderr, the session JSON, and the sentinel +
#      verified-state.json that the tools should have written.
#   5. Writes a single structured report at /tmp/r7.11-smoke-report.md.
#
# This script does NOT make halt-or-unstage decisions. The report is the
# operator's input. The script exits 0 if Hermes ran (regardless of
# verification verdict). It only fails if Hermes itself didn't launch or the
# report couldn't be written.

set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-ubuntu-vm}"
R_AGENT="${R_AGENT:-.hermes/hermes-agent}"  # $HOME-relative path to Hermes on VM
SCAFFOLD="/tmp/r7.11-smoke-scaffold"
REPORT="/tmp/r7.11-smoke-report.md"
STDOUT_LOG="/tmp/r7.11-smoke-stdout.txt"
STDERR_LOG="/tmp/r7.11-smoke-stderr.txt"
SESSION_LOG="/tmp/r7.11-smoke-session.json"
SENTINEL_PATH="${SCAFFOLD}/.session-end-signal.json"
ESCALATE_PATH="${SCAFFOLD}/.session-escalate-signal.json"
VSTATE_PATH="${SCAFFOLD}/verified-state.json"

# The toolset choice: hermes-cli is the right one because the stage script
# adds the three new names to _HERMES_CORE_TOOLS, which is the underlying
# list referenced by hermes-cli. (Verified by inspecting toolsets.py during
# tool-loader investigation: line ~265 in canonical toolsets.py.)
TOOLSET="hermes-cli"
MODEL="gemma-4-26B-A4B-it-MLX-8bit"
SOURCE_TAG="r7.11-smoke"
HARD_TIMEOUT_S=300

PROMPT='Call verify_phase for phase 1 on /tmp/r7.11-smoke-scaffold (scaffold_root=/tmp/r7.11-smoke-scaffold), then call end_session_for_handoff with completed_phase=1 and scaffold_root=/tmp/r7.11-smoke-scaffold.'

log() { echo "[smoke-r7.11] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

# Source OMLX_API_KEY — accept either the standard location or env var.
if [[ -z "${OMLX_API_KEY:-}" ]]; then
  if [[ -f "$HOME/.hermes-omlx-key" ]]; then
    # shellcheck disable=SC1091
    source "$HOME/.hermes-omlx-key"
  fi
fi
if [[ -z "${OMLX_API_KEY:-}" ]]; then
  die "OMLX_API_KEY not set in environment and ~/.hermes-omlx-key not found. Export OMLX_API_KEY before running this script."
fi

# --- Phase A: build scaffold on VM ---
log "Phase A: build smoke scaffold at ${SCAFFOLD} on ${REMOTE_HOST}"

ssh "$REMOTE_HOST" "rm -rf ${SCAFFOLD} && mkdir -p ${SCAFFOLD}/src"

ssh "$REMOTE_HOST" "cat > ${SCAFFOLD}/PLAN.md" <<'PLAN_EOF'
# Smoke test scaffold

## Phase 1: Trivial implementation
Objective: define and use one symbol
Paths: src/foo.py
Acceptance Criteria: `foo()` is defined and called.
Size estimate: small
PLAN_EOF

ssh "$REMOTE_HOST" "cat > ${SCAFFOLD}/src/foo.py" <<'FOO_EOF'
"""Trivial single-symbol module for r7.11 smoke trial."""


def foo():
    return "hello"


result = foo()
print(result)
FOO_EOF

ssh "$REMOTE_HOST" "cat > ${SCAFFOLD}/verify-config.json" <<'CFG_EOF'
{"schema_version": "1.0", "verify_phase": {}}
CFG_EOF

log "Phase A: scaffold layout:"
ssh "$REMOTE_HOST" "ls -la ${SCAFFOLD} && echo '---PLAN.md---' && cat ${SCAFFOLD}/PLAN.md && echo '---foo.py---' && cat ${SCAFFOLD}/src/foo.py && echo '---verify-config.json---' && cat ${SCAFFOLD}/verify-config.json"

# --- Phase B: launch Hermes with a hard timeout ---
log "Phase B: launch hermes chat (timeout ${HARD_TIMEOUT_S}s, model ${MODEL}, toolset ${TOOLSET})"

local_start=$(date +%s)
set +e
ssh "$REMOTE_HOST" "cd ~/${R_AGENT} && OMLX_API_KEY='${OMLX_API_KEY}' timeout ${HARD_TIMEOUT_S} ./venv/bin/hermes chat \
  -m ${MODEL} \
  -Q \
  --max-turns 15 \
  -t ${TOOLSET} \
  --source ${SOURCE_TAG} \
  -q '${PROMPT//\'/\'\\\'\'}' \
  > ${STDOUT_LOG} 2> ${STDERR_LOG}"
hermes_exit=$?
set -e
local_end=$(date +%s)
wall_secs=$((local_end - local_start))

log "Phase B: hermes exit=${hermes_exit}, wall=${wall_secs}s"

# --- Phase C: capture session JSON ---
log "Phase C: locate + copy session JSON for source-tag ${SOURCE_TAG}"

# Find the most recent session JSON whose `source` field is r7.11-smoke.
# The Hermes session files live at ~/.hermes/sessions/session_*.json.
ssh "$REMOTE_HOST" "
  python3 - <<'PYEOF'
import json, os, glob, time, shutil
sessions_dir = os.path.expanduser('~/.hermes/sessions')

# Primary: source-field lookup. Works only if Hermes' SQLite session DB
# is populating the `source` field into session JSONs (broken since
# 2026-04-25 per r7.x-followups F-1; works prior to that regression).
src_candidates = []
for path in glob.glob(os.path.join(sessions_dir, 'session_*.json')):
    try:
        with open(path) as f:
            data = json.load(f)
        if data.get('source') == '${SOURCE_TAG}':
            src_candidates.append((os.path.getmtime(path), path))
    except Exception:
        continue

# Fallback: mtime within the last 10 minutes. Covers the smoke trial
# wall-clock window. F-1 workaround until SessionDB writes are restored.
mtime_candidates = []
if not src_candidates:
    cutoff = time.time() - 600  # 10 minutes
    for path in glob.glob(os.path.join(sessions_dir, 'session_*.json')):
        mtime = os.path.getmtime(path)
        if mtime >= cutoff:
            mtime_candidates.append((mtime, path))

if src_candidates:
    src_candidates.sort(reverse=True)
    src = src_candidates[0][1]
    shutil.copy(src, '${SESSION_LOG}')
    print(f'COPIED {src} -> ${SESSION_LOG} (via source-tag)')
elif mtime_candidates:
    mtime_candidates.sort(reverse=True)
    src = mtime_candidates[0][1]
    shutil.copy(src, '${SESSION_LOG}')
    print(f'COPIED {src} -> ${SESSION_LOG} (via mtime fallback; F-1)')
else:
    print('NO_SESSION_FOUND')
PYEOF
"

# --- Phase D: snapshot scaffold final state + sentinels ---
log "Phase D: capture sentinels + verified-state.json"
have_end_sentinel=$(ssh "$REMOTE_HOST" "[ -f ${SENTINEL_PATH} ] && echo yes || echo no")
have_escalate_sentinel=$(ssh "$REMOTE_HOST" "[ -f ${ESCALATE_PATH} ] && echo yes || echo no")
have_vstate=$(ssh "$REMOTE_HOST" "[ -f ${VSTATE_PATH} ] && echo yes || echo no")
# Compose summary: which sentinel(s) fired
if [[ "$have_end_sentinel" == "yes" && "$have_escalate_sentinel" == "yes" ]]; then
  sentinel_summary="both (end + escalate) — anomaly; parent should produce one OR the other"
elif [[ "$have_end_sentinel" == "yes" ]]; then
  sentinel_summary="end-signal only"
elif [[ "$have_escalate_sentinel" == "yes" ]]; then
  sentinel_summary="escalate-signal only"
else
  sentinel_summary="neither — parent did not call end_session_for_handoff or escalate_to_operator"
fi

# Tool registration error scan
tool_errors=$(ssh "$REMOTE_HOST" "grep -i 'tool.*load.*error\|cannot.*import.*tools\|r7_11_lib' ${STDERR_LOG} 2>/dev/null | head -50 || true")

# --- Phase E: write structured report ---
log "Phase E: write report at ${REPORT}"

ssh "$REMOTE_HOST" "bash -s" <<REMOTE_REPORT
set -e
cat > ${REPORT} <<'REPORT_EOF'
# r7.11 smoke trial report

REPORT_EOF

cat >> ${REPORT} <<EOM

## Run summary
- Source tag: ${SOURCE_TAG}
- Model: ${MODEL}
- Toolset: ${TOOLSET}
- Hermes exit code: ${hermes_exit}
- Wall-clock: ${wall_secs}s
- Hard timeout: ${HARD_TIMEOUT_S}s
- End-session sentinel present: ${have_end_sentinel}
- Escalate sentinel present: ${have_escalate_sentinel}
- Sentinel summary: ${sentinel_summary}
- verified-state.json present: ${have_vstate}

## Stdout (full)
EOM
echo '\`\`\`' >> ${REPORT}
cat ${STDOUT_LOG} >> ${REPORT} 2>/dev/null || echo '(stdout file missing)' >> ${REPORT}
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## Stderr (full)
EOM
echo '\`\`\`' >> ${REPORT}
cat ${STDERR_LOG} >> ${REPORT} 2>/dev/null || echo '(stderr file missing)' >> ${REPORT}
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## Session-end sentinel (.session-end-signal.json)
EOM
echo '\`\`\`json' >> ${REPORT}
if [ -f ${SENTINEL_PATH} ]; then
  cat ${SENTINEL_PATH} >> ${REPORT}
else
  echo '(absent — end_session_for_handoff did not fire)' >> ${REPORT}
fi
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## Escalate sentinel (.session-escalate-signal.json)
EOM
echo '\`\`\`json' >> ${REPORT}
if [ -f ${ESCALATE_PATH} ]; then
  cat ${ESCALATE_PATH} >> ${REPORT}
else
  echo '(absent — escalate_to_operator did not fire)' >> ${REPORT}
fi
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## verified-state.json
EOM
echo '\`\`\`json' >> ${REPORT}
if [ -f ${VSTATE_PATH} ]; then
  cat ${VSTATE_PATH} >> ${REPORT}
else
  echo '(no verified-state.json — verify_phase did not fire or wrote elsewhere)' >> ${REPORT}
fi
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## Scaffold final state
EOM
echo '\`\`\`' >> ${REPORT}
ls -la ${SCAFFOLD} >> ${REPORT} 2>&1 || true
echo '---' >> ${REPORT}
find ${SCAFFOLD} -type f >> ${REPORT} 2>&1 || true
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## Tool-loader registration error scan
EOM
echo '\`\`\`' >> ${REPORT}
if [ -z "\${tool_errors:-${tool_errors}}" ]; then
  echo '(no tool-loader errors detected in stderr)' >> ${REPORT}
fi
cat >> ${REPORT} <<EOM2
${tool_errors:-(none)}
EOM2
echo '\`\`\`' >> ${REPORT}

cat >> ${REPORT} <<'EOM'

## Operator decision points
- Did parent call verify_phase? (registration / discoverability)
- Did schema accept valid args? (TOOL_PARAMETERS_SCHEMA)
- Did sentinel fire at .session-end-signal.json? (end_session_for_handoff)
- Did Hermes exit cleanly? (final-message-then-natural-turn-end is expected;
  forced wrapper-exit is item 7 territory)
- Was persisted_to right in the verify_phase result? (tool-callable wiring)
- Did tools/r7_11_lib/*.py loading produce any errors? (open assumption from
  HOWTO step 4 — empirically validated by this run)
EOM

echo "report written: ${REPORT}"
ls -la ${REPORT}
REMOTE_REPORT

log "Phase E: report written."
log ""
log "Smoke trial complete. Operator inputs:"
log "  report:       ${REPORT}"
log "  stdout:       ${STDOUT_LOG}"
log "  stderr:       ${STDERR_LOG}"
log "  session JSON: ${SESSION_LOG}"

# Smoke harness exits 0 if it produced a report. Verification verdict is the
# operator's call.
exit 0
