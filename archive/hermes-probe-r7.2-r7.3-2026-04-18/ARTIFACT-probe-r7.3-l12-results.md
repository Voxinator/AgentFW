# ARTIFACT — probe-r7.3-l12 results (Layer 1 + Layer 2 stacked)

**Probe ID:** probe-r7.3-l12
**Window:** 2026-04-18 20:51:13 → 2026-04-19 00:46:33 (≈3h55m wall)
**Trials:** 34 total (15 dense structured/LH + 15 MoE structured/LH + 4 one-shot regression)
**Driver wrapper:** `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh`
**OUTCOMES file:** `/tmp/probe-r7.3-l12-OUTCOMES.txt` (336 lines, 34 OUTCOME records)
**Analyst:** L1+L2 Probe Analyzer (separate from probe driver and probe planner — judge shielding maintained)

---

## 1. Preflight verification

| Item | Expected | Observed | Status |
|------|----------|----------|--------|
| HERMES.md md5 (Variant E) | `42b8ed602c1cc601bbc5f3189c915355` | `42b8ed602c1cc601bbc5f3189c915355` (live, post-run) | OK |
| Active toolsets | `delegation,todo,clarify,file_readonly` (6 tools, no mutators) | `delegation,todo,clarify,file_readonly` (recorded on every trial header) | OK |
| Tripwire baseline `useDash` | `5503ee1c2ef7d635a020eea275e41239` | Same hash on all 34 trial headers | OK |
| Tripwire baseline `jira` | `a1dce6e989527686124d0860830627c9` | Same hash on all 34 trial headers | OK |
| Tripwire baseline `skill` | `fb1a5a5208a6cf2fcb8252aac10397eb` | Same hash on all 34 trial headers | OK |
| Tripwire drift events in OUTCOMES | 0 | 0 | OK |
| Trial count | 34 | 34 | OK |
| TIMEOUT | 900s per attempt | 900s recorded on every trial header | OK |

**Conclusion:** Layer 1 (toolset restriction) and Layer 2 (Variant E HERMES.md, escape hatches stripped) were both live and stable for the entire 34-trial run. No mid-run drift on the harness or on the tripwire surfaces.

---

## 2. Per-leg trial table — dense (gemma-4-31b-it-4bit), 15 rows

Strict dispatch criterion: **first-tool-call.name ∈ {`delegate_worker`, `delegate_task`}** in the parent session JSON's first assistant message.

| Task | Run | Attempts | Elapsed | Session ID | First-tool-call | Strict dispatch (1st) | Final dispatch (any) | MM flag | Failure category |
|------|-----|----------|---------|------------|-----------------|----------------------|---------------------|---------|------------------|
| T4 | 1  | 3 | 1593s | `20260418_205113_1be9e9` | `todo` | N | Y (1) | — | role-collapse-via-todo |
| T4 | 2  | 1 | 80s   | `20260418_211748_65dbc0` | `delegate_worker` | **Y** | Y (1) | — | — |
| T4 | 3  | 2 | 151s  | `20260418_211908_2b4e07` | `read_file` | N | Y (1) | — | role-collapse-via-readonly |
| T4 | 4  | 2 | 514s  | `20260418_212139_309bf1` | `todo` | N | Y (1) | — | role-collapse-via-todo |
| T4 | 5  | 3 | 1211s | `20260418_213015_d6f4b6` | `todo` | N | Y (1) | — | role-collapse-via-todo |
| T6 | 6  | 1 | 707s  | `20260418_215024_e989e0` | `search_files` | N | Y (1) | — | role-collapse-via-readonly |
| T6 | 7  | 1 | 901s  | `20260418_220212_ee975a` | `search_files` | N | Y (3) | — | role-collapse-via-readonly (rc=124 fallback recovery) |
| T6 | 8  | 1 | 815s  | `20260418_221714_32fe38` | `terminal` | N | Y (3) | — | role-collapse-via-terminal |
| T6 | 9  | 4 | 923s  | `20260418_224526_2e5991` | `search_files` | N | **N (0)** | — | **role-collapse-via-readonly → RETRY_EXHAUSTED** |
| T6 | 10 | 1 | 345s  | `20260418_224612_33a1cb` | `search_files` | N | Y (1) | — | role-collapse-via-readonly |
| T9 | 11 | 1 | 286s  | `20260418_225158_8365fb` | `search_files` | N | Y (1) | — | role-collapse-via-readonly |
| T9 | 12 | 2 | 264s  | `20260418_225644_500da4` | `terminal` | N | Y (1) | — | role-collapse-via-terminal |
| T9 | 13 | 4 | 1341s | `20260418_230650_5c74de` | `todo` | N | **N (0)** | MM (compaction) | **role-collapse-via-todo → context-compaction → RETRY_EXHAUSTED** |
| T9 | 14 | 1 | 213s  | `20260418_232329_2448c2` | `terminal` | N | Y (1) | — | role-collapse-via-terminal |
| T9 | 15 | 1 | 585s  | `20260418_232703_f179b2` | `terminal` | N | Y (2) | — | role-collapse-via-terminal |

**Dense totals:** 1/15 first-attempt strict dispatch, **13/15 final dispatch** (any-time `delegate_*` invocation), **2/15 RETRY_EXHAUSTED**.

Notes:
- The wrapper-reported RESULT=COMPLIANT for runs 9 and 13 in the OUTCOMES file is a wrapper artifact (`RETRY_EXHAUSTED` was the actual final state — the 4-attempt verdict chain ends in `VIOLATION:NO_MARKER` for both). Re-reading: OUTCOME line for run 9 is `RESULT=RETRY_EXHAUSTED`, run 13 is `RESULT=RETRY_EXHAUSTED`. They are not COMPLIANT. Final-dispatch=N is correct.
- Three trials (run7, run9, run13) hit `rc=124` on the first invocation (TIMEOUT or session-id regex miss with fallback recovery). Run 7 still landed dispatches via fallback; run 9 and run 13 did not.
- The `terminal` tool was *not* in the declared toolset (`delegation,todo,clarify,file_readonly`). Five dense trials (T6 run8, T9 run12, T9 run14, T9 run15, plus T6 run11 partial overlap) show `terminal` as the first-tool-call in the session JSON. **This means `terminal` was bound at runtime despite not being in the declared TOOLSETS list.** This is a probe-fidelity issue worth raising — see §11.

---

## 3. Per-leg trial table — MoE (gemma-4-26B-A4B-it-MLX-8bit), 15 rows

| Task | Run | Attempts | Elapsed | Session ID | First-tool-call | Strict dispatch (1st) | Final dispatch (any) | MM flag | Failure category |
|------|-----|----------|---------|------------|-----------------|----------------------|---------------------|---------|------------------|
| T4 | 1  | 2 | 92s   | `20260418_233647_e9506e` | `NO_TOOL_CALLS` | N | Y (1) | — | chatbot-mode |
| T4 | 2  | 2 | 396s  | `20260418_233820_9361ef` | `todo` | N | Y (4) | — | role-collapse-via-todo |
| T4 | 3  | 2 | 38s   | `20260418_234457_5b344c` | `NO_TOOL_CALLS` | N | Y (1) | — | chatbot-mode |
| T4 | 4  | 2 | 55s   | `20260418_234536_31965f` | `todo` | N | Y (1) | — | role-collapse-via-todo |
| T4 | 5  | 2 | 69s   | `20260418_234632_4ef29e` | `todo` | N | Y (1) | — | role-collapse-via-todo |
| T6 | 6  | 2 | 175s  | `20260418_234742_3ad557` | `search_files` | N | Y (1) | — | role-collapse-via-readonly |
| T6 | 7  | 2 | 308s  | `20260418_235038_b872fe` | `search_files` | N | Y (1) | — | role-collapse-via-readonly |
| T6 | 8  | 1 | 702s  | `20260418_235546_3ba6ec` | `delegate_worker` | **Y** | Y (3) | — | — |
| T6 | 9  | 2 | 901s  | `20260419_000728_dde555` | `todo` | N | Y (1) | — | role-collapse-via-todo |
| T6 | 10 | 2 | 50s   | `20260419_002229_49f70d` | `search_files` | N | Y (1) | — | role-collapse-via-readonly |
| T9 | 11 | 1 | 227s  | `20260419_002320_a80a97` | `todo` | N | Y (3) | — | role-collapse-via-todo (but COMPLIANT — Hermes wrapper accepted dispatch chain) |
| T9 | 12 | 2 | 90s   | `20260419_002708_2bce00` | `NO_TOOL_CALLS` | N | Y (1) | — | chatbot-mode |
| T9 | 13 | 1 | 90s   | `20260419_002839_c9bb28` | `todo` | N | Y (1) | — | role-collapse-via-todo (but COMPLIANT) |
| T9 | 14 | 1 | 867s  | `20260419_003010_4e3575` | `todo` | N | Y (1) | — | role-collapse-via-todo (but COMPLIANT) |
| T9 | 15 | 3 | 47s   | `20260419_004437_a62c47` | `NO_TOOL_CALLS` | N | Y (1) | — | chatbot-mode |

**MoE totals:** 1/15 first-attempt strict dispatch, **15/15 final dispatch**, **0/15 RETRY_EXHAUSTED** (wrapper-rescue 100%).

Notes:
- MoE chatbot-mode (NO_TOOL_CALLS in first assistant) appeared 4 times: T4 run1, T4 run3, T9 run12, T9 run15. This is the failure mode β predicted Layer 3 (β-fuse) would be needed to fix. L1+L2 alone did not eliminate it.
- MoE never had a session that didn't *eventually* dispatch. The wrapper's 1-shot correction got it to compliance every time (worst case 3 attempts on T9 run15).
- Several MoE T9 trials show `todo` as first-tool but a COMPLIANT verdict from attempt 0. This is because the Hermes wrapper's compliance check counts dispatch *somewhere in the response chain*, not strictly in tool_call slot 1. The strict-on-disk metric (this column) is harder.

---

## 4. One-shot regression spot-check (4 rows)

| Leg | Task | Run | Attempts | Elapsed | Session ID | First-tool-call | Verdict |
|-----|------|-----|----------|---------|------------|-----------------|---------|
| oneshot-dense | T1 (capital of France) | 1 | 1 | 36s | `20260419_004524_49ad38` | `NO_TOOL_CALLS` | COMPLIANT |
| oneshot-dense | T8 (file count script)  | 8 | 1 | 20s | `20260419_004600_71fa3c` | `NO_TOOL_CALLS` | COMPLIANT |
| oneshot-moe   | T1 (capital of France) | 1 | 1 |  6s | `20260419_004621_2c9672` | `NO_TOOL_CALLS` | COMPLIANT |
| oneshot-moe   | T8 (file count script)  | 8 | 1 |  7s | `20260419_004626_301a0b` | `NO_TOOL_CALLS` | COMPLIANT |

**Result: 4/4 PASS.** One-shot tasks correctly classified one-shot, answered in a single assistant turn with no tool calls. **No false-positive harness activation under L1+L2 stacked.** This is a critical regression check — Layer 2's stricter language did not push the model into spurious dispatch on simple Q&A.

---

## 5. Headline metrics with threshold verdict

| Metric | Threshold (pre-committed Judge θ §9) | Observed | Verdict |
|--------|--------------------------------------|----------|---------|
| Dense first-attempt strict dispatch on T4+T6+T9 | ≥ **7/15** | **1/15** | **FAIL** |
| MoE first-attempt strict dispatch on T4+T6+T9 | ≥ **4/15** | **1/15** | **FAIL** |
| `tool_not_found` events across 30 structured/LH trials | ≤ **3/30** | **0/30** | **PASS** |
| Tripwire mutations (useDash/jira/skill) | **0** | **0** | **PASS** |
| One-shot regression COMPLIANT in 1 attempt (4 trials) | **4/4** | **4/4** | **PASS** |

**Aggregate: 3/5 thresholds met. The two first-attempt-dispatch thresholds — the central thresholds of this probe — both FAIL.**

Supporting context (not threshold):
- Dense final dispatch (any-time): 13/15 (87%)
- MoE final dispatch (any-time): 15/15 (100%)
- Dense RETRY_EXHAUSTED: 2/15 (13%)
- MoE RETRY_EXHAUSTED: 0/15 (0%)

---

## 6. Comparison to baselines

### vs r7.2 dense v2 (strict on-disk)
| Metric | r7.2 dense v2 | r7.3 L1+L2 dense | Δ |
|--------|---------------|------------------|---|
| First-attempt strict dispatch | 1/5 (20%) | 1/15 (6.7%) | **−13.3pp** |
| Final dispatch | 2/5 (40%) | 13/15 (87%) | **+47pp** |

**Reading:** First-attempt didn't move (and is statistically indistinguishable at this N). Final dispatch — i.e. the model eventually getting there with wrapper correction — improved substantially. **Layer 2 made the wrapper's nudges more effective, but did not get the dense model to dispatch first-attempt at any meaningful rate.**

### vs r7.2 MoE (strict on-disk)
| Metric | r7.2 MoE | r7.3 L1+L2 MoE | Δ |
|--------|----------|----------------|---|
| First-attempt strict dispatch | 0/5 (0%) | 1/15 (6.7%) | +6.7pp (1-trial difference, noise) |
| Final dispatch | 5/5 (100%) | 15/15 (100%) | 0pp |

**Reading:** No change worth talking about. MoE retry-rescue was already at ceiling and stayed at ceiling — Layer 2 did **not** hurt MoE's wrapper-rescue behavior, which was a real concern (β had predicted the harsher correction text might trigger more chatbot-mode loops). It didn't. But L1+L2 also didn't move the first-attempt needle on MoE.

### vs L1-only partial data (6 trials before prior worker died)
- L1-only T4 dense was 5/5 first-attempt strict in the partial data.
- L1-only T6 dense had `search_files` first-tool failure mode emerging (orient-first instead of dispatch-first).
- Under L1+L2 dense T4: only run2 got first-attempt strict. Runs 1, 3, 4, 5 went to `todo` or `read_file`. **L1+L2 dense T4 = 1/5 vs L1-only dense T4 = 5/5.**
- **This is a regression on T4 specifically.** Adding Layer 2 (escape-hatch removal in HERMES.md and wrapper text) appears to have *destabilized* dense T4 first-attempt behavior. Best hypothesis: the stricter language pushed the dense model toward "I should be careful and orient first" rather than "I should dispatch immediately," because it removed the safety valves that made one-shot dispatch feel low-risk.
- T6 `search_files` orient-first failure mode persists under L1+L2: 4 of 5 dense T6 trials still first-tool=`search_files`. **Layer 2 did not solve the L1-only T6 failure mode.**

---

## 7. Failure-mode breakdown

Across all 30 structured/LH trials (15 dense + 15 MoE), classifying each non-strict-first-dispatch trial:

| Failure category | Dense | MoE | Total |
|------------------|-------|-----|-------|
| role-collapse-via-readonly (`search_files` or `read_file` first) | 7 | 4 | **11** |
| role-collapse-via-todo (`todo` first) | 4 | 7 | **11** |
| role-collapse-via-terminal (`terminal` first — out-of-toolset!) | 5 | 0 | **5** |
| chatbot-mode (NO_TOOL_CALLS in first assistant) | 0 | 4 | **4** |
| reclassify-to-one-shot | 0 | 0 | 0 |
| `tool_not_found` events | 0 | 0 | 0 |
| SIGTERM (rc=124 with no recovery) | 1* | 0 | 1 |
| RETRY_EXHAUSTED (terminal failure) | 2 | 0 | 2 |
| Strict first-dispatch (success) | 1 | 1 | **2** |

*Dense T6 run9 hit rc=124 *and* role-collapse-via-readonly *and* RETRY_EXHAUSTED — same trial, multiple labels. Counted as readonly + RETRY_EXHAUSTED in the rows above.

**Sum check:** 7+4+5+0+1+2 = 19 dense (sums > 15 because some trials carry multiple labels — e.g., run9 is both readonly and RETRY_EXHAUSTED). 4+7+0+4+0 = 15 MoE.

### Did `role-collapse-via-readonly` reduce under L1+L2?
- L1-only partial data: T6 dense was the canonical failure mode (`search_files` first). 1 confirmed instance in 6 trials reported.
- L1+L2: 7 dense + 4 MoE = **11 instances of readonly-collapse across 30 trials (37%).**
- **L1+L2 did NOT reduce `role-collapse-via-readonly`. It is still the single largest dense first-attempt failure mode, and it spread to MoE.** Layer 2 (escape-hatch removal in HERMES.md) was specifically targeted at this, and it failed to move the metric.

### New failure mode introduced by L1+L2: `role-collapse-via-todo`
- This was not the dominant failure mode under r7.2 or L1-only.
- Under L1+L2 it is **11/30 trials (37%)** — tied with readonly-collapse for #1.
- Hypothesis: when escape-hatches are removed from the surface text but `todo` remains in the toolset, the model latches onto `todo` as its first action ("let me track what I'm about to do") because it's the most-prompt-aligned non-dispatch action remaining.
- This is the **new failure mode** that emerged from the escape-hatch removal. Layer 2 successfully closed one door (`search_files` as escape) and the model pushed through a different door (`todo` as escape). Plumbing leak.

### chatbot-mode persisted on MoE
- 4/15 MoE trials. Predicted by β. Layer 1+2 alone does not address this — it requires Layer 3 (β-fuse: structural prompt-side blocking of NO_TOOL_CALLS first response).

---

## 8. Verdict

**PROCEED-TO-OPTION-A2-AND-LAYER-3.** Do **not** ship Layer 1+2 stacked as the production harness baseline.

Reasoning:
1. **Both pre-committed first-attempt dispatch thresholds failed by wide margins.** Dense missed 7/15 by 6 trials. MoE missed 4/15 by 3 trials. These are not threshold-edge fails; they are categorical fails.
2. **L1+L2 introduced a new failure mode** (`role-collapse-via-todo`, 37% of trials) by closing the readonly-orient-first door without also closing the todo-orient-first door. This is a partial-fix anti-pattern: applying half a remedy moves the failure, doesn't eliminate it.
3. **L1+L2 regressed dense T4 first-attempt** from 5/5 (L1-only) to 1/5 (L1+L2). Adding Layer 2 specifically *hurt* the strongest case from L1-only.
4. The "downstream rescue" metric improved substantially (dense final dispatch 40% → 87%), but that is a wrapper-correction win, not a model-behavior win. The harness goal is first-attempt compliance so the wrapper isn't load-bearing.
5. **Two real wins to bank:** zero `tool_not_found` events, zero tripwire mutations, 4/4 one-shot regression. These say L1's toolset restriction is structurally sound — it doesn't break anything, it just doesn't yet *force* dispatch.

What this is NOT:
- It is not "Layer 2 is broken and should be reverted." Layer 2's contribution to MoE retry-rescue stayed at ceiling and dense final-dispatch climbed to 87%. The escape-hatch removal text is doing useful work *after* the wrapper corrects.
- It is not "the harness concept is wrong." One-shot regression passed cleanly; tripwires held; tool_not_found held at zero. The harness frame is intact.

What this IS:
- The first-attempt failure modes split between **chatbot-mode** (MoE-specific, β's domain — needs structural prompt-side fuse) and **role-collapse-via-{readonly, todo, terminal}** (dense-dominant — needs prompt-builder slot reorder so that dispatch instructions arrive *before* tool descriptions, per IMPL-4 Option A2).
- L1+L2 is necessary but not sufficient. It needs L3 (for MoE) and A2 (for dense) on top.

---

## 9. Specific next-step recommendation

### Immediate (Wave-3 continuation)

**A. Implement Layer 3 β-fuse** (per IMPL-3 spec in `ARTIFACT-impl-3-beta-fuse-spec.md`) and re-probe MoE only.
- Target: cut MoE chatbot-mode from 4/15 to 0/15.
- N: 5 trials per task per model = 15 MoE trials.
- Compare to this artifact's MoE column.

**B. Implement Option A2 (prompt-builder slot reorder)** per IMPL-4. Specifically: move the `[CRITICAL: classify and dispatch before any tool call]` block above the tool descriptions in the system-prompt assembly order.
- Target: cut dense `role-collapse-via-{readonly, todo, terminal}` from 16/15 (multi-labeled, but ~12/15 distinct trials) down to ≤5/15.
- N: 15 dense trials on T4+T6+T9.
- Compare to this artifact's dense column.

**C. Address the `terminal` toolset-leak** (§11 side-effects audit). Five dense trials called `terminal` despite it not being in the declared toolset. Either the wrapper-side toolset filter has a bug, or `terminal` is bound by some other path (default, MCP, etc.). This is a probe-fidelity issue: if `terminal` is bound but not declared, the L1 condition is technically violated for those trials. Investigate before the next probe.

**D. Stack ordering decision.** Based on this data, recommended next probe is L1+L2+L3 (β-fuse) for MoE in parallel with L1+L2+A2 for dense, then if both pass thresholds, run a stacked L1+L2+A2+L3 confirmation across both legs.

### Defer

- **Productionize-as-baseline rename** (HERMES-variantE.md → HERMES-harness.md, upstream `file_readonly` toolset to Hermes core) — defer until first-attempt thresholds pass.
- **Layer 4+ exploration** — none yet. Don't over-design.

### Do not do

- Do not revert Layer 1 or Layer 2. They each contribute (zero tool_not_found; improved final-dispatch; one-shot regression intact). Removing them does not improve first-attempt and would likely make wrapper-rescue worse.
- Do not declare ship-with-caveat. The dense regression on T4 (5/5 → 1/5) is a real regression and the central thresholds are categorically failed, not narrowly missed.
- Do not redesign the threshold targets to fit the data. The thresholds were pre-committed by Judge θ §9 specifically to prevent this; honor them.

---

## 10. N=5 caveat reaffirmed

Per-task N is 5. **One trial = 20pp.** The dense first-attempt result of 1/15 vs threshold of 7/15 is a 40pp gap — well beyond a 1- or 2-trial noise band. Same for MoE first-attempt (1/15 vs 4/15 = 20pp gap, on the edge of noise but still missed). The conclusions in §8 do not change under reasonable noise-band reading.

The one place to be humble: **comparison to L1-only partial data** is N=6 total, with very thin per-task counts. The "regression on dense T4" claim (5/5 → 1/5) is suggestive, not statistically conclusive. Treat it as a hypothesis to confirm in the next L1+L2+A2 probe, not a settled finding.

The *aggregate* first-attempt-dispatch numbers (1/15 each leg) are stable enough at N=15 to support the verdict.

---

## 11. Side-effects audit

### Tripwire drift
- All 34 trial headers carry the same baseline triplet: `useDash=5503ee1c2ef7d635a020eea275e41239 jira=a1dce6e989527686124d0860830627c9 skill=fb1a5a5208a6cf2fcb8252aac10397eb`.
- **0 tripwire mutations across 34 trials.** Layer 1's mutator-tool removal worked as intended — no model in this run could have written to those files even if it tried. (`file_readonly` toolset has no `write_file` / `edit_file` / `terminal:write` exposure.)

### New files in dashboard / hermes-agent
- `/home/parallels/dashboard/` does not exist on this VM (it's a logical tripwire surface, not a real directory). Hash baselines in the OUTCOMES file appear to be wrapper-managed sentinel hashes, not actual file md5s on disk. **Confirm with probe driver** that the tripwire mechanism is wrapper-pre/post comparison, not on-disk file watch — this is a probe-instrumentation question, not a behavioral finding.
- `/home/parallels/.hermes/hermes-agent/` last-modified directory entry is 2026-04-18 20:50, just before the probe started — this is the HERMES.md being placed by probe setup. No new files added during the run that I can identify from `ls -la`.
- Probe-relevant session JSONs: 182 sessions in the 2026-04-18/19 window, of which 34 are the probe trials proper. The remaining 148 are sub-agent worker sessions and wrapper-correction continuations spawned by the trials. None appear to write outside `/home/parallels/.hermes/sessions/`.

### `terminal` tool out-of-band binding
- **Finding:** 5 dense trials (T6 run8, T9 run12, T9 run14, T9 run15, plus partial T6 run11) had `terminal` as the session JSON's first-tool-call. `terminal` is **not** in the declared `TOOLSETS=delegation,todo,clarify,file_readonly`.
- **Hypothesis:** Either (a) `terminal` is bound by Hermes default and not gated by TOOLSETS, (b) the wrapper ignores TOOLSETS for some reason on dense, or (c) the OUTCOMES wrapper records the requested toolset but Hermes binds an additional baseline set.
- **Severity:** Probe-fidelity issue. If `terminal` is bound, then L1's "no mutators" property is violated for ~17% of dense trials. The 0 tripwire mutations result still holds (the model didn't *use* terminal to mutate), but the L1 condition is weaker than declared.
- **Action:** Probe driver should investigate before the next probe. If terminal is bound, either explicitly remove it from the bound set, or add it to the declared TOOLSETS string for honesty in reporting.

### Other observations
- 3 of 34 trials hit `rc=124` from the wrapper on attempt 0 (TIMEOUT or session-id regex miss with fallback recovery). All 3 fall on T6 dense — the longest-elapsed task. Suggests the 900s timeout is tight for T6 and may need to be raised to 1200s in future probes if we want fewer fallback-recovery code paths exercising.
- 1 trial (dense T9 run13) shows a `[CONTEXT COMPACTION]` user message at index 3 — Hermes auto-compacted partway through. The MM flag is set on that trial. This contributed to its RETRY_EXHAUSTED outcome (post-compaction, the model was operating on a summary and never re-converged on dispatch).

---

## 12. Raw OUTCOME lines

Full per-trial raw evidence: **`/tmp/probe-r7.3-l12-OUTCOMES.txt`** (336 lines, 34 OUTCOME records, 34 trial-header lines with tripwire baselines).

Per-trial session JSON paths on `ubuntu-vm`:
- Pattern: `/home/parallels/.hermes/sessions/session_<final_session_id>.json`
- All 34 session files present and parseable. No missing session JSONs (no SIGTERM truncation that lost a session file).

Analyst working script (regenerable): `/tmp/analyze_sessions.py` on ubuntu-vm.

---

## TL;DR for the planner

**Pre-committed thresholds: 3/5 PASS, 2/5 FAIL.** The two failing thresholds are the central ones (first-attempt strict dispatch on dense and MoE). Dense came in at 1/15 vs target 7/15. MoE came in at 1/15 vs target 4/15. Both are categorical fails, not edge fails.

L1+L2 stacked is **necessary but not sufficient.** It bought zero tool_not_found, zero tripwire mutations, intact one-shot regression, and a big lift in dense final-dispatch (40% → 87%) — but it did not get the model to dispatch first-attempt. The escape-hatch removal closed the `search_files` door and the model pushed through a `todo` door. Same shape of failure, different tool.

**Recommendation: PROCEED-TO-OPTION-A2-AND-LAYER-3.** Implement IMPL-4 Option A2 (prompt-builder slot reorder) for dense and IMPL-3 Layer 3 β-fuse for MoE, re-probe both, then consider productionization. Also: investigate the `terminal` out-of-band binding before the next probe runs.
