# Hermes-flavored AgentFW — Next Steps

**Last updated:** 2026-04-21 (post-r7.8)
**Purpose:** Session-handoff doc. A fresh agent or human picking up this work cold should be able to act on this file + `DESIGN.md` + `INSTALL.md` + `DEPENDENCIES.md` + `PROBE-RESULTS-r7.md` + `CEILING-FINDING-r7.8.md` + the full handoff at `campaign-handoff/HANDOFF-post-r7.8.md`.

---

## State at handoff (2026-04-21, post-r7.8)

The `r7.5-hermes-prerelease` GitHub tag (commit `001a1a9`) remains the operator-facing milestone. Three follow-up campaigns after r7.5 — **r7.6**, **r7.7**, **r7.8** — all landed HOLD on worker quality. See `PROBE-RESULTS-r7.md` §19-§23 for the full campaign-arc record.

**The load-bearing finding:** r7.8's Arm K' (pure vanilla Hermes-on-Gemma-4-MoE control) scored **4/20**, exactly matching r7.6 Arm A's baseline of 4/20. Across 3 campaigns and 5 non-baseline arms (HWO 8/17 non-LOST; A1 5/20; A1+A2+HWO 7/20; T1 2/20; vanilla 4/20), **every intervention lands within 1-2σ of the vanilla baseline at n=20.** The agentic-layer is at ceiling on this evaluation. See `CEILING-FINDING-r7.8.md` for the standalone writeup.

**Campaign summary (condensed):**

| Campaign | Arm | Config | PASS/20 | Verdict |
|----------|-----|--------|---------|---------|
| r7.6 A | vanilla (β-fuse only) | — | 4/20 | baseline |
| r7.6 B | + HWO scaffold | HERMES-WORKER.md | 8/17 non-LOST | HOLD |
| r7.7 G | + A1 | child-toolset restriction | 5/20 | HOLD (noise) |
| r7.7 F | + A1 + A2 + HWO | write-before-claim gate | 7/20 | HOLD (noise) |
| r7.8 K | + T1 | cross-turn loop detector | 2/20 | HOLD |
| r7.8 K' | vanilla control | — | 4/20 | ceiling confirmation |

**VM state at handoff:** CANONICAL. HERMES.md md5 `0780c232a6cb52e13e432261f0d68ad9`. All 4 tripwires MATCH (`HERMES.md`, `SKILL.md`, `jira-briefing.sh`, `useDashboard.ts`). β-fuse dispatch holds 100% across all 80+ trials — the r7.4/7.5 dispatch ship remains sound. No tripwire mutations across any r7.6/7.7/7.8 probe run.

**Tracked-file drift since r7.5 tag:**
- `variants/hermes/HERMES-variantF.md` — +1 line (anti-pattern #6 "Retry Re-Classification", landed in r7.6 Fix 4).
- `variants/hermes/delegate_worker_v2.py` — +64 env-gated lines (A1 child-toolset restriction behind `HERMES_CHILD_TOOLSET_RESTRICT`; behaviorally identical with env var unset).

Neither warrants a new tag. The tag's copies are immutable at ref; only main drifted. Both are annotated in the r7.5 release-notes campaign-arc addendum at `variants/hermes/RELEASE-NOTES-r7.5-hermes-prerelease.md`.

---

## Source of truth for r7.9 planning

The authoritative post-r7.8 decision doc is **`campaign-handoff/HANDOFF-post-r7.8.md`**. Any fresh session picking up r7.9 work should read that file top-to-bottom before dispatching anything. It contains:

- Full campaign-arc evidence (§2)
- Hardware + substrate constraints (§3)
- Four r7.9 directions with exact procedures, budgets, success criteria, and risks (§4)
- Hard constraints — things that must not drift (§5)
- Required reading order for the fresh session (§6)
- Open methodology questions learned from r7.8 (§7)
- Known traps and carried-forward infrastructure notes (§8)
- VM + pre-release state at exit (§9)
- First-5-minutes checklist (§10)

This file (NEXT-STEPS) is a roadmap pointer; the handoff is the content.

---

## r7.9 options (one paragraph each — see handoff for full procedure)

### Option α — Substrate upgrade to Gemma-4-31B-dense

Maybe the ceiling is the Gemma-4 MoE variant, not Hermes's agentic layer. Three campaigns of agentic-layer tuning have not moved the needle on T5/T6/T10. If the substrate itself caps at ~20%, substrate upgrade is the load-bearing move. Operator-confirmed hardware-compatible (`gemma-4-31B-it-4bit`, 4-bit dense). Requires pre-probe oMLX restart discipline (orphaned-session accumulation under sustained dense load). Budget: one overnight for 5-trial vet; if vet ≥60%, second overnight for 20-per-task matrix. See `HANDOFF-post-r7.8.md` §4 Option α for the exact procedure.

### Option β — Generation-layer, correctly targeted

The three tested agentic interventions (HWO, A1+A2, T1) missed the actual substrate. r7.8-P1a's layer attribution: 36% of FAILs are sampler, 18% parser, 18% prompt-thrash. Properly-targeted generation-layer patches could hit — but only if placed correctly (C1 failed because it was inside `parse()`; the real gate is upstream at `run_agent.py:8633`). Three concrete candidates from r7.8 research: pattern-similarity loop detector (T1.1 — Jaccard ≥0.9 replacing T1's byte-identical match), harmony `reasoning_parser` in oMLX `model_settings.json`, pre-parser content scrubber at `run_agent.py:8633` (C1 moved upstream). Budget: one overnight per candidate (~10-12h); candidates 1+2 bundle cleanly as Arm L. See `HANDOFF-post-r7.8.md` §4 Option β.

### Option γ — Broader eval

The 4-task eval (T4/T5/T6/T10) may be selecting for Gemma-4-MoE's specific weaknesses. The north-star claim "general-purpose harness that runs on any project type" has not been tested — all three campaigns benchmark on the same 4 tasks. If the existing interventions (HWO, A1, A2, T1) were benchmark-tuning all along, a broader eval would reveal that. Design a new 5-8 task battery stratified across short-loop, data-transform, small-refactor, Q&A-with-citation, planning-only dimensions; re-run vanilla + HWO across all tasks × 5 trials. Budget: ~1.5 days (design + encode + overnight run). See `HANDOFF-post-r7.8.md` §4 Option γ.

### Option δ — Combined (operator lean)

Operator's r7.8 morning-summary lean: **α + γ in parallel**, with β deferred pending α/γ results. Rationale: α tells us whether substrate is the ceiling (one overnight, low-risk); γ tells us whether existing campaign value was real or benchmark-tuned (~1.5 days). If α hits 60%+ dense, the next arc is substrate-first + re-verify existing interventions on dense. If γ surfaces that HWO generalizes well, even a HOLD verdict on MoE becomes a meaningful shipped asset. If both come back flat, β is the last honest swing. Ordering: α first (smaller scope, faster answer). See `HANDOFF-post-r7.8.md` §4 Option δ.

**Not-a-fourth-option (explicit):** more agentic-layer prompt tuning on MoE with the same 4-task eval. Three campaigns of evidence say this is the wrong place to spend a fourth overnight.

---

## Hard constraints (carry forward from handoff §5)

- **Pre-release tag `r7.5-hermes-prerelease` is immutable.** Operator-only. Never force-push, never delete, never re-tag.
- **Tripwire md5s must not drift mid-campaign:** HERMES.md `0780c232a6cb52e13e432261f0d68ad9`; SKILL.md `fb1a5a5208a6cf2fcb8252aac10397eb`; jira-briefing.sh `a1dce6e989527686124d0860830627c9`; useDashboard.ts `5503ee1c2ef7d635a020eea275e41239`. Every probe wrapper verifies these pre- and post-trial.
- **VM must be canonical at session end.** All `.probe-*-orig` staging artifacts removed; all variant changes unstaged; `run_agent.py` md5 returns to baseline.
- **No pushes to `origin/main` without operator authorization.**
- **No secret values in tracked files.** `OMLX_API_KEY` stays in `/tmp/r7.7-env.sh` (owner-only 600).
- **The harness is the product.** Every intervention carries a one-line "why this generalizes beyond T4/T5/T6/T10" justification. If it can only be argued to help one task, it fails the design bar.
- **Jira cron weekday path must stay safe.** `SKILL.md` + `jira-briefing.sh` on canonical md5s for the duration of any campaign — Monday's cron run is operator-production.

---

## Methodology rules learned the hard way (from r7.8 handoff §7)

- **Vet sample must stratify by failure mode, not task.** r7.8 T1 passed 5/5 vet but Mode D was exercised in exactly 1 of 5 vet trials; the 20-trial matrix revealed the intervention landed 2/20. New rule: every vet includes ≥2 trials per targeted failure mode.
- **`check.py` is not a worker-quality gate.** It measures dispatch integrity only. All ship gates must use fresh-LLM judges on the deep session JSON.
- **Per-arm randomization for ablation integrity.** If oMLX health drifts monotonically across a long session (paging, orphaned sessions), sequential arms bias the comparison. Interleave batches.
- **Noise-band explicit per plan.** Pre-commit the verdict band before trials run, so verdicts are mechanical not interpretive.
- **Publication vs ship threshold.** Operator framing: 60% = "interesting enough to tell John"; 75% = ship gate + ablation-clean.

---

## How to start (first-5-minutes checklist for fresh session)

1. Read this file.
2. Read `campaign-handoff/HANDOFF-post-r7.8.md` top-to-bottom.
3. Read `CEILING-FINDING-r7.8.md` and `campaign-handoff/MORNING-SUMMARY-latest.md` (symlink to r7.8 morning summary).
4. Classify the task — output `[TASK CLASS: long-horizon]` with justification per CLAUDE.md Critical Rule #1.
5. Confirm operator intent: α / β / γ / δ? If operator silent, produce a ranked recommendation with one-line rationale and HALT awaiting go/no-go.
6. Source env: `source /tmp/r7.7-env.sh`; verify `$OMLX_API_KEY` populated (first 4 chars only). If missing, ask operator to regenerate.
7. Run `./probe-preflight.sh` — must return PASS before any work.
8. Verify VM canonical: `ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md'` → expect `0780c232…`.
9. Build a new PROGRESS file per chosen option (e.g., `PROGRESS-r7.9-alpha.md`). Include pre-committed noise band, vet-sample-stratification rule, operator pre-approvals carried forward.
10. Confirm r7.9 scope with operator before dispatching any implementation worker.
11. Plan. Dispatch. Judge. Iterate. Do not collapse roles in the main session.

---

## What r7.6/7.7/7.8 banked (inventory for re-use)

Infrastructure that survives the HOLD verdicts and is available to r7.9:

- `probe-preflight.sh` — non-bypassable pre-probe env gate (Agent-dispatch, oMLX health, tripwire baseline, VM idle).
- `CALIBRATION-r7.6-judge-protocol.md` — standing fresh-LLM judge calibration protocol.
- `probe-variant{H,I,J}-{stage.sh,wrapper.sh,check.py}` — r7.6/7.7 probe harnesses (H = HWO scaffold on G; I = rev-2 fixes; J = A1/A2 env-forwarding wrapper). The `variantJ-wrapper` is the env-forwarding wrapper — always use variantJ or later for any campaign that passes env-gated interventions through to the child.
- `variants/hermes/write_before_claim_gate.py` — A2 detect-only gate module (reusable).
- `variants/hermes/delegate_worker_v2.py` — β-fuse tool + A1 env-gated child-toolset restriction.
- `oMLX hot-reload` via `POST /admin/api/reload` (session-cookie auth from `POST /admin/api/login`, NOT Bearer). Verified working for sampler/parser tunes.
- **Substrate/eval knowledge**: Gemma-4-26B-A4B-it-MLX-8bit MoE = vanilla ~20% on T4/T5/T6/T10. `gemma-4-31B-it-4bit` dense is hardware-compatible but untested.

---

## What NOT to do (anti-patterns from this campaign arc)

- Do not re-probe an agentic-layer intervention on the existing T4/T5/T6/T10 matrix expecting ≥60%. Three campaigns say this surface is at ceiling.
- Do not vet with 5 random trials and assume scaling — stratify by failure mode.
- Do not trust `check.py` output as a worker-quality signal; it checks dispatch compliance only.
- Do not run arms sequentially across a 10+ hour oMLX session without per-arm randomization or pre-probe restart — sustained load drifts the substrate.
- Do not commit `OMLX_API_KEY` or any `/tmp/r7.*-env.sh` file with live values.
- Do not retag `r7.5-hermes-prerelease`. Ship forward under a new tag when there is a real ship thesis.

---

*The campaign's honest answer was hard-earned: three campaigns of agentic-layer patching did not move the MoE worker-quality ceiling. The path forward is now shaped by evidence rather than guesses. α, β, γ, or δ — pick one, commit, measure. The harness is the product; the firmware is the investment.*
