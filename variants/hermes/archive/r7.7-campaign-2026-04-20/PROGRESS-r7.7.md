# PROGRESS — r7.7 Path A (child-structural fixes)

**Campaign:** Hermes variant r7.7 — A1 (child toolset restriction) + A2 (write-before-claim runtime gate).
**Started:** 2026-04-20.
**Operator:** Brian Taylor.
**Plan:** `PLAN-r7.7-path-A-child-structural-fixes.md` (838 lines, polished + judge-ACCEPTED).

---

## Operator decisions resolved

- **§13.1 Ablation:** ✅ Arm F + Arm G (full ablation). 2026-04-20.
- **§13.2 HERMES-variantF.md drift tag/notes:** pending (not blocking).
- **§13.3 8 IMPL-4 questions:** pending (not blocking r7.7).
- **§13.4 Ship-gate flex:** pending (can resolve at S10 with data in hand).
- **§13.5 Ship authorization:** procedural — operator gate at S10.
- **§13.6 oMLX restart in autonomous:** accepted — agent halts + escalates; operator restarts via Mac UI.

### In-flight scope amendments (post-S1/S2 findings)

- **A2 scope: NARROW (detect-only).** Per S2 findings: no retry, no correction-turn, no model re-inference. A2 just marks `a2_gate_outcome ∈ {CLEAN, FABRICATED}` on the session JSON. Reasons: (a) `_cleanup_task_resources` already ran by hook point at 9109 — retry would operate on stale state; (b) SIGTERM handling only works on main thread + non-CLI entrypoints have no handler at all + cross-child races; (c) retry is speculative lift on a 26B MoE; (d) ~2h faster probe wall-clock. Retry is deferred to r7.8 if narrow-A2 lift is insufficient.
- **A2 write-tool set:** `{write_file, patch, execute_code, terminal, skill_manage}` WITH **path-aware matching for `skill_manage`** — only matches claims whose path is under `~/.hermes/skills/<name>/`. Preserves the Hermes skills-system detection surface without false positives on unrelated skill_manage calls.
- **Plan §7 is frozen** for this campaign. Scope amendments live here + in the S2 research artifact + in the S4 implementation artifact. Post-campaign, plan §7 can be back-fixed.

---

## S-step state (§8 sequencing matrix)

| Step | Status | Owner | Artifact | Notes |
|------|--------|-------|----------|-------|
| S0   | completed (retry PASS) | main session → S0/S0-retry worker | `ARTIFACT-r7.7-S0-preflight.md` | 4/4 gates green; oMLX CLEAN; VM canonical |
| S1   | completed | S1 worker | `ARTIFACT-r7.7-A1-diag.md` | H-A1c CONFIRMED; patch sketch ready for S3 |
| S2   | completed | S2 worker | `ARTIFACT-r7.7-A2-hook-research.md` | Hook 9109; narrow-scope + path-aware skill_manage approved |
| S3   | completed | S3 worker | `ARTIFACT-r7.7-A1-impl.md` | delegate_worker_v2.py edited + variantJ-A1-stage.sh + 5/5 unit tests |
| S4   | completed | S4 worker | `ARTIFACT-r7.7-A2-impl.md` | narrow-scope gate module + stage script + 11/11 self-tests; adapted hook to `self._a2_gate_outcome` + `_save_session_log` |
| S5   | completed | S5 judge | `ARTIFACT-r7.7-A1-judge.md` | ACCEPT. Flag ON: child tools=[read_file,search_files] (todo absent). Flag OFF: todo present (baseline). VM canonical post-unstage. 3 non-blocking notes. |
| S6   | REJECT (iteration 1) | S6 judge | `ARTIFACT-r7.7-A2-judge.md` | Precision 7/7 PASS; recall 7/10 FAIL. Two root causes: (a) last-msg-role-tool bug; (b) todo-payload fabrication out-of-scope for Arm F. Stage script scp bug also flagged. |
| S4-redo | in_progress | S4-redo worker (dispatched) | — | Fix scp + FN(a); skip FN(b) (out-of-scope for Arm F) |
| S6-redo | completed | S6-redo judge | `ARTIFACT-r7.7-A2-judge-redo.md` | ACCEPT. Precision 10/10, Recall 10/10 on Arm-F-realistic corpus. Live MoE trial: a2_gate_outcome populated correctly on parent + 2 children (all CLEAN). VM canonical. |
| S7   | completed | S7 worker | `ARTIFACT-r7.7-S7-smoke.md` + new `probe-variantJ-wrapper.sh` | **GO.** T4 PASS (26s, child tools=[read_file,search_files]); T10 PASS — parent `a2_gate_outcome=FABRICATED` correctly caught over-claim; child clean; A1 stopped ~17 tripwire-pressure writes. VM canonical at exit. |
| S8 Arm F | **COMPLETE** | S8-F-B1/B2/B3/B4 workers | `ARTIFACT-r7.7-S8-F-B{1,2,3,4}-trials.md` + original-attempt trials | **20/20 trials: 18 CLEAN + 2 FABRICATED** (both on T10; T10-run3 and T10-run5). VM canonical across all batches. A2 actively catching fabrication in the campaign (validates gate). |
| S8 Arm F judges | **COMPLETE** | 20 fresh-LLM judges in 4 waves of 5 | `ARTIFACT-r7.7-judge-ArmF-T<n>-run<m>.md` × 20 | **Final: 7/20 PASS (35%)**. T4 3/5, T5 1/5, T6 **0/5**, T10 3/5. Dominant failures: Mode 2 thrash, Mode 3 channel-pollution, Mode 4 out-of-context. A2 gate's FABRICATED call on T10-run5 independently corroborated by judge; T10-run3 flagged as parent-side FP (child clean). |
| S8 Arm G | **COMPLETE** | S8-G-B1/B2/B3/B4 workers | `ARTIFACT-r7.7-S8-G-B{1,2,3,4}-trials.md` | 20/20 dispatch-compliant. Total wall-clock ~1.2h across 4 batches. |
| S8 Arm G judges | **COMPLETE** | 20 fresh-LLM judges in 4 waves | `ARTIFACT-r7.7-judge-ArmG-T<n>-run<m>.md` × 20 | **5/20 PASS (25%)**. T4: 5/5, T5: 0/5, T6: 0/5, T10: 0/5. |
| S9 Ship judge | **COMPLETE** | S9 fresh-context worker | `ARTIFACT-r7.7-S9-ship-judge.md` | **VERDICT: HOLD (noise-band)**. Arm F 7/20, Arm G 5/20. A1 alone is a no-op. A2+HWO contributes +2, almost entirely on T10. T4 inversion (Arm G beats Arm F). T6 unsolvable on this substrate. **Key new finding: ~2/3 of failures are GENERATION-LAYER (channel token leak, finish_reason=length, degenerate loops) — A1+A2 target the wrong substrate.** |
| S10 Operator decision | pending | operator | — | r7.7 final ship/scope decision; campaign-arc summary + r7.8 scope recommendations packaged. |
| S7   | blocked | — | — | Integration smoke test; blocked by S5+S6 |
| S8   | blocked | — | — | Probe matrix: Arm F 20 trials + Arm G 20 trials; blocked by S7 |
| S8.5 | blocked | — | — | Judge-rejection recovery (only if triggered by S5/S6) |
| S9   | blocked | — | — | Ship judge (fresh sub-agent applies pre-committed thresholds); blocked by S8 |
| S10  | blocked | — | — | Ship decision — operator gate |
| S11  | blocked | — | — | PROGRESS + morning summary |

---

## Context health checkpoints

| Timestamp | Steps completed | Self-assessment | Notes |
|-----------|-----------------|-----------------|-------|
| 2026-04-20 T_init | 0 (fresh after review) | OK | Review + polish consumed significant context; monitor after S0 |

**Re-assess after every 3 S-steps completed.** If DEGRADED → summarize + hand off to fresh session.

### Arm F verdict vs plan thresholds

- Plan §9.6 SHIP ≥15/20: **NOT MET** (7/20)
- Plan §9.6 HOLD-CLOSE 13-14/20: **NOT MET**
- Plan §9.6 HOLD 9-12/20: **NOT MET**
- Updated noise band (P1-18) 6-8/20 "indistinguishable from r7.6 Arm B baseline (8/20)": **HITS this band**
- RETREAT ≤5/20 + T4 regression: **NOT MET** (T4 actually improved slightly over Arm B; no regression)

**Arm F outcome: HOLD — indistinguishable from baseline at n=20.** A1+A2+HWO did not materially move worker-quality. A2 gate validated as mechanism (correctly caught T10-run5 fabrication) but fabrication is a small slice of the failure space; ~80% of FAILs are Mode 2/3/4 (thrash/channel/out-of-context) which the plan honestly said A1+A2 wouldn't address.

**Arm G is now load-bearing for r7.8 scope.** If Arm G ≈ Arm F (~7/20), A2+HWO added nothing; r7.8 should drop them and pursue deeper structural restrictions. If Arm G << Arm F, A2+HWO is the (modest) contributor and r7.8 polishes them.

### Arm F resumption plan (post-attempt-1 failure)

Attempt 1 of S8 Arm F failed at trial 3 — worker detached run-all as a background process with an unstage-watcher daemon; watcher fired unstage prematurely while trial 3 (T6-run1) was still mid-run on VM. **2 valid trials retained:** T4-run1 PASS (a2_gate=CLEAN), T5-run1 PASS (a2_gate=CLEAN). VM was restored to canonical post-cleanup.

Resumption design: **5-trial batched workers**, no detachment. Each batch worker stages the full stack (idempotent), runs 5 trials serially, unstages at end, returns session paths. Main session dispatches next batch on return. 4 batches to complete remaining 18 Arm F trials.

**OMLX_SWAP_MAX_GB calibrated from 5.5 → 30** per operator 2026-04-20. Old threshold was ~3× too aggressive; real degradation pathology is swap > 30 GB + oMLX process RAM > 100 GB. Memory note updated.

### Known small debts (post-campaign polish)

- **variantF-stage.sh now uploads A1-patched delegate_worker_v2.py.** Because S3 edited the Mac-side source. Gate is env-controlled so functional-correct for r7.7 arms, but breaks "variantF = r7.5 baseline md5" invariant. Matters only if operator wants byte-identical-to-r7.5 Arm B re-baseline (§9.2 "if needed"). Post-campaign fix: either keep two Mac-side variants of delegate_worker_v2.py (.r75 + .r77), or document the md5 drift as expected.
- **variantJ-A1-stage.sh `status` subcommand doesn't reliably report UNSTAGED after unstage** (backup file is byte-identical to current). Cosmetic; add `rm -f .probe-r7.7-orig` to unstage path.
- **Pre-existing "unhashable type: 'slice'" error in delegate_worker_v2** surfacing intermittently; predates r7.7 (observed 2026-04-19). Orthogonal; may affect probe trial success rate. Track separately.

---

## Pre-flight checklist (from §17)

- ☐ Plan + MORNING-SUMMARY read end-to-end (main session: DONE during review phase)
- ☐ probe-preflight.sh runs PASS (AGENT_DISPATCH_AVAILABLE=1, OMLX_SWAP_MAX_GB=5.5, OMLX_API_KEY set)
- ☐ File md5s match §14 baselines
- ☐ VM canonical state verified via ssh
- ☐ §13 decisions surfaced to operator (§13.1 RESOLVED; others acceptable at this stage)
- ☐ S1 + S2 dispatched in parallel (after S0 PASS)

---

## Known constraints carried forward

- **Operator-manual oMLX restart required** before each long probe run and whenever health-check reports DEGRADED. Agent halts + escalates; does not proceed.
- **Jira cron tripwire** weekday 8am in America/Los_Angeles. Check `date +%u +%H` before S8 starts; if <12h to next cron, halt S8 until after cron window.
- **Tripwire md5 baselines** (verify canonical at S0 and mid-probe every 5 trials per P1-15 / R7 substrate-migration risk):
  - `HERMES.md` = `0780c232a6cb52e13e432261f0d68ad9`
  - `SKILL.md` = `fb1a5a5208a6cf2fcb8252aac10397eb`
  - `jira-briefing.sh` = `a1dce6e989527686124d0860830627c9`
  - `useDashboard.ts` = `5503ee1c2ef7d635a020eea275e41239`
- **Hermes version lock:** v2026.4.8 / commit `86960cdb` / Python 3.11.15.
- **Model:** Gemma-4-26B-A4B-MLX-8bit (MoE). Dense + Qwen + 122B OUT OF SCOPE.
