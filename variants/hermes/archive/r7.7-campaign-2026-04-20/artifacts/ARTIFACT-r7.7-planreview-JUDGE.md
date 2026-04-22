---
type: plan-edit judge verdict
date: 2026-04-20
plan-under-review: PLAN-r7.7-path-A-child-structural-fixes.md
---
# Judge verdict — r7.7 plan edit pass

Judged from fresh context. Plan read end-to-end (838 lines). Synthesis used as oracle. Did not read the edit worker's diff report.

## Per-item verdicts

| Item | Verdict | Evidence (line range or quote) | Notes |
|------|---------|--------------------------------|-------|
| P0-1 | ACCEPT | `grep -rn '<raw-key>' ...` (operator knows the value) returned zero matches | Line 104 uses `<REDACTED>` placeholder correctly. |
| P0-2 | ACCEPT | L69-70: "`git log r7.5-hermes-prerelease..HEAD` is empty — HEAD commit IS the tag commit. The 'drift' is uncommitted working-tree state, not history." | Enumerates 1 uncommitted edit + 164 untracked. |
| P0-3 | ACCEPT | L83: "Source patch chains on VM (each with `.probe-d-orig` through `.probe-r7.6-orig` backups): `model_tools.py`, `run_agent.py`, `toolsets.py`. `delegate_worker_v2.py` is staged INTO … tools/ … no persistent backup chain." | Names the correct three files; clarifies delegate_worker_v2.py. |
| P0-4 | ACCEPT | L72: "Fix 3 + Fix 4 wrapper patches to `probe-variantI-wrapper.sh` / `probe-variantH-wrapper.sh` are IN the pre-release commit already (not drift)." | Wrappers explicitly removed from drift list. |
| P1-5 | ACCEPT | L175-178: `test -n "$OMLX_API_KEY" \|\| { echo "OMLX_API_KEY not set — confirm with operator before continuing"; exit 2; }`. Also §17 L808: "☐ Confirm operator has exported OMLX_API_KEY; do not proceed without it." | Matches synthesis prescription. |
| P1-6 | ACCEPT | L171-173: `test -x /Users/briantaylor/Projects/AgentFW/probe-preflight.sh \|\| { echo "preflight script missing — see ARTIFACT-r7.6-P1C-fix5-impl.md to reconstruct"; exit 2; }` | Pre-flight existence check present. |
| P1-7 | ACCEPT | §5.1 L207-215: declares alias, provides `ssh ubuntu-vm -- true` probe, halt-on-failure. Also in §17 L810. | Matches synthesis. |
| P1-8 | ACCEPT | L180-184: "do NOT hand-set AGENT_DISPATCH_AVAILABLE. Instead, verify by dispatching a trivial Agent sub-agent probe…" Also §17 L809. | Hand-export replaced by verification. |
| P1-9 | ACCEPT | §5.2 L217-224: "oMLX lacks a verified CLI restart recipe on this host… Autonomous mode: oMLX restart is a mandatory operator-interaction-required gate. Added to §13 decision points." Also §13 item 6 (L681). | Marked as mandatory operator-interaction gate, as prescribed (option b). |
| P1-10 | ACCEPT | §7.2 L340-350: "Do NOT anchor on line number… Locate with: `grep -n 'def run_conversation' ~/.hermes/hermes-agent/agent/run_agent.py`". Also §7.6 L455: "via the grep-anchor method in §7.2 (do NOT hard-code line numbers; B.0's ~9109 snapshot will rot…)". | No longer cites 9109 as the hook point; uses grep anchor. |
| P1-11 | ACCEPT | §7.4 L431-435: `WRITE_TOOL_NAMES = frozenset({'write_file', 'patch', 'execute_code', 'terminal', 'skill_manage', …})` with comment "verify skill_manage file-write semantics at S2 — drop if metadata-only." Prefix matcher preserved. | Matches synthesis five-name version with verify-at-S2 comment. |
| P1-12 | ACCEPT | §11 R4 L625-631: (1) `signal.signal(signal.SIGTERM, handler)` that saves session.messages then re-raises; (2) "Hard wall-clock cap on retries: 60 seconds per retry attempt, 120 seconds cumulative"; (3) try/except/finally for ordinary exceptions; (4) restore prior handler. | Matches synthesis exactly, including the 60s/120s caps. |
| P1-13 | ACCEPT | §7.7 L468-471 + §8 S6 row L491: "runtime-regex calibration gate (ship-blocking at S6): feed gate 10 synthetic + 10 real r7.6 session JSONs… Required thresholds: ≥9/10 precision… ≥8/10 recall". Explicitly labeled "ship-blocking" and S7 cannot start until passed. | Matches synthesis prescription; duplicated in sequencing matrix. |
| P1-14 | ACCEPT | §6.4 L298-315: `_resolve_parent_toolsets` with three-way fallback `enabled_toolsets → valid_tool_names → DEFAULT_TOOLSETS`; `_derive_restricted_child_toolset` built on it; explicit unit-test requirement at L315: "parent_agent with enabled_toolsets=None and valid_tool_names=None → _derive_restricted_child_toolset returns DEFAULT_TOOLSETS minus todo, NOT []". | Matches synthesis. |
| P1-15 | ACCEPT | §11 R7 L645-653: "Substrate migration (A1 pushes fabrication from `todo` to `terminal`)". Mitigations include pre-probe tripwire md5 baseline, mid-probe md5 check every 5 trials with halt-on-drift, post-probe attribution. | Matches synthesis. |
| P1-16 | ACCEPT | §1 L28: "A1 — Child toolset restriction. Strip `todo` from the default child toolset. A1 removes the **dominant** `todo`-as-write fabrication substrate observed on r7.6 T10 trials. Other fabrication routes (prose-only 'Created X' with no matching tool call at all; pseudo-tool-call emission in assistant content) remain — those are caught post-hoc by A2 but are not structurally prevented. A1 eliminates ONE substrate, not all fabrication." | Explicit acknowledgment of other fabrication routes. |
| P1-17 | ACCEPT | §9.7 L567: "Aggregate projection: **11-16/20**, centered around **13.5/20** (midpoint sum of per-task priors: T4=4.5 + T5=1.5 + T6=3.5 + T10=4.0). Under stated uniform-independent priors, **P(SHIP ≥15/20) ≈ 20-25%** — not negligible." | Matches synthesis: 13.5/20 center and P(SHIP) ≈ 20-25%. |
| P1-18 | ACCEPT | §9.6 L555-556: "HOLD-with-noise-note: Arm F = 6-8/20. Arm B=8 has 95% CI ~[4,13] at n=20; this band is indistinguishable from baseline at this sample size." "RETREAT: Arm F ≤ 5/20 AND per-task regression on T4 (scaffold-known-good 4/5+ in r7.6). Both conditions must hold." | Matches synthesis AND-clause + noise-band HOLD. |
| P1-19 | ACCEPT | §18 L824-832: three bullets (1) Arm G ablation separates A1 from A2 lift, (2) formal HOLD-CLOSE evidence justifies r7.8, (3) a2_gate_outcome is reusable infra. EV summary line at L832. Cross-reference from §9.7 L569: "See §18 for the EV argument supporting running Path A even under expected HOLD-CLOSE." | New §18 present with all three EV bullets as synthesized. |
| P1-20 | ACCEPT | §16 L788: "S8 probe matrix… 5-7h MoE trials… + 1h judges"; L794-795: "Sequential estimate: ~14-17h (without ablation), ~17-21h (with ablation). Parallelized estimate: ~11-14h (without ablation), ~14-17h (with ablation)." L797: reconciliation paragraph with §9.2's "12-15h". §9.2 L531 also reads "~12-15h" as the 4-arm 80-trial framing — no longer contradicted. | All numbers match synthesis prescription. |
| P1-21 | ACCEPT | §8.5 L502-510: new subsection. (1) main reads judge findings; (2) dispatches NEW worker, explicit "Do NOT reuse the S3/S4 worker context"; (3) "Max 2 judge iterations per fix. After 2 rejections… halt the sequencing matrix and escalate to operator"; (4) S7 blocks on both S5 and S6 accepting; (5) log as separate S-step row. | Exceeds synthesis requirement with useful additions (partial-accept blocking rule, PROGRESS.md log requirement). |
| P1-22 | ACCEPT | §12 L663: "Pseudo-tool-call sentinel leak… r7.6 Fix 2 patched the Gemma parser (relaxed prefix requirement) and reduced but did not eliminate the leak: 3/20 trials in r7.6 P1-C still emitted pseudo-tool-call sentinels… If r7.7 shows >2/20 pseudo-tool-call incidents, dispatch a follow-up F3A′ diag." L664: "Out-of-context child deployment (Mode 4)" with pwd+env-check suggestion for r7.8. L665: "Ambiguous-path SCOPE resolution (Mode 5)" with workaround + log file. | All three modes named + described. |
| P1-23 | ACCEPT | §14 L703: "variantG role: r7.5 turn-0 β-fuse toolset restriction — stages with `.probe-r7.5-orig` backup suffix and patches the child's turn-0 available toolset on top of variantF's β-fuse dispatch layer. Load-bearing in the pre-release arm stack (variantF→G→H→I). Stays staged in Arm B re-baseline and in all r7.7 Arms (G, H, F). Do not modify." | One-liner added to §14; clearer than simply dropping. |

## Overall

**23 of 23 ACCEPT, 0 PARTIAL, 0 REJECT.**

## Blocking issues (REJECTs)

None.

## Non-blocking issues (PARTIALs worth noting)

None. A few observations that are *not* PARTIALs but are worth flagging for awareness:

- **§9.2 Arms table uses Arm G / Arm H / Arm F labels** (L527-529). The rest of the plan is consistent with this, and §18 L828 correctly references "Arm G (A1-only)". No inconsistency introduced; flagging only because the labels differ from r7.6's Arm A/B convention — readers coming from r7.6 should map mentally.
- **P1-11 frozenset kept five names including `skill_manage`** with a verify-at-S2 comment. The synthesis allowed either the five-name version (with comment) or the four-name version; the plan picked option (a). Defensible; no rework needed.
- **P1-9 mitigation chose option (b)** (mandatory operator-interaction gate) rather than (a) (document CLI recipe). Synthesis allowed either; option (b) is the safer choice given no verified CLI recipe exists on this host. Defensible.

## New inconsistencies introduced (if any)

None detected on a close read. Specific cross-reference checks passed:

- §9.7 L569 "See §18 for the EV argument" — §18 exists at L824.
- §8 sequencing matrix (L483-496) internally consistent with §8.5 (L502-510).
- §16 S8 row (L788) says "5-7h"; parallelized rollup (L795) says 11-14h without ablation — arithmetic consistent.
- §5 L171-190 preflight steps numbered 1-8; §17 L806-820 checklist maps each step. Consistent.
- §6.4 A1 helper pseudocode (L300-315) is now self-consistent — `_derive_restricted_child_toolset` calls `_resolve_parent_toolsets`, which has the three-way fallback.
- §11 R7 mitigation (L649-652) references §14 md5 baselines; §14 L742-745 provides them.
- §12 pseudo-tool-call follow-up "dispatch F3A′" is a new name; it's not defined elsewhere but is clearly a forward-reference scope label, not a broken cross-reference.

## Recommendation

**SHIP.**

All 23 punch-list items are ACCEPT. The edit pass addressed the P0 framing/secrecy issues, the P1 correctness gates, the ship-gate math, the EV articulation, and the failure-mode catalog. No new internal inconsistencies detected. The plan is fresh-session-executable as written.

Caveats (non-blocking, for the main session planner when picking up the plan):
- The plan is now 838 lines. Fresh-session read time at S0 is ~45-60 min as §16 estimates.
- The §8.5 judge-rejection protocol adds a "max 2 iterations then halt+escalate" constraint that the planner must honor — this interacts with §13 operator-decision-points and should be flagged in the first operator check-in.
- P1-13's ship-blocking S6 calibration gate (≥9/10 precision, ≥8/10 recall on 20 JSONs) could plausibly block S7 on a first-pass probe. That's working-as-intended but worth surfacing to the operator in the S0 status read-out so expectations are set.

No re-dispatch to edit worker required. Plan is ready for operator review + session hand-off.
