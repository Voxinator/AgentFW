---
type: r7.8 P3a — C1 parser-scrubber vet
date: 2026-04-21
---
# r7.8 P3a — C1 vet

## Md5 pin
- r7.7 baseline (pre-patch, live): `9967c49506ea6a8e9654c9a0191304fe`
- C1-patched (deployed for vet): `68dbae3eb6e2524084414bf4f20b92df`
- Post-revert (must match baseline): `9967c49506ea6a8e9654c9a0191304fe` — MATCH

## Unit tests

13/13 PASS on the hermes-venv Python (`~/.hermes/hermes-agent/venv/bin/python3`). Assertions:

- `_scrub_channel_markers('<channel|>')` == ''
- `_scrub_channel_markers('<|channel|>')` == ''
- `_scrub_channel_markers('thought\n<channel|>')` == ''
- `_scrub_channel_markers('<start|><end|>')` == ''
- `_scrub_channel_markers('<channel|>Hello<channel|>')` == 'Hello'
- `_scrub_channel_markers('See channel 4')` == 'See channel 4' (negative)
- `_scrub_channel_markers('<channel|>thought\n<channel|>' * 21)` == '' (boundary)
- `parse('<channel|>thought\n<channel|>')` → `(None, None)` (full-path)
- `_scrub_channel_markers('analysis\n<channel|>')` == ''
- `_scrub_channel_markers('<tool_call|>')` == ''
- `_scrub_channel_markers('<|return|>')` == ''
- `_scrub_channel_markers('<|message|>')` == ''

All 13 unit assertions PASS. Scrubber works correctly at the function level. Problem surfaces only at integration.

## Conflict with variantH?

Yes. variantH's stage script patches the same file (`gemma_parser.py`). Attempting `probe-variantH-stage.sh stage` on top of a C1-patched file applied variantH's two changes cleanly (no stage error), but variantH's `.probe-r7.6-orig` backup captured the r7.7 baseline rather than the C1-patched file, meaning a subsequent `unstage` would nuke C1. I unstaged variantH and re-deployed the C1 file to preserve Arm A purity per the spec's "Only C1's parser fix is in play" constraint. VariantH never participated in the 5 trials. VariantF + variantG remained staged (they don't touch `gemma_parser.py`); because the Arm A env has no `HERMES_WORKER_OVERLAY`/`HERMES_CHILD_TOOLSET_RESTRICT`/`HERMES_WRITE_BEFORE_CLAIM_GATE` variables set, their hooks are dormant in the no-op path.

## 5-trial results

All trials ran synchronously under ARM=A with TIMEOUT_PER_TURN=1500, OMLX_SWAP_MAX_GB=30, TOOLSETS=`delegation,todo,clarify,file_readonly`, MODEL=`gemma-4-26B-A4B-it-MLX-8bit`.

| Trial | Task | Run | Parent session | Child sessions | Child marker hits | PASS/FAIL | Notes |
|-------|------|-----|----------------|----------------|-------------------|-----------|-------|
| 1 | T4 | 1 | `20260421_003210_32e765` | `003226_8dff2c`, `003233_5ea0ce` | 5 (parent) + 4 (children, across `<tool_call\|>` and `thought\n<channel\|>`) | PASS | Concrete-blocked summary names goal paths (`src/auth/session.ts`, `tests/auth.test.ts`); asks for clarification because paths do not exist on VM. 39s wall. |
| 2 | T5 | 1 | `20260421_003315_75e972` | `003345_253022`, `003349_9a5673`, `003353_e8eb3b`, `003400_7713ed`, `003405_ae5c94` | 14 (parent) + 5 (each child = one `<\|tool_call>…<tool_call\|>` pseudo-tool-call) | PASS | Concrete-blocked summary names goal path `/media/psf/Projects/chief-of-staff-dashboard` and goal ("Save logic / fetching logic / stale data"). 57s wall. Children each emitted a single prefix-stripped pseudo-tool-call that never resolved. |
| 3 | T6 | 1 | `20260421_003433_a888f6` | `003442_1b3fcd`, `003523_df2a7d`, `003557_c795bb`, `003804_f41777`, `003832_84e7f6` | 75 total across parent+5 children | PASS | Concrete-blocked summary names Phase 1 scope and the missing `terminal` tool; child `84e7f6` explicitly lists available tools. 260s wall. This matches r7.7's T6 stuck-long-horizon signature. |
| 4 | T6 | 2 | `20260421_003921_4c8481` | `003930_3718d5` | 14 total | **FAIL (fabrication)** | Parent claims "Phase 1 complete" and "`PLAN.md` has been created at `docs/features/export-feature/PLAN.md`" but VM filesystem has no such file, and TOOLSETS does not include file-write tools. 42s wall (too short for real work). Child emitted `Calling the search_files tool...` trailer only. |
| 5 | T10 | 1 | `20260421_004022_42c376` | `004031_a8d8dc`, `004047_0cdaf8`, `004105_64f945` | 6 total | **FAIL (fabrication)** | Parent claims deliverables at `/home/parallels/Projects/chief-of-staff-dashboard/migrations/pg-upgrade-2026/PLAN.md` — no such file exists on the VM. Children emitted `<\|tool_call>call:bash_executor:execute{...}<tool_call\|>` and `call:bash:execute{...}` pseudo-tool-calls that never executed. 63s wall. |

Per-trial totals (turns containing at least one channel marker, and total marker hits):

- trial1-T4r1: 10 marker turns / 12 hits / 3 sessions
- trial2-T5r1: 19 / 19 / 6
- trial3-T6r1: 75 / 75 / 6
- trial4-T6r2: 14 / 14 / 2
- trial5-T10r1: 6 / 6 / 4
- **GRAND TOTAL: 126 marker hits across all 5 trials' parent + child content**

### Why C1 failed to scrub despite 13/13 unit-test pass

Integration-level dead code path:

1. `run_agent.py:8633` (the only caller of `GemmaToolCallParser.parse`) gates on `"<|tool_call>" in _raw or "[Calling tool:" in _raw`. Content emitted as bare `<channel|>` / `thought\n<channel|>` / `<tool_call|>` (closer-only) does NOT contain the opening `<|tool_call>` sentinel and fails this gate. The parser is never invoked.
2. Even when the parser IS invoked, `run_agent.py:8639-8643` only writes `_parsed_content` back onto `assistant_message.content` when `_parsed_calls` is truthy. A scrub-only result (no tool_calls recovered) is discarded.
3. C1's scrub added at the no-markup early-return (line 71) therefore cannot fire on the dominant pollution pattern — the gate upstream of `parse()` rejects it first.

C1 as specified is structurally insufficient to scrub the dominant channel-pollution pathology because the parser is not the pollution's gatekeeper. Any effective scrubber must live either (a) at run_agent.py's `_raw` consumption site (unconditional, pre-gate), or (b) at the message-persistence site where `assistant_message.content` is finalized.

## Success/failure verdict

- Trial PASS count: **3/5** (T4-r1, T5-r1, T6-r1 = concrete-blocked summaries; T6-r2, T10-r1 = fabrication FAIL). Meets the ≥2/5 threshold.
- Channel-marker count: **126** across 5 trials (must be 0). **Threshold MISSED.**
- Tripwire drift: **NO.** All 4 canonical tripwires PASS pre and post.
- SIGTERM observed: **NO.** Hermes process count returned to idle (1 = pgrep itself) after each trial. No unexpected mid-turn kills.

### Verdict: **REJECT C1**

Rationale: the zero-channel-marker criterion is a hard failure criterion per the spec. C1 scrubs at the parser boundary, but the dominant channel-pollution path (bare `<channel|>` / `thought\n<channel|>` content with no opening `<|tool_call>` sentinel) is gated OUT of the parser entirely at `run_agent.py:8633` before `parse()` is ever called. 126 marker hits across 5 trials confirm C1 does not touch this path. Unit tests pass because the scrubber function itself works; integration fails because the scrubber is never reached.

### Recommendation for P3b / follow-up

The fix must move upstream of the parser gate. Two viable siblings to a re-specced C1:
- **C1'**: Apply `_GEMMA_CHANNEL_MARKER_RE.sub` directly at `run_agent.py:~8630` on `_raw` *before* the gate check. Empty result → replace `assistant_message.content` with None and skip parser. Non-empty scrubbed → feed to parser. This catches all 6 variants regardless of whether structured tool_calls were present.
- **C1''**: Separately, unconditionally apply the scrubber to the session-log persistence layer (wherever `assistant_message.content` is serialized to `sessions/session_*.json`), so even if the live turn slips through, the persisted record is clean.

Both belong in run_agent.py, not gemma_parser.py. The P1b ranking's note that C1 had "highest generalization" was predicated on assumption the parser was always called; that assumption is falsified by this vet.

Secondary finding (bonus for P3b triage): T6-r2 and T10-r1 exhibit **fabrication of completion claims** (model asserts files were written when no write tool was dispatched and no file exists on VM). This is a separate pathology from channel pollution and persists whether C1 is applied or not — it matches r7.6 inv-4 (fabricated completion). C1 neither fixes nor worsens it.

## Revert

- `probe-variantF-stage.sh unstage`: OK — toolsets.py, model_tools.py, run_agent.py restored from `.probe-r7.4-orig`; delegate_worker_v2.py moved to /tmp.
- `probe-variantG-stage.sh unstage`: OK — run_agent.py restored from `.probe-r7.5-orig`.
- `probe-variantH-stage.sh unstage`: already unstaged mid-procedure (to preserve C1 purity); re-confirmed clean at final check.
- `gemma_parser.py` restored from `.probe-r7.8-orig`, backup file removed.
- Final md5: `9967c49506ea6a8e9654c9a0191304fe` — **MATCHES r7.7 baseline**.
- Preflight re-run post-revert: all gates PASS (agent_dispatch, omlx, tripwire, vm_idle).
- Variants unstaged: **YES** (F, G, H all unstaged; only baseline live on VM).
