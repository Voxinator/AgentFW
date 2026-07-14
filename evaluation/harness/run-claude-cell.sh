#!/usr/bin/env bash
# =============================================================================
# run-claude-cell.sh — hermetic Claude Code CLI runner for AgentFW golden-task
# cells (H1, PLAN-r9-evalfix.md). Fixes the GT-2 trace-capture defect: the
# committed transcript exposes the FULL execution trace (tool_use records,
# intermediate assistant messages, tool results), not just the final message.
#
# ISOLATION MECHANISM (probed and verified 2026-07-13, claude CLI 2.1.207):
#   1. CLAUDE_CONFIG_DIR is pointed at a runner-managed mktemp config dir.
#      This removes the operator's global CLAUDE.md (an r8 AgentFW install),
#      plugins, settings, and MCP registrations from the subject's context.
#      Verified mechanically: a sentinel token planted in the fixture's
#      project CLAUDE.md was echoed back by the subject, while the r8
#      kernel's distinctive phrase was reported ABSENT, and the stream-json
#      init event showed plugins=[] and mcp_servers=[].
#   2. --mcp-config '{"mcpServers":{}}' plus --strict-mcp-config force an
#      empty MCP server set regardless of any other config source. The
#      runner additionally hard-asserts mcp_servers == [] (and plugins
#      empty) in the init event and aborts the cell if that fails.
#   3. AUTH (macOS Keychain, with rotation handling — probed behavior):
#      the CLI does NOT read the default Keychain entry when
#      CLAUDE_CONFIG_DIR is overridden; it reads <config>/.credentials.json,
#      then MIGRATES it into a config-dir-specific Keychain entry
#      ("Claude Code-credentials-<hash>") and deletes the file. If the
#      access token is expired the CLI refreshes it, and the refresh
#      ROTATES the refresh token — silently invalidating whatever older
#      copy the operator's main entry holds. The runner therefore:
#        a. materializes the FRESHEST credential it can find (max
#           expiresAt across the main Keychain entry, any leftover
#           per-config-dir entries, and ~/.claude/.credentials.json) into
#           the isolated config dir (mode 600, never echoed, never
#           committed, deleted with the mktemp tree);
#        b. snapshots the Keychain service list before the run; and
#        c. on exit, reconciles: if the subject created a fresher
#           credential generation under its per-run entry, that generation
#           is written back to the operator's main entry, and every
#           per-run entry is deleted. Without (c), each harness run that
#           triggers a token refresh would strand the operator's login.
#      Secrets flow only between `security` subprocess calls; they are
#      never printed, logged, or written inside the repo.
#   4. Session persistence is confined: with CLAUDE_CONFIG_DIR isolated,
#      session/history files land under the mktemp config dir and are
#      removed by the EXIT trap. (Persistence must stay ON during the run —
#      the two-turn path resumes the session via `claude -p --resume <id>`.)
#   5. stream-json in print mode requires --verbose (probed; without it the
#      CLI rejects the flag combination).
#   6. The subject runs with --dangerously-skip-permissions INSIDE the
#      hermetic mktemp fixture so tool calls execute headlessly. The fixture
#      dir is the cwd; the blast radius is the throwaway workdir.
#
# TRANSCRIPT HYGIENE:
#   - Sanitizer rewrites every /Users/<name> to /Users/USER, strips the
#     operator's login name and hostname, and redacts API-key-shaped tokens.
#   - Before emitting, the sanitized transcript must pass the hygiene sweep
#     (same regex class as the repo publication-hygiene rule). A transcript
#     that would still fail is REFUSED: nonzero exit, nothing written to the
#     output path.
#
# USAGE:
#   run-claude-cell.sh --selftest
#   run-claude-cell.sh --out <transcript.md> --prompt-file <f> \
#       [--phase2-file <f>] [--turn3-file <f>] [--fixture <seed-repo-dir>] \
#       [--model <m>] [--gt <label>] [--timeout <seconds>]
#
# TURN STRUCTURE (PLAN-r9-fixpass2 H5):
#   - Every turn's section opens with a column-0 boundary line matching
#     ^===== TURN <n> (turn 1 included), consistent with run-codex-cell.sh.
#   - Every INJECTED turn-2/turn-3 prompt payload is rendered VERBATIM between
#     the exact delimiter lines
#         ----- INJECTED PROMPT BEGIN -----
#         ----- INJECTED PROMPT END -----
#     inside its turn section.
#   - Any SUBJECT-content line beginning `=====` or `----- INJECTED` gets one
#     space prepended before the markers are written, so a subject cannot
#     spoof a turn boundary or an injected-prompt delimiter: runner-emitted
#     markers are the only column-0 instances.
#   - TURN3-DELIVERED: <n> bytes is emitted into the header ONLY when
#     third-turn model output is non-empty (same rule as PHASE2-DELIVERED).
#   - --turn3-file requires --phase2-file (a third turn resumes the second).
#
# SELFTEST (--selftest) writes into evaluation/harness/selftest-out/
# (gitignored):
#   gt0-selftest-claude.md  — trivial three-turn run (turn 1 exercises a real
#                             tool_use; turn 2 is injected via --resume and
#                             must echo PHASE2-ACK; turn 3 is injected via
#                             --resume and must echo TURN3-ACK)
#   sanitizer-check.txt     — proof a planted /Users/<name> line was removed
#   refusal-check.txt       — proof a poisoned transcript was REFUSED
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ADAPTER_DIR="$REPO_ROOT/adapters/claude-code"

# Hygiene regex assembled from concatenated fragments so this script never
# contains the literal poison strings (the repo publication sweep may run
# over evaluation/ recursively).
HYGIENE_RE='rmcp::''transport|Auth''Required|www_''authenticate|\.well-''known/oauth|/Users/[a-z]'

KC_SERVICE='Claude Code-credentials'

MODEL="sonnet"
SELFTEST=0
FIXTURE_SEED=""
PROMPT=""
PHASE2=""
TURN3=""
OUT=""
GT_LABEL="cell"
TIMEOUT_S=600

die() { echo "run-claude-cell: ERROR: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --selftest)     SELFTEST=1; shift ;;
    --fixture)      FIXTURE_SEED="$2"; shift 2 ;;
    --prompt)       PROMPT="$2"; shift 2 ;;
    --prompt-file)  PROMPT="$(cat "$2")"; shift 2 ;;
    --phase2)       PHASE2="$2"; shift 2 ;;
    --phase2-file)  PHASE2="$(cat "$2")"; shift 2 ;;
    --turn3)        TURN3="$2"; shift 2 ;;
    --turn3-file)   TURN3="$(cat "$2")"; shift 2 ;;
    --model)        MODEL="$2"; shift 2 ;;
    --out)          OUT="$2"; shift 2 ;;
    --gt)           GT_LABEL="$2"; shift 2 ;;
    --timeout)      TIMEOUT_S="$2"; shift 2 ;;
    -h|--help)      sed -n '2,95p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *)              die "unknown argument: $1" ;;
  esac
done

command -v claude >/dev/null 2>&1 || die "claude CLI not on PATH"
command -v python3 >/dev/null 2>&1 || die "python3 required"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/agentfw-claude-cell.XXXXXX")"

CONFIG_DIR="$WORK/config"
FIXTURE_DIR="$WORK/fixture"
KC_BASELINE="$WORK/keychain-services-baseline.txt"

HAVE_SECURITY=0
command -v security >/dev/null 2>&1 && HAVE_SECURITY=1

list_cred_services() {
  [ "$HAVE_SECURITY" -eq 1 ] || return 0
  security dump-keychain 2>/dev/null \
    | grep -oE '"Claude Code-credentials[^"]*"' | tr -d '"' | sort -u || true
}

# Reconcile Keychain state after a run: push the freshest credential
# generation back to the operator's main entry, delete per-run entries.
reconcile_credentials() {
  [ "$HAVE_SECURITY" -eq 1 ] || return 0
  [ -f "$KC_BASELINE" ] || return 0
  local now_list="$WORK/keychain-services-now.txt"
  list_cred_services > "$now_list"
  python3 - "$KC_SERVICE" "$KC_BASELINE" "$now_list" <<'PYEOF' || true
import json, subprocess, sys
main_svc, baseline_f, now_f = sys.argv[1], sys.argv[2], sys.argv[3]
baseline = set(open(baseline_f).read().split("\n"))
now = set(open(now_f).read().split("\n"))
new = sorted(s for s in (now - baseline) if s.startswith(main_svc + "-"))
if not new:
    sys.exit(0)
def read(svc):
    r = subprocess.run(["security", "find-generic-password", "-s", svc, "-w"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None
def expiry(blob):
    try:
        return json.loads(blob).get("claudeAiOauth", {}).get("expiresAt", 0) or 0
    except Exception:
        return 0
main_blob = read(main_svc)
main_exp = expiry(main_blob) if main_blob else 0
best_blob, best_exp = None, main_exp
for svc in new:
    blob = read(svc)
    if blob and expiry(blob) > best_exp:
        best_blob, best_exp = blob, expiry(blob)
if best_blob:
    subprocess.run(["security", "add-generic-password", "-U", "-s", main_svc,
                    "-a", subprocess.run(["id", "-un"], capture_output=True,
                                          text=True).stdout.strip(),
                    "-w", best_blob], capture_output=True)
for svc in new:
    subprocess.run(["security", "delete-generic-password", "-s", svc],
                   capture_output=True)
PYEOF
}

cleanup() {
  reconcile_credentials
  rm -rf "$WORK"
}
trap cleanup EXIT

# --- adapter install: project-level layout per adapters/claude-code/INSTALL.md
install_adapter() {
  mkdir -p "$FIXTURE_DIR"
  if [ -n "$FIXTURE_SEED" ]; then
    [ -d "$FIXTURE_SEED" ] || die "fixture seed dir not found: $FIXTURE_SEED"
    cp -R "$FIXTURE_SEED/." "$FIXTURE_DIR/"
  fi
  [ -f "$ADAPTER_DIR/CLAUDE-block.md" ] || die "missing $ADAPTER_DIR/CLAUDE-block.md"
  [ -d "$REPO_ROOT/policy" ] || die "missing $REPO_ROOT/policy"
  [ -f "$REPO_ROOT/tools/validate-plan" ] || die "missing $REPO_ROOT/tools/validate-plan"
  {
    echo '<!-- AGENTFW:BEGIN r9 -->'
    cat "$ADAPTER_DIR/CLAUDE-block.md"
    echo '<!-- AGENTFW:END r9 -->'
  } >> "$FIXTURE_DIR/CLAUDE.md"
  mkdir -p "$FIXTURE_DIR/.claude/skills" "$FIXTURE_DIR/.claude/agents"
  cp -R "$ADAPTER_DIR/skills/agentfw" "$FIXTURE_DIR/.claude/skills/agentfw"
  cp -R "$REPO_ROOT/policy" "$FIXTURE_DIR/.claude/skills/agentfw/policy"
  mkdir -p "$FIXTURE_DIR/.claude/skills/agentfw/tools"
  cp -p "$REPO_ROOT/tools/validate-plan" "$FIXTURE_DIR/.claude/skills/agentfw/tools/validate-plan"
  chmod +x "$FIXTURE_DIR/.claude/skills/agentfw/tools/validate-plan"
  if ls "$ADAPTER_DIR/agents/"agentfw-*.md >/dev/null 2>&1; then
    cp "$ADAPTER_DIR/agents/"agentfw-*.md "$FIXTURE_DIR/.claude/agents/"
  fi
  [ -f "$ADAPTER_DIR/capability.yaml" ] && \
    cp "$ADAPTER_DIR/capability.yaml" "$FIXTURE_DIR/.claude/skills/agentfw/capability.yaml"
  return 0
}

# --- isolated config dir: minimal state + freshest credential (never echoed)
setup_config() {
  mkdir -p "$CONFIG_DIR"
  chmod 700 "$CONFIG_DIR"
  list_cred_services > "$KC_BASELINE"
  python3 - "$CONFIG_DIR/.claude.json" <<'PYEOF'
import json, os, sys
out = sys.argv[1]
minimal = {"hasCompletedOnboarding": True}
src = os.path.expanduser("~/.claude.json")
if os.path.exists(src):
    try:
        d = json.load(open(src))
        if "oauthAccount" in d:
            minimal["oauthAccount"] = d["oauthAccount"]
    except Exception:
        pass
json.dump(minimal, open(out, "w"))
PYEOF
  # pick the freshest credential across every known source
  python3 - "$KC_SERVICE" "$KC_BASELINE" "$CONFIG_DIR/.credentials.json" <<'PYEOF'
import json, os, subprocess, sys
main_svc, baseline_f, out = sys.argv[1], sys.argv[2], sys.argv[3]
candidates = []
def expiry(blob):
    try:
        return json.loads(blob).get("claudeAiOauth", {}).get("expiresAt", 0) or 0
    except Exception:
        return -1
fpath = os.path.expanduser("~/.claude/.credentials.json")
if os.path.exists(fpath):
    blob = open(fpath).read().strip()
    candidates.append((expiry(blob), blob))
for svc in {main_svc} | set(open(baseline_f).read().split("\n")):
    if not svc:
        continue
    r = subprocess.run(["security", "find-generic-password", "-s", svc, "-w"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        candidates.append((expiry(r.stdout.strip()), r.stdout.strip()))
candidates = [c for c in candidates if c[0] >= 0]
if not candidates:
    sys.exit(1)
candidates.sort(key=lambda c: c[0])
with open(out, "w") as fh:
    fh.write(candidates[-1][1])
os.chmod(out, 0o600)
PYEOF
  [ -s "$CONFIG_DIR/.credentials.json" ] || \
    die "no Claude credential available (file or Keychain) — cannot run hermetic cell with auth intact"
}

# --- one headless turn; args: prompt, out.jsonl, [resume-session-id]
run_turn() {
  local prompt="$1" outfile="$2" resume_id="${3:-}"
  local -a args=(-p)
  [ -n "$resume_id" ] && args+=(--resume "$resume_id")
  args+=("$prompt" --model "$MODEL" --output-format stream-json --verbose
         --mcp-config '{"mcpServers":{}}' --strict-mcp-config
         --dangerously-skip-permissions)
  local rc=0
  (
    cd "$FIXTURE_DIR"
    CLAUDE_CONFIG_DIR="$CONFIG_DIR" \
      perl -e 'alarm shift; exec @ARGV' "$TIMEOUT_S" claude "${args[@]}"
  ) > "$outfile" 2> "$outfile.err" || rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "run-claude-cell: turn failed (exit $rc); sanitized stderr follows" >&2
    sed -e 's|/Users/[A-Za-z0-9._-]*|/Users/USER|g' "$outfile.err" >&2 || true
    return "$rc"
  fi
}

# --- assert the init event proves isolation (empty MCP set, no plugins)
assert_isolation() {
  local jsonl="$1"
  python3 - "$jsonl" <<'PYEOF' || die "isolation assertion failed: subject inherited MCP servers or plugins"
import json, sys
for line in open(sys.argv[1]):
    try: ev = json.loads(line)
    except Exception: continue
    if ev.get("type") == "system" and ev.get("subtype") == "init":
        assert ev.get("mcp_servers") == [], "mcp_servers not empty: %r" % ev.get("mcp_servers")
        assert ev.get("plugins") in ([], None), "plugins not empty: %r" % ev.get("plugins")
        sys.exit(0)
sys.exit(1)  # no init event at all
PYEOF
}

extract_session_id() {
  python3 - "$1" <<'PYEOF'
import json, sys
for line in open(sys.argv[1]):
    try: ev = json.loads(line)
    except Exception: continue
    if ev.get("type") == "system" and ev.get("subtype") == "init":
        print(ev["session_id"]); sys.exit(0)
sys.exit(1)
PYEOF
}

# --- render stream-json (1, 2, or 3 turns) into a markdown transcript
#     exposing the full trace. Every turn section opens with a column-0
#     `===== TURN <n>` boundary; injected turn-2/turn-3 payloads are rendered
#     VERBATIM between `----- INJECTED PROMPT BEGIN/END -----` delimiters;
#     subject-content lines beginning `=====` or `----- INJECTED` are escaped
#     (one space prepended) BEFORE the runner-emitted markers are written, so
#     the markers are the only column-0 instances.
#     Prints PHASE2_BYTES=<n> and TURN3_BYTES=<n> on stdout; transcript -> $4.
render_transcript() {
  local turn1="$1" turn2="$2" turn3="$3" out_md="$4"
  GT_LABEL="$GT_LABEL" MODEL="$MODEL" PROMPT="$PROMPT" PHASE2="$PHASE2" \
  TURN3="$TURN3" FIXTURE_SEED="$FIXTURE_SEED" \
  python3 - "$turn1" "$turn2" "$turn3" "$out_md" <<'PYEOF'
import json, os, re, subprocess, sys, datetime

turn1, turn2, turn3, out_md = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

def load(path):
    evs = []
    if path and os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line: continue
            try: evs.append(json.loads(line))
            except Exception: pass
    return evs

def clip(s, n=2000):
    s = str(s)
    return s if len(s) <= n else s[:n] + f"\n... [truncated, {len(s)} chars total]"

# Escape SUBJECT content: a line beginning `=====` or `----- INJECTED` gets one
# space prepended so subjects cannot spoof turn boundaries or delimiters.
# Runner-emitted markers are appended AFTER this, so they remain the only
# column-0 instances.
def esc(s):
    return re.sub(r"(?m)^(=====|----- INJECTED)", r" \1", str(s))

def render_events(evs, w):
    for ev in evs:
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            w.append(f"`[init]` session_id=`{ev.get('session_id')}` model=`{ev.get('model')}` "
                     f"mcp_servers={ev.get('mcp_servers')} plugins={ev.get('plugins')} "
                     f"permissionMode={ev.get('permissionMode')}\n")
        elif t == "assistant":
            for b in ev.get("message", {}).get("content", []):
                bt = b.get("type")
                if bt == "text":
                    w.append("**assistant:**\n\n" + esc(b.get("text", "")) + "\n")
                elif bt == "thinking":
                    w.append("**assistant (thinking):** " + esc(clip(b.get("thinking", ""), 600)) + "\n")
                elif bt == "tool_use":
                    w.append(f"**tool_use: `{b.get('name')}`** (id `{b.get('id')}`)\n\n"
                             "```json\n" + esc(clip(json.dumps(b.get("input", {}), indent=2), 2000)) + "\n```\n")
        elif t == "user":
            c = ev.get("message", {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        content = b.get("content")
                        if isinstance(content, list):
                            content = "\n".join(x.get("text", "") for x in content
                                                if isinstance(x, dict))
                        w.append("**tool_result:**\n\n```\n" + esc(clip(content, 1500)) + "\n```\n")
        elif t == "result":
            w.append(f"`[result]` subtype={ev.get('subtype')} is_error={ev.get('is_error')} "
                     f"num_turns={ev.get('num_turns')} duration_ms={ev.get('duration_ms')}\n")

evs1, evs2, evs3 = load(turn1), load(turn2), load(turn3)

def assistant_bytes(evs):
    n = 0
    for ev in evs:
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") == "text":
                    n += len(b.get("text", "").encode("utf-8"))
    return n

p2_bytes = assistant_bytes(evs2)
p3_bytes = assistant_bytes(evs3)
init1 = next((e for e in evs1 if e.get("type") == "system" and e.get("subtype") == "init"), {})
try:
    ver = subprocess.run(["claude", "--version"], capture_output=True, text=True,
                         timeout=30).stdout.strip()
except Exception:
    ver = "unknown"

hdr = []
hdr.append(f"# {os.environ.get('GT_LABEL','cell')} — claude cell transcript\n")
hdr.append(f"- generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
hdr.append("- runner: evaluation/harness/run-claude-cell.sh (hermetic: isolated "
           "CLAUDE_CONFIG_DIR, empty strict MCP config, adapter installed at project level)")
hdr.append(f"- claude_code: {ver}")
hdr.append(f"- model: {os.environ.get('MODEL','')} (resolved: {init1.get('model')})")
hdr.append(f"- session_id: {init1.get('session_id')}")
hdr.append(f"- fixture_seed: {os.environ.get('FIXTURE_SEED') or '(none — bare adapter fixture)'}")
hdr.append(f"- mcp_servers: {init1.get('mcp_servers')}")
if p2_bytes > 0:
    hdr.append(f"PHASE2-DELIVERED: {p2_bytes} bytes")
if p3_bytes > 0:
    hdr.append(f"TURN3-DELIVERED: {p3_bytes} bytes")
hdr.append("")

# Injected payloads are rendered VERBATIM (no escaping) between the exact
# delimiter lines; the payload is runner-injected, not subject content.
def injected_block(payload):
    return ("----- INJECTED PROMPT BEGIN -----\n"
            + payload
            + "\n----- INJECTED PROMPT END -----\n")

body = []
body.append("===== TURN 1 =====\n")
body.append("## Turn 1 — subject prompt\n")
body.append(esc(os.environ.get("PROMPT", "")) + "\n")
body.append("## Turn 1 — execution trace\n")
render_events(evs1, body)
if evs2:
    body.append(f"===== TURN 2 (injected; resumed session {init1.get('session_id')}) =====\n")
    body.append("## Turn 2 — injected prompt\n")
    body.append(injected_block(os.environ.get("PHASE2", "")))
    body.append("## Turn 2 — execution trace\n")
    render_events(evs2, body)
if evs3:
    body.append("===== TURN 3 (injected; resumed session) =====\n")
    body.append("## Turn 3 — injected prompt\n")
    body.append(injected_block(os.environ.get("TURN3", "")))
    body.append("## Turn 3 — execution trace\n")
    render_events(evs3, body)

open(out_md, "w").write("\n".join(hdr) + "\n" + "\n".join(body) + "\n")
print(f"PHASE2_BYTES={p2_bytes}")
print(f"TURN3_BYTES={p3_bytes}")
PYEOF
}

# --- identity sanitizer (in place)
sanitize_file() {
  python3 - "$1" <<'PYEOF'
import getpass, re, socket, sys
path = sys.argv[1]
s = open(path, encoding="utf-8", errors="replace").read()
s = re.sub(r"/Users/[A-Za-z0-9._-]+", "/Users/USER", s)
s = re.sub(r"sk-ant-[A-Za-z0-9_-]+", "REDACTED-TOKEN", s)
for ident in {getpass.getuser(), socket.gethostname(), socket.gethostname().split(".")[0]}:
    if ident and len(ident) > 2:
        s = s.replace(ident, "USER" if ident == getpass.getuser() else "HOST")
open(path, "w", encoding="utf-8").write(s)
PYEOF
}

# --- hygiene gate: returns 0 = clean, 1 = dirty
hygiene_clean() { ! grep -qE "$HYGIENE_RE" "$1"; }

# --- run one full cell (turn 1 [+ turn 2]) and emit sanitized transcript.
#     Refuses (exit 3, no transcript at $OUT) if hygiene sweep still fails.
#     Every step propagates failure explicitly: this function is safe to
#     call from `||` contexts where `set -e` is suspended.
run_cell() {
  [ -n "$PROMPT" ] || { echo "run-claude-cell: --prompt/--prompt-file required" >&2; return 1; }
  [ -n "$OUT" ] || { echo "run-claude-cell: --out required" >&2; return 1; }
  if [ -n "$TURN3" ] && [ -z "$PHASE2" ]; then
    echo "run-claude-cell: --turn3/--turn3-file requires --phase2/--phase2-file (a third turn resumes the second)" >&2
    return 1
  fi
  install_adapter || return 1
  setup_config || return 1

  local t1="$WORK/turn1.jsonl" t2="$WORK/turn2.jsonl" t3="$WORK/turn3.jsonl" rc=0
  run_turn "$PROMPT" "$t1" || { echo "run-claude-cell: turn 1 failed" >&2; return 1; }
  assert_isolation "$t1" || return 1
  local sid
  sid="$(extract_session_id "$t1")" || { echo "run-claude-cell: no session_id in turn-1 init event" >&2; return 1; }

  if [ -n "$PHASE2" ]; then
    run_turn "$PHASE2" "$t2" "$sid" || { echo "run-claude-cell: turn 2 (--resume) failed" >&2; return 1; }
  else
    : > "$t2"
  fi

  if [ -n "$TURN3" ]; then
    # `claude -p --resume` forks to a NEW session id; turn 3 must resume the
    # turn-2 session (falling back to turn 1's id) or turn-2 context is lost.
    local sid2
    sid2="$(extract_session_id "$t2")" || sid2="$sid"
    run_turn "$TURN3" "$t3" "$sid2" || { echo "run-claude-cell: turn 3 (--resume) failed" >&2; return 1; }
  else
    : > "$t3"
  fi

  local raw="$WORK/transcript-raw.md" meta
  meta="$(render_transcript "$t1" "$t2" "$t3" "$raw")" || return 1
  PHASE2_BYTES="$(printf '%s\n' "$meta" | sed -n 's/^PHASE2_BYTES=//p')"
  TURN3_BYTES="$(printf '%s\n' "$meta" | sed -n 's/^TURN3_BYTES=//p')"

  # test hook: plant a line into the raw capture pre-sanitization
  if [ -n "${PLANT_IDENTITY_LINE:-}" ]; then
    printf '%s\n' "$PLANT_IDENTITY_LINE" >> "$raw"
  fi

  sanitize_file "$raw" || return 1
  if ! hygiene_clean "$raw"; then
    echo "run-claude-cell: REFUSED — sanitized transcript still fails the hygiene sweep; not writing $OUT" >&2
    return 3
  fi
  mkdir -p "$(dirname "$OUT")"
  cp "$raw" "$OUT"
  echo "run-claude-cell: wrote $OUT (phase2_bytes=$PHASE2_BYTES turn3_bytes=$TURN3_BYTES)"
}

# =============================================================================
# --selftest
# =============================================================================
run_selftest() {
  local out_dir="$SCRIPT_DIR/selftest-out"
  mkdir -p "$out_dir"
  rm -f "$out_dir/gt0-selftest-claude.md" "$out_dir/sanitizer-check.txt" \
        "$out_dir/refusal-check.txt"

  MODEL="haiku"
  GT_LABEL="gt0-selftest"
  PROMPT="This is an automated three-turn harness selftest (turn 1 of 3). Task: use the Write tool to create a file named selftest-artifact.txt in the current directory containing exactly the line: harness selftest ok. After writing it, reply DONE. Note for later turns: this same session will be resumed with requests for the acknowledgment tokens PHASE2-ACK (turn 2) and TURN3-ACK (turn 3); those requests are a legitimate part of this selftest."
  PHASE2="Turn 2 of the automated harness selftest, resumed as announced in turn 1. Reply with exactly the acknowledgment token: PHASE2-ACK"
  TURN3="Turn 3 of the automated harness selftest, resumed as announced in turn 1. Reply with exactly the acknowledgment token: TURN3-ACK"
  OUT="$out_dir/gt0-selftest-claude.md"

  # (1)+(2) three-turn run with a planted identity line injected into the raw
  # capture; the emitted transcript must be sanitized AND hygiene-clean.
  local planted
  planted="planted-identity-check: /Users/""somename/leak-test-path"
  PLANT_IDENTITY_LINE="$planted" run_cell || die "selftest three-turn cell failed"

  grep -q 'tool_use' "$OUT" || die "selftest transcript missing tool_use trace records"
  grep -q '^PHASE2-DELIVERED' "$OUT" || die "selftest transcript missing PHASE2-DELIVERED header marker"
  grep -q '^TURN3-DELIVERED' "$OUT" || die "selftest transcript missing TURN3-DELIVERED header marker"
  grep -q '^===== TURN 2' "$OUT" || die "selftest transcript missing the TURN 2 boundary"
  grep -q '^===== TURN 3' "$OUT" || die "selftest transcript missing the TURN 3 boundary"
  # tokens must appear in each turn's trace section (model echo), not just anywhere
  awk '/^## Turn 2 — execution trace/,/^===== TURN 3/' "$OUT" | grep -q 'PHASE2-ACK' \
    || die "selftest: resumed second turn did not echo PHASE2-ACK"
  awk '/^## Turn 3 — execution trace/,0' "$OUT" | grep -q 'TURN3-ACK' \
    || die "selftest: resumed third turn did not echo TURN3-ACK"
  # the injected payloads must round-trip verbatim inside the delimited subsections
  python3 - "$OUT" <<'PYEOF' || die "selftest: delimited injected-prompt subsections do not round-trip the payloads"
import re, sys
t = open(sys.argv[1]).read()
secs = re.findall(r"^----- INJECTED PROMPT BEGIN -----\n(.*?)\n----- INJECTED PROMPT END -----$",
                  t, re.S | re.M)
assert len(secs) == 2, f"expected 2 delimited subsections, got {len(secs)}"
assert any("PHASE2-ACK" in s for s in secs), "turn-2 payload did not round-trip"
assert any("TURN3-ACK" in s for s in secs), "turn-3 payload did not round-trip"
PYEOF

  # (2) planted-identity proof
  if grep -qE '/Users/[a-z]' "$OUT"; then
    echo "SANITIZER-CHECK: FAIL — planted identity path survived sanitization" > "$out_dir/sanitizer-check.txt"
    die "sanitizer check failed"
  fi
  grep -q 'planted-identity-check: /Users/USER/leak-test-path' "$OUT" \
    || die "sanitizer check: planted line not found in sanitized form"
  {
    echo "SANITIZER-CHECK: PASS"
    echo "A synthetic line containing a real-looking lowercase home-directory path"
    echo "was injected into the raw capture before sanitization. In the emitted"
    echo "transcript it appears as: planted-identity-check: /Users/USER/leak-test-path"
    echo "and no lowercase home-directory path remains anywhere in the transcript."
  } > "$out_dir/sanitizer-check.txt"

  # (3) refusal proof: a deliberately poisoned transcript must be REFUSED.
  local poison_dir poison_out rc=0
  poison_dir="$WORK/poison"
  mkdir -p "$poison_dir"
  poison_out="$poison_dir/poisoned-transcript.md"
  {
    echo "# poisoned transcript (synthetic, selftest refusal check)"
    echo "server said: Auth""Required while negotiating"
  } > "$poison_dir/raw.md"
  # exercise the same gate run_cell uses
  if hygiene_clean "$poison_dir/raw.md"; then
    echo "REFUSAL-CHECK: FAIL — poisoned transcript passed the hygiene sweep" > "$out_dir/refusal-check.txt"
    die "refusal check failed: hygiene gate did not flag poison"
  fi
  # end-to-end: run the emit path in a subshell and prove nonzero exit + no file
  set +e
  (
    set -e
    if ! hygiene_clean "$poison_dir/raw.md"; then
      exit 3
    fi
    cp "$poison_dir/raw.md" "$poison_out"
  )
  rc=$?
  set -e
  if [ "$rc" -eq 0 ] || [ -f "$poison_out" ]; then
    echo "REFUSAL-CHECK: FAIL — poisoned transcript was emitted (exit $rc)" > "$out_dir/refusal-check.txt"
    die "refusal check failed: poisoned transcript was emitted"
  fi
  {
    echo "REFUSED"
    echo "A deliberately poisoned transcript (containing an auth-material marker in"
    echo "the hygiene sweep's pattern class) was submitted to the emit gate."
    echo "Result: REFUSED with nonzero exit code $rc; no transcript file was written"
    echo "to the output path (verified absent post-run)."
  } > "$out_dir/refusal-check.txt"

  # final sweep over everything the selftest wrote
  if grep -rlE '/Users/[a-z]' "$out_dir" | grep -q .; then
    die "selftest output directory failed the identity sweep"
  fi
  echo "run-claude-cell: selftest PASS"
  echo "  - $out_dir/gt0-selftest-claude.md"
  echo "  - $out_dir/sanitizer-check.txt"
  echo "  - $out_dir/refusal-check.txt"
}

if [ "$SELFTEST" -eq 1 ]; then
  run_selftest
else
  run_cell
fi
