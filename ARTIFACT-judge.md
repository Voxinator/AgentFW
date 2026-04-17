# ARTIFACT — Judge

**Date:** 2026-04-17
**Role:** Fresh judge, cold review
**Question:** Is there enough public info on Claude Opus 4.7 to meaningfully tune AgentFW r6?

---

## 1. Verdict

**Sufficient.** Anthropic's own "what's new," migration guide, and Claude-Code-specific best-practices docs (all Official tier) document at least eight 4.7-specific behavior deltas that map directly onto named AgentFW r6 surfaces, enough to drive a concrete r7 tuning pass including two changes to `core/harness-core.md`.

---

## 2. Scored tuning proposals

Each proposal is evaluated on the three-bar test:
- (a) cited Opus 4.7 behavior (Artifact B, preferably official),
- (b) specific AgentFW surface with file path + quoted rule (Artifact A),
- (c) direction of change.

---

### Proposal 1 — Remove "double-check your work" scaffolding from self-review guidance

**(a) Behavior, cited.** Anthropic whats-new / migration-guide: "Self-verification is built in. Devises ways to verify its own outputs before reporting back." Anthropic explicitly suggests **removing** scaffolding like "double-check the slide layout before returning" and re-baselining. (Artifact B §3, item 5; Official tier.)

**(b) Surface, cited.** `references/anti-patterns.md` — "Self-Review": *"Same context writes code and verifies it. Context will check for intended behavior, not actual behavior."* (Artifact A, surface 18.) Also `core/harness-core.md` Critical Rule 3 (NO SELF-VERIFY).

**(c) Direction.** *Reword, not remove.* AgentFW's rule is about role separation (an independent judge), not about asking the model to double-check itself. The risk is that tuners conflate Anthropic's advice ("stop telling it to double-check") with AgentFW's rule ("use a separate judge context"). Add an explicit clarifying note in `anti-patterns.md` distinguishing in-context self-verification (now built-in, fine) from self-review-as-judge (still prohibited).

**Rationale.** Anthropic's guidance does NOT contradict the role-separation principle — it says the model self-verifies before returning, not that it replaces an independent-context judge. But AgentFW users reading Artifact B will be tempted to weaken Rule 3. Pre-empt that.

**Passes 3-bar test: YES.**

---

### Proposal 2 — Explicitly request subagent fan-out in worker-dispatch prompts

**(a) Behavior, cited.** Whats-new: "Fewer subagents by default. The model is more judicious about delegation. *Explicitly request fan-out when you want it.* 'Spawn multiple subagents in the same turn when fanning out across items or reading multiple files.'" (Artifact B §3, item 4; Official best-practices doc.)

**(b) Surface, cited.** `references/prompt-design.md` — "Sub-agent prompts, context budget, judge shielding." Worker-dispatch prompt templates. Also `core/harness-core.md` Critical Rule 5: *"WHEN IN DOUBT, DECOMPOSE."* (Artifact A, surface 23 and Rule 5.)

**(c) Direction.** *Add.* Insert an explicit "Spawn one subagent per independent sub-problem in the same turn" instruction into worker-dispatch templates and into Rule 5's guidance text. Do not just say "decompose" — say "dispatch N subagents in the same turn for fan-out."

**Rationale.** 4.7's default is fewer subagents. AgentFW's correct behavior is more subagents. The gap must be explicitly closed in prompt text or the framework's decomposition intent will be quietly under-executed.

**Passes 3-bar test: YES.**

---

### Proposal 3 — Set default effort to `xhigh` for implementation workers, `high` for judges

**(a) Behavior, cited.** Effort doc: "`xhigh` (NEW) — 'the recommended starting point for coding and agentic work.' Default effort in Claude Code is now xhigh." And: "`max` … on most workloads adds significant cost for relatively small quality gains, and on some structured-output or less intelligence-sensitive tasks it can lead to overthinking." (Artifact B §2 Effort levels; Official.)

**(b) Surface, cited.** `core/harness-core.md` Reference Loading Protocol and `references/prompt-design.md` (sub-agent prompt design). Also implicitly: `references/verification-tiers.md` — judges need reliable thinking. AgentFW currently does not encode any effort-level defaults anywhere (Artifact A surfaces 22, 23, 24 all concern prompt design but none mention effort tier).

**(c) Direction.** *Add.* Add a short subsection to `references/prompt-design.md` specifying default effort tiers by role: workers=xhigh, judges=high, lookups/mechanical=low or medium. Note `max` is reserved.

**Rationale.** This is the single cheapest, highest-leverage change. Official guidance, clean mapping to role taxonomy, no existing rule overridden.

**Passes 3-bar test: YES.**

---

### Proposal 4 — Tighten instructions to be more literal and explicit

**(a) Behavior, cited.** Migration guide: "More literal instruction-following. Will not silently generalize an instruction from one item to another, and will not infer requests you didn't make." Especially pronounced at low/medium effort. (Artifact B §3, item 1; Official.)

**(b) Surface, cited.** `core/harness-core.md` CRITICAL RULES preamble (surface 1) — imperative rules. Also `references/prompt-design.md` — worker-dispatch templates (surface 23). Current Rule 2: *"DO NOT COLLAPSE ROLES. The main session plans and dispatches. Sub-agents implement."*

**(c) Direction.** *Reword.* The Critical Rules are already imperative; audit them for any "and similar" / "etc." / generalization patterns and make each item explicit. Specifically, Rule 4 says "Check PROGRESS.md before every dispatch" — good, already explicit. Rule 5 ("When in doubt, decompose") is the kind of abstract instruction 4.7 may not generalize from; tie it to a concrete trigger (see Proposal 2).

**Rationale.** 4.7's literal-following helps AgentFW's structural-enforcement posture (cited in Artifact B §5.D as reinforcement). But it also means any vague/general instruction elsewhere in the framework must be re-audited. The preamble already passes; the reference files need a sweep.

**Passes 3-bar test: YES.**

---

### Proposal 5 — Raise max_tokens budgets throughout by ~35% to absorb the new tokenizer

**(a) Behavior, cited.** Whats-new: "Tokenizer: NEW. Same input maps to 1.0×–1.35× as many tokens as 4.6 (up to ~35% more)." (Artifact B §2; Official.)

**(b) Surface, cited.** `references/prompt-design.md` — "Context Budget for Sub-Agents": *"500 lines of relevant context outperforms 2000 lines of mixed context."* (Artifact A surface 23.) Also `core/harness-core.md` "Reference Loading Protocol": *"Core always loaded (~175 lines)."* (Surface 22.)

**(c) Direction.** *Reword / recalibrate.* Replace line-count heuristics with token-count heuristics, or explicitly note that line counts under 4.7 tokenize to ~20–35% more tokens than under 4.6. The "500 lines" and "~175 lines" numbers are now weaker proxies.

**Rationale.** AgentFW uses line counts as prompt-budget proxies. With a new tokenizer that can inflate by 35%, the advice is still directionally right but arithmetically off. Cheap to fix.

**Passes 3-bar test: YES.**

---

### Proposal 6 — Lean into file-system memory (PROGRESS.md, PLAN.md, SESSION_LOG.md)

**(a) Behavior, cited.** Whats-new: "Better file-system-based memory use. Writes scratchpads/notes more effectively and leverages them in later turns." (Artifact B §3 item 8; Official.)

**(b) Surface, cited.** `references/state-management.md` — PROGRESS.md protocol, task state machine (Artifact A surfaces 4, 11, 12, 13). Also Rule 4: *"CHECK PROGRESS.md BEFORE EVERY DISPATCH. … The state file is ground truth, not your memory."*

**(c) Direction.** *Tighten.* AgentFW's architecture already uses file-system memory as ground truth. With 4.7's improved scratchpad use, elevate PROGRESS.md / PLAN.md / SESSION_LOG.md to first-class memory citations in worker prompts — have workers explicitly echo-read-and-quote the relevant line(s) before acting. This leverages a model strength that didn't exist before.

**Rationale.** AgentFW was right to bet on file-based state; 4.7 makes that bet pay more. Worker prompts can now reasonably say "quote the PROGRESS.md line you are acting on" without friction.

**Passes 3-bar test: YES.**

---

### Proposal 7 — Keep the 3-task health-gate cadence; do NOT loosen based on 1M / 98.5% needle claims

**(a) Behavior, cited.** Needle-in-a-Haystack: 98.5% at 1M. BUT: migration guide recommends server-side compaction; 4.6-era GitHub issue (reputable, #34685) documented self-reported degradation at 40–48% context usage and carries over as 4.7 baseline concern per Artifact B. Anthropic has NOT published a 4.7-specific agentic-context degradation curve. (Artifact B §2, §4 gap 1, §5.F; Official + Reputable.)

**(b) Surface, cited.** `references/state-management.md` — Context Health Gate: *"After every 3 tasks reach completed/verified, re-read PROGRESS.md and self-assess against Critical Rules. Output `[CONTEXT HEALTH: OK/DEGRADED]`."* (Artifact A surface 4; core/harness-core.md Session Protocol §7 also references this.) Artifact A surface 27 notes the 3-task cadence is "the Opus 4.7-specific tuning dial."

**(c) Direction.** *No change (hold).* Against the temptation to loosen to 4 or 5 tasks based on the 1M / 98.5% claims. Add a one-line comment in the rule explaining *why* we are not loosening yet: "Needle retrieval ≠ agentic instruction-adherence. Hold cadence at 3 until an empirical probe says otherwise."

**Rationale.** This is still a tuning proposal — "reword to document why we're not changing it" is a real edit. It immunizes the rule against well-meaning loosening by future tuners reading the 1M marketing.

**Passes 3-bar test: YES.**

---

### Proposal 8 — Make adaptive-thinking enablement explicit in judge dispatch

**(a) Behavior, cited.** Whats-new: "Adaptive thinking is the only supported mode… Adaptive is off by default; must be explicitly enabled via `thinking: {type: 'adaptive'}`." Artifact B §4 gap 7 names the specific concern: "if adaptive decides to skip thinking for what looks like a short evaluation prompt, judge quality degrades silently." (Official for the mechanism; judge-impact is inferred but grounded.)

**(b) Surface, cited.** `references/prompt-design.md` — "Judge Shielding": *"Judge receives only requirements + system state + verification criteria. NOT worker's implementation plan or reasoning."* (Artifact A surface 24.) Judge prompts are currently structured for shielding but not for thinking-enablement.

**(c) Direction.** *Add.* Augment judge-dispatch templates with explicit `thinking: {type: 'adaptive'}` and a minimum-thinking signal (e.g., a longer explicit rubric in the judge prompt, which biases adaptive to deliberate). Also set effort to `high` (from Proposal 3).

**Rationale.** Judges are the exact case where silent thinking-skip is worst. A short prompt + shielded context + default-off thinking = the model might respond immediately with a shallow verdict.

**Passes 3-bar test: YES.**

---

### Proposal 9 — Remove any "summarize after every N tool calls" scaffolding

**(a) Behavior, cited.** Migration guide: "Built-in progress updates during long agentic traces. Anthropic suggests removing scaffolding like 'After every 3 tool calls, summarize progress' and re-baselining." (Artifact B §3, item 6; Official.)

**(b) Surface, cited.** This is the trickiest one. AgentFW's Context Health Gate (Artifact A surface 4) fires "after every 3 tasks reach completed/verified" — this is task-count, not tool-call-count, and is gated on observable state rather than a fixed interval. It is NOT the scaffolding Anthropic recommends removing. The surface that could plausibly match is `references/observability.md` SESSION_LOG event types (surface 20) and "When to Log" (surface 21) — but those are event-based, not interval-based.

**(c) Direction.** *No change.* Document in the r7 notes that AgentFW's periodic-reflection pattern is task-state-triggered, not tool-call-interval-triggered, and therefore survives 4.7's recommendation.

**Rationale.** Important NEGATIVE finding: the surface that looks like it should change doesn't. Worth stating explicitly so a future tuner doesn't delete the health gate citing Anthropic's advice.

**Passes 3-bar test: YES** (behavior cited, surface cited, direction = "hold and document why"). This is a legitimate rewording/annotation change, not a no-op.

---

### Proposal 10 — Consider task-budgets beta for bounded worker dispatch

**(a) Behavior, cited.** Whats-new: "Task budgets (beta)… Beta header: `task-budgets-2026-03-13`. Advisory token budget across full agentic loop. Minimum 20k tokens. Do not set for open-ended work." (Artifact B §2 Task Budgets, §5.E; Official.)

**(b) Surface, cited.** `core/permissions.md` — Worker Scope Constraints: *"Every worker dispatch includes explicit scope: allowed paths, allowed operations, forbidden operations, side-effect budget."* (Artifact A surface 14.) "Side-effect budget" is already a concept; token budget is a natural sibling.

**(c) Direction.** *Add.* Add "token budget" as a fourth component of worker scope, with the note that it uses 4.7's task-budgets beta header when supported, and is NOT set on judges or open-ended investigation.

**Rationale.** Aligns a 4.7-new feature with an existing AgentFW concept. Clean fit.

**Passes 3-bar test: YES.**

---

### Proposal 11 — Route web-research-heavy subtasks with caution (BrowseComp regression)

**(a) Behavior, cited.** Vellum + whats-new: "BrowseComp: 79.3% — down 4.4 pts from 4.6, trailing GPT-5.4 Pro (89.3%) and Gemini 3.1 Pro (85.9%). Only notable regression." (Artifact B §2; Reputable w/ some official grounding.)

**(b) Surface, cited.** `playbooks/pm-investigation.md` (per reference index in harness-core.md) — product/market investigation often web-research-heavy. Also implicitly `playbooks/bug-hunting.md`. Artifact A does not enumerate a specific quoted rule here — the surface map focuses on enforcement rules, not playbook routing.

**(c) Direction.** *Would be "add" (a note in pm-investigation.md).* But the surface is not quoted in Artifact A with a specific rule — it's a playbook file whose content isn't surfaced.

**Passes 3-bar test: PARTIAL — the behavior is cited (reputable tier, consistent with Anthropic's own card per Vellum), but the AgentFW surface is named by file only, not by quoted rule. Marking NO on strict reading of the rubric.**

---

### Proposal 12 — Loosen the <20-line one-shot threshold based on 4.7's coding gains

**(a) Behavior, cited.** SWE-bench Verified 87.6%, CursorBench +12 pts, "3× more production tasks resolved" per Anthropic (Artifact B §2). Some of this is code-task benchmark strength.

**(b) Surface, cited.** `core/harness-core.md` One-shot criteria: *"One-shot applies ONLY when: (a) zero files are modified, OR (b) exactly one file is modified with fewer than 20 lines changed AND the change has no cross-file dependencies."* (Artifact A surface 3.)

**(c) Direction.** *Would be "loosen" to e.g. <30 lines.*

**Rationale.** Benchmark strength is about correctness at task completion, NOT about whether the main session should one-shot vs. delegate. The threshold is a role-separation gate, not a capability gate. Loosening it because 4.7 is smarter is the exact "main session collapses into worker" failure mode the framework exists to prevent.

**Passes 3-bar test: NO.** Behavior cited but surface-to-behavior linkage is wrong. Marked "does not pass" per the rubric's note to not rubber-stamp sensible-sounding proposals with weak linkage.

---

### Proposal 13 — Weaken Rule 3 (NO SELF-VERIFY) because 4.7 self-verifies

**(a) Behavior, cited.** Whats-new: built-in self-verification (Artifact B §3 item 5).

**(b) Surface, cited.** `core/harness-core.md` Critical Rule 3: *"DO NOT SELF-VERIFY. The context that wrote the code cannot verify the code. Dispatch a separate judge."*

**(c) Direction.** *Would be "loosen."*

**Rationale.** Anthropic does not claim 4.7's self-verification replaces an independent judge. Artifact B §5.D explicitly notes: "Role separation (Rule 2) remains necessary… built-in self-verification but makes no claim that it substitutes for an independent judge." Loosening Rule 3 rests on misreading the evidence.

**Passes 3-bar test: NO.** Rejecting this proposal; listing it here to document that the judge considered and rejected a superficially attractive tuning direction.

---

## 3. Summary tally

**Passing proposals: 10** (Proposals 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
**Failing proposals: 3** (Proposals 11, 12, 13 — kept in the list to document judge reasoning)

**Files touched by passing proposals:**
- `core/harness-core.md` — Proposals 2, 4, 5, 7 (4 changes touch core)
- `references/anti-patterns.md` — Proposal 1
- `references/prompt-design.md` — Proposals 2, 3, 5, 8
- `references/state-management.md` — Proposals 6, 7
- `core/permissions.md` — Proposal 10
- `references/observability.md` — Proposal 9 (annotation only)

**Sufficiency check against rubric:**
- ≥ 6 changes passing: **YES (10 ≥ 6).**
- ≥ 2 touching `core/harness-core.md`: **YES (4 ≥ 2 — proposals 2, 4, 5, 7).**

**Overall: Sufficient.**

---

## 4. Named gaps — what would move us from "Sufficient" to "strong revision"

These are the things Artifact B does NOT contain that would upgrade the tuning pass from "reasonable defaults" to "empirically calibrated."

1. **A 4.7-specific agentic-context degradation curve.** Needle-in-haystack at 98.5% is necessary but not sufficient. We need: at what % of context consumed does rule adherence (e.g., classification-gate compliance, delegation discipline) drop by N%? This is the empirical basis for tuning the 3-task health-gate cadence (Proposal 7) rather than just defending the status quo.

2. **Self-verification reliability vs. independent-judge reliability.** Anthropic claims built-in self-verification. No published comparison against a separate-context judge on a realistic bug-detection or correctness task. Without this, Rule 3 is defensible but not empirically re-calibrated.

3. **Subagent-spawning threshold data.** "Fewer subagents by default" — how many fewer, on what kinds of tasks, compared to 4.6? Without this, Proposal 2 ("explicitly request fan-out") is qualitatively right but quantitatively unguided.

4. **Effort-tier measured quality curves for judge-style work.** Proposal 3 recommends `high` for judges. Anthropic says `max` overthinks structured output, but there's no curve comparing `high` vs. `xhigh` vs. `max` specifically on verification/evaluation prompts.

5. **Task-budget semantics across subagents.** Artifact B gap 5 names this. Matters for Proposal 10's exact wording.

6. **GT-6 and GT-7 results on 4.7 baseline.** AgentFW's own regression tests have not been run against 4.7 (Artifact A §"Known Eval Signal"). These are the highest-signal internal probes available. Their absence is the single largest empirical gap.

7. **Adaptive-thinking engagement rate on short/shielded judge prompts.** Proposal 8 is based on an Artifact B gap (item 7) acknowledging no public data. A short probe could answer this directly.

---

## 5. Recommended next step

**Run an empirical probe first, then proceed with r7 tuning, in that order.**

**Specifically:**

(a) Before writing r7, **re-run the existing golden-tasks suite (GT-1 through GT-7) on Opus 4.7 baseline** (unchanged r6 framework). Measure:
  - Classification-gate compliance rate across GT-1..GT-7.
  - Role-collapse incidents in GT-6 (late-session delegation).
  - Genuine-assessment rate in GT-7 (health gate, evidence-backed `[CONTEXT HEALTH]`).
  - Tool-call count and subagent-dispatch count per task (expecting fewer on 4.7; this validates Proposal 2).
  - Self-verification incidents where an independent judge would have disagreed (validates Proposal 1/Rule 3).

(b) Then do the r7 tuning pass. **Top 3 changes to ship first (highest confidence, lowest regression risk):**

  1. **Proposal 3** — add effort-tier defaults (`xhigh` workers, `high` judges) to `references/prompt-design.md`. Cheapest, clearest-cited, no rule weakening.
  2. **Proposal 2** — add explicit "spawn N subagents in the same turn for fan-out" language to worker-dispatch templates and Rule 5. Directly counteracts 4.7's "fewer subagents by default" default.
  3. **Proposal 6** — tighten PROGRESS.md / PLAN.md / SESSION_LOG.md integration in worker prompts (quote-before-act). Leverages 4.7's improved scratchpad use; costs nothing; reinforces Rule 4.

(c) Defer Proposal 7's annotation, Proposal 11 (BrowseComp routing), and any health-gate threshold change until after the empirical probe.

The probe is low-cost and will redirect the tuning pass if the predictions from Artifact B don't hold on this specific deployment. The r7 pass without the probe is defensible; the r7 pass informed by the probe is a strong revision.

---

**End of Artifact**
