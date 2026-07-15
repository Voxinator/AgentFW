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
PASS_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$*"; }

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

# Anchored to line start AND word-bounded (trailing space after BEGIN/END) like the
# installer's own detection — a bare substring count would false-count PROSE mentions of the
# marker names in user content (see check 6), and an un-word-bounded prefix would match
# lookalikes such as '<!-- AGENTFW:BEGINNING …' (see check 13) — and code-fence-aware via the
# CommonMark-aware tracker MIRRORED from the installer's FENCE_TRACKER: an opening fence is a
# run of >=3 backticks or >=3 tildes (up to 3 leading spaces; backtick info strings may not
# contain a backtick); it closes only on a line of the SAME character with run length >= the
# opening run (up to 3 leading spaces, only trailing whitespace — spaces/tabs/CR, so CRLF
# fences close too — after); shorter or other-character runs are content; fenced marker lines
# are invisible (see checks 8-11 and 15). A plain grep can track none of this.
FENCE_TRACKER='{
  ftl = $0
  sub(/^ ? ? ?/, "", ftl)
  ftc = substr(ftl, 1, 1)
  if (infence) {
    if (ftc == fchar) {
      ftn = 1
      while (substr(ftl, ftn + 1, 1) == fchar) ftn++
      if (ftn >= flen && substr(ftl, ftn + 1) ~ /^[ \t\r]*$/) infence = 0
    }
  } else if (ftc == "`" || ftc == "~") {
    ftn = 1
    while (substr(ftl, ftn + 1, 1) == ftc) ftn++
    if (ftn >= 3 && (ftc == "~" || substr(ftl, ftn + 1) !~ /`/)) {
      infence = 1; fchar = ftc; flen = ftn
    }
  }
}
'
count_begin() {
  [ -f "$1/CLAUDE.md" ] || { printf '0'; return; }
  awk "$FENCE_TRACKER"'
    !infence && /^<!-- AGENTFW:BEGIN / { n++ }
    END { print n + 0 }
  ' "$1/CLAUDE.md"
}

# Mirror of the installer's uninstall strip: remove every REAL (unfenced) AGENTFW block plus
# the single installer-added separator blank line before it; fenced marker examples are user
# content and pass through untouched. Used to compute EXPECTED post-uninstall files.
strip_blocks() {
  awk "$FENCE_TRACKER"'
    { L[NR] = $0
      if (!infence && $0 ~ /^<!-- AGENTFW:BEGIN /) T[NR] = 1
      else if (!infence && $0 ~ /^<!-- AGENTFW:END /) T[NR] = 2
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

# ==============================================================================================
# (9) TILDE-fence immunity (Sol's destructive repro): a well-paired verbatim marker example
#     inside a ~~~ fence (with an inner sentinel) must be invisible to every scanner.
#     install → real block appended, fenced example byte-preserved; uninstall → cmp-identical.
# ==============================================================================================
SB7="$(mktemp -d)"; SANDBOXES+=("$SB7")
TILDE_SENTINEL='TILDE-SENTINEL: I live between the tilde-fenced markers'
cat > "$SB7/CLAUDE.md" <<'EOF'
Prose before the tilde example.
USER-SENTINEL: keep me

~~~text
<!-- AGENTFW:BEGIN r9 -->
TILDE-SENTINEL: I live between the tilde-fenced markers
<!-- AGENTFW:END r9 -->
~~~

Prose after the tilde example.
EOF
ORIG7="$SRC/tilde-original.snapshot"
cp "$SB7/CLAUDE.md" "$ORIG7"

CLAUDE_DIR="$SB7" bash "$INSTALL" install > /dev/null || fail "check 9: install exited non-zero on tilde-fenced example file"
[ "$(count_begin "$SB7")" -eq 1 ] || fail "check 9: expected exactly one REAL block after install, got $(count_begin "$SB7")"
grep -qF "$TILDE_SENTINEL" "$SB7/CLAUDE.md" || fail "check 9: tilde-fenced inner sentinel destroyed by install (tilde fence not tracked)"
strip_blocks "$SB7/CLAUDE.md" > "$SRC/tilde-stripped"
cmp -s "$SRC/tilde-stripped" "$ORIG7" || fail "check 9: post-install file minus REAL block != original (tilde example or user prose altered)"
CLAUDE_DIR="$SB7" bash "$INSTALL" uninstall > /dev/null || fail "check 9: uninstall exited non-zero on tilde-fenced example file"
cmp -s "$SB7/CLAUDE.md" "$ORIG7" || fail "check 9: post-uninstall file not cmp-identical to the pre-install snapshot (tilde-fenced example deleted or altered)"
pass "tilde-fence immunity — ~~~ fence containing well-paired verbatim markers + inner sentinel: install/uninstall roundtrip cmp-identical, sentinel intact throughout"

# ==============================================================================================
# (10) FOUR-BACKTICK fence containing literal ``` lines AND a well-paired marker example: the
#      tracker must NOT close the ```` fence on the inner ``` runs (shorter run = content).
# ==============================================================================================
SB8="$(mktemp -d)"; SANDBOXES+=("$SB8")
QUAD_SENTINEL='QUAD-SENTINEL: I live inside the four-backtick fence'
cat > "$SB8/CLAUDE.md" <<'EOF'
Prose before the four-backtick example.
USER-SENTINEL: keep me

````markdown
```
<!-- AGENTFW:BEGIN r9 -->
QUAD-SENTINEL: I live inside the four-backtick fence
<!-- AGENTFW:END r9 -->
```
````

Prose after the four-backtick example.
EOF
ORIG8="$SRC/quad-original.snapshot"
cp "$SB8/CLAUDE.md" "$ORIG8"

CLAUDE_DIR="$SB8" bash "$INSTALL" install > /dev/null || fail "check 10: install exited non-zero on four-backtick example file"
[ "$(count_begin "$SB8")" -eq 1 ] || fail "check 10: expected exactly one REAL block after install, got $(count_begin "$SB8") (inner \`\`\` closed the \`\`\`\` fence?)"
grep -qF "$QUAD_SENTINEL" "$SB8/CLAUDE.md" || fail "check 10: four-backtick inner sentinel destroyed by install"
strip_blocks "$SB8/CLAUDE.md" > "$SRC/quad-stripped"
cmp -s "$SRC/quad-stripped" "$ORIG8" || fail "check 10: post-install file minus REAL block != original (four-backtick example altered)"
CLAUDE_DIR="$SB8" bash "$INSTALL" uninstall > /dev/null || fail "check 10: uninstall exited non-zero on four-backtick example file"
cmp -s "$SB8/CLAUDE.md" "$ORIG8" || fail "check 10: post-uninstall file not cmp-identical (four-backtick example or its inner \`\`\` lines altered)"
pass "four-backtick fence — \`\`\`\` fence containing literal \`\`\` lines + well-paired markers + sentinel: inner shorter runs did NOT close the fence; roundtrip cmp-identical"

# ==============================================================================================
# (11) 3-space-INDENTED fence: opener and closer indented by 3 spaces are still fences; the
#      marker example inside is invisible; roundtrip cmp-identical.
# ==============================================================================================
SB9="$(mktemp -d)"; SANDBOXES+=("$SB9")
INDENT_SENTINEL='INDENT-SENTINEL: I live inside the indented fence'
cat > "$SB9/CLAUDE.md" <<'EOF'
Prose before the indented example.
USER-SENTINEL: keep me

   ```text
<!-- AGENTFW:BEGIN r9 -->
INDENT-SENTINEL: I live inside the indented fence
<!-- AGENTFW:END r9 -->
   ```

Prose after the indented example.
EOF
ORIG9="$SRC/indent-original.snapshot"
cp "$SB9/CLAUDE.md" "$ORIG9"

CLAUDE_DIR="$SB9" bash "$INSTALL" install > /dev/null || fail "check 11: install exited non-zero on indented-fence file"
[ "$(count_begin "$SB9")" -eq 1 ] || fail "check 11: expected exactly one REAL block after install, got $(count_begin "$SB9") (3-space-indented fence not recognized?)"
grep -qF "$INDENT_SENTINEL" "$SB9/CLAUDE.md" || fail "check 11: indented-fence inner sentinel destroyed by install"
CLAUDE_DIR="$SB9" bash "$INSTALL" uninstall > /dev/null || fail "check 11: uninstall exited non-zero on indented-fence file"
cmp -s "$SB9/CLAUDE.md" "$ORIG9" || fail "check 11: post-uninstall file not cmp-identical (indented fence example altered)"
pass "indented fence — 3-space-indented \`\`\` fence with verbatim markers + sentinel: roundtrip cmp-identical"

# ==============================================================================================
# (12) UNCLOSED fence at EOF (backtick AND tilde): every mutating subcommand must REFUSE with
#      an error naming the unclosed fence, leave the file byte-identical, and create no assets;
#      status warns but exits 0.
# ==============================================================================================
for FKIND in backtick tilde; do
  SBU="$(mktemp -d)"; SANDBOXES+=("$SBU")
  if [ "$FKIND" = backtick ]; then OPENER='```markdown'; else OPENER='~~~text'; fi
  printf '%s\n%s\n%s\n' 'user line before' "$OPENER" 'trailing content after the unclosed fence' > "$SBU/CLAUDE.md"
  ORIGU="$SRC/unclosed-$FKIND.snapshot"
  cp "$SBU/CLAUDE.md" "$ORIGU"
  for sub in install upgrade uninstall; do
    if CLAUDE_DIR="$SBU" bash "$INSTALL" "$sub" > "$SBU/$sub.log" 2>&1; then
      fail "check 12: $sub did NOT refuse on an unclosed $FKIND fence"
    fi
    grep -qi 'unclosed' "$SBU/$sub.log" || fail "check 12: $sub refusal message does not say 'unclosed' ($FKIND)"
    cmp -s "$SBU/CLAUDE.md" "$ORIGU" || fail "check 12: $sub modified the file despite refusing ($FKIND; must be byte-identical)"
    [ -e "$SBU/skills/agentfw" ] && fail "check 12: $sub created skills/agentfw despite refusing ($FKIND)"
  done
  CLAUDE_DIR="$SBU" bash "$INSTALL" status > "$SBU/status.log" 2>&1 || fail "check 12: status exited non-zero on unclosed $FKIND fence"
  grep -qi 'unclosed' "$SBU/status.log" || fail "check 12: status does not warn about the unclosed $FKIND fence"
  cmp -s "$SBU/CLAUDE.md" "$ORIGU" || fail "check 12: status modified the file ($FKIND)"
done
pass "unclosed-fence refusal — unclosed backtick AND tilde fences: install/upgrade/uninstall all refuse (error says 'unclosed'), file byte-identical, no assets created; status warns and exits 0"

# ==============================================================================================
# (13) LOOKALIKE marker: '<!-- AGENTFW:BEGINNING of notes -->' is ordinary user content — it
#      must neither match the (word-bounded) marker regexes nor cause a refusal. install
#      proceeds normally; uninstall restores the original file cmp-identical.
# ==============================================================================================
SB10="$(mktemp -d)"; SANDBOXES+=("$SB10")
cat > "$SB10/CLAUDE.md" <<'EOF'
<!-- AGENTFW:BEGINNING of notes -->
USER-SENTINEL: keep me
<!-- AGENTFW:ENDNOTE also just user content -->
EOF
ORIG10="$SRC/lookalike-original.snapshot"
cp "$SB10/CLAUDE.md" "$ORIG10"

CLAUDE_DIR="$SB10" bash "$INSTALL" install > /dev/null || fail "check 13: install refused or failed on lookalike marker lines (false refusal)"
[ "$(count_begin "$SB10")" -eq 1 ] || fail "check 13: expected exactly one REAL block after install, got $(count_begin "$SB10") (lookalike counted as a marker?)"
grep -qF '<!-- AGENTFW:BEGINNING of notes -->' "$SB10/CLAUDE.md" || fail "check 13: lookalike BEGINNING line destroyed by install"
grep -qF '<!-- AGENTFW:ENDNOTE also just user content -->' "$SB10/CLAUDE.md" || fail "check 13: lookalike ENDNOTE line destroyed by install"
grep -qF "$SENTINEL" "$SB10/CLAUDE.md" || fail "check 13: user sentinel lost on install over lookalike markers"
CLAUDE_DIR="$SB10" bash "$INSTALL" uninstall > /dev/null || fail "check 13: uninstall exited non-zero on lookalike file"
cmp -s "$SB10/CLAUDE.md" "$ORIG10" || fail "check 13: post-uninstall file not cmp-identical to the original (lookalike lines stripped or altered)"
pass "lookalike immunity — '<!-- AGENTFW:BEGINNING of notes -->' + user lines: install proceeded normally (no false refusal), block added exactly once, all user lines preserved, uninstall restored cmp-identical"

# ==============================================================================================
# (14) Capability state: install packages the adapter's capability.yaml into the skill;
#      status writes active-capabilities.yaml with PER-RULE probe results reflecting REAL
#      entries in the sandbox settings.json's permissions.deny (present rules yes, absent
#      ones no) plus the aggregate — a PARTIAL real deny set must aggregate to 'partial'.
# ==============================================================================================
SB11="$(mktemp -d)"; SANDBOXES+=("$SB11")
printf '{"permissions":{"deny":["Read(~/.ssh/**)","Read(**/.env)","Bash(git push --force:*)"]}}\n' > "$SB11/settings.json"
CLAUDE_DIR="$SB11" bash "$INSTALL" install > /dev/null || fail "check 14: install exited non-zero"
[ -f "$SB11/skills/agentfw/capability.yaml" ] || fail "check 14: capability.yaml not packaged into the installed skill"
cmp -s "$SB11/skills/agentfw/capability.yaml" "$SRC/adapters/claude-code/capability.yaml" || fail "check 14: packaged capability.yaml differs from the adapter source"
[ -e "$SB11/skills/agentfw/active-capabilities.yaml" ] && fail "check 14: active-capabilities.yaml exists before any status run (must be status-generated)"
CLAUDE_DIR="$SB11" bash "$INSTALL" status > "$SB11/status.log" 2>&1 || fail "check 14: status exited non-zero"
ACT="$SB11/skills/agentfw/active-capabilities.yaml"
[ -f "$ACT" ] || fail "check 14: status did not write active-capabilities.yaml"
grep -q 'generated by agentfw-install status' "$ACT" || fail "check 14: active-capabilities.yaml lacks the generated-by header"
grep -q '^  deny_ssh: yes$' "$ACT" || fail "check 14: deny_ssh not reported yes despite .ssh deny rule in settings.json"
grep -q '^  deny_env: yes$' "$ACT" || fail "check 14: deny_env not reported yes despite .env deny rule"
grep -q '^  deny_git_push_force: yes$' "$ACT" || fail "check 14: deny_git_push_force not reported yes despite the deny rule"
grep -q '^  deny_aws: no$' "$ACT" || fail "check 14: deny_aws not reported no (rule absent from settings.json)"
grep -q '^  deny_secrets: no$' "$ACT" || fail "check 14: deny_secrets not reported no (rule absent)"
grep -q '^deterministic_permissions_configured: partial$' "$ACT" || fail "check 14: aggregate not 'partial' for a partial real deny set"
grep -q '^  agentfw_implementer: yes$' "$ACT" || fail "check 14: agentfw_implementer not reported yes"
grep -q '^  agentfw_verifier: yes$' "$ACT" || fail "check 14: agentfw_verifier not reported yes"
grep -q '^  agentfw_plan_critic: yes$' "$ACT" || fail "check 14: agentfw_plan_critic not reported yes"
grep -q '^validator_present: yes$' "$ACT" || fail "check 14: validator_present not reported yes"
grep -q '^manifest_present: yes$' "$ACT" || fail "check 14: manifest_present not reported yes"
grep -q 'deny .aws:               no' "$SB11/status.log" || fail "check 14: status console output does not mirror the per-rule detail"
grep -q 'deterministic_permissions_configured: partial' "$SB11/status.log" || fail "check 14: status console output does not mirror the 'partial' aggregate"
pass "active-capabilities — capability.yaml packaged cmp-identical into the skill; status probe wrote per-rule results for REAL deny entries (ssh/env/git-push-force yes, aws/secrets no) with aggregate 'partial', mirrored on the console"

# ==============================================================================================
# (14b) HOSTILE probe seed: an empty deny array with every rule SIGNATURE planted in
#       permissions.allow and in a _comment. A whole-file substring grep reports all five as
#       active deny rules; the JSON-parsing probe must report all five no, aggregate false.
# ==============================================================================================
SB11B="$(mktemp -d)"; SANDBOXES+=("$SB11B")
cat > "$SB11B/settings.json" <<'EOF'
{
  "_comment": "docs mention .env .aws secrets git push --force and ~/.ssh here — prose, not rules",
  "permissions": {
    "allow": ["Read(~/.ssh/**)", "Read(./.env)", "Read(~/.aws/**)", "Read(**/secrets/**)", "Bash(git push --force:*)"],
    "deny": []
  }
}
EOF
CLAUDE_DIR="$SB11B" bash "$INSTALL" install > /dev/null || fail "check 14b: install exited non-zero"
CLAUDE_DIR="$SB11B" bash "$INSTALL" status > "$SB11B/status.log" 2>&1 || fail "check 14b: status exited non-zero"
ACTB="$SB11B/skills/agentfw/active-capabilities.yaml"
[ -f "$ACTB" ] || fail "check 14b: status did not write active-capabilities.yaml"
for k in deny_ssh deny_env deny_aws deny_secrets deny_git_push_force; do
  grep -q "^  $k: no\$" "$ACTB" || fail "check 14b: $k not reported no — signature outside permissions.deny (allow/_comment) counted as an active deny rule"
done
grep -q '^deterministic_permissions_configured: false$' "$ACTB" || fail "check 14b: aggregate not 'false' with an empty deny array"
grep -q 'deterministic_permissions_configured: false' "$SB11B/status.log" || fail "check 14b: console aggregate not 'false'"
grep -q 'deny .ssh:               no' "$SB11B/status.log" || fail "check 14b: console per-rule deny .ssh not 'no' despite the signature living only in allow"
pass "hostile probe seed — empty deny array + all five signatures planted in permissions.allow and a _comment: probe reports every rule no and aggregate false (nothing outside permissions.deny counts)"

# ==============================================================================================
# (14c) MALFORMED settings.json (trailing comma): the probe must report every rule 'unknown'
#       and aggregate 'unknown' — never yes, never a crash; status still exits 0.
# ==============================================================================================
SB11C="$(mktemp -d)"; SANDBOXES+=("$SB11C")
printf '{"permissions":{"deny":["Read(~/.ssh/**)","Read(./.env)",]}}\n' > "$SB11C/settings.json"
CLAUDE_DIR="$SB11C" bash "$INSTALL" install > /dev/null || fail "check 14c: install exited non-zero"
CLAUDE_DIR="$SB11C" bash "$INSTALL" status > "$SB11C/status.log" 2>&1 || fail "check 14c: status exited non-zero on malformed settings.json (must degrade to unknown, not crash)"
ACTC="$SB11C/skills/agentfw/active-capabilities.yaml"
[ -f "$ACTC" ] || fail "check 14c: status did not write active-capabilities.yaml"
for k in deny_ssh deny_env deny_aws deny_secrets deny_git_push_force; do
  grep -q "^  $k: unknown\$" "$ACTC" || fail "check 14c: $k not reported unknown on malformed JSON"
done
grep -q '^deterministic_permissions_configured: unknown$' "$ACTC" || fail "check 14c: aggregate not 'unknown' on malformed JSON"
grep -q 'deterministic_permissions_configured: unknown' "$SB11C/status.log" || fail "check 14c: console aggregate not 'unknown'"
pass "malformed-settings probe — trailing-comma settings.json: status exits 0, every per-rule entry unknown, aggregate unknown (never yes, no crash)"

# ==============================================================================================
# (14d) FULL real deny set (the canonical settings.example.json entries — env requires the
#       broadest form Read(**/.env), so the full trio is seeded): every per-rule entry yes,
#       aggregate true.
# ==============================================================================================
SB11D="$(mktemp -d)"; SANDBOXES+=("$SB11D")
printf '{"permissions":{"deny":["Read(~/.ssh/**)","Read(./.env)","Read(./.env.*)","Read(**/.env)","Read(~/.aws/**)","Read(**/secrets/**)","Bash(git push --force:*)"]}}\n' > "$SB11D/settings.json"
CLAUDE_DIR="$SB11D" bash "$INSTALL" install > /dev/null || fail "check 14d: install exited non-zero"
CLAUDE_DIR="$SB11D" bash "$INSTALL" status > "$SB11D/status.log" 2>&1 || fail "check 14d: status exited non-zero"
ACTD="$SB11D/skills/agentfw/active-capabilities.yaml"
[ -f "$ACTD" ] || fail "check 14d: status did not write active-capabilities.yaml"
for k in deny_ssh deny_env deny_aws deny_secrets deny_git_push_force; do
  grep -q "^  $k: yes\$" "$ACTD" || fail "check 14d: $k not reported yes despite the full canonical deny set"
done
grep -q '^deterministic_permissions_configured: true$' "$ACTD" || fail "check 14d: aggregate not 'true' with all five deny rules present"
grep -q 'deterministic_permissions_configured: true' "$SB11D/status.log" || fail "check 14d: console aggregate not 'true'"
pass "full deny-set probe — the full canonical deny set seeded: every per-rule entry yes, aggregate true"

# ==============================================================================================
# (14e) HOSTILE containment seed (verified release-blocker repro): a NARROWER single-file rule
#       (Read(~/.ssh/known_hosts)) and an UNRELATED command carrying the force-push substring
#       (Bash(echo git push --force is bad:*)) must both report no — containment is decided by
#       canonical-form matching, never substring presence. Read(**/.env) IS the canonical
#       broadest env form, so deny_env is yes; aggregate is partial. settings_schema_valid
#       stays true (well-typed JSON, just weak rules).
# ==============================================================================================
SB11E="$(mktemp -d)"; SANDBOXES+=("$SB11E")
printf '{"permissions":{"deny":["Read(~/.ssh/known_hosts)","Bash(echo git push --force is bad:*)","Read(**/.env)"]}}\n' > "$SB11E/settings.json"
CLAUDE_DIR="$SB11E" bash "$INSTALL" install > /dev/null || fail "check 14e: install exited non-zero"
CLAUDE_DIR="$SB11E" bash "$INSTALL" status > "$SB11E/status.log" 2>&1 || fail "check 14e: status exited non-zero"
ACTE="$SB11E/skills/agentfw/active-capabilities.yaml"
[ -f "$ACTE" ] || fail "check 14e: status did not write active-capabilities.yaml"
grep -q '^  deny_ssh: no$' "$ACTE" || fail "check 14e: deny_ssh not 'no' — narrower single-file rule Read(~/.ssh/known_hosts) counted as covering the whole directory"
grep -q '^  deny_git_push_force: no$' "$ACTE" || fail "check 14e: deny_git_push_force not 'no' — unrelated echo command counted via substring match"
grep -q '^  deny_env: yes$' "$ACTE" || fail "check 14e: deny_env not 'yes' despite the canonical broadest form Read(**/.env)"
grep -q '^  deny_aws: no$' "$ACTE" || fail "check 14e: deny_aws not 'no' (rule absent)"
grep -q '^  deny_secrets: no$' "$ACTE" || fail "check 14e: deny_secrets not 'no' (rule absent)"
grep -q '^  settings_schema_valid: true$' "$ACTE" || fail "check 14e: settings_schema_valid not 'true' on well-typed JSON"
grep -q '^deterministic_permissions_configured: partial$' "$ACTE" || fail "check 14e: aggregate not 'partial' (exactly one canonical rule present)"
grep -q 'deny .ssh:               no' "$SB11E/status.log" || fail "check 14e: console per-rule deny .ssh not 'no'"
grep -q 'deny git push --force:   no' "$SB11E/status.log" || fail "check 14e: console per-rule deny git push --force not 'no'"
pass "hostile containment seed — Read(~/.ssh/known_hosts) and Bash(echo git push --force is bad:*) both report no (canonical-form matching, no substring credit), Read(**/.env) reports yes, aggregate partial, schema diagnostic true"

# ==============================================================================================
# (14f) SCHEMA diagnostic: permissions.deny of an unexpected TYPE (a string, not a list) in
#       otherwise-valid JSON — probe must report settings_schema_valid false, rules no (no deny
#       entries usable), aggregate false; status still exits 0.
# ==============================================================================================
SB11F="$(mktemp -d)"; SANDBOXES+=("$SB11F")
printf '{"permissions":{"deny":"Read(~/.ssh/**)"}}\n' > "$SB11F/settings.json"
CLAUDE_DIR="$SB11F" bash "$INSTALL" install > /dev/null || fail "check 14f: install exited non-zero"
CLAUDE_DIR="$SB11F" bash "$INSTALL" status > "$SB11F/status.log" 2>&1 || fail "check 14f: status exited non-zero on deny-of-wrong-type settings.json"
ACTF="$SB11F/skills/agentfw/active-capabilities.yaml"
[ -f "$ACTF" ] || fail "check 14f: status did not write active-capabilities.yaml"
grep -q '^  settings_schema_valid: false$' "$ACTF" || fail "check 14f: settings_schema_valid not 'false' when permissions.deny is a string"
grep -q '^  deny_ssh: no$' "$ACTF" || fail "check 14f: deny_ssh not 'no' (a non-list deny holds no usable rules)"
grep -q '^deterministic_permissions_configured: false$' "$ACTF" || fail "check 14f: aggregate not 'false'"
grep -q 'settings_schema_valid:   false' "$SB11F/status.log" || fail "check 14f: console does not report the schema diagnostic"
pass "schema diagnostic — permissions.deny of wrong type (string) in valid JSON: settings_schema_valid false, rules no, aggregate false, status exit 0"

# ==============================================================================================
# (14g) FIRST-COMMAND containment (verified release-blocker repro, external review #6): a Bash
#       deny whose --force token appears AFTER a shell operator does not protect force-pushes —
#       'Bash(git push origin main && echo --force:*)' must report no. Glued-operator variant
#       ('main;echo --force') must not smuggle the flag past the cut either. A real first-command
#       force-push with a chained suffix still counts yes.
# ==============================================================================================
SB11G="$(mktemp -d)"; SANDBOXES+=("$SB11G")
printf '{"permissions":{"deny":["Bash(git push origin main && echo --force:*)","Bash(git push origin main;echo --force:*)"]}}\n' > "$SB11G/settings.json"
CLAUDE_DIR="$SB11G" bash "$INSTALL" install > /dev/null || fail "check 14g: install exited non-zero"
CLAUDE_DIR="$SB11G" bash "$INSTALL" status > "$SB11G/status.log" 2>&1 || fail "check 14g: status exited non-zero"
ACTG="$SB11G/skills/agentfw/active-capabilities.yaml"
[ -f "$ACTG" ] || fail "check 14g: status did not write active-capabilities.yaml"
grep -q '^  deny_git_push_force: no$' "$ACTG" || fail "check 14g: --force after a shell operator (&& or glued ;) was credited to git push"
grep -q '^deterministic_permissions_configured: false$' "$ACTG" || fail "check 14g: aggregate not 'false' for operator-smuggled flags"
# Positive control is ISOLATED to the chained entry alone — with a plain canonical entry also
# present, the 'yes' could come from it and over-truncation of the chained form would go unseen.
printf '{"permissions":{"deny":["Bash(git push -f origin main && rm -rf /tmp/x:*)"]}}\n' > "$SB11G/settings.json"
CLAUDE_DIR="$SB11G" bash "$INSTALL" status > "$SB11G/status2.log" 2>&1 || fail "check 14g: status exited non-zero on positive control"
grep -q '^  deny_git_push_force: yes$' "$ACTG" || fail "check 14g: a genuine first-command force-push deny no longer counts (over-truncation)"
pass "first-command containment — Bash(git push origin main && echo --force:*) and the glued ';echo --force' variant both report no (flags after a shell operator are not git push's); a genuine first-command force-push deny still reports yes"

# ==============================================================================================
# (15) CRLF file with a PAIRED fence: '```text\r' opens and '```\r' closes (the trailing CR is
#      trailing whitespace, not fence content) — a well-formed CRLF file must NOT be refused as
#      'unclosed', and its fenced marker example + sentinel must roundtrip cmp-identical.
# ==============================================================================================
SB12="$(mktemp -d)"; SANDBOXES+=("$SB12")
printf 'CRLF prose before.\r\nUSER-SENTINEL: keep me\r\n\r\n```text\r\n<!-- AGENTFW:BEGIN r9 -->\r\nCRLF-SENTINEL: I live inside the CRLF fence\r\n<!-- AGENTFW:END r9 -->\r\n```\r\nCRLF prose after.\r\n' > "$SB12/CLAUDE.md"
ORIG12="$SRC/crlf-original.snapshot"
cp "$SB12/CLAUDE.md" "$ORIG12"

CLAUDE_DIR="$SB12" bash "$INSTALL" install > "$SB12/install.log" 2>&1 || {
  cat "$SB12/install.log" >&2
  fail "check 15: install refused/failed on a well-formed CRLF file (paired CRLF fence misread as unclosed?)"
}
[ "$(count_begin "$SB12")" -eq 1 ] || fail "check 15: expected exactly one REAL block after install, got $(count_begin "$SB12")"
grep -qF 'CRLF-SENTINEL' "$SB12/CLAUDE.md" || fail "check 15: CRLF fenced inner sentinel destroyed by install"
CLAUDE_DIR="$SB12" bash "$INSTALL" uninstall > /dev/null || fail "check 15: uninstall exited non-zero on CRLF file"
cmp -s "$SB12/CLAUDE.md" "$ORIG12" || fail "check 15: post-uninstall CRLF file not byte-identical (CR bytes or fenced example altered)"
pass "CRLF fence — well-formed CRLF file with a paired fence containing a marker example + sentinel: no false 'unclosed' refusal, install/uninstall roundtrip cmp-identical (CR bytes preserved)"

# ==============================================================================================
# (16) MISSING final newline: a CLAUDE.md whose last line is unterminated. append_block must
#      terminate it to place the block (recording the fact as a manifest directive that even
#      survives upgrade's manifest rewrite), and uninstall must strip that added newline again
#      so the restore is byte-identical — no silent final-newline normalization.
# ==============================================================================================
SB13="$(mktemp -d)"; SANDBOXES+=("$SB13")
printf 'first user line\nUSER-SENTINEL: keep me' > "$SB13/CLAUDE.md"   # NO trailing newline
ORIG13="$SRC/no-final-newline.snapshot"
cp "$SB13/CLAUDE.md" "$ORIG13"
[ -n "$(tail -c 1 "$SB13/CLAUDE.md")" ] || fail "check 16: fixture unexpectedly ends with a newline"

CLAUDE_DIR="$SB13" bash "$INSTALL" install > /dev/null || fail "check 16: install exited non-zero on file without a final newline"
[ "$(count_begin "$SB13")" -eq 1 ] || fail "check 16: expected exactly one block after install, got $(count_begin "$SB13")"
grep -qF "$SENTINEL" "$SB13/CLAUDE.md" || fail "check 16: sentinel lost on install over unterminated final line"
grep -qF '#agentfw:no-final-newline' "$SB13/skills/agentfw/.install-manifest" \
  || fail "check 16: manifest does not record the missing final newline"
CLAUDE_DIR="$SB13" bash "$INSTALL" upgrade > /dev/null || fail "check 16: upgrade exited non-zero"
grep -qF '#agentfw:no-final-newline' "$SB13/skills/agentfw/.install-manifest" \
  || fail "check 16: upgrade's manifest rewrite LOST the no-final-newline record"
CLAUDE_DIR="$SB13" bash "$INSTALL" uninstall > /dev/null || fail "check 16: uninstall exited non-zero"
cmp -s "$SB13/CLAUDE.md" "$ORIG13" || fail "check 16: post-uninstall file not byte-identical (final newline normalized in?)"
pass "missing final newline — CLAUDE.md without a trailing newline: install exit 0, record kept through upgrade's manifest rewrite, uninstall restores cmp-identical including the ABSENT final newline"

# ==============================================================================================
# (17) SKILL EXAMPLE ↔ VALIDATOR SYNC: each adapter SKILL.md embeds exactly one example plan
#      block fenced as ```json agentfw-plan, making the SKILL.md itself a valid single-block
#      input to tools/validate-plan. Run the real validator against BOTH files so the shipped
#      examples can never desynchronize from the enforced schema again (the v1.1
#      integration_seam/risk_class regression shipped exactly that way).
# ==============================================================================================
for sk in "$SRC/adapters/claude-code/skills/agentfw/SKILL.md" "$REPO_ROOT/adapters/codex/skills/agentfw/SKILL.md"; do
  [ -f "$sk" ] || fail "check 17: SKILL.md missing: $sk"
  SKOUT="$(python3 "$SRC/tools/validate-plan" "$sk" 2>&1)" \
    || fail "check 17: validate-plan rejected the embedded example in $sk: $SKOUT"
  printf '%s\n' "$SKOUT" | grep -q '^PASS' || fail "check 17: validator output lacks PASS for $sk: $SKOUT"
done
pass "skill example sync — the embedded agentfw-plan example in BOTH adapter SKILL.md files validates against the current schema via tools/validate-plan (exit 0, PASS)"

# ==============================================================================================
# (18) COMMAND RESOLUTION: status must persist both command -v and type for each command-critical
#      utility. The ordinary sandbox proves the five real macOS system paths. Separate sandboxes
#      prove that an exported grep wrapper is classified as a function (not mislabeled as the
#      system grep), an unavailable sqlite3 is explicit and non-fatal, hostile function text is
#      valid YAML, and settings.json remains untouched/absent throughout.
# ==============================================================================================
RESOLUTION_ARGS=()
for utility in grep sed find md5 sqlite3; do
  resolved="$(command -v "$utility")" || fail "check 18a: required macOS system utility missing: $utility"
  case "$resolved" in
    /*) ;;
    *) fail "check 18a: $utility did not resolve to an absolute system path in the ordinary sandbox: $resolved" ;;
  esac
  RESOLUTION_ARGS+=("$utility" "$resolved")
done
python3 - "$ACT" "${RESOLUTION_ARGS[@]}" <<'PY' \
  || fail "check 18a: active-capabilities.yaml did not preserve real command/type resolutions"
import sys
import yaml

path, args = sys.argv[1], sys.argv[2:]
with open(path, encoding="utf-8") as fh:
    data = yaml.safe_load(fh)
resolution = data["command_resolution"]
for utility, expected in zip(args[0::2], args[1::2]):
    actual = resolution[utility]
    assert actual["command_v_status"] == "resolved", (utility, actual)
    assert actual["command_v"] == expected, (utility, actual, expected)
    assert actual["type_status"] == "resolved", (utility, actual)
    assert expected in actual["type"], (utility, actual, expected)
PY
grep -q '^Command resolution (current status shell):$' "$SB11/status.log" \
  || fail "check 18a: status console output lacks the command-resolution report"
pass "command resolution — ordinary status persists exact absolute command -v paths plus type output for grep/sed/find/md5/sqlite3; console mirrors the report"

SB14="$(mktemp -d)"; SANDBOXES+=("$SB14")
CLAUDE_DIR="$SB14" bash "$INSTALL" install > /dev/null || fail "check 18b: install exited non-zero"
[ ! -e "$SB14/settings.json" ] || fail "check 18b: fixture unexpectedly has settings.json before wrapper probe"
CLAUDE_DIR="$SB14" INSTALL="$INSTALL" /bin/bash -s > "$SB14/status.log" 2>&1 <<'BASH' \
  || fail "check 18b: status exited non-zero with an exported grep wrapper"
grep() {
  : "hostile yaml: # [] {} \" ' \\ and a multiline function body"
  /usr/bin/grep "$@"
}
export -f grep
bash "$INSTALL" status
BASH
ACT14="$SB14/skills/agentfw/active-capabilities.yaml"
python3 - "$ACT14" <<'PY' \
  || fail "check 18b: wrapper resolution was mislabeled or active-capabilities.yaml is invalid"
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)
grep = data["command_resolution"]["grep"]
assert grep["command_v_status"] == "resolved", grep
assert grep["command_v"] == "grep", grep
assert grep["type_status"] == "resolved", grep
assert "grep is a function" in grep["type"], grep
assert "hostile yaml: # [] {}" in grep["type"], grep
PY
[ ! -e "$SB14/settings.json" ] || fail "check 18b: status created or changed user settings during wrapper probe"
/usr/bin/grep -q 'grep command -v \[resolved\]: grep' "$SB14/status.log" \
  || fail "check 18b: console did not report wrapper command-v resolution"
pass "command wrapper resolution — exported grep function is recorded via command -v + multiline type output, hostile YAML punctuation parses safely, settings remain absent"

SB15="$(mktemp -d)"; SANDBOXES+=("$SB15")
CLAUDE_DIR="$SB15" bash "$INSTALL" install > /dev/null || fail "check 18c: install exited non-zero"
MINPATH="$SB15/command-path"
mkdir -p "$MINPATH"
for utility in dirname awk sed ls tr date grep find md5; do
  resolved="$(command -v "$utility")" || fail "check 18c: cannot construct restricted PATH; missing $utility"
  ln -s "$resolved" "$MINPATH/$utility"
done
[ ! -e "$SB15/settings.json" ] || fail "check 18c: fixture unexpectedly has settings.json before missing-command probe"
PATH="$MINPATH" CLAUDE_DIR="$SB15" /bin/bash "$INSTALL" status > "$SB15/status.log" 2>&1 \
  || fail "check 18c: status exited non-zero when sqlite3 was unavailable"
ACT15="$SB15/skills/agentfw/active-capabilities.yaml"
python3 - "$ACT15" <<'PY' \
  || fail "check 18c: unavailable sqlite3 was not explicit or generated YAML is invalid"
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)
sqlite = data["command_resolution"]["sqlite3"]
assert sqlite["command_v_status"] == "missing", sqlite
assert sqlite["command_v"] == "", sqlite
assert sqlite["type_status"] == "missing", sqlite
assert "not found" in sqlite["type"], sqlite
PY
[ ! -e "$SB15/settings.json" ] || fail "check 18c: status created or changed user settings during missing-command probe"
grep -q 'sqlite3 command -v \[missing\]:' "$SB15/status.log" \
  || fail "check 18c: console did not report unavailable sqlite3 explicitly"
pass "missing command resolution — sqlite3 absent from a restricted PATH is recorded explicitly, status exits 0, YAML parses, settings remain absent"

printf 'ALL CHECKS PASSED (%d/%d)\n' "$PASS_COUNT" "$PASS_COUNT"
