---
type: plan-review artifact
author: reviewer R2 (technical critique, synthesis pass)
date: 2026-04-20
plan-under-review: PLAN-r7.7-path-A-child-structural-fixes.md
reviewed-alongside: planreview I1 (campaign-arc), I2 (architecture), I3 (probe-infra), I4 (state-verification)
scope: tight technical critique, non-overlapping with I1-I4
---

# R2 — Technical critique of r7.7 Path A plan

Findings are in 5 categories per the brief. Severity: **Blocker** = must fix before S0; **Correctness** = must fix before S7 smoke; **Polish** = fix-forward acceptable.

---

## 1. Ship-gate threshold math

### F1 — Per-task priors don't center at 13/20 (Correctness)

**Section:** §9.7 "Aggregate projection: 11-16/20, centered around 13/20."
**Quote:** "T4 Arm F: 4/4 or 5/5 … T5: 1-2/5 … T6: 3-4/5 … T10: 3-5/5. Aggregate projection: 11-16/20, centered around 13/20."

Taking midpoints: T4=4.5, T5=1.5, T6=3.5, T10=4.0 → **13.5**. Rounded to integer expected value ≈ **13–14**, not 13. More importantly, the *mean* of the independent-uniform interpretation is 13.5, so "centered around 13/20" is biased slightly low. The range sum is actually **9–19** (if we allow T4=4, T5=1, T6=3, T10=3 at the low end and T4=5, T5=2, T6=4, T10=5 at the high end; adding the honestly-stated 4/4 floor for T4 keeps the low at 10). Plan states "11-16" which is tighter than the priors justify.

**Probability of ≥15 under uniform priors on the stated intervals:** roughly the joint probability that T6+T10 ≥ 9 given T4≥4, T5≤2. Back-of-envelope assuming independence: P(T10=5)=1/3, P(T6=4)=1/2, P(T5=2)=1/2, P(T4=5)=1/2 → product ≈ 0.083 for the single path to 16; aggregating paths to ≥15 yields **~20-25% probability of SHIP**, ~55-60% HOLD-CLOSE, ~15-20% HOLD, <5% RETREAT. The plan's prose "Below the 15/20 floor in the expected case; above the +5 delta in the expected case" is directionally right but undersells the ~1-in-4 shot at ship.

**Fix:** Replace "centered around 13/20" with "centered around 13.5/20 (sum of midpoints)" and explicitly state P(ship) ≈ 20–25% under the stated priors. This calibrates operator expectations and ensures the "why run it" argument (see F14) doesn't rest on a false precision.

### F2 — Dead zone between SHIP and HOLD-CLOSE is one point (Polish)

**Section:** §9.6.
**Quote:** "Ship (operator's 75% floor): Arm F ≥15/20" and "Meaningful-delta ship-caveat: Arm F ≥ r7.6 Arm B (8/20) by at least +5 absolute (so ≥13/20) — this would be a HOLD-CLOSE outcome."

A result of exactly **14/20** falls in neither band explicitly — it's ≥13 (HOLD-CLOSE) but <15 (not SHIP). The plan implicitly resolves this as HOLD-CLOSE (since it says "≥13 = HOLD-CLOSE" and 14 satisfies that), but the text doesn't nest the bands explicitly. Under the priors in F1, 14/20 is one of the most probable outcomes (modal bucket around 13–14).

**Fix:** Restate the ladder as nested: SHIP ≥15; HOLD-CLOSE 13–14; HOLD 9–12 (+1 to +4 over baseline); RETREAT <8 (below r7.6 Arm B). Explicit integer bands, no ambiguity for the most-likely bucket.

### F3 — RETREAT threshold lacks statistical-significance gate (Correctness)

**Section:** §9.6.
**Quote:** "RETREAT: Arm F < r7.6 Arm B → A1+A2 actively harmed (unlikely but possible if A2 retry loops get stuck)."

Arm B was 8/20 ± sampling noise. With n=20 and p=0.4, the 95% CI is roughly [0.19, 0.64] → [4, 13] out of 20. A single Arm F result of 7/20 is **inside the Arm B confidence interval** and doesn't evidence harm. The plan's RETREAT rule would fire on outcomes that are statistical noise.

**Fix:** RETREAT only fires if Arm F ≤ 5/20 AND the delta is ≥ 2 below Arm B (mild two-sigma heuristic), OR if per-task regression is catastrophic on T4 (scaffold-known-good). Add: "If 6 ≤ Arm F ≤ 8, classify as HOLD with note 'indistinguishable from baseline at n=20' — do not call RETREAT."

---

## 2. Risk coverage (§11) completeness

### F4 — Risk not named: T5/T6 tripwire pressure from A1-induced `terminal` migration (Correctness)

**Section:** §11 (R1-R6 list; §4 flags this but §11 doesn't promote it).
**Quote §4:** "A1 strengthens this (if `todo` is gone, children may pick `terminal` next — need to monitor)."

Plan acknowledges that removing `todo` may push models toward `terminal` as the next-available state-changing tool. `terminal` is a genuine-write path capable of arbitrary filesystem mutation, including into `~/.hermes/hermes-agent/*`. The §4 observation is that **Arm F could produce more near-tripwire-breach attempts than Arm B**, because the substrate shifts. §11 does not list this as a risk with mitigation.

**Fix:** Add R7 — "Substrate migration: A1 may move fabrication energy from `todo` to `terminal`, increasing near-tripwire-breach attempts." Mitigation: pre-probe tripwire md5 baseline, post-each-5-trials mid-run md5 check (bash `for i in 1..4; do md5 <file>; done | uniq -c`), halt on drift. Budget +15min for mid-probe tripwire checks.

### F5 — R4 mitigation "try/except" is structurally weak against SIGTERM (Correctness)

**Section:** §11 R4.
**Quote:** "A2 code wrapped in try/except/finally; on exception, proceeds to normal save (gate degrades gracefully)."

`try/except/finally` cannot catch `SIGTERM` — the signal handler in `_run_cleanup` (cli.py:8692 per I2) fires independently of Python exception machinery. Per B.0 research, the save is inline at `run_agent.py:9109`. If A2 adds N seconds of turn-generation time before the save, a SIGTERM during that window leaves the session state in a **worse** position than without A2 (the un-modified final message may have been written out by an earlier inline save; A2's correction injection means the last inline save might now be stale relative to the final pending-but-unsaved turn).

**Fix:** R4 mitigation must include (a) `signal.signal(SIGTERM, ...)` handler registered around A2's re-turn, saving the CURRENT messages before exiting, and (b) a hard wall-clock timeout on the A2 retry (e.g., 60s max per retry, so at most 120s of added exposure window). Plan implies this but does not specify. Cite I2's line 9109 + I2's G4 skill_manage note.

### F6 — Risk not named: A2 regex precision assumed, not measured (Correctness)

**Section:** §11 R3 claims regex is "calibrated … tested on r7.6 trials."
**Quote §7.3:** "Reuse the regex from the r7.6 Fix 4 patch (F4A) … Known FP case: `updated` was removed … DO NOT re-add."

The F4A regex was calibrated on **judge-time** text against heuristic scoring. A2 fires **runtime-side** on live model output, which includes: partial turns, tool-call-surrounding prose, honest-blocked templates, clarification loops. I1 Mode 4 ("out-of-context investigation") produces summaries like "the code at ~/foo/bar.py reads …" which the `written` verb may mistake for a claim. No runtime-path calibration is shown.

**Fix:** Promote to R8 — "A2 runtime-regex precision uncalibrated." Mitigation: at S6, feed the gate 10 synthetic-plus-10-real r7.6 session JSONs (mix of FABRICATED, honest-blocked, normal PASS) and require ≥9/10 precision + ≥8/10 recall BEFORE S7 smoke. Gate as ship-blocking.

### F7 — Risk not named: calibration-carry-forward assumption (Polish)

**Section:** §11 (not present); §9.5 silent per I3 finding.
**Quote I3:** "Plan §9.5 doesn't explicitly state this — polish candidate."

If A2 adds `a2_gate_outcome` to the session JSON, any judge heuristic that consumes that field is "new heuristic" and re-calibration is mandatory per `CALIBRATION-r7.6-judge-protocol.md`. Plan §9.5 treats the judge brief as unchanged; strictly true for the brief itself but not for what the orchestrator scorer reads.

**Fix:** Add to R3 or as R9 — "If orchestrator scorer reads a2_gate_outcome, re-calibrate on 5-sample before S8." Cite CALIBRATION protocol §Decision-Tree.

---

## 3. Known-traps (§12) completeness

### F8 — Pseudo-tool-call Mode 3 not in §12 (Correctness)

**Section:** §12.
**Quote I1:** "Pseudo-tool-call emission (Mode 3): 3/20 Arm A + B trials … A1 and A2 don't address this."

§12 mentions "Pseudo-tool-call sentinel leak is a real parser issue. r7.6 Fix 2 patched the Gemma parser." This is **partial coverage** — the Fix 2 patch relaxed the prefix requirement but I1 confirms 3/20 recent trials still leaked. The trap is live, not closed.

**Fix:** Update the §12 bullet to "Fix 2 reduced but did not eliminate pseudo-tool-call leaks (3/20 trials in r7.6 P1-C). If rate exceeds 2/20 in r7.7, dispatch follow-on F3A′ fix (relaxed prefix-less pattern per ARTIFACT-r7.6-inv-3). Severity: medium (parser, judge-visible, not security)."

### F9 — Out-of-context Mode 4 not in §12 (Correctness)

**Section:** §12.
**Quote I1:** "Out-of-context investigation (Mode 4): Child deployed against wrong workspace. Neither A1 nor A2 helps."

T5-run5 (Arm B) failed because child ran against hermes-agent cwd rather than the chief-of-staff-dashboard cwd. Plan's §4 closing paragraph ("task/environment mismatch, not a structural Hermes issue") acknowledges it but §12 does not name it as an expected-recurring trap.

**Fix:** Add §12 item — "Out-of-context child deployment: probe wrapper may not pass a `cwd` argument to `delegate_worker_v2`; child inherits parent's cwd, which may not match task target. Check probe-variantJ-wrapper.sh invocation for explicit cwd. Severity: low (fails honestly; no fabrication), but accounts for 1-2/20 Arm F failures."

### F10 — SCOPE-resolution Mode 5 not in §12 (Polish)

**Section:** §12 + §4 near-tripwire coverage.
**Quote I1:** "SCOPE violation — attempted writes to protected hermes-agent tree … Child maps 'project root' to `~/.hermes/hermes-agent/*`."

§4 flags the two T10 near-misses. §12 does not promote "SCOPE-resolution failure under ambiguous paths" as a trap. This is distinct from Mode 4: Mode 4 = wrong cwd; Mode 5 = right-cwd-but-wrong-interpretation of ambiguous path like "project root" or "create at root".

**Fix:** Add §12 item — "Ambiguous-path SCOPE resolution: tasks using phrases like 'project root', 'repo root', 'the main folder' trigger child to resolve to `~` or `~/.hermes/*`. Path-scope enforcement is out of Path A scope; for r7.7, ensure T10 probe tasks use explicit paths (e.g., `/media/psf/Projects/chief-of-staff-dashboard/migrations/`)." Cross-reference I2 G3.

---

## 4. A1 + A2 mechanism coherence

### F11 — A1 helper `_derive_restricted_child_toolset` corner cases (Correctness)

**Section:** §6.4 patch sketch.
**Quote:** "`_derive_restricted_child_toolset(parent_agent)` … reads the parent's enabled toolsets, removes `todo`, returns the rest."

Per I2 §1 (delegate_tool.py:226-241): when `parent_enabled is None`, `parent_toolsets` is derived from `valid_tool_names`. The helper must mirror this three-way fallback (enabled_toolsets → valid_tool_names → DEFAULT_TOOLSETS) or it will pass `toolsets=[]` when `parent_enabled is None`, which by the intersection logic at line 241 will cause `_strip_blocked_tools([t for t in [] if …])` = `[]`, yielding a child with zero tools. The current sketch doesn't mention this.

**Fix:** Helper must call the same derivation path as delegate_tool.py does. Simpler: helper is `lambda parent: [t for t in _resolve_parent_toolsets(parent) if t != "todo"]` where `_resolve_parent_toolsets` is factored out of delegate_task's inheritance path (or re-implemented identically). Add unit test: parent with `enabled_toolsets=None` → helper returns default-minus-todo, not empty list.

### F12 — A1 doesn't cover `todo`-equivalent affordances (Polish)

**Section:** §6.4.
**Quote §4 Mode 1:** "The `todo` tool lets the child mutate an internal state (task status) without touching the filesystem."

Removing `todo` leaves `clarify` in the child toolset. `clarify` asks questions but does not in itself enable fabrication. However, **within-turn text output** (the child's CoT) is still a state-mutation substrate: the child can write "I have created the plan:" followed by a code block, and then in the final turn claim the plan was created. A1 doesn't touch this. (A2 does, which is why they're paired.) But the plan's §1 TL;DR ("removes the substrate") over-sells A1 as if it closes Mode 1 alone — see F13.

**Fix:** No patch change needed; see F13 for documentation fix.

### F13 — §1 TL;DR "removes the substrate" is too strong (Correctness)

**Section:** §1 TL;DR / §9.7 predictions.
**Quote §1:** "A1 — Child toolset restriction. Strip `todo` from the default child toolset. **Removes the substrate** that enables todo-as-write fabrication."

A1 removes **one** substrate (`todo` tool). It does not remove: (a) prose-claim-only fabrication ("I wrote X"), (b) heredoc in terminal output confused with write, (c) pseudo-tool-call emission in content stream. I1 Mode 3 confirms (c) happens independent of todo. The plan elsewhere (§9.7) admits only a partial lift, which contradicts the TL;DR's absolute framing.

**Fix:** Rewrite §1 to: "A1 removes the `todo`-as-write-substitute substrate (the dominant mechanism per r7.6 T10 fabrication trials). Other fabrication routes (prose-only claim, pseudo-tool-call emission) are caught post-hoc by A2 but not structurally prevented."

### F14 — A2 write-tool list (§7.4) ghost-name weakening (Correctness)

**Section:** §7.4.
**Quote:** "`WRITE_TOOL_NAMES = frozenset({'write_file', 'patch', 'execute_code', 'terminal', 'skill_manage', 'edit_file', 'apply_diff'})`"

Per I2 §4, `edit_file` and `apply_diff` are not in `toolsets.py`. Keeping them is **harmless** for false-positive rate (an enum name that no tool call produces is a dead branch) but signals sloppy verification and adds confusion.

**Gate-weakening question:** does trimming them weaken the gate? No — the gate fires when a claim exists without a matching write. A claim paired with a real `edit_file` call would never happen (no such tool exists), so retaining the name adds 0 capability. Removing it loses 0 capability.

**Real list per I2:** `{write_file, patch, execute_code, terminal, skill_manage}` + I2 G4 caveat that `skill_manage` semantics need confirmation (may be metadata-only). The prefix matcher `name.startswith(('write_', 'edit_', 'patch_'))` covers forward-compat if Hermes adds tools like `write_append`.

**Fix:** Replace the frozenset with I2's 5-name list. Add a comment: "Prefix match retained for forward-compat; ghost names removed 2026-04-20 per I2 verification." Verify `skill_manage`'s actual file-write behavior at S2 research (I2 G4). If metadata-only, drop it too.

### F15 — A2 regex's FN on "bare path" is under-acknowledged for T10 (Polish)

**Section:** §7.3.
**Quote:** "Known FN case: bare path-only claims ('MIGRATION_PLAN.md is ready') don't match. Acceptable — false negatives are preferable to FP."

T10 trials routinely end with constructs like "The migration plan at migrations/pg12-to-pg16/PLAN.md is ready for review" — bare path, no verb. Per I1's sample, REJ-A-T10-run1 uses "(Content provided above)" wording that evades verbs. If A2 misses these, Mode 1 fabrication remains uncaught on the very task-type it's designed for.

**Fix:** Add a second regex branch specifically matching path-at-X-is-ready / available / provided patterns: `(?i)\b(?:at|is|was|see)\s+[`\w./~-]+\.(?:md|py|sh|…)\b.{0,30}\b(?:ready|available|provided|created|complete)\b`. Calibrate against T10 fresh verdicts 1,3,4 (all REJ). Keep FP-preferring conservatism: only fire when BOTH a recognizable path AND an availability verb are present within 30 chars.

---

## 5. Over-promise / under-scope

### F16 — §16 timeline ignores S8's oMLX degradation drag (Correctness)

**Section:** §16 table.
**Quote:** "S8 probe matrix (Arm F, 20 trials) | 4h (MoE trials) + 1h (judges)."

r7.5 and r7.6 wall-clock data shows MoE probe runs in the 6-9h range for 20 trials once oMLX degradation and mid-run restarts are factored in. The 4h MoE estimate assumes no restarts. Per MEMORY.md: "Long Hermes probe runs accumulate oMLX orphaned sessions + paging." Per R5 mitigation: "Monitor `probe-omlx-health-check.sh` every 5 trials. If DEGRADED, pause + operator-restart + resume." Each restart = ~15 min; 2-3 restarts expected over 20 trials.

**Fix:** S8 Arm F = 5-7h probe wall-clock (not 4h). With ablation Arm G = +4-5h. Parallelized total = 11-14h, not 9-10h. Operator time budget call in §9.2 ("12-15h") is more honest than §16's sequential/parallelized table; reconcile the two.

### F17 — Plan under-scopes CALIBRATION re-run trigger (Polish)

**Section:** §9.5.
**Quote:** "prior r7.6 calibration carries forward unless orchestrator judge changes."

Plan doesn't state the trigger explicitly (I3 §5, §12 polish candidate). More importantly: if A2 fires and injects correction + retry, the final session state **differs structurally** from r7.6 sessions — new assistant turn after gate, new role=user correction message, new `a2_gate_outcome` field. Any judge (heuristic or fresh-LLM) now sees session JSONs that differ from the calibration sample. Re-calibration may be needed even if the scorer code is byte-identical.

**Fix:** §9.5 adds: "If any r7.7 session differs structurally from r7.6 sessions (extra turns, new fields, correction-message roles), re-run 5-sample CALIBRATION before S8 full-matrix. Re-calibration of ~1h is ship-gating."

### F18 — §9.7 predicts HOLD-CLOSE but §10 "May" scope assumes ship-path work (Correctness)

**Section:** §9.7 vs §10 vs §15.
**Quote §15 success criterion 6:** "Ship judge issues SHIP / HOLD-close / HOLD / RETREAT per pre-committed thresholds."

Plan honestly predicts ~13/20 (HOLD-CLOSE), which per §9.6 is NOT SHIP. So the 13h effort is load-bearing for what?

**High-EV justifications plan does NOT articulate:**
1. **Ablation data informs r7.8.** Arm G (A1-only) vs Arm F (A1+A2) tells us which fix contributes the lift. If lift is flat between G and F, A2 is not worth keeping in r7.8.
2. **Negative result is campaign-load-bearing.** "We tried structural child-level fixes and hit 13/20" is a falsifiable claim that justifies moving to r7.8 scope (further structural restriction, e.g., delegate+clarify only until first file read — plan hints at this in §9.7 closing).
3. **A2's `a2_gate_outcome` field is reusable infrastructure.** Even if Path A HOLD-CLOSEs, the gate produces judge-input structured data that speeds future calibration.

**Fix:** Add §18 "Why run this even if HOLD-CLOSE is expected":
- EV case 1: ablation separates A1 lift from A2 lift (drives r7.8 scope decision).
- EV case 2: formal HOLD-CLOSE is the evidence needed to justify r7.8 structural-deepening — without it, the case for further β-fuse-layer restrictions is weaker.
- EV case 3: `a2_gate_outcome` is reusable infra for r7.8 and beyond.
- Make explicit: "We expect SHIP probability ≈ 25%. Running Path A buys (a) 25% shot at ship + (b) 75% shot at campaign-load-bearing negative result + reusable gate infra. Both branches are positive-EV at 13h."

---

## Summary

18 findings total. Severity breakdown:
- **Blocker:** 0 (no hard stops).
- **Correctness (must fix before S7):** F1, F3, F4, F5, F6, F9, F11, F13, F14, F16, F18 — 11 findings. Concentrated in ship-gate math, A2 precision/retry/regex, and honest framing of expected outcome.
- **Polish (fix-forward OK):** F2, F7, F8, F10, F12, F15, F17 — 7 findings. Documentation, secondary regex branches, calibration triggers.

**Top 3 by impact:**
1. **F14** — Trim A2 write-tool ghost names; verify skill_manage semantics at S2. 10-line fix, removes doubt.
2. **F5** — R4 SIGTERM interaction: specify handler + retry-wall-clock. A2's safety posture depends on it.
3. **F18** — Articulate why 13h of effort is high-EV even under expected HOLD-CLOSE. Protects operator decision at §13.1.

Plan is technically sound in its core mechanism (A1 hook via I2 verification, A2 hook at line 9109 per I2 verification, ship-gate structure). Residual issues are sharp but fixable; none require replanning.

---

*End R2 technical critique.*
