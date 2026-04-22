# ARTIFACT — r7.6 P1C Fix 3 implementation notes (rev 2, 2026-04-19)

**Worker role:** Fix 3 implementation — back-port variantH anti-child-attachment logic to `probe-variantI-wrapper.sh` + raise `TIMEOUT_PER_TURN` default to 1500s.

**Spec:** `PLAN-r7.6-P1C-fixes-implementation.md` §5.

## 1. File identity

| File | md5 | Line count |
|------|-----|------------|
| `probe-variantI-wrapper.sh` (before) | `301c61af896bec95f6efc63c8a8e342d` | 240 |
| `probe-variantI-wrapper.sh` (after) | `95cef027235f1a4716878640796c016f` | 377 |
| `probe-variantI-wrapper.sh.pre-rev2-fix3` (snapshot) | `301c61af896bec95f6efc63c8a8e342d` | 240 |

**Line-count delta:** +137 lines (240 → 377).

Snapshot matches pre-edit md5 exactly, so rollback via `cp probe-variantI-wrapper.sh.pre-rev2-fix3 probe-variantI-wrapper.sh` restores the pre-Fix-3 state byte-exact.

## 2. Changes by block (post-edit line ranges)

### 2.1 Header comment (new, 2 lines added at top)

Lines 2-3 of the new file:

```
# Fix 3 (rev 2, r7.6-P1C) — anti-child-attachment + timeout raise 2026-04-19
# See PLAN-r7.6-P1C-fixes-implementation.md §5 for rationale.
```

### 2.2 TIMEOUT_PER_TURN raise (1 line modified, line 31)

Before: `TIMEOUT_PER_TURN=900`
After: `: "${TIMEOUT_PER_TURN:=1500}"  # Fix 3 (rev 2, r7.6-P1C): raised 900→1500 for overlay-on long tasks; env-overridable`

The `: "${VAR:=DEFAULT}"` idiom lets `TIMEOUT_PER_TURN` be overridden via env var (matching variantH line 27's pattern).

### 2.3 Port Block 1 — `run_check` + `EXPECTED_PREFIX_B64` plumbing (lines 72-85 + 175-181)

**2.3a — `run_check` rewrite (lines 74-82):** now passes `--expected-prompt-prefix-b64 '$EXPECTED_PREFIX_B64'` to the VM-side check script. Ported verbatim from variantH lines 64-74 (docstring preserved for the rationale).

**2.3b — `EXPECTED_PREFIX_B64` computation (lines 175-181):** inserted immediately after `TRIAL_START_EPOCH=$(date +%s)` and before the SENTINEL setup. Uses `printf '%s' | head -c 80 | base64 | tr -d '\n'` exactly as in variantH line 170.

### 2.4 Port Block 2 — anti-child-attachment fallback recovery (lines 209-322)

Replaced the minimalist 20-line fallback block (pre-edit lines 176-194) with the full 114-line variantH-equivalent logic:

- **`FALLBACK_USED=false` initial** (line 210).
- **Expanded search rationale comment** (lines 212-223).
- **Source-tag scan** preserved; last-resort scan now returns ALL post-sentinel sessions (not just `| tail -1`), so the content-match loop has the full candidate set (line 227).
- **`EXPECTED_PREFIX_HEX`** computed for byte-compare (lines 234-236).
- **`read_candidate_prefix_hex` helper** ported verbatim (lines 241-273). Reads candidate's messages[0].content, falls through to first user-role message, retries on empty.
- **Candidate-iteration loop** (lines 275-295): loops over `$FALLBACK_CANDIDATES`, compares each to `$EXPECTED_PREFIX_HEX`, accepts only on match.
- **Match handling** (lines 297-318): sets `FALLBACK_USED=true` on accept; emits `OUTCOME RESULT=ERROR detail=WRONG_SESSION` on rejection with `reason=content_mismatch candidates=$N`, or `detail=NO_SESSION_ID` if the candidate set was empty.

### 2.5 Port Block 3 — FALLBACK_USED retry shrink (lines 325-336)

Immediately after `CHAIN="A0:rc=$RC"`:

```
if [[ "$FALLBACK_USED" == "true" ]]; then
  log "FALLBACK_USED=true → shrinking MAX_RETRIES from $MAX_RETRIES to 1 for this trial"
  MAX_RETRIES=1
  CHAIN="$CHAIN | fallback_recovered_content_verified"
fi
```

Rationale comment preserved from variantH lines 321-326.

### 2.6 New correction case — `VIOLATION:EMPTY_SYNTHESIS` (lines 146-162)

Added between `VIOLATION:NO_ASSISTANT_RESPONSE` and the `*)` default branch in `correction_for()`. The message instructs the model to emit either (a) a concise synthesis referencing worker results, or (b) the honest-blocked template verbatim, and explicitly forbids re-dispatch or marker-only responses.

This case has no analog in variantH; it is a net-new addition for variantI per spec §5.2.

## 3. Grep verification

| Token | Required | Observed | Status |
|-------|----------|----------|--------|
| `expected-prompt-prefix` | ≥2 | 3 | PASS (docstring + run_check call + post-Fix comments) |
| `EXPECTED_PREFIX_B64` | ≥2 | 3 | PASS (set in main flow, used in run_check, referenced in comment) |
| `TIMEOUT_PER_TURN` with default 1500 | ≥1 | confirmed at line 31 (`: "${TIMEOUT_PER_TURN:=1500}"`) + 3 uses downstream | PASS |
| `FALLBACK_USED` | ≥2 | 4 (init false, set true on match, test in shrink, comment ref) | PASS |
| `WRONG_SESSION` | ≥1 | 4 (OUTCOME emission + surrounding log lines + docstring) | PASS |
| `EMPTY_SYNTHESIS` (in correction_for) | ≥1 | 1 (case label at line 146) | PASS |

Syntax: `bash -n probe-variantI-wrapper.sh` — silent/clean.

## 4. HERMES_WORKER_OVERLAY plumbing preservation (§5.4 requirement)

Preserved verbatim — none of the ARM selection / `HWO_PREFIX` / env-prefix logic was touched. Confirmed references:

- Arm-selection block (lines 42-55): sets `HWO_PREFIX="HERMES_WORKER_OVERLAY=1"` when ARM=B or when env var already set.
- Main `ssh_run` invocation (line 203): `${HWO_PREFIX} timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat ...` — HWO_PREFIX expands to the overlay env-var assignment for Arm B, empty for Arm A.
- Correction-retry `ssh_run` (line 368): same pattern inside the retry loop — overlay propagates into every retry attempt as well.
- Startup log line (line 171): `OVERLAY=${HWO_PREFIX:-off}` still echoes the overlay state for trace diagnostics.

No change in overlay behavior between pre- and post-Fix-3.

## 5. Structural differences variantH vs variantI that required adjustment

1. **variantI has an ARM-selection block** (lines 42-55) that variantH lacks. I preserved it untouched; the `HWO_PREFIX` substitution in `ssh_run` lines was left intact. The port inserted new code around (not through) this block.

2. **variantI's pre-edit last-resort fallback used `| tail -1`** (narrowing to one candidate at the shell level). In the port I removed the `tail -1`, matching variantH's behavior of returning ALL post-sentinel candidates, so the content-match loop can iterate through them rather than being pre-reduced to one. This is the correct behavior for anti-child-attachment — we want to find the RIGHT candidate, not the most recent one.

3. **variantI's `run_check`** initially had no `$EXPECTED_PREFIX_B64` dependency; the port introduces that ordering constraint. I verified the `EXPECTED_PREFIX_B64` computation (line 181) is reachable BEFORE the first `run_check` invocation (first call is inside the `while` loop at line 338, after both the initial SSH and the fallback recovery have run; `EXPECTED_PREFIX_B64` is set long before that at line 181, directly after `TRIAL_START_EPOCH`). No ordering issue.

4. **variantI's log-start message** includes `ARM=${ARM_DISPLAY} OVERLAY=${HWO_PREFIX:-off}` — kept as-is; the `TIMEOUT=${TIMEOUT_PER_TURN}s` portion now reports 1500 by default instead of 900.

5. **No variantH-equivalent exists for the `VIOLATION:EMPTY_SYNTHESIS` case.** It was added per spec §5.2 as a fresh case in `correction_for()`. The template mirrors the tone and structure of adjacent cases (heredoc for multi-paragraph, single-line for terse cases).

6. **variantH's correction-retry `ssh_run`** does not have an HWO prefix (variantH predates overlay logic). variantI's correction-retry ssh_run at line 368 retains the `${HWO_PREFIX}` — preserving Arm B overlay behavior across retries. This is a variantI-specific property the port leaves untouched.

## 6. Rollback

```
cp /Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh.pre-rev2-fix3 \
   /Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh
# verify: md5 -q probe-variantI-wrapper.sh → 301c61af896bec95f6efc63c8a8e342d
```

## 7. Not performed (per scope)

- No probe runs.
- No VM mutations.
- No edits to any file other than `probe-variantI-wrapper.sh` + snapshot + this artifact.
- No git operations.
