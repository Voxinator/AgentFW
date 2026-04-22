---
type: S9 ship judge verdict
date: 2026-04-20
campaign: r7.7 Path A
judge: S9 (fresh-context)
---
# S9 ship judge — r7.7 Path A

## Method note (fresh context)

I read each of the 40 per-trial judge artifacts directly and parsed `WORKER_QUALITY` from the machine-parseable verdict block. I read PLAN §9.6 thresholds directly. I deliberately did not read the PROGRESS-r7.7 §"Arm F verdict vs plan thresholds" or any synthesis artifact, so this verdict is independent of main-session interpretation.

## Raw data

### Arm F verdicts (20 files)

| Trial | Verdict | Dominant failure mode |
|-------|---------|-----------------------|
| T4-run1 | FAIL | Pseudo-tool-call text loop (50K-char rumination, no synthesis); COMPLETION+CORRECTNESS+TURN_EFF all FAIL |
| T4-run2 | PASS | Clean concrete-blocked summary naming three missing GOAL_PATHS |
| T4-run3 | PASS | Clean concrete-blocked summary; parent-session evaluated per fallback |
| T4-run4 | FAIL | Halted-mid-plan: ended on stream-of-consciousness self-correction, no summary |
| T4-run5 | PASS | Clean concrete-blocked summary |
| T5-run1 | FAIL | Silent-mid-plan termination; finish_reason=length truncations + `<channel\|>` artifacts |
| T5-run2 | FAIL | Terminated-while-planning (forward-looking PLAN block as terminal turn) |
| T5-run3 | PASS | Clean concrete-blocked summary citing zero-result search |
| T5-run4 | FAIL | Wrong-directory thrash; no path arg on search_files; final turn = planning |
| T5-run5 | FAIL | Spinning-on-planning, mid-parenthetical fragment after continue-prompt |
| T6-run1 | FAIL | Runaway repetition loop on PLAN block; truncation + degenerate continuation |
| T6-run2 | FAIL | Silent termination — every assistant turn empty / `thought\n<channel\|>` fragments |
| T6-run3 | FAIL | Truncated mid-exploration; `<channel\|>` markers; never reached write/plan phase |
| T6-run4 | FAIL | Halted-before-action: 12 discovery calls then voluntary stop in plan-draft mode |
| T6-run5 | FAIL | Single search then `[]<tool_call\|>` junk fragment as terminal content |
| T10-run1 | PASS | Clean concrete-blocked summary identifying missing write_file/mkdir tools |
| T10-run2 | PASS | Clean concrete-blocked summary with actionable parent-ask |
| T10-run3 | PASS | Clean concrete-blocked summary; child misused read_file as workaround but was honest |
| T10-run4 | FAIL | Stream-of-consciousness "I have execute_code" plan, no summary or block |
| T10-run5 | FAIL | No final assistant message; two terminal-rejected attempts then session end |

### Arm G verdicts (20 files)

| Trial | Verdict | Dominant failure mode |
|-------|---------|-----------------------|
| T4-run1 | PASS | Clean concrete-blocked summary |
| T4-run2 | PASS | Clean concrete-blocked summary; identified workspace as Python-based |
| T4-run3 | PASS | Clean concrete-blocked summary naming all three goal files |
| T4-run4 | PASS | Concrete-blocked summary after multi-truncation recovery |
| T4-run5 | PASS | Clean concrete-blocked summary |
| T5-run1 | FAIL | Truncated mid-action; `thought\n<channel\|>` fragment, no synthesis; TURN_EFF FAIL |
| T5-run2 | FAIL | Search-thrash on dashboard pattern; budget exhaustion (42>20 turns); TURN_EFF FAIL |
| T5-run3 | FAIL | TURN_EFFICIENCY FAIL despite COMPLETION/CORRECTNESS PASS |
| T5-run4 | FAIL | TURN_EFFICIENCY FAIL despite COMPLETION/CORRECTNESS PASS |
| T5-run5 | FAIL | Truncation mid-exploration; no synthesis after one GOAL_PATH read |
| T6-run1 | FAIL | Exploratory-loop-no-synthesis; A1-only has no runtime gate to interrupt |
| T6-run2 | FAIL | All 14 assistant turns empty / channel-token fragments; max-turns exhaustion |
| T6-run3 | FAIL | 21 assistant turns of channel-fragment content; mkdir attempt rejected |
| T6-run4 | FAIL | Schema-search thrash + truncation before synthesis |
| T6-run5 | FAIL | Silent mid-run termination during discovery |
| T10-run1 | FAIL | shell_execute hallucinated tool retried; no concrete-blocked summary |
| T10-run2 | FAIL | shell_execute hallucinated tool retried twice; session ended |
| T10-run3 | FAIL | Truncated mid-cycle (last msg = tool result); no synthesis; TURN_EFF FAIL |
| T10-run4 | FAIL | Truncation; no synthesis |
| T10-run5 | FAIL | Degenerate "I'll try write_file / I'll try execute_command" loop after continue-prompt |

## Tallies

| Arm | T4 | T5 | T6 | T10 | Total PASS/20 | LOST |
|-----|----|----|----|-----|---------------|------|
| Arm F (HWO + A1 + A2) | 3/5 | 1/5 | 0/5 | 3/5 | **7/20** (35%) | 0 |
| Arm G (A1 only) | 5/5 | 0/5 | 0/5 | 0/5 | **5/20** (25%) | 0 |

(LOST=0 in both arms — every trial produced an evaluable child session and a definite verdict. The "non-LOST denominator" SHIP rule reduces to absolute count.)

## Threshold evaluation (plan §9.6 pre-committed, applied mechanically)

- **SHIP ≥15/20 absolute Arm F PASS:** **NOT MET** (7/20, short by 8)
- **Alternative narrow ship** (T4 ≥4/5 AND T5+T6+T10 ≥11/15): **NOT MET** (T4=3/5 below 4/5; T5+T6+T10=4/15 well below 11/15)
- **HOLD-CLOSE 13-14/20** (≥+5 over Arm B=8): **NOT MET** (7/20 < 13)
- **HOLD ≤+3 over Arm B** (i.e., Arm F in [9, 11]/20): **NOT MET** (7/20 is BELOW Arm B baseline by 1)
- **HOLD-with-noise-note 6-8/20** (P1-18 noise-band addition; the plan's "Arm B=8 has 95% CI ~[4,13] at n=20; band is indistinguishable from baseline"): **MET** (Arm F=7/20)
- **RETREAT ≤5/20 AND T4 regression below scaffold-known-good 4/5:** **NOT MET** (Arm F=7 fails the ≤5 prong even though T4=3/5 alone would meet the regression prong; both conditions required)

**Determination per pre-committed thresholds:** Arm F lands inside the 6-8/20 noise band. Per plan language this is "no measurable effect; indistinguishable from r7.6 Arm B baseline at n=20" rather than HOLD or RETREAT.

## A1 isolation (Arm G vs r7.6 Arm A = 4/20)

Arm G total = **5/20**, vs r7.6 Arm A baseline (no scaffold) = 4/20. **A1-only lift = +1 absolute.** This is well within sampling noise at n=20 (Arm A 95% CI per the plan ≈ [1, 9]). On the A1-isolation question — does removing `todo` and similar substrate alone improve worker quality — the data says **no measurable effect**.

## A2+HWO marginal (Arm F vs Arm G)

Total delta: **Arm F − Arm G = 7 − 5 = +2** (within noise).

Per-task:
- **T4:** Arm F=3/5 vs Arm G=5/5 → **Arm G beats Arm F by 2** on the easiest task. This is a notable inversion: the additional HWO+A2 layers appear to *hurt* T4 worker quality (or, more honestly, are within trial noise but trending negative).
- **T5:** Arm F=1/5 vs Arm G=0/5 → +1 (within noise)
- **T6:** Arm F=0/5 vs Arm G=0/5 → 0 (both arms are total wipeouts on this task)
- **T10:** Arm F=3/5 vs Arm G=0/5 → **+3 in Arm F's favor.** This is the only directional signal in the ablation: HWO+A2 produces concrete-blocked summaries on T10 where A1-only produces hallucinated-tool retries and degenerate loops. The 3 T10 Arm F PASSes are all clean blocked-with-reason summaries naming missing write tools; the 5 Arm G T10 trials all FAIL on truncation, hallucinated `shell_execute`, or silent termination.

## Failure-mode pattern (cross-arm observation)

The dominant FAIL mode in both arms is not fabrication — it is **silent termination, truncation mid-action, or text-loops with `thought\n<channel\|>` channel-token leakage**. Across 28 FAILs (13 Arm F + 15 Arm G), 0 trials show a fabricated-completion claim that breached HONESTY (every FAIL retains HONESTY=PASS, often vacuously). Worker-quality failure on this MoE model is currently a *generation-layer pathology* (channel token formatting, length-truncation mid-turn, degenerate planning loops), not a dispatch-layer or honesty-layer pathology. A1 (todo removal) and A2 (runtime gate) target the wrong substrate for ~2/3 of observed failures.

## VERDICT

**HOLD (noise-band; document as "no measurable effect; indistinguishable from r7.6 Arm B baseline at n=20")**

Rationale: Arm F = 7/20 lands inside the plan's pre-committed 6-8/20 noise-band, one trial below the r7.6 Arm B baseline of 8/20. Per the plan's own language this band is statistically indistinguishable from baseline at n=20, so it is neither a SHIP, a HOLD-CLOSE, a clean HOLD lift, nor a RETREAT. Path A's combined HWO+A1+A2 stack produced no measurable improvement over the r7.6 HWO-only scaffold; the ablation reveals A1-only is also indistinguishable from no-scaffold (5/20 vs 4/20). The only directional signal is A2+HWO's +3 lift on T10 over A1-only, attributable to A2 (or HWO) producing clean concrete-blocked summaries where A1-only produces degenerate loops. The dominant failure mode across both arms is generation-layer truncation/channel-token leakage, which neither A1 nor A2 was designed to address.

## Recommended operator actions

1. **Do not ship r7.7 as a worker-quality release.** SHIP threshold not met by a wide margin (7/20 vs 15/20 floor); narrow-ship T4 fallback also not met (T4=3/5 below 4/5). Hand back HOLD verdict.
2. **β-fuse dispatch layer remains shippable as r7.5 already established** — the campaign was not regressing dispatch, and Arm F shows no SCOPE/tripwire breaches across 20 trials (every trial has SCOPE=PASS, TRIPWIRE_DRIFT=NO). Path A added zero protective regression on dispatch integrity.
3. **Preserve A2's `a2_gate_outcome` infrastructure** even though A2 did not move the needle here — it is reusable telemetry for future campaigns (per plan §18 argument 3).
4. **Consider whether r7.7 changes should be reverted, kept as no-op overhead, or kept on the strength of T10 alone.** T10's +3 Arm F over Arm G is the only positive signal and is small. The data does not justify shipping the combined stack as a worker-quality improvement, but T10's clean blocked-summary behavior under HWO+A2 is the one piece of evidence worth preserving in r7.8 scoping.
5. **Run a documented HOLD post-mortem** capturing the noise-band determination explicitly so that future campaigns do not re-litigate this n=20 indistinguishability claim.

## r7.8 scope implications (mechanical, from the ablation)

- **A1 (todo removal) — drop from r7.8 critical path.** Arm G = 5/20 vs r7.6 Arm A = 4/20 is +1 and indistinguishable from noise. A1 alone is not load-bearing. Keep the change because it has no downside, but do not invest more design effort in A1 variants.
- **A2 (runtime fabrication gate) — keep, but reframe.** A2 did not produce a global lift, but it produced the only positive directional signal (T10: +3 Arm F over Arm G). The mechanism appears to be that A2 forces the child to emit a concrete-blocked summary when it cannot produce writes, which converts silent FAILs into PASSes specifically on long-horizon write-required tasks. Worth preserving with the understanding that its scope is narrower than projected.
- **HWO scaffolding — at its prompt-level ceiling.** The r7.6 Arm B → r7.7 Arm F arc shows further prompt scaffolding is not buying additional lift on this 26B MoE model. Plan §9.7's prediction (and the r7.6 morning summary's interpretation) that prompt-level guardrails plateau is confirmed.
- **Generation-layer pathology is the real blocker.** The dominant failure mode across both arms is `thought\n<channel\|>` token leakage, finish_reason=length truncation mid-turn, degenerate planning text-loops, and silent post-tool-result termination. None of A1, A2, or HWO targets this substrate. r7.8 scope should pivot to one of:
  - **(a)** Sampler/decoding fix: enforce stop-on-channel-marker, raise min-tokens-after-tool-result floor, or post-process truncations.
  - **(b)** Toolset further restricted (the plan §9.7 idea: only `delegate, clarify, read_file` until first write attempt — β-fuse one level deeper) to constrain the planning loop substrate.
  - **(c)** Stronger local model (the r7.6 morning summary's option (c)). The 26B MoE may simply be at its ceiling on this flywheel.
- **T6 is a structural wipeout (0/5 in BOTH arms).** Long-horizon write-required tasks with phased deliverables under restricted toolsets are unsolvable on the current substrate. r7.8 scope should explicitly carve T6 out of the worker-quality success criterion until generation-layer or toolset-layer changes land.
- **T4 regression in Arm F vs Arm G needs an explanation in r7.8 planning.** HWO+A2 producing 3/5 where A1-only produces 5/5 is small-n but counter-directional. Hypothesis to test in r7.8: HWO/A2 may be inducing additional planning-text generation that triggers the same truncation pathology that hurts T5/T6.

**Bottom line for the operator's S10 authorization:** HOLD. Path A produced no measurable worker-quality lift over r7.6 Arm B; the ablation cleanly shows A1 isolated is also a no-op; the one positive signal (A2+HWO on T10) is too narrow to justify a worker-quality SHIP claim against the pre-committed 75% floor. The campaign nonetheless delivered the value §18 promised: r7.8 scope is now empirically grounded rather than speculative.
