# Probe Blockers Resolved — Hermes Harness Recon

Read-only recon on `ubuntu-vm` (parallels@10.211.55.3). Sibling to
`ARTIFACT-workerC-hermes-live.md` (loaded first, not re-run).

---

## 0. Summary table

| # | Question | One-line answer |
|---|----------|-----------------|
| Q1 | Where are session jsonl logs? | `~/.hermes/sessions/*.jsonl` — name: `YYYYMMDD_HHMMSS_<8hex>.jsonl` (session_id). 35 current files; also `sessions_backup/` (110 files) and `sessions_archive/pre_v0.8_upgrade/` (55). No auto-retention — `hermes sessions prune --older-than 90` is manual. |
| Q2 | HERMES.md drift vs. canonical? | **IDENTICAL.** md5 `0780c232a6cb52e13e432261f0d68ad9` matches both `~/.hermes/hermes-agent/HERMES.md` and `~/HERMES.md` on the VM against `variants/hermes/HERMES.md` locally. 130 lines, zero drift. |
| Q3 | Gemma sampling / temperature config? | **Uses server defaults.** Hermes does NOT send `temperature`, `top_p`, `top_k`, `max_tokens` on primary turns (`run_agent.py:5367-5451`). No sampling params in `~/.hermes/config.yaml`. Primary-turn MLX call relies entirely on whatever oMLX server at `10.211.55.2:8000` defaults to. Aux client has plumbing for temperature but only fills it when caller supplies it. |
| Q4 | Fresh-session mechanism? | **`hermes chat -q "<prompt>" --source probe-r7`** — every invocation generates a new `session_id` (`cli.py:1523-1529`). No shared state with the running Discord gateway, no lock contention. For Discord specifically: `/new` or `/reset` in the same thread resets the session_key; creating a new Discord thread is also a new session_id. |

---

## Q1 — Session log location

**Directory:** `/home/parallels/.hermes/sessions/` (absolute).

**Evidence — ls:**

```
$ ssh ubuntu-vm 'ls -la ~/.hermes/sessions/ | head -10'
drwx------  2 parallels parallels  12288 Apr 17 17:59 .
drwx------ 25 parallels parallels   4096 Apr 17 18:52 ..
-rw-rw-r--  1 parallels parallels  31775 Apr 10 16:00 20260410_155934_344896f7.jsonl
-rw-rw-r--  1 parallels parallels  32103 Apr 10 18:38 20260410_183722_961c4f9e.jsonl
-rw-rw-r--  1 parallels parallels  36471 Apr 17 17:59 20260417_174835_7b378b58.jsonl
-rw-------  1 parallels parallels  46599 Apr 10 17:24 session_20260403_172901_5a40a295.json
-rw-------  1 parallels parallels  79096 Apr 17 17:59 session_20260417_174835_7b378b58.json
-rw-------  1 parallels parallels 242514 Apr 10 17:39 session_cron_068af7645c26_20260410_173301.json
...
$ ssh ubuntu-vm 'ls ~/.hermes/sessions/ | wc -l'  →  35
```

**Naming conventions observed:**

| Type | Pattern | Who writes |
|------|---------|-----------|
| Event stream | `YYYYMMDD_HHMMSS_<8hex>.jsonl` | primary transcript log (append-only jsonl) |
| Snapshot | `session_YYYYMMDD_HHMMSS_<6-8hex>.json` | full serialized SessionEntry / transcript (pretty JSON) |
| Cron agent | `session_cron_<short-id>_YYYYMMDD_HHMMSS.json` | sessions triggered by `hermes cron` jobs |
| Index | `sessions.json` | the SessionStore's on-disk metadata index |

The hex suffix on `.jsonl` files is the `short_uuid = uuid.uuid4().hex[:8]` assembled at
`cli.py:1527-1529`:

```python
timestamp_str = self.session_start.strftime("%Y%m%d_%H%M%S")
short_uuid = uuid.uuid4().hex[:6]
self.session_id = f"{timestamp_str}_{short_uuid}"
```

Gateway-created sessions follow the same `YYYYMMDD_HHMMSS_<8hex>` scheme (see `gateway/session.py:735`:
`session_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"`), hence 6-hex vs 8-hex
differences — CLI emits 6, gateway emits 8.

**Also:**
- `/home/parallels/.hermes/sessions_backup/` — 110 jsonl files (flat snapshot backup).
- `/home/parallels/.hermes/sessions_archive/pre_v0.8_upgrade/` — 55 jsonl from pre-v0.8 migration.
- `/home/parallels/.hermes/logs/{agent,gateway,errors}.log` + `gateway.out` — stdout/stderr of the daemon.
- `/home/parallels/.hermes/state.db` (SQLite, 8.1 MB) — session metadata & message index.
  The SessionDB is the search/query source of truth; `.jsonl` is the human-readable transcript.

**Retention / rotation:** **None automatic.** `hermes sessions prune --older-than 90 [--source SOURCE]`
is a manual command (default `older-than=90` days). Current oldest file in `sessions/` is from
Apr 9; oldest in `sessions_backup/` is from Mar 31. So nothing has been pruned in the last ~2
weeks. For a probe with 30 runs, disk growth is negligible (~35KB each = ~1MB total).

**Implication for probe:** After each cold `hermes chat -q` call, read its `.jsonl` by session_id.
Session_id is emitted to stdout on `hermes chat` exit (see `--pass-session-id` flag docs).
Alternatively query via `hermes sessions list --source probe-r7`.

---

## Q2 — HERMES.md drift

**Result: ZERO drift.** md5 identical across VM and local canonical.

```
$ md5sum live files on VM
0780c232a6cb52e13e432261f0d68ad9  /home/parallels/.hermes/hermes-agent/HERMES.md
0780c232a6cb52e13e432261f0d68ad9  /home/parallels/HERMES.md

$ md5 /tmp/hermes-live-HERMES.md                                           # cat'd over SSH
MD5 (/tmp/hermes-live-HERMES.md) = 0780c232a6cb52e13e432261f0d68ad9

$ md5 /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES.md        # canonical
MD5 (/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES.md) = 0780c232a6cb52e13e432261f0d68ad9
```

- `wc -l` on live: **130 lines**.
- `wc -l` on canonical: 130 lines (same; not re-checked because md5 match proves byte-identity).
- Diff: empty (skipped because byte-identity is stronger).

Line counts, byte counts, and md5s all agree. There is no drift to report — the live file IS the
canonical variant. Both hits on disk (`~/.hermes/hermes-agent/HERMES.md` and `~/HERMES.md`) are the
same file content (same md5), likely kept in sync manually or by a setup script.

**Implication for probe:** Whatever the r7 hermes variant is set to today is exactly what Gemma is
ingesting on-VM. No per-host divergence to account for.

---

## Q3 — Gemma sampling / temperature config

**Answer: Hermes sends NO sampling params on primary-model turns. Gemma uses oMLX server defaults.**

### 3a. config.yaml has zero sampling params

```
$ ssh ubuntu-vm 'grep -niE "temperature|top_p|top_k|max_tokens|sampling|repeat_penalty" ~/.hermes/config.yaml'
NO_MATCH_IN_CONFIG_YAML
```

Only sampling-adjacent fields in the whole config file are:
```
21:  reasoning_effort: medium
162:  show_reasoning: false
```
`reasoning_effort` only maps to `extra_body.reasoning.effort` for providers that support it
(OpenRouter / GitHub Models / Anthropic). oMLX likely ignores it.

### 3b. Primary api_kwargs omits temperature

`run_agent.py:5367-5385` (the assembly used for every primary-model chat.completions.create):

```python
api_kwargs = {
    "model": self.model,
    "messages": sanitized_messages,
    "timeout": float(os.getenv("HERMES_API_TIMEOUT", 1800.0)),
}
if self.tools:
    api_kwargs["tools"] = self.tools
if self.max_tokens is not None:
    api_kwargs.update(self._max_tokens_param(self.max_tokens))
elif self._is_openrouter_url() and "claude" in (self.model or "").lower():
    ...    # OpenRouter-Anthropic path, sets max_tokens=provider limit
```

No `temperature`, no `top_p`, no `top_k`, no `top_k_logits`, no `repeat_penalty` — ever.
`self.max_tokens` is None for the oMLX/Gemma config (no config.yaml override found).
The only sampling-bearing field that *might* be set is `max_tokens`, and only if the user pointed
at OpenRouter+Claude (not our case — we're at `http://10.211.55.2:8000/v1` with `gemma-4-31b-it-4bit`).

### 3c. Where temperature IS set in the codebase

```
$ ssh ubuntu-vm 'grep -rniE "temperature|sampling_params|top_p|top_k" ~/.hermes/hermes-agent/agent/ ~/.hermes/hermes-agent/hermes_cli/ | head -20'
agent/title_generator.py:42:            temperature=0.3,          # title generation (not main turn)
agent/models_dev.py:61:     temperature: bool = False             # capability flag, not a value
agent/auxiliary_client.py:489,510-511: optional kwarg passthrough
agent/auxiliary_client.py:1893,1907-1908: optional kwarg passthrough
agent/auxiliary_client.py:1943,2043,2075,2146,2214: optional kwarg passthrough
agent/anthropic_adapter.py:1309-1310: "Anthropic requires temperature=1 when thinking is enabled"
run_agent.py:3274-3276: Codex Responses normalizer passthrough
run_agent.py:5754,5766,5785:  temperature=0.3  (some special path — codex kwargs)
```

The only hard-coded `temperature` value that fires on the primary path is `0.3` inside
`title_generator.py:42` — a helper that names sessions. Not a user turn.

`auxiliary_client.py:290` is explicit:
```
# support max_output_tokens or temperature — omit to avoid 400 errors.
```
i.e. aux requests also omit temperature by default. Gemma-4-31B is primary (not aux), but this
confirms the overall posture: omit-and-trust-the-server.

### 3d. MLX server defaults — not probed

Per user rules we do NOT hit `10.211.55.2:8000`. We can't report the server's actual default
temperature. But we can say: whatever oMLX uses (likely ~1.0 or model-specific) is what r7 Gemma
saw. If the probe wants to control for sampling, **wrap the request to inject a temperature**, or
add it via a fork of `run_agent.py:5367` — neither is ideal for the r7 probe, but both are options.

**Summary for Q3:**
- **Value sent:** none (server default).
- **Where it's set:** not set anywhere in the primary path. File:line for the
  primary api_kwargs assembly: `run_agent.py:5367-5451`. File:line for the optional passthrough that
  would honor a user-supplied value: `run_agent.py:3274-3276` (Codex Responses only — inert here).
- **Global vs per-task:** neither, because it's omitted.

---

## Q4 — Fresh-session mechanism

**Recommendation for the 30-probe: use `hermes chat -q "<prompt>" --source probe-r7` from the shell.**
Every invocation generates a fresh `session_id`, bypasses the Discord gateway, and cleanly writes a
`sessions/<id>.jsonl` for post-hoc analysis.

### 4a. CLI — fresh session per invocation (recommended)

`cli.py:1523-1529`:
```python
# Session ID: reuse existing one when resuming, otherwise generate fresh
if resume:
    self.session_id = resume
    self._resumed = True
else:
    timestamp_str = self.session_start.strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    self.session_id = f"{timestamp_str}_{short_uuid}"
```

Every `hermes chat` without `--resume`/`--continue` produces a NEW `session_id`. The session is
recorded to SQLite (`cli.py:3471-3480`) with source tag `HERMES_SESSION_SOURCE` (defaults to
`"cli"`, settable via `--source`). No history is loaded because `self._resumed = False`, so
`_preload_resumed_session()` short-circuits at `cli.py:2593`.

`hermes chat` doesn't touch the running gateway (pid 2509972) — it's an independent Python
process that instantiates its own `AIAgent` and OpenAI client. No lock, no socket handshake. Fully
parallel-safe up to whatever concurrent-request limit oMLX can handle.

`-q/--query` makes it non-interactive (single prompt → single response → exit). `-Q/--quiet`
suppresses banner/spinner — ideal for scripting.

**Probe harness sketch:**
```bash
for i in $(seq 1 30); do
  ssh ubuntu-vm "~/.hermes/hermes-agent/venv/bin/hermes chat -Q -q 'Task: <prompt>' --source probe-r7-run$i"
done
```

Each iteration: fresh session_id, fresh conversation_history, fresh HERMES.md load.
Cold-start guarantee: strong.

### 4b. Discord `/new` and `/reset` — works in-band but heavier

`hermes_cli/commands.py:48-49`:
```python
CommandDef("new", "Start a new session (fresh session ID + history)", "Session",
           aliases=("reset",)),
```

Dispatched in `gateway/run.py:1939-1952` and handled by `_handle_reset_command`
(`gateway/run.py:3245+`), which calls `session_store.reset_session(session_key)` to produce a new
`session_id` for that Discord thread's session_key. The `session_key` itself is unchanged
(still `agent:main:discord:...:<thread_id>[:<user_id>]` per `gateway/session.py:444-502`), but
conversation history is zeroed.

Viable but more friction: requires a Discord-bot-capable probe driver, rate-limits, cached-agent
eviction (`gateway/run.py:6261`), etc. Every `/new` also triggers `session:end` + `session:reset`
plugin hooks and memory flush (`gateway/run.py:3253-3310`), which have side effects.

### 4c. Discord — new thread per run

Creating a new Discord thread makes the session_key different (thread_id is part of the key per
`gateway/session.py:484-499`), so Hermes creates a fresh `SessionEntry` automatically. Works but
requires Discord API calls from the probe driver and leaves thread pollution behind.

### 4d. Gateway restart — DO NOT use

Heavy. Resets everything including `~/.hermes/skills/` caches and plugin state. 30 restarts = 30
risks of leaving the gateway in a bad state. Rejected.

### 4e. Caveats

- `hermes chat` reads cwd for HERMES.md. Running from `/home/parallels/` picks up
  `/home/parallels/HERMES.md` (cwd hit, no git-walk needed since that dir isn't a git repo).
  Running from `~/.hermes/hermes-agent/` picks up the one there (git-root hit). Both files have
  the same md5 (Q2), so either cwd works — but **pin cwd for reproducibility**.
  Suggested: `cd ~/.hermes/hermes-agent && hermes chat -Q -q ...` so the prompt-builder hits the
  known-canonical variant.
- The CLI also reads `SOUL.md` (`~/.hermes/SOUL.md`, 2.4KB identity prompt — not part of AgentFW).
  That will influence outputs. Either strip it for the probe, or acknowledge it as part of the
  baseline.
- A single `hermes chat -q` is one turn. If the probe tasks are multi-turn, either (a) compose the
  whole task into a single prompt, or (b) use interactive mode and drive via expect/stdin.

---

## 5. Unknown unknowns

1. **SOUL.md is loaded separately from HERMES.md.** Not in scope for the probe, but it's 2.4KB of
   identity prompt at `~/.hermes/SOUL.md` that gets injected into every session. If the r7 probe
   wants a "pure AgentFW" measurement, set `HERMES_SKIP_SOUL=1` (if supported — not verified) or
   temporarily rename it. Confirmed loaded in prior recon; not re-checked here.

2. **`max_turns` default is 90 per turn.** `--max-turns N` overrides. This is the cap on tool-call
   iterations within a single user→assistant exchange. If probe tasks are meant to test harness
   discipline (e.g. "did the agent decompose/classify/dispatch?"), 90 is generous but not
   unlimited. Set explicitly in the probe: `--max-turns 50` or whatever r7 calls for.

3. **`HERMES_YOLO_MODE=1` implicit via `--yolo`.** If the probe expects no approval prompts to
   block scripting, either set `--yolo` or ensure the prompt doesn't trigger dangerous-command
   approval gates.

4. **SQLite state.db is 8.1 MB of accumulated session metadata.** The probe's 30 new sessions will
   all go into it. Not a problem, just noting.

5. **Qwen aux model is on the same server as Gemma** — if oMLX at `10.211.55.2:8000` is
   single-threaded or round-robins under load, parallel probe runs could serialize unexpectedly.
   Sequential execution (one `hermes chat` at a time) is safest for r7's timing-sensitive tests.

6. **No per-primary-turn temperature control** means we cannot, on the Hermes side, set
   deterministic seeds or temperature=0 without patching `run_agent.py:5367`. If r7 wants a
   deterministic re-run, this is the load-bearing edit to make. One-line change:
   `api_kwargs["temperature"] = 0.0` before the `return`. Do NOT do this on ubuntu-vm without
   user approval — this is a production host.

7. **Gateway-mode sessions via Discord are auto-reset** by the idle/daily policy
   (`gateway/session.py:626-671`). CLI sessions aren't subject to auto-reset because each CLI
   invocation starts a new session_id anyway. Good; confirms CLI is the cleaner probe surface.

---

## 6. Suggested edits to PLAN-hermes-harness-probe.md

(Inferred from the four blockers — plan file not currently in repo; working from the dispatch
instructions in this task.)

1. **Probe driver: use `hermes chat -Q -q '<prompt>' --source probe-r7-run$i`.**
   Drop any Discord-bot requirement. Run sequentially over SSH. Pin cwd to
   `~/.hermes/hermes-agent/` so HERMES.md discovery is deterministic.

2. **Data collection: read `~/.hermes/sessions/<session_id>.jsonl`** (full turn log, tool calls,
   responses). session_id will be emitted by `hermes chat` on exit. Also grab the corresponding
   `session_<id>.json` snapshot for serialized metadata. Fetch both over SSH; do not modify in
   place on the host.

3. **Sampling: accept server-default temperature (~1.0 for oMLX/Gemma).** Do NOT attempt to
   override in config (not supported) unless the probe explicitly wants a deterministic run — in
   which case a one-line patch to `run_agent.py:5385` is required, and that is an `ask-first`
   mutation on a production host.

4. **HERMES.md variant: no action needed.** md5-identical to canonical. Do NOT overwrite on the
   VM unless upgrading to a new variant for the probe — which is a separate, state-changing task.

5. **Baseline contamination risk: SOUL.md is always injected.** Either strip it (after approval)
   or treat r7 results as "HERMES.md + SOUL.md" baseline rather than pure-AgentFW.

6. **Concurrency: run probes sequentially.** oMLX/Gemma on the Mac is the bottleneck; parallel SSH
   calls will just queue at the server anyway. Sequential is simpler and keeps per-run timing
   comparable.

7. **Retention: no cleanup needed post-probe.** 30 sessions × ~35KB = ~1MB added to
   `~/.hermes/sessions/`. Can clean later with `hermes sessions prune --source probe-r7 --yes`.

8. **Tag clearly: `--source probe-r7` in every run** so post-hoc filtering is trivial via
   `hermes sessions list --source probe-r7` or SQLite queries against
   `~/.hermes/state.db`.

9. **Kill-switch: none needed.** CLI probes are independent of the running gateway (pid 2509972).
   No shared state, no locks. Can abort mid-run without corrupting the Discord side.

10. **HERMES.md discovery: cwd-dependent.** If the probe driver does `ssh ubuntu-vm 'hermes chat
    ...'` without `cd`, the cwd is `~` which contains a copy of HERMES.md — still works, same
    content. But for reproducibility pin: `ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q -q "..." --source probe-r7'`.
