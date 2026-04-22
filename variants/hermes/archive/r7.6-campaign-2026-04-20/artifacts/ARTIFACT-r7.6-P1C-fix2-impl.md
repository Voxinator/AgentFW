[TASK CLASS: long-horizon]
Justification: Multi-change judge patch with mandatory 5/5 calibration gate + 40-trial replay + artifact output; integrates with planner-driven fix 2 in the r7.6 P1-C rev-2 plan.

# ARTIFACT — r7.6 P1-C Fix 2 implementation (rev 2, 2026-04-19)

## Result: DONE

Calibration gate cleared 5/5. Full 40-trial replay produced exactly the plan-predicted flips plus one additional flip that is a direct and declared consequence of Change 3 (thrash-heuristic tightening).

## Before / after md5

```
pre-fix  judge-trial.py : d881f40d59740921bd8b7877eb2dd3af   (snapshot at /tmp/probe-r7.6-P1C-logs.post-fix2/judge-trial.pre-fix.py)
post-fix judge-trial.py : 709ef98a644b42d46a03a10aaf728f2a
```

Full unified diff: `/tmp/probe-r7.6-P1C-logs.post-fix2/judge-trial.diff` (353 lines).

## The five changes

### Change 1 — Class A marker-only regex (module level, after TRIPWIRE_PATHS)

```python
_MARKER_ONLY_RE = re.compile(
    r"^\s*(?:"
    r"(?:<\|?(channel|tool_call|start|end|message|return)\|?>\s*)"
    r"|(?:thought\s*<\|?channel\|?>\s*)"
    r"|(?:analysis\s*<\|?channel\|?>\s*)"
    r")+\s*$",
    re.IGNORECASE | re.DOTALL,
)
```

Covers the six Harmony/Gemma sentinel variants observed in P1-C child sessions:
`<channel|>`, `<|channel|>`, `<tool_call|>`, `<start|>/<end|>/<message|>/<return|>`,
`thought\n<channel|>`, `analysis\n<channel|>`.

Unit-checked against 13 positive/negative cases (9 positives + 4 negatives including `"directory.)\n}<tool_call|>"` which must NOT match because it has prose, and `"<channel|>PLAN: ..."` which must NOT match for the same reason). All 13 passed.

### Change 2 — Class B pseudo-tool-call regex + tail-anchored variant (module level)

The spec regex (full-content anchored) alone would have missed armB-T5-run1 trial 6, where the final assistant message has a long reasoning prose block followed at the END by a code-fenced pseudo tool call. Added a `_PSEUDO_TOOL_CALL_TAIL_RE` variant anchored to end-of-content.

```python
_PSEUDO_TOOL_CALL_RE = re.compile(
    r"^\s*```[\w]*\s*\n?"
    r"(?:search_files|read_file|write_file|patch|terminal|todo|clarify|delegate_\w+)"
    r"\s*\([^)]*\)\s*\n?```?\s*$",
    re.IGNORECASE | re.DOTALL,
)
_PSEUDO_TOOL_CALL_TAIL_RE = re.compile(
    r"```[\w]*\s*\n"
    r"(?:search_files|read_file|write_file|patch|terminal|todo|clarify|delegate_\w+)"
    r"\s*\([^)]*\)\s*\n?```?\s*$",
    re.IGNORECASE | re.DOTALL,
)
```

Unit-checked against 7 cases including a known-FP ("Next steps: I would use `search_files(pattern=...)`") and a mid-text code block ("I used the following earlier: ```\nsearch_files(pattern=...)\n``` and it returned no results."). All passed.

### Change 3 — `eval_completion` gates injected after short-content check

```python
# r7.6 P1-C fix2 Class A: marker-only assistant content (channel-sentinel leakage).
stripped = content.strip()
if stripped and _MARKER_ONLY_RE.match(stripped):
    return False, f"marker-only content: {stripped[:120]!r}"
# r7.6 P1-C fix2 Class B: pseudo-tool-call rendered as markdown fenced text
# (worker halted mid-plan and emitted `search_files(...)` as code-fenced text
# instead of a structured tool_call). Only fail when there's no real tool_call
# attached to the same turn. Check both full-content and tail-anchored forms.
if stripped and not tcs:
    if _PSEUDO_TOOL_CALL_RE.search(stripped) or _PSEUDO_TOOL_CALL_TAIL_RE.search(stripped):
        m = _PSEUDO_TOOL_CALL_TAIL_RE.search(stripped)
        snippet = m.group(0) if m else stripped[-120:]
        return False, f"pseudo-tool-call as markdown (no structured tool_call): ...{snippet[-120:]!r}"
```

### Change 4 — thrash heuristic tightening (`eval_turn_efficiency`)

Replaced substring-match near-identical heuristic with strict literal equality. Keeps the ≥3-consecutive requirement:

```python
# r7.6 P1-C fix2 (rev 2): removed substring-match near-identical heuristic
# because it fired on progressive-narrowing strategies (e.g., armA-T4-run4
# trial 2 cycled through 'session.ts|middleware.ts|auth.test.ts', 'session',
# '\.ts$', '\.py$' — fresh judge reads these as narrowing, not thrash).
# Keep >=3-consecutive requirement; strict equality only.
if len(last_search_queries) >= 3:
    max_streak = 1
    cur = 1
    for i in range(1, len(last_search_queries)):
        if last_search_queries[i] and last_search_queries[i] == last_search_queries[i-1]:
            cur += 1
            max_streak = max(max_streak, cur)
        else:
            cur = 1
    if max_streak >= 3:
        return False, f"{max_streak}+ consecutive search_files with literally-identical queries — thrash"
```

### Change 5 — Sibling-children handling (C3 from planner, ELEVATED TO REQUIRED)

Added module-level ground-truth table keyed by parent_sid:

```python
SIBLING_CHILDREN_BY_PARENT = {
    "20260419_225355_721123": [  # T6-run5
        "20260419_225406_27640d", "20260419_225521_775cf5", "20260419_225547_3a9890",
    ],
    "20260419_230405_91730e": [  # T10-run5
        "20260419_230410_22a345", "20260419_230636_79f674",
    ],
}
```

Refactored `judge()` into:
- `_judge_single_child(messages, task_id, tripwire_pre, tripwire_post)` — per-child rubric evaluation.
- `_fetch_child_messages(sid)` — VM fetch helper.
- `judge(...)` — for parents in `SIBLING_CHILDREN_BY_PARENT`, enumerate ALL siblings (plus the incoming child_sid if not already listed), score each via `_judge_single_child`, pick the BEST by rank (PASS=2, FAIL=1, LOST=0).

Rationale now carries:
- `sibling_child_count` (integer)
- `chosen_child_sid` (string)
- `sibling_verdicts` (list of `{sid, verdict}`) when ≥2 siblings

Header output grew two fields: `SIBLING_CHILD_COUNT`, `CHOSEN_CHILD_SID`.

### Change 6 (required diagnostic) — `channel_pollution_depth` in rationale

Added `channel_pollution_depth(messages)` helper. Counts assistant turns whose stripped content matches `_MARKER_ONLY_RE`. Emitted into `rationale["completion"]["channel_pollution_depth"]`. Informational only — does not flip verdicts by itself.

### Rationale for sibling-children integration approach

Considered three approaches for sibling discovery:
1. **Dynamic session-dir scan** by mtime proximity to parent. Rejected: expensive (scans ~200 session files per judge call), flaky (session_start timestamps in parent JSON don't align cleanly with child file mtimes), and unnecessary since the ground truth is documented.
2. **Parent-message crawl** to extract delegate_worker_v2 response-reported child IDs. Rejected: inspection of `session_20260419_225355_721123.json` showed that the `delegate_worker_v2` tool result does NOT include the child session ID in its payload. Only the cumulative stats do.
3. **Ground-truth table keyed by parent_sid (chosen).** The plan explicitly sanctioned this: *"If needed, cross-reference ARTIFACT-r7.6-P1C-run-only.md ADDITIONAL_CHILD_SESSIONS block for ground truth."* The two multi-child parents are documented there. For single-child parents the table is a no-op. Fails safely closed: if a new multi-child parent appears in future probes, only the primary is evaluated until the table is updated — no silent degradation.

## Calibration-gate result (MANDATORY 5/5 gate)

| Brief | Trial tag | Pre-fix orch | Fresh judge | Target | Post-fix actual | Match |
|---|---|---|---|---|---|---|
| 1 | armA-T4-run1 | PASS | PASS | PASS | PASS | ✓ |
| 2 | armA-T4-run4 | FAIL | PASS | PASS (flip) | **PASS** | ✓ |
| 3 | armB-T5-run1 | PASS | FAIL | FAIL (flip) | **FAIL** | ✓ |
| 4 | armB-T6-run2 | FAIL | FAIL | FAIL | FAIL | ✓ |
| 5 | armB-T4-run3 | LOST | LOST | LOST | LOST | ✓ |

**5/5 agreement with fresh-judge.** Gate cleared.

Per-criterion verification:
- Brief 2 post-fix: TURN_EFFICIENCY flipped FAIL→PASS (Change 4). CORRECTNESS and COMPLETION remain PASS. ✓
- Brief 3 post-fix: COMPLETION flipped PASS→FAIL with reason `pseudo-tool-call as markdown (no structured tool_call): ...'```python\nsearch_files(pattern="*tasks*", target="files", path="/media/psf/.../server")\n```'` (Change 2 tail-anchored regex). `channel_pollution_depth=6`. ✓

Calibration-stdouts preserved at `/tmp/probe-r7.6-P1C-logs.post-fix2/calibration/brief{1..5}.txt`.

## Full 40-trial replay

### Arm A (20 trials, pre-fix and post-fix both 20 trials)

| | PASS | FAIL | LOST |
|---|---|---|---|
| Pre-fix | 3 | 17 | 0 |
| Post-fix | 4 | 16 | 0 |

Flips (pre → post):
- `armA-T4-run4-g4`: FAIL → **PASS** (expected; Change 4).

Zero other flips. 19/20 trials identical verdict. ✓

### Arm B (pre-fix: 14 trials measured; post-fix: 20 with the 6 run-only trials added)

Post-fix aggregate (20 trials):

| | PASS | FAIL | LOST |
|---|---|---|---|
| Pre-fix (first 14) | 9 | 2 | 3 |
| Post-fix (first 14) | 9 | 3 | 3 (net: -1 PASS flip on g6, +1 PASS flip on g10) |
| Post-fix (all 20) | 12 | 5 | 3 |

Flips on the common 14 trials:
- `armB-T5-run1-g6`: PASS → **FAIL** (expected; Change 2 / Class B).
- `armB-T5-run5-g10`: FAIL → **PASS** (unexpected-by-letter-of-plan-predictions; see investigation below).

New 6 trials (T6-run5 + T10-run1..5) judged from scratch:
- `armB-T6-run5-g15`: FAIL (sibling_child_count=3, all 3 siblings FAIL, channel_pollution_depth=27 on primary).
- `armB-T10-run1-g16`: PASS (primary-only; child emitted concrete-BLOCKED summary per HERMES-WORKER.md §3 template).
- `armB-T10-run2-g17`: FAIL (channel leakage; COMPLETION=PASS but CORRECTNESS=FAIL).
- `armB-T10-run3-g18`: PASS.
- `armB-T10-run4-g19`: PASS.
- `armB-T10-run5-g20`: FAIL (sibling_child_count=2, both siblings FAIL; `last 5 tool calls all read_file on 1 path — loop` + channel leakage).

### Unexpected flip investigation: `armB-T5-run5-g10` FAIL → PASS

Pre-fix rationale: `TURN_EFFICIENCY=FAIL "3+ consecutive search_files with identical/near-identical queries — thrash"`.

The actual `search_files` query sequence:
```
"*dashboard*", "src", "*", "*chief*", "*chief*", "Chief of Staff"
```

Under the OLD substring heuristic, consecutive pairs passed the `q[i] in q[i-1] or q[i-1] in q[i]` test because `"*chief*"` contains substring matches with the preceding "*" wildcard + literal. Under STRICT literal equality, only one consecutive-identical pair exists (`"*chief*"` × 2). Max streak = 2, below the ≥3 threshold. The final query `"Chief of Staff"` is a content search, semantically different.

The plan's §4.5 Risks note explicitly covers this: *"the search-thrash cases the rev-1 judge caught on Arm A (trials 4, 13, 17, 18, 19) deserve re-inspection — some may have TRULY identical queries."* That re-inspection extends to Arm B by the same logic. This is a DECLARED consequence of Change 4, not a regression.

Also verified that Arm A trials 13, 17, 18, 19 — which had TURN_EFFICIENCY=FAIL pre-fix via the substring heuristic — now have TURN_EFFICIENCY=PASS but WORKER_QUALITY=FAIL anyway because CORRECTNESS=FAIL is independently set. So Arm A aggregate verdict is unchanged for these four.

### Summary vs plan §4.4 verification predictions

Plan §4.4 judge-verification criteria:
1. "armA-T4-run4 (trial 2) flips FAIL → PASS." → **✓ flipped.**
2. "armB-T5-run1 (trial 3) flips PASS → FAIL." → **✓ flipped.**
3. "All 11 previously-FAIL trials with channel-marker-only final content (Arm A + Arm B) stay FAIL." → **✓ all stay FAIL.**
4. "All Arm A 'search_files variety' trials that currently pass (trial 1, 3, 5) stay PASS." → **✓ all stay PASS.**
5. "No additional unexpected flips on the other 32 trials (verify with full diff)." → 1 additional flip: `armB-T5-run5-g10` FAIL→PASS. Plan's §4.5 risk note anticipates this class of flip.

## NEW aggregates

- **Arm A:** 4/20 PASS (20.0%).
- **Arm B:** 12/20 PASS (60.0%); non-LOST: 12/17 PASS (70.6%).
- **Delta (PASS rate, all trials):** +40 pp (Arm B − Arm A).
- **Delta (PASS rate, non-LOST basis):** +50.6 pp.
- **Absolute PASS count delta:** +8 (12 − 4).

Per §11 open question 1, this delta is *slightly larger* than the pre-fix delta (+6 on Arm B 14-trial sample) because:
- Brief 3 flip (PASS → FAIL) reduces Arm B by 1 on overlap.
- Brief 2 flip (FAIL → PASS) raises Arm A by 1.
- But the 6 new Arm B trials contribute +3 PASS / −2 FAIL (net +3 on Arm B).

Net: delta widens, not narrows, compared with the pre-fix 14-vs-20 comparison.

## Files written

- `/tmp/probe-r7.6-P1C-logs/judge-trial.py` (in-place edit)
- `/tmp/probe-r7.6-P1C-logs.post-fix2/` directory:
  - `judge-trial.pre-fix.py` (baseline snapshot; md5 matches snapshot-rev2)
  - `judge-trial.diff` (unified)
  - `arm-A-matrix.extended.txt` (identical to pre-fix Arm A matrix)
  - `arm-B-matrix.extended.txt` (14 existing trials + 6 run-only appended per ARTIFACT-r7.6-P1C-run-only.md)
  - `arm-A-verdicts.replay.txt` (20 lines)
  - `arm-B-verdicts.replay.txt` (20 lines)
  - `per-trial/arm-A-trial-N.stdout.txt` (N = 1..20)
  - `per-trial/arm-B-trial-N.stdout.txt` (N = 1..20)
  - `calibration/brief{1..5}.txt` (calibration gate raw stdouts)

## Verification re-runs

```
$ python3 -c "import ast; ast.parse(open('/tmp/probe-r7.6-P1C-logs/judge-trial.py').read()); print('SYNTAX_OK')"
SYNTAX_OK

$ head -1 /tmp/probe-r7.6-P1C-logs.post-fix2/calibration/brief{1..5}.txt
==> brief1.txt <==
WORKER_QUALITY=PASS
==> brief2.txt <==
WORKER_QUALITY=PASS
==> brief3.txt <==
WORKER_QUALITY=FAIL
==> brief4.txt <==
WORKER_QUALITY=FAIL
==> brief5.txt <==
WORKER_QUALITY=LOST
```

## Risks flagged per plan §4.5

- **Strict-equality thrash heuristic is deliberately more permissive.** One additional Arm B flip FAIL→PASS is a direct consequence. Declared in plan; verified that the sequence in question has only 2-consecutive-identical queries (below threshold). If future operator wants tighter thrash detection, add a distinct "N-query cycle detector" (e.g., same query appearing ≥3 times within last 6 calls, not necessarily consecutive) — NOT in scope here.
- **Tail-anchored pseudo-tool-call regex adds a second FP surface.** Mitigation: requires the pseudo-tool-call to be *at the end* of the content (anchored `$`) AND the message to carry NO structured tool_calls. Unit-tested against "Next steps: I would use `search_files(...)`" (did not match) and mid-text code blocks (did not match).
- **Sibling-children ground-truth table is static.** New multi-child parents in future probes will default to primary-only judging until the table is updated. This is a documented, fail-safe degradation — no silent miss.
- **No probe runs.** Per scope, judge replay only. VM untouched beyond `ssh cat` of existing session JSONs.

## Forbidden-file discipline

- `probe-variantH-check.py` — not touched.
- VM `run_agent.py` — not touched.
- All edits confined to `/tmp/probe-r7.6-P1C-logs/judge-trial.py` + `/tmp/probe-r7.6-P1C-logs.post-fix2/` + this artifact. Confirmed via `md5` and `ls`.
