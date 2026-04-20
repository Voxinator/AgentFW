# ARTIFACT — Worker α — Hermes System-Prompt Anatomy

Session analyzed: `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json`
Model: `gemma-4-31b-it-4bit`   Platform: `cli`   Provider: `custom` (local oMLX at 10.211.55.2:8000)
Variant: `HERMES-variantD.md` (Hard Contract + Dispatch Scaffolding, 230 lines)

---

## 1. Prompt builder overview

The system prompt is assembled by `AIAgent._build_system_prompt()` in
`/home/parallels/.hermes/hermes-agent/run_agent.py` lines 2582–2745.
Helper functions live in `/home/parallels/.hermes/hermes-agent/agent/prompt_builder.py`.

Assembly is a simple `prompt_parts: list[str]` that is joined with `\n\n` at the end. The
order of `.append(...)` calls is the on-wire order (no re-sorting). Concretely:

```
prompt_parts = []

# Slot 1 — Identity
if load_soul_md():
    prompt_parts = [SOUL.md]        # primary identity (when HERMES_HOME/SOUL.md exists)
else:
    prompt_parts = [DEFAULT_AGENT_IDENTITY]  # fallback hardcoded string

# Slot 2 — Tool-aware behavioral guidance (joined with a single space)
tool_guidance = []
if "memory"         in valid_tool_names: tool_guidance.append(MEMORY_GUIDANCE)
if "session_search" in valid_tool_names: tool_guidance.append(SESSION_SEARCH_GUIDANCE)
if "skill_manage"   in valid_tool_names: tool_guidance.append(SKILLS_GUIDANCE)
if tool_guidance: prompt_parts.append(" ".join(tool_guidance))

# Slot 3 — Nous subscription block (empty for this session)
prompt_parts.append(build_nous_subscription_prompt(...))  # "" here

# Slot 4 — Tool-use enforcement (model-gated)
if model matches ("gpt","codex","gemini","gemma","grok"):
    prompt_parts.append(TOOL_USE_ENFORCEMENT_GUIDANCE)
    if model contains "gemini" or "gemma":
        prompt_parts.append(GOOGLE_MODEL_OPERATIONAL_GUIDANCE)
    if model contains "gpt" or "codex":
        prompt_parts.append(OPENAI_MODEL_EXECUTION_GUIDANCE)

# Slot 5 — Caller-provided system_message (gateway-injected, usually None)
if system_message: prompt_parts.append(system_message)

# Slot 6 — Built-in memory store blocks
if memory_enabled: prompt_parts.append(MEMORY.md block)   # "memory"
if user_profile_enabled: prompt_parts.append(USER.md block) # "user"

# Slot 7 — External memory provider (honcho/supermemory/etc; empty here)
prompt_parts.append(memory_manager.build_system_prompt())

# Slot 8 — Skills index (only when skills tools registered)
prompt_parts.append(build_skills_system_prompt(...))

# Slot 9 — Project context files (HERMES.md is here)
#   Priority: HERMES.md > AGENTS.md > CLAUDE.md > .cursorrules
#   Wrapped with "# Project Context\n\nThe following project context files..."
prompt_parts.append(build_context_files_prompt(cwd=TERMINAL_CWD, skip_soul=True))

# Slot 10 — Timestamp / session / model / provider
prompt_parts.append(f"Conversation started: {now}\nModel: {model}\nProvider: {provider}")

# Slot 11 — Platform hint (one-paragraph string keyed on self.platform)
prompt_parts.append(PLATFORM_HINTS["cli"])

return "\n\n".join(prompt_parts)
```

Key structural facts:
- `delegate_worker` tool **schema** is NOT in the system prompt text — it is delivered via
  the OpenAI `tools` array as JSON schema.
- The `HOW TO DISPATCH WORKERS` scaffolding (with `<tool_call>` worked example) lives
  **inside HERMES.md**, which enters the system prompt via Slot 9 — i.e. deep in the
  middle of the prompt.
- SOUL.md is loaded **once** (either as identity at the top OR as a context file,
  never both). In this session SOUL.md came through as identity (Slot 1), so
  `skip_soul=True` when context files are built.
- The system prompt is **cached** on `self._cached_system_prompt` after first build and
  only rebuilt after compression events (for prefix-cache stability).

---

## 2. System prompt anatomy — byte-range map

Total: **36,165 chars / 36,684 bytes / 466 lines**.

| Byte range        | Size  | Section                                              |
|-------------------|------:|------------------------------------------------------|
| `[    0..  2411]` |  2.4K | **SOUL.md** (`# Hermes Agent Persona` + `# You are Hermes` + `## How you think` / `## Model reality` / `## Memory` / `## Your disposition`) |
| `[ 2412..  3779]` |  1.4K | **Tool-aware behavioral guidance** — MEMORY_GUIDANCE + SESSION_SEARCH_GUIDANCE + SKILLS_GUIDANCE (joined with single space) |
| `[ 3780..  4605]` |  0.8K | `# Tool-use enforcement` (TOOL_USE_ENFORCEMENT_GUIDANCE) |
| `[ 4606..  5699]` |  1.1K | `# Google model operational directives` (GOOGLE_MODEL_OPERATIONAL_GUIDANCE) |
| `[ 5700..  8074]` |  2.4K | **Built-in MEMORY block** (`MEMORY (your personal notes) [55% — 2,232/4,000 chars]`) |
| `[ 8075.. 12074]` |  4.0K | **Built-in USER PROFILE block** (`USER PROFILE (who the user is) [97% — 3,886/4,000 chars]`) |
| `[12075.. 23858]` | 11.8K | **`## Skills (mandatory)`** + `<available_skills>` index (54 skills across ~15 categories) |
| `[23859.. 23955]` |  0.1K | `# Project Context` wrapper header |
| `[23956.. 35970]` | 12.0K | **`## HERMES.md`** — full HERMES-variantD.md body. Internal structure: |
|  `[23970..24336]` |       |   — variant preamble (`# AgentFW — Core Instructions (Hermes Variant D — Hard Contract + Dispatch Scaffolding)`) |
|  `[24337..25304]` |       |   — `## CRITICAL: First-Line Output Contract` |
|  `[25305..25807]` |       |   — `## Why this matters` |
|  `[25808..27215]` |       |   — `## Classification criteria (enumerate ALL that apply …)` + `### one-shot`, `### structured`, `### long-horizon` |
|  `[27216..27953]` |       |   — `## Classification pressure — named failure modes` |
|  `[27954..29838]` |       |   — `## Planner-Worker-Judge Architecture` + `### HARD RULE: Role Separation` |
|  `[29839..33207]` |       |   — **`## HOW TO DISPATCH WORKERS — CRITICAL`** (with `<tool_call>` worked examples × 3) |
|  `[33208..34179]` |       |   — `## Permission Protocol` |
|  `[34180..35196]` |       |   — `## Session Protocol` + `### Start`, `### During`, `### End` |
|  `[35197..35970]` |       |   — `## Core Pattern: Decompose → Parallelize → Verify → Iterate` |
| `[35971.. 36071]` |  0.1K | Timestamp/session/model/provider line |
| `[36072.. 36164]` |  0.1K | `PLATFORM_HINTS["cli"]` ("You are a CLI AI Agent…") |

Observations:
- 66% of the system prompt is **pre-HERMES.md preamble** (bytes 0–23955).
- HERMES.md itself (including the variant header) occupies bytes 23,956–35,970 — the
  last ~33% of the prompt, but **not** the final bytes: the timestamp + platform hint
  sit after it.
- **Skills index is the single largest block** (11.8K / 33% of the prompt), sandwiched
  between USER profile and HERMES.md.

---

## 3. `HOW TO DISPATCH WORKERS` position analysis

Absolute location inside the system prompt:

| Metric                                   | Value      |
|------------------------------------------|------------|
| Start byte of `## HOW TO DISPATCH WORKERS — CRITICAL` | **29,839** |
| End byte (section runs to)               | **33,207** |
| Section length                           | **3.4K / ~9.3% of the prompt** |
| Distance from start of prompt            | 29,839 bytes (82% of the way through) |
| Distance from end of prompt              | 6,326 bytes (17% of the way from end) |
| Distance from last byte of HERMES.md     | 2,763 bytes after HERMES end (35,970) |
| `<tool_call>` worked example             | First appears at byte **30,109** |

What surrounds it:
- **Before** (bytes 27,954..29,838, 1.9K): Planner-Worker-Judge Architecture + HARD RULE
  Role Separation. This is prose *about* workers — high semantic overlap, good priming.
- **After** (bytes 33,208..34,179, 1.0K): Permission Protocol (a table of tiers). Lower
  semantic overlap; this is where attention peels off dispatch onto unrelated rules.
- **Tail of prompt** (bytes 34,180..36,164, 2.0K): Session Protocol + Core Pattern +
  timestamp + platform hint. The **very last** paragraph the model sees is
  "You are a CLI AI Agent. Try not to use markdown…" — not about dispatch.

The three `<tool_call>` worked examples inside the section are at bytes:
- 30,109 (template shape)
- 30,276 ("Implement a caching middleware…")
- 30,790 ("Verify that src/middleware/cache.ts…")

All three sit in the **middle-back quarter** of the prompt. None are near the recency
zone (final ~1K).

---

## 4. Tool schema delivery path

Tool schemas are **in the `tools` array**, not in the system prompt text. They are
handed to Gemma as OpenAI-format function definitions.

Session field: `tools` — **29 entries** (not 52 — the 52 in the background likely counts
the full tool registry pre-filter; the 29 here are what actually got bound for this
session). Total tool-schema payload: **38,364 bytes** (larger than the system prompt
itself at 36,684 bytes).

Order (alphabetical — `sorted()` is applied somewhere in tool binding):

```
 [ 0] browser_back              245 B
 [ 1] browser_click             465 B
 [ 2] browser_console         1,031 B
 [ 3] browser_get_images        330 B
 [ 4] browser_navigate          603 B
 [ 5] browser_press             398 B
 [ 6] browser_scroll            409 B
 [ 7] browser_snapshot          840 B
 [ 8] browser_type              504 B
 [ 9] browser_vision          1,012 B
 [10] clarify                 1,290 B
 [11] cronjob                 3,083 B
 [12] delegate_task           3,721 B   ← LARGEST single schema
 [13] delegate_worker         1,040 B   ← the dispatch primitive
 [14] execute_code            2,380 B
 [15] memory                  2,177 B
 [16] patch                   1,534 B
 [17] process                 1,229 B
 [18] read_file                 923 B
 [19] search_files            1,786 B
 [20] session_search          2,287 B
 [21] skill_manage            2,828 B
 [22] skill_view                826 B
 [23] skills_list               321 B
 [24] terminal                3,564 B
 [25] text_to_speech            684 B
 [26] todo                    1,646 B
 [27] vision_analyze            608 B
 [28] write_file                600 B
```

Position of `delegate_worker`: **index 13 of 29 (45th percentile, dead-middle)**.

Notable neighbours:
- Immediately preceding: `delegate_task` (index 12, 3.7K — nearly 4× the size of
  `delegate_worker`). For a model doing shallow schema scanning, the larger, more
  verbose `delegate_task` schema dominates attention over `delegate_worker`. There is
  also a real risk of `delegate_task` being picked as the dispatch primitive by
  accident — the model would need to read the HERMES.md prose (buried at bytes
  29,339+) to know "use `delegate_worker` not `delegate_task`."
- The "orient with terminal/search_files" bias has strong support in the tools array:
  `terminal` is the **second-largest schema** (3.6K at index 24) and `search_files`
  (1.8K at index 19) and `read_file` (923 B at index 18) are present in the
  middle-to-late part of the alphabetically-sorted list. Those are normal-looking,
  unambiguous primitives — easy wins for the model's next-tool selector.

---

## 5. Attention geometry assessment

On a 36,684-byte system prompt + 38,364-byte tool array + 200-byte user message
(~75 KB total input; ~18–20K tokens for Gemma's tokenizer), attention is not uniform.
Well-studied empirical biases on long-context decoder models:

1. **Sink tokens (prompt start)** — high attention. In Hermes these are SOUL.md
   persona lines ("You are Brian Taylor's personal Hermes agent…"). **Helpful for
   identity, irrelevant for dispatch.**

2. **Recency zone (prompt end, last ~500 tokens)** — high attention. In this session
   the recency zone contains:
   - Core Pattern paragraph (mentions `delegate_worker` at byte 35,438 — one mention,
     buried in prose)
   - Timestamp / Model / Provider line
   - `PLATFORM_HINTS["cli"]` — "You are a CLI AI Agent. Try not to use markdown…"

   **The last thing Gemma reads is a formatting hint about markdown, not a dispatch
   directive.** The recency slot is wasted on CLI-platform cosmetics.

3. **Middle attention ("lost in the middle")** — well-documented degradation for
   inputs >8K tokens. Bytes 12,000–24,000 (the skills index + project-context wrapper)
   are squarely in the attention valley. Fortunately `HOW TO DISPATCH WORKERS`
   (29,839..33,207) is **past** the deepest valley, but it's still ~6KB before the
   end — not in the recency zone.

4. **Keyword-fine-tuned attention** — Gemma-4-IT is a Google instruction-tuned model;
   it was NOT fine-tuned on AgentFW. Nothing in its training primes it to attend to
   `## HOW TO DISPATCH WORKERS — CRITICAL`. By contrast, it **was** trained to attend
   to:
   - Tool schemas in the `tools` array (Gemma function-calling format)
   - Natural `## ...` markdown headings (weak positive)
   - Recency and the very start (structural)

5. **Tool-array-driven planning** — Gemma's function-calling head reads the tools list
   when deciding what to emit. With `delegate_worker` at index 13/29 (middle, and
   half the size of the adjacent `delegate_task`), plus richer/longer schemas for
   `terminal`/`search_files`/`read_file`, the tool-selection prior leans toward
   "orient with read-only primitives" — exactly the observed bias.

Qualitative verdict: **The dispatch scaffolding is positioned in a local-maximum
section (end of HERMES.md, post-Planner-Worker-Judge priming) but the global prompt
geometry still puts it well behind the tool array in effective influence.** The tool
array's position-bias toward commonly-named, larger schemas wins the first-token race.

---

## 6. Reorder hypotheses

H1 — **Move HERMES.md from Slot 9 to Slot 4 (right after model-specific guidance, before memory/user/skills).**
Rationale: today HERMES.md sits behind ~24K bytes of SOUL.md + memory + USER profile
+ skills index. Promoting it to roughly byte 5,700 would place the Critical Rules and
HOW TO DISPATCH WORKERS inside the first third of the prompt — closer to the sink
zone. Risk: SOUL.md is the identity anchor; putting HERMES.md too close to it may
confuse persona. Mitigation: keep SOUL.md in Slot 1; insert HERMES.md right after
Google guidance.

H2 — **Move `HOW TO DISPATCH WORKERS` *out* of HERMES.md into a dedicated final slot,
  after `PLATFORM_HINTS`.**
Rationale: the recency zone is the second-highest-attention region and it is
currently occupied by a markdown-format hint. Swapping in the dispatch contract
(with the `<tool_call>` worked example) would put the operator in the last 3–4KB
the model reads before generating. Cost: the section would duplicate content that
already exists in HERMES.md unless HERMES.md is edited to remove its dispatch
subsection. Expected lift: highest of the three hypotheses.

H3 — **Reduce skills-index bulk or gate it behind `/skill` request.**
Rationale: `<available_skills>` is 11.8K bytes — the single largest section — and
sits in the attention valley. Most of it is irrelevant to the current task and
still consumes tokens that push HERMES.md further from the sink. Dropping to a
top-20 list or lazy-loading via `skill_view(name)` would reclaim ~10K bytes of
prompt real estate and pull HERMES.md ~30% closer to the start.

H4 — **Reorder the tool array so `delegate_worker` is first (or sort by
"dispatch-critical").**
Rationale: alphabetical ordering puts `browser_*` in positions 0–9 and
`delegate_worker` at 13. Many function-calling models give the first schemas a
token-level prior. Putting `delegate_worker` first — or at minimum ahead of
`delegate_task` — would reduce the "pick the big delegate_task by accident" risk
and lift the dispatch primitive's visibility. This is a tool-binding change, not
a prompt change.

H5 — **Shorten or remove `delegate_task` schema when `delegate_worker` is the
  intended dispatch primitive.**
Rationale: `delegate_task` (3.7K) is 3.5× the size of `delegate_worker` (1.0K) and
sits immediately before it in the array. Size-driven attention + alphabetical
adjacency means the model "sees" `delegate_task` more strongly. If HERMES.md says
"use `delegate_worker` not `delegate_task`" but the tools array puts `delegate_task`
first and bigger, the prompt is contradicting itself at the structural level.

---

## 7. Cheapest experiments to test

E1 — **Platform-hint swap (5-minute change; single-file edit to run_agent.py)**
Replace the final Slot 11 content: instead of emitting `PLATFORM_HINTS["cli"]` as the
last `prompt_parts` entry, emit a short dispatch-reminder like:
```
REMINDER: For structured tasks, your first tool call MUST be delegate_worker
with a complete goal string. See HOW TO DISPATCH WORKERS above.
```
Still surface the CLI markdown hint but before the reminder. Then re-run r7 eval.
If dispatch rate moves from 0–1/5 to ≥2/5, recency-zone theory is confirmed.

E2 — **Reorder: HERMES.md up to Slot 4 (30-minute change; edit `_build_system_prompt`
order)**
Move `build_context_files_prompt(...)` append to right after the Google guidance
append, before the memory/user blocks. Keep everything else identical. Re-run r7
eval. If dispatch rate improves but E1 did not, the middle-attention valley was the
problem.

E3 — **Trim skills index to 5 curated entries (15-minute config change;
`~/.hermes/skills/` prune or a temporary override in build_skills_system_prompt)**
Reduces 11.8K → ~1.5K, shortens system prompt by ~10K, pulls HERMES.md from byte
23,956 to ~13,956. No code changes to HERMES.md. Re-run r7 eval. This isolates the
"skills index is crowding out HERMES.md" hypothesis from the "HERMES.md is too far
from recency" hypothesis.

Cheapest single experiment to run first: **E1** (platform hint swap). It costs one
line of Python, leaves HERMES.md untouched, and directly tests the strongest
attention-geometry hypothesis (recency-zone occupancy by irrelevant content). If E1
moves the needle, promote it; if it doesn't, move to E3 (skills trim) before E2
(reorder).

---

## Appendix — key file paths

- Prompt builder helpers: `/home/parallels/.hermes/hermes-agent/agent/prompt_builder.py`
- Main assembly:          `/home/parallels/.hermes/hermes-agent/run_agent.py` lines 2582–2745
- HERMES variant D:        `/home/parallels/.hermes/hermes-agent/HERMES-variantD.md` (230 lines, active)
- SOUL.md (identity):      `/home/parallels/.hermes/SOUL.md`
- Session JSON:            `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json`
