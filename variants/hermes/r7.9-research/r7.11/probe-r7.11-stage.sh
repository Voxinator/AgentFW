#!/usr/bin/env bash
# probe-r7.11-stage.sh — Stage/unstage r7.11 (verify_phase + handoff tools).
#
# r7.11 adds three new Hermes tools to the parent's surface:
#   - verify_phase              (tiers 1/2/3/3.5 verification engine)
#   - end_session_for_handoff   (session-end sentinel writer)
#   - escalate_to_operator      (escalate sentinel writer)
#
# On-VM layout (operator-approved):
#   ~/.hermes/hermes-agent/tools/r7_11_lib/__init__.py
#   ~/.hermes/hermes-agent/tools/r7_11_lib/verified_state.py
#   ~/.hermes/hermes-agent/tools/r7_11_lib/verify_phase.py
#   ~/.hermes/hermes-agent/tools/r7_11_lib/verify_phase_tool.py
#   ~/.hermes/hermes-agent/tools/r7_11_lib/handoff_tools.py
#   ~/.hermes/hermes-agent/tools/r7_11_verify_phase.py   (thin shim)
#   ~/.hermes/hermes-agent/tools/r7_11_end_session.py    (thin shim)
#   ~/.hermes/hermes-agent/tools/r7_11_escalate.py       (thin shim)
#   + edits to ~/.hermes/hermes-agent/toolsets.py        (add 3 names to _HERMES_CORE_TOOLS)
#   + edits to ~/.hermes/hermes-agent/model_tools.py     (add 3 imports)
#
# Tool-loader investigation (recorded 2026-04-26):
#   model_tools.py uses an EXPLICIT import list (`tools.web_tools`,
#   `tools.terminal_tool`, ...). It does NOT scan tools/ for modules.
#   Other subdirectories already exist and are not scanned (browser_providers/,
#   environments/). So tools/r7_11_lib/ is safe — the shim is what gets
#   imported, the lib is treated as a sub-package only.
#
# USAGE:
#   ./probe-r7.11-stage.sh stage      # install r7.11 layer on canonical
#   ./probe-r7.11-stage.sh unstage    # delegates to probe-r7.11-unstage.sh
#   ./probe-r7.11-stage.sh status     # show markers + md5s
#   ./probe-r7.11-stage.sh dry-run    # print what would run, no mutation
#
# SAFETY:
#   * Pre-flight md5 check on canonical HERMES.md and run_agent.py — fail-fast
#     if VM was modified by something else.
#   * Pre-flight check that tools/toolsets.py.probe-r7.11-orig is absent
#     (refuses to layer on a partial prior state).
#   * Backups suffixed `.probe-r7.11-orig` for toolsets.py + model_tools.py.
#   * Mutation log at /tmp/r7.11-stage-mutation-log.txt on VM.
#   * md5 snapshot at /tmp/r7.11-stage-md5s.txt on VM.
#   * Post-patch `python3 -m py_compile` sanity-check on every edited .py.
#
# IMPORT REWRITE (sibling absolute -> relative inside r7_11_lib/):
#   verify_phase_tool.py imports `verified_state` and `verify_phase` as siblings.
#   On the Mac these resolve via PYTHONPATH=r7.11/. On VM under tools/r7_11_lib/
#   they need to be relative imports. The stage script applies these rewrites
#   while copying:
#     ^import verified_state$           -> from . import verified_state
#     ^import verify_phase$             -> from . import verify_phase
#     ^import verify_phase as vp_mod$   -> from . import verify_phase as vp_mod
#     ^from verified_state import       -> from .verified_state import
#     ^from verify_phase import         -> from .verify_phase import
#   Anchored at start of line so `import verified_state.foo` etc. (none today)
#   would not trigger; survey shows this is sufficient for the current modules.
#
# ENV: bash 4+, ssh-able as $REMOTE_HOST, scp.

set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-ubuntu-vm}"

# Local source files (Mac side, this directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_VERIFIED_STATE="${SCRIPT_DIR}/verified_state.py"
LOCAL_VERIFY_PHASE="${SCRIPT_DIR}/verify_phase.py"
LOCAL_VERIFY_PHASE_TOOL="${SCRIPT_DIR}/verify_phase_tool.py"
LOCAL_HANDOFF_TOOLS="${SCRIPT_DIR}/handoff_tools.py"
LOCAL_LIB_INIT="${SCRIPT_DIR}/r7_11_lib/__init__.py"
LOCAL_UNSTAGE_SCRIPT="${SCRIPT_DIR}/probe-r7.11-unstage.sh"
# r7.10 minimum-mechanism source — its tool-description teaches the parent the
# `## Phase N:` PLAN.md format the verifier expects. Must be staged alongside
# the new r7.11 tools (item 8 trial 1 surfaced this gap; see REPORT-r7.11-item8-trial-1.md).
LOCAL_WRITE_PLAN_MD="${LOCAL_WRITE_PLAN_MD:-${SCRIPT_DIR}/../r7.10/write_plan_md.py.r7.10-min}"

# Remote paths
R_AGENT="${R_AGENT:-.hermes/hermes-agent}"   # relative to remote $HOME
R_TOOLSETS="${R_AGENT}/toolsets.py"
R_MODEL_TOOLS="${R_AGENT}/model_tools.py"
R_LIB_DIR="${R_AGENT}/tools/r7_11_lib"
R_TOOLS_DIR="${R_AGENT}/tools"
R_SHIM_VERIFY="${R_AGENT}/tools/r7_11_verify_phase.py"
R_SHIM_END="${R_AGENT}/tools/r7_11_end_session.py"
R_SHIM_ESCALATE="${R_AGENT}/tools/r7_11_escalate.py"
R_WRITE_PLAN_MD="${R_AGENT}/tools/write_plan_md.py"

# Mutation artifacts
R_MUTLOG="/tmp/r7.11-stage-mutation-log.txt"
R_MD5S="/tmp/r7.11-stage-md5s.txt"
BAK_SUFFIX=".probe-r7.11-orig"

# Canonical md5s (pre-flight check). Override via env for fixture-driven tests.
CANONICAL_HERMES_MD="${CANONICAL_HERMES_MD:-0780c232a6cb52e13e432261f0d68ad9}"
CANONICAL_RUN_AGENT="${CANONICAL_RUN_AGENT:-94ad8712678df5e96b9f407446edf249}"

# Test/fixture mode: when set, run script-side ops against a local fixture
# instead of ssh'ing. Used by test_probe_r7_11.py.
FIXTURE_ROOT="${FIXTURE_ROOT:-}"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-r7.11-stage] $*"; }

# --- abstraction so tests can drive against a local fixture ---
if [[ -n "$FIXTURE_ROOT" ]]; then
  # Local-fixture mode: $REMOTE_HOST irrelevant; rewrite remote paths to
  # live under $FIXTURE_ROOT.
  R_AGENT="${FIXTURE_ROOT}/.hermes/hermes-agent"
  R_TOOLSETS="${R_AGENT}/toolsets.py"
  R_MODEL_TOOLS="${R_AGENT}/model_tools.py"
  R_LIB_DIR="${R_AGENT}/tools/r7_11_lib"
  R_TOOLS_DIR="${R_AGENT}/tools"
  R_SHIM_VERIFY="${R_AGENT}/tools/r7_11_verify_phase.py"
  R_SHIM_END="${R_AGENT}/tools/r7_11_end_session.py"
  R_SHIM_ESCALATE="${R_AGENT}/tools/r7_11_escalate.py"
  R_WRITE_PLAN_MD="${R_AGENT}/tools/write_plan_md.py"
  R_MUTLOG="${FIXTURE_ROOT}/tmp-r7.11-stage-mutation-log.txt"
  R_MD5S="${FIXTURE_ROOT}/tmp-r7.11-stage-md5s.txt"
  ssh_run() { bash -c "$*"; }
  remote_cp() { cp "$1" "$2"; }
  remote_mkdir() { mkdir -p "$1"; }
  remote_cat_to() { cat > "$1"; }
  remote_test_f() { [[ -f "$1" ]]; }
  md5_remote() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
else
  ssh_run() { ssh "$REMOTE_HOST" "$@"; }
  remote_cp() {
    # $1 = local path, $2 = remote path (relative to $HOME)
    scp -q "$1" "${REMOTE_HOST}:${2}"
  }
  remote_mkdir() {
    ssh "$REMOTE_HOST" "mkdir -p \"$1\""
  }
  remote_cat_to() {
    ssh "$REMOTE_HOST" "cat > \"$1\""
  }
  remote_test_f() {
    ssh "$REMOTE_HOST" "[ -f \"$1\" ]"
  }
  md5_remote() {
    ssh "$REMOTE_HOST" "md5sum \"$1\" 2>/dev/null | awk '{print \$1}'"
  }
fi

md5_local() {
  if command -v md5 >/dev/null 2>&1; then
    md5 -q "$1" 2>/dev/null
  else
    md5sum "$1" 2>/dev/null | awk '{print $1}'
  fi
}

# --- import-rewrite helper (also exposed for testing) ---
# Reads stdin, writes stdout with sibling-absolute imports converted to relative.
r7_11_rewrite_imports() {
  # Use sed extended regex; the rewrites are anchored at start of line.
  # Order matters: do `from X import` before `import X` so we don't mangle.
  sed -E \
    -e 's/^from verified_state import /from .verified_state import /' \
    -e 's/^from verify_phase import /from .verify_phase import /' \
    -e 's/^import verified_state$/from . import verified_state/' \
    -e 's/^import verify_phase as vp_mod$/from . import verify_phase as vp_mod/' \
    -e 's/^import verify_phase$/from . import verify_phase/'
}

# Expose the rewrite as a function for tests to source.
if [[ "${1:-}" == "--rewrite-imports" ]]; then
  r7_11_rewrite_imports
  exit 0
fi

# --- pre-flight: local source files exist ---
preflight_local() {
  for f in "$LOCAL_VERIFIED_STATE" "$LOCAL_VERIFY_PHASE" \
           "$LOCAL_VERIFY_PHASE_TOOL" "$LOCAL_HANDOFF_TOOLS" \
           "$LOCAL_LIB_INIT" "$LOCAL_UNSTAGE_SCRIPT" \
           "$LOCAL_WRITE_PLAN_MD"; do
    [[ -f "$f" ]] || die "missing local source: $f"
  done
}

# --- pre-flight: VM is at canonical state ---
preflight_canonical() {
  local md_h md_r
  md_h=$(md5_remote "${R_AGENT}/HERMES.md")
  md_r=$(md5_remote "${R_AGENT}/run_agent.py")
  if [[ "$md_h" != "$CANONICAL_HERMES_MD" ]]; then
    die "canonical drift: HERMES.md md5=$md_h expected=$CANONICAL_HERMES_MD. VM was modified by something else; refusing to stage. Investigate before re-running."
  fi
  if [[ "$md_r" != "$CANONICAL_RUN_AGENT" ]]; then
    die "canonical drift: run_agent.py md5=$md_r expected=$CANONICAL_RUN_AGENT. VM was modified by something else; refusing to stage. Investigate before re-running."
  fi
}

# --- pre-flight: no stale backups (refuse to stack) ---
preflight_no_stale() {
  if remote_test_f "${R_TOOLSETS}${BAK_SUFFIX}"; then
    die "stale backup ${R_TOOLSETS}${BAK_SUFFIX} exists; refusing to stage on a partial prior state. Run unstage first."
  fi
  if remote_test_f "${R_MODEL_TOOLS}${BAK_SUFFIX}"; then
    die "stale backup ${R_MODEL_TOOLS}${BAK_SUFFIX} exists; refusing to stage on a partial prior state. Run unstage first."
  fi
}

# --- the staging shim contents (HEREDOCs) ---

emit_shim_verify() {
  cat <<'SHIM_EOF'
"""r7_11_verify_phase — Hermes tool registration for verify_phase.

Thin shim that pulls metadata + handler from tools.r7_11_lib.verify_phase_tool
and self-registers via tools.registry. Auto-discovered by model_tools.py
through its explicit import list (added by probe-r7.11-stage.sh).
"""

import json
from tools.registry import registry
from tools.r7_11_lib.verify_phase_tool import (
    TOOL_NAME,
    TOOL_DESCRIPTION,
    TOOL_PARAMETERS_SCHEMA,
    verify_phase_tool,
)


VERIFY_PHASE_SCHEMA = {
    "name": TOOL_NAME,
    "description": TOOL_DESCRIPTION,
    "parameters": TOOL_PARAMETERS_SCHEMA,
}


def _handle(args, **kw):
    # Hermes' result-handling pipeline triggers an unhashable-slice error
    # when handlers return non-string values. JSON-encode the dict result.
    # session_id is injected by the registry/dispatcher when available;
    # the underlying function accepts session_id=None and synthesizes one.
    result = verify_phase_tool(
        phase_id=args.get("phase_id"),
        scaffold_root=args.get("scaffold_root"),
        tier=args.get("tier", 3),
        with_runtime_smoke_test=args.get("with_runtime_smoke_test"),
        verify_config_path=args.get("verify_config_path"),
        plan_md_path=args.get("plan_md_path"),
        verified_state_path=args.get("verified_state_path"),
        session_id=kw.get("session_id"),
    )
    return json.dumps(result)


registry.register(
    name=TOOL_NAME,
    toolset="delegation",
    schema=VERIFY_PHASE_SCHEMA,
    handler=_handle,
    check_fn=lambda: True,
    description=TOOL_DESCRIPTION,
    emoji="✅",
)
SHIM_EOF
}

emit_shim_end() {
  cat <<'SHIM_EOF'
"""r7_11_end_session — Hermes tool registration for end_session_for_handoff."""

import json
from tools.registry import registry
from tools.r7_11_lib.handoff_tools import (
    END_SESSION_TOOL_NAME,
    END_SESSION_TOOL_DESCRIPTION,
    END_SESSION_TOOL_PARAMETERS_SCHEMA,
    end_session_for_handoff,
)


END_SESSION_SCHEMA = {
    "name": END_SESSION_TOOL_NAME,
    "description": END_SESSION_TOOL_DESCRIPTION,
    "parameters": END_SESSION_TOOL_PARAMETERS_SCHEMA,
}


def _handle(args, **kw):
    # Handlers must return strings (Hermes result-handling triggers
    # unhashable-slice on non-string returns).
    result = end_session_for_handoff(
        scaffold_root=args.get("scaffold_root"),
        completed_phase=args.get("completed_phase"),
        parent_intent_log=args.get("parent_intent_log"),
        parent_summary=args.get("parent_summary", ""),
        session_id=kw.get("session_id"),
    )
    return json.dumps(result)


registry.register(
    name=END_SESSION_TOOL_NAME,
    toolset="delegation",
    schema=END_SESSION_SCHEMA,
    handler=_handle,
    check_fn=lambda: True,
    description=END_SESSION_TOOL_DESCRIPTION,
    emoji="🏁",
)
SHIM_EOF
}

emit_shim_escalate() {
  cat <<'SHIM_EOF'
"""r7_11_escalate — Hermes tool registration for escalate_to_operator."""

import json
from tools.registry import registry
from tools.r7_11_lib.handoff_tools import (
    ESCALATE_TOOL_NAME,
    ESCALATE_TOOL_DESCRIPTION,
    ESCALATE_TOOL_PARAMETERS_SCHEMA,
    escalate_to_operator,
)


ESCALATE_SCHEMA = {
    "name": ESCALATE_TOOL_NAME,
    "description": ESCALATE_TOOL_DESCRIPTION,
    "parameters": ESCALATE_TOOL_PARAMETERS_SCHEMA,
}


def _handle(args, **kw):
    # Handlers must return strings (Hermes result-handling triggers
    # unhashable-slice on non-string returns).
    result = escalate_to_operator(
        scaffold_root=args.get("scaffold_root"),
        reason=args.get("reason"),
        message=args.get("message"),
        suggested_action=args.get("suggested_action"),
        session_id=kw.get("session_id"),
    )
    return json.dumps(result)


registry.register(
    name=ESCALATE_TOOL_NAME,
    toolset="delegation",
    schema=ESCALATE_SCHEMA,
    handler=_handle,
    check_fn=lambda: True,
    description=ESCALATE_TOOL_DESCRIPTION,
    emoji="🚨",
)
SHIM_EOF
}

# --- toolsets.py / model_tools.py edit helpers ---

# Append the three new tool names to `_HERMES_CORE_TOOLS` list in toolsets.py.
# Idempotent via grep guard.
patch_toolsets() {
  local target="$1"
  python3 - "$target" <<'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    src = f.read()

new_names = ['"verify_phase"', '"end_session_for_handoff"', '"escalate_to_operator"', '"write_plan_md"']
if all(name in src for name in new_names):
    print("toolsets.py: r7.11 tool names already present, no-op")
    sys.exit(0)

# Find the closing `]` of _HERMES_CORE_TOOLS list. Pattern: line "_HERMES_CORE_TOOLS = ["
# then content, then closing "]". We'll insert before the closing ].
m = re.search(r'(_HERMES_CORE_TOOLS\s*=\s*\[)(.*?)(\n\])', src, re.DOTALL)
if not m:
    print("ERROR: could not locate _HERMES_CORE_TOOLS list", file=sys.stderr)
    sys.exit(1)

insertion = (
    '    # r7.11: phase verification + handoff (probe-r7.11) + write_plan_md (r7.10 carry-forward)\n'
    '    "verify_phase", "end_session_for_handoff", "escalate_to_operator", "write_plan_md",\n'
)
patched = src[:m.end(2)] + '\n' + insertion + src[m.start(3)+1:]
with open(path, "w") as f:
    f.write(patched)
print("toolsets.py: appended r7.11 tool names to _HERMES_CORE_TOOLS")
PYEOF
}

# Add three import strings to the explicit module-import list in model_tools.py.
# The list is the one matching `for module_name in [...]` near line ~135.
# We locate `"tools.delegate_worker",` and insert after it. Idempotent via grep.
patch_model_tools() {
  local target="$1"
  python3 - "$target" <<'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    src = f.read()

new_imports = ['"tools.r7_11_verify_phase"', '"tools.r7_11_end_session"', '"tools.r7_11_escalate"', '"tools.write_plan_md"']
if all(imp in src for imp in new_imports):
    print("model_tools.py: r7.11 imports already present, no-op")
    sys.exit(0)

# Locate the line `"tools.delegate_worker",` and insert after it
anchor = re.compile(r'^(\s*)"tools\.delegate_worker",\s*$', re.MULTILINE)
m = anchor.search(src)
if not m:
    print("ERROR: could not find anchor 'tools.delegate_worker' in model_tools.py", file=sys.stderr)
    sys.exit(1)

indent = m.group(1)
insertion = (
    f'\n{indent}# r7.11: phase verification + handoff (probe-r7.11) + write_plan_md (r7.10 carry-forward)\n'
    f'{indent}"tools.r7_11_verify_phase",\n'
    f'{indent}"tools.r7_11_end_session",\n'
    f'{indent}"tools.r7_11_escalate",\n'
    f'{indent}"tools.write_plan_md",'
)
patched = src[:m.end()] + insertion + src[m.end():]
with open(path, "w") as f:
    f.write(patched)
print("model_tools.py: appended r7.11 imports after tools.delegate_worker")
PYEOF
}

# --- staging logic ---

cmd_stage() {
  log "Staging r7.11 (verify_phase + handoff tools) on ${REMOTE_HOST}${FIXTURE_ROOT:+ (fixture: $FIXTURE_ROOT)}..."

  preflight_local
  preflight_canonical
  preflight_no_stale

  # Phase 1: init mutation log
  log "Phase 1: initialize mutation log at $R_MUTLOG"
  ssh_run "echo '# r7.11 stage mutation log (start' \"\$(date -Is)\" ')' > $R_MUTLOG"

  # Phase 2: backup toolsets.py + model_tools.py
  log "Phase 2: backup toolsets.py + model_tools.py"
  ssh_run "cp ${R_TOOLSETS} ${R_TOOLSETS}${BAK_SUFFIX}"
  ssh_run "cp ${R_MODEL_TOOLS} ${R_MODEL_TOOLS}${BAK_SUFFIX}"
  ssh_run "echo 'phase2: backups created' >> $R_MUTLOG"

  # Phase 3: create r7_11_lib/ directory
  log "Phase 3: create $R_LIB_DIR"
  remote_mkdir "$R_LIB_DIR"
  ssh_run "echo 'phase3: r7_11_lib/ created' >> $R_MUTLOG"

  # Phase 4: copy lib modules with import rewrite
  log "Phase 4: copy four lib modules into r7_11_lib/ (with import rewrite)"
  # __init__.py copies as-is
  remote_cp "$LOCAL_LIB_INIT" "${R_LIB_DIR}/__init__.py"
  # verified_state.py — no sibling imports, copies as-is
  remote_cp "$LOCAL_VERIFIED_STATE" "${R_LIB_DIR}/verified_state.py"
  # verify_phase.py — no sibling imports, copies as-is
  remote_cp "$LOCAL_VERIFY_PHASE" "${R_LIB_DIR}/verify_phase.py"
  # verify_phase_tool.py — has `import verified_state`, `import verify_phase as vp_mod`,
  # `from verified_state import (...)`, `from verify_phase import ...`. Rewrite.
  r7_11_rewrite_imports < "$LOCAL_VERIFY_PHASE_TOOL" | remote_cat_to "${R_LIB_DIR}/verify_phase_tool.py"
  # handoff_tools.py — no sibling imports, copies as-is
  remote_cp "$LOCAL_HANDOFF_TOOLS" "${R_LIB_DIR}/handoff_tools.py"
  ssh_run "echo 'phase4: lib modules copied + import-rewritten' >> $R_MUTLOG"

  # Phase 4.5: scp write_plan_md.py (r7.10 minimum-mechanism source).
  # Belt-and-suspenders refusal if the file already exists — Phase 1's
  # stale-backup guard should have caught this, but a stray file with no
  # backup means partial state we shouldn't overwrite.
  log "Phase 4.5: scp write_plan_md.py (r7.10 minimum-mechanism source)"
  if remote_test_f "$R_WRITE_PLAN_MD"; then
    die "tools/write_plan_md.py already exists at $R_WRITE_PLAN_MD; refusing to overwrite. Run unstage first."
  fi
  remote_cp "$LOCAL_WRITE_PLAN_MD" "$R_WRITE_PLAN_MD"
  ssh_run "echo 'phase4.5: write_plan_md.py copied' >> $R_MUTLOG"

  # Phase 5: write three thin shims
  log "Phase 5: write three thin shim files in tools/"
  emit_shim_verify   | remote_cat_to "$R_SHIM_VERIFY"
  emit_shim_end      | remote_cat_to "$R_SHIM_END"
  emit_shim_escalate | remote_cat_to "$R_SHIM_ESCALATE"
  ssh_run "echo 'phase5: shims written' >> $R_MUTLOG"

  # Phase 6: patch toolsets.py + model_tools.py in place.
  # Strategy: write each patcher to a tempfile, ship to /tmp on remote,
  # invoke. In fixture mode the tempfile lives locally and is invoked locally.
  log "Phase 6: patch toolsets.py + model_tools.py"
  local patcher_toolsets patcher_model_tools
  patcher_toolsets=$(mktemp)
  patcher_model_tools=$(mktemp)

  cat > "$patcher_toolsets" <<'EOPY'
import sys, re
path = sys.argv[1]
with open(path) as f:
    src = f.read()
# Option A anchoring: a single r7.11-tagged insertion that also carries
# write_plan_md (r7.10 carry-forward; teaches `## Phase N:` PLAN.md format).
new_names = ['"verify_phase"', '"end_session_for_handoff"', '"escalate_to_operator"', '"write_plan_md"']
if all(n in src for n in new_names):
    print("toolsets.py: r7.11 tool names already present, no-op"); sys.exit(0)
m = re.search(r'(_HERMES_CORE_TOOLS\s*=\s*\[)(.*?)(\n\])', src, re.DOTALL)
if not m:
    print("ERROR: anchor missing in toolsets.py", file=sys.stderr); sys.exit(1)
ins = '    # r7.11: phase verification + handoff (probe-r7.11) + write_plan_md (r7.10 carry-forward)\n    "verify_phase", "end_session_for_handoff", "escalate_to_operator", "write_plan_md",\n'
patched = src[:m.end(2)] + '\n' + ins + src[m.start(3)+1:]
open(path, "w").write(patched)
print("toolsets.py: appended r7.11 tool names to _HERMES_CORE_TOOLS")
EOPY

  cat > "$patcher_model_tools" <<'EOPY'
import sys, re
path = sys.argv[1]
with open(path) as f:
    src = f.read()
# Option A anchoring: a single r7.11-tagged insertion block that also
# carries tools.write_plan_md (r7.10 carry-forward).
new_imports = ['"tools.r7_11_verify_phase"', '"tools.r7_11_end_session"', '"tools.r7_11_escalate"', '"tools.write_plan_md"']
if all(imp in src for imp in new_imports):
    print("model_tools.py: r7.11 imports already present, no-op"); sys.exit(0)
anchor = re.compile(r'^(\s*)"tools\.delegate_worker",\s*$', re.MULTILINE)
m = anchor.search(src)
if not m:
    print("ERROR: anchor 'tools.delegate_worker' missing in model_tools.py", file=sys.stderr); sys.exit(1)
indent = m.group(1)
ins = f'\n{indent}# r7.11: phase verification + handoff (probe-r7.11) + write_plan_md (r7.10 carry-forward)\n{indent}"tools.r7_11_verify_phase",\n{indent}"tools.r7_11_end_session",\n{indent}"tools.r7_11_escalate",\n{indent}"tools.write_plan_md",'
patched = src[:m.end()] + ins + src[m.end():]
open(path, "w").write(patched)
print("model_tools.py: appended r7.11 imports after tools.delegate_worker")
EOPY

  if [[ -n "$FIXTURE_ROOT" ]]; then
    python3 "$patcher_toolsets"    "$R_TOOLSETS"
    python3 "$patcher_model_tools" "$R_MODEL_TOOLS"
  else
    scp -q "$patcher_toolsets"    "${REMOTE_HOST}:/tmp/r7.11-patch-toolsets.py"
    scp -q "$patcher_model_tools" "${REMOTE_HOST}:/tmp/r7.11-patch-model-tools.py"
    ssh "$REMOTE_HOST" "python3 /tmp/r7.11-patch-toolsets.py    $R_TOOLSETS"
    ssh "$REMOTE_HOST" "python3 /tmp/r7.11-patch-model-tools.py $R_MODEL_TOOLS"
  fi
  rm -f "$patcher_toolsets" "$patcher_model_tools"
  ssh_run "echo 'phase6: toolsets.py + model_tools.py patched' >> $R_MUTLOG"

  # Phase 7: py_compile sanity
  log "Phase 7: py_compile sanity check"
  ssh_run "python3 -m py_compile ${R_TOOLSETS} ${R_MODEL_TOOLS} ${R_LIB_DIR}/__init__.py ${R_LIB_DIR}/verified_state.py ${R_LIB_DIR}/verify_phase.py ${R_LIB_DIR}/verify_phase_tool.py ${R_LIB_DIR}/handoff_tools.py ${R_SHIM_VERIFY} ${R_SHIM_END} ${R_SHIM_ESCALATE} ${R_WRITE_PLAN_MD}" \
    || die "py_compile failed; staging is in an INCONSISTENT state. Run unstage to recover."
  ssh_run "echo 'phase7: py_compile OK' >> $R_MUTLOG"

  # Phase 8: post-stage md5 snapshot + manifest
  log "Phase 8: post-stage md5 snapshot"
  ssh_run "{ echo '# r7.11 stage post-stage md5s (' \"\$(date -Is)\" ')'; \
            md5sum ${R_TOOLSETS} ${R_MODEL_TOOLS} ${R_LIB_DIR}/*.py ${R_SHIM_VERIFY} ${R_SHIM_END} ${R_SHIM_ESCALATE} ${R_WRITE_PLAN_MD}; \
          } > $R_MD5S"
  ssh_run "echo 'phase8: md5 snapshot at $R_MD5S' >> $R_MUTLOG"

  log ""
  log "STAGE COMPLETE."
  log "  mutation log: $R_MUTLOG"
  log "  md5 snapshot: $R_MD5S"
  log "  shims:        $R_SHIM_VERIFY"
  log "                $R_SHIM_END"
  log "                $R_SHIM_ESCALATE"
  log "  write_plan_md:  $R_WRITE_PLAN_MD"
  log "  lib dir:      $R_LIB_DIR"
}

cmd_status() {
  log "r7.11 stage status:"
  ssh_run "echo '  toolsets.py backup:    '; [ -f ${R_TOOLSETS}${BAK_SUFFIX} ] && echo '  YES' || echo '  absent'"
  ssh_run "echo '  model_tools.py backup: '; [ -f ${R_MODEL_TOOLS}${BAK_SUFFIX} ] && echo '  YES' || echo '  absent'"
  ssh_run "echo '  shims:'; for f in ${R_SHIM_VERIFY} ${R_SHIM_END} ${R_SHIM_ESCALATE} ${R_WRITE_PLAN_MD}; do [ -f \"\$f\" ] && echo \"    \$f: present\" || echo \"    \$f: ABSENT\"; done"
  ssh_run "echo '  lib dir:'; [ -d ${R_LIB_DIR} ] && ls ${R_LIB_DIR}/ || echo '    absent'"
  if remote_test_f "$R_MD5S"; then
    log "  md5 snapshot exists: $R_MD5S"
  else
    log "  md5 snapshot absent (no successful stage recorded)"
  fi
}

cmd_dry_run() {
  log "DRY RUN — would execute these steps:"
  echo "  1. preflight: local sources exist"
  echo "  2. preflight: VM at canonical (HERMES.md=$CANONICAL_HERMES_MD, run_agent.py=$CANONICAL_RUN_AGENT)"
  echo "  3. preflight: no stale ${BAK_SUFFIX} backups"
  echo "  4. cp ${R_TOOLSETS} ${R_TOOLSETS}${BAK_SUFFIX}"
  echo "  5. cp ${R_MODEL_TOOLS} ${R_MODEL_TOOLS}${BAK_SUFFIX}"
  echo "  6. mkdir -p ${R_LIB_DIR}"
  echo "  7. scp ${LOCAL_LIB_INIT} -> ${R_LIB_DIR}/__init__.py"
  echo "  8. scp ${LOCAL_VERIFIED_STATE} -> ${R_LIB_DIR}/verified_state.py"
  echo "  9. scp ${LOCAL_VERIFY_PHASE} -> ${R_LIB_DIR}/verify_phase.py"
  echo " 10. cat ${LOCAL_VERIFY_PHASE_TOOL} | r7_11_rewrite_imports > ${R_LIB_DIR}/verify_phase_tool.py"
  echo " 11. scp ${LOCAL_HANDOFF_TOOLS} -> ${R_LIB_DIR}/handoff_tools.py"
  echo " 11.5 scp ${LOCAL_WRITE_PLAN_MD} -> ${R_WRITE_PLAN_MD}"
  echo " 12. write ${R_SHIM_VERIFY}, ${R_SHIM_END}, ${R_SHIM_ESCALATE}"
  echo " 13. patch ${R_TOOLSETS}: append 4 tool names to _HERMES_CORE_TOOLS (incl. write_plan_md)"
  echo " 14. patch ${R_MODEL_TOOLS}: append 4 imports after tools.delegate_worker (incl. tools.write_plan_md)"
  echo " 15. py_compile every modified .py (incl. write_plan_md.py)"
  echo " 16. record md5 snapshot at $R_MD5S"
  log "Local file md5s (would be uploaded):"
  echo "  verified_state.py:    $(md5_local "$LOCAL_VERIFIED_STATE")"
  echo "  verify_phase.py:      $(md5_local "$LOCAL_VERIFY_PHASE")"
  echo "  verify_phase_tool.py: $(md5_local "$LOCAL_VERIFY_PHASE_TOOL") (will be rewritten)"
  echo "  handoff_tools.py:     $(md5_local "$LOCAL_HANDOFF_TOOLS")"
  echo "  r7_11_lib/__init__.py: $(md5_local "$LOCAL_LIB_INIT")"
  echo "  write_plan_md.py:     $(md5_local "$LOCAL_WRITE_PLAN_MD")"
}

cmd_unstage() {
  exec bash "$LOCAL_UNSTAGE_SCRIPT" "$@"
}

case "${1:-}" in
  stage)          cmd_stage ;;
  unstage)        shift; cmd_unstage "$@" ;;
  status)         cmd_status ;;
  dry-run|dryrun) cmd_dry_run ;;
  --rewrite-imports) r7_11_rewrite_imports ;;
  *) echo "Usage: $0 {stage|unstage|status|dry-run|--rewrite-imports}" >&2; exit 2 ;;
esac
