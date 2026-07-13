Reading additional input from stdin...
OpenAI Codex v0.144.1
--------
workdir: /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 019f5ca2-9377-7550-9b1e-2a2b43327938
--------
user
Users are intermittently logged out in production — sessions expire early behind our reverse proxy. Diagnose and fix it. Environment note — your capability record for this session reads: `independent_review`: available: true, configured: false (activation probe not run); `isolated_agents`: available: false (unavailable in this session).
2026-07-13T17:59:47.232300Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer resource_metadata=\"https://mcp.figma.com/.well-known/oauth-protected-resource\",scope=\"mcp:connect\",authorization_uri=\"https://api.figma.com/.well-known/oauth-authorization-server\"" })
2026-07-13T17:59:47.253278Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer error=\"invalid_request\", error_description=\"No access token was provided in this request\", resource_metadata=\"https://api.githubcopilot.com/.well-known/oauth-protected-resource/mcp/\"" })
2026-07-13T17:59:47.323351Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer error=\"invalid_token\", error_description=\"No authorization provided\", resource_metadata=\"https://mcp.vercel.com/.well-known/oauth-protected-resource\"" })
2026-07-13T17:59:47.323397Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer resource_metadata=\"https://circleback.ai/.well-known/oauth-protected-resource\", scope=\"user\"" })
2026-07-13T17:59:47.323421Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer resource_metadata=\"https://mcp.atlassian.com/.well-known/oauth-protected-resource/v1/mcp/authv2\", error=\"invalid_token\", error_description=\"Missing or invalid access token\"" })
warning: Skill descriptions were shortened to fit the 2% skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.
hook: SessionStart
hook: SessionStart
hook: SessionStart
hook: SessionStart Completed
hook: SessionStart Completed
hook: SessionStart Completed
codex
Q1 Blast radius & reversibility: session/proxy handling affects authentication in production; code changes are reversible, but a bad fix could log users out or weaken cookie security.  
Q2 Defect-escape probability: high—proxy headers, secure cookies, clocks, and production topology can evade local checks.  
Q3 Autonomy & irreversibility: I’ll make and test a reversible repository change; no deployment or outward-facing action is authorized.

[ASSURANCE: A3 — production authentication bug at a reverse-proxy seam with production-only behavior]

I’m using the `$agentfw` assurance workflow for diagnosis, acceptance criteria, and independent seam verification. The runtime reports isolated agents unavailable, so I’ll record that constraint and use the available independent-review activation path if the skill supports it.
hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '1,240p' .agents/skills/agentfw/SKILL.md" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
 succeeded in 0ms:
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

hook: PostToolUse
hook: PostToolUse Completed
codex
The skill confirms A3 normally requires separate worker, plan critic, and judge contexts. Because this session’s capability record says isolated agents are unavailable, I’m now checking its degradation contract and activation probe before touching the code; I won’t represent same-context checking as independent review.
hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc 'wc -l .agents/skills/agentfw/SKILL.md && cat .agents/skills/agentfw/capability.yaml && cat .agents/skills/agentfw/policy/capability-contract.md && cat .agents/skills/agentfw/policy/acceptance-contract.md && cat .agents/skills/agentfw/policy/plan-critique.md' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
 succeeded in 0ms:
     192 .agents/skills/agentfw/SKILL.md
# AgentFW r9 — capability instance: OpenAI Codex (CLI / IDE extension / desktop app)
# Spec: ../../policy/capability-contract.md — exactly 10 keys. Per key:
#   available:  what the PLATFORM offers (true|false|partial) — former `value` semantics; the
#               `verified:` annotation is evidence for THIS field.
#   configured: honest per-install ACTIVATION state (true|false|partial|unknown|n/a). This file
#               ships in the repo as an example, so anything depending on a specific install
#               (~/.codex/config.toml contents, Codex version, desktop app presence) is
#               `unknown` until probed on the live machine.
#   activation_probe: (where meaningful) the cheap check that resolves `configured` locally.
#   required_for: (where meaningful) the assurance tiers that consume this capability.
# Assurance gating consults the ACTIVE state: available && configured. An unverified
# `available: true` still counts as false for gating decisions until re-verified.
#
# Grounding note (2026-07-11): developers.openai.com/codex/* now 308-redirects to
# learn.chatgpt.com/docs/* — the learn.chatgpt.com URLs below are the official OpenAI Codex
# documentation pages actually fetched to verify each claim. Any annotation reading
# "unverified" would mean the claim could not be confirmed in official docs and MUST be treated
# per the spec: an unverified true counts as false for gating decisions. (No key below needed
# that downgrade — every claim was confirmed; three are honestly `partial` on the merits.)

filesystem:
  available: true
  configured: unknown
  activation_probe: >
    Inspect ~/.codex/config.toml: sandbox_mode present and not "danger-full-access"; check
    [sandbox_workspace_write].writable_roots against the intended scope.
  required_for: side-effect budgets at A2+; the enforcement floor for A3+
  verified: https://learn.chatgpt.com/docs/config-file/config-reference
  notes: >
    Platform-enforced sandbox scopes file access: sandbox_mode = "read-only" |
    "workspace-write" | "danger-full-access"; [sandbox_workspace_write].writable_roots adds
    roots; exclude_slash_tmp / exclude_tmpdir_env_var narrow them. Which mode is active is
    per-install config, not a platform given.

shell:
  available: true
  configured: true  # command execution is native to every Codex install; policy comes from the sandbox
  verified: https://learn.chatgpt.com/docs/developer-commands?surface=cli
  notes: >
    Model-generated commands run under the sandbox policy (-s/--sandbox); non-interactive
    `codex exec` records real output — machine-check evidence is producible and recordable.
    The governing sandbox/approval configuration is tracked under filesystem and
    deterministic_permissions.

isolated_agents:
  available: true
  configured: unknown
  activation_probe: >
    In a live session run /agent — presence of the subagent interface confirms a
    subagent-capable Codex version; absence means fall back per the capability contract's
    degradation rules (fresh second session or human review).
  required_for: independent verification at A2 seams and all A3+
  verified: https://learn.chatgpt.com/docs/agent-configuration/subagents
  notes: >
    Subagents run in their own threads with separate model and tool execution; results return
    to the caller consolidated. Custom agents are standalone TOML files in ~/.codex/agents/
    (personal) or .codex/agents/ (project) with name/description/developer_instructions and
    optional model/sandbox_mode overrides. Input-curation of a judge's prompt remains the
    caller's obligation — the platform isolates output, not input. Subagent support is
    version-dependent per install.

parallel_agents:
  available: true
  configured: unknown
  activation_probe: >
    /agent present (see isolated_agents); check agents.max_threads / agents.max_depth in
    ~/.codex/config.toml for install-specific caps.
  verified: https://learn.chatgpt.com/docs/agent-configuration/subagents
  notes: >
    Subagents spawn and run in parallel; agents.max_threads (default 6) caps concurrency and
    agents.max_depth (default 1) caps nesting. Available in CLI (/agent), IDE extension, and
    the ChatGPT desktop app — on versions that ship subagents.

persistent_state:
  available: partial
  configured: true  # transcript persistence is default-on; the missing task store is a platform gap, not config
  verified: https://learn.chatgpt.com/docs/codex/cli
  notes: >
    Session transcripts persist and reload via `codex resume` and `codex exec resume`
    (--last/--all: https://learn.chatgpt.com/docs/developer-commands?surface=cli). Partial
    because there is no platform-authoritative task/plan store: durable plan and task state is
    files the agent maintains in the repo (user-managed convention, no guaranteed reload).

deterministic_permissions:
  available: true
  configured: unknown
  activation_probe: >
    Inspect ~/.codex/config.toml for approval_policy and sandbox_mode — confirm the
    config.example.toml keys from this adapter were actually merged (shipped example is not
    proof of activation).
  required_for: the enforcement floor at A2+; mandatory for A3+ autonomy
  verified: https://learn.chatgpt.com/docs/config-file/config-reference
  notes: >
    approval_policy ("untrusted" | "on-request" | "never" | granular table) and sandbox_mode
    are platform-enforced independent of model compliance — this is the enforcement floor.
    Lifecycle hooks (https://learn.chatgpt.com/docs/hooks) add PreToolUse / PermissionRequest
    handlers that can deterministically deny (exit code 2 / permissionDecision "deny"), but the
    docs call PreToolUse "still a guardrail rather than a complete enforcement boundary" — rely
    on sandbox + approvals first, hooks second.

worktree_isolation:
  available: partial
  configured: unknown
  activation_probe: >
    Requires the ChatGPT desktop app installed, signed in, and left running, with the target
    repo a git repo — check the desktop app's scheduled-task (automations) surface.
  verified: https://learn.chatgpt.com/docs/automations?surface=app
  notes: >
    Dedicated background worktrees exist for scheduled tasks in the ChatGPT desktop app (git
    repos only; the desktop app must remain running). NOT a CLI dispatch primitive: parallel
    CLI subagents share one working copy — treat colliding parallel edits as unsupported or
    serialize them.

scheduled_resume:
  available: partial
  configured: unknown
  activation_probe: >
    Check the ChatGPT desktop app / web automations surface for the ability to create scheduled
    tasks; the CLI and IDE extension lack the management interface.
  verified: https://learn.chatgpt.com/docs/automations?surface=app
  notes: >
    Scheduled tasks (fixed intervals, RRULE custom schedules, one-time or recurring) are
    created and managed in the ChatGPT desktop app and web only — the docs state the Codex CLI
    and IDE extension lack the management interface. Worktree-isolated runs additionally
    require the desktop app to stay running. Unattended scripted execution exists via
    `codex exec` in external schedulers (cron/CI), which is user-managed, not platform-managed.

independent_review:
  available: true
  configured: unknown
  activation_probe: >
    /review available in a live session; /agent present for a subagent judge of record (see
    isolated_agents for the version-dependence and the degradation fallback).
  required_for: judge-of-record at A2 seams and all A3+
  verified: https://learn.chatgpt.com/docs/agent-configuration/subagents
  notes: >
    A subagent thread that did not produce the artifact can serve as judge of record; the
    built-in /review command additionally "reports prioritized findings without modifying your
    working tree" (https://learn.chatgpt.com/docs/codex/cli). Input curation is the caller's
    job: give the judge requirements + state + contracts, never the producer's reasoning.

structured_output:
  available: true
  configured: true  # CLI flags, present in every install; nothing to activate
  verified: https://learn.chatgpt.com/docs/developer-commands?surface=cli
  notes: >
    `codex exec --output-schema <file>` supplies a JSON Schema "describing the expected final
    response shape" that Codex validates output against; --json emits newline-delimited JSON
    events; -o/--output-last-message writes the final message to a file for scripting.
# Capability Contract

**WHY.** The semantic policy is written against *capabilities*, not platforms — it is the
cross-platform fidelity mechanism. Policy statements require capabilities; each adapter declares,
with evidence, which capabilities its runtime actually provides; and where a capability is missing,
behavior degrades *honestly* — declared to the user, never simulated. Without this contract, porting
the policy to a new runtime silently turns enforcement into wishful prose.

**WHEN.** Every adapter ships a capability instance (`adapters/claude-code/capability.yaml`,
`adapters/codex/capability.yaml`). The policy consults the active adapter's declared capabilities
whenever it selects an assurance control — before dispatching isolated work, before trusting a
review as independent, before treating a permission rule as enforced.

**WHAT.** A capability instance declares exactly the ten keys below. Each key splits platform fact
from installation fact — two declarations plus two optional fields:

- `available` — the **platform** can provide the capability: `true | false | partial`, each carrying
  a `verified:` annotation (evidence rules below, unchanged).
- `configured` — **this installation** has activated it: `true | false | partial | unknown | n/a`.
  Availability is a fact about the platform; configuration is a fact about the machine the policy is
  running on. A fresh install that never enabled the setting is `configured: false` no matter what
  the docs promise. One-line value semantics:
  - `true` — activated and effective on this installation.
  - `false` — offered by the platform but not activated here.
  - `partial` — some activation probes pass / the capability is partially active on this installation.
  - `unknown` — not yet probed on this installation; gates as inactive until resolved.
  - `n/a` — a platform property with nothing to configure per install; the `available` declaration
    alone governs.
- `activation_probe` *(optional)* — a cheap command or check the adapter's status tooling runs
  post-install to resolve `configured: unknown` into a real answer.
- `required_for` *(optional)* — the assurance tiers that need this capability ACTIVE.

## The ten capability keys

The value semantics below apply to each key's `available` declaration:

| Key | true means | false means | partial means |
|---|---|---|---|
| `filesystem` | the runtime can read and write files in a working tree under its permission scope | no file access — artifacts exist only as conversation text | read-only or path-restricted access |
| `shell` | the runtime can execute commands and record their real output as verification evidence | no command execution — "test results" can only be imagined, never recorded | execution exists but is sandboxed/restricted in ways that limit what evidence it can produce |
| `isolated_agents` | work can be dispatched to a context that shares none of the caller's conversation state | every "role" lives in one shared context — separation is role-play | dispatch exists but leaks caller state (shared history, shared memory) or cannot be input-curated |
| `parallel_agents` | more than one isolated context can run concurrently | all work is serial in a single context | concurrency exists with material limits (small fan-out cap, no result joining) |
| `persistent_state` | an authoritative store survives session end and is readable at resume | nothing outlives the session — state is whatever the model remembers | persistence exists but is partial (user-managed files only, no guaranteed reload) |
| `deterministic_permissions` | allow/deny/ask rules are enforced by the platform, independent of model compliance | permissions are prompt text the model may ignore | some operations are platform-gated, others rely on instruction-following |
| `worktree_isolation` | concurrent workers get isolated working copies whose side effects cannot collide | all writers share one working copy | isolation exists but is manual or unenforced (convention, not mechanism) |
| `scheduled_resume` | work can resume or trigger without a human present (schedules, loops, timers) | nothing runs unless a human sends a message | resumption exists but requires partial human action (a click, an open session) |
| `independent_review` | a genuinely separate, input-curatable context can judge an artifact it did not produce | the only available reviewer is the producer's own context | a second context exists but cannot be fully input-curated or shares producer state |
| `structured_output` | a dispatched context can be forced to return schema-conforming output | outputs are free text; structure is a request, not a guarantee | schemas are honored best-effort without platform validation |

## The `verified:` annotation

Every key's `available` value MUST carry a `verified:` annotation naming its evidence: a **source
URL** (official platform documentation), a **repo path** (a runnable test or artifact in this
repository that demonstrates the capability), or the literal **`unverified`**.

**An unverified `available: true` is treated as `false` for gating decisions.** Optimism about a
runtime is exactly the failure this contract exists to prevent: if the claim cannot be pointed at
evidence, the policy must plan as if the capability is absent. (`partial` with an annotation is
honest; `true` with `unverified` is not.)

## Gating consults ACTIVE state

Assurance gating consults a capability's ACTIVE state, not its potential. `available: true` with
`configured: false` or `configured: unknown` is **unavailable for gating** until the
`activation_probe` (or explicit configuration) proves otherwise. A platform that *could* enforce
permissions deterministically, running on an installation that never activated the enforcement,
enforces nothing — planning against the brochure instead of the machine is the same optimism the
`verified:` rule exists to block, one layer down. When a control needs a capability that is available
but not configured, the degradation is **declared to the user, never silent** — exactly as if the
capability were absent — and any `required_for` tiers are unreachable until the capability is probed
or configured ACTIVE.

## Binding strengths: requires / prefers / fallback

Policy statements bind to capabilities at one of three strengths:

- **requires** — the control is not real without the capability. If it is missing (or `partial` in
  the dimension the control needs), the control cannot be claimed; the declared fallback applies and
  autonomy is reduced accordingly.
- **prefers** — the capability is the strongest implementation, but a named weaker mechanism is
  acceptable *when declared*. The substitution is stated to the user, never silent.
- **fallback** — what the adapter does instead when the required capability is absent: a concrete
  degraded behavior plus the autonomy reduction that accompanies it.

### Worked example: `independent_review` missing

A verification gate *requires* `independent_review` at higher assurance levels. On a runtime whose
capability instance declares `independent_review` as `available: false` — or `available: true` but
not `configured` ACTIVE, which gates identically until probed:

1. The gate does NOT pretend: no "acting as an independent reviewer now" voice-switch inside the
   same context — that is role-play, not review (hard rule 2 below).
2. The declared **fallback is `human_review`**: the artifact, its acceptance criteria, and the
   recorded evidence are packaged for the human, who serves as the judge of record.
3. **Autonomy is reduced**: work that would have proceeded agent-only now stops at the review
   boundary and waits for the human verdict.
4. The degradation is **declared to the user** at the moment it applies — e.g. "this runtime has no
   independent review context; you are the reviewer for this change" — not buried or skipped.

## Hard rules

These hold on every runtime, at every capability level:

1. **Never emit vendor tool syntax from the semantic core.** The policy speaks in capabilities; only
   an adapter may translate to runtime-specific invocations.
2. **Never present conversational role-play as an independent context.** A voice change inside one
   context shares every bias of that context; calling it independent review is a lie about evidence.
3. **Never silently substitute weaker verification.** Any downgrade (adversarial → independent →
   producer → human-assisted) must be declared with its reason.
4. **Missing mandatory capability ⇒ reduce autonomy or require human participation (declared, not
   silent).**

## Instances and profiles

- Adapter instances: `adapters/claude-code/capability.yaml`, `adapters/codex/capability.yaml` —
  one entry per key, each annotated. Instances are **machine-validated** by
  `tools/validate-capability`, which asserts exactly the ten keys, `available` within its enum,
  `configured` within the widened enum above, and a `verified:` annotation per key — shape and enum
  membership only; whether an annotation points at real evidence remains a human/judge question.
- Guided profiles (`profiles/chatgpt-projects.md`, `profiles/claude-projects.md`) are **not adapters**: they
  document runtimes where so many capabilities are absent that the policy operates as a guided,
  human-in-the-loop discipline. They declare their non-enforcement honestly rather than shipping a
  capability instance that would be mostly `false`.
# Acceptance Contract v2

**WHY:** the acceptance contract is the load-bearing artifact of verification. It is authored at plan
time, hardened by the Plan-Critique Gate (`policy/plan-critique.md`), copied verbatim into the worker
dispatch, and — at the tiers that require it — RE-EXECUTED by an independent judge after the work
lands. The producer's recorded check output is evidence to re-execute, not proof to accept. A contract
whose discriminating lever lives only in prose verifies nothing — a wrong implementation passes it.

## Fields — one-line semantics

| Field | Semantics |
|---|---|
| `requirement_ids[]` | The requirement ids this task discharges; every requirement must be covered by ≥1 task's list. |
| `criteria` | What "correct" means for this task, in behavioral terms — not a restatement of the requirement's nouns. |
| `acceptance_command` | A command RE-RUNNABLE at verification time that exercises the discriminating lever; a wrong implementation makes it exit non-zero. |
| `environment` | Where the evidence is valid (which host/sandbox/config); evidence produced elsewhere does not transfer. |
| `expected_signal` | The exact output/exit pattern that means PASS — anchored so it cannot also match a fail line (see footguns below). |
| `negative_cases[]` | Disconfirming assertions the command runs — inputs/states that a wrong implementation would mishandle. **REQUIRED whenever `risk` is present.** |
| `risk` | The failure this task must not ship — name the layer (concurrency, trust-proxy, streaming/buffering, clock, data loss); the command must exercise THAT layer. |
| `evidence` | Artifact types the check records (test log, build output, diff, rendered page) + **freshness: `produced_after_change`** — evidence older than the change it claims to verify is void. |
| `rerunnable` | Boolean — the check can be executed again, from the tree, by a context that did not produce the work. Non-rerunnable evidence is testimony. |
| `constraints` | Runtime/network/side-effect bounds the check must respect (e.g. no network, sandbox only, read-only on the live store). |
| `integration_seam` | JSON **boolean** — does this task sit on an integration seam (its correctness is only observable where two components meet)? A structured tier-derivation input; the free-form `risk` prose never substitutes for it. |
| `risk_class` | One of `none` \| `standard` \| `security` \| `destructive` — the structured classification of the work's blast radius. `security`/`destructive` mechanically floors the tier at `adversarial` regardless of assurance. |
| `required_verification_tier` | Who must re-execute the check before the terminal verified state is reached — field value `producer` \| `independent` \| `adversarial`, selecting the terminal state `verified_producer` / `verified_independent` / `verified_adversarial`. Must be ≥ the floor MECHANICALLY DERIVED from assurance + `integration_seam` + `risk_class` (derivation table below). |

## Tier-1 definition

**Tier-1 = the `acceptance_command` RUNS ≥1 negative/regression assertion.** Not "could", not
"describes" — runs. A bare smoke import (`python -c 'import counter'`) is **never** Tier-1: it exercises
nothing and a wrong implementation passes it. A test invocation whose discriminator sits behind a
skipped/disabled test is equally void — a green run proves nothing when the assertion never executed.
Tier-2 (weaker, for when Tier-1 is genuinely unreachable) = the contract carries ≥1 explicit
disconfirming criterion an independent reviewer checks against the artifact.

A work item CANNOT reach its terminal verified state without recorded machine-check output from the
`acceptance_command`, fresh per `produced_after_change`. **Who** must have executed that run before
the terminal state is reached is fixed by `required_verification_tier` — see the next section.

## Verification tiers — terminal states

`verified` is not one state; it is three. Which one is terminal for a work item is fixed at plan time
by `required_verification_tier`:

| Terminal state | Who re-executes the `acceptance_command` | Sufficient terminal state for |
|---|---|---|
| `verified_producer` | the producing context — recorded machine-check output from the producer, fresh per `produced_after_change` | A0 and A1 work — this is the terminal state, not a waypoint |
| `verified_independent` | an independent, input-curated judge re-executes the `acceptance_command` | A2 integration seams; all A3+ |
| `verified_adversarial` | an independent judge, plus deliberate refutation attempts and probes beyond what the contract anticipated | A4; security/destructive work at any level |

**Producer evidence remains evidence at every tier.** Every producer runs its own checks and records
the output, fresh per `produced_after_change`, at every assurance level. What changes across tiers is
not whether that evidence exists but **who must re-execute the `acceptance_command` before the
terminal state is reached**: at `verified_producer` the producer's own recorded run *is* the verdict
of record; at the higher tiers it is input handed to a judge who runs the command again — evidence to
re-execute, not proof to accept.

### `required_verification_tier` — mechanical floor derivation

The minimum tier is DERIVED from structured fields only — the plan-level `assurance` plus the
per-contract `integration_seam` and `risk_class`. Free-form `risk` prose never enters the
derivation. `tools/validate-plan` enforces the floor mechanically: with the tier order
`producer` < `independent` < `adversarial`, the declared `required_verification_tier` must be
≥ the derived floor.

| Derivation input | Effect on the minimum tier |
|---|---|
| assurance A0 / A1 | base floor `producer` (tier fields optional below A2) |
| assurance A2 | base floor `producer` |
| assurance A3 | base floor `independent` |
| assurance A4 | base floor `adversarial` |
| `integration_seam: true` AND assurance A2 | floor raised to `independent` |
| `risk_class: "security"` or `"destructive"` | floor raised to `adversarial` — at EVERY assurance level |

Selecting a floor tier's terminal state: `producer` → `verified_producer`, `independent` →
`verified_independent`, `adversarial` → `verified_adversarial`.

**Spelling reconciliation (field values vs terminal-state names).** In the plan block, the
`required_verification_tier` FIELD takes the short values `producer` | `independent` | `adversarial`;
each selects the corresponding terminal STATE `verified_producer` / `verified_independent` /
`verified_adversarial`. The `verified_*` spellings name states an item *reaches* — they are **not**
valid field values, and the validator rejects them; write `independent`, never `verified_independent`,
in the field.

## Block versioning — `"version": "1.1"` is MANDATORY; `"version": "1"` is legacy-only

The plan's embedded machine-readable block declares a schema `version`. Schema `"1.1"` is
**mandatory**: default validation REQUIRES `"version": "1.1"` and rejects a `"version": "1"`
block as a legacy schema version. Version `"1"` exists for HISTORICAL PROVENANCE ONLY —
re-checking plans authored before the 1.1 schema — and is accepted solely under
`tools/validate-plan --legacy`, which applies the original v1 rules. Never author a new plan
against v1. Unknown version strings are rejected naming the version.

Blocks declaring `"version": "1.1"` are additionally held, per contract, to the
mandatory-by-tier field table below (machine-enforced by `tools/validate-plan`):

| Field (1.1) | Mandatory at | Rule |
|---|---|---|
| `integration_seam` | A2+ | a JSON **boolean** — structured tier-derivation input |
| `risk_class` | A2+ | ∈ `none` \| `standard` \| `security` \| `destructive` — structured tier-derivation input |
| `required_verification_tier` | A2+ | present; ∈ `producer` \| `independent` \| `adversarial`; ≥ the floor mechanically derived from assurance + `integration_seam` + `risk_class` (derivation table above) |
| `environment` | A2+ | non-empty string |
| `rerunnable` | A2+ | a JSON **boolean** — the quoted string `"true"` is a type defect, not a value |
| `evidence` | A3+ | non-empty (string or object) |
| `constraints` | never — **explicitly optional** | type-checked only when present (string, list, or object) |

Below A2 the tier fields are optional, with one exception that binds at EVERY assurance level:
a contract declaring `risk_class` `security` or `destructive` must declare
`required_verification_tier: "adversarial"` — the floor derivation does not relax below A2.

Fields not listed keep their version-1 rules (`criteria` / `acceptance_command` / `expected_signal`
non-empty; `rerunnable` present at A2+; `risk` ⇒ `negative_cases`; A3/A4 ⇒ `negative_cases` in every
contract).

## Evidence classes — non-code and mixed work

When the deliverable is not (only) executable code, "machine-checkable" fans out into five evidence
classes. A contract for such work names which classes it uses; each class establishes only what it can
establish, and no class substitutes for another.

| Class | What it is | What it establishes — and what it never can |
|---|---|---|
| **behavioral-machine** | a command that exercises the artifact's behavior (test run, executable example, renderer round-trip asserting semantics) | behavior under the exercised conditions — the strongest class wherever any runtime exists |
| **structural-artifact** | link checkers, format/schema validators, rendering checks, pattern searches | form only. A link checker never validates substance; a structural pass says nothing about whether the content is true |
| **source-grounded** | every load-bearing claim traced to a retrievable source, plus contradiction checks across sources | that claims are grounded and mutually consistent — not that the synthesis is complete or well-judged |
| **expert-judgment** | a designated reviewer judging against explicit disconfirming criteria written BEFORE the review | substance quality — valid only when the criteria predate the review and the reviewer records what would have failed the artifact |
| **human-authorization** | explicit human sign-off | permission for irreversible or outward-facing effects — never a substitute for any other class's evidence |

### Combination table — minimum classes by assurance tier

| Work / tier | Minimum evidence-class combination |
|---|---|
| docs / design, A0–A1 | structural-artifact (producer-run) |
| docs / design, A2+ | structural-artifact + expert-judgment (independent, per the item's `required_verification_tier`) |
| research, A0–A1 | source-grounded (producer-run spot checks) |
| research, A2 | structural-artifact + source-grounded + independent expert-judgment |
| research / docs, A3+ | the full A2 row, executed at the item's `required_verification_tier` |
| irreversible or outward-facing effects, any tier | the applicable row above + human-authorization |

Prose-only acceptance ("reads well", "covers the topic") remains **never Tier-1** and never sufficient
on its own: it is expert-judgment with no disconfirming criteria — which is to say, no evidence class
at all. Record every class's output as evidence.

## Exemplar — BAD vs GOOD (concurrency risk)

**BAD — prose-only lever (a wrong implementation still passes):**
```jsonc
{
  "criteria": "counter increments are atomic under concurrency",
  "acceptance_command": "python -c 'import counter'",   // smoke import — exercises nothing
  "expected_signal": "no error; atomicity verified",     // ATOMICITY LIVES ONLY IN PROSE
  "risk": "concurrency",                                 // never exercised => BLOCKER
  "negative_cases": []                                   // risk present, no negative case => invalid
}
```

**GOOD — runs a negative/regression assertion a wrong implementation fails:**
```jsonc
{
  "criteria": "200 parallel increments yield a final count of exactly 200",
  "acceptance_command": "node test/atomicity.test.js  # fires 200 parallel incrs, asserts final===200; exits non-zero on drift",
  "expected_signal": "(✓|PASS).*atomic increment under 200-way concurrency",
  "risk": "concurrency — command spawns real parallel writers, not a serial loop",
  "negative_cases": ["parallel writers with injected scheduling jitter still converge to exactly 200"]
}
```

The rule generalizes: when `risk` names a production-environment failure layer (concurrency,
trust-proxy, streaming/buffering, clock), the command must exercise **that layer** — a unit test one
layer down does not discharge it.

## Signal-anchoring footguns

- **The fail-line trap.** `grep -q '<test name>'` alone is a BUG — it matches a test runner's
  `✕ <test name>` FAIL line as readily as `✓ <test name>`. Anchor `expected_signal` to the pass
  marker: `grep -qE '(✓|PASS).*<test name>'`.
- **The pipe-discards-exit-code trap.** `command | tee log` reports `tee`'s success, not the test's —
  a failing test exits green. Capture `${PIPESTATUS[0]}` (or drop the pipe) so a failing test actually
  fails the gate.
- General principle: `expected_signal` must be a pattern that **cannot** appear in a failing run. If a
  fail line can print it, the signal is unanchored and the contract is broken.

## Validation

Structural completeness of contracts (non-empty `criteria` + `acceptance_command` + `expected_signal`;
`risk` ⇒ non-empty `negative_cases`; coverage; acyclic deps) is machine-checked by `tools/validate-plan`
against the plan's embedded `json agentfw-plan` block — see `policy/plan-critique.md` Layer 1. Whether
the command is STRONG enough to exercise the lever is a Layer-2 judge question; the validator cannot
answer it.
# Plan-Critique Gate — two layers

**WHY:** the plan is the highest-leverage artifact — every worker and judge inherits its quality, yet
nothing verifies it before dispatch. A runtime will happily dispatch an unjudged plan; this policy will
not. The gate splits into a deterministic layer (cheap, mechanical, always runnable) and a semantic
layer (a judge, engaged proportionally).

**WHEN:** Layer 1 runs on every plan that carries a machine-readable block — it costs one command.
Layer 2 fires for **A2+ plans, destructive plans, architectural ambiguity, or shared derived values**
(two tasks depending on the same computed fact). A0/A1 trivial plans SKIP Layer 2 — judging a one-line
plan is Complexity Accumulation; skipping requires naming the relaxation, silence is not one.

**WHAT:** Layer 1 = `tools/validate-plan` over the plan's embedded block; Layer 2 = an independent
judge context driving the C0–C5 rubric over the plan.

## Layer 1 — deterministic validation (`tools/validate-plan`)

The plan embeds exactly one fenced block opening with ```` ```json agentfw-plan ```` and closing with
```` ``` ````. The validator (stdlib-only, exit-code honest) mechanically checks:

1. The block parses as valid JSON with no duplicate object keys at any level (last-wins duplicate
   keys are rejected as silently-accepted ambiguity), and `version` is present and — in default
   mode — exactly `"1.1"`: **schema 1.1 is mandatory**. A `"version": "1"` block is rejected as a
   legacy schema version; unknown version strings are rejected naming the version. The `--legacy`
   flag accepts `"version": "1"` blocks under the ORIGINAL v1 rules (rules 2–10 below; none of
   rule 11's 1.1 fields are required — the task-id precheck still applies in every mode, being a
   validator correctness fix rather than a schema rule) — a provenance boundary for re-checking
   plans authored before the 1.1 schema, never a license to author new v1 plans.
2. `assurance` is present and one of A0–A4.
3. **Substance:** A2+ plans ⇒ `requirements` and `tasks` lists are non-empty (an assured plan
   cannot be empty of either).
4. **Record shape:** every requirement record carries a non-empty `id` and `text`.
4b. **Task-id precheck:** EVERY task carries a non-empty string `id`, checked BEFORE the
   coverage, dependency, and cycle validations below — a missing/empty task id is its own
   defect (keyword `empty`) naming the task index, never a downstream error or a silent skip.
5. **Identity:** requirement ids are unique; task ids are unique.
6. **Coverage:** every requirement id is covered by ≥1 task's `requirement_ids`, and every
   `requirement_ids` entry names a DECLARED requirement (no phantom references).
7. **Contracts:** every task carries a contract with non-empty `criteria` + `acceptance_command` +
   `expected_signal`; A2+ plans ⇒ every contract also carries the `rerunnable` field.
8. **Dependencies:** `deps` reference existing task ids and are acyclic (real cycle detection).
9. **Risk discipline:** `risk` present ⇒ `negative_cases` non-empty.
10. **Assurance discipline:** A3/A4 plans ⇒ EVERY contract has non-empty `negative_cases`.
11. **Schema 1.1 structured tier derivation:** per contract at A2+ — `integration_seam` (a JSON
    boolean) and `risk_class` (∈ `none` | `standard` | `security` | `destructive`) are REQUIRED
    structured derivation inputs; `required_verification_tier` present, ∈ `producer` |
    `independent` | `adversarial`, and ≥ the MECHANICALLY DERIVED minimum tier
    (`producer` < `independent` < `adversarial`): base floor by assurance — A2 ⇒ `producer`,
    A3 ⇒ `independent`, A4 ⇒ `adversarial`; `integration_seam: true` AND assurance A2 ⇒ floor
    `independent`; `risk_class` `security`/`destructive` ⇒ floor `adversarial` at EVERY
    assurance level (enforced even below A2 whenever the field is present). Free-form `risk`
    prose NEVER enters the derivation. Also per contract at A2+ — non-empty `environment`
    string; `rerunnable` is a JSON boolean (a quoted `"true"` is a type defect). Per contract
    at A3+ — non-empty `evidence` (string or object). `constraints` is explicitly optional,
    type-checked only when present. Field semantics, the mandatory-by-tier table, and the
    derivation table: `policy/acceptance-contract.md`.

Exit 0 + `PASS` on success; on any failure, non-zero exit with messages naming the offending
task/requirement id and defect class. All defects are reported, not just the first.

**Defect-keyword contract (stable, grep-able):** every failure message carries exactly one of the
defect-class keywords `contract`, `cover`, `cycl`, `negative`, `assurance`, `empty`, `duplicate`,
`tier`, `version` (`tier` covers every tier-derivation defect — a missing/invalid
`required_verification_tier`, a missing/invalid `integration_seam` or `risk_class` derivation
input, or a declared tier below the mechanically derived floor; `empty` includes the task-id
precheck; `version` covers legacy-`"1"` and unknown-version rejections, the legacy message also
naming `--legacy`). Harness code and fixtures key on these words; changing them is a breaking
schema change to this file, the schema of record.

**Honest limit (Layer 1):** the validator verifies **structure and coverage** — that a discriminating
command EXISTS for every requirement and the plan graph is sound. It **cannot judge command STRENGTH**:
whether the `acceptance_command` truly exercises the lever the `risk` names, or merely exits green
around it. That is Layer 2's job. A Layer-1 PASS raises the floor; it green-lights nothing semantically.

**Temporal split:** at plan time the `acceptance_command` is read as a spec — it need not run green on
a greenfield tree. At verification time it must run, and be re-run by the independent judge.

## Layer 2 — semantic judge (C0–C5 rubric)

**Input-curation (bright line):** the judge receives the **plan + requirements ONLY** — never the
planner's exploration reasoning, never a sibling judge's verdict. Contaminated input produces a judge
that confirms intent instead of checking reality.

Each check with its one-line pass test:

- **C0 Substrate-grounding** — every quantitative/existence claim (a size, a count, "branch exists",
  "file present") is verified against the live substrate. *Pass:* each such claim cites a command run
  against reality, not an assertion.
- **C1 Independence** — tasks sit at real seams. *Pass:* no task secretly bundles two deliverables;
  each could be dispatched alone.
- **C2 Acceptance contract — prose-vs-mechanical (core check)** — the discriminating lever is
  REACHABLE by the `acceptance_command`, not just asserted in `expected_signal` prose. *Pass:* a wrong
  implementation makes the command exit non-zero, and the command exercises the layer the `risk` names
  (concurrency, trust-proxy, streaming/buffering, clock ⇒ blocker if unexercised). Tier-1 lever = ≥1
  negative/regression assertion the command RUNS; Tier-2 = ≥1 disconfirming criterion.
- **C3 Dependencies + cross-task consistency** — deps stated/acyclic; shared derived values
  reconciled. *Pass:* a shared value is a shared imported artifact (identity asserted) or an in-task
  consistency assertion — UNLESS some task (including an integration task) genuinely exercises the seam.
- **C4 Risk/role + (destructive plans) irreversible-op pre-mortem** — risk/blast-radius/assumptions
  surfaced; role separation mapped; harness proportional. *Pass:* destructive steps carry a complete
  inventory of everything touched + each item's post-op state, verify-on-mirror-before-live, and
  rollback *restorability* (not just backup integrity).
- **C5 Approach-fit (EVERY task)** — acceptance encodes a discriminating fixture, not a
  noun-restatement of the requirement. *Pass:* each task's acceptance asserts the *behavior* the
  requirement specifies; extra scrutiny where the task's own `risk` names an ambiguity. A C5 "concern"
  severity STILL feeds the overall verdict.
- **Coverage/completeness** — build the requirement→task matrix: map every requirement component to
  the task + `acceptance_command` that mechanically verifies it. *Pass:* no component is verified
  nowhere (the mocked-here-skipped-there hole). Plus per task: "can a wrong implementation still pass
  this acceptance_command?"

## Compose / stop policy

- **Judge count:** ONE judge by default (a deliberate leanness/independence trade). TWO independent
  judges with disjoint inputs for **A3+/destructive** plans.
- **Single-judge blocker:** one confirming independent pass before any re-plan — never re-plan off a
  single unconfirmed verdict.
- **Hard 2-pass cap.** Cap reached with an open blocker ≠ proceed → **escalate to the human**. Never
  auto-dispatch past an open blocker.
- **Do NOT trust a model-judged convergence signal.** Empirically, later passes each caught a real,
  distinct defect while the model's own "would another pass help?" said no every time — a fixed cap is
  better-calibrated than loop-until-clean. Never a numeric score (invites plan-polishing). Beyond pass
  2 clean = plan-polishing.
- **Disposition by check:** a C5 goal-vs-proof contradiction ⇒ **restart** the plan; C2/C3 defects ⇒
  **local revise**. A check rated "clean" cannot coexist with a real defect mapped to it.

## Honest limit (whole gate)

A clean verdict RAISES THE FLOOR on plan structure + verifiability. It does not machine-check command
strength beyond a judge's reading, and it does not verify correctness of the eventual work — the
downstream independent verification tier (see `policy/acceptance-contract.md`) still owns that.

**Contract-bounded verification has a ceiling.** Acceptance contracts bound what verification sees:
a verifier that only re-executes the contracts inherits every blind spot the plan author had.
Verifiers must therefore additionally attempt **off-contract hostile probes** — empty inputs,
duplicate inputs, hostile/seeded user content, bypass paths the contracts never anticipated — and
report them alongside the contract re-runs. This is an empirical lesson, not a hypothetical: the two
probes that broke this framework's own first build (an empty assured plan that PASSed validation, and
a phantom requirement reference that PASSed coverage) were both off-contract.

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '1,220p' .agents/skills/agentfw/policy/acceptance-contract.md && sed -n '1,260p' .agents/skills/agentfw/policy/plan-critique.md && sed -n '120,320p' .agents/skills/agentfw/policy/capability-contract.md && codex review --help" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
 succeeded in 0ms:
# Acceptance Contract v2

**WHY:** the acceptance contract is the load-bearing artifact of verification. It is authored at plan
time, hardened by the Plan-Critique Gate (`policy/plan-critique.md`), copied verbatim into the worker
dispatch, and — at the tiers that require it — RE-EXECUTED by an independent judge after the work
lands. The producer's recorded check output is evidence to re-execute, not proof to accept. A contract
whose discriminating lever lives only in prose verifies nothing — a wrong implementation passes it.

## Fields — one-line semantics

| Field | Semantics |
|---|---|
| `requirement_ids[]` | The requirement ids this task discharges; every requirement must be covered by ≥1 task's list. |
| `criteria` | What "correct" means for this task, in behavioral terms — not a restatement of the requirement's nouns. |
| `acceptance_command` | A command RE-RUNNABLE at verification time that exercises the discriminating lever; a wrong implementation makes it exit non-zero. |
| `environment` | Where the evidence is valid (which host/sandbox/config); evidence produced elsewhere does not transfer. |
| `expected_signal` | The exact output/exit pattern that means PASS — anchored so it cannot also match a fail line (see footguns below). |
| `negative_cases[]` | Disconfirming assertions the command runs — inputs/states that a wrong implementation would mishandle. **REQUIRED whenever `risk` is present.** |
| `risk` | The failure this task must not ship — name the layer (concurrency, trust-proxy, streaming/buffering, clock, data loss); the command must exercise THAT layer. |
| `evidence` | Artifact types the check records (test log, build output, diff, rendered page) + **freshness: `produced_after_change`** — evidence older than the change it claims to verify is void. |
| `rerunnable` | Boolean — the check can be executed again, from the tree, by a context that did not produce the work. Non-rerunnable evidence is testimony. |
| `constraints` | Runtime/network/side-effect bounds the check must respect (e.g. no network, sandbox only, read-only on the live store). |
| `integration_seam` | JSON **boolean** — does this task sit on an integration seam (its correctness is only observable where two components meet)? A structured tier-derivation input; the free-form `risk` prose never substitutes for it. |
| `risk_class` | One of `none` \| `standard` \| `security` \| `destructive` — the structured classification of the work's blast radius. `security`/`destructive` mechanically floors the tier at `adversarial` regardless of assurance. |
| `required_verification_tier` | Who must re-execute the check before the terminal verified state is reached — field value `producer` \| `independent` \| `adversarial`, selecting the terminal state `verified_producer` / `verified_independent` / `verified_adversarial`. Must be ≥ the floor MECHANICALLY DERIVED from assurance + `integration_seam` + `risk_class` (derivation table below). |

## Tier-1 definition

**Tier-1 = the `acceptance_command` RUNS ≥1 negative/regression assertion.** Not "could", not
"describes" — runs. A bare smoke import (`python -c 'import counter'`) is **never** Tier-1: it exercises
nothing and a wrong implementation passes it. A test invocation whose discriminator sits behind a
skipped/disabled test is equally void — a green run proves nothing when the assertion never executed.
Tier-2 (weaker, for when Tier-1 is genuinely unreachable) = the contract carries ≥1 explicit
disconfirming criterion an independent reviewer checks against the artifact.

A work item CANNOT reach its terminal verified state without recorded machine-check output from the
`acceptance_command`, fresh per `produced_after_change`. **Who** must have executed that run before
the terminal state is reached is fixed by `required_verification_tier` — see the next section.

## Verification tiers — terminal states

`verified` is not one state; it is three. Which one is terminal for a work item is fixed at plan time
by `required_verification_tier`:

| Terminal state | Who re-executes the `acceptance_command` | Sufficient terminal state for |
|---|---|---|
| `verified_producer` | the producing context — recorded machine-check output from the producer, fresh per `produced_after_change` | A0 and A1 work — this is the terminal state, not a waypoint |
| `verified_independent` | an independent, input-curated judge re-executes the `acceptance_command` | A2 integration seams; all A3+ |
| `verified_adversarial` | an independent judge, plus deliberate refutation attempts and probes beyond what the contract anticipated | A4; security/destructive work at any level |

**Producer evidence remains evidence at every tier.** Every producer runs its own checks and records
the output, fresh per `produced_after_change`, at every assurance level. What changes across tiers is
not whether that evidence exists but **who must re-execute the `acceptance_command` before the
terminal state is reached**: at `verified_producer` the producer's own recorded run *is* the verdict
of record; at the higher tiers it is input handed to a judge who runs the command again — evidence to
re-execute, not proof to accept.

### `required_verification_tier` — mechanical floor derivation

The minimum tier is DERIVED from structured fields only — the plan-level `assurance` plus the
per-contract `integration_seam` and `risk_class`. Free-form `risk` prose never enters the
derivation. `tools/validate-plan` enforces the floor mechanically: with the tier order
`producer` < `independent` < `adversarial`, the declared `required_verification_tier` must be
≥ the derived floor.

| Derivation input | Effect on the minimum tier |
|---|---|
| assurance A0 / A1 | base floor `producer` (tier fields optional below A2) |
| assurance A2 | base floor `producer` |
| assurance A3 | base floor `independent` |
| assurance A4 | base floor `adversarial` |
| `integration_seam: true` AND assurance A2 | floor raised to `independent` |
| `risk_class: "security"` or `"destructive"` | floor raised to `adversarial` — at EVERY assurance level |

Selecting a floor tier's terminal state: `producer` → `verified_producer`, `independent` →
`verified_independent`, `adversarial` → `verified_adversarial`.

**Spelling reconciliation (field values vs terminal-state names).** In the plan block, the
`required_verification_tier` FIELD takes the short values `producer` | `independent` | `adversarial`;
each selects the corresponding terminal STATE `verified_producer` / `verified_independent` /
`verified_adversarial`. The `verified_*` spellings name states an item *reaches* — they are **not**
valid field values, and the validator rejects them; write `independent`, never `verified_independent`,
in the field.

## Block versioning — `"version": "1.1"` is MANDATORY; `"version": "1"` is legacy-only

The plan's embedded machine-readable block declares a schema `version`. Schema `"1.1"` is
**mandatory**: default validation REQUIRES `"version": "1.1"` and rejects a `"version": "1"`
block as a legacy schema version. Version `"1"` exists for HISTORICAL PROVENANCE ONLY —
re-checking plans authored before the 1.1 schema — and is accepted solely under
`tools/validate-plan --legacy`, which applies the original v1 rules. Never author a new plan
against v1. Unknown version strings are rejected naming the version.

Blocks declaring `"version": "1.1"` are additionally held, per contract, to the
mandatory-by-tier field table below (machine-enforced by `tools/validate-plan`):

| Field (1.1) | Mandatory at | Rule |
|---|---|---|
| `integration_seam` | A2+ | a JSON **boolean** — structured tier-derivation input |
| `risk_class` | A2+ | ∈ `none` \| `standard` \| `security` \| `destructive` — structured tier-derivation input |
| `required_verification_tier` | A2+ | present; ∈ `producer` \| `independent` \| `adversarial`; ≥ the floor mechanically derived from assurance + `integration_seam` + `risk_class` (derivation table above) |
| `environment` | A2+ | non-empty string |
| `rerunnable` | A2+ | a JSON **boolean** — the quoted string `"true"` is a type defect, not a value |
| `evidence` | A3+ | non-empty (string or object) |
| `constraints` | never — **explicitly optional** | type-checked only when present (string, list, or object) |

Below A2 the tier fields are optional, with one exception that binds at EVERY assurance level:
a contract declaring `risk_class` `security` or `destructive` must declare
`required_verification_tier: "adversarial"` — the floor derivation does not relax below A2.

Fields not listed keep their version-1 rules (`criteria` / `acceptance_command` / `expected_signal`
non-empty; `rerunnable` present at A2+; `risk` ⇒ `negative_cases`; A3/A4 ⇒ `negative_cases` in every
contract).

## Evidence classes — non-code and mixed work

When the deliverable is not (only) executable code, "machine-checkable" fans out into five evidence
classes. A contract for such work names which classes it uses; each class establishes only what it can
establish, and no class substitutes for another.

| Class | What it is | What it establishes — and what it never can |
|---|---|---|
| **behavioral-machine** | a command that exercises the artifact's behavior (test run, executable example, renderer round-trip asserting semantics) | behavior under the exercised conditions — the strongest class wherever any runtime exists |
| **structural-artifact** | link checkers, format/schema validators, rendering checks, pattern searches | form only. A link checker never validates substance; a structural pass says nothing about whether the content is true |
| **source-grounded** | every load-bearing claim traced to a retrievable source, plus contradiction checks across sources | that claims are grounded and mutually consistent — not that the synthesis is complete or well-judged |
| **expert-judgment** | a designated reviewer judging against explicit disconfirming criteria written BEFORE the review | substance quality — valid only when the criteria predate the review and the reviewer records what would have failed the artifact |
| **human-authorization** | explicit human sign-off | permission for irreversible or outward-facing effects — never a substitute for any other class's evidence |

### Combination table — minimum classes by assurance tier

| Work / tier | Minimum evidence-class combination |
|---|---|
| docs / design, A0–A1 | structural-artifact (producer-run) |
| docs / design, A2+ | structural-artifact + expert-judgment (independent, per the item's `required_verification_tier`) |
| research, A0–A1 | source-grounded (producer-run spot checks) |
| research, A2 | structural-artifact + source-grounded + independent expert-judgment |
| research / docs, A3+ | the full A2 row, executed at the item's `required_verification_tier` |
| irreversible or outward-facing effects, any tier | the applicable row above + human-authorization |

Prose-only acceptance ("reads well", "covers the topic") remains **never Tier-1** and never sufficient
on its own: it is expert-judgment with no disconfirming criteria — which is to say, no evidence class
at all. Record every class's output as evidence.

## Exemplar — BAD vs GOOD (concurrency risk)

**BAD — prose-only lever (a wrong implementation still passes):**
```jsonc
{
  "criteria": "counter increments are atomic under concurrency",
  "acceptance_command": "python -c 'import counter'",   // smoke import — exercises nothing
  "expected_signal": "no error; atomicity verified",     // ATOMICITY LIVES ONLY IN PROSE
  "risk": "concurrency",                                 // never exercised => BLOCKER
  "negative_cases": []                                   // risk present, no negative case => invalid
}
```

**GOOD — runs a negative/regression assertion a wrong implementation fails:**
```jsonc
{
  "criteria": "200 parallel increments yield a final count of exactly 200",
  "acceptance_command": "node test/atomicity.test.js  # fires 200 parallel incrs, asserts final===200; exits non-zero on drift",
  "expected_signal": "(✓|PASS).*atomic increment under 200-way concurrency",
  "risk": "concurrency — command spawns real parallel writers, not a serial loop",
  "negative_cases": ["parallel writers with injected scheduling jitter still converge to exactly 200"]
}
```

The rule generalizes: when `risk` names a production-environment failure layer (concurrency,
trust-proxy, streaming/buffering, clock), the command must exercise **that layer** — a unit test one
layer down does not discharge it.

## Signal-anchoring footguns

- **The fail-line trap.** `grep -q '<test name>'` alone is a BUG — it matches a test runner's
  `✕ <test name>` FAIL line as readily as `✓ <test name>`. Anchor `expected_signal` to the pass
  marker: `grep -qE '(✓|PASS).*<test name>'`.
- **The pipe-discards-exit-code trap.** `command | tee log` reports `tee`'s success, not the test's —
  a failing test exits green. Capture `${PIPESTATUS[0]}` (or drop the pipe) so a failing test actually
  fails the gate.
- General principle: `expected_signal` must be a pattern that **cannot** appear in a failing run. If a
  fail line can print it, the signal is unanchored and the contract is broken.

## Validation

Structural completeness of contracts (non-empty `criteria` + `acceptance_command` + `expected_signal`;
`risk` ⇒ non-empty `negative_cases`; coverage; acyclic deps) is machine-checked by `tools/validate-plan`
against the plan's embedded `json agentfw-plan` block — see `policy/plan-critique.md` Layer 1. Whether
the command is STRONG enough to exercise the lever is a Layer-2 judge question; the validator cannot
answer it.
# Plan-Critique Gate — two layers

**WHY:** the plan is the highest-leverage artifact — every worker and judge inherits its quality, yet
nothing verifies it before dispatch. A runtime will happily dispatch an unjudged plan; this policy will
not. The gate splits into a deterministic layer (cheap, mechanical, always runnable) and a semantic
layer (a judge, engaged proportionally).

**WHEN:** Layer 1 runs on every plan that carries a machine-readable block — it costs one command.
Layer 2 fires for **A2+ plans, destructive plans, architectural ambiguity, or shared derived values**
(two tasks depending on the same computed fact). A0/A1 trivial plans SKIP Layer 2 — judging a one-line
plan is Complexity Accumulation; skipping requires naming the relaxation, silence is not one.

**WHAT:** Layer 1 = `tools/validate-plan` over the plan's embedded block; Layer 2 = an independent
judge context driving the C0–C5 rubric over the plan.

## Layer 1 — deterministic validation (`tools/validate-plan`)

The plan embeds exactly one fenced block opening with ```` ```json agentfw-plan ```` and closing with
```` ``` ````. The validator (stdlib-only, exit-code honest) mechanically checks:

1. The block parses as valid JSON with no duplicate object keys at any level (last-wins duplicate
   keys are rejected as silently-accepted ambiguity), and `version` is present and — in default
   mode — exactly `"1.1"`: **schema 1.1 is mandatory**. A `"version": "1"` block is rejected as a
   legacy schema version; unknown version strings are rejected naming the version. The `--legacy`
   flag accepts `"version": "1"` blocks under the ORIGINAL v1 rules (rules 2–10 below; none of
   rule 11's 1.1 fields are required — the task-id precheck still applies in every mode, being a
   validator correctness fix rather than a schema rule) — a provenance boundary for re-checking
   plans authored before the 1.1 schema, never a license to author new v1 plans.
2. `assurance` is present and one of A0–A4.
3. **Substance:** A2+ plans ⇒ `requirements` and `tasks` lists are non-empty (an assured plan
   cannot be empty of either).
4. **Record shape:** every requirement record carries a non-empty `id` and `text`.
4b. **Task-id precheck:** EVERY task carries a non-empty string `id`, checked BEFORE the
   coverage, dependency, and cycle validations below — a missing/empty task id is its own
   defect (keyword `empty`) naming the task index, never a downstream error or a silent skip.
5. **Identity:** requirement ids are unique; task ids are unique.
6. **Coverage:** every requirement id is covered by ≥1 task's `requirement_ids`, and every
   `requirement_ids` entry names a DECLARED requirement (no phantom references).
7. **Contracts:** every task carries a contract with non-empty `criteria` + `acceptance_command` +
   `expected_signal`; A2+ plans ⇒ every contract also carries the `rerunnable` field.
8. **Dependencies:** `deps` reference existing task ids and are acyclic (real cycle detection).
9. **Risk discipline:** `risk` present ⇒ `negative_cases` non-empty.
10. **Assurance discipline:** A3/A4 plans ⇒ EVERY contract has non-empty `negative_cases`.
11. **Schema 1.1 structured tier derivation:** per contract at A2+ — `integration_seam` (a JSON
    boolean) and `risk_class` (∈ `none` | `standard` | `security` | `destructive`) are REQUIRED
    structured derivation inputs; `required_verification_tier` present, ∈ `producer` |
    `independent` | `adversarial`, and ≥ the MECHANICALLY DERIVED minimum tier
    (`producer` < `independent` < `adversarial`): base floor by assurance — A2 ⇒ `producer`,
    A3 ⇒ `independent`, A4 ⇒ `adversarial`; `integration_seam: true` AND assurance A2 ⇒ floor
    `independent`; `risk_class` `security`/`destructive` ⇒ floor `adversarial` at EVERY
    assurance level (enforced even below A2 whenever the field is present). Free-form `risk`
    prose NEVER enters the derivation. Also per contract at A2+ — non-empty `environment`
    string; `rerunnable` is a JSON boolean (a quoted `"true"` is a type defect). Per contract
    at A3+ — non-empty `evidence` (string or object). `constraints` is explicitly optional,
    type-checked only when present. Field semantics, the mandatory-by-tier table, and the
    derivation table: `policy/acceptance-contract.md`.

Exit 0 + `PASS` on success; on any failure, non-zero exit with messages naming the offending
task/requirement id and defect class. All defects are reported, not just the first.

**Defect-keyword contract (stable, grep-able):** every failure message carries exactly one of the
defect-class keywords `contract`, `cover`, `cycl`, `negative`, `assurance`, `empty`, `duplicate`,
`tier`, `version` (`tier` covers every tier-derivation defect — a missing/invalid
`required_verification_tier`, a missing/invalid `integration_seam` or `risk_class` derivation
input, or a declared tier below the mechanically derived floor; `empty` includes the task-id
precheck; `version` covers legacy-`"1"` and unknown-version rejections, the legacy message also
naming `--legacy`). Harness code and fixtures key on these words; changing them is a breaking
schema change to this file, the schema of record.

**Honest limit (Layer 1):** the validator verifies **structure and coverage** — that a discriminating
command EXISTS for every requirement and the plan graph is sound. It **cannot judge command STRENGTH**:
whether the `acceptance_command` truly exercises the lever the `risk` names, or merely exits green
around it. That is Layer 2's job. A Layer-1 PASS raises the floor; it green-lights nothing semantically.

**Temporal split:** at plan time the `acceptance_command` is read as a spec — it need not run green on
a greenfield tree. At verification time it must run, and be re-run by the independent judge.

## Layer 2 — semantic judge (C0–C5 rubric)

**Input-curation (bright line):** the judge receives the **plan + requirements ONLY** — never the
planner's exploration reasoning, never a sibling judge's verdict. Contaminated input produces a judge
that confirms intent instead of checking reality.

Each check with its one-line pass test:

- **C0 Substrate-grounding** — every quantitative/existence claim (a size, a count, "branch exists",
  "file present") is verified against the live substrate. *Pass:* each such claim cites a command run
  against reality, not an assertion.
- **C1 Independence** — tasks sit at real seams. *Pass:* no task secretly bundles two deliverables;
  each could be dispatched alone.
- **C2 Acceptance contract — prose-vs-mechanical (core check)** — the discriminating lever is
  REACHABLE by the `acceptance_command`, not just asserted in `expected_signal` prose. *Pass:* a wrong
  implementation makes the command exit non-zero, and the command exercises the layer the `risk` names
  (concurrency, trust-proxy, streaming/buffering, clock ⇒ blocker if unexercised). Tier-1 lever = ≥1
  negative/regression assertion the command RUNS; Tier-2 = ≥1 disconfirming criterion.
- **C3 Dependencies + cross-task consistency** — deps stated/acyclic; shared derived values
  reconciled. *Pass:* a shared value is a shared imported artifact (identity asserted) or an in-task
  consistency assertion — UNLESS some task (including an integration task) genuinely exercises the seam.
- **C4 Risk/role + (destructive plans) irreversible-op pre-mortem** — risk/blast-radius/assumptions
  surfaced; role separation mapped; harness proportional. *Pass:* destructive steps carry a complete
  inventory of everything touched + each item's post-op state, verify-on-mirror-before-live, and
  rollback *restorability* (not just backup integrity).
- **C5 Approach-fit (EVERY task)** — acceptance encodes a discriminating fixture, not a
  noun-restatement of the requirement. *Pass:* each task's acceptance asserts the *behavior* the
  requirement specifies; extra scrutiny where the task's own `risk` names an ambiguity. A C5 "concern"
  severity STILL feeds the overall verdict.
- **Coverage/completeness** — build the requirement→task matrix: map every requirement component to
  the task + `acceptance_command` that mechanically verifies it. *Pass:* no component is verified
  nowhere (the mocked-here-skipped-there hole). Plus per task: "can a wrong implementation still pass
  this acceptance_command?"

## Compose / stop policy

- **Judge count:** ONE judge by default (a deliberate leanness/independence trade). TWO independent
  judges with disjoint inputs for **A3+/destructive** plans.
- **Single-judge blocker:** one confirming independent pass before any re-plan — never re-plan off a
  single unconfirmed verdict.
- **Hard 2-pass cap.** Cap reached with an open blocker ≠ proceed → **escalate to the human**. Never
  auto-dispatch past an open blocker.
- **Do NOT trust a model-judged convergence signal.** Empirically, later passes each caught a real,
  distinct defect while the model's own "would another pass help?" said no every time — a fixed cap is
  better-calibrated than loop-until-clean. Never a numeric score (invites plan-polishing). Beyond pass
  2 clean = plan-polishing.
- **Disposition by check:** a C5 goal-vs-proof contradiction ⇒ **restart** the plan; C2/C3 defects ⇒
  **local revise**. A check rated "clean" cannot coexist with a real defect mapped to it.

## Honest limit (whole gate)

A clean verdict RAISES THE FLOOR on plan structure + verifiability. It does not machine-check command
strength beyond a judge's reading, and it does not verify correctness of the eventual work — the
downstream independent verification tier (see `policy/acceptance-contract.md`) still owns that.

**Contract-bounded verification has a ceiling.** Acceptance contracts bound what verification sees:
a verifier that only re-executes the contracts inherits every blind spot the plan author had.
Verifiers must therefore additionally attempt **off-contract hostile probes** — empty inputs,
duplicate inputs, hostile/seeded user content, bypass paths the contracts never anticipated — and
report them alongside the contract re-runs. This is an empirical lesson, not a hypothetical: the two
probes that broke this framework's own first build (an empty assured plan that PASSed validation, and
a phantom requirement reference that PASSed coverage) were both off-contract.
- Guided profiles (`profiles/chatgpt-projects.md`, `profiles/claude-projects.md`) are **not adapters**: they
  document runtimes where so many capabilities are absent that the policy operates as a guided,
  human-in-the-loop discipline. They declare their non-enforcement honestly rather than shipping a
  capability instance that would be mostly `false`.
WARNING: proceeding, even though we could not create PATH aliases: Operation not permitted (os error 1)
Run a code review non-interactively

Usage: codex review [OPTIONS] [PROMPT]

Arguments:
  [PROMPT]
          Custom review instructions. If `-` is used, read from stdin

Options:
  -c, --config <key=value>
          Override a configuration value that would otherwise be loaded from `~/.codex/config.toml`.
          Use a dotted path (`foo.bar.baz`) to override nested values. The `value` portion is parsed
          as TOML. If it fails to parse as TOML, the raw string is used as a literal.
          
          Examples: - `-c model="o3"` - `-c 'sandbox_permissions=["disk-full-read-access"]'` - `-c
          shell_environment_policy.inherit=all`

      --strict-config
          Error out when config.toml contains fields that are not recognized by this version of
          Codex

      --enable <FEATURE>
          Enable a feature (repeatable). Equivalent to `-c features.<name>=true`

      --uncommitted
          Review staged, unstaged, and untracked changes

      --base <BRANCH>
          Review changes against the given base branch

      --disable <FEATURE>
          Disable a feature (repeatable). Equivalent to `-c features.<name>=false`

      --commit <SHA>
          Review the changes introduced by a commit

      --title <TITLE>
          Optional commit title to display in the review summary

  -h, --help
          Print help (see a summary with '-h')

hook: PostToolUse
hook: PostToolUse Completed
codex
The activation probe succeeded: the installed CLI exposes a non-mutating `codex review` command, so independent review can be activated after the change. The in-session isolated-worker capability remains unavailable; I’ll test the policy’s permitted fresh-session fallback for plan critique/implementation, and if that cannot run I’ll stop at the human-review boundary rather than silently collapsing roles.

I’m now inventorying the application, session configuration, proxy assumptions, tests, and repository state before drafting the A3 contract.
hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "pwd && git status --short && rg --files -g '"'!node_modules'"' -g '"'!vendor'"' | sed -n '1,240p' && rg -n \"session|cookie|proxy|trust proxy|secure|sameSite|maxAge|expires|X-Forwarded|forwarded\" -g '"'!node_modules'"' -g '"'!vendor'"' ." in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
 succeeded in 0ms:
/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
?? .agents/
?? AGENTS.md
AGENTS.md
./AGENTS.md:10:  (integration seams; production-only behavior: concurrency, trust-proxy, streaming, clock)?

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "find . -maxdepth 3 -type f -not -path './.git/*' -print | sort && git log --oneline --decorate -8 && git branch --show-current && git ls-tree -r --name-only HEAD | sed -n '1,240p'" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H
 exited 128 in 0ms:
./AGENTS.md
fatal: your current branch 'main' does not have any commits yet

hook: PostToolUse
hook: PostToolUse Completed
codex
I can’t diagnose or fix this yet because the supplied workspace contains no application code or configuration:

- Git branch `main` has no commits.
- The only project file is `AGENTS.md`.
- No session, proxy, deployment, manifest, or test files exist.
- No files were changed.

Please populate this workspace with the application repository, or provide the correct workspace path. Include the reverse-proxy configuration if it lives outside the repository. Once available, I’ll reproduce the forwarded-protocol/session-expiry behavior, implement the fix, and run producer plus independent review checks.
hook: Stop
hook: Stop Completed
tokens used
34,532
I can’t diagnose or fix this yet because the supplied workspace contains no application code or configuration:

- Git branch `main` has no commits.
- The only project file is `AGENTS.md`.
- No session, proxy, deployment, manifest, or test files exist.
- No files were changed.

Please populate this workspace with the application repository, or provide the correct workspace path. Include the reverse-proxy configuration if it lives outside the repository. Once available, I’ll reproduce the forwarded-protocol/session-expiry behavior, implement the fix, and run producer plus independent review checks.

session_id: 019f5ca2-9377-7550-9b1e-2a2b43327938
