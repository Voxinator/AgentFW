---
type: r7.8 P3b — S1 sampler-tune vet
date: 2026-04-21
worker: P3b vet worker
candidate: S1 — conservative sampler tune
model: gemma-4-26B-A4B-it-MLX-8bit (Gemma-4 MoE)
---
# r7.8 P3b — S1 vet

## Md5 pin

- r7.8 baseline: `0afa458cd2441524782b94a64bd952ae`
- S1-patched:    `79ad2c25bdb7d851e00b7653b8c0f937`
- Post-revert:   `0afa458cd2441524782b94a64bd952ae` (**matches baseline**)

## Diff applied

Single target entry: `models."gemma-4-26B-A4B-it-MLX-8bit"` in `/Users/briantaylor/.omlx/model_settings.json`.
(The spec name "Gemma-4-26B-A4B-MLX-8bit" best-matches this entry; the `-it-` infix is the only deviation. No other Gemma entry was modified — `gemma-4-31b-it-4bit` is the dense variant and outside the MoE target scope.)

```diff
      "max_context_window": 131072,
      "max_tokens": 16384,
-     "temperature": 0.8,
-     "top_p": 0.95,
-     "top_k": 64,
+     "temperature": 0.6,
+     "top_p": 0.9,
+     "top_k": 40,
      "force_sampling": false,
      ...
-     "is_default": false
+     "is_default": false,
+     "repetition_penalty": 1.08,
+     "min_p": 0.03
```

All five S1 keys applied as specified. `max_tokens=16384` preserved.

## Hot-reload verdict

**SUCCESS.**

- Documented endpoint `/admin/api/reload-models` is stale — current oMLX exposes `/admin/api/reload`.
- Admin endpoints require a **session cookie**, not Bearer. Flow: `POST /admin/api/login` with JSON body `{"api_key": "<OMLX_API_KEY>"}` → `Set-Cookie` → pass `-b` on subsequent admin calls.
- `POST /admin/api/reload` returned `{"status":"ok","message":"Re-discovered 12 models from 2 directories"}` (HTTP 200).
- In-memory settings verified via `GET /admin/api/models`: `temperature=0.6, top_p=0.9, top_k=40, repetition_penalty=1.08, min_p=0.03`. All five keys applied.
- Post-revert verification: `temperature=0.8, top_p=0.95, top_k=64, repetition_penalty=None, min_p=None` — confirms revert took effect in-memory.

Endpoint discrepancy flagged for P1c doc correction but did not block the vet.

## 5-trial results

Vanilla Arm A (variantF + G + H staged; no A1 / A2 / HWO / C1). Serial execution. Wrapper: `probe-variantH-wrapper.sh`. Toolsets: `delegation,todo,clarify,file_readonly`. `TIMEOUT_PER_TURN=1500`, wall-clock cap=1800s.

| Trial | Task | Run | Parent SID | Children (N) | Parent turns | Child turns (sum) | **Total turns** | **Max consec identical tool_calls** | Channel markers (total) | Wrapper verdict | Deep PASS/FAIL |
|-------|------|-----|------------|--------------|--------------|-------------------|-----------------|--------------------------------------|------------------------|-----------------|----------------|
| 1 | T4  | 1 | `20260421_004812_28a0a9` | 1 | 2 | 12 | **14** | **1** | 11 | COMPLIANT | PASS |
| 2 | T5  | 1 | `20260421_004856_1ef98c` | 2 | 6 | 49 | **55** | **8** | 33 | COMPLIANT | **FAIL (degenerate loop)** |
| 3 | T6  | 1 | `20260421_005015_416a02` | 1 | 4 | 18 | **22** | **3** | 16 | COMPLIANT | PASS |
| 4 | T6  | 2 | `20260421_005105_8a49bf` | 1 | 7 | 29 | **36** | **2** | 31 | COMPLIANT | PASS |
| 5 | T10 | 1 | `20260421_005230_ac6420` | 2 | 4 | 81 | **85** | **36** | 54 | COMPLIANT | **FAIL (degenerate loop)** |

Per-child detail on the two degenerate-loop trials:
- **T5-r1 child0** (`20260421_004900_5400e2`): 46 turns, 45 tool_calls, `max_run=8` consecutive identical tool_calls. 25 channel markers in content.
- **T10-r1 child0** (`20260421_005235_068a8d`): 51 turns, 50 tool_calls, `max_run=36`. Hard Mode D loop.
- **T10-r1 child1** (`20260421_005502_87c71d`): 30 turns, 30 tool_calls, `max_run=27`. Hard Mode D loop.

Tripwire post each trial: PASS (all 4 canonical). No SIGTERM observed in any hermes process. All wrappers returned `RESULT=COMPLIANT`.

## Verdict

- PASS count (wrapper check.py): 5/5
- PASS count (deep criteria — no degenerate loop): **3/5** (T4, T6-r1, T6-r2)
- Turn counts sorted: [14, 22, 36, 55, 85]
- **Median total turns: 36** (threshold ≤15 — **2.4× over**)
- Mean total turns: 42.4
- **Any trial with ≥5 consecutive identical tool_calls: YES** — T5-r1 (8), T10-r1 (36 AND 27)
- Tripwire drift: NO
- SIGTERM: NO
- Hot-reload accepted: YES

### **Verdict: REJECT S1**

**Reasons (ANY of these trigger REJECT per success criteria):**
1. Median turn count 36 vastly exceeds ≤15 threshold. S1's `repetition_penalty=1.08` did not curb overshoot — T10-r1 consumed 85 total turns, worse than r7.7's 42/48-turn overshoots. S1 failed its primary mechanism-of-action prediction.
2. Three trials (T5-r1, T10-r1 ×2 children) exhibit **≥5 consecutive identical tool_calls**. This is the Mode D "degenerate loop" indicator — exactly what `repetition_penalty` was hypothesized to damp. T10-r1's child0 produced 36 consecutive identical tool_calls despite the repetition penalty — suggesting `repetition_penalty` applies at token level (where tool-call JSON scaffold is stable noise) and does not meaningfully reduce semantic-level repetition across tool-call arguments.
3. Channel marker pollution is untouched (expected — S1 doesn't target it), but counts are high (11–54 per trial) confirming the P1c diagnosis that channel leakage requires a separate intervention (S3 / C1 / reasoning_parser).

### Collateral observation

Wrapper `check.py` (COMPLIANT verdict path) is **not sensitive to Mode D degenerate loops** — all 5 trials passed its gate even when a child executed 36 consecutive identical tool_calls. The wrapper's pass/fail signal is therefore misleading as a single-metric gate for sampler research; deep metrics are mandatory. Flag for P3 planner: the vet's quantitative criteria (median turns, max_run) caught the failure the wrapper missed. Keep deep-metric analysis as a gating layer for all remaining candidates.

Notably the overall PASS rate (5/5 wrapper) is consistent with the side finding in P3a that vanilla Arm A hit 3/5 — S1 did not make things worse on the coarse check, but it did not deliver the targeted improvements either. On median total turns (42.4 mean) S1 actually looks **worse** than the r7.7 Arm G baseline cited in the vet spec (20+ median). If anything, the conservative sampler slowed progress toward the goal without preventing loops.

## Revert verified

- `model_settings.json` md5 matches baseline: **YES** (`0afa458cd2441524782b94a64bd952ae`)
- `/admin/api/reload` re-issued post-revert; in-memory settings show baseline values (temp=0.8, top_p=0.95, top_k=64, rep_pen=None, min_p=None)
- variantH unstaged: YES (gemma_parser.py and run_agent.py restored from `.probe-r7.6-orig`)
- variantG unstaged: YES (run_agent.py restored from `.probe-r7.5-orig`)
- variantF unstaged: YES (toolsets.py, model_tools.py, run_agent.py restored from `.probe-r7.4-orig`; `delegate_worker_v2.py` moved aside)
- HERMES.md tripwire: **MATCH** (`PREFLIGHT=PASS`, `[GATE: tripwire] PASS (all 4 canonical)`)
- Admin session cookie `/tmp/omlx-cookies.txt` removed
- No residual `.probe-r7.8-orig` file left in `~/.omlx/`

## Notes for planner

1. **S4 gating.** P2 synthesis specifies S4 (S1 + S3 combined) runs only if S1 vet passes. **S1 failed**; per spec, substitute T1 (cross-turn loop detector, score 17) as Candidate 3 — the Mode D failure mode here is exactly what T1 is designed to catch at the harness level. T1 may be the right intervention even without S1 as floor.
2. **Hot-reload doc patch.** `ARTIFACT-r7.8-P1c-sampler-research.md` lists `POST /admin/api/reload-models` — current oMLX exposes `POST /admin/api/reload` only, and requires a session cookie from `POST /admin/api/login` (JSON body with `api_key`). The Bearer token that works for `/v1/*` is **not** accepted by `/admin/*`. Suggest a one-line correction in that doc.
3. **repetition_penalty mechanism note.** The 1.08 penalty did not reduce tool_call-level repetition. Hypothesis: in Gemma-4 MoE's tokenization, the tool_call JSON structure (`{"name":"search_files","arguments":...`) shares enough stable token prefix that the penalty spreads across scaffold tokens rather than distinguishing semantic repetition. Future sampler research may need a higher penalty (1.15+) AND narrower top_p/top_k (0.85/30) to bite — or shift to a cross-turn loop detector (T1) that operates at the tool_call-hash layer instead of token layer.
4. **Channel markers.** Persistent across all 5 trials regardless of sampler config, confirming P1c's diagnosis that only S3 / reasoning_parser / C1-variant can address this class. Revisit after loop-detection gating is in place.

## Trial infrastructure artifacts

- Logs: `/tmp/r7.8-P3b-S1-logs/{T4,T5,T6,T10}-run*.log`
- Trial runner: `/tmp/r7.8-P3b-S1-run-trial.sh`
- Session JSONs on VM: `/home/parallels/.hermes/sessions/session_202604210[0-5]*.json`

Time budget used: ~35 min end-to-end (well within 60–90 min budget).
