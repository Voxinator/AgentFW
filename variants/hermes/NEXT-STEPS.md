# Hermes-flavored AgentFW — Next Steps

**Purpose:** Session-handoff doc. A fresh agent or human picking up this work cold should be able to act on this doc + `DESIGN.md` + `INSTALL.md` + `DEPENDENCIES.md` + `PROBE-RESULTS-r7.md` + the r7.2 / r7.3 / r7.4 / r7.5 ARTIFACT-* files in the repo root alone.

---

## State at handoff (2026-04-19 end of r7.5 pre-release prep)

The r7.5 pre-release to GitHub is published as `r7.5-hermes-prerelease`. See `/RELEASE-NOTES-r7.5-hermes-prerelease.md` for the authoritative release notes.

**r7.5 verdict:** HOLD-narrow per `ARTIFACT-r7.5-SHIP-judge-verdict.md`. Dispatch missed the floor by 1/20 (16/20 vs 17/20, within r7.4 empty-first-turn variance); worker-quality ship gate failed decisively (3/20 vs 15/20 floor) on an orthogonal child-execution problem that β-fuse was never designed to solve. The β-fuse dispatch thesis remains intact — v2-adoption 20/20 (100%); the 4 first-attempt misses recovered cleanly via the correction loop with the same `messages[1]` empty-turn signature observed in r7.4.

**r7.5 what shipped as code (previously landed in this session's repo):**
- `probe-variantG-stage.sh` — r7.5 turn-0 toolset restriction hook stager. Layers on top of `probe-variantF-stage.sh`.
- `probe-variantG-wrapper.sh` — r7.5 wrapper with Tier-1 SIGTERM content-match recovery (`--expected-prompt-prefix-b64`) and `TIMEOUT_PER_TURN` env-override support.
- `probe-variantG-check.py` — r7.5 analyzer with `ERROR:WRONG_SESSION` verdict for mis-attached child sessions and base64 prompt-prefix decoding.
- `probe-omlx-health-check.sh` — Mac-side oMLX health probe.
- VM-side: `_resolve_tools_for_turn_r75a` in `run_agent.py` (unstaged at return to canonical).

**r7.5 what shipped as documentation (this session):**
- `/RELEASE-NOTES-r7.5-hermes-prerelease.md` (new, top-level)
- `variants/hermes/INSTALL.md` (new — authoritative install procedure, supersedes `IMPLEMENTATION.md`)
- `variants/hermes/DEPENDENCIES.md` (new — exact tested versions)
- `variants/hermes/DESIGN.md` (refreshed for variantF + turn-0 architecture; prior version described r7 variantD state)
- `variants/hermes/NEXT-STEPS.md` — this section added
- `README.md` — Hermes variant status callout + corrected r7.1 numbers
- `metadata.json` — version bump to 7.5.0 with `hermes_variant_status`
- `CHANGELOG.md` — r7.5 entry added

**VM state at handoff:** CANONICAL. HERMES.md md5 `0780c232a6cb52e13e432261f0d68ad9`. variantF and variantG both UNSTAGED (backup files `.probe-r7.4-orig`, `.probe-r7.5-orig` preserved for re-staging). All three tripwires (SKILL.md, jira-briefing.sh, useDashboard.ts) canonical. The Monday 8am Jira cron runs against canonical HERMES.md until operator authorizes a swap.

---

## r7.6 agenda (address the 4 worker-quality failure modes)

Per `ARTIFACT-r7.5-SHIP-judge-verdict.md` Part 5. Six workstreams; prioritized by expected worker-quality lift per hour of work.

### W1 — Child-session contract scaffolding (highest expected lift)

- **What:** a `HERMES-WORKER.md` analog injected into child sessions teaching honest-blocked return, no-fabrication-without-write discipline, and pre-budget-exhaustion summary turns. Analogous to how `HERMES-variantF.md` teaches parents.
- **Addresses:** fabrication (2 T10 trials), turn discipline (~7 trials), possibly pseudo-tool-call emission.
- **Why W1 not W2:** the contract is the thing children are missing entirely today (they inherit the full toolset and no harness instructions). Tool scoping alone won't teach them to stop and report blocked.
- **Impl surface:** Hermes child-dispatch path — inject worker contract as part of child's system prompt in `_delegate_task`.

### W2 — Child-toolset restriction

- **What:** by default bind reduced toolset for dispatched children — e.g. `file_readonly,terminal,todo,clarify,write_file,patch` — with `search_files` gated behind explicit escalation. Analogous to the r7.5 turn-0 hook but applied to child sessions, not parent turn 0.
- **Addresses:** search_files thrash (7 trials). Compounds with W1.
- **Impl surface:** `run_agent.py` child-spawn site; probe with a new `probe-variantH-*` harness layered on top of G.

### W3 — Turn-budget tuning for long-horizon

- **What:** for `classification=long-horizon`, increase child `--max-turns` from 20 to 30.
- **Addresses:** T6/T10 budget exhaustion where the child was converging but hit the cap.
- **Impl surface:** wrapper env override + default bump in `probe-variantH-wrapper.sh`. Cheap; ~20 min + probe time.

### W4 — Anti-fabrication post-trial guardrail

- **What:** judge-layer or wrapper-layer post-check: if child summary contains `/(?:created|generated|wrote) [^.]+(file|dir|script|plan|doc)/i`, verify at least one `write_file` / `patch` / `terminal` tool call with matching target appears in transcript. If not → automatic HONESTY=FAIL.
- **Addresses:** 2 T10 trials; arguably the worst failure mode because the child presents work confidently.
- **Impl surface:** `probe-variantH-check.py`; no Hermes-side change required.

### W5 — Pseudo-tool-call detection

- **What:** Hermes-layer response-schema enforcement — if `assistant.content` contains literal `<tool_call|>` or `call:<name>{`, surface as parse error and retry with correction message. Same pattern as r7.5 turn-0 NO_MARKER correction loop.
- **Addresses:** 3 pseudo-tool-call trials. Model-side tool-format regression specific to certain prompt-turn states on MoE.
- **Impl surface:** `run_agent.py` assistant-response handler (new parse gate + correction injection).

### W6 — Child-side SIGTERM research (Tier 3 Hermes handler)

- **What:** mirror the r7.4 parent-side investigation for child sessions. Likely same root cause. B3 Tier-3 upstream Hermes signal handler (deferred from r7.5) becomes more attractive with child-side SIGTERM evidence.
- **Addresses:** 8 mid-tool SIGTERM truncation trials (biggest failure-mode cluster).
- **Impl surface:** upstream Hermes PR candidate. Spec in `ARTIFACT-r7.4-sigterm-research.md`.

---

## Operator decision tree

Three live decisions, independent of the r7.6 agenda:

### D1 — Canonicalize variantF now or wait?

Per r7.5 ship judge Part 5: **r7.4 SHIP-WITH-CAVEAT for variantF is not retroactively weakened by r7.5's worker-quality HOLD.** Worker quality wasn't measured in r7.4. r7.5's dispatch numbers are indistinguishable from r7.4 within-sample; the worker-quality failure is on a separate axis (child execution) that β-fuse was never designed to address.

- **Option A — swap canonical variantF now.** Jira cron exercises dispatch-layer improvement. Rollback is single-command unstage. Recommended if the operator's production use case is dispatch-only (not child-quality-sensitive) or if the canonical swap is the way to accumulate additional evidence under production load.
- **Option B — hold canonical at `0780c232…`.** Wait until r7.6 closes worker-quality gate. Recommended if production use case exercises child execution heavily, or if operator policy is "both dispatch and worker quality must clear."

### D2 — Which r7.6 workstreams in what order?

Recommended ordering (by expected lift per hour):

1. W1 (child scaffolding) — highest expected lift; prerequisite for meaningful W2 measurement
2. W3 (turn budget) — cheap; run alongside W1
3. W2 (child toolset restriction) — compounds with W1; needs W1 to know what behavior the toolset is pushing children toward
4. W4 (anti-fabrication) — orthogonal; ship in parallel
5. W5 (pseudo-tool-call detection) — orthogonal; ship in parallel
6. W6 (child SIGTERM Tier 3) — biggest absolute surface but requires upstream coordination; longest path

W1 + W3 + W4 is the minimal "get worker quality above 50%" bundle; W2 + W5 closes to ~75%; W6 unlocks the remaining 25% at the cost of upstream-Hermes work.

### D3 — Upstream `delegate_worker_v2` to Hermes?

Optional. If the operator wants v2 to land in upstream Hermes rather than stay as a variants-only patch, see NEXT-STEPS Priority 4 below (unchanged since r7.4). Not on critical path.

---

## Legacy sections below (r7.4 state at handoff)

- **Variant F is a ship-candidate with caveats.** r7.4 Phase D probe is complete; ship-decision judge v2 (`ARTIFACT-r7.4-ship-judge-verdict-v2.md`) returned **SHIP-WITH-CAVEAT**. MoE cleared its ≥8/20 first-attempt threshold unambiguously at 17/20 (>2× margin). Dense cleared the threshold proportionally (10/13 = 77% measured) but not absolutely on measured data alone (10/20 PASS, 3 FAIL, 7 unmeasured). One-shot regression 0/12 across legs. v2-adoption 100% on compliant trials for both models. Lift vs r7.3 baseline: 11.5× dense, 12.7× MoE.
- **Variant F artifacts are ready but NOT yet deployed to canonical.** `variants/hermes/delegate_worker_v2.py`, `variants/hermes/HERMES-variantF.md` (md5 `01c0e77bb2a6e753a8ea9063784a25e0`), `probe-variantF-{check.py,wrapper.sh,stage.sh}` all exist and are tested. The VM is currently **UNSTAGED canonical** — HERMES.md on the VM is still canonical md5 `0780c232a6cb52e13e432261f0d68ad9`. The `delegate_worker_v2` tool is registered side-by-side with v1 on the VM (additive, harmless under canonical HERMES.md which doesn't mention v2).
- **r7.3 Priority-1 blocker resolved.** The "terminal bound outside the toolset gate" finding was not a gate bypass. Direct probes confirmed the runtime binds exactly 6 tools (`clarify, delegate_task, delegate_worker, read_file, search_files, todo`) under `TOOLSETS=delegation,todo,clarify,file_readonly`. In r7.3's 4 "leak" trials, the model *hallucinated* a `terminal` tool name; the runtime rejected it; no command ever executed. Fix was a 10-line analyzer change in the probe check script (now native in `probe-variantF-check.py`). See `ARTIFACT-r7.4-p1-terminal-binding.md` + judge verdict.
- **Architectural thesis:** fully validated. Gemma-4-31B dense and Gemma-4-26B-A4B MoE both orchestrate AgentFW locally under β-fuse. The r7.3 dispatch problem is substantively solved on MoE and partially solved on dense (with a known, closable `todo`/`search_files` escape).
- **Cross-model integrity intact.** AgentFW `core/`, `references/`, `playbooks/`, `templates/`, non-Hermes variants — all untouched and byte-identical across r7.4.

The Hermes harness is NOT currently active in production under Variant F. Activation is manual and operator-controlled; the Monday 8am Jira cron runs against canonical HERMES.md until the operator authorizes the swap.

---

## What we know works (bank these — confirmed across r7.2 + r7.3 + r7.4)

- **β-fuse `delegate_worker_v2` as first action is reliable on MoE and effective on dense.** Structured/LH first-attempt PASS: MoE 17/20 (85%, cleared ≥8/20 threshold with >2× margin); dense 10/13 measured (77%, cleared the proportional 70% equivalent of the ≥14/20 absolute threshold; 7 unmeasured). Classification-as-tool-call-argument removes the "marker without dispatch" failure mode observed in r7.3. See `ARTIFACT-r7.4-phase-d-moe-results.md`, `ARTIFACT-r7.4-phase-d-dense-results.md`, `ARTIFACT-r7.4-phase-d-dense-gapfill.md`.
- **v2-adoption on compliant trials is 100% on both legs.** When the model calls the `delegation` toolset first, it calls v2 with a correct classification every time (10/10 dense, 20/20 MoE eventual, 17/20 MoE strict-first-tool). The β-fuse payload mechanism works as designed.
- **One-shot regression intact under β-fuse.** 0/12 combined failures (0/6 dense, 0/6 MoE on T1/T2/T8). The contract does not force structured dispatch on trivial tasks; the `one-shot` classification is an accepted enum value that short-circuits the dispatch requirement.
- **r7.3 → r7.4 step-function improvement.** 6.7% → 77% dense (11.5×) and 6.7% → 85% MoE (12.7×). Measured across three task types (T4 refactor, T5 bug-hunt, T6 long-horizon) plus T9/T10 on MoE. Not a margin-of-error shift.
- **Variant B classification gate + wrapper retry loop.** Both mechanisms still operate under Variant F as defense-in-depth. When the model escapes at the tool layer (dense `todo`/`search_files` cases), the wrapper correctly detects the violation, issues a NO_MARKER correction, and retries. RETRY_EXHAUSTED is reached cleanly on escape trials — the contract is enforced at the wrapper layer even when the model bypasses it at the tool layer.
- **Toolset restriction mechanically prevents mutator tool calls.** 0 tripwire mutations across all r7.4 probe runs (dense + MoE combined). Layer-1 structural property (`file_readonly` excludes `write_file`, `patch`, `skill_manage`, terminal writes) holds on every trial. The r7.3 "terminal leak" was a probe-analyzer artifact, not a gate bypass (see `ARTIFACT-r7.4-p1-terminal-binding.md`).

---

## What we know does NOT work (do not re-attempt without new evidence)

- **β-fuse alone under a wide toolset (the `todo`/`search_files` escape).** On dense, 3/13 measured structured/LH trials (T5 runs 1–2, T6 run 1) bypassed `delegate_worker_v2` by calling `todo` (2×) or `search_files` (1×) as their first tool, then exhausted the retry loop without ever calling v2 (47, 47, 26 messages respectively). These tools are legitimately bound in the probe's TOOLSETS. **β-fuse forces classification-as-payload when the model chooses the delegation path, but does not force the delegation path itself when other callable tools are in scope.** MoE showed 0/20 escapes on the same toolset — pattern is a dense-specific behavioral pull, not a harness defect. Fix is a v2.1 toolset-scoping change (Priority 2 below).
- **Inflated wrapper-SIGTERM-counted dispatch metrics.** The r7 60%/80% numbers came from a wrapper-side compliance check that counted dispatch *anywhere in the response chain* (including child-worker sessions). Strict on-disk first-attempt parsing of the parent session JSON gave ~1/5 across r7, r7.2, and r7.3. **Always re-check wrapper-reported COMPLIANT verdicts against the persisted session JSON.** r7.4 check scripts read `tool_calls[0].function.arguments.classification` directly from msg[1] — wrapper-stdout metrics are still not authoritative.
- **More aggressive prompt language alone (r7.3 L2 finding).** Escape-hatch removal in HERMES.md and wrapper text destabilized the cases L1 was solving — dense T4 went from 5/5 first-attempt under L1-only to 1/5 under L1+L2. Stricter wording without structural backstop pushes the model toward "be careful, orient first" rather than "dispatch immediately." β-fuse provides the structural backstop that language alone did not.
- **Removing escape hatches one at a time.** r7.3 closed the `search_files` orientation door and the model pushed through `todo` instead (`role-collapse-via-todo` jumped to 11/30 trials). r7.4 β-fuse under the same toolset sees 3/13 dense trials still reaching for `todo`/`search_files` first. Whack-a-mole — the model finds the next escape on the surface. Need a coordinated multi-door close (turn-0 toolset restriction: Priority 2).

---

## Priority 1 — Productionize Variant F (if operator authorizes ship)

**Trigger:** operator approval to swap the canonical HERMES.md on the VM from the current md5 `0780c232…` to Variant F's `01c0e77bb2a6e753a8ea9063784a25e0`.

**Why it's gated on operator authorization.** The Monday 8am Jira daily briefing cron runs against canonical HERMES.md. Under Variant F, the cron will exercise β-fuse via `delegate_worker_v2` for its structured work. MoE 17/20 (85%) and dense 10/13 (77%) measured suggest the cron will be substantively more reliable, but the first production run under the new contract is the operator's decision. See `ARTIFACT-r7.4-ship-judge-verdict-v2.md` §"Productionization steps".

### Ship path (if authorized)

1. **Swap HERMES.md on the VM.** Preserve the current canonical at `~/.hermes/HERMES-canonical-backup.md` (md5 `0780c232…`). Install `variants/hermes/HERMES-variantF.md` as `~/.hermes/HERMES.md` (md5 `01c0e77b…`). Keep `probe-variantF-stage.sh` / a matching unstage script ready for one-command rollback.
2. **Update the baseline md5 in probe infrastructure.** `PROBE-RESULTS-r7.md` baseline table + any stage/unstage scripts that assert `0780c232…` need updating to `01c0e77b…`. The canonical-backup remains the rollback target.
3. **Cron safety confirmation.** Manually run the Jira daily-briefing prompt once on the VM under Variant F before Monday 8am. Verify dispatch fires (first tool = `delegate_worker_v2` with `classification=structured` or `long-horizon`), child worker completes, parent summary is persisted. Verify tripwires remain clean.
4. **Monitor Monday 8am cron under β-fuse.** Watch the first 1–2 cycles for v2 adoption, worker quality, and any new failure modes. If anomalies: stage-down to canonical HERMES.md (one-command rollback via the stage script's unstage mode).
5. **Keep Variant F stage script for rollback.** Do not delete `probe-variantF-stage.sh` post-ship; it remains the authoritative swap/rollback harness.

### Alternative (if operator prefers caution)

Continue running canonical HERMES.md for Monday's cron. Deploy Variant F after Monday's successful run, giving one more weekend to review the gap-fill numbers and the dense escape caveat. No VM changes required; Variant F artifacts remain staged in `variants/hermes/` and the repo root.

---

## Priority 2 — r7.5: tighten β-fuse to close the dense `todo`/`search_files` escape

**Spec (to be written):** `ARTIFACT-impl-5-turn-0-toolset-restriction.md` (sibling to IMPL-3).

**Why.** The SHIP-WITH-CAVEAT verdict documents the dense `todo`/`search_files` escape as a v2.1 known limitation. Closing it is the highest-value next step after ship: it takes dense from 77% measured to projected ≥90%, unifies the dense/MoE behavioral profile, and removes the one documented caveat that might matter under richer production toolsets.

### Design: turn-0 toolset restriction

- **Mechanism.** Bind only `delegation,clarify` at turn 0. After the model calls `delegate_worker_v2` (any classification) or `clarify`, grant the full toolset for subsequent turns.
- **Implementation options:**
  1. **New hermes-side hook** — add a `turn_index`-aware toolset resolver in `run_agent.py` or `toolsets.py` that consults a per-session state flag (`classification_done`). Cleanest, requires upstream patch.
  2. **New toolset bundle (`beta_fuse_turn_0`)** in `toolsets.py` — pre-wire a bundle that resolves to `delegation,clarify` at turn 0 and to the requested union at turn ≥1. Simpler, reuses existing toolset machinery.
- **Probe plan.** Re-run dense T5 runs 1–5 and T6 runs 1–2 (the 7 trials that yielded the 3 escapes and the 4 clean passes) under the turn-0 restriction. Target: escape rate drops from 3/7 to 0/7.
- **Rollback.** Single-file revert (either the hook or the toolset bundle definition).

**Estimated cost:** ~3–4 hours implementation + ~2 hours probe.

---

## Priority 3 — r7.5: fill the dense coverage gap

**Why.** The ship judge's SHIP-WITH-CAVEAT verdict rests on dense 10/13 measured + 7 unmeasured (T6 runs 3–5 and T10 runs 1–5). The 77% measured rate projects to ~15–16/20 under full coverage, but it is a projection. Closing the gap converts projection into measurement and — if the measured rate holds — removes the "absolute threshold not strictly cleared" caveat retroactively.

### Scope

1. Run T6 runs 3, 4, 5 and T10 runs 1, 2, 3, 4, 5 under current β-fuse (Variant F, no turn-0 restriction). 8 dense trials, ~60–90 min wall-clock.
2. **Wrapper prerequisite — timeout fix.** The r7.4 dense run hit the SIGTERM-parent-loss bug on long tasks. Make `TIMEOUT_PER_TURN` env-configurable in `probe-variantE-wrapper.sh` / `probe-variantF-wrapper.sh` (default 900s, allow override to 1500s+ for T6/T10). Add a fallback content-match check so a missed `session_id:` line from a SIGTERM'd parent can still be recovered by matching `messages[0].content` prompt text in `~/.hermes/sessions/*.json`.
3. **Orphan-process hygiene.** Pre-flight `pgrep -f runner.sh` gate to confirm no orphan orchestrators on the mac side (parent-PID-90529 incident from the dense leg).
4. Expected result: combined dense absolute count ~15–16/20 → clears the ≥14/20 threshold strictly, eliminating the v2-verdict caveat.

**Note:** If Priority 2 lands first, run this gap-fill under the tightened turn-0 toolset and report both numbers (with-and-without dense escape coverage).

---

## Priority 4 — Documentation: upstream-contribution path for `delegate_worker_v2`

Optional, operator-directed.

If the operator wants `delegate_worker_v2` to land in upstream Hermes (rather than live as a variants-only patch), prepare a minimal PR:
- Schema + handler per `ARTIFACT-impl-3-beta-fuse-spec.md` §1–§2.
- Coexistence with v1 (v1 retained, emits `deprecation_notice` in response).
- Planned v1 sunset in a future Hermes release after two probe rounds confirm adoption ≥95%.
- Reference r7.4 ship verdict for empirical justification.

Skip this priority if the operator is content keeping v2 as an AgentFW-specific variant.

---

## Priority 5 — Worker quality (deferred to r8)

Now that parent dispatch reliably fires (MoE 85%, dense 77% measured under β-fuse; projected higher under Priority 2's turn-0 restriction), we can finally probe child behavior. Known concerns from r7-era observations remain:

- Children sometimes run in the wrong working directory and loop reading unrelated files.
- Children invent data in summaries (e.g. inventing service names for a DB topology document).
- Children don't complete before the parent times out.

The r7-era estimate of "~25% useful-completion ceiling" assumed the inflated 80% dispatch rate. Under a true ~77–85% first-attempt dispatch rate, the worker-quality ceiling now gates end-to-end task success. r8 scope should include worker-quality probes with known-goal direct spawns, worker skill bundles, and restricted worker toolsets. See git history of this file for the prior r8 design sketch.

---

## Priority 6 — Implement Option A2 (prompt-builder slot reorder)

**Spec:** `ARTIFACT-impl-4-soul-restructure.md` §4 Option A2 + §5 recommendation.

**Why.** Per α's prompt anatomy and IMPL-4's confirmed slot order (§3 + Appendix), HERMES.md sits at slot 10 of 12 in `_build_system_prompt`, behind an 11.8 KB skills index, and the recency zone (slot 12) is wasted on a CLI markdown formatting hint. For Gemma-class models the classification gate is structurally far from both the sink-token and recency-zone attention peaks.

### The change

- **File:** `~/.hermes/hermes-agent/agent/run_agent.py`, `_build_system_prompt` (lines ~2582–2740 per IMPL-4 Appendix).
- **Edit:** move the `prompt_parts.append(context_files_prompt)` block (currently after the skills_prompt append) to AFTER the `prompt_parts.append(PLATFORM_HINTS[platform_key])` block. ~10 lines moved.
- **Effect:** HERMES.md becomes the absolute last block in the system prompt — the recency zone — so the classification rules are the last thing the model sees before generating its first reply token.
- **Reversibility:** single-file revert. No content changes to SOUL.md / USER.md / MEMORY.md / HERMES.md itself.
- **Combines with:** β-fuse (Priority 2) — recency-zone HERMES.md is more valuable when the harness rules in HERMES.md are themselves stronger.

### Bonus micro-fix (per IMPL-4 §5)

Independent of A2: drop or shrink `PLATFORM_HINTS[platform]`. It's the current last block; once A2 is applied, this hint moves immediately before HERMES.md. If the CLI markdown hint is not load-bearing for any current Hermes use case (see open question #7), removing it tightens the prompt further.

### Open questions only the operator can answer

Before A2 can be optimized further (and especially before Option B, the SOUL/USER/MEMORY content trim, becomes viable), the operator needs to answer the 8 questions from IMPL-4 §6 verbatim:

1. **SOUL.md sacred lines.** Confirm that the persona paragraphs (`kawaii`-presetted, "push back when he's about to break something", "match his register") are content the user considers core, not legacy. If yes, Option B's SOUL.md trim is capped at ~10–15% (tightening prose only, no rule changes).
2. **SOUL/HERMES conceptual separation.** Does the user want SOUL.md and HERMES.md to remain distinct files? If yes → Option C is off the table. If the user is open to merging → C becomes viable as a fallback.
3. **USER.md project rolodex.** Is the ABC Supply org chart (Mike Mardis, Will Hyde, Cole Cummings, etc., ~30 named people) something Hermes needs in every system prompt, or is it acceptable to migrate the rarely-referenced names to `mempalace` and keep only the user's direct reports in USER.md? This is the single biggest USER.md trim opportunity (~1.0 KB).
4. **USER.md household-task slot.** The Wednesday garbage reminder is operational state. May the worker move it to a scheduled job (or to `dashboard-decisions.md`) and remove it from USER.md?
5. **MEMORY.md "CRITICAL ERROR HANDLING DIRECTIVE".** This is a behavior rule, not a memory. May the worker relocate it to SOUL.md (so it is not at risk of being evicted by the next memory cycle)?
6. **April 2026 config-fix log in MEMORY.md.** Now that the new config is presumably stable, may the worker archive this entry?
7. **`PLATFORM_HINTS` CLI markdown hint.** Is the CLI markdown formatting hint at slot 12 load-bearing for any current Hermes use case? If no, removing or shrinking it is the cheapest single win.
8. **A2 vs A1 placement preference.** A2 places HERMES.md at the recency zone (last block). A1 places it immediately after SOUL.md (sink zone). Both are improvements over status quo; the user may have a preference based on which behavior they care about most: A2 favors first-token classification compliance; A1 favors persona-and-harness coherence early in the prompt.

---

## Priority 7 — Speculative / research (unchanged from r7 handoff)

These items remain valid speculation but are not on the critical path:

- **Multi-level delegation** (raise `MAX_DEPTH` from 2 to 3 or 4 for complex long-horizon tasks).
- **Structured artifact passing** (a `delegate_worker_structured` variant enforcing JSON output schema for Planner-Judge flows).
- **Per-class dispatch tools** (`delegate_implementation`, `delegate_investigator`, `delegate_planner`, `delegate_judge` — each with its own schema description tuned to the task class).

All three are post-β-fuse work. β-fuse may subsume per-class tools (the `classification` arg already differentiates) and may be the right place to add structured-artifact slots as additional optional args.

---

## A quick way to resume the thread

If you're picking this up fresh:

1. Read `ARTIFACT-r7.4-ship-judge-verdict-v2.md` — authoritative SHIP-WITH-CAVEAT verdict and residual-risk register (20 min).
2. Read `ARTIFACT-r7.4-phase-d-moe-results.md` + `ARTIFACT-r7.4-phase-d-dense-results.md` + `ARTIFACT-r7.4-phase-d-dense-gapfill.md` — the raw probe numbers behind the verdict (30 min total).
3. Skim `ARTIFACT-r7.4-p1-terminal-binding.md` + judge verdict — P1 resolution (r7.3 "terminal leak" was an analyzer artifact, not a gate bypass) (10 min).
4. Read `ARTIFACT-impl-3-beta-fuse-spec.md` — the β-fuse design that shipped in r7.4 (15 min).
5. Read `DESIGN.md` + `IMPLEMENTATION.md` — architecture, stage/unstage mechanics (20 min).
6. Skim `ARTIFACT-impl-4-soul-restructure.md` — prompt-builder slot reorder + the 8 operator-decision questions, still unanswered (15 min).

### Decide entry point

- **If the operator authorizes ship** → execute Priority 1 (productionize Variant F on the VM; cron-safety confirm before Monday 8am). ~1 hour + a manual cron-path verification.
- **If the operator defers ship until after Monday** → no VM changes this weekend; start Priority 2 design (turn-0 toolset restriction spec, `ARTIFACT-impl-5-…`) which is independent of the ship decision. ~1–2 hours spec, then ~3–4 hours implementation.
- **If the operator wants the dense threshold cleared strictly before ship** → execute Priority 3 (wrapper timeout fix + dense T6 runs 3–5 + T10 runs 1–5). ~90 min wall-clock + pre-flight `pgrep -f runner.sh`.
- **If the operator has finally answered the 8 questions** → execute Priority 6 (Option A2 slot reorder). Cheapest single win and compounds with β-fuse on the recency-zone attention peak.

**Do NOT** run another probe against the current β-fuse wrapper without the SIGTERM timeout fix on T5/T6/T10. The r7.4 dense leg hit this bug and required the gap-fill patch.

Good luck.
