---
type: r7.8 P1c — sampler + generation param research
date: 2026-04-21
scope: Gemma-4 MoE (gemma-4-26B-A4B-it-MLX-8bit) served by oMLX, consumed by Hermes on ubuntu-vm
---
# r7.8 P1c — sampler research

## TL;DR

1. **Hermes sends ZERO explicit sampler params** (no `temperature`, `top_p`, `top_k`, `repetition_penalty`, `frequency_penalty`, `stop`) to oMLX for chat-completions. Only `max_tokens` is conditionally set. All sampler tuning happens server-side via `/Users/briantaylor/.omlx/model_settings.json` per-model entries. This is the single biggest leverage point for r7.8: **one file edit affects every parent + child generation, regardless of task, toolset, or variant.**
2. oMLX accepts the full OpenAI sampler surface per-request (`temperature, top_p, top_k, repetition_penalty, min_p, presence_penalty, frequency_penalty, max_tokens, stop, seed, xtc_probability, xtc_threshold`) with confirmed behavior on the applied log line `"Sampling params: ..."`. `stop` works (finish_reason transitions to `"stop"` on match).
3. oMLX's server-side `ModelSettings` dataclass does NOT include `stop` or `frequency_penalty` — those are per-request-only. **S3 (stop-token hardening) is the one intervention that requires a Hermes code edit.** S1, S2, S4 (without stop-token addition) are server-side-only.
4. Current Gemma-4 MoE defaults: `temperature=0.8, top_p=0.95, top_k=64, repetition_penalty=1.0 (disabled), max_tokens=16384`. `repetition_penalty=1.0` means **no repetition control is active** — consistent with the 45-identical-`search_files` loop in Arm F T6-run5.
5. oMLX supports hot-reload via `PUT /admin/api/models/{model_id}/settings` — no server restart needed to apply changes. Direct `model_settings.json` edits require `POST /admin/api/reload-models`.

## Current state

### oMLX exposed / accepted sampler params (per-request, probed live)

Probed via `POST /v1/chat/completions` on `gemma-4-26B-A4B-it-MLX-8bit`; oMLX log echoes the applied values on the `"Sampling params: ..."` DEBUG line.

| Param | Accepted? | Evidence | Notes |
|-------|-----------|----------|-------|
| `temperature` | Yes | `/Users/briantaylor/.omlx/logs/server.log` line `temp=None` when omitted; applied line reports `temperature=0.8` from model_settings | Default 0.8 for Gemma-4 MoE |
| `top_p` | Yes | Applied line shows `top_p=0.95` | Default 0.95 |
| `top_k` | Yes | Applied line shows `top_k=64` | Default 64 |
| `repetition_penalty` | Yes | Applied line shows `repetition_penalty=1.0` (no model_settings override) | **Currently disabled** |
| `min_p` | Yes | Probed: `min_p=0.05` shows up in applied line | Default 0.0 |
| `presence_penalty` | Yes | Probed: parameter accepted, applied | Default 0.0 |
| `frequency_penalty` | Yes | Probed: accepted without error | Default 0.0 |
| `stop` | Yes | Probed `stop:["channel"]` → `finish_reason: "stop"` after 5 tokens matching `channel` | Works |
| `seed` | Yes | Accepted | Good for replayable probes |
| `xtc_probability`, `xtc_threshold` | Yes | Visible in log | Excluded values cutoff — advanced sampler |
| `max_tokens` | Yes | Always forwarded when present | Default 16384 for Gemma-4 MoE |

### Hermes-passed params (actually sent)

Traced in `run_agent.py:5229 _build_api_kwargs()`:

- `model`, `messages`, `timeout` — always.
- `tools` — when present.
- `max_tokens` — via `self._max_tokens_param(self.max_tokens)` when `self.max_tokens is not None`. Default is `None` unless set via CLI flag or `config.yaml:model.max_tokens`.
- `extra_body["reasoning"]` — only for providers that support it (OpenRouter, GitHub Copilot, Nous). Not active on oMLX path.
- `extra_body["provider"]` — OpenRouter-only.
- `extra_body["options"]["num_ctx"]` — Ollama-only.

**No temperature, no top_p, no top_k, no repetition_penalty, no frequency_penalty, no presence_penalty, no stop, no min_p.** Confirmed by server log: every Hermes-origin request arrives with `temp=None` (oMLX's annotation for "not in request body").

### Hardcoded / literal defaults

- `run_agent.py:5754` — auxiliary codex-summary call uses `temperature=0.3, max_tokens=5120`. Irrelevant to main agent generation path.
- `run_agent.py:5785` — similar auxiliary path, `temperature=0.3`.
- `trajectory_compressor.py:76` — compression pipeline uses `temperature=0.3`. Only runs when compression triggers.
- No other hardcoded sampler literals on the main generation path.

### Configurable knobs (end-user surface)

Per file `/Users/briantaylor/.omlx/model_settings.json`, for `gemma-4-26B-A4B-it-MLX-8bit`:

```json
{
  "max_context_window": 131072,
  "max_tokens": 16384,
  "temperature": 0.8,
  "top_p": 0.95,
  "top_k": 64,
  "ttl_seconds": 300,
  ...
}
```

These five fields (`max_tokens, temperature, top_p, top_k, repetition_penalty, min_p, presence_penalty`) plus a few reserved slots are first-class per-model server defaults. A `null`/omitted field → falls through to global defaults in `settings.json:sampling.*` (globally `temperature=1.0, top_p=0.95, top_k=0, repetition_penalty=1.0, max_tokens=32768`).

### What the oMLX `ModelSettings` dataclass does NOT have

Confirmed by reading `/Applications/oMLX.app/Contents/Resources/omlx/model_settings.py`:

- No `stop` / `stop_tokens` / `stop_sequences` field.
- No `frequency_penalty` field.
- No `seed`.
- No `xtc_*`.

**Implication:** `stop` and `frequency_penalty` can only be delivered per-request. Since Hermes sends neither today, using them requires Hermes-side code.

### Hermes config path for per-call params

Hermes has a `temperature` attribute on the `HermesAgent` class threaded into auxiliary paths (compressor, codex summary) but **does not plumb it into `_build_api_kwargs()`** for the main chat-completions call. The cleanest extension point for per-request sampler overrides would be inside `_build_api_kwargs` (`run_agent.py:5367`) — adding keys to `api_kwargs` for oMLX base_urls.

### Child worker path

Children spawned via `delegate_worker_v2` → `delegate_task` → new `run_agent` subprocess → same `_build_api_kwargs()` → same (empty) sampler envelope → same oMLX endpoint → same server-side model_settings apply. **Server-side sampler tuning uniformly applies to parent and child.** This is the r7.6 "dispatch vs worker quality decouple" memory — β-fuse solved dispatch, but workers still inherit the sampler defaults that drive thrash/leakage.

---

## Pathology-to-fix mapping

Cross-referencing r7.7 FAIL patterns against sampler-level knobs known to address each class of failure in the literature:

| Pathology | Evidence in r7.7 | Sampler lever(s) |
|-----------|-----------------|------------------|
| **Degenerate loops** (identical repeated tool calls) | Arm F T6-run5: 48 turns, 45 `search_files` with identical or near-identical queries | `repetition_penalty` (1.05–1.15 typical); `frequency_penalty` (0.05–0.3); `presence_penalty` (mild, 0.05–0.15). Lower `temperature` helps indirectly by reducing drift into rut states, but is weaker. |
| **Channel leakage** (`<channel\|>`, `thought\n<channel`, Harmony/OAI-style control markers bleeding into `content`) | Arm F T6-run1, T6-run5 | Primary: **stop-token hardening** via `stop=[...]`. Secondary: `reasoning_parser` in model_settings (Gemma-4 has no mapped parser right now → raw tokens can surface). Tertiary: lower `temperature` to reduce prob of low-probability control-token sampling. |
| **Truncation mid-sentence** (implied `finish_reason=length`) | Multiple FAILs across r7.7 | `max_tokens` uplift (current per-model default is 16384 — generous for a single turn, so truncation is likely a Hermes-passed cap or context-window issue, NOT a sampler issue per se). Verify by checking actual `finish_reason` in failed traces. |
| **Thrash without progress** (high-diversity exploration that never converges) | Pattern across several T5/T6 runs | Lower `temperature` (0.8 → 0.5–0.6) to bias toward higher-probability, more committed completions. Tradeoff: reduces diversity in ambiguous planning moments. |
| **Run-on / filler** (low information density) | Occasional in Arm F, C | `frequency_penalty` mild (0.05–0.1) penalizes token reuse. |

---

## Candidate intervention sets

All candidates below are **read-only to the codebase unless marked CODE**. Server-side changes take effect via admin API (hot-reload, no restart). Each candidate is independently pin-and-rollback safe via `/Users/briantaylor/.omlx/model_settings.json` file md5 capture.

### S1: Conservative tune (server-side only)

**Changes** to `model_settings.json :: gemma-4-26B-A4B-it-MLX-8bit`:

| Field | Current | S1 |
|-------|---------|----|
| `temperature` | 0.8 | **0.6** |
| `top_p` | 0.95 | 0.9 |
| `top_k` | 64 | 40 |
| `repetition_penalty` | (absent → 1.0) | **1.08** |
| `min_p` | (absent → 0.0) | 0.03 |
| `max_tokens` | 16384 | 16384 (unchanged) |

**Rationale.** Moderately lower temperature reduces drift; `top_p=0.9` + `top_k=40` tightens the sampling pool without over-constraining; `repetition_penalty=1.08` is in the "gentle" band that most tuning guides (mlx-lm, vllm, llama.cpp) cite as safe for coherence; `min_p=0.03` drops long-tail noise. All values land in widely-used ranges for Gemma-3/4-class instruction models.

**Generalization argument.** Pure sampler tune. Affects every generation — parent, child, auxiliary codex summary path (if it uses server defaults, though the hardcoded `temperature=0.3` there overrides). Any worker, any toolset, any variant sees the same sampler.

**Rollback.** `md5 /Users/briantaylor/.omlx/model_settings.json` before; if verdict is worse, `PUT /admin/api/models/gemma-4-26B-A4B-it-MLX-8bit/settings` with the original values, then `POST /admin/api/reload-models`. File-diff trivial.

**Vet plan.** 3 trials on Arm F suite, focused on high-failure tasks T5, T6, T8. Measure: (a) degenerate-loop rate (>10 identical tool calls in window), (b) channel-leak rate, (c) verdict (PASS/PARTIAL/FAIL), (d) wallclock and turn count. Compare against r7.7 baseline. Success = loop rate drops and verdicts do not regress.

### S2: Strict repetition control (server-side only)

**Changes** to `model_settings.json :: gemma-4-26B-A4B-it-MLX-8bit`:

| Field | Current | S2 |
|-------|---------|----|
| `temperature` | 0.8 | 0.7 |
| `top_p` | 0.95 | 0.9 |
| `top_k` | 64 | 40 |
| `repetition_penalty` | (absent → 1.0) | **1.2** |
| `min_p` | (absent → 0.0) | 0.03 |

**Rationale.** Aggressive `repetition_penalty=1.2` is in the range where loops are reliably broken but where coherent tool-call JSON / code blocks can start to degrade (the penalty applies to ALL tokens including `{`, `"`, function-name tokens that legitimately repeat across calls). Explicitly tests the "does repetition control break tool-call fidelity?" question.

**Generalization argument.** Same as S1 — every generation.

**Rollback.** Same md5 pattern as S1.

**Vet plan.** 3 trials on Arm F, same tasks as S1 — but with extra attention to tool-call JSON validity. Success = loops drop AND tool-call success rate holds (pass rate on PASS-eligible tasks does not drop). Failure mode to watch for: JSON malformation, especially repeated bracket/quote tokens.

**Risk flag.** Literature (mlx-lm issue tracker, llama.cpp community) reports `repetition_penalty > 1.15` frequently hurts structured-output quality. If S1 succeeds, S2 probably overshoots and should be de-prioritized.

### S3: Aggressive stop-tokens (requires Hermes code edit)

**Changes:**

1. **CODE (Hermes, small):** In `run_agent.py :: _build_api_kwargs()` (line ~5367), when `self.base_url` matches an oMLX endpoint (e.g., contains `:8000` or explicit `HERMES_OMLX_STOP_TOKENS=1`), add:
   ```python
   api_kwargs["stop"] = [
       "<channel|>",
       "<|channel|>",
       "thought\n<channel",
       "<end_of_turn>",  # Gemma native EOS; belt-and-suspenders
   ]
   ```
   Gate behind env var `HERMES_OMLX_STOP_TOKENS` so it's opt-in per run.

2. No server-side changes.

**Rationale.** Channel leakage (`<channel|>` in visible content) is the most consistent non-loop failure signature in r7.7 Arm F. The leak occurs because Gemma-4 has no registered `reasoning_parser` in oMLX (`reasoning_parser` field is `None` for both Gemma-4 models in `model_settings.json`), so control tokens intended for a Harmony-style reasoning split are emitted as plain text. Setting `stop` at the request level cuts the stream at first occurrence and the generation ends cleanly (`finish_reason=stop`). The trailing truncated segment never reaches the tool-call parser, so it can't corrupt function extraction.

**Generalization argument.** All oMLX-served generations get the same stop set. Every worker and parent sees it identically. Orthogonal to other sampler knobs — can stack with S1.

**Rollback.** `git checkout -- run_agent.py` on the VM, restart Hermes parent. File-level diff is ~5 lines.

**Vet plan.** 3–5 trials specifically targeting the tasks where r7.7 saw channel leakage (T6, likely T8). Measure: (a) `<channel|>`-in-content rate (target: 0), (b) `finish_reason` distribution shift toward `stop`, (c) verdict quality (did cutting short lose useful content?). Secondary: test one task where channel markers do NOT normally appear to verify no collateral damage.

**Risk flag.** If a legitimate content block ever contains the literal string `<channel|>` (e.g., the agent discusses the leakage bug in reply text), this will falsely truncate. Low practical risk; mitigation is narrower stop strings or regex-exclusion.

### S4: Combined (S1 + S3)

**Changes:** Apply server-side S1 settings AND the Hermes-side stop-token addition from S3. Unchanged from those two deltas individually.

**Rationale.** Addresses both the thrash/loop axis (S1) and the leakage axis (S3) simultaneously. Two near-orthogonal pathologies; stacking expected to be approximately additive.

**Generalization argument.** Everything in S1 and S3 applies.

**Rollback.** Revert `model_settings.json` via admin API AND revert Hermes code change. Both rollbacks are independent and can be done in isolation if one succeeds and one fails.

**Vet plan.** 3 trials on Arm F with full-suite measurement. Pre-stack: run S1 alone (3 trials) and S3 alone (3 trials) to establish per-axis effect before combining; S4 is the confirmation run. This is the experiment that would ship if both axes prove helpful individually.

### (Deferred) S5: Presence + frequency penalty mix

**Changes:** Add `presence_penalty=0.1, frequency_penalty=0.1` to S1 baseline.

**Rationale.** Complementary to `repetition_penalty` — attacks repetition at the token-type level (presence) and frequency-weighted level (frequency), while `repetition_penalty` is a context-window-window-based multiplicative penalty. On small local models these three interact nontrivially.

**Why deferred.** Adds variables to the experiment without clear literature consensus that the stack helps over `repetition_penalty` alone. Revisit only if S1/S2 don't sufficiently solve loops.

---

## Ranking

Scored on `generalization × expected_impact × rollback_safety`, three-way qualitative:

| Rank | Candidate | Gen | Impact | Rollback | Notes |
|------|-----------|-----|--------|----------|-------|
| 1 | **S1** (Conservative) | 10/10 | 7/10 | 10/10 | One JSON edit; affects everything; zero-risk rollback. Fixes the biggest current gap: `repetition_penalty=1.0` is effectively OFF. |
| 2 | **S3** (Stop-tokens) | 9/10 | 8/10 for leakage / 3/10 for loops | 9/10 | Directly attacks channel leakage which is a distinctive, repeatable r7.7 failure. Requires code edit — slightly higher friction, but affects every oMLX generation. |
| 3 | **S4** (S1 + S3) | 10/10 | 9/10 | 9/10 | Only rank it lower than S1 because it bundles two changes — vet each first, then combine. Likely final ship target. |
| 4 | **S2** (Strict repetition) | 10/10 | 6/10 (upside) / 4/10 (downside) | 10/10 | Literature risk of degrading tool-call JSON. Only run if S1 proves insufficient on loop rate. |
| 5 | S5 (Penalty mix) | 10/10 | 5/10 | 10/10 | Deferred unless S1 is clearly inadequate. |

### Recommended execution order for P2

1. **S1 first.** Single JSON edit via admin API, 3-trial Arm F probe. Low effort, broad impact. Establishes whether server-side sampler tuning alone moves the needle.
2. **S3 second, in parallel if possible.** Hermes code edit gated on env var. 3–5 trial probe focused on leakage tasks. Independent of S1 so can be vetted simultaneously.
3. **S4 as confirmation.** Only after S1 and S3 individually prove positive.
4. S2 only as fallback if S1's gentle repetition_penalty under-corrects.

---

## Appendix A: exact change mechanics

### Applying S1/S2 (server-side)

```bash
# Capture current state for rollback
md5 /Users/briantaylor/.omlx/model_settings.json > /tmp/omlx_model_settings.md5.pre

# Edit the file (update gemma-4-26B-A4B-it-MLX-8bit block)
# ... edit ...

# Trigger hot reload without restart
curl -X POST http://localhost:8000/admin/api/reload-models \
  -H "Authorization: Bearer $OMLX_API_KEY"

# Verify a probe request logs the new sampling params
curl -s http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $OMLX_API_KEY" \
  -d '{"model":"gemma-4-26B-A4B-it-MLX-8bit","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'
tail -3 /Users/briantaylor/.omlx/logs/server.log
# Expect: "Sampling params: temperature=0.6, top_p=0.9, top_k=40, repetition_penalty=1.08, ..."
```

**Rollback:**
```bash
# Revert file content, reload
curl -X POST http://localhost:8000/admin/api/reload-models \
  -H "Authorization: Bearer $OMLX_API_KEY"
```

Alternative: use the typed admin API `PUT /admin/api/models/{model_id}/settings` with a JSON body to avoid direct file editing — the endpoint handles atomic write + in-memory update in one call.

### Applying S3 (Hermes code)

1. On VM, edit `/home/parallels/.hermes/hermes-agent/run_agent.py` around line 5367 (in `_build_api_kwargs`, after the `api_kwargs = {...}` initialization for non-codex, non-anthropic path):
    ```python
    # r7.8 S3: stop-token hardening for oMLX/Gemma-4
    if os.getenv("HERMES_OMLX_STOP_TOKENS") and ":8000" in (self.base_url or ""):
        api_kwargs["stop"] = [
            "<channel|>",
            "<|channel|>",
            "thought\n<channel",
            "<end_of_turn>",
        ]
    ```
2. Restart Hermes parent process on VM.
3. Run probe with `HERMES_OMLX_STOP_TOKENS=1` in env.

**Rollback:** `git checkout -- ~/.hermes/hermes-agent/run_agent.py` and restart.

---

## Appendix B: parameter-precedence contract (oMLX)

Confirmed by reading `/Applications/oMLX.app/Contents/Resources/omlx/server.py:1938-1951`:

1. **Per-request param** > model_settings.json > global settings.json — for sampler params.
2. EXCEPT: keys in `model_settings.forced_ct_kwargs` (chat_template kwargs only) are locked server-side. Not relevant to sampler params.
3. When a request omits a sampler param, oMLX falls through to model_settings, then global. When model_settings entry is missing a key, global applies. Global `repetition_penalty=1.0` → effectively disabled unless someone sets it.

So: S1's server-side additions cannot be overridden by any current Hermes request (which sends nothing). Adding `repetition_penalty` to model_settings is a no-contest change. S3's per-request `stop` overrides any server-side behavior on that specific request.

---

## Appendix C: known-unknowns

1. **Gemma-4 MoE's `reasoning_parser` field is `None`.** Gemma-4 uses the Harmony-style `<channel|>`-delimited reasoning format in its chat template. oMLX has builtin parsers for `"qwen", "harmony", "llama"` (per `model_settings.py:59`). Setting `reasoning_parser="harmony"` might be the actual root-cause fix for channel leakage — stripping the markers server-side before they reach Hermes. **This is a candidate for a separate P1c follow-up.** It was out of scope for pure sampler research but is adjacent; flag for the planner. Confirmation: verify Gemma-4's chat template outputs Harmony-format `<channel|>` markers and whether oMLX's harmony parser handles those specific tokens.

2. **`max_tokens` truncation root-cause** is unclear from sampler research alone — need to check a specific r7.7 FAIL trace for `finish_reason` to confirm it's `length` before blaming max_tokens. Current 16384 default seems sufficient for one-turn generation, so truncation might be context-window-side (prompt + reserve exceeding model's 131072 window) rather than output-side.

3. **xtc_probability / xtc_threshold** are exposed but undocumented in oMLX's surface-visible docs. Advanced samplers (exclude top choices) can help with diversity collapse — potentially relevant for thrash. Worth exploring if S1 under-corrects; deferred as the parameter space expands significantly.

---

## Summary for planner

- **One-line lever:** `repetition_penalty` is currently 1.0 (off) for Gemma-4 MoE. Setting it to 1.08–1.10 in `model_settings.json` via hot-reload is a zero-risk, high-generalization fix that attacks degenerate loops directly.
- **Second high-leverage lever:** Hermes-side per-request `stop` parameter for channel markers. Requires ~5 lines of code, env-var-gated, targets a distinct and repeatable pathology.
- **Combined (S4) is the likely ship target** once each axis is individually verified.
- **Non-sampler follow-up worth a separate worker:** set `reasoning_parser="harmony"` on Gemma-4 entries in `model_settings.json` — might be the actual root-cause fix for channel leakage and obsolete the need for S3's stop-tokens.
