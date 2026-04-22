# ARTIFACT — r7.6 P1-C Fix 2 fresh-context judge (2026-04-19)

## Verdict: ACCEPT

The patched `judge-trial.py` (md5 `709ef98a644b42d46a03a10aaf728f2a`) satisfies every
checkable claim in `PLAN-r7.6-P1C-fixes-implementation.md` §4.4 and
`ARTIFACT-r7.6-P1C-fix2-impl.md`. All six checks pass. No out-of-scope mutations.
Recommend proceeding to C2 second-sample calibration.

---

## Evidence by check

### Check 1 — Diff confirms both regexes + thrash strictening + sibling support

File examined: `/tmp/probe-r7.6-P1C-logs.post-fix2/judge-trial.diff` (353 lines).

- **`_MARKER_ONLY_RE` (Class A, plan §4.1):** present at diff lines 35-42. Regex
  enumerates all six alternatives from the plan: `channel | tool_call | start | end |
  message | return` plus the two prefixed forms `thought\n<channel|>` and
  `analysis\n<channel|>`. Case-insensitive, DOTALL. PASS.

- **`_PSEUDO_TOOL_CALL_RE` (Class B, plan §4.1):** present at diff lines 50-55.
  Implementation adds a second tail-anchored variant
  `_PSEUDO_TOOL_CALL_TAIL_RE` (diff lines 56-61) — this is a designed addition
  needed for the armB-T5-run1 trial where prose precedes the fenced
  pseudo-call (acknowledged in impl notes). Functions allow-lists nine tool
  names, case-insensitive, DOTALL. PASS.

- **Near-identical substring heuristic removed (plan §4.2 Change 3):** diff lines
  120-143 show the substring `q[i] in q[i-1]` branch deleted and replaced with
  strict equality `last_search_queries[i] == last_search_queries[i-1]`. Error
  message updated to `"literally-identical queries — thrash"`. PASS.

- **Sibling-children handling (plan §4.3 Change 4):**
  `SIBLING_CHILDREN_BY_PARENT` table at diff lines 15-27 contains exactly the
  two parents documented in `ARTIFACT-r7.6-P1C-run-only.md` ADDITIONAL_CHILD_SESSIONS
  (T6-run5 with 3 children, T10-run5 with 2 children). The `judge()` function is
  rewritten to iterate candidate sids, call `_judge_single_child()` per sid, and
  pick the best by rank `PASS > FAIL > LOST` (diff lines 272-299). Rationale now
  records `sibling_child_count`, `chosen_child_sid`, and when >1 sibling
  `sibling_verdicts`. PASS.

### Check 2 — Replay flips match expected set

Common-trial diff (pre-fix snapshot-rev2 vs post-fix2 replay):

| Trial | Pre-fix | Post-fix | Expected by plan | Match |
|---|---|---|---|---|
| armA-T4-run4 (g4) | FAIL | PASS | FAIL → PASS (Change 3) | YES |
| armB-T5-run1 (g6) | PASS | FAIL | PASS → FAIL (Change 2 tail regex) | YES |
| armB-T5-run5 (g10) | FAIL | PASS | FAIL → PASS (declared consequence of Change 3, plan §4.5) | YES |

All remaining 32 common trials unchanged — `diff` against both arms shows
only these 3 flips + 6 newly-added Arm B trials (g15..g20 = T6-run5 + T10-run1..5).

- All 11 Arm A + Arm B trials that previously FAILed for channel-marker-only
  content remain FAIL (verified by inspecting the pre-fix/post-fix verdict
  listings; no channel-pollution FAIL flips to PASS).
- Arm A known-clean trials (g1, g3, g5) remain PASS.
- No unexpected flips.

PASS.

### Check 3 — Calibration agreement 5/5

Parent-sid cross-walk to fresh-verdict artifacts (authoritative gate target):

| Brief | Fresh verdict | Parent SID | Fresh verdict | Judge output | Match |
|---|---|---|---|---|---|
| brief1 (armA-T4-run1, TRIAL_N=1) | verdict-1 | `20260419_202058_1ba6de` | PASS | PASS | YES |
| brief2 (armA-T4-run4, TRIAL_N=4) | verdict-2 | `20260419_202309_a7614f` | PASS | PASS | YES |
| brief3 (armB-T5-run1, TRIAL_N=6) | verdict-3 | `20260419_212503_e0a728` | FAIL | FAIL | YES |
| brief4 (armB-T6-run2, TRIAL_N=12) | verdict-4 | `20260419_220217_711f56` | FAIL | FAIL | YES |
| brief5 (armB-T4-run3, TRIAL_N=3) | verdict-5 | `20260419_212256_d885e6` | LOST | LOST | YES |

5/5. PASS.

Independent spot-checks (hard-rule requirement):

1. Re-ran patched judge on armB-T5-run1 (brief 3): returned `WORKER_QUALITY=FAIL`,
   `COMPLETION=FAIL` with evidence `pseudo-tool-call as markdown (no structured
   tool_call): ...'``python\nsearch_files(...)\n```'` — matches brief verbatim
   and fresh verdict 3's FAIL determination (worker emitted a fenced pseudo
   tool-call as its final content).
2. Re-ran patched judge on armB-T6-run5 (sibling-children case): returned
   `WORKER_QUALITY=FAIL`, `SIBLING_CHILD_COUNT=3`, `CHOSEN_CHILD_SID=20260419_225406_27640d`,
   with full `sibling_verdicts` listing all three children (`225406_27640d`,
   `225521_775cf5`, `225547_3a9890`) — all FAIL, best-of picks primary. Matches
   stored per-trial output bit-for-bit, confirming the worker's artifact was not
   hand-edited.

### Check 4 — Sibling-children integration

T6-run5 (parent `20260419_225355_721123`): 3 children evaluated, all FAIL,
rationale records `"sibling_child_count": 3` and a `sibling_verdicts` array of
length 3. `CHOSEN_CHILD_SID=20260419_225406_27640d` (primary, best-of ties
broken by first-evaluated). Matches `ARTIFACT-r7.6-P1C-run-only.md` line 64-65.

T10-run5 (parent `20260419_230405_91730e`): 2 children evaluated, both FAIL,
rationale records `"sibling_child_count": 2` and a 2-element `sibling_verdicts`
array with `230410_22a345` and `230636_79f674`. Matches `ARTIFACT-r7.6-P1C-run-only.md`
line 66. PASS.

### Check 5 — No out-of-scope mutations

- `probe-variantH-check.py` md5 = `873935f65e1bb91942dde1139dd57f92` — matches
  expected unchanged hash. mtime `Apr 19 20:07:18` (pre-fix, unchanged since
  implementation began at ~23:47).
- No VM-side writes (judge does SSH fetch only; replay uses cached JSON).

PASS.

### Check 6 — py_compile

`python3 -m py_compile /tmp/probe-r7.6-P1C-logs/judge-trial.py` returns 0.
PASS.

---

## Discrepancies between worker's claims and actual state

None of substance. Three minor observations:

1. Worker's impl artifact credits the armB-T5-run1 flip to Change 2 tail-anchored
   regex. Verified correct — the tail regex actually fires (not the full-content
   one) as shown by the per-trial brief3 evidence snippet.
2. Worker notes the armB-T5-run5 PASS flip is a "declared consequence" of
   Change 3 (thrash strictening). Verified — the pre-fix FAIL reason was
   near-identical-query thrash, which no longer fires under strict equality.
3. Calibration brief TRIAL_N numbers differ from fresh-verdict TRIAL_N numbers
   (brief2 shows TRIAL_N=4 vs fresh verdict 2's TRIAL_N=2). This is expected —
   briefs use the global trial index (T4 offset + run_num = 0+4=4), while
   fresh verdicts were numbered sequentially 1..5 by the calibration sampler.
   Parent SID uniquely identifies the trial and matches in every case.

---

## Recommendation

**Proceed to C2 second-sample calibration** (next 5 unseen trials) per planner's
C3 directive. The patched judge is ready for the broader disagreement-survey
phase. No revisions required.

Scope reminder for the next judge run: remain READ-ONLY on judge-trial.py; if
C2 surfaces a verdict disagreement, loop back to planner for a rev-3 patch,
not a direct edit.
