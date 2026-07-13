# AgentFW

## What This Is

AI capabilities look jagged when you ask for one-shot answers. The same model that writes a flawless function will hallucinate a dependency or skip a critical edge case two prompts later. The inconsistency isn't in the model — it's in the lack of structure around it. Apply the same organizational patterns that make human teams effective (task decomposition, parallel execution, independent verification, iterative refinement) and the surface smooths out.

As of r9, AgentFW is a **portable governance layer**: a **platform-neutral semantic policy** (`policy/` — assurance levels, acceptance contracts, verification tiers, role separation; names capabilities and invariants, never vendor runtime primitives) **compiled into native adapters** (`adapters/` — each one maps the policy onto a specific runtime's real, deterministic controls). Where a runtime supplies enforcement (Claude Code, Codex), the adapter compiles into it; where none exists (chat products), guided profiles (`profiles/`) degrade honestly instead of pretending. The r9 thesis:

> *"r9 governs work through portable assurance contracts compiled into native runtime behavior where a runtime exists to compile into, and into explicit, evidence-bearing model commitments where it doesn't — with the honesty to say which is which per adapter."*

AgentFW remains structured Markdown plus a few small stdlib-only validators — not a framework, library, or SDK.

## Status: r9 draft pre-release

**r9 status: draft — not eval-validated (golden-task re-run pending).** Released as draft pre-release tag `r9-draft`.

- **Last validated release: r8** (tag `r8`) — still installed from `core/` + `references/`, and it remains the validated install until r9 passes evaluation.
- **Eval ledger, stated honestly:** r8's last golden-task run (2026-05-29) scored **5 PASS / 3 UNTESTED** — the 3 "partials" were test-design issues, meaning those criteria were UNTESTED, not passed. **No outcome eval has run against r9.** The golden-task rewrite plus outcome evals are the gate for shedding draft status.

What "draft" means here: r9 is structurally complete, its mechanical layers are suite-tested, and it has been externally reviewed across seven rounds with zero open findings (see [Verification & provenance](#verification--provenance)) — but none of that is evidence that r9 *improves agent outcomes*. Only the pending evals can show that.

> **Hermes variant moved.** The Hermes variant (Gemma-4 running AgentFW as a local orchestrator on Hermes Agent) has been extracted to its own project, **`agentfw-hermes`**, and removed from this repo. It is no longer part of AgentFW core. Historical commits in this repo's git history and `archive/` are unaffected.

## What r9 is

r9 splits the framework into four surfaces:

### `policy/` — the platform-neutral semantic policy

- **Assurance model A0–A4** (`policy/assurance-model.md`) — how much independent evidence a change needs before it is believed, derived from three questions (blast radius/reversibility, defect-escape probability, autonomy/irreversibility). Replaces r8's task classification as the primary framing.
- **Acceptance Contract v2** (`policy/acceptance-contract.md`) — requirement ids, environment, negative cases, evidence freshness, evidence classes for non-shell work, tiered verified states (`verified_producer` / `verified_independent` / `verified_adversarial`). Plan blocks use a **machine-enforced v1.1 schema** (versioned; v1 blocks retain v1 rules so historical plans still pass).
- **Two-layer Plan-Critique Gate** (`policy/plan-critique.md`) — Layer 1 is a real, runnable deterministic validator (`tools/validate-plan`, with positive and hostile fixtures); Layer 2 is the C0–C5 semantic judge inherited from r8.
- **Capability contracts** (`policy/capability-contract.md` + per-adapter `capability.yaml`) — every platform claim carries a `verified:` annotation (an unverified true gates as false), and each entry splits what the platform makes **available** from what a given install has **configured**, with an `activation_probe` to check locally. Assurance gating consults the active install, not the platform brochure.
- **Recovery** (`policy/recovery.md`) — failure scope, contamination analysis, retry budget, evidence invalidation, lesson-not-state carry-forward.
- **Anti-patterns** (`policy/anti-patterns.md`) — the r8 catalog plus **Prose-API** and **Adapter Sprawl**.

### `adapters/` — native adapters

- **`adapters/claude-code/`** — thin bootloader + skill + agent definitions, with a marker-block installer (`tools/agentfw-install`) whose uninstall restores user content **byte-identically** (manifest-based, roundtrip-tested including hostile fence cases).
- **`adapters/codex/`** — doc-grounded adapter; platform capability claims verified against official documentation, annotated per source.
- Both ship INSTALL / UPGRADE / UNINSTALL docs and a `capability.yaml`.

### `profiles/` — guided degradation profiles (not adapters)

`profiles/chatgpt-projects.md` (standard ChatGPT/Projects) and `profiles/claude-projects.md` (Claude.ai Projects) — honest lower-autonomy profiles for runtimes with no enforcement surface. Explicitly *not* adapters.

### `tools/` — validators, installer, tests

`tools/validate-plan` (deterministic Layer-1 plan validation), `tools/validate-capability` (capability.yaml schema validation), `tools/agentfw-install` (marker-block installer), `tools/fixtures/` (positive + hostile plan and capability fixtures), and `tools/tests/` (`install-roundtrip.sh`, `check-links.sh`).

**Scope boundary (deliberate):** r9 ships exactly two native adapters (Claude Code, Codex) and two guided profiles (standard ChatGPT/Projects, Claude.ai Projects). ChatGPT Work — a different surface with hosted subagents/skills — is acknowledged but deferred to **r9.1** as the designated adapter candidate, per the Adapter Sprawl rule (no platform binding ships before the existing adapters pass evals). This is a deliberate boundary, not full ChatGPT parity.

## Install / Upgrade / Uninstall

| Platform | Install | Upgrade | Uninstall |
|---|---|---|---|
| Claude Code | `adapters/claude-code/INSTALL.md` | `adapters/claude-code/UPGRADE.md` | `adapters/claude-code/UNINSTALL.md` |
| Codex | `adapters/codex/INSTALL.md` | `adapters/codex/UPGRADE.md` | `adapters/codex/UNINSTALL.md` |
| ChatGPT / Projects (guided profile) | `profiles/chatgpt-projects.md` | — | — |
| Claude.ai Projects (guided profile) | `profiles/claude-projects.md` | — | — |

The r8 install path (`bootstrap.md` → `core/harness-core.md` as CLAUDE.md) remains available and is still the validated one — see [r8 below](#r8--the-last-validated-release).

## Verification & provenance

What r9's quality claims rest on — and what they don't:

- **Built by the process it encodes.** The r9 build and both follow-up passes ran under the full harness: judged plans (Plan-Critique Gate over each plan before dispatch), parallel workers with disjoint file ownership, and independent + adversarial verification of the results.
- **Externally reviewed, seven rounds.** Seven rounds of adversarial external review (GPT 5.6 Sol), every finding independently re-reproduced against the tree before acceptance. Review #7 verdict: approved, **zero open findings**.
- **Mechanical suite state:** install roundtrip **25/25** (including hostile fence cases: tilde fences, four-backtick fences with inner triple-backtick lines, indented fences, unclosed-fence refusal, marker lookalikes); **17 hostile plan fixtures + 3 capability fixtures** all rejected with the defect named; capability validation exercised through **both parser paths** (PyYAML present and the stdlib fallback); **54 relative links/references** checked resolvable (`tools/tests/check-links.sh`).
- **What has NOT happened:** no outcome evals. The golden tasks have not been rewritten for r9's assurance framing and no golden-task run has executed against r9. Structural completeness and review coverage are evidence of *form*, not of *improved agent outcomes* — that evidence is exactly what the draft label is waiting on.

## Directory Structure

```
agentfw/
├── metadata.json                  # Project metadata (version 9.0.0-draft, install routing)
├── README.md                      # This file
├── CHANGELOG.md                   # Version history with audit trail
├── DESIGN.md                      # r8 design spec (r9 banner inside; full revision lands with validated r9)
├── bootstrap.md                   # r8 installer (carries an r9 notice)
│
├── policy/                        # r9 semantic policy (platform-neutral)
│   ├── core.md                    # Policy core — critical rules, verification tiers, invariants
│   ├── assurance-model.md         # A0–A4 derivation
│   ├── acceptance-contract.md     # Contract v2 + v1.1 plan-block schema of record
│   ├── plan-critique.md           # Two-layer Plan-Critique Gate
│   ├── capability-contract.md     # Capability claims: available/configured/verified
│   ├── recovery.md                # Failure scope, contamination, retry budget
│   └── anti-patterns.md           # Catalog incl. Prose-API, Adapter Sprawl
│
├── adapters/                      # Native adapters (compile the policy into real controls)
│   ├── claude-code/               # Bootloader, skill, agents, capability.yaml, settings example,
│   │                              #   INSTALL/UPGRADE/UNINSTALL (marker-block installer)
│   └── codex/                     # AGENTS.md, skill, capability.yaml, config example,
│                                  #   INSTALL/UPGRADE/UNINSTALL (doc-grounded)
│
├── profiles/                      # Guided degradation profiles (NOT adapters)
│   ├── chatgpt-projects.md        # Standard ChatGPT/Projects
│   └── claude-projects.md         # Claude.ai Projects
│
├── tools/
│   ├── validate-plan              # Deterministic Layer-1 plan validator (stdlib python)
│   ├── validate-capability        # capability.yaml schema validator (stdlib python)
│   ├── agentfw-install            # Marker-block installer/upgrader/uninstaller + status probes
│   ├── fixtures/                  # plan-good + 17 hostile plan fixtures; capability/ bad fixtures
│   └── tests/                     # install-roundtrip.sh (25 cases), check-links.sh
│
├── core/                          # r8 firmware (LAST VALIDATED INSTALL — harness-core.md, permissions.md)
├── references/                    # r8 reference docs (native-primitives, verification tiers, …)
├── playbooks/                     # r6-era scenario playbooks (retained)
├── templates/                     # r6-era state/plan/log templates (retained)
├── evaluation/                    # Golden tasks + eval protocol (r8-framed; r9 rewrite pending)
├── variants/                      # r6-era variants — superseded by adapters/, retained for history
└── archive/                       # Historical framework snapshots and probe artifacts
```

> The Hermes variant that previously lived under `variants/hermes/` has been extracted to its own project (`agentfw-hermes`).

## r8 — the last validated release

r8 (tag `r8`, 2026-05-29) reframed the firmware as a governance layer over Claude Code 2.1 native primitives: the runtime supplies the harness (Workflow tool, subagents, Plan mode, Skills, MEMORY, hooks, worktrees); the firmware supplies classification, role discipline, the verification standard, and restraint (Rule 6: PREFER NATIVE PRIMITIVES). It added the Plan-Critique Gate + Acceptance-Contract spine, `references/native-primitives.md`, and GT-8; dropped cross-model content (Claude-Code-only); and extracted the Hermes variant.

r8 remains fully installable and is the release whose golden-task ledger stands (5 PASS / 3 UNTESTED):

```
cat bootstrap.md | claude        # detects environment and installs r8
# or manually:
cp core/harness-core.md ~/.claude/CLAUDE.md
```

r9 carries r8's load-bearing judgment forward: the input-curation bright line, the C0–C5 rubrics, the visible markers as forcing functions, and the Complexity Accumulation counterweight — now applied to the framework's own machinery.

## Version History

- **r1** (2025-03-01): Initial version as a single document
- **r2** (2025-05-15): Scenario playbooks for feature dev, bug hunting, maker projects
- **r3** (2025-09-01): Refined role separation, PM investigation playbook
- **r4** (2026-04-04): Modular restructure, permission model, evaluation system, observability, self-install
- **r5** (2026-04-06): Structural enforcement hardening — classification gate, verification gates, Tier 1 enforcement
- **r6** (2026-04-10): Context degradation resistance — Critical Rules preamble, state-driven health gate, delegation self-check
- **r7** (2026-04-17): Cross-model tuning pass for Opus 4.7 without non-target regression
- **r7.1–r7.11** (2026-04-18 → 2026-04-30): Hermes-variant probe + campaign arc — extracted to `agentfw-hermes`; full history remains there and in this repo's git history
- **r8** (2026-05-29): v8 governance refactor — governance layer over Claude Code 2.1 native primitives, Plan-Critique Gate + Acceptance-Contract spine, GT-8. **Last validated release.**
- **r9-draft** (2026-07-11): Portable governance layer — platform-neutral semantic policy (`policy/`) + native adapters (claude-code, codex) + guided profiles + runnable validators. Built via the full harness, externally reviewed across seven rounds (zero open findings), mechanically suite-tested — **draft — not eval-validated (golden-task re-run pending)**.
