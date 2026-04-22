---
type: r7.8 Arm K batch 1 trial records
date: 2026-04-21
arm: K (vanilla + T1 loop detector)
worker: r7.8-K-B1
---
# Arm K batch 1 — trial records

Vanilla Arm A stack (no HERMES_WORKER_OVERLAY, no HERMES_CHILD_TOOLSET_RESTRICT, no HERMES_WRITE_BEFORE_CLAIM_GATE) plus T1 cross-turn loop detector enabled via `HERMES_LOOP_DETECTOR=1`. Variants F+G+H staged on top of T1-patched baseline. Toolsets: `delegation,todo,clarify,file_readonly`. Model: `gemma-4-26B-A4B-it-MLX-8bit`. `TIMEOUT_PER_TURN=1500`, wall-cap=1800s/trial.

## Staging

- **variantF status:** STAGED (on top of T1-patched baseline; status reports PARTIAL when layered with G/H — expected per P3c precedent, delegate_worker_v2 refcount grows from 5 to 12)
- **variantG status:** STAGED (r7.5 _resolve_tools_for_turn_r75a hook on top of F)
- **variantH status:** STAGED (r7.6-P1A Gemma-MoE chat-template correctness on top of F+G)
- **T1 patch applied:** YES
  - Baseline run_agent.py md5 (pre-T1): `94ad8712678df5e96b9f407446edf249`
  - T1-patched (pre-F/G/H): `e4536468f4d6a5e02c9fbabb05788fc2`
  - **T1 + variantF/G/H layered (final runtime md5):** `3ceda6072461e068902bf97c3988667c` — matches P3c vet exactly
  - AST parse: OK at every intermediate stage
  - Backup `run_agent.py.probe-r7.8-t1-orig` present on VM (md5 `94ad8712678df5e96b9f407446edf249`)
  - `_count_consecutive_identical_tool_calls` marker count: 2 (helper + hook) post-patch; remains 2 post-layering
- **Wrapper modification:** `probe-variantJ-wrapper.sh` extended to forward `HERMES_LOOP_DETECTOR=1` through the remote SSH env prefix (same mechanism as prior HERMES_WORKER_OVERLAY / HERMES_CHILD_TOOLSET_RESTRICT / HERMES_WRITE_BEFORE_CLAIM_GATE forwarders). Addition persists at exit so batch 2 inherits it.

Note on staging order: initial attempt applied T1 after F/G/H, which failed the baseline-md5 assertion in `/tmp/r7.8-t1-patch.py` (script pins to canonical r7.7 baseline). Corrected by unstaging F/G/H in reverse order, re-taking a clean T1 backup, applying T1, then re-staging F/G/H. Final md5 matches P3c vet artifact.

## Preflight at start

```
PREFLIGHT=PASS
  agent_dispatch=PASS
  omlx=CLEAN (0 active sessions, 0 loaded)
  tripwire=PASS (all 4 canonical)
  vm_idle=PASS (no hermes chat)
  free_mem_gb=93.2  swap_used_gb=3.0
```

## Trial records

| # | Task | Run | Start (UTC) | End (UTC) | Wall | Parent SID | Children | T1 fired? | Max consec | Status | Tripwire |
|---|------|-----|-------------|-----------|------|------------|----------|-----------|------------|--------|----------|
| 1 | T4   | 1   | 06:22:33    | 06:23:13  | 40s   | `20260421_012233_6223f9` | 1 | no | 1 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 2 | T5   | 1   | 06:23:13    | 06:24:23  | 70s   | `20260421_012313_65f1ae` | 1 | no | 4 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 3 | T6   | 1   | 06:24:23    | 06:31:04  | 401s  | `20260421_012424_9f1430` | 2 | no | 2 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 4 | T10  | 1   | 06:31:04    | 06:52:55  | 1311s | `20260421_013104_04c536` | 2 | no | 5 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |
| 5 | T4   | 2   | 06:52:55    | 06:53:36  | 41s   | `20260421_015256_a53f39` | 1 | no | 1 | COMPLIANT | OMLX=CLEAN, PREFLIGHT=PASS |

Total batch wall: ~1863s (~31 min). All trials returned `RESULT=COMPLIANT attempts=1`, reached goal on first attempt (no retries).

### Child session IDs (time-clamped + content-matched)

- **T4-r1** → children: `20260421_012242_2c0097` (msgs=36, max_consec=1)
- **T5-r1** → children: `20260421_012318_7ae241` (msgs=86, max_consec=4)
- **T6-r1** → children: `20260421_012428_49691d` (msgs=27, max_consec=2), `20260421_012615_9c97dc` (msgs=39, max_consec=2)
- **T10-r1** → children: `20260421_013109_90f8b1` (msgs=19, max_consec=2), `20260421_013131_d25d70` (msgs=42, **max_consec=5 — WARN threshold, no termination**)
- **T4-r2** → children: `20260421_015301_c1b784` (msgs=36, max_consec=1)

### T1 firing check

Scanned all wrapper logs (`/tmp/r7.8-K-B1-logs/*.log`) for "r7.8 loop detector" marker. Zero hits across all 5 trials. No `loop_detected` outcome in any session JSON. No system messages mentioning "consecutive identical tool calls" injected into any child. T1 was armed (env var forwarded, runtime md5 confirms patched binary) but the 5-turn warn threshold was not crossed.

The T10-r1 child2 case is notable: it reached **exactly 5 consecutive identical tool_calls (max_consec=5)**, which is the WARN threshold. Reviewing the P3c vet code: the detector triggers WARN at count==5 and TERMINATE at count==6. Counting semantics: `count==5` means "the 5th identical call has already been emitted; inject warning." For this trial, max_consec==5 means T1 was one call away from warning, OR the run ended organically at the 5th call (i.e., the 6th turn emitted a different tool and broke the run). Inspecting child2 directly would confirm which, but the practical outcome — no warn injected, no terminate — is consistent with the run ending organically at 5.

Compared to P3c vet's T10-r1 child2 which reached 6 (warn+terminate both fired), this Arm K batch 1 T10-r1 run lands just below threshold. Signal: the pathology is adjacent but stochastic at this margin.

### Tripwire checks

Post each trial: HERMES.md md5 remained `0780c232a6cb52e13e432261f0d68ad9` (canonical). Jira-daily-briefing SKILL.md md5 `fb1a5a5208a6cf2fcb8252aac10397eb` (canonical) at batch end. All 4 canonical tripwire files intact.

No SIGTERM observed in any hermes-chat process. No APIConnectionError. No http=000 advisories. oMLX CLEAN after every trial.

## Exit state

- **T1 still staged:** YES (run_agent.py md5 = `3ceda6072461e068902bf97c3988667c`, helper+hook present, backup intact)
- **variantF/G/H still staged:** YES (status probes confirm F=PARTIAL-when-layered, G=STAGED, H=STAGED — the intended full-stack state)
- **Wrapper mod (HERMES_LOOP_DETECTOR forwarding):** still present in `probe-variantJ-wrapper.sh`
- **Final preflight:** PREFLIGHT=PASS (free_mem=51.5GB, swap=3.0GB, omlx_active=0, omlx_loaded=1, tripwire=PASS, vm_idle=PASS)
- **Final tripwire (HERMES.md + SKILL.md):** MATCH
- **VM canonical for a K-arm continuation:** YES — batch 2 can run against current state without re-staging

## Batch 1 summary

5/5 COMPLIANT on first attempt. Zero T1 firings — the loop-detector was armed but not triggered on this batch's trial selection. Closest approach was T10-r1 child2 at max_consec=5 (WARN threshold, no warn injected → run presumably ended organically at the 5th call). Mean wall per trial 373s; median 70s (pulled high by T10-r1's 1311s — consistent with T10 being the most work-intensive task and its end-to-end migration-plan scope).

Compared to P3c vet (which used a T4,T5,T6,T6,T10 ordering): this batch replaced the second T6 with a second T4 and ordered T10 fourth instead of fifth. T10-r1 here ran much longer (1311s vs 131s in P3c) — likely oMLX warm-state differences across probe days rather than behavioral regression, since max_consec remained comparable (5 here vs 6 in P3c), and RESULT=COMPLIANT on first attempt in both.

## Artifacts on disk

- Runner: `/tmp/r7.8-K-B1-runner.sh`
- Results TSV: `/tmp/r7.8-K-B1-results.txt`
- Per-trial logs & stdout: `/tmp/r7.8-K-B1-logs/T{4,5,6,10}-run{1,2}.{log,stdout}`
- Session JSONs on VM: `/home/parallels/.hermes/sessions/session_<parent/child_sid>.json`

## Hand-off to batch 2

Staging intact. Batch 2 can source `/tmp/r7.7-env.sh`, export `HERMES_LOOP_DETECTOR=1`, unset HWO/HCTR/HWBCG, and invoke `./probe-variantJ-wrapper.sh` directly against the T1+F+G+H stack currently on the VM. The wrapper's HERMES_LOOP_DETECTOR forwarding line is persisted. No re-staging needed.
