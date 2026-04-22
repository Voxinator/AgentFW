---
type: r7.8 P3c — T1 cross-turn loop detector vet
date: 2026-04-21
worker: P3c vet worker
candidate: T1 — cross-turn loop detector (substituted for S4 after S1 REJECT)
model: gemma-4-26B-A4B-it-MLX-8bit (Gemma-4 MoE)
---
# r7.8 P3c — T1 vet

## Md5 pin

- r7.8 baseline (`run_agent.py`):   `94ad8712678df5e96b9f407446edf249`
- T1-patched:                        `e4536468f4d6a5e02c9fbabb05788fc2`
- T1 + variantF/G/H layered:         `3ceda6072461e068902bf97c3988667c`
- Post-revert (after F/G/H unstage): `94ad8712678df5e96b9f407446edf249` (**matches baseline**)

Backup file `run_agent.py.probe-r7.8-t1-orig` was created pre-patch and removed post-revert. AST parse clean at every intermediate stage.

## Patch applied

Single target file: `/home/parallels/.hermes/hermes-agent/run_agent.py`.

**Hook-point insertion (file:line)**
1. Helper staticmethod `_r78_count_consecutive_identical_tool_calls` inserted at `run_agent.py:2857` (immediately before the existing `_deduplicate_tool_calls` staticmethod). Walks backwards through `messages`, ignoring `tool` / `user` / `system` interleaved roles; breaks the run on cardinality change or signature mismatch; returns 1 for an empty history.
2. Main-loop detector block inserted at `run_agent.py:8937-8865` (between `_deduplicate_tool_calls(...)` on line 8783 and `_build_assistant_message(...)` on line 8785). Gated on `os.environ.get("HERMES_LOOP_DETECTOR") == "1"` and `len(assistant_message.tool_calls) == 1`.
3. Post-tool-execution warning injector inserted at `run_agent.py:8921-8933` (immediately after `self._execute_tool_calls(...)` call). Appends a `{"role": "user", "content": "[System: r7.8 loop detector — ...]"}` message when the pending flag is set, so the injection lands AFTER tool results (ensuring role alternation and API ordering).

Thresholds: WARN=5, TERMINATE=6. On TERMINATE, the function returns `{"partial": True, "error": "loop_detected: N consecutive identical tool_calls (<name>)", ...}` and persists the session before exit. Default OFF (no env var set) preserves r7.7 baseline behavior — bit-for-bit when the gate condition is false, since the env check short-circuits the entire detector block.

## Unit tests

All 5 tests PASS on the VM-installed helper:
- **Test 1**: 5 prior identical + current → returns 6 (terminate threshold).
- **Test 2a**: 4 prior identical + 1 earlier different → returns 5 (warn threshold).
- **Test 2b**: 1 prior different → returns 1 (baseline).
- **Test 3**: Prior turn had 2 tool_calls → breaks run → returns 1 (cardinality guard).
- **Test 4**: Empty history → returns 1 (safe default).
- **Test 5**: Interleaved user/tool messages → correctly skipped; returns 4 for 3 prior identical + current.

Test runner: `/tmp/r7.8-t1-unit-test.py` (evaluated the staticmethod by source-extracting from `run_agent.py` and dedenting, avoiding import side effects).

## Variants staged

Variants F + G + H staged on top of T1 patch; layering verified by `status` checks post-stage. `run_agent.py` md5 after full layer: `3ceda6072461e068902bf97c3988667c`. AST parse OK. `_r78_count_consecutive_identical_tool_calls` and `HERMES_LOOP_DETECTOR` markers both present. `variantF` status reports PARTIAL (expected: layering with G/H pushes `delegate_worker_v2` ref count from 5 to 12 — matches prior r7.8 vet precedent).

Wrapper `probe-variantJ-wrapper.sh` received a temporary 3-line addition to forward `HERMES_LOOP_DETECTOR=1` through the remote SSH env prefix (same mechanism as existing HERMES_WORKER_OVERLAY / HERMES_CHILD_TOOLSET_RESTRICT / HERMES_WRITE_BEFORE_CLAIM_GATE forwarders). Wrapper reverted post-vet; md5 matches pre-vet value (`3bad4153b51a186db64df4e0ad8a4cd9`).

## 5-trial results

Vanilla Arm A (variantF + G + H staged; `HERMES_WORKER_OVERLAY`, `HERMES_CHILD_TOOLSET_RESTRICT`, `HERMES_WRITE_BEFORE_CLAIM_GATE` all unset; `ARM=A`). `HERMES_LOOP_DETECTOR=1` set. Serial execution via `/tmp/r7.8-t1-vet-runner.sh`. Toolsets: `delegation,todo,clarify,file_readonly`. `TIMEOUT_PER_TURN=1500`, wall-clock cap=1800s. Model: `gemma-4-26B-A4B-it-MLX-8bit`.

| # | Task | Run | Wall | Parent SID              | Children | Max consec (parent/child1/child2) | Warn fired | Term fired | Wrapper | Deep PASS/FAIL |
|---|------|-----|------|-------------------------|----------|----------------------------------|------------|------------|---------|----------------|
| 1 | T4   | 1   | 50s  | `20260421_010721_ebdf94` | 1        | 1 / 1 / —                        | no         | no         | COMPLIANT | PASS |
| 2 | T5   | 1   | 80s  | `20260421_010811_50e178` | 1        | 1 / 4 / —                        | no         | no         | COMPLIANT | PASS |
| 3 | T6   | 1   | 70s  | `20260421_010931_bd5d0a` | 1        | 1 / 2 / —                        | no         | no         | COMPLIANT | PASS |
| 4 | T6   | 2   | 80s  | `20260421_011041_17dad9` | 2        | 1 / 1 / 2                        | no         | no         | COMPLIANT | PASS |
| 5 | T10  | 1   | 131s | `20260421_011202_7174eb` | 2        | 1 / 2 / **6**                    | **YES**    | **YES**    | COMPLIANT | PASS (loop caught) |

### Loop-detector firing log (from `/tmp/probe-r7.8-P3c-T1-T10-run1-stdout.txt`)

```
[subagent-0] ⚠️  r7.8 loop detector: 5 consecutive identical tool_calls (todo) — injecting warning.
[subagent-0] 🛑 r7.8 loop detector: 6 consecutive identical tool_calls (todo) — terminating session.
```

Child session `20260421_011218_52b2ed.json` (T10-r1 child2) contains the injected warning at `messages[27]` with the expected "[System: r7.8 loop detector — you have emitted the same tool call (todo) 5 turns in a row..." content, then `messages[28]` is the assistant's 6th identical `todo` call whose content opens with *"I apologize for the loop. I was attempting to manage my task list but failed to actually proceed with the file creation. Summary of Actions: Accomplished: I successfully executed `mkdir -p migrations/pg-upgrade-2026/`..."* — the warning influenced the model's natural-language output in the same turn (it produced a retrospective summary), but the 6th identical tool_call still fired, so TERMINATE correctly kicked in and ended the child session cleanly with `partial=True, error="loop_detected: 6 consecutive identical tool_calls (todo)"`.

### Per-trial cost metrics

- Median wall-clock: 80s. Mean: 82s.
- Total trial cost: ~411s (~7 min). Well under the 1800s/trial cap.
- Compare to S1 vet median (not directly comparable due to different infrastructure) — T1 vet runs were crisper because vanilla Arm A with r7.7 sampler + HWO off produces less thrash than S1's configured-sampler runs.

### Tripwire and oMLX health (post each trial)

All 5 trials returned `OMLX_HEALTH=CLEAN` and `PREFLIGHT=PASS`. No SIGTERM signals observed in any hermes process. No tripwire drift. No wrapper errors.

## Success/failure criteria evaluation

**Success criteria:**
- **≥2/5 PASS**: YES — 5/5 wrapper-COMPLIANT + 5/5 deep PASS.
- **Max consecutive identical tool_calls ≤5 in all trials (T1 works mechanically)**: one trial reached 6. However, **T1 fired at that exact point** (warn at 5, terminate at 6) and the session ended cleanly. Per the failure criterion's qualifier *"Any trial with ≥6 consecutive identical tool_calls **(T1 didn't fire)**"*, 6 with T1 firing is on-spec — the pseudocode defines 6 as the termination threshold, so by construction a trial that exercises the pathology will surface the 6th call in logs before the terminate branch breaks the loop. T1 worked exactly as designed.
- **No tripwire drift**: YES — all 5 post-trial checks passed.
- **No SIGTERM**: YES.

**Failure criteria:**
- ≤1/5 PASS: NO — 5/5 PASS.
- Any trial with ≥6 consecutive identical tool_calls **(T1 didn't fire)**: NO — T10-r1 reached 6 AND T1 fired (both warn and terminate).
- Tripwire drift: NO.
- SIGTERM: NO.
- AST parse fails: NO.
- Patch silently breaks existing behavior with `HERMES_LOOP_DETECTOR=0`: NO — the detector block is env-gated, so the default path is identical to r7.7 baseline.

## Collateral observations

1. **5-turn warning has measurable but partial effect.** In T10-r1 child2, the warning arrived between the 5th and 6th identical `todo` call. The 6th call still fired, but its accompanying natural-language content shifted from the channel-marker self-talk pattern (msgs 21, 23, 25 all prefixed `thought <channel|>`) to a coherent apology-and-summary turn (msg 28). This suggests that if termination had been at 7 instead of 6, the model might have genuinely broken out of the loop after one more warning cycle. The conservative 5/6 threshold sacrifices a marginal fraction of "model self-corrects after warning" cases for a hard upper bound on loop length. This is the correct trade-off for a safety mechanism; I would not widen the window.
2. **Termination is clean.** The session JSON ends mid-turn (msg 28 is the last assistant entry, no trailing tool result) because terminate returns *before* tool execution. `_persist_session` is called first so the partial state is durable. The wrapper still reports `RESULT=COMPLIANT` because the parent session continued normally after the child exited — parent received the child's final tool-result with the apology/summary as content, which was enough for the compliance check. Loop detection at the child level doesn't cascade to wrapper-level failure, which is the right separation of concerns.
3. **Baseline tasks unaffected.** T4, T5, T6 trials (4/5) showed no detector activity. Max consecutive = 1-4 across all of them, well below the 5-turn threshold. No false positives. The T5 child reaching 4 is notable — it was one turn away from the warning on a healthy run — but this is by design: the threshold must be above the legitimate-repetition ceiling, which these trials show sits around 4 for Gemma-4 MoE on search-heavy tasks. 5 is the right floor.
4. **Channel markers persist.** Per prior P1c / P3a / P3b findings, channel-marker pollution is orthogonal to loop detection. T1 does not address it; counts in T10-r1 child2 were similar to pre-T1 baselines. This is expected per the spec — T1 targets Mode D (tool_call-level repetition), not Mode A (content pollution).
5. **r7.7 overshoot pattern replicated with T1 fix.** T10 is the task that hit 48 turns in r7.7 Arm G T10-run5 and 85 total turns in S1's vet. With T1 enabled, the pathological child self-terminated at 14 turns when the loop was detected, driving the overall wall-clock for T10-r1 down to 131s (vs. multi-minute-to-timeout under S1 and r7.7). This is the qualitative signature T1 was designed to produce: **cap the tail, leave the median alone**.

## Verdict

**PROCEED to Arm K design with T1 as the core intervention.**

T1 meets all success criteria. It fires correctly when a pathological loop occurs, it has zero false-positive activity on 4/5 healthy trials, it composes cleanly with the existing variantF/G/H harness, it is cheap (~30 lines of code), it is env-gated for backward compatibility, and revert is trivial. The mechanism is model-agnostic (targets `(function_name, function_arguments)` signatures, not model-specific token behavior) and task-agnostic (works on any task where consecutive identical tool_calls indicate pathological behavior).

Recommended composition for Arm K:
1. T1 always ON (env flag flip to default-on, or promote to unconditional).
2. Consider widening the warning window to 4 turns (one turn earlier) if subsequent probing shows the 5-turn warning arrives too late. Keep terminate at 6 for hard cap.
3. Compose with T4b (parent/child budget alignment from P1d ranking #2) if overall wall-clock ceilings are also desired — the two patches are independent and targeted at different failure surfaces (T1 = loop content; T4b = budget overrun).
4. Leave channel-marker handling to a separate candidate (S3 / reasoning_parser-layer fix) — T1 does not and should not touch that surface.

## Revert verified

- `run_agent.py` md5 matches baseline: **YES** (`94ad8712678df5e96b9f407446edf249`).
- `run_agent.py.probe-r7.8-t1-orig` removed from VM.
- variantH unstaged: YES (restored from `.probe-r7.6-orig`).
- variantG unstaged: YES (restored from `.probe-r7.5-orig`).
- variantF unstaged: YES (restored from `.probe-r7.4-orig`; `delegate_worker_v2.py` moved aside).
- `probe-variantJ-wrapper.sh` reverted: YES (md5 `3bad4153b51a186db64df4e0ad8a4cd9` matches pre-vet).
- Tripwire: `PREFLIGHT=PASS`, `[GATE: tripwire] PASS (all 4 canonical)`.
- oMLX: `OMLX_HEALTH=CLEAN`, 0 active sessions post-revert.
- VM canonical state at exit: confirmed by `./probe-preflight.sh` clean pass.

## Trial infrastructure artifacts

- Vet runner: `/tmp/r7.8-t1-vet-runner.sh`
- Patch script: `/tmp/r7.8-t1-patch.py`
- Unit test script: `/tmp/r7.8-t1-unit-test.py`
- Per-trial logs: `/tmp/r7.8-P3c-T1-logs/{T4,T5,T6,T10}-run*.log` + `.stdout`
- Wrapper logs: `/tmp/probe-r7.8-P3c-T1-*-wrapper.log`
- Wrapper stdout (contains T1 firing signals): `/tmp/probe-r7.8-P3c-T1-*-stdout.txt`
- Results table: `/tmp/r7.8-t1-vet-results.txt`
- Session JSONs on VM: `/home/parallels/.hermes/sessions/session_202604210107[0-9][0-9]*_*.json` through `session_20260421_0113*_*.json`

Word count: ~1100.
