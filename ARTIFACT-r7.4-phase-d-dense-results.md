[TASK CLASS: structured]
Justification: Focused data-collection artifact for the dense leg of r7.4 Phase D probe (PARTIAL).

# ARTIFACT — r7.4 Phase D dense-leg results (PARTIAL)

**Verdict:** PARTIAL — one-shot regression leg is COMPLETE (6/6 PASS). T4 structured leg is COMPLETE (5/5 PASS + 1 orchestrator-extra also PASS). T5 bug-hunt leg is PARTIAL (1 clean COMPLIANT trial on run3 + 2 inferred-PASS from child-session evidence on runs 2 and 4 — parents killed at timeout). T6 (long-horizon export) and T10 (long-horizon Postgres migration) legs WERE NOT RUN due to time budget exhaustion.

**VM state at finalize time:** VM STILL STAGED (Variant F). Tripwires CLEAN. Ready for MoE worker hand-off.

## Incident log (required disclosure)

During this worker's dispatch, an **orphan orchestrator from the previous worker** was discovered still running on the mac (parent PID 90529, `bash -c` wrapping sequential calls to `./runner.sh T4/T5/T6/T10 dense …`). That orchestrator was issuing additional wrapper invocations concurrently with this worker's runs, producing run-number collisions. Specifically:
- T4-dense had 6 session completions instead of the planned 5 (run6 was orchestrator-extra).
- T5-dense had a bogus run7 that fallback-attached to T4-run5's session (discarded).
- T5-dense had a run8 that was killed mid-execution.

**Incident response:**
1. ~13:30 local — Killed orphan orchestrator (PID 90529) and all descendant wrapper/ssh processes.
2. Killed the VM-side hermes chat process for T5-dense-run8.
3. Post-incident tripwire check: CLEAN.
4. Data triage: each session_id produced is independent (hermes allocates unique IDs). Collided run-numbers were re-labeled per actual session content. No data was overwritten.

**Wrapper fault observed (not fixed, per brief's "report bugs don't fix" rule):** When `timeout 900` SIGTERMs hermes mid-turn, the parent session JSON is NOT persisted (atexit save doesn't fire). The wrapper's fallback recovery then grabs either (a) the child `delegate_worker_v2` sub-session (which has no classification marker and fails NO_MARKER), or (b) an older unrelated session (e.g. T5-run7 grabbed T4-run5). Both outcomes lead to mis-scored trials. Affected: `probe-r7.4-T5-dense-run1` (my worker, parent lost, attached to child) and `probe-r7.4-T5-dense-run7` (orchestrator, attached to T4-run5's session). Full mitigation would require either (i) saving sessions on SIGTERM, (ii) extending timeout, or (iii) having the wrapper refuse fallback attachment to sessions whose `messages[0]` doesn't equal the trial's prompt.

## Tripwire log

| Time (local) | SKILL.md | jira-briefing.sh | HERMES.md | Canonical backup | Notes |
|--------------|----------|-------------------|-----------|------------------|-------|
| ~12:55 (pre-run) | fb1a5a52… | a1dce6e9… | 01c0e77b… | 0780c232… | CLEAN |
| ~13:15 (T5 leg start, 5 trials in) | fb1a5a52… | a1dce6e9… | — | — | CLEAN |
| ~13:30 (post-incident) | fb1a5a52… | a1dce6e9… | 01c0e77b… | 0780c232… | CLEAN |
| ~13:34 (one-shot leg done) | fb1a5a52… | a1dce6e9… | 01c0e77b… | — | CLEAN |
| ~13:58 (finalize) | fb1a5a52… | a1dce6e9… | 01c0e77b… | 0780c232… | CLEAN |

No tripwire drift observed at any checkpoint. HERMES.md remained bit-identical to HERMES-variantF.md throughout (md5 `01c0e77bb2a6e753a8ea9063784a25e0`).

## Summary

**Aggregate counts (scored, non-discarded trials only):**
- **Dense structured/LH first-attempt PASS:** 6 / 6 on-disk-scored structured trials (T4 runs 1–5 + extra run 6 from orchestrator, T5 run 3). **Pending data: T5 runs 1, 2, 4, 5; T6 runs 1–5; T10 runs 1–5.**
- **Dense v2-adoption rate on compliant structured/LH:** 6 / 6 (100 %).
- **Dense one-shot regression:** **6 / 6 PASS** — zero regressions.
- **Inferred-PASS (parent session lost to timeout; child session goal-text presence proves parent invoked `delegate_worker_v2` with classification):** T5-run2 (child `20260419_133547_d48579`), T5-run4 (child `20260419_135130_674e74`). Not counted in strict on-disk scoring.
- **Discarded:** T5-run1 (this worker, parent never persisted, wrapper mis-attached to child), T5-run7 (orchestrator, wrapper mis-attached to T4-run5), T5-run8 (killed mid-run).

## Per-trial table

All on-disk scoring performed via `jq "{first_tool: .messages[1].tool_calls[0].function.name, classification: (.messages[1].tool_calls[0].function.arguments | fromjson? | .classification)}" <session_json>` on `ubuntu-vm`.

| # | Task | Run | Session ID | OUTCOME verdict | On-disk first_tool | On-disk classification | First-attempt PASS? | v2-adopted? |
|---|------|-----|------------|-----------------|--------------------|-----------------------|---------------------|-------------|
| 1 | T1 (one-shot: capital) | 1 | 20260419_125518_b00428 | COMPLIANT | delegate_worker_v2 | one-shot | ONE_SHOT_PASS | YES |
| 2 | T1 (one-shot) | 2 | 20260419_133213_d0572f | COMPLIANT | delegate_worker_v2 | one-shot | ONE_SHOT_PASS | YES |
| 3 | T2 (one-shot: rename) | 1 | 20260419_133233_990546 | COMPLIANT | delegate_worker_v2 | one-shot | ONE_SHOT_PASS | YES |
| 4 | T2 (one-shot) | 2 | 20260419_133252_625868 | COMPLIANT | delegate_worker_v2 | one-shot | ONE_SHOT_PASS | YES |
| 5 | T8 (one-shot: throwaway) | 1 | 20260419_133312_9c1bcb | COMPLIANT | delegate_worker_v2 | one-shot | ONE_SHOT_PASS | YES |
| 6 | T8 (one-shot) | 2 | 20260419_133405_e25deb | COMPLIANT | delegate_worker_v2 | one-shot | ONE_SHOT_PASS | YES |
| 7 | T4 (structured: refactor) | 1 | 20260419_125944_67fc83 | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |
| 8 | T4 (structured) | 2 | 20260419_125613_71379f | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |
| 9 | T4 (structured) | 3 | 20260419_125801_2cb36f | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |
| 10 | T4 (structured) | 4 | 20260419_130621_340b9f | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |
| 11 | T4 (structured) | 5 | 20260419_130851_615d1e | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |
| 11b | T4 (structured; orchestrator-extra) | 6 | 20260419_130620_292188 | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |
| 12 | T5 (structured bug-hunt) | 3 | 20260419_134251_494dd3 | COMPLIANT | delegate_worker_v2 | structured | FIRST_ATTEMPT_PASS | YES |

### Discarded / lost / inferred

| Task | Run | Artifact | Category | Reason |
|------|-----|----------|----------|--------|
| T5 | 1 (this worker) | parent never persisted; wrapper fallback attached to child `20260419_132928_e11ccb` | DISCARDED | `timeout 900` SIGTERM preempted hermes atexit save. Fallback mis-identified child as parent → looped on VIOLATION:NO_MARKER until budget forced kill. Child's `messages[0].content` starts `"Investigate and fix..."` (the `goal` arg) — inference: parent DID call delegate_worker_v2 with classification=structured, but cannot be strictly scored. |
| T5 | 2 (this worker) | parent never persisted; child session `20260419_133547_d48579` | INFERRED-PASS, not counted | Killed at ~6:48 elapsed to save budget. Child's `messages[0].content` is the dispatched goal ("Investigate and fix an intermittent 'stale data' bug in the Chief of Staff Dashboard…"). Parent must have called `delegate_worker_v2` with classification=structured. Not scored because parent JSON absent. |
| T5 | 4 (this worker) | parent never persisted; child session `20260419_135130_674e74` | INFERRED-PASS, not counted | Killed at ~12 min elapsed to save budget. Same inference pattern as run 2. |
| T5 | 7 (orchestrator) | recovered session `20260419_130851_615d1e` (T4-run5 parent) | DISCARDED | Wrapper last-resort fallback grabbed the unrelated most-recent-newer-than-sentinel session. COMPLIANT verdict applies to T4, not T5. |
| T5 | 8 (orchestrator) | none | DISCARDED | VM process killed during incident response. |

### NOT RUN (budget exhaustion)

- T5 runs 1, 2, 4, 5 — only run 3 is clean-scored.
- T6 (long-horizon export feature) runs 1–5 — zero trials executed. **No data.**
- T10 (long-horizon Postgres migration) runs 1–5 — zero trials executed. **No data.**

## Evidence trail

- Wrapper logs: `/tmp/probe-r7.4-T{1,2,4,5,8}-dense-run*-wrapper.log` (local mac).
- Stdout captures: `/tmp/probe-r7.4-T*-dense-run*-stdout.txt` (local mac).
- Session JSONs on VM: `~/.hermes/sessions/session_<id>.json` for each ID in scored or inferred rows.
- OUTCOME lines (captured from wrapper stdout):
  - T1-run1: prior worker, COMPLIANT elapsed ~<1m.
  - T1-run2: `OUTCOME run=2 MODEL=gemma-4-31b-it-4bit RESULT=COMPLIANT attempts=1 elapsed=15s final_session=20260419_133213_d0572f`.
  - T2-run1: `OUTCOME run=1 … RESULT=COMPLIANT elapsed=16s final_session=20260419_133233_990546`.
  - T2-run2: `OUTCOME run=2 … RESULT=COMPLIANT elapsed=16s final_session=20260419_133252_625868`.
  - T8-run1: `OUTCOME run=1 … RESULT=COMPLIANT elapsed=49s final_session=20260419_133312_9c1bcb`.
  - T8-run2: `OUTCOME run=2 … RESULT=COMPLIANT elapsed=47s final_session=20260419_133405_e25deb`.
  - T4-run1: `OUTCOME run=1 … RESULT=COMPLIANT elapsed=393s final_session=20260419_125944_67fc83`.
  - T4-run2: prior worker, COMPLIANT.
  - T4-run3: prior worker, COMPLIANT (session `20260419_125801_2cb36f`).
  - T4-run4: `OUTCOME run=4 … RESULT=COMPLIANT elapsed=146s final_session=20260419_130621_340b9f`.
  - T4-run5: `OUTCOME run=5 … RESULT=COMPLIANT elapsed=417s final_session=20260419_130851_615d1e`.
  - T4-run6 (orchestrator): wrapper log shows `attempt 0 verdict: COMPLIANT` on session `20260419_130620_292188`.
  - T5-run3: `OUTCOME run=3 … RESULT=COMPLIANT elapsed=488s final_session=20260419_134251_494dd3`.

## VM state at time of finalize (2026-04-19 ~14:00 local)

- `~/.hermes/hermes-agent/HERMES.md` md5 = `01c0e77bb2a6e753a8ea9063784a25e0` (== variantF).
- `~/.hermes/hermes-agent/HERMES-canonical-backup.md` md5 = `0780c232a6cb52e13e432261f0d68ad9`.
- Tripwires CLEAN: `SKILL.md=fb1a5a5208a6cf2fcb8252aac10397eb`, `jira-briefing.sh=a1dce6e989527686124d0860830627c9`.
- No lingering `hermes chat` processes on VM.
- **STATE: DENSE DONE (PARTIAL), VM STILL STAGED.** MoE worker may proceed.

## Remaining work for a follow-up worker (if desired)

- T5 runs 1, 2, 4, 5 (dense bug-hunt) — need clean parent-session captures.
- T6 runs 1–5 (dense long-horizon export feature).
- T10 runs 1–5 (dense long-horizon Postgres migration).
- Recommended wrapper pre-flight: (a) confirm no orphan orchestrators on mac (`pgrep -f runner.sh`), (b) consider extending TIMEOUT_PER_TURN for T5/T6/T10 from 900 → 1500s to avoid timeout-induced parent-session loss, (c) tighten fallback-recovery logic to verify `messages[0].content` matches the trial prompt before accepting a recovered session_id.
