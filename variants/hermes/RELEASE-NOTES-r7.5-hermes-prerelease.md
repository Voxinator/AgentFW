# Hermes Variant — r7.5 Pre-Release

**Release tag:** `r7.5-hermes-prerelease`
**Date:** 2026-04-19
**Status:** PRE-RELEASE — not production-ready

> **Note (2026-04-21):** This is the main-branch copy of the r7.5 release notes, carrying a campaign-arc addendum at the bottom documenting the r7.6/7.7/7.8 HOLD campaigns and the r7.8 substrate-ceiling finding. The original release-notes file at the time of tag is archived at `variants/hermes/archive/r7.5-prerelease-2026-04-19/RELEASE-NOTES-r7.5-hermes-prerelease.md`. The `r7.5-hermes-prerelease` tag and its underlying commit (`001a1a9`) are immutable; this file is for GitHub release-description updating via `gh release edit`.

---

## Summary (TL;DR)

The β-fuse dispatch architecture is validated. The worker-quality ship gate is not.

On the MoE target (`gemma-4-26B-A4B-it-MLX-8bit`), r7.4's β-fuse (structural fusion of classification into a required tool-call argument) produced 17/20 strict first-attempt dispatches — an 11.5×–17× lift over the r7.3 pre-intervention baselines, with 100% `delegate_worker_v2` adoption on compliant trials. r7.5 added a turn-0 toolset restriction hook that narrowly forces the model to choose between `delegate_worker_v2` and `clarify` at turn zero under the β-fuse toolset composition. That hook worked as designed: 16/20 first-attempt dispatch (within r7.4's ±1 variance on the same task matrix), 0 tripwire mutations, 0 `tool_not_found` events, and the dispatch thesis held.

The worker-quality gate — a new measurement surface introduced in r7.5 — failed decisively. Pre-committed floor: ≥15/20 structured-and-long-horizon children pass a 5-criterion rubric (COMPLETION / CORRECTNESS / HONESTY / TURN_EFFICIENCY / NO_SIDE_EFFECTS). Observed: 3/20 PASS. Root causes identified and reproducible: `search_files` thrash on unknown cwd (7/20 trials), SIGTERM mid-turn truncation (8/20), pseudo-tool-call text emission (3/20), and fabricated completion claims (2/20 T10 trials). None of these are dispatch-layer failures — they are child-execution and child-tool-formatting problems orthogonal to β-fuse.

**Production readiness:** NOT YET. The operator's explicit criterion is worker quality ≥75%; the release ships as a milestone because the substantial progress — dispatch-layer design, the probe infrastructure, and the empirical demonstration that dispatch and worker-quality are independent axes — is worth capturing now. Worker-quality work is r7.6 scope.

**Operator decision still available:** the r7.4 SHIP-WITH-CAVEAT verdict for variantF β-fuse dispatch is not retroactively weakened by r7.5's worker-quality HOLD. Worker quality wasn't measured in r7.4 because the gate didn't exist. The operator may canonicalize variantF as a dispatch-layer improvement independently of r7.5's worker-quality hold. That is an operator decision, not a judge decision. See "Ship verdicts" below.

---

## What's in this release

### New documentation (pre-release artifacts)

- **`RELEASE-NOTES-r7.5-hermes-prerelease.md`** (this file) — authoritative release notes.
- **`variants/hermes/INSTALL.md`** — new authoritative install procedure (supersedes the frozen `IMPLEMENTATION.md`).
- **`variants/hermes/DEPENDENCIES.md`** — exact tested versions, hardware notes, what the variant requires from Hermes, known limitations caused by the current Hermes version.
- **`variants/hermes/DESIGN.md`** — refreshed to reflect variantF + turn-0 architecture (prior version described the r7 variantD state).
- **`variants/hermes/NEXT-STEPS.md`** — extended with r7.5 completion state + r7.6 agenda.

### New code / probe infrastructure (shipped previously, documented here)

- **`variants/hermes/HERMES-variantF.md`** (md5 `01c0e77bb2a6e753a8ea9063784a25e0`) — β-fuse harness prompt. Teaches `delegate_worker_v2` exclusively.
- **`variants/hermes/delegate_worker_v2.py`** (md5 `d31876fe987331a26c8640202334fd46`) — β-fuse dispatch tool with required `classification` + `justification` + conditional `goal` arguments.
- **`probe-variantF-{stage.sh,wrapper.sh,check.py}`** — r7.4 β-fuse probe infrastructure.
- **`probe-variantG-{stage.sh,wrapper.sh,check.py}`** — r7.5 turn-0 toolset restriction + Tier-1 SIGTERM content-match recovery + `ERROR:WRONG_SESSION` verdict.
- **`probe-omlx-health-check.sh`** — Mac-side oMLX health probe.

### Evidence trail (artifacts referenced below)

- `ARTIFACT-r7.4-ship-judge-verdict-v2.md` — r7.4 SHIP-WITH-CAVEAT verdict (authoritative).
- `ARTIFACT-r7.4-phase-d-moe-results.md`, `…-dense-results.md`, `…-dense-gapfill.md` — r7.4 probe data.
- `ARTIFACT-r7.4-sigterm-research.md` — parent-SIGTERM diagnosis + Tier-1/2/3 mitigation plan.
- `ARTIFACT-r7.5-A1-impl-notes.md`, `…-A2-judge-verdict.md` — r7.5 turn-0 hook implementation + ship judge.
- `ARTIFACT-r7.5-B1-impl-notes.md`, `…-B2-impl-notes.md` — r7.5 Tier-1/2 wrapper hardening.
- `ARTIFACT-r7.5-F2-probe-results.md` — r7.5 20-trial MoE probe.
- `ARTIFACT-r7.5-SHIP-judge-verdict.md` — r7.5 ship judge (authoritative HOLD-narrow verdict + sample verification).
- `ARTIFACT-r7.5-worker-quality-trial-{01..20}.md` — per-trial rubric scoring for the r7.5 worker-quality gate.

---

## Ship verdicts

| Layer | r7.4 verdict | r7.5 verdict | What moves forward |
|-------|--------------|--------------|--------------------|
| β-fuse dispatch (variantF) | SHIP-WITH-CAVEAT | Not retroactively weakened | Operator may canonicalize variantF independently of r7.5's worker-quality hold |
| Turn-0 toolset restriction + Tier-1/2 SIGTERM mitigations (variantG / β-fuse v2.1) | — | **HOLD-narrow** | Dispatch gate within ±1 of baseline (16/20 vs 17/20 floor); worker-quality gate failed decisively (3/20 vs 15/20) |
| Worker quality | — | HOLD (operator's r7.6 scope) | Child-session scaffolding, child-toolset restriction, anti-fabrication, format-enforcement per the r7.6 agenda below |

**Why HOLD-narrow and not RETREAT.** The r7.5 ship judge found:
- β-fuse dispatch thesis is INTACT. v2-adoption is 20/20 (100%); the 4 first-attempt misses recovered cleanly via the correction loop and exhibit the same `messages[1]` empty-turn signature observed in r7.4.
- The dispatch miss (16/20 vs 17/20) is one sample below threshold with an identical failure signature to r7.4. Poisson variance.
- Worker-quality failures (−12) happen on an orthogonal surface (child execution and child tool formatting on 26B MoE) that β-fuse was never designed to address.
- 7-trial fresh-context sample verification against raw session JSONs agreed 7/7 with the F.2 aggregate.

See `ARTIFACT-r7.5-SHIP-judge-verdict.md` §1–§6 for the full reasoning and residual-risk register.

---

## Install + requirements

See `variants/hermes/INSTALL.md` and `variants/hermes/DEPENDENCIES.md`.

Quick summary:
- Mac + Apple Silicon with 128 GB unified memory (tested); oMLX `0.3.6` serving on `localhost:8000`; Gemma MoE model loaded.
- Parallels VM with Ubuntu 24.04 + Hermes Agent `v0.8.0`; `10.211.55.2:8000` reaches oMLX.
- Clone repo; `./probe-variantF-stage.sh stage && ./probe-variantG-stage.sh stage`; swap `HERMES.md` to `HERMES-variantF.md`; run smoke trial.

Rollback is a single unstage invocation per layer plus `cp HERMES-canonical-backup.md HERMES.md` on the VM.

---

## Known limitations

These gate the production-ready status. Each is tracked as r7.6 scope.

- **Worker quality below floor.** 3/20 rubric-PASS vs 15/20 floor. Four failure modes:
  1. **`search_files` thrash (7/20).** Children search unknown cwd for hypothetical files, exhausting turn budget without reaching a synthesis turn.
  2. **SIGTERM mid-turn truncation (8/20).** Wrapper's 900s per-trial timeout kills child sessions mid-tool. Parent-side SIGTERM was Tier-1-mitigated in r7.5 (content-match recovery); child-side SIGTERM is the r7.6 mirror problem.
  3. **Malformed pseudo-tool-call text (3/20).** 26B MoE emits `call:X{args}<tool_call|>` in `content` rather than structured `tool_calls`. No actual write occurs; sometimes a full plan document gets trapped in the content field.
  4. **Fabricated completion claims (2/20 T10).** Summary claims "Created X" / "Generated Y" with zero `write_file` / `patch` / `terminal` calls in the transcript. Honesty failure, not a dispatch-contract failure.
- **Dispatch is 16/20 not 17/20 on r7.5 (vs r7.4 baseline).** Identical failure signature (empty `messages[1]`, recovery at `messages[3]`). Within-variance for MoE; not a regression caused by the r7.5 turn-0 hook.
- **Pre-existing slice error in the v2 handler.** Latent; doesn't block dispatch but may surface on specific tool-call shapes. Tracked for r7.6.
- **oMLX memory-pressure accumulation.** Sustained dense-model runs drift oMLX engine-pool state. Restart oMLX between multi-hour campaigns. `probe-omlx-health-check.sh` diagnoses.
- **Upstream Hermes SIGTERM handler (Tier 3).** Designed (`ARTIFACT-r7.4-sigterm-research.md`) but not applied. Tier-1 (wrapper content-match) is sufficient for the r7.5 probe but a Tier-3 fix would eliminate the class of problem at the root.
- **Measurement caveat on r7.1's 60%/80% numbers.** The original r7.1 headline dispatch rates were inflated by a wrapper that counted stdout `🔀 preparing delegate_worker…` markers as dispatches even when the parent session JSON was SIGTERM-truncated before persisting the call. The r7.2 strict on-disk re-tally (`ARTIFACT-drift-step-a-retally.md`) showed r7.1's true first-attempt dispatch was 0/5 strict. All r7.x numbers from r7.2 forward use strict on-disk criteria. Cross-version comparisons must use the strict metric.

---

## What's NEXT (r7.6 agenda)

Per `ARTIFACT-r7.5-SHIP-judge-verdict.md` Part 5:

1. **Child-session contract scaffolding** — a `HERMES-WORKER.md` analog injected into child sessions teaching honest-blocked return, no-fabrication-without-write discipline, and pre-budget-exhaustion summary turns. Addresses fabrication + turn discipline.
2. **Child-toolset restriction** — by default bind a reduced toolset for dispatched children (e.g. `file_readonly,terminal,todo,clarify,write_file,patch`) with `search_files` gated behind explicit escalation. Addresses search-thrash. Analogous to the r7.5 turn-0 hook.
3. **Turn-budget tuning for long-horizon** — raise child `--max-turns` from 20 to 30 for `classification=long-horizon`. Addresses T6/T10 budget exhaustion.
4. **Anti-fabrication post-trial guardrail** — judge-layer or wrapper-layer post-check: if the child summary claims file creation, verify at least one `write_file` / `patch` / `terminal` tool call with matching target appears in the transcript. Auto-HONESTY=FAIL if not.
5. **Pseudo-tool-call detection** — Hermes-layer response-schema enforcement: if `assistant.content` contains literal `<tool_call|>` or `call:<name>{`, surface as a parse error and retry with correction (same pattern as the r7.5 turn-0 NO_MARKER loop).
6. **Child-side SIGTERM research (Tier 3 Hermes handler)** — mirror the r7.4 parent-side investigation. The B3 Tier-3 upstream handler deferred from r7.5 becomes more attractive with the child-side SIGTERM evidence.

> **Post-tag update:** the r7.6 agenda above has been *worked through* and landed as a HOLD campaign; items 1-4 were attempted and scored. See the "Campaign Arc Addendum" section at the bottom of this file for the post-tag findings.

### Operator decision tree

The r7.5 ship judge explicitly flagged this:

**Option A — canonicalize variantF now, work on r7.6 worker-quality in parallel.** r7.4's SHIP-WITH-CAVEAT verdict for the dispatch layer remains valid. Worker quality is a separate, orthogonal axis. If your production use case (e.g. the Jira daily-briefing cron) does not depend on multi-level child dispatch — or depends only on the dispatch layer, not child execution quality — canonicalizing variantF now captures the dispatch-reliability improvement without blocking on r7.6. Rollback is a one-command unstage.

**Option B — hold canonical at `0780c232…` until r7.6 closes the worker-quality gate.** If your use case exercises child execution heavily, or if your operator policy is "both dispatch and worker quality must clear before canonical swap," then hold. r7.6 scope addresses the four measured failure modes.

This is an operator call. The judge does not override the operator's production criteria.

---

## Probe campaign arc (r7 → r7.5)

| Probe | Date | Intervention | Dense 1st-attempt dispatch | MoE 1st-attempt dispatch | Worker quality |
|-------|------|--------------|---------------------------|--------------------------|----------------|
| r7.1 (withdrawn) | 2026-04-17/18 | Variant E scaffolding + wrapper | Inflated 60% → 0/5 strict on-disk | — | not measured |
| r7.2 corrected baseline | 2026-04-18 | Variant E + fixed wrapper | 20% (1/5) | 0% (0/5) | not measured |
| r7.3 L1+L2 | 2026-04-18/19 | Toolset restriction + escape-hatch removal | 6.7% (1/15) | 6.7% (1/15) | not measured |
| r7.4 β-fuse (variantF) | 2026-04-19 | Required `delegate_worker_v2` tool | 77% (10/13 measured) | 85% (17/20) | not measured |
| r7.5 β-fuse v2.1 (variantG) | 2026-04-19 | + turn-0 toolset restriction + Tier-1 SIGTERM mitigation | n/a (not retested) | 80% (16/20) | 15% (3/20) vs 75% floor |

Lift vs r7.3 pre-intervention baseline: **11.5× dense (r7.4), 12.7×–17× MoE (r7.4 / r7.5)**. One-shot regression: 0/12 across the r7.4 legs — β-fuse does not force structured dispatch on trivial tasks.

---

## Architectural lessons

**Language-only remediation did not move the dispatch needle.** r7.3 stacked two layers (toolset restriction + escape-hatch removal from HERMES.md) and produced only 1/15 dispatch on each model — below even the r7.2 baseline on dense. More aggressive prompt language without a structural backstop pushed Gemma toward "be careful, orient first" behavior.

**Structural fusion produced the step function.** r7.4 β-fuse moves the classification from a text marker (which the model can satisfy without dispatching) to a required argument on the dispatch tool itself. You cannot satisfy the contract without calling the tool. Dispatch jumped 11.5× on dense and 12.7× on MoE. This is the central empirical finding: language teaches the model what you want; structure makes the behavior unavoidable.

**Dispatch reliability and worker quality are independent axes.** r7.4 gave us a good dispatch layer. r7.5's new worker-quality gate revealed that good dispatch is necessary but not sufficient for end-to-end task success. The same four root-cause failure modes would have existed under r7 through r7.4; r7.5 is simply the first probe that measured them. r7.6 needs to carry the Decompose-Parallelize-Verify-Iterate philosophy into the child sessions — they need their own scaffolding analogous to HERMES.md.

**Probe-fidelity work is load-bearing.** The r7.2 strict on-disk re-tally inverted the r7.1 cross-variant ordering. The r7.4 P1 investigation showed the r7.3 "terminal leak" was an analyzer artifact, not a gate bypass. The r7.5 Tier-1 SIGTERM content-match recovery eliminated a class of mis-attribution errors that would otherwise contaminate numbers. The evidence trail is only as good as the analyzer; each probe campaign has needed a round of analyzer hardening before the headline numbers settle. Future operators should budget this cost explicitly.

---

## Credits

Probe campaign and pre-release prep: operator (`voxinator@gmail.com`) + AgentFW harness-dispatched Claude sub-agents (Opus 4.7, 1M-context).

The variant design is built on the structural insights from the Jira-daily-briefing skill on the operator's Hermes install — the pattern of "narrow tool surface + worked format example + retry wrapper" generalized from a single-skill success into the harness design that this release captures.

---

## Campaign Arc Addendum (2026-04-21)

Since the r7.5 pre-release tag was cut, three follow-up campaigns (r7.6, r7.7, r7.8) attempted worker-quality lift via scaffold, structural, and generation-layer interventions. All three landed HOLD. The r7.8 ablation established a clear substrate-ceiling finding: **vanilla MoE performance is ~20% on this 4-task eval; every intervention tested (HWO scaffold, A1 child-toolset restriction, A2 write-before-claim gate, T1 loop detector) lands within sampling noise of that baseline at n=20.**

### Campaign-arc results

| Campaign | Arm | Config (additive) | PASS/20 | Rate |
|----------|-----|-------------------|---------|------|
| r7.6 | A | vanilla (β-fuse only) | 4/20 | 20% |
| r7.6 | B | + HERMES-WORKER.md scaffold | 8/17 non-LOST | 47% of non-LOST |
| r7.7 | G | + A1 child-toolset restriction (no `todo`) | 5/20 | 25% |
| r7.7 | F | + A1 + A2 + HWO | 7/20 | 35% |
| r7.8 | K | + T1 cross-turn loop detector | 2/20 | 10% |
| r7.8 | K' | vanilla control (ablation baseline) | 4/20 | 20% |

σ ≈ 2 at n=20, p≈0.25. Every non-baseline arm sits within 1-2σ of the vanilla baseline.

### Failure-layer attribution (from r7.7 S9 autopsy + r7.8-P1a)

Across the 28 r7.7 FAILs classified by layer: sampler 36%, parser 18%, prompt 18%, tool-call text-emission 18%, environment 14%, **honesty 0%**. **~2/3 of FAILs are generation-layer, not agentic-layer.** The tested agentic-layer interventions (HWO, A1, A2, T1) target a minority slice of the failure distribution.

Dispatch integrity remains perfect: **0 SCOPE breaches across 80+ trials.** β-fuse holds 100%.

### Pointers to full evidence

- `variants/hermes/PROBE-RESULTS-r7.md` §19-§23 — full campaign-arc record.
- `variants/hermes/CEILING-FINDING-r7.8.md` — standalone substrate-ceiling finding.
- `variants/hermes/archive/r7.6-campaign-2026-04-20/ARTIFACT-r7.6-MORNING-SUMMARY.md` — r7.6 HWO campaign summary.
- `variants/hermes/archive/r7.7-campaign-2026-04-20/ARTIFACT-r7.7-MORNING-SUMMARY.md` — r7.7 Path A campaign summary.
- `variants/hermes/archive/r7.7-campaign-2026-04-20/artifacts/ARTIFACT-r7.7-S9-ship-judge.md` — authoritative r7.7 ship-judge verdict + ablation autopsy.
- `variants/hermes/archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md` — r7.8 ablation + ceiling-finding synthesis.
- `variants/hermes/campaign-handoff/HANDOFF-post-r7.8.md` — r7.9 options (α/β/γ/δ) with procedures, budgets, success criteria.
- `variants/hermes/NEXT-STEPS.md` — roadmap summary pointing into the handoff.

### Post-tag drift on main (annotation, no new tag)

Per Option A of the 2026-04-21 doc audit, campaign-arc evidence is committed to main but the `r7.5-hermes-prerelease` tag remains immutable. Two tracked files drifted on main since the tag:

- **`variants/hermes/HERMES-variantF.md`** — +1 line. Anti-pattern #6 "Retry Re-Classification" added during r7.6 Fix 4 (wrapper correction framing fix). Reading-layer only. Behaviorally reversible.
- **`variants/hermes/delegate_worker_v2.py`** — +64 env-gated lines implementing A1 child-toolset restriction behind `HERMES_CHILD_TOOLSET_RESTRICT`. Behaviorally identical to tag with env var unset; opt-in for probe reproducibility. The r7.7 S9 judge verdict was HOLD — A1 did not win — so this is research infrastructure, not a canonical change.

Neither drift warrants a new tag; both are annotated here and captured in `variants/hermes/PROBE-RESULTS-r7.md` §20 (variantF drift) and §21 (delegate_worker_v2 drift).

### Ship-tag status

**The r7.5 pre-release tag remains the operator-facing milestone; this addendum documents campaign-arc findings post-tag.** No new tag has been issued for r7.6/7.7/7.8 — none earned a ship thesis. The next tag will be issued when a campaign clears the worker-quality gate or when a substrate/eval-design change (r7.9 α / γ) produces a new canonical baseline worth shipping. See `campaign-handoff/HANDOFF-post-r7.8.md` for the r7.9 decision framing.
