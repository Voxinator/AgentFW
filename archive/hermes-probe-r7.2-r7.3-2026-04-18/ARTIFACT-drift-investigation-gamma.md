# ARTIFACT — Drift Investigation Worker γ (state / cross-session contamination)

Scope: Does a "fresh" `hermes chat` invocation today actually see a clean slate,
or does it carry state from prior probe runs via memory / session search /
auto-resume / skills / Discord threads?

Read-only over ssh ubuntu-vm. Time-boxed 15 min. r7.2 dense probe on 2026-04-18.

---

## 1. Memory system audit

**MEMORY.md:** `/home/parallels/.hermes/memories/MEMORY.md`
- Size: 2243 bytes, mtime **2026-04-07 19:18:19** (11 days old).
- Content (5 entries, `§`-delimited) includes:
  - A directive about error-handling (`CRITICAL ERROR HANDLING DIRECTIVE…`)
  - Config-fix April 2026 note (memory limit 4k chars, aux model swap to Qwen3-VL-8B-MLX-4bit, session_search timeout 60s)
  - Dashboard-moved-to-shared-folder note
  - Chief of Staff Dashboard status (React/Vite, cyan/purple theme)
  - MemPalace install note (557 memories in ChromaDB, `bash ~/.hermes/tools/mempalace-search.sh "…"`)

**USER.md:** 3903 bytes, mtime **2026-04-02 20:57:09** (16 days old).
- Full Brian Taylor profile (ABC Supply PM, income goals, household, tools list).

**MEMORY.md.lock / USER.md.lock:** zero-byte advisory locks, untouched since Apr 2.

**`memory_tool.py` behavior:** "Frozen snapshot" pattern, by design. Comment in
`builtin_memory_provider.py:57`:

> *Uses the frozen snapshot captured at load time. This ensures the system prompt
> stays stable throughout a session (preserving the prompt cache), even though
> the live entries may change via tool calls.*

Writes are durable on disk immediately but do NOT hot-reload into the current
session's system prompt. They ARE visible to the next session.

**Auto-load on new session?** Yes. `run_agent.py` lines ~2660–2680 build the
system prompt; if `self._memory_store` is populated, it appends
`format_for_system_prompt("memory")` and `format_for_system_prompt("user")`.
`BuiltinMemoryProvider.is_available() → True` (always active; cannot be disabled).

**Writes during today's probes?** Zero. Across all 62 `session_20260418_*.json`
files: **0 `memory` tool calls** and **0 `session_search` tool calls**.
`MEMORY.md` mtime confirms no writes since Apr 7.

Conclusion: the memory content is stable across trials today. Every main probe
session at model gemma-4-31b-it-4bit receives an **identical** MEMORY.md /
USER.md block.

---

## 2. Session search audit

**`session_search_tool.py`:** 504 lines. FTS5 search over SQLite `state.db`,
then auxiliary-model (Gemini Flash / Qwen3-VL) summarizes top-3 matching
sessions. **Never auto-invoked.** Only runs when the agent calls
`session_search(query=…)`.

Registration: `run_agent.py:223` lists `"session_search"` as a valid tool name;
dispatch at lines 5968 and 6348. Guidance in the system prompt
(`prompt_builder.py:160`):

> *When the user references something from a past conversation or you suspect
> relevant cross-session context exists, use session_search to recall it before
> asking them to repeat themselves.*

**Usage in today's r7.2 probes:** zero (see §1 count). No probe session pulled
past transcripts into its context via this tool.

The `session_search` tool IS exposed to the agent, but on a one-shot `-Q` probe
it is not triggered by the probe task prompts. Not a contamination vector today.

---

## 3. Continuation / resume audit

**Wrapper invocation** (`/media/psf/Projects/AgentFW/probe-variantE-wrapper.sh:147`):

```
cd ~/.hermes/hermes-agent && timeout 900 ./venv/bin/hermes chat \
  -m $MODEL -Q --max-turns 20 --checkpoints -q "$P" --source $SOURCE_TAG
```

No `--resume`, no `--continue` on the first turn. A new session_id is always
generated in `run_agent.py:906–909`:

```python
timestamp_str = self.session_start.strftime("%Y%m%d_%H%M%S")
short_uuid = uuid.uuid4().hex[:6]
self.session_id = f"{timestamp_str}_{short_uuid}"
```

Correction turns (line 216 of wrapper) DO use `--resume $SESSION_ID` — but that
reuses the SAME trial's session, not a prior trial's. It is intra-trial, not
cross-trial.

**parent_session_id check:** spot-checked 5 of today's probe sessions —
`parent_session_id: None` in every one. Fresh sessions, no auto-continuation.

**Prompt-cache key:** `run_agent.py:5283` sets `prompt_cache_key = self.session_id`.
Each session has a unique cache key; the underlying OMLX server cache is
per-session, not shared across probe trials.

Conclusion: every `hermes chat -Q …` invocation genuinely creates a new session
with a fresh `session_id`. Resume-based contamination is not happening.

---

## 4. prompt_builder content sources

`run_agent.py:_build_system_prompt()` concatenates, in order:

1. SOUL.md (from `~/.hermes/SOUL.md`) — 2411 bytes, mtime Apr 10.
2. Behavioral guidance for whichever tools are loaded (`MEMORY_GUIDANCE`,
   `SESSION_SEARCH_GUIDANCE`, `SKILLS_GUIDANCE`).
3. Nous subscription guidance.
4. Tool-use enforcement guidance (gemma matches `TOOL_USE_ENFORCEMENT_MODELS`
   via the "gemma" substring → injected).
5. Google operational directives (gemma matches "gemma"/"gemini" → injected).
6. Optional `system_message` arg (variant wrappers use this to inject
   HERMES-variantD.md / HERMES-variantB.md content).
7. **MEMORY.md verbatim** (if `_memory_enabled`).
8. **USER.md verbatim** (if `_user_profile_enabled`).
9. External memory-manager system-prompt blocks (none active here).
10. Skills index (`build_skills_system_prompt`) — enumerates all skills from
    `~/.hermes/skills/`.
11. Context files (`build_context_files_prompt`) — HERMES.md, AGENTS.md,
    `.cursorrules` etc. from cwd tree. Wrapper runs in
    `~/.hermes/hermes-agent/`, so HERMES.md / AGENTS.md from THAT repo get
    injected here.
12. Timestamp line, model identity, CLI-mode postscript.

**What DOESN'T get injected:** no "recent activity summary", no
"last_session_summary" file, no cached prior-response text. Session history
lives in SQLite and is surfaced only if `session_search` is explicitly invoked.
No auto-attached prior-session digest.

Verified on a real session:
- Trial-9-v2 session `session_20260418_145925_118829.json` system_prompt length
  36165. Contains SOUL.md verbatim, MEMORY.md verbatim, USER.md verbatim
  (confirmed by substring match of all three files into `system_prompt`).

---

## 5. Session store state

- `/home/parallels/.hermes/sessions/`: **131 files** today (was ~35 a week ago).
- `sessions_backup/`: 110 files (stale backup).
- `sessions_archive/`: 1 file.
- `state.db`: 12.98 MB (FTS5 index + sessions table). mtime 15:11 today.
- No `sessions.db` file; SQLite index is `state.db`.

**Does session count affect startup?** `session_search` queries are ranked by
FTS5; more data = slightly slower search, but session_search isn't being called
on probe trials. No on-startup scan of prior sessions in `run_agent.__init__`
(only `_session_db.create_session()` which is an UPSERT of the new row).

Conclusion: growing session count is not currently impacting probe latency or
content.

---

## 6. Today's probe session analysis — system-prompt fingerprinting

Across all 62 `session_20260418_*.json`, three distinct system-prompt sizes:

| size (bytes) | count | SOUL? | MEMORY/USER? | variant framework? | interpretation |
|---|---|---|---|---|---|
| 14940 | 20 | ❌ | ❌ | ❌ | **delegated sub-agent** (`delegate_task` / `delegate_worker` spawns with `skip_context_files=True`, line 304 of `delegate_tool.py`) |
| 29743 |  2 | ✓ | ❌ | ✓ | **anomaly** — SOUL + variant content but no MEMORY/USER block (see §8 H3) |
| 36165 | 40 | ✓ | ✓ | ✓ | **main probe trial** |

Spot-check diff of two 36165-byte sessions at different times
(`145925_118829` vs `145811_dd6c5a`): **1 character differs**, position 36022,
the `Conversation started: …` timestamp minute. Everything else — SOUL,
MEMORY, USER, skill index, variant scaffolding — is byte-identical.

Contamination signals in today's 36165-byte probes:
- MEMORY.md injection includes: `dex@brianscotttaylor.com`, "Chief of Staff
  Dashboard", "MemPalace long-term memory installed. 557 memories…"
- USER.md injection includes: Brian Taylor's full PM profile, team roster,
  Jira project IDs, priorities — ~3.9 KB of dense personal context.
- Skill index lists 30+ skills including `systematic-debugging`,
  `subagent-driven-development`, `test-driven-development`,
  `vite-shared-folder-migration`, `jira-daily-briefing`, `mempalace-*`, etc.

None of this is *new* contamination from prior probe runs. It's **baseline
persona load** that has been present all along. What matters for drift is:
**has this baseline changed between r7 dense (evening 2026-04-17) and r7.2
dense (afternoon 2026-04-18)?**

Tripwire: MEMORY.md mtime 2026-04-07, USER.md mtime 2026-04-02, SOUL.md mtime
2026-04-10 — all **pre-date r7 dense**. So the memory payload is stable across
both runs; it is not the drift cause via this vector.

Possible second-order contamination: the skill index is generated dynamically
from `~/.hermes/skills/`. If new skills were added after r7, the index grows
and pushes the system prompt larger → different prefix-cache behavior.
Worth a size-diff vs r7 session artifacts.

---

## 7. Skill auto-attachment audit

- `~/.hermes/skills/` — searched for `auto_attach: true`, `always_load`,
  `preload`: **no matches** (only p5.js skill references `preload()` as a p5
  API function). No skill manifest currently opts into automatic loading.
- All SKILL.md files require explicit `skill_view(name)` to surface content.
- The `<available_skills>` section of the system prompt is a short catalog
  (name + one-line description), not full skill bodies. So the *index* is
  always present but *content* is not.

Conclusion: no skill auto-attachment drift vector. The catalog's contents are
derivable from the skills directory; if a skill was added/removed between r7
and r7.2 the catalog would change, but individual skill bodies are not being
auto-loaded.

---

## 8. Ranked hypotheses — cross-session contamination as drift cause

### H1 (most plausible) — **No cross-session contamination; drift is elsewhere**
Every probe trial today loads the *same* SOUL + MEMORY + USER + skill index
as every other trial, and those files haven't moved since before r7 dense.
No `session_search`, no `memory` writes, no resume. Fresh session_id per
invocation. If the same bytes go in and different behavior comes out, the
contamination isn't in the Hermes state layer. Look at: OMLX server warmth /
KV-cache state across rapid back-to-back requests, model weights reload,
temperature/sampling nondeterminism, or a config change to the wrapper itself
between r7 and r7.2.

*Evidence:* identical system-prompt hashes (modulo timestamp) across 40
main-probe sessions; MEMORY/USER/SOUL mtimes all predate r7.

### H2 (moderately plausible) — **Skill catalog drift inflates prompt**
If `~/.hermes/skills/` gained/lost entries between r7 and r7.2, the
`<available_skills>` block in the system prompt changes. At ~36 KB the
prompt sits near common context-window budgeting thresholds; a 500-byte
shift in the skill catalog could reshuffle cache hits or push a later slot
past a boundary. Easy to verify: diff an r7 session system_prompt against
an r7.2 session system_prompt (both 36165 today — but the r7 sessions may
be a different size).

*Experiment:* pull a Trial-N session from r7 dense (2026-04-17 evening),
compare `system_prompt` length and md5 to a Trial-N r7.2 session.

### H3 (anomaly worth investigating) — **Two 29743-byte sessions today with SOUL + variant but NO MEMORY/USER**
Sessions `012003_439ddc` (01:20) and `151145_7fc577` (15:11) are 6422 bytes
shorter than the 36165 baseline and specifically lack the verbatim
Brian-Taylor MEMORY + USER content — while still including SOUL and variant
scaffolding. This means the probe was run with `_memory_enabled=False` and/or
`_user_profile_enabled=False`. The config toggle for this could be an env
var, `config.yaml` flag, or a CLI arg the wrapper is conditionally passing.
If the same flag is getting flipped mid-probe, different trials see
different system prompts.

*Experiment:* identify what code path produces the 29743-byte prompt. Search
for toggles that disable `_memory_enabled` / `_user_profile_enabled`.
Candidates: `--no-memory`, `hermes memory off`, config reload on cron event,
or a race on `memories/*.lock`.

### H4 (low plausibility, discounted) — **session_search backdoor**
Theoretically the agent could `session_search` a prior probe trial, pull
in similar task content, and bias the current response. **Ruled out**: zero
`session_search` calls across all 62 sessions today.

### H5 (low plausibility, discounted) — **Auto-resume / parent_session_id**
All sampled sessions have `parent_session_id=None`. Wrapper never passes
`--resume` or `--continue` on the first turn. Ruled out.

### H6 (speculative) — **Discord thread / gateway state leak**
`~/.hermes/discord_threads.json` mtime 2026-04-17 23:29 — touched recently
but 69 bytes (essentially empty). `gateway_state.json` exists but wrapper
invokes `hermes chat -Q` directly (bypasses gateway). Very unlikely to leak
into -Q probes.

---

## 9. Proposed experiments (for a follow-up worker, not this one)

1. **Identical-fingerprint gate.** Add a step to the wrapper: after each probe
   trial, hash the session's `system_prompt` and compare to the baseline
   recorded at the start of the probe run. If it differs beyond the timestamp
   line, fail the trial with `VIOLATION:PROMPT_DRIFT`. This turns H1/H2/H3
   into a hard gate.

2. **r7-vs-r7.2 prompt diff.** Pull one 36165-byte main-probe session from
   each of: r7 dense (2026-04-17 evening), r7.2 dense-v1, r7.2 dense-v2.
   Diff the three system_prompts. Anything more than timestamp drift is a
   real content change.

3. **Trace the 29743-byte anomaly.** Re-run with `HERMES_DEBUG_PROMPT=1` (or
   equivalent) and dump which code paths set `_memory_enabled=False`. Likely
   suspects: `hermes_cli/memory_setup.py`, `hermes_cli/profiles.py`,
   `config.yaml` reload between trials.

4. **OMLX warm/cold isolation.** If H1 is right, the drift is in the model
   server. Probe with explicit `curl` to the OMLX endpoint using identical
   request bodies across back-to-back calls, hash the responses, measure
   nondeterminism. If responses diverge for identical prompts, the drift is
   sampling-level, not state-level.

5. **state.db FTS5 size effect.** Probe with the sessions directory
   temporarily moved aside (131 → 0 sessions). Does Hermes still behave the
   same? Rules out "bigger index slows startup and changes timing-dependent
   behavior".

---

## Artifacts referenced

- `/home/parallels/.hermes/memories/MEMORY.md` (2243 B, 2026-04-07)
- `/home/parallels/.hermes/memories/USER.md` (3903 B, 2026-04-02)
- `/home/parallels/.hermes/SOUL.md` (2411 B, 2026-04-10)
- `/home/parallels/.hermes/state.db` (12.98 MB)
- `/home/parallels/.hermes/hermes-agent/agent/prompt_builder.py`
- `/home/parallels/.hermes/hermes-agent/agent/builtin_memory_provider.py`
- `/home/parallels/.hermes/hermes-agent/agent/memory_manager.py`
- `/home/parallels/.hermes/hermes-agent/tools/memory_tool.py`
- `/home/parallels/.hermes/hermes-agent/tools/session_search_tool.py`
- `/home/parallels/.hermes/hermes-agent/tools/delegate_tool.py` (line 304:
  `skip_context_files=True` for sub-agents)
- `/home/parallels/.hermes/hermes-agent/run_agent.py` (session_id gen
  line 906, memory injection ~2666, session_search dispatch 5968/6348)
- `/media/psf/Projects/AgentFW/probe-variantE-wrapper.sh` (line 147 =
  first-turn invocation; line 216 = correction-turn resume)
- `/home/parallels/.hermes/sessions/session_20260418_145925_118829.json`
  (Trial-9-v2 reference, 36165-byte system_prompt)
- `/home/parallels/.hermes/sessions/session_20260418_012003_439ddc.json`
  (29743-byte anomaly #1)
- `/home/parallels/.hermes/sessions/session_20260418_151145_7fc577.json`
  (29743-byte anomaly #2)
