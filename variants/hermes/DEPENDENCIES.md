# Hermes Variant — Dependencies and Tested Versions

**Status:** pre-release (r7.5-hermes-prerelease)
**Last tested:** 2026-04-19

This is the empirically-tested configuration. Other combinations may work but have not been probed. Numbers cited here are the ones that produced the probe results in `PROBE-RESULTS-r7.md`, `ARTIFACT-r7.4-ship-judge-verdict-v2.md`, and `ARTIFACT-r7.5-SHIP-judge-verdict.md`.

---

## Host platform

- **Host OS:** macOS 26.3.1 (build 25D771280a)
- **Hardware:** Apple Silicon M5 Max, 18 cores (6 performance + 12 efficiency), 128 GB unified memory
- **Minimum working set observed:** MoE `gemma-4-26B-A4B-it-MLX-8bit` ~6–17 GB loaded; dense `gemma-4-31b-it-4bit` ~18 GB loaded. oMLX reports a 108 GB headroom ceiling on this hardware; sustained long probe runs accumulate session state — restart oMLX between multi-hour campaigns (see `probe-omlx-health-check.sh`).

## VM platform

- **Virtualizer:** Parallels Desktop 26.3.0 (build 57392)
- **Guest OS:** Ubuntu 24.04.4 LTS (`noble`), kernel `6.17.0-19-generic`, `aarch64`
- **SSH alias used by all probe scripts:** `ubuntu-vm` (configure in `~/.ssh/config`)

Any aarch64 Linux VM with SSH access from the Mac host should work; only Parallels + Ubuntu 24.04 has been probed end-to-end.

## Hermes Agent

- **Upstream:** `github.com/NousResearch/hermes-agent`
- **Version tested:** `v0.8.0` (pyproject `name = "hermes-agent"`, `version = "0.8.0"`)
- **Git tag / commit:** `v2026.4.8` / `86960cdb` ("chore: release v0.8.0 (2026.4.8) (#6135)")
- **Install location on VM:** `~/.hermes/hermes-agent/`
- **Python venv:** `~/.hermes/hermes-agent/venv/` (Python 3.11.15)

The Hermes install on VM is a fork with local modifications for this variant; the upstream r7.5 patch footprint is three files (`model_tools.py`, `toolsets.py`, `run_agent.py`) plus two additive tool files (`tools/delegate_worker.py`, `tools/delegate_worker_v2.py`). Patches are idempotent and backup the originals — see `INSTALL.md` and `probe-variantF-stage.sh`, `probe-variantG-stage.sh`.

## Models (served via oMLX)

- **oMLX server:** `0.3.6` (macOS app, `com.omlx.app`, `CFBundleShortVersionString=0.3.6`)
- **Server endpoint:** `localhost:8000` on Mac host
- **VM-to-Mac reachability:** `10.211.55.2:8000` from the Ubuntu guest (Parallels host-only network)
- **Default model reported by `/health`:** `gemma-4-31b-it-4bit`

Two Gemma variants were probed:

| Role | oMLX model name | Use |
|------|-----------------|-----|
| Dense | `gemma-4-31b-it-4bit` | Primary probe subject through r7.2. Still covered in r7.4 dense leg. |
| MoE (4B-active) | `gemma-4-26B-A4B-it-MLX-8bit` (aliased `gemma-4-26b-a4b-it-mlx-8bit`) | Primary probe subject r7.3 onward. MoE cleared r7.4 ship dispatch threshold with >2× margin (17/20). r7.5 worker-quality gate was measured on this model (3/20 PASS). |

Sampling (from `~/.omlx/model_settings.json`, production-realistic, not overridden):
- `temperature = 0.8`
- `top_p = 0.95`
- `top_k = 64`
- `max_context_window = 131072`

No determinism override was applied during probing. Run-to-run variance is meaningful — numbers here are 20-trial aggregates, not single-run reproducibles. See `probe-reproducibility.md`.

## Python / runtime

- **VM Python (Hermes venv):** 3.11.15
- **VM system Python:** 3.12.3
- **Hermes pyproject pin:** `requires-python = ">=3.11"`

Hermes dependency pins relevant to this variant (from `pyproject.toml`):
- `openai>=2.21.0,<3` (oMLX's OpenAI-compatible surface)
- `anthropic>=0.39.0,<1`
- `httpx>=0.28.1,<1`
- `pydantic>=2.12.5,<3`
- `tenacity>=9.1.4,<10`
- `fire>=0.7.1,<1`
- `rich>=14.3.3,<15`

The variant does not add Python dependencies beyond what Hermes already installs.

## What the variant requires from Hermes

These are the load-bearing Hermes behaviors the variant depends on. Breakage in any of these breaks the variant:

- **`hermes chat -t <toolset>` flag.** Runtime-level toolset restriction. Probe passes e.g. `-t delegation,todo,clarify,file_readonly`. Added in r7.3.
- **`file_readonly` toolset bundle** in `toolsets.py` exposing `read_file` + `search_files` only. Added in r7.3 as additive; canonical bundles untouched.
- **`cli.main()` single-query mode** (`hermes chat -Q -q "<prompt>" --max-turns N --checkpoints`). The probe wrapper invokes this specifically.
- **Tool registry that accepts runtime-added tools.** `tools/delegate_worker.py` and `tools/delegate_worker_v2.py` are patched in via `model_tools.py` imports. See `probe-variantF-stage.sh`.
- **`run_conversation` with inline session persistence.** Session JSON is written under `~/.hermes/sessions/session_*.json`. Relevant for SIGTERM behavior (see limitations below).
- **OpenAI-compatible API branch** in `_build_api_kwargs` (patched by the r7.5 turn-0 toolset restriction hook — `probe-variantG-stage.sh`).

## Known limitations caused by Hermes version

- **`_persist_session` is inline in `run_conversation`, not `atexit`.** When the parent session is SIGTERM'd (e.g. by the wrapper's per-trial timeout), the session JSON may truncate mid-turn — parent's `delegate_worker_v2` call is lost from disk even though the child session exists. Fully diagnosed; Tier-1 mitigation (wrapper content-match on fallback recovery) shipped in `probe-variantF-wrapper.sh` / `probe-variantG-wrapper.sh`. Tier-3 (upstream Hermes SIGTERM handler) is designed but not applied. See `ARTIFACT-r7.4-sigterm-research.md`.
- **`cli.main()` single-query mode installs no SIGTERM handler of its own.** The probe wrapper's Tier-1 fix (content-match-based session recovery by prompt-prefix) is the working mitigation.
- **Child sessions inherit the parent's full toolset by default** (no HERMES-WORKER.md equivalent injected at child spawn time). This is load-bearing for the r7.5 worker-quality failure modes (search_files thrash on wrong cwd, fabricated completion claims). Tracked as r7.6 scope.
- **Session loop guards are strict.** Hermes' built-in "run this exact search N times" loop guard fires correctly in the r7.5 probe (e.g. trial 20). The guard works; the worker still emitted a fabricated summary after being refused, which is a separate r7.6 worker-honesty problem.

## Hardware guidance

- **Minimum unified memory for MoE (primary probe target):** the MoE model is ~17 GB resident when loaded; oMLX's engine pool reports a configurable 108 GB headroom on 128 GB hardware. 32 GB or less has not been tested.
- **Dense (`gemma-4-31b-it-4bit`):** ~18 GB resident, similar footprint.
- **Running both concurrently:** oMLX's `/health` endpoint reports `loaded_count` — the engine pool can hold both (`model_count: 12`), but probe campaigns that alternate between dense and MoE in the same hour risk oMLX memory-pressure drift. Restart oMLX between multi-hour campaigns. `probe-omlx-health-check.sh` probes the Mac side from the VM.
- **Swap pressure tripwire:** the operator's rule-of-thumb during r7.5 was "restart oMLX if swap >4 GB or free memory <44 GB." These are empirical; adjust for your hardware.
- **Network:** oMLX must be reachable at `localhost:8000` from the Mac host and at `10.211.55.2:8000` from the VM (the Parallels host-only address). `OMLX_API_KEY` is required for authenticated `/v1/*` queries but not for `/health`.
