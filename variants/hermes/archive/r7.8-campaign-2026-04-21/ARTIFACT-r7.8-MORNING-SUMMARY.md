[TASK CLASS: long-horizon]
Justification: Full r7.8 overnight autonomous campaign — research phase, vet phase (3 candidates), 40-trial ablation matrix, 40 fresh-LLM judges, ship-judge verdict, r7.9 handoff implications.

# MORNING SUMMARY — r7.8 overnight autonomous campaign

**Date:** 2026-04-21 (operator asleep throughout; intended for wake review)
**VM state at exit:** CANONICAL
**Pre-release tag:** untouched
**Tripwires:** clean throughout

---

## TL;DR — **HOLD. Major surfaced finding: r7.6/r7.7/r7.8 interventions all land in noise band of pure baseline.**

r7.8 tested one intervention (**T1 — cross-turn loop detector** in Hermes's generation loop) against an ablation baseline. Both ran 20-trial matrices.

| Arm | Config | T4 | T5 | T6 | T10 | **Total** |
|-----|--------|----|----|----|-----|-----------|
| r7.6 Arm A (baseline reference) | none | 4/5 | 0/5 | 0/5 | 0/5 | **4/20 (20%)** |
| r7.6 Arm B | HWO scaffold | 4/4 | 0/5 | 2/4 | 2/4 | 8/17 |
| r7.7 Arm F | HWO + A1 + A2 | 3/5 | 1/5 | 0/5 | 3/5 | 7/20 (35%) |
| r7.7 Arm G | A1 only | 5/5 | 0/5 | 0/5 | 0/5 | 5/20 (25%) |
| **r7.8 Arm K** | **T1 only** | **2/5** | 0/5 | 0/5 | 0/5 | **2/20 (10%)** |
| **r7.8 Arm K'** | **vanilla baseline** | **4/5** | 0/5 | 0/5 | 0/5 | **4/20 (20%)** |

Arm K (T1) actually underperformed the control by 2 trials on T4 (the scaffold-known-good task). Arm K' (baseline) exactly matched r7.6 Arm A — confirming the vanilla Hermes substrate is ~20% on the T4-T5-T6-T10 test set.

**Ship-judge-equivalent verdict: HOLD.** No r7.8 intervention crosses the 60% interesting-enough threshold. All four prior-campaign interventions (HWO, A1, A2, T1) land within sampling noise of the pure vanilla baseline at n=20.

This is a campaign-redirecting result.

---

## Campaign execution summary

Autonomous phases (all completed):
1. **P1 (research) — 4 parallel workers** on failure-mode classification, Gemma parser, sampler, stop-token/truncation
2. **P2 (synthesis)** — ranked 3 candidates: C1 (parser scrubber), S1 (sampler tune), T1 (loop detector); designed vet plan
3. **P3 (vet)** — 3 × 5-trial small-sample vets with md5-pin + rollback
4. **P4 (probe matrix)** — 20 trials × 2 arms = 40 trials across 8 batches (no worker-detachment failures this time)
5. **P5 (brief builder)** — 40 per-trial judge briefs constructed
6. **P6 (judge matrix)** — 40 fresh-LLM judges in 8 waves of 5
7. **P7 (this summary)**

Total wall-clock: ~10 hours (within overnight budget).

---

## Vet outcomes — two rejections + one pass that didn't scale

### C1 — Gemma parser universal channel-marker scrubber: **REJECT**
- Unit tests 13/13 PASS — scrubber logic is sound in isolation
- But **the parser gate at run_agent.py:8633 bypasses `parse()` for pure channel pollution**; C1 lived inside `parse()` and was unreachable for the dominant failure mode
- 126 channel markers observed in 5-trial output (threshold was 0)
- **Implication:** C1 as designed is wrong; a *pre-parser* content post-processor in run_agent.py would be the correct placement. Not implemented this night.

### S1 — Conservative sampler tune: **REJECT**
- Patch applied cleanly via hot-reload of `/Users/briantaylor/.omlx/model_settings.json`
- But **`repetition_penalty=1.08` hits stable JSON scaffold tokens, not semantic repetition in tool-call arguments** — 3/5 trials had ≥5 consecutive identical tool_calls (T10-r1 had 36!)
- Median 36 turns (threshold ≤15)
- **P1c research doc was wrong about the admin-reload endpoint** — correct path is `POST /admin/api/reload` via session cookie from `POST /admin/api/login`, not Bearer. Documented for future.
- **Side finding**: wrapper `check.py` (dispatch-compliance gate) reported PASS on all 5 S1 trials despite 3 having severe degenerate loops. **check.py cannot be trusted as worker-quality gate.**

### T1 — Cross-turn loop detector: **PASS (in vet)** → scaled poorly
- Vet 5/5: T10-r1 exercised the pathology (6 consecutive identical todos), T1 fired WARN at 5 + TERMINATE at 6 exactly as spec'd
- But at n=20 (Arm K): T1 fired WARN 6× (all on T10), 0 TERMINATEs, overall PASS rate 2/20
- **Vet was non-representative** — only 1 of 5 vet trials exercised the Mode D pathology, and the other 4 passed via the vanilla substrate's natural T4/T5 clean-blocked behavior
- **T1's exact-match limitation is the killer**: 6+ Arm K FAILs were pattern-varied search thrash that evaded byte-identical detection

---

## Key campaign-redirecting findings

### 1. The vanilla substrate is 20%

Arm K' (F+G+H + nothing) hit **4/20 exactly matching r7.6 Arm A (no-scaffold baseline 4/20)**. This is not coincidence; it's measurement converging. The vanilla Hermes-on-Gemma-4-MoE substrate scores ~20% on the T4-T5-T6-T10 test set regardless of (most) interventions.

### 2. All tested interventions land in the ~4-8/20 noise band

Across 3 campaigns + 5 non-baseline arms, scores: 7/20 (F), 5/20 (G), 2/20 (K), 8/17 (B re-computed with LOST handling), 4/20 (K'). **σ ≈ 2 at n=20** for a p~0.25 rate — every observed arm is within 1-2σ of the baseline.

### 3. Per-task shape is the invariant, not the intervention

- **T4 (structured, files-don't-exist): ~80% regardless of arm.** The "concrete-blocked" behavior is intrinsic to the base model.
- **T5/T6/T10: near-0% regardless of arm.** All failures are thrash/channel/truncation/fabrication — generation-layer pathologies that prompt/toolset/gate interventions don't touch.

**If you drop T4 from the denominator**, every arm scores ~0-3/15 on the "hard" tasks (T5+T6+T10). No intervention has moved that needle.

### 4. T1 is mechanistically correct but scoped too narrowly

T1 fires correctly on byte-identical consecutive tool_calls (6 WARNs across 20 trials, all on T10's `todo`-spam pattern). But **the dominant thrash pattern is semantic repetition (different search queries for the same conceptual target)** which T1 can't see. A pattern-similarity version (e.g., Jaccard similarity on tool args ≥0.9 → treat as equivalent) would catch ~6 additional FAILs at the cost of implementation complexity.

### 5. T1 may hurt T4 performance

Arm K T4: 2/5; Arm K' T4: 4/5; r7.6 Arm A T4: 4/5. **Injecting T1's WARN system message mid-conversation may be confusing the model on tasks where it would naturally terminate cleanly.** Small-n caveat (σ≈1 on T4-binomial), but the direction is suggestive.

### 6. Infrastructure wins

- Hot-reload oMLX mechanism verified for sampler tuning (useful for r7.9)
- md5-pin + rollback pattern works cleanly across 3 vet attempts
- Batched 5-trial workers eliminated r7.7's detached-orchestration failure mode
- Child sessions persisted correctly throughout; no r7.7-style "missing children" scan issues
- VM canonical at every batch boundary

---

## What r7.8 actually confirmed (the tiny-wins column)

1. **Hermes sends ZERO sampler params to oMLX** on the main generation path — all behavior is `/Users/briantaylor/.omlx/model_settings.json` defaults. Critical config-vs-code insight.
2. **`repetition_penalty` is disabled (1.0) in current Gemma-4 MoE settings** — that's structurally why Mode D loops occur. A properly-targeted repetition-penalty mechanism would help, but the 1.08 setting tested was too mild + hits wrong tokens.
3. **T1 proves loop-detection at the conversation layer works** — future r7.9 iteration with pattern similarity would likely catch more.
4. **Parser gate at run_agent.py:8633 is the correct pre-parser insertion point for any content post-processor** — C1's failure taught this.
5. **oMLX admin API**: `POST /admin/api/login` for session cookie + `POST /admin/api/reload` for hot-reload. P1c doc had this wrong.

---

## r7.9 scope implications (the serious recommendations)

Given the campaign's redirecting conclusion ("the substrate is 20%"), r7.9 should **stop grinding on the same test set with minor prompt/tool variations** and instead:

### Option α — Substrate upgrade
Operator mentioned a **>60% result on MoE would motivate 31B-dense trials against John's conversation threshold**. Since no r7.6/r7.7/r7.8 intervention has cleared ~40%, the base substrate may be the ceiling. r7.9 could test:
- **Gemma-4-31B-it-4bit (dense)** — operator confirmed hardware compatibility
- Operator-endorsed only if operator authorizes (dense has oMLX orphaned-session concerns; needs pre-probe restart discipline)

### Option β — Generation-layer, done right
Target the actual failure modes, not shadow gates:
- **Pattern-similarity loop detector** (T1.1 — Jaccard similarity ≥0.9 on tool args → treat as repetition). Directly addresses 6+ FAILs T1 missed.
- **harmony reasoning_parser** (flagged in P1c side note) — may root-cause channel leakage by having oMLX parse Gemma's reasoning tokens correctly at the model-server layer. Never vetted.
- **Pre-parser content scrubber** in run_agent.py:8633 (C1 moved upstream) — ~30 lines, fixes Mode 3 (channel pollution, 5/28 FAILs).
- **Per-tool-call `max_tokens` raise + explicit EOS handling** — may fix mid-turn truncation.

### Option γ — Acknowledge the ceiling
Operator could formally accept that **Hermes-on-Gemma-4-MoE caps around 20-35% on this evaluation**, document the campaign findings, and either (a) change evaluation (broader task types that don't select for long-horizon fabrication/thrash), or (b) change substrate (dense or cloud inference backup for hard tasks).

### Option δ — Test generalization NOT on this eval
The north-star was "general-purpose harness that runs on any project type." **None of the r7.6/r7.7/r7.8 campaigns measured generalization** — all were T4/T5/T6/T10. r7.9 could run a **new eval** (e.g., 3-5 new tasks chosen to stress different harness dimensions) and see if ANY of the existing interventions (HWO, A1, A2, T1) actually generalize, or if they were benchmark-tuning all along.

---

## Artifacts produced this session

**New this campaign (all on Mac; untracked):**
- Research: `ARTIFACT-r7.8-P1{a,b,c,d}-*.md` — failure modes, parser, sampler, stop-tokens
- Synthesis: `ARTIFACT-r7.8-P2-synthesis.md`
- Vets: `ARTIFACT-r7.8-P3{a,b,c}-{C1,S1,T1}-vet.md`
- Probe batches: `ARTIFACT-r7.8-{K,KP}-B{1,2,3,4}-trials.md` (8 files)
- Judge briefs: `ARTIFACT-r7.8-P5-judge-briefs-built.md` + 40 briefs in `/tmp/r7.8-judge-briefs/`
- Judge verdicts: `ARTIFACT-r7.8-judge-{ArmK,ArmKP}-T<id>-run<n>.md` (40 files)
- This summary: `ARTIFACT-r7.8-MORNING-SUMMARY.md`

**VM state:** canonical. All .probe-r7.8*orig backups removed. Run_agent.py restored to baseline md5 `94ad8712678df5e96b9f407446edf249`. HERMES.md + SKILL.md + jira-briefing.sh + useDashboard.ts all canonical.

---

## Status of the three things you asked me to track

| | Status | Notes |
|---|---|---|
| VM canonical at session end | ✅ | HERMES.md `0780c232…` MATCH; all 4 tripwires MATCH |
| Pre-release on GitHub | ✅ untouched | Tag `r7.5-hermes-prerelease` immutable; no pushes |
| Weekday Jira cron safe | ✅ | SKILL.md + jira-briefing.sh canonical throughout 40+ trials |

---

## Honest self-assessment

- **Vet-first discipline caught 2 of 3 candidate interventions before they burned a 20-trial matrix** (C1 + S1 both rejected). That's the vet framework working.
- **T1 passed vet but failed to scale** — because n=5 was unrepresentative for an intervention whose effect size only manifests on a specific sub-population of trials (Mode D pathology). For future campaigns, **vet sample should stratify by target failure mode**, not by task alone.
- **The 10-hour overnight budget was used on a HOLD result.** Operator got the honest answer + the actionable redirection (β, γ, δ above), but the substrate-is-the-ceiling finding would have been discoverable with just Arm K' alone (4/20 matches baseline).
- **Campaign-direction credit**: r7.7 ship-judge's "2/3 of failures are generation-layer, not agentic-layer" was RIGHT, and r7.8 confirmed it the hard way. The agentic-layer interventions genuinely don't have the leverage.

*The substrate is the ceiling on this test set. The path forward is either substrate upgrade (Option α), correctly-targeted generation-layer interventions (Option β), or a new evaluation that actually measures generalization (Option δ).*

*Good morning. VM is clean. The answer this campaign delivered is uncomfortable but clarifying.*
