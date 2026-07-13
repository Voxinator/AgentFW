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
