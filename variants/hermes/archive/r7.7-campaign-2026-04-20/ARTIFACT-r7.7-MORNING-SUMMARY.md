[TASK CLASS: long-horizon]
Justification: Aggregate of full r7.7 Path A campaign — Arm F + Arm G probes, 40 trials, 40 fresh-LLM judges, ship-judge verdict, and r7.8 handoff implications.

# MORNING SUMMARY — r7.7 Path A campaign

**Date:** 2026-04-20 (late evening; intended for 2026-04-21 morning review)
**Executed:** autonomously across the day per operator authorization
**VM state:** CANONICAL at exit
**Pre-release tag:** untouched
**Tripwires:** clean throughout

---

## TL;DR — HOLD verdict; A1+A2 missed the substrate

r7.7 Path A shipped two structural fixes (A1: child-toolset restriction removing `todo`; A2: write-before-claim runtime gate) on top of the r7.6 HWO scaffold. The full ablation campaign ran cleanly — but neither arm crossed the 75 % worker-quality floor.

| Arm | Config | PASS / 20 | vs r7.6 baseline |
|-----|--------|-----------|------------------|
| **Arm G** (A1 only) | A1 only, no scaffold, no A2 | **5 / 20 (25 %)** | +1 over Arm A (4/20) — **noise** |
| **Arm F** (A1 + A2 + HWO) | full stack | **7 / 20 (35 %)** | -1 from Arm B (8/20) — **noise** |

Both arms land in the noise band relative to r7.6 baselines. **Verdict (S9 ship judge, fresh context): HOLD.** No SHIP. No canonical swap.

The campaign's most important finding is not the verdict — it's the failure-mode autopsy:

> **~2/3 of FAILs are generation-layer pathologies, not agentic-layer.** Across 28 FAIL trials: zero HONESTY violations. Dominant patterns: `thought\n<channel|>` token leakage, `finish_reason=length` mid-turn truncation, degenerate planning text-loops, silent post-tool-result termination.

**A1 and A2 were targeting the wrong substrate.** The model isn't fabricating completions because it has access to `todo` — it's failing to *generate coherent text at all* on long-horizon tasks. Removing `todo` and gating fabrication claims doesn't move that needle.

---

## Per-task breakdown — the ablation tells a richer story than the aggregate

| Task   | r7.6 A | r7.6 B | r7.7 G (A1) | r7.7 F (A1+A2+HWO) | Δ Arm F vs Arm G | Interpretation |
|--------|--------|--------|-------------|--------------------|------------------|----------------|
| **T4** (structured, files-don't-exist) | 4/5 | 4/4 | **5/5** | 3/5 | **−2** | HWO **hurts** T4. Scaffold's "stop after 3 unproductive searches" causes premature termination → text-loops in the residual turns. |
| **T5** (structured bug-hunt) | 0/5 | 0/5 | 0/5 | 1/5 | +1 | Mode 2 thrash + Mode 4 wrong-cwd dominant. Neither arm engages the actual failure. |
| **T6** (long-horizon, plan + implement) | 0/5 | 2/4 (non-LOST) | **0/5** | **0/5** | 0 | **Wipeout in both arms.** Generation-layer thrash is unsolvable on this substrate. |
| **T10** (long-horizon, postgres migration) | 0/5 | 2/4 (non-LOST) | 0/5 | 3/5 | **+3** | HWO+A2 enables honest-blocked summaries; A2 gate caught real fabrication on run 5 (independently corroborated). |

**The uncomfortable shape:** the only place HWO+A2 helps is T10. The only place A1 alone helps is T4 (and HWO+A2 actively *hurts* it there). T6 is dead in both arms. T5 is dead in both arms.

---

## What r7.7 confirmed (the wins)

1. **A2 runtime gate works as designed.** Caught the T10-run5 fabrication; judge independently corroborated. The mechanism is sound — its *target* (fabrication-style failures) is just rare in this campaign.
2. **A1 child-toolset restriction works as designed.** Child sessions verifiably exclude `todo`; A1 prevented multiple near-tripwire-breach attempts (children tried to mkdir into `~/.hermes/hermes-agent/*`; toolset restriction blocked them).
3. **β-fuse dispatch holds 100 %.** Every parent in 40 trials called `delegate_worker_v2` correctly. The r7.4 dispatch ship still stands.
4. **Tripwire integrity perfect across 40 trials + multiple stage/unstage cycles.** No SCOPE breaches, no canonical drift.
5. **Path-aware `skill_manage` matching works** (S6-redo verified 10/10 precision, 10/10 recall on Arm-F-realistic corpus).
6. **VM canonicalization protocol is reliable** even under failure (initial S8 attempt failed mid-flight; clean recovery).

---

## What r7.7 cost us — and what it bought

**Cost:** ~12 hours of wall-clock (probing + judging + recovery from a failed initial S8 attempt). One detached-orchestration mishap that was caught and unwound cleanly.

**Bought:**
- Definitive answer that A1 alone is a no-op on this substrate.
- Definitive answer that A2's *mechanism* works but its *target distribution* doesn't dominate.
- Per-task ablation data that pinpoints generation-layer as the next intervention surface.
- Calibrated thresholds (P1-13 ≥9/10 precision, ≥8/10 recall on A2 gate) and infra (path-aware skill_manage, idempotent stage stack F→G→H→I→J-A1→J-A2) ready to reuse.
- Updated calibration of `OMLX_SWAP_MAX_GB` to 30 (was 5.5, demonstrably too aggressive).

---

## The r7.8 problem statement (for next campaign)

The S9 verdict is mechanical: HOLD. The interesting question is "what do we do next?" — and r7.7's data answers that more precisely than the aggregate suggests.

**Key insight from S9 ablation:** Path A's interventions assumed the dominant failure was *behavioral* (the model chooses to fabricate; the model chooses to claim completion). The data shows the dominant failure is *generative* (the model emits malformed tokens; the model truncates; the model loops within a single turn).

**r7.8 candidate intervention surfaces** (mechanically derived from S9 + I1):

1. **Generation-layer fixes**
   - Sampler tuning (top-p, temperature, repetition penalty) on the Gemma backend
   - Stop-token discipline (stop on `<channel|>` leak; stop on detected loop)
   - max_tokens-per-turn raise + better truncation handling
   - Channel-marker post-processor that strips polluted tokens before serialization

2. **Deeper structural restriction** (β-fuse one layer deeper)
   - Child gets only `delegate_task` + `clarify` until it has read at least one file (forces reconnaissance before action)
   - Restrict per-task-class child toolset (T6/T10 long-horizon get different defaults than T4/T5 structured)

3. **Per-task-class scaffolding**
   - Drop HWO for T4-class (it hurts there)
   - Keep HWO for T10-class (helps honest-blocking)
   - Try a different scaffold for T5/T6 (current one doesn't engage the failures)

4. **Environment / cwd scoping**
   - Mode 4 (out-of-context investigation) is ~5/28 FAILs. Pre-pass child cwd to delegate_worker_v2; have it set workdir before any tool call.

5. **Out-of-scope (per operator constraints):**
   - Stronger local model (Qwen3.5 ruled out, 122B doesn't run, Gemma-4 is best efficient)
   - Different model family for tool-use (operator confirmed)

---

## Status of the three things you asked me to track

| | Status | Notes |
|---|---|---|
| VM canonical at session end | ✅ | HERMES.md `0780c232a6cb52e13e432261f0d68ad9` MATCH; all 4 tripwires MATCH |
| Pre-release on GitHub | ✅ untouched | Tag `r7.5-hermes-prerelease` immutable; no pushes this session |
| Monday/weekday Jira cron safe | ✅ | Canonical SKILL.md and jira-briefing.sh unchanged across all 40 trials + many stage/unstage cycles |

---

## Files changed this campaign (all on main; nothing pushed)

**New on Mac (untracked):**
- `variants/hermes/write_before_claim_gate.py` (A2 detect-only gate module)
- `variants/hermes/test_delegate_worker_v2_a1.py` (A1 unit tests)
- `probe-variantJ-A1-stage.sh`, `probe-variantJ-A2-stage.sh` (stage scripts)
- `probe-variantJ-wrapper.sh` (env-forwarding wrapper, fixes variantI's drop of A1/A2 flags)
- `PROGRESS-r7.7.md` (campaign state file)
- ~70 artifacts: `ARTIFACT-r7.7-*` (planreview, S0-preflight, S7-smoke, batch trials, judge verdicts, S9 ship-judge, this summary)

**Modified on Mac (working tree only; differs from r7.5 tag):**
- `variants/hermes/delegate_worker_v2.py` — A1 patch (env-gated; behavior identical with `HERMES_CHILD_TOOLSET_RESTRICT` unset)
- `variants/hermes/HERMES-variantF.md` — Fix 4 retry amplifier (carried forward from r7.6)

**VM:** returned to canonical. All variant staging unstaged. No source patches.

---

## Recommended decisions

### r7.7 ship action

**Accept HOLD verdict. No canonical swap. No tag.** Path A code stays on Mac as research artifacts; can be staged again if r7.8 wants to combine with new interventions. Pre-release tag `r7.5-hermes-prerelease` remains the operator-facing milestone.

### r7.8 scope direction

Operator authorized r7.8 to be planned + executed autonomously overnight on the same hardware/model substrate. Planning phase will spawn many sub-agents to:
- Re-read the campaign-arc evidence
- Generate hypothesis trees for generation-layer fixes
- Score candidate interventions against r7.7 failure-mode counts
- Pick the 1-2 highest-EV candidates and design probes
- Run probes + judges
- Produce r7.8 morning-summary equivalent

### What stays untouched

- Pre-release tag (`r7.5-hermes-prerelease`) — operator-only
- Tripwire files (`HERMES.md`, `SKILL.md`, `jira-briefing.sh`, `useDashboard.ts`) — hard limit
- VM canonical state at every batch boundary
- Pre-commit secret scan before ANY hypothetical push

---

*End r7.7 campaign artifact. Operator reviews + approves r7.7 close + r7.8 direction. r7.8 runs autonomously through the night per operator's "many many agents" authorization.*

*Good night. The data is honest. The path forward is clearer than the verdict suggests.*
