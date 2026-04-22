# ARTIFACT — r7.6 P1C Fix 3 fresh-context judge verdict (2026-04-19)

**Judge role:** verify the Fix 3 implementation (variantH→variantI wrapper back-port + `TIMEOUT_PER_TURN` raise + `VIOLATION:EMPTY_SYNTHESIS` correction case) against `PLAN-r7.6-P1C-fixes-implementation.md` §5.

**Inputs reviewed (read-only):**
- `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh` (post-Fix-3)
- `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh.pre-rev2-fix3` (snapshot)
- `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh` (reference)
- `/Users/briantaylor/Projects/AgentFW/probe-variantH-check.py` (check-script coupling)
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-P1C-fix3-impl.md` (worker claims)
- Plan §5.1–§5.6

**Scope enforcement:** read-only throughout. No wrapper edits, no probes, no VM mutations.

---

## Verdict: **ACCEPT with caveats**

Fix 3 functional content is correctly implemented, bash-clean, and preserves all variantI-specific plumbing. All numeric grep checks pass or exceed claims. However, the ARTIFACT's file-identity header (md5 / line count / §2.6 scope description) is **stale**: the current file contains additional Fix-4-lineage content (`retry_preamble` helper + per-branch invocations) that the ARTIFACT does not disclose as a Fix-3 change. This is not a functional defect — the Fix 4 preamble was already present in variantH and the port picked it up as a side-effect of mirroring variantH's `correction_for()` — but it is a disclosure gap the caller should know about.

---

## 1. File identity check (caveats)

| Item | ARTIFACT §1 claim | Actual observation | Status |
|------|-------------------|---------------------|--------|
| pre-edit md5 (snapshot) | `301c61af896bec95f6efc63c8a8e342d` | `301c61af896bec95f6efc63c8a8e342d` | PASS |
| post-edit md5 (current file) | `95cef027235f1a4716878640796c016f` | `f1022e994a46838c180e4bf8da4171ee` | **MISMATCH** |
| post-edit line count | 377 | 426 | **MISMATCH (+49 lines)** |

**Interpretation.** The worker either (a) did additional edits after writing the ARTIFACT and didn't update §1, or (b) computed the ARTIFACT md5 from an intermediate state before completing the Fix 4 preamble port from variantH. The judge-brief supplied md5 (`95cef027...`) matches the ARTIFACT but NOT the file — so the brief's provenance trail was based on the same stale state.

The +49-line delta is fully accounted for by the Fix 4 `retry_preamble` helper (lines 108–132) and the `{ printf '%s\n\n' "$preamble"; ... }` wrappers in every existing `correction_for()` branch (lines 140, 152, 167, 178, 184 ~8 extra lines each). This is Fix-4-lineage content already present in variantH (variantH lines 112–140, confirmed by independent grep). In other words, the port brought Fix 4's retry preamble along with Fix 3's Blocks 1–3 — not an out-of-scope *new* addition, but also not disclosed in ARTIFACT §2.6 which claims only `VIOLATION:EMPTY_SYNTHESIS` was added to `correction_for()`.

**Caveat 1 (disclosure):** ARTIFACT §2.6 is understated. `correction_for()` received both the new `VIOLATION:EMPTY_SYNTHESIS` case AND a rewrite of every existing branch to inject the retry preamble.

**Caveat 2 (cross-variant drift):** Because variantH already had Fix 4 and variantI now also has Fix 4-equivalent logic, the two wrappers are coherent. The `/judge-brief` sentence "variantH wrapper should be untouched by Fix 3 (Fix 4 impl will touch it; that's separate)" is satisfied for variantH — H md5 `64b75e00...` is untouched, and `git status` shows no modification — but the framing implied Fix 4 landing on variantI would be a separate future step. It has effectively already landed on variantI via this port.

---

## 2. Diff-against-snapshot check (§5.4 expected blocks)

Computed via `diff -u probe-variantI-wrapper.sh.pre-rev2-fix3 probe-variantI-wrapper.sh`. Each of the four Fix-3 blocks is present:

| Block | Source (variantH ref) | Target (variantI post-Fix-3) | Status |
|-------|------------------------|------------------------------|--------|
| `TIMEOUT_PER_TURN` default 1500 with env-override | variantH line 27 `: "${TIMEOUT_PER_TURN:=1500}"` | variantI line 31 identical | PASS |
| Block 1: `run_check` passes `--expected-prompt-prefix-b64` | variantH lines 73 | variantI lines 75–82 | PASS |
| Block 1: `EXPECTED_PREFIX_B64` computation | variantH line ~210 | variantI line 230 `EXPECTED_PREFIX_B64=$(printf '%s' "$TASK_TEXT" \| head -c 80 \| base64 \| tr -d '\n')` | PASS |
| Block 2: anti-child-attachment fallback (FALLBACK_CANDIDATES, read_candidate_prefix_hex, content-match loop, WRONG_SESSION emission) | variantH lines ~246–360 | variantI lines 258–349 | PASS |
| Block 3: `FALLBACK_USED=true → MAX_RETRIES=1` | variantH lines ~367–378 | variantI lines 378–383 | PASS |
| New `VIOLATION:EMPTY_SYNTHESIS` in `correction_for()` | no variantH analog | variantI lines 189–207 (`cat <<'MSGEOF'` with (a) synthesis / (b) honest-blocked template) | PASS |

All six required structural additions are present and mirror variantH semantics where applicable.

---

## 3. HERMES_WORKER_OVERLAY plumbing preserved (variantI-specific)

Plan §5.4 singles out this requirement. Evidence:

- Arm selection block (lines 42–55): `HWO_PREFIX="HERMES_WORKER_OVERLAY=1"` when `ARM=B` or env var set; empty otherwise — unchanged.
- Initial `ssh_run` (line 252): `${HWO_PREFIX} timeout $TIMEOUT_PER_TURN ./venv/bin/hermes chat ...` — HWO carried through.
- Correction-retry `ssh_run` (line 417): identical HWO_PREFIX carrier — HWO carried through on retries too.
- Startup log (line 220): reports `OVERLAY=${HWO_PREFIX:-off}`.

Both `ssh_run` invocations carry `HWO_PREFIX`. Worker's ARTIFACT §4 claim is confirmed.

---

## 4. bash -n syntax check

`bash -n probe-variantI-wrapper.sh` — silent (exit 0). **PASS.**

---

## 5. Grep counts vs worker claims

| Token | Plan/brief threshold | Worker claim | Actual | Status |
|-------|------------------------|---------------|--------|--------|
| `expected-prompt-prefix` | ≥2 | 3 | 3 | PASS |
| `EXPECTED_PREFIX_B64` | ≥2 | 3 | 3 | PASS |
| `TIMEOUT_PER_TURN` (default 1500 present) | ≥1 | present | line 31 `: "${TIMEOUT_PER_TURN:=1500}"` + 3 downstream uses | PASS |
| `FALLBACK_USED` | ≥2 | 4 | 4 | PASS |
| `WRONG_SESSION` | ≥1 | 4 | 4 | PASS |
| `EMPTY_SYNTHESIS` | ≥1 | 1 | 1 | PASS |

All thresholds met or exceeded. Worker's claimed counts match observed counts exactly.

---

## 6. Candidate-scan bug fix (variantI-specific)

Pre-edit line 179 had `FALLBACK_CANDIDATES=$(ssh_run "... \| sort -n \| tail -1 \| awk '{print \$2}'")` — pre-reducing to one candidate at the shell level, which would have prevented the content-match loop from iterating multi-candidate fallback sets.

Post-edit line 261 is `FALLBACK_CANDIDATES=$(ssh_run "... \| sort -n \| awk '{print \$2}'")` (no `tail -1`). The content-match `while IFS= read -r CPATH; do ... done <<< "$FALLBACK_CANDIDATES"` loop (lines 304–324) now iterates all post-sentinel candidates and breaks only on a content-match. **PASS.**

The only remaining `tail -1` in the file (line 360) is used solely to capture a breadcrumb session id (`LAST_CAND_SID`) for the WRONG_SESSION OUTCOME message after all candidates fail — not a scanning constraint. Correct behavior.

---

## 7. File-out-of-scope check

- `probe-variantH-wrapper.sh` md5 `64b75e00efc1056dcb1883a54e162033` — **untouched** (`git status` shows `??` untracked but no modification to previously-tracked state; no edits since Fix 3 began).
- `probe-variantH-check.py` — untouched.
- No other file modifications attributable to Fix 3. **PASS.**

---

## 8. Discrepancies summary

1. **ARTIFACT §1 md5 and line count are stale.** Actual file md5 is `f1022e994a46838c180e4bf8da4171ee` (not `95cef027...`); actual line count is 426 (not 377). Delta = +49 lines = undisclosed Fix-4 preamble port.
2. **ARTIFACT §2.6 is understated.** `correction_for()` was rewritten to inject a `retry_preamble` into every branch (not only the new `VIOLATION:EMPTY_SYNTHESIS` case). The helper `retry_preamble()` itself (lines 108–132) is new to variantI and is Fix-4 lineage.
3. **Judge brief's claimed post-Fix-3 md5 (`95cef027...`) likewise does not match the file.** This suggests the brief was based on the same stale ARTIFACT state. The judge-brief sentence "variantH wrapper should be untouched by Fix 3 (Fix 4 impl will touch it; that's separate)" is technically honored for variantH but the Fix 4 lineage *did* land on variantI as a side-effect of the port — something the planner may want to reconcile in Fix 4's implementation plan.

None of these discrepancies break the Fix 3 functional contract or introduce functional defects. All structural, grep, syntax, plumbing, and bug-fix checks pass. The verdict is **ACCEPT**; the caveats are disclosure/book-keeping, not correctness.

---

## 9. Recommended follow-up (non-blocking)

- Planner: reconcile Fix 4 status for variantI. Either mark Fix 4 as "already landed via Fix 3 port" for variantI, or decide whether additional Fix-4 work is needed on top.
- Worker (if re-engaged): refresh ARTIFACT §1 md5 + line count; expand §2.6 to disclose the retry_preamble port.
- Optional: Fix-3 post-land validation (plan §5.5) — one Arm B-style T5 trial at 1500s timeout — remains pending per scope (probes forbidden here).
