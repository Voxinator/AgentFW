[TASK CLASS: long-horizon]
Justification: Post-r7.8 handoff — operator reviewing campaign-arc evidence to pick r7.9 direction. Self-contained cold-start doc.

# HANDOFF — post-r7.8 for next campaign session

**Author:** overnight session 2026-04-20/04-21 that ran r7.8 autonomously
**Date:** 2026-04-21
**Operator:** Brian Taylor (voxinator@gmail.com)
**Self-containment:** this doc + the ARTIFACTs it references is everything a fresh session needs. Cross-references are evidence trails, not prerequisites.

---

## 1. TL;DR (for the fresh agent)

Three successive overnight campaigns (r7.6, r7.7, r7.8) ran full 20-trial ablation matrices on the 4-task eval set (T4/T5/T6/T10) against the Hermes variant of AgentFW. Every intervention landed **inside the noise band of the vanilla Hermes-on-Gemma-4-26B-MoE baseline (~4/20 = 20% worker-quality PASS).** The campaign's honest answer is: the agentic layer is not moving the needle on this substrate. The ceiling is somewhere other than where we've been patching. r7.7 S9 ship-judge formalized this with a "noise-band" HOLD verdict; r7.8's dedicated ablation (Arm K = T1 cross-turn loop detector vs Arm K' = pure vanilla) confirmed it empirically — Arm K scored **2/20**, Arm K' scored **4/20** exactly matching r7.6 Arm A's baseline of 4/20. β-fuse dispatch (r7.4-r7.5 pre-release) remains the only shipped worker-quality-adjacent improvement; everything above it has failed to compose.

The decision space for r7.9 is framed in §4. Three distinct directions exist (α substrate upgrade / β generation-layer done right / γ broader eval), plus a combined recommendation (δ) that the operator was leaning toward in the r7.8 morning summary. The operator has already asked John about dense (31B) trials — that thread may come back with a verdict. This handoff exists so a fresh context can pick up cold with the evidence already synthesized and pick α, β, γ, or δ without re-litigating the prior three campaigns.

---

## 2. Campaign arc evidence (single source of truth)

Aggregate table: every arm tested across r7.6 / r7.7 / r7.8, per-task, n=20 unless noted.

| Campaign | Arm | Config (additive) | T4 | T5 | T6 | T10 | Total PASS/20 | Rate |
|----------|-----|-------------------|----|----|----|-----|---------------|------|
| r7.6 | Arm A | vanilla (β-fuse dispatch only) | 4/5 | 0/5 | 0/5 | 0/5 | **4/20** | 20% |
| r7.6 | Arm B | + HERMES-WORKER.md (HWO) scaffold | 4/4 | 0/5 | 2/4 | 2/4 | **8/17** (non-LOST) | 47% of non-LOST |
| r7.7 | Arm G | + A1 child-toolset restriction (no `todo`) | 5/5 | 0/5 | 0/5 | 0/5 | **5/20** | 25% |
| r7.7 | Arm F | + HWO + A1 + A2 write-before-claim gate | 3/5 | 1/5 | 0/5 | 3/5 | **7/20** | 35% |
| r7.8 | Arm K | + T1 cross-turn loop detector only | 2/5 | 0/5 | 0/5 | 0/5 | **2/20** | 10% |
| r7.8 | Arm K' | vanilla baseline control | 4/5 | 0/5 | 0/5 | 0/5 | **4/20** | 20% |

At n=20 with p≈0.25, σ≈2. Every non-baseline arm sits within 1-2σ of the vanilla baseline.

**Rejected-in-vet candidates** (never graduated to 20-trial matrix):
- **r7.8 C1** — universal parser channel-marker scrubber. Unit tests 13/13 PASS, but the parser gate at `run_agent.py:8633` bypasses the `parse()` method for pure channel pollution; C1 was placed inside `parse()` and unreachable for the dominant pathology.
- **r7.8 S1** — conservative sampler tune (`temperature 0.8→0.6`, `top_p 0.95→0.9`, `top_k 64→40`, `repetition_penalty 1.0→1.08`, `min_p 0.0→0.03` on oMLX server-side). Median 36 turns (threshold ≤15); 3/5 trials with ≥5 consecutive identical tool_calls; `repetition_penalty=1.08` hit stable JSON scaffold tokens instead of semantic tool-arg repetition.

### Key observations (the invariants)

- **Vanilla ~20% on this eval.** r7.8 Arm K' (4/20) matches r7.6 Arm A (4/20) exactly. This is measurement converging.
- **All interventions land in ~2-8/20 noise band.** Range of all 5 non-vanilla arms: 2/20 to 8/17.
- **Per-task shape is invariant.** T4 ≈ 60-100% regardless of arm. T5/T6/T10 ≈ 0-3/5 regardless of arm. Drop T4 from the denominator and no arm has moved the hard-task needle.
- **~2/3 of FAILs are generation-layer pathologies, not agentic-layer.** Per r7.8-P1a failure-mode classification of 28 FAILs from r7.7: sampler 36%, parser 18%, prompt 18%, tool-call 18%, environment 14%, honesty 0%. Dispatch integrity is perfect (0 SCOPE breaches across 80+ trials).
- **β-fuse dispatch holds 100%.** Every parent in every trial across 3 campaigns correctly called `delegate_worker_v2`. No dispatch regression from any intervention stack. r7.5 pre-release tag remains sound.
- **r7.8 T1 vet was non-representative.** 5-trial vet passed on the strength of 1 trial exercising the Mode D pathology; 20-trial matrix showed 6 T1-WARN fires, 0 TERMINATEs, and 2 T4 regressions suggesting T1 may actively hurt tasks it wasn't designed for.
- **Infrastructure wins this campaign.** oMLX hot-reload for sampler tuning verified. md5-pin + rollback pattern applied cleanly across 3 vet attempts. Batched 5-trial workers eliminated r7.7's detached-orchestration failure mode.

Evidence citations (stable paths):
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-judge-*` — r7.6 40-trial fresh-LLM judges
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-judge-Arm{F,G}-T{4,5,6,10}-run{1..5}.md` — r7.7 40 judges
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-S9-ship-judge.md` — r7.7 ship verdict + ablation autopsy
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-judge-{ArmK,ArmKP}-T<id>-run<n>.md` — r7.8 40 judges
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-MORNING-SUMMARY.md` — r7.8 synthesis + 3 forward options
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-P1a-failure-modes.md` — 28-FAIL classification by layer

---

## 3. Hardware + substrate constraints (operator-confirmed)

- **Host**: Mac M5 Max / 128 GB unified memory / macOS 26.3.1
- **Guest runtime**: Parallels Desktop 26.3.0 → Ubuntu VM at `10.211.55.2` (aliased `ubuntu-vm` via SSH config)
- **Inference server**: oMLX 0.x on Mac at `localhost:8000`; VM reaches it at `10.211.55.2:8000`
- **Model in-use**: **`gemma-4-26B-A4B-it-MLX-8bit`** (Gemma-4 MoE, 8-bit). Operator-determined "best efficient" for this flywheel.
- **Model authorized but not yet tested**: **`gemma-4-31B-it-4bit`** (Gemma-4 dense, 4-bit). Hardware-compatible per operator confirmation. Requires pre-probe oMLX restart discipline (see §8).
- **Model ruled out**: Qwen3.5-class — weak tool-calling in operator empirical tests.
- **Model infeasible**: 122B-class on this hardware.
- **oMLX paging threshold**: `OMLX_SWAP_MAX_GB=30` (operator calibration 2026-04-20; was 5.5 — demonstrably too aggressive for sustained runs).
- **Hermes version pin**: v2026.4.8 / commit `86960cdb` / Python 3.11.15

**Hermes runtime state (verified live during r7.8 close):**
- `HERMES.md` md5 `0780c232a6cb52e13e432261f0d68ad9`
- `SKILL.md` md5 `fb1a5a5208a6cf2fcb8252aac10397eb`
- `jira-briefing.sh` md5 `a1dce6e989527686124d0860830627c9`
- `useDashboard.ts` md5 `5503ee1c2ef7d635a020eea275e41239`
- `run_agent.py` baseline md5 `94ad8712678df5e96b9f407446edf249`

**Env file**: `/tmp/r7.7-env.sh` on Mac (owner-only 600). Contains `OMLX_API_KEY`, `AGENT_DISPATCH_AVAILABLE=1`, `OMLX_SWAP_MAX_GB=30`. **Never commit this file with values.** Redact before any repo-side save. Key is also resolvable via `OMLX_API_KEY` env inheritance if the fresh session sources `/tmp/r7.7-env.sh` at session start.

---

## 4. Recommended next-step options (decision framing)

Three distinct directions emerged from the r7.8 morning summary, plus a combined recommendation. Each option includes a thesis, exact procedure, budget, success criterion, and risk.

### Option α — Substrate upgrade to Gemma-4-31B-dense

- **Thesis.** Maybe the ceiling is the Gemma-4 MoE variant, not Hermes's agentic layer. Three campaigns of agentic-layer tuning have not moved the needle on T5/T6/T10. If the substrate itself caps at ~20%, substrate upgrade is the load-bearing move.
- **Exact procedure**:
  1. Stop oMLX (`osascript -e 'quit app "oMLX"'` or via Activity Monitor), wait ~10s, restart. This is the pre-probe discipline per operator memory note about orphaned-session accumulation on sustained dense load.
  2. Verify oMLX has the `gemma-4-31B-it-4bit` model entry in `/Users/briantaylor/.omlx/model_settings.json`. If missing, add it with the standard Gemma-4 template (copy from MoE entry, update model id, set sampler defaults to match MoE: `temperature=0.8`, `top_p=0.95`, `top_k=64`).
  3. Run `probe-preflight.sh` to confirm VM↔oMLX↔model wiring is sound.
  4. Run a small-sample vet (5 trials × 4 tasks = 20 total) against pure vanilla Hermes (no HWO, no A1/A2, no T1). `ARM=VANILLA`, model override via env or config.
  5. 40 fresh-LLM judges on the 20 trials.
  6. Compare PASS rate against r7.8 Arm K' (4/20 = 20%).
  7. If ≥12/20 (60%), that's the "interesting enough" threshold per operator's conversation framing. Proceed to full 20-per-task (80 trial) matrix for publication-quality measurement.
- **Budget**: one overnight for vet (~6-8h wall-clock). If vet passes 60%, a second overnight for the 80-trial matrix + 80 judges.
- **Success criterion**: dense ≥60% on the same 4-task eval, ideally on the vet run.
- **Risk**:
  - oMLX degradation concerns on sustained dense load (more paging, higher orphaned-session accumulation rate).
  - Dense is larger; may be slower per turn; wall-clock budget may balloon. Plan for 1.5-2× trial time.
  - If dense is still ~20%, the finding is "the 4-task eval itself is pathological" — pointing toward option γ.
- **Signals operator wants**: a 60%+ MoE result would unblock the operator's external 31B-dense conversation with John; a 60%+ dense result would motivate making dense the canonical substrate.

### Option β — Generation-layer, correctly targeted

- **Thesis.** Our three tested agentic interventions (HWO, A1+A2, T1) missed the actual substrate. r7.8-P1a's layer attribution says 36% of FAILs are sampler, 18% are parser, 18% are prompt-thrash. Properly-targeted generation-layer patches could hit — but only if placed correctly (C1 failed because it was inside `parse()`; the real gate is upstream at `run_agent.py:8633`). Three concrete candidates surfaced in r7.8 research but were not vetted.
- **Top 3 concrete candidates (from r7.8 research)**:
  1. **Pattern-similarity loop detector (T1.1)** — r7.8 T1 used byte-identical match on `(tool_name, arguments)` signatures. Arm K matrix showed 6+ FAILs were *semantically* repetitive (different search queries for the same conceptual target) and evaded T1. Replace the exact-match check with Jaccard similarity ≥0.9 on tool arguments (or more robustly, embed-then-cosine). Threshold and hysteresis reusable from T1. Evidence: `ARTIFACT-r7.8-P1d-stoptoken-research.md` §5 T1 block; `ARTIFACT-r7.8-MORNING-SUMMARY.md` §"T1 is mechanistically correct but scoped too narrowly".
  2. **Harmony reasoning_parser in oMLX model_settings** — `ARTIFACT-r7.8-P1c-sampler-research.md` Appendix C flagged that Gemma-4 MoE's `reasoning_parser` field is currently `None`. oMLX has builtin `"harmony"` parser. Setting `"reasoning_parser": "harmony"` on both Gemma-4 entries in `~/.omlx/model_settings.json` may strip `<channel|>` / `<tool_call|>` / `[]<tool_call|>` markers server-side before Hermes ever sees them. Addresses 5/28 FAILs (Mode 3 channel pollution) plus compounded fragments in ~13 secondary-mode trials. Never vetted. Hot-reload via `POST /admin/api/reload` (see §8).
  3. **Pre-parser content scrubber at `run_agent.py:8633`** — C1's correct placement. C1 at ~30 lines was placed inside `parse()` (unreachable); the right location is *before* the parser gate, on the raw content path. Design: strip `<channel|>`, `<|channel|>`, `thought\n<channel`, `<tool_call|>`, `[]<tool_call|>` substrings from assistant content field before persistence; require at least one non-empty synthesis turn before session termination. Evidence: `ARTIFACT-r7.8-P1C-impl-notes.md` (C1 post-mortem); `ARTIFACT-r7.8-MORNING-SUMMARY.md` §"Parser gate at run_agent.py:8633 is the correct pre-parser insertion point".
- **Exact procedure per candidate**: (a) implement with `.probe-r7.9-*-orig` backup + md5 pin, (b) unit-test in isolation, (c) 5-trial stratified vet (see §7 methodology note — vet must include ≥2 trials per targeted failure mode, not 1 per task), (d) if vet passes on mechanism + doesn't regress healthy-path, run 20-trial Arm K2 + Arm K2' control, (e) 40 fresh-LLM judges, (f) verdict.
- **Budget**: one overnight per candidate if run serially (~10-12h each); candidates 1+2 could be bundled into a single Arm (call it Arm L = pattern-similarity-T1 + harmony-parser) since they address different failure modes.
- **Success criterion**: combined Arm ≥12/20 (60%) on the same 4-task eval, ideally ≥8/15 on the hard-task subset (T5+T6+T10).
- **Risk**:
  - May still hit substrate ceiling. If vanilla is truly 20% due to model capability, even well-targeted generation-layer patches may only reclaim the "garbage-output" fraction (5-8 FAILs) without flipping hard-task outcomes.
  - Harmony parser change is oMLX-side; unknown how `gemma-4-26B-A4B-it-MLX-8bit`'s chat-template emits channel markers — Appendix C flags this as "confirm first".
  - Pattern-similarity detector risks false-positives on legitimate iterative discovery (e.g. reading 5 related files).

### Option γ — Broader eval to measure generalization

- **Thesis.** The 4-task eval (T4/T5/T6/T10) may be selecting for Gemma-4-MoE's specific weaknesses. The north-star claim "general-purpose harness that runs on any project type" has not been tested — all three campaigns benchmark on the same 4 tasks. If the existing interventions (HWO, A1, A2, T1) were benchmark-tuning all along, a broader eval would reveal that. If they generalize, the campaign's value was higher than the headline verdict implied.
- **Exact procedure**:
  1. Design a new 5-8 task battery stratified across the dimensions r7.8 did not test:
     - (a) **short-loop** — single read+edit+verify cycle, no search phase (e.g., "add a logging line to known file and run tests")
     - (b) **data transform** — structured input → structured output with schema check (e.g., "convert these 20 JSON records into a CSV with these column mappings")
     - (c) **small refactor** — rename symbol across ≤3 files with compile check (e.g., "rename function `foo` to `bar` in this small repo")
     - (d) **Q&A-with-citation** — read known repo, answer a question with file:line citations (e.g., "where is authentication configured, and cite the line")
     - (e) **multi-phase planning-only (no execution)** — produce a 5-step PLAN.md for a stated goal with honest blocking on missing info (e.g., "write a PLAN.md for migrating X to Y; you have read-only access")
  2. Encode each task as a probe harness entry equivalent to T4/T5/T6/T10 structure — goal prompt, success rubric, oracle files or expected behavior.
  3. Re-run vanilla + one intervention (HWO by default, since it showed the largest positive signal on T10 in r7.7) across all 8 tasks × 5 trials = 40 trials per arm = 80 total.
  4. 80 fresh-LLM judges.
  5. Compare per-task and per-dimension rates; look for generalization lift vs. benchmark-overfit signal.
- **Budget**: 1 day to design + encode eval + 1 overnight to run = ~1.5 days.
- **Success criterion**: a defensible statement about which tasks/dimensions the current harness + interventions actually generalize across. "The harness improves (a, b, d) by ≥15pp but is flat on (c, e)" is an acceptable answer; "the harness generalizes nowhere" is also an acceptable answer.
- **Risk**:
  - May invalidate existing measurements — if the harness doesn't generalize, the r7.4 pre-release value claim weakens.
  - Changes the denominator; future comparisons to r7.6/7.7/7.8 become cross-eval comparisons.
  - Task encoding work is nontrivial; there are ways to accidentally build a new benchmark that still overfits to Gemma-4-MoE quirks.

### Option δ — Combined recommendation (operator lean from r7.8 summary)

Operator's r7.8 morning summary leaned toward **α + γ in parallel**, with β deferred pending α/γ results.

- **Rationale**: α tells us whether substrate is the ceiling (one overnight, low-risk low-info-if-no or high-risk high-info-if-yes). γ tells us whether the existing campaign value was real or benchmark-tuned (~1.5 days). If α hits 60%+ dense, the campaign's next arc is substrate-first + re-verify existing interventions on dense. If γ surfaces that HWO generalizes well, even a HOLD verdict on MoE becomes a meaningful shipped asset. If both come back flat, the field closes gracefully and β becomes the last honest swing.
- **Ordering suggestion**: start α first (smaller scope, faster answer, unblocks the John conversation). γ in the following campaign slot. β only if both α and γ are inconclusive.

**Not-a-fourth-option (explicit)**: more agentic-layer prompt tuning on MoE with the same 4-task eval. Three campaigns of evidence say this is the wrong place to spend a fourth overnight.

---

## 5. Hard constraints (do NOT violate)

- **Pre-release tag `r7.5-hermes-prerelease` is immutable.** Operator-only. Never force-push, never delete, never re-tag.
- **Tripwire files are canonical and must never drift mid-campaign:**
  - `HERMES.md` md5 `0780c232a6cb52e13e432261f0d68ad9`
  - `SKILL.md` md5 `fb1a5a5208a6cf2fcb8252aac10397eb`
  - `jira-briefing.sh` md5 `a1dce6e989527686124d0860830627c9`
  - `useDashboard.ts` md5 `5503ee1c2ef7d635a020eea275e41239`
  - Every probe wrapper verifies these pre- and post-trial. Any drift → campaign halts.
- **VM must be canonical at session end.** Non-negotiable. Any `.probe-*-orig` staging artifacts removed; all variant changes unstaged; `run_agent.py` md5 returns to baseline `94ad8712678df5e96b9f407446edf249`. Operator confirms via `probe-preflight.sh`.
- **No pushes to `origin/main` without operator authorization.** Not even for "just the artifacts".
- **No secret values in tracked files.** `OMLX_API_KEY` stays in `/tmp/r7.7-env.sh` (owner-only) and env vars. If a workflow would put it on disk inside the repo, halt and ask.
- **The harness is the product.** No task-specific tuning. Every intervention must carry a one-line "why this generalizes beyond T4/T5/T6/T10" justification. If a candidate can only be argued to help one task, it fails the design bar.
- **Jira cron weekday path must stay safe.** `SKILL.md` + `jira-briefing.sh` remain on their canonical md5s for the duration of any campaign — Monday's cron run is operator-production.

---

## 6. What the fresh session should read (in order)

1. **This file** (`/Users/briantaylor/Projects/AgentFW/HANDOFF-post-r7.8.md`).
2. `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-MORNING-SUMMARY.md` — the headline with the ceiling-finding and the original 3 options.
3. `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.7-MORNING-SUMMARY.md` — prior campaign's pivot-to-generation-layer thesis (which r7.8 then tested and partially disconfirmed).
4. `/Users/briantaylor/Projects/AgentFW/CLAUDE.md` — AgentFW doctrine. Critical rules, role separation, classification gate, Planner-Worker-Judge.
5. `/Users/briantaylor/Projects/AgentFW/PROGRESS-r7.8.md` — campaign state at close; operator pre-approvals carry forward.
6. **If choosing Option β**:
   - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-P1a-failure-modes.md` — full per-trial attribution of 28 FAILs by layer. Drives candidate prioritization.
   - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-P1c-sampler-research.md` — Appendix C flags the harmony `reasoning_parser` lead (candidate β.2). Documents hot-reload mechanics.
   - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-P1d-stoptoken-research.md` — T1 implementation sketch and the pattern-similarity upgrade path (candidate β.1).
   - `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.8-P3c-T1-vet.md` — T1 vet outcome showing exact-match limitation.
7. **If choosing Option α**: `ARTIFACT-r7.8-P1c-sampler-research.md` §"Current state" for oMLX model_settings template — you'll need to add a `gemma-4-31B-it-4bit` block following the same shape.
8. **If choosing Option γ**: `/Users/briantaylor/.claude/projects/-Users-briantaylor-Projects-AgentFW/memory/MEMORY.md` for any cross-campaign notes; eval-protocol under `evaluation/eval-protocol.md` for the existing eval's measurement discipline.
9. **For deep dives**: archived campaign logs under `/Users/briantaylor/Projects/AgentFW/archive/` (r7.6 and r7.2-r7.3 dirs present; r7.7 and r7.8 still in root as of handoff, will be archived by operator or first-5-minutes housekeeping).

---

## 7. Open methodology questions (for operator discussion)

These surfaced as lessons from r7.8 and should shape r7.9 design regardless of which option is chosen.

- **Vet sample must stratify by failure mode, not task.** r7.8 T1 passed 5/5 vet but the Mode D pathology (consecutive-identical tool_calls) was exercised in exactly 1 of 5 vet trials. The 20-trial matrix revealed 6 Mode-D fires, 0 terminates (because T1's exact-match missed the semantically-equivalent variants), and 2 T4 regressions. **New rule**: every vet sample must include ≥2 trials per targeted failure mode. For r7.9, this means pre-classifying 2-3 of the vet trials as known Mode-D/3/2/R triggers before running.
- **Wrapper `check.py` is insufficient for worker-quality gating.** S1 vet had 3/5 trials with degenerate loops reported as PASS by the wrapper (it checks dispatch compliance, not worker-quality). Deep-judge analysis caught it. **New rule**: all ship gates and vet thresholds must use fresh-LLM judges on the deep session JSON, never `check.py` alone. `check.py` is for dispatch integrity; it does not measure worker output quality.
- **Per-arm randomization for ablation integrity.** Current r7.x design runs arms sequentially (e.g., Arm K then Arm K'). If oMLX health drifts monotonically across a long session (paging, orphaned sessions), this biases the comparison. Consider interleaved batches: run batch 1 of K, batch 1 of K', batch 2 of K, batch 2 of K'. Verify oMLX health is flat across batches. This is particularly important for α because dense model runs are heavier on oMLX and more prone to drift.
- **Noise-band explicit per plan.** r7.7's ship plan was the first to pre-commit a "6-8/20 noise band" range. r7.8 honored it. r7.9 should pre-commit its noise band before any trials run, so verdicts are mechanical not interpretive.
- **Publication threshold vs. ship threshold.** Operator's r7.8 framing set `12/20 = 60%` as the "interesting enough to tell John" threshold (not a ship gate). r7.9 α/β/γ should separate: "does this unblock the operator's external conversation?" (60% bar) vs. "does this warrant a canonical swap + new pre-release?" (75% bar + ablation-clean).

---

## 8. Known traps carried forward

- **oMLX admin reload endpoint** = `POST /admin/api/reload` (not `POST /admin/api/reload-models`, which `ARTIFACT-r7.8-P1c-sampler-research.md` documented incorrectly). Authentication is via a **session cookie** obtained from `POST /admin/api/login` with the admin password — NOT a Bearer token for admin endpoints. `OMLX_API_KEY` Bearer auth works for `/v1/*` endpoints (inference) but NOT for `/admin/*`.
- **variantH + C1-class parser patches both edit `gemma_parser.py`.** Conflict handling requires distinct backup suffixes: `.probe-r7.8-c1-orig` vs `.probe-r7.6-orig`. Track suffix conventions in the PROGRESS file.
- **Hot-reload oMLX takes ~3s to propagate.** Scripts that invoke inference immediately after `POST /admin/api/reload` may see stale settings briefly. Add a 5s sleep or a single warm-up inference call before starting real trials.
- **`probe-variantJ-wrapper.sh` is the env-forwarding wrapper.** variantI-wrapper silently dropped r7.7 A1/A2 env flags — that's why r7.7 had a mid-campaign wrapper-swap. Always use variantJ-wrapper (or later) for any campaign that passes env-gated interventions through to the child.
- **Child sessions do not inherit the parent's `IterationBudget`.** Per `ARTIFACT-r7.8-P1d-stoptoken-research.md` §1: child sessions get a fresh 50-turn budget regardless of `--max-turns 20` on the parent. This is why r7.7 Arm G T5-run2 hit 42 turns despite a 20-turn advertised budget. If wall-clock caps matter for r7.9, implement T4b (parent/child budget alignment) per that artifact's §5.
- **`repetition_penalty=1.0` is the current default** in Gemma-4 MoE's `/Users/briantaylor/.omlx/model_settings.json` — effectively disabled. This is structurally why Mode D loops occur. r7.8 S1 tested `1.08` and rejected (hit stable JSON scaffold tokens, not semantic arg repetition). Any r7.9 sampler work should target the harmony `reasoning_parser` angle instead (β.2) or leave sampler alone.
- **Hermes sends ZERO sampler params to oMLX on the main path.** All sampler behavior lives in `/Users/briantaylor/.omlx/model_settings.json`. Single file, one edit, global effect — this is the biggest leverage point for sampler-side interventions. Per-request overrides from Hermes require code changes in `run_agent.py:5367` (`_build_api_kwargs`).

---

## 9. VM + pre-release state at handoff

- **VM canonical**: confirmed at r7.8 close. `HERMES.md` md5 `0780c232a6cb52e13e432261f0d68ad9` MATCH. All 4 tripwires MATCH.
- **Pre-release tag**: `r7.5-hermes-prerelease` untouched on GitHub. No pushes this session.
- **No unstaged probe residue on VM**. All `.probe-r7.8-*-orig` backups removed. `run_agent.py` md5 restored to baseline `94ad8712678df5e96b9f407446edf249`.
- **oMLX swap threshold**: `OMLX_SWAP_MAX_GB=30` (operator calibration 2026-04-20).
- **`/tmp/r7.7-env.sh` on Mac**: contains `OMLX_API_KEY` value (owner-only 600). DO NOT commit. DO NOT archive with value. Redact before any repo-side save. If `/tmp/r7.7-env.sh` has been rotated out between handoff and fresh-session pickup, the operator will need to regenerate it from the oMLX admin panel.
- **Mac working-tree state**: many untracked `ARTIFACT-r7.6-*`, `ARTIFACT-r7.7-*`, `ARTIFACT-r7.8-*` files present in repo root (campaign artifacts). Plus `PROGRESS-r7.8.md`. One modified file: `variants/hermes/HERMES-variantF.md` (working-tree-only Fix 4 "Retry Re-Classification" carryover from r7.6; operator deferred decision on new tag vs release-note amendment). This does not block r7.9; just noted so the fresh session does not panic at `git status` output.
- **Archived campaigns**: `/Users/briantaylor/Projects/AgentFW/archive/hermes-probe-r7-2026-04-18/` and `hermes-probe-r7.2-r7.3-2026-04-18/` contain older campaign bundles. r7.6/7.7/7.8 artifacts are still in repo root (not yet archived).

---

## 10. How to start (first-5-minutes checklist for fresh session)

```
1. Read this file (HANDOFF-post-r7.8.md) top-to-bottom.
2. Read ARTIFACT-r7.8-MORNING-SUMMARY.md.
3. Classify the task — output [TASK CLASS: long-horizon] with justification per CLAUDE.md Critical Rule #1.
4. Confirm operator intent: α (substrate), β (generation-layer), γ (broader eval), or δ (combined)?
   - If operator silent and feeding this doc into another session for analysis only, produce a ranked recommendation with one-line rationale and HALT awaiting go/no-go.
5. Source the env file: `source /tmp/r7.7-env.sh` on Mac, then verify `$OMLX_API_KEY` is populated (first 4 chars only; never echo full value). If file missing, ask operator to regenerate.
6. Run `/Users/briantaylor/Projects/AgentFW/probe-preflight.sh` — must return PASS before any work. This validates VM↔oMLX↔tripwire state.
7. Verify VM canonical: `ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md'` → expect `0780c232a6cb52e13e432261f0d68ad9`. Repeat for other three tripwire files.
8. Build new PROGRESS file per chosen option (e.g., PROGRESS-r7.9-alpha.md). Include: chosen option, phases with budgets, operator pre-approvals carried from PROGRESS-r7.8.md §"Operator pre-approvals", vet-sample-stratification rule from §7 of this handoff, pre-committed noise band for the arm.
9. Confirm r7.9 scope with operator before dispatching any implementation worker. If in autonomous mode, confirm the authorization was renewed for r7.9 specifically (r7.8 auth did not extend automatically).
10. Plan. Dispatch. Judge. Iterate. Do not collapse roles in the main session.
```

---

*Good luck. The campaign's honest answer was hard-earned: three campaigns of agentic-layer patching did not move the MoE worker-quality ceiling. The path forward is now shaped by evidence rather than guesses. α, β, γ, or δ — pick one, commit, measure. The harness is the product; the firmware is the investment.*
