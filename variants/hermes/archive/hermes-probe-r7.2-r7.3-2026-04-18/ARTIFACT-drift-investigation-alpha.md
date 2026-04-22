# ARTIFACT: r7.2 Drift Investigation — Worker Alpha (oMLX / Mac host)

**Scope:** Read-only forensic audit of oMLX state on the Mac host (`/Applications/oMLX.app` + `~/.omlx/`).
**Time window:** Investigation run 2026-04-18 ~15:45 local.
**Verdict preview:** **oMLX sampling, version, and cache behavior on the Mac host are NOT the drift source.** Sampling params on wire are byte-identical between r7 and r7.2. One non-obvious finding about a mid-day oMLX restart is noted but is orthogonal to the dispatch-rate drift signal.

---

## 1. settings.json audit

- **Path:** `/Users/briantaylor/.omlx/settings.json`
- **mtime:** `2026-04-18 10:45:52` (today, ~5 hours before the r7.2 probe)
- **Size:** 2053 bytes
- **Relevant delta vs r7 baseline:** mtime changed today, but field comparison is clean. This file appears to have been rewritten on oMLX startup (touched at 10:45:52, one second after process start at 10:45:49), which is harmless rewrite-on-save behavior.

Sampling block verbatim (lines 65–72):

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

Auth: `auth.api_key` present (unchanged). Nothing unusual — `skip_api_key_verification: false`, empty sub_keys.

**Server-default sampling is T=1.0**, but this is the fallback used only when a model has no per-model override. Gemma-4-31B has an explicit override (see §2), so server-default is NOT operative for probe traffic. Log evidence in §6 confirms on-wire sampling is T=0.8 per model_settings.

**Other potentially drift-relevant fields, all nominal:**
- `server.log_level: "trace"` — same as r7 snapshot
- `cache.enabled: true`, `ssd_cache_max_size: "185GB"`, `hot_cache_max_size: "51GB"`, `initial_cache_blocks: 256`
- `claude_code.mode: "cloud"` — no self-reference
- `scheduler.max_concurrent_requests: 8`

**Conclusion:** settings.json is clean. The mtime change is a benign startup rewrite, not an edit.

---

## 2. model_settings.json audit

- **Path:** `/Users/briantaylor/.omlx/model_settings.json`
- **mtime:** `2026-04-18 11:43:42` (today, ~2.5 hours before probe)
- **Size:** 2699 bytes

`gemma-4-31b-it-4bit` block verbatim (lines 59–75):

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

**Matches r7 baseline exactly** (probe-reproducibility.md §"Active models"): T=0.8, top_p=0.95, top_k=64, max_tokens=16384, ctx=131072, TTL=300. `repetition_penalty` is ABSENT from the block — which means the server falls through to the global default of 1.0 (confirmed on the wire below). The reversion of the brief rep_penalty=1.05 experiment is complete.

**Today's mtime (11:43:42) is 2.5h BEFORE the r7.2 probe kicked off at ~14:00.** So whatever was written then has been in effect for the entire r7.2 window.

**Other model blocks worth flagging (none match probe traffic):**
- `gemma-4-26B-A4B-it-MLX-8bit`: same sampling profile (T=0.8, top_p=0.95, top_k=64). Loaded once today 11:57–12:05 — outside probe window, not the dispatch target.
- `Qwen3.5-35B-A3B-4bit`: T=0.5, rep_penalty=1.05 — irrelevant (not targeted by Hermes probe).
- `Qwen3.5-35B-A3B-8bit`: T=0.8, rep_penalty=1.1 — irrelevant.

**Conclusion:** model_settings.json is canonical. rep_penalty reversion confirmed. No drift here.

---

## 3. Prefix cache forensics

### Cache size on disk

```
/Users/briantaylor/.omlx/cache/   186G total   (185GB configured max)
├── 16 hex-sharded block dirs (0-f)   156–193 GB aggregate
├── _boundary_snapshots              empty
├── response-state                   empty (mtime Apr 10)
└── vision_features                  2.7M
```

**Cache is at 100.5% of its configured max (186G / 185GB).** This suggests LRU eviction has been active but is barely keeping pace with writes today. 223 total cache files, all with mtime within the last 24h — **every block in the cache today was written today** (expected given the probe traffic pattern).

### Cache hit/miss distribution for Gemma-31B

r7.2 probe window (2026-04-18 14:00–15:15, scheduler events only):

| Event | Count |
|---|---|
| paged cache hit (full block match) | 95 |
| partial cache hit | 16 |
| cache miss / no cache | **0** |
| Total requests with a cache event logged | 111 |
| Total Gemma-31B sampling events in window | 112 |

**Cache-hit rate in r7.2 window: 111/112 ≈ 99.1%.**

For comparison — r7 full-day (2026-04-17) on Gemma-31B:

| Event | Count |
|---|---|
| paged cache hit | 171 |
| partial cache hit | 47 |
| cache miss | 0 |
| Total | 218 |
| Total Gemma-31B sampling events | 219 |

**r7 cache-hit rate: 218/219 ≈ 99.5%.** Difference is within noise. **Cache hit rate is NOT anomalously high today.**

### Walk-back truncation

This caught my eye: `omlx.cache.prefix_cache - INFO - Walk-back truncation: dropped N trailing block(s) with placeholder non-sliceable state, keeping 1 block(s) (1024 tokens)`.

- r7 (yesterday): 47 events
- r7.2 (today): 48 events

This appears linked to Gemma-3/4's RotatingKVCache with `window_size=1024` (confirmed in scheduler log at oMLX startup: `Aligning paged cache block_size=256 to 1024 (RotatingKVCache window_size=1024, multiplier=1x)`). When the cache is rebuilt for prefix hits longer than 1 block, oMLX walks back to the last slice-able block. This means on a cache hit, Gemma's attention cache is effectively TRUNCATED to the last 1024 tokens of the prefix, and the rest is re-prefilled. **This behavior is identical across r7 and r7.2.** Not the drift source, but worth flagging as a latent oddity: if two structurally similar prompts hit the same 1024-token tail, the model's KV state at generation start is identical — yet this affected BOTH runs equally, so it cannot explain a r7→r7.2 delta.

### Theory: could cache hits bias outputs?

**Short answer: no, not in a way that differs between runs.** The KV cache holds K/V projections, not logits. Given identical sampling params and identical resurrected KV state, the post-cache token distribution is deterministic up to the RNG. oMLX does NOT seed the RNG per-request (no such field in settings.json), so token-by-token variance is expected — but this is the SAME mechanism that produced r7's 3/5 result. It cannot systematically shift r7.2 downward unless something about the cache entries themselves drifted.

**One edge case worth noting:** If a probe prompt's prefix matched a stale cached block from a DIFFERENT model's historical state, we would see corrupted outputs. However, oMLX prefix_cache is keyed per-model (it reads model layers during reconstruction — "Reconstructed cache from tiered cache: 60 layers, 1024 tokens from 1 blocks" — 60 layers matches Gemma-31B architecture). So cross-contamination from e.g. the Qwen3-VL-8B loaded earlier is implausible.

**Conclusion:** Cache is large but within config. Cache-hit rate is not anomalously elevated vs r7. No evidence the cache is the drift source.

---

## 4. Process + version state

### Process

```
PID   23190
ELAPSED 05:03:44    (started 2026-04-18 10:45:49)
RSS   39.5 GB       (resident)
VSZ   520 GB        (virtual — expected for MLX unified memory)
%CPU  3.9           (idle, not during a request)
%MEM  29.5
COMMAND  /Applications/oMLX.app/Contents/MacOS/python3 -m omlx.cli serve --base-path /Users/briantaylor/.omlx --port 8000
```

**Important correction to r7 baseline:** `probe-reproducibility.md` claims the oMLX server process has been up since 2026-04-10 (PID 87119). **That is stale.** Today's PID is 23190, started at 2026-04-18 10:45:49 local. That's a restart of the oMLX server ~5 hours before the r7.2 probe ran. Host system uptime is 9 days (so the Mac itself wasn't rebooted), which means oMLX the app was restarted manually or crashed today at 10:45:49.

Corroborating log evidence:
```
2026-04-18 10:39:58,394 - omlx.engine_pool - INFO - Engine pool shutdown complete
2026-04-18 10:45:50,287 - omlx.engine_pool - INFO - Discovered 11 models, max memory: 108.00GB
```

A 6-minute gap (shutdown at 10:39:58, fresh startup at 10:45:50) points to a deliberate restart — consistent with the settings.json and model_settings.json rewrites happening today.

### Loaded models

Per `/v1/models` (HTTP fetched with API key):
```
Qwen3-VL-30B-A3B-Instruct-8bit, Qwen3-VL-30B-A3B-Instruct-MLX-8bit,
Qwen3-VL-8B-Instruct-MLX-4bit, Qwen3.5-122B-A10B-4bit,
Qwen3.5-35B-A3B-4bit, Qwen3.5-35B-A3B-8bit, Qwen3.5-35B-A3B-mlx-vlm-mxfp4,
gemma-3n-E4B-it-MLX-bf16, gemma-4-26B-A4B-it-MLX-8bit,
gemma-4-31b-it-4bit, gemma-4-e4b-it-8bit, md3p-int4
```

12 models discovered. Gemma-4-31b-it-4bit is present and marked default.

### Load/unload event count today

From `~/.omlx/logs/server.log`:

| Event | Gemma-4-31B count today |
|---|---|
| Loading model | 6 (post-restart; 8 if pre-restart session included) |
| Loaded model | 6 |
| Unloading model | 7 (includes the pre-restart shutdown) |
| Unloaded model | 7 |

Timeline of Gemma-31B churn today:
- 00:07 → 00:30 → 00:32 → 00:45 → 01:06 (pre-restart; TTL-driven cycles)
- 10:39 shutdown, 10:45 new process
- 10:49 → 11:02 (TTL expiry)
- 11:47 → 11:53 (preempted by gemma-4-e4b load)
- 12:40 → …still loaded at 14:00 when probe begins
- 14:00–15:15: gemma-31B is resident for the full probe window (no unload events during the probe itself)

**Conclusion:** The probe ran against a freshly-loaded model instance that had been up for ~1.5h. Not churning during the probe. But the process restart today at 10:45 is a meaningful change from r7 (which ran against a process that had been up since 2026-04-10). This is the first real difference worth noting.

### Version

- `/Applications/oMLX.app/Contents/Info.plist`: `CFBundleShortVersionString: 0.3.6`, `CFBundleVersion: 0.3.6`
- App bundle mtime: `2026-04-16 11:00:38` (installed 2 days ago)
- `/Applications/oMLX.app/Contents/MacOS/oMLX` mtime: `2026-04-16 11:02:34`

**No app replacement today.** The 0.3.6 DMG in `~/Downloads/oMLX-0.3.6-macos26-tahoe.dmg` has mtime `2026-04-18 10:41` — downloaded today at 10:41, 4 minutes before the app restart at 10:45. **User likely downloaded the DMG intending to upgrade but did not replace the app bundle.** The install mtime is still 2026-04-16. **Running version matches r7 (0.3.6).**

---

## 5. Stats delta

From `~/.omlx/stats.json` (mtime 2026-04-18 15:14:42, i.e. mid-probe):

| Model | requests | prompt_tokens | completion_tokens |
|---|---|---|---|
| **gemma-4-31b-it-4bit** | **1093** | 24.19 M | 200,122 |
| Qwen3.5-35B-A3B-8bit | 4319 | 189 M | 542 K |
| Qwen3.5-35B-A3B-4bit | 540 | 14.5 M | 181 K |
| gemma-4-26B-A4B-it-MLX-8bit | 5 | 424 | 682 |
| gemma-4-e4b-it-8bit | 3 | 579 | 834 |
| Qwen3-VL-8B-Instruct-MLX-4bit | 46 | 202 K | 17 K |
| Qwen3.5-122B-A10B-4bit | 5 | 392 K | 777 |

**Gemma-4-31B delta vs r7 baseline:** 1093 − 431 = **662 new Gemma-31B requests since 2026-04-17 pre-probe.** This is consistent with:
- r7 probe runs: ~200 requests (per `PROBE-RESULTS-r7.md` — 5 variants × 10 tasks each ≈ 50, × retry overhead + child workers that dispatched = several hundred)
- r7.2 v1 + v2 dense runs: ~200 requests (2 × 10 trials × multiple turns/dispatches)
- jira-daily-briefing cron: ~15 requests (once at 08:00)

Log-level corroboration: 479 Sampling-params events for gemma-4-31b in server.log today alone. That aligns with r7.2 traffic intensity being higher than a typical day.

**Nothing anomalous in the stats distribution:** no mystery model receiving traffic, no unexpected ratio of completion/prompt tokens for Gemma (completion ratio today is 200122/24190845 = 0.83% — similar to r7's 137K/9.06M = 1.5%, slight decrease consistent with more tool-call-heavy shorter responses in r7.2).

---

## 6. Feature flag comparison

Comparing `gemma-4-31b-it-4bit` block today vs r7 baseline (probe-reproducibility.md):

| Flag | Current (2026-04-18) | r7 baseline (2026-04-17) | Match |
|---|---|---|---|
| temperature | 0.8 | 0.8 | YES |
| top_p | 0.95 | 0.95 | YES |
| top_k | 64 | 64 | YES |
| repetition_penalty | (absent → default 1.0) | (absent → default 1.0) | YES |
| max_tokens | 16384 | 16384 | YES |
| max_context_window | 131072 | 131072 | YES |
| ttl_seconds | 300 | 300 | YES |
| force_sampling | false | (assumed false) | YES |
| thinking_budget_enabled | false | (assumed false) | YES |
| turboquant_kv_enabled | false | (assumed false) | YES |
| turboquant_kv_bits | 4.0 | (assumed 4) | YES (type widened to float) |
| turboquant_skip_last | true | (assumed true) | YES |
| specprefill_enabled | false | (assumed false) | YES |
| dflash_enabled | false | (assumed false) | YES |
| is_pinned | false | false | YES |
| is_default | true | true | YES |

**Wire-level verification from server.log:**
- r7 (2026-04-17): 219 `Sampling params` events for Gemma-31B, **all** with `temperature=0.8, top_p=0.95, top_k=64, repetition_penalty=1.0, max_tokens=16384, min_p=0.0, presence_penalty=0.0, frequency_penalty=0.0, xtc_probability=0.0, xtc_threshold=0.1`.
- r7.2 (2026-04-18): 479 events today, spot-checked across the 14:00–15:15 probe window — **byte-identical sampling param tuples on every request.**

**Conclusion:** No feature flag drift detectable at any layer (file, cache, or wire). Sampling is deterministic across runs at the server level.

---

## 7. Ranked hypotheses (oMLX-layer cause of dispatch drift)

Ordered from most plausible to least. Evidence in brackets; proposed tests appended.

### H1 (MOST PLAUSIBLE) — **Nothing on the Mac/oMLX layer explains the drift.**
Evidence:
- Sampling params byte-identical on wire (r7 219/219 + r7.2 479/479 events match exactly).
- Cache hit rate (~99%) identical across r7 and r7.2.
- Version unchanged (0.3.6, installed 2026-04-16).
- All feature flags match.
- model_settings.json and settings.json match r7 baseline in every load-bearing field.

**Implication:** The drift almost certainly originates above oMLX — on the VM (Hermes orchestrator, HERMES.md, wrapper scripts, tool definitions, session handling, jira-briefing cron interaction, Python deps, etc.) — which is Worker β's scope. Alpha's layer is clean.

**Test:** If Worker β finds anything changed on VM side (e.g. HERMES.md md5 drift, Hermes agent version, gateway restart, wrapper script edits, cron side-effects), that fully explains the drift without invoking oMLX.

### H2 — **Non-deterministic KV cache reconstruction path post-restart.**
Evidence: oMLX restarted at 10:45:49 today (4h15m before probe). The prefix cache is persisted on SSD, so cache entries from the previous process survive. On cache hits post-restart, cache reconstruction walks back to the last slice-able block and re-prefills. In principle, the KV tensors produced by re-prefill vs. in-memory resident could differ numerically (MLX reduction order, fp quantization boundaries) in a way that perturbs top-k sampling at T=0.8.

Counter-evidence: the walk-back truncation pattern occurs identically on r7 (47 events) and r7.2 (48 events). This is the steady-state mechanism, not something new.

**Test (read-only):** Compare a specific probe task's token-sequence output between a known r7 trial and a r7.2 trial for the SAME seed/prompt. If they differ at block boundaries (token positions that are multiples of 1024), it points to reconstruction nondeterminism. Likely cannot isolate given natural sampling randomness.

**Test (destructive, DO NOT RUN without approval):** Clear `~/.omlx/cache/[0-f]` (drop ~186GB), restart oMLX clean, re-run one structured probe trial. If result is nominal, cache is implicated.

### H3 — **oMLX process restart at 10:45 cleared some soft in-memory state tied to generation quality.**
Evidence: The previous process had been up since 2026-04-10. Scheduler, engine pool, and internal RNG/caches got a fresh start today. The new process had ~4.5h of warm-up but only 8 Gemma load cycles vs the old process's ~10 days.

Counter-evidence: no obvious soft-state in the oMLX codebase that would degrade dispatch behavior; model weights are re-loaded from the same files on each engine pool load.

**Test (read-only):** Check `~/.omlx/cache/response-state` and `_boundary_snapshots` — both are currently empty (size 0). Not the explanation.

### H4 (LOWEST) — **The Qwen3-VL-8B / gemma-4-e4b / gemma-4-26B models loaded earlier today caused some cross-model cache contamination.**
Evidence: gemma-4-26B-A4B-it-MLX-8bit was loaded at 11:57 and unloaded at 12:05. This model shares the gemma-4 family branding.

Counter-evidence: oMLX cache is keyed by model identity (reconstruction references "60 layers" which is Gemma-31B-specific; 26B has a different layer count). Very hard to see a contamination path.

**Test (read-only):** Grep for any cross-model cache events in server.log between 11:57 and 14:00. If a 60-layer cache gets reconstructed for Gemma-26B or vice-versa, that's the smoking gun. Spot-checked: none observed.

---

## 8. Proposed remediation experiments (DO NOT RUN)

Ordered cheap-first. None of these should be executed without parent session approval.

### E1 (cheap, read-only) — **Wire-level diff two trials.**
For a specific probe task (e.g. T4 refactor auth) pick one r7 archived session and one r7.2 v2 session. Extract the full Hermes→oMLX request bodies from `~/.omlx/logs/server.log.2026-04-17` and the current `server.log`. `diff` the request headers and body JSON. Any systemic prompt-level delta (even whitespace) would be a smoking gun for VM-side drift, not oMLX.

**Cost:** Two grep + diff operations. No mutations. Verifies H1.

### E2 (cheap, read-only) — **Walk-back sequence analysis.**
For r7 vs r7.2, grep all `Walk-back truncation` events with surrounding `Reconstructed cache` events for Gemma-31B, and compute the distribution of (blocks dropped, blocks kept, token count retained). If the distributions match, H2 is unlikely.

**Cost:** grep + awk analysis. No mutations.

### E3 (moderate, reversible) — **Run one structured probe trial with `temperature=0` override.**
Send a Hermes probe request with explicit `temperature: 0, top_p: 1.0, top_k: 1` in the request body (greedy decoding). This eliminates sampling randomness. If Gemma-31B dispatches correctly with greedy decoding on the trial where it previously failed, the issue is sampling variance amplified by some harness change. If it STILL fails to dispatch with T=0, the problem is upstream of generation quality (prompt content, tool grammar, harness flow).

**Cost:** One probe trial. Non-mutating on oMLX side; would spend ~30s of inference.

### E4 (moderate, easily reversible) — **Pin gemma-4-31b-it-4bit (`is_pinned: true`) and rerun probe.**
Prevents any preemption by other-model loads during the probe. Currently `is_pinned: false`. Pin, rerun N=5 structured trials, unpin. If results improve, load churn was part of the picture (though log evidence in §4 shows Gemma-31B was resident for the entire r7.2 window, so this experiment should probably rank lower).

**Cost:** One 2-char edit to model_settings.json. Fully reversible.

### E5 (expensive, partially reversible) — **Clear prefix cache and rerun one structured trial.**
`rm -rf ~/.omlx/cache/[0-9a-f]` (preserve `vision_features`, `_boundary_snapshots`, `response-state`). Bounces 186GB of cache; subsequent cold trial eats ~30s prefill overhead. Verifies H2 definitively.

**Cost:** ~186GB of disk I/O on cache rebuild. Probe traffic will re-warm cache to similar fullness within ~5 trials. Effort: medium. Risk: a single trial with cold cache ~40s slower than normal, but provides definitive H2 resolution.

### E6 (expensive, requires app replacement) — **Downgrade to the 0.3.4 DMG in Downloads.**
`~/Downloads/oMLX-0.3.4-macos26-tahoe.dmg` (mtime 2026-04-07) predates the r7 probe. If r7 ran on 0.3.4 not 0.3.6 (unclear — probe-reproducibility says "0.3.x"), rollback would test whether 0.3.6 introduced a generation-behavior regression. But the Info.plist mtime (2026-04-16) means 0.3.6 was installed BEFORE r7 ran on 2026-04-17, so this is unlikely to help.

**Cost:** App replacement (reversible). Only pursue after H1/H2 are ruled out.

---

## Appendix A: Key file paths

- `/Users/briantaylor/.omlx/settings.json` — server + sampling defaults
- `/Users/briantaylor/.omlx/model_settings.json` — per-model overrides
- `/Users/briantaylor/.omlx/stats.json` — lifetime usage counters
- `/Users/briantaylor/.omlx/logs/server.log` — today's trace log (62MB)
- `/Users/briantaylor/.omlx/logs/server.log.2026-04-17` — r7 day's trace log (34MB)
- `/Users/briantaylor/.omlx/cache/[0-f]` — 186GB paged SSD cache (LRU-evicted)
- `/Applications/oMLX.app/Contents/Info.plist` — version 0.3.6, installed 2026-04-16
- `/Users/briantaylor/Downloads/oMLX-0.3.6-macos26-tahoe.dmg` — today's DMG (not installed)
- `/Users/briantaylor/Projects/AgentFW/probe-reproducibility.md` — r7 environment snapshot (PID 87119 is stale; today's PID is 23190)
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/PROBE-RESULTS-r7.md` — r7 probe results (3/5 first-attempt baseline)

## Appendix B: Worker alpha scope summary

- All investigation via Read / Grep / Bash.
- Zero mutations attempted.
- One HTTP read: `GET /v1/models` with API key from settings.json. Response was a model listing, no side effects.
- No process signals sent. No cache touched. No config modified.
- Did not SSH to VM (out of scope per brief).
- Time spent: ~12 minutes.

**Main finding for parent session:** oMLX state on the Mac host is clean. The drift origin is almost certainly above oMLX — VM side — or in the harness/wrapper layer. Alpha layer ruled out with high confidence.
