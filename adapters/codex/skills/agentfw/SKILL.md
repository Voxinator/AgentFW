---
name: agentfw
description: AgentFW r9 operational playbook for OpenAI Codex. Use for multi-component or multi-file work, integration seams, production/security/infra changes, bug fixes, autonomous or long-running tasks — anything deriving to assurance A2 or above. Supplies role separation, acceptance contracts, the plan-critique gate, verification standards, and recovery policy.
---

# AgentFW r9 — Operational Playbook (Codex)

You already derived an assurance level from the bootloader kernel in AGENTS.md and emitted
`[ASSURANCE: Ax — <justification>]`. This skill is the full playbook for A2+ work. The neutral
policy it compiles from lives at `../../../../policy/` in the AgentFW repo; the install copies
that directory alongside this file (as `policy/` next to this SKILL.md) and the Layer-1
validator too (as `tools/validate-plan` next to this SKILL.md), so the references below
resolve — and the validator runs — without the repo checkout.

## 0. Capability preflight (run before any A2+ work)

Assurance gating consults the ACTIVE install, not the platform brochure. Before engaging the A2+
workflow below:

1. Read the packaged capability contract — the manual install (INSTALL.md Step 2) copies the
   adapter's `capability.yaml` next to this SKILL.md; fall back to
   `adapters/codex/capability.yaml` in an AgentFW repo checkout only if the packaged copy is
   missing:

   ```sh
   cat ./capability.yaml   # packaged beside this SKILL.md; secondary path: the repo checkout
   ```

2. There is no installer on Codex, so no generated active-state file exists: run each
   capability's documented `activation_probe` (listed per key in the capability contract)
   manually, and record the results in your plan before relying on any configured-state claim.

A capability that the derived assurance tier requires but that is unavailable or unconfigured
means you degrade per the policy's degradation rules
(`../../../../policy/capability-contract.md`; post-install `policy/capability-contract.md`
beside this file) — reduced autonomy or human participation, DECLARED in the plan, never silent.

## 1. Assurance derivation (full table)

Three questions — Q1 blast radius & reversibility; Q2 defect-escape probability; Q3 autonomy &
irreversibility — map to a level. Full model: `../../../../policy/assurance-model.md`
(post-install: `policy/assurance-model.md` beside this file).

| Level | Typical | Controls |
|---|---|---|
| A0 | lookup / explanation / tiny reversible edit | direct execution; producer check |
| A1 | bounded single-seam implementation | lightweight plan; producer tests (machine-checked) |
| A2 | multi-component / integration seams | decompose; independent verification at seams; Layer-1 plan validation; Layer-2 critique if ambiguity/shared values |
| A3 | production bug, security, infra; autonomy compounded by risk (see escalators) | independent workers + independent verifier; full acceptance contracts; both plan-critique layers; checkpoints |
| A4 | irreversible / destructive / critical autonomous | A3 + adversarial verification + explicit human authorization + rollback proof (restorability, not just backup integrity) |

Escalators (any one bumps to at least A3): production/live infra; security-sensitive;
destructive/history-rewriting; autonomy PLUS at least one of {material side effects, unclear
integration seams, elevated defect-escape probability, no rapid human review}. Autonomy alone
does not escalate: a routine, reversible multi-file refactor with strong tests is A2 even when
run autonomously. Verification tiers: **producer** always;
**independent** at A2 seams and all A3+; **adversarial** at A4 and for security/destructive work
regardless of level.

## 2. Role separation → Codex primitives

One context that plans, implements, and verifies checks for what it *intended*, not what
*happened*. Codex subagents run in their own threads with separate model and tool execution and
return consolidated results to the caller — drive that isolation; don't re-describe it in prose.

| Role | Codex primitive |
|---|---|
| Planner / dispatcher | main session. Never writes A2+ implementation inline. |
| Worker | a subagent thread (spawn via delegation; inspect with `/agent`). One task per dispatch, contract copied verbatim into the prompt. Optionally a custom agent: a TOML file in `~/.codex/agents/` or `.codex/agents/` with `name`, `description`, `developer_instructions`, and its own `sandbox_mode`. |
| Judge of record | a *separate* subagent thread that did not produce the artifact, input-curated. For working-tree review, the built-in `/review` reports findings without modifying the tree. |
| Plan critic | a separate subagent given the plan + requirements ONLY (Layer 2 below). |
| Parallel fan-out | parallel subagents (`agents.max_threads`, default 6; nesting capped by `agents.max_depth`, default 1). |

**Isolation limits on this platform (per the packaged `capability.yaml` — §0; repo checkout:
`adapters/codex/capability.yaml`):** parallel CLI subagents share
one working copy — `worktree_isolation` is partial (desktop-app scheduled tasks only). Serialize
colliding edits or partition by path; never assume worktree isolation the CLI does not provide.
If no subagent-capable Codex is available, the independent-verification fallback per the
capability contract's degradation rules is a **second, fresh Codex session** given only
requirements + state + contracts — or **human review**. Never present a voice-switch inside one
context as independent review.

**Judge input-curation (no native analog — you supply it):** the runtime isolates a subagent's
*output* but does not stop you contaminating a judge's *input*. A judge receives ONLY requirements
+ current state + acceptance criteria/contracts. Never the producer's plan, reasoning, or
self-assessment. On judge failure: findings → planner → a *new* worker, not the stale one.

## 3. Acceptance Contract v2 + plan blocks

Every A2+ task carries a contract (full spec: `../../../../policy/acceptance-contract.md`):
`requirement_ids[]`, `criteria`, `acceptance_command`, `environment`, `expected_signal` (anchored —
must not also match a fail line), `negative_cases[]` (REQUIRED whenever `risk` is present), `risk`,
`evidence` (freshness: produced_after_change), `integration_seam` (JSON boolean),
`risk_class` (none | standard | security | destructive), `required_verification_tier`
(producer | independent | adversarial), `rerunnable` (JSON boolean), `constraints` (optional).
Tier-1 lever = at least
one negative/regression assertion the command actually RUNS — a bare smoke import is not Tier-1.
Non-shell work (docs/research/design): a named mechanical check (grep/link-check/renderer) plus a
designated independent reviewer; prose-only acceptance is never Tier-1.

Plans embed one machine-readable block, fenced as ` ```json agentfw-plan ` (the example below
uses that exact fence, so this SKILL.md itself validates as a single-block input to
`tools/validate-plan` — the AgentFW roundtrip suite runs exactly that check):

```json agentfw-plan
{ "version": "1.1", "assurance": "A3",
  "requirements": [{"id": "R1", "text": "..."}],
  "tasks": [{ "id": "T1", "title": "...", "deps": [],
              "contract": { "requirement_ids": ["R1"], "criteria": "...",
                            "acceptance_command": "...", "expected_signal": "...",
                            "environment": "...", "evidence": "...",
                            "integration_seam": false, "risk_class": "standard",
                            "required_verification_tier": "independent",
                            "risk": "...", "negative_cases": ["..."], "rerunnable": true }}]}
```

Schema versioning: `"version": "1.1"` is MANDATORY. A `"version": "1"` block is rejected by
default and accepted only via `validate-plan --legacy` — historical provenance only (re-checking
plans authored before the 1.1 schema); never author a new plan against v1. `"1.1"` requires, per
contract at A2+: `integration_seam` (JSON boolean) and `risk_class` (the structured
tier-derivation inputs — free-form `risk` prose never substitutes), `required_verification_tier`
∈ {producer, independent, adversarial} and ≥ the floor mechanically derived from assurance +
`integration_seam` + `risk_class` (A3 ⇒ independent; A4 ⇒ adversarial; `integration_seam: true`
at A2 ⇒ independent; risk_class security/destructive ⇒ adversarial at EVERY level), a non-empty
`environment`, and `rerunnable` as a JSON boolean; at A3+ also a non-empty `evidence`.
`constraints` stays optional.

**Layer 1 (deterministic — run it, always):** run the validator BEFORE the first worker
dispatch. Resolve it skill-relative FIRST: `python3 <skill-dir>/tools/validate-plan <plan.md>` —
the copy installed next to this SKILL.md (`./tools/validate-plan`). Fallback, only if the
skill-local copy is missing: `python3 tools/validate-plan <plan.md>` from an AgentFW repo
checkout. It requires a local shell with `python3` (stdlib
only) — on Codex that means running it as a sandboxed command; in `read-only` sandbox it can run
but the plan file must already exist on disk. It mechanically checks: block parses; assurance
valid; every requirement covered by some task; every contract non-empty; deps acyclic; risk ⇒
negative_cases; A3/A4 ⇒ negative_cases everywhere. Exit 0 + PASS or a named defect.

**Layer 2 (semantic judge — A2 with ambiguity/shared values, all A3+):** dispatch a plan-critic
subagent with the plan + requirements ONLY. It runs the C0–C5 rubric
(`../../../../policy/plan-critique.md`): C0 substrate-grounding, C1 independence, C2
prose-vs-mechanical reachability (core check), C3 deps + cross-task consistency, C4 risk/role +
irreversible-op pre-mortem, C5 approach-fit, plus requirement→task coverage. Hard 2-pass cap; a
single-judge BLOCKER gets one confirming independent pass before any re-plan; cap-with-open-blocker
never proceeds — escalate to the human. Honest limit: Layer 1 cannot judge command STRENGTH;
Layer 2's clean verdict raises the floor, it does not verify correctness — downstream judges own
that.

## 4. Effects → native controls

Prompt instructions never count as enforcement when the platform offers deterministic controls.
Compile the effects taxonomy into `~/.codex/config.toml` (see `config.example.toml` in this
adapter — merge, don't replace):

| Effect dimension | Codex control |
|---|---|
| filesystem read | `sandbox_mode = "read-only"` for review-only runs |
| filesystem write/delete | `sandbox_mode = "workspace-write"` scopes writes to the workspace; extend deliberately via `[sandbox_workspace_write].writable_roots`; never default to `danger-full-access` |
| process (tests, linters) | commands run inside the active sandbox; `approval_policy = "on-request"` (or `"untrusted"`) gates escalation |
| network egress | `[sandbox_workspace_write] network_access = false` — platform-enforced off switch |
| version-control commit/push | no dedicated key: route through `approval_policy` so push/history-rewrite pauses for approval. A PreToolUse hook can deny force-pushes deterministically (exit 2), but official docs call hooks "a guardrail rather than a complete enforcement boundary" — treat hook denial as defense-in-depth, advisory beyond the sandbox floor, not the primary control. |
| external systems (deploy/send) | `approval_policy` at minimum; A4 additionally requires explicit human authorization in-conversation |

Two judgments have no native expression and stay yours: (1) every dispatched worker gets an
explicit scope + side-effect budget in its prompt (and, for custom agents, its own `sandbox_mode`);
(2) novel operations no rule anticipates default to ask. Workers escalate (STOP and report), never
ask forgiveness.

## 5. Context health

Event-triggered self-audit — after compaction, before a high-risk transition, on repeated
verification failures, on requirement change, on `codex resume` of an old session — plus a
fallback interval of roughly every 3 tasks reaching verified. Re-read state from disk (plan file,
task states, transcripts), then emit `[CONTEXT HEALTH: OK — <evidence>]` or
`[CONTEXT HEALTH: DEGRADED — <rule/invariant>]` and correct FIRST. A bare OK without evidence is
Rubber-Stamp Compliance. Resumed sessions reconstruct context from the transcript — treat every
resume as a mandatory health check, not a continuation you can trust blind.

## 6. Recovery

Decision model in `../../../../policy/recovery.md`: classify failure scope (local | contract |
architectural | environmental), analyze blast radius and evidence contamination, spend a bounded
retry budget, explicitly invalidate stale evidence, and restart with the *lesson*, not the
accumulated state. Fix forward only when it is demonstrably safer than rollback. Late-discovered
errors (surfacing after several unverified tasks) are structural regardless of apparent severity.

## 7. The counterweight — Complexity Accumulation

Native tooling is biased toward MORE machinery; a feature never tells you to stop using it. The
right amount of harness is the minimum that still decomposes and verifies. Another subagent/layer
is not the fix for a messy run — cleaner isolation and roles are. Anti-pattern catalog (Role
Collapse, Self-Review, Rubber-Stamp Compliance, Prose-API, Adapter Sprawl, …):
`../../../../policy/anti-patterns.md`.
