#!/usr/bin/env bash
# install-roundtrip.sh — proof for T3's risk: the installer must never clobber user content.
#
# Runs the real tools/agentfw-install against mktemp CLAUDE_DIR sandboxes. Never touches the
# real ~/.claude. Each numbered check prints "PASS: <what>" only after real assertions, or
# exits 1 with a FAIL message.
#
# Hermetic w.r.t. sibling r9 tasks: the installer requires the repo's policy/ dir; if it does
# not exist yet (parallel build), the test stages a temp copy of the source tree with a clearly
# labeled fixture policy file. The installer's policy-copy code path is exercised either way —
# the sentinel/marker assertions below are always against real installer behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SENTINEL='USER-SENTINEL: keep me'

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# --- stage a source tree (real files; fixture policy/ only if the repo lacks one) -------------
SRC="$(mktemp -d)"
SANDBOXES=()
cleanup() { rm -rf "$SRC" "${SANDBOXES[@]:-}"; }
trap cleanup EXIT

mkdir -p "$SRC/tools" "$SRC/adapters"
cp -p "$REPO_ROOT/tools/agentfw-install" "$SRC/tools/agentfw-install"
cp -R "$REPO_ROOT/adapters/claude-code" "$SRC/adapters/claude-code"
if [ -d "$REPO_ROOT/policy" ]; then
  cp -R "$REPO_ROOT/policy" "$SRC/policy"
else
  mkdir -p "$SRC/policy"
  printf '# FIXTURE policy file (repo policy/ not built yet at test time)\n' > "$SRC/policy/core.md"
fi
INSTALL="$SRC/tools/agentfw-install"
[ -x "$INSTALL" ] || fail "installer is not executable: $INSTALL"

count_begin() { grep -c 'AGENTFW:BEGIN' "$1/CLAUDE.md" 2>/dev/null || true; }

# ==============================================================================================
# (1) Fresh install into a sandbox seeded with a user sentinel line.
# ==============================================================================================
SB1="$(mktemp -d)"; SANDBOXES+=("$SB1")
printf '%s\n' "$SENTINEL" > "$SB1/CLAUDE.md"

CLAUDE_DIR="$SB1" bash "$INSTALL" install > /dev/null

[ "$(count_begin "$SB1")" -eq 1 ] || fail "check 1: expected exactly one AGENTFW:BEGIN, got $(count_begin "$SB1")"
grep -qF "$SENTINEL" "$SB1/CLAUDE.md" || fail "check 1: user sentinel lost on fresh install"
grep -q 'AGENTFW:END' "$SB1/CLAUDE.md" || fail "check 1: END marker missing"
[ -s "$SB1/skills/agentfw/SKILL.md" ] || fail "check 1: skill not installed"
for a in agentfw-implementer agentfw-verifier agentfw-plan-critic; do
  [ -s "$SB1/agents/$a.md" ] || fail "check 1: agent $a.md not installed"
done
[ -d "$SB1/skills/agentfw/policy" ] || fail "check 1: policy/ dir not copied into skill"
ls "$SB1/skills/agentfw/policy/"*.md > /dev/null 2>&1 || fail "check 1: policy/ copy is empty"
pass "fresh install — block present exactly once, sentinel preserved, skill + 3 agents + policy/ installed"

# ==============================================================================================
# (2) Second install run on the same sandbox — idempotence.
# ==============================================================================================
CLAUDE_DIR="$SB1" bash "$INSTALL" install > /dev/null
[ "$(count_begin "$SB1")" -eq 1 ] || fail "check 2: second install produced $(count_begin "$SB1") BEGIN markers (expected 1)"
grep -qF "$SENTINEL" "$SB1/CLAUDE.md" || fail "check 2: sentinel lost on re-install"
pass "idempotence — second install still exactly ONE AGENTFW:BEGIN, sentinel intact"

# ==============================================================================================
# (3) Upgrade over a seeded MARKER-LESS r8-style CLAUDE.md.
#     Layout: r8 heading + r8-ish body + user sentinel + user MCP-style section.
# ==============================================================================================
SB2="$(mktemp -d)"; SANDBOXES+=("$SB2")
cat > "$SB2/CLAUDE.md" <<'EOF'
<!-- AgentFW v8 — Claude Code only. Source: github.com/Voxinator/AgentFW -->
# AgentFW — Core Instructions

AI capabilities appear "jagged" when we ask for one-shot answers. The firmware is the product.

## CRITICAL RULES — override all other guidance
1. **CLASSIFY BEFORE ACTING.** Output `[TASK CLASS: one-shot | structured | long-horizon]`.
2. **DO NOT COLLAPSE ROLES.** Plan / implement / verify are different jobs.

## The Governance Mindset
You operate within Claude Code's runtime. It provides the harness.

## Two Enforcement Gates
1. **Tier-1 verification gate.** No completed->verified without recorded machine-check output.

## Reference Index
- `core/harness-core.md` — this file (always loaded)
- `references/anti-patterns.md`

> **Future target (note):** out of scope for v8.

USER-SENTINEL: keep me

## MCP Usage Instructions

### My personal MCP rules
1. If an MCP exists for the task, use it.
EOF

CLAUDE_DIR="$SB2" bash "$INSTALL" upgrade > "$SB2/upgrade.log" 2>&1 || {
  cat "$SB2/upgrade.log" >&2
  fail "check 3: upgrade exited non-zero on marker-less r8 file"
}

[ "$(count_begin "$SB2")" -eq 1 ] || fail "check 3: expected exactly one AGENTFW:BEGIN after upgrade, got $(count_begin "$SB2")"
grep -q '^# AgentFW — Core Instructions' "$SB2/CLAUDE.md" && fail "check 3: r8 heading still present in live file after upgrade"
grep -qF "$SENTINEL" "$SB2/CLAUDE.md" || fail "check 3: user sentinel lost during marker-less upgrade"
grep -q '^## MCP Usage Instructions' "$SB2/CLAUDE.md" || fail "check 3: user MCP section lost during marker-less upgrade"
grep -q 'My personal MCP rules' "$SB2/CLAUDE.md" || fail "check 3: user MCP section body lost during marker-less upgrade"
BACKUP=$(ls "$SB2"/CLAUDE.md.agentfw-backup-* 2>/dev/null | head -1) || true
[ -n "${BACKUP:-}" ] && [ -f "$BACKUP" ] || fail "check 3: no backup file created for marker-less upgrade"
grep -q '^# AgentFW — Core Instructions' "$BACKUP" || fail "check 3: backup does not contain the old r8 content"
grep -qF "$SENTINEL" "$BACKUP" || fail "check 3: backup is not the full original file"
pass "marker-less r8 upgrade — new block present, r8 heading excised, sentinel + user MCP section preserved, full-original backup exists"

# ==============================================================================================
# (4) Uninstall on the upgraded sandbox — zero markers, user content byte-identical.
#     Primary assertion: cmp the post-uninstall file against the computed expectation — the
#     pre-uninstall snapshot minus the AGENTFW block(s) and the installer-added separator
#     blank line. Secondary: marker/sentinel/section greps.
# ==============================================================================================
SENTINEL_COUNT_BEFORE=$(grep -cF "$SENTINEL" "$SB2/CLAUDE.md")
SNAP="$SRC/pre-uninstall.snapshot"
EXPECTED="$SRC/expected-post-uninstall"
cp "$SB2/CLAUDE.md" "$SNAP"
awk '
  { L[NR] = $0 }
  END {
    inb = 0
    for (i = 1; i <= NR; i++) {
      if (L[i] ~ /AGENTFW:BEGIN/) {
        inb = 1; del[i] = 1
        if (i > 1 && L[i-1] ~ /^[[:space:]]*$/ && !del[i-1]) del[i-1] = 1
      } else if (L[i] ~ /AGENTFW:END/) {
        del[i] = 1; inb = 0
      } else if (inb) del[i] = 1
    }
    for (i = 1; i <= NR; i++) if (!del[i]) print L[i]
  }
' "$SNAP" > "$EXPECTED"

CLAUDE_DIR="$SB2" bash "$INSTALL" uninstall > /dev/null

cmp -s "$SB2/CLAUDE.md" "$EXPECTED" || fail "check 4: post-uninstall CLAUDE.md is not byte-identical to snapshot-minus-block (user content altered)"
grep -q 'AGENTFW' "$SB2/CLAUDE.md" && fail "check 4: AGENTFW markers still present after uninstall"
[ "$(grep -cF "$SENTINEL" "$SB2/CLAUDE.md")" -eq "$SENTINEL_COUNT_BEFORE" ] || fail "check 4: sentinel line count changed across uninstall"
grep -q '^## MCP Usage Instructions' "$SB2/CLAUDE.md" || fail "check 4: user MCP section lost during uninstall"
[ -e "$SB2/skills/agentfw" ] && fail "check 4: skills/agentfw still present after uninstall"
ls "$SB2/agents/"agentfw-*.md > /dev/null 2>&1 && fail "check 4: agentfw-*.md agent files still present after uninstall"
pass "uninstall — post-uninstall file cmp-identical to snapshot-minus-block, zero AGENTFW markers, sentinel count unchanged ($SENTINEL_COUNT_BEFORE), user MCP section intact, skill + agents removed"

# ==============================================================================================
# (5) Uninstall where CLAUDE.md was ONLY the block — file must be removed.
# ==============================================================================================
SB3="$(mktemp -d)"; SANDBOXES+=("$SB3")
CLAUDE_DIR="$SB3" bash "$INSTALL" install > /dev/null
[ "$(count_begin "$SB3")" -eq 1 ] || fail "check 5: install into empty sandbox did not produce one block"
CLAUDE_DIR="$SB3" bash "$INSTALL" uninstall > /dev/null
[ -e "$SB3/CLAUDE.md" ] && fail "check 5: block-only CLAUDE.md not removed on uninstall"
pass "block-only uninstall — CLAUDE.md removed when nothing but the AgentFW block remained"

printf 'ALL CHECKS PASSED (5/5)\n'
