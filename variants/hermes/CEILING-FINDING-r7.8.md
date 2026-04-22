# Substrate Ceiling Finding — r7.8 Ablation Data

**Date of finding:** 2026-04-21 (r7.8 ablation close)
**Status:** Load-bearing campaign-arc conclusion
**Scope:** Hermes variant of AgentFW running on Gemma-4-26B-A4B-it-MLX-8bit (MoE, 8-bit)
**Evaluation:** T4/T5/T6/T10 task set (4-task worker-quality matrix)

---

## Headline

**Vanilla Hermes-on-Gemma-4-MoE substrate scores ~20% (4/20) on the T4-T5-T6-T10 worker-quality eval. Across three campaigns (r7.6, r7.7, r7.8) and five distinct agentic-layer interventions, every arm lands within 1-2σ of that baseline at n=20.** The agentic layer is at ceiling on this eval; the remaining leverage is in substrate, generation-layer, or eval-design — not in prompt, toolset, or structural-dispatch interventions.

---

## The aggregate table

Every 20-trial arm tested across r7.6 / r7.7 / r7.8, per-task, strict on-disk scoring, fresh-LLM judged.

| Campaign | Arm | Config (additive) | T4 | T5 | T6 | T10 | Total PASS/20 | Rate |
|----------|-----|-------------------|----|----|----|-----|---------------|------|
| r7.6 | Arm A | vanilla (β-fuse dispatch only) | 4/5 | 0/5 | 0/5 | 0/5 | **4/20** | 20% |
| r7.6 | Arm B | + HERMES-WORKER.md (HWO) scaffold | 4/4 | 0/5 | 2/4 | 2/4 | **8/17 non-LOST** | 47% of non-LOST |
| r7.7 | Arm G | + A1 child-toolset restriction (no `todo`) | 5/5 | 0/5 | 0/5 | 0/5 | **5/20** | 25% |
| r7.7 | Arm F | + HWO + A1 + A2 write-before-claim gate | 3/5 | 1/5 | 0/5 | 3/5 | **7/20** | 35% |
| r7.8 | Arm K | + T1 cross-turn loop detector only | 2/5 | 0/5 | 0/5 | 0/5 | **2/20** | 10% |
| r7.8 | Arm K' | vanilla baseline control | 4/5 | 0/5 | 0/5 | 0/5 | **4/20** | 20% |

At n=20 with p≈0.25, σ≈2. The σ band around the 4/20 vanilla baseline is roughly 2-6/20. Every non-baseline arm sits within 1-2σ of the baseline.

---

## Per-task invariance — the shape is in the substrate, not the intervention

- **T4 (structured, files-don't-exist): ~80% regardless of arm.** The "concrete-blocked" behavior is intrinsic to the base model — it recognizes that the target files don't exist in the workspace and terminates cleanly. HWO scaffold reinforces this on Arm B; A1 reinforces it on Arm G; every other arm is within ±2 trials of 4/5.
- **T5 / T6 / T10: near-0% regardless of arm.** All failures are thrash, channel-marker pollution, mid-turn truncation, or fabrication — generation-layer pathologies that prompt-level / toolset-level / gate-level interventions don't touch.

**Drop T4 from the denominator** and every arm scores 0-3/15 on the hard tasks (T5+T6+T10). No tested intervention has moved that needle. The aggregate variance across arms is almost entirely explained by T4 noise plus occasional T10 rescues from HWO+A2.

This is the core evidence for the ceiling finding: the *shape* of the per-task distribution is the invariant. The interventions don't reshape it; they barely perturb it.

---

## Where the FAILs actually live — r7.8-P1a attribution

r7.8's P1a phase classified every FAIL from the r7.7 campaign (28 trials) by layer, to answer "if we fix the dominant failure layer, how much of the failure surface do we claim?"

| Layer | % of r7.7 FAILs | Dominant pathology |
|-------|-----------------|--------------------|
| Sampler | 36% | `finish_reason=length` mid-turn truncation; degenerate in-turn loops |
| Parser | 18% | `<channel\|>` / `<tool_call\|>` token leakage in assistant content |
| Prompt | 18% | Silent post-tool-result termination; empty follow-up turns |
| Tool-call | 18% | Malformed pseudo-tool-calls in content; wrong tool for intent |
| Environment | 14% | cwd misattribution; search-thrash on nonexistent paths |
| **Honesty** | **0%** | No fabrication among the 28 r7.7 FAILs (A2 caught the one T10 case and gated it) |

**~2/3 of FAILs (sampler + parser + prompt + tool-call text-emission ≈ 70-90% depending on how you count overlap) are generation-layer pathologies**, not agentic-layer. The tested interventions (HWO, A1, A2, T1) target agentic-layer behaviors (classification, toolset, honesty, semantic loop-detection). They address a minority slice of the failure distribution.

Dispatch integrity, by contrast, is perfect: **0 SCOPE breaches across 80+ trials**. β-fuse dispatch holds 100%. The r7.4/7.5 dispatch ship remains sound.

---

## Why this matters — the three implications

### 1. Agentic-layer interventions are at ceiling on this eval.

Three campaigns of prompt / toolset / structural-gate tuning have each produced results within 1-2σ of the vanilla baseline at n=20. The signal:noise ratio for agentic-layer work against a 20% baseline at n=20 is fundamentally weak. The next agentic-layer candidate would need to promise a large absolute lift (say +20pp to reach ~40%) to be distinguishable from noise at that sample size — and three campaigns say no such candidate has emerged from the obvious intervention space (scaffolding, toolset restriction, runtime gates, loop detection).

### 2. The real leverage is substrate + generation-layer + eval-design.

- **Substrate:** if vanilla caps at ~20% and interventions can't move it, the substrate itself may be the ceiling. r7.9 Option α (substrate upgrade to Gemma-4-31B dense) tests this directly.
- **Generation-layer:** per the P1a attribution, 70%+ of FAILs are at the generation layer. r7.9 Option β targets the correct location: pattern-similarity loop detector (Jaccard ≥0.9 replacing T1's byte-identical match); harmony `reasoning_parser` in oMLX `model_settings.json` (addresses channel-marker leakage server-side); pre-parser content scrubber at `run_agent.py:8633` (C1 moved upstream from `parse()` where it was unreachable).
- **Eval-design:** if the 4-task matrix is selecting for MoE-specific weaknesses (long-horizon fabrication, complex tool sequences, unknown-cwd search), the existing campaign value may have been benchmark-tuning all along. r7.9 Option γ proposes a new 5-8 task battery stratified across short-loop, data-transform, small-refactor, Q&A-with-citation, planning-only — to test whether the harness + existing interventions *generalize*.

### 3. β-fuse dispatch remains shipped and sound.

r7.4 and r7.5 established a dispatch-layer thesis that this ceiling finding does not weaken. Across all 80+ trials in r7.6/7.7/7.8, every parent called `delegate_worker_v2` correctly with a valid classification + justification + goal. The r7.5 pre-release tag (`r7.5-hermes-prerelease`, commit `001a1a9`) remains the operator-facing milestone. The ceiling is on worker-quality, not on dispatch.

---

## Measurement converging — the single strongest piece of evidence

r7.8 Arm K' (pure vanilla control, no HWO, no A1, no A2, no T1) hit **4/20 = 20%**. r7.6 Arm A (pure vanilla baseline) hit **4/20 = 20%**. Same task matrix. Same model. Same scoring rule. Same numeric result.

This is not coincidence — it is measurement converging. At n=20 with p≈0.25, two independent draws from the vanilla distribution are expected to land ±2 of each other, and exact matches are plausible. The Arm K' measurement was explicitly designed as an ablation control to bracket the substrate baseline under the exact hardware + eval conditions of the r7.8 campaign. It did. The baseline is ~20%.

Given that vanilla is ~20% and every intervention lands 2-8/20, the honest reading of three campaigns is: **the tested agentic-layer surface does not carry enough leverage to move this measurement.** Further work on the same surface would not be expected to, either.

---

## Cross-references

- `variants/hermes/PROBE-RESULTS-r7.md` §19-§23 — campaign-arc record (r7.5 pre-release, r7.6 HWO, r7.7 A1+A2, r7.8 T1 + ceiling finding).
- `variants/hermes/archive/r7.6-campaign-2026-04-20/ARTIFACT-r7.6-MORNING-SUMMARY.md` — r7.6 HWO scaffold campaign headline (HOLD, 8/20 vs 15/20 floor).
- `variants/hermes/archive/r7.7-campaign-2026-04-20/ARTIFACT-r7.7-MORNING-SUMMARY.md` — r7.7 Path A campaign headline (HOLD, A1+A2 in noise band).
- `variants/hermes/archive/r7.7-campaign-2026-04-20/artifacts/ARTIFACT-r7.7-S9-ship-judge.md` — authoritative r7.7 ship-judge verdict; introduces the "~2/3 of FAILs are generation-layer" framing that r7.8 confirmed.
- `variants/hermes/archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md` — r7.8 ablation + ceiling-finding synthesis.
- `variants/hermes/campaign-handoff/HANDOFF-post-r7.8.md` — decision framing for r7.9 (options α/β/γ/δ with exact procedures, budgets, success criteria).
- `variants/hermes/campaign-handoff/MORNING-SUMMARY-latest.md` — symlink to r7.8 morning summary.
- `variants/hermes/NEXT-STEPS.md` — roadmap pointer.

---

## What this is not

- **Not a claim that Hermes + Gemma is bad.** β-fuse dispatch works at 100%. One-shot tasks pass cleanly. The T4 "concrete-blocked" behavior is textbook. The substrate is competent at well-scoped, short-horizon tasks; it struggles at the long-horizon + search-heavy + plan-and-implement shape of T5/T6/T10.
- **Not a final word on the eval.** r7.9 Option γ exists precisely because one honest reading of this finding is "the 4-task eval may be selecting for MoE-specific weaknesses; the harness may generalize elsewhere." Broader eval would confirm or refute.
- **Not a recommendation to stop the project.** Three exhausting directions remain (α / β / γ) and a combined recommendation (δ). Each has a specific success criterion and a bounded budget. The campaign's honest answer narrowed the search, it didn't close it.
- **Not a retroactive invalidation of r7.4 / r7.5.** The dispatch-layer thesis those campaigns established is independent of worker-quality. The r7.5 pre-release tag remains the operator-facing milestone.

---

*The agentic layer is at ceiling on the T4/T5/T6/T10 eval against vanilla Hermes-on-Gemma-4-MoE. The leverage is elsewhere. The campaign-arc's hardest-won contribution is narrowing the search space for r7.9.*
