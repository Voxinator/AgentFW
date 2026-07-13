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
# The validator is packaged into installs from a single source (repo tools/validate-plan);
# the installer refuses honestly without it, so the test requires the real file.
[ -f "$REPO_ROOT/tools/validate-plan" ] || fail "repo tools/validate-plan missing — installer packages it; cannot test without it"
cp -p "$REPO_ROOT/tools/validate-plan" "$SRC/tools/validate-plan"
[ -f "$REPO_ROOT/tools/fixtures/plan-good.md" ] || fail "repo tools/fixtures/plan-good.md missing — needed to execute the sandbox validator"
INSTALL="$SRC/tools/agentfw-install"
[ -x "$INSTALL" ] || fail "installer is not executable: $INSTALL"

# Anchored to line start like the installer's own detection — a bare substring count would
# false-count PROSE mentions of the marker names in user content (see check 6) — and
# code-fence-aware like the installer's scanners: a column-0 ``` line toggles fence state and
# fenced marker lines are invisible (see check 8). A plain grep can track neither.
FENCE_GATE='/^```/ { infence = !infence }
'
count_begin() {
  [ -f "$1/CLAUDE.md" ] || { printf '0'; return; }
  awk "$FENCE_GATE"'
    !infence && /^<!-- AGENTFW:BEGIN/ { n++ }
    END { print n + 0 }
  ' "$1/CLAUDE.md"
}

# Mirror of the installer's uninstall strip: remove every REAL (unfenced) AGENTFW block plus
# the single installer-added separator blank line before it; fenced marker examples are user
# content and pass through untouched. Used to compute EXPECTED post-uninstall files.
strip_blocks() {
  awk "$FENCE_GATE"'
    { L[NR] = $0
      if (!infence && $0 ~ /^<!-- AGENTFW:BEGIN/) T[NR] = 1
      else if (!infence && $0 ~ /^<!-- AGENTFW:END/) T[NR] = 2
    }
    END {
      inb = 0
      for (i = 1; i <= NR; i++) {
        if (T[i] == 1) {
          inb = 1; del[i] = 1
          if (i > 1 && L[i-1] ~ /^[[:space:]]*$/ && !del[i-1]) del[i-1] = 1
        } else if (T[i] == 2) {
          del[i] = 1; inb = 0
        } else if (inb) del[i] = 1
      }
      for (i = 1; i <= NR; i++) if (!del[i]) print L[i]
    }
  ' "$1"
}

# ==============================================================================================
# (1) Fresh install into a sandbox seeded with a user sentinel line.
# ==============================================================================================
SB1="$(mktemp -d)"; SANDBOXES+=("$SB1")
printf '%s\n' "$SENTINEL" > "$SB1/CLAUDE.md"

CLAUDE_DIR="$SB1" bash "$INSTALL" install > /dev/null

[ "$(count_begin "$SB1")" -eq 1 ] || fail "check 1: expected exactly one AGENTFW:BEGIN, got $(count_begin "$SB1")"
grep -qF "$SENTINEL" "$SB1/CLAUDE.md" || fail "check 1: user sentinel lost on fresh install"
grep -q '^<!-- AGENTFW:END' "$SB1/CLAUDE.md" || fail "check 1: END marker missing"
[ -s "$SB1/skills/agentfw/SKILL.md" ] || fail "check 1: skill not installed"
for a in agentfw-implementer agentfw-verifier agentfw-plan-critic; do
  [ -s "$SB1/agents/$a.md" ] || fail "check 1: agent $a.md not installed"
done
[ -d "$SB1/skills/agentfw/policy" ] || fail "check 1: policy/ dir not copied into skill"
ls "$SB1/skills/agentfw/policy/"*.md > /dev/null 2>&1 || fail "check 1: policy/ copy is empty"
[ -f "$SB1/skills/agentfw/.install-manifest" ] || fail "check 1: install manifest not written"
grep -q '^agents/agentfw-implementer.md$' "$SB1/skills/agentfw/.install-manifest" || fail "check 1: manifest missing agent entry"
pass "fresh install — block present exactly once, sentinel preserved, skill + 3 agents + policy/ + manifest installed"

# ==============================================================================================
# (1b) Packaged validator: present, executable, and EXECUTED inside the sandbox against a
#      staged copy of the plan-good fixture — packaging asserted by execution, not inventory.
# ==============================================================================================
VP="$SB1/skills/agentfw/tools/validate-plan"
[ -f "$VP" ] || fail "check 1b: validator not packaged into the installed skill ($VP)"
[ -x "$VP" ] || fail "check 1b: packaged validator is not executable"
cp "$REPO_ROOT/tools/fixtures/plan-good.md" "$SB1/staged-plan-good.md"
VOUT="$("$VP" "$SB1/staged-plan-good.md" 2>&1)" || fail "check 1b: sandbox validator exited non-zero on plan-good fixture: $VOUT"
printf '%s\n' "$VOUT" | grep -q 'PASS' || fail "check 1b: sandbox validator output lacks PASS: $VOUT"
pass "sandbox validator — installed copy is executable and EXECUTED in the sandbox against the staged plan-good fixture (exit 0, PASS output)"

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
strip_blocks "$SNAP" > "$EXPECTED"

# Hostile seed: a USER-created agent that matches the agentfw-* name pattern. Uninstall is
# manifest-driven and must NOT remove it (a glob would).
mkdir -p "$SB2/agents"
CUSTOM="$SB2/agents/agentfw-custom.md"
CUSTOM_REF="$SRC/agentfw-custom.reference"
printf '%s\n%s\n' '# user-owned agent — not installed by AgentFW' "$SENTINEL" > "$CUSTOM"
cp "$CUSTOM" "$CUSTOM_REF"
[ -f "$SB2/skills/agentfw/.install-manifest" ] || fail "check 4: manifest absent before uninstall (upgrade should have written it)"

CLAUDE_DIR="$SB2" bash "$INSTALL" uninstall > "$SB2/uninstall.log" 2>&1 || { cat "$SB2/uninstall.log" >&2; fail "check 4: uninstall exited non-zero"; }

cmp -s "$SB2/CLAUDE.md" "$EXPECTED" || fail "check 4: post-uninstall CLAUDE.md is not byte-identical to snapshot-minus-block (user content altered)"
grep -q 'AGENTFW' "$SB2/CLAUDE.md" && fail "check 4: AGENTFW markers still present after uninstall"
[ "$(grep -cF "$SENTINEL" "$SB2/CLAUDE.md")" -eq "$SENTINEL_COUNT_BEFORE" ] || fail "check 4: sentinel line count changed across uninstall"
grep -q '^## MCP Usage Instructions' "$SB2/CLAUDE.md" || fail "check 4: user MCP section lost during uninstall"
[ -e "$SB2/skills/agentfw" ] && fail "check 4: skills/agentfw still present after uninstall"
for a in agentfw-implementer agentfw-verifier agentfw-plan-critic; do
  [ -e "$SB2/agents/$a.md" ] && fail "check 4: shipped agent $a.md still present after uninstall"
done
pass "uninstall — post-uninstall file cmp-identical to snapshot-minus-block, zero AGENTFW markers, sentinel count unchanged ($SENTINEL_COUNT_BEFORE), user MCP section intact, skill + 3 shipped agents removed"

# ==============================================================================================
# (4b) Hostile-uninstall assertions: user file survives; manifest consumed.
# ==============================================================================================
[ -f "$CUSTOM" ] || fail "check 4b: user-created agentfw-custom.md was DELETED by uninstall"
cmp -s "$CUSTOM" "$CUSTOM_REF" || fail "check 4b: agentfw-custom.md content altered by uninstall"
grep -qi 'manifest' "$SB2/uninstall.log" || fail "check 4b: uninstall log does not mention the manifest (manifest not consumed?)"
[ -e "$SB2/skills/agentfw/.install-manifest" ] && fail "check 4b: manifest still present after uninstall"
pass "hostile uninstall — user-created agentfw-custom.md survived byte-identical while the three shipped agents were removed; manifest was present before uninstall and consumed by it"

# ==============================================================================================
# (5) Uninstall where CLAUDE.md was ONLY the block — file must be removed.
# ==============================================================================================
SB3="$(mktemp -d)"; SANDBOXES+=("$SB3")
CLAUDE_DIR="$SB3" bash "$INSTALL" install > /dev/null
[ "$(count_begin "$SB3")" -eq 1 ] || fail "check 5: install into empty sandbox did not produce one block"
CLAUDE_DIR="$SB3" bash "$INSTALL" uninstall > /dev/null
[ -e "$SB3/CLAUDE.md" ] && fail "check 5: block-only CLAUDE.md not removed on uninstall"
pass "block-only uninstall — CLAUDE.md removed when nothing but the AgentFW block remained"

# ==============================================================================================
# (6) PROSE mentions of the marker names in user content must be inert (off-contract probe
#     hardening): install → upgrade → uninstall over a file whose prose says "AGENTFW:BEGIN"
#     and "AGENTFW:END" mid-sentence (including both on the SAME line). A substring-matching
#     installer treats the prose as a block and deletes to EOF.
# ==============================================================================================
SB4="$(mktemp -d)"; SANDBOXES+=("$SB4")
cat > "$SB4/CLAUDE.md" <<'EOF'
I once wrote a doc about AGENTFW:BEGIN markers and how AGENTFW:END works.
USER-SENTINEL: keep me
Mid-sentence, same line: AGENTFW:BEGIN then AGENTFW:END must both be inert prose.
EOF
ORIG4="$SRC/prose-original.snapshot"
cp "$SB4/CLAUDE.md" "$ORIG4"

CLAUDE_DIR="$SB4" bash "$INSTALL" install > /dev/null || fail "check 6: install exited non-zero on prose-mention file"
[ "$(count_begin "$SB4")" -eq 1 ] || fail "check 6: expected exactly one real block after install, got $(count_begin "$SB4")"
grep -qF "$SENTINEL" "$SB4/CLAUDE.md" || fail "check 6: sentinel lost on install over prose mentions"
grep -qF 'I once wrote a doc about AGENTFW:BEGIN markers' "$SB4/CLAUDE.md" || fail "check 6: prose mention line destroyed by install"
grep -qF 'AGENTFW:BEGIN then AGENTFW:END must both be inert prose' "$SB4/CLAUDE.md" || fail "check 6: same-line prose mention destroyed by install"
# Byte-level: post-install file minus the real block must equal the original file.
STRIPPED4="$SRC/prose-stripped"
strip_blocks "$SB4/CLAUDE.md" > "$STRIPPED4"
cmp -s "$STRIPPED4" "$ORIG4" || fail "check 6: user lines not byte-preserved by install (post-install minus block != original)"

CLAUDE_DIR="$SB4" bash "$INSTALL" upgrade > /dev/null || fail "check 6: upgrade exited non-zero on prose-mention file"
[ "$(count_begin "$SB4")" -eq 1 ] || fail "check 6: upgrade produced $(count_begin "$SB4") real blocks (expected 1)"
grep -qF 'I once wrote a doc about AGENTFW:BEGIN markers' "$SB4/CLAUDE.md" || fail "check 6: prose mention destroyed by upgrade"
grep -qF "$SENTINEL" "$SB4/CLAUDE.md" || fail "check 6: sentinel lost on upgrade over prose mentions"

CLAUDE_DIR="$SB4" bash "$INSTALL" uninstall > /dev/null || fail "check 6: uninstall exited non-zero on prose-mention file"
cmp -s "$SB4/CLAUDE.md" "$ORIG4" || fail "check 6: post-uninstall file not byte-identical to the original prose file (prose mentions or user lines altered)"
pass "prose-mention immunity — install/upgrade/uninstall over prose 'AGENTFW:BEGIN'/'AGENTFW:END' mentions (incl. same-line): real block managed, prose + sentinel byte-preserved, uninstall restores the original file cmp-identical"

# ==============================================================================================
# (7) Unterminated real BEGIN marker (no END line): every mutating subcommand must REFUSE and
#     leave the file byte-identical — never delete to EOF.
# ==============================================================================================
SB5="$(mktemp -d)"; SANDBOXES+=("$SB5")
cat > "$SB5/CLAUDE.md" <<'EOF'
user line before
<!-- AGENTFW:BEGIN r9 -->
stale half-block content
USER-SENTINEL: keep me
EOF
ORIG5="$SRC/unterminated-original.snapshot"
cp "$SB5/CLAUDE.md" "$ORIG5"
for sub in install upgrade uninstall; do
  if CLAUDE_DIR="$SB5" bash "$INSTALL" "$sub" > "$SB5/$sub.log" 2>&1; then
    fail "check 7: $sub did NOT refuse on an unterminated AGENTFW:BEGIN block"
  fi
  grep -qi 'malformed' "$SB5/$sub.log" || fail "check 7: $sub refusal message does not name the malformed marker structure"
  cmp -s "$SB5/CLAUDE.md" "$ORIG5" || fail "check 7: $sub modified the file despite refusing (must be byte-identical)"
  [ -e "$SB5/skills/agentfw" ] && fail "check 7: $sub created skills/agentfw despite refusing"
done
CLAUDE_DIR="$SB5" bash "$INSTALL" status > "$SB5/status.log" 2>&1 || fail "check 7: status exited non-zero on unterminated block"
grep -qi 'malformed' "$SB5/status.log" || fail "check 7: status does not warn about the malformed marker structure"
cmp -s "$SB5/CLAUDE.md" "$ORIG5" || fail "check 7: status modified the file"
pass "unterminated-block refusal — install/upgrade/uninstall all refuse (named 'malformed' error), file byte-identical, no assets installed; status warns without touching the file"

# ==============================================================================================
# (8) FENCED verbatim marker example: a well-paired real-marker example inside a user's ```
#     code fence at column 0 (with a sentinel line BETWEEN the fenced markers) must be
#     INVISIBLE to every scanner. install → real block appended, fenced example (incl. its
#     inner sentinel) byte-preserved; upgrade → same; uninstall → file cmp-identical to the
#     pre-install snapshot. A fence-unaware scanner treats the example as the real block:
#     upgrade replaces it and uninstall deletes it.
# ==============================================================================================
SB6="$(mktemp -d)"; SANDBOXES+=("$SB6")
FENCED_SENTINEL='FENCED-EXAMPLE-SENTINEL: I live between the fenced markers'
cat > "$SB6/CLAUDE.md" <<'EOF'
Prose before the example.
USER-SENTINEL: keep me

This is how the installed markers look:

```
<!-- AGENTFW:BEGIN r9 -->
FENCED-EXAMPLE-SENTINEL: I live between the fenced markers
<!-- AGENTFW:END r9 -->
```

Prose after the example.
EOF
ORIG6="$SRC/fenced-original.snapshot"
cp "$SB6/CLAUDE.md" "$ORIG6"

CLAUDE_DIR="$SB6" bash "$INSTALL" install > /dev/null || fail "check 8: install exited non-zero on fenced-example file"
[ "$(count_begin "$SB6")" -eq 1 ] || fail "check 8: expected exactly one REAL block after install, got $(count_begin "$SB6")"
[ "$(grep -c '^<!-- AGENTFW:BEGIN' "$SB6/CLAUDE.md")" -eq 2 ] || fail "check 8: raw column-0 BEGIN line count != 2 after install (fenced example + real block)"
grep -qF "$FENCED_SENTINEL" "$SB6/CLAUDE.md" || fail "check 8: fenced inner sentinel destroyed by install (fenced example treated as real block)"
strip_blocks "$SB6/CLAUDE.md" > "$SRC/fenced-stripped"
cmp -s "$SRC/fenced-stripped" "$ORIG6" || fail "check 8: post-install file minus REAL block != original (fenced example or user prose altered by install)"

CLAUDE_DIR="$SB6" bash "$INSTALL" upgrade > /dev/null || fail "check 8: upgrade exited non-zero on fenced-example file"
[ "$(count_begin "$SB6")" -eq 1 ] || fail "check 8: upgrade produced $(count_begin "$SB6") REAL blocks (expected 1)"
[ "$(grep -c '^<!-- AGENTFW:BEGIN' "$SB6/CLAUDE.md")" -eq 2 ] || fail "check 8: raw column-0 BEGIN line count != 2 after upgrade"
grep -qF "$FENCED_SENTINEL" "$SB6/CLAUDE.md" || fail "check 8: fenced inner sentinel destroyed by upgrade (upgrade replaced the fenced example)"
strip_blocks "$SB6/CLAUDE.md" > "$SRC/fenced-stripped"
cmp -s "$SRC/fenced-stripped" "$ORIG6" || fail "check 8: post-upgrade file minus REAL block != original (fenced example or user prose altered by upgrade)"

CLAUDE_DIR="$SB6" bash "$INSTALL" uninstall > /dev/null || fail "check 8: uninstall exited non-zero on fenced-example file"
cmp -s "$SB6/CLAUDE.md" "$ORIG6" || fail "check 8: post-uninstall file not cmp-identical to the pre-install snapshot (fenced example deleted or user prose altered)"
pass "fenced marker-example immunity — install/upgrade/uninstall over a column-0 \`\`\` fence containing well-paired verbatim markers + inner sentinel: real block managed exactly once, fenced example byte-preserved throughout, uninstall restores the pre-install file cmp-identical"

printf 'ALL CHECKS PASSED (10/10)\n'
