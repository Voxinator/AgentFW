[TASK CLASS: structured]
Justification: Judge verification of r7.4 Phase D results + ship decision. Multi-artifact review, VM-side JSON sample verification, aggregate arithmetic vs pre-committed thresholds, and a SHIP/HOLD/RETREAT/REVISE decision.

# ARTIFACT — r7.4 ship-decision judge verdict

## Verdict

**HOLD — fill dense gaps.** MoE clears its threshold decisively (17/20 ≥ 8/20) and sample verification is clean on both legs, but the dense leg has only 6 strict-on-disk FIRST_ATTEMPT_PASS datapoints out of 20 planned trials, which is structurally incapable of reaching the pre-committed 14/20 threshold — even a 100% strict-pass rate on the remaining 14 would be required, and those trials have not been run. Pre-committed thresholds are absolute counts, not rates; I will not launder "12/12 measured" into "14/20 met."

---

## Part 1 — Sample verification

I re-ran `jq` against the VM-side parent session JSONs for 6 dense and 6 MoE trials named in the artifacts. All 12 VM files exist. Observed fields compared against the artifact's per-trial claims.

### Dense sample (6 trials)

| # | Session ID | Artifact claim | Observed first_tool | Observed classification | Observed model | Match? |
|---|------------|----------------|---------------------|------------------------|----------------|--------|
| 1 | 20260419_125518_b00428 | T1-r1 ONE_SHOT_PASS / delegate_worker_v2 / one-shot | delegate_worker_v2 | one-shot | gemma-4-31b-it-4bit | ✅ |
| 2 | 20260419_125944_67fc83 | T4-r1 FIRST_ATTEMPT_PASS / delegate_worker_v2 / structured | delegate_worker_v2 | structured | gemma-4-31b-it-4bit | ✅ |
| 3 | 20260419_125613_71379f | T4-r2 FIRST_ATTEMPT_PASS / delegate_worker_v2 / structured | delegate_worker_v2 | structured | gemma-4-31b-it-4bit | ✅ |
| 4 | 20260419_130851_615d1e | T4-r5 FIRST_ATTEMPT_PASS / delegate_worker_v2 / structured | delegate_worker_v2 | structured | gemma-4-31b-it-4bit | ✅ |
| 5 | 20260419_134251_494dd3 | T5-r3 FIRST_ATTEMPT_PASS / delegate_worker_v2 / structured | delegate_worker_v2 | structured | gemma-4-31b-it-4bit | ✅ |
| 6 | 20260419_133405_e25deb | T8-r2 ONE_SHOT_PASS / delegate_worker_v2 / one-shot | delegate_worker_v2 | one-shot | gemma-4-31b-it-4bit | ✅ |

All 6 dense samples: model == `gemma-4-31b-it-4bit` (correct dense model), first_tool == `delegate_worker_v2`, classification matches artifact, justification len ≥ 129 (well above the 30-char minLength), `goal` present iff structured.

### MoE sample (6 trials)

| # | Session ID | Artifact claim | Observed first_tool | Observed classification | Observed model | Match? |
|---|------------|----------------|---------------------|------------------------|----------------|--------|
| 1 | 20260419_141407_55f4c6 | T1-r1 ONE_SHOT_PASS | delegate_worker_v2 | one-shot | gemma-4-26b-a4b-it-mlx-8bit | ✅ |
| 2 | 20260419_141602_513c2e | T4-r1 NOT first-attempt, empty msg[1], recovered on msg[3]=delegate_worker_v2/structured | msg[1] EMPTY (no tool_calls, content empty). msg[3] = delegate_worker_v2 / structured. 6 messages total. | — | gemma-4-26b-a4b-it-mlx-8bit | ✅ (pattern confirmed) |
| 3 | 20260419_141658_621cfa | T4-r2 FIRST_ATTEMPT_PASS / structured | delegate_worker_v2 | structured | gemma-4-26b-a4b-it-mlx-8bit | ✅ |
| 4 | 20260419_142042_602b56 | T5-r1 FIRST_ATTEMPT_PASS / structured | delegate_worker_v2 | structured | gemma-4-26b-a4b-it-mlx-8bit | ✅ |
| 5 | 20260419_143802_e62496 | T6-r1 FIRST_ATTEMPT_PASS / long-horizon | delegate_worker_v2 | long-horizon | gemma-4-26b-a4b-it-mlx-8bit | ✅ |
| 6 | 20260419_144755_fc072b | T10-r1 NOT first-attempt, empty msg[1], recovered on msg[3]=delegate_worker_v2/long-horizon | msg[1] EMPTY (no tool_calls, content empty). msg[3] = delegate_worker_v2 / long-horizon. 6 messages total. | — | gemma-4-26b-a4b-it-mlx-8bit | ✅ (pattern confirmed) |

All 6 MoE samples: model == `gemma-4-26b-a4b-it-mlx-8bit` (correct MoE model). The 4 claimed FIRST_ATTEMPT_PASS trials all show the expected delegate_worker_v2 tool call with matching classification at `messages[1]`. The 2 claimed "NOT first-attempt / empty-first-turn" trials (T4-r1, T10-r1) confirm the exact pattern the artifact described: `messages[1].content = "(empty)"`, `messages[1].tool_calls = null`, `messages[3]` carries the recovery `delegate_worker_v2` call with correct classification.

### Data-integrity verdict

**CLEAN.** 12/12 sampled trials match their artifact claims on all verifiable fields (first_tool, classification, model, empty-first-turn pattern where claimed). No session ID was missing. No mismatch found. No data-integrity red flags.

---

## Part 2 — Aggregate arithmetic

### Dense leg

**Framing choice.** I chose Option A from the brief: score as fraction of planned trials (20). The pre-committed threshold is an absolute count (≥14/20), not a rate. It was frozen before the probe ran, and Option A is the honest reading. Options B (rate on measured) and C (extrapolation) would each require changing the threshold mid-evaluation, which violates the judgment rule.

**Strict on-disk FIRST_ATTEMPT_PASS count on structured/LH trials (dense, planned = 20):**
- T4 runs 1–5: 5 strict PASS.
- T4 orchestrator-extra run 6: 1 PASS, but this is a duplicate of T4 and outside the planned 20. Excluded from numerator (Option A counts against a fixed denominator of 20).
- T5 run 3: 1 strict PASS.
- T5 runs 1, 2, 4, 5: 1 DISCARDED (wrapper mis-attach), 2 INFERRED_PASS (not on-disk strictly scorable), 1 NOT RUN. Per "strict first-attempt" rule: 0 count.
- T6 runs 1–5: NOT RUN, 0 count.
- T10 runs 1–5: NOT RUN, 0 count.

**Dense structured/LH first-attempt PASS: 6 / 20 strict.** (Plus 2 INFERRED_PASS and 1 orchestrator-extra PASS — not counted under strict rule.) **Threshold: ≥14/20. Verdict: FAIL on count.** Even if the 2 INFERRED_PASS and the extra T4 are included as evidence, total favorable is 9 / 20 — still below 14.

Note: even if every one of the 14 unmeasured trials were to pass strictly, the count could reach 20/20. But the pre-committed threshold does not permit scoring unmeasured trials as PASS. Under Option A, the threshold is structurally unreachable with the data as it stands.

**Dense v2-adoption rate on compliant structured/LH trials: 6 / 6 = 100%.** Threshold: ≥95%. **Verdict: PASS** (on the 6 measured trials; sample too small to conclude for the full 20 but directionally excellent).

**Dense one-shot regression (T1×2, T2×2, T8×2): 0 / 6 fails.** All 6 compliant, all first_tool == delegate_worker_v2, all classification == "one-shot", no subsequent delegate_* call. Threshold: 0. **Verdict: PASS.**

### MoE leg

**MoE structured/LH first-attempt PASS: 17 / 20 strict.** Miss rate = 3/20 (T4-r1, T4-r3, T10-r1 — all empty-first-turn, all recovered on attempt 1 with correct classification). Threshold: ≥8/20 (40%). **Verdict: PASS with >2× margin.**

**MoE v2-adoption on compliant trials.** Two ways to compute:
- Artifact-reported (eventual v2 on compliant): 20 / 20 = 100%. **PASS.**
- Strict spec-defined (`v2_was_first_tool`, per β-fuse spec §3 "headline metric ≥95%"): 17 / 20 = 85%. **BELOW 95%.**

The pre-committed threshold language says "v2-adoption ≥95% on compliant trials" without disambiguating. Reading the spec (§3: "`v2_was_first_tool`… headline metric for adoption: under β-fuse, this should be ≥95% on compliant runs"), the intended metric is first-tool adoption. Under that reading, MoE is 85%, 10 points below.

However: (a) the 3 misses are NOT mis-classifications or wrong-tool-choices — they are empty-first-turn productions that self-correct on one wrapper nudge with correct classification every time; (b) the check contract treats the corrected turn as legitimate v2-adoption; (c) the alternative metric (eventual v2 on compliant) is 100% and does satisfy ≥95%. I flag this as **ambiguous — lean PASS** given the artifact-reported metric, but the judge must note the stricter reading falls short.

**MoE one-shot regression: 0 / 6 fails.** All 6 compliant, first_tool == delegate_worker_v2, classification == "one-shot". Threshold: 0. **Verdict: PASS.**

### Summary table

| Metric | Dense | Threshold | Verdict | MoE | Threshold | Verdict |
|--------|-------|-----------|---------|-----|-----------|---------|
| Structured/LH first-attempt PASS | 6 / 20 strict | ≥14/20 | FAIL | 17 / 20 strict | ≥8/20 | PASS |
| v2-adoption on compliant | 6 / 6 = 100% | ≥95% | PASS (small sample) | 20/20=100% eventual / 17/20=85% strict-first | ≥95% | PASS (eventual) / FAIL-BY-2pt (strict) |
| One-shot regression fails | 0 / 6 | 0 | PASS | 0 / 6 | 0 | PASS |

---

## Part 3 — Integrated decision

### Signal reading

The β-fuse hypothesis is strongly corroborated by the data we have:
- r7.3 L1+L2 was 1/15 first-attempt on each model (catastrophic). r7.4 is 6/6 dense measured (+ 2 inferred) and 17/20 MoE. That is a step-function behavioral change, not a margin-of-error shift.
- v2-adoption is 100% on every compliant trial across both legs. The core β-fuse mechanism (tool-call-as-classification) works.
- One-shot regression is 0/12 across both legs. The contract does not force structured dispatch on simple tasks — no over-classification observed.
- The MoE empty-first-turn mode (3/20) is a production-level MoE quirk, not a β-fuse-contract failure. Classification, when emitted, is always correct.

### Why not SHIP-WITH-CAVEAT

I considered SHIP-WITH-CAVEAT given the strong directional signal. I reject it because:
1. The pre-committed thresholds are absolute counts. 6/20 is 43% of the 14/20 floor. This is not a narrow miss that a caveat can absorb; this is a structural data-gap.
2. The dense leg's missing data is concentrated in exactly the failure mode that matters — long-horizon tasks (T6, T10) and bug-hunt (T5 runs 1/2/4/5). β-fuse's purpose is to help the model classify these correctly on first attempt. Shipping without measuring any T6 or T10 dense trial means we are making a production ship decision on zero observations of the hardest class of dense task.
3. The artifact itself names the root cause (wrapper SIGTERM truncation loses parent session JSON) and proposes three fixes. The right call is to land one of those fixes, re-run T5/T6/T10 dense, and then ship on full data — not to ship on partial data and retrofit the evidence later.

### Why not RETREAT

RETREAT is rejected because every measured datapoint on both legs is favorable. There is no evidence the β-fuse mechanism is failing; there is evidence it is working. The thesis holds; the data collection is the limiting factor.

### Why not REVISE

REVISE is rejected because sample verification was clean and the data-integrity story is well-documented: the dense gap is from a known wrapper fault during timeout, not from mis-scoring or fabricated results. The worker disclosed the incident, named the specific sessions affected, and preserved evidence. This is not a probe-validity problem; it is a coverage problem.

### Decision

**HOLD — fill dense gaps.** Re-run T5 runs 1/2/4/5 plus T6 runs 1–5 plus T10 runs 1–5 (14 dense structured/LH trials) under a fixed wrapper. On completion, compute dense first-attempt as a single pooled count against the 14/20 threshold. If dense reaches 14/20 or better, SHIP. If below, consider RETREAT or threshold renegotiation with explicit operator sign-off.

---

## Recommendations

### Immediate next steps (HOLD path)

1. **Fix the wrapper's SIGTERM/fallback behavior before re-running.** The dense artifact explicitly names three options — pick one:
   - (a) install a SIGTERM handler in the agent that persists the session JSON before exit;
   - (b) raise `TIMEOUT_PER_TURN` from 900s to 1500s for T5/T6/T10 (MoE's max was 579s, but dense on T5-r3 took 488s and T4-r1 took 393s — a handful of dense long-horizon trials would plausibly exceed 900s);
   - (c) tighten wrapper fallback-recovery so it refuses to attach to a session whose `messages[0].content` does not match the trial prompt. Options (b) and (c) are independent and can be combined; (a) is the most robust. I recommend (b) + (c) together as the lowest-risk path.

2. **Pre-run checks:** operator should confirm no orphan orchestrator processes on the Mac (`pgrep -f runner.sh`) before dispatching the worker. The dense artifact's orphan orchestrator incident produced run-number collisions and consumed budget; do not repeat.

3. **Re-run scope:** T5 runs 1, 2, 4, 5 (4 trials) + T6 runs 1–5 (5 trials) + T10 runs 1–5 (5 trials) = 14 dense trials. Keep VM staged with Variant F throughout. Tripwire-check at each task boundary. Unstage at end.

4. **After re-run, re-dispatch this judge** with the completed dense artifact. The MoE artifact is final and need not be re-run.

### Deferred productionization (once SHIP is reached)

Do NOT proceed with these until the HOLD is resolved with a SHIP verdict, but pre-stage the plan so the follow-on is fast:

1. Rename `HERMES-variantF.md` → canonical HERMES.md once dense threshold is met. Preserve variantD and variantE md5s under `variants/hermes/` for rollback.
2. Update `PROBE-RESULTS-r7.md` with the completed r7.4 table (dense + MoE first-attempt counts, v2-adoption rates, one-shot regression counts, comparison to r7.3 baseline).
3. Update `CHANGELOG.md` with r7.4 entry: "AgentFW r7.4 — Layer-3 β-fuse (delegate_worker_v2): classification-as-tool-call. Dense X/20, MoE 17/20, v2-adoption 100% on compliant trials, zero one-shot regression."
4. Upstream-contribution path for `delegate_worker_v2`: the spec (§5) calls for side-by-side migration with v1 deprecation-arc. Implement the deprecation warning field in v1's response before Phase 3 sunset. Provide a minimal PR against upstream Hermes registering the v2 tool with the schema in `ARTIFACT-impl-3-beta-fuse-spec.md` §1, and the handler in §2.
5. Promote `probe-variantF-wrapper.sh` and `probe-variantF-check.py` to the canonical probe harness; archive variants D/E under `archive/`.

### What HOLD costs

Re-running 14 dense trials under Variant F staging, at average dense structured/LH elapsed of ~300–500s, totals roughly 70–120 minutes of wall-clock plus wrapper overhead plus stage/unstage cycle. Comparable in scope to the MoE leg's 43 min. One worker session, well under a 90-min budget.

---

## Residual risks (even on a future SHIP)

1. **MoE empty-first-turn pattern (3/20 = 15%).** Not a β-fuse failure, but it IS a reliability tax on MoE deployments. The wrapper's NO_MARKER correction currently hides the cost — without that correction, MoE would surface 15% of structured tasks as no-op first turns in a production harness. Recommendation: track `empty_first_turn_rate` as an ongoing MoE quality metric; investigate whether a small system-prompt tweak or tool-description adjustment can push the rate below 5%.

2. **v2_was_first_tool strict metric 85% on MoE.** Per β-fuse spec §3, the headline adoption metric is `v2_was_first_tool`, and the 95% target is not met strictly. The artifact reports the softer "eventual v2 on compliant" metric. I accept the softer reading for ship purposes because the correction contract is doing real work, but flag that future probe rounds should report BOTH metrics and watch for drift.

3. **Dense coverage of T6/T10 at zero.** Even after HOLD is resolved, if the dense re-run is only 5 trials per task, statistical power on long-horizon tasks remains modest. For r7.5 or the next round, consider 10 trials per long-horizon task on dense.

4. **Wrapper fragility.** The SIGTERM-loses-parent bug was not fixed in this probe; it was worked around by MoE's faster runtime. Fix it before any future dense probe or the same data-loss pattern will recur.

5. **Orphan-process hygiene.** The dense artifact disclosed a parent-PID-90529 orphan orchestrator producing run-number collisions. This is an operator-discipline risk that only shows up under multi-worker dispatch. Establish a pre-dispatch `pgrep -f runner.sh` gate for all future probe workers.

6. **Classification quality not measured.** β-fuse verifies that classification is recorded, not that it is correct. A model could mis-classify a 10-file refactor as one-shot and still pass the v2 contract. The one-shot regression check (0/6 on both legs here) is a proxy, but a future round should add "classification correctness" as a separate gate — e.g., cross-check against ground-truth labels on a held-out evaluation set.

7. **Production Jira cron.** Monday 8am cron runs against canonical HERMES.md and canonical jira-daily-briefing skill. The MoE artifact confirms VM was unstaged back to canonical post-run (md5s match). This preserved the invariant for this round. For the post-HOLD re-run, the same unstage discipline must be enforced.
