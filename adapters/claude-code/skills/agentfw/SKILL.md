---
name: agentfw
description: AgentFW r9 operational playbook for Claude Code. Use for multi-component or multi-file work, integration seams, production/security/infra changes, bug fixes, autonomous or long-running tasks — anything deriving to assurance A2 or above. Supplies role separation, acceptance contracts, the plan-critique gate, verification standards, and recovery policy.
---

# AgentFW r9 — Operational Playbook (Claude Code)

You already derived an assurance level from the bootloader kernel and emitted
`[ASSURANCE: Ax — <justification>]`. This skill is the full playbook for A2+ work. The neutral
policy it compiles from is installed alongside this file under `./policy/` (the installer copies
the repo's `policy/` directory to `skills/agentfw/policy/`, so these references resolve without
the repo checkout).

## 1. Assurance derivation (full table)

Three questions — Q1 blast radius & reversibility; Q2 defect-escape probability; Q3 autonomy &
irreversibility — map to a level. Full model: `./policy/assurance-model.md`.

| Level | Typical | Controls |
|---|---|---|
| A0 | lookup / explanation / tiny reversible edit | direct execution; producer check |
| A1 | bounded single-seam implementation | lightweight plan; producer tests (machine-checked) |
| A2 | multi-component / integration seams | decompose; independent verification at seams; Layer-1 plan validation; Layer-2 critique if ambiguity/shared values |
| A3 | production bug, security, infra, multi-file autonomous | independent workers + independent verifier; full acceptance contracts; both plan-critique layers; checkpoints |
| A4 | irreversible / destructive / critical autonomous | A3 + adversarial verification + explicit human authorization + rollback proof (restorability, not just backup integrity) |

Escalators (any one bumps to at least A3): production/live infra; security-sensitive;
destructive/history-rewriting; autonomous multi-file. Verification tiers: **producer** always;
**independent** at A2 seams and all A3+; **adversarial** at A4 and for security/destructive work
regardless of level.

## 2. Role separation → native primitives

One context that plans, implements, and verifies checks for what it *intended*, not what
*happened*. Claude Code enforces output isolation structurally (a subagent's final message returns
to the caller, not the user) — drive it; don't re-describe it.

| Role | Native primitive |
|---|---|
| Planner / dispatcher | main session (or Plan mode + Plan agent). Never writes A2+ implementation inline. |
| Worker | Agent subagent — the installed `agentfw-implementer` agent, or a Workflow `agent()` step. One task per dispatch, contract copied verbatim into the prompt. |
| Judge of record | a *separate* subagent — the installed `agentfw-verifier` agent (or a Workflow judge step), input-curated. |
| Plan critic | the installed `agentfw-plan-critic` agent (Layer 2 of the plan-critique gate). |
| Parallel fan-out | multiple Agent calls in one message, or `parallel()`. Use `isolation: "worktree"` when parallel edits collide on the same files. |

**Judge input-curation (no native analog — you supply it):** the runtime isolates a subagent's
*output* but does not stop you contaminating a judge's *input*. A judge receives ONLY requirements
+ current state + acceptance criteria/contracts. Never the producer's plan, reasoning, or
self-assessment. On judge failure: findings → planner → a *new* worker, not the stale one.

## 3. Acceptance Contract v2 + plan blocks

Every A2+ task carries a contract (full spec: `./policy/acceptance-contract.md`):
`requirement_ids[]`, `criteria`, `acceptance_command`, `environment`, `expected_signal` (anchored —
must not also match a fail line), `negative_cases[]` (REQUIRED whenever `risk` is present), `risk`,
`evidence` (freshness: produced_after_change), `rerunnable`, `constraints`. Tier-1 lever = at least
one negative/regression assertion the command actually RUNS — a bare smoke import is not Tier-1.
Non-shell work (docs/research/design): a named mechanical check (grep/link-check/renderer) plus a
designated independent reviewer; prose-only acceptance is never Tier-1.

Plans embed one machine-readable block, fenced as ` ```json agentfw-plan ` :

```
{ "version": "1", "assurance": "A0|A1|A2|A3|A4",
  "requirements": [{"id": "R1", "text": "..."}],
  "tasks": [{ "id": "T1", "title": "...", "deps": [],
              "contract": { "requirement_ids": ["R1"], "criteria": "...",
                            "acceptance_command": "...", "expected_signal": "...",
                            "risk": "...", "negative_cases": ["..."], "rerunnable": true }}]}
```

**Layer 1 (deterministic — run it, always):** `python3 tools/validate-plan <plan.md>` from the
AgentFW repo BEFORE the first worker dispatch. It mechanically checks: block parses; assurance
valid; every requirement covered by some task; every contract non-empty; deps acyclic; risk ⇒
negative_cases; A3/A4 ⇒ negative_cases everywhere. Exit 0 + PASS or a named defect.

**Layer 2 (semantic judge — A2 with ambiguity/shared values, all A3+):** dispatch
`agentfw-plan-critic` with the plan + requirements ONLY. It runs the C0–C5 rubric
(`./policy/plan-critique.md`): C0 substrate-grounding, C1 independence, C2 prose-vs-mechanical
reachability (core check), C3 deps + cross-task consistency, C4 risk/role + irreversible-op
pre-mortem, C5 approach-fit, plus requirement→task coverage. Hard 2-pass cap; a single-judge
BLOCKER gets one confirming independent pass before any re-plan; cap-with-open-blocker never
proceeds — escalate to the human. Honest limit: Layer 1 cannot judge command STRENGTH; Layer 2's
clean verdict raises the floor, it does not verify correctness — downstream judges own that.

## 4. Effects → native controls

Prompt instructions never count as enforcement when the platform offers deterministic controls.
Compile the effects taxonomy into `settings.json` (see `settings.example.json` in this adapter —
merge, don't replace):

| Effect dimension | Native control |
|---|---|
| filesystem read | `permissions.allow` (Read/Grep/Glob) |
| filesystem write/delete | `permissions.ask` (Write/Edit); deny secrets paths |
| process (tests, linters) | `permissions.allow` for read-only checks |
| network egress | `permissions.ask` (curl/wget/installs) |
| version-control commit/push | `permissions.ask`; **deny + PreToolUse hook** for force-push to protected branches |
| external systems (deploy/send) | `permissions.ask` at minimum; A4 requires explicit human authorization |

Two judgments have no native expression and stay yours: (1) every dispatched worker gets an
explicit scope + side-effect budget in its prompt; (2) novel operations no rule anticipates default
to ask. Workers escalate (STOP and report), never ask forgiveness.

## 5. Context health

Event-triggered self-audit — after compaction, before a high-risk transition, on repeated
verification failures, on requirement change, on long-pause resume — plus a fallback interval of
roughly every 3 tasks reaching verified. Re-read state from disk (plan, task states, journal), then
emit `[CONTEXT HEALTH: OK — <evidence>]` or `[CONTEXT HEALTH: DEGRADED — <rule/invariant>]` and
correct FIRST. A bare OK without evidence is Rubber-Stamp Compliance.

## 6. Recovery

Decision model in `./policy/recovery.md`: classify failure scope (local | contract | architectural
| environmental), analyze blast radius and evidence contamination, spend a bounded retry budget,
explicitly invalidate stale evidence, and restart with the *lesson*, not the accumulated state.
Fix forward only when it is demonstrably safer than rollback. Late-discovered errors (surfacing
after several unverified tasks) are structural regardless of apparent severity.

## 7. The counterweight — Complexity Accumulation

Native tooling is biased toward MORE machinery; a feature never tells you to stop using it. The
right amount of harness is the minimum that still decomposes and verifies. Another
panel/subagent/layer is not the fix for a messy run — cleaner isolation and roles are. Anti-pattern
catalog (Role Collapse, Self-Review, Rubber-Stamp Compliance, Prose-API, Adapter Sprawl, …):
`./policy/anti-patterns.md`.
