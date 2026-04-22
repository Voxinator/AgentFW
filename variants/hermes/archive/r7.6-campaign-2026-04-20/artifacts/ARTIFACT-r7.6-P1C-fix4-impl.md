# ARTIFACT — r7.6-P1C Fix 4 implementation (rev-2)

**Scope:** Implementation worker output. Parent one-shot misclassification on retry (H4B branch of PLAN §6.4).
**Date:** 2026-04-19
**Author:** Fix 4 implementation worker (sub-agent)
**Plan reference:** `/Users/briantaylor/Projects/AgentFW/PLAN-r7.6-P1C-fixes-implementation.md` §6.4 branch #2
**Diag reference:** `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-P1C-diag-parent-one-shot.md`

---

## Summary

Applied the H4B fix recommended by the diagnostic: `correction_for()` in both `probe-variantI-wrapper.sh` and `probe-variantH-wrapper.sh` now prepends a "RETRY preamble" containing the original `$TASK_TEXT` (truncated to 1500 bytes) and an explicit "preserve your original classification" directive before every correction message. Additionally, applied the optional HERMES-variantF.md add-on (~5 lines) adding a sixth named failure mode — **Retry Re-Classification** — to the Classification pressure section.

Fix 3 additions in `probe-variantI-wrapper.sh` (anti-child-attachment, `TIMEOUT_PER_TURN=1500`, `FALLBACK_USED`, `EXPECTED_PREFIX_B64`, `WRONG_SESSION`, `VIOLATION:EMPTY_SYNTHESIS` branch) are all preserved.

---

## md5 before → after

| File | Before | After |
|------|--------|-------|
| `probe-variantI-wrapper.sh` | `95cef027235f1a4716878640796c016f` | `f1022e994a46838c180e4bf8da4171ee` |
| `probe-variantH-wrapper.sh` | `6958c8bbc3567d1d221e04e5706ecee9` | `64b75e00efc1056dcb1883a54e162033` |
| `variants/hermes/HERMES-variantF.md` | `01c0e77bb2a6e753a8ea9063784a25e0` (per diag) | `24e8d1c0f7e1e0e95b26c38af974b8ce` |

**Rollback snapshots created:**
- `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh.pre-rev2-fix4`
- `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh.pre-rev2-fix4`

(HERMES-variantF.md not snapshotted because the add-on is minimal and easily revertible by deleting item #6 and the Retry Re-Classification paragraph; pre-commit hook governance lives with operator. If operator wants a snapshot, mkdir a `.pre-rev2-fix4` copy manually.)

---

## Diff summary — variantI

### Structural change in the `correction_for()` region (original lines 108-166, now 108-216)

1. **New helper function `retry_preamble()`** (lines ~108-132, ~25 lines).
   Inserted immediately before `correction_for()`. Emits a single preamble block via a `PREAMBLE_EOF` heredoc that:
   - Declares `CONTEXT: This is a RETRY of the task you were originally asked to solve.`
   - Frames the correction as continuation, not a new one-shot.
   - Re-injects `$TASK_TEXT` truncated to 1500 bytes inside `--- BEGIN ORIGINAL TASK ---` / `--- END ORIGINAL TASK ---` delimiters.
   - Ends with `CORRECTION (specific protocol issue from the previous attempt):` — the subsequent branch-specific message appends below.

2. **`correction_for()` body rewritten** (lines ~134-216):
   - At function entry: `local preamble; preamble=$(retry_preamble)` computes the preamble once per invocation.
   - Each of the SEVEN case branches (`VIOLATION:NO_MARKER`, `VIOLATION:NO_DISPATCH:*`, `VIOLATION:ROLE_COLLAPSE:*`, `VIOLATION:FABRICATION`, `VIOLATION:NO_ASSISTANT_RESPONSE`, `VIOLATION:EMPTY_SYNTHESIS`, `*)` default) now wraps its original message body in a `{ printf '%s\n\n' "$preamble"; <original body>; }` block.
   - Original MSGEOF heredocs and echo strings are preserved verbatim INSIDE the braces (no semantic change to the correction language), with two targeted additions: `NO_ASSISTANT_RESPONSE` and the `*)` default now explicitly say "preserving your original classification" in their echo text.

3. **Fix 4 comment block** (lines 108-120): ~13 lines of documentation explaining the change, referencing `ARTIFACT-r7.6-P1C-diag-parent-one-shot.md` and the 1500-byte rationale.

**Net LOC added:** ~60 lines (preamble function + case-branch wrapping + comments). **Net LOC deleted:** zero (all original correction text preserved).

### What was NOT changed in variantI

- Lines 1-107 (header, env parsing, Fix 3 `TIMEOUT_PER_TURN=1500`, helpers, `run_check()`, `compute_mm()`).
- Lines 217-end (main flow, Fix 3 anti-child-attachment fallback, retry loop, OUTCOME emission).

All Fix 3 additions verified intact — see "Fix 3 preservation" section below.

---

## Diff summary — variantH

Structurally identical to variantI, applied symmetrically to `probe-variantH-wrapper.sh::correction_for()` (original lines 112-154, now 112-199).

Differences from variantI version:
- No `VIOLATION:EMPTY_SYNTHESIS` branch (variantH doesn't have one — that was a Fix-3-era variantI-only addition). The default `*)` branch handles all unknown verdicts including EMPTY_SYNTHESIS, and it includes the preamble.
- Fix 4 comment block notes "Applied symmetrically to variantH (no observed failures of this class yet, but same wrapper contract)."
- Total of SIX case branches wrapped (vs. seven in variantI).

**Net LOC added:** ~55 lines. **Net LOC deleted:** zero.

---

## Diff summary — HERMES-variantF.md (optional add-on APPLIED)

Single edit in `## Classification pressure — named failure modes` section: added item #6 after existing items 1-5:

```markdown
6. **Retry Re-Classification** — Fix 4 (r7.6-P1C, 2026-04-19). When a user turn
   opens with "CONTEXT: This is a RETRY..." or "Re-read HERMES.md and respond
   again..." or otherwise frames itself as a protocol correction, do NOT
   classify the correction message itself as a new one-shot task. The
   correction is a directive to continue the ORIGINAL task (whose text is
   typically re-injected in the same turn). Preserve your original
   classification (or, if the retry is your first view of the task, classify
   based on the ORIGINAL TASK block, not on the correction framing).
```

Net LOC added: ~5 (one numbered item).

**Decision rationale:** Diag §"Recommended fix" → "Secondary — add-on: ~5-line clause in HERMES-variantF.md §'Classification pressure — named failure modes' (after pattern #5)..." explicitly recommends this as a secondary mitigation layered on top of the wrapper fix (primary). Operator pre-commit hasn't been reported as locking HERMES-variantF.md. The amplifier teaches the model directly that corrections referencing "Re-read HERMES.md" are retry directives, matching the exact trigger phrase used in the wrapper default-branch and in the H4A trials' session idx 0 content. Low risk, high coverage complement to the wrapper re-injection.

---

## Verification

### bash -n syntax

```
$ bash -n /Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh && echo "variantI: OK"
variantI: OK
$ bash -n /Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh && echo "variantH: OK"
variantH: OK
```

Both pass. No syntax errors.

### Grep: TASK_TEXT inside correction_for() body

- `probe-variantI-wrapper.sh` line 122: `local original_task_prefix="${TASK_TEXT:0:1500}"` (inside `retry_preamble()`, which is called from `correction_for()` via `preamble=$(retry_preamble)` at line 137). ✓
- `probe-variantH-wrapper.sh` line 125: same pattern, called from line 140. ✓

### Grep: "CONTEXT:" / "original" / "ORIGINAL TASK" in correction preamble

Both wrappers contain the exact string `CONTEXT: This is a RETRY of the task you were originally asked to solve.` and the `--- BEGIN ORIGINAL TASK ---` / `--- END ORIGINAL TASK ---` delimiters. ✓

### Manual visual inspection: preamble present in ALL branches

Counted `printf '%s\n\n' "$preamble"` occurrences:
- variantI: **7** (matching 7 case branches — NO_MARKER, NO_DISPATCH, ROLE_COLLAPSE, FABRICATION, NO_ASSISTANT_RESPONSE, EMPTY_SYNTHESIS, default). ✓
- variantH: **6** (matching 6 case branches — NO_MARKER, NO_DISPATCH, ROLE_COLLAPSE, FABRICATION, NO_ASSISTANT_RESPONSE, default). ✓

No branch forgets the preamble.

### Smoke test (shell-sourced, no VM invocation)

Extracted `retry_preamble` + `correction_for` from both wrappers, invoked with a realistic `TASK_TEXT`, verified output:

```
=== variantI correction_for "VIOLATION:EMPTY_SYNTHESIS" ===
CONTEXT: This is a RETRY of the task you were originally asked to solve. ...
--- BEGIN ORIGINAL TASK ---
Refactor the auth module to use the new session store. Three files need changes: src/auth/session.ts, src/middleware/auth.ts, ...
--- END ORIGINAL TASK ---
CORRECTION (specific protocol issue from the previous attempt):
Your delegated worker(s) returned results but you produced no final synthesis ...
```

Preamble + original task + correction body render in the correct order. Likewise tested default branch and variantH NO_MARKER / default — all work.

---

## Fix 3 preservation confirmation (variantI)

All Fix 3 (rev 2) additions intact:

| Fix 3 feature | Grep location | Present? |
|---------------|---------------|----------|
| Header comment | line 2: `# Fix 3 (rev 2, r7.6-P1C) — anti-child-attachment + timeout raise 2026-04-19` | ✓ |
| `TIMEOUT_PER_TURN:=1500` | line 31 | ✓ |
| `run_check()` with `--expected-prompt-prefix-b64` | lines 74-83 | ✓ |
| `VIOLATION:EMPTY_SYNTHESIS` branch in `correction_for` | line 189 (shifted from original ~146 due to preamble insertion) | ✓ |
| `EXPECTED_PREFIX_B64` computation | line 230 | ✓ |
| Anti-child-attachment fallback block (content-match via hex compare) | lines 258-369 (shifted from original ~195-295) | ✓ |
| `FALLBACK_USED` flag + shrink-retries-to-1 | lines 259, 348, 372, 379 | ✓ |
| `WRONG_SESSION` error-emission path | lines 358, 361-362 | ✓ |

All 9 Fix 3 features verified present post-Fix-4. No regressions.

(variantH doesn't have Fix 3 — Fix 3 was variantI-only per plan §5; variantH already had the anti-child-attachment block as its r7.5-B1 baseline.)

---

## HERMES-variantF.md add-on decision

**Decision: APPLIED.**

**Rationale:** The diag artifact's "Recommended fix" section (lines 203-209) lists the HERMES-variantF.md clause as "Secondary — add-on: ~5-line clause in HERMES-variantF.md §'Classification pressure — named failure modes' (after pattern #5)." This is explicit diag recommendation, not speculation. The operator has not flagged HERMES-variantF.md as frozen (it's listed in the plan's §2.4 file-under-edit baselines alongside `delegate_worker_v2.py`, and the diag worker explicitly inspected it).

The add-on teaches the model directly what the wrapper preamble encodes implicitly — a belt-and-suspenders for a failure mode whose root cause (session-persistence-under-SIGTERM) is not 100% eliminated by the wrapper fix alone. H4A was probability ~75% contributing factor per diag §"Hypothesis weighting"; addressing it has expected value.

The edit is minimal (~5 lines), non-invasive (appended to an existing numbered list), and easily revertible.

---

## Estimated effect on future retries

**Qualitative prediction:**

With the preamble in place, on any retry round (even after SIGTERM-before-persistence wipes the original task from the session JSON), the model's next user turn will include:
1. An explicit "this is a RETRY — do not re-classify" directive.
2. The full original task text, inline.
3. The specific protocol correction for the prior-attempt violation.

The model is therefore reading the preamble CONTEXT clause + ORIGINAL TASK block + correction together, as a single user turn. The diag's failure analysis predicts this reframes the classification problem: instead of "classify this protocol-correction-only turn" (which legitimately resolves to one-shot-no-goal), the model faces "classify this original task that the user is retrying" (which resolves to whatever the original task warrants — structured with a goal for T4/T5/T6).

**Falsifier:** if on a post-Fix-4 Arm B T4 trial that hits SIGTERM, the retry still produces `classification="one-shot"` with justification referencing "the user is correcting a protocol violation" (i.e., ignoring the BEGIN ORIGINAL TASK block), H4B was not the full story and H4A should be escalated. Plan §6.5 "5-trial smoke" is the intended validator.

**Expected outcome on the plan's S10 validation probe:**
- Three one-shot-no-goal cascades observed on Arm B (per plan §6.1) should disappear.
- Elapsed times may increase marginally on retry rounds (larger correction payload — preamble + 1500-byte task + correction = ~2KB instead of ~0.5KB). At Hermes's current token budget this is negligible; worst-case a few hundred extra tokens per retry round.
- No regression on non-retry paths (COMPLIANT attempts=1 trials never invoke `correction_for()`, so the preamble never fires there).

**Risk flagged per plan §6.6:**
- Risk: "fix alters behavior on legitimate one-shot tasks (T1/T2/T8)." *Mitigation per plan:* smoke-probe 2× T1 after fix. Expected: COMPLIANT attempts=1, classification=one-shot. Unchanged because T1/T2/T8 typically pass on attempt 0 — the preamble would only fire if a one-shot trial takes a retry round, in which case it says "preserve your original classification (one-shot / structured / long-horizon)" — the model still retains the one-shot option.
- Risk: "fix interacts with Fix 2." Not observed during implementation; Fix 2 is judge-side, Fix 4 is wrapper-side. No file overlap.
- Additional risk not in §6.6: the 1500-byte cap on `$TASK_TEXT` may truncate future long-prompt tasks (current probe-tasks.md prompts are ≤~1100 bytes per diag, so headroom exists). If future tasks exceed this, planner should bump the cap to e.g. 4000 and document.

---

## Files touched

**Edited:**
- `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh`
- `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh`
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md`

**Created (rollback snapshots):**
- `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh.pre-rev2-fix4`
- `/Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh.pre-rev2-fix4`

**Not touched (forbidden per plan §9 and worker scope):**
- `variants/hermes/delegate_worker_v2.py` (H4C rejected per diag)
- `probe-variantH-check.py`
- VM files
- Any core/, references/, playbooks/, templates/

**Probe runs:** None (scope forbade them).

---

## Next step per plan §8

Fix 4 is complete and ready for its judge verification gate (plan §8 S8). Judge brief per plan §6.5 should:
- Diff patched wrappers against `.pre-rev2-fix4` snapshots; confirm only `correction_for()` region changed plus comment block.
- Confirm Fix 3 additions preserved in variantI (pattern list above).
- Run bash -n on both.
- Inspect HERMES-variantF.md diff — single-item append in Classification pressure list.
- (Optional per plan §6.5) run 5-trial artificial-retry smoke on Arm B T4 / T5 to validate the H4B falsifier.
