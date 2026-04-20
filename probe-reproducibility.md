# probe-reproducibility.md — Hermes Harness Probe: environment snapshot

**Last updated 2026-04-19 (r7.3 finished)**
**Originally captured:** 2026-04-17
**Purpose:** Record the exact runtime state when the probe is run, so results can be reproduced or invalidated if the environment drifts.

---

## Mac host (oMLX server)

- **App:** oMLX 0.3.6 installed at `/Applications/oMLX.app` (CFBundleShortVersionString 0.3.6, CFBundleVersion 0.3.6, app bundle mtime 2026-04-16)
- **Server process:** `python3 -m omlx.cli serve --base-path /Users/briantaylor/.omlx --port 8000` — **PID 23190, restarted 2026-04-18 10:45:49** (was PID 87119 from 2026-04-10 startup; the old process was shut down at 10:39:58 and a new one started at 10:45:49 same day)
- **Config dirs:** `~/.omlx/` (settings, model_settings, cache, logs, stats); `~/Library/Application Support/oMLX/` (app-level config)
- **Listen:** `0.0.0.0:8000`, CORS `*`, log level `trace`
- **Auth:** API key required for `/v1/*` endpoints (key in `~/.omlx/settings.json`)
- **Settings rewrites today:** `settings.json` (mtime 2026-04-18 10:45:52) and `model_settings.json` (mtime 2026-04-18 11:43:42) were both rewritten today during the rep_penalty=1.05 toggle-and-revert experiment. End-state field values match the original snapshot exactly — no operative drift, just timestamp churn.
- **Weights:** unchanged from r7 baseline.

## Reachable from

- Local: `http://localhost:8000`
- Parallels ubuntu-vm guest: `http://10.211.55.2:8000`

## Active models (at probe time)

From `~/.omlx/model_settings.json`:

| Model | is_default | temp | top_p | top_k | max_tokens | max_ctx | rep_penalty | ttl_s | Notes |
|-------|------------|------|-------|-------|------------|---------|-------------|-------|-------|
| gemma-4-31b-it-4bit | **true** | 0.8 | 0.95 | 64 | 16384 | 131072 | (default 1.0) | 300 | Hermes primary |
| gemma-4-26B-A4B-it-MLX-8bit | false | 0.8 | 0.95 | 64 | — | 131072 | (default 1.0) | — | A/B parity sibling — identical sampling profile to dense |
| Qwen3-VL-8B-Instruct-MLX-4bit | false | 0.1 | — | — | 4096 | 131072 | — | — | Hermes auxiliary (vision, compression) |
| Qwen3.5-35B-A3B-4bit | false | 0.5 | — | — | 8192 | 131072 | 1.05 | — | Prior primary; historical |
| Qwen3.5-35B-A3B-8bit | false | 0.8 | — | — | — | 131072 | 1.1 | — | Prior primary; historical residue in stats |
| Qwen3.5-122B-A10B-4bit | false | — | — | — | — | 131072 | — | — | Rarely used |

**Operative sampling for the probe (Gemma-4-31B):** T=0.8, top_p=0.95, top_k=64, max_tokens=16384, ttl_seconds=300, repetition_penalty=Default(1.0). **Wire-confirmed identical** across r7 (219/219 events) and r7.2 (479/479 events) sampling traces.

## Server-wide sampling fallback (not applied to Gemma)

`~/.omlx/settings.json`: T=1.0, top_p=0.95, top_k=0, max_tokens=32768, repetition_penalty=1.0. Only used when a model has no per-model override. Gemma has explicit overrides, so server fallback is not operative for the probe.

## Usage stats baseline

From `~/.omlx/stats.json` (most recent observation 2026-04-18 mid-probe: 1093 Gemma-31B requests lifetime). Probe runs typically add 200–600 Gemma requests per session depending on retry overhead and child workers. Daily jira-briefing cron adds ~15 Gemma requests at ~08:00 local.

## Ubuntu VM (Hermes orchestrator)

- Install: `~/.hermes/hermes-agent/`
- Gateway: `python -m hermes_cli.main gateway run --replace`, PID 2509972, up since 2026-04-10
- Session logs: `/home/parallels/.hermes/sessions/`, jsonl naming `YYYYMMDD_HHMMSS_<hex>.jsonl`
- Sampling control: **none** sent from Hermes; per-request API calls omit temperature/top_p/top_k. Gemma's per-model oMLX defaults win.

---

## Hermes-side modifications staged from r7 + r7.3

Currently on the VM under `~/.hermes/hermes-agent/`:

### Code patches (delegate_worker scaffolding, r7 + r7.3)

| File | Status | Backup(s) | Notes |
|------|--------|-----------|-------|
| `delegate_worker.py` | **NEW** (added during r7) | n/a (didn't exist pre-r7) | md5 `031df77464d3a3643be4ac7316307356` |
| `toolsets.py` | MODIFIED | `.probe-d-orig` (pre-r7) and `.probe-r7.3-orig` (pre-r7.3) — both pre-r7.3-baseline | r7.3 added `file_readonly` toolset (`read_file` + `search_files` only) |
| `model_tools.py` | MODIFIED | `.probe-d-orig` | imports delegate_worker |
| `run_agent.py` | MODIFIED | `.probe-d-orig` | routes delegate_worker through delegate_task's special-case dispatch |

### HERMES.md variants on VM

| File | md5 | Status |
|------|-----|--------|
| `HERMES.md` | `0780c232a6cb52e13e432261f0d68ad9` | **CANONICAL** — post safety-revert (live) |
| `HERMES-canonical-backup.md` | `0780c232a6cb52e13e432261f0d68ad9` | reference for restore |
| `HERMES-variantD.md` | `4477b8ee1d87c3a3afa9e8646168841f` | r7 ship-candidate — hard contract + delegate_worker scaffolding |
| `HERMES-variantE.md` | `42b8ed602c1cc601bbc5f3189c915355` | r7.3 escape-hatch-stripped variant of D |
| `HERMES-variantD-backup.md` | `4477b8ee1d87c3a3afa9e8646168841f` | variantD safety backup from r7.3 |

### SKILL.md mutated-state backups (Trial 9 reverts, today)

- `SKILL.md.pre-revert-20260418_1340` — Trial 9 v1 mutated state backup
- `SKILL.md.pre-revert-20260418_dense-v2` — Trial 9 dense-v2 mutated state backup

---

## Mac-side wrapper modifications (r7.2 + r7.3)

Under `/Users/briantaylor/Projects/AgentFW/`:

| File | md5 | Status |
|------|-----|--------|
| `probe-variantE-wrapper.sh` | `b652038b1b255de912cab765266da7c2` (re-verify before each session) | LIVE — supports MODEL env var (required), SOURCE_PREFIX env var, TOOLSETS env var (optional, passes `-t` flag), TIMEOUT_PER_TURN=900, session-ID fallback recovery, session-JSON model check |
| `probe-variantE-wrapper.sh.pre-r7.3-orig` | `9fd987c5e18e6aa70a05426c473fc0a3` | pre-r7.3 backup (still includes the wrapper-bug fixes from r7.2) |
| `probe-variantE-wrapper.sh.pre-r7.3-l2-orig` | `9fd987c5e18e6aa70a05426c473fc0a3` | also pre-r7.3 baseline (IMPL-2 created this BEFORE applying L2; surgical L2-only rollback documented in IMPL-2 artifact) |
| `probe-variantE-check.py` | `725d8e6b0cbb2e772fa1cb23aa1c7919` | unchanged from r7 |

---

## Tripwire baselines (current known-good)

| File | md5 |
|------|-----|
| `useDashboard.ts` | `5503ee1c2ef7d635a020eea275e41239` |
| `jira-briefing.sh` | `a1dce6e989527686124d0860830627c9` |
| `SKILL.md` | `fb1a5a5208a6cf2fcb8252aac10397eb` (post 2 reverts today) |

---

## How to fully unstage everything (back to pure-canonical state)

1. `cp ~/.hermes/hermes-agent/HERMES-canonical-backup.md ~/.hermes/hermes-agent/HERMES.md`
   (already done as of 2026-04-19 — live HERMES.md is canonical)
2. `./probe-variantD-stage.sh unstage` — restores `model_tools.py`, `toolsets.py`, `run_agent.py` from `.probe-d-orig`; moves `delegate_worker.py` to `/tmp`
3. **Optional verification:** if the `.probe-d-orig` restore left the `file_readonly` toolset in `toolsets.py`, also restore from `.probe-r7.3-orig`. Confirm `file_readonly` is absent in `toolsets.py` post-unstage.
4. **Optional cleanup:** delete `HERMES-variantE.md` and `HERMES-variantD.md` from VM if not needed for resume.

---

## How to re-stage for next-session continuation (resume r7.3)

1. `./probe-variantD-stage.sh stage` (idempotent — re-applies r7 + r7.3 patches)
2. `scp variants/hermes/HERMES-variantE.md ubuntu-vm:~/.hermes/hermes-agent/` (skip if already there — verify by md5 `42b8ed602c1cc601bbc5f3189c915355`)
3. To make Variant E live:
   ```bash
   ssh ubuntu-vm 'cd ~/.hermes/hermes-agent && cp HERMES.md HERMES-canonical-backup.md && cp HERMES-variantE.md HERMES.md'
   ```
4. Verify md5 of live `HERMES.md` matches expected (`42b8ed602c1cc601bbc5f3189c915355` for variantE, or `0780c232a6cb52e13e432261f0d68ad9` for canonical).

---

## Probe wrapper invocation pattern (canonical r7.3 form)

Includes all r7.3 features (TOOLSETS gating, restricted tool surface, session-JSON model check):

```bash
MODEL=gemma-4-31b-it-4bit \
  SOURCE_PREFIX=probe-r7.X-tag \
  TOOLSETS=delegation,todo,clarify,file_readonly \
  /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh <run_num> <<<"<task text>"
```

`TOOLSETS` is optional. When set, the wrapper appends `-t "$TOOLSETS"` to both initial and `--resume` retry calls; when unset, the wrapper passes no `-t` flag (full default 29-tool surface).

The recommended r7.3 toolset list above resolves to 6 tools: `delegate_task`, `delegate_worker`, `todo`, `clarify`, `read_file`, `search_files`. Mutator tools (`patch`, `write_file`, `terminal`, `execute_code`, `skill_manage`) are physically absent — role-collapse is mechanically impossible at the tool-registry level.

---

## Claude Code routing

`~/.omlx/settings.json` → `claude_code.mode: "cloud"`. This Claude Code session runs on Anthropic cloud inference, NOT on the local oMLX server. No self-reference confound.

---

## How fresh sessions are issued (low-level, without wrapper)

```bash
cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q -q "<PROMPT>" --source probe-r7-run<N>
```

Each invocation generates a new `session_id`. No gateway restart needed. 30 sequential calls are independent.

## Daily cron touching Gemma

- `jira-daily-briefing` job fires ~08:00 local; ~14-15 tool calls per run. Real traffic, not probe-related. If the probe runs across 08:00, the stats-delta comparison will include those extra calls — note the run window.

---

## Invalidation triggers

If any of these change between now and probe execution, re-snapshot this file:

- `~/.omlx/model_settings.json` (sampling overrides, default model)
- `~/.omlx/settings.json` (server config)
- `~/.hermes/hermes-agent/HERMES.md` md5 on the ubuntu-vm
- `~/.hermes/hermes-agent/toolsets.py` (could affect TOOLSETS gate behavior — particularly any change to the `file_readonly` entry)
- `~/.hermes/hermes-agent/delegate_worker.py` md5 (could affect dispatch reliability)
- `~/.hermes/hermes-agent/model_tools.py` or `run_agent.py` (could affect dispatch routing)
- oMLX app version (check `~/Downloads/oMLX-*.dmg` mtimes; if a newer version is installed, some fields above may have moved)
- oMLX server process restart (PID change from 23190; check `ps -o lstart -p $(pgrep -f omlx.cli)`)
- Hermes gateway restart (clears in-memory state; check `ps -o lstart -p 2509972`)
- `probe-variantE-wrapper.sh` md5 drift from `b652038b1b255de912cab765266da7c2`
- `probe-variantE-check.py` md5 drift from `725d8e6b0cbb2e772fa1cb23aa1c7919`
