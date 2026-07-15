# AgentFW

## What This Is

**AgentFW is a governance layer for AI agents — the discipline that turns a capable model into a dependable one.**

Model capability looks jagged when you ask for one-shot answers. The same system that writes a flawless function will hallucinate a dependency, skip an edge case, or quietly delete something it shouldn't two prompts later. That inconsistency isn't really in the model — it's in the absence of structure around it. Human teams don't rely on any one person being perfect; they rely on decomposition, parallel work, independent review, and the discipline to verify before believing. AgentFW gives an agent the same scaffolding, as policy it must follow rather than advice it may ignore.

It is built on one load-bearing distinction: **separate what can be *guaranteed* from what can only be *encouraged*, and never let the second masquerade as the first.**

- **A platform-neutral semantic policy** (`policy/`) — assurance levels, acceptance contracts, verification tiers, role separation, effect classification. It names capabilities and invariants, never a specific vendor's runtime, so the same governance travels across platforms.
- **Compiled into native adapters** (`adapters/`) — each adapter maps that policy onto a runtime's *real, deterministic* controls. Where a runtime supplies enforcement (Claude Code, Codex), the adapter compiles into it and the guarantee is mechanical. Where none exists (chat products), guided profiles (`profiles/`) degrade honestly instead of pretending to enforce.
- **Backed by machine-checked evidence** — a stdlib validator that gates plans before any work is dispatched, an installer whose uninstall restores your files byte-for-byte, a schema that fails safe on unknown versions, and a suite that must be green for anything to ship.

> *"Govern work through portable assurance contracts compiled into native runtime behavior where a runtime exists to compile into, and into explicit, evidence-bearing model commitments where it doesn't — with the honesty to say which is which, per adapter."*

The result is deliberately small: **structured Markdown plus a few stdlib-only validators — no framework, no library, no SDK, no runtime dependency.** Nothing to install into your build, nothing to lock into. You can read the entire policy in an afternoon and audit every guarantee it makes. That legibility is the point: a governance layer you cannot inspect is just another thing to trust blindly, which is the problem it exists to solve.

## Status: v9.0.0 — released

**Released 2026-07-15 as `v9.0.0`** under a two-tier release bar (`RELEASE-BAR-r9.md`): a deterministic layer that is **machine-verified and release-blocking**, and a behavioral layer that is **measured and published with its limitations** rather than claimed as guaranteed.

- **Tier 1 — deterministic layer (release-blocking, satisfied):** installer roundtrip **25/25**, `tools/validate-plan` full fixture suite (schema 1.2 floors, fail-safe versioning, review-tier emission), capability contracts under both parsers, **57** relative links resolvable, r8 dirs frozen, publication-hygiene sweep clean over all committed transcripts. All green at release.
- **Tier 2 — behavioral layer (published with limits):** behavior was exercised on **Claude Code** (claude-sonnet-5) and **Codex** (gpt-5.6-sol) across a fixtured smoke plus three targeted fix passes. Results are linked below and are honest about scope: **n=1 per cell** — behavior demonstrated changed, not proven stable. Targeted safety regressions were corrected and demonstrated at n=1 (see the fix-pass results docs); larger statistical calibration (n≥5, `EVAL-MATRIX-DESIGN.md`) is **post-release future work**, not a v9.0 blocker.
- **Behavioral compliance is model- and version-dependent, not guaranteed.** The framework's mechanical guarantees hold deterministically; whether a given model follows the semantic policy on a given run is a propensity these evals measure, not a certainty — and a model update re-opens the behavioral (not the deterministic) question.
- **r8** (tag `r8`) remains available as the prior release, installable from `core/` + `references/`.

Evidence, linked: `evaluation/results-r9-fixtured-smoke.md` (fixtured smoke), `evaluation/results-r9-fixpass2.md` (destructive-floor + dual-review fixes), `evaluation/results-r9-fixpass3.md` (post-blocker protocol, machine-consumed review tier, delegated-evidence rule), `evaluation/results-r9-fixpass4.md` (authorization-provenance negative control — the fix inverted the codex polarity to refuse a simulated authorization). Each carries its own adversarial audit and, for the last, an Opus-tier final semantic review.

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
- **Mechanical suite state:** install roundtrip **25/25** (including hostile fence cases: tilde fences, four-backtick fences with inner triple-backtick lines, indented fences, unclosed-fence refusal, marker lookalikes); hostile plan + capability fixtures all rejected with the defect named; capability validation exercised through **both parser paths** (PyYAML present and the stdlib fallback); **57 relative links/references** checked resolvable (`tools/tests/check-links.sh`).
- **Outcome evals — exercised, published, bounded.** Golden tasks were rewritten for r9's assurance framing, fixtured target repos built, and behavior run on both native adapters across a smoke plus three fix passes (links in [Status](#status-v900--released)). The evidence is **n=1 per cell**: it demonstrates that targeted behaviors changed under the framework (including safety regressions corrected — the destructive-authorization-provenance negative control now refuses a simulated authorization on both platforms), not that behavior is statistically stable. Larger calibration (n≥5) is scoped in `EVAL-MATRIX-DESIGN.md` as future work. Behavioral compliance is model- and version-dependent, not guaranteed.

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

r8 remains fully installable and is the last validated release; its 2026-05-29 golden-task ledger reads 5 PASS / 3 PARTIAL / 0 FAIL (the 3 PARTIALs treated as UNTESTED under the honest-ledger rule):

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
