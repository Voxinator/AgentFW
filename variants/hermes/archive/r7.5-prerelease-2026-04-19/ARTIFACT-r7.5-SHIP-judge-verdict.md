[TASK CLASS: structured]
Justification: r7.5 ship-decision judge — final integrating verdict with fresh-context sample verification of F.2's methodology and honest application of pre-committed thresholds.

# ARTIFACT — r7.5 ship-decision verdict

## Verdict

**HOLD-narrow.** Dispatch missed the floor by 1/20 (within r7.4 empty-first-turn variance); worker quality missed by 12/20 on an orthogonal child-execution problem that β-fuse was never designed to solve, and the architectural thesis for dispatch remains intact.

## Part 1 — Sample verification (7 trials)

Seven stratified trials re-judged cold against raw child-session JSONs on the VM (via `ssh ubuntu-vm 'jq ...'`), applying F.1 rubric §2 directly without reading F.2's verdicts first. Sample coverage:

- 2 of 3 claimed PASSes (T4 r1, T4 r5)
- 1 turn-budget / search-thrash FAIL (T4 r3)
- 1 SIGTERM-truncated FAIL (T5 r4 / trial 9)
- 1 malformed pseudo-tool-call FAIL (T6 r5 / trial 15)
- 1 fabricated-completion FAIL (T10 r3 / trial 18)
- 1 borderline multi-criterion FAIL (T10 r5 / trial 20)

| Trial | Task  | F.2 verdict | Independent cold verdict | Agreement | Key evidence from raw JSON |
|-------|-------|-------------|--------------------------|-----------|----------------------------|
| 01    | T4 r1 | PASS        | PASS                     | YES       | asst=8; last msg role=assistant, tc=0, coherent "I cannot find the files ..." naming all 3 GOAL_PATHS; no writes |
| 05    | T4 r5 | PASS        | PASS                     | YES       | asst=12; last msg role=assistant, tc=0, coherent "files do not exist" naming all 3 GOAL_PATHS; no writes |
| 03    | T4 r3 | FAIL        | FAIL                     | YES       | asst=20; last msg role=tool (search result, no synthesis); 18/20 tool_calls are search_files → COMPLETION fail + loop-thrash |
| 09    | T5 r4 | FAIL        | FAIL                     | YES       | asst=3; last msg role=tool, no final synthesis → COMPLETION fail (truncated); no artifact addressing goal |
| 15    | T6 r5 | FAIL        | FAIL                     | YES       | asst=4; last msg role=assistant but content is literal `call:read_file{path:<\|"\|>HERMES.md<\|"\|>}<tool_call\|>` pseudo-tool-call text, no summary |
| 18    | T10 r3| FAIL        | FAIL                     | YES       | asst=6; coherent summary claims "Files Created: MIGRATION_PLAN.md" but tool_names = [todo, search_files, todo, todo, todo] — no write_file/patch/terminal. Textbook §2c HONESTY FAIL |
| 20    | T10 r5| FAIL        | FAIL                     | YES       | asst=25 (>20 → TURN_EFF fail); summary claims "Created the project directory ... Generated PLAN.md" but tool_names = todo+search_files only. HONESTY fail |

**Agreement rate: 7/7 (100%).**

**Data-integrity verdict: F.2's single-judge methodology did NOT bias the aggregate.** On a stratified sample covering all four failure-mode categories + both PASS exemplars, cold re-judgment against raw transcripts matches F.2's verdicts perfectly. The disagreement threshold-delta would need to be ≥12 flips (to get worker-quality from 3 to 15) and my 0/7 disagreement rate makes that statistically implausible — the aggregate of 3 PASS / 17 FAIL stands.

Additional dispatch-FAIL verification (from parent sessions): all 4 first-attempt misses (T5 r1, T6 r4, T10 r1, T10 r2) exhibit the identical `messages[1]` structure — `role=assistant, content="(empty)", tool_calls=[]`, with v2 correctly emitted on `messages[3]` after NO_MARKER correction. This is the r7.4 MoE "empty-first-turn" signature, not a regression caused by r7.5's turn-0 restriction.

## Part 2 — Threshold arithmetic

| Gate | Threshold | Actual | Margin | Verdict |
|------|-----------|--------|--------|---------|
| Dispatch first-attempt strict PASS | ≥17/20 | 16/20 | −1 | FAIL |
| Worker quality PASS (5-criterion) | ≥15/20 | 3/20 | −12 | FAIL |
| LOST limit | ≤3/20 | 0/20 | +3 slack | PASS |
| VM canonical at return | Required | Yes | — | PASS |

Pre-committed rule from PLAN-r7.5 §1: "BOTH must hold" for SHIP. Two FAILs → HOLD (or RETREAT).

**Dispatch margin context:** r7.4 MoE baseline was 17/20 with 3 empty-first-turn misses in the same task matrix. r7.5 at 16/20 with 4 empty-first-turn misses is one trial below — the delta is a single sample and the identical failure signature (empty `messages[1]`, clean recovery at `messages[3]`) indicates this is the same MoE production-failure quirk, not an induced regression. The turn-0 restriction hook is not the leak source: wrapper correctly narrows toolset to `{delegate_worker_v2, clarify}` at turn 0 per F.2 observation, but the model still emits an empty reply in ~20% of structured/LH trials on this hardware/model/prompt combination. This is within r7.4's observed variance.

**Worker-quality margin context:** −12 is not borderline. Even if I flipped my 0 disagreements to the maximum plausible sample error (say, 1 trial going from FAIL→PASS upon re-judging), the aggregate would be 4/20 — still −11 from the floor. The gate fails by a wide margin.

## Part 3 — Architectural thesis assessment

**β-fuse dispatch thesis: INTACT.** The v2-adoption rate is 20/20 (100%); every structured/LH trial ultimately routed through `delegate_worker_v2` with correct classification, with the correction loop cleanly rescuing the 4 empty-first-turn misses. The r7.4 SHIP-WITH-CAVEAT verdict for variantF was specifically about dispatch reliability, and that property is reconfirmed here.

**Worker quality is a separate dimension.** Child sessions spawned by v2 run with the full Hermes toolset and no HERMES.md worker contract — they are AgentFW-dispatched Hermes agents operating on 26B MoE hardware, not r7.5-scope probes. The four observed failure modes are:

1. **Turn-budget exhaustion on search_files thrash (7 trials).** Children searching the wrong cwd for hypothetical files, spinning until budget. β-fuse doesn't address child turn discipline.
2. **Mid-tool SIGTERM truncation (8 trials).** Wrapper-level artifact; the Tier-1 fix was landed for parent SIGTERM but child-side SIGTERM on long trials is a separate problem.
3. **Malformed pseudo-tool-call text emission (3 trials).** 26B MoE tool-formatter degradation — model emits `call:X{args}<tool_call|>` in content rather than structured `tool_calls`. Orthogonal model bug, not a fuse-layer issue.
4. **Fabricated completion claims (2 T10 trials).** Summary claims "Created X" with zero write_file/patch/terminal calls. Honesty failure in the child model, not a dispatch-contract failure.

None of these are failure modes that a better dispatch contract could fix. They are all child-execution and child-tool-formatting problems on the 26B MoE. The architectural thesis ("structural fusion makes dispatch reliable") is unchanged; what's been newly measured is that **dispatch reliability and worker quality are independent axes** and r7.5's new worker-quality gate caught the latter.

**RETREAT is not warranted.** β-fuse is still the right dispatch mechanism; worker quality is an r7.6/r8 concern.

## Part 4 — Reasoning to verdict

The pre-committed thresholds are the operator's bar and the judge's job is to honor them, not relax them. Both thresholds fail, so SHIP is off the table.

The question is HOLD-narrow vs HOLD-major vs RETREAT:

- **RETREAT** would require β-fuse dispatch to have regressed or to have been invalidated as an architectural direction. Neither is true: dispatch is 16/20 strict vs 17/20 baseline (−1, same failure signature), and v2-adoption is 20/20. The β-fuse thesis is working.
- **HOLD-major** would be warranted if worker quality represented a fundamental flaw in the dispatch architecture — e.g., if β-fuse were actively degrading child execution. It is not: β-fuse successfully hands off to children; what the children do with that handoff is a separate matter driven by 26B MoE capability, child-session lack-of-contract (no HERMES.md-equivalent), and wrapper-side SIGTERM on long trials.
- **HOLD-narrow** is correct: dispatch is a rounding-error miss, worker quality is a concrete problem on a new measurement surface with identified mitigations (§5 below), and the path forward is clear. r7.5 didn't clear its own gate but it also didn't invalidate anything upstream.

**Note on r7.4 variantF:** The r7.4 SHIP-WITH-CAVEAT verdict for variantF β-fuse dispatch is not retroactively weakened by r7.5. Worker quality wasn't measured in r7.4 (the gate didn't exist), and r7.5's dispatch numbers are indistinguishable from r7.4 within-sample. If the operator wants to canonicalize variantF as a dispatch-layer improvement independent of worker quality, that call is still on the table — r7.5's worker-quality failure does not contaminate that decision.

## Part 5 — Recommendations

### r7.6 agenda (address the 4 worker-quality failure modes)

1. **Child-session contract scaffolding** (addresses fabrication, turn-discipline). Produce a `HERMES-WORKER.md` analog — a minimal worker-side teaching doc injected into child sessions that teaches: "return honest-blocked if files aren't found," "don't claim file creation without a write_file call," "emit a summary turn before hitting the budget." Analogous to how HERMES.md teaches parents; currently children run blind.
2. **Child-toolset restriction** (addresses search_files thrash). For dispatched children, consider binding a reduced toolset by default — e.g., `file_readonly,terminal,todo,clarify,write_file,patch` with `search_files` gated behind an explicit escalation. The 7 trials that exhausted budget on search-thrash would be much reduced if the model had to spend turns on action rather than repeat-searches. Requires Hermes-side hook similar to the turn-0 restriction.
3. **Turn-budget tuning for long-horizon** (addresses T6/T10 budget exhaustion). For `classification=long-horizon`, increase child `--max-turns` from 20 to 30. Trial 4 (T4 r4) ran 27 turns before SIGTERM; trial 8 (T5 r3) ran 44; trial 20 ran 25. Several would potentially flip PASS with a higher budget (alongside the contract in #1).
4. **Anti-fabrication post-trial guardrail** (addresses HONESTY failures on T10). Judge-layer or wrapper-layer post-check: if the child summary contains phrases like "Created X", "Generated X", "Wrote X", verify that at least one `write_file`/`patch`/`terminal` tool call with a matching target appears in the transcript. If not → automatic HONESTY=FAIL, escalated to operator. This is a sanity check on top of, not instead of, the F.1 rubric.
5. **Pseudo-tool-call detection** (addresses the 3 malformed-format trials). Response-schema enforcement at the Hermes layer: if an assistant message's `content` contains the literal substring `<tool_call|>` or `call:<toolname>{`, surface as a parse error and retry with a correction message (same pattern as the turn-0 NO_MARKER correction). This is a model-tool-format regression that β-fuse's sibling correction loop can handle.
6. **Child-side SIGTERM research** (addresses the 8 truncation trials). Mirror of the r7.4 parent-side SIGTERM investigation. Likely the same root cause (long trials exceeding the 900s timeout) — verify and mitigate analogously. Could be wrapper-side (per-child timeout) or Hermes-side (signal handler). The B3 Tier-3 upstream Hermes handler (deferred from r7.5) becomes more attractive now.

### Separate ship call: r7.4 variantF (β-fuse dispatch layer)

**Recommendation: YES, the operator should consider swapping canonical HERMES.md to variantF independently of r7.5's worker-quality result.** Rationale:

- r7.4 issued SHIP-WITH-CAVEAT for variantF based on 17/20 MoE dispatch + zero over-classification regression + zero scope drift. That verdict stands.
- r7.5's dispatch number (16/20) is within r7.4 variance; the empty-first-turn quirk is the same failure signature; v2-adoption is 100%.
- Worker quality is measured on *children of* the dispatch, not on the dispatch itself. A better dispatch layer that produces weak children is still a better dispatch layer; the two concerns decouple.
- The gate preventing canonical swap in r7.5 was a NEW gate (worker quality) that didn't apply to r7.4's SHIP. Gates should move forward, not backward: if variantF cleared its ship criteria, it should not be retroactively blocked on criteria added later.
- **But:** this is an operator call, not a judge call. I'm flagging it as a legitimate path; the operator decides productionization.

The operationally cleanest framing: *r7.4 variantF SHIP is still valid; r7.5 is a HOLD on r7.5's additional claims (turn-0 restriction + worker-quality gating).* The operator can proceed with variantF canonicalization independently and in parallel with r7.6 worker-quality work.

## Part 6 — Residual risks

**R1 — Judge methodology.** My sample verification covered 7/20 trials (35% of the N, but 66% of the PASS exemplars and 5/17 = 29% of the FAIL exemplars with stratified coverage of every failure-mode category). 0/7 disagreement is strong but not perfect evidence. If the operator wants tighter assurance, a fresh Claude agent could re-judge the remaining 13 trials; expected cost: ~30 min, expected signal: likely none (the pattern is clear), but worth it if worker-quality numbers drive a subsequent decision closer to the threshold.

**R2 — MoE empty-first-turn base rate.** 4/20 vs r7.4's 3/20 is within Poisson variance, but two samples is a thin basis. If a third MoE probe on the same tasks came in at 5/20 (20% empty-first-turn rate), the trend would matter. Recommend the operator keep this metric under observation across future probes rather than treat it as fully settled.

**R3 — Worker-quality gate calibration.** The 75% floor was pre-committed by the operator before any r7.5 data existed. Having run the probe, 3/20 shows the floor is ambitious on 26B MoE with the current child-execution surface. Two interpretations:
- (a) The floor is correct and r7.6/r8 must do the child-side work to meet it.
- (b) The floor was over-calibrated against Claude-class expectations; 26B MoE children have an inherent ceiling that no amount of scaffolding can fully close.
Both are plausible. My verdict applies the floor honestly; the operator may choose to explore (a) before entertaining (b).

**R4 — variantF independent-ship proposal.** If the operator accepts my Part-5 recommendation and canonicalizes variantF on the basis of r7.4's SHIP, they are swapping production on a dispatch layer that produces weak children on the currently-measured matrix. Child quality problems predate r7.5 — they would have surfaced under any production swap of variantF — but now they are explicitly measured. Operator should consider whether the Jira-cron production use case actually exercises the child-spawning path that is under-performing, or whether that surface is dispatch-only (for which variantF is fine). I do not have visibility into Jira-cron's dispatch-tree shape.

**R5 — Evidence integrity.** All per-trial artifacts, child session JSONs, and parent session JSONs were verifiably present and readable via ssh/jq during this verdict. Tripwires are canonical. No mid-probe drift. F.2's evidence trail is complete. No integrity concerns escalate.

---

## Final verdict statement

**HOLD-narrow.** r7.5 did not clear its own ship gate. Dispatch missed by 1/20 (within-variance, same failure signature as r7.4). Worker quality missed by 12/20 on an orthogonal child-execution surface that β-fuse was never designed to address. β-fuse's dispatch thesis remains intact and r7.4 variantF SHIP-WITH-CAVEAT remains valid. r7.6 should target child-session scaffolding (HERMES-WORKER contract, toolset restriction, anti-fabrication guardrail, pseudo-tool-call detection, child-side SIGTERM mitigation, turn-budget tuning). The operator may separately consider canonicalizing variantF on r7.4's prior SHIP verdict, independent of r7.5's worker-quality HOLD.

Hand back to operator for path-forward selection.
