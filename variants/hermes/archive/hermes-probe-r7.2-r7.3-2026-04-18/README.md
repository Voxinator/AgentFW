# Archive — Hermes Probe r7.2 + r7.3 (2026-04-18 / 2026-04-19)

This directory preserves 29 intermediate artifacts from the r7.2 (MoE A/B + drift investigation) and r7.3 (Layer 1+2 remediation attempt) probe rounds. All findings are consolidated into the canonical docs at:

- `variants/hermes/PROBE-RESULTS-r7.md` — methodology + r7/r7.2/r7.3 history with corrected numbers
- `variants/hermes/NEXT-STEPS.md` — revised priorities (Variant E ship-candidate withdrawn)
- `variants/hermes/IMPLEMENTATION.md` — install/rollback (unchanged from r7)
- `variants/hermes/DESIGN.md` — architecture (unchanged from r7)
- `HANDOFF-2026-04-19.md` (project root) — single-file handoff for fresh sessions
- `CHANGELOG.md` — r7.2 + r7.3 entries

Use the archive when you need raw evidence: per-trial session data, mid-probe judge reasoning, drift-investigation worker reports, remediation playbook source, revert histories. The consolidated docs cite this archive by filename.

---

## Headline outcome (corrected after Step A re-tally)

The r7 ship-candidate framing for Variant E (60% first-attempt / 80% final) was a measurement artifact. Strict on-disk re-tally on 2026-04-18 showed the true rate was 0/5 first-attempt, 1/5 final. r7.2 and r7.3 confirm the same level (~1/5 first-attempt across the harness). r7.3 attempted Layer 1+2 remediation (toolset restriction + escape-hatch removal stacked) and FAILED both pre-committed first-attempt thresholds (dense 1/15 vs ≥7/15; MoE 1/15 vs ≥4/15).

The architectural thesis (Gemma orchestrates AgentFW locally) is partially validated — dispatches do occur — but at much lower reliability than r7 reported. Layer 3 (β-fuse) implementation is the high-leverage next move; see `ARTIFACT-impl-3-beta-fuse-spec.md`. The terminal-binding probe-fidelity issue is the gating dependency before any further toolset-restriction work.

---

## Contents by phase

### Phase 1 — r7.2 dense + MoE A/B
- `ARTIFACT-probe-r7.2-dense.md` — dense leg v1 (with wrapper bookkeeping bugs)
- `ARTIFACT-probe-r7.2-dense-v2.md` — dense leg v2 (with fixed wrapper; the canonical dense baseline)
- `ARTIFACT-probe-r7.2-moe.md` — MoE leg (0/5 first, 5/5 final — striking retry-rescue asymmetry)
- `ARTIFACT-probe-r7.2-wrapper-fixes.md` — wrapper bug fixes (TIMEOUT 300→900, session-ID fallback, MODEL check via session JSON)

### Phase 2 — Drift root-cause investigation (5 parallel workers + judge)
Triggered when r7.2 dense appeared to regress from r7's claimed 3/5 to 1/5 first-attempt. Investigation revealed it was not a regression — it was a measurement artifact in r7's wrapper bookkeeping.

- `ARTIFACT-drift-investigation-alpha.md` — oMLX state + cache forensics. Verdict: oMLX clean.
- `ARTIFACT-drift-investigation-beta.md` — Hermes config + source integrity. Verdict: clean.
- `ARTIFACT-drift-investigation-gamma.md` — cross-session contamination check. Verdict: no contamination.
- `ARTIFACT-drift-investigation-delta.md` — live sampling-params verification + cache-corruption forensics. Found 263 `Cache base_size mismatch` warnings post-restart but did not prove causation.
- `ARTIFACT-drift-investigation-epsilon.md` — r7-vs-r7.2 session-JSON byte diff. **Critical finding: r7's "successful dispatch" sessions show same role-collapse pattern on disk as r7.2's "failed" sessions; r7's wrapper was generously counting SIGTERM-truncated outputs as dispatches.**
- `ARTIFACT-drift-judge-synthesis.md` — synthesis judge. Recommended Step A re-tally (which confirmed ε's reframe).

### Phase 3 — Step A: strict re-tally
- `ARTIFACT-drift-step-a-retally.md` — re-scored r7's persisted sessions under strict on-disk criterion (first tool call must be `delegate_worker` or `delegate_task`). r7 = 0/5 first-attempt, 1/5 final. **The "drift" was illusory; the "ship-candidate" framing was based on inflated wrapper-counted dispatches.**

### Phase 4 — r7.2 SKILL.md mutation reverts (Trial 9 hazard)
- `ARTIFACT-revert-r7.2-skill-md.md` — first revert (Trial 9 child worker patched SKILL.md via `patch` tool)
- `ARTIFACT-revert-r7.2-skill-md-v2.md` — second revert (Trial 9 main session patched SKILL.md via `skill_manage` tool, different mechanism, same target line)

### Phase 5 — r7.3 7-worker remediation diagnostic + design swarm
After r7.2 confirmed dense+MoE both at ~1/5 first-attempt, dispatched 7 parallel workers to diagnose root causes + design remediation candidates.

- `ARTIFACT-remediation-worker-alpha-prompt-anatomy.md` — system prompt assembly + attention geometry. Found HERMES.md buried at byte 29,839 of 36,684 behind 11.8KB skills index.
- `ARTIFACT-remediation-worker-beta-first-turn.md` — dense vs MoE first-turn byte diff. **Found dense and MoE fail differently: dense always emits a tool (often wrong); MoE often emits no tool at all (chatbot-mode).**
- `ARTIFACT-remediation-worker-gamma-retry-divergence.md` — retry-response analysis. **Dense isn't mis-reading correction; it's actively disagreeing and citing escape-hatch clauses.**
- `ARTIFACT-remediation-worker-delta-tool-surface.md` — 29-tool surface forensics. `delegate_worker` 3.5× smaller than adjacent `delegate_task`; 20:1 description-dilution against pro-use competitors.
- `ARTIFACT-remediation-worker-epsilon-toolset-restriction.md` — toolset-restriction experiment design (3 tiers).
- `ARTIFACT-remediation-worker-zeta-prompt-rewrites.md` — 4 HERMES.md/schema rewrite variants.
- `ARTIFACT-remediation-worker-eta-correction-rewrites.md` — 4 wrapper correction-text variants.
- `ARTIFACT-remediation-judge-theta-playbook.md` — synthesis judge. Recommended ε-T1+δ-reorder first; η-C2+ζ-R2 second; β-fuse third (architectural endgame).

### Phase 6 — r7.3 Wave-1 implementations + Wave-2 verification
- `ARTIFACT-impl-1-toolset-restriction.md` — Layer 1 implementation (file_readonly toolset on VM, wrapper TOOLSETS env-var passthrough). Smoke test PASSED with 6-tool surface.
- `ARTIFACT-impl-2-escape-hatch-removal.md` — Layer 2 implementation (HERMES-variantE.md sibling created, wrapper correction text tightened).
- `ARTIFACT-impl-3-beta-fuse-spec.md` — Layer 3 spec only (delegate_worker_v2 with classification+justification+goal as required args). NOT implemented; ready when L1+L2 fall short (which they did).
- `ARTIFACT-impl-4-soul-restructure.md` — SOUL.md / USER.md / MEMORY.md restructure analysis. 3 options (A reorder, B compress, C merge) with 8 user-decision questions.
- `ARTIFACT-wave2-verifier-judgment.md` — cold-context verifier of all 4 IMPL artifacts. Verdict: GO for Wave-3.

### Phase 7 — r7.3 Wave-3 probe execution
- `ARTIFACT-probe-r7.3-l1.md` — Layer 1 only probe (partial; 6/30 trials before worker context-exhausted; T4 dense 5/5 first-attempt suggested L1 worked, but `terminal` first-tool on T6 surfaced new escape mode and probe-fidelity issue).
- `ARTIFACT-probe-r7.3-l12-results.md` — Layer 1+2 stacked probe (34 trials, FAILED both first-attempt thresholds; new failure mode `role-collapse-via-todo` 11/30; T4 dense regressed L1-only 5/5 → L1+L2 1/5; **5 dense trials called `terminal` despite restriction = probe-fidelity blocker**).

### Phase 8 — Probe driver
- `probe-r7.3-l12-driver.sh` — sequential 34-trial driver for L1+L2 probe. Served its purpose; archived for reference.

---

## Chronology

```
2026-04-18 ~12:00 — r7.2 dense v1 ran (10 trials, wrapper bookkeeping bugs surfaced)
2026-04-18 ~13:25 — Trial 9 v1 mutated SKILL.md via patch (revert artifact a)
2026-04-18 ~14:00 — Wrapper bug fixes (TIMEOUT 300→900, session-ID fallback, MODEL check)
2026-04-18 ~14:30 — r7.2 dense v2 ran (10 trials, fixed wrapper; new SKILL.md mutation by Trial 9)
2026-04-18 ~15:25 — Trial 9 v2 mutated SKILL.md via skill_manage (revert artifact b)
2026-04-18 ~16:00 — r7.2 MoE leg ran (10 trials, MoE distinct failure mode confirmed)
2026-04-18 ~17:00 — r7.2 final judge synthesis
2026-04-18 ~18:00 — Drift investigation triggered; 5 workers dispatched in parallel
2026-04-18 ~19:00 — Drift judge synthesis: ε's session-byte-diff is the load-bearing finding
2026-04-18 ~19:30 — Step A re-tally: r7 strict = 0/5 first, 1/5 final. Drift was illusory.
2026-04-18 ~20:00 — r7.3 7-worker remediation playbook dispatched
2026-04-18 ~21:00 — Judge θ synthesis: L1+L2 first; β-fuse spec only; A2 + slot reorder later
2026-04-18 ~21:30 — Wave-1 IMPL workers (1: toolset restriction, 2: escape-hatch removal, 3: β-fuse spec, 4: SOUL restructure analysis)
2026-04-18 ~22:00 — Wave-2 verifier: GO
2026-04-18 ~22:30 — Wave-3 L1-only probe partial (6/30 trials, worker context-exhausted)
2026-04-18 ~23:00 — Pivot to Wave-3 L1+L2 stacked probe
2026-04-19 ~00:46 — L1+L2 probe complete: FAILED thresholds, role-collapse-via-todo + T4 regression + terminal probe-fidelity issue
2026-04-19 ~01:00 — Documentation consolidation + safety revert (HERMES.md back to canonical)
```

---

## How to use the archive

**If you need to verify a specific number** in the consolidated docs, find the matching trial artifact here. Each `ARTIFACT-probe-r7.X-*.md` has session paths, first-assistant-line snippets, tool-call sequences, and aggregate metrics.

**If you need to replay the drift discovery**, read in order:
1. `ARTIFACT-probe-r7.2-dense.md` (apparent regression)
2. `ARTIFACT-drift-investigation-{alpha,beta,gamma,delta,epsilon}.md` (5 parallel hypotheses)
3. `ARTIFACT-drift-judge-synthesis.md` (judge synthesis)
4. `ARTIFACT-drift-step-a-retally.md` (the dispositive measurement)

**If you need to understand the remediation playbook**, read in order:
1. `ARTIFACT-remediation-worker-{alpha,beta,gamma,delta,epsilon,zeta,eta}.md` (7 parallel investigations + designs)
2. `ARTIFACT-remediation-judge-theta-playbook.md` (ranked playbook)
3. `ARTIFACT-impl-{1,2,3,4}.md` (implementation/design artifacts)
4. `ARTIFACT-wave2-verifier-judgment.md` (verification)
5. `ARTIFACT-probe-r7.3-l1.md` and `ARTIFACT-probe-r7.3-l12-results.md` (probe results)

**If you need to understand a SKILL.md revert**, `ARTIFACT-revert-r7.2-skill-md.md` and `ARTIFACT-revert-r7.2-skill-md-v2.md` describe how surgical str_replace was used to revert Gemma's mutations using session-JSON-derived old/new strings as oracle.

**If you're adapting the probe infrastructure for the next round**, the wrapper + check.py at top level are current; the driver `probe-r7.3-l12-driver.sh` is here for reference. New probes should use either the wrapper directly or build a fresh driver per task shape.

---

## Do NOT modify archive contents

The archive is append-only. If a future probe round (r7.4, r8) produces its own artifacts, create a sibling directory (`archive/hermes-probe-r7.4-YYYY-MM-DD/` or similar) rather than adding to this one. Each archive directory is a self-contained snapshot of one probe round, frozen at the time of consolidation.

Rationale: integrity of the historical record matters. r7's wrong SHIP verdict was reversed in this round; we preserve both the original analysis (Path 4 verdict in `archive/hermes-probe-r7-2026-04-18/`) and the reframe (this archive's drift-investigation + Step A artifacts) as audit trail.
