# ARTIFACT — r7.6-P1C Fix 4 judge verdict

**Scope:** Fresh-context judge for PLAN-r7.6-P1C-fixes-implementation.md §6 (Fix 4 — parent one-shot misclassification on retry). Read-only verification of wrapper retry-preamble implementation + optional HERMES-variantF.md amplifier.
**Date:** 2026-04-19
**Author:** Fix 4 judge (sub-agent, fresh context)
**Verdict:** **ACCEPT**

---

## Inputs verified

| File | Observed md5 | Brief-stated md5 | Match |
|------|--------------|------------------|-------|
| `probe-variantI-wrapper.sh` (post) | `f1022e994a46838c180e4bf8da4171ee` | `f1022e99...` | YES |
| `probe-variantI-wrapper.sh.pre-rev2-fix4` | `95cef027235f1a4716878640796c016f` | `95cef027...` | YES |
| `probe-variantH-wrapper.sh` (post) | `64b75e00efc1056dcb1883a54e162033` | `64b75e00...` | YES |
| `probe-variantH-wrapper.sh.pre-rev2-fix4` | `6958c8bbc3567d1d221e04e5706ecee9` | `6958c8bb...` | YES |
| `variants/hermes/HERMES-variantF.md` (post) | `24e8d1c0f7e1e0e95b26c38af974b8ce` | `24e8d1c0...` | YES |
| `variants/hermes/delegate_worker_v2.py` | `d31876fe987331a26c8640202334fd46` | `d31876fe987331a26c8640202334fd46` (H4C rejected) | YES (unchanged) |

Independent baseline check for `HERMES-variantF.md`: the committed version at `001a1a9` (most recent commit touching the file) hashes to `01c0e77bb2a6e753a8ea9063784a25e0`, matching the diag's stated pre-release md5. Git-diff shows **exactly one** insertion line (no deletions, no other modifications).

---

## Check 1 — Wrapper diff pre/post Fix 4

### 1a. `retry_preamble()` helper present in both wrappers

- variantI line 121-132: `retry_preamble()` function defined; produces a heredoc beginning `CONTEXT: ...`, embeds `${original_task_prefix}` inside `--- BEGIN ORIGINAL TASK ---` / `--- END ORIGINAL TASK ---` delimiters, terminates with `CORRECTION (specific protocol issue from the previous attempt):`. ✓
- variantH line 124-135: structurally identical function. ✓

Format matches plan §6 spec (`CONTEXT: ...ORIGINAL TASK:... CORRECTION:...`).

### 1b. EVERY branch in `correction_for()` prepends the preamble

Exhaustive per-branch verification (grep + independent diff):

**variantI — 7 case branches, 7 `printf '%s\n\n' "$preamble"` prepends:**

| Line | Branch | Preamble prepended? |
|------|--------|----------------------|
| 139 | `VIOLATION:NO_MARKER` | YES (line 141) |
| 151 | `"VIOLATION:NO_DISPATCH:structured"|"VIOLATION:NO_DISPATCH:long-horizon"` | YES (line 153) |
| 165 | `"VIOLATION:ROLE_COLLAPSE:structured"|"VIOLATION:ROLE_COLLAPSE:long-horizon"` | YES (line 167) |
| 177 | `VIOLATION:FABRICATION` | YES (line 179) |
| 183 | `VIOLATION:NO_ASSISTANT_RESPONSE` | YES (line 185) |
| 189 | `VIOLATION:EMPTY_SYNTHESIS` | YES (line 191) |
| 209 | `*)` default | YES (line 211) |

`grep -c 'printf .%s.n.n. "\$preamble"'` = **7**, matching branch count. No branch missed.

**variantH — 6 case branches, 6 preamble prepends** (no `VIOLATION:EMPTY_SYNTHESIS` branch; EMPTY_SYNTHESIS correctly falls through to `*)` default which also includes the preamble):

| Line | Branch | Preamble prepended? |
|------|--------|----------------------|
| 142 | `VIOLATION:NO_MARKER` | YES (line 144) |
| 154 | `"VIOLATION:NO_DISPATCH:structured"|"VIOLATION:NO_DISPATCH:long-horizon"` | YES (line 156) |
| 168 | `"VIOLATION:ROLE_COLLAPSE:structured"|"VIOLATION:ROLE_COLLAPSE:long-horizon"` | YES (line 170) |
| 180 | `VIOLATION:FABRICATION` | YES (line 182) |
| 186 | `VIOLATION:NO_ASSISTANT_RESPONSE` | YES (line 188) |
| 192 | `*)` default | YES (line 194) |

`grep -c` = **6**. No branch missed.

### 1c. `$TASK_TEXT` injection (with 1500-byte truncation)

- variantI line 122: `local original_task_prefix="${TASK_TEXT:0:1500}"`; referenced on line 127 inside the heredoc. ✓
- variantH line 125: same pattern; referenced on line 130. ✓

### Diff discipline

`diff .pre-rev2-fix4 <post>` on each wrapper shows:
- No deletions (only insertions of the preamble block, the `preamble=$(retry_preamble)` initialization line, and the `{...}` braces wrapping each branch body).
- Original MSGEOF heredocs and echo bodies are preserved verbatim except for two minor in-message edits: `NO_ASSISTANT_RESPONSE` and `*)` default now append "(preserving your original classification for the original task above)" / "(preserve the original classification for the task above)" — consistent with the diag's §"Recommended fix" tightening. Not a regression; aligned with Fix 4 intent.
- No out-of-scope lines touched. Fix 3 region (variantI only) untouched.

**Check 1: PASS.**

---

## Check 2 — Fix 3 preservation in variantI

All 9 features from the brief verified intact via direct grep (line numbers shift due to Fix 4 insertion, but content is present):

| # | Fix 3 feature | Evidence |
|---|---------------|----------|
| 1 | Header comment referencing Fix 3 | line 2: `# Fix 3 (rev 2, r7.6-P1C) — anti-child-attachment + timeout raise 2026-04-19` |
| 2 | `TIMEOUT_PER_TURN=1500` default with env-override | line 31: `: "${TIMEOUT_PER_TURN:=1500}"  # Fix 3 (rev 2, r7.6-P1C): raised 900→1500...` |
| 3 | `run_check` passes `--expected-prompt-prefix-b64` | line 82: `ssh_run "python3 $CHECK_REMOTE ... --expected-prompt-prefix-b64 '$EXPECTED_PREFIX_B64' ..."` |
| 4 | `EXPECTED_PREFIX_B64` defined | line 230: `EXPECTED_PREFIX_B64=$(printf '%s' "$TASK_TEXT" \| head -c 80 \| base64 \| tr -d '\n')` |
| 5 | `VIOLATION:EMPTY_SYNTHESIS` branch in `correction_for()` | line 189 |
| 6 | Anti-child-attachment fallback block | lines 261-369: `EXPECTED_PREFIX_HEX`, `read_candidate_prefix_hex`, content-match/MISMATCH logic |
| 7 | `FALLBACK_USED` flag + `MAX_RETRIES=1` on fallback | lines 259, 348, 379-381 |
| 8 | `WRONG_SESSION` result path | lines 358, 361-362 |
| 9 | (implicit from 1-8) Overall Fix 3 structural coherence | all blocks intact and reachable |

**Check 2: PASS.** No Fix 3 feature regressed.

---

## Check 3 — HERMES-variantF.md amplifier

**Independent baseline diff:** `git show 001a1a9:variants/hermes/HERMES-variantF.md` hashes to `01c0e77bb2a6e753a8ea9063784a25e0` — matches the diag's stated pre-release baseline. I did not rely on the worker's claim; I re-derived the baseline from git.

`git diff variants/hermes/HERMES-variantF.md` output:

```
@@ -86,6 +86,7 @@ These are the patterns to resist:
 3. **Orient-First Drift** — ...
 4. **Rubber-Stamp Classification** — ...
 5. **Role Collapse** — ...
+6. **Retry Re-Classification** — Fix 4 (r7.6-P1C, 2026-04-19). When a user turn opens with "CONTEXT: This is a RETRY..." or "Re-read HERMES.md and respond again..." or otherwise frames itself as a protocol correction, do NOT classify the correction message itself as a new one-shot task. The correction is a directive to continue the ORIGINAL task (whose text is typically re-injected in the same turn). Preserve your original classification (or, if the retry is your first view of the task, classify based on the ORIGINAL TASK block, not on the correction framing).
 
 If you catch yourself doing any of these mid-response, stop. ...
```

**diffstat:** `1 file changed, 1 insertion(+)`. **Exactly ONE line added, zero lines deleted, zero lines modified.**

Content checks:
- ✓ Addition is in the "Classification pressure — named failure modes" section (line 89, directly after item #5 Role Collapse).
- ✓ Placement matches plan §6.4 H4A branch recommendation (5-line clause in classification gate area).
- ✓ Addresses retry-classification preservation: explicitly tells the model to preserve original classification when it sees a retry-framed user turn.
- ✓ Language matches wrapper's preamble: the added item quotes `"CONTEXT: This is a RETRY..."` (the wrapper preamble's opening line) AND `"Re-read HERMES.md and respond again..."` (the wrapper's default-branch correction text). Both signals cite consistent triggers.
- ✓ References the `ORIGINAL TASK block` by name, matching the `--- BEGIN ORIGINAL TASK ---` / `--- END ORIGINAL TASK ---` delimiters emitted by `retry_preamble()`.
- ✓ No unintentional deletions or modifications to any other variantF content (confirmed by `git diff --stat` = 1 insertion, 0 deletions).

**Note on line count:** the brief expects "~5 lines added"; the implementation compressed the clause into a single numbered-list item (one logical line, ~110 words). This is a stylistic choice consistent with the surrounding enumerated list format (items 1-5 are also single paragraphs within numbered bullets). The intent of "~5 lines" (i.e., a short addition in the classification-pressure area) is met. Not a concern.

**Check 3: PASS.**

---

## Check 4 — `bash -n` syntax

```
$ bash -n /Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh && echo "variantI: OK"
variantI: OK
$ bash -n /Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh && echo "variantH: OK"
variantH: OK
```

Both silent, both pass. **Check 4: PASS.**

---

## Check 5 — Smoke test the preamble rendering

Extracted `retry_preamble` + `correction_for` from each wrapper into an isolated script, sourced, and invoked with realistic TASK_TEXT values. Results (full transcript in judge session):

### variantI smoke (TASK_TEXT = T4-like "Refactor the auth module...")

Tested 4 branches: `VIOLATION:EMPTY_SYNTHESIS`, `VIOLATION:NO_MARKER`, `VIOLATION:FABRICATION`, and `*)` default (via `SOMETHING_ELSE`). All produce output in exact expected order:

```
CONTEXT: This is a RETRY of the task you were originally asked to solve. ...
<blank>
--- BEGIN ORIGINAL TASK ---
Refactor the auth module to use the new session store. Three files need changes: ...
--- END ORIGINAL TASK ---
<blank>
CORRECTION (specific protocol issue from the previous attempt):
<blank>
<branch-specific message body>
```

### variantH smoke (TASK_TEXT = T5-like "Debug why the dashboard shows stale data...")

Tested 3 branches: `VIOLATION:NO_MARKER`, `VIOLATION:NO_DISPATCH:structured`, and `VIOLATION:EMPTY_SYNTHESIS` (falls through to `*)` default). All render identically structured preamble + ORIGINAL TASK block + CORRECTION + branch body.

**No rendering artifacts observed:**
- `${original_task_prefix}` expands correctly inside the heredoc.
- `PREAMBLE_EOF` (unquoted sentinel) allows interpolation as intended.
- `'MSGEOF'` (quoted sentinel) correctly suppresses interpolation of tool-call template placeholders like `<one-shot|structured|long-horizon>` inside the branch bodies.
- The `{ printf ...; cat <<...; }` braces compose correctly; no premature EOF or heredoc-nesting issues.
- Blank-line separation between preamble, body, and branch message is visually clean.

**Check 5: PASS.**

---

## Check 6 — No files out of scope

Independent md5 verification:
- `delegate_worker_v2.py` md5 = `d31876fe987331a26c8640202334fd46`, matching brief's expected value and diag's pre-Fix-4 value. H4C correctly rejected — no schema changes.
- No other Hermes-related files in `variants/hermes/` modified (git status only shows variantF.md modified among tracked hermes variant files).
- `probe-variantH-check.py` not modified (unchanged from diag md5 context; variantH wrapper still references the same CHECK_REMOTE/LOCAL_CHECK paths).

**Check 6: PASS.**

---

## Verdict: ACCEPT

All six checks pass. Fix 4 is correctly implemented per plan §6.4 H4B (primary branch) + H4A (amplifier branch). No H4C schema changes as specified.

**Key confirmations:**
- Both wrappers have a `retry_preamble()` helper producing the exact `CONTEXT: ...ORIGINAL TASK:... CORRECTION:...` format per plan spec.
- Both wrappers' `correction_for()` functions exhaustively prepend the preamble to every case branch (7 for variantI, 6 for variantH — all verified independently via diff + grep + smoke test, not by taking the worker's claim on faith).
- `$TASK_TEXT` is injected in every branch via the 1500-byte-truncated `original_task_prefix` variable.
- All 9 Fix 3 features preserved in variantI (no regression).
- HERMES-variantF.md amplifier is a single targeted insertion in the correct section, with language aligning with the wrapper preamble's trigger phrases. **Zero unintended variantF text changes** (git-diff stat: 1 insertion, 0 deletions).
- `bash -n` clean on both wrappers.
- Smoke test confirmed actual rendering produces the intended format on ≥2 branches per wrapper (7 branches tested total).
- `delegate_worker_v2.py` unchanged (md5 matches expected `d31876fe...`).

**No unintended variantF text changes detected.** The single-item append in the enumerated list is minimal, isolated, and semantically correct.

---

## Concerns (minor, non-blocking)

1. **"~5 lines" vs. one long line:** The HERMES-variantF.md addition is a single line (one numbered item, ~110 words of prose). The plan anticipated "~5 lines added." The compression is stylistically consistent with the surrounding enumerated list (items 1-5 are also one-line paragraphs per item) and does not reduce the amplifier's effect. No action needed; flagged for completeness.

2. **Fix 4 comment blocks differ slightly between variantI and variantH.** VariantI's comment (lines 108-120) says "one-shot-no-goal cascade observed in armB-T4-run3 / armB-T5-run4"; variantH's (lines 112-123) adds "(variantI) ... Applied symmetrically to variantH (no observed failures of this class yet, but same wrapper contract)." This is correct scoping — the failure was only observed on variantI, but symmetric application to variantH prevents future drift. Not a concern; flagged as design intent.

3. **Pre-Fix-4 `NO_ASSISTANT_RESPONSE` and `*)` branches now carry additional "(preserving original classification...)" text inside their message bodies.** This is a minor intent-tightening beyond the pure re-injection, but consistent with the diag's §"Recommended fix" and Fix 4 intent. Post-Fix-4 model still receives the same structural directive plus the explicit in-body reminder. Acceptable. Flagged because it's technically an edit INSIDE an existing MSGEOF / echo body (not purely additive wrapping), and future judges scanning for "original bodies preserved verbatim" should note this nuance.

4. **No probe run / runtime validation performed** (per brief: "READ-ONLY ... no probe runs"). The 5-trial artificial-retry smoke referenced in plan §6.5 is downstream of this judge and left to S8/S10 validation. Preamble rendering correctness is verified at the shell/string level only. This is the intended judge scope; flagging for planner awareness.

No concern rises to REVISE or REJECT threshold.
