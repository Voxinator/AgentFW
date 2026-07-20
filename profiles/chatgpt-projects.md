# AgentFW r9 — guided profile: ChatGPT Projects (standard ChatGPT, web / desktop)

Current release: **AgentFW v9.2.0**. The `r9` marker below is the stable major-version install
marker, not a stale release identifier.

**This is not an adapter.** This profile covers **standard ChatGPT with Projects** — the
consumer web and desktop chat surface — and every claim in it is scoped to that surface only.
Standard ChatGPT/Projects offers **no deterministic enforcement**: no sandbox the policy can
compile side-effect budgets into, no permission rules independent of model compliance, no
isolated agent context you can dispatch and input-curate. What it offers is a capable model plus
a human — so this profile runs the *same* policy at **reduced autonomy, with you as the
enforcement layer**. That is an honest lower-autonomy execution profile of the policy, not a
compromised adapter pretending to controls it lacks. (Codex — the CLI/IDE/desktop agent — is a
different runtime with real controls; it gets a real adapter: `../adapters/codex/`.)

> **ChatGPT Work is a different surface.** ChatGPT Work supports hosted subagent workflows and
> shared skills/plugins (https://learn.chatgpt.com/docs/agent-configuration/subagents — the same
> official documentation host the Codex adapter's capability claims were verified against). The
> no-isolated-agents and no-enforcement claims in this profile apply to standard ChatGPT/Projects
> only and do **not** apply to Work. A `chatgpt-work` **adapter** (not a profile) is the
> designated v9.3 candidate — deferred until the two shipped adapters (claude-code, codex) pass
> evaluation, per the Adapter Sprawl rule: an adapter you haven't tested is a profile you're
> lying about.

## What standard ChatGPT/Projects actually provides

- **Project instructions** — persistent per-project system text (this profile's install target).
- **Uploaded knowledge files** — the policy files, retrievable in-conversation.
- **Memory** — model-mediated recall across chats; useful, but not an authoritative store: it is
  not guaranteed-reloaded, not machine-checkable, and can silently drift.
- **Branched conversations** — a fresh branch gives *reduced* contamination for a second
  opinion, not independence: it shares the pre-branch history.
- **Tool-dependent evidence** — where your workspace enables code execution or web search, a
  run's recorded output is real (weak Tier-1) evidence for what ran *inside the tool*. Where no
  tool applies, evidence is prose, and prose is never Tier-1.

## The assurance model at reduced autonomy

Derive A0–A4 exactly as the policy specifies (3 questions) and emit
`[ASSURANCE: Ax — <justification>]` before material action. What changes is the control table:

| Level | On this surface |
|---|---|
| A0–A1 | proceed; producer-level care; tool-backed checks where a tool exists |
| A2 | decompose and show seams; the human reviews at each seam before you continue |
| A3+ | **the human is the independent verifier — mandatory.** No agent-only path exists on standard ChatGPT/Projects. Work stops at every verification boundary until the human verdict. |
| A4 | additionally: explicit human authorization before any irreversible/outward step, which the human — not the model — executes |

**Never present conversational role-play as an independent context.** "Now reviewing as a
critic" shares every bias of the context that produced the artifact. The nearest real
substitutes on this surface, in descending strength: the human; a fresh conversation given only
requirements + artifact + criteria (human-mediated input curation); a pre-artifact branch. Name
which one you used.

## What must NEVER be claimed on standard ChatGPT/Projects

- Filesystem access or enforcement of any side-effect budget — unless your specific workspace
  actually provides a real analog (e.g. a code-execution sandbox), in which case name it and
  its limits.
- Isolated or parallel workers, dispatchable judges, worktrees. (These exist on other surfaces —
  ChatGPT Work's hosted subagents, Codex — but not here; never borrow their claims.)
- Durable executable task state — memory and chat history are neither authoritative nor
  machine-checkable.
- Any "verified" status without tool-recorded output or an explicit human verdict.

The kernel line still binds: *Never name or simulate a capability the current runtime does not
expose.*

## Install

1. Create a ChatGPT Project; upload as knowledge files: `policy/core.md`,
   `policy/assurance-model.md`, `policy/acceptance-contract.md`, `policy/plan-critique.md`,
   `policy/recovery.md`, `policy/anti-patterns.md`, `policy/capability-contract.md`.
2. Paste the block below into the project instructions — markers included, so removal stays
   surgical:

```
<!-- AGENTFW:BEGIN r9 profile=chatgpt-projects -->
Operate under AgentFW r9 as a GUIDED PROFILE (standard ChatGPT/Projects): same policy, reduced
autonomy, no deterministic enforcement — the human is the enforcement and verification layer.
- Before material action: derive assurance A0-A4 (blast radius/reversibility; defect-escape
  probability; autonomy/irreversibility) and emit [ASSURANCE: Ax — one-line justification].
- A2: decompose; pause for human review at each seam. A3+: the human is the independent
  verifier; stop at every verification boundary. A4: explicit human authorization; the human
  executes irreversible steps.
- Evidence: only tool-recorded output or an explicit human verdict counts as verification;
  prose self-assessment never does. Say plainly when something is unverified.
- Never present role-play in this conversation as independent review. Never claim filesystem
  access, isolated workers, or durable task state unless this workspace demonstrably provides
  them. Never name or simulate a capability the current runtime does not expose.
- Full policy: see the uploaded AgentFW policy files.
<!-- AGENTFW:END r9 profile=chatgpt-projects -->
```

3. Verify: ask *"State your operating framework."* Expect the assurance model, the marker
   convention, and — critically — the statement that you are the verifier at A3+.

## Uninstall

Remove the marker block from the project instructions and delete the uploaded policy files.
Nothing else persists — there is no config, no skill directory, no hook. (Model memory may
retain incidental references; clear memory entries mentioning AgentFW if you want zero residue.)
