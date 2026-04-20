# ARTIFACT — Judge Synthesis: r6 Hermes Addendum Fit Analysis

**Judge:** Fresh-context synthesis (no worker reasoning access beyond artifacts)
**Date:** 2026-04-17
**Inputs:** `ARTIFACT-workerA-addendum.md`, `ARTIFACT-workerB-agentfw.md`, `ARTIFACT-workerC-hermes-live.md`, `PLAN-r6-hermes-addendum.md`, `variants/hermes/HERMES.md`

---

## 1. Executive verdict

The r6 Hermes addendum is **architecturally well-considered but addressed to a harness that is not actually executing on the live install**. The addendum (PLAN-r6-hermes-addendum.md) builds careful adaptations — skills-based load, IterationBudget gates, cron carve-out, benchmark regression — on top of assumptions that Worker C's live probe contradicts on three load-bearing points: (a) the user-described "deterministic Complexity vs. Resource" router does not run (`smart_model_routing.enabled: false`); (b) the `claude --acp --stdio` delegation path has code but no installed binary; (c) HERMES.md is already loaded every turn via prompt_builder.py but produces **zero classification markers, zero delegate_task calls, zero PROGRESS.md artifacts** across three recent sessions. The addendum's most valuable contributions (H10 cron carve-out, H11 benchmark regression gate) survive this reality check. Its core behavioral apparatus (H1 Critical Rules, H3 health gate, H4 delegation self-check) is prescribing behaviors the live agent is not currently performing even with the prior HERMES.md loaded — skills-based packaging alone will not fix that.

**Confidence:** High on the describe-vs-execute gap (Worker C has direct log evidence). Medium on whether the addendum's mitigations would close it.

---

## 2. Three-way fit matrix

| # | Capability / Assumption | Claimed by user | Assumed by addendum | Observed in live install |
|---|---|---|---|---|
| 1 | Primary model | Gemma-4-31B planner/judge/code | `gemma-4-31b-it-4bit`, fallback parser at run_agent.py:~8070 | Confirmed: config.yaml `model.default: gemma-4-31b-it-4bit`; every turn hits it (Worker C §4) |
| 2 | Auxiliary model | Qwen3-VL-8B-Instruct-MLX-4bit | Used for "chunking, OCR/vision, summarization/filtering"; "skills-hub matching (future)" | Confirmed. Used for compression/vision/web_extract/session_search/skills_hub/approval/mcp/flush_memories (Worker C §8) |
| 3 | Complexity router | "Simple/Multimodal/Volume→Aux; Implementation→External; else→Primary" | Not directly addressed; addendum treats primary as the planner/judge default | **Disabled.** `smart_model_routing.enabled: false`, `cheap_model: {}`. Every user turn goes to primary unconditionally (Worker C §6) |
| 4 | Delegation to Claude Code via ACP | `claude --acp --stdio` subprocess via `delegate_task` | Referenced only as "External CLI implementation" implicitly via delegate_task; not central to the plan | Code path exists (`tools/delegate_tool.py` `acp_command` override, `copilot_acp_client.py`). Default ACP binary is `copilot`, not `claude`. **Neither `claude` nor `copilot` is installed on the VM** (Worker C §7, §11 row 3). Calling it would fail at Popen. |
| 5 | HERMES.md loading | Implied as "system prompt" | H0: skills-based load at `~/.hermes/skills/software-development/hermes-harness/SKILL.md`; `variants/hermes/HERMES.md` becomes thin pointer | **Currently loaded every turn via prompt_builder.py `_load_hermes_md`.** Walks to git root; present at `~/.hermes/hermes-agent/HERMES.md` and `~/HERMES.md` (Worker C §5). The addendum's skill install does NOT yet exist. |
| 6 | PROGRESS.md | Not claimed by user | H5 drops it: "Hermes has no PROGRESS.md"; advisory `MEMORY.md` replacement | Confirmed absent. One hit total on disk — a template in `skills/gstack-harness-templates/` (Worker C §9). No sessions create one. |
| 7 | Classification markers (`[TASK CLASS: ...]`) | Not explicitly claimed | H1 Rule 1 (with cron carve-out); H3 health-gate marker | **Zero occurrences across three recent sessions** (Worker C §10). The loaded HERMES.md already prescribes the Planner-Worker-Judge architecture; the agent ignores it in practice. |
| 8 | delegate_task invocations | User says Hermes "can spawn" via delegate_task | H1 Rule 2 names it; H4 decision-point gates trigger it | **Zero invocations across three recent sessions.** Only appears in `session_meta` as the tool definition (Worker C §10). |
| 9 | Role separation (Planner ≠ Worker ≠ Judge) | Implicit in "Implementation → External" | Mandatory for structured work (H1 Rules 2-3); H4 enforces | Not observed. Children inherit parent credentials; no runtime enforcement of judge independence (Worker C §11 row 9). |
| 10 | Context compression | Not directly claimed | H3 / H9 reference "50% compression trigger" and "trajectory compressor" | Real. `trajectory_compressor.py` (65K) exists; `compression.threshold: 0.5` in config; live log entries at Apr 10 and Apr 17 show Qwen summarization fires (Worker C §8). The "50% trigger" is in fact a ratio threshold on context, not iteration count. |
| 11 | IterationBudget (60 default) | Not claimed | Central to H3 gates (50% / 80%) and H4 constraint on dispatch | `MAX_DEPTH=2`, `MAX_CONCURRENT_CHILDREN=3`, `DEFAULT_MAX_ITERATIONS=50` in delegate_tool.py (Worker C §7). Addendum cites 60 as the primary cap; Worker C saw 50 as the child default. The primary main-session cap was not directly quoted by Worker C. |
| 12 | Skills-hub auto-matching | Implicit via "Qwen3-VL-8B auxiliary" | H0/H10 assume auxiliary model matches skills via frontmatter `exclude_contexts` | `skills_hub` auxiliary entry exists in config; the `exclude_contexts` field is **flagged as "not an existing Hermes convention"** in the addendum itself (H10:270). Not confirmed in live code. |
| 13 | Cron carve-out | User does not claim; addendum does | H10 + H11: hermes-harness skill not attached to cron jobs | No cron integration examined by Worker C beyond presence of `~/.hermes/cron/`. Jira-daily-briefing skill exists; cron jobs.json not probed. Addendum's claim plausible but unverified live. |
| 14 | Benchmark baseline (Jira 100%) | Not claimed | H11 treats 30/40/20/10 as ground truth | Not verified by Worker C in live logs. `~/.hermes/skills/productivity/jira-daily-briefing/benchmark/run-benchmark.sh` referenced by the addendum (H11 step 2) but not inspected. |
| 15 | MLX-on-Ubuntu paradox | User locates aux as "MLX-4bit" | Treats auxiliary as a callable endpoint | **Resolved.** MLX inference runs on the Parallels macOS host at `10.211.55.2:8000` (oMLX server). Ubuntu VM is orchestrator client only (Worker C §1, §4). |

---

## 3. Confirmed assumptions (addendum is right about these)

These map from addendum text to evidence in Worker C's live probe.

**C1. Primary is Gemma-4-31B.** Addendum line 21 / H11:285. Config `model.default: gemma-4-31b-it-4bit`; every gateway turn logs `model 'gemma-4-31b-it-4bit'` (Worker C §4).

**C2. Auxiliary is Qwen3-VL-8B-Instruct-MLX-4bit.** Addendum H0:38. Config's `auxiliary.*` all pinned to that model; live log: `Auxiliary compression: using custom (Qwen3-VL-8B-Instruct-MLX-4bit)` at four timestamps across Apr 10 and Apr 17 (Worker C §8).

**C3. Gemma emits tool calls as raw text; fallback parser handles conversion.** Addendum preamble:21. Worker C's §4 doesn't quote the parser line directly but Worker A §3.6 cites `run_agent.py:~8070`. Consistent with Gemma's 10/100 structured output; the architectural premise is sound.

**C4. `delegate_task` primitive exists with depth cap + concurrency cap.** Addendum preamble:24, H1:67-71. Worker C §7 confirms `MAX_DEPTH=2`, `MAX_CONCURRENT_CHILDREN=3`. Iteration default for children is 50, not 60 — see gap G6.

**C5. Context compression at ~50% is a real mechanism.** Addendum H3:144, H9:239. Worker C §8: config `compression.threshold: 0.5`; `trajectory_compressor.py` exists; live fires observed.

**C6. HERMES.md loads via prompt_builder auto-discovery.** Addendum H0:42-44 rejected this path but it is in fact already the live path (Worker C §5 quotes `_HERMES_MD_NAMES = (".hermes.md", "HERMES.md")` at prompt_builder.py:89; priority list at lines 948-952). The addendum's rejection was on grounds of "patch surface collision"; live evidence shows the mechanism works and is in use today.

**C7. SOUL.md exists as an identity slot.** Addendum preamble:22 says "currently empty; personality is kawaii." Worker C §5 confirms SOUL.md is 2423 bytes, loaded separately.

**C8. Hermes uses Discord as primary live surface.** Addendum preamble:20 presumes Discord threads. Worker C §10 / §12 Q7 confirms "All recent gateway.log traffic is Discord."

**C9. Qwen auxiliary is used for more than vision.** Addendum preamble:21 lists "chunking, OCR/vision, summarization/filtering." Worker C §8 shows the auxiliary is wired for eight task types including memory flush and approval, not just VL.

---

## 4. Assumption gaps — ranked by severity

### GAP 1 — CRITICAL: The addendum prescribes behaviors the live agent does not perform even with HERMES.md already loaded

**What the addendum assumes:** HERMES.md-style instruction (Critical Rules, classify-first, delegate_task dispatch, Planner-Worker-Judge) will shape Gemma's multi-step behavior. The entire r6 Hermes plan — H1 (Critical Rules), H3 (health gate), H4 (delegation self-check), H13 (golden tasks) — is premised on the model reliably emitting `[TASK CLASS: ...]` markers, calling `todo list` as an observable trigger, and dispatching `delegate_task` at decision points.

**What's actually true:** Worker C §10 observed three recent sessions where Gemma was asked structured questions (including questions about its own routing architecture). Results:
- Zero classification blocks across all three sessions.
- Zero `delegate_task` calls (string search returned only the tool definition in `session_meta`).
- Zero PROGRESS.md artifacts created.
- Every turn resolved in 1 API call.

Yet HERMES.md (AgentFW hermes variant) **was already loaded every turn** via prompt_builder.py. The 130-line Planner-Worker-Judge instruction is in Gemma's context. Gemma describes the harness eloquently when asked about it but does not execute it.

**Severity: CRITICAL.**

**Why it matters:** Moving the text from `HERMES.md` (auto-discovered every turn) into a skill file (`hermes-harness/SKILL.md`, manual `/hermes-harness` activation) does not change the underlying adherence problem. It changes *when* the text is loaded, not *whether the model follows it.* The addendum's primary behavioral claims assume loading ≈ following. Worker C's evidence says that's false for this model.

**Evidence:** Worker C §5 (HERMES.md is loaded every turn); Worker C §10 (three sessions, no protocol compliance); Worker A §2.1 (addendum targets degradation in long sessions but doesn't cite specific Hermes degradation incidents); PLAN-r6-hermes-addendum.md H3:146 (the addendum acknowledges Gemma's 10/100 structured output is "exactly the failure pattern").

---

### GAP 2 — CRITICAL: The user's deterministic complexity router does not exist at runtime

**What the addendum assumes:** Implicit throughout. The addendum does not directly reference the user's "Simple/Multimodal/Volume→Auxiliary, Implementation→External, else→Primary" rule, but it treats the primary model as the planner/judge default and discusses "external CLI implementation" via delegate_task acp_command. This presumes a routing layer that selects between these three tiers.

**What's actually true:** Worker C §6 examined `smart_model_routing.py` (194 lines). The `choose_cheap_model_route` function performs keyword-gated routing to a cheap model BUT `smart_model_routing.enabled: false` in config.yaml and `cheap_model: {}` is empty. The function short-circuits on line 174 (`if not _coerce_bool(cfg.get("enabled"), False): return None`). **Every user turn is routed to Gemma-4-31B unconditionally.**

The auxiliary_client.py (2226 lines) has fixed task→model bindings (compression→Qwen, vision→Qwen, etc.) — task-type routing, not content-complexity routing. When the user told Hermes "Give me a deterministic rundown" (Worker C §10, Apr 17 17:56), Gemma returned the exact tri-tier rule set the user described — meaning **Gemma is describing (or roleplaying) a router that is not implemented.** This is effectively the model hallucinating its own architecture.

**Severity: CRITICAL.**

**Why it matters:** The addendum doesn't depend on the router being real (it treats primary as default, which is what actually runs). But this gap reveals something fundamental about describe-vs-execute: **the user's mental model of their own system is partly shaped by what Gemma says back, not by what the code does.** Any r6 deliverable that claims to integrate with "the router" is integrating with fiction.

**Evidence:** Worker C §6 (config + source code); Worker C §10 (Gemma's verbatim reply describing the rule the code doesn't implement); Worker C §11 row 4.

---

### GAP 3 — HIGH: The `claude --acp --stdio` delegation path is code without a binary

**What the addendum assumes:** Not called out explicitly in the addendum, but user said "Hermes can spawn `claude --acp --stdio` via delegate_task." Addendum H1:67-71 names delegate_task as the dispatch primitive, and the implicit assumption is that it works.

**What's actually true:** Worker C §7. The code path exists in `tools/delegate_tool.py:915-951` (`acp_command`, `acp_args` params) and `agent/copilot_acp_client.py` (`Popen([acp_command] + acp_args, ...)`). But:
- Default ACP binary is `copilot` (GitHub Copilot CLI), not `claude`. `claude --acp --stdio` requires an explicit `acp_command="claude"` at call time.
- Neither `claude` nor `copilot` is installed on the Ubuntu VM. `which claude copilot` → empty. No `/usr/local/bin/claude`, no `~/.local/bin/claude`, no `HERMES_COPILOT_ACP_COMMAND` in the running gateway's environ.
- A `delegate_task(acp_command="claude")` call would fail at Popen with the known error: "Could not start Copilot ACP command 'copilot'. Install GitHub Copilot CLI or set HERMES_COPILOT_ACP_COMMAND/COPILOT_CLI_PATH."

**Severity: HIGH.**

**Why it matters:** The user described "Implementation → External (Claude Code via ACP)" as part of their architecture. The default Hermes delegation produces **in-process Python AIAgent children running Gemma**, not Claude Code subprocess. If the user expects implementation-tier tasks to route to Claude, that expectation is not being met by the system today. The addendum's H1 Rule 2 ("dispatch a `delegate_task` subagent") would, in current state, dispatch another Gemma instance — not a different model.

**Evidence:** Worker C §7 (code + binary absence); Worker C §11 row 3; Worker C §12 Q1.

---

### GAP 4 — HIGH: `exclude_contexts` frontmatter is flagged by the addendum itself as unverified

**What the addendum assumes:** H10:260-270 proposes a YAML frontmatter field `activation.exclude_contexts: [cron, batch]` as a secondary mechanism to keep hermes-harness out of cron sessions. The addendum acknowledges at H10:270 that this "is not an existing Hermes convention."

**What's actually true:** Worker C did not verify the skills-hub matching logic in live code. The addendum itself warns (H10:270): "If the auxiliary model's matching logic doesn't read `exclude_contexts`, this is advisory-only; the real safety comes from mechanism #1 (explicit cron attachment)."

**Severity: HIGH** (only because the addendum already hedges).

**Why it matters:** If mechanism #1 (explicit skill attachment in `jobs.json`) is the sole real control, that's one line of defense, not two. The risk model in H11 (benchmark regression) depends on the defense holding. Worth probing the `skills_hub` auxiliary config and auxiliary_client.py for what fields it actually reads.

**Evidence:** PLAN-r6-hermes-addendum.md H10:270 (self-flagged); Worker C §8 (auxiliary.skills_hub exists but its matching schema wasn't probed).

---

### GAP 5 — HIGH: Structured-marker risk is acknowledged but the addendum still depends on it

**What the addendum assumes:** H1 Rule 1 and H3 health gate require Gemma to emit `[TASK CLASS: ...]` and `[CONTEXT HEALTH: OK — <evidence>]` as in-band text. H3:146 explicitly admits: "Gemma-4's structured prose output is unreliable (10/100 on benchmark mode). The `[CONTEXT HEALTH: OK — evidence]` marker is structured prose in exactly the failure pattern."

**What's actually true:** Worker C §10 — across three recent sessions with HERMES.md already loaded, **zero classification markers appeared.** The addendum's mitigation (H11 benchmark regression) measures whether markers degrade the Jira benchmark, not whether markers fire at all in interactive sessions.

**Severity: HIGH.**

**Why it matters:** The addendum's own risk register (Risk Summary row 2) classifies "Gemma fails to emit protocol markers reliably" as HIGH with mitigation "H11 benchmark + GT-7-hermes calibration." H11 alone cannot validate this because H11 benchmarks the cron path (where the skill is specifically not attached); GT-7-hermes is a manual Discord test that requires human instrumentation. There is no automated coverage that the protocol markers actually fire in the target environment.

**Evidence:** Worker A §3.2, §5.1, §7 "Critical Risk"; Worker C §10; PLAN-r6-hermes-addendum.md H3:146, risk table line 447.

---

### GAP 6 — MEDIUM: IterationBudget number mismatch (60 vs. 50)

**What the addendum assumes:** Addendum preamble line 20: "60-iteration hard IterationBudget." H3 triggers are 30/60 (50%) and 48/60 (80%).

**What's actually true:** Worker C §7 quotes `delegate_tool.py`: `DEFAULT_MAX_ITERATIONS=50` for children. Worker C did not separately probe the main-session iteration cap (`HERMES_MAX_ITERATIONS` env var), but the child default of 50 suggests a discrepancy.

**Severity: MEDIUM.**

**Why it matters:** If the primary budget is actually 50 (or configurable and defaulting lower), the 30/48 trigger points in H3 are at 60% and 96%, not 50% and 80%. The H3 design was percentage-based precisely to handle reconfiguration, but the addendum's stated constants should be verified and aligned.

**Evidence:** Worker C §7; PLAN-r6-hermes-addendum.md line 20, H3:106.

---

### GAP 7 — MEDIUM: `todo` tool semantics not verified

**What the addendum assumes:** H1 Rule 4, H3, H4, H9 all reference `todo list` as an observable tool call and `todo` as the state substrate. Worker A §4.4 flags this as a gap: the exact command format, state machine, and status values are undocumented in the addendum.

**What's actually true:** Worker C did not probe the `todo` tool definition directly, but listed skills include `gstack-harness-planner/worker/judge/templates` — suggesting Hermes has harness-role skills and some notion of task state tracking. The `state.db` sqlite file (8.1 MB) likely holds it. Not verified in live code.

**Severity: MEDIUM.**

**Why it matters:** H3's gate and H4's dispatch-check both trigger `todo list` as the observable call that prevents rubber-stamping. If `todo list` isn't a real agent-level tool, or if its semantics differ from what the addendum assumes, the gates don't have a reliable trigger. The addendum assumes a specific interface without citing the agent tool spec.

**Evidence:** Worker A §4.4, §6.5; Worker C §9 (state.db + skills presence, but no tool schema quoted).

---

### GAP 8 — MEDIUM: "The 50% compression trigger" conflates two different 50%s

**What the addendum assumes:** H3 fires at 50% **iteration budget used** (iteration 30 of 60). H9 says corrective action is to "request context compression via the existing 50% compression trigger."

**What's actually true:** Worker C §8: config has `compression.threshold: 0.5` under `compression:` section. This is a **context ratio threshold** (token fill), not an iteration count. The two 50%s are measuring different things. The addendum conflates them at H3:144 and H9:239.

**Severity: MEDIUM.**

**Why it matters:** Iteration count and token fill diverge — a session could hit 30/60 iterations well before or well after 50% token fill, depending on message size. If the addendum intends the health gate to co-fire with compression, the trigger conditions need to be decoupled or reconciled.

**Evidence:** Worker C §8 (compression.threshold: 0.5); PLAN-r6-hermes-addendum.md H3:144, H9:239.

---

### GAP 9 — LOW: Skill-install path is new; prompt_builder path already works

**What the addendum assumes:** H0 treats skills-based load as the correct install path and rejects context-file auto-discovery. Rationale includes "requires a prompt_builder.py edit and collision risk with fallback parser patch surface."

**What's actually true:** Worker C §5 — `_load_hermes_md` in prompt_builder.py is already implemented, already loads HERMES.md every turn via a walk-to-git-root search. The addendum's "requires an edit" premise is false: **the mechanism already exists and works.** The real question is whether skills-based load is additionally desirable (opt-in scoping, cron isolation) — which is a legitimate argument — not whether auto-discovery is feasible.

**Severity: LOW** (doesn't invalidate the H0 decision, just its rationale).

**Why it matters:** The addendum's stated rejection of context-file auto-discovery rests partly on a factual error. The decision may still be correct on other grounds (opt-in activation, cron isolation) but the argument is weaker than presented. Worth reflecting in H0 revision that the mechanism exists and the reason to prefer skills is scope control, not implementation difficulty.

**Evidence:** Worker C §5; PLAN-r6-hermes-addendum.md H0:42-44.

---

## 5. "Describe vs. execute" gap — the central question

Worker C's evidence makes the describe-vs-execute gap the most consequential finding in this review.

**The evidence (Worker C §10, direct quote from session 20260417_174835):**

- User: "What model do you use to summarize long documents?"
- Gemma (powered by the AIAgent loop, with HERMES.md loaded): "For most of my heavy lifting and reasoning, I'm currently powered by **Gemma-4-31B**... I typically follow a 'decompose and synthesize' pattern: 1. Chunking... 2. Map-Reduce... 3. Final Synthesis..."
- User: "Give me a short deterministic rundown for how you choose which model to use."
- Gemma: [returns the tri-tier routing rule the user described as ground truth]
- User: "are you really set up to use claude code?"
- Gemma: "Yes, I am! But it's important to be precise about *how* I use it. I don't 'become' Claude Code; instead, I act as the orchestrator. In my `delega[te_task]..."

Every one of these replies resolved in a single API call. Zero tool use. Zero delegate_task. No classification block. **The model is describing the harness without executing it.** The harness text is in context; the model treats it as information about what the system (supposedly) does, not as instructions about what *it* should do.

**How much of the r6 addendum is aimed at a harness that isn't running?**

Let me map each major addendum section to execution reality:

| Addendum | Targets | Live status |
|---|---|---|
| H0 — install as skill | Switches load mechanism | Current auto-discovery already loads HERMES.md every turn; load is not the bottleneck |
| H1 — Critical Rules | Adherence in multi-step work | Model currently doesn't emit markers at all (Worker C §10) |
| H3 — IterationBudget health gate | Fires at 30/60 and 48/60 | No sessions observed reaching these depths; never tested |
| H4 — delegation self-check | Triggers at decision points | Agent doesn't invoke delegate_task at all in observed sessions |
| H5 — PROGRESS.md replacement | MEMORY.md one-liner | N/A — no state tracking observed |
| H6 — cron carve-out in core | Isolation | Cron sessions aren't observed as broken; not in the dataset |
| H7 — rubber-stamp anti-pattern | Named failure mode | Can't rubber-stamp markers that aren't emitted |
| H9 — degradation recovery | Triggered by health gate | Gate never fires; recovery path dead |
| H10 — cron carve-out mechanism | Prevents skill loading in cron | Plausible but unverified; depends on jobs.json mechanism |
| H11 — benchmark regression | Catches cron regression | **The one guard rail that's empirically grounded** |
| H12 — variant diff carve-out | Documentation | Doesn't affect runtime |
| H13 — golden tasks GT-6/7-hermes | Behavioral verification | **Right target; this is exactly what would catch the describe-vs-execute gap** |

**Reading:** Of the 13 additions, H11 and H13 are the ones that would actually surface whether Gemma executes the harness or just describes it. The rest are mostly *specifications* of the harness. The harness-specification work is not wrong — if execution starts working, these specs matter. But they do not cause execution.

**Harsh but warranted conclusion:** The r6 Hermes addendum is ~70% harness-specification work (valuable if Gemma starts following instructions) and ~30% risk containment (H10, H11, H13) (valuable regardless). The addendum's implicit assumption is that the specification problem is the bottleneck. Worker C's data suggests the execution problem is the bottleneck, and the addendum does not address it directly.

**What would actually close the gap:**
1. An empirical test that Gemma, with this prompt, emits `[TASK CLASS: ...]` on a structured task. Run before specifying the rest.
2. A minimum reproducible behavior: one forced delegation on one structured task. If that doesn't work reliably, every downstream piece (H3 gate, H4 self-check, H9 recovery) fires in a vacuum.
3. A tighter, more assertive prompt — possibly mirroring Sonnet 4.6 tuning ("Your response MUST begin with `[TASK CLASS: ...]`") which the Hermes addendum explicitly does not apply (Worker A §5.3).

---

## 6. Cross-model integrity check

The r6 Hermes addendum is designed as a **variant-specific addendum**, separate from PLAN-r6.md. Does it preserve AgentFW's cross-model integrity for Opus 4.7 / Sonnet 4.6 / GPT-5-tier variants?

**Finding: Yes, the addendum preserves cross-model integrity, with minor concerns.**

**Evidence for preservation:**

1. **H12 (Variant diff carve-out):** Explicitly confines the Hermes divergence to the Hermes variant. "Variant diff (Claude Code, Generic variants): Diff against core. Only permitted differences: HTML comment on line 1, Templates/Evaluation entries in Reference Index." The Hermes variant gets its own rules (`todo` vs PROGRESS.md, delegate_task vs sub-agent prompts, IterationBudget percentage vs task count, cron carve-out). Claude Code / Generic stay pinned to core. This is exactly the right architecture for cross-model integrity.

2. **H0 isolation:** The hermes-harness skill lives at `~/.hermes/skills/...`, not in `variants/claude-code/` or `variants/generic/`. No shared file surface.

3. **H13 (golden tasks):** GT-6-hermes and GT-7-hermes are **new** entries added alongside the canonical GT-6 and GT-7. Upstream golden tasks for Claude Code remain unchanged. H13:375: "The upstream GT-6 and GT-7 remain canonical for Claude Code variant."

4. **Critical Rules semantic equivalence (H12):** The five Hermes rules (H1) map 1:1 semantically to the five Claude Code rules in harness-core.md. Same structural commitments, different substrate (todo vs PROGRESS.md, delegate_task vs sub-agent prompts). Worker B §4 confirms the five canonical rules; Worker A §1.2 tabulates the 1:1 mapping.

**Minor concerns:**

1. **"Rule 1 carve-out" could be mis-ported.** H1:63-64 adds an exception: "Single-purpose curl sequences in a cron skill that already declares scope do not need classification." If this exception phrasing leaks into the canonical core (via a careless future sync), it would introduce an escape hatch that Opus 4.7 / Sonnet 4.6 don't currently have. Worker B §4 shows the canonical Rule 1 is strict: "No exceptions. No silent skipping." The addendum's H12 guards against this by documenting Hermes as divergent, but operator discipline is the enforcement.

2. **Reference Index compression (A2) is skipped for Hermes (H2).** Not a cross-model concern directly, but the rationale — "the hermes-harness skill has its own minimal reference section" — means Hermes does not benefit from whatever the A2 compression achieved in core. If A2 was a behavioral improvement, Hermes misses it. Worker B §10 describes r6 as "shifted from memory-driven to state-driven gates" — the state-driven shift is preserved in Hermes (H3 uses `todo list` as observable trigger), so behavioral intent transfers even if specific text doesn't.

3. **Sonnet 4.6 tunings not applied.** Worker A §5.3: Sonnet-addendum proposed "Your response MUST begin with..." hard-output-contract framing for marker elision. Hermes addendum does NOT pick this up. Gemma is likelier than Sonnet to elide markers (10/100 structured output). Cross-model integrity would argue for applying the Sonnet tuning to the Hermes addendum, since Hermes has the same failure mode more severely. The addendum doesn't reference Sonnet's observations at all.

**Overall:** The addendum respects the cross-model variant architecture. The Hermes divergence is well-scoped to the Hermes variant, and H12 documents it as intentional. The one real cross-model concern is that the r6 addendum didn't ingest r6 learnings from the Sonnet 4.6 addendum — these are peer documents but they don't cross-reference.

---

## 7. Ranked recommendations (top 7)

Ranked by impact × ease. Impact = degree to which the recommendation resolves a live gap. Ease = implementation cost.

### R1 — Run a minimum-viable "does Gemma emit a classification marker" probe BEFORE committing to the r6 Hermes plan

- **What:** One-shot probe. Load HERMES.md (current state). Send "structured task: investigate why log X has spam — identify causes, rank hypotheses." Check assistant output for `[TASK CLASS: ...]` block. Repeat 3 times.
- **Where:** Run via `~/.hermes/hermes-agent` CLI or Discord thread. Log in `evaluation/results-r7-hermes-probe-YYYY-MM-DD.md` (new file).
- **Why:** Directly tests Gap 1 (Critical). If Gemma doesn't emit the marker on day 1 with HERMES.md already loaded, H1/H3/H4 specifications fire in a vacuum. This probe is the load-bearing empirical input the plan lacks.
- **Effort:** S (3 probes, ~20 minutes).
- **Risk if not done:** The entire r6 Hermes plan ships as specification theater. Spec is good; but if the model doesn't follow specs, the cost of a full H14 rollout (install skill, backup run_agent.py, run benchmark 2x, draft golden tasks, run golden tasks) is spent on a non-problem while the real problem (adherence) is untouched.

### R2 — Apply Sonnet 4.6's hard-output-contract framing to the Hermes Critical Rules

- **What:** Rewrite H1 Rule 1 from "Output `[TASK CLASS: ...]` before sequences of 3+ tool calls..." to "**Your response MUST begin with `[TASK CLASS: ...]` on any task spanning 3+ tool calls.** Non-emission is a protocol violation." Mirror the Sonnet tuning Worker A §5.3 cited. Apply to the draft `hermes-harness/SKILL.md`.
- **Where:** PLAN-r6-hermes-addendum.md H1 (line 54-83). Also `ADDENDUM-sonnet-4-6.md` should be cited in the r6 addendum.
- **Why:** Gemma is more prone to elision than Sonnet (10/100 structured output vs. 2/3 Sonnet tasks). If Sonnet needed hard-output-contract framing, Gemma needs it more. Addresses Gap 5.
- **Effort:** S (20-line edit).
- **Risk if not done:** Markers elide silently. GT-7-hermes "fail signal: Markers appear without `todo list` calls" can't distinguish from "markers never emerged at all."

### R3 — Verify `exclude_contexts` and `skills_hub` auxiliary matching logic in live code before relying on mechanism #2

- **What:** Grep `~/.hermes/hermes-agent/agent/auxiliary_client.py` for `exclude_contexts`, `activation`, `tags`, `hermes:` — confirm or refute the frontmatter convention. If not supported, remove mechanism #2 from H10 and document mechanism #1 (explicit cron attachment) as the sole control.
- **Where:** PLAN-r6-hermes-addendum.md H10 (line 252-273). Results go in H10 updated text.
- **Why:** Gap 4. The addendum itself flagged this as unverified. Worker C did not probe it. Ten minutes of Grep resolves it.
- **Effort:** S (10 minutes of grep + edit).
- **Risk if not done:** Cron isolation rests on a single line of defense, but the plan claims two. Operator could misjudge the safety margin.

### R4 — Reconcile IterationBudget numbers and decouple the two "50%" triggers

- **What:** Probe live: (a) `HERMES_MAX_ITERATIONS` in config.yaml or env; (b) `DEFAULT_MAX_ITERATIONS` in delegate_tool.py for parent vs. child. Update H3 with correct numbers. Rewrite H3:144 and H9:239 to distinguish "context fill 50% (compression trigger)" from "iteration budget 50% (health gate trigger)" — don't conflate.
- **Where:** PLAN-r6-hermes-addendum.md H3 (line 103-147), H9 (line 228-246), preamble line 20.
- **Why:** Gaps 6 and 8. Two separate mechanisms are currently described as one. Reconciling makes the corrective actions in H9 unambiguous.
- **Effort:** S (15 minutes of probing + edit).
- **Risk if not done:** In a DEGRADED health event, the operator or agent doesn't know whether to force compression (context ratio) or wait (iteration). Corrective action is ambiguous.

### R5 — Confirm `delegate_task` with acp_command="claude" works end-to-end on the user's setup before shipping a harness that mentions external CLI implementation

- **What:** User-side task. Confirm either (a) claude/copilot CLI is installed somewhere Hermes can reach, or (b) the expectation is that "External CLI" delegation is aspirational and should be marked as such in HERMES.md and the skill draft. If aspirational, drop references to external CLI from user-facing architecture descriptions (including the tri-tier routing if ever documented).
- **Where:** User decision; reflected in PLAN-r6-hermes-addendum.md as a new H-numbered section or in the Open Questions list.
- **Why:** Gap 3. User's described architecture includes "Implementation → External (Claude Code via ACP)." Live install can't execute this path. The addendum should state clearly whether this is live or planned.
- **Effort:** M (requires user info and possibly binary install; edit is small).
- **Risk if not done:** User mental model diverges from system capability. Downstream plans assume a capability that isn't there. Gemma continues to tell the user "Yes, I am set up to use Claude Code" when in fact it would fail at Popen.

### R6 — Promote H11 (benchmark regression) to run BEFORE H1/H3/H4 spec work lands

- **What:** Reorder H14 so HB (baseline benchmark) + HF (post-change benchmark) bracket a no-op skill install: create the skill directory with placeholder content (just the frontmatter), run baseline, create a realistic SKILL.md, re-run. This isolates the cost of *having* the skill present from the cost of its *content.*
- **Where:** PLAN-r6-hermes-addendum.md H14 (line 379-402).
- **Why:** Addresses a subtle risk: the addendum's H11 assumes the whole skill is installed atomically. If the regression appears, we don't know whether it's from the skill's existence (e.g., skills-hub auxiliary overhead) or its content (protocol markers landing unexpectedly). Separating these isolates the signal.
- **Effort:** M (one extra benchmark run, ~15 minutes if tooling is smooth).
- **Risk if not done:** If a regression shows up, root-cause analysis takes longer and might lead to wrong conclusions (e.g., removing content when the issue is presence).

### R7 — Add a behavioral eval for HERMES.md adherence that doesn't require human Discord driving

- **What:** New golden task GT-8-hermes: automated script that starts a fresh Hermes session, sends a canned structured prompt ("identify the 3 largest files in ~/.hermes/logs and explain why"), and greps the output for `[TASK CLASS: ...]` and `delegate_task` tool calls. Pass = both present. Fail = either absent.
- **Where:** `evaluation/golden-tasks.md` — new section GT-8-hermes. Reference from PLAN-r6-hermes-addendum.md H13.
- **Why:** GT-6-hermes and GT-7-hermes are manual Discord tests. They require human judgment to trigger phase transitions. Gap 1 (describe-vs-execute) needs an automated regression check that runs on every change.
- **Effort:** M (write a small driver script + canned prompt + grep check).
- **Risk if not done:** Adherence degrades silently between releases. The human-driven golden tasks catch it at best monthly; automated eval catches it on every r-number bump.

---

## 8. What should be verified before any changes land

**Pre-commit checks (all should pass before any r6 Hermes artifact is written to disk):**

1. **R1 probe:** Run the minimum-viable classification-marker probe 3 times on the current HERMES.md (unchanged). Baseline: does Gemma emit `[TASK CLASS]` at all? Result expected: zero (per Worker C §10). This establishes the baseline against which any improvement is measured. Golden task reference: GT-6 canonical (golden-tasks.md), adapted as inline probe.

2. **R3 exclude_contexts verify:** Grep `~/.hermes/hermes-agent/agent/auxiliary_client.py` for `exclude_contexts` / `activation` / frontmatter reading. Pass/fail determines whether mechanism #2 in H10 survives.

3. **R4 iteration budget probe:** Read `~/.hermes/config.yaml` for `HERMES_MAX_ITERATIONS` or equivalent env var. Confirm parent-session cap vs. child `DEFAULT_MAX_ITERATIONS=50` in delegate_tool.py. Update H3 trigger math accordingly.

4. **R6 baseline + no-op benchmark:** Per H11 step 2, on clean state. Then install a skill with just frontmatter (no content). Re-run. Expectation: scores identical.

5. **delegate_task end-to-end probe:** Run a one-shot `delegate_task` dispatch in interactive mode with a trivial task ("list 3 files in /tmp"). Confirm a child AIAgent spawns, completes, and returns result. If it fails (e.g., a config/plumbing issue), H1 Rule 2 is fiction regardless of any addendum text.

6. **Golden task dry run (GT-6-hermes, GT-7-hermes):** Run once against current HERMES.md (before installing the skill). Establishes the failure mode baseline. After skill install, re-run — improvement or no-improvement becomes the primary signal for whether the addendum's work is effective.

**Reference to existing golden tasks:** `evaluation/golden-tasks.md` contains GT-1 through GT-7. GT-6 (Late-Session Delegation Resistance) and GT-7 (Context Health Gate Activation) are the Claude Code canonicals. Worker B §2 and §11 reinforce that golden tasks are the regression-catching mechanism for behavioral drift.

---

## 9. Open questions for the human operator

1. **Is `claude --acp --stdio` delegation a live capability or aspirational?** Worker C §12 Q1. Neither `claude` nor `copilot` is installed on ubuntu-vm. Is Hermes running on another machine too, with those binaries present? Or is the "External CLI" tier of the routing description something you expect to add, not something that runs today? This directly shapes R5 and the accuracy of HERMES.md / the skill draft.

2. **Did you ever observe Gemma emit `[TASK CLASS: ...]` in practice?** Worker C found zero across three recent sessions. If you have seen it work in older sessions, please share a `sessions_archive/` pointer — the probe in R1 would then need to isolate the conditions that make it work vs. not work.

3. **Is `smart_model_routing.enabled: false` intentional, or forgotten?** Worker C §6 notes the "Simple/Complex/Implementation" router you described to Worker C is the exact routing rule the **code supports but is disabled.** Did you turn it off during a debugging session and forget to re-enable? Or was the tri-tier description what you wanted to build, not what you built? The answer changes what "routing" means in the r6 plan.

4. **Is the Jira-daily-briefing benchmark score of 30/40/20/10 still current?** H11 treats these as baseline. When was the last measured run? If the baseline has drifted, H11's acceptance criteria are against stale numbers.

5. **Should the Hermes addendum pick up Sonnet 4.6's marker-elision tunings?** R2 argues yes — Gemma is more prone to elision than Sonnet. But you may have a reason for keeping the Hermes addendum insulated from Sonnet-specific findings (e.g., separate evolution tracks). This is a deliberate choice.

6. **What's the expected primary main-session iteration cap?** Worker C saw `DEFAULT_MAX_ITERATIONS=50` for children but didn't probe the main-session cap. Addendum says 60. Which is right?

7. **Do you actually want the hermes-harness skill to be the activation surface, or is the existing prompt_builder auto-discovery (HERMES.md) acceptable?** The addendum's H0 rationale includes a factual error (Gap 9 — "requires prompt_builder edit" is false because the mechanism exists). The skill approach has legitimate benefits (opt-in, cron isolation), but the existing approach also works. Which pain point are you optimizing for?

8. **Are there sessions in `sessions_archive/` or `state.db` that show successful `delegate_task` usage?** Worker C searched three recent JSONL files and found zero. If older sessions show the tool being invoked, we need to understand what changed. If never, we need to understand why `delegate_task` is in the tool definition but not in the observed behavior.

---

## 10. Summary — the judge's core finding

The r6 Hermes addendum is **careful, well-scoped, cross-model-safe, and missing its most important empirical input**. It specifies a harness adaptation for a set of Hermes primitives (`todo`, `delegate_task`, IterationBudget, compression) that exist in code. It acknowledges risk (Gemma structured output) and mitigates the highest-impact path (cron benchmark regression via H11). Its variant-diff carve-out (H12) and golden task additions (H13) are correctly structured and preserve cross-model integrity for the Claude Code / Generic / Sonnet-tuned variants.

The load-bearing gap is Gap 1: **HERMES.md is already loaded every turn; the agent does not follow it.** Across three recent live sessions, zero protocol markers, zero delegate_task calls, zero PROGRESS.md artifacts. The addendum treats the *loading* problem as the bottleneck (via H0 skills-based load); Worker C's data shows the *adherence* problem is the bottleneck. Reconfiguring how the instruction text reaches the model does not cause the model to execute it.

The fastest path forward is R1 (empirical probe) and R2 (Sonnet-style hard-output-contract framing). H10, H11, H12, H13 are all worth shipping regardless. H1, H3, H4 should not ship until R1 establishes they're not specs for a harness that doesn't run.

---

**End of judge synthesis.**
