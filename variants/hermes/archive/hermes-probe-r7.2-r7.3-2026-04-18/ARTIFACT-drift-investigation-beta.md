# ARTIFACT — Drift Investigation (Worker β)

**Scope:** Hermes-on-ubuntu-vm state, read-only SSH probes.
**Timebox:** 15 minutes.
**Date:** 2026-04-18
**Compared against:** r7 baseline (2026-04-17 evening, 3/5 first-attempt dispatch).

---

## 1. Live file md5 integrity check

| File | Expected md5 | Actual md5 | Match |
|------|--------------|------------|-------|
| `~/.hermes/hermes-agent/HERMES.md` | `4477b8ee1d87c3a3afa9e8646168841f` | `4477b8ee1d87c3a3afa9e8646168841f` | YES |
| `~/.hermes/hermes-agent/HERMES-canonical-backup.md` | `0780c232a6cb52e13e432261f0d68ad9` | `0780c232a6cb52e13e432261f0d68ad9` | YES |
| `~/.hermes/hermes-agent/tools/delegate_worker.py` | `031df77464d3a3643be4ac7316307356` | `031df77464d3a3643be4ac7316307356` | YES |

Local reference md5s (`/Users/briantaylor/Projects/AgentFW/variants/hermes/*`) both match (`HERMES-variantD.md` + `delegate_worker.py`). File sizes, line counts, mtimes all consistent (Apr 18 12:12, which is this morning's r7.2 landing — no edits during the eval).

- `HERMES.md`: 12,060 bytes, 210 lines, mtime `2026-04-18 12:12`
- `HERMES-canonical-backup.md`: 8,440 bytes, 130 lines, mtime `2026-04-18 12:12`
- `delegate_worker.py`: 2,672 bytes, mtime `2026-04-18 12:12`

**Verdict: No drift in HERMES.md, canonical backup, or delegate_worker.py. Byte-identical to local canonical sources.**

---

## 2. Source patch verification

Diffs between live Hermes sources and their `.probe-d-orig` backups (the Apr 18 00:06/00:10 pre-patch snapshots):

### `model_tools.py`
```
156a157
>         "tools.delegate_worker",
```
**Exactly +1 line. Matches spec.**

### `toolsets.py`
```
56:  "execute_code", "delegate_task",  →  "execute_code", "delegate_task", "delegate_worker",
193: "tools": ["delegate_task"],       →  "tools": ["delegate_task", "delegate_worker"],
248: "execute_code", "delegate_task",  →  "execute_code", "delegate_task", "delegate_worker",
276: "execute_code", "delegate_task",  →  "execute_code", "delegate_task", "delegate_worker",
```
**Exactly 4 `delegate_worker` insertions. Matches spec.**

### `run_agent.py`
```
6009: elif function_name == "delegate_task":        →  elif function_name in ("delegate_task", "delegate_worker"):
6386: elif function_name == "delegate_task":        →  elif function_name in ("delegate_task", "delegate_worker"):
```
**Exactly 2 sites, `==` → `in (...)`. Matches spec.**

**Verdict: All three patched files carry ONLY the documented delegate_worker changes. No hidden divergence.**

---

## 3. SOUL.md audit

**Path:** `~/.hermes/SOUL.md` (2,423 bytes, mtime **2026-04-10 16:20:42**)

A second file exists at `~/.hermes/hermes-agent/docker/SOUL.md` (536 bytes, mtime Mar 31) — this is the in-repo docker example, not the live one. `prompt_builder.py::load_soul_md` reads only `get_hermes_home() / "SOUL.md"`, i.e. the Apr 10 one.

**Content summary:** kawaii-presetted Hermes persona, skills-first disposition, terminal-first tooling, warns about raw-text tool-call format emitted by the local model, documents MEMORY.md/USER.md cap handling, instructs to use `mempalace-search.sh`. Nothing r7.2/delegate_worker-specific.

**Mtime = Apr 10 16:20** is the key fact: **SOUL.md has not been touched since r7 (or r6, or r5) — it is identical to the r7 run.** SOUL.md is NOT a drift source.

---

## 4. Hermes git + version state

```
HEAD detached at v2026.4.8
Last commit: 86960cdbb0148145890e2ee90b4e157fa899f6e1
             "chore: release v0.8.0 (2026.4.8) (#6135)"  2026-04-08
Reflog:
  86960cdb HEAD@{2026-04-10 17:21:17}: checkout: moving from main to v2026.4.8
  2556cfda HEAD@{2026-04-04 16:50:56}: reset / pull --ff-only origin main: Fast-forward
  c36aa5fe HEAD@{2026-03-31 19:34:55}: clone
```

- **No `git pull` since Apr 4. No checkout since Apr 10.** No unexpected upstream delta.
- `git log --since="2026-04-17 18:00"`: empty. No new commits from upstream.
- Tracked files with uncommitted diffs: `cron/scheduler.py` (+12), `environments/tool_call_parsers/__init__.py` (+1), `model_tools.py` (our patch), `run_agent.py` (our patch), `tools/todo_tool.py` (+5/-2), `toolsets.py` (our patch).
- The three extra-tracked diffs (`cron/scheduler.py`, `tool_call_parsers/__init__.py`, `tools/todo_tool.py`) have been there since Apr 10 or earlier — they are **not new today**, and were in place during r7 as well. They're unrelated Hermes-local customizations.
- Untracked files: canonical HERMES variants, probe-d-orig backups, `gemma_parser.py`, `delegate_worker.py`, `dashboard_tasks_tool.py`, `DATABASE_AUDIT.md`.

**Verdict: Zero upstream/git drift since r7. Hermes code tree is frozen at v2026.4.8 + our known delta.**

---

## 5. Skills + prompt_builder audit

### Auto-load behavior (`prompt_builder.py`)

- **Identity slot:** `load_soul_md()` → `~/.hermes/SOUL.md`.
- **Project context slot:** first-match-wins among `.hermes.md/HERMES.md` (walk to git root) → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`. Only ONE project-context type loads.
- **Skills prompt:** built from all `~/.hermes/skills/**/{SKILL.md,DESCRIPTION.md}`. Two-layer cache (in-process LRU + disk snapshot at `.skills_prompt_snapshot.json`). Snapshot invalidated by mtime/size manifest mismatch.
- **Memory injection:** `MEMORY.md`/`USER.md` are uploaded to Honcho (if the Honcho memory provider is active), surfaced via memory tool, not directly injected into the system prompt here.
- `prompt_builder.py` itself: **mtime 2026-04-10 17:21** (from v2026.4.8 checkout). `git diff --stat`: **no changes**. Behaviorally unchanged since r7.

### Skills snapshot state

- `~/.hermes/.skills_prompt_snapshot.json`: 56,750 bytes, **regenerated at 2026-04-18 15:07** — meaning some skill's mtime changed, invalidating the snapshot, and it was rebuilt. 102 skill entries, 27 category descriptions.
- Skills directory mtime top-10 (most recent first):
  - **`productivity/atlassian/jira-daily-briefing/SKILL.md` — 2026-04-18 15:25** *(touched AFTER snapshot rebuild; next agent start will re-invalidate)*
  - `productivity/atlassian/jira-briefing-benchmark/SKILL.md` — 2026-04-10 16:37
  - `research/*`, `red-teaming/godmode`, `productivity/google-workspace`, `mlops/training`, `dogfood`, `creative/*`, `autonomous-ai-agents/claude-code` — all 2026-04-10 16:26 (from v2026.4.8 checkout)
  - Older skills 2026-04-02 through 2026-03-31

### Noteworthy skills present that MATCH r7.2 pattern

- `~/.hermes/skills/gstack-harness-planner/SKILL.md` — "**Planner role wrapper for agentic harness**"
- `~/.hermes/skills/gstack-harness-worker/SKILL.md` — "**Worker role wrapper**"
- `~/.hermes/skills/gstack-harness-judge/SKILL.md` — "**Judge role wrapper**"
- `~/.hermes/skills/gstack-harness-templates/PROGRESS.md` — **a PROGRESS.md template that is itself instructions**

These are skills that talk explicitly about delegate_task, planner-worker-judge architecture, verification tiers, and role separation — i.e. **exactly the AgentFW vocabulary.** They were present during r7 as well (mtimes Mar 31 / Apr 1).

### Memory content

`~/.hermes/memories/MEMORY.md` (Apr 7 19:18, 2,243 bytes) and `USER.md` (Apr 2 20:57, 3,903 bytes) — both untouched since r7. Content is ABC Supply work context, personal profile, MemPalace mining notes — nothing r7.2-relevant.

### Unexpected `~/.hermes/agent/` directory

**NEW FILES since r7 era:**
- `~/.hermes/agent/PROGRESS.md` — mtime **2026-04-18 00:38:10** (DB migration phase tracker, clearly not-ours)
- `~/.hermes/agent/DB_TOPOLOGY.md` — mtime **2026-04-18 00:38:10** (PostgreSQL 12→16 migration topology)

These look like scratch artifacts from a session last night (Apr 18 00:38) — NOT loaded by prompt_builder (`~/.hermes/agent/` is not a path it reads; it reads `~/.hermes/SOUL.md`, `~/.hermes/skills/`, `~/.hermes/memories/` via honcho). **Likely harmless to r7.2 behavior, but documents that Hermes ran a planning session ~00:38 Apr 18 and the PROGRESS.md convention from the gstack-harness skill was instantiated.**

---

## 6. Gateway + process state

```
parallels  2509972  0.0  2.2  867740  181360 ?  Sl  Apr10  3:55
           python -m hermes_cli.main gateway run --replace
```

- **PID 2509972 — still alive. Same PID as r7 baseline.** Uptime 8 days.
- `gateway.pid` / `gateway_state.json` both mtime **2026-04-10 17:22**. `start_time: 84277476` (monotonic), `updated_at: 2026-04-10T22:22:26`.
- **The gateway has NOT been reloaded since before r7.** It's been running the same process for the entire r6→r7→r7.2 window.
- `processes.json` is 2 bytes (empty `{}`), updated Apr 10 17:22.

**Verdict: Gateway process-identity is stable. No reload could have changed loaded SOUL.md/HERMES.md/skill content.**

---

## 7. New files since r7 (filtered)

Excluding sessions/logs/state.db/cache/checkpoints/git, files with mtime > SOUL.md (2026-04-10):

- **`~/.hermes/agent/PROGRESS.md`** (Apr 18 00:38) — NEW (see §5)
- **`~/.hermes/agent/DB_TOPOLOGY.md`** (Apr 18 00:38) — NEW (see §5)
- `~/.hermes/.skills_prompt_snapshot.json` (Apr 18 15:07) — regenerated today
- `~/.hermes/gateway_state.json` (Apr 10 17:22) — pre-r7
- `~/.hermes/cron/.tick.lock`, `~/.hermes/cron/output/**` (Apr 10–17) — cron briefings, unrelated
- `~/.hermes/cron/jobs.json`, `~/.hermes/config.yaml` (Apr 10) — pre-r7
- **`~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md`** (Apr 18 15:25) — modified TODAY, after 1447 run
- All `~/.hermes/hermes-agent/**/*.py` files listed are Apr 10 17:21 — from the v2026.4.8 checkout, NOT new edits.

No `memory/`, `context/`, or `cache/` subdir additions in hermes-agent.

---

## 8. Ranked hypotheses — Hermes-layer cause of dispatch drift

### H1 — Snapshot regeneration between r7 and r7.2 pulled in a different cached skills prompt (LOW-MEDIUM)
**Evidence:**
- `.skills_prompt_snapshot.json` mtime is **2026-04-18 15:07** (during/just before today's r7.2 sweep).
- Manifest-hash invalidation happens on any skill file mtime/size change; a skill file got touched ≤15:07 which invalidated the r7 snapshot.
- The skills prompt is ~20-80KB of prefix — any change shifts the prefix cache boundary, which can perturb a loose-tail model like Hermes's local Qwen.
**Counter-evidence:**
- `_load_skills_snapshot` only returns content if the manifest still matches; if it was stale it was simply rebuilt with current state. Regeneration alone doesn't change *content*, only rebuilds the file. Need to check whether ANY skill content actually changed vs. only mtime.
- No skill was created/deleted between r7 and r7.2-dense (15:07). `jira-daily-briefing` was re-edited at **15:25 — AFTER 15:07** — so the 15:07 rebuild was triggered by something else (possibly the Apr 18 12:12 HERMES.md/delegate_worker.py file writes, or prior sessions today).

### H2 — Hermes-side prefix cache warming differs r7 vs. r7.2 (MEDIUM)
**Evidence:**
- Same gateway PID 2509972 with 8-day uptime. Internal `_SKILLS_PROMPT_CACHE` LRU has 8-slot capacity.
- Between r7 evening and r7.2 sweep, the agent/ PROGRESS.md session at Apr 18 00:38 and any other intervening sessions would have rotated LRU entries.
- Platform-keyed cache (`os.environ.get("HERMES_PLATFORM")` / `HERMES_SESSION_PLATFORM`) means a CLI run produces a different cache key than a Discord gateway invocation.
- Net: internal cache state is different today vs. last night, without any file visibly changing.
**Counter-evidence:**
- The cache only controls *construction speed* of the skills prompt; the final prompt text is deterministic given the same inputs. Cache state shouldn't alter content unless a race or snapshot corruption happened.

### H3 — The `agent/PROGRESS.md`+`DB_TOPOLOGY.md` instantiated in a prior Apr 18 00:38 session changed Hermes's self-model via session history or memory (LOW)
**Evidence:**
- The planner-worker-judge gstack skills install Brian as a Planner-role user; if a session at 00:38 invoked them and produced a PROGRESS.md in `~/.hermes/agent/`, Hermes "saw itself planning" last night.
- `state.db` wal is 4MB with recent mtime — session state is active.
- Memory Honcho provider might have absorbed "I've been doing planner-worker-judge work lately" as a fact.
**Counter-evidence:**
- `MEMORY.md` mtime is **Apr 7 19:18** — not updated since r7. So no persisted memory shift.
- Session-local state shouldn't leak across `hermes chat -q` invocations unless --continue/-c is used.

### H4 — prompt_builder.py loaded DIFFERENT project context on r7 vs. r7.2 due to cwd (MEDIUM-HIGH)
**Evidence:**
- `_load_hermes_md(cwd_path)` walks from cwd to git root looking for `.hermes.md`/`HERMES.md`. If the r7 probe was launched from a cwd whose git root contains an `HERMES.md`, but r7.2 probe was launched from a different cwd, the loaded **project context** differs.
- `HERMES.md`/`HERMES-variantD.md`/`HERMES-canonical-backup.md`/`HERMES-variantB.md` are all **inside `~/.hermes/hermes-agent/`**, which IS a git repo. If launched with cwd inside `hermes-agent/`, prompt_builder will walk up and load `~/.hermes/hermes-agent/HERMES.md` (variant D — the one we want). If launched from a cwd not inside any git repo with an HERMES.md, it loads NOTHING for project context.
- Additionally, `load_soul_md` always loads `~/.hermes/SOUL.md`, but `build_context_files_prompt` is called with `skip_soul=True` when soul was already in the identity slot. If the caller forgot `skip_soul=True`, SOUL.md is duplicated. Conversely, if the identity slot went missing today, SOUL.md might be absent entirely.
**This is the most investigable hypothesis** — Worker α's Mac-side probe setup determines the cwd.

### H5 — Hermes gateway serving stale cached system prompt because process has been up 8 days (LOW)
**Evidence:**
- Uptime 8 days, PID 2509972 unchanged.
- In-process `_SKILLS_PROMPT_CACHE` is LRU(8); if HERMES.md itself was updated at 12:12 today but the gateway never re-read it (because cache didn't see the mtime change? because cwd-dependent caching retained an old entry?), we'd be running yesterday's HERMES.md in gateway sessions.
**Counter-evidence:**
- The skills snapshot on disk DID refresh at 15:07, suggesting the manifest check fired. HERMES.md is not part of the skills manifest though — it's loaded fresh each build by `_load_hermes_md` with no file-level cache shown. Re-read every invocation. So the gateway can't be serving stale HERMES.md.
- BUT: if we're running via `hermes chat -q` from a cwd that doesn't contain HERMES.md, the file is simply not loaded. Gateway-served sessions (Discord) use cwd of the gateway process (Apr 10 startup cwd).

### H6 — The `jira-daily-briefing` skill edit at 15:25 contaminated today's runs (VERY LOW)
**Evidence:** The edit landed at 15:25. If the r7.2-dense probes ran after 15:25, the skills prompt includes different jira-briefing text.
**Counter-evidence:** The 15:07 snapshot was already generated before 15:25, and subsequent calls would either (a) rebuild snapshot on mtime mismatch or (b) use in-process cache until restart. Even if rebuilt, the jira-briefing skill is unrelated to dispatch routing — no reason it would affect delegate_worker calls.

---

## 9. Proposed remediation experiments (do NOT run)

Ordered cheap → expensive:

1. **Confirm cwd used by r7 and r7.2 probe wrappers (α's job).** If the probe launches Hermes from a cwd that is NOT inside a git repo with `HERMES.md` at the root, variant D is never loaded. Expected to be the most likely explanation.

2. **Force-refresh snapshot + clear in-process cache:**
   `rm ~/.hermes/.skills_prompt_snapshot.json` then re-run one dense probe dispatch. If result matches r7, the stale-cache theory is confirmed.

3. **Run one r7.2-dense probe with explicit cwd:**
   `cd ~/.hermes/hermes-agent && hermes chat -q "<dispatch prompt>"`
   vs. the same invocation from `/tmp`. Compare first-attempt dispatch outcome. Distinguishes H4 cleanly.

4. **Isolate gateway prefix state:** restart gateway (`hermes gateway stop && hermes gateway run`) and re-run r7.2-dense. If dispatch rate recovers to 3/5, H2 (gateway cache accumulation) is confirmed.

5. **Delete `~/.hermes/agent/PROGRESS.md` + `DB_TOPOLOGY.md`, clear any active session/continuation references to them, re-run probe.** H3 check. Cheap; mostly for ruling out.

6. **Diff `.skills_prompt_snapshot.json` contents between a known-good r7 backup (if one exists) and current.** If no backup exists, save current and diff against one made after explicit snapshot regen post cache-clear.

7. **Temporarily replace HERMES.md with a sentinel file (e.g. append a unique token) and check whether the dispatch actually reads it** via a probe that asks the agent to echo the sentinel. Confirms variant-D is actually reaching the system prompt.

8. **Rebuild Hermes venv from scratch** (most expensive; only if 1–7 are inconclusive). Rules out any unseen pyc/egg-info drift.

---

## Summary for planner

- **Files are clean.** HERMES.md, canonical backup, delegate_worker.py, and the three source patches are byte-identical to their canonical local counterparts and contain only documented changes.
- **Git tree is frozen** at v2026.4.8 since Apr 10. No upstream activity since r7.
- **SOUL.md, MEMORY.md, USER.md untouched** since r7. Gateway is the same process (PID 2509972, 8-day uptime).
- **Two mild anomalies:**
  1. `~/.hermes/agent/PROGRESS.md` + `DB_TOPOLOGY.md` created at 2026-04-18 00:38 (a planner-session artifact from earlier today) — probably inert but documents that Hermes was doing planner-worker-judge work at that time.
  2. `jira-daily-briefing/SKILL.md` was modified today at 15:25, and `.skills_prompt_snapshot.json` rebuilt at 15:07. The skills prefix almost certainly shifted between r7 and r7.2.
- **Top suspect (H4):** cwd-dependent `HERMES.md` loading. `prompt_builder._load_hermes_md` walks cwd to git root; r7 and r7.2 probes may have been launched from different cwds, loading different (or no) project context. Worker α needs to report the Mac-side wrapper's `cd` behavior.
- **Second suspect (H2):** in-process `_SKILLS_PROMPT_CACHE` on the long-running gateway has rotated state since r7. If the probes go through the Hermes gateway, prefix-cache state is not r7-identical even though files are.
