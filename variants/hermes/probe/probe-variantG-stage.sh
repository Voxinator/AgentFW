#!/usr/bin/env bash
# probe-variantG-stage.sh — Stage/unstage the r7.5-A1 turn-0 toolset restriction
# hook on top of Variant F (β-fuse). Layers ON TOP OF variantF — stage/unstage
# variantF separately via probe-variantF-stage.sh. Without variantF staged, the
# v2 dispatch won't exist; variantG only installs the conditional tool binding.
#
# USAGE:
#   ./probe-variantG-stage.sh stage      # patch run_agent.py with the turn-0 hook (backup .probe-r7.5-orig)
#   ./probe-variantG-stage.sh unstage    # restore .probe-r7.5-orig backup on run_agent.py
#   ./probe-variantG-stage.sh status     # show md5 state + whether variantF appears staged
#
# SAFETY:
#   * Patch is idempotent (checks for a unique marker before insert).
#   * Backup uses `.probe-r7.5-orig` suffix (coexists with .probe-r7.4-orig, .probe-d-orig).
#   * DOES NOT modify variantF's state — variantF must be staged separately first
#     for a β-fuse probe to run end-to-end. variantG status reports variantF state
#     so the operator can detect layering mistakes.
#   * Aborts on mid-stage failure; requires manual recovery (no auto-rollback).
#
# The hook:
#   When the in-progress session is using the exact β-fuse toolset string
#   ("delegation,todo,clarify,file_readonly") AND no prior assistant message
#   has called delegate_worker_v2, restrict the tools sent to the LLM to
#   only {delegate_worker_v2, clarify}. After v2 has fired at least once,
#   the full declared toolset is bound normally. Any other toolset (e.g.
#   canonical hermes-cli used by cron / hermes-telegram) is untouched.

set -euo pipefail

REMOTE_HOST="ubuntu-vm"
REMOTE_RUNAGENT="~/.hermes/hermes-agent/run_agent.py"
BAK_SUFFIX=".probe-r7.5-orig"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[probe-variantG-stage] $*"; }

ssh_run() { ssh "$REMOTE_HOST" "$@"; }

md5_remote() { ssh_run "md5sum $1 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true; }

cmd_stage() {
  log "Staging Variant G (r7.5-A1 turn-0 toolset restriction hook on run_agent.py)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

# Idempotency marker: the new method definition is a stable unique string
if grep -q '_resolve_tools_for_turn_r75a' run_agent.py; then
  echo "  run_agent.py: already patched (idempotent no-op)"
  exit 0
fi

[[ -f run_agent.py.probe-r7.5-orig ]] || cp run_agent.py run_agent.py.probe-r7.5-orig

python3 - <<'PYEOF'
import io, sys

path = "run_agent.py"
with open(path, "r") as f:
    src = f.read()

# Anchor 1 — insert the helper method RIGHT BEFORE def _build_api_kwargs.
anchor1 = '    def _build_api_kwargs(self, api_messages: list) -> dict:'

# New method body. Guarded on exact β-fuse toolset composition; scans
# api_messages for any assistant tool_call whose function.name == "delegate_worker_v2".
# Returns a filtered list of tool schemas (preserving order) when turn-0 restriction
# applies; returns self.tools unchanged otherwise.
method_insert = (
    '    # --- r7.5-A1 turn-0 β-fuse toolset restriction hook ---\n'
    '    # Restrict the tools sent to the LLM on turn 0 of a β-fuse probe\n'
    '    # session (toolset EXACTLY delegation,todo,clarify,file_readonly) to\n'
    '    # {delegate_worker_v2, clarify} until delegate_worker_v2 has been\n'
    '    # called at least once. Any other toolset composition is untouched,\n'
    '    # so canonical hermes-cli / hermes-telegram / cron sessions are not\n'
    '    # affected. Marker in method name (`_r75a`) doubles as idempotency\n'
    '    # grep for the stage script.\n'
    '    _BETA_FUSE_TOOLSET_SET = frozenset({"delegation", "todo", "clarify", "file_readonly"})\n'
    '    _BETA_FUSE_TURN0_ALLOWED = frozenset({"delegate_worker_v2", "clarify"})\n'
    '\n'
    '    def _resolve_tools_for_turn_r75a(self, api_messages):\n'
    '        """Return possibly-restricted tool list for the current turn.\n'
    '\n'
    '        If self.enabled_toolsets is exactly the β-fuse probe set and no\n'
    '        assistant message in api_messages has yet called delegate_worker_v2,\n'
    '        restrict to {delegate_worker_v2, clarify}. Otherwise return self.tools.\n'
    '        Defensive: if the filtered result is empty (e.g. v2 not in tools\n'
    '        because variantF was not staged), falls back to self.tools rather\n'
    '        than starving the model of tools.\n'
    '        """\n'
    '        tools = self.tools\n'
    '        if not tools:\n'
    '            return tools\n'
    '        enabled = getattr(self, "enabled_toolsets", None)\n'
    '        if not enabled:\n'
    '            return tools\n'
    '        # Exact composition match (order-insensitive) against β-fuse set.\n'
    '        if frozenset(enabled) != self._BETA_FUSE_TOOLSET_SET:\n'
    '            return tools\n'
    '        # Scan api_messages for any prior assistant delegate_worker_v2 call.\n'
    '        v2_called = False\n'
    '        for m in (api_messages or []):\n'
    '            if not isinstance(m, dict) or m.get("role") != "assistant":\n'
    '                continue\n'
    '            for tc in (m.get("tool_calls") or []):\n'
    '                fn = (tc.get("function") or {}) if isinstance(tc, dict) else {}\n'
    '                if fn.get("name") == "delegate_worker_v2":\n'
    '                    v2_called = True\n'
    '                    break\n'
    '            if v2_called:\n'
    '                break\n'
    '        if v2_called:\n'
    '            return tools\n'
    '        # Turn-0 restriction: filter to {delegate_worker_v2, clarify}.\n'
    '        restricted = [\n'
    '            t for t in tools\n'
    '            if isinstance(t, dict)\n'
    '            and (t.get("function") or {}).get("name") in self._BETA_FUSE_TURN0_ALLOWED\n'
    '        ]\n'
    '        return restricted if restricted else tools\n'
    '\n'
)

if anchor1 not in src:
    print("ERROR: anchor1 (def _build_api_kwargs) not found")
    sys.exit(1)
if src.count(anchor1) != 1:
    print(f"ERROR: anchor1 not unique (count={src.count(anchor1)})")
    sys.exit(1)

src = src.replace(anchor1, method_insert + anchor1, 1)

# Anchor 2 — replace anthropic-branch tools argument.
anchor2 = '                tools=self.tools,\n                max_tokens=self.max_tokens,'
anchor2_new = '                tools=self._resolve_tools_for_turn_r75a(api_messages),\n                max_tokens=self.max_tokens,'
if src.count(anchor2) != 1:
    print(f"ERROR: anchor2 not unique (count={src.count(anchor2)})")
    sys.exit(1)
src = src.replace(anchor2, anchor2_new, 1)

# Anchor 3 — replace OpenAI-branch tools assignment.
anchor3 = '        if self.tools:\n            api_kwargs["tools"] = self.tools\n'
anchor3_new = (
    '        _resolved_tools_r75a = self._resolve_tools_for_turn_r75a(api_messages)\n'
    '        if _resolved_tools_r75a:\n'
    '            api_kwargs["tools"] = _resolved_tools_r75a\n'
)
if src.count(anchor3) != 1:
    print(f"ERROR: anchor3 not unique (count={src.count(anchor3)})")
    sys.exit(1)
src = src.replace(anchor3, anchor3_new, 1)

# Final sanity: marker present twice (method def + used in 2 sites) => 3 total hits
hits = src.count("_resolve_tools_for_turn_r75a")
if hits != 3:
    print(f"ERROR: expected 3 occurrences of _resolve_tools_for_turn_r75a, got {hits}")
    sys.exit(1)

with open(path, "w") as f:
    f.write(src)

print(f"  run_agent.py: inserted turn-0 β-fuse hook ({hits} marker hits)")
PYEOF
REMOTE_SCRIPT

  log ""
  log "STAGE COMPLETE."
  log "  run_agent.py.probe-r7.5-orig backup in place"
  log "  Hook: _resolve_tools_for_turn_r75a invoked in _build_api_kwargs (both API branches)"
  log "  NOTE: variantF must be staged separately for the β-fuse dispatch to work."
}

cmd_unstage() {
  log "Unstaging Variant G (restoring run_agent.py.probe-r7.5-orig)..."

  ssh_run "bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/.hermes/hermes-agent

if [[ -f run_agent.py.probe-r7.5-orig ]]; then
  cp run_agent.py.probe-r7.5-orig run_agent.py
  echo "  run_agent.py restored from .probe-r7.5-orig"
else
  echo "  run_agent.py: no r7.5 backup found — skipping (already unstaged?)"
fi

# Verify no stray r7.5 marker remains (0 unless something else uses the string)
stray=$(grep -c '_resolve_tools_for_turn_r75a' run_agent.py 2>/dev/null || true)
if [[ "${stray:-0}" -ne 0 ]]; then
  echo "WARNING: r7.5 hook marker still present ($stray hits) — investigate before next stage."
  exit 1
fi
echo "  verified: no stray _resolve_tools_for_turn_r75a references"
REMOTE_SCRIPT

  log "UNSTAGE COMPLETE."
}

cmd_status() {
  log "Current Variant G state on $REMOTE_HOST:"

  local hits bak runagent_md5 hermes_md5 variantf_v2_refs variantf_present
  hits=$(ssh_run "grep -c '_resolve_tools_for_turn_r75a' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  hits=${hits:-0}
  bak=$(ssh_run "[[ -f ~/.hermes/hermes-agent/run_agent.py.probe-r7.5-orig ]] && echo yes || echo no")
  runagent_md5=$(md5_remote "$REMOTE_RUNAGENT")
  hermes_md5=$(md5_remote "~/.hermes/hermes-agent/HERMES.md")
  variantf_v2_refs=$(ssh_run "grep -c 'delegate_worker_v2' $REMOTE_RUNAGENT 2>/dev/null || true" | head -1)
  variantf_v2_refs=${variantf_v2_refs:-0}
  variantf_present=$(ssh_run "[[ -f ~/.hermes/hermes-agent/tools/delegate_worker_v2.py ]] && echo yes || echo no")

  printf "  run_agent.py _resolve_tools_for_turn_r75a hits: %s (expect 3 when staged, 0 when canonical)\n" "$hits"
  printf "  run_agent.py.probe-r7.5-orig backup present:   %s\n" "$bak"
  printf "  run_agent.py md5:                              %s\n" "${runagent_md5:-<absent>}"
  printf "  run_agent.py delegate_worker_v2 refs (variantF): %s (expect 5 when variantF staged)\n" "$variantf_v2_refs"
  printf "  variantF tool file present on VM:              %s\n" "$variantf_present"
  printf "  HERMES.md md5 (canonical 0780c232a6cb52e13e432261f0d68ad9): %s\n" "${hermes_md5:-<absent>}"

  if [[ "$hits" -eq 3 ]]; then
    if [[ "$variantf_present" == "yes" && "$variantf_v2_refs" -ge 5 ]]; then
      echo "  STATE: STAGED (r7.5 Variant G on top of r7.4 Variant F)"
    else
      echo "  STATE: VARIANT-G STAGED BUT VARIANT-F NOT STAGED — β-fuse dispatch will not work"
    fi
  elif [[ "$hits" -eq 0 ]]; then
    echo "  STATE: VARIANT-G UNSTAGED"
  else
    echo "  STATE: PARTIAL — investigate before running probe or returning control"
  fi
}

case "${1:-}" in
  stage)    cmd_stage ;;
  unstage)  cmd_unstage ;;
  status)   cmd_status ;;
  verify)   cmd_status ;;
  "")       die "usage: $0 {stage|unstage|status}" ;;
  *)        die "unknown subcommand: $1" ;;
esac
