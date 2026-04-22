# ARTIFACT — Worker B: External Dossier on Claude Opus 4.7

Produced 2026-04-17 for AgentFW tuning. Worker scope: read-only web research.

Reliability tiers:
- **Official** — Anthropic-owned domain (anthropic.com, claude.com, platform.claude.com, support.claude.com)
- **Reputable** — Named reporter at a recognized outlet, primary-cloud provider blog, or widely-read dev publication
- **Rumor** — Single-source aggregators, SEO-farm blogs, or derivative "explainer" pages. Treat as directional only.

---

## 1. Source inventory

| # | URL | Tier | One-line note |
|---|-----|------|---------------|
| 1 | https://www.anthropic.com/news/claude-opus-4-7 | Official | Primary announcement. Benchmarks, positioning, safety profile. |
| 2 | https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7 | Official | Authoritative "what's new" doc. Breaking changes, behavior deltas, migration. |
| 3 | https://platform.claude.com/docs/en/about-claude/models/migration-guide | Official | Full migration guide and checklist. Most actionable source. |
| 4 | https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code | Official | Anthropic's own Claude Code best-practices guide for 4.7. |
| 5 | https://platform.claude.com/docs/en/build-with-claude/effort | Official | Per-effort-level guidance (low/medium/high/xhigh/max) for Opus 4.7. |
| 6 | https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking | Official | Adaptive thinking is the only supported thinking mode on 4.7. |
| 7 | https://platform.claude.com/docs/en/build-with-claude/context-windows | Official | 1M context, server-side compaction notes. |
| 8 | https://github.blog/changelog/2026-04-16-claude-opus-4-7-is-generally-available/ | Reputable | GitHub's GA announcement (Copilot integration). |
| 9 | https://aws.amazon.com/blogs/aws/introducing-anthropics-claude-opus-4-7-model-in-amazon-bedrock/ | Reputable | AWS Bedrock launch post. |
| 10 | https://www.cnbc.com/2026/04/16/anthropic-claude-opus-4-7-model-mythos.html | Reputable | CNBC — positioning vs. unreleased "Mythos" and cyber safeguards. |
| 11 | https://www.axios.com/2026/04/16/anthropic-claude-opus-model-mythos | Reputable | Axios — confirms Mythos still benchmarks higher. |
| 12 | https://venturebeat.com/.../anthropic-releases-claude-opus-4-7-narrowly-retaking-lead-... | Reputable | VentureBeat benchmark roundup. |
| 13 | https://siliconangle.com/2026/04/16/anthropic-launches-claude-opus-4-7-coding-visual-reasoning-improvements/ | Reputable | Vision and coding improvements. |
| 14 | https://thenextweb.com/news/anthropic-claude-opus-4-7-coding-agentic-benchmarks-release | Reputable | Compares to GPT-5.4 and Gemini 3.1 Pro. |
| 15 | https://www.vellum.ai/blog/claude-opus-4-7-benchmarks-explained | Reputable | Granular benchmark table. Surfaces the BrowseComp regression. |
| 16 | https://www.helpnetsecurity.com/2026/04/16/claude-opus-4-7-released/ | Reputable | Cybersecurity-safeguard framing. |
| 17 | https://news.ycombinator.com/item?id=47793411 | Reputable | HN community discussion thread on 4.7 launch. |
| 18 | https://news.ycombinator.com/item?id=47793546 | Reputable | HN thread on the 4.7 model card. |
| 19 | https://simonwillison.net/ | Reputable | Simon tested 4.7 via pelican-on-bicycle; used 4.7 for Datasette 1.0a28. |
| 20 | https://github.com/anthropics/claude-code/issues/34685 | Reputable | Claude Code bug report documenting Opus 4.6 self-reporting context degradation at 40–48%. Carries over as 4.7 baseline concern. |
| 21 | https://www.threads.com/@boris_cherny/post/DXMqkOkFOGr/ | Reputable | Anthropic staff (Boris Cherny) quote: "more agentic, more precise … carries context across sessions." |
| 22 | https://www.finout.io/blog/claude-opus-4.7-pricing-the-real-cost-story-behind-the-unchanged-price-tag | Reputable | Tokenizer-driven effective price increase of 0–35%. |
| 23 | https://www.theregister.com/2026/04/17/claude_opus_wrote_chrome_exploit/ | Reputable | El Reg — researcher used 4.7 to produce a working Chrome exploit for $2,283. |
| 24 | https://llm-stats.com/blog/research/claude-opus-4-7-vs-opus-4-6 | Reputable | Aggregated benchmark comparison 4.7 vs 4.6. |
| 25 | https://www.labellerr.com/blog/claude-opus-4-7-vs-opus-4-6-comparison/ | Rumor | SEO-style rewrite; used only to corroborate. |
| 26 | https://hackernoon.com/claude-opus-47-is-here-and-it-changes-the-coding-model-race | Rumor | Derivative recap. |
| 27 | https://claudefa.st/blog/models/claude-opus-4-7 | Rumor | Fan site; fetch flagged this explicitly. |
| 28 | https://lushbinary.com/blog/claude-opus-4-7-developer-guide-benchmarks-vision-migration/ | Rumor | Aggregator explainer. |
| 29 | https://dev.to/speedy_devv/claude-opus-47-what-actually-changed-for-agentic-coding-4i27 | Rumor | Developer blog, one author. |
| 30 | https://adam.holter.com/claude-opus-4-7-delivers-autonomy-gains-on-hard-coding-tasks/ | Rumor | Single-author blog. |
| 31 | https://dgtldept.substack.com/p/claude-opus-4-6-actually-did-get-dumber-regression-fixes | Rumor | Historical — on Opus 4.6 complaints that motivated 4.7 changes. |
| 32 | https://blog.matthewbrunelle.com/the-claude-coding-vibes-are-getting-worse/ | Rumor | Historical — 4.6-era context-rot complaints. |

Total: **32 sources consulted** (7 official, 17 reputable, 8 rumor-tier).

---

## 2. What we know — verified facts about Claude Opus 4.7

All facts below cross-checked against at least one **official** source unless noted otherwise.

### Identity & release
- Model ID: `claude-opus-4-7`. Released **April 16, 2026**. Successor to Opus 4.6 (Feb 2026). [Official: announcement, whats-new]
- Anthropic's "most capable generally available model to date" — but explicitly **behind** the (still-unreleased) **Claude Mythos Preview** on most frontier benchmarks. [Official + CNBC, Axios]
- Pricing unchanged vs. 4.6: **$5 / MTok input, $25 / MTok output**. [Official]

### Spec sheet
- **Context window:** 1M tokens at standard API pricing (no long-context premium). [Official]
- **Max output:** 128k tokens. [Official]
- **Tokenizer:** NEW. Same input maps to **1.0×–1.35×** as many tokens as 4.6 (up to ~35% more). [Official]
- **Thinking:** Adaptive thinking is the **only supported mode**. `thinking: {type: "enabled", budget_tokens: N}` returns a 400. Adaptive is **off by default**; must be explicitly enabled via `thinking: {type: "adaptive"}`. [Official]
- **Sampling parameters removed:** Setting `temperature`, `top_p`, or `top_k` to any non-default value returns a 400. [Official]
- **Thinking display default changed to `"omitted"`** (was `"summarized"` on 4.6). Need to opt in for summarized reasoning text. [Official]
- **Prefill removed** (since Opus 4.6, still enforced). [Official]

### Effort levels (Opus 4.7)
Per Anthropic's effort doc:
- `low` — short scoped tasks only; pair with explicit checklists.
- `medium` — cost-sensitive default for routine workflows.
- `high` (API default) — intelligence-sensitive work; sweet spot for many use cases.
- **`xhigh` (NEW)** — "the recommended starting point for coding and agentic work." Default effort in Claude Code is now xhigh.
- `max` — "reserve for genuinely frontier problems … on most workloads max adds significant cost for relatively small quality gains, and on some structured-output or less intelligence-sensitive tasks it can lead to overthinking."
- **Effort calibration is stricter** than on 4.6 — especially at low/medium, the model scopes its work to what was asked rather than going above and beyond.

### Task budgets (beta, new in 4.7)
- Beta header: `task-budgets-2026-03-13`. Advisory token budget across full agentic loop. Model sees a running countdown. Minimum 20k tokens. Do **not** set for open-ended work where quality beats speed. [Official]

### Key benchmark numbers (from Vellum + Anthropic sources; Vellum cross-checked Anthropic's card)
- **SWE-bench Verified:** 87.6% (↑ from 80.8%)
- **SWE-bench Pro:** 64.3% (↑ from 53.4%; +10.9 pts). Beats GPT-5.4 (57.7%) and Gemini 3.1 Pro (54.2%).
- **Terminal-Bench 2.0:** 69.4% (↑ from 65.4%). Mythos still leads at 82.0%.
- **MCP-Atlas (tool use):** 77.3%. "+14.6 pt jump — largest single improvement in the agentic suite."
- **OSWorld-Verified (computer use):** 78.0% (↑ from 72.7%)
- **CursorBench:** 70% (↑ from 58%; +12 pts)
- **GPQA Diamond:** 94.2% (↑ from 91.3%)
- **CharXiv visual reasoning:** 82.1% (no tools) / 91.0% (with tools)
- **Humanity's Last Exam (with tools):** 54.7%
- **Needle-in-a-Haystack:** 98.5% accuracy across 1M context. [Startup Fortune; needs corroboration — plausibly from Anthropic's card]
- **BrowseComp:** 79.3% — **down 4.4 pts from 4.6**, trailing GPT-5.4 Pro (89.3%) and Gemini 3.1 Pro (85.9%). **Only notable regression.**
- **Rakuten-SWE-Bench:** Anthropic claims 3× more production tasks resolved vs. 4.6.

### Safety / alignment
- "Largely well-aligned and trustworthy, though not fully ideal." [Official]
- Higher than 4.6 on **10 of 15** Anthropic behavioral dimensions.
- Improvements in **honesty** and **prompt-injection resistance**.
- Modestly **weaker** on harm-reduction advice about controlled substances.
- **New real-time cybersecurity safeguards**: prohibited/high-risk requests can trigger refusals. Legitimate security researchers must apply to the Cyber Verification Program.

---

## 3. Behavior deltas vs. Opus 4.6

Each item below is mentioned in Anthropic's **whats-new** or **migration-guide** page (both official). These are the AgentFW-relevant bits.

1. **More literal instruction-following.** "Will not silently generalize an instruction from one item to another, and will not infer requests you didn't make." Prompts tuned for 4.6's looser interpretation may underperform. Especially pronounced at low/medium effort.

2. **Response length now calibrates to task complexity** rather than a fixed verbosity default. Simple questions get shorter answers; open-ended analysis gets longer. Existing "be concise" scaffolding may need re-tuning.

3. **Fewer tool calls by default.** Reasons more, tools less. To increase tool use, raise effort or add explicit per-tool guidance.

4. **Fewer subagents by default.** The model is more judicious about delegation. *Explicitly request fan-out when you want it.* "Spawn multiple subagents in the same turn when fanning out across items or reading multiple files."

5. **Self-verification is built in.** "Devises ways to verify its own outputs before reporting back." Anthropic explicitly suggests **removing** scaffolding like "double-check the slide layout before returning" and re-baselining.

6. **Built-in progress updates during long agentic traces.** Anthropic suggests **removing** scaffolding like "After every 3 tool calls, summarize progress" and re-baselining.

7. **More direct, less validation-forward tone.** Fewer emoji. More opinionated.

8. **Better file-system-based memory use.** Writes scratchpads/notes more effectively and leverages them in later turns. Pairs with the client-side memory tool.

9. **Stricter effort calibration.** Low/medium do what is asked, not more. If under-thinking on complex problems, **raise effort rather than prompting around it.**

10. **xhigh effort level** — new, between high and max. Best for coding and agentic use cases. Default in Claude Code.

11. **Task budgets (beta)** — the model self-paces against an advisory budget. Distinct from `max_tokens` (hard cap, model-unaware).

12. **Adaptive-only thinking + interleaved thinking on by default.** Interleaved between tool calls.

13. **Thinking content omitted by default** — streaming UIs will see a long pause before output unless `display: "summarized"` is set.

14. **High-resolution vision.** Max image resolution up to 2576px / 3.75MP (was 1568px / 1.15MP). Pointing/bounding-box coords are 1:1 with pixels (no scale-factor math). Improves screenshot understanding and computer use.

15. **Cybersecurity refusal layer added.** Previously allowed security queries may now refuse; verified researchers apply to the Cyber Verification Program.

Staff commentary (Reputable tier): Boris Cherny (Anthropic Claude Code) on Threads: "more agentic, more precise, and a lot better at long-running work. It carries context across sessions and handles ambiguity much better."

---

## 4. Gaps — what AgentFW tuners still can't verify

These are questions whose answers would directly change AgentFW but are not publicly documented as of today.

1. **Effective context length under agentic load.** Anthropic advertises 1M with 98.5% needle-in-haystack. But documented self-reported degradation on Opus 4.6 started at ~20% context in real Claude Code sessions (see GH issue 34685). There is **no published 4.7-specific curve**. Anthropic's own recommendation of server-side compaction implies "context rot" remains a factor but is not quantified.

2. **Planner-worker-judge behavior empirical data.** Anthropic documents that 4.7 "spawns fewer subagents by default" and is more self-verifying — both structurally relevant to AgentFW's role-separation rule — but **no public data** on whether self-verification is as reliable as an independent judge context. AgentFW's prior rule ("a context that wrote the code cannot verify the code") likely still holds, but Anthropic has not confirmed or denied it for 4.7.

3. **Hallucination / protocol-violation rates under long traces.** "Scored higher on 10 of 15 behavioral dimensions" is qualitative. No published numbers on rule-adherence decay across context depth, which is AgentFW's core concern (the 3-task re-read cadence was designed around this).

4. **How strict is "strict effort calibration" really?** Anthropic says low/medium "scope to what was asked." What is the measurable floor — does that mean the model will refuse to do a 4-step plan if you ask at low effort, or just truncate? Not stated.

5. **Task-budget interaction with subagents.** Beta docs don't clarify whether the budget is shared across spawned subagents or re-started per-subagent. Matters for AgentFW's dispatch accounting.

6. **Cross-session memory semantics.** Boris Cherny says "carries context across sessions." Official docs say only that the model is "better at writing and using file-system-based memory" — implying the persistence is still file-based, not model-intrinsic. Unverified whether anything has changed on the server side for Claude.ai sessions.

7. **Whether "adaptive thinking" changes judge-style prompts.** Judges benefit from deliberate thinking; if adaptive decides to skip thinking for what looks like a short evaluation prompt, judge quality degrades silently. No public guidance.

8. **Real refusal-rate change for DevOps / security-adjacent code.** The new cyber safeguards are advertised as targeted, but HN thread comments (rumor-tier) include reports of false-positive refusals. Not confirmed with scale.

9. **The **1M context variant as a distinct thing.** The "Opus 4.7 1M" variant mentioned in the task brief appears to be the same model — the 1M window is the default, not a separate tier. We found **no evidence** of a separate "1M variant" SKU with different pricing or degradation characteristics. (Claude Agent SDK model ID is `claude-opus-4-7[1m]` per this session's own env, but public docs don't distinguish.)

10. **Empirical Tau-bench numbers.** Searched; not in Anthropic's published cut. Present only in a few rumor-tier roundups, inconsistent — omit from tuning decisions.

---

## 5. Tuning-actionable signals for AgentFW

Concrete, ready-to-apply changes. Each tagged with the official source supporting it.

### A. Effort and thinking defaults — structural
- **Default to `xhigh` effort for AgentFW workers doing implementation or investigation work.** [effort doc, best-practices doc]
- **Default to `high` for judges** — enough to guarantee thinking, avoids `max`'s tendency to overthink structured outputs. [effort doc]
- **Use `low` or `medium` only for short scoped tasks** (e.g., mechanical file-moves, lookups). Pair with explicit checklists. [migration guide]
- **Always explicitly enable adaptive thinking** (`thinking: {type: "adaptive"}`); it is off by default on 4.7. [whats-new]
- For interactive workflows where user watches streaming, **set `thinking.display: "summarized"`** so the user doesn't see a silent pause. [whats-new]

### B. Prompt changes — remove scaffolding that 4.7 now does natively
- **Delete "double-check your work before returning"** scaffolding. 4.7 self-verifies. [whats-new: Knowledge work]
- **Delete "after every N tool calls, summarize"** — 4.7 gives built-in progress updates. [migration guide]
- **Review verbosity-control prompts.** 4.7 calibrates to task complexity automatically; old "be concise" overrides may over-truncate complex outputs. Positive examples beat negative instructions. [migration guide]

### C. Prompt changes — ADD scaffolding that 4.7 now suppresses by default
- **Explicitly request subagent fan-out when desired.** 4.7 spawns fewer by default. Phrase like: "Spawn one subagent per independent file in the same turn." [best-practices doc]
- **Be more literal and explicit.** 4.7 won't generalize an instruction from one item to another. List items explicitly rather than relying on "and similar." [migration guide]
- **If you need more tool calls, say so explicitly**, or raise effort. 4.7 reasons more, tools less. [whats-new]

### D. Structural-enforcement fit with AgentFW's existing rules
- **Classification gate (Rule 1) is reinforced** — more literal instruction-following means explicit `[TASK CLASS]` outputs will actually be produced rather than generalized-away. Keep.
- **Role separation (Rule 2) remains necessary.** Anthropic documents built-in self-verification but makes no claim that it substitutes for an independent judge. AgentFW's separation principle is not contradicted.
- **Judge shielding (Rule 3) still valid.** No change.
- **Progress.md re-read cadence (Rule 4, 3-task cadence)** remains justified. No published data changes the degradation picture. Historical 4.6-era self-reported degradation at ~20–48% context usage is *unaddressed* in 4.7 docs. Recommend keeping the cadence — possibly tightening if using long worker contexts.
- **"When in doubt, decompose" (Rule 5)** aligns with Anthropic's own explicit guidance: spawn multiple subagents for fan-out across files/items.

### E. Token / budget tuning
- **Raise `max_tokens` headroom ~35%** everywhere to absorb the tokenizer change. [whats-new]
- **At `xhigh` or `max` effort, set `max_tokens` ≥ 64k.** [best-practices doc]
- **Consider adopting task budgets (beta) for bounded worker dispatch** — e.g., "you have 50k tokens to complete this investigation." Use `task-budgets-2026-03-13` beta header. Do NOT apply to judges or to open-ended exploration. Minimum 20k. [whats-new]

### F. Context-degradation hygiene (AgentFW's signature concern)
- **Treat usable agentic context as well below 1M.** Community reports from the 4.6 era (GH issue 34685) had the model itself recommending restart at ~48% usage. Anthropic's 4.7 doc does not refute this and continues to recommend **server-side compaction** for long sessions. For AgentFW: keep per-worker context tight; prefer fresh dispatches over "just keep going."
- **Server-side compaction beta is available** for Opus 4.7 — worth integrating as a fallback, but don't rely on it for judge-quality verification. [context-windows doc]
- **Use file-system-based memory more aggressively.** 4.7 is "better at writing and using" scratchpads. Aligns with PROGRESS.md/PLAN.md pattern. [whats-new: Memory]

### G. Watch-outs / known regressions
- **BrowseComp −4.4 pts.** If AgentFW workflows rely heavily on web-research/browse-style tasks, 4.7 is *worse* than 4.6 at some of this and trails GPT-5.4 Pro and Gemini 3.1 Pro meaningfully. Consider routing research-heavy subtasks differently, or compensating with stronger explicit search guidance.
- **Cyber safeguards may refuse legitimate tasks.** If AgentFW is used for security research, plan for false-positive refusals and possibly the Cyber Verification Program application.
- **Streaming UIs will show pauses** unless `display: "summarized"` is explicitly set.
- **Client-side token estimators will under-count.** Any AgentFW code that pre-estimates context usage from character count will be off by up to 35%.

### H. Opus 4.7 1M variant specifics
No evidence the "1M variant" is a distinct SKU — 1M is standard on Opus 4.7. The env-reported model ID `claude-opus-4-7[1m]` appears to be a Claude Agent SDK / Claude Code internal alias for the 1M-enabled context routing, not a separate model. Treat tuning guidance above as applying to both "normal" and "1M" usage patterns. Needle-in-haystack holds at 98.5% per Anthropic's claim, but agentic-context quality degradation at depth is the real constraint, not retrieval accuracy.

---

## Open questions worth re-checking in 2–4 weeks

- Independent long-context degradation curves (Needle-in-Haystack is necessary, not sufficient).
- First thorough Simon Willison / third-party eval write-up on 4.7 (his weblog so far has only brief mentions).
- Real-world refusal rate data for the new cyber safeguards.
- Any follow-up from Anthropic on Mythos, since 4.7 is publicly positioned as "second-best to Mythos."
- Whether Anthropic publishes more granular data on the "10-of-15 behavioral dimensions" honesty claim.
