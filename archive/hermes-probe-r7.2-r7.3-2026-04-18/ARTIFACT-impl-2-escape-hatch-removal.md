# IMPL-2 Artifact — Escape-Hatch Removal (r7.3 Layer 2)

**Date:** 2026-04-18
**Worker:** IMPL-2
**Authorization:** "GO GO GO" mandate
**Scope:** Strip escape clauses dense Gemma exploits to legitimately refuse dispatch (γ-finding from r7.2 drift investigation).

---

## Files Changed

1. **NEW**: `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantE.md` (sibling to variantD, not staged on VM)
2. **MODIFIED**: `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (correction text only)
3. **BACKUP**: `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh.pre-r7.3-l2-orig`

---

## Coordination with IMPL-1

When IMPL-2 began, no wrapper backup existed (`probe-variantE-wrapper.sh.pre-r7.3-orig` not found). IMPL-2 created its own backup `probe-variantE-wrapper.sh.pre-r7.3-l2-orig` capturing the pre-IMPL-1, pre-IMPL-2 baseline.

During the edit cycle, the file was modified by IMPL-1 (TOOLSETS env var support added). IMPL-2 re-read the file, confirmed IMPL-1's changes were isolated to the TOOLSETS feature (lines 24-32, 130, 156, 225), and that the `correction_for()` function was untouched. IMPL-2's edits are isolated to the `correction_for()` function. **No conflict.** Both layers coexist in the live wrapper.

---

## Diff 1: HERMES-variantD.md → HERMES-variantE.md

### Change A — Header (lines 1-3)

**Before (variantD):**
```
# AgentFW — Core Instructions (Hermes Variant D — Hard Contract + Dispatch Scaffolding)

> **PROBE-LOCAL FILE.** `HERMES-variantD.md`. Variant B's hard output contract + explicit scaffolding for a simplified dispatch tool (`delegate_worker`). Layered on the Jira-skill pattern: give the model a narrow tool surface with a worked format example. Not production.
```

**After (variantE):**
```
# AgentFW — Core Instructions (Hermes Variant E — Escape-Hatch Stripped)

> **PROBE-LOCAL FILE.** `HERMES-variantE.md`. Variant D's hard contract + dispatch scaffolding, but with the "you may relax" / "re-classify to one-shot" escape hatches removed (γ-finding from r7.2 drift investigation). For structured/long-horizon tasks, dispatch is mandatory; no rationalization route.
```

### Change B — Mid-response self-correction softener (line 82)

**Before:**
```
If you catch yourself doing any of these mid-response, stop and re-classify.
```

**After:**
```
If you catch yourself doing any of these mid-response, stop and dispatch a worker. Re-classification to `one-shot` is not the remedy — dispatch is.
```

Rationale: Dense Gemma exploited "stop and re-classify" as license to drop from `structured` to `one-shot` when self-correcting. Removed the re-classify route; substituted dispatch.

### Change C — "When NOT to use delegate_worker" list (lines 140-143)

**Before:**
```
**When NOT to use `delegate_worker`:**
- Class is `one-shot` (handle directly, no dispatch).
- Quick factual answer or orientation read.
- The task is literally a single tool call (e.g., run one terminal command) — just run it.
```

**After:**
```
**When NOT to use `delegate_worker`:**
- Class is `one-shot` (handle directly, no dispatch).
```

Rationale: "Quick factual answer or orientation read" and "literally a single tool call" gave dense rationalization fuel — it would unilaterally reframe a structured ticket as "really just an orientation read" and skip dispatch. Stripped to the one-shot exception only.

### Change D — Role-separation relaxation list (lines 153-157)

**Before:**
```
**Role separation can be relaxed ONLY when:**
- Class is `one-shot` (by definition below the threshold)
- Trivial changes with purely mechanical verification
- Quick lookups and orientation reads
- The human is actively co-driving as judge
```

**After:**
```
**Role separation can be relaxed ONLY when:**
- Class is `one-shot`
```

Rationale: The four-bullet relaxation list was the primary γ-flagged escape route. Each non-one-shot bullet ("trivial mechanical", "quick lookups", "human co-driving") was a separately defensible rationalization the dense model used to refuse dispatch on structured tasks. Stripped to one bullet only.

### Change E — Imperative tightening in HOW TO DISPATCH WORKERS opening

**Added to the opening sentence (line ~111 area):**

Original ends: "...instead of writing code directly in the main session. To do so, output a tool call..."

New: "...instead of writing code directly in the main session. **Structured tasks dispatch via `delegate_worker`; no exceptions outside `one-shot`.** To do so, output a tool call..."

### Sections kept VERBATIM from variantD

- HARD RULE: Role Separation block (lines 94-105 in variantD; load-bearing positive language per IMPL-2 spec)
- "Role separation is mandatory when" four-bullet list
- All other sections (classification criteria, permission protocol, session protocol, core pattern, examples)

---

## Diff 2: probe-variantE-wrapper.sh — `correction_for()` function

### NO_DISPATCH:structured / NO_DISPATCH:long-horizon (line 103)

**Before:**
```
Do not call patch, write_file, terminal, execute_code, or skill_manage in the main session for this task. If you truly believe dispatch isn't warranted, re-classify to `one-shot` with a specific justification — but by default, dispatch.
```

**After:**
```
Do not call patch, write_file, terminal, execute_code, or skill_manage in the main session for this task. Dispatch is mandatory for this class. Re-classification is not an option here.
```

Rationale: The "re-classify to `one-shot`" softener was the verbatim escape route Gemma used in r7.2 trials. The corrective re-prompt itself was teaching the escape. Replaced with hard "not an option" language.

### ROLE_COLLAPSE:structured / ROLE_COLLAPSE:long-horizon

No changes. The existing message contains no re-classify language; only direct "your FIRST substantive action must be `delegate_worker`" instruction. Per IMPL-2 spec ("if there's any reclassify language"), no edit needed.

### Other violation messages

NO_MARKER, FABRICATION, NO_ASSISTANT_RESPONSE, default — all unchanged.

---

## Smoke Test

**Command:**
```bash
bash -n /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh  # parse check
MODEL=gemma-4-31b-it-4bit SOURCE_PREFIX=probe-r7.3-l2-smoke \
  /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh 0 <<<"What's the capital of France?"
```

**OUTCOME:**
```
PARSE_OK
[probe-r7.3-l2-smoke run0] MODEL=gemma-4-31b-it-4bit SOURCE_PREFIX=probe-r7.3-l2-smoke TOOLSETS=<default> TIMEOUT=900s
[probe-r7.3-l2-smoke run0] task: What's the capital of France?...
[probe-r7.3-l2-smoke run0] attempt 0: initial invocation
[probe-r7.3-l2-smoke run0] session_id captured: 20260418_193538_eb0c58
[probe-r7.3-l2-smoke run0] attempt 0 verdict: COMPLIANT
OUTCOME run=0 MODEL=gemma-4-31b-it-4bit RESULT=COMPLIANT attempts=1 elapsed=46s final_session=20260418_193538_eb0c58 chain="A0:rc=0 | A0:COMPLIANT"
```

**Verdict:** PASS — COMPLIANT in 1 attempt, 46s elapsed. No behavior regression for trivial one-shot. The `TOOLSETS=<default>` field in the log line confirms IMPL-1's L1 layer is also active and coexisting cleanly.

Note: HERMES-variantE.md is NOT yet staged on the VM — the smoke test ran against the existing remote `HERMES.md` (which is variantD content per current deployment). The smoke test exercises only the wrapper's correction-text path; the variantE doc is a sibling artifact awaiting a separate deployment step.

---

## Rollback Procedure

**Layer 2 only (this work):**
```bash
# 1. Remove the new sibling doc (no deployment to undo on VM)
rm /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantE.md

# 2. Restore the wrapper correction text from backup
#    NOTE: pre-r7.3-l2-orig captures pre-IMPL-1 + pre-IMPL-2 state.
#    Using it directly will ALSO revert IMPL-1's TOOLSETS feature.
#    To rollback ONLY L2 (preserving L1), manually edit the
#    NO_DISPATCH:structured/long-horizon correction text back to the
#    original "If you truly believe dispatch isn't warranted, re-classify..."
#    sentence (see Diff 2 above for exact strings).

# Full rollback (both L1 and L2):
cp /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh.pre-r7.3-l2-orig \
   /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh
```

**Surgical L2-only rollback (preserves IMPL-1):**

Edit `correction_for()` `VIOLATION:NO_DISPATCH:structured|long-horizon` branch and replace:
- `"Dispatch is mandatory for this class. Re-classification is not an option here."`
with:
- `"If you truly believe dispatch isn't warranted, re-classify to \`one-shot\` with a specific justification — but by default, dispatch."`

---

## Summary

- HERMES-variantE.md created as sibling to variantD with 4 escape-hatch strips + 1 imperative tightening + header rewrite. Load-bearing "HARD RULE: Role Separation" block kept verbatim.
- Wrapper `correction_for()` updated for NO_DISPATCH; ROLE_COLLAPSE unchanged (no re-classify language present).
- Wrapper still parses; smoke test passes COMPLIANT in 1 attempt for trivial one-shot.
- Coexists cleanly with IMPL-1's TOOLSETS env-var addition.
- Rollback documented; HERMES-variantE.md is a sibling not yet deployed to VM, so deployment-side rollback is a no-op.
