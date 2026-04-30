# Hermes Variant — Installation (r7.11 internal RC)

**Status**: internal RC. Tag `hermes-r7.11-rc1` (pre-release on GitHub).

This is the authoritative install procedure for the Hermes variant of AgentFW. It installs the **r7.11** firmware — the verified-state multi-session resumable architecture with execution-tier acceptance verification (tier 3.7) — onto a Hermes Agent installation on a remote VM.

The installer is canonical-preserving: every file it mutates is backed up via the `.probe-r7.11-orig` convention and restored on `--uninstall`. The canonical Hermes install is byte-identical before and after install/uninstall cycles.

For background on what r7.11 is and what it changes, see:
- `r7.9-research/r7.11/README.md` — milestone tree overview
- `r7.9-research/r7.11/HANDOFF-r7.11-current.md` — campaign-close runbook with empirical baseline

For dependency versions tested, see `DEPENDENCIES.md`.

---

## Quick install (recommended)

From the AgentFW repo root:

```bash
bash variants/hermes/install.sh
```

That runs pre-flight checks (Mac + VM), the 227-test local suite, then stages the firmware. ~30 seconds end-to-end. Idempotent (refuses to re-stage over existing staged state).

To verify everything is in place without mutating anything:

```bash
bash variants/hermes/install.sh --check
```

To restore the canonical Hermes install:

```bash
bash variants/hermes/install.sh --uninstall
```

To run a smoke test after install (requires `OMLX_API_KEY`):

```bash
OMLX_API_KEY=... bash variants/hermes/install.sh --smoke
```

To target a non-default ssh alias OR a non-default Hermes path on the VM:

```bash
bash variants/hermes/install.sh --host=my-hermes-vm
bash variants/hermes/install.sh --hermes-path=opt/hermes-agent
# Or via env vars:
HERMES_HOST=my-hermes-vm HERMES_PATH=opt/hermes-agent bash variants/hermes/install.sh
```

`--hermes-path` is interpreted as `$HOME`-relative on the VM. Default is `.hermes/hermes-agent` (the upstream-recommended location).

If your Hermes is a slightly different version than the tested baseline (and the canonical md5s don't match), you can override the drift halt with:

```bash
bash variants/hermes/install.sh --allow-canonical-drift
```

This converts the md5 mismatch from FAIL to WARN. **CAUTION**: staging may fail or produce unexpected results against an untested Hermes version. The baseline md5s in `install.sh` are pinned to Hermes Agent v0.8.0 commit `86960cdb`; any other Hermes version requires either:
- Updating the baseline md5s in `install.sh` (after empirically verifying r7.11 works against your version), OR
- Using `--allow-canonical-drift` (you're on your own for compatibility).

See `bash variants/hermes/install.sh --help` for the full flag list.

---

## What the installer does

### Phase 1 — Mac-side pre-flight

- Checks `ssh` and `python3` on PATH
- Checks the r7.11 milestone tree exists at `variants/hermes/r7.9-research/r7.11/`
- Checks all required source files are present (probe scripts, source modules, r7.10 carry-forward dependency)

### Phase 2 — VM-side pre-flight

- Checks ssh to the VM works (BatchMode; key auth required)
- Checks Hermes installed at `~/.hermes/hermes-agent/`
- Checks canonical baseline md5s match: `HERMES.md`, `run_agent.py`, `toolsets.py`, `model_tools.py` (any drift halts install)
- Checks Hermes' Python is 3.11.x (warns if not — scaffold venvs must match for ABI compatibility, see F-6 in `r7.x-followups.md`)
- Checks no stale `.probe-r7.11-orig` backups (would indicate a prior install that wasn't unstaged cleanly)
- Checks no prior r7.11 staging (idempotency: refuses to re-stage; uninstall first)

### Phase 3 — Local test suite (227 tests)

Runs all 7 r7.11 test files locally on the Mac. Halts before staging if any test fails — won't stage broken firmware. Skip with `--skip-tests` if you've already verified.

### Phase 4 — Stage firmware on VM

Invokes `r7.9-research/r7.11/probe-r7.11-stage.sh stage`, which:

1. Backs up `~/.hermes/hermes-agent/toolsets.py` and `model_tools.py` to `.probe-r7.11-orig`
2. Creates `~/.hermes/hermes-agent/tools/r7_11_lib/`
3. Copies 4 lib modules (`verified_state.py`, `verify_phase.py`, `verify_phase_tool.py`, `handoff_tools.py`) with import-path rewrites
4. Copies the r7.10 carry-forward `write_plan_md.py` to `~/.hermes/hermes-agent/tools/`
5. Writes 3 thin shim files at `tools/r7_11_*.py` for Hermes' tool registration
6. Patches `toolsets.py` (appends 4 names to `_HERMES_CORE_TOOLS`) and `model_tools.py` (appends 4 imports)
7. Runs `python3 -m py_compile` on the patched files for syntax sanity
8. Snapshots the post-stage md5 set to `/tmp/r7.11-stage-md5s.txt`

### Phase 5 — Post-stage verification

Confirms each expected staged file is present on the VM, and that the canonical tripwires (`HERMES.md`, `run_agent.py`) are still byte-identical to the baseline.

### Phase 6 (optional, `--smoke`) — Smoke test

Invokes `r7.9-research/r7.11/smoke-r7.11.sh`, which runs a minimal `hermes chat` invocation against the staged firmware to confirm tool registration is healthy end-to-end. Requires `OMLX_API_KEY` in env (any oMLX-compatible auth token).

---

## Prerequisites

See `DEPENDENCIES.md` for full tested-version detail. Summary:

### Mac side

- Bash, `ssh`, `python3` (3.9+ on the Mac for running tests; the VM needs 3.11)
- This repo cloned
- `~/.ssh/config` alias pointing at the Hermes VM (default `ubuntu-vm`; override via `--host=` or `HERMES_HOST` env var)
- (No assumption about your local repo path; the installer derives paths from its own location)
- A local OpenAI-compatible inference endpoint (oMLX recommended; `gemma-4-26B-A4B-it-MLX-8bit` MoE was the n=5 baseline model)

### VM side

- Linux VM with `ssh` access from Mac
- Hermes Agent installed somewhere on the VM (upstream `github.com/NousResearch/hermes-agent`, tested at `v0.8.0` / commit `86960cdb`). Default install path assumed: `$HOME/.hermes/hermes-agent/`. If you installed it elsewhere, pass `--hermes-path=<path>` (`$HOME`-relative) or set `HERMES_PATH`.
- Hermes' Python venv at `<hermes-path>/venv/` running Python 3.11.x (uv-managed cpython-3.11.15 on the tested rig)
- Canonical Hermes install (no prior modifications to `HERMES.md`, `run_agent.py`, `toolsets.py`, or `model_tools.py`); the installer halts on canonical drift unless `--allow-canonical-drift` is passed

### To run trials post-install

- A scaffold directory on the VM with:
  - `USER-PROMPT.md` — the task description for the parent agent
  - `verify-config.json` — verifier configuration (defaults are fine; see `r7.9-research/r7.11/VERIFY-CONFIG-SCHEMA.md`)
  - `.venv/` — a Python venv built with the **same Python version Hermes uses** (3.11.x), with the project's third-party deps installed (per F-6, mismatched Python versions cause silent ABI failures at acceptance-runner time)
- See `r7.9-research/r7.11/HOWTO-r7.11-multi.md` for scaffold preparation detail

---

## Manual procedure (fallback)

If you'd rather run the steps by hand (or the installer doesn't fit your environment), here's the manual procedure. The automated installer is just a wrapper around this.

```bash
cd variants/hermes/r7.9-research/r7.11

# Run the test suite
for f in test_verified_state test_verify_phase test_verify_phase_tool \
         test_handoff_tools test_hermes_multi test_content_verify test_probe_r7_11; do
  python3 ${f}.py 2>&1 | tail -1
done
# Expect: all "passed" / "OK"

# Verify VM canonical state
ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md \
                       ~/.hermes/hermes-agent/run_agent.py \
                       ~/.hermes/hermes-agent/toolsets.py \
                       ~/.hermes/hermes-agent/model_tools.py'
# Expect:
#   0780c232a6cb52e13e432261f0d68ad9  HERMES.md
#   94ad8712678df5e96b9f407446edf249  run_agent.py
#   5d126e7f1987468c0514cbc474ba12eb  toolsets.py
#   10aaf53294ba39569844ebac7076e9c9  model_tools.py

# Stage
bash probe-r7.11-stage.sh stage

# Verify staged state
ssh ubuntu-vm 'ls ~/.hermes/hermes-agent/tools/r7_11_lib \
                  ~/.hermes/hermes-agent/tools/r7_11_*.py \
                  ~/.hermes/hermes-agent/tools/write_plan_md.py'
```

To uninstall manually:

```bash
bash variants/hermes/r7.9-research/r7.11/probe-r7.11-unstage.sh
```

---

## Running a trial post-install

**See `USAGE.md` for progressive examples** — Level 0 (smoke) through Level 5 (your own task). Levels 0-2 take under 5 minutes and prove the full lifecycle works.

Quick reference for direct invocation:

```bash
ssh ubuntu-vm \
  "cd /path/to/AgentFW/variants/hermes/r7.9-research/r7.11/ && \
   OMLX_API_KEY='...' python3 hermes_multi.py run /path/to/scaffold/ \
     --transport local"
```

`hermes_multi.py run` drives bootstrap → phase loop → completion / escalate. Polls sentinels, archives sessions, routes via `verified-state.json`. See `HOWTO-r7.11-multi.md` for the full subcommand reference (`run`, `resume`, `status`).

The wrapper exits with:
- `0` — all phases verified (success)
- `2` — escalate (parent called `escalate_to_operator` OR max revisions exceeded)
- `3` — wrapper internal error
- `4` — malformed scaffold or config

---

## Troubleshooting

| Problem | Likely cause | Action |
|---|---|---|
| `cannot ssh to ubuntu-vm` | ssh config or key auth | Test `ssh ubuntu-vm true` directly; check `~/.ssh/config` |
| `Hermes not installed at ~/.hermes/hermes-agent` | Hermes Agent isn't installed on the VM | Install Hermes Agent first (see upstream); installer assumes Hermes is already present |
| `md5 mismatch` on canonical files | Different Hermes version than the tested baseline OR prior modifications | Restore canonical Hermes; OR pass `--allow-canonical-drift` (CAUTION: untested); OR update baseline md5s in `install.sh` after empirically verifying compatibility |
| `Hermes not installed at ~/.hermes/hermes-agent` but Hermes IS installed elsewhere | Default path doesn't match your install | Pass `--hermes-path=<path>` (`$HOME`-relative) or set `HERMES_PATH` env var |
| `stale .probe-r7.11-orig backup(s) detected` | Previous install didn't unstage cleanly | Run `bash install.sh --uninstall` to restore canonical |
| `r7.11 firmware appears already staged` | Prior install hasn't been removed | Run `bash install.sh --uninstall` first, then re-install |
| Test suite fails locally | Source-tree integrity issue | Investigate the failing test; do NOT bypass with `--skip-tests` unless you know what you're doing |
| `hermes_multi.py run` escalates on phase 1 with `command-not-found: cd` | F-11 not landed (your r7.11 source is older than 2026-04-30) | Update to current r7.11 |
| Acceptance command runs but tests fail with `ModuleNotFoundError` | Scaffold `.venv/` Python version doesn't match Hermes' Python | Rebuild scaffold venv with Hermes' Python 3.11 (see F-6) |

For deeper troubleshooting see `r7.9-research/r7.11/r7.x-followups.md` (F-1 through F-12 with closure status).

---

## What "internal RC" means

n=5 confirmation on the T6 capability-curve workload landed 3/5 strict completion (cleared the pre-committed RC threshold). 0/5 trials reproduced the trial-3 failure mode (verifier-pass without acceptance-pass). Every load-bearing architectural component held in every trial that exercised it.

The 2 trials that escalated did so on real, operator-actionable issues (parent recovery exhaustion on a tier-3 catch; bootstrap ceremonial-sentinel-firing) — both are deferred to r7.12 reliability tuning.

This is internal-grade infrastructure: shippable for use against T6-class workloads with operator-supervised execution. Not yet vetted for production-autonomous use; r7.12 work addresses the remaining reliability surfaces.

---

## Versioning + provenance

- Tag: `hermes-r7.11-rc1`
- Branch: `hermes-r7.11-internal-rc` (merged to main 2026-04-30)
- Pre-release URL: https://github.com/Voxinator/agentfw/releases/tag/hermes-r7.11-rc1
- This file (`INSTALL.md`) is the authoritative install procedure for the Hermes variant. Older release notes (e.g., `RELEASE-NOTES-r7.5-hermes-prerelease.md`, `IMPLEMENTATION.md`) are historical and do not describe r7.11.
