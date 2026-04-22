---
type: plan-review edit-diff
date: 2026-04-20
plan-edited: PLAN-r7.7-path-A-child-structural-fixes.md
punch-list: ARTIFACT-r7.7-planreview-SYNTHESIS.md
scope: P0-2 through P1-23 (22 items). P0-1 already done in main session; P2 skipped per scope.
---

# r7.7 plan-review edit diff

## Per-item status table

| Item | Status | Section(s) touched | Summary of edit |
|------|--------|---------------------|-----------------|
| P0-2 | APPLIED | §3 (Repo + pre-release status) | Rewrote "main drifted" framing: HEAD == tag commit; drift is uncommitted working-tree (1 edit + 164 untracked), not history. |
| P0-3 | APPLIED | §3 (VM state) | Corrected backup-chain file list to `model_tools.py`, `run_agent.py`, `toolsets.py`; noted `delegate_worker_v2.py` is staged-in/unstaged-out with no persistent chain. |
| P0-4 | APPLIED | §3 (Repo + pre-release status) | Moved `probe-variantH-wrapper.sh` / `probe-variantI-wrapper.sh` out of drift list; stated Fix 3+4 patches are IN the pre-release commit. |
| P1-5 | APPLIED | §5 (pre-flight), §17 checklist | Replaced no-op `export OMLX_API_KEY="$OMLX_API_KEY"` with `test -n "$OMLX_API_KEY"` halt-on-empty check; added §17 checklist item confirming operator exported it. |
| P1-6 | APPLIED | §5 (pre-flight) | Added preflight-script existence check (`test -x probe-preflight.sh ...`) with pointer to fix5-impl artifact. |
| P1-7 | APPLIED | new §5.1, §17 checklist | Declared ssh-alias policy; added `ssh ubuntu-vm -- true` verification in preflight and in §17. |
| P1-8 | APPLIED | §5 (pre-flight), §17 checklist | Removed hand-export of `AGENT_DISPATCH_AVAILABLE=1`; replaced with "verify by trivial Agent sub-agent probe" directive; updated §17 accordingly. |
| P1-9 | APPLIED | new §5.2, §13 (decision points) | Declared oMLX restart as mandatory-operator-interaction gate in autonomous mode (no verified CLI recipe); added decision point #6; linked from R5 mitigation. |
| P1-10 | APPLIED | §7.2, §7.6 | Replaced `run_agent.py:~9109` line-number anchor with grep-based anchor (`grep -n 'def run_conversation'` then find first `_persist_session` call); added halt-escalate on zero/multiple matches. Updated §7.6 step 1 to point at §7.2 method. |
| P1-11 | APPLIED | §7.4 | Trimmed `WRITE_TOOL_NAMES` frozenset to `{write_file, patch, execute_code, terminal, skill_manage}`; added skill_manage verify-at-S2 comment; kept prefix matcher with forward-compat justification. |
| P1-12 | APPLIED | §11 R4 | Replaced "try/except/finally" hand-wave with concrete 4-part mitigation: SIGTERM handler that persists messages, 60s/120s wall-clock caps via signal.alarm/watchdog, try/except for Python exceptions, handler restoration in `finally`. Documented A2 as best-effort with bounded exposure window. |
| P1-13 | APPLIED | §8 S6 row, §7.7 | Added runtime-regex calibration gate: 10 synthetic + 10 real r7.6 sessions across FABRICATED/honest-blocked/normal-PASS; ≥9/10 precision AND ≥8/10 recall required; S7 blocked until gate passes; iterations logged to `ARTIFACT-r7.7-A2-runtime-calibration.md`. Marked ship-blocking in both S6 row and §7.7. |
| P1-14 | APPLIED | §6.4 | Rewrote helper pseudocode: explicit `_resolve_parent_toolsets` mirroring the three-way fallback (enabled_toolsets → valid_tool_names → DEFAULT_TOOLSETS); `_derive_restricted_child_toolset` returns resolved-minus-todo. Added required unit-test assertion for `enabled_toolsets=None` → default-minus-todo (not `[]`). |
| P1-15 | APPLIED | §11 new R7 | Added R7 substrate-migration risk (A1 pushing fabrication energy to `terminal`); mitigation = pre-probe tripwire md5 baseline, mid-probe md5 check every 5 trials, post-probe attribution check. |
| P1-16 | APPLIED | §1 TL;DR | Rewrote A1 bullet: A1 removes the *dominant* todo-substrate, not all fabrication; prose-only and pseudo-tool-call paths remain (caught post-hoc by A2, not structurally prevented). |
| P1-17 | APPLIED | §9.7 | Changed "centered around 13/20" to "centered around 13.5/20; P(SHIP ≥15/20) ≈ 20-25% under stated priors"; showed the midpoint math (4.5+1.5+3.5+4.0). |
| P1-18 | APPLIED | §9.6 | Split RETREAT band: HOLD-with-noise-note at 6-8/20 (indistinguishable at n=20 per Arm B CI); RETREAT requires ≤5/20 AND T4 per-task regression (both conditions). |
| P1-19 | APPLIED | new §18 | Added "Why run this even if HOLD-CLOSE expected" section with three EV bullets: Arm G ablation disambiguation, HOLD-CLOSE evidence as r7.8 justification, `a2_gate_outcome` as reusable infra. EV summary closes positive. §9.7 cross-references §18. |
| P1-20 | APPLIED | §16 | Updated S8 row to 5-7h with oMLX restart overhead; updated sequential estimate to 14-17h (no ablation) / 17-21h (with); parallelized to 11-14h / 14-17h; reconciled with §9.2's 12-15h framing explicitly. |
| P1-21 | APPLIED | new §8.5 | Added judge-rejection protocol: main session reads findings; dispatch NEW worker (don't reuse S3/S4 context); max 2 iterations per fix then halt+escalate; S7 blocks on both S5/S6 accepting; log each rejection as separate PROGRESS.md row. |
| P1-22 | APPLIED | §12 | Updated pseudo-tool-call entry: Fix 2 reduced but did not eliminate (3/20 rate); trigger F3A' follow-up if >2/20 in r7.7. Added new entries for Mode 4 (out-of-context child deployment, wrong cwd/workspace) and Mode 5 (ambiguous-path SCOPE resolution). |
| P1-23 | APPLIED | §14 (files NOT to modify) | Added variantG one-liner describing its role: r7.5 turn-0 β-fuse toolset restriction with `.probe-r7.5-orig` suffix; load-bearing in variantF→G→H→I stack; stays staged across r7.7 arms. |
| P0-1 | SKIPPED (pre-authorized exclusion) | — | Already handled in main session per punch-list; lines 104 and 562 remain as-is (already `<REDACTED>`). |

## Pass-by-pass log

- Pass 1 (§3 rewrite, P0-2/3/4) — done.
- Pass 2 (§5 pre-flight + §7.4 write-tool list, P1-5 through P1-11) — done. Split §5 into numbered steps 1-8 plus subsections §5.1 (ssh alias) and §5.2 (oMLX restart policy).
- Pass 3 (§7 A2 safety, §6.4 helper, §11 R4, P1-12/13/14) — done. Note: P1-13 required edits in two places (S6 row in §8 AND §7.7 verification) because calibration gate is both a sequencing-matrix gate and a verification step; both edited consistently.
- Pass 4 (§1 TL;DR, §9.6/9.7, §11 R7, new §18, P1-15/16/17/18/19) — done.
- Pass 5 (new §8.5, §12 modes, §16 timeline, P1-20/21/22) — done.
- Pass 6 (§9.2 variantG clarification, P1-23) — done. Added to §14 (files NOT to modify) per operator instruction to describe rather than drop.
- Pass 7 (sweep check) — done. Found and fixed four internal inconsistencies (see below).

## Sweep-pass findings + follow-up edits

Internal inconsistencies created by the earlier passes, resolved in Pass 7:

1. **§17 starting checklist** still told the agent to `Run probe-preflight.sh (AGENT_DISPATCH_AVAILABLE=1, OMLX_SWAP_MAX_GB=5.5)` — directly contradicting the new §5 step 3 "do NOT hand-set AGENT_DISPATCH_AVAILABLE." Rewrote the checklist to match §5's ordering (OMLX_API_KEY check, Agent-dispatch trivial-probe, ssh alias, preflight, md5s) and to reference §8.5 judge-rejection protocol. Also bumped "5 pending decision points" to "6" to match the new §13 item.
2. **§7.6 step 1** still said "at line ~9109" — directly contradicting the new §7.2 grep-anchor directive. Rewrote to point back to §7.2 and state explicitly "do NOT hard-code line numbers."
3. **§13 operator decision points** — the new §5.2 policy cites "Added to §13 decision points" but the item wasn't actually added. Added decision point #6 (oMLX restart in autonomous mode) to close the loop.
4. **§11 R5 mitigation** — referenced "operator-restart + resume" without linking to the new §5.2 policy. Added the cross-reference so the risk mitigation and the operational policy are consistent.

## Ambiguities resolved with a judgment call

1. **P1-11 skill_manage retention.** Synthesis said "verify skill_manage file-write semantics at S2; drop if metadata-only." I kept `skill_manage` in the frozenset with the "verify at S2, drop if metadata-only" comment rather than pre-removing it — reasoning: leaving it in is conservative (avoids A2 false-negatives if skill_manage does write); the S2 worker can drop it cleanly later. Flagging as ambiguity because a reader could argue for pre-removal.
2. **P1-16 A1 bullet scope.** Synthesis fix text mentioned "pseudo-tool-call emission" as a remaining fabrication path. I included it verbatim. This may create a forward-reference loop with §12's Mode 3 entry — reader may want me to cross-link. Did not add a link; §12 handles the detail already and an inline link would bloat §1.
3. **P1-19 EV percentages.** Synthesis fix text said "P(SHIP) ≈ 25% × (ship benefit) + 75% × (campaign-load-bearing negative)." I split the 75% into 50% HOLD-CLOSE + 25% HOLD/RETREAT to match the probability shape implied by §9.7's 20-25% SHIP estimate, since lumping HOLD-CLOSE with HOLD/RETREAT undersells the scope-shaping value. Judgment call — could be reverted to the original 25/75 split if operator prefers the simpler framing.
4. **P1-22 Mode 3/4/5 framing.** Synthesis told me to "update §12 pseudo-tool-call entry" and "add §12 entries for out-of-context and SCOPE-resolution." I numbered them Mode 4 and Mode 5 (since §4 already has Modes 1 and 2, and §12 already lists pseudo-tool-call as an implicit Mode 3). Added explicit "Mode 4" / "Mode 5" labels inline. If operator wants these un-numbered or re-numbered, trivial fix.
5. **P1-23 variantG placement.** Synthesis gave a choice ("drop from §9.2 or add §14 one-liner"). Per the instruction that followed ("add the description rather than drop"), placed the description as a bullet under §14's "Files NOT to modify" list — the most relevant spot. Could alternatively live in §2 campaign arc or §9.2 arm-table footnote; I picked the file-map location because that's where fresh agents hunt for variant-suffix meaning.

## P2 items noticed and correctly skipped

Items I would have wanted to apply but held back per scope:

- **P2a** §8 S7/S8 "main session" vs "main session dispatches worker" — normalization pass needed; noticed but skipped.
- **P2b** §9.5 explicit statement that main-dispatches-judges IS role-separated (not a fallback) — could strengthen by one sentence; skipped.
- **P2c** §6.4/§7.6 A1-edits-Mac-side vs A2-edits-VM-side asymmetry — should be stated explicitly once; skipped.
- **P2d** §17 autonomous-mode defaults for the 6 decision points (which I bumped from 5) — would be useful; skipped.
- **P2e** §5 VM pre-stage order verification at S0 — skipped.
- **P2f** Mac swap check (`vm_stat`) in §5 — skipped.
- **P2g** §6.3 research worker — specify `ssh ubuntu-vm -- rg` OR scp+local-grep — skipped.
- **P2h** §5 reading-docs sequential-vs-parallel budget — skipped.
- **P2i** `/tmp/probe-r7.6-P1C-logs/judge-trial.py` md5 labeled ephemeral — already partially addressed in P0-2 rewrite ("ephemeral /tmp; recoverable") but the explicit md5 line in §14 still lists it; skipped the latter refinement.
- **P2j** `md5` vs `md5sum` ambiguity — I did add `md5 -q` in the §5 command (P1-5/6 side-effect) but §14's md5 baseline header line doesn't specify; skipped.
- **P2k** Arm B "≤2 weeks stale" trigger clarification — skipped.
- **P2l** Jira cron `date +%u` check — skipped.
- **P2m** §14 VM md5s "expected-if-idle" framing — skipped.
- **P2n** Dead-zone ladder at 14/20 — the new §9.6 HOLD/HOLD-with-noise/RETREAT bands get close but don't explicitly resolve 14/20 (which is between HOLD-with-noise 6-8 and HOLD-CLOSE 13-14); P2 polish would nest it explicitly.
- **P2o** A2 bare-path FN "path-is-ready" regex branch — mentioned FN case in §7.3 but didn't add the branch.
- **P2p** A1 doesn't cover prose-only fabrication — addressed in the P1-16 TL;DR rewrite, but §6.1 could also mention; skipped the second-spot edit.
- **P2q** Calibration-carry-forward explicit trigger — skipped.
- **P2r** Untracked count 164 vs "~50+" framing — §3 now says 164 explicitly (from P0-2); no further framing work needed.

## Constraints honored

- No commits, no stage/unstage, no VM mutations. Only plan document edited.
- Other artifacts NOT touched (e.g., ARTIFACT-r7.7-planreview-* artifacts not retroactively updated even where a P1 fix implies they're now slightly stale).
- Task class header at lines 1-2 preserved verbatim.
- No sections renumbered; added §5.1, §5.2, §8.5, §18 (per P1-7, P1-9, P1-21, P1-19).
- P0-1 skipped as instructed (already redacted in main session).
- All P2 items skipped as instructed.

## Summary

All 22 authorized items (P0-2 through P1-23) applied. Sweep pass caught and fixed four cross-section inconsistencies introduced by earlier passes. Five judgment-call ambiguities logged above; none material enough to halt. Plan file ends at ~835 lines (up from 720) — growth concentrated in new §5.1/5.2, §8.5, §18, and the §7/§11 mitigation expansions.
