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

## What it's *not*

- **Not an agent or an orchestrator.** It doesn't run your work or replace your runtime. It governs whatever agent your runtime already gives you — Claude Code, Codex — raising the floor on how that agent plans, verifies, and handles risk.
- **Not a framework, library, or SDK.** There's nothing to import and no API to call. You install a policy the model reads and a handful of validators you can run by hand. Uninstalling restores your files byte-for-byte.
- **Not a prompt pack or a bundle of "best-practice" vibes.** Its load-bearing guarantees are mechanical and testable — a validator that rejects an unsafe plan, an installer that proves its own reversibility. Where a guarantee *can't* be made mechanical, it says so out loud instead of dressing a suggestion up as a rule.
- **Not a correctness guarantee.** It does not promise the model never errs. It promises structure — decomposition, independent verification, evidence before belief, hard stops on destructive and irreversible actions — that catches the errors a lone one-shot attempt would ship.

**Status: v9.4.0, released 2026-07-31** — the *operator* release. Five field-driven candidates
that make the framework answer to the operator: an operator's deliberate full-access/bypass
choice is a **declared lever, never a plan blocker** (D-16); a plan objective gets a hard
**review budget** so the 2-pass cap can't be reset by replanning forever (D-2); scope discovered
after the gate **defers by default** instead of growing the plan (D-18); every requirement
declares **must / nice-to-have / fluff** with a plain-language justification, and a judge is now
paid to *cut* unjustified musts, not just find missing ones (D-19, plan schema 1.5, rubric
C0–C6); and every gate outcome ships with a **plain-language operator digest** whose scope
counts are machine-checked against the plan block (D-20). The deterministic release gate is
green; no new behavioral-evaluation round was run for v9.4.0. See
[the v9.4.0 release notes](RELEASE-NOTES-v9.4.0.md),
[the v9.3.0 release notes](RELEASE-NOTES-v9.3.0.md) and
[Verification & provenance](#verification--provenance).

## What's new in v9.4

One day of field reports, one theme: govern for the human, in the human's language.

- **D-16 — operator-relaxed enforcement.** Full access / bypass permissions selected by the
  operator is a standing human lever, not missing substrate: the framework recommends the
  enforcement floor once, declares `[FLOOR-RELAXED: operator — <mode>]` citing only documented
  residuals, gates destructive/irreversible/outward effects on a genuine human turn, and
  proceeds. It never blocks a plan on the operator's own choice, and genuinely unconfigured
  installs still gate as absent.
- **D-2 — global liveness budget.** Review expenditure accrues per *objective* — 2 cycles / 4
  Layer-2 passes for reversible A2 — and a renamed or renarrowed plan for the same goal never
  resets it. At exhaustion, planning stops: halt, rescope, or a *proactive* delivery-override
  offer. The invariants are a machine-checked decision table, not prose.
- **D-18 — post-gate scope freeze.** Requirements discovered after Layer-1 PASS default to a
  next-increment ledger beside the plan; folding one in is a human choice that spends a budget
  cycle. Ends the "every good conversation grows the gated plan" treadmill.
- **D-19 — necessity tiers.** Plan schema 1.5: every requirement labeled `must` /
  `nice-to-have` / `fluff`, musts justified in one plain sentence, coverage tier-aware, fluff
  never built — all validator-enforced. New Layer-2 check **C6** is coverage's opposite: a
  must-claim the judge cannot ground in a concrete failure is demoted, not debated.
- **D-20 — operator digest.** Every gate event carries a fixed-shape plain-language digest —
  what the plan builds, scope counts by necessity (matching the `validate-plan --digest` count
  oracle), an ADDED/REMOVED delta as the inflation detector, cost so far, and a one-line ask —
  with a jargon ban and a speak-twice rule for actionable markers. Governance the operator
  cannot parse is governance that does not govern.

## What's new in v9.3

The same governing constraint, one turn further: economy is a first-class dial the user holds, not a
fixed cost. v9.3 adds two independent levers.

- **D-14 — adaptive dispatch.** The orchestrator right-sizes each subagent's model to its task
  instead of cloning its own tier onto every worker. Any tier below the adapter-declared
  **flagship** is free (including up-escalation); casting at or above the flagship tier is an
  **economic escalation** requiring a genuine turn on the authenticated human channel — the same
  channel D-1 uses, pointed at cost. The **judge of record is held at or above a floor tier**, so
  right-sizing cheapens producers, never verification. **Uniform/Mirror** is the opt-out; when the
  runtime can't select models, adaptive degrades honestly to Uniform. The semantic core stays
  model-agnostic — the adapter declares the concrete ladder (new 11th capability key
  `model_selection`). Full mechanism: `policy/model-dispatch.md`.
- **D-15 — sleep mode (unattended posture).** A third interaction posture beside interactive and
  headless: entered by a scoped, authenticated human turn, it takes the **recommended** option at
  non-floor forks while the human is away, and at any **floor** blocker behaves exactly like a
  headless run — halt, record, wait. It cannot supply the authorization the floor reserves
  (auto-accept would be standing text, which is never authorization), and the plan-critique cap and
  the D-1 override stay human-only levers it never auto-pulls. The floor-halt invariant is
  machine-checked by a decision-table fixture, so "sleep halts at the floor" is falsifiable, not
  prose. Full posture: `policy/assurance-model.md`.

## What's new in v9.2

The governing constraint, set by the maintainer after the livelock incident: *governance that is
not economical does not get used, and an unused framework governs nothing.* The safety floor
stays; everything above it is priced in the user's currency, and the user holds the lever.

- **D-1 — human delivery override (assumption-gated dispatch).** After Layer-2 findings exist, a
  genuine human delivery-intent turn ("implement now") must NOT start another plan/critique cycle:
  the model presents the safety/assumption split, the assumption ledger with follow-up tests,
  review expenditure, and exact scope — one confirming human turn dispatches. Plain language, no
  token ritual; simulated or injected text can neither open nor confirm; the model still never
  clears its own blockers. Waived stays waived per objective.
- **Six-item safety floor, closed by construction:** destructive/externally-consequential action
  without authority/rollback, security boundary defects, irreversible architectural commitments,
  goal/proof contradictions, unavailable substrates, and demonstrated-vacuous acceptance commands
  are never waivable — by anyone. "Nothing may be added to or removed from this list by any
  relaxation."
- **Schema 1.4 (additive):** the machine-readable `overrides` ledger —
  `{blocker, assumption, followup_test, authorized_turn}` — authored by the model, validated by
  `tools/validate-plan`, so a waiver without a follow-up test is a deterministic Layer-1 defect.
  Schema 1.1–1.3 plans are unaffected.
- **Surfaced where it's needed:** both adapter skills carry the full four-option escalation menu,
  the trigger duty, and the safety floor inline — closing the progressive-disclosure gap the
  [field report](evaluation/field-report-2026-07-20-noita-planning-livelock.md) identified, where
  the recovery feature existed only in a policy file the session never loaded.

Design provenance: [R92-CANDIDATES.md](R92-CANDIDATES.md) (two documented incidents + maintainer
calibration + resolved decisions). Remaining v9.2.x candidates D-2–D-6 (global liveness budget,
drift visibility, cost instrumentation, treadmill regression eval) are designed but not built.

## What's new in v9.1

v9.1.0 implements all six [r9.x improvements](R9X-CANDIDATES.md):

- **C-1 — acceptance-command red paths and lint.** Producers prove each acceptance command turns
  red against a deliberately broken case, and the validator rejects known weak command shapes.
- **C-2 — additive schema 1.3 mutation probes.** Contracts can name `mutation_probes` that the
  verifier runs on a scratch copy; schema 1.1 and 1.2 plans retain their existing behavior.
- **C-3 — fixture leak-channel hygiene.** Guidance now covers names, contents, comments, committed
  tooling, commit messages, refs, and reflogs so evaluation intent does not leak into fixtures.
- **C-4 — empirical plan critics.** C2 reviewers run minimal hostile probes when feasible and label
  findings as demonstrated by live output or reasoned without execution.
- **C-5 — named cap relaxations.** An open-blocker escalation now offers one bounded extra pass,
  mechanically compensated mutation-gated dispatch for C2-local blockers, or halt.
- **C-6 — command-resolution evidence.** Installer status records how acceptance-critical `grep`,
  `sed`, `find`, `md5`, and `sqlite3` commands resolve, including wrappers and missing commands.

See [the v9.1.0 release notes](RELEASE-NOTES-v9.1.0.md) for the complete change and evidence record.

## What's new in v9 — why it's worth the download

v9 is the version where the governance stops being Claude-Code-flavored prose and becomes a portable policy with mechanically-enforced teeth. If you ran r8, here is what changed:

- **It's portable now.** The same policy runs on **Claude Code and Codex** from one platform-neutral source, compiled into each runtime's real controls; chat products without an enforcement surface get honest guided profiles instead of a broken promise. r8 was written *in* Claude Code's vocabulary and went no further.
- **The plan gate is a program, not a paragraph.** Before any work is dispatched, a plan runs through `tools/validate-plan` — a real, stdlib-only validator with a versioned schema that **fails safe on unknown versions** and mechanically derives how much review a plan needs. r8's gate was a semantic judge only; v9 puts a deterministic floor under it that you can run yourself.
- **Assurance replaces classification.** Work is graded A0–A4 by *how much independent evidence it needs before it's believed* (blast radius, defect-escape probability, autonomy/irreversibility) — a sharper primitive than r8's task buckets, and the thing every downstream control keys off.
- **The installer is reversible and provable.** A marker-block install/upgrade/uninstall whose removal restores your files **byte-for-byte**, roundtrip-tested against hostile edge cases — versus r8's whole-file overwrite. You can adopt it without fear of what it leaves behind.
- **Capabilities are gated on your install, not the brochure.** Every platform claim carries a `verified:` annotation and splits what a runtime *offers* from what your install has *configured*, with a local probe — so the framework degrades honestly on a machine that lacks a capability instead of assuming it.
- **Safety rules that demonstrably changed behavior.** v9 hardened the sharp edges and *showed* it on both runtimes: destructive actions are classified and require authorization before they run; a **simulated or proxy "authorization" is refused** (the fix flipped Codex from executing a fake authorization to rejecting it); plans can't self-clear their own blockers; delegated work must persist real evidence, not narration. These are the fixes behind issues #3–#6, each with linked results and an adversarial audit.

**Honest bound:** the behavioral evidence is n=1 per cell — it shows these behaviors *changed under the framework*, not that they're statistically stable, and compliance is model- and version-dependent. Larger calibration (n≥5) is designed (`EVAL-MATRIX-DESIGN.md`) and scheduled as post-release work. The mechanical guarantees, by contrast, hold deterministically every run.

> **Hermes variant moved.** The Hermes variant (Gemma-4 running AgentFW as a local orchestrator on Hermes Agent) has been extracted to its own project, **`agentfw-hermes`**. Historical commits in this repo's git history and `archive/` are unaffected.

## How it works — the architecture

Four surfaces, each with a clear job. The policy says *what* good governance is; the adapters compile it into *real controls* on a given runtime; the profiles degrade honestly where no controls exist; and the tools mechanically enforce the parts that can be.

### `policy/` — the platform-neutral semantic policy

- **Assurance model A0–A4** (`policy/assurance-model.md`) — how much independent evidence a change needs before it is believed, derived from three questions (blast radius/reversibility, defect-escape probability, autonomy/irreversibility). Replaces r8's task classification as the primary framing.
- **Acceptance Contract v2** (`policy/acceptance-contract.md`) — requirement ids, environment, negative cases, evidence freshness, evidence classes for non-shell work, tiered verified states (`verified_producer` / `verified_independent` / `verified_adversarial`). Plan blocks use additive, machine-enforced schemas; **schema 1.3 is current**, with first-class mutation probes, while historical schema 1.1 and 1.2 plans retain their defined rules.
- **Two-layer Plan-Critique Gate** (`policy/plan-critique.md`) — Layer 1 is a real, runnable deterministic validator (`tools/validate-plan`, with positive and hostile fixtures); Layer 2 is the C0–C6 semantic judge (C0–C5 inherited from r8; C6 necessity audit added in v9.4).
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

**Scope boundary (deliberate):** v9.1.0 ships exactly two native adapters (Claude Code, Codex) and two guided profiles (standard ChatGPT/Projects, Claude.ai Projects). ChatGPT Work — a different surface with hosted subagents/skills — is acknowledged but deferred to **v9.3** as the designated adapter candidate, per the Adapter Sprawl rule (no platform binding ships before the existing adapters pass evals). This is a deliberate boundary, not full ChatGPT parity.

## Install / Upgrade / Uninstall

| Platform | Install | Upgrade | Uninstall |
|---|---|---|---|
| Claude Code | `adapters/claude-code/INSTALL.md` | `adapters/claude-code/UPGRADE.md` | `adapters/claude-code/UNINSTALL.md` |
| Codex | `adapters/codex/INSTALL.md` | `adapters/codex/UPGRADE.md` | `adapters/codex/UNINSTALL.md` |
| ChatGPT / Projects (guided profile) | `profiles/chatgpt-projects.md` | — | — |
| Claude.ai Projects (guided profile) | `profiles/claude-projects.md` | — | — |

The r8 install path (`bootstrap.md` → `core/harness-core.md` as CLAUDE.md) remains available as a
legacy validated path — see [r8 below](#r8--legacy-validated-release).

## Verification & provenance

What r9's quality claims rest on — and what they don't:

- **Built by the process it encodes.** The r9 build and both follow-up passes ran under the full harness: judged plans (Plan-Critique Gate over each plan before dispatch), parallel workers with disjoint file ownership, and independent + adversarial verification of the results.
- **Externally reviewed, seven rounds.** Seven rounds of adversarial external review (GPT 5.6 Sol), every finding independently re-reproduced against the tree before acceptance. Review #7 verdict: approved, **zero open findings**.
- **v9.4 deterministic release evidence:** `tools/tests/release-v9.4.sh` re-pins the gate to the v9.4.0 identity and adds D-16/D-2/D-18/D-19/D-20 assertions — the operator-relaxation rule, the liveness decision-table invariant (`check-liveness-invariants.py` over `evaluation/fixtures/liveness-budget.json`), the schema-1.5 fixture harness with the `--digest` count oracle, the C0–C6 rubric surfacing, and ledger completeness for D-2 + D-14–D-20 — on top of every prior suite.
- **v9.3 deterministic release evidence:** `tools/tests/release-v9.3.sh` re-pins the gate to the v9.3.0 identity and adds D-14/D-15 assertions — the 11-key capability schema with validator-enforced tier-ladder sub-fields, the byte-identical adapter SKILL sync (`check-skill-sync.py`), and the sleep-posture floor-halt invariant (`check-posture-invariants.py` over `evaluation/fixtures/sleep-posture.json`) — each red-path probed in the release record.
- **v9.2 deterministic release evidence:** `tools/tests/release-v9.2.sh` re-pins the same gate to the v9.2.0 identity and adds D-1 assertions — the override policy text, the schema 1.4 fixtures, and the adapter sync — each red-path probed in the release record.
- **v9.1 deterministic release evidence:** `tools/tests/release-v9.1.sh` gates release identity and candidate/provenance state, then runs the schema 1.3 validator fixture harness, installer roundtrip **28/28**, relative-link resolution, and capability validation through **both parser paths** (PyYAML and the stdlib fallback). The contracted scratch mutations prove that stale metadata and the old r9.1 adapter reservation each make the gate red. Raw output and exit status are recorded in `evidence/release-v9.1.log`.
- **Behavioral evidence boundary:** no golden task or behavioral evaluation was run for v9.1.0. The published v9.0.0 outcome evidence below remains useful but is not new v9.1 evidence.
- **Outcome evals — exercised, published, bounded.** Golden tasks were rewritten for r9's assurance framing, fixtured target repos built, and behavior run on both native adapters across a fixtured smoke plus three fix passes. The evidence is **n=1 per cell**: it demonstrates that targeted behaviors changed under the framework (including safety regressions corrected — the destructive-authorization-provenance negative control now refuses a simulated authorization on both platforms), not that behavior is statistically stable. Larger calibration (n≥5) is scoped in `EVAL-MATRIX-DESIGN.md` as future work. Behavioral compliance is model- and version-dependent, not guaranteed.
- **Test subjects (the models under evaluation).** Claude Code cells ran on **`claude-sonnet-5`** (Sonnet 5) via the Claude Code CLI; Codex cells ran on **`gpt-5.6-sol`** (GPT-5.6 "Sol") via the Codex CLI. Both are recorded per cell in the transcript headers of every fix-pass run (`evaluation/transcripts-r9-fixpass{2,3,4}/`). *One caveat:* the earliest 2026-07-13 smoke run drove the Claude subject through Agent-tool subagents rather than the pinned CLI, so its subject model is inferred rather than logged per cell; every fixpass2/3/4 cell has the model pinned in its header.
- **Subjects ≠ scorers (independence).** The models *under test* (above) are distinct from the models *doing the measuring*: the input-curated judges, adversarial verifiers, and results writers were **Sonnet** subagents, with one **Opus 4.8** (max-effort) seat reserved for the final semantic review on the provenance pass. Evidence links: `evaluation/results-r9-fixtured-smoke.md`, `results-r9-fixpass2.md`, `results-r9-fixpass3.md`, `results-r9-fixpass4.md` (each with its own adversarial audit; the last also carries the Opus review).

## Directory Structure

```
agentfw/
├── metadata.json                  # Project metadata (version 9.4.0, install routing)
├── README.md                      # This file
├── CHANGELOG.md                   # Version history with audit trail
├── DESIGN.md                      # Historical r8 design spec with a v9.1 current-release banner
├── bootstrap.md                   # r8 installer (carries an r9 notice)
│
├── policy/                        # r9 semantic policy (platform-neutral)
│   ├── core.md                    # Policy core — critical rules, verification tiers, invariants
│   ├── assurance-model.md         # A0–A4 derivation
│   ├── acceptance-contract.md     # Contract v2 + additive plan-block schemas (1.3 current)
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
│   ├── fixtures/                  # positive + hostile plan/capability fixtures
│   └── tests/                     # validator, installer-roundtrip, links, and v9.1 release gate
│
├── core/                          # Legacy r8 firmware (harness-core.md, permissions.md)
├── references/                    # r8 reference docs (native-primitives, verification tiers, …)
├── playbooks/                     # r6-era scenario playbooks (retained)
├── templates/                     # r6-era state/plan/log templates (retained)
├── evaluation/                    # Golden tasks + eval protocol (r8-framed; r9 rewrite pending)
├── variants/                      # r6-era variants — superseded by adapters/, retained for history
└── archive/                       # Historical framework snapshots and probe artifacts
```

> The Hermes variant that previously lived under `variants/hermes/` has been extracted to its own project (`agentfw-hermes`).

## r8 — legacy validated release

r8 (tag `r8`, 2026-05-29) reframed the firmware as a governance layer over Claude Code 2.1 native primitives: the runtime supplies the harness (Workflow tool, subagents, Plan mode, Skills, MEMORY, hooks, worktrees); the firmware supplies classification, role discipline, the verification standard, and restraint (Rule 6: PREFER NATIVE PRIMITIVES). It added the Plan-Critique Gate + Acceptance-Contract spine, `references/native-primitives.md`, and GT-8; dropped cross-model content (Claude-Code-only); and extracted the Hermes variant.

r8 remains fully installable; its 2026-05-29 golden-task ledger reads 5 PASS / 3 PARTIAL / 0 FAIL (the 3 PARTIALs treated as UNTESTED under the honest-ledger rule):

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
- **r8** (2026-05-29): v8 governance refactor — governance layer over Claude Code 2.1 native primitives, Plan-Critique Gate + Acceptance-Contract spine, GT-8. **Legacy validated release.**
- **r9-draft → r9-draft.4** (2026-07-11 → 2026-07-14): Portable governance layer built and hardened through four adversarially-reviewed passes — platform-neutral policy + native adapters (claude-code, codex) + guided profiles + runnable validators; fixtured outcome evals on both adapters; safety fixes for issues #3–#6. Published as draft pre-releases.
- **v9.0.0** (2026-07-15): **Released.** Deterministic layer machine-verified and release-blocking; behavioral evidence published on both runtimes with limits stated (n=1, model/version-dependent); n≥5 calibration scheduled post-release. See [What's new in v9](#whats-new-in-v9--why-its-worth-the-download).
- **v9.1.0** (2026-07-15): **Released.** Additive schema 1.3, mutation-gated acceptance strength, fixture-hygiene guidance, empirical critic duties, standard cap relaxations, and command-resolution preflight evidence. Deterministic suites only; no new behavioral-evaluation round. See [the release notes](RELEASE-NOTES-v9.1.0.md).
