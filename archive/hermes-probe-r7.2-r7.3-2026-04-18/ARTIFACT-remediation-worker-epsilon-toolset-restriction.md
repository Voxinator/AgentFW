# ARTIFACT — Worker epsilon: toolset-restriction experiment design

Status: READ-ONLY design. No experiments run. Do not execute without planner approval.

Source inspection: `~/.hermes/hermes-agent/toolsets.py` (via SSH to ubuntu-vm), `hermes chat --help`, `hermes_cli/main.py`, `hermes_cli/tools_config.py`, `hermes_cli/nous_subscription.py`, and the in-repo wrapper `probe-variantE-wrapper.sh`.

---

## 1. Hermes toolset mechanism

### Definition model
`toolsets.py` exposes a single `TOOLSETS` dict. Each entry has three fields:

```python
"<name>": {
    "description": "...",
    "tools":    [ ... list of tool-name strings ... ],
    "includes": [ ... list of other toolset names to compose in ... ],
}
```

The resolver (`resolve_toolset(name)` / `resolve_multiple_toolsets([names])`) walks `includes` recursively, de-duplicates tool names, and returns a flat list. Toolsets can therefore be composed from atomic toolsets or from scenario bundles.

### Atomic / category toolsets relevant to us
| Toolset | Tools |
|---|---|
| `web` | web_search, web_extract |
| `search` | web_search |
| `terminal` | terminal, process |
| `file` | read_file, write_file, patch, search_files |
| `skills` | skills_list, skill_view, skill_manage |
| `todo` | todo |
| `memory` | memory |
| `clarify` | clarify |
| `code_execution` | execute_code |
| `delegation` | delegate_task, delegate_worker |
| `session_search` | session_search |
| `vision` | vision_analyze |
| `image_gen` | image_generate |
| `browser` | browser_* (10 tools) + web_search |
| `tts` | text_to_speech |
| `cronjob` | cronjob |
| `messaging` | send_message |

### Scenario / platform toolsets
- `safe` — composes `web + vision + image_gen`. Notable: no terminal, no file.
- `debugging` — `terminal + process` plus `web + file`.
- `hermes-cli` — the DEFAULT for the CLI, expands to `_HERMES_CORE_TOOLS` (every atomic tool listed above except `mixture_of_agents` and the `rl_*` tools).
- `hermes-api-server`, `hermes-telegram`, `hermes-discord`, `hermes-acp` — platform-specific bundles, all roughly equivalent to the core set minus UI-only tools.

The important fact: **`-t/--toolsets` replaces the default `hermes-cli` bundle wholesale**. Whatever the user passes becomes the complete tool surface for the session (plus any memory-plugin-injected tools, which are orthogonal). There is no "subtract" flag — granularity is at the toolset level, not the individual tool level.

### CLI flag
`hermes chat -t TOOLSETS` / `--toolsets TOOLSETS` — value is a comma-separated list of toolset names (e.g. `-t delegation,clarify`). `hermes_cli/main.py` passes `args.toolsets` straight through to the agent constructor.

### Default resolution
`hermes_cli/tools_config.py` line 123 maps `"cli" -> default_toolset: "hermes-cli"`. If no `-t` flag, the CLI loads `hermes-cli`, which includes `terminal`, `file` (write_file + patch), `skills` (skill_manage), `code_execution`, AND `delegation`. All of Gemma's observed role-collapse offenders are live by default.

### Individual-tool disable?
Scanning toolsets.py, `tools_config.py`, and `main.py`: there is no `--disable-tools` or `--without` flag. Granularity is toolset-only. To "remove specific offenders" we have to construct a custom toolset via an edit to `toolsets.py` or by passing a list of atomic toolsets that excludes the offender categories.

---

## 2. Tier 1 experiment design — "minimal harness"

Goal: keep orientation tools (read_file, search_files) and planning (todo, clarify), but remove every mutation/execution tool. Gemma can still feel it is "orienting" but cannot fall into `terminal ls` → `write_file PLAN.md` → `patch SKILL.md` traps.

### Toolsets to enable
- `delegation` — provides `delegate_worker` (and `delegate_task`, harmless)
- `todo` — in-main-session planning
- `clarify` — ability to ask user questions
- **Partial `file`**: we want `read_file` + `search_files` but NOT `write_file` + `patch`. The atomic `file` toolset bundles all four, so tier 1 requires a **new toolset** in toolsets.py, e.g.:

```python
"file_readonly": {
    "description": "Read-only file access: read and search, no write/patch",
    "tools": ["read_file", "search_files"],
    "includes": []
}
```

That edit is the one non-reversible (well, git-reversible) piece of tier 1. No CLI-only path achieves read-only file access.

### CLI invocation
```bash
cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q --max-turns 20 --checkpoints \
  -m gemma-4-31b-it-4bit \
  -t delegation,todo,clarify,file_readonly \
  --source probe-r7.3-restricted-tier1-run1 \
  -q "<Task 4 text>"
```

### Excluded (silently absent)
terminal, process, write_file, patch, execute_code, skill_manage, skills_list, skill_view, browser_*, session_search, memory, web_*, vision_analyze, image_generate, tts, cronjob, messaging, ha_*, dashboard_task_*.

### Predicted outcome
Dispatch rate jumps from 1/5 to ~3-4/5. Residual non-dispatch attempts most likely become:
- (a) clarify calls ("what file should I look at?")
- (b) read_file / search_files exploration without dispatch, eventually running out of turns
- (c) attempt to call `terminal` and get a tool-not-found error, then pivot to dispatch on the next turn

If dispatch rate doesn't move, the hypothesis is falsified — see section 7.

---

## 3. Tier 2 experiment design — "dispatch-only"

Most restrictive. Gemma cannot orient at all; must dispatch or ask the user.

### Toolsets
- `delegation`
- `clarify`

### CLI invocation
```bash
cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q --max-turns 20 --checkpoints \
  -m gemma-4-31b-it-4bit \
  -t delegation,clarify \
  --source probe-r7.3-restricted-tier2-run1 \
  -q "<Task 4 text>"
```

### Predicted outcome
Two realistic modes:
1. Dispatch rate -> 5/5. Model has nothing else to reach for; `delegate_worker` is the shortest path to any useful action.
2. Stall / clarify-spam / failure. Gemma-31B dense may hallucinate tool calls it no longer has (e.g. emit `<tool_call>{"name": "terminal", ...}`), receive tool-not-found, and either loop on retries or emit a natural-language refusal ("I would need shell access to complete this task").

Mode (2) is informative: it shows the disposition is *so* locked onto terminal/write that it cannot route through dispatch even when given no alternative. That would point to a deeper training-data / prior issue, not a tool-competition issue.

---

## 4. Tier 3 experiment design — "remove offenders"

Surgical. Keep the default surface minus the four empirically-observed role-collapse triggers.

### Target exclusions
From Trial 5, 6, 9 in today's dense runs: `terminal`, `write_file`, `patch`, `skill_manage`, `execute_code`. Also pull `process` along with `terminal` (same atomic toolset) and leave `skills_list`/`skill_view` read-only alternatives to `skill_manage` removed for cleanliness.

### Approach
No individual-tool disable exists, so tier 3 requires either:

**Option A** (preferred — reversible via git): add two new compound toolsets to `toolsets.py`:

```python
"file_readonly": {
    "description": "Read + search only",
    "tools": ["read_file", "search_files"],
    "includes": []
},
"skills_readonly": {
    "description": "List + view skills, no manage",
    "tools": ["skills_list", "skill_view"],
    "includes": []
},
"hermes-cli-no-offenders": {
    "description": "hermes-cli minus terminal/process, write_file/patch, execute_code, skill_manage",
    "tools": [
        "web_search", "web_extract",
        "vision_analyze", "image_generate",
        "browser_navigate", "browser_snapshot", "browser_click",
        "browser_type", "browser_scroll", "browser_back",
        "browser_press", "browser_get_images",
        "browser_vision", "browser_console",
        "text_to_speech",
        "todo", "memory",
        "session_search",
        "clarify",
        "delegate_task", "delegate_worker",
        "cronjob",
        "send_message",
    ],
    "includes": ["file_readonly", "skills_readonly"]
},
```

**Option B** (no code edit, more atoms): pass a longer list of existing atomic toolsets:
```
-t delegation,todo,clarify,memory,session_search,web,vision,image_gen,browser,tts,cronjob,messaging
```
This is equivalent except it forgoes read_file / search_files entirely (since the atomic `file` toolset bundles writers too). If we want read-only file access, Option A is required.

### CLI invocation (Option A)
```bash
cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q --max-turns 20 --checkpoints \
  -m gemma-4-31b-it-4bit \
  -t hermes-cli-no-offenders \
  --source probe-r7.3-restricted-tier3-run1 \
  -q "<Task 4 text>"
```

### Predicted outcome
Dispatch rate should land between tier 1 and tier 2 — probably ~3/5. Gemma still has the broadest palette (web, browser, memory, etc.) so it can wander, but the four role-collapse attractors are gone. If dispatch rate is similar to tier 1, that tells us read_file/search_files are NOT role-collapse triggers (they stay available in tier 1); the offender removal is what matters. If tier 3 < tier 1, the presence of browser/web/memory itself is attracting the model away from dispatch.

---

## 5. Cost / risk per tier

| Tier | Trials needed (structured+LH tasks 3+4) | ≈ wall-clock (dense, 2 tasks × N trials × ~4min) | Side-effect risk | Reversibility |
|---|---|---|---|---|
| 1 | N=5 per task, 2 tasks = 10 trials | ~40 min | None — read+delegate+todo+clarify; no mutation path exists | `git checkout toolsets.py` to drop `file_readonly`; else just stop passing `-t` |
| 2 | N=5 per task = 10 trials | ~40 min | None — only delegate+clarify; cannot touch filesystem from main session | CLI flag only; drop flag to revert |
| 3 | N=5 per task = 10 trials | ~40 min | Low — read-only file + read-only skills + non-file mutators absent | `git checkout toolsets.py` to drop new toolsets; CLI flag drops to revert |

Wrapper changes: `probe-variantE-wrapper.sh` currently hard-codes the `hermes chat` command with no `-t` flag. To pass toolsets it needs one edit (add `-t $TOOLSETS` to both `ssh_run` invocations) or a cloned variant `probe-variantE-restricted-wrapper.sh` parameterised on a `TOOLSETS` env var. Cloning is preferred — keeps the existing r7 wrapper pristine for comparison runs.

Session-persistence concern: when the retry loop `--resume`s a session with a *different* `-t` flag, Hermes' behaviour is untested. Safest: pass the same `-t` on every attempt within a trial (the retry/correction turns inherit the same restricted toolset). If that proves unstable, skip the retry loop for these experiments and score attempt-0 only — dispatch rate at attempt-0 is the signal we care about.

### Things that do NOT add risk
- No mutation tools in tier 1/2 means `--checkpoints` has nothing to checkpoint — benign.
- `--yolo` is NOT used and MUST NOT be added; there is no need.
- Running dense Gemma only; MoE is already near-ceiling and adds no information at this cost.

### Things to watch
- Gemma hallucinating unavailable tools. Session logs will show `tool_not_found` errors. Treat those as dispatch-non-events, not wrapper errors.
- Judge script (`probe-variantE-check.py`) verdicts: NO_DISPATCH should still fire for structured tasks that didn't dispatch; ROLE_COLLAPSE should be mechanically impossible in tiers 1 and 2 (no mutation tool to call) and rare-to-impossible in tier 3 (only memory/cronjob/send_message mutators remain, none of which the judge currently counts as role collapse).

---

## 6. Recommended first experiment — Tier 1

Tier 1 is the best info-per-trial ratio.

**Why not tier 2:** too severe — if dispatch rate is 5/5, we have learned only that "model dispatches when given nothing else", which is close to tautological. We would still need tier 1 to learn whether orientation surface matters.

**Why not tier 3:** requires more invasive `toolsets.py` edits (a new compound toolset) and leaves too many distractors to isolate the offender effect. Its unique value appears only after tier 1 has a result.

**Why tier 1:** one minimal `toolsets.py` addition (`file_readonly`), retains plausible "orientation" path, still forces the dispatch-or-nothing choice for any action beyond looking. Dispatch delta from 1/5 → tier-1 directly tests the tool-surface hypothesis.

Suggested sequence:
1. Clone `probe-variantE-wrapper.sh` → `probe-r7.3-restricted-wrapper.sh`, parameterise `-t`.
2. Add `file_readonly` toolset to `toolsets.py` (single dict entry).
3. Run N=5 on Task 3 (structured) + N=5 on Task 4 (long-horizon) under tier 1.
4. If tier-1 dispatch jumps (>= 3/5), proceed to tier 3 to find the minimum-impact configuration for a production remediation. If tier-1 doesn't move, run tier 2 next as a disposition-confirmation probe — if tier 2 also doesn't dispatch, the issue is not tool competition.

Approximate cost to decision: 10 trials = ~40 min dense wall-clock + ~5 min wrapper edit + ~2 min toolsets.py edit. Cheapest viable test of the hypothesis.

---

## 7. What this would disambiguate

### Outcome A — tier-1 dispatch rate ≥ 4/5
**Hypothesis confirmed.** Gemma's low dispatch rate is caused by competing "natural" tools (terminal, write_file) that the default CLI surface exposes. Remediation becomes trivial: ship a restricted toolset as the recommended configuration for Gemma-class dense models, or add a prompt-level instruction "the following tools are unavailable in this session" that references the offenders. We did not need to change HERMES.md text, the wrapper, or the model.

### Outcome B — tier-1 dispatch rate ≈ 1-2/5 (unchanged)
**Hypothesis falsified at tier 1.** The disposition runs deeper than tool competition. Candidate explanations to investigate next:
- Gemma-31B-dense has a prior toward immediate procedural action regardless of available tools (would show up as hallucinated tool calls or wordy "I would do X" narration in tier 2).
- HERMES.md text is being processed but not followed — the problem is instruction-following, not tool layout.
- Context-window / position effects: classification marker lands but dispatch requirement is lost mid-prompt.

Next probe in this branch: tier 2. If tier 2 also fails to dispatch (stall or hallucinate), we have isolated the issue to the model's execution disposition and tool-surface restriction is not a viable lever — we'd move to either a different base model for dense, a fine-tune, or a wrapper-level pre-dispatch enforcer that synthesises the `delegate_worker` call on the model's behalf when classification is structured/LH.

### Outcome C — tier-1 dispatch rate 3/5
**Partial confirmation.** The tool surface contributes but is not the whole story. Proceed to tier 3 to disentangle "orientation tools compete" from "specific offenders compete". Compare dispatch rate across tiers 1 and 3:
- Tier 3 ≈ tier 1 → offenders are the issue; keep orientation tools, ship restriction on mutators.
- Tier 3 < tier 1 → even the remaining wide surface (web, browser) distracts; minimal toolset is the right production configuration.

---

## Appendix — files read

- `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (local)
- `~/.hermes/hermes-agent/toolsets.py` (remote, full read)
- `~/.hermes/hermes-agent/hermes_cli/main.py` (remote, targeted grep — args.toolsets plumbing at line 644)
- `~/.hermes/hermes-agent/hermes_cli/tools_config.py` (remote, targeted grep — default_toolset mapping line 123)
- `~/.hermes/hermes-agent/hermes_cli/nous_subscription.py` (remote, targeted grep — resolve_toolset usage)
- `hermes chat --help` output (remote)

No files written, no commands run on the VM beyond `cat`, `ls`, and `grep`. No mutations.
