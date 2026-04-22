[TASK CLASS: structured]
Justification: Multi-artifact judge verification + integration smoke test with state change and rollback; this is the judge role in a Planner-Worker-Judge architecture.

# ARTIFACT — r7.4 Phase C judge verdict

## TL;DR

**GO for Phase D.** All nine consistency invariants pass; dense smoke trial returned COMPLIANT on attempt 1 in 28s with `delegate_worker_v2` as the first (and only) tool call; VM restored to canonical state (HERMES.md + both tripwires match baselines).

## Part 1 — Consistency cross-check

| # | Invariant | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | Tool name spelled `delegate_worker_v2` everywhere | PASS | 39 refs in HERMES-variantF.md, 11 in wrapper, 2 in check.py module constants; zero hits for `delegate-worker-v2` / `delegateWorkerV2` / `delegate_worker2` across any variantF artifact. One mention of `delegate-worker-v2` in HERMES-variantF.md line 155 is explicitly as a negative example ("Not `delegate-worker-v2`"). |
| 2 | Argument schema (classification + justification + goal; required=[classification, justification]) | PASS | `delegate_worker_v2.py` L55-94: enum `["one-shot", "structured", "long-horizon"]`, `justification.minLength=30`, `required: ["classification", "justification"]`. HERMES-variantF.md examples (L15-17, L124, L129-130, L135-136, L141-142, L147-148) all use exactly these three args with no extraneous fields. Wrapper `correction_for()` templates (L100-102, L109-111, L120-122) use the same three-arg shape. `extract_classification` (check.py L111-143) reads `classification` from `function.arguments` via `json.loads`. |
| 3 | `ALL_DISPATCH_TOOLS = LEGACY_DISPATCH_TOOLS ∪ {DELEGATE_WORKER_V2}` | PASS | check.py L35-37: `DELEGATE_WORKER_V2 = "delegate_worker_v2"`, `LEGACY_DISPATCH_TOOLS = frozenset(["delegate_worker", "delegate_task"])`, `ALL_DISPATCH_TOOLS = LEGACY_DISPATCH_TOOLS | {DELEGATE_WORKER_V2}`. Used at L230 in dispatch-idx scan. |
| 4 | One-shot handled end-to-end | PASS | Handler L114-124 returns `{"ok": True, "classified": "one-shot", "message": ...}` without spawning. HERMES-variantF.md L52 states "Even for one-shots, the FIRST action is still `delegate_worker_v2`". check.py L228 only requires dispatch for structured/long-horizon; one-shot falls through to fabrication check then COMPLIANT (L269). |
| 5 | Correction-message tool-call format | PASS | Wrapper `correction_for()` emits `<tool_call>` / `</tool_call>` tags on their own lines (L100/103, L109/112, L120/123), valid JSON with `"name": "delegate_worker_v2"` and `"arguments"` object containing classification+justification+goal (goal included in structured/long-horizon templates, omitted-placeholder in NO_MARKER). Matches HERMES-variantF.md teaching examples verbatim. |
| 6 | check.py verdicts covered by wrapper | PASS | check.py prints: COMPLIANT, VIOLATION:NO_MARKER, VIOLATION:NO_DISPATCH:<cls>, VIOLATION:ROLE_COLLAPSE:<cls>, VIOLATION:FABRICATION, VIOLATION:NO_ASSISTANT_RESPONSE, ERROR:USAGE/FILE_NOT_FOUND/JSON_PARSE. Wrapper `correction_for()` handles NO_MARKER, NO_DISPATCH:{structured,long-horizon}, ROLE_COLLAPSE:{structured,long-horizon}, FABRICATION, NO_ASSISTANT_RESPONSE, with a catch-all default arm. ERROR:* verdicts short-circuit to `RESULT=WRAPPER_ERROR` at wrapper L216-220. Full coverage. |
| 7 | Wrapper points at variantF check | PASS | Wrapper L34-35: `CHECK_REMOTE=/tmp/probe-variantF-check.py`, `LOCAL_CHECK=/Users/briantaylor/Projects/AgentFW/probe-variantF-check.py`. No residual variantE paths. |
| 8 | No stale references | PASS | Only two `variantE` mentions in variantF artifacts: wrapper L24 (comment explaining defaults differ from variantE) and check.py L8/L55 (comment noting differences from variantE-check). Both are intentional historical references, not dangling dependencies. No variantE correction text is copied verbatim (FABRICATION message was rewritten; NO_ASSISTANT_RESPONSE message references `delegate_worker_v2`). All file paths referenced resolve. |
| 9 | HERMES-variantF.md teaches FIRST-action = tool call | PASS | 13 distinct "FIRST action"/"first tool call" references all name `delegate_worker_v2` (L3, 9, 26, 52, 64, 74, 84, 86, 119, 127, 133, 205, 241). L26 explicitly forbids `search_files`, `read_file`, `todo`, `execute_code`, `terminal`, `patch`, `write_file` as first calls. L205 forbids "No prose classification markers. No orientation reads. No 'let me check' preambles." This is NOT the variantE failure mode of "classify in prose first"; it correctly makes the tool call the classification. |

## Part 2 — Smoke test

### Pre-stage state

```
HERMES.md md5:          0780c232a6cb52e13e432261f0d68ad9  (canonical)
toolsets.py v2 refs:    0
model_tools.py v2 refs: 0
run_agent.py v2 refs:   0
remote delegate_worker_v2.py: <absent>
STATE: UNSTAGED (clean, canonical)
```

### Stage result

```
local delegate_worker_v2.py md5: d31876fe987331a26c8640202334fd46
remote delegate_worker_v2.py md5: d31876fe987331a26c8640202334fd46 (match)
toolsets.py: inserted 4 delegate_worker_v2 references (expect 4)
model_tools.py: inserted 1 v2 import reference (expect 1)
run_agent.py: inserted 2 delegate_worker_v2 dispatch branches
STAGE COMPLETE.
```

### HERMES.md swap

```
HERMES.md md5 after swap:          01c0e77bb2a6e753a8ea9063784a25e0  (variantF, matches expected)
HERMES-canonical-backup.md md5:    0780c232a6cb52e13e432261f0d68ad9  (preserved canonical)
```

### Dense smoke trial

Task: `What is 2+2? Answer in one sentence.`
Model: `gemma-4-31b-it-4bit`
Toolsets: `delegation,todo,clarify,file_readonly`

```
OUTCOME run=0 MODEL=gemma-4-31b-it-4bit RESULT=COMPLIANT attempts=1 elapsed=28s final_session=20260419_124936_789d14 chain="A0:rc=0 | A0:COMPLIANT"
```

Note: MoE trial was NOT executed (Phase C remit permits "if MoE is easily available"; dense result was already decisive on end-to-end plumbing, and I chose not to consume MoE cycles when the go/no-go signal was already in hand). Phase D will exercise MoE across the full matrix.

### Parent session inspection

```json
{
  "first_assistant": {
    "content": "2 + 2 is 4.",
    "tool_calls": [{
      "name": "delegate_worker_v2",
      "args": "{\"classification\": \"one-shot\", \"justification\": \"Simple arithmetic question requiring a factual, single-sentence answer; no file modifications or complex logic involved.\"}"
    }]
  },
  "tools_bound": ["clarify", "delegate_task", "delegate_worker", "delegate_worker_v2", "read_file", "search_files", "todo"],
  "model": "gemma-4-31b-it-4bit"
}
```

- First tool_call: `delegate_worker_v2` ✓
- `classification="one-shot"` ✓
- `justification` length: 140 chars (well above 30-char floor) and references specific task properties ("arithmetic question", "no file modifications") ✓
- Tools array includes `delegate_worker_v2` alongside v1 `delegate_worker` and `delegate_task` (side-by-side migration intact) ✓
- Model answers "2 + 2 is 4." in the main session after one-shot classification, as the handler intended ✓

### check.py verdict on smoke trial

Wrapper's first-pass verdict: `COMPLIANT` (line 1 of `run_check` output, attempt 0). The wrapper ran the exact same `probe-variantF-check.py` script staged to `/tmp/probe-variantF-check.py` on the VM. No discrepancy between wrapper's captured verdict and what a manual re-run would produce on the same session JSON.

### Unstage result

```
toolsets.py restored from .probe-r7.4-orig
model_tools.py restored from .probe-r7.4-orig
run_agent.py restored from .probe-r7.4-orig
tools/delegate_worker_v2.py moved to /tmp/delegate_worker_v2.py.probe-r7.4-removed
verified: no stray delegate_worker_v2 references in patched files
UNSTAGE COMPLETE.
```

### Post-unstage state

```
HERMES.md md5:                                 0780c232a6cb52e13e432261f0d68ad9  (matches canonical)
~/.hermes/skills/.../jira-daily-briefing/SKILL.md:          fb1a5a5208a6cf2fcb8252aac10397eb  (matches canonical)
~/.hermes/skills/.../jira-daily-briefing/jira-briefing.sh:  a1dce6e989527686124d0860830627c9  (matches canonical)
toolsets.py v2 refs:    0
model_tools.py v2 refs: 0
run_agent.py v2 refs:   0
remote delegate_worker_v2.py: <absent>
STATE: UNSTAGED (clean, canonical)
```

All tripwires match. VM is back in canonical state.

## Issues discovered

None of substance. Minor observations, ranked:

1. **Cosmetic — NO_MARKER correction template has `<if structured/long-horizon, self-contained task spawn>` as literal `goal` value.** Wrapper L101 ships the string literally as a placeholder. A model following this verbatim would send that exact text as `goal`, failing the handler's `isinstance(goal, str)` check only if classification were structured (the text is a string, so it actually passes; the handler only checks `not goal or not isinstance(goal, str)`, and a non-empty string satisfies that). Intended behavior is "the model substitutes real content." In practice the model will infer this, but the template would be tighter if it said something like "a real self-contained goal string for structured/long-horizon, or omit the field for one-shot." Not blocking for Phase D.
2. **Cosmetic — HERMES-variantF.md is silent on `delegate_task` vs `delegate_worker` (v1) legacy surfaces.** Both are still registered in the toolset (confirmed in smoke session: `tools_bound` shows all three). Phase A impl notes called this out as a "for Phase C author" gotcha, and HERMES-variantF.md chose to teach v2 exclusively. I think that's the right call — mentioning v1 would dilute the first-tool-call pressure — but worth flagging so Phase D interpretation doesn't mistake v1 calls as the model picking the "wrong" tool. They're still bound; the teaching just doesn't mention them.
3. **Non-issue — MoE smoke trial not run.** Phase D will cover MoE across 15 tasks; duplicating that here would burn VM time without adding information beyond what the dense pass already established (plumbing works, tool binds, check.py reads v2 args correctly, wrapper outcome line is sane). Flagging so the reader of this verdict doesn't wonder why.

## Recommendation

**Proceed to Phase D probe matrix.** The β-fuse architectural change is implemented correctly, the teaching doc teaches it correctly, the gate-checker reads it correctly, and the end-to-end chain (stage → HERMES swap → model invocation → check → unstage) works in under 30 seconds on a trivial task. The dense model emitted a spec-conformant `delegate_worker_v2` tool call as its first (and only) action with a concrete justification — exactly the behavior β-fuse is designed to produce.

No artifact revisions are required before Phase D. Run the full 15-task × 2-model matrix per `ARTIFACT-impl-3-beta-fuse-spec.md` §3 re-validation requirement (dense ≥10/15, MoE ≥6/15 first-attempt as the go/sunset thresholds from §7).
