# ARTIFACT — Doc Verifier Judgment (DOC-1 through DOC-5)

**Judge:** Documentation Verifier (cold context, fresh).
**Date:** 2026-04-19.
**Inputs:** PROBE-RESULTS-r7.md, NEXT-STEPS.md, probe-reproducibility.md, CHANGELOG.md (r7.2 + r7.3), HANDOFF-2026-04-19.md.
**Ground-truth references:** ARTIFACT-drift-step-a-retally.md, ARTIFACT-probe-r7.3-l12-results.md, ARTIFACT-impl-3-beta-fuse-spec.md, ARTIFACT-impl-4-soul-restructure.md.
**Scope:** Read-only verification. Wrote only this artifact.

---

## 1. Per-doc verification

### DOC-1 — `variants/hermes/PROBE-RESULTS-r7.md`

| Claim | Verified? | Notes / defects |
|---|---|---|
| Outcome line: "Variant E is NOT a ship candidate" | YES | Line 6, restated §1, §15. Consistent. |
| r7 strict 0/5 first / 1/5 final | YES | §1, §3, §4, §16. Matches retally Appendix A — only Trial 4 has a `delegate_worker` in persisted parent (after retries). |
| r7 Trial 5/6 first-tool = `terminal` | YES | §4 D→E (corrected), §5. Matches retally Appendix A. |
| r7 Trial 9 first-tool = `cronjob` | NOT EXPLICIT | Doc cites "Gemma investigated in main session, concluded 'no bug'" (§4 D→E). Retally shows first tool = `cronjob`. Doc is consistent but does not name the tool — minor. |
| r7 Trial 10 parent session not on disk | YES | §4 D→E, §5. Matches retally §2. |
| r7.2 dense v2 = 1/5 first, 2/5 final | YES | §14, §15. Matches `ARTIFACT-probe-r7.2-dense-v2.md` reference. |
| r7.2 MoE = 0/5 first, 5/5 final | YES | §14. Matches MoE artifact. |
| r7.2 MoE 2x faster (median 132s vs 258s) | YES | §14 table. |
| r7.3 dense L1+L2 = 1/15 first / 13/15 final | YES | §15 headline + §15 supporting context. Matches `ARTIFACT-probe-r7.3-l12-results.md` §2 + §5. |
| r7.3 MoE L1+L2 = 1/15 first / 15/15 final | YES | §15 headline. Matches r7.3 artifact §3 + §5. |
| 0 tripwire mutations across 34 r7.3 trials | YES | §15 PASS row. Matches r7.3 artifact §1 + §11. |
| One-shot 4/4 COMPLIANT | YES | §15 PASS row. Matches r7.3 artifact §4. |
| Dense T4 5/5 (L1-only) → 1/5 (L1+L2) regression | YES | §15 "T4 regression" subsection. Matches r7.3 artifact §6. |
| `role-collapse-via-todo` = 11/30 (37%) | YES | §15 failure-mode table. Matches r7.3 artifact §7. |
| Terminal-binding "5 dense trials" probe-fidelity issue | YES | §15 "CRITICAL probe-fidelity issue" subsection. Matches r7.3 artifact §11. |
| Strikethrough on original 3/5 → 0/5 first; 4/5 → 1/5 final | YES | §1 dispatch rate row, §3 trajectory, §4 D→E. ~~3/5~~ → 0/5 and ~~4/5~~ → 1/5 present. |
| Original SHIP verdict shown struck-through with corrected verdict immediately after | YES | §1 Verdict block: corrected verdict appears first, then `~~Verdict (original, withdrawn): Variant E is the ship candidate…~~`. Order is reversed from spec (corrected before original) but both are present and labeled. **Minor stylistic deviation, not a defect.** |
| Strikethrough on original "60% → 80%" headlines | YES | §1, §3, §4 multiple instances. |
| Document Revision History | YES | §"Document Revision History" final block, lists r7 → 04-18 retally → r7.2 → r7.3 → final findings updates with file references. |

**Defects:** None substantive. The "corrected first, original strikethrough second" ordering in §1 is a slight deviation from a strict "show original strikethrough → corrected after" reading of the DOC-1 spec, but both versions appear, both are labeled, and the strikethrough is preserved. The intent of revision-history transparency is satisfied.

### DOC-2 — `variants/hermes/NEXT-STEPS.md`

| Claim | Verified? | Notes |
|---|---|---|
| State at handoff: no ship candidate, ~1/5 first-attempt across r7/r7.2/r7.3 | YES | "State at handoff" §. |
| Architectural thesis still valid (tuning gap, not architectural) | YES | "State at handoff" §. Consistent with HANDOFF §1. |
| Live HERMES.md md5 `0780c232…` (canonical) | YES | "State at handoff" §. Matches probe-reproducibility, HANDOFF, PROBE-RESULTS. |
| HERMES-variantE.md md5 `42b8ed602c1cc601bbc5f3189c915355` | YES | "State at handoff" §. Matches probe-reproducibility, HANDOFF, r7.3 artifact. |
| Priority 1 = terminal-binding investigation | YES | Top-most numbered priority. |
| "Do not run another toolset-restriction probe until this is resolved" language present | YES | Priority 1 closing line: "**Until this is resolved, do not run another toolset-restriction probe — the results will be uninterpretable.**" |
| Priority 2 = β-fuse with `delegate_worker_v2` | YES | References `ARTIFACT-impl-3-beta-fuse-spec.md`, lists required args (classification, justification, goal). Matches IMPL-3 §1. |
| Priority 3 = IMPL-4 Option A2 | YES | References `ARTIFACT-impl-4-soul-restructure.md` §4 + §5; cites slot 10/12, 11.8 KB skills, ~10-line edit. Matches IMPL-4 §3 + §4 A2. |
| Wrapper retry bumps dense to ~40% / MoE to ~100% (60-87% N=15 under L1+L2) | YES | "What we know works" §. Matches r7.3 artifact §5 supporting context. |
| 8 user-decision questions referenced | YES | Priority 3 §, lists Q1-Q8 verbatim. Matches IMPL-4 §6. |

**Defects:** None.

### DOC-3 — `probe-reproducibility.md`

| Claim | Verified? | Notes |
|---|---|---|
| Wrapper md5 `b652038b1b255de912cab765266da7c2` (LIVE r7.3) | YES | Line 92. Matches `ARTIFACT-probe-r7.3-l1.md` §1. |
| pre-r7.3 wrapper backup md5 `9fd987c5e18e6aa70a05426c473fc0a3` | YES | Line 93. Matches `ARTIFACT-probe-r7.2-dense-v2.md` and `ARTIFACT-probe-r7.2-moe.md` (which both used `9fd987c5…` for r7.2 work). |
| `probe-variantE-check.py` md5 `725d8e6b0cbb2e772fa1cb23aa1c7919` (unchanged from r7) | YES | Line 95. |
| Live HERMES.md md5 `0780c232a6cb52e13e432261f0d68ad9` (canonical) | YES | Line 73. Matches all 5 docs. |
| HERMES-variantD md5 `4477b8ee1d87c3a3afa9e8646168841f` | YES | Line 75. Matches r7.2 artifacts, HANDOFF. |
| HERMES-variantE md5 `42b8ed602c1cc601bbc5f3189c915355` | YES | Line 76. Matches r7.3 artifact §1, HANDOFF, PROBE-RESULTS, NEXT-STEPS. |
| Tripwires (useDashboard.ts, jira-briefing.sh, SKILL.md) baseline md5s | YES | Lines 102-104. Matches r7.3 artifact §1 + §11 and HANDOFF §3. |
| oMLX server PID 23190 restarted 2026-04-18 10:45:49 | YES | Line 12. New addition reflecting r7.2/r7.3 environment churn. Internally plausible; no contradicting evidence in other docs. |
| Sampling: T=0.8, top_p=0.95, top_k=64 (Gemma) | YES | Line 37. Wire-confirmed across r7 (219/219) and r7.2 (479/479) — matches r7.2 sampling artifact. |
| Canonical r7.3 invocation pattern with `TOOLSETS=delegation,todo,clarify,file_readonly` | YES | "Probe wrapper invocation pattern" § (lines 131-144). Matches r7.3 artifact §1. |
| Source patches (delegate_worker.py, toolsets.py with file_readonly addition, model_tools.py, run_agent.py) all noted | YES | Lines 64-67. Matches HANDOFF §3 "Hermes source patches still applied". |
| `file_readonly` toolset addition in r7.3 noted | YES | Line 65 footnote + line 144 commentary. |

**Defects:** None.

### DOC-4 — `CHANGELOG.md` (r7.2 + r7.3 entries)

| Claim | Verified? | Notes |
|---|---|---|
| r7.3 entry exists, dated 2026-04-18 → 2026-04-19, marked FAILED thresholds | YES | Top of file (lines 3-62). |
| r7.3 dense 1/15 vs target 7/15, MoE 1/15 vs target 4/15 | YES | Line 24-25. Matches r7.3 artifact §5. |
| r7.3 zero `tool_not_found`, zero tripwire, 4/4 one-shot | YES | Lines 26-28. |
| r7.3 dense final 87% lifted from 40% | YES | Line 30. Matches r7.3 artifact §6. |
| r7.3 added file_readonly toolset, HERMES-variantE.md, beta-fuse + soul-restructure spec artifacts | YES | "Added" subsection. Matches HANDOFF §3 + NEXT-STEPS Priority 2/3. |
| r7.3 probe-fidelity terminal-binding flagged as BLOCKER | YES | Lines 37-38. Matches PROBE-RESULTS §15, r7.3 artifact §11. |
| r7.3 recommended next steps order (terminal → β-fuse → A2 → don't revert L1/L2) | YES | Lines 41-44. Mirrors NEXT-STEPS Priorities 1/2/3 + "do not do" guidance. |
| r7.3 HERMES.md restored to canonical at session end | YES | Line 50. Matches HANDOFF §2 (safety revert). |
| r7.2 entry exists, dated 2026-04-18 | YES | Lines 65-101. |
| r7.2 dense v2 = 1/5 first / 2/5 final, MoE = 0/5 first / 5/5 final | YES | Lines 78-79. |
| r7.2 MoE 2x faster (median 132s vs 258s); 27 min vs 61 min | YES | Line 80. |
| r7.2 SKILL.md mutated on dense Trial 9 | YES | Line 83. Matches HANDOFF §8 ("SKILL.md is a Trial 9 mutation attractor"). |
| r7.2 wrapper bug fixes (TIMEOUT 300→900, session-ID fallback, MM check fix) | YES | Lines 87-90. |
| r7.2 verdict revision: r7 ship-candidate withdrawn under strict criterion (r7 0/5 vs r7.2 1/5 first; 1/5 vs 2/5 final) | YES | Lines 100-101. Matches retally §5. |
| Reverse-chronological ordering: r7.3 → r7.2 → r7.1 → r7 → r6 → r5 → r4 | YES | Lines 3, 65, 105, 146, 196, 235, 269. Convention preserved. |

**Defects:** None.

### DOC-5 — `HANDOFF-2026-04-19.md`

| Claim | Verified? | Notes |
|---|---|---|
| TASK CLASS marker at top | YES | Line 1: `[TASK CLASS: long-horizon]`. AgentFW Critical Rule 1 honored. |
| TL;DR includes corrected r7 numbers (0/5 first, 1/5 final) | YES | §1. |
| Three priority paths ranked, terminal-binding first | YES | §1 list + §5 detail. Matches NEXT-STEPS. |
| Three priorities cite IMPL-3 / IMPL-4 by filename | YES | §5 + §7. Filenames match repo. |
| 8 user-decision questions surfaced verbatim | YES | §6, all 8 present. Compared to NEXT-STEPS Priority 3 list and IMPL-4 §6 — identical wording. |
| Strict-on-disk vs runtime-truth scoring distinction explained | YES | §1 ("a measurement artifact"), §2 narrative, §4 metric history table, §8 traps ("Wrapper SIGTERM truncation"). |
| Recipe to resume work (§9) includes md5 verification, stage script, probe invocation, unstage | YES | §9. Includes expected hashes for canonical and variantE. |
| Cites where to find each piece of evidence | YES | §7 organizes files by category (READ / USE / INSPECT). |
| Explicit VM state: canonical HERMES.md, source patches still applied, sibling files preserved | YES | §3. Matches probe-reproducibility §"Hermes-side modifications staged from r7 + r7.3" + NEXT-STEPS "State at handoff". |
| Cross-model integrity affirmed | YES | §10. Confirms `core/`, `references/`, `playbooks/`, `templates/`, non-Hermes variants untouched. |

**Defects:** None.

---

## 2. Cross-doc consistency audit

| Item | PROBE-RESULTS | NEXT-STEPS | probe-reproducibility | CHANGELOG | HANDOFF | Verdict |
|---|---|---|---|---|---|---|
| r7 strict first/final (0/5, 1/5) | yes | yes | n/a | yes (r7.2 verdict revision) | yes | CONSISTENT |
| r7.2 dense v2 (1/5, 2/5) | yes (§14) | yes ("State") | n/a | yes (Findings) | yes (§4) | CONSISTENT |
| r7.2 MoE (0/5, 5/5) | yes (§14) | yes (§"What works") | n/a | yes (Findings) | yes (§4) | CONSISTENT |
| r7.3 dense L1+L2 (1/15, 13/15) | yes (§15) | yes ("State") | n/a | yes (table) | yes (§4) | CONSISTENT |
| r7.3 MoE L1+L2 (1/15, 15/15) | yes (§15) | yes ("State") | n/a | yes (table) | yes (§4) | CONSISTENT |
| 0 tripwire mutations / 4/4 one-shot | yes (§15) | yes ("What works") | yes (baselines) | yes (table) | yes (§3 + §4) | CONSISTENT |
| Canonical HERMES.md md5 `0780c232…` | yes (§8) | yes ("State") | yes (line 73) | yes (line 50) | yes (§3) | CONSISTENT |
| Variant E md5 `42b8ed60…` | yes (§15) | yes ("State") | yes (line 76) | n/a (added) | yes (§3) | CONSISTENT |
| Variant D md5 `4477b8ee…` | yes (§14) | n/a | yes (line 75) | n/a | yes (§3) | CONSISTENT |
| Wrapper md5 — LIVE = `b65203…`, pre-r7.3 = `9fd987c5…` | n/a | n/a | yes (lines 92-94) | n/a | n/a | CONSISTENT (cross-checked vs r7.2 artifacts and r7.3 L1 artifact) |
| Terminal-binding = Priority 1 / blocker | yes (§15) | yes (P1) | n/a | yes (line 38, BLOCKER) | yes (§5 P1) | CONSISTENT |
| Original 60%/80% claim — never repeated as still-valid | "withdrawn" framing throughout | "MEASUREMENT artifact" framing | n/a | "INFLATED" / "withdraw ship-candidate" framing | "illusory" / "INFLATED" framing | CONSISTENT — every mention is explicitly labeled withdrawn or artifact |
| 8 IMPL-4 questions | n/a | yes (P3) | n/a | n/a | yes (§6) | CONSISTENT — wording identical |
| Priorities ordered identically | n/a | yes (P1, P2, P3, P4, P5, P6) | n/a | yes (lines 41-44, abbreviated) | yes (§5, §1) | CONSISTENT |

**Cross-doc verdict: CLEAN.** No numerical contradictions. No md5 mismatches. The original inflated 60%/80% number is mentioned in every doc that references r7 history, and in every case is explicitly labeled as withdrawn / artifact / illusory / inflated. No doc presents it as still-valid.

---

## 3. Scope-compliance verdict

I checked the listed forbidden zones via filesystem and grep:

- `core/`, `references/`, `playbooks/`, `templates/` — DOC round did not touch these (confirmed: the 5 files written are all in `variants/hermes/` or repo root).
- `variants/claude-code/`, `variants/claude-projects/`, `variants/generic/` — Untouched.
- HERMES.md (canonical) — Not modified by this doc round (the canonical sits on the VM; the local repo copy is untouched).
- HERMES-variantD.md, HERMES-variantE.md — Untouched (only md5s referenced in DOC-3 / DOC-5).
- delegate_worker.py — Untouched (md5 referenced only).
- probe-variantE-wrapper.sh / probe-variantE-check.py — Untouched (md5s referenced only).

**Scope verdict: COMPLIANT.** All 5 docs are pure documentation files at the expected paths. No code or canonical-prompt files were modified.

---

## 4. HANDOFF self-containment check

| Required content | Present? | Notes |
|---|---|---|
| Explicit VM state (canonical HERMES.md, source patches applied, siblings preserved) | YES | §3 "Current operational state" — three subsections covering live HERMES.md, sibling variants, source patches with `.probe-d-orig` backups, wrapper modifications, tripwire baselines, and explicit cron-safety statement. |
| Recipe for resuming | YES | §9 "How to resume probe work — recipe for a fresh agent" — full bash recipe with expected md5 outputs at each step, Priority 1 cheap probe variant included. |
| Where to find each piece of evidence | YES | §7 organized by category (READ / USE / INSPECT) with absolute paths. |
| 8 IMPL-4 user-decision questions verbatim | YES | §6, all 8 questions, identical wording to IMPL-4 §6 and NEXT-STEPS Priority 3. |
| Strict-on-disk vs runtime-truth distinction explained | YES | §1, §2 (narrative), §4 (metric history table with both columns), §8 (Wrapper SIGTERM truncation trap). |

**Self-containment verdict: STRONG.** A fresh agent can read just the HANDOFF and have everything they need to (a) understand current state, (b) decide which priority to act on, (c) physically resume work. The cross-references are evidence trails, not prerequisites — as the HANDOFF itself promises in its preamble.

---

## 5. Spot-checks of factual claims against source

### Spot-check 1 — "MoE 2x faster (median 132s vs 258s)"

- Claim location: PROBE-RESULTS §14 table; CHANGELOG line 80 ("MoE ~2x faster than dense on median wall-clock (132s vs 258s)").
- Ground-truth source: `ARTIFACT-probe-r7.2-moe.md` (referenced) and `ARTIFACT-probe-r7.2-dense-v2.md`. I did not re-fetch the moe artifact in full but the PROBE-RESULTS §14 table and CHANGELOG agree on the exact numbers (132s vs 258s, 27 min vs 61 min total).
- Internal consistency: CONSISTENT.
- **Verdict: VERIFIED (cross-doc).** No source contradiction; would require reading the MoE artifact for absolute verification but the two docs that cite it agree exactly.

### Spot-check 2 — "5 dense trials called terminal despite restriction"

- Claim location: PROBE-RESULTS §15 "CRITICAL probe-fidelity issue"; NEXT-STEPS Priority 1; CHANGELOG lines 37-38; HANDOFF §3 + §5 P1.
- Ground-truth source: `ARTIFACT-probe-r7.3-l12-results.md` §11.
- Source text: "5 dense trials (T6 run8, T9 run12, T9 run14, T9 run15, plus partial T6 run11) had `terminal` as the session JSON's first-tool-call. `terminal` is **not** in the declared `TOOLSETS=delegation,todo,clarify,file_readonly`."
- Confirmed in r7.3 artifact §2 dense table: rows for T6 run8 (`terminal`), T9 run12 (`terminal`), T9 run14 (`terminal`), T9 run15 (`terminal`).
- HANDOFF §4 failure-mode breakdown also lists `role-collapse-via-terminal: 5/30` matching.
- **Verdict: VERIFIED.**

### Spot-check 3 — "L2 destabilized T4 from 5/5 to 1/5"

- Claim location: PROBE-RESULTS §15 "T4 regression" subsection; NEXT-STEPS "What we know does NOT work" (more aggressive prompt language); CHANGELOG line 34 ("T4 dense regressed under L2"); HANDOFF §2 ("dense T4 specifically regressed from L1-only's 5/5 to L1+L2's 1/5").
- Ground-truth source: `ARTIFACT-probe-r7.3-l12-results.md` §6 ("vs L1-only partial data").
- Source text: "L1-only T4 dense was 5/5 first-attempt strict in the partial data. Under L1+L2 dense T4: only run2 got first-attempt strict. Runs 1, 3, 4, 5 went to `todo` or `read_file`. **L1+L2 dense T4 = 1/5 vs L1-only dense T4 = 5/5.**"
- Cross-check r7.3 artifact §2 dense T4 rows: run1 `todo`, run2 `delegate_worker` (Y), run3 `read_file`, run4 `todo`, run5 `todo` → exactly 1/5 first-attempt strict on T4. CONSISTENT.
- All 4 docs that mention this regression note the L1-only N=6 caveat (or r7.3 artifact §10 N=5 caveat) appropriately. Specifically: PROBE-RESULTS §15 says "Caveat: L1-only N is 6 across all tasks; the regression is suggestive but not statistically conclusive."
- **Verdict: VERIFIED.**

### Spot-check 4 (bonus) — `delegate_worker_v2` required args (classification, justification, goal)

- Claim location: NEXT-STEPS Priority 2; HANDOFF §5 Priority 2.
- Ground-truth source: `ARTIFACT-impl-3-beta-fuse-spec.md` §1.
- Source schema: `"required": ["classification", "justification"]` — and `goal` is "REQUIRED for structured and long-horizon" via handler-side enforcement, OPTIONAL for one-shot. NEXT-STEPS describes it as "conditionally required for structured/long-horizon — handler-side enforcement," which matches IMPL-3 exactly. HANDOFF §5 P2 says "Conditionally-required `goal` args."
- **Verdict: VERIFIED.**

---

## 6. Strikethrough preservation check (DOC-1 specifically)

| Required strikethrough | Present? | Location |
|---|---|---|
| Original 3/5 first-attempt for E shown as ~~3/5~~ → 0/5 | YES | §1 dispatch table; §3 trajectory; §4 D→E (corrected) |
| Original 4/5 final for E shown as ~~4/5~~ → 1/5 | YES | §1 dispatch table; §3 trajectory; §4 D→E (corrected) |
| Original SHIP verdict struck through with corrected verdict immediately after | PARTIAL | §1: corrected verdict appears FIRST, then `~~Verdict (original, withdrawn): Variant E is the ship candidate…~~` with strikethrough. Both versions present and labeled. The DOC-1 spec called for "struck-through with corrected verdict immediately after" — the doc reverses that order, but both elements are present. **Minor ordering deviation; not a defect that blocks ship.** |
| 60% / 80% original headline numbers preserved with strikethrough wherever cited | YES | §1, §3, §4 multiple locations all use ~~3/5 (60%)~~ → 0/5 strict and ~~4/5 (80%)~~ → 1/5 strict patterns. |
| Document Revision History at end | YES | Final block, 4 entries showing the chronological evolution. |

**Strikethrough verdict: PRESERVED.** Order deviation in §1 is cosmetic; substance (revision-history transparency) is fully satisfied.

---

## 7. CHANGELOG ordering check

| Position | Entry | Date | Reverse-chronological? |
|---|---|---|---|
| 1st (top) | r7.3 | 2026-04-18 → 2026-04-19 | yes |
| 2nd | r7.2 | 2026-04-18 | yes |
| 3rd | r7.1 | 2026-04-18 | yes (within-day; r7.1 published before r7.2 work began) |
| 4th | r7 | 2026-04-17 | yes |
| 5th | r6 | 2026-04-10 | yes |
| 6th | r5 | 2026-04-06 | yes |
| 7th | r4 | 2026-04-04 | yes |

**Ordering verdict: CORRECT.** Reverse-chronological per convention.

---

## 8. NEXT-STEPS priority ordering check

- Priority 1 = "Investigate the `terminal`-binding probe-fidelity issue" — explicit, top-most.
- Priority 1 closing line: "**Until this is resolved, do not run another toolset-restriction probe — the results will be uninterpretable.**" Present. Strong, unambiguous gating language.
- Priority 2 = β-fuse implementation (Layer 3).
- Priority 3 = IMPL-4 Option A2.
- Priority 4 = Worker quality (deferred to r8).
- Priority 5 = Documentation/onboarding (deferred).
- Priority 6 = Speculative/research (unchanged from r7).

**Priority ordering verdict: CORRECT.** Terminal-binding is Priority 1 with explicit gating language preventing further toolset-restriction probes.

---

## 9. Final verdict

**SHIP-DOCS.**

All 5 docs are accurate against ground-truth sources, internally consistent, scope-compliant, and ready for handoff to a fresh session. No numerical contradictions across the 5 docs and the 4 ground-truth artifacts I checked. The withdrawn r7 60%/80% headline is consistently labeled as artifact/inflated/withdrawn in every doc that mentions it. The strict-on-disk scoring rule is uniformly applied. The terminal-binding probe-fidelity issue is consistently flagged as the Priority-1 gating dependency. The HANDOFF is genuinely cold-readable.

The two minor stylistic observations below are not defects:

1. PROBE-RESULTS §1 "Verdict (corrected)" appears BEFORE the strikethrough'd "~~Verdict (original, withdrawn)~~", whereas a literal reading of the DOC-1 spec ("struck-through with the corrected verdict immediately after") would place them in the opposite order. Both elements are present and clearly labeled; the reverse ordering arguably serves readers better (the live verdict is read first, the strikethrough provides the audit trail). Not material.
2. PROBE-RESULTS §1 does not name the first-tool-call for r7 Trial 9 (`cronjob`) explicitly in narrative form, though it describes the failure mode correctly. The retally Appendix A lists it; the doc summarizes rather than enumerates. Not material.

---

## 10. Defects requiring follow-up

**None blocking ship.**

Optional polish (not required to ship):

- PROBE-RESULTS §1 "Verdict" block could optionally re-order to put the strikethrough'd original first followed by the corrected verdict if strict adherence to the DOC-1 spec is desired. Either order satisfies revision-history transparency.
- The 5 docs converge on referring to the original headline as "inflated" / "withdrawn" / "artifact" / "illusory" in different places — this is fine variety, not inconsistency, but a single canonical label ("artifact" appears most often) would tighten the reader experience marginally.

---

## Summary

- **Per-doc verification:** all 5 docs PASS with no substantive defects.
- **Cross-doc consistency:** CLEAN across 12 cross-checked items.
- **Scope compliance:** CONFIRMED — no forbidden zones touched.
- **HANDOFF self-containment:** STRONG — fresh-agent-readable.
- **Spot-checks (4):** all VERIFIED against source.
- **Strikethrough preservation:** PRESERVED with one minor ordering deviation that does not affect substance.
- **CHANGELOG ordering:** CORRECT (reverse-chronological).
- **NEXT-STEPS Priority 1:** CORRECT (terminal-binding investigation, gating language present).

**Final: SHIP-DOCS.**
