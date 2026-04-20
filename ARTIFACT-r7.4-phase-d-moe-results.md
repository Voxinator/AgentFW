[TASK CLASS: structured]
Justification: MoE leg data-collection artifact for r7.4 Phase D.

# ARTIFACT — r7.4 Phase D MoE-leg results

**Verdict:** COMPLETE. All 26 MoE trials ran under Variant F β-fuse staging. Zero SIGTERM-truncations. Zero LOST trials. Zero tripwire drift. VM restored to canonical state at finalize.

**MoE model:** `gemma-4-26b-a4b-it-mlx-8bit`.
**Wrapper:** `/Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh` with `TOOLSETS=delegation,todo,clarify,file_readonly`, `TIMEOUT_PER_TURN=900` (default), `MAX_RETRIES=3`.
**Start:** ~14:14 local, 2026-04-19. **End (artifact finalize + unstage):** ~14:57 local. **Wall clock:** ~43 min (well under 90-min budget).

## Summary

Aggregate counts (all scored against on-disk `messages[1].tool_calls[0]`):

- **MoE structured/LH first-attempt PASS:** **17 / 20 strict.** Zero INFERRED_PASS needed (no parent sessions were lost).
- **MoE v2-adoption rate on compliant structured/LH:** **20 / 20** (every structured/LH trial eventually emitted `delegate_worker_v2` with correct classification; 3 required one correction turn after an EMPTY first assistant reply).
- **MoE one-shot regression:** **6 / 6 PASS.** All one-shot trials emitted `delegate_worker_v2` with `classification=one-shot` on first attempt. **No MoE over-classification regression observed.**
- **LOST trials:** 0. **SIGTERM-truncations:** 0. MoE completed every trial well within the 900s timeout — biggest wall-clock was T5-run3 at 579s.

Strict first-attempt failures (3 total) were all the same pattern: the MoE model produced an **empty assistant reply** (no content, no tool calls) on attempt 0, then emitted `delegate_worker_v2` with correct classification + justification + goal after the NO_MARKER correction on attempt 1. This is the **MoE empty-first-turn** failure mode, distinct from the over-classification regression the probe was designed to measure.

## Per-trial table

All scored via `jq` over `messages[1].tool_calls[0]` on the parent session JSON.

| # | Task | Run | Session ID | OUTCOME | On-disk first_tool | Classification | Goal? | First-attempt PASS? | v2-adopted? | Elapsed |
|---|------|-----|------------|---------|---------------------|----------------|-------|---------------------|-------------|---------|
| 1 | T1 (one-shot: capital) | 1 | 20260419_141407_55f4c6 | COMPLIANT | delegate_worker_v2 | one-shot | no | ONE_SHOT_PASS | YES | 22s |
| 2 | T1 (one-shot) | 2 | 20260419_141434_c3b41e | COMPLIANT | delegate_worker_v2 | one-shot | no | ONE_SHOT_PASS | YES | 5s |
| 3 | T2 (one-shot: rename) | 1 | 20260419_141445_5aefd2 | COMPLIANT | delegate_worker_v2 | one-shot | no | ONE_SHOT_PASS | YES | 14s |
| 4 | T2 (one-shot) | 2 | 20260419_141504_5ece09 | COMPLIANT | delegate_worker_v2 | one-shot | no | ONE_SHOT_PASS | YES | 13s |
| 5 | T8 (one-shot: throwaway) | 1 | 20260419_141523_f12aab | COMPLIANT | delegate_worker_v2 | one-shot | no | ONE_SHOT_PASS | YES | 9s |
| 6 | T8 (one-shot) | 2 | 20260419_141537_42a0fa | COMPLIANT | delegate_worker_v2 | one-shot | no | ONE_SHOT_PASS | YES | 11s |
| 7 | T4 (structured: refactor) | 1 | 20260419_141602_513c2e | COMPLIANT (2 attempts) | null (empty msg[1]) → delegate_worker_v2 | (structured on msg[3]) | yes (msg[3]) | NOT first-attempt | YES (after correction) | 42s |
| 8 | T4 (structured) | 2 | 20260419_141658_621cfa | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 58s |
| 9 | T4 (structured) | 3 | 20260419_141800_0e7048 | COMPLIANT (2 attempts) | null (empty msg[1]) → delegate_worker_v2 | (structured on msg[3]) | yes (msg[3]) | NOT first-attempt | YES (after correction) | 57s |
| 10 | T4 (structured) | 4 | 20260419_141901_25928a | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 54s |
| 11 | T4 (structured) | 5 | 20260419_141959_d42b2f | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 32s |
| 12 | T5 (structured bug-hunt) | 1 | 20260419_142042_602b56 | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 142s |
| 13 | T5 (structured bug-hunt) | 2 | 20260419_142310_d31c0b | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 42s |
| 14 | T5 (structured bug-hunt) | 3 | 20260419_142356_da805a | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 579s |
| 15 | T5 (structured bug-hunt) | 4 | 20260419_143341_e23762 | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 74s |
| 16 | T5 (structured bug-hunt) | 5 | 20260419_143500_76bb41 | COMPLIANT | delegate_worker_v2 | structured | yes | FIRST_ATTEMPT_PASS | YES | 168s |
| 17 | T6 (long-horizon export) | 1 | 20260419_143802_e62496 | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 263s |
| 18 | T6 (long-horizon export) | 2 | 20260419_144232_b82e6a | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 68s |
| 19 | T6 (long-horizon export) | 3 | 20260419_144345_800c87 | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 89s |
| 20 | T6 (long-horizon export) | 4 | 20260419_144523_f25a5d | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 111s |
| 21 | T6 (long-horizon export) | 5 | 20260419_144719_99069f | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 23s |
| 22 | T10 (LH postgres migration) | 1 | 20260419_144755_fc072b | COMPLIANT (2 attempts) | null (empty msg[1]) → delegate_worker_v2 | (long-horizon on msg[3]) | yes (msg[3]) | NOT first-attempt | YES (after correction) | 101s |
| 23 | T10 (LH postgres migration) | 2 | 20260419_144942_d14f80 | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 50s |
| 24 | T10 (LH postgres migration) | 3 | 20260419_145041_9c2267 | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 45s |
| 25 | T10 (LH postgres migration) | 4 | 20260419_145133_09349a | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 87s |
| 26 | T10 (LH postgres migration) | 5 | 20260419_145305_5f3115 | COMPLIANT | delegate_worker_v2 | long-horizon | yes | FIRST_ATTEMPT_PASS | YES | 32s |

## LOST trials + inferred-PASS details

**None.** MoE had no SIGTERM-truncations and no parent-session losses across all 26 trials. The fail-fast mitigation plan was never triggered. Dense-leg hazard (T5/T6/T10 timing out and losing parents) did not recur on MoE — all long tasks finished well under 900s (max observed: T5-run3 at 579s).

## Per-task first-attempt-PASS breakdown

- **T4 (multi-file refactor, structured):** 3 / 5 strict (runs 2, 4, 5). Runs 1 and 3 produced empty first-turn, then recovered after NO_MARKER correction. 5 / 5 v2-adopted.
- **T5 (bug-hunt, structured):** 5 / 5 strict. Every run emitted `delegate_worker_v2 / structured / goal` on first attempt. Notable: this is the task that hit dense hardest (dense lost runs 1/2/4 to SIGTERM) — MoE ran it cleanly with max elapsed 579s.
- **T6 (long-horizon export):** 5 / 5 strict. Every run: `delegate_worker_v2 / long-horizon / goal` on first attempt.
- **T10 (LH postgres migration):** 4 / 5 strict (runs 2, 3, 4, 5). Run 1 produced empty first-turn → NO_MARKER → recovered on attempt 1.

## Empty-first-turn failure mode (MoE-specific)

3 of 20 structured/LH trials (T4-run1, T4-run3, T10-run1) exhibited the same pattern on on-disk inspection:

- `messages[0]` — user prompt verbatim.
- `messages[1]` — assistant, empty content string, no `tool_calls` array.
- `messages[2]` — user (wrapper's VIOLATION:NO_MARKER correction).
- `messages[3]` — assistant, `tool_calls[0].function.name == "delegate_worker_v2"`, with correct classification + goal.

This is a distinct failure mode from the over-classification regression that r7.3 Phase B measured on MoE. It is **not** a misclassification — when the model does emit a tool call, it chooses correctly (0 wrong classifications across 23 trials that reached a classification). It is a **production failure** (empty response), not a **routing failure** (wrong class / wrong tool).

Under the wrapper's correction contract the trials are fully recovered and v2-adopted, so downstream orchestration behavior would be identical. For strict first-attempt scoring, these count as MISS (3/20 = 15% miss rate, 85% strict PASS).

## Tripwire log

| Time (local) | SKILL.md | jira-briefing.sh | HERMES.md | Notes |
|--------------|----------|-------------------|-----------|-------|
| ~14:12 (pre-run) | fb1a5a52… | a1dce6e9… | 01c0e77b… (variantF) | CLEAN (VM staged) |
| ~14:15 (post one-shot leg) | fb1a5a52… | a1dce6e9… | (not re-checked) | CLEAN |
| ~14:21 (post T4 leg) | fb1a5a52… | a1dce6e9… | (not re-checked) | CLEAN |
| ~14:38 (post T5 leg) | fb1a5a52… | a1dce6e9… | (not re-checked) | CLEAN |
| ~14:48 (post T6 leg) | fb1a5a52… | a1dce6e9… | (not re-checked) | CLEAN |
| ~14:55 (post T10 leg, pre-unstage) | fb1a5a52… | a1dce6e9… | 01c0e77b… (variantF still) | CLEAN |
| ~14:57 (post-unstage finalize) | fb1a5a52… | a1dce6e9… | **0780c232… (canonical)** | CANONICAL |

No drift at any checkpoint.

## VM final state (post-unstage, 2026-04-19 ~14:57 local)

Verified via `md5sum` on the VM after running `probe-variantF-stage.sh unstage`:

| File | md5 | Canonical baseline | Match? |
|------|-----|--------------------|--------|
| `~/.hermes/hermes-agent/HERMES.md` | `0780c232a6cb52e13e432261f0d68ad9` | `0780c232a6cb52e13e432261f0d68ad9` | ✓ |
| `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` | `fb1a5a5208a6cf2fcb8252aac10397eb` | `fb1a5a5208a6cf2fcb8252aac10397eb` | ✓ |
| `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` | `a1dce6e989527686124d0860830627c9` | `a1dce6e989527686124d0860830627c9` | ✓ |

Unstage also restored `toolsets.py`, `model_tools.py`, `run_agent.py` from `.probe-r7.4-orig` backups and moved `delegate_worker_v2.py` to `/tmp/delegate_worker_v2.py.probe-r7.4-removed`. Stage script verified "no stray delegate_worker_v2 references in patched files."

No lingering `hermes chat` processes on VM (verified via `ps -ef | grep hermes`). No lingering wrapper processes on Mac.

**STATE: VM CANONICAL. Monday 8am Jira cron will run against canonical HERMES.md and canonical jira-daily-briefing skill. No probe residue.**

## Cross-leg comparison (MoE vs dense)

| Metric | Dense (clean-scored) | MoE |
|--------|----------------------|-----|
| One-shot first-attempt PASS | 6 / 6 | 6 / 6 |
| T4 structured first-attempt PASS | 5 / 5 (+1 orchestrator-extra) | 3 / 5 |
| T5 bug-hunt first-attempt PASS | 1 / 1 (4 LOST to SIGTERM, 2 inferred-PASS from child) | 5 / 5 |
| T6 long-horizon first-attempt PASS | NOT RUN | 5 / 5 |
| T10 LH migration first-attempt PASS | NOT RUN | 4 / 5 |
| v2-adoption on compliant | 100% | 100% |
| Over-classification regression on one-shot | 0 | 0 |
| Failure mode observed | SIGTERM-truncation on long tasks | Empty first-turn (3/20 structured/LH trials) |

MoE’s runtime characteristics are dramatically more favorable for this probe: the longest trial (T5-run3) finished in 579s, and no trial approached the 900s timeout. Dense lost 4+ structured trials to SIGTERM. MoE’s only deviation is an intermittent empty-first-turn pattern (15% on structured/LH) that is fully recovered by a single wrapper correction, with correct classification on the recovery attempt every time.

## Evidence trail

- Wrapper logs: `/tmp/probe-r7.4-T{1,2,4,5,6,8,10}-moe-run*-wrapper.log` on local mac.
- Stdout captures: `/tmp/probe-r7.4-T*-moe-run*-stdout.txt` on local mac.
- Session JSONs on VM: `~/.hermes/sessions/session_<id>.json` for each ID in the per-trial table above.
- All OUTCOME lines captured and reflected in the per-trial table (COMPLIANT column + attempts count).
- The 3 multi-attempt trials' raw message sequences were inspected via `jq "[.messages[] | {role, first_tool, content_prefix}]"` to confirm the empty-first-turn pattern (verified for T4-run1; T4-run3 and T10-run1 inferred from identical OUTCOME chain `A0:VIOLATION:NO_MARKER | A1_correct:rc=0 | A1:COMPLIANT` and on-disk `msg1_tool=null, msg1_content_head="(empty)"` check on T10-run1).

## Scope adherence

- MoE leg ONLY ran. Dense artifact untouched.
- T9 (Jira cron) BANNED and never executed.
- No tripwire drift; no stop needed.
- Fail-fast kill contingency never triggered (no SIGTERM loops observed).
- No wrapper patches attempted; the wrapper was used as-is.
- VM restored to canonical state; verified via md5 on all three canonical paths.
