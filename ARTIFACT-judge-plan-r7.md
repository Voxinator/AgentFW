# Judge Artifact — PLAN-r7.md

**Judge role:** Fresh judge, no prior context.
**Date:** 2026-04-17
**Artifact under review:** `/Users/briantaylor/Projects/AgentFW/PLAN-r7.md`

---

## 1. Verdict

**Accept-with-revisions.** The plan structurally encodes the user intent (probe-gated, bloat-capped, core-agnostic, rejections documented), but a few quoted "current surfaces" are paraphrases rather than verbatim quotes of the named file — workers acting on the plan literally would be searching for strings that do not exist.

---

## 2. Scorecard

| # | Test | Result | Rationale |
|---|------|--------|-----------|
| 1 | Core stays model-agnostic | **Pass** | §0 non-goals explicitly forbid model-specific branches in `core/`. §3 puts all 4.7-specific knobs (`xhigh`, adaptive thinking, `task-budgets-2026-03-13` beta header) into `references/prompt-design.md` as a bounded ≤25-line "Model-family knobs (non-binding)" subsection. §5 budgets `core/harness-core.md` at +0 and `core/permissions.md` at +0. No Anthropic-SDK language appears in any core-file diff. |
| 2 | No-regression gate is concrete and enforceable | **Pass** | §1.1 names four models; §1.2 names GT-1..GT-7 citing `evaluation/golden-tasks.md` (all seven exist); §1.3 names six metrics with definitions plus token usage; §1.4 names an output file (`evaluation/results-r6-baseline-multimodel-YYYY-MM-DD.md`) with specified table shape; §1.5 states a measurable threshold (≥1 SD regression on any §1.3 metric aborts). A human could run this without inventing numbers. |
| 3 | Bloat budget is real | **Pass** | §5 states a total cap (≤70 lines ex-CHANGELOG), per-file sub-budgets sum to ≤47 (5+30+10+2+0+0), with headroom documented. Scope-cut rules on overrun are explicit. §9 Planner Note 5 flags the one disagreement with the brief (Proposal 10 moving out of `core/permissions.md` drops that file's +≤4 to +0) and justifies it. |
| 4 | Rejected proposals documented | **Pass** | §4 table explicitly handles all four: P5 Reject (tokenizer portability), P11 Defer (3-bar test PARTIAL), P12 Reject (role-gate not capability-gate), P13 Reject (misreading of source). One-line reasons given for each. No silent drops. |
| 5 | Probe-before-ship sequencing | **Pass** | §1 opening sentence: "Phase 0 MUST complete before any Phase 1 edit is dispatched." §1.5 closing: "Phase 0 is a hard gate. Phase 1 worker dispatch is forbidden until the results file exists." Unambiguous. |
| 6 | Diff realism | **Fail** | Two of the six quoted surfaces drift from the actual file text. See §3 below. Workers acting literally on the plan would not find the strings. Substantive intent is preserved, but the plan claims verbatim quotes that aren't verbatim. |

**Overall:** 5/6 pass. The one fail is mechanical and correctable in ≤15 minutes but must be corrected before worker dispatch.

---

## 3. Diff-Realism Spot-Checks

### Proposal 1 — `references/anti-patterns.md` Self-Review section — **MISMATCH**

- **Plan's claimed current surface (§2.1):** *"Same context writes code and verifies it. Context will check for intended behavior, not actual behavior."*
- **Actual text at `references/anti-patterns.md` line 25:** *"The same context that wrote code or made changes then runs verification checks on its own work. It will check for what it intended, not what happened. It will miss the same edge cases in both passes. Verification must come from a fresh context that evaluates artifacts cold, without access to the implementer's reasoning or intent."*
- **Match:** No. The quote is a paraphrase/compression, not a verbatim quote. A worker running an exact-match search will not find it. Substantively aligned but literally drifted.

### Proposal 6 — `core/harness-core.md` Rule 4 — **MATCH (with documented ellipsis)**

- **Plan's claimed current surface (§2.4):** *"CHECK PROGRESS.md BEFORE EVERY DISPATCH … The state file is ground truth."*
- **Actual text at `core/harness-core.md` line 14:** *"**CHECK PROGRESS.md BEFORE EVERY DISPATCH.** Read the task states. Do not re-dispatch completed or in-progress tasks. Do not dispatch tasks with unverified dependencies. The state file is ground truth, not your memory."*
- **Match:** Yes, with an explicit ellipsis marking the elision. Acceptable.

### Proposal 7 — `references/state-management.md` Context Health Gate — **MISMATCH (citation misdirection)**

- **Plan's claimed current surface (§2.5):** *"After every 3 tasks reach completed/verified, re-read PROGRESS.md and self-assess against Critical Rules. Output `[CONTEXT HEALTH: OK/DEGRADED]`."*
- **Actual text at `references/state-management.md` line 66 (the file the plan edits):** *"After every 3 tasks reach `completed` or `verified` status in PROGRESS.md, the planner MUST perform a context health check before dispatching the next worker:"* followed by a numbered list through line 80.
- **Match:** No. The quoted surface matches `core/harness-core.md` line 140 (Session Protocol §7), NOT the file the plan proposes to modify. The annotation the plan wants to add is meant to land "immediately below the rule" — but the rule in `references/state-management.md` is a multi-line numbered protocol, not a one-liner. The worker needs a precise insertion point. Substantive intent is fine; precise landing location is ambiguous.

### Proposal 2 — `references/prompt-design.md` worker-dispatch/context-budget section — **PARTIAL MATCH**

- **Plan's claimed current surface (§2.2):** "Worker-dispatch prompt guidance centered on context scoping."
- **Actual text at `references/prompt-design.md`:** The file is short (41 lines). There is a §"Context Budget for Sub-Agents" starting line 15, with Include/Exclude/The Rule subsections. No explicit "worker-dispatch" subsection exists — the closest is the top-of-file bulleted list on prompt design generally.
- **Match:** Partial. The described section exists in substance; the name is informal. Acceptable since the plan's phrasing is descriptive, not a quote.

**Net:** 2 of 4 spot-checked quotes drift. Workers need a corrected plan or will escalate.

---

## 4. Planner Disagreements (from §9)

1. **Phase 0 cost (Note 1).** Planner flags 28 runs across 4 models as expensive; gate auto-relaxes if models are inaccessible. **My take: accept.** The auto-relaxation is well-scoped (flagged in CHANGELOG, does not block shipping against Anthropic baselines, which are the primary guard).
2. **Proposal 4 scope (Note 2).** Planner wants a dedicated worker despite ±0 line delta. **My take: accept.** Audit-only work still benefits from a dedicated isolated worker; it's a legitimate task, not a checkbox.
3. **Proposal 6 bloat risk (Note 3).** Planner raised P6 sub-budget from judge's ≤5 to ≤10. **My take: accept.** Judge's ≤5 was optimistic. The fallback ("cut example, keep principle if >7") is the right escape valve.
4. **§3 subsection accretion risk (Note 4).** Planner flags that `references/prompt-design.md`'s model-family subsection will feel tight by r8 and may need to become its own reference file. **My take: accept, defer.** Correct diagnosis, correct deferral — don't pre-create a file for hypothetical future content.
5. **Proposal 10 moved out of `core/permissions.md` (Note 5).** Planner cut +≤4 budget to +0 by moving the token-budget discussion into the §3 model-family subsection. Brief had budgeted +≤4 to `core/permissions.md`. **My take: accept (override in planner's favor).** Moving Anthropic-SDK-specific language (the `task-budgets-2026-03-13` beta header) out of `core/permissions.md` is more consistent with the user's "core stays model-agnostic" intent than the brief's original budget. Planner correctly recognized that the brief's sub-budget would have violated the user's primary constraint. This is exactly the kind of flagged disagreement the harness expects.

**No disagreements require negotiation or override.** The planner handled all five correctly.

---

## 5. Revisions Needed (Blockers Before Worker Dispatch)

1. **Proposal 1 — fix the quoted surface.** Replace the §2.1 "Current surface" paraphrase with the actual verbatim text at `references/anti-patterns.md` line 25 (Self-Review section). The worker's insertion point should be explicit: "append clarifier sentence after the existing three-sentence block on line 25."
2. **Proposal 7 — fix the quoted surface OR redirect the file citation.** The quoted surface is from `core/harness-core.md` line 140, not the edit target `references/state-management.md`. Either:
   - (a) Use the actual `references/state-management.md` line 66 text as the "current surface," and state the annotation lands after the numbered list ending at line 80; OR
   - (b) Split P7 into two parallel edits (one in each file), but that raises the line budget — preferred option is (a).
3. **Proposal 2 — tighten the named insertion point.** Replace "Sub-agent prompt templates / context budget section" with the literal heading `## Context Budget for Sub-Agents` and state whether the fan-out paragraph goes above "### Include", inside "The Rule", or at the bottom.

**Non-blocking polish (nice-to-have, ship without if needed):**
- §7 Rollout step 7 says "version 6.0.0 → 7.0.0" — confirm SemVer intent. r6 → r7 is a revision; MAJOR bump is a separate policy question.
- §6 Abort criteria (§6.2) uses ≥1 SD on some metrics but ≥15% on tokens. The mixed-threshold approach is defensible but worth a one-line rationale.

---

## 6. Additional Checks Requested

- **"What do I do first tomorrow morning" answer:** **Yes.** The plan leaves no ambiguity: run Phase 0 (§1), which means pulling up GT-1..GT-7, running them across 4 models on unchanged r6, and writing results to `evaluation/results-r6-baseline-multimodel-YYYY-MM-DD.md`. That is tomorrow's task.
- **§3 model-family subsection placement:** **Correct.** Lives at end of `references/prompt-design.md`, not in `core/`. Explicitly budgeted ≤25 lines. Non-binding labeled.
- **Planner disagreements summary:** Five items in §9. Summarized in §4 above. All accepted.

---

## 7. Ship-Readiness

**Not ready as-is.** Fix the three quoted-surface drifts in §5 (≤15 minutes of work — they are mechanical corrections to the plan document, not to the codebase). After that, the plan is ready for Phase 0 worker dispatch, and Phase 1/2 are clean to proceed pending Phase 0 gate results.


---

## 8. Re-Judgment (post-revision)

**Verdict: SHIP.**

### Per-Spot-Check Results

- **Spot-check A — Proposal 1 (§2.1): MATCH.** PLAN line 84 quotes the Self-Review anti-pattern verbatim against `references/anti-patterns.md` line 25, and specifies the insertion point ("Append a single clarifier sentence immediately after the existing paragraph, preserving the blank-line separator to the next anti-pattern").
- **Spot-check B — Proposal 7 (§2.5): MATCH.** PLAN line 121 quotes the Context Health Gate opening verbatim against `references/state-management.md` line 66, correctly cites `references/state-management.md` (not harness-core.md), and points the annotation to "after the numbered list ends (post-line ~80)" — the numbered list runs through line 76 with trailing clarifiers to line 80, so the insertion location is accurate.
- **Spot-check C — Proposal 2 (§2.2): MATCH.** PLAN line 92 cites the verbatim heading `## Context Budget for Sub-Agents`, names all three subsections (`### Include`, `### Exclude`, `### The Rule`), and specifies the insertion point precisely as "above `### Include`, directly under the `## Context Budget for Sub-Agents` intro sentence," with a justification for that placement.

### Polish Checks

- **Token rationale after §6.2 abort criteria: PRESENT.** PLAN line 230: *"Rationale for mixed thresholds: Token threshold is absolute because SD is undefined on per-task token variance until a baseline exists."* Satisfies the non-blocking ask.
- **§7 SemVer intent: CLEAR.** Step 7 (line 248) explicitly specifies "version 6.0.0 → 7.0.0, revision r6 → r7." The intent is stated plainly as a MAJOR bump aligned to the revision. No added rationale was required by the non-blocking check — only clarity, which is present.

### Residual Concerns

None that block shipping. Prior §5 blocking drifts are all resolved. The r8 accretion-risk flag (§9 item 4 in the plan) and the Phase 0 cost concern (§9 item 1) remain valid long-term considerations but are out of scope for r7.

**Recommendation:** Proceed to Phase 0 worker dispatch. Plan is ready.
