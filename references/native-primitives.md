<!-- AgentFW v8 — Claude Code only. Source: github.com/Voxinator/AgentFW -->
# Native Primitives — Delegation Map + Plan-Critique Recipe

Claude Code 2.1 absorbed AgentFW's *mechanisms* as runtime primitives. This file names which primitive
replaces which firmware concept, and operationalizes the one mechanism with no native analog — the
Plan-Critique Gate. The throughline: **the firmware governs whether / when / how-well; the runtime executes how.**

## Delegation Map — primitive → firmware concept it replaces

| Claude Code 2.1 primitive | Firmware concept it executes | Division of labor |
|---|---|---|
| **Workflow tool** (`agent()`, `parallel()`, `pipeline()`, judge-panel, resume/journal) | Planner-Worker-Judge architecture + the Decompose→Parallelize→Verify→Iterate runtime | firmware decides whether/when to orchestrate; runtime executes the orchestration |
| **Agent subagents** (typed; final message returns to caller) | Worker/judge dispatch + structural OUTPUT-isolation | firmware decides who to dispatch and curates inputs; runtime isolates outputs |
| **Plan mode + Plan agent** | The plan-first gate (plan before dispatch) | firmware decides when a plan is required; runtime drafts/holds it |
| **Skills** (code-review, verify, security-review, deep-research) | Verification execution | firmware sets the recorded-artifact standard; runtime runs the check |
| **MEMORY** | Durable cross-session state (decisions, facts) | firmware decides what's worth persisting; runtime stores/retrieves it |
| **Task system + Cron / schedule / loop** | Long-horizon autonomy (multi-session continuity) | firmware decides cadence + stop conditions; runtime executes the schedule |
| **Permission modes + allow/deny/ask + hooks + worktrees** | Enforcement of the permission taxonomy | firmware supplies the taxonomy + novel-op judgment; runtime enforces deterministically |
| **Context compaction** | Window management | firmware triggers the health gate against drift; runtime compacts |

## Plan-Critique via Workflow judge-panel

Operationalizes the Core-Pattern gate in `core/harness-core.md`. Fires on structured/long-horizon plans only;
one-shot/trivial SKIP. Input-curated: the judge sees plan + requirements ONLY — never the planner's exploration
reasoning, never a sibling judge's verdict.

### (a) Check checklist — one-line pass test each
- **C0 Substrate-grounding** — every quantitative/existence claim probed against the live repo. *Pass:* each size/count/"exists" claim cites a command run against reality (`du -sh .git`, `git ls-tree`, `ls-files --others`), not an assertion.
- **C1 Independence** — tasks sit at real seams. *Pass:* no task secretly bundles two deliverables; each could be dispatched alone.
- **C2 Acceptance contract (prose-vs-mechanical, core)** — the discriminating lever is REACHABLE by `acceptance_command`, not just asserted in `expected_signal`. *Pass:* a wrong impl makes the command exit non-zero; the command exercises the layer the `risk` names.
- **C3 Dependencies + cross-task consistency** — deps stated/acyclic; shared derived values reconciled. *Pass:* a shared value is a shared imported artifact (identity asserted) or an in-task consistency assertion — UNLESS some task already exercises the seam.
- **C4 Risk/role (+ irreversible-op pre-mortem)** — risk/blast-radius/assumptions + role separation mapped; destructive plans inventory every ref/tag/worktree/untracked + post-op state. *Pass:* destructive steps verify-on-mirror-before-live and prove rollback *restorability*, not just bundle integrity.
- **C5 Approach-fit (EVERY task)** — acceptance encodes a discriminating fixture, not a noun-restatement. *Pass:* each task's acceptance asserts the *behavior* the requirement specifies; extra scrutiny where the task's own `risk` names an ambiguity.
- **Coverage/completeness** — every requirement component maps to a task+acceptance that mechanically verifies it. *Pass:* no requirement component is verified nowhere (no mocked-here-skipped-there hole).

Severity feeds the verdict: a C5 goal-vs-proof contradiction ⇒ **restart**; C2/C3 defects ⇒ **local revise**; a C5
"concern" STILL counts toward the overall verdict (a blockers-only consumer must not drop it). Self-consistency:
a check rated "clean" cannot coexist with a real defect mapped to it.

### (b) Acceptance Contract schema — `{criteria, acceptance_command, expected_signal, risk}`

```jsonc
{
  "criteria":          "what 'correct' means for this task, in behavioral terms",
  "acceptance_command": "a shell command RE-RUNNABLE at verification that exercises the discriminating lever",
  "expected_signal":   "the exact stdout/exit pattern that means PASS (anchored, not a substring a fail line also prints)",
  "risk":              "the production-environment failure this task must not ship (concurrency, trust-proxy, streaming, clock)"
}
```

**BAD — prose-only lever (a wrong impl still passes):**
```jsonc
{
  "criteria": "counter increments are atomic under concurrency",
  "acceptance_command": "python -c 'import counter'",          // smoke import — exercises nothing
  "expected_signal": "no error; atomicity verified",            // ATOMICITY LIVES ONLY IN PROSE
  "risk": "concurrency"                                          // never exercised ⇒ BLOCKER
}
```
Equally BAD: `npm test -- atomicity` when the discriminator sits behind `describe.skip(...)` — a green run proves
nothing because the assertion never executed. For a logic/concurrency/proxy risk this is a hard blocker.

**GOOD — runs a negative/regression assertion a wrong impl fails:**
```jsonc
{
  "criteria": "200 parallel increments yield a final count of exactly 200",
  "acceptance_command": "node test/atomicity.test.js  # fires 200 parallel incrs, asserts final===200; exits non-zero on drift",
  "expected_signal": "(✓|PASS).*atomic increment under 200-way concurrency",
  "risk": "concurrency — command spawns real parallel writers, not a serial loop"
}
```
**Signal-anchoring footguns (validated at shell-semantics depth):**
- `grep -q '<test name>'` alone is a **BUG** — it matches a jest `✕ <test name>` FAIL line as readily as `✓ <test name>`.
  Anchor to the pass marker: `grep -qE '(✓|PASS).*<test name>'`.
- `command | tee log` **discards the exit code** — you read `tee`'s success, not the test's. Capture
  `${PIPESTATUS[0]}` (or drop the pipe) so a failing test actually fails the gate.

### (c) Approach-fit — GOOD vs BAD
- **BAD (noun-restatement):** requirement says "GET /api/users honors a `limit` query param"; task acceptance is
  "endpoint returns users with a limit" — restates the requirement's nouns; a hardcoded `limit=100` passes.
- **GOOD (discriminating fixture):** acceptance asserts the *behavior* — "`GET /api/users?limit=10` resolves to
  10 rows, not the default 100" — a wrong default-honoring impl fails.

### (d) Coverage check
After per-task checks, build the requirement→task matrix: list every component of the requirement, map each to the
task + `acceptance_command` that mechanically verifies it. Flag any component verified NOWHERE. This catches the
mocked-in-T1, skipped-E2E-in-T6 hole where half a requirement (e.g. an S3 adapter never hit against real transport)
ships unverified — a whole-plan gap that no per-task check sees.

### (e) Convergence / stop
- **Hard 2-pass cap** (default structured). A single-judge BLOCKER triggers ONE confirming independent pass before
  any re-plan.
- **Escalate on capped-with-open-blocker:** cap reached + blocker open ≠ proceed → hand to the human via
  ExitPlanMode. Never auto-dispatch past an open blocker.
- **Do NOT trust a model-judged convergence signal.** Empirically, passes 2 and 3 each caught a real, distinct bug
  while the model's own `would_another_pass_help` returned false all three times — a fixed cap is better-calibrated
  than "loop until clean." Never a numeric score (invites plan-polishing). Beyond pass 2 clean = plan-polishing.

### (f) Recipe sketch — ILLUSTRATIVE, adapt to the real Workflow API, not a drop-in
```python
# ILLUSTRATIVE pseudocode — names/shape WILL differ from the live Workflow tool. Do not paste verbatim.
def plan_critique_gate(plan, requirements, tier="structured"):
    n_judges = 2 if tier in ("long-horizon", "prod", "infra", "bug") else 1
    for attempt in range(2):                      # HARD cap = 2 passes
        verdicts = parallel([                      # disjoint inputs per judge; NO sibling verdicts shared
            agent(role="plan-judge",
                  input={"plan": plan, "requirements": requirements},  # input-curated: no planner reasoning
                  rubric=CHECKLIST_C0_THROUGH_COVERAGE)
            for _ in range(n_judges)
        ])
        if n_judges == 1 and verdicts[0].has_blocker:             # single-judge blocker → confirm
            verdicts.append(agent(role="plan-judge", input={"plan": plan, "requirements": requirements},
                                  rubric=CHECKLIST_C0_THROUGH_COVERAGE))
        blockers = [b for v in verdicts for b in v.blockers]
        if not blockers:
            return "clean"                          # raises the floor — downstream judges still own correctness
        if any(b.check == "C5" and b.kind == "goal_vs_proof" for b in blockers):
            plan = replan(plan, blockers)           # contradiction ⇒ restart
        else:
            plan = revise(plan, blockers)           # C2/C3 ⇒ local revise
    return escalate_to_human(plan, open_blockers=blockers)   # capped-with-open-blocker → ExitPlanMode
```

**Honest limit:** this gate forces the discriminating command to EXIST and be RE-RUN; it cannot machine-check command
STRENGTH — that stays a judge question. It raises the floor on plan structure + verifiability; it does not verify
correctness. Downstream Tier-1 judges still own that.
