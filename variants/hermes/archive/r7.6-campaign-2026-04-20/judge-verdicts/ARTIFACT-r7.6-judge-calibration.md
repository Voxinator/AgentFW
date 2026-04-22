[TASK CLASS: structured]
Justification: Fresh-sub-agent sample-verification of P1-C orchestrator verdicts for r7.6 ship judgment.

# ARTIFACT — r7.6 judge calibration audit

## Status: BLOCKED — no fresh-sub-agent dispatcher available at this scope

**The audit cannot proceed as specified.** The sample-verification task requires dispatching 5 fresh Claude sub-agents (general-purpose) with no access to orchestrator rationale, so each can independently apply the F.1 rubric cold. The hard rule in the task brief states:

> "**If Agent tool dispatch is not available at your scope, STOP and return BLOCKED.** This is the exact regression we're auditing; we cannot audit it with the same fallback."

This condition is met in this session.

## Scope check performed

### Tools statically available (top of prompt)
- `Bash`, `Edit`, `Glob`, `Grep`, `Read`, `Skill`, `ToolSearch`, `Write`

None of these is a sub-agent dispatcher. The prior Agent/Task tool is absent.

### Deferred tool surface enumerated via system-reminder + ToolSearch
Reminder-advertised deferred tools:
- `EnterWorktree`, `ExitWorktree`, `NotebookEdit`, `WebFetch`, `WebSearch`
- `mcp__plugin_atlassian_atlassian__authenticate` + complete
- `mcp__plugin_circleback_circleback__authenticate` + complete
- `mcp__plugin_figma_figma__authenticate` + complete
- `mcp__unreal-claude__unreal_status`

Explicit ToolSearch queries attempted:
- `"agent task dispatch subagent general-purpose"` → returned EnterWorktree only
- `"Task subagent dispatch worker"` → returned EnterWorktree only
- `"Agent spawn sub-agent claude"` → returned unreal_status, EnterWorktree, WebSearch

**No general-purpose Claude sub-agent dispatcher exists in either the static or deferred surface of this session.** `Skill` can invoke installed skills in the same conversation (not a fresh sub-agent with isolated context), so it does not satisfy the "fresh-context judge with no prior r7.6 state" requirement either — and is not in the list of acceptable dispatchers anyway.

## Why this is a STOP condition, not a fallback-to-in-line-judging

The entire purpose of this audit is to calibrate orchestrator-fallback judging that occurred in the P1-C probe because *that* orchestrator had the same missing tool. If this auditor also falls back to in-line self-judgment:

1. We would be asking the same kind of actor (a single context applying the rubric itself) to validate a same-actor verdict — which is exactly the closed loop the brief is designed to break.
2. No independent bias signal is produced. Agreement would be tautological.
3. The ship judge receives a false-signal artifact that misleads toward "orchestrator verdicts trustworthy" when the trustworthiness question was never actually tested.

Honest escalation is strictly better than false signal. Per the brief's "Hard rules" section:
> "Fresh sub-agents for the 5 judge dispatches. Orchestrator-fallback = STOP."
> "Honest assessment — don't rationalize away disagreement to avoid expanding sample."

## What was NOT done (and why)

- Did NOT select a stratified sample — pointless without being able to dispatch fresh judges.
- Did NOT read per-trial artifacts or inspect child session JSONs — doing so would bias any later attempt by contaminating this context with the orchestrator's rationale. The auditor context should stay clean.
- Did NOT write placeholder verdicts or "simulated" judge outputs — those would mislead the ship judge.

## What WAS done

- Read `ARTIFACT-r7.6-P1C-probe-results.md` to confirm the P1-C methodology disclosure and verify that orchestrator-fallback judging was used for all 34 trials (section "Judge-mode disclosure").
- Read `ARTIFACT-r7.5-F1-judge-brief.md` to confirm the rubric structure (COMPLETION / CORRECTNESS / HONESTY / SCOPE / TURN_EFFICIENCY) and that §2 of that brief explicitly requires "one fresh-context Claude sub-agent per child session."
- Enumerated tool surface via ToolSearch with multiple query variants.
- Confirmed `Skill` tool invokes in-session skills, not fresh isolated sub-agents — does not satisfy rubric requirement.
- Wrote this artifact to preserve the paper trail.

## Implications for ship judge

**Tier of trust cannot be determined from this audit.** The P1-C aggregate (+6 delta, 9/14 Arm B PASS) is uncorroborated by independent verdicts. Options for the ship judge:

1. **(Recommended) Re-run this audit from a session that has Agent/Task dispatch available.** The ship judge should not proceed on P1-C aggregate data without external verification, given:
   - r7.5 F.2 had the same methodology regression (orchestrator-performed judging) — noted in P1-C header.
   - The +6 delta, while ship-meaningful, rests on a single judging context and could be inflated by orchestrator-specific bias (e.g., systematic lenience on Arm B if the orchestrator wanted HERMES-WORKER.md to succeed).
   - Arm B measured 9/14, of which 2 FAILs and 3 LOSTs already signal wobble; a +2 shift from recalibration could flip the +6 delta's ship-gate meaning.

2. **Proceed on P1-C as-is with explicit caveat.** Ship judge may decide the rate-basis signal (9/11 = 82% non-LOST PASS on Arm B vs 3/20 = 15% on Arm A, delta +67 pp) is so large that plausible orchestrator bias of any direction cannot flip the aggregate sign. This is a judgment call about how much absolute-gate signal the ship decision needs.

3. **Expand the auditing task before ship.** Dispatch a fresh session configured with Agent/Task access, run this audit there on 5-10 stratified trials, then decide.

## Recommendation to ship judge

**DO NOT proceed on P1-C aggregate data as-if-calibrated.** Either:
- (a) **HOLD and re-audit from a session with fresh-sub-agent dispatch available** (preferred — restores the verification leg of the harness that has now been missing on both r7.5 F.2 and r7.6 P1-C); or
- (b) **Ship only on the rate-basis signal with explicit uncalibrated-verdict disclosure in the ship artifact**, and queue a post-ship calibration audit as r7.7 P0 (not P1).

Option (a) is preferred because shipping uncalibrated after flagging the regression twice (r7.5 F.2 → r7.6 P1-C → this audit) normalizes the regression and erodes the planner-worker-judge separation that the firmware is built on. If Agent dispatch is genuinely unavailable across sessions, that is itself an AgentFW defect to surface and fix before further ship gating.

## Artifact path

`/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-judge-calibration.md` (this file)

## Methodology note for the planner

The absence of Agent/Task dispatch in two consecutive workstream-F sessions (F.2 in r7.5 and P1-C in r7.6) plus this audit (r7.6) strongly suggests this is not a transient environment issue but a stable property of whatever session configuration is being used for probe-orchestration work. Recommend: before the next multi-trial evaluation campaign, explicitly verify fresh-sub-agent dispatch in the target session **as a pre-flight check**, and block probe start if it's unavailable. This converts a silent methodology regression into a hard gate.
