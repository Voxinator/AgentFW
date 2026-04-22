# ARTIFACT — Worker δ — Tool-Surface Forensics

Session referenced: `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json`
(same session anatomised by Worker α — raw JSON lives on ubuntu-vm; local inspection
derives from Worker α's tool table and Worker ε's `toolsets.py` read).

Scope: what `delegate_worker` is competing with in Gemma's first-action decision.

Important calibration up front: the brief says "52 tools visible to Gemma". That
number is the full Hermes **tool registry** size (the `total tools: 52` printed by
`IMPLEMENTATION.md`'s verify step — it counts every tool imported into the registry,
including ones gated by `check_fn`). The **actual tool-array bound for this session**
is **29 entries** — `check_fn` filters prune memory-plugin tools, ACP extras, and
tools whose backends aren't active. Gemma's real tool surface in
`session_20260418_141126_4fe2e2` is 29, not 52. This artifact treats the 29-tool
array as the authoritative tool surface; where upstream claims assume 52, we flag it.

---

## 1. Tool inventory — the 29 bound tools in order

Raw source: `session_20260418_141126_4fe2e2.json` `tools[]` array (as extracted by
Worker α). Tools are **alphabetically sorted** — confirmed by visual inspection of
the list; this is consistent with `sorted()` being applied inside the tool-binding
path in `run_agent.py`.

Total tool-array payload size: **38,364 bytes** — larger than the entire system
prompt text (36,684 bytes). The schemas dominate.

| # | Name | Toolset category |
|---|---|---|
| 0 | `browser_back` | browser |
| 1 | `browser_click` | browser |
| 2 | `browser_console` | browser |
| 3 | `browser_get_images` | browser |
| 4 | `browser_navigate` | browser |
| 5 | `browser_press` | browser |
| 6 | `browser_scroll` | browser |
| 7 | `browser_snapshot` | browser |
| 8 | `browser_type` | browser |
| 9 | `browser_vision` | browser |
| 10 | `clarify` | clarify |
| 11 | `cronjob` | cronjob |
| 12 | `delegate_task` | delegation |
| 13 | **`delegate_worker`** | **delegation** |
| 14 | `execute_code` | code_execution |
| 15 | `memory` | memory |
| 16 | `patch` | file |
| 17 | `process` | terminal |
| 18 | `read_file` | file |
| 19 | `search_files` | file |
| 20 | `session_search` | session_search |
| 21 | `skill_manage` | skills |
| 22 | `skill_view` | skills |
| 23 | `skills_list` | skills |
| 24 | `terminal` | terminal |
| 25 | `text_to_speech` | tts |
| 26 | `todo` | todo |
| 27 | `vision_analyze` | vision |
| 28 | `write_file` | file |

**`delegate_worker` is at index 13 of 29 — middle of the list (45th percentile).**

Not in this session (present in registry's 52 but filtered out by `check_fn`):
memory-plugin tools (honcho, supermemory wrappers), `image_generate` (no image
backend bound on this VM), `send_message` (messaging transport off for CLI),
`mixture_of_agents`, `rl_*` training tools, `dashboard_tasks_*` (plugin not loaded).

---

## 2. Schema size table — ranked by bytes

| Rank | Tool | Bytes | Rough desc-length | Params | Notes |
|---|---|---:|---:|---:|---|
| 1 | **`delegate_task`** | **3,721** | ~1,400 ch | 6 (goal, context, toolsets, tasks, max_iterations, acp_command/acp_args) | Two-mode union schema (goal XOR tasks-array). **Largest single schema.** |
| 2 | **`terminal`** | **3,564** | ~1,300 ch | 4 (command, cwd, timeout, background) | Heavy description with side-effect warnings and examples. |
| 3 | `cronjob` | 3,083 | ~1,100 ch | 5 | Rarely-used, but expensive. |
| 4 | `skill_manage` | 2,828 | ~1,000 ch | 3 | |
| 5 | `execute_code` | 2,380 | ~800 ch | 3 (code, language, timeout) | |
| 6 | `session_search` | 2,287 | ~700 ch | 3 | |
| 7 | `memory` | 2,177 | ~800 ch | 3 | |
| 8 | `search_files` | 1,786 | ~650 ch | 5 (pattern, path, type, etc.) | Orientation primitive — rich schema. |
| 9 | `todo` | 1,646 | ~600 ch | 2 | |
| 10 | `patch` | 1,534 | ~500 ch | 3 (file_path, old_str, new_str) | |
| 11 | `clarify` | 1,290 | ~450 ch | 1 | |
| 12 | `process` | 1,229 | ~400 ch | 3 | Background-process control. |
| 13 | **`delegate_worker`** | **1,040** | **488 ch** | **1 (goal)** | Dispatch primitive. Smallest single-arg tool we want the model to pick. |
| 14 | `browser_console` | 1,031 | ~350 ch | 2 | |
| 15 | `browser_vision` | 1,012 | ~400 ch | 2 | |
| 16 | `read_file` | 923 | ~300 ch | 3 (file_path, start_line, end_line) | Orientation primitive. |
| 17 | `browser_snapshot` | 840 | ~300 ch | 1 | |
| 18 | `skill_view` | 826 | ~300 ch | 1 | |
| 19 | `text_to_speech` | 684 | ~200 ch | 2 | |
| 20 | `vision_analyze` | 608 | ~200 ch | 2 | |
| 21 | `browser_navigate` | 603 | ~200 ch | 1 | |
| 22 | `write_file` | 600 | ~200 ch | 2 | |
| 23 | `browser_type` | 504 | ~150 ch | 2 | |
| 24 | `browser_click` | 465 | ~150 ch | 1 | |
| 25 | `browser_press` | 398 | ~150 ch | 1 | |
| 26 | `browser_scroll` | 409 | ~150 ch | 2 | |
| 27 | `browser_get_images` | 330 | ~100 ch | 1 | |
| 28 | `skills_list` | 321 | ~100 ch | 0 | |
| 29 | `browser_back` | 245 | ~80 ch | 0 | |

**Dominance analysis — top 3 schemas account for 10,368 bytes (27%) of the entire
tool array:**
- `delegate_task` (3,721) + `terminal` (3,564) + `cronjob` (3,083) = 10,368 bytes.
- `delegate_worker` at 1,040 bytes is **3.6× smaller than `delegate_task` and 3.4×
  smaller than `terminal`**. Size-weighted attention puts the dispatch primitive at
  a severe disadvantage vs. the two tools it most needs to out-compete.

---

## 3. Competing-tools analysis — first action on a structured task

Task 4 is "Refactor the auth module to use the new session store. Three files need
changes: src/auth/session.ts, src/auth/middleware.ts, and tests/auth.test.ts."

For Gemma's first tool call after emitting `[TASK CLASS: structured]`, the natural
candidates are:

| Tool | Affordance | "Orienting?" | Why Gemma picks it first |
|---|---|---|---|
| `terminal` | run shell command | **Yes — primary** | SOUL.md (identity block) explicitly describes Hermes as "terminal-first"; the model's CLI training data is saturated with `ls`, `cat`, `grep` patterns. Schema is 2nd-largest, rich with examples. |
| `search_files` | ripgrep-style search | **Yes — strong** | 5-param schema, "search for pattern in codebase" framing; the obvious reply to "refactor" is "let me find the relevant files first". |
| `read_file` | open specific file | Yes — secondary | Only useful once paths are known; prose says "you can access any file directly". |
| `patch` | edit existing file | No — mutating | Gemma tends to go here AFTER orienting. Once it orients, it's already role-collapsed. |
| `write_file` | create/rewrite file | No — mutating | Same trap. |
| `todo` | track subtasks | Weak orienting | Can be used to "plan" in-session, which encourages main-session role retention. |
| `delegate_worker` | spawn subagent | Dispatching | Competes against all of the above; only 1 of 29 tools says "hand off". |

**The orienting-affordance disposition is Gemma's core problem.** `terminal` and
`search_files` both *feel* like "I'll just look first" — low-stakes, non-mutating,
recoverable. The model's prior is that orientation precedes action, and the tool
array offers two excellent-looking orientation primitives. `delegate_worker` is the
*only* tool in the array that requires Gemma to stop orienting and hand off.

### Do any competing tools DISCOURAGE use for structured tasks?

Scanning descriptions:

- `terminal` — no discouragement. Its schema description encourages use as the
  primary shell. Example commands for `ls`, `cat`, test runners.
- `search_files` — no discouragement. "Search for patterns... recursively..."
- `read_file` — no discouragement. "Access any file directly by using this tool."
- `patch` / `write_file` — mild hedges about destructive ops, no task-class gating.
- `todo` — neutral.
- `delegate_task` — famously has *"WHEN NOT TO USE: Single tool call → just call
  the tool directly"* (Hermes upstream text; called out in `DESIGN.md` as
  anti-dispatch). This is *worse than neutral* — it actively tells Gemma to skip
  dispatch when a task "feels like a single action".
- `delegate_worker` — the only tool with an **affirmative** "ALWAYS USE THIS TOOL
  when the task class is `structured` or `long-horizon`" statement.

**Net result:** `delegate_worker`'s description tries to assert primacy, but it
competes against 28 other descriptions that don't back off. Every tool in the array
effectively says "use me!" — a single tool saying "always use me for class X" is
just one voice in a crowd. And `delegate_task`'s "WHEN NOT TO USE: Single tool call"
clause is actively sabotaging `delegate_worker`'s message because Gemma reads
*both* descriptions and the anti-dispatch one registers.

---

## 4. Schema-description comparison — `delegate_worker` vs 5 competitors

Verbatim description language (edited for length; full text in
`variants/hermes/delegate_worker.py` line 22+ locally, and via SSH for the others).

### `delegate_worker` (1,040 B total, ~488 char description)
> "Spawn ONE worker subagent to complete a task in an isolated, fresh context. The
> worker has its own conversation, terminal, and toolset; only the final summary is
> returned to you.
>
> **ALWAYS USE THIS TOOL** when the task class is `structured` or `long-horizon`.
> Do NOT call patch, write_file, terminal, execute_code, or skill_manage directly
> from the main session for such tasks — dispatch to a worker via this tool
> instead.
>
> Pass everything the worker needs in the single `goal` argument — the worker has
> no memory of your conversation..."

**Assertiveness:** HIGH. Explicit "ALWAYS USE" + explicit list of forbidden
competing tools.

### `delegate_task` (3,721 B — 3.5× larger)
Has the infamous *"WHEN NOT TO USE: Single tool call → just call the tool directly"*
plus detailed `tasks[]` batch-mode instructions, ACP routing, toolset arguments.
**Undermines** `delegate_worker` directly: tells Gemma it's okay to "just call the
tool directly" when a task looks single-action. For Gemma's shallow classifier,
most tasks "look single-action".

**Assertiveness:** MIXED — strong prose about when to use, strong prose about when
NOT to use. Internally contradictory.

### `terminal` (3,564 B — 3.4× larger)
Uses "run a command in the terminal... you can use this for file operations,
running tests, git, anything". Provides ~8 worked examples. Strong positive
framing, no task-class caveats.

**Assertiveness:** HIGH. Broad-application language. "Anything" is a direct
competitor to "structured".

### `search_files` (1,786 B — 1.7× larger)
"Fast file pattern matching... supports full regex... use this for orientation,
finding definitions, finding usages." Explicit orientation framing with 4+ example
patterns.

**Assertiveness:** HIGH for orientation framing specifically — the exact
disposition that triggers role-collapse.

### `patch` (1,534 B — 1.5× larger)
"Make targeted edits... old_str must be unique... prefer this over write_file when
modifying existing files." Framed as the preferred mutation path.

**Assertiveness:** MEDIUM-HIGH. Says "prefer this" without task-class guard.

### `write_file` (600 B — smaller than `delegate_worker`)
"Write contents to a file. Overwrites if exists." No task-class guard.

**Assertiveness:** LOW (short description) but direct affordance for "create files".
Still in the way.

### Stack-up verdict

`delegate_worker`'s "ALWAYS USE THIS TOOL when structured/long-horizon" is the
**only** description in the array that gates behaviour on task class. Every other
tool says "use me!" unconditionally. Between the anti-dispatch clause in
`delegate_task` and the broad-use framings in `terminal`/`search_files`,
`delegate_worker`'s directive is diluted to ~1 of 29 voices — and the voice is
short (488 char). The signal is present; it is not load-bearing.

**Fix direction:** either add "ONLY USE FOR ONE-SHOT TASKS" language to competing
tools (very invasive — Hermes upstream text), or trim the competitor surface so
there are fewer voices (toolset restriction — see §6).

---

## 5. Tool-order position — attention implications

Position: **`delegate_worker` is at index 13 of 29 (45th percentile — dead middle).**

### Observed / suspected biases

1. **Alphabetical sort is the enemy.** The list is `sorted()` alphabetically, which
   pushes `browser_*` (10 tools) to the top (indices 0–9). Gemma's first 9 tool
   slots — the highest-attention part of the tool array — are all browser
   interactions the model will almost never use on a VM-local coding task. Pure
   waste of position.

2. **`delegate_task` precedes `delegate_worker`.** Indices 12 → 13. The 3.7K
   older-sibling schema is scanned first and is 3.5× larger. For a model doing
   shallow next-token selection, the larger adjacent schema dominates; risk of
   Gemma emitting a `delegate_task` call meant for `delegate_worker` is real, and
   upstream session data already shows Gemma reaching for `delegate_task` under
   variant B (pre-variant-D).

3. **Middle-of-list attention valley.** In tool-list ordering, the first few and
   last few positions get position-bias lift; the middle is where attention dips.
   Index 13 is squarely in the valley.

4. **Strong competitors cluster late.** `terminal` (24), `search_files` (19),
   `read_file` (18), `todo` (26), `write_file` (28) all appear in the second half.
   Gemma scans the full list once before emitting; the recency-biased last
   schemas are the common mutation/orientation primitives, not the dispatch
   primitive. By the time the model reaches the end, `terminal`'s 3.6K schema is
   the freshest in attention.

### Structural disadvantage summary

- Position 13 of 29 → middle attention valley.
- Preceded by 3.5×-sized competitor (`delegate_task`) that says "don't dispatch for
  single tool calls".
- Followed by 16 tools, of which 5 (`patch`, `read_file`, `search_files`,
  `terminal`, `todo`, `write_file`) are the exact competitors we want it to beat.
- Nothing in the ordering advantages `delegate_worker`.

**Cheap structural fix:** inject `delegate_worker` at index 0 by breaking the
alphabetical sort, or by adding a `priority` field to the schema and sorting
descending by priority before alphabetical. One ~10-line patch to wherever
`sorted()` is called inside tool binding.

---

## 6. Toolset composition options — minimal-to-full

Source: `~/.hermes/hermes-agent/toolsets.py` TOOLSETS dict, as inventoried in
Worker ε's artifact. 17 atomic/category toolsets. The CLI default (`hermes-cli`)
pulls in essentially everything.

### Atomic / category toolsets (what each includes)

| Toolset | Tools bundled | Gemma-relevant? |
|---|---|---|
| `delegation` | `delegate_task`, `delegate_worker` | Core — always want this on |
| `terminal` | `terminal`, `process` | **Role-collapse attractor** |
| `file` | `read_file`, `write_file`, `patch`, `search_files` | **Mixed — readers good, writers collapse** |
| `skills` | `skills_list`, `skill_view`, `skill_manage` | `skill_manage` is role-collapse attractor (Trial 9 mutated SKILL.md) |
| `todo` | `todo` | Orientation-adjacent; keep |
| `clarify` | `clarify` | Safe; keep |
| `memory` | `memory` | Harmless-ish; session-level |
| `code_execution` | `execute_code` | Role-collapse attractor |
| `session_search` | `session_search` | Safe; wander-tempting |
| `web` | `web_search`, `web_extract` | Distractor |
| `search` | `web_search` | Distractor |
| `browser` | 10 browser_* + web_search | Distractor, huge surface |
| `vision` | `vision_analyze` | Irrelevant for coding |
| `image_gen` | `image_generate` | Irrelevant |
| `tts` | `text_to_speech` | Irrelevant |
| `cronjob` | `cronjob` | Irrelevant; heavy schema |
| `messaging` | `send_message` | Not bound in CLI |

### Scenario/platform toolsets

- `safe` — `web + vision + image_gen`. **No terminal, no file.** (Interesting as a
  template; but no dispatch either, so useless as-is.)
- `debugging` — `terminal + process + web + file`. Heavy on attractors.
- `hermes-cli` (**default**) — expands to `_HERMES_CORE_TOOLS` which is every
  atomic toolset above except `mixture_of_agents` and `rl_*`. This is what Gemma
  sees by default.

### Minimal-to-full configurations, with estimated tool counts

| Configuration | Toolsets | Approx tool count | What gets exposed | Predicted dispatch effect |
|---|---|---:|---|---|
| **Full** (current default) | `hermes-cli` | **29** (the 52-registry-filtered-to-29 we see) | Everything | Baseline — 1/5 dispatch on Task 4 in r7.2 |
| **Deletion-heavy** | `delegation, todo, clarify, memory, web, browser, session_search, vision, image_gen, tts, cronjob` | ~22 (removes terminal/file/skills/code_execution) | No terminal, no file, no patch, no execute_code. Still wide surface of distractors. | Likely +1/5 — removes role-collapse but distractors remain |
| **Tier 3 (offenders removed)** | `hermes-cli-no-offenders` custom compound + `file_readonly` + `skills_readonly` | ~20 | Everything except terminal, process, write_file, patch, execute_code, skill_manage. Read-only file + read-only skills intact. | Predicted ~3/5 (Worker ε) |
| **Tier 1 (minimal orient-or-dispatch)** | `delegation, todo, clarify, file_readonly` | **5** (`delegate_task`, `delegate_worker`, `todo`, `clarify`, `read_file`, `search_files`) | Can read/search, plan, clarify, or dispatch. Cannot mutate. | Predicted ~3–4/5 (Worker ε) |
| **Tier 2 (dispatch-or-ask)** | `delegation, clarify` | **3** (`delegate_task`, `delegate_worker`, `clarify`) | Can dispatch or ask. No orientation possible. | Predicted 5/5 OR stall-by-hallucination; forcibly disambiguates tool-competition vs. disposition |

### Which configurations plausibly force dispatch?

- **Tier 2 (3 tools)** forces dispatch in the strongest sense — there is literally
  no other action that changes state or produces information. If Gemma still fails
  to dispatch here, the problem isn't the tool surface at all.
- **Tier 1 (5–6 tools)** keeps an orientation path (`read_file` + `search_files`)
  so the model isn't forced into dispatch, but removes every role-collapse
  attractor (`terminal`, `patch`, `write_file`, `execute_code`, `skill_manage`).
  If the model orients, it cannot then mutate — it must dispatch to change state.
  This is the experimentally cleanest configuration.
- **Tier 3 (~20 tools)** is the production-ready candidate — preserves wide
  surface (browser, web, memory) for other task classes while pruning the four
  known offenders. Good for shipping, weak for isolating hypotheses.

### Implementation cost per tier

- **Tier 1:** one `toolsets.py` entry (`file_readonly`, 5 lines), one CLI flag
  (`-t delegation,todo,clarify,file_readonly`). Reversible by `git checkout`.
- **Tier 2:** no code edit, pure CLI flag (`-t delegation,clarify`). Fully
  reversible.
- **Tier 3:** one compound `toolsets.py` entry (~20 lines across three toolsets),
  CLI flag.

---

## 7. Proposed A/B experiment — restricted-toolset probe

Design only; do not run without planner approval.

### Hypothesis

> Gemma's low dispatch rate on structured tasks is bottlenecked on the presence of
> competing "natural" orienting and mutating tools (`terminal`, `search_files`,
> `patch`, `write_file`, `execute_code`). Removing these from the tool surface
> should cause dispatch rate to rise significantly.

### Primary experiment — Tier 1 vs. baseline

**Control (already in the can):** r7.2 dense Task 4, default tool surface. Result:
1/5 dispatch across the 5-trial sweep.

**Treatment:** r7.3 dense Task 4, restricted toolset.

```bash
# One-time: add file_readonly toolset to toolsets.py
# (5-line dict entry, git-reversible)

# Per-trial invocation:
ssh ubuntu-vm "cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q \
  --max-turns 20 --checkpoints \
  -m gemma-4-31b-it-4bit \
  -t delegation,todo,clarify,file_readonly \
  --source probe-r7.3-restricted-tier1-task4-runN \
  -q \"<Task 4 text from probe-tasks.md §Task 4>\""
```

**N = 5 trials.** Matched against the r7.2 dense Task 4 baseline (same model, same
VM, same HERMES.md, same task text, same max-turns budget, same query phrasing).
Only variable: `-t delegation,todo,clarify,file_readonly` instead of default.

### Predicted outcomes & interpretation

| Dispatch result | Interpretation | Next step |
|---|---|---|
| 4/5 or 5/5 | Hypothesis confirmed — tool competition is the dominant failure mode. Ship restricted toolset as Gemma-default config. | Run Tier 3 to find minimum-impact production config. |
| 3/5 | Partial confirmation — tool surface matters but not exclusively. | Run Tier 3 and Tier 2 to disentangle. |
| 1–2/5 (≈ baseline) | Hypothesis falsified. Disposition runs deeper than tool competition. | Run Tier 2 — if that also fails, problem is model disposition or prompt positioning (see Worker α reorder hypotheses). |
| 0/5 with hallucinated tool calls | Model emitting `<tool_call>{"name": "terminal", ...}` for tools not in the array. Suggests training-prior dominance over tool schema — tool restriction is a dead end, need wrapper-level dispatch enforcer. | Abandon tool-restriction lever; revisit prompt-reorder (Worker α H1–H3) or synthesised-dispatch wrapper. |

### Secondary experiments (if Tier 1 lands)

1. **Tier 2** as disposition-sanity-check: if Tier 2 dispatch rate < Tier 1,
   orientation tools are a bigger contributor than mutators; if Tier 2 = Tier 1,
   mutators (`terminal`, `patch`, `write_file`, `execute_code`, `skill_manage`)
   are the entire story. Either answer is shippable.
2. **Tier 3** as production-config validation: dispatch rate across the full
   10-task probe suite under Tier 3 tells us if the restricted config generalises
   or if it's overfit to Task 4.
3. **Tool-order bias check (separate from toolset restriction):** hold tool set
   constant (Tier 1 configuration) and swap order so `delegate_worker` is at
   index 0 of the 5-6 tools. Should not change dispatch much at this small size,
   but tests whether order bias is a live signal independent of surface size.

### Cost estimate

- Tier 1 alone: 5 trials × ~4 min/trial = **~20 min wall-clock** + ~5 min
  `toolsets.py` edit + ~5 min wrapper flag edit. **~30 min total to decision.**
- Full tier 1 + 2 + 3 sweep (5 trials each, Task 4 only): ~60 min wall-clock +
  ~15 min setup. **~75 min to a shippable config.**

### Side-effect & risk assessment

- **Tier 1 mutation surface = zero.** No mutation tool is available, so mutation
  cannot happen regardless of what Gemma attempts. `--checkpoints` has nothing to
  checkpoint. `--yolo` not needed, must not be added.
- **Session-persist concern:** if the retry wrapper `--resume`s a session with a
  different `-t` flag, Hermes behaviour is untested. Mitigation: run the
  restricted-toolset trials WITHOUT the retry wrapper initially. Score attempt-0
  dispatch only. That's the signal we care about anyway.
- **Tool hallucination monitoring:** if Gemma emits `<tool_call>` for a tool
  absent from the array, Hermes will return `tool_not_found`. Log those as
  "dispatch-non-event" and treat them as signal for Outcome D above.

### Why this is the cheapest next experiment in the remediation chain

All five remediation workers' analyses converge on this: Worker α says "tool array
dominates prompt geometry for Gemma" (H4/H5), Worker ε has already designed the
toolsets.py patch and wrapper change, Worker δ (this document) confirms the surface
has 4 role-collapse-attractor tools in prominent positions — restricting the
surface is the minimum-invasive change that tests the dominant hypothesis. If it
moves the needle, the remediation is a config change, not a prompt rewrite or a
model swap.

---

## Appendix A — Where `delegate_worker`'s message gets drowned

To make the dilution concrete: count the characters of tool descriptions that say
"use me for general/structured tasks" versus `delegate_worker`'s 488-char
"ALWAYS USE THIS TOOL when structured/long-horizon".

Rough character budgets of pro-use framing across the 29 tools:
- `delegate_task` (~1,400 ch): explicit anti-dispatch clause
- `terminal` (~1,300 ch): "anything" framing, many examples
- `search_files` (~650 ch): orientation framing
- `patch` (~500 ch): "prefer this" framing
- `read_file` (~300 ch): "access any file" framing
- `todo` (~600 ch): planning framing
- Others (browser, skills, memory, cronjob, etc.): ~5,000 ch cumulative, all
  positive-use

Total competing positive-use framing: **~9,750 characters.**
`delegate_worker`'s directive: **488 characters.**
Ratio: ~20:1 against.

Even if Gemma weights `delegate_worker`'s description at 10× (because of "ALWAYS"),
it's still competing against 2× its emphasis-weighted volume from other schemas —
and the competing schemas have the natural cognitive advantage of describing
"how things get done" which primed-pretrained dispositions strongly favour.

---

## Appendix B — File paths referenced

- Session JSON (remote only): `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json`
- Tool registry import: `/home/parallels/.hermes/hermes-agent/model_tools.py`
- Toolset definitions: `/home/parallels/.hermes/hermes-agent/toolsets.py`
- CLI default resolution: `/home/parallels/.hermes/hermes-agent/hermes_cli/tools_config.py` (line 123)
- CLI toolset flag plumbing: `/home/parallels/.hermes/hermes-agent/hermes_cli/main.py` (line 644)
- Local `delegate_worker` source: `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker.py`
- Worker α anatomy (tool-array data): `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-alpha-prompt-anatomy.md`
- Worker ε toolset research: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-remediation-worker-epsilon-toolset-restriction.md`
- Task definitions: `/Users/briantaylor/Projects/AgentFW/probe-tasks.md` (Task 4, line 63)
- r7.2 baseline: `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense.md`
