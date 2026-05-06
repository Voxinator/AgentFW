# REPORT-skill-item9-n5 — skill-as-wrapper validation against r7.11 baseline

**Campaign:** skill-validation-2026-05
**Author:** John (operator) + harness; methodology guidance from Brian
**Dates:** 2026-05-03 to 2026-05-05
**Total trials:** n=14 across four tracks
**Status:** closed on finding
**Companion artifact:** harness, evidence, and per-trial archives at `variants/hermes/r7.9-research/r7.11/skill-validation-harness/`

---

## TL;DR

Skill-as-wrapper architecture (`r7-11-orchestrate` SKILL.md, replacing `hermes_multi.py` subprocess wrapper) was validated against r7.11 item-9's T6 fastapi+reportlab workload. **n=5 strict completion: 0/5; charitable: 1/5.** Below RC threshold (≥3/5 strict).

The campaign's central finding is **not** that the skill-as-wrapper architecture fails on T6 workloads, but that *teaching-level mechanisms produce form without substance* for behaviors load-bearing on synthesis-trust closure. Specifically: across all 14 trials with 4 different operator-prompt variants, the orchestrator never read `verified-state.json` between `verify_phase` returning and the next routing decision. PHASE LOOP step C (the state read) is taught in SKILL.md and skipped uniformly.

This maps to r7.11's larger pattern: synthesis-trust closure was achieved at the `verify_phase` boundary by making verification deterministic Python (not LLM judgment). The state-reading absence is the same pattern at a different surface — coordination between verify and dispatch needs deterministic enforcement, not LLM compliance with skill text.

**r7.12 design recommendation:** preserve skill-as-wrapper architectural shape; add deterministic enforcement at the tool-API level. Specific candidate: `verify_phase` auto-invokes a tier-4 whole-scaffold check when called for the last declared phase. Empirical validation of that specific fix is the next campaign.

---

## 1. Pre-committed thresholds (matches r7.11 item-9 rubric)

- **Strict completion:** content_verify reports 0 HIGH findings under consolidation rules (UNWIRED_API + UNWIRED_INLINE same-file → single HIGH; ≥2 TEST_STUB → single) AND every phase in `verified-state.json` reaches `verified_passed`.
- **Charitable completion:** strict, OR HIGH findings only on files whose tier-3.7 acceptance test exercises them.
- **RC threshold:** n=5 trials, ≥3/5 strict.
- **Adherence-clean:** all five adherence counts (sequential_loop_adherence, skipped_verify_phase_count, narrative_routing_count, partial_success_misreport, inappropriate_session_end_count) at zero.

Scoring tool: `content_verify.py` (canonical, unmodified from r7.11 baseline).
Score wrapper: `bin/score.sh` adds the all-phases-verified gate per Brian's RC-scoring call (2026-05-03).

---

## 2. Campaign metadata

- **Model:** `gemma-4-26b-a4b-it-8bit` (oMLX, native on Mac).
- **Python ABI:** 3.11.x in scaffold `.venv` matching Hermes `venv`.
- **Hermes:** v0.12.0 (stock), with John's compat patch on branch `compat/hermes-v0.12` (commit `b3f8b55`) and rc2 cherry-picked (commit `5af15a3`).
- **Skill:** `~/.hermes/skills/autonomous-ai-agents/r7-11-orchestrate/SKILL.md` (sha `9f20a821…`).
- **Scaffold (canonical):** Brian's `scaffold-baseline.tar.gz` (sha `9d0d08b7…`), extracted from `item8-trial-1-archive` pre-trial state.
- **Scaffold (variant):** `scaffold-baseline-consolidated.tar.gz` (sha `4e91…`), `src/export/{csv,json,pdf,formats}.py` replaced by single `src/export/serializers.py` stub.
- **Launch method:** `hermes chat -q "<prompt>" -s r7-11-orchestrate -m gemma-4-26b-a4b-it-8bit --max-turns N` via `bin/launch-q.py`. Same launch shape as `hermes_multi.py:354`.
- **Each trial archive:** scaffold post-state (`scaffold.tar` + uncompressed `scaffold-work/`), Hermes session JSON (filtered to orchestrator session), `verified-state.json`, `score.json`, `adherence.json`, `tui.log`, `manifest.json`.

---

## 3. Per-trial summary

Per Brian's call (2026-05-03): adherence reported for every trial including SUCCESS trials. A 5/5 strict outcome with 5/5 zero narrative_routing is a different reliability story than 5/5 strict with 5/5 narrative_routing > 0.

### Track A — orchestrator-skill on canonical scaffold (n=5)

| Trial | Wallclock | Marker | Strict | Charitable | seq | skip_vp | narr_route | inapp_end | partial_succ | state_reads | Mechanism |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 21m 9s | SUCCESS | FAIL | **PASS** | OK | 0 | 2 | 0 | no | 0 | UNWIRED_API HIGH on `src/auth/permissions.py` (tier-3 missed cross-file wiring; lucky stub-alignment got it wired during phase 2) |
| 2 | 27m 56s | ESCALATE | FAIL | FAIL | OK | 0 | 0 | 0 | no | 0 | verifier-gaming spiral: worker created `dummy_usage.py` then attempted `python3 -m src.export.dummy_usage` (denied/timeout); 5 phase-1 revisions before max |
| 3 | 24m 39s | ESCALATE | FAIL | FAIL | OK | 0 | 0 | 0 | no | 0 | verifier-gaming spiral + tool-confusion: `from hermes_tools import` execute_code spam; 7 phase-1 revisions; orchestrator concluded with "verifier is producing false-positive CAT1 errors" rationalization |
| 4 | 6m 56s | ESCALATE | FAIL | FAIL | OK | 0 | 0 | 0 | no | 0 | stdlib namespace shadowing: `src/export/csv.py` collides with stdlib `csv`; orchestrator correctly diagnosed but couldn't fix within sandbox |
| 5 | 21m 10s | none | FAIL | FAIL | OK | 0 | 1 | 0 | no | 0 | rationalize-and-trail-off: phase 1+2 verified_failed; orchestrator declared *"I am ignoring the defined-unused warnings… Phase 3 will resolve them"*; never dispatched phase 3; hit turn limit; no terminal marker emitted |

**Track A aggregate: 0/5 strict, 1/5 charitable, 0/5 adherence-clean.** Median wallclock 21m 10s. **state_reads = 0 across all 5 trials.**

Five distinct failure mechanisms, all tracing to PHASE 0's `ls -R <scaffold>` step anchoring authoring on observed scaffold stubs. The model produces `src/export/{csv,json,pdf}.py` split across all 5 trials regardless of run-to-run variance, because the scaffold's stub files exist at those paths and PHASE 0 fits its plan to them.

### Track B-2b-subproc — bootstrap-authored PLAN (n=1, hypothesis falsified)

| Trial | Wallclock | Marker | Strict | Charitable | content_verify_charitable | state_reads | Outcome |
|---|---|---|---|---|---|---|---|
| 1 (broken bootstrap) | 24m 11s | SUCCESS | FAIL | FAIL | FAIL | 0 | preserved as `trial-B-2b-subproc-1-broken-bootstrap`; bootstrap-plan.py prompt told session to read USER-PROMPT.md from disk + showed OBJECTIVE/PATHS template — both biased toward stub-fitting. Reproduced the orchestrator's failure pattern. Methodology bug. |
| 1 (corrected bootstrap) | 37m | SUCCESS | FAIL | FAIL | FAIL | 0 | bootstrap-plan.py rewritten to mirror `hermes_multi.py:_build_bootstrap_prompt` (USER-PROMPT inlined, brief instructions, no template). Bootstrap session still authored `csv.py`/`json.py`/`pdf.py` split. Hypothesis falsified: gemma-4-26b on v0.12 Hermes defaults to one-file-per-format Python convention regardless of authoring context. |

**Hypothesis tested:** Brian's 2b proposal that bootstrap-child PLAN authoring (USER-PROMPT-anchored, no scaffold ls) would produce consolidated decompositions and avoid the cross-phase wiring trap.

**Result:** falsified at n=1. Both authoring contexts (orchestrator-skill PHASE 0, bootstrap-child) produce identical PLAN shape (`csv.py`/`json.py`/`pdf.py` split). r7.11 item-9's consolidated `serializers.py` outcome (trials 5.1, 5.2, 5.5) is **not reproducible** by faithful bootstrap prompt replication in current environment.

Possible explanations (not isolated): model behavior shifted between April 2026 baseline and current setup; v0.12's larger tool surface (55 tools, 126 skills visible to bootstrap session) creates different authoring biases; system-prompt delta. **The campaign cannot rely on r7.11's lucky baseline outcomes; convention-driven authoring choices on gemma-4-26b dominate context-prompting.** Methodological humbling worth noting in r7.12 design discussions.

n=1 is sufficient because the hypothesis was structurally falsified: same shape PLAN → same downstream behavior. Trials 2-3 of 2b-subproc would test the orchestrator-mechanical-degradation pattern (separate observation), not the primary hypothesis.

### Track A-tier4 — operator-prompt tier-4 PHASE FINAL gate (n=5)

Operator-prompt addition: *"After all phases verified_passed and BEFORE emitting r7.11 SUCCESS, run `python3 content_verify.py {scaffold} --json` via terminal. If exit 1, dispatch corrective worker to fix HIGH findings, re-verify, re-run gate. Max 3 tier-4 rounds."*

| Trial | Wallclock | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Tier-4 invoked | Strict | Charitable | state_reads | Mechanism |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 38m | passed (7r) | failed (8r) | pending | n/a | no | FAIL | FAIL | 0 | tier-4 awareness induced over-effort on phase 1 (7 revs) → revision budget exhausted on phase 2 (8 revs) before reaching PHASE FINAL |
| 2 | 26m | failed (4r) | pending | pending | n/a | no | FAIL | FAIL | 0 | phase 1 spiral, ESCALATE on max revisions |
| 3 | 30m 20s | passed (2r) | passed (1r) | passed (1r) | passed (0r) | **yes** | **PASS** | **PASS** | 0 | **first strict pass in campaign.** Orchestrator-authored 4-phase PLAN (4th phase orchestrator-internal-cleanup); all phases passed; tier-4 fired; caught `unwired-inline` HIGH on `src/api/export.py`; orchestrator parsed JSON, dispatched targeted corrective, re-ran gate clean, emitted SUCCESS |
| 4 | n/a | passed (1r) | passed (1r) | failed (4r) | pending | no | FAIL | FAIL | 0 | got further than baseline (phase 1+2 quick); phase 3 spiral; first `inappropriate_session_end_count=1` since rc2 (orchestrator under tier-4 prompt pressure called legacy `end_session_for_handoff` at escalate path) |
| 5 | n/a | failed (5r) | pending | pending | pending | partial | FAIL | FAIL | 0 | phase 1 spiral; orchestrator started invoking content_verify proactively *inside* per-phase loop (not just at PHASE FINAL) — tier-4 awareness leaked into per-phase debugging |

**Track A-tier4 aggregate: 1/5 strict, 1/5 charitable, 0/5 adherence-clean.**

**Tier-4 mechanism, when invoked, works.** Trial 3 demonstrates the gate firing as designed: content_verify exit 1 with structured findings → orchestrator parses JSON → dispatches targeted corrective with finding category in context → corrective worker resolves the cross-file wiring issue → re-run gate exits 0 → SUCCESS.

**Tier-4 reach rate is the bottleneck.** 1 of 5 trials reached PHASE FINAL. Per-phase trap (the same Track A baseline failure) kills 4/5 trials before the gate can fire. The tier-4 prompt addition shifts but doesn't remove the per-phase failure surface; it appears to push the orchestrator into more aggressive per-phase wiring revisions (trial 1 phase 1 went from 1 rev baseline → 7 revs with tier-4 prompt) which exhausts revision budget elsewhere.

### Track A-tier4-cons — combined design (consolidated scaffold + tier-4 prompt) (n=3)

Consolidated-scaffold tar replaces `src/export/{csv,json,pdf,formats}.py` with single `src/export/serializers.py` stub. Tier-4 operator prompt unchanged from Track A-tier4.

Hypothesis: scaffold change reduces phase-1 trap frequency (fewer split-file CAT1 findings) → more trials reach PHASE FINAL → tier-4 gate fires → strict pass rate improves toward RC threshold.

| Trial | Wallclock | PLAN shape | Phase 1 | Phase 2 | Phase 3 | Tier-4 invoked | Strict | Charitable | partial_success_misreport | state_reads | Outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | timeout @ 90m | **consolidated** (`serializers.py` single-file phase 1) | **passed (2r)** | failed (worker iter budget) | pending | no | FAIL | FAIL | no | 0 | scaffold change worked on phase 1; phase 2 worker hit Hermes' 50/50 iteration ceiling; harness wall-clock killed before recovery |
| 2 | timeout @ 90m | consolidated | passed (4r) | passed (2r) | passed (0r) | no | FAIL | FAIL | no | 0 | all phases legitimately verified_passed; harness wall-clock fired during phase 3 cleanup work, before SUCCESS emission. **Phase 1 still required 4 revisions of CAT1 wiring-gaming** (`if __name__ == "__main__"` block added to `serializers.py` to satisfy AST analysis) — consolidation reduced finding count but not gaming behavior |
| 3 | 33m 20s | consolidated | passed (2r) | **failed (4r)** | passed (1r) | no | FAIL | FAIL | **YES** | 0 | **fabricated SUCCESS.** Orchestrator emitted `r7.11 SUCCESS` claiming "Phases: 3 verified_passed (plus 1 cleanup phase)". `verified-state.json` showed phase 2 verified_failed at the same instant. Orchestrator never read state, never invoked tier-4 gate, declared SUCCESS based on its own narrative tracking. |

**Track A-tier4-cons aggregate: 0/3 strict, 0/3 charitable, 0/3 adherence-clean.**

Three findings from this track:

1. **Consolidated scaffold reduces phase-1 trap frequency, as predicted.** 3/3 trials cleared phase 1 in 2-4 revisions vs Track A's 5-7 revision spirals. Brian's r7.12 scaffold-convention proposal is empirically supported on this dimension.

2. **Consolidated scaffold reveals new bottlenecks.** With phase 1 quick, complexity moves to phase 2 (which now bears API + permissions in one phase) and phase 3 (tests + docs). Trials hit Hermes' 50/50 worker iteration limit (trial 1) and the 90-min harness wall-clock (trials 1, 2). The combined-design wall-clock distribution is shifted higher than baseline.

3. **Tier-4 gate is bypassable.** Trial 3 produced the campaign's clearest §5b failure: fabricated SUCCESS marker emitted while a phase was still verified_failed. The orchestrator never read state, never invoked the gate it was instructed to invoke, and routed on its own narrative.

The combined design at n=3 produced 0/3 strict — *worse* than tier-4-alone (1/5). The expected gain from scaffold change was absorbed by new failure modes that the operator-prompt tier-4 doesn't address. This is the campaign's load-bearing finding for r7.12 design.

---

## 4. Stable findings across n=14

### state_reads = 0, every trial

Across all 14 trials in 4 tracks (Track A baseline 5 + B-2b-subproc 1 + tier-4 5 + combined 3), the orchestrator **never** read `verified-state.json` between `verify_phase` returning and its next routing decision. PHASE LOOP step C in SKILL.md says verbatim: *"state = read_file(scaffold_root + '/verified-state.json')"*. Across 4 different operator-prompt variants and 2 different scaffold variants, the orchestrator skipped this step every time.

This is not noise. It is a property of the orchestrator-skill architecture on this scaffold class.

### inappropriate_session_end_count = 0 (rc2 holds), 13/14 trials

rc2 (the `write_plan_md` json.dumps fix) holds across the campaign. Pre-rc2 pre-flight runs surfaced `end_session_for_handoff` calls correlated 3/3 with `write_plan_md` slice errors. With rc2, 13 of 14 trials show 0 inappropriate handoff calls. Single slip on tier-4 trial 4, attributed to prompt pressure during escalation flow.

### Per-phase failure mechanisms (Track A baseline)

5 distinct mechanisms across 5 trials:
1. UNWIRED_API HIGH despite SUCCESS marker (tier-3 cross-file wiring scope gap)
2. Verifier-gaming spiral via `dummy_usage.py` runtime-call-site fabrication
3. Verifier-gaming spiral + tool-confusion (`hermes_tools import` execute_code spam)
4. Stdlib namespace shadowing (`csv.py`/`json.py`/`pdf.py` vs Python stdlib)
5. Rationalize-and-trail-off (orchestrator declares intent to proceed, doesn't, hits turn limit, no marker)

All 5 trace to PHASE 0's `ls -R` anchoring authoring on scaffold stubs. The mechanism that *triggers* failure varies; the *underlying* condition is consistent.

### Orchestrator-blames-verifier rationalization

Track A trials 2 and 3 escalated with the orchestrator concluding the verifier was wrong rather than fixing the implementation:

> Trial 2: *"You may need to adjust the verify-config.json to ignore these specific CAT1 warnings or manually override the phase status in verified-state.json."*

> Trial 3: *"This is a known limitation of phased verification. Please manually verify the implementation in src/export/ and proceed to Phase 2."*

This is a distinct failure surface from synthesis-trust narrative-routing. The orchestrator is not lying; it is correctly identifying that it cannot satisfy the verifier within the path scope of phase 1, and proposing the operator change the rubric. The campaign cannot relax the rubric (verifier integrity is the architecture's whole point), so the rationalization terminates the trial. **r7.12 design needs to either close the cross-phase wiring tension at PLAN-authoring or revision-dispatch, or train the orchestrator to escalate-with-correct-action rather than escalate-with-rubric-relaxation-request.**

---

## 5. The central finding

Across 4 different operator-prompt variants — bare skill (Track A), bootstrap-then-skill (B-2b-subproc), skill+tier-4 prompt (Track A-tier4), skill+tier-4 prompt+consolidated scaffold (combined) — `state_reads=0` is invariant. The orchestrator does not read `verified-state.json` to ground routing decisions, regardless of what the operator prompt or scaffold tells it. The skill teaches the read; the model skips the read.

This is the campaign's load-bearing finding for r7.12 design.

It maps to a larger pattern from r7.11. Synthesis-trust closure was achieved at the `verify_phase` boundary by making verification deterministic Python (not LLM judgment). Tiers 1/2/3/3.5/3.7 are deterministic checks the orchestrator cannot influence by claim. The state-reading absence is the same pattern at a different surface — coordination *between* `verify_phase` and the next dispatch needs deterministic enforcement, not LLM compliance with skill text.

**Teaching-level mechanisms produce form without substance for behaviors load-bearing on synthesis-trust closure.** The orchestrator follows PHASE LOOP *form* (sequential dispatches, verify_phase per phase, no skipped verifies) but skips PHASE LOOP step C (the state read) — which is the step that closes the synthesis-trust property.

---

## 6. Methodological note — partial baseline reproducibility

r7.11 item-9's bootstrap-authored PLANs (trials 5.1, 5.2, 5.5) consolidated serializers into a single `src/export/serializers.py` module. The campaign's faithful bootstrap replication (B-2b-subproc) did not reproduce this consolidation. Possible causes (not isolated): model behavior shifted between April 2026 and 2026-05-04; v0.12 Hermes' larger tool surface biases authoring; system-prompt delta.

This means r7.11's baseline outcomes are partially environmental. The campaign's empirical conclusions are anchored on current Hermes/gemma; future work needs to account for variance across model/env, not rely on lucky baselines.

The finding does not invalidate r7.11's results. r7.11 measured what r7.11 measured. But comparisons against that baseline ("does the skill match the subprocess wrapper at the same point?") are conditional on conditions the skill validation cannot fully replicate.

---

## 7. Comparison to r7.11 item-9 (subprocess baseline)

| Metric | Subprocess wrapper (r7.11 item-9) | Skill-as-wrapper (this campaign) | Delta |
|---|---|---|---|
| Strict 5-trial pass rate | 3/5 | 0/5 | -3 |
| Charitable 5-trial pass rate | 5/5 (per r7.11 README) | 1/5 | -4 |
| Median wallclock | ~30 min (per r7.11 manifest entries) | 21m 9s (Track A baseline) / 30m 20s (tier-4) / N/A combined | comparable |
| state_reads in verify→dispatch coordination | n/a (subprocess wrapper reads state in bash code, not in LLM context) | 0/14 trials | architectural delta |
| Failure modes | F-2 (json.dumps), F-9 part C (scaffold convention), tier-3 false-positives in venv-isolated trials | 5+ (split-file CAT1 spiral, verifier-gaming, namespace shadowing, rationalize-trail-off, fabricated SUCCESS, etc.) | new surfaces specific to LLM-driven coordination |

The subprocess wrapper closed coordination boundaries with deterministic bash. The skill-as-wrapper opens them to the orchestrator's LLM judgment. **The state-reading absence is the cost of that opening.** The campaign argues that opening cannot be teaching-closed; it must be tool-API-closed.

---

## 8. r7.12 design recommendation

**Preserve skill-as-wrapper as the architectural shape.** The skill achieves the North Star Brian articulated — "Hermes is supposed to be the interface" — and removes the bash-wrapper dependency. r7.11 item-9 demonstrated subprocess wrappers can clear RC threshold; this campaign demonstrates the skill *cannot* via teaching alone. The architectural choice is between two failure-mode classes, both of which are addressable.

**Add deterministic enforcement at the tool-API level.** Specifically:

### 8a. Primary recommendation: `verify_phase` auto-invokes tier-4 on the last declared phase (option 2(b))

When `verify_phase` is called for the last phase in `verified-state.json:spec.phases` and that phase verifies_passed (or after `max_revisions`), it automatically runs a whole-scaffold content_verify-equivalent check before returning. The result is incorporated into `verified-state.json` as a tier-4 verdict.

The orchestrator's PHASE FINAL emission logic continues to live in skill text, but the gate runs deterministically — not because the orchestrator chose to invoke it. Whether the orchestrator emits SUCCESS or ESCALATE based on tier-4's verdict is its problem; the architecture *surfaces truth* at a deterministic boundary the orchestrator cannot avoid.

This is the closest design to r7.11's deterministic-verifier pattern: same shape, extended scope.

### 8b. Combine with state_token enforcement if 8a alone proves insufficient (option 2(a))

`verify_phase` returns a `state_token` (hash of `verified-state.json`). Subsequent `delegate_task` or PHASE FINAL emission must include the token in context; stale token forces re-read or call fails. Makes state-reading mechanically required, not optionally observed.

This addresses the §5b narrative-routing surface directly: the orchestrator cannot dispatch the next phase or emit a terminal marker without the architecture having received a fresh state read.

### 8c. Architecture-level rebuild (option 3, fallback)

Rebuild PHASE LOOP coordination in deterministic code (subprocess wrapper redux, but lighter — verify_phase + state machine in Python, orchestrator-LLM only handles delegate-context content). Reserve for case where 8a + 8b prove insufficient on follow-up empirical work.

### What's NOT recommended

- **Widening tier-3 to whole-scaffold scope.** Phase 1's tier-3 firing on unwired serializers before phase 2 wires them produces phantom findings → orchestrator enters verifier-gaming spiral on architecturally-correct work. Track A demonstrated this pattern even with current per-phase tier-3.
- **Skill-text additions teaching the orchestrator harder to read state.** Falsified at n=14 across 4 prompt variants. Teaching is bounded.
- **Scaffold convention change as a primary fix.** Combined-design data shows scaffold change alone (with tier-4 as operator prompt) reduces phase-1 traps but creates new failure surfaces. Useful as a secondary mitigation, not a primary fix.

### Empirical validation of the recommendation

The next campaign's first probe should re-run Track A's 5 trials with `verify_phase` patched per 8a. Predicted outcomes:
- If skill clears RC threshold (≥3/5 strict): r7.12 architecture validated; ship 8a.
- If skill remains <3/5 strict: 8a is necessary but not sufficient; layer in 8b (state_token).
- If skill remains <3/5 strict with both: deeper architectural issue; consider 8c.

Don't pre-commit; let the next campaign's data drive the choice.

---

## 9. Per-trial archive index

```
skill-validation-harness/archives/
├── trial-A-1/                        Track A baseline trial 1 (charitable PASS)
├── trial-A-2/                          ESCALATE (verifier-gaming spiral, dummy_usage.py)
├── trial-A-3/                          ESCALATE (verifier-gaming + tool-confusion)
├── trial-A-4/                          ESCALATE (stdlib namespace shadowing)
├── trial-A-5/                          NO marker (rationalize-trail-off)
├── trial-A-1-pre-fix/                Preserved: trial-A-1 first attempt before Hermes-venv dep fix
├── trial-A-tier4-1/                  Tier-4 probe trial 1 (ESCALATE phase 2 spiral)
├── trial-A-tier4-2/                    ESCALATE (phase 1 spiral)
├── trial-A-tier4-3/                    SUCCESS strict — only strict pass in campaign
├── trial-A-tier4-4/                    ESCALATE (phase 3 spiral; inappropriate_session_end=1)
├── trial-A-tier4-5/                    ESCALATE (phase 1 spiral; tier-4 leaked into per-phase loop)
├── trial-A-tier4-cons-1/             Combined-design trial 1 (timeout, worker iter budget on phase 2)
├── trial-A-tier4-cons-2/               TIMEOUT (all phases verified_passed but wallclock killed before SUCCESS)
├── trial-A-tier4-cons-3/               FABRICATED SUCCESS (partial_success_misreport=true)
├── trial-B-2b-subproc-1/             Bootstrap-authored PLAN, corrected bootstrap
├── trial-B-2b-subproc-1-broken-bootstrap/   Preserved: methodology bug evidence
└── prior-medians.json                Wallclock-median rolling state
```

Each `trial-*/` directory contains:
- `manifest.json` — trial metadata (track, model, scaffold sha, AgentFW commit, wallclock)
- `score.json` — content_verify findings + campaign verdict (strict/charitable + all_phases_verified_passed + campaign_findings)
- `adherence.json` — per-trial adherence scorecard (5 counts + sequential violations + dispatch counts)
- `verified-state.json` — final verifier state at trial end
- `session.json` — Hermes orchestrator session JSON (filtered to "Run r7.11" first user message)
- `tui.log` — full hermes chat -q stdout/stderr capture
- `scaffold.tar` + `scaffold-work/` — post-trial scaffold contents

Pre-flight evidence at `track-b-scaffolds/2b-bootstrap-child/` (3 sessions × {tui-log, session-json}) documents the rc2-correlation-with-end_session finding from before the campaign opened.

---

## 10. Track 2c — resume scenario (writeup from accidental preview)

Track 2c (mid-phase Ctrl-C resume) was scoped as a deliberate probe but the data was generated incidentally by Track A trial 5: turn limit hit mid-phase, no terminal marker emitted, scaffold left with phase 1+2 verified_failed and phase 3 pending. Skill currently has no resume path; `verified-state.json` is the durable state but the orchestrator-LLM does not have an entry-point semantic for "I'm resuming, here's where I left off."

What resume would need to handle:
- `verified-state.json` exists but final phase is non-`verified_passed`
- Scaffold contents reflect partial work (some phase paths populated, some untouched)
- Orchestrator must decide: revise the failed phase, re-dispatch a fresh worker, or escalate

Minimal change to add resume support: PHASE 0's first action becomes "if `verified-state.json` exists, parse it, set internal state to first non-passed phase, skip PLAN authoring; else (no state file) author PLAN as today." Subsequent PHASE LOOP iteration unchanged. Estimated ~30 lines of skill markdown.

Not built or tested in this campaign per Brian's call; documented from trial 5's archive. Becomes its own item if/when r7.12 adoption requires it.

---

## 11. Verdict

Skill-as-wrapper architecture below RC threshold for T6 capability-curve workloads via teaching-level enforcement of state-grounded routing. **0/5 strict, 1/5 charitable, 0/14 adherence-clean across all variants tested.**

The architectural shape is preserved; the specific implementation needs deterministic enforcement at coordination boundaries, not skill teaching. Specific candidate: `verify_phase` auto-invokes tier-4 on the last declared phase. Empirical validation of that fix is the next campaign.

The campaign's value is the isolation, not the strict pass rate. Skill validation came in below threshold; the campaign isolated *why* (state-reading absence, not skill-following or training-prior bleed) and surfaced a tractable r7.12 design constraint. r7.12 doesn't ship from this report; r7.12 design starts from this report.

---

*Report assembled 2026-05-05 from harness archives at `variants/hermes/r7.9-research/r7.11/skill-validation-harness/`. Independent re-scoring possible against preserved per-trial scaffold + session JSON + verified-state.json.*
