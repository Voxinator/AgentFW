# ARTIFACT — Worker δ: r7.2 Drift Root-Cause Investigation (Sampling Axis)

**Worker:** δ (delta)
**Scope:** Verify whether sampling parameters for `gemma-4-31b-it-4bit` at runtime
match `model_settings.json`. Rule sampling drift in or out.
**Time boxed:** 15 min. **Mutations:** one controlled chat completion request (harmless).

---

## 1. Model settings snapshot

**`~/.omlx/model_settings.json` → `gemma-4-31b-it-4bit` block (verbatim):**

```json
"gemma-4-31b-it-4bit": {
  "max_context_window": 131072,
  "max_tokens": 16384,
  "temperature": 0.8,
  "top_p": 0.95,
  "top_k": 64,
  "force_sampling": false,
  "ttl_seconds": 300,
  "thinking_budget_enabled": false,
  "turboquant_kv_enabled": false,
  "turboquant_kv_bits": 4.0,
  "turboquant_skip_last": true,
  "specprefill_enabled": false,
  "dflash_enabled": false,
  "is_pinned": false,
  "is_default": true
}
```

**`~/.omlx/settings.json` → server-wide `sampling` fallback block (verbatim):**

```json
"sampling": {
  "max_context_window": 32768,
  "max_tokens": 32768,
  "temperature": 1.0,
  "top_p": 0.95,
  "top_k": 0,
  "repetition_penalty": 1.0
}
```

Note: model-level block overrides server fallback when a request targets
`gemma-4-31b-it-4bit`. Server-level has `top_k=0, temp=1.0` — only relevant
for models lacking a dedicated block.

---

## 2. Step 2 — clean completion sampling (no tools, no system prompt)

Request: `haiku about debugging`, `max_tokens=200`, no overrides.

Observed at `2026-04-18 15:49:10,032`:

```
Sampling params: temperature=0.8, top_p=0.95, top_k=64,
repetition_penalty=1.0, min_p=0.0, presence_penalty=0.0,
frequency_penalty=0.0, max_tokens=200,
xtc_probability=0.0, xtc_threshold=0.1 (model: gemma-4-31b-it-4bit)
```

| Field | model_settings.json | Observed | Match |
| --- | --- | --- | --- |
| temperature | 0.8 | 0.8 | yes |
| top_p | 0.95 | 0.95 | yes |
| top_k | 64 | 64 | yes |
| repetition_penalty | (not set → default 1.0) | 1.0 | yes |
| max_tokens | 16384 (default) | 200 (request override) | yes |
| min_p | n/a | 0.0 | default |
| xtc_probability | n/a | 0.0 | default |

**Clean completion sampling is exact per model_settings.json. No drift at this layer.**

---

## 3. Step 5 — Hermes-like completion sampling (production-shaped)

Request: system = `HERMES.md` + `SOUL.md` (8935 chars, ~2109 prompt tokens),
user = Task-4 style auth-refactor prompt, `tools=[delegate_worker]`,
`max_tokens=300`. No sampling overrides in payload.

Server-side sampling log at `2026-04-18 15:49:57,200`:

```
Sampling params: temperature=0.8, top_p=0.95, top_k=64,
repetition_penalty=1.0, min_p=0.0, presence_penalty=0.0,
frequency_penalty=0.0, max_tokens=300,
xtc_probability=0.0, xtc_threshold=0.1 (model: gemma-4-31b-it-4bit)
```

**Identical to clean completion.** Tool-schema presence does NOT alter sampling.
System-prompt length does NOT alter sampling. `finish_reason=tool_calls` emitted
cleanly, response well-formed. Only difference from step 2: `max_tokens=300`
vs `200` (per request).

---

## 4. Step 6 — r7.2 probe invocation audit

Captured probe request `68f151ac-25b4-4610-8b71-1bfcbe77e16f` at
`2026-04-18 15:08:20`:

```
Sampling params: temperature=0.8, top_p=0.95, top_k=64, repetition_penalty=1.0,
min_p=0.0, presence_penalty=0.0, frequency_penalty=0.0, max_tokens=16384,
xtc_probability=0.0, xtc_threshold=0.1 (model: gemma-4-31b-it-4bit)
```

Request metadata:
- prompt_tokens: **18,214**
- cached hit: 17,408 (17 blocks from tiered SSD cache) — `paged cache hit`
- **WARNING emitted by scheduler:**
  `Cache base_size mismatch: computed 36864, expected 17408 (cached_tokens). Using cached_tokens for boundary alignment.`
- finished: `stop`, 24 tokens generated
- **Generated text (malformed):**
  ```
  <|tool_call>call:terminal{command:<|"|>netstat -tulpn | grep 5432<|"|>}<tool_call|>
  ```
  (broken special-token boundaries; `<|"|>` appearing inline; wrapper `<tool_call|>` instead of `</tool_call>`.)

Sampling params: **identical** to steps 2 & 3.

---

## 5. r7 vs r7.2 sampling delta

Cross-checked against r7 era (`server.log.2026-04-17`) and older logs back to
Apr 14. Every single `Sampling params` line for `gemma-4-31b-it-4bit` is
character-for-character identical on the sampling fields (temp, top_p, top_k,
rep_penalty, min_p, xtc). The only field that varies is `max_tokens`, which is
per-request.

**No sampling delta between r7 and r7.2.** The probe sampling note in
`probe-reproducibility.md` (T=0.8, top_p=0.95, top_k=64, rep_penalty=1.0) holds.

However, two NEW scheduler-level behaviors ARE present in r7.2 that were ABSENT
in r7:

| Signal | Apr 15 | Apr 16 | Apr 17 (r7) | Apr 18 (r7.2) |
| --- | --- | --- | --- | --- |
| `Cache base_size mismatch` WARN count | 0 | 0 | **0** | **263** |
| `Normalized RotatingKVCache snapshot` DEBUG count | 850 | 850 | 54,300 | 86,650 |
| `Walk-back truncation: ... non-sliceable` | 1 | 1 | 47 | 48 |

Gemma-4-31b is loaded today as `engine: vlm, type: vlm` (VLMBatchedEngine,
`VLM tool calling enabled: parser=gemma4`). r7 era ALSO used the VLM engine
(confirmed in `server.log.2026-04-17`). Engine identity unchanged.

**Model settings for Gemma were edited today at 11:35:21, 11:37:38, 11:43:37
local time** (3 sequential `Updated settings for model 'gemma-4-31b-it-4bit'`).
The FIRST `Cache base_size mismatch` WARN appeared at **12:40:30** — roughly
57 min after the settings edits, coinciding with a server/engine reload
(`Engine started`, `VLMBatchedEngine loaded`).

---

## 6. Verdict

**Sampling is NOT the drift cause.** Rule it out.

Evidence:
- All runtime sampling lines equal `model_settings.json` exactly (temp=0.8,
  top_p=0.95, top_k=64, rep_penalty=1.0, min_p=0.0, xtc_*=default).
- Sampling identical between r7 3/5-passing runs and r7.2 1-2/5 failing runs.
- System prompt length, tool-schema presence, max_tokens differences do not
  perturb sampling.

**Actual drift driver (strong hypothesis based on collateral evidence):**
Tiered-cache / KV-cache alignment corruption on long-prompt probe requests.

Specifically:
- r7.2 probes send ~18K-token prompts. These exceed the 2048-slot rotating
  sliding-window KV cache `max_size=1024`, forcing thousands of
  `Normalized RotatingKVCache` operations per request (2,050 in a 10s window
  for one probe).
- The SSD prefix cache returns blocks that the current (reloaded) engine
  treats as `placeholder non-sliceable state` — Walk-back truncation drops
  all but the last block, and the scheduler emits
  `Cache base_size mismatch: computed 36864, expected 17408`.
- The scheduler "aligns to cached_tokens" anyway and proceeds — so the model
  consumes a KV-cache prefix whose logical-vs-physical boundary is off by a
  factor of ~2. This is indistinguishable from poisoned KV for the attention
  module.
- The output shows up as malformed special tokens (`<|tool_call>call:...<|"|>...<tool_call|>`)
  — exactly the signature of a model whose attention alignment is wrong,
  not a model whose sampler is misconfigured.
- Zero `Cache base_size mismatch` warnings on r7 or earlier. Zero today for
  the two short-prompt sanity requests I fired (haiku + 2109-token Hermes
  request — both fit inside one block and used fresh paged cache).

The critical delta is: **r7.2 probes rely on large cached prefixes from the
SSD tiered cache, and today's engine cannot slice those cached blocks
correctly.** This is almost certainly a regression in the oMLX tiered-cache
block format or the `BlockAwarePrefixCache` reconstruction path introduced
sometime between the r7 run (Apr 17 ~23:31) and today's first probe
(Apr 18 ~12:40), across a server restart that happened at 12:40:30.

---

## 7. Remediation

**Short-term (to validate the hypothesis — no scope change):**
1. Flush the SSD prefix cache on the Mac:
   `mv ~/.omlx/cache ~/.omlx/cache.r7-2-bad && mkdir ~/.omlx/cache`
   (Or ask the human to do it — this is an `ask-first` mutation.)
2. Restart oMLX to reinitialize an empty tiered cache.
3. Re-run the r7.2 dense probe. Expected outcome if hypothesis is correct:
   - Zero `Cache base_size mismatch` warnings in the log.
   - Probe pass-rate returns toward 3/5.
4. If pass-rate recovers: the regression is confined to stale SSD cache
   blocks being loaded by the post-update engine. File against oMLX as
   "tiered cache block format incompatibility after VLM engine restart".

**Medium-term (if flush fixes it):**
- Add a cache-version tag in the SSD cache. On engine init, invalidate blocks
  whose tag does not match. This is the correct fix and belongs in oMLX.
- Until oMLX ships that fix, add a Hermes-side pre-probe step that asserts
  zero `Cache base_size mismatch` warnings in the last N log lines before
  starting a scoring run. Abort if any are present.

**If flush does NOT fix it:**
- The drift is deeper than cache. Next investigation axis: the tokenizer /
  chat template. Worker δ's haiku completion used no template; Hermes-like
  used `HERMES.md` (8935 chars). Neither produced malformed tokens. The
  r7.2 probe (18K tokens from cache) did. That isolates the failure to
  either (a) the cached-block layout issue above, or (b) a tokenizer path
  that only activates for very long prompts / structured templates.
- Worker ε should take that branch: capture full template rendering for a
  probe request vs a fresh request and diff.

**Do NOT recommend changing sampling params.** Sampling is clean. Any
temperature tweak would mask the real bug.

---

## Appendix — artefact paths

- `/Users/briantaylor/.omlx/model_settings.json`
- `/Users/briantaylor/.omlx/settings.json`
- `/Users/briantaylor/.omlx/logs/server.log` (r7.2 — 62MB, 129K lines)
- `/Users/briantaylor/.omlx/logs/server.log.2026-04-17` (r7 era — 34MB)
- `/Users/briantaylor/Projects/Hermes/HERMES.md`, `/Users/briantaylor/Projects/Hermes/SOUL.md`
  (used to construct step 5 production-shaped request)

Request IDs captured for reference:
- `ec63132f` — step 2 clean completion
- `157242cc-8f0c-4ce8-aa6a-b8027c6b42d4` — step 5 Hermes-shaped completion
- `68f151ac-25b4-4610-8b71-1bfcbe77e16f` — step 6 audited r7.2 probe
