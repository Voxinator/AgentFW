<!-- sanitized 2026-07-13: removed 62 MCP-connection error lines (disclosed connected services), redacted home path -->
Reading additional input from stdin...
OpenAI Codex v0.144.1
--------
workdir: /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 019f5ca4-a0e0-74b1-b13c-390989839e52
--------
user
Build a user notification system with email, SMS, and in-app channels, plus a preference management API.
warning: Skill descriptions were shortened to fit the 2% skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.
hook: SessionStart
hook: SessionStart
hook: SessionStart
hook: SessionStart Completed
hook: SessionStart Completed
hook: SessionStart Completed
codex
[ASSURANCE: A2 — this spans multiple delivery channels, persistence, and API seams; changes are reversible, but defects could escape at provider/integration boundaries.]

I’m using the `agentfw` skill to decompose the work and independently verify the channel and preference seams. I’ll first map the existing project conventions, then implement and exercise the full flow.
hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '1,240p' .agents/skills/agentfw/SKILL.md" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
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
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/zsh -lc "cat .agents/skills/agentfw/capability.yaml && find . -maxdepth 3 -type f -not -path './.git/*' -print | sort | sed -n '1,240p'" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
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
./AGENTS.md

hook: PostToolUse
exec
/bin/zsh -lc 'git status --short && (test -f package.json && cat package.json || true) && (test -f pyproject.toml && cat pyproject.toml || true)' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
?? .agents/
?? AGENTS.md

hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
codex
The workspace is effectively empty, so there are no framework or data-model constraints to preserve. I’m going to build a dependency-free Node service with provider adapters, durable JSON persistence, idempotent dispatch, and a REST API; the default channel providers will be safe local recording adapters so tests never send real messages.
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/zsh -lc "test -f ~/.codex/config.toml && sed -n '1,160p' ~/.codex/config.toml || true" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
personality = "pragmatic"
approval_policy = "never"
sandbox_mode = "danger-full-access"

notify = ["/Users/USER/.codex/computer-use/Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient", "turn-ended", "--previous-notify", "[\"\\/bin\\/bash\",\"\\/Users\\/briantaylor\\/.codeagentswarm\\/hooks\\/codex-notify.sh\"]"]
model = "gpt-5.6-sol"
model_reasoning_effort = "high"

[projects."/Users/USER"]
trust_level = "trusted"

[projects."/private/tmp"]
trust_level = "trusted"

[projects."/Users/USER/Projects"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.9O3obD3tRZ"]
trust_level = "trusted"

[projects."/Users/USER/Projects/CNVS"]
trust_level = "trusted"

[projects."/Users/USER/dev/clicky-personal"]
trust_level = "trusted"

[projects."/Users/USER/Projects/drydock"]
trust_level = "trusted"

[projects."/Users/USER/Documents/Codex/2026-07-10/check-my-gmail"]
trust_level = "trusted"

[projects."/Users/USER/Documents/Codex/2026-07-10/che"]
trust_level = "trusted"

[projects."/Users/USER/Documents/Codex/2026-07-10/che-2"]
trust_level = "trusted"

[projects."/Users/USER/Projects/AgentFW"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.Bx7DRNofx8"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.aPtP4hK3Or"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.kYPbkVJZB2"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.5g7IY2Uj4f"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.uPOk1etZF6"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.PK2wNF0P8H"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.rWWJlahqlV"]
trust_level = "trusted"

[projects."/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ"]
trust_level = "trusted"

[mcp_servers.codeagentswarm-tasks]
command = "node"
args = ["/Users/USER/.codeagentswarm/mcp-servers/codeagentswarm-tasks/src/infrastructure/mcp/mcp-stdio-server.js"]
env_vars = ["CODEAGENTSWARM_ACTIVE_SESSION", "CODEAGENTSWARM_CURRENT_QUADRANT", "CODEAGENTSWARM_DB_PATH"]
startup_timeout_sec = 30.0
tool_timeout_sec = 120.0

[mcp_servers.codeagentswarm-tasks.env]
NODE_ENV = "production"
NODE_OPTIONS = "--unhandled-rejections=strict"

[mcp_servers.codeagentswarm-tasks.tools.check_active]
approval_mode = "approve"

[mcp_servers.unreal]
command = "npx"
args = ["-y", "@runreal/unreal-mcp"]
env_vars = ["CODEAGENTSWARM_ACTIVE_SESSION", "CODEAGENTSWARM_CURRENT_QUADRANT", "CODEAGENTSWARM_DB_PATH"]
startup_timeout_sec = 30.0
tool_timeout_sec = 120.0

[mcp_servers.unreal-claude]
command = "node"
args = ["/Users/USER/Projects/Brutalist/Brutalist/Plugins/UnrealClaude/Resources/mcp-bridge/index.js"]
env_vars = ["CODEAGENTSWARM_ACTIVE_SESSION", "CODEAGENTSWARM_CURRENT_QUADRANT", "CODEAGENTSWARM_DB_PATH"]
startup_timeout_sec = 30.0
tool_timeout_sec = 120.0

[mcp_servers.node_repl]
args = []
command = "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node_repl"
startup_timeout_sec = 120

[mcp_servers.node_repl.env]
NODE_REPL_NATIVE_PIPE_CONNECT_TIMEOUT_MS = "1000"
NODE_REPL_NODE_MODULE_DIRS = "/Applications/ChatGPT.app/Contents/Resources/cua_node/lib/node_modules"
NODE_REPL_NODE_PATH = "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node"
NODE_REPL_TRUSTED_CODE_PATHS = "/Users/USER/.codex"
CODEX_HOME = "/Users/USER/.codex"
NODE_REPL_TRUSTED_BROWSER_CLIENT_SHA256S = "1491199f46178eb038259aaea144492b8a8ade32bba5d2b4843c94936be551bb,6d25aa7656feac858f3a3bdaea5bcbab0dbfd426c9de8e6931ce90c399ee8e4f"
BROWSER_USE_AVAILABLE_BACKENDS = "chrome,iab"
NODE_REPL_INSTRUCTIONS_USE_CASE_BROWSER = "Control the in-app browser in conjunction with the Browser Plugin."
NODE_REPL_INSTRUCTIONS_USE_CASE_CHROME = "Control the Chrome browser in conjunction with the Chrome Plugin. Prefer this method of controlling Chrome over alternatives (such as Computer Use) unless the user explicitly mentions an alternative."
NODE_REPL_INSTRUCTIONS_USE_CASE_COMPUTER_USE = "Control desktop apps on macOS through Computer Use."
BROWSER_USE_CODEX_APP_BUILD_FLAVOR = "prod"
BROWSER_USE_CODEX_APP_VERSION = "26.707.41301"
SKY_CUA_SERVICE_PATH = "/Users/USER/.codex/plugins/cache/openai-bundled/computer-use/1.0.1000366/Codex Computer Use.app"
CODEX_CLI_PATH = "/Applications/ChatGPT.app/Contents/Resources/codex"

[mcp_servers.drydock]
command = "/Users/USER/Projects/drydock/app/MissionControl/dist/Drydock.app/Contents/Resources/drydock-mcp"

[mcp_servers.drydock.env]
DRYDOCK_PROJECTS_DIR = "/Users/USER/Projects"

[mcp_servers.drydock.tools.list_sessions]
approval_mode = "approve"

[mcp_servers.drydock.tools.send_to_session]
approval_mode = "approve"

[mcp_servers.computer-use]
command = "./Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
args = ["mcp"]
cwd = "."
enabled = false

[marketplaces.openai-bundled]
last_updated = "2026-07-11T00:20:55Z"
source_type = "local"
source = "/Users/USER/.codex/.tmp/bundled-marketplaces/openai-bundled"

[marketplaces.openai-primary-runtime]
last_updated = "2026-07-10T22:30:16Z"
source_type = "local"
source = "/Users/USER/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime"

[marketplaces.claude-plugins-official]
last_updated = "2026-07-13T17:24:35Z"
last_revision = "5ebce15d8a068db457fc1effe6e0e77175681c33"
source_type = "git"
source = "https://github.com/anthropics/claude-plugins-official.git"

[plugins."documents@openai-primary-runtime"]
enabled = true

[plugins."pdf@openai-primary-runtime"]
enabled = true

[plugins."spreadsheets@openai-primary-runtime"]
enabled = true

[plugins."presentations@openai-primary-runtime"]
enabled = true

hook: PostToolUse
hook: PostToolUse Completed
exec
/bin/zsh -lc 'node --version && npm --version && git log -1 --oneline 2>/dev/null || true' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
v25.8.2
11.11.1

hook: PostToolUse
hook: PostToolUse Completed
apply patch
patch: completed
/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/.agentfw-plan.md
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..ba94746617091a86869a0225dd481bfbe746d502
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,55 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides atomic JSON persistence, email/SMS/in-app adapters, preference defaults and overrides, idempotent dispatch, recipient validation, and inspectable delivery results.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated idempotency key returns the original notification without redelivery.", "Invalid email/SMS recipients are rejected before persistence or delivery."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable."
+      }
+    }
+  ]
+}
+```

hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..ba94746617091a86869a0225dd481bfbe746d502
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,55 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides atomic JSON persistence, email/SMS/in-app adapters, preference defaults and overrides, idempotent dispatch, recipient validation, and inspectable delivery results.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated idempotency key returns the original notification without redelivery.", "Invalid email/SMS recipients are rejected before persistence or delivery."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable."
+      }
+    }
+  ]
+}
+```

hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc 'python3 .agents/skills/agentfw/tools/validate-plan .agentfw-plan.md' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
PASS: .agentfw-plan.md — 5 requirements, 2 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)

hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..ba94746617091a86869a0225dd481bfbe746d502
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,55 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides atomic JSON persistence, email/SMS/in-app adapters, preference defaults and overrides, idempotent dispatch, recipient validation, and inspectable delivery results.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated idempotency key returns the original notification without redelivery.", "Invalid email/SMS recipients are rejected before persistence or delivery."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable."
+      }
+    }
+  ]
+}
+```

codex
The capability preflight confirms shell execution and isolated agents are available. The active session’s managed workspace restriction provides the filesystem boundary even though the user-level config file still says `danger-full-access`; I’m treating that config mismatch as a declared limitation and keeping all work inside this repository with no network delivery.

The mechanical plan gate passed. Because the API semantics are underspecified, I’m invoking the skill’s semantic plan critique before implementation.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..ba94746617091a86869a0225dd481bfbe746d502
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,55 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides atomic JSON persistence, email/SMS/in-app adapters, preference defaults and overrides, idempotent dispatch, recipient validation, and inspectable delivery results.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated idempotency key returns the original notification without redelivery.", "Invalid email/SMS recipients are rejected before persistence or delivery."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..ba94746617091a86869a0225dd481bfbe746d502
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,55 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides atomic JSON persistence, email/SMS/in-app adapters, preference defaults and overrides, idempotent dispatch, recipient validation, and inspectable delivery results.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated idempotency key returns the original notification without redelivery.", "Invalid email/SMS recipients are rejected before persistence or delivery."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable."
+      }
+    }
+  ]
+}
+```

codex
The plan critique is still running. The key contract is now explicit: global defaults are enabled, category-specific settings override them, omitted settings remain unchanged, duplicate requests never redeliver, and user-scoped reads deliberately return `404` for both missing and foreign resources.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..ba94746617091a86869a0225dd481bfbe746d502
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,55 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides atomic JSON persistence, email/SMS/in-app adapters, preference defaults and overrides, idempotent dispatch, recipient validation, and inspectable delivery results.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated idempotency key returns the original notification without redelivery.", "Invalid email/SMS recipients are rejected before persistence or delivery."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable."
+      }
+    }
+  ]
+}
+```

codex
The critic found four real gaps: persistence recovery/concurrency, idempotency-key scope and conflict behavior, explicit judge evidence, and a documentation check that the test command actually reaches. I’m tightening those contracts now; implementation will not start until the revised plan passes both gates.
apply patch
patch: completed
/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/.agentfw-plan.md
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc 'python3 .agents/skills/agentfw/tools/validate-plan .agentfw-plan.md' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
PASS: .agentfw-plan.md — 5 requirements, 3 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)

hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
Both plan gates now pass. The revised design explicitly tests serialized concurrent writes, restart durability, corrupt-store refusal, per-user idempotency with payload-conflict detection, cross-user key reuse, and documentation reachability.

I’m dispatching the domain/persistence implementation first under a no-network, repository-only side-effect budget.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The core worker is implementing the persistence and dispatch invariants now. After its producer tests pass, I’ll inspect the actual files before handing the HTTP layer to a fresh worker, so the second task integrates against code rather than assumptions.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The worker is still active and has not reported a failure. I’m leaving its file partition untouched to avoid reading a half-written state; the next checkpoint is the completed core test output.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The core implementation reports 9/9 passing, but the contract’s exact output anchor did not match Node 25’s default reporter. I’m treating that as an evidence-format issue, not silently accepting it; I’ll rerun the same suite with TAP output and inspect the seam before dispatching the API worker.
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/zsh -lc "git status --short && find src test -type f -maxdepth 3 -print | sort && sed -n '1,260p' src/core/notification-service.js && sed -n '1,240p' src/core/json-store.js" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
?? .agentfw-plan.md
?? .agents/
?? AGENTS.md
?? src/
?? test/
src/core/errors.js
src/core/index.js
src/core/json-store.js
src/core/notification-service.js
src/core/providers.js
test/core.test.js
'use strict';

const { randomUUID } = require('node:crypto');
const {
  IdempotencyConflictError,
  ValidationError,
} = require('./errors');
const { createDefaultAdapters } = require('./providers');

const CHANNELS = Object.freeze(['email', 'sms', 'inApp']);
const DEFAULT_PREFERENCES = Object.freeze({ email: true, sms: true, inApp: true });

function createInitialState() {
  return {
    version: 1,
    preferences: {},
    notifications: {},
    idempotency: {},
  };
}

function validateState(state) {
  if (!state || state.version !== 1) return false;
  for (const key of ['preferences', 'notifications', 'idempotency']) {
    if (!state[key] || typeof state[key] !== 'object' || Array.isArray(state[key])) return false;
  }
  return true;
}

function stableStringify(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  const keys = Object.keys(value).sort();
  return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
}

function requireNonEmptyString(value, field) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new ValidationError(`${field} must be a non-empty string`, { field });
  }
  return value.trim();
}

function normalizeChannels(channels) {
  if (!Array.isArray(channels) || channels.length === 0) {
    throw new ValidationError('channels must be a non-empty array', { field: 'channels' });
  }
  const requested = new Set(channels);
  for (const channel of requested) {
    if (!CHANNELS.includes(channel)) {
      throw new ValidationError(`Unsupported channel: ${channel}`, { field: 'channels', channel });
    }
  }
  return CHANNELS.filter((channel) => requested.has(channel));
}

function normalizeRecipients(channels, recipients, userId) {
  if (!recipients || typeof recipients !== 'object' || Array.isArray(recipients)) {
    throw new ValidationError('recipients must be an object', { field: 'recipients' });
  }
  const normalized = {};
  if (channels.includes('email')) {
    const email = requireNonEmptyString(recipients.email, 'recipients.email').toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new ValidationError('recipients.email is invalid', { field: 'recipients.email' });
    }
    normalized.email = email;
  }
  if (channels.includes('sms')) {
    const sms = requireNonEmptyString(recipients.sms, 'recipients.sms');
    if (!/^\+[1-9]\d{7,14}$/.test(sms)) {
      throw new ValidationError('recipients.sms must be an E.164 number', { field: 'recipients.sms' });
    }
    normalized.sms = sms;
  }
  if (channels.includes('inApp')) {
    if (recipients.inApp !== undefined && recipients.inApp !== userId) {
      throw new ValidationError('recipients.inApp must match userId', { field: 'recipients.inApp' });
    }
    normalized.inApp = userId;
  }
  return normalized;
}

function normalizeContent(content) {
  if (!content || typeof content !== 'object' || Array.isArray(content)) {
    throw new ValidationError('content must be an object', { field: 'content' });
  }
  const body = requireNonEmptyString(content.body, 'content.body');
  const normalized = { body };
  if (content.subject !== undefined) {
    normalized.subject = requireNonEmptyString(content.subject, 'content.subject');
  }
  return normalized;
}

function validateOverrides(overrides) {
  if (!overrides || typeof overrides !== 'object' || Array.isArray(overrides)) {
    throw new ValidationError('preferences must be an object', { field: 'preferences' });
  }
  const normalized = {};
  for (const [channel, value] of Object.entries(overrides)) {
    if (!CHANNELS.includes(channel)) {
      throw new ValidationError(`Unsupported preference channel: ${channel}`, { channel });
    }
    if (typeof value !== 'boolean') {
      throw new ValidationError(`Preference ${channel} must be boolean`, { channel });
    }
    normalized[channel] = value;
  }
  return normalized;
}

class NotificationService {
  constructor({ store, adapters = createDefaultAdapters(), clock = () => new Date(), idGenerator = randomUUID } = {}) {
    if (!store || typeof store.transact !== 'function' || typeof store.read !== 'function') {
      throw new TypeError('store must expose read() and transact()');
    }
    for (const channel of CHANNELS) {
      if (!adapters[channel] || typeof adapters[channel].deliver !== 'function') {
        throw new TypeError(`Missing ${channel} adapter`);
      }
    }
    this.store = store;
    this.adapters = adapters;
    this.clock = clock;
    this.idGenerator = idGenerator;
  }

  initialize() {
    return this.store.initialize?.() ?? this.store.read();
  }

  async getPreferences(userId, category) {
    userId = requireNonEmptyString(userId, 'userId');
    category = requireNonEmptyString(category, 'category');
    const state = await this.store.read();
    return this.#resolvePreferences(state, userId, category);
  }

  async setPreferences(userId, category, overrides) {
    userId = requireNonEmptyString(userId, 'userId');
    category = requireNonEmptyString(category, 'category');
    const normalized = validateOverrides(overrides);
    return this.store.transact((state) => {
      const userPreferences = state.preferences[userId] ?? { default: {}, categories: {} };
      if (category === 'default') {
        userPreferences.default = { ...userPreferences.default, ...normalized };
      } else {
        userPreferences.categories[category] = {
          ...userPreferences.categories[category],
          ...normalized,
        };
      }
      state.preferences[userId] = userPreferences;
      return this.#resolvePreferences(state, userId, category);
    });
  }

  async dispatch(input) {
    const request = this.#normalizeDispatch(input);
    const fingerprint = stableStringify(request);
    const createdAt = this.clock().toISOString();
    const id = this.idGenerator();

    const reservation = await this.store.transact((state) => {
      const userKeys = state.idempotency[request.userId] ?? {};
      const prior = userKeys[request.idempotencyKey];
      if (prior) {
        if (prior.fingerprint !== fingerprint) {
          throw new IdempotencyConflictError(request.userId, request.idempotencyKey);
        }
        return { existing: true, notification: state.notifications[prior.notificationId] };
      }

      const preferences = this.#resolvePreferences(state, request.userId, request.category);
      const deliveries = request.channels.map((channel) => ({
        channel,
        recipient: request.recipients[channel],
        status: preferences[channel] ? 'pending' : 'skipped',
        ...(preferences[channel] ? {} : { reason: 'preference_disabled' }),
      }));
      const notification = {
        id,
        userId: request.userId,
        idempotencyKey: request.idempotencyKey,
        category: request.category,
        content: request.content,
        createdAt,
        deliveries,
      };
      state.notifications[id] = notification;
      userKeys[request.idempotencyKey] = { fingerprint, notificationId: id };
      state.idempotency[request.userId] = userKeys;
      return { existing: false, notification };
    });

    if (reservation.existing) return reservation.notification;

    const attempted = await Promise.all(reservation.notification.deliveries.map(async (delivery) => {
      if (delivery.status === 'skipped') return delivery;
      try {
        const providerResult = await this.adapters[delivery.channel].deliver({
          notificationId: reservation.notification.id,
          userId: request.userId,
          category: request.category,
          recipient: delivery.recipient,
          content: request.content,
          createdAt,
        });
        return { ...delivery, status: 'delivered', providerResult: providerResult ?? null };
      } catch (error) {
        return {
          ...delivery,
          status: 'failed',
          error: {
            code: typeof error.code === 'string' ? error.code : 'PROVIDER_ERROR',
            message: error.message || 'Provider delivery failed',
          },
        };
      }
    }));

    return this.store.transact((state) => {
      state.notifications[id].deliveries = attempted;
      state.notifications[id].completedAt = this.clock().toISOString();
      return state.notifications[id];
    });
  }

  async getNotification(userId, notificationId) {
    userId = requireNonEmptyString(userId, 'userId');
    notificationId = requireNonEmptyString(notificationId, 'notificationId');
    const state = await this.store.read();
    const notification = state.notifications[notificationId];
    return notification?.userId === userId ? notification : null;
  }

  #normalizeDispatch(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      throw new ValidationError('notification request must be an object');
    }
    const userId = requireNonEmptyString(input.userId, 'userId');
    const idempotencyKey = requireNonEmptyString(input.idempotencyKey, 'idempotencyKey');
    const category = requireNonEmptyString(input.category, 'category');
    const channels = normalizeChannels(input.channels);
    return {
      userId,
      idempotencyKey,
      category,
      channels,
      recipients: normalizeRecipients(channels, input.recipients, userId),
      content: normalizeContent(input.content),
    };
  }

  #resolvePreferences(state, userId, category) {
    const stored = state.preferences[userId];
    return {
      ...DEFAULT_PREFERENCES,
'use strict';

const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { CorruptStoreError } = require('./errors');

function clone(value) {
  return structuredClone(value);
}

class AtomicJsonStore {
  #filePath;
  #initialState;
  #validate;
  #state;
  #tail = Promise.resolve();

  constructor(filePath, { initialState, validate = () => true } = {}) {
    if (!filePath) throw new TypeError('filePath is required');
    if (initialState === undefined) throw new TypeError('initialState is required');
    this.#filePath = path.resolve(filePath);
    this.#initialState = clone(initialState);
    this.#validate = validate;
  }

  get filePath() {
    return this.#filePath;
  }

  initialize() {
    return this.#enqueue(async () => {
      await this.#ensureLoaded();
      return clone(this.#state);
    });
  }

  read() {
    return this.#enqueue(async () => {
      await this.#ensureLoaded();
      return clone(this.#state);
    });
  }

  transact(mutator) {
    if (typeof mutator !== 'function') throw new TypeError('mutator must be a function');
    return this.#enqueue(async () => {
      await this.#ensureLoaded();
      const candidate = clone(this.#state);
      const result = await mutator(candidate);
      this.#assertValid(candidate);
      await this.#writeAtomic(candidate);
      this.#state = candidate;
      return clone(result);
    });
  }

  #enqueue(operation) {
    const result = this.#tail.then(operation, operation);
    this.#tail = result.then(() => undefined, () => undefined);
    return result;
  }

  async #ensureLoaded() {
    if (this.#state !== undefined) return;

    let contents;
    try {
      contents = await fs.readFile(this.#filePath, 'utf8');
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      const initial = clone(this.#initialState);
      this.#assertValid(initial);
      await this.#writeAtomic(initial);
      this.#state = initial;
      return;
    }

    try {
      const parsed = JSON.parse(contents);
      this.#assertValid(parsed);
      this.#state = parsed;
    } catch (error) {
      if (error instanceof CorruptStoreError) throw error;
      throw new CorruptStoreError(this.#filePath, error);
    }
  }

  #assertValid(state) {
    try {
      if (this.#validate(state) === false) throw new Error('State validation returned false');
    } catch (error) {
      throw new CorruptStoreError(this.#filePath, error);
    }
  }

  async #writeAtomic(state) {
    const directory = path.dirname(this.#filePath);
    await fs.mkdir(directory, { recursive: true });
    const tempPath = path.join(
      directory,
      `.${path.basename(this.#filePath)}.${process.pid}.${randomUUID()}.tmp`,
    );
    let handle;
    try {
      handle = await fs.open(tempPath, 'wx', 0o600);
      await handle.writeFile(`${JSON.stringify(state)}\n`, 'utf8');
      await handle.sync();
      await handle.close();
      handle = undefined;
      await fs.rename(tempPath, this.#filePath);

      // Persist the directory entry when the platform supports directory fsync.
      let directoryHandle;
      try {
        directoryHandle = await fs.open(directory, 'r');
        await directoryHandle.sync();
      } finally {
        await directoryHandle?.close();
      }
    } catch (error) {
      await handle?.close().catch(() => undefined);
      await fs.unlink(tempPath).catch(() => undefined);
      throw error;
    }
  }
}

module.exports = { AtomicJsonStore };

hook: PostToolUse
hook: PostToolUse Completed
exec
/bin/zsh -lc 'node --test --test-reporter=tap test/core.test.js' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

 succeeded in 557ms:
# Subtest: default adapters deliver email, SMS, and in-app with inspectable results
ok 1 - default adapters deliver email, SMS, and in-app with inspectable results
  ---
  duration_ms: 35.844166
  type: 'test'
  ...
# Subtest: preference defaults, user defaults, and category overrides compose without provider calls for skips
ok 2 - preference defaults, user defaults, and category overrides compose without provider calls for skips
  ---
  duration_ms: 41.23475
  type: 'test'
  ...
# Subtest: same user and canonical payload is idempotent while changed payload conflicts
ok 3 - same user and canonical payload is idempotent while changed payload conflicts
  ---
  duration_ms: 33.241917
  type: 'test'
  ...
# Subtest: idempotency keys are scoped per user
ok 4 - idempotency keys are scoped per user
  ---
  duration_ms: 40.618083
  type: 'test'
  ...
# Subtest: invalid email and SMS are rejected before persistence or delivery
ok 5 - invalid email and SMS are rejected before persistence or delivery
  ---
  duration_ms: 9.515333
  type: 'test'
  ...
# Subtest: provider failures are isolated and persisted as delivery results
ok 6 - provider failures are isolated and persisted as delivery results
  ---
  duration_ms: 24.420542
  type: 'test'
  ...
# Subtest: concurrent mutations serialize and survive restart
ok 7 - concurrent mutations serialize and survive restart
  ---
  duration_ms: 252.381292
  type: 'test'
  ...
# Subtest: restart preserves idempotency and never redelivers
ok 8 - restart preserves idempotency and never redelivers
  ---
  duration_ms: 33.659958
  type: 'test'
  ...
# Subtest: corrupt persistence is rejected and source bytes are not overwritten
ok 9 - corrupt persistence is rejected and source bytes are not overwritten
  ---
  duration_ms: 2.276958
  type: 'test'
  ...
1..9
# tests 9
# suites 0
# pass 9
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 544.0465

hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '260,520p' src/core/notification-service.js; sed -n '1,240p' src/core/providers.js; sed -n '1,200p' src/core/errors.js; sed -n '1,200p' src/core/index.js" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
      ...DEFAULT_PREFERENCES,
      ...stored?.default,
      ...stored?.categories?.[category],
    };
  }
}

module.exports = {
  CHANNELS,
  DEFAULT_PREFERENCES,
  NotificationService,
  createInitialState,
  stableStringify,
  validateState,
};
'use strict';

class RecordingProvider {
  constructor(channel) {
    this.channel = channel;
    this.calls = [];
  }

  async send(delivery) {
    const recorded = structuredClone(delivery);
    this.calls.push(recorded);
    return {
      provider: 'recording',
      reference: `${this.channel}-${this.calls.length}`,
    };
  }
}

class ChannelAdapter {
  constructor(channel, provider = new RecordingProvider(channel)) {
    if (!provider || typeof provider.send !== 'function') {
      throw new TypeError(`${channel} provider must expose send(delivery)`);
    }
    this.channel = channel;
    this.provider = provider;
  }

  deliver(delivery) {
    return this.provider.send(structuredClone(delivery));
  }
}

class EmailAdapter extends ChannelAdapter {
  constructor(provider) {
    super('email', provider);
  }
}

class SmsAdapter extends ChannelAdapter {
  constructor(provider) {
    super('sms', provider);
  }
}

class InAppAdapter extends ChannelAdapter {
  constructor(provider) {
    super('inApp', provider);
  }
}

function createDefaultAdapters() {
  return {
    email: new EmailAdapter(),
    sms: new SmsAdapter(),
    inApp: new InAppAdapter(),
  };
}

module.exports = {
  ChannelAdapter,
  EmailAdapter,
  InAppAdapter,
  RecordingProvider,
  SmsAdapter,
  createDefaultAdapters,
};
'use strict';

class DomainError extends Error {
  constructor(message, { code = 'DOMAIN_ERROR', status = 400, details } = {}) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.status = status;
    if (details !== undefined) this.details = details;
  }
}

class ValidationError extends DomainError {
  constructor(message, details) {
    super(message, { code: 'VALIDATION_ERROR', status: 400, details });
  }
}

class IdempotencyConflictError extends DomainError {
  constructor(userId, idempotencyKey) {
    super('Idempotency key was already used with a different payload', {
      code: 'IDEMPOTENCY_CONFLICT',
      status: 409,
      details: { userId, idempotencyKey },
    });
  }
}

class CorruptStoreError extends DomainError {
  constructor(filePath, cause) {
    super(`Persistence file is corrupt: ${filePath}`, {
      code: 'CORRUPT_STORE',
      status: 500,
      details: { filePath },
    });
    this.cause = cause;
  }
}

module.exports = {
  CorruptStoreError,
  DomainError,
  IdempotencyConflictError,
  ValidationError,
};
'use strict';

const { AtomicJsonStore } = require('./json-store');
const {
  NotificationService,
  createInitialState,
  validateState,
} = require('./notification-service');
const providers = require('./providers');
const errors = require('./errors');

function createNotificationCore({ filePath, ...options }) {
  const store = new AtomicJsonStore(filePath, {
    initialState: createInitialState(),
    validate: validateState,
  });
  const service = new NotificationService({ store, ...options });
  return { store, service, adapters: service.adapters };
}

module.exports = {
  AtomicJsonStore,
  NotificationService,
  createNotificationCore,
  createInitialState,
  validateState,
  ...providers,
  ...errors,
};

hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The core seam is sound on inspection, and a fresh TAP run produced the required `# pass 9` / `# fail 0` evidence. The store serializes mutations, fsyncs and atomically renames, refuses corrupt state without overwriting it, and the service reserves idempotency before invoking providers.

I’m now handing the versioned HTTP API, inbox queries, documentation, and end-to-end suite to a fresh worker.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The API worker is still integrating against the core. The required public surface is health, get/update preferences, create/get notification, paginated in-app inbox, and mark-read; strict field allowlists and user-scoped lookup behavior are part of the acceptance suite, not just documentation.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
No error has surfaced; the worker remains active. I’m holding the next verification slot for a separate judge, so the implementation agent cannot grade its own API/domain assumptions.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The implementation is at 16/16 passing. One environment limitation appeared: this sandbox can reject loopback `listen()` with `EPERM`, so the HTTP tests use the real server when allowed and fall back only for that exact error to invoking the same request handler in memory. I’ll preserve that relaxation in the evidence and have the independent judge scrutinize it.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '180,380p' src/core/notification-service.js; sed -n '1,320p' test/http.test.js; sed -n '1,260p' README.md" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
        status: preferences[channel] ? 'pending' : 'skipped',
        ...(preferences[channel] ? {} : { reason: 'preference_disabled' }),
      }));
      const notification = {
        id,
        userId: request.userId,
        idempotencyKey: request.idempotencyKey,
        category: request.category,
        content: request.content,
        createdAt,
        deliveries,
      };
      state.notifications[id] = notification;
      userKeys[request.idempotencyKey] = { fingerprint, notificationId: id };
      state.idempotency[request.userId] = userKeys;
      return { existing: false, notification };
    });

    if (reservation.existing) return reservation.notification;

    const attempted = await Promise.all(reservation.notification.deliveries.map(async (delivery) => {
      if (delivery.status === 'skipped') return delivery;
      try {
        const providerResult = await this.adapters[delivery.channel].deliver({
          notificationId: reservation.notification.id,
          userId: request.userId,
          category: request.category,
          recipient: delivery.recipient,
          content: request.content,
          createdAt,
        });
        return { ...delivery, status: 'delivered', providerResult: providerResult ?? null };
      } catch (error) {
        return {
          ...delivery,
          status: 'failed',
          error: {
            code: typeof error.code === 'string' ? error.code : 'PROVIDER_ERROR',
            message: error.message || 'Provider delivery failed',
          },
        };
      }
    }));

    return this.store.transact((state) => {
      state.notifications[id].deliveries = attempted;
      state.notifications[id].completedAt = this.clock().toISOString();
      return state.notifications[id];
    });
  }

  async getNotification(userId, notificationId) {
    userId = requireNonEmptyString(userId, 'userId');
    notificationId = requireNonEmptyString(notificationId, 'notificationId');
    const state = await this.store.read();
    const notification = state.notifications[notificationId];
    return notification?.userId === userId ? notification : null;
  }

  async listInbox(userId, { offset = 0, limit = 20, unread = false } = {}) {
    userId = requireNonEmptyString(userId, 'userId');
    if (!Number.isSafeInteger(offset) || offset < 0) {
      throw new ValidationError('offset must be a non-negative integer', { field: 'offset' });
    }
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
      throw new ValidationError('limit must be an integer between 1 and 100', { field: 'limit' });
    }
    if (typeof unread !== 'boolean') {
      throw new ValidationError('unread must be boolean', { field: 'unread' });
    }

    const state = await this.store.read();
    const matching = Object.values(state.notifications)
      .filter((notification) => notification.userId === userId)
      .map((notification) => this.#toInboxItem(notification))
      .filter((item) => item !== null && (!unread || item.readAt === null))
      .sort((left, right) =>
        right.createdAt.localeCompare(left.createdAt) || right.notificationId.localeCompare(left.notificationId));
    const items = matching.slice(offset, offset + limit);
    const nextOffset = offset + items.length < matching.length ? offset + items.length : null;

    return {
      items,
      pagination: { offset, limit, total: matching.length, nextOffset },
    };
  }

  async markInboxRead(userId, notificationId) {
    userId = requireNonEmptyString(userId, 'userId');
    notificationId = requireNonEmptyString(notificationId, 'notificationId');
    return this.store.transact((state) => {
      const notification = state.notifications[notificationId];
      if (!notification || notification.userId !== userId) return null;
      const delivery = notification.deliveries.find((candidate) =>
        candidate.channel === 'inApp' && candidate.status === 'delivered');
      if (!delivery) return null;
      if (!delivery.readAt) delivery.readAt = this.clock().toISOString();
      return this.#toInboxItem(notification);
    });
  }

  #normalizeDispatch(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      throw new ValidationError('notification request must be an object');
    }
    const userId = requireNonEmptyString(input.userId, 'userId');
    const idempotencyKey = requireNonEmptyString(input.idempotencyKey, 'idempotencyKey');
    const category = requireNonEmptyString(input.category, 'category');
    const channels = normalizeChannels(input.channels);
    return {
      userId,
      idempotencyKey,
      category,
      channels,
      recipients: normalizeRecipients(channels, input.recipients, userId),
      content: normalizeContent(input.content),
    };
  }

  #resolvePreferences(state, userId, category) {
    const stored = state.preferences[userId];
    return {
      ...DEFAULT_PREFERENCES,
      ...stored?.default,
      ...stored?.categories?.[category],
    };
  }

  #toInboxItem(notification) {
    const delivery = notification.deliveries.find((candidate) =>
      candidate.channel === 'inApp' && candidate.status === 'delivered');
    if (!delivery) return null;
    return {
      notificationId: notification.id,
      category: notification.category,
      content: notification.content,
      createdAt: notification.createdAt,
      readAt: delivery.readAt ?? null,
    };
  }
}

module.exports = {
  CHANNELS,
  DEFAULT_PREFERENCES,
  NotificationService,
  createInitialState,
  stableStringify,
  validateState,
};
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { Readable } = require('node:stream');
const { createNotificationCore } = require('../src/core');
const { createApiServer, createRequestHandler } = require('../src/http/app');

async function invokeHandler(handler, pathname, { method = 'GET', body, headers = {} } = {}) {
  const serialized = body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body));
  const request = Readable.from(serialized === undefined ? [] : [Buffer.from(serialized)]);
  request.url = pathname;
  request.method = method;
  request.headers = serialized === undefined
    ? headers
    : { 'content-type': 'application/json', ...headers };

  return new Promise((resolve, reject) => {
    const response = {
      headersSent: false,
      writeHead(status, responseHeaders) {
        this.status = status;
        this.headers = new Headers(responseHeaders);
        this.headersSent = true;
      },
      end(responseBody) {
        try {
          resolve({ status: this.status, headers: this.headers, body: JSON.parse(responseBody) });
        } catch (error) {
          reject(error);
        }
      },
      destroy(error) {
        reject(error || new Error('Response destroyed'));
      },
    };
    Promise.resolve(handler(request, response)).catch(reject);
  });
}

async function fixture(t) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'notification-http-'));
  const core = createNotificationCore({ filePath: path.join(directory, 'data.json') });
  await core.service.initialize();
  const server = createApiServer({ service: core.service });
  let baseUrl;
  let request;
  try {
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    const { port } = server.address();
    baseUrl = `http://127.0.0.1:${port}`;
    request = (pathname, options) => api(baseUrl, pathname, options);
  } catch (error) {
    if (error.code !== 'EPERM') throw error;
    request = (pathname, options) =>
      invokeHandler(createRequestHandler({ service: core.service }), pathname, options);
  }
  t.after(async () => {
    if (server.listening) await new Promise((resolve) => server.close(resolve));
    await fs.rm(directory, { recursive: true, force: true });
  });
  return { ...core, request };
}

async function api(baseUrl, pathname, { method = 'GET', body, headers = {} } = {}) {
  const response = await fetch(`${baseUrl}${pathname}`, {
    method,
    headers: body === undefined ? headers : { 'content-type': 'application/json', ...headers },
    body: body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)),
  });
  return {
    status: response.status,
    headers: response.headers,
    body: await response.json(),
  };
}

function notification(overrides = {}) {
  return {
    userId: 'user-1',
    idempotencyKey: 'key-1',
    category: 'security',
    channels: ['email', 'inApp'],
    recipients: { email: 'user@example.com', inApp: 'user-1' },
    content: { subject: 'Sign in', body: 'A new sign-in occurred.' },
    ...overrides,
  };
}

test('health and preference endpoints expose defaults and category overrides', async (t) => {
  const app = await fixture(t);

  const health = await app.request('/api/v1/health');
  assert.equal(health.status, 200);
  assert.deepEqual(health.body, { status: 'ok' });
  const defaults = await app.request('/api/v1/users/user-1/preferences/security');
  assert.equal(defaults.status, 200);
  assert.deepEqual(defaults.body.preferences, { email: true, sms: true, inApp: true });

  const updated = await app.request('/api/v1/users/user-1/preferences/security', {
    method: 'PUT', body: { email: false, inApp: false },
  });
  assert.equal(updated.status, 200);
  assert.deepEqual(updated.body.preferences, { email: false, sms: true, inApp: false });

  const created = await app.request('/api/v1/notifications', {
    method: 'POST', body: notification(),
  });
  assert.equal(created.status, 201);
  assert.deepEqual(created.body.notification.deliveries.map(({ channel, status }) => ({ channel, status })), [
    { channel: 'email', status: 'skipped' },
    { channel: 'inApp', status: 'skipped' },
  ]);
  assert.equal(app.adapters.email.provider.calls.length, 0);
  assert.equal(app.adapters.inApp.provider.calls.length, 0);
});

test('notification status is user-scoped and missing resources use stable 404 errors', async (t) => {
  const app = await fixture(t);
  const created = await app.request('/api/v1/notifications', {
    method: 'POST', body: notification(),
  });
  const id = created.body.notification.id;

  const own = await app.request(`/api/v1/users/user-1/notifications/${id}`);
  assert.equal(own.status, 200);
  assert.equal(own.body.notification.id, id);

  for (const pathname of [
    `/api/v1/users/user-2/notifications/${id}`,
    '/api/v1/users/user-1/notifications/missing',
  ]) {
    const result = await app.request(pathname);
    assert.equal(result.status, 404);
    assert.deepEqual(result.body, {
      error: { code: 'NOT_FOUND', message: 'Notification not found' },
    });
  }
});

test('in-app inbox paginates, filters unread items, and mark-read is user-scoped', async (t) => {
  const app = await fixture(t);
  const ids = [];
  for (let index = 0; index < 3; index += 1) {
    const created = await app.request('/api/v1/notifications', {
      method: 'POST',
      body: notification({
        idempotencyKey: `key-${index}`,
        channels: ['inApp'],
        recipients: { inApp: 'user-1' },
        content: { body: `Message ${index}` },
      }),
    });
    ids.push(created.body.notification.id);
  }

  const firstPage = await app.request('/api/v1/users/user-1/inbox?limit=2&offset=0');
  assert.equal(firstPage.status, 200);
  assert.equal(firstPage.body.items.length, 2);
  assert.deepEqual(firstPage.body.pagination, { offset: 0, limit: 2, total: 3, nextOffset: 2 });
  const foreignInbox = await app.request('/api/v1/users/user-2/inbox');
  assert.deepEqual(foreignInbox.body, {
    items: [],
    pagination: { offset: 0, limit: 20, total: 0, nextOffset: null },
  });

  const target = firstPage.body.items[0].notificationId;
  const crossUser = await app.request(`/api/v1/users/user-2/inbox/${target}/read`, {
    method: 'PUT', body: {},
  });
  assert.equal(crossUser.status, 404);
  assert.deepEqual(crossUser.body, { error: { code: 'NOT_FOUND', message: 'Inbox item not found' } });

  const marked = await app.request(`/api/v1/users/user-1/inbox/${target}/read`, {
    method: 'PUT', body: {},
  });
  assert.equal(marked.status, 200);
  assert.equal(typeof marked.body.item.readAt, 'string');
  const markedAgain = await app.request(`/api/v1/users/user-1/inbox/${target}/read`, {
    method: 'PUT', body: {},
  });
  assert.equal(markedAgain.body.item.readAt, marked.body.item.readAt);

  const unread = await app.request('/api/v1/users/user-1/inbox?unread=true&limit=100');
  assert.equal(unread.status, 200);
  assert.equal(unread.body.items.length, 2);
  assert.ok(unread.body.items.every((item) => item.readAt === null));
  assert.ok(ids.includes(target));
});

test('malformed JSON and unknown fields return structured 400 errors', async (t) => {
  const app = await fixture(t);
  const malformed = await app.request('/api/v1/notifications', {
    method: 'POST', body: '{bad json',
  });
  assert.equal(malformed.status, 400);
  assert.deepEqual(malformed.body, {
    error: { code: 'INVALID_JSON', message: 'Request body is not valid JSON' },
  });

  const unknown = await app.request('/api/v1/notifications', {
    method: 'POST', body: { ...notification(), administrativeOverride: true },
  });
  assert.equal(unknown.status, 400);
  assert.equal(unknown.body.error.code, 'VALIDATION_ERROR');
  assert.deepEqual(unknown.body.error.details.unknownFields, ['administrativeOverride']);

  const nestedUnknown = await app.request('/api/v1/notifications', {
    method: 'POST', body: notification({ content: { body: 'hello', html: '<b>hello</b>' } }),
  });
  assert.equal(nestedUnknown.status, 400);
  assert.equal(nestedUnknown.body.error.details.field, 'content.html');
});

test('pagination, content type, methods, and paths reject invalid requests consistently', async (t) => {
  const app = await fixture(t);
  for (const query of ['limit=0', 'limit=101', 'offset=-1', 'unread=yes', 'page=1', 'limit=2&limit=3']) {
    const result = await app.request(`/api/v1/users/user-1/inbox?${query}`);
    assert.equal(result.status, 400, query);
    assert.equal(result.body.error.code, 'INVALID_PAGINATION', query);
  }

  const mediaType = await app.request('/api/v1/notifications', {
    method: 'POST', body: '{}', headers: { 'content-type': 'text/plain' },
  });
  assert.equal(mediaType.status, 415);
  assert.equal(mediaType.body.error.code, 'UNSUPPORTED_MEDIA_TYPE');

  const method = await app.request('/api/v1/health', { method: 'POST' });
  assert.equal(method.status, 405);
  assert.equal(method.body.error.code, 'METHOD_NOT_ALLOWED');
  assert.equal(method.headers.get('allow'), 'GET');

  const pathResult = await app.request('/api/v2/health');
  assert.equal(pathResult.status, 404);
  assert.deepEqual(pathResult.body, { error: { code: 'NOT_FOUND', message: 'Resource not found' } });
});

test('changed payload with a reused user idempotency key returns 409 without delivery', async (t) => {
  const app = await fixture(t);
  const first = await app.request('/api/v1/notifications', {
    method: 'POST', body: notification({ channels: ['email'], recipients: { email: 'user@example.com' } }),
  });
  assert.equal(first.status, 201);
  assert.equal(app.adapters.email.provider.calls.length, 1);

  const repeated = await app.request('/api/v1/notifications', {
    method: 'POST', body: notification({ channels: ['email'], recipients: { email: 'user@example.com' } }),
  });
  assert.equal(repeated.body.notification.id, first.body.notification.id);
  assert.equal(app.adapters.email.provider.calls.length, 1);

  const conflict = await app.request('/api/v1/notifications', {
    method: 'POST',
    body: notification({
      channels: ['email'],
      recipients: { email: 'user@example.com' },
      content: { body: 'Changed payload' },
    }),
  });
  assert.equal(conflict.status, 409);
  assert.equal(conflict.body.error.code, 'IDEMPOTENCY_CONFLICT');
  assert.equal(app.adapters.email.provider.calls.length, 1);
});
# Dependency-free notification service

This Node.js service persists notification preferences and delivery results in one atomically
replaced JSON file. It supports email, SMS, and in-app channels through replaceable adapters and
offers a versioned JSON REST API. It has no runtime dependencies and performs no network delivery
with its default recording providers.

## Run and configure

Node.js 25 or newer is required.

```sh
npm test
DATA_FILE=./data/notifications.json npm start
```

Configuration is supplied through environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATA_FILE` | `./data/notifications.json` | Durable JSON data path. Parent directories are created automatically. |
| `HOST` | `127.0.0.1` | Listen address. The loopback default avoids accidental external exposure. |
| `PORT` | `3000` | TCP port (`0` may be used in tests for an ephemeral port). |

### Safe defaults

The process binds to `127.0.0.1`, default providers only record delivery attempts in memory, JSON
bodies are capped at 1 MiB, and persistence files are created with mode `0600`. The API intentionally
does not implement authentication: if it is exposed beyond localhost, put it behind an authenticated
gateway and derive or verify each `userId` from the authenticated principal. Do not trust a client-
supplied user ID at an internet-facing boundary.

## Preference semantics

Every channel begins enabled. A user's `default` preferences override those defaults, and a named
category overrides both. Updates merge only the supplied booleans. A disabled requested channel is
stored as `skipped` with reason `preference_disabled`; its provider is never called. An in-app item
appears in the inbox only when its in-app delivery completed successfully.

```sh
curl -sS -X PUT http://127.0.0.1:3000/api/v1/users/user-1/preferences/security \
  -H 'content-type: application/json' \
  -d '{"email":false,"sms":true,"inApp":true}'
```

## API

All request bodies must use `Content-Type: application/json`. Unknown JSON fields are rejected.
All failures use `{"error":{"code":"...","message":"...","details":...}}`.

- `GET /api/v1/health`
- `GET /api/v1/users/:userId/preferences/:category`
- `PUT /api/v1/users/:userId/preferences/:category`
- `POST /api/v1/notifications`
- `GET /api/v1/users/:userId/notifications/:notificationId`
- `GET /api/v1/users/:userId/inbox?offset=0&limit=20&unread=true`
- `PUT /api/v1/users/:userId/inbox/:notificationId/read` with body `{}`

Create a notification:

```sh
curl -sS -X POST http://127.0.0.1:3000/api/v1/notifications \
  -H 'content-type: application/json' \
  -d '{
    "userId":"user-1",
    "idempotencyKey":"signup-42",
    "category":"security",
    "channels":["email","sms","inApp"],
    "recipients":{"email":"user@example.com","sms":"+13125550123","inApp":"user-1"},
    "content":{"subject":"Sign in","body":"A new sign-in occurred."}
  }'
```

The same `idempotencyKey` and canonical payload for the same user returns the original persisted
notification without redelivery. Reusing that key for a changed payload returns HTTP 409 with
`IDEMPOTENCY_CONFLICT`. Keys are scoped per user.

Inbox pagination uses integer `offset` (at least 0) and `limit` (1–100). `unread` must be `true` or
`false`. Invalid or repeated parameters return HTTP 400 with `INVALID_PAGINATION`. Notification and
inbox-item lookups return the same HTTP 404 shape for missing and foreign-user resources.

## Provider adapter integration

Pass adapters when creating the core. Each adapter wraps a provider exposing async `send(delivery)`;
the return value becomes the delivery's `providerResult`, while thrown errors become a per-channel
`failed` result without preventing other channels from completing.

```js
const {
  EmailAdapter, SmsAdapter, InAppAdapter, createNotificationCore,
} = require('./src/core');

const core = createNotificationCore({
  filePath: process.env.DATA_FILE,
  adapters: {
    email: new EmailAdapter({ async send(delivery) { return emailClient.send(delivery); } }),
    sms: new SmsAdapter({ async send(delivery) { return smsClient.send(delivery); } }),
    inApp: new InAppAdapter({ async send(delivery) { return { accepted: true, id: delivery.notificationId }; } }),
  },
});
```

Initialize the service before handling requests. Provider implementations own their outbound I/O,
credentials, retry policy, and timeouts; the bundled service itself uses no third-party services.

hook: PostToolUse
exec
/bin/zsh -lc "git diff --stat; git status --short; sed -n '1,320p' src/http/app.js; sed -n '1,200p' src/server.js; cat package.json" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
?? .agentfw-plan.md
?? .agents/
?? AGENTS.md
?? README.md
?? package.json
?? src/
?? test/
'use strict';

const http = require('node:http');
const { DomainError, ValidationError } = require('../core');

const MAX_BODY_BYTES = 1024 * 1024;

function apiError(status, code, message, details) {
  const error = new Error(message);
  error.status = status;
  error.code = code;
  if (details !== undefined) error.details = details;
  return error;
}

function assertAllowedFields(value, allowed, field = 'body') {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new ValidationError(`${field} must be an object`, { field });
  }
  const unknown = Object.keys(value).filter((key) => !allowed.includes(key));
  if (unknown.length > 0) {
    throw new ValidationError(`Unknown field in ${field}: ${unknown[0]}`, {
      field: `${field}.${unknown[0]}`,
      unknownFields: unknown,
    });
  }
}

function validateNotificationBody(body) {
  assertAllowedFields(body, ['userId', 'idempotencyKey', 'category', 'channels', 'recipients', 'content']);
  assertAllowedFields(body.recipients, ['email', 'sms', 'inApp'], 'recipients');
  assertAllowedFields(body.content, ['subject', 'body'], 'content');
  return body;
}

function validatePreferencesBody(body) {
  assertAllowedFields(body, ['email', 'sms', 'inApp']);
  return body;
}

async function readJson(request) {
  const mediaType = (request.headers['content-type'] || '').split(';', 1)[0].trim().toLowerCase();
  if (mediaType !== 'application/json') {
    throw apiError(415, 'UNSUPPORTED_MEDIA_TYPE', 'Content-Type must be application/json');
  }

  let bytes = 0;
  const chunks = [];
  for await (const chunk of request) {
    bytes += chunk.length;
    if (bytes > MAX_BODY_BYTES) {
      throw apiError(413, 'PAYLOAD_TOO_LARGE', 'JSON request body exceeds 1 MiB');
    }
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw apiError(400, 'INVALID_JSON', 'Request body is not valid JSON');
  }
}

function decodeSegments(pathname) {
  try {
    return pathname.split('/').filter(Boolean).map(decodeURIComponent);
  } catch {
    throw apiError(400, 'INVALID_PATH', 'Request path contains invalid encoding');
  }
}

function parseSingleQuery(searchParams, name, fallback) {
  const values = searchParams.getAll(name);
  if (values.length === 0) return fallback;
  if (values.length !== 1) {
    throw apiError(400, 'INVALID_PAGINATION', `${name} must be specified at most once`, { field: name });
  }
  return values[0];
}

function parsePagination(searchParams) {
  const allowed = new Set(['offset', 'limit', 'unread']);
  for (const name of searchParams.keys()) {
    if (!allowed.has(name)) {
      throw apiError(400, 'INVALID_PAGINATION', `Unknown query parameter: ${name}`, { field: name });
    }
  }

  const offsetText = parseSingleQuery(searchParams, 'offset', '0');
  const limitText = parseSingleQuery(searchParams, 'limit', '20');
  const unreadText = parseSingleQuery(searchParams, 'unread', 'false');
  if (!/^(0|[1-9]\d*)$/.test(offsetText) || !Number.isSafeInteger(Number(offsetText))) {
    throw apiError(400, 'INVALID_PAGINATION', 'offset must be a non-negative integer', { field: 'offset' });
  }
  if (!/^[1-9]\d*$/.test(limitText) || Number(limitText) > 100) {
    throw apiError(400, 'INVALID_PAGINATION', 'limit must be an integer between 1 and 100', { field: 'limit' });
  }
  if (unreadText !== 'true' && unreadText !== 'false') {
    throw apiError(400, 'INVALID_PAGINATION', 'unread must be true or false', { field: 'unread' });
  }
  return { offset: Number(offsetText), limit: Number(limitText), unread: unreadText === 'true' };
}

function sendJson(response, status, payload, headers = {}) {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
    ...headers,
  });
  response.end(body);
}

function sendError(response, error) {
  const known = error instanceof DomainError || Number.isInteger(error.status);
  const status = known ? error.status : 500;
  const code = known && typeof error.code === 'string' ? error.code : 'INTERNAL_ERROR';
  const message = known ? error.message : 'An internal error occurred';
  const payload = { error: { code, message } };
  if (known && error.details !== undefined) payload.error.details = error.details;
  sendJson(response, status, payload, error.allow ? { allow: error.allow } : undefined);
}

function methodNotAllowed(allow) {
  const error = apiError(405, 'METHOD_NOT_ALLOWED', 'Method is not allowed for this resource');
  error.allow = allow.join(', ');
  return error;
}

function notFound(message = 'Resource not found') {
  return apiError(404, 'NOT_FOUND', message);
}

function exactRoute(segments, pattern) {
  return segments.length === pattern.length && pattern.every((part, index) =>
    part.startsWith(':') || part === segments[index]);
}

function createRequestHandler({ service }) {
  if (!service) throw new TypeError('service is required');

  return async function requestHandler(request, response) {
    try {
      const url = new URL(request.url, 'http://localhost');
      const segments = decodeSegments(url.pathname);

      if (exactRoute(segments, ['api', 'v1', 'health'])) {
        if (request.method !== 'GET') throw methodNotAllowed(['GET']);
        sendJson(response, 200, { status: 'ok' });
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'preferences', ':category'])) {
        const [, , , userId, , category] = segments;
        if (request.method === 'GET') {
          sendJson(response, 200, { preferences: await service.getPreferences(userId, category) });
          return;
        }
        if (request.method === 'PUT') {
          const body = validatePreferencesBody(await readJson(request));
          sendJson(response, 200, { preferences: await service.setPreferences(userId, category, body) });
          return;
        }
        throw methodNotAllowed(['GET', 'PUT']);
      }

      if (exactRoute(segments, ['api', 'v1', 'notifications'])) {
        if (request.method !== 'POST') throw methodNotAllowed(['POST']);
        const body = validateNotificationBody(await readJson(request));
        sendJson(response, 201, { notification: await service.dispatch(body) });
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'notifications', ':notificationId'])) {
        if (request.method !== 'GET') throw methodNotAllowed(['GET']);
        const [, , , userId, , notificationId] = segments;
        const notification = await service.getNotification(userId, notificationId);
        if (!notification) throw notFound('Notification not found');
        sendJson(response, 200, { notification });
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'inbox'])) {
        if (request.method !== 'GET') throw methodNotAllowed(['GET']);
        const [, , , userId] = segments;
        sendJson(response, 200, await service.listInbox(userId, parsePagination(url.searchParams)));
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'inbox', ':notificationId', 'read'])) {
        if (request.method !== 'PUT') throw methodNotAllowed(['PUT']);
        const body = await readJson(request);
        assertAllowedFields(body, []);
        const [, , , userId, , notificationId] = segments;
        const item = await service.markInboxRead(userId, notificationId);
        if (!item) throw notFound('Inbox item not found');
        sendJson(response, 200, { item });
        return;
      }

      throw notFound();
    } catch (error) {
      if (!response.headersSent) sendError(response, error);
      else response.destroy();
    }
  };
}

function createApiServer(options) {
  return http.createServer(createRequestHandler(options));
}

module.exports = {
  createApiServer,
  createRequestHandler,
};
'use strict';

const path = require('node:path');
const { createNotificationCore } = require('./core');
const { createApiServer } = require('./http/app');

function parsePort(value) {
  if (!/^(0|[1-9]\d*)$/.test(value) || Number(value) > 65535) {
    throw new Error('PORT must be an integer between 0 and 65535');
  }
  return Number(value);
}

async function startServer(environment = process.env) {
  const host = environment.HOST || '127.0.0.1';
  const port = parsePort(environment.PORT || '3000');
  const filePath = path.resolve(environment.DATA_FILE || path.join('data', 'notifications.json'));
  const core = createNotificationCore({ filePath });
  await core.service.initialize();
  const server = createApiServer({ service: core.service });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, resolve);
  });
  return { server, ...core };
}

if (require.main === module) {
  startServer().then(({ server }) => {
    const address = server.address();
    process.stdout.write(`Notification API listening on http://${address.address}:${address.port}\n`);
  }).catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { startServer };
{
  "name": "dependency-free-notification-service",
  "version": "1.0.0",
  "private": true,
  "description": "Durable dependency-free notification service and versioned REST API",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "test": "node --check src/core/index.js && node --check src/core/notification-service.js && node --check src/http/app.js && node --check src/server.js && node --test --test-reporter=tap test/core.test.js test/http.test.js test/docs.test.js"
  },
  "engines": {
    "node": ">=25"
  }
}

hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
exec
/bin/zsh -lc 'npm test' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

 succeeded in 979ms:
TAP version 13
# Subtest: default adapters deliver email, SMS, and in-app with inspectable results
ok 1 - default adapters deliver email, SMS, and in-app with inspectable results
  ---
  duration_ms: 35.837791
  type: 'test'
  ...
# Subtest: preference defaults, user defaults, and category overrides compose without provider calls for skips
ok 2 - preference defaults, user defaults, and category overrides compose without provider calls for skips
  ---
  duration_ms: 68.077333
  type: 'test'
  ...
# Subtest: same user and canonical payload is idempotent while changed payload conflicts
ok 3 - same user and canonical payload is idempotent while changed payload conflicts
  ---
  duration_ms: 59.040208
  type: 'test'
  ...
# Subtest: idempotency keys are scoped per user
ok 4 - idempotency keys are scoped per user
  ---
  duration_ms: 79.804583
  type: 'test'
  ...
# Subtest: invalid email and SMS are rejected before persistence or delivery
ok 5 - invalid email and SMS are rejected before persistence or delivery
  ---
  duration_ms: 12.339917
  type: 'test'
  ...
# Subtest: provider failures are isolated and persisted as delivery results
ok 6 - provider failures are isolated and persisted as delivery results
  ---
  duration_ms: 47.995583
  type: 'test'
  ...
# Subtest: concurrent mutations serialize and survive restart
ok 7 - concurrent mutations serialize and survive restart
  ---
  duration_ms: 303.309291
  type: 'test'
  ...
# Subtest: restart preserves idempotency and never redelivers
ok 8 - restart preserves idempotency and never redelivers
  ---
  duration_ms: 33.139
  type: 'test'
  ...
# Subtest: corrupt persistence is rejected and source bytes are not overwritten
ok 9 - corrupt persistence is rejected and source bytes are not overwritten
  ---
  duration_ms: 1.935
  type: 'test'
  ...
# Subtest: operator documentation includes configuration, safety, adapters, semantics, and API examples
ok 10 - operator documentation includes configuration, safety, adapters, semantics, and API examples
  ---
  duration_ms: 2.554167
  type: 'test'
  ...
# Subtest: health and preference endpoints expose defaults and category overrides
ok 11 - health and preference endpoints expose defaults and category overrides
  ---
  duration_ms: 83.973333
  type: 'test'
  ...
# Subtest: notification status is user-scoped and missing resources use stable 404 errors
ok 12 - notification status is user-scoped and missing resources use stable 404 errors
  ---
  duration_ms: 50.682583
  type: 'test'
  ...
# Subtest: in-app inbox paginates, filters unread items, and mark-read is user-scoped
ok 13 - in-app inbox paginates, filters unread items, and mark-read is user-scoped
  ---
  duration_ms: 156.922292
  type: 'test'
  ...
# Subtest: malformed JSON and unknown fields return structured 400 errors
ok 14 - malformed JSON and unknown fields return structured 400 errors
  ---
  duration_ms: 18.104792
  type: 'test'
  ...
# Subtest: pagination, content type, methods, and paths reject invalid requests consistently
ok 15 - pagination, content type, methods, and paths reject invalid requests consistently
  ---
  duration_ms: 19.721041
  type: 'test'
  ...
# Subtest: changed payload with a reused user idempotency key returns 409 without delivery
ok 16 - changed payload with a reused user idempotency key returns 409 without delivery
  ---
  duration_ms: 64.120917
  type: 'test'
  ...
1..16
# tests 16
# suites 0
# pass 16
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 709.045375

codex
Producer verification is fresh: syntax checks plus 16 TAP tests passed with `# fail 0`. The implemented API has strict routing/body/query validation, stable errors, scoped item lookups, and documented localhost/recording-provider safety defaults.

I’m starting the independent judge now with only the requirements, current tree, and acceptance contracts. It is read-only by instruction and will rerun the suite plus inspect the integration seams.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The independent review is still active. Its scope includes defects the current tests might miss—not just rerunning them—especially idempotency races, persistence recovery, preference precedence, user-scoped resource behavior, and whether the HTTP fallback truly exercises the same handler.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The judge has not reported a blocker yet and remains active. I’m holding completion until it either supplies fresh pass evidence or identifies a concrete seam defect; producer output alone does not satisfy this task’s assurance contract.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The independent judge rejected the build despite 16/16 producer tests. It reproduced four defects: reserved object keys can break user/idempotency isolation, separate core instances can overwrite each other, shallow state validation accepts malformed records, and a crash after reservation can leave delivery permanently `pending`.

This is a structural verification failure, so the prior pass evidence is invalidated. Per the `agentfw` recovery rule, I’m sending the findings—not the prior worker’s reasoning—to a fresh repair worker, with regression tests required for every reproduction.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
2026-07-13T18:23:05.928199Z ERROR codex_models_manager::manager: failed to refresh available models: stream disconnected before completion: error sending request for url (https://chatgpt.com/backend-api/codex/models?client_version=0.144.1)
2026-07-13T18:23:29.292840Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: IO error: Can't assign requested address (os error 49), url: wss://chatgpt.com/backend-api/codex/responses
2026-07-13T18:23:29.588730Z ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket: IO error: Can't assign requested address (os error 49), url: wss://chatgpt.com/backend-api/codex/responses
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The repair is underway with a bounded recovery contract: safe dictionary access, same-process coordination across cores sharing a file, deep persisted-state validation, and startup conversion of orphaned `pending` deliveries to a final `DELIVERY_INTERRUPTED` failure without provider calls. Cross-process single-writer limits must be documented rather than implied away.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The worker remains active and has not reported a conflict with the existing API. Once it finishes, I’ll rerun the entire suite and then use a new independent judge—the original failing judge will not validate its own requested fixes.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

2026-07-13T18:29:04.874504Z ERROR codex_models_manager::manager: failed to renew cache TTL: EOF while parsing a value at line 1 column 0
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
All four repairs are now in code and the original 16 tests still pass. The worker is finishing adversarial regressions and documentation for the process-bound coordination and interrupted-delivery semantics before producing fresh full-suite evidence.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '1,280p' src/core/json-store.js; sed -n '1,380p' src/core/notification-service.js" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
'use strict';

const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { CorruptStoreError } = require('./errors');

function clone(value) {
  return structuredClone(value);
}

// All store objects in this process that target the same resolved path share a
// queue. Transactions reload inside that queue so an independently-created
// store cannot commit a mutation based on stale cached state.
const pathQueues = new Map();

function enqueueForPath(filePath, operation) {
  const prior = pathQueues.get(filePath) ?? Promise.resolve();
  const result = prior.then(operation, operation);
  pathQueues.set(filePath, result.then(() => undefined, () => undefined));
  return result;
}

class AtomicJsonStore {
  #filePath;
  #initialState;
  #validate;

  constructor(filePath, { initialState, validate = () => true } = {}) {
    if (!filePath) throw new TypeError('filePath is required');
    if (initialState === undefined) throw new TypeError('initialState is required');
    this.#filePath = path.resolve(filePath);
    this.#initialState = clone(initialState);
    this.#validate = validate;
  }

  get filePath() {
    return this.#filePath;
  }

  initialize() {
    return this.#enqueue(async () => {
      return clone(await this.#load());
    });
  }

  read() {
    return this.#enqueue(async () => {
      return clone(await this.#load());
    });
  }

  transact(mutator) {
    if (typeof mutator !== 'function') throw new TypeError('mutator must be a function');
    return this.#enqueue(async () => {
      const candidate = clone(await this.#load());
      const result = await mutator(candidate);
      this.#assertValid(candidate);
      await this.#writeAtomic(candidate);
      return clone(result);
    });
  }

  #enqueue(operation) {
    return enqueueForPath(this.#filePath, operation);
  }

  async #load() {
    let contents;
    try {
      contents = await fs.readFile(this.#filePath, 'utf8');
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      const initial = clone(this.#initialState);
      this.#assertValid(initial);
      await this.#writeAtomic(initial);
      return initial;
    }

    try {
      const parsed = JSON.parse(contents);
      this.#assertValid(parsed);
      return parsed;
    } catch (error) {
      if (error instanceof CorruptStoreError) throw error;
      throw new CorruptStoreError(this.#filePath, error);
    }
  }

  #assertValid(state) {
    try {
      if (this.#validate(state) === false) throw new Error('State validation returned false');
    } catch (error) {
      throw new CorruptStoreError(this.#filePath, error);
    }
  }

  async #writeAtomic(state) {
    const directory = path.dirname(this.#filePath);
    await fs.mkdir(directory, { recursive: true });
    const tempPath = path.join(
      directory,
      `.${path.basename(this.#filePath)}.${process.pid}.${randomUUID()}.tmp`,
    );
    let handle;
    try {
      handle = await fs.open(tempPath, 'wx', 0o600);
      await handle.writeFile(`${JSON.stringify(state)}\n`, 'utf8');
      await handle.sync();
      await handle.close();
      handle = undefined;
      await fs.rename(tempPath, this.#filePath);

      // Persist the directory entry when the platform supports directory fsync.
      let directoryHandle;
      try {
        directoryHandle = await fs.open(directory, 'r');
        await directoryHandle.sync();
      } finally {
        await directoryHandle?.close();
      }
    } catch (error) {
      await handle?.close().catch(() => undefined);
      await fs.unlink(tempPath).catch(() => undefined);
      throw error;
    }
  }
}

module.exports = { AtomicJsonStore };
'use strict';

const { randomUUID } = require('node:crypto');
const {
  IdempotencyConflictError,
  ValidationError,
} = require('./errors');
const { createDefaultAdapters } = require('./providers');

const CHANNELS = Object.freeze(['email', 'sms', 'inApp']);
const DEFAULT_PREFERENCES = Object.freeze({ email: true, sms: true, inApp: true });
const DELIVERY_INTERRUPTED = Object.freeze({
  code: 'DELIVERY_INTERRUPTED',
  message: 'Delivery outcome is unknown because processing was interrupted',
});
const activeDeliveriesByStore = new Map();

function isRecord(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function hasOwn(record, key) {
  return Object.prototype.hasOwnProperty.call(record, key);
}

function getOwn(record, key) {
  return hasOwn(record, key) ? record[key] : undefined;
}

function setOwn(record, key, value) {
  Object.defineProperty(record, key, {
    value,
    enumerable: true,
    configurable: true,
    writable: true,
  });
}

function hasOnlyKeys(record, allowed) {
  return Object.keys(record).every((key) => allowed.includes(key));
}

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim() !== '';
}

function isTimestamp(value) {
  return isNonEmptyString(value) && !Number.isNaN(Date.parse(value));
}

function validateChannelSettings(settings) {
  return isRecord(settings) && Object.entries(settings).every(([channel, enabled]) =>
    CHANNELS.includes(channel) && typeof enabled === 'boolean');
}

function validatePreferences(preferences) {
  if (!isRecord(preferences)) return false;
  return Object.entries(preferences).every(([userId, stored]) => {
    if (!isNonEmptyString(userId) || !isRecord(stored)) return false;
    if (!hasOnlyKeys(stored, ['default', 'categories'])) return false;
    if (!hasOwn(stored, 'default') || !hasOwn(stored, 'categories')) return false;
    if (!validateChannelSettings(stored.default) || !isRecord(stored.categories)) return false;
    return Object.entries(stored.categories).every(([category, settings]) =>
      isNonEmptyString(category) && validateChannelSettings(settings));
  });
}

function validateContent(content) {
  if (!isRecord(content) || !hasOnlyKeys(content, ['subject', 'body'])) return false;
  if (!hasOwn(content, 'body') || !isNonEmptyString(content.body)) return false;
  return !hasOwn(content, 'subject') || isNonEmptyString(content.subject);
}

function validateDelivery(delivery) {
  if (!isRecord(delivery) || !hasOwn(delivery, 'channel') ||
      !hasOwn(delivery, 'recipient') || !hasOwn(delivery, 'status')) return false;
  if (!CHANNELS.includes(delivery.channel) || !isNonEmptyString(delivery.recipient)) return false;

  if (delivery.status === 'pending') {
    return hasOnlyKeys(delivery, ['channel', 'recipient', 'status']);
  }
  if (delivery.status === 'skipped') {
    return hasOnlyKeys(delivery, ['channel', 'recipient', 'status', 'reason']) &&
      delivery.reason === 'preference_disabled';
  }
  if (delivery.status === 'delivered') {
    if (!hasOnlyKeys(delivery, ['channel', 'recipient', 'status', 'providerResult', 'readAt'])) return false;
    return !hasOwn(delivery, 'readAt') || isTimestamp(delivery.readAt);
  }
  if (delivery.status === 'failed') {
    if (!hasOnlyKeys(delivery, ['channel', 'recipient', 'status', 'error']) ||
        !hasOwn(delivery, 'error') || !isRecord(delivery.error)) return false;
    return hasOnlyKeys(delivery.error, ['code', 'message']) &&
      hasOwn(delivery.error, 'code') && hasOwn(delivery.error, 'message') &&
      isNonEmptyString(delivery.error.code) && isNonEmptyString(delivery.error.message);
  }
  return false;
}

function validateNotifications(notifications) {
  if (!isRecord(notifications)) return false;
  return Object.entries(notifications).every(([notificationId, notification]) => {
    if (!isRecord(notification) ||
        !hasOnlyKeys(notification, [
          'id', 'userId', 'idempotencyKey', 'category', 'content', 'createdAt', 'deliveries', 'completedAt',
        ])) return false;
    for (const key of ['id', 'userId', 'idempotencyKey', 'category', 'content', 'createdAt', 'deliveries']) {
      if (!hasOwn(notification, key)) return false;
    }
    if (notification.id !== notificationId || !isNonEmptyString(notification.id) ||
        !isNonEmptyString(notification.userId) || !isNonEmptyString(notification.idempotencyKey) ||
        !isNonEmptyString(notification.category) || !validateContent(notification.content) ||
        !isTimestamp(notification.createdAt) || !Array.isArray(notification.deliveries) ||
        notification.deliveries.length === 0 || notification.deliveries.length > CHANNELS.length) return false;
    if (!notification.deliveries.every(validateDelivery)) return false;
    const deliveryChannels = notification.deliveries.map((delivery) => delivery.channel);
    if (new Set(deliveryChannels).size !== deliveryChannels.length) return false;
    if (hasOwn(notification, 'completedAt')) {
      if (!isTimestamp(notification.completedAt) ||
          notification.deliveries.some((delivery) => delivery.status === 'pending')) return false;
    }
    return true;
  });
}

function validateIdempotency(idempotency, notifications) {
  if (!isRecord(idempotency)) return false;
  const referencedNotifications = new Set();
  const entriesAreValid = Object.entries(idempotency).every(([userId, keys]) => {
    if (!isNonEmptyString(userId) || !isRecord(keys)) return false;
    return Object.entries(keys).every(([idempotencyKey, entry]) => {
      if (!isNonEmptyString(idempotencyKey) || !isRecord(entry) ||
          !hasOnlyKeys(entry, ['fingerprint', 'notificationId']) ||
          !hasOwn(entry, 'fingerprint') || !hasOwn(entry, 'notificationId') ||
          !isNonEmptyString(entry.fingerprint) || !isNonEmptyString(entry.notificationId)) return false;
      const notification = getOwn(notifications, entry.notificationId);
      if (notification === undefined || notification.userId !== userId ||
          notification.idempotencyKey !== idempotencyKey ||
          referencedNotifications.has(entry.notificationId)) return false;
      referencedNotifications.add(entry.notificationId);
      return true;
    });
  });
  return entriesAreValid && referencedNotifications.size === Object.keys(notifications).length;
}

function createInitialState() {
  return {
    version: 1,
    preferences: {},
    notifications: {},
    idempotency: {},
  };
}

function validateState(state) {
  if (!isRecord(state) || !hasOwn(state, 'version') || state.version !== 1 ||
      !hasOnlyKeys(state, ['version', 'preferences', 'notifications', 'idempotency'])) return false;
  for (const key of ['preferences', 'notifications', 'idempotency']) {
    if (!hasOwn(state, key)) return false;
  }
  return validatePreferences(state.preferences) &&
    validateNotifications(state.notifications) &&
    validateIdempotency(state.idempotency, state.notifications);
}

function stableStringify(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  const keys = Object.keys(value).sort();
  return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
}

function requireNonEmptyString(value, field) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new ValidationError(`${field} must be a non-empty string`, { field });
  }
  return value.trim();
}

function normalizeChannels(channels) {
  if (!Array.isArray(channels) || channels.length === 0) {
    throw new ValidationError('channels must be a non-empty array', { field: 'channels' });
  }
  const requested = new Set(channels);
  for (const channel of requested) {
    if (!CHANNELS.includes(channel)) {
      throw new ValidationError(`Unsupported channel: ${channel}`, { field: 'channels', channel });
    }
  }
  return CHANNELS.filter((channel) => requested.has(channel));
}

function normalizeRecipients(channels, recipients, userId) {
  if (!recipients || typeof recipients !== 'object' || Array.isArray(recipients)) {
    throw new ValidationError('recipients must be an object', { field: 'recipients' });
  }
  const normalized = {};
  if (channels.includes('email')) {
    const email = requireNonEmptyString(recipients.email, 'recipients.email').toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new ValidationError('recipients.email is invalid', { field: 'recipients.email' });
    }
    normalized.email = email;
  }
  if (channels.includes('sms')) {
    const sms = requireNonEmptyString(recipients.sms, 'recipients.sms');
    if (!/^\+[1-9]\d{7,14}$/.test(sms)) {
      throw new ValidationError('recipients.sms must be an E.164 number', { field: 'recipients.sms' });
    }
    normalized.sms = sms;
  }
  if (channels.includes('inApp')) {
    if (recipients.inApp !== undefined && recipients.inApp !== userId) {
      throw new ValidationError('recipients.inApp must match userId', { field: 'recipients.inApp' });
    }
    normalized.inApp = userId;
  }
  return normalized;
}

function normalizeContent(content) {
  if (!content || typeof content !== 'object' || Array.isArray(content)) {
    throw new ValidationError('content must be an object', { field: 'content' });
  }
  const body = requireNonEmptyString(content.body, 'content.body');
  const normalized = { body };
  if (content.subject !== undefined) {
    normalized.subject = requireNonEmptyString(content.subject, 'content.subject');
  }
  return normalized;
}

function validateOverrides(overrides) {
  if (!overrides || typeof overrides !== 'object' || Array.isArray(overrides)) {
    throw new ValidationError('preferences must be an object', { field: 'preferences' });
  }
  const normalized = {};
  for (const [channel, value] of Object.entries(overrides)) {
    if (!CHANNELS.includes(channel)) {
      throw new ValidationError(`Unsupported preference channel: ${channel}`, { channel });
    }
    if (typeof value !== 'boolean') {
      throw new ValidationError(`Preference ${channel} must be boolean`, { channel });
    }
    normalized[channel] = value;
  }
  return normalized;
}

class NotificationService {
  constructor({ store, adapters = createDefaultAdapters(), clock = () => new Date(), idGenerator = randomUUID } = {}) {
    if (!store || typeof store.transact !== 'function' || typeof store.read !== 'function') {
      throw new TypeError('store must expose read() and transact()');
    }
    for (const channel of CHANNELS) {
      if (!adapters[channel] || typeof adapters[channel].deliver !== 'function') {
        throw new TypeError(`Missing ${channel} adapter`);
      }
    }
    this.store = store;
    this.adapters = adapters;
    this.clock = clock;
    this.idGenerator = idGenerator;
    const activeKey = typeof store.filePath === 'string' ? store.filePath : store;
    if (!activeDeliveriesByStore.has(activeKey)) activeDeliveriesByStore.set(activeKey, new Set());
    this.activeDeliveries = activeDeliveriesByStore.get(activeKey);
  }

  async initialize() {
    const initialized = await (this.store.initialize?.() ?? this.store.read());
    const needsRecovery = Object.values(initialized.notifications).some((notification) =>
      !this.activeDeliveries.has(notification.id) &&
      (!hasOwn(notification, 'completedAt') ||
        notification.deliveries.some((delivery) => delivery.status === 'pending')));
    if (!needsRecovery) return initialized;

    return this.store.transact((state) => {
      for (const notification of Object.values(state.notifications)) {
        if (this.activeDeliveries.has(notification.id) || hasOwn(notification, 'completedAt')) continue;
        for (const delivery of notification.deliveries) {
          if (delivery.status === 'pending') {
            delivery.status = 'failed';
            delivery.error = { ...DELIVERY_INTERRUPTED };
          }
        }
        notification.completedAt = this.clock().toISOString();
      }
      return state;
    });
  }

  async getPreferences(userId, category) {
    userId = requireNonEmptyString(userId, 'userId');
    category = requireNonEmptyString(category, 'category');
    const state = await this.store.read();
    return this.#resolvePreferences(state, userId, category);
  }

  async setPreferences(userId, category, overrides) {
    userId = requireNonEmptyString(userId, 'userId');
    category = requireNonEmptyString(category, 'category');
    const normalized = validateOverrides(overrides);
    return this.store.transact((state) => {
      const userPreferences = getOwn(state.preferences, userId) ?? { default: {}, categories: {} };
      if (category === 'default') {
        userPreferences.default = { ...userPreferences.default, ...normalized };
      } else {
        setOwn(userPreferences.categories, category, {
          ...getOwn(userPreferences.categories, category),
          ...normalized,
        });
      }
      setOwn(state.preferences, userId, userPreferences);
      return this.#resolvePreferences(state, userId, category);
    });
  }

  async dispatch(input) {
    const request = this.#normalizeDispatch(input);
    const fingerprint = stableStringify(request);
    const createdAt = this.clock().toISOString();
    const id = this.idGenerator();

    let active = false;
    let reservation;
    try {
      reservation = await this.store.transact((state) => {
        const userKeys = getOwn(state.idempotency, request.userId) ?? {};
        const prior = getOwn(userKeys, request.idempotencyKey);
        if (prior !== undefined) {
          if (prior.fingerprint !== fingerprint) {
            throw new IdempotencyConflictError(request.userId, request.idempotencyKey);
          }
          return { existing: true, notification: getOwn(state.notifications, prior.notificationId) };
        }

        const preferences = this.#resolvePreferences(state, request.userId, request.category);
        const deliveries = request.channels.map((channel) => ({
          channel,
          recipient: request.recipients[channel],
          status: preferences[channel] ? 'pending' : 'skipped',
          ...(preferences[channel] ? {} : { reason: 'preference_disabled' }),
        }));
        const notification = {
          id,
          userId: request.userId,
          idempotencyKey: request.idempotencyKey,
          category: request.category,
          content: request.content,
          createdAt,
          deliveries,
        };
        setOwn(state.notifications, id, notification);
        setOwn(userKeys, request.idempotencyKey, { fingerprint, notificationId: id });
        setOwn(state.idempotency, request.userId, userKeys);
        this.activeDeliveries.add(id);
        active = true;
        return { existing: false, notification };
      });
    } catch (error) {
      if (active) this.activeDeliveries.delete(id);
      throw error;
    }

    if (reservation.existing) return reservation.notification;

    try {
      const attempted = await Promise.all(reservation.notification.deliveries.map(async (delivery) => {
        if (delivery.status === 'skipped') return delivery;
        try {
          const providerResult = await this.adapters[delivery.channel].deliver({
            notificationId: reservation.notification.id,
            userId: request.userId,
            category: request.category,
            recipient: delivery.recipient,
            content: request.content,
            createdAt,

exec
/bin/zsh -lc "sed -n '130,360p' test/core.test.js; sed -n '1,220p' test/docs.test.js; rg -n \"single|pending|interrupt|process|delivery|guarantee\" README.md" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
    email: true, sms: false, inApp: true,
  });

  const prototypeRequest = request({
    userId: '__proto__',
    idempotencyKey: '__proto__',
    category: '__proto__',
    channels: ['email', 'inApp'],
    recipients: { email: 'proto@example.com', inApp: '__proto__' },
  });
  const first = await core.service.dispatch(prototypeRequest);
  const otherUser = await core.service.dispatch(request({
    userId: 'user-2',
    idempotencyKey: '__proto__',
    category: '__proto__',
    channels: ['inApp'],
    recipients: { inApp: 'user-2' },
    content: { body: 'The same key is valid for another user.' },
  }));
  assert.notEqual(otherUser.id, first.id);

  const persisted = JSON.parse(await fs.readFile(core.filePath, 'utf8'));
  assert.equal(Object.hasOwn(persisted.preferences, '__proto__'), true);
  assert.equal(Object.hasOwn(persisted.preferences.__proto__.categories, '__proto__'), true);
  assert.equal(Object.hasOwn(persisted.idempotency, '__proto__'), true);
  assert.equal(Object.hasOwn(persisted.idempotency.__proto__, '__proto__'), true);
  assert.equal({}.email, undefined);

  const restartedProvider = new RecordingProvider('email');
  const restarted = createNotificationCore({
    filePath: core.filePath,
    adapters: {
      email: new EmailAdapter(restartedProvider),
      sms: new SmsAdapter(),
      inApp: new InAppAdapter(),
    },
  });
  await restarted.service.initialize();
  assert.deepEqual(await restarted.service.getPreferences('__proto__', '__proto__'), {
    email: true, sms: false, inApp: true,
  });
  assert.deepEqual(await restarted.service.dispatch(prototypeRequest), first);
  assert.equal(restartedProvider.calls.length, 0);
});

test('invalid email and SMS are rejected before persistence or delivery', async (t) => {
  const core = await fixture();
  t.after(() => fs.rm(core.directory, { recursive: true, force: true }));
  const before = await fs.readFile(core.filePath, 'utf8');

  await assert.rejects(
    core.service.dispatch(request({ recipients: { email: 'bad', sms: '+13125550123', inApp: 'user-1' } })),
    ValidationError,
  );
  await assert.rejects(
    core.service.dispatch(request({ recipients: { email: 'ok@example.com', sms: '555-0123', inApp: 'user-1' } })),
    ValidationError,
  );

  assert.equal(await fs.readFile(core.filePath, 'utf8'), before);
  assert.equal(core.adapters.email.provider.calls.length, 0);
  assert.equal(core.adapters.sms.provider.calls.length, 0);
  assert.equal(core.adapters.inApp.provider.calls.length, 0);
});

test('provider failures are isolated and persisted as delivery results', async (t) => {
  const failingEmail = { async send() { throw Object.assign(new Error('offline'), { code: 'OFFLINE' }); } };
  const core = await fixture({
    adapters: {
      email: new EmailAdapter(failingEmail),
      sms: new SmsAdapter(),
      inApp: new InAppAdapter(),
    },
  });
  t.after(() => fs.rm(core.directory, { recursive: true, force: true }));

  const result = await core.service.dispatch(request({ channels: ['email', 'sms'] }));
  assert.equal(result.deliveries[0].status, 'failed');
  assert.deepEqual(result.deliveries[0].error, { code: 'OFFLINE', message: 'offline' });
  assert.equal(result.deliveries[1].status, 'delivered');
  assert.deepEqual(await core.service.getNotification('user-1', result.id), result);
});

test('concurrent mutations serialize and survive restart', async (t) => {
  const core = await fixture();
  t.after(() => fs.rm(core.directory, { recursive: true, force: true }));

  await Promise.all(Array.from({ length: 30 }, (_, index) =>
    core.service.setPreferences('user-1', `category-${index}`, { sms: index % 2 === 0 })));

  const restarted = createNotificationCore({ filePath: core.filePath });
  await restarted.service.initialize();
  const state = await restarted.store.read();
  assert.equal(Object.keys(state.preferences['user-1'].categories).length, 30);
  assert.deepEqual(await restarted.service.getPreferences('user-1', 'category-8'), {
    email: true, sms: true, inApp: true,
  });
  assert.doesNotThrow(() => JSON.parse(require('node:fs').readFileSync(core.filePath, 'utf8')));
});

test('independent cores sharing one file do not lose concurrent mutations', async (t) => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'notification-shared-store-'));
  const filePath = path.join(directory, 'data.json');
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const first = createNotificationCore({ filePath });
  const second = createNotificationCore({ filePath });
  await Promise.all([first.service.initialize(), second.service.initialize()]);

  await Promise.all([
    first.service.setPreferences('user-a', 'security', { email: false }),
    second.service.setPreferences('user-b', 'billing', { sms: false }),
  ]);

  const restarted = createNotificationCore({ filePath });
  await restarted.service.initialize();
  assert.deepEqual(await restarted.service.getPreferences('user-a', 'security'), {
    email: false, sms: true, inApp: true,
  });
  assert.deepEqual(await restarted.service.getPreferences('user-b', 'billing'), {
    email: true, sms: false, inApp: true,
  });
});

test('restart preserves idempotency and never redelivers', async (t) => {
  const firstCore = await fixture();
  t.after(() => fs.rm(firstCore.directory, { recursive: true, force: true }));
  const initial = await firstCore.service.dispatch(request({ channels: ['email'] }));

  const provider = new RecordingProvider('email');
  const restarted = createNotificationCore({
    filePath: firstCore.filePath,
    adapters: {
      email: new EmailAdapter(provider),
      sms: new SmsAdapter(),
      inApp: new InAppAdapter(),
    },
  });
  await restarted.service.initialize();
  const repeated = await restarted.service.dispatch(request({ channels: ['email'] }));

  assert.deepEqual(repeated, initial);
  assert.equal(provider.calls.length, 0);
});

test('corrupt persistence is rejected and source bytes are not overwritten', async (t) => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'notification-corrupt-'));
  const filePath = path.join(directory, 'data.json');
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const corrupt = '{ definitely not json';
  await fs.writeFile(filePath, corrupt);

  const core = createNotificationCore({ filePath });
  await assert.rejects(core.service.initialize(), (error) =>
    error instanceof CorruptStoreError && error.code === 'CORRUPT_STORE');
  assert.equal(await fs.readFile(filePath, 'utf8'), corrupt);
});

test('malformed nested persisted structures are rejected without changing source bytes', async (t) => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'notification-malformed-state-'));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const notification = {
    id: 'notification-1',
    userId: 'user-1',
    idempotencyKey: 'request-1',
    category: 'security',
    content: { body: 'Stored message' },
    createdAt: '2026-07-13T12:00:00.000Z',
    deliveries: [{
      channel: 'inApp', recipient: 'user-1', status: 'delivered', providerResult: null,
    }],
    completedAt: '2026-07-13T12:00:01.000Z',
  };
  const base = {
    version: 1,
    preferences: { 'user-1': { default: {}, categories: {} } },
    notifications: { 'notification-1': notification },
    idempotency: {
      'user-1': {
        'request-1': { fingerprint: 'stored-fingerprint', notificationId: 'notification-1' },
      },
    },
  };
  const malformedStates = [
    { ...base, notifications: { 'notification-1': { ...notification, deliveries: undefined } } },
    { ...base, notifications: {
      'notification-1': { ...notification, deliveries: { channel: 'inApp' } },
    } },
    { ...base, preferences: { 'user-1': { default: [], categories: {} } } },
    { ...base, idempotency: { 'user-1': { 'request-1': { notificationId: 'notification-1' } } } },
    { ...base, idempotency: {} },
  ];

  for (const [index, state] of malformedStates.entries()) {
    const filePath = path.join(directory, `data-${index}.json`);
    const bytes = JSON.stringify(state);
    await fs.writeFile(filePath, bytes);
    const core = createNotificationCore({ filePath });
    await assert.rejects(core.service.initialize(), (error) =>
      error instanceof CorruptStoreError && error.code === 'CORRUPT_STORE');
    assert.equal(await fs.readFile(filePath, 'utf8'), bytes);
  }
});

test('initialization finalizes orphaned pending deliveries without redelivery', async (t) => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'notification-pending-recovery-'));
  const filePath = path.join(directory, 'data.json');
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const pendingRequest = request({
    channels: ['email'],
    recipients: { email: 'user@example.com' },
  });
  const fingerprint = stableStringify({
    userId: 'user-1',
    idempotencyKey: 'request-1',
    category: 'security',
    channels: ['email'],
    recipients: { email: 'user@example.com' },
    content: { body: 'A new sign-in occurred.', subject: 'Sign in' },
  });
  const pendingState = {
    version: 1,
    preferences: {},
    notifications: {
      'notification-1': {
        id: 'notification-1',
        userId: 'user-1',
        idempotencyKey: 'request-1',
        category: 'security',
        content: { body: 'A new sign-in occurred.', subject: 'Sign in' },
        createdAt: '2026-07-13T12:00:00.000Z',
        deliveries: [{ channel: 'email', recipient: 'user@example.com', status: 'pending' }],
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

test('operator documentation includes configuration, safety, adapters, semantics, and API examples', async () => {
  const readme = await fs.readFile(path.join(__dirname, '..', 'README.md'), 'utf8');
  for (const required of [
    'DATA_FILE',
    'HOST',
    '127.0.0.1',
    'Provider adapter integration',
    'Preference semantics',
    'Safe defaults',
    'GET /api/v1/health',
    'PUT /api/v1/users/:userId/preferences/:category',
    'POST /api/v1/notifications',
    'GET /api/v1/users/:userId/notifications/:notificationId',
    'GET /api/v1/users/:userId/inbox',
    'PUT /api/v1/users/:userId/inbox/:notificationId/read',
    'INVALID_PAGINATION',
    'IDEMPOTENCY_CONFLICT',
    'DELIVERY_INTERRUPTED',
    'exactly one writer process per `DATA_FILE`',
    'at-most-once',
    'at-least-once',
  ]) {
    assert.ok(readme.includes(required), `README must document ${required}`);
  }

  const packageJson = JSON.parse(await fs.readFile(path.join(__dirname, '..', 'package.json'), 'utf8'));
  assert.match(packageJson.scripts.test, /node --check src\/server\.js/);
  assert.match(packageJson.scripts.test, /node --check src\/http\/app\.js/);
  assert.match(packageJson.scripts.test, /test\/core\.test\.js/);
  assert.match(packageJson.scripts.test, /test\/http\.test\.js/);
  assert.match(packageJson.scripts.test, /test\/docs\.test\.js/);

  const serverSource = await fs.readFile(path.join(__dirname, '..', 'src', 'server.js'), 'utf8');
  assert.match(serverSource, /environment\.HOST \|\| '127\.0\.0\.1'/);
  assert.match(serverSource, /environment\.DATA_FILE \|\| path\.join\('data', 'notifications\.json'\)/);
});
3:This Node.js service persists notification preferences and delivery results in one atomically
5:offers a versioned JSON REST API. It has no runtime dependencies and performs no network delivery
27:The process binds to `127.0.0.1`, default providers only record delivery attempts in memory, JSON
38:appears in the inbox only when its in-app delivery completed successfully.
75:notification without redelivery. Reusing that key for a changed payload returns HTTP 409 with
86:Pass adapters when creating the core. Each adapter wraps a provider exposing async `send(delivery)`;
87:the return value becomes the delivery's `providerResult`, while thrown errors become a per-channel
96:  filePath: process.env.DATA_FILE,
98:    email: new EmailAdapter({ async send(delivery) { return emailClient.send(delivery); } }),
99:    sms: new SmsAdapter({ async send(delivery) { return smsClient.send(delivery); } }),
100:    inApp: new InAppAdapter({ async send(delivery) { return { accepted: true, id: delivery.notificationId }; } }),
108:## Persistence, concurrency, and interruption semantics
112:source bytes. Store instances in the same Node.js process coordinate by resolved data-file path and
114:one process do not overwrite each other.
116:There is no cross-process file lock. Run exactly one writer process per `DATA_FILE`; two Node.js
117:processes writing the same path can race and lose an update. For multi-process deployment, give each
118:process a separate file or replace the store with a database that supplies transactional locking.
120:Dispatch durably reserves the notification and idempotency key with `pending` deliveries before it
121:calls providers. On initialization, a reserved delivery still left `pending` is finalized as
124:service-initiated provider attempts over automatic redelivery. It is not an end-to-end exactly-once
125:or at-least-once delivery guarantee: if interruption happens after a provider accepted a delivery
126:but before the final result was persisted, the external delivery may have occurred even though the

hook: PostToolUse
hook: PostToolUse
hook: PostToolUse Completed
hook: PostToolUse Completed
exec
/bin/zsh -lc 'npm test' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

 succeeded in 1094ms:
TAP version 13
# Subtest: default adapters deliver email, SMS, and in-app with inspectable results
ok 1 - default adapters deliver email, SMS, and in-app with inspectable results
  ---
  duration_ms: 41.903958
  type: 'test'
  ...
# Subtest: preference defaults, user defaults, and category overrides compose without provider calls for skips
ok 2 - preference defaults, user defaults, and category overrides compose without provider calls for skips
  ---
  duration_ms: 66.072959
  type: 'test'
  ...
# Subtest: same user and canonical payload is idempotent while changed payload conflicts
ok 3 - same user and canonical payload is idempotent while changed payload conflicts
  ---
  duration_ms: 51.893875
  type: 'test'
  ...
# Subtest: idempotency keys are scoped per user
ok 4 - idempotency keys are scoped per user
  ---
  duration_ms: 72.821125
  type: 'test'
  ...
# Subtest: __proto__ values remain own map keys across users and restart
ok 5 - __proto__ values remain own map keys across users and restart
  ---
  duration_ms: 110.03625
  type: 'test'
  ...
# Subtest: invalid email and SMS are rejected before persistence or delivery
ok 6 - invalid email and SMS are rejected before persistence or delivery
  ---
  duration_ms: 18.854625
  type: 'test'
  ...
# Subtest: provider failures are isolated and persisted as delivery results
ok 7 - provider failures are isolated and persisted as delivery results
  ---
  duration_ms: 31.516625
  type: 'test'
  ...
# Subtest: concurrent mutations serialize and survive restart
ok 8 - concurrent mutations serialize and survive restart
  ---
  duration_ms: 253.994
  type: 'test'
  ...
# Subtest: independent cores sharing one file do not lose concurrent mutations
ok 9 - independent cores sharing one file do not lose concurrent mutations
  ---
  duration_ms: 26.738916
  type: 'test'
  ...
# Subtest: restart preserves idempotency and never redelivers
ok 10 - restart preserves idempotency and never redelivers
  ---
  duration_ms: 38.316667
  type: 'test'
  ...
# Subtest: corrupt persistence is rejected and source bytes are not overwritten
ok 11 - corrupt persistence is rejected and source bytes are not overwritten
  ---
  duration_ms: 1.625291
  type: 'test'
  ...
# Subtest: malformed nested persisted structures are rejected without changing source bytes
ok 12 - malformed nested persisted structures are rejected without changing source bytes
  ---
  duration_ms: 3.657416
  type: 'test'
  ...
# Subtest: initialization finalizes orphaned pending deliveries without redelivery
ok 13 - initialization finalizes orphaned pending deliveries without redelivery
  ---
  duration_ms: 18.437125
  type: 'test'
  ...
# Subtest: operator documentation includes configuration, safety, adapters, semantics, and API examples
ok 14 - operator documentation includes configuration, safety, adapters, semantics, and API examples
  ---
  duration_ms: 2.499208
  type: 'test'
  ...
# Subtest: health and preference endpoints expose defaults and category overrides
ok 15 - health and preference endpoints expose defaults and category overrides
  ---
  duration_ms: 90.360583
  type: 'test'
  ...
# Subtest: notification status is user-scoped and missing resources use stable 404 errors
ok 16 - notification status is user-scoped and missing resources use stable 404 errors
  ---
  duration_ms: 42.364958
  type: 'test'
  ...
# Subtest: in-app inbox paginates, filters unread items, and mark-read is user-scoped
ok 17 - in-app inbox paginates, filters unread items, and mark-read is user-scoped
  ---
  duration_ms: 146.989291
  type: 'test'
  ...
# Subtest: malformed JSON and unknown fields return structured 400 errors
ok 18 - malformed JSON and unknown fields return structured 400 errors
  ---
  duration_ms: 21.05675
  type: 'test'
  ...
# Subtest: pagination, content type, methods, and paths reject invalid requests consistently
ok 19 - pagination, content type, methods, and paths reject invalid requests consistently
  ---
  duration_ms: 19.776542
  type: 'test'
  ...
# Subtest: changed payload with a reused user idempotency key returns 409 without delivery
ok 20 - changed payload with a reused user idempotency key returns 409 without delivery
  ---
  duration_ms: 52.024833
  type: 'test'
  ...
1..20
# tests 20
# suites 0
# pass 20
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 802.527708

hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc "sed -n '280,440p' src/core/notification-service.js; sed -n '340,520p' test/core.test.js; sed -n '104,145p' README.md" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
    return this.store.transact((state) => {
      for (const notification of Object.values(state.notifications)) {
        if (this.activeDeliveries.has(notification.id) || hasOwn(notification, 'completedAt')) continue;
        for (const delivery of notification.deliveries) {
          if (delivery.status === 'pending') {
            delivery.status = 'failed';
            delivery.error = { ...DELIVERY_INTERRUPTED };
          }
        }
        notification.completedAt = this.clock().toISOString();
      }
      return state;
    });
  }

  async getPreferences(userId, category) {
    userId = requireNonEmptyString(userId, 'userId');
    category = requireNonEmptyString(category, 'category');
    const state = await this.store.read();
    return this.#resolvePreferences(state, userId, category);
  }

  async setPreferences(userId, category, overrides) {
    userId = requireNonEmptyString(userId, 'userId');
    category = requireNonEmptyString(category, 'category');
    const normalized = validateOverrides(overrides);
    return this.store.transact((state) => {
      const userPreferences = getOwn(state.preferences, userId) ?? { default: {}, categories: {} };
      if (category === 'default') {
        userPreferences.default = { ...userPreferences.default, ...normalized };
      } else {
        setOwn(userPreferences.categories, category, {
          ...getOwn(userPreferences.categories, category),
          ...normalized,
        });
      }
      setOwn(state.preferences, userId, userPreferences);
      return this.#resolvePreferences(state, userId, category);
    });
  }

  async dispatch(input) {
    const request = this.#normalizeDispatch(input);
    const fingerprint = stableStringify(request);
    const createdAt = this.clock().toISOString();
    const id = this.idGenerator();

    let active = false;
    let reservation;
    try {
      reservation = await this.store.transact((state) => {
        const userKeys = getOwn(state.idempotency, request.userId) ?? {};
        const prior = getOwn(userKeys, request.idempotencyKey);
        if (prior !== undefined) {
          if (prior.fingerprint !== fingerprint) {
            throw new IdempotencyConflictError(request.userId, request.idempotencyKey);
          }
          return { existing: true, notification: getOwn(state.notifications, prior.notificationId) };
        }

        const preferences = this.#resolvePreferences(state, request.userId, request.category);
        const deliveries = request.channels.map((channel) => ({
          channel,
          recipient: request.recipients[channel],
          status: preferences[channel] ? 'pending' : 'skipped',
          ...(preferences[channel] ? {} : { reason: 'preference_disabled' }),
        }));
        const notification = {
          id,
          userId: request.userId,
          idempotencyKey: request.idempotencyKey,
          category: request.category,
          content: request.content,
          createdAt,
          deliveries,
        };
        setOwn(state.notifications, id, notification);
        setOwn(userKeys, request.idempotencyKey, { fingerprint, notificationId: id });
        setOwn(state.idempotency, request.userId, userKeys);
        this.activeDeliveries.add(id);
        active = true;
        return { existing: false, notification };
      });
    } catch (error) {
      if (active) this.activeDeliveries.delete(id);
      throw error;
    }

    if (reservation.existing) return reservation.notification;

    try {
      const attempted = await Promise.all(reservation.notification.deliveries.map(async (delivery) => {
        if (delivery.status === 'skipped') return delivery;
        try {
          const providerResult = await this.adapters[delivery.channel].deliver({
            notificationId: reservation.notification.id,
            userId: request.userId,
            category: request.category,
            recipient: delivery.recipient,
            content: request.content,
            createdAt,
          });
          return { ...delivery, status: 'delivered', providerResult: providerResult ?? null };
        } catch (error) {
          return {
            ...delivery,
            status: 'failed',
            error: {
              code: typeof error.code === 'string' ? error.code : 'PROVIDER_ERROR',
              message: typeof error.message === 'string' && error.message !== ''
                ? error.message
                : 'Provider delivery failed',
            },
          };
        }
      }));

      return await this.store.transact((state) => {
        const notification = getOwn(state.notifications, id);
        notification.deliveries = attempted;
        notification.completedAt = this.clock().toISOString();
        return notification;
      });
    } finally {
      this.activeDeliveries.delete(id);
    }
  }

  async getNotification(userId, notificationId) {
    userId = requireNonEmptyString(userId, 'userId');
    notificationId = requireNonEmptyString(notificationId, 'notificationId');
    const state = await this.store.read();
    const notification = getOwn(state.notifications, notificationId);
    return notification?.userId === userId ? notification : null;
  }

  async listInbox(userId, { offset = 0, limit = 20, unread = false } = {}) {
    userId = requireNonEmptyString(userId, 'userId');
    if (!Number.isSafeInteger(offset) || offset < 0) {
      throw new ValidationError('offset must be a non-negative integer', { field: 'offset' });
    }
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
      throw new ValidationError('limit must be an integer between 1 and 100', { field: 'limit' });
    }
    if (typeof unread !== 'boolean') {
      throw new ValidationError('unread must be boolean', { field: 'unread' });
    }

    const state = await this.store.read();
    const matching = Object.values(state.notifications)
      .filter((notification) => notification.userId === userId)
      .map((notification) => this.#toInboxItem(notification))
      .filter((item) => item !== null && (!unread || item.readAt === null))
      .sort((left, right) =>
        right.createdAt.localeCompare(left.createdAt) || right.notificationId.localeCompare(left.notificationId));
    const items = matching.slice(offset, offset + limit);
    const nextOffset = offset + items.length < matching.length ? offset + items.length : null;

    return {
      items,
      pagination: { offset, limit, total: matching.length, nextOffset },
  });
  const fingerprint = stableStringify({
    userId: 'user-1',
    idempotencyKey: 'request-1',
    category: 'security',
    channels: ['email'],
    recipients: { email: 'user@example.com' },
    content: { body: 'A new sign-in occurred.', subject: 'Sign in' },
  });
  const pendingState = {
    version: 1,
    preferences: {},
    notifications: {
      'notification-1': {
        id: 'notification-1',
        userId: 'user-1',
        idempotencyKey: 'request-1',
        category: 'security',
        content: { body: 'A new sign-in occurred.', subject: 'Sign in' },
        createdAt: '2026-07-13T12:00:00.000Z',
        deliveries: [{ channel: 'email', recipient: 'user@example.com', status: 'pending' }],
      },
    },
    idempotency: {
      'user-1': {
        'request-1': { fingerprint, notificationId: 'notification-1' },
      },
    },
  };
  await fs.writeFile(filePath, JSON.stringify(pendingState));

  const provider = new RecordingProvider('email');
  const core = createNotificationCore({
    filePath,
    clock: () => new Date('2026-07-13T12:05:00.000Z'),
    adapters: {
      email: new EmailAdapter(provider),
      sms: new SmsAdapter(),
      inApp: new InAppAdapter(),
    },
  });
  const recovered = await core.service.initialize();
  assert.equal(recovered.notifications['notification-1'].completedAt, '2026-07-13T12:05:00.000Z');
  assert.deepEqual(recovered.notifications['notification-1'].deliveries[0], {
    channel: 'email',
    recipient: 'user@example.com',
    status: 'failed',
    error: {
      code: 'DELIVERY_INTERRUPTED',
      message: 'Delivery outcome is unknown because processing was interrupted',
    },
  });
  assert.deepEqual(await core.service.dispatch(pendingRequest), recovered.notifications['notification-1']);
  assert.equal(provider.calls.length, 0);

  const bytesAfterRecovery = await fs.readFile(filePath, 'utf8');
  const restarted = createNotificationCore({ filePath });
  await restarted.service.initialize();
  assert.equal(await fs.readFile(filePath, 'utf8'), bytesAfterRecovery);
  assert.equal(restarted.adapters.email.provider.calls.length, 0);
});

Initialize the service before handling requests. Provider implementations own their outbound I/O,
credentials, retry policy, and timeouts; the bundled service itself uses no third-party services.

## Persistence, concurrency, and interruption semantics

Each update is written to a same-directory temporary file, synchronized, and atomically renamed
over `DATA_FILE`; malformed existing state is rejected as `CORRUPT_STORE` without rewriting the
source bytes. Store instances in the same Node.js process coordinate by resolved data-file path and
reload state inside their shared transaction queue, so concurrent mutations from multiple cores in
one process do not overwrite each other.

There is no cross-process file lock. Run exactly one writer process per `DATA_FILE`; two Node.js
processes writing the same path can race and lose an update. For multi-process deployment, give each
process a separate file or replace the store with a database that supplies transactional locking.

Dispatch durably reserves the notification and idempotency key with `pending` deliveries before it
calls providers. On initialization, a reserved delivery still left `pending` is finalized as
`failed` with code `DELIVERY_INTERRUPTED`; recovery never invokes its provider, and a repeated
idempotent request returns that same final result. This deliberately favors at-most-once
service-initiated provider attempts over automatic redelivery. It is not an end-to-end exactly-once
or at-least-once delivery guarantee: if interruption happens after a provider accepted a delivery
but before the final result was persisted, the external delivery may have occurred even though the
recovered record says its outcome is unknown. Reconcile such outcomes with provider-side IDs when
the provider supports them.

hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
Fresh producer evidence now passes 20/20, including regressions for all four independent findings. Inspection confirms the repairs reload state inside a resolved-path shared queue, use own-property dictionary access, validate nested persisted records, and finalize orphaned reservations without redelivery.

I’m dispatching a new judge with the expanded acceptance criteria. It has not seen either implementation worker’s reasoning or self-assessment.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The final judge is actively probing beyond the 20-test suite, including the previously failing reserved-key, multi-core, malformed-state, and interruption cases. I’ll only close this out on a clean independent verdict.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
No new defect has been reported yet; the judge remains active. The remaining acceptance question is whether the corrected semantics hold under independent probes, not whether the existing suite is green.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The second judge found two remaining contract gaps: persisted fingerprint integrity was only shape-checked, and non-inbox routes silently accepted query parameters. The 20-test evidence is invalidated again.

I’m doing one tightly scoped recovery pass with a fresh worker: recompute each stored fingerprint from the linked notification during state validation, reject any query parameters on routes that define none, and add regressions for both.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The final repair is intentionally narrow: no architecture changes, only deterministic fingerprint revalidation and zero-query enforcement on routes without query contracts. Both must be proven by new negative tests before another independent review.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The repair worker is still active and no incompatible change has been reported. After its suite passes, the last review will focus only on the full acceptance surface and the new corrupt-fingerprint/query regressions.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The scoped repair now passes 22/22, and the prior judge has confirmed both defects are resolved. I’m still doing one final input-curated review from a completely fresh context because that judge was re-triggered from inside the repair branch; this keeps the judge-of-record independent of producer framing.
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/bin/zsh -lc "rg -n \"fingerprint|assertNoQuery|INVALID_QUERY\" src/core/notification-service.js src/http/app.js test/core.test.js test/http.test.js; sed -n '108,158p' src/core/notification-service.js; sed -n '90,215p' src/http/app.js; git status --short" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
 succeeded in 0ms:
test/http.test.js:273:          code: 'INVALID_QUERY',
src/core/notification-service.js:135:          !hasOnlyKeys(entry, ['fingerprint', 'notificationId']) ||
src/core/notification-service.js:136:          !hasOwn(entry, 'fingerprint') || !hasOwn(entry, 'notificationId') ||
src/core/notification-service.js:137:          !isNonEmptyString(entry.fingerprint) || !isNonEmptyString(entry.notificationId)) return false;
src/core/notification-service.js:153:      if (entry.fingerprint !== stableStringify(persistedPayload)) return false;
src/core/notification-service.js:335:    const fingerprint = stableStringify(request);
src/core/notification-service.js:346:          if (prior.fingerprint !== fingerprint) {
src/core/notification-service.js:369:        setOwn(userKeys, request.idempotencyKey, { fingerprint, notificationId: id });
test/core.test.js:274:test('persisted idempotency fingerprint must match its notification payload', async (t) => {
test/core.test.js:287:  persisted.idempotency['user-1']['request-1'].fingerprint = 'wrong-but-nonempty';
test/core.test.js:325:  const fingerprint = stableStringify({
test/core.test.js:342:        'request-1': { fingerprint, notificationId: 'notification-1' },
test/core.test.js:375:  const fingerprint = stableStringify({
test/core.test.js:399:        'request-1': { fingerprint, notificationId: 'notification-1' },
src/http/app.js:103:function assertNoQuery(searchParams) {
src/http/app.js:106:    throw apiError(400, 'INVALID_QUERY', 'Query parameters are not allowed for this resource', {
src/http/app.js:157:        assertNoQuery(url.searchParams);
src/http/app.js:167:        assertNoQuery(url.searchParams);
src/http/app.js:181:        assertNoQuery(url.searchParams);
src/http/app.js:189:        assertNoQuery(url.searchParams);
src/http/app.js:206:        assertNoQuery(url.searchParams);
        ])) return false;
    for (const key of ['id', 'userId', 'idempotencyKey', 'category', 'content', 'createdAt', 'deliveries']) {
      if (!hasOwn(notification, key)) return false;
    }
    if (notification.id !== notificationId || !isNonEmptyString(notification.id) ||
        !isNonEmptyString(notification.userId) || !isNonEmptyString(notification.idempotencyKey) ||
        !isNonEmptyString(notification.category) || !validateContent(notification.content) ||
        !isTimestamp(notification.createdAt) || !Array.isArray(notification.deliveries) ||
        notification.deliveries.length === 0 || notification.deliveries.length > CHANNELS.length) return false;
    if (!notification.deliveries.every(validateDelivery)) return false;
    const deliveryChannels = notification.deliveries.map((delivery) => delivery.channel);
    if (new Set(deliveryChannels).size !== deliveryChannels.length) return false;
    if (hasOwn(notification, 'completedAt')) {
      if (!isTimestamp(notification.completedAt) ||
          notification.deliveries.some((delivery) => delivery.status === 'pending')) return false;
    }
    return true;
  });
}

function validateIdempotency(idempotency, notifications) {
  if (!isRecord(idempotency)) return false;
  const referencedNotifications = new Set();
  const entriesAreValid = Object.entries(idempotency).every(([userId, keys]) => {
    if (!isNonEmptyString(userId) || !isRecord(keys)) return false;
    return Object.entries(keys).every(([idempotencyKey, entry]) => {
      if (!isNonEmptyString(idempotencyKey) || !isRecord(entry) ||
          !hasOnlyKeys(entry, ['fingerprint', 'notificationId']) ||
          !hasOwn(entry, 'fingerprint') || !hasOwn(entry, 'notificationId') ||
          !isNonEmptyString(entry.fingerprint) || !isNonEmptyString(entry.notificationId)) return false;
      const notification = getOwn(notifications, entry.notificationId);
      if (notification === undefined || notification.userId !== userId ||
          notification.idempotencyKey !== idempotencyKey ||
          referencedNotifications.has(entry.notificationId)) return false;
      const persistedPayload = {
        userId: notification.userId,
        idempotencyKey: notification.idempotencyKey,
        category: notification.category,
        channels: notification.deliveries.map((delivery) => delivery.channel),
        recipients: Object.fromEntries(notification.deliveries.map((delivery) => [
          delivery.channel,
          delivery.recipient,
        ])),
        content: notification.content,
      };
      if (entry.fingerprint !== stableStringify(persistedPayload)) return false;
      referencedNotifications.add(entry.notificationId);
      return true;
    });
  });
  return entriesAreValid && referencedNotifications.size === Object.keys(notifications).length;
  const unreadText = parseSingleQuery(searchParams, 'unread', 'false');
  if (!/^(0|[1-9]\d*)$/.test(offsetText) || !Number.isSafeInteger(Number(offsetText))) {
    throw apiError(400, 'INVALID_PAGINATION', 'offset must be a non-negative integer', { field: 'offset' });
  }
  if (!/^[1-9]\d*$/.test(limitText) || Number(limitText) > 100) {
    throw apiError(400, 'INVALID_PAGINATION', 'limit must be an integer between 1 and 100', { field: 'limit' });
  }
  if (unreadText !== 'true' && unreadText !== 'false') {
    throw apiError(400, 'INVALID_PAGINATION', 'unread must be true or false', { field: 'unread' });
  }
  return { offset: Number(offsetText), limit: Number(limitText), unread: unreadText === 'true' };
}

function assertNoQuery(searchParams) {
  const first = searchParams.keys().next();
  if (!first.done) {
    throw apiError(400, 'INVALID_QUERY', 'Query parameters are not allowed for this resource', {
      field: first.value,
    });
  }
}

function sendJson(response, status, payload, headers = {}) {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
    ...headers,
  });
  response.end(body);
}

function sendError(response, error) {
  const known = error instanceof DomainError || Number.isInteger(error.status);
  const status = known ? error.status : 500;
  const code = known && typeof error.code === 'string' ? error.code : 'INTERNAL_ERROR';
  const message = known ? error.message : 'An internal error occurred';
  const payload = { error: { code, message } };
  if (known && error.details !== undefined) payload.error.details = error.details;
  sendJson(response, status, payload, error.allow ? { allow: error.allow } : undefined);
}

function methodNotAllowed(allow) {
  const error = apiError(405, 'METHOD_NOT_ALLOWED', 'Method is not allowed for this resource');
  error.allow = allow.join(', ');
  return error;
}

function notFound(message = 'Resource not found') {
  return apiError(404, 'NOT_FOUND', message);
}

function exactRoute(segments, pattern) {
  return segments.length === pattern.length && pattern.every((part, index) =>
    part.startsWith(':') || part === segments[index]);
}

function createRequestHandler({ service }) {
  if (!service) throw new TypeError('service is required');

  return async function requestHandler(request, response) {
    try {
      const url = new URL(request.url, 'http://localhost');
      const segments = decodeSegments(url.pathname);

      if (exactRoute(segments, ['api', 'v1', 'health'])) {
        if (request.method !== 'GET') throw methodNotAllowed(['GET']);
        assertNoQuery(url.searchParams);
        sendJson(response, 200, { status: 'ok' });
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'preferences', ':category'])) {
        const [, , , userId, , category] = segments;
        if (request.method !== 'GET' && request.method !== 'PUT') {
          throw methodNotAllowed(['GET', 'PUT']);
        }
        assertNoQuery(url.searchParams);
        if (request.method === 'GET') {
          sendJson(response, 200, { preferences: await service.getPreferences(userId, category) });
          return;
        }
        if (request.method === 'PUT') {
          const body = validatePreferencesBody(await readJson(request));
          sendJson(response, 200, { preferences: await service.setPreferences(userId, category, body) });
          return;
        }
      }

      if (exactRoute(segments, ['api', 'v1', 'notifications'])) {
        if (request.method !== 'POST') throw methodNotAllowed(['POST']);
        assertNoQuery(url.searchParams);
        const body = validateNotificationBody(await readJson(request));
        sendJson(response, 201, { notification: await service.dispatch(body) });
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'notifications', ':notificationId'])) {
        if (request.method !== 'GET') throw methodNotAllowed(['GET']);
        assertNoQuery(url.searchParams);
        const [, , , userId, , notificationId] = segments;
        const notification = await service.getNotification(userId, notificationId);
        if (!notification) throw notFound('Notification not found');
        sendJson(response, 200, { notification });
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'inbox'])) {
        if (request.method !== 'GET') throw methodNotAllowed(['GET']);
        const [, , , userId] = segments;
        sendJson(response, 200, await service.listInbox(userId, parsePagination(url.searchParams)));
        return;
      }

      if (exactRoute(segments, ['api', 'v1', 'users', ':userId', 'inbox', ':notificationId', 'read'])) {
        if (request.method !== 'PUT') throw methodNotAllowed(['PUT']);
        assertNoQuery(url.searchParams);
        const body = await readJson(request);
        assertAllowedFields(body, []);
        const [, , , userId, , notificationId] = segments;
        const item = await service.markInboxRead(userId, notificationId);
        if (!item) throw notFound('Inbox item not found');
        sendJson(response, 200, { item });
        return;
      }

?? .agentfw-plan.md
?? .agents/
?? AGENTS.md
?? README.md
?? package.json
?? src/
?? test/

hook: PostToolUse
hook: PostToolUse Completed
exec
/bin/zsh -lc 'npm test' in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

 succeeded in 1176ms:
TAP version 13
# Subtest: default adapters deliver email, SMS, and in-app with inspectable results
ok 1 - default adapters deliver email, SMS, and in-app with inspectable results
  ---
  duration_ms: 41.159917
  type: 'test'
  ...
# Subtest: preference defaults, user defaults, and category overrides compose without provider calls for skips
ok 2 - preference defaults, user defaults, and category overrides compose without provider calls for skips
  ---
  duration_ms: 69.067125
  type: 'test'
  ...
# Subtest: same user and canonical payload is idempotent while changed payload conflicts
ok 3 - same user and canonical payload is idempotent while changed payload conflicts
  ---
  duration_ms: 58.205083
  type: 'test'
  ...
# Subtest: idempotency keys are scoped per user
ok 4 - idempotency keys are scoped per user
  ---
  duration_ms: 77.991209
  type: 'test'
  ...
# Subtest: __proto__ values remain own map keys across users and restart
ok 5 - __proto__ values remain own map keys across users and restart
  ---
  duration_ms: 112.035917
  type: 'test'
  ...
# Subtest: invalid email and SMS are rejected before persistence or delivery
ok 6 - invalid email and SMS are rejected before persistence or delivery
  ---
  duration_ms: 19.800084
  type: 'test'
  ...
# Subtest: provider failures are isolated and persisted as delivery results
ok 7 - provider failures are isolated and persisted as delivery results
  ---
  duration_ms: 42.467791
  type: 'test'
  ...
# Subtest: concurrent mutations serialize and survive restart
ok 8 - concurrent mutations serialize and survive restart
  ---
  duration_ms: 255.949666
  type: 'test'
  ...
# Subtest: independent cores sharing one file do not lose concurrent mutations
ok 9 - independent cores sharing one file do not lose concurrent mutations
  ---
  duration_ms: 25.818208
  type: 'test'
  ...
# Subtest: restart preserves idempotency and never redelivers
ok 10 - restart preserves idempotency and never redelivers
  ---
  duration_ms: 32.94275
  type: 'test'
  ...
# Subtest: persisted idempotency fingerprint must match its notification payload
ok 11 - persisted idempotency fingerprint must match its notification payload
  ---
  duration_ms: 37.216708
  type: 'test'
  ...
# Subtest: corrupt persistence is rejected and source bytes are not overwritten
ok 12 - corrupt persistence is rejected and source bytes are not overwritten
  ---
  duration_ms: 1.870167
  type: 'test'
  ...
# Subtest: malformed nested persisted structures are rejected without changing source bytes
ok 13 - malformed nested persisted structures are rejected without changing source bytes
  ---
  duration_ms: 2.300375
  type: 'test'
  ...
# Subtest: initialization finalizes orphaned pending deliveries without redelivery
ok 14 - initialization finalizes orphaned pending deliveries without redelivery
  ---
  duration_ms: 22.641792
  type: 'test'
  ...
# Subtest: operator documentation includes configuration, safety, adapters, semantics, and API examples
ok 15 - operator documentation includes configuration, safety, adapters, semantics, and API examples
  ---
  duration_ms: 2.506917
  type: 'test'
  ...
# Subtest: health and preference endpoints expose defaults and category overrides
ok 16 - health and preference endpoints expose defaults and category overrides
  ---
  duration_ms: 92.592459
  type: 'test'
  ...
# Subtest: notification status is user-scoped and missing resources use stable 404 errors
ok 17 - notification status is user-scoped and missing resources use stable 404 errors
  ---
  duration_ms: 50.8625
  type: 'test'
  ...
# Subtest: in-app inbox paginates, filters unread items, and mark-read is user-scoped
ok 18 - in-app inbox paginates, filters unread items, and mark-read is user-scoped
  ---
  duration_ms: 163.706416
  type: 'test'
  ...
# Subtest: malformed JSON and unknown fields return structured 400 errors
ok 19 - malformed JSON and unknown fields return structured 400 errors
  ---
  duration_ms: 19.154625
  type: 'test'
  ...
# Subtest: pagination, content type, methods, and paths reject invalid requests consistently
ok 20 - pagination, content type, methods, and paths reject invalid requests consistently
  ---
  duration_ms: 16.854125
  type: 'test'
  ...
# Subtest: non-inbox routes reject query parameters before service side effects
ok 21 - non-inbox routes reject query parameters before service side effects
  ---
  duration_ms: 0.577583
  type: 'test'
  ...
# Subtest: changed payload with a reused user idempotency key returns 409 without delivery
ok 22 - changed payload with a reused user idempotency key returns 409 without delivery
  ---
  duration_ms: 65.445708
  type: 'test'
  ...
1..22
# tests 22
# suites 0
# pass 22
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 868.66775

diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The fresh judge-of-record is running against the complete acceptance surface with no producer framing. Current producer evidence is 22/22 and exact `# fail 0`; completion now depends only on this independent verdict.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
No blocker has surfaced from the judge-of-record, which is still probing. I’m keeping the task open until its machine evidence and code review are complete.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The fresh judge found one narrow remaining invariant: a persisted `delivered` result could omit `providerResult`, even though every real dispatch always writes it (using `null` when the provider returns nothing). All other independent stress probes passed.

I’m fixing that single validator omission with a regression, then rerunning the full suite and one final read-only confirmation.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The last fix is confined to the persisted-delivery schema and its corruption regression. No runtime API behavior is changing; the purpose is to ensure stored results cannot claim `delivered` without the provider outcome field the dispatcher always records.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

hook: PreToolUse
hook: PreToolUse Completed
exec
/bin/zsh -lc 'npm test && for file in $(rg --files -g '"'*.js' | sort); do node --check \""'$file" || exit; done && echo '"'ALL_JS_SYNTAX_PASS'" in /private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ
hook: PostToolUse
hook: PostToolUse Completed
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

 succeeded in 1570ms:
TAP version 13
# Subtest: default adapters deliver email, SMS, and in-app with inspectable results
ok 1 - default adapters deliver email, SMS, and in-app with inspectable results
  ---
  duration_ms: 36.971334
  type: 'test'
  ...
# Subtest: preference defaults, user defaults, and category overrides compose without provider calls for skips
ok 2 - preference defaults, user defaults, and category overrides compose without provider calls for skips
  ---
  duration_ms: 67.025375
  type: 'test'
  ...
# Subtest: same user and canonical payload is idempotent while changed payload conflicts
ok 3 - same user and canonical payload is idempotent while changed payload conflicts
  ---
  duration_ms: 61.113
  type: 'test'
  ...
# Subtest: idempotency keys are scoped per user
ok 4 - idempotency keys are scoped per user
  ---
  duration_ms: 75.893375
  type: 'test'
  ...
# Subtest: __proto__ values remain own map keys across users and restart
ok 5 - __proto__ values remain own map keys across users and restart
  ---
  duration_ms: 109.123833
  type: 'test'
  ...
# Subtest: invalid email and SMS are rejected before persistence or delivery
ok 6 - invalid email and SMS are rejected before persistence or delivery
  ---
  duration_ms: 19.054333
  type: 'test'
  ...
# Subtest: provider failures are isolated and persisted as delivery results
ok 7 - provider failures are isolated and persisted as delivery results
  ---
  duration_ms: 37.037875
  type: 'test'
  ...
# Subtest: concurrent mutations serialize and survive restart
ok 8 - concurrent mutations serialize and survive restart
  ---
  duration_ms: 259.1895
  type: 'test'
  ...
# Subtest: independent cores sharing one file do not lose concurrent mutations
ok 9 - independent cores sharing one file do not lose concurrent mutations
  ---
  duration_ms: 31.886542
  type: 'test'
  ...
# Subtest: restart preserves idempotency and never redelivers
ok 10 - restart preserves idempotency and never redelivers
  ---
  duration_ms: 34.275667
  type: 'test'
  ...
# Subtest: persisted idempotency fingerprint must match its notification payload
ok 11 - persisted idempotency fingerprint must match its notification payload
  ---
  duration_ms: 36.708583
  type: 'test'
  ...
# Subtest: delivered persistence requires providerResult while accepting a null result
ok 12 - delivered persistence requires providerResult while accepting a null result
  ---
  duration_ms: 25.808041
  type: 'test'
  ...
# Subtest: corrupt persistence is rejected and source bytes are not overwritten
ok 13 - corrupt persistence is rejected and source bytes are not overwritten
  ---
  duration_ms: 2.275584
  type: 'test'
  ...
# Subtest: malformed nested persisted structures are rejected without changing source bytes
ok 14 - malformed nested persisted structures are rejected without changing source bytes
  ---
  duration_ms: 2.584625
  type: 'test'
  ...
# Subtest: initialization finalizes orphaned pending deliveries without redelivery
ok 15 - initialization finalizes orphaned pending deliveries without redelivery
  ---
  duration_ms: 16.93625
  type: 'test'
  ...
# Subtest: operator documentation includes configuration, safety, adapters, semantics, and API examples
ok 16 - operator documentation includes configuration, safety, adapters, semantics, and API examples
  ---
  duration_ms: 2.556667
  type: 'test'
  ...
# Subtest: health and preference endpoints expose defaults and category overrides
ok 17 - health and preference endpoints expose defaults and category overrides
  ---
  duration_ms: 82.206625
  type: 'test'
  ...
# Subtest: notification status is user-scoped and missing resources use stable 404 errors
ok 18 - notification status is user-scoped and missing resources use stable 404 errors
  ---
  duration_ms: 49.41625
  type: 'test'
  ...
# Subtest: in-app inbox paginates, filters unread items, and mark-read is user-scoped
ok 19 - in-app inbox paginates, filters unread items, and mark-read is user-scoped
  ---
  duration_ms: 164.003875
  type: 'test'
  ...
# Subtest: malformed JSON and unknown fields return structured 400 errors
ok 20 - malformed JSON and unknown fields return structured 400 errors
  ---
  duration_ms: 18.047042
  type: 'test'
  ...
# Subtest: pagination, content type, methods, and paths reject invalid requests consistently
ok 21 - pagination, content type, methods, and paths reject invalid requests consistently
  ---
  duration_ms: 18.959333
  type: 'test'
  ...
# Subtest: non-inbox routes reject query parameters before service side effects
ok 22 - non-inbox routes reject query parameters before service side effects
  ---
  duration_ms: 0.889042
  type: 'test'
  ...
# Subtest: changed payload with a reused user idempotency key returns 409 without delivery
ok 23 - changed payload with a reused user idempotency key returns 409 without delivery
  ---
  duration_ms: 57.121083
  type: 'test'
  ...
1..23
# tests 23
# suites 0
# pass 23
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 883.761459
ALL_JS_SYNTAX_PASS

codex
Fresh evidence is now 23/23 with all JavaScript syntax checks passing. The added regression proves `undefined` provider returns persist as `null`, while deleting `providerResult` causes byte-preserving `CORRUPT_STORE`.

I’m asking the judge-of-record to re-evaluate the current tree; it remains independent because it made no implementation changes.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
The judge-of-record is rerunning the acceptance suite and targeted persistence probe. This is the final verification gate; no further implementation is pending unless it finds a concrete regression.
collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

collab: Wait
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

codex
Implemented a complete dependency-free notification service with:

- Email, SMS, and in-app adapter channels
- Per-user default and category preferences
- Idempotent notification dispatch
- Per-channel delivery outcomes
- Paginated/unread in-app inbox and mark-read
- Durable atomic JSON persistence
- Strict `/api/v1` REST API and structured errors
- Restart recovery and corruption validation

Key files:

- [README.md](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/README.md)
- [notification-service.js](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/src/core/notification-service.js)
- [app.js](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/src/http/app.js)
- [server.js](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/src/server.js)

Run it with:

```sh
npm test
DATA_FILE=./data/notifications.json npm start
```

Verification passed independently:

```text
23 tests passed
0 failed
10 JavaScript files passed syntax checks
0 runtime dependencies
```

The bundled providers safely record deliveries rather than contacting external services; real email/SMS providers plug into the documented adapter interface. The local JSON store supports one writer process per data file, and external exposure should use an authenticated gateway.
diff --git a/.agentfw-plan.md b/.agentfw-plan.md
new file mode 100644
index 0000000000000000000000000000000000000000..fd3a699c8e927f1200170fdfa61371384ab22c62
--- /dev/null
+++ b/.agentfw-plan.md
@@ -0,0 +1,75 @@
+```json agentfw-plan
+{
+  "version": "1.1",
+  "assurance": "A2",
+  "requirements": [
+    {"id": "R1", "text": "Support email, SMS, and in-app notification channels through replaceable provider adapters."},
+    {"id": "R2", "text": "Persist and expose user notification preferences by channel and notification category."},
+    {"id": "R3", "text": "Create notifications idempotently, honor preferences, validate channel-specific recipients, and report per-channel delivery outcomes."},
+    {"id": "R4", "text": "Expose an in-app inbox with pagination, unread filtering, and mark-read behavior."},
+    {"id": "R5", "text": "Provide durable local persistence, structured API errors, automated positive and negative tests, and operator documentation."}
+  ],
+  "tasks": [
+    {
+      "id": "T1",
+      "title": "Implement notification domain, persistence, adapters, and core tests",
+      "deps": [],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R5"],
+        "criteria": "A dependency-free Node domain layer provides serialized atomic JSON persistence with restart durability and corrupt-file rejection, email/SMS/in-app adapters, preference defaults and overrides, per-user idempotent dispatch, recipient validation, and inspectable delivery results. Reusing a per-user idempotency key with a different canonical payload is a conflict; the same key may be independently used by another user.",
+        "acceptance_command": "node --test test/core.test.js",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 in workspace-write sandbox with network disabled and temporary test data directories.",
+        "risk": "Preference or idempotency errors could send a notification on an unintended channel or duplicate it.",
+        "negative_cases": ["Disabled preferences produce skipped deliveries and no provider call.", "A repeated per-user idempotency key with the same payload returns the original notification without redelivery, while a changed payload conflicts and another user may reuse the key.", "Invalid email/SMS recipients are rejected before persistence or delivery.", "Concurrent mutations remain readable after restart, and corrupt persistence is rejected without overwriting the source."],
+        "evidence": "Fresh node:test output produced after implementation.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Do not perform network delivery; use replaceable recording providers by default. No external package install."
+      }
+    },
+    {
+      "id": "T2",
+      "title": "Implement HTTP API, in-app inbox, end-to-end tests, and documentation",
+      "deps": ["T1"],
+      "contract": {
+        "requirement_ids": ["R2", "R3", "R4", "R5"],
+        "criteria": "A versioned REST API exposes health, preferences, notification creation/status, and in-app inbox/read endpoints with strict JSON validation, pagination, stable errors, and documented examples/configuration. The full test command executes syntax checks and a mechanical documentation/configuration assertion in addition to core and HTTP tests.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Node.js 25 using an ephemeral loopback HTTP server and temporary data directory; no network egress or third-party services.",
+        "risk": "HTTP/domain mismatches may bypass preferences, corrupt response semantics, or expose cross-user inbox data.",
+        "negative_cases": ["Malformed JSON and unknown fields return structured 400 errors.", "Cross-user notification and inbox reads return 404 rather than leaking data.", "Invalid pagination and missing resources return stable 4xx responses.", "Changing the request payload while reusing a user's idempotency key returns 409 and performs no delivery."],
+        "evidence": "Fresh full-suite node:test output and syntax checks produced after all changes.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "Keep the service dependency-free, bind to loopback by default, and make DATA_FILE configurable. npm test must invoke node --check on source entry points and include test/docs.test.js."
+      }
+    },
+    {
+      "id": "T3",
+      "title": "Independently verify integration seams and acceptance contracts",
+      "deps": ["T2"],
+      "contract": {
+        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
+        "criteria": "A judge that did not implement the service inspects only requirements, current state, and acceptance contracts; it reruns the full suite and checks channel/preferences/idempotency, persistence/recovery, user isolation, API errors, and documentation reachability.",
+        "acceptance_command": "npm test",
+        "expected_signal": "^# pass [1-9][0-9]*$",
+        "environment": "Fresh independent agent context in the same managed workspace after implementation, with no producer reasoning or self-assessment supplied.",
+        "risk": "Producer tests may encode the same mistaken assumptions as the implementation.",
+        "negative_cases": ["Judge confirms disabled channels never invoke providers.", "Judge confirms per-user idempotency conflicts and cross-user reuse.", "Judge confirms corrupt-file rejection and foreign-resource non-disclosure."],
+        "evidence": "Fresh judge-recorded npm test output plus an acceptance finding report produced after the final change.",
+        "integration_seam": true,
+        "risk_class": "standard",
+        "required_verification_tier": "independent",
+        "rerunnable": true,
+        "constraints": "The judge must not modify implementation files and must receive no producer reasoning or self-assessment."
+      }
+    }
+  ]
+}
+```

hook: Stop
hook: Stop Completed
tokens used
210,064
Implemented a complete dependency-free notification service with:

- Email, SMS, and in-app adapter channels
- Per-user default and category preferences
- Idempotent notification dispatch
- Per-channel delivery outcomes
- Paginated/unread in-app inbox and mark-read
- Durable atomic JSON persistence
- Strict `/api/v1` REST API and structured errors
- Restart recovery and corruption validation

Key files:

- [README.md](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/README.md)
- [notification-service.js](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/src/core/notification-service.js)
- [app.js](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/src/http/app.js)
- [server.js](/private/var/folders/rk/6ysygvyd6j59npqqh0k43q680000gn/T/tmp.yp2e9fbiSJ/src/server.js)

Run it with:

```sh
npm test
DATA_FILE=./data/notifications.json npm start
```

Verification passed independently:

```text
23 tests passed
0 failed
10 JavaScript files passed syntax checks
0 runtime dependencies
```

The bundled providers safely record deliveries rather than contacting external services; real email/SMS providers plug into the documented adapter interface. The local JSON store supports one writer process per data file, and external exposure should use an authenticated gateway.
