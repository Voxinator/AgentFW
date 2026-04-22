[TASK CLASS: structured]
Justification: Cross-mode synthesis for r7.6 Phase 0 failure-mode investigation. Read 4 investigator reports + r7.5 baseline + prior ship judge + 8 trial artifacts; produce priority order + experiment bundle + baseline re-score recommendation.

# ARTIFACT — r7.6 cross-mode synthesis verdict

## TL;DR

**Priority order (r7.6 Phase 1):** inv-3 (30-45m parser fix, highest leverage/hour) → inv-2 G1 (3-4h chat-template content filter, unifies with inv-3 as "oMLX+Gemma-MoE chat-template" surgery) → inv-4 F4A (1-2h mechanical fabrication detector, pre-probe) → inv-1 F3A HERMES-WORKER.md (4-6h; the behavioral lift that needs the cleanup underneath it before being measurable).

**Key correction to inv-1:** its claim that HERMES-WORKER.md provides cross-cutting coverage of modes 3 and 4 is **partially false for mode 3 and partially true for mode 4**. Inv-3's evidence is load-bearing: the model IS emitting the correct Gemma Format 1; the problem is a parser gate that the prompt cannot reach. A prompt can't fix a parser-gate miss. For mode 4, F4A's mechanical check is structurally superior to prompt language (campaign lesson applies).

**Unified-chat-template insight (inv-2 + inv-3):** both are oMLX-side serialization on the same 26B MoE stack, manifesting as different symptoms (channel-marker leakage in content; opening-sentinel stripped on tool_call). **Recommend a single "Gemma-MoE chat-template correctness" workstream that lands both fixes together** and adds a regex-based content normalizer at the `run_agent.py:8908` boundary. Unified fix is ~5-7h vs 8-10h doing them independently.

**r7.5 reframing — ship verdict does not flip:** my independent re-read of the 8 reframed trials (6, 7, 9, 10, 11, 12, 13, 14) shows **0/8 would flip to PASS** on a tool-call-content re-judgment. The children were genuinely incomplete (wrong cwd, 3-4 turns, no synthesis possible even with clean content). Inv-2's reframe corrects the *mechanism* label but not the *outcome*. r7.5 worker-quality stays at 3/20. HOLD-narrow remains correct.

**Experiment bundle recommendation: HYBRID.** Land inv-3 + inv-2 + inv-4 pre-probe (mechanical, code-verifiable, non-behavioral). Probe inv-1 F3A alone as the behavioral intervention, with a baseline-control arm of the three cleanups landed but no HERMES-WORKER.md. This cleanly attributes behavioral delta to the prompt layer, not the cleanup layer.

---

## Part 1 — Per-mode verdict table

| Mode | Inv | True incidence (corrected) | Root cause per investigator | Top fix | Effort | Inv confidence | Layer |
|------|-----|---------------------------|-----------------------------|---------|--------|----------------|-------|
| #1 search_files thrash | inv-1 | 6/20 direct thrash (investigator corrects to 6 from operator-stated 7; trial 17 is hybrid thrash + pseudo-tool-call) | H2A + H2B: child has no stop-heuristic, no plan-then-execute pattern, no turn-budget signal; 26B MoE defaults to exploration-as-progress with no ceiling | F3A: HERMES-WORKER.md preamble in `_build_child_system_prompt` teaching plan/stop/budget/anti-fabrication, pairs well with F3B turns-remaining scaffold | M (4-6h F3A alone; ~7-8h with F3B) | Medium-high on mechanism; **inferential** on effect-size estimates ("probabilistic, not deterministic"; explicitly self-flagged as uncalibrated) | Scaffolding-layer (child system prompt) |
| #2 "SIGTERM truncation" (REFRAMED) | inv-2 | 8/20; **reframed — NOT SIGTERM**. Confirmed via `exit_reason=completed`, 6-57s durations (well under 900s), clean JSON persistence on all 8 | H2F: 26B MoE emits harmony/channel markers (`<channel\|>`, `thought\n<channel\|>`) as its only user-visible content on oMLX+Gemma-MoE. Tool_calls parse, but every assistant `content` is chat-template leakage. Hermes' empty-follow-up fallback silently exits with `completed=True` despite no synthesis | F2G: G1 upstream content-filter (regex on `run_agent.py:8908` to treat channel-marker-only content as empty, routes to `(empty)` terminal) + G2 check.py `WORKER_EMPTY_SYNTHESIS` verdict. F2A Tier 3 SIGTERM handler is still valuable but **does not fix these 8 trials** | G1+G2: 5-6h combined. F2A separate: ~4h | **High** on mechanism (direct VM evidence, regex-matched content); high on "SIGTERM is wrong label" | Chat-template-layer (oMLX+Gemma-MoE) + harness-layer fallback-path |
| #3 pseudo-tool-call emission | inv-3 | **3/20 corrected from operator-stated 4** (trial 20 reclassified out; it's actually mode-4 fabrication + channel leak, not Format-1 emission) | H3F + H3E: Gemma 4 26B MoE emits Gemma Format 1 (`call:fn{args}<tool_call\|>`) with opening `<\|tool_call>` sentinel stripped by oMLX chat-template. Hermes' `GemmaToolCallParser` exists but detection gate at `run_agent.py:8631` AND parser regex at `gemma_parser.py:26-30` both require the opening sentinel, so the half-sentinel form never triggers the parser | F3A′: 2-line detection-gate relaxation + one additional prefix-less regex in `gemma_parser.py` | **S (5 LOC, 30-45m)** | **High** (parser code read directly, pattern is syntactically unambiguous, 100% trial coverage) | Chat-template-layer (oMLX strip) + harness-layer (parser gate) |
| #4 fabricated completion | inv-4 | 2/20 confirmed (T10 only; both have ZERO write/patch/terminal calls and 4+ `todo` calls mis-used as write-substitutes) | H4A + H4D: T10's long-horizon "produce X.md" framing elicits narrative planning; 26B MoE generates the plan content as prose and treats `todo` status-transitions as stand-ins for actual file writes. H4E (MoE weak grounding) as amplifier | F4A: extend `probe-variantF-check.py` FABRICATION detector to flag "completion claim naming filename/path AND zero write-type tool calls". Mechanical, cross-cutting. F4B (worker prompt language) as cheap adjuvant; F4C (read-back enforcement) deferred to r7.7+ | F4A: 1-2h + 2h validation. Full V1-V3: 6-8h VM | **Medium** (n=2/20 is small; mechanism is identified but fix is indicated, not proven); explicitly flagged | Harness-layer (mechanical check) + scaffolding-layer (prompt adjuvant) |

**Layer distribution:**
- inv-2 (G1) + inv-3 (F3A′) are **both chat-template-layer** surgery on the same oMLX+Gemma-MoE stack (see Part 2 below).
- inv-1 F3A is **scaffolding-layer** (child system prompt) — purely behavioral/model-facing.
- inv-4 F4A is **harness-layer** (check.py post-hoc detection) — mechanical and deterministic.

---

## Part 2 — Cross-cutting insights

### Insight 1: inv-2 G1 and inv-3 F3A′ are two symptoms of one root problem

**Yes — they are ONE problem: oMLX+Gemma-MoE chat-template serialization with Hermes.** Both manifest at the same boundary (`run_agent.py` reading model-surface content) on the same stack (gemma-4-26b-a4b-it-mlx-8bit). The symptoms diverge because Hermes has two downstream consumers of that surface:

- **Tool-call parser path** (inv-3): looks for sentinel pairs; the opening sentinel is stripped; parse miss.
- **Content-persistence path** (inv-2): takes the raw content as assistant message; channel markers leak through as visible output; fallback silently exits.

A unified fix would place a normalizer at `run_agent.py:8908` (or immediately after `assistant_message.content` is read) that:
1. Strips the channel-marker prefix (`^(thought\s*)?<channel\|>` and variants) from content (inv-2 G1).
2. If the stripped content begins with `call:\w+\{` or contains `<tool_call\|>`, route to the Gemma parser even without `<\|tool_call>` prefix (inv-3 F3A′).

This gets you both fixes for approximately the effort of either one alone (~4-5h combined vs 3-4h + 0.75h separate = still ~same; the efficiency win is in testing/validation, not coding). **I recommend landing them as a single "Gemma-MoE chat-template correctness" worker dispatch, with one unit-test file covering both cases.**

### Insight 2: inv-1's cross-cutting claim for mode 3 is FALSE

Inv-1 claims F3A (HERMES-WORKER.md) will "plausibly PASS trials 15/16" because the honest-blocked template "should crowd out the `call:write_file{...}` mode." This is **wrong per inv-3's evidence**.

Inv-3 established:
- The model IS emitting syntactically correct Gemma Format 1 tool calls.
- The opening sentinel is stripped by the oMLX server, not by the model.
- The parser gate + regex require the opening sentinel.

No amount of prompt-level instruction to the model can prevent the oMLX server from stripping its own template marker. The prompt could teach the model to emit structured tool_calls instead of Gemma Format 1 — but the model is already attempting to do that; the stripping happens between the model and Hermes. **Prompt-layer fixes cannot reach into the oMLX chat-template boundary.**

The correct fix for mode 3 is inv-3's parser relaxation. Any prompt-side effect would be coincidental and unreliable. Inv-1's claim here should be withdrawn.

### Insight 3: inv-1's cross-cutting claim for mode 4 is PARTIALLY true but mechanical-inferior

Inv-1 claims F3A's anti-fabrication rule will recover HONESTY on T10. Inv-4's evidence: the two fabrication trials had ZERO write-type tool calls and mis-used `todo` as a write-substitute. A prompt rule "do not claim writes without tool-call evidence" targets the exact mechanism.

**But** the campaign's own established lesson (per F.2 recommendation #4 and inv-4's explicit statement): "language-only fixes have a bad track record per this campaign's arc." The 26B MoE at 8-bit quantization has demonstrated poor compliance with system-prompt negative-constraints. A mechanical F4A check (regex-match claim phrase + absence of write tool-call in session → automatic FAIL) **catches the failure post-hoc with 100% recall by construction**, regardless of model compliance.

**Correct framing:** F4A is the primary fix for mode 4; F3A's anti-fabrication line is a cheap adjuvant that may or may not help. Inv-1 should not claim credit for mode 4 in its cross-cutting assertions; F4A should land first and F3A's effect on mode 4 measured as a residual lift (not a primary lift).

### Insight 4: applying the campaign's prior lesson honestly

"Language-only fixes don't move the needle; structural and mechanical fixes do."

Mapping this to the 4 investigators:
- **inv-3 (F3A′):** purely mechanical parser fix. Deterministic. Highest compliance with the lesson.
- **inv-2 (G1):** mechanical content-normalizer. Deterministic. High compliance.
- **inv-4 (F4A):** mechanical post-hoc detector. Deterministic. High compliance.
- **inv-1 (F3A):** scaffolding-layer system prompt. Behavioral. Partial compliance — this is a "structural scaffold" in the sense that it's reliably injected, but its *effect* on the 26B MoE is probabilistic. Campaign lesson says language alone won't move the needle; inv-1's self-described effect ("probabilistic, not deterministic" with "bimodal distribution collapsing toward the clean mode") is honest about this and proposes measurement at 5 trials × 4 tasks to characterize the probabilistic effect.

**Implication for priority:** the three mechanical fixes should land first and their effect should be measured. The scaffolding fix should land second and be measured against that cleaner baseline. This also lets us isolate whether the prompt layer is actually doing work, or whether the mechanical fixes alone close enough of the gap.

### Insight 5: a tension I want to flag

Inv-1's fix (HERMES-WORKER.md) assumes children *need teaching* because they run without a contract. Inv-2's fix (content-filter) assumes children are *emitting productive tool calls but polluted content*. These framings are both true but suggest different priorities:

- If inv-2 G1 lands and children start routing through `final_response="(empty)"` cleanly, the 8 reframed-mode-2 trials become **visibly incomplete** rather than silently-completed-with-garbage. This will show up as MORE WORKER_QUALITY=FAIL in raw counts (because the fallback was masking empty synthesis as "completed"), but the failures are now legible and diagnosable. inv-1's HERMES-WORKER.md then has more headroom: a child with a stop-heuristic + plan doctrine is much more likely to produce an honest-blocked summary on a wrong-cwd task than a child without one.

- So the fixes compose: inv-2 G1 unmasks the failure mode; inv-1 F3A gives the model the tools to avoid it.

This is the argument for landing inv-2 before inv-1, even though inv-2 alone will likely increase the visible FAIL count initially.

---

## Part 3 — Reframing implication on r7.5 baseline

### 3.1 — Independent re-read of the 8 reframed trials

Per inv-2, trials 6, 7, 9, 10, 11, 12, 13, 14 were mis-labeled as SIGTERM-truncated. They are instead "productive children with chat-template-polluted content" that exited cleanly via the empty-follow-up fallback.

I re-read all 8 per-trial artifacts. For each, I ask: **if I remove the chat-template-artifact FAIL and re-judge on the CONTENT OF TOOL CALLS (ignoring the garbled content fields), would this trial PASS?**

| # | Task | Asst turns | Tool-call evidence | Goal addressed? | Re-judged verdict |
|---|------|-----------|---------------------|-----------------|-------------------|
| 6 | T5 (stale-data bug) | 11 | 10+ productive search_files, read_file on code files | Searched; never named root cause of stale-data bug | **FAIL** (CORRECTNESS=FAIL per F.2; "goal unaddressed"; no patch, no diagnosis) |
| 7 | T5 (stale-data bug, retry-path child) | 12 | Similar to #6 | Same as #6 | **FAIL** |
| 9 | T5 (stale-data) | 3 | Only 1-2 tool calls; search result from wrong cwd | No. Only 3 turns, no investigation depth | **FAIL** |
| 10 | T5 (cache invalidation patch) | 4 | Read jira-cache.ts (21144 chars) | Investigated but did NOT patch. CORRECTNESS=PASS in F.2 but COMPLETION=FAIL because no patch emitted | **FAIL** (worker never wrote the fix) |
| 11 | T6 (feature build) | 3 | Only todo setup | No. Barely started | **FAIL** |
| 12 | T6 (feature build) | 10 | Searches in wrong dir (hermes-agent root) | No. Never located product code | **FAIL** |
| 13 | T6 (feature build) | 3 | Read hermes-agent/package.json | No. Barely started | **FAIL** |
| 14 | T6 (feature build) | 9 | Searches in wrong dir | No. Never located product code | **FAIL** |

**Independent verdict: 0/8 would flip to PASS.**

The children's tool-call productivity is genuinely low (3/4/9/10/11/12 turns is not enough to complete these tasks; children were in wrong cwd for several). Even with clean content, they did not reach "produced a summary addressing the goal" or "wrote a correct artifact." The chat-template pollution is downstream of the task-completion state — the children were going to fail regardless of whether their content was clean or polluted, because they didn't actually complete the work.

### 3.2 — Adjusted PASS rate

If 0/8 would flip with inv-2 G1 applied, the adjusted PASS rate is unchanged: **3/20 (15%).**

The baseline brief's hypothetical ("if 6 of 8 would PASS, we'd be at 9/20") does not hold. The evidence is:
- The 8 trials had 3-12 assistant turns (most under 10); several in the wrong cwd.
- All 8 had tool-call sequences that either terminated too early (no synthesis reached yet) or searched the wrong directory.
- The chat-template artifact masked the reason for exit (empty-follow-up → silent completed) but did not cause the underlying failure to complete.

### 3.3 — Ship-verdict implications

- **Arithmetic does NOT flip.** Worker-quality gate is still 3/20 vs 15/20 floor = -12 below. HOLD-narrow remains correct.
- **Framing correction is still important for r7.6 planning.** The prior ship judge listed "Mid-tool SIGTERM truncation (8 trials)" as failure mode #2 and recommended "Child-side SIGTERM research" as r7.6 agenda item #6. That recommendation is now wrong: SIGTERM wasn't involved. The correct r7.6 recommendation is "chat-template content normalization" (inv-2 G1) + "unmask the failure by routing to `(empty)` terminal so the problem is diagnosable."
- **Planning impact:** we are NOT "closer to the ship gate than it looked" (the arithmetic doesn't move), but we ARE "pointed at a much cheaper fix for 8 trials than we thought." Child-side SIGTERM handling (which would have required wrapper rewrites or Hermes-core signal-handler work) is NOT what these 8 need. A content-filter regex + fallback-path change is what they need. **That's a multi-day effort saved.**

---

## Part 4 — Priority order

### Recommended order

**1. inv-3 F3A′ (Gemma parser prefix-tolerant fallback)** — FIRST

- **Effort:** 30-45 min (~5 LOC across `run_agent.py` + `gemma_parser.py`, + 2-3 unit tests).
- **Leverage:** 3/3 coverage of mode-3 trials (recovers actual tool calls that are currently being emitted as text).
- **Risk:** VERY LOW. Pure parser relaxation. Backward-compatible.
- **Dependency:** none — can land standalone.
- **Why first:** the parser fix is a prerequisite to accurately re-judging mode-3 trials in any future probe. Without it, pseudo-tool-call trials remain mis-classified as content-level failures when they are actually parser-gate failures. Landing this first cleans the measurement surface for all downstream work.
- **Sub-recommendation:** combine the landing with inv-2's G1 into a single "Gemma-MoE chat-template correctness" worker dispatch (see Insight 1). They touch adjacent code.

**2. inv-2 G1 (channel-marker content-normalizer) + G2 (WORKER_EMPTY_SYNTHESIS verdict)** — SECOND

- **Effort:** 3-4h for G1 (upstream regex + turn-loop branch) + 2h for G2 (check.py). Combined 5-6h; unified with #1 potentially ~7h total for the "chat-template correctness" workstream.
- **Leverage:** reclassifies 8/20 trials (not fixes them — unmasks them). Makes the failure mode legible. Paves the way for inv-1 to have a cleaner baseline.
- **Risk:** LOW. Content-normalization regex is specific; edge cases surfaced by inv-2's open questions can be handled by widening the regex + verbose logging on rejection.
- **Dependency:** pairs naturally with #1 (same code surface); no hard dependency.
- **Why second:** structural/mechanical fix with clear evidence. Must land before inv-1's probe so the probe's "silent completions" become visible failures that inv-1's HERMES-WORKER.md can be fairly measured against.

**3. inv-4 F4A (fabrication detector in check.py)** — THIRD

- **Effort:** 1-2h (extend existing FABRICATION rule in check.py with new regex + tool-call-absence check; emit `VIOLATION:FABRICATION:NO_WRITE_TOOL`).
- **Leverage:** 2/2 coverage of mode-4 trials; cross-cutting (catches any future fabrication regardless of task or variant).
- **Risk:** LOW. No VM changes; regex tightened per inv-4 §F4A to require path+extension (not bare verbs).
- **Dependency:** none. Independent of #1 and #2.
- **Why third:** smallest scope, mechanical, sets a permanent floor against fabrication across all future probes. Should land before inv-1's probe so fabrication lift from F3A can be attributed to F3A (not to a pre-existing detector catching it).

**4. inv-1 F3A HERMES-WORKER.md** — FOURTH (the behavioral intervention)

- **Effort:** 4-6h prompt + source edit; behind a flag default-off for probe gating.
- **Leverage:** uncertain but potentially large. Targets the dominant thrash mechanism (H2A + H2B). Secondary claimed benefits for modes 3 and 4 are now re-attributed (mode 3 → inv-3's fix; mode 4 → inv-4's fix). Residual expected lift for mode 1 primary and mode 4 as an adjuvant.
- **Risk:** LOW-MEDIUM. Scaffolding-only; no architectural change. Needs smoke-test on non-probe delegation (Jira-briefing, etc.) to confirm no regression on real workloads.
- **Dependency:** SHOULD land after #1, #2, #3 so its effect is measured against a clean baseline. If it lands first, we cannot attribute the measured lift between "prompt did work" vs "inv-2 unmasked, inv-3 recovered, inv-4 detected."
- **Why fourth:** the only behavioral/scaffolding-layer fix in the bundle; campaign lesson says land structural first. Also benefits from the other three being in place (see Insight 5).

### Rejected ordering: inv-1 first

Inv-1 self-describes as the fix with the broadest reach. But its claimed cross-cutting benefits are over-stated (Part 2 Insights 2 & 3). Landing inv-1 first would:
- Conflate its scaffolding effect with inv-2/3/4's mechanical effects on a subsequent probe.
- Risk an "it worked because of HERMES-WORKER.md" false attribution.
- Leave modes 3 and 4 unfixed for longer (inv-3's 30-min parser fix is waiting).

**Correct order lands the easy-to-verify mechanical fixes first, then measures the prompt-layer fix as the residual.**

---

## Part 5 — Experiment bundle proposal

### Recommended: HYBRID

The three mechanical fixes (inv-3, inv-2, inv-4) have their correctness verifiable at the code level — unit tests + regex-match on stored session JSONs. They do not need a probe to attribute effects. Land them pre-probe.

The scaffolding fix (inv-1 F3A) affects model behavior and must be probed. Probe it against a baseline that already has the three mechanical fixes landed.

### Stage sequence

**Stage 0 (pre-probe, code-only):** Land inv-3 F3A′ + inv-2 G1/G2 as a single "Gemma-MoE chat-template correctness" worker dispatch.
- Deliverables: 2 source patches + 2-3 unit tests + check.py extension (G2).
- Validation: unit tests pass; replay all 20 r7.5 child session JSONs through patched check.py and confirm: (a) the 3 mode-3 trials produce recovered tool_calls; (b) the 8 mode-2 trials produce `VIOLATION:EMPTY_SYNTHESIS` verdicts; (c) none of the 5 other trials regress.
- Effort: 6-8h.
- Success criterion: code-verifiable. Pass/fail is deterministic.

**Stage 1 (pre-probe, code-only):** Land inv-4 F4A in check.py.
- Deliverables: check.py extension + regex constant + new violation verdict.
- Validation: replay 20 r7.5 child session JSONs; confirm 2 mode-4 trials emit `VIOLATION:FABRICATION:NO_WRITE_TOOL`; confirm 18 non-fabrication trials do not.
- Effort: 1-2h.
- Success criterion: code-verifiable.

**Stage 2 (probe):** Measure inv-1 F3A against Stage-0+Stage-1 baseline.
- Deliverables: HERMES-WORKER.md content file + `delegate_tool.py` patch behind env flag.
- Smoke-test: Jira-briefing dispatch + one readonly investigation dispatch must produce behaviorally-equivalent output with flag on.

### Probe matrix (Stage 2)

| Arm | Stage-0 fixes | Stage-1 fix | HERMES-WORKER.md | Purpose |
|-----|---------------|-------------|------------------|---------|
| **A (Baseline-clean)** | Applied | Applied | **Off** | Cleaned r7.5 baseline — pure comparable number for "what does the fleet look like with mechanical fixes only" |
| **B (F3A)** | Applied | Applied | **On** | Measures F3A's residual lift on top of mechanical fixes |

5 trials per task × 4 tasks (T4, T5, T6, T10) × 2 arms = **40 trials total.**

### Success criteria per arm

**Arm A expected outcome (re-baselined):**
- Mode 3 trials: 3/3 now parse correctly → likely +1 to +2 worker-quality PASSes (recovered tool_calls may lead to completed work).
- Mode 2 trials: 8/8 now show `VIOLATION:EMPTY_SYNTHESIS` (failure unmasked, not fixed) → net-zero PASS delta from this mode. But makes the failure diagnosable.
- Mode 4 trials: 2/2 now emit `VIOLATION:FABRICATION:NO_WRITE_TOOL` with same FAIL verdict as before → net-zero.
- Mode 1 trials: unchanged from r7.5.
- **Expected Arm A PASS rate: 4-5/20.** (3/20 baseline + 1-2 mode-3 recoveries.)

**Arm B expected outcome (F3A applied):**
- Mode 1 thrash: inv-1 estimates +5 of 6 trials flip → +5 PASSes.
- Mode 2 unmasked: HERMES-WORKER.md gives children a plan/stop/budget doctrine → some of these trials that currently fail at 3-10 turns may actually produce an honest-blocked summary. Plausible +2 to +3 PASSes.
- Mode 3 parser-recovered: residual lift from prompt quality on those trials: 0 to +1.
- Mode 4: F4A already catches; F3A's anti-fabrication line is adjuvant. 0 to +1 PASS.
- **Expected Arm B PASS rate: 11-15/20.**

### Per-arm PASS thresholds (pre-committed)

- **Arm A:** ≥ 4/20 (establishes the cleaned baseline; confirms mechanical fixes alone deliver a small lift).
- **Arm B:** ≥ 10/20 (doubles the baseline lift; below ship-gate 15/20 but materially closer).
- **Arm B - Arm A delta:** ≥ 5 trials (confirms F3A is doing real work beyond the mechanical cleanups).
- **HONESTY PASS on T10 in Arm B:** ≥ 4/5 (confirms anti-fabrication works in practice, complementing F4A detector).

### Tripwire gates

- Zero VM canonical drift in any trial.
- Arm A must not regress on non-probe workloads (Jira-briefing smoke-test).

### Why NOT a single 4-way combined probe

- Entangles effects across layers. Unable to attribute whether a PASS delta came from parser, content-filter, detector, or prompt.
- Makes failure diagnosis hard. If the probe lands at 7/20 instead of 11/20, we need to know which fix underperformed.

### Why NOT a 4-arm isolated probe

- Would be 4 × 20 = 80 trials plus a baseline-clean control = 100 trials. At ~10 min per trial that's 16+ hours of VM time.
- The three mechanical fixes can be verified without a probe (code + session-replay).

### VM time estimate

- Stage 0 + Stage 1: 0 hours VM time. All code + session-replay verification.
- Stage 2 probe: 40 trials × ~10 min per trial = **~7 hours VM time.** Plus orchestration + judging = ~9-10 hours total. Well within a single phase-1 probe session.

---

## Part 6 — r7.5 baseline re-score recommendation

**Recommendation: DO NOT formally re-score r7.5. Document the reframing in r7.6 docs and move on.**

Rationale:
- The arithmetic does not flip (0/8 reframed trials would PASS on re-judgment per Part 3). r7.5's 3/20 stands.
- The reframing is about *mechanism labels*, not *outcomes*. Changing "SIGTERM truncation" to "chat-template empty-synthesis" in the r7.5 aggregate doesn't change any PASS/FAIL.
- Re-scoring would create churn: new artifacts, updated cross-references, invalidated handoff docs. All for a labeling correction.
- r7.5's HOLD-narrow verdict is robust — see prior ship judge's stratified re-judgment of 7 trials (0/7 disagreement). Adding "oh, and also mode 2 was mis-labeled" doesn't move the verdict.

**What to do instead:**
- In r7.6 Phase 1 planning docs, add an explicit note: "r7.5's 'mode 2: SIGTERM truncation (8 trials)' was empirically reframed in r7.6 Phase 0 inv-2 as chat-template channel-marker leakage. See ARTIFACT-r7.6-inv-2-sigterm-truncation.md. The r7.5 aggregate numbers are unchanged by this reframing; the r7.6 fix path is however materially different."
- Update PLAN-r7.5.md's "r7.6 agenda" section (if any) to replace "Child-side SIGTERM research" with "Gemma-MoE chat-template correctness (inv-2 + inv-3 unified)."
- Cross-link this synthesis artifact from the r7.5 SHIP judge verdict as an addendum.

If the operator specifically requests a formal re-score artifact (say, for external communication or ship-gate arithmetic at the next threshold), issue `ARTIFACT-r7.5-baseline-reframed.md` with the 8-trial re-read table from Part 3.2 above. Either stance is defensible; the lightweight "acknowledge in r7.6 docs" route preserves momentum.

---

## Next-step concrete deliverables for operator

### What to approve (gate these decisions)

1. **Approve the priority order and staging** (Parts 4 & 5). Especially: do the three mechanical fixes (inv-3, inv-2, inv-4) land as pre-probe code changes before the F3A behavioral probe, yes or no?
2. **Approve the "unified chat-template correctness" framing** for landing inv-2 G1 + inv-3 F3A′ in one worker dispatch. This is a design judgment call — the code surfaces overlap but could also be landed as two separate patches if the operator prefers cleaner attribution per investigator.
3. **Approve the Arm A/B probe matrix** (40 trials total, not 80+). Pre-commit to the per-arm PASS thresholds (Arm A ≥ 4/20; Arm B ≥ 10/20; B−A delta ≥ 5).
4. **Decide r7.5 re-score: yes (formal artifact) or no (document in r7.6 planning only).** My recommendation: no; document only.

### What to dispatch next

**Worker dispatch #1 — "Gemma-MoE chat-template correctness" (implementation worker):**
- Scope: land inv-3 F3A′ parser patches + inv-2 G1/G2 content-normalizer + check.py `WORKER_EMPTY_SYNTHESIS` verdict as a single unified patch.
- Forbidden ops: no HERMES.md changes; no delegate_tool.py changes; no child-prompt changes.
- Side-effect budget: ~5 LOC in run_agent.py + ~10 LOC in gemma_parser.py + ~10 LOC in check.py + unit tests + 1 replay of 20 r7.5 session JSONs for verification.
- Expected artifact: a source-patch artifact + a verification artifact showing the 20 r7.5 trials re-classified correctly.

**Worker dispatch #2 — "F4A fabrication-detector extension" (implementation worker):**
- Scope: extend `probe-variantF-check.py` FABRICATION detection per inv-4 F4A spec.
- Forbidden ops: no VM changes.
- Side-effect budget: ~40 LOC Python + 1 regex-boundary audit for false-positives + 1 replay of 20 r7.5 session JSONs.
- Can run in parallel with dispatch #1 (different files, no shared state).

**Judge dispatch #3 — "Pre-probe verification" (fresh judge):**
- Scope: read both implementation-worker artifacts + the two replay outputs. Confirm: (a) all 3 mode-3 trials recover; (b) all 8 mode-2 trials emit `VIOLATION:EMPTY_SYNTHESIS`; (c) all 2 mode-4 trials emit `VIOLATION:FABRICATION:NO_WRITE_TOOL`; (d) no other trial's verdict changes unexpectedly.
- Gates the Stage-2 probe: if any dispatch-3 verification fails, iterate on the implementation before probing.

**Worker dispatch #4 — "HERMES-WORKER.md authoring + delegate_tool.py hook" (implementation worker, after #3 passes):**
- Scope: write HERMES-WORKER.md per inv-1 F3A spec + patch `_build_child_system_prompt` to prepend it behind env flag `HERMES_WORKER_PROMPT_OVERLAY=1`.
- Forbidden ops: no changes to Gemma parser; no changes to check.py; no changes to r7.5 baselines.
- Smoke-test gate: Jira-briefing dispatch with flag on must produce equivalent-quality output.

**Probe dispatch #5 — "r7.6 Phase 1 F3A probe" (probe worker):**
- Scope: run 40-trial matrix (Arm A + Arm B) per Part 5.
- Produces: 40 child-session JSONs + 40 per-trial artifacts + 1 aggregate artifact.

**Judge dispatch #6 — "r7.6 F3A ship-judge":**
- Evaluate Arm A PASS, Arm B PASS, and B−A delta against pre-committed thresholds.
- Recommend SHIP / HOLD / RETREAT for r7.6.

### Operator-gated decisions (not for me)

- **Ship-gate threshold after reframing:** the operator pre-committed 15/20 (75%) for worker-quality. Arm B is expected at 10-15/20. Does the operator soften the gate (to ~12/20) given the reframing shows we're actually ~4-5 trials closer than the r7.5 aggregate suggested for FIXABLE reasons? Or hold the 15/20 bar and plan for a further r7.7 probe?
- **Independent variantF canonicalization (from prior ship judge):** still on the table. Does this synthesis change anything? No — variantF is a parent-dispatch property, unrelated to child chat-template or child scaffolding. The prior recommendation to canonicalize variantF independently on r7.4's SHIP still stands.
- **r7.5 formal re-score:** my recommendation is "no formal artifact; document in r7.6 planning." Operator decides.

---

## Appendix — explicit handling of tensions between investigators

1. **inv-1 claims cross-cutting benefit for mode 3.** → REJECTED per Insight 2. Parser-layer fix is required; prompt cannot reach the oMLX boundary. Inv-1's HERMES-WORKER.md may produce coincidental pattern-match benefits but is not reliable.

2. **inv-1 claims cross-cutting benefit for mode 4.** → PARTIALLY ACCEPTED but downgraded. F4A's mechanical check is structurally superior. Inv-1's anti-fabrication line remains as a cheap adjuvant worth including in the prompt but not as the primary fix.

3. **inv-2 labels 8 trials as "productive children with polluted content."** → ACCEPTED on mechanism, REJECTED on implied outcome-lift. Children were genuinely incomplete; unmask doesn't rescue. 0/8 re-judged PASS.

4. **inv-2 recommends F2A Tier 3 SIGTERM handler.** → DEFERRED, not rejected. F2A is real infrastructure value for future runs where parents genuinely exceed 900s, but it does NOT fix the 8 r7.5 trials and should not be bundled with the r7.6 Phase 1 probe. File as r7.7+ work.

5. **inv-3 corrects "4/20 pseudo-tool-call" to "3/20; trial 20 reclassified out."** → ACCEPTED. Trial 20's content is `<channel|>` leakage + fabricated summary, not Gemma Format 1. This aligns with inv-4's inclusion of trial 20 in the fabrication cohort. Consistency check: inv-3 and inv-4 agree; the investigators cross-validated correctly.

6. **inv-4 notes campaign prior against language-only fixes.** → ACCEPTED and generalized. Applied to the ordering recommendation (Part 4): mechanical fixes first, scaffolding fix last and measured-on-cleaned-baseline.

7. **Sample-size concerns (inv-4 explicitly flags n=2/20).** → ACCEPTED. The Arm A/B matrix at 5 trials/task preserves the r7.5 power level. If fabrication shows up again at 2/5 T10 in Arm A, the pattern re-confirms; if 0/5, we learn the r7.5 incidence was noise. Either way, F4A detector is cheap enough to keep as a permanent floor.

No remaining unresolved tensions across the 4 investigations.
