# PLAN-r9 — AgentFW r9: semantic policy + native platform adapters

Status: DRAFT pending Plan-Critique Gate verdict. Author: planner session 2026-07-11.

## Objective

Build AgentFW r9: a platform-neutral **semantic policy** (`policy/`) plus **native adapters**
(`adapters/claude-code/`, `adapters/codex/`) and **guided degradation profiles** (`profiles/`),
incorporating the accepted improvements from the r9 design review (assurance model A0–A4, two-layer
Plan-Critique Gate with a real deterministic validator, acceptance contract v2, capability contracts,
invariants-not-APIs for state/effects, anti-patterns carried forward, markers kept as forcing
functions) plus first-class **clean upgrade and clean uninstall** instructions per platform.

## Substrate grounding (C0 — verified against live repo 2026-07-11)

- Repo root `/Users/briantaylor/Projects/AgentFW`, branch `main`, clean tree at `90f3e7e`. (`git status`)
- r8 core `core/harness-core.md` = **13,480 bytes** (`wc -c`). Installed live at `~/.claude/CLAUDE.md`
  (14,256 bytes — includes user's non-AgentFW "MCP Usage Instructions" section) as a **whole file with
  no delimiter markers** → upgrade tooling must handle marker-less prior installs.
- `variants/claude-code/CLAUDE.md` = **12,547 bytes of r6 content** (stale; superseded by r9 `adapters/`).
  `variants/claude-projects/` + `variants/generic/` exist (r6-era). (`find variants -type f`)
- `metadata.json` version = `8.0.0`, compatibility `["claude-code"]`. (`cat metadata.json`)
- No `policy/`, `adapters/`, `profiles/`, or `tools/` directories exist yet. (`ls`)
- Existing eval suite: `evaluation/golden-tasks.md`, latest run `results-2026-05-29.md` (5 pass / 3
  partial-reclassified — r9 docs must carry the honest re-ledger: 5 pass / 3 UNTESTED).

## Requirements

- **R1** Semantic policy core is platform-neutral: names no vendor runtime primitive; vendor names appear only as `adapters/…` path references.
- **R2** Assurance model A0–A4 replaces task classes; derived from 3 questions (blast radius/reversibility, defect-escape probability, autonomy/irreversibility); marker `[ASSURANCE: Ax — justification]` mandatory before material action (visible-rationale decision retained).
- **R3** Verification tiers producer / independent / adversarial bound to assurance levels, with evidence rules (recorded machine-check output, freshness = produced after change, unrestarted service = unverified).
- **R4** Acceptance Contract v2 schema (requirement_ids, criteria, verification{command, environment, expected, negative_cases}, evidence, risk, constraints, rerunnable) incl. non-shell evidence path for docs/research; Tier-1 = ≥1 negative/regression assertion the command runs.
- **R5** Plan-Critique Gate split into Layer 1 deterministic validation (a real, runnable `tools/validate-plan` with positive AND negative fixtures) + Layer 2 semantic judge inheriting the C0–C5 rubric; A2+ only for Layer 2; hard 2-pass cap; open blocker escalates to human.
- **R6** State, effects, and events specified as **invariants + minimum evidence**, never as function signatures (no prose-APIs); schemas exist only where a real validator consumes them.
- **R7** Capability contract spec + per-adapter `capability.yaml`; missing mandatory capability ⇒ reduce autonomy / human fallback; never simulate a missing capability; never silently substitute weaker verification.
- **R8** Anti-patterns carried forward as first-class policy, plus new r9 entries: Prose-API, Adapter Sprawl.
- **R9** Claude Code adapter: thin bootloader (safety kernel, ≤2,500 bytes) + `skills/agentfw/SKILL.md` (progressive disclosure) + 3 agent definitions (implementer, verifier, plan-critic) + `settings.example.json` + `capability.yaml`.
- **R10** Codex adapter: `AGENTS.md` bootloader (≤2,500 bytes) + skill + `config.example.toml` + `capability.yaml` whose platform claims are grounded in official docs (every capability annotated `verified:` with a source URL or `unverified`).
- **R11** Guided profiles (`profiles/chatgpt.md`, `profiles/claude-projects.md`) documented as honest lower-autonomy profiles, explicitly NOT adapters, with no-enforcement honesty statements.
- **R12** Clean UPGRADE (from r6/r7/r8 marker-less installs) and clean UNINSTALL per adapter, as INSTALL.md/UPGRADE.md/UNINSTALL.md; for Claude Code an idempotent `tools/agentfw-install` (install/upgrade/uninstall/status) using `<!-- AGENTFW:BEGIN r9 -->`/`<!-- AGENTFW:END r9 -->` block markers that **preserves the user's non-AgentFW content**, proven by a runnable roundtrip test.
- **R13** Repo integration is non-destructive (r8 `core/`/`references/`/`variants/` untouched); README r9 section, CHANGELOG r9 entry, metadata → `9.0.0-dev`; r9 labeled **draft — not eval-validated** everywhere status is stated.
- **R14** Recovery decision model as policy: failure scope (local|contract|architectural|environmental), blast-radius/contamination analysis, retry budget, explicit evidence invalidation, lesson-not-state carry-forward, fix-forward-when-safer.
- **R15** Context Health: event-triggered (post-compaction, pre-high-risk transition, repeated verification failures, requirement change, long-pause resume) + fallback interval (~3 verified tasks); `[CONTEXT HEALTH: …]` marker kept with evidence requirement.
- **R16** Cross-file consistency: single spec sheet governs shared terminology/values; all relative links in new files resolve; banned-vocabulary and marker-spelling checks pass.

---

## SPEC SHEET (authoritative shared artifact — copied verbatim into every worker dispatch)

Workers: where this spec sheet and your own judgment conflict, the spec sheet wins. It is the C3
consistency mechanism — do not improvise shared values.

### S1. Identity & status
- Version: **r9 / 9.0.0-dev**. Status string used everywhere: **"draft — not eval-validated (golden-task re-run pending)"**.
- Thesis (verbatim, appears in policy/core.md and README): *"r9 governs work through portable assurance
  contracts compiled into native runtime behavior where a runtime exists to compile into, and into
  explicit, evidence-bearing model commitments where it doesn't — with the honesty to say which is
  which per adapter."*

### S2. Markers (kept as forcing functions — model MUST emit; adapters may hide from end-user display)
- `[ASSURANCE: A0|A1|A2|A3|A4 — <one-line justification>]` before any material action. A0 may be a single short line. No silent skip; skipping a gate requires naming the relaxation.
- `[CONTEXT HEALTH: OK — <evidence>]` / `[CONTEXT HEALTH: DEGRADED — <rule/invariant>]`. A bare OK without evidence is Rubber-Stamp Compliance.

### S3. Assurance derivation (exactly 3 questions → level)
- **Q1 Blast radius & reversibility:** what does this touch; can it be trivially undone?
- **Q2 Defect-escape probability:** can a defect plausibly escape the producer's own checks (integration seams, production-only behavior: concurrency, trust-proxy, streaming, clock)?
- **Q3 Autonomy & irreversibility:** is the agent operating unsupervised; is any step irreversible or outward-facing?

| Level | Typical | Controls |
|---|---|---|
| A0 | lookup/explanation/tiny reversible edit | direct execution; producer check |
| A1 | bounded single-seam implementation | lightweight plan; producer tests (machine-checked) |
| A2 | multi-component / integration seams | decompose; independent verification at seams; Layer-1 plan validation; Layer-2 critique if ambiguity/shared values |
| A3 | production bug, security, infra, multi-file autonomous | independent workers + independent verifier; full acceptance contracts; both Plan-Critique layers; checkpoints |
| A4 | irreversible/destructive/critical autonomous | A3 + adversarial verification + explicit human authorization + rollback proof (restorability, not just backup integrity) |

Escalators (any one bumps ≥A3): production/live infra; security-sensitive; destructive/history-rewriting;
autonomous multi-file. Verification tiers: **producer** always; **independent** at A2 seams and all A3+;
**adversarial** at A4 and for security/destructive regardless of level.

### S4. Acceptance Contract v2 (fields; full spec in policy/acceptance-contract.md)
`requirement_ids[]`, `criteria`, `acceptance_command`, `environment` (where evidence is valid),
`expected_signal` (anchored — must not match a fail line), `negative_cases[]` (REQUIRED whenever `risk`
is present), `risk`, `evidence` (artifact types + freshness: produced_after_change), `rerunnable`
(bool), `constraints` (runtime/network). Tier-1 lever = ≥1 negative/regression assertion the command
RUNS. Non-shell work (docs/research/design): `acceptance_command` may be a named mechanical check
(grep/link-check/renderer) plus a designated independent reviewer; prose-only acceptance is never Tier-1.

### S5. Machine-readable plan block (consumed by tools/validate-plan)
Plans embed one fenced block opening exactly with ` ```json agentfw-plan ` and closing with ` ``` `:
```
{ "version": "1", "assurance": "A0|A1|A2|A3|A4",
  "requirements": [{"id": "R1", "text": "..."}],
  "tasks": [{ "id": "T1", "title": "...", "deps": ["T0"],
              "contract": { "requirement_ids": ["R1"], "criteria": "...",
                            "acceptance_command": "...", "expected_signal": "...",
                            "risk": "...", "negative_cases": ["..."], "rerunnable": true }}]}
```
Layer-1 checks (ALL mechanical): block parses as JSON; `assurance` present and valid; every requirement
id is covered by ≥1 task's `requirement_ids`; every task has a contract with non-empty
`criteria`+`acceptance_command`+`expected_signal`; `deps` reference existing task ids and are acyclic;
`risk` present ⇒ `negative_cases` non-empty; `assurance` A3/A4 ⇒ EVERY contract has non-empty
`negative_cases`. Exit 0 + `PASS` on success; on failure exit non-zero with a message that names BOTH the
offending task/requirement id AND the defect class via one of these keywords: `contract`, `cover`,
`cycl`, `negative`, `assurance`. python3 stdlib ONLY (json/re/sys — no PyYAML).

### S6. Vocabulary rules
- `policy/*.md` MUST NOT name vendor runtime primitives. Banned tokens in policy files:
  `CLAUDE.md`, `AGENTS.md`, `agent()`, `parallel()`, `pipeline()`, `ExitPlanMode`, `Copilot`,
  `claim_work_item`, `record_attempt`, `get_objective`. Vendor names (claude/codex/chatgpt/openai/
  anthropic, case-insensitive) may appear ONLY within `adapters/…` or `profiles/…` relative-path references.
  Mechanical check: `grep -riE 'claude|codex|chatgpt|openai|anthropic' policy/ | grep -vE 'adapters/|profiles/'` → empty.
- State/effects/events in policy are INVARIANTS + minimum evidence (e.g., "an authoritative store exists
  and is declared by the adapter"; "work items carry verification status + evidence references";
  "evidence is fresher than the change it verifies"), never function signatures or API names.
- Effects taxonomy dimensions (policy names them; adapters compile them): filesystem (read/write/delete
  scopes), process (run tests/start services), network (read/egress), version-control (commit/push/
  history-rewrite), external systems (create/send/deploy). Rule verbatim: *"Prompt instructions never
  count as enforcement when the platform offers deterministic controls."*

### S7. Capability contract (spec in policy/capability-contract.md; instances in adapters/*/capability.yaml)
Exactly these 10 keys, each `true|false|partial`, each with a `verified:` annotation (source URL, repo
path, or `unverified`): `filesystem, shell, isolated_agents, parallel_agents, persistent_state,
deterministic_permissions, worktree_isolation, scheduled_resume, independent_review, structured_output`.
Rules: never emit vendor tool syntax from the semantic core; never present conversational role-play as an
independent context; never silently substitute weaker verification; missing mandatory capability ⇒ reduce
autonomy or require human participation (declared, not silent).

### S8. Input-curation bright line (verbatim in policy/core.md and both verifier/plan-critic agent defs)
A judge of record receives ONLY: the requirements, the current state (diff, change summary, artifacts,
live repo), and the acceptance criteria/contracts. NEVER the producer's plan, reasoning, or
self-assessment. A producer's recorded check output is evidence to re-execute, not proof to accept.

### S9. Install-block convention (Claude Code adapter)
AgentFW content in a user-level instruction file lives between exactly:
`<!-- AGENTFW:BEGIN r9 -->` and `<!-- AGENTFW:END r9 -->` (own lines). Install = insert block (backup
first, `<file>.agentfw-backup-<date>`); upgrade = replace any existing `AGENTFW:BEGIN … AGENTFW:END`
block regardless of version tag, or detect marker-less r6/r7/r8 installs by heading heuristics
(`# AgentFW — Core Instructions` / `Agentic Harness Framework`) and offer extraction; uninstall = remove
block + skill dir + `agentfw-*` agent files, preserving ALL non-AgentFW content byte-for-byte; if the
file becomes empty/whitespace-only, remove it. `tools/agentfw-install` (bash) honors `CLAUDE_DIR` env
override (default `~/.claude`) so tests run in a sandbox; subcommands: `install|upgrade|uninstall|status`;
idempotent (re-running install ⇒ exactly one block). Install also copies `policy/` into
`$CLAUDE_DIR/skills/agentfw/policy/` so the skill's references resolve without the repo.

### S10. Canonical r9 file tree (workers write ONLY their assigned paths)
```
policy/core.md                    policy/assurance-model.md         policy/recovery.md
policy/anti-patterns.md           policy/acceptance-contract.md     policy/plan-critique.md
policy/capability-contract.md
tools/validate-plan               tools/agentfw-install
tools/fixtures/plan-good.md       tools/fixtures/plan-bad-missing-contract.md
tools/fixtures/plan-bad-cyclic.md tools/fixtures/plan-bad-uncovered-req.md
tools/fixtures/plan-bad-risk-without-negative.md
tools/tests/install-roundtrip.sh  tools/tests/check-links.sh
adapters/claude-code/{CLAUDE-block.md, skills/agentfw/SKILL.md,
  agents/{agentfw-implementer.md, agentfw-verifier.md, agentfw-plan-critic.md},
  settings.example.json, capability.yaml, INSTALL.md, UPGRADE.md, UNINSTALL.md}
adapters/codex/{AGENTS.md, skills/agentfw/SKILL.md, config.example.toml, capability.yaml,
  INSTALL.md, UPGRADE.md, UNINSTALL.md}
profiles/chatgpt.md               profiles/claude-projects.md
README.md (edit)                  CHANGELOG.md (edit)               metadata.json (edit)
```
(`CLAUDE-block.md` is the bootloader payload the installer wraps in AGENTFW markers — named so nobody
mistakes it for a full CLAUDE.md replacement.)

### S11. Style & content rules
- Match r8 voice: terse, directive, **WHY/WHEN/WHAT** framing for gates, bold rule names, tables where enumerable.
- Bootloaders (CLAUDE-block.md, adapters/codex/AGENTS.md) ≤ **2,500 bytes** each and contain the safety
  kernel: assurance classification + marker; invoke the agentfw skill for A2+; verification-evidence rule
  (no verified without recorded machine-check); side-effects through native controls; *"Never name or
  simulate a capability the current runtime does not expose."*; pointer to the skill for everything else.
- Profiles must each contain the exact phrases: **"not an adapter"** and **"no deterministic enforcement"**.
- Honest-limit paragraphs: policy/plan-critique.md states Layer 1 cannot judge command STRENGTH;
  README r9 section carries the S1 status string and the 5 pass / 3 UNTESTED eval re-ledger.
- Carry forward (adapted, not rewritten from scratch): C0–C5 rubric + GOOD/BAD contract exemplars +
  signal-anchoring footguns from `references/native-primitives.md`; anti-pattern catalog from
  `references/anti-patterns.md` (+ new **Prose-API**: specifying behavior as function signatures/APIs no
  runtime implements, creating the illusion of enforcement; + new **Adapter Sprawl**: shipping platform
  bindings that no eval has executed — an adapter you haven't tested is a profile you're lying about);
  trust-tier taxonomy from `core/permissions.md` recast as the effects taxonomy; recovery content from
  `references/error-recovery.md` recast per R14.

---

## Tasks

**T1 — Policy core.** Files: `policy/core.md`, `policy/assurance-model.md`, `policy/recovery.md`,
`policy/anti-patterns.md`. Sources to read: r8 `core/harness-core.md`, `references/anti-patterns.md`,
`references/error-recovery.md`, `core/permissions.md`, `references/verification-tiers.md`.
Scope: write only these 4 files. No network.

**T2 — Contracts + gate + validator.** Files: `policy/acceptance-contract.md`, `policy/plan-critique.md`,
`tools/validate-plan` (executable), 5 fixtures under `tools/fixtures/`. Sources:
`references/native-primitives.md` (C0–C5, exemplars, footguns). Scope: only these files. No network.

**T3 — Claude Code adapter + install tooling.** Files per S10 `adapters/claude-code/*`,
`tools/agentfw-install`, `tools/tests/install-roundtrip.sh`. Sources: r8 core (content basis for
SKILL.md), `bootstrap.md` + `variants/claude-code/install-notes.md` (prior install/upgrade art, to be
superseded), Claude Code agent-definition frontmatter conventions. Scope: only these files. No network.

**T4 — Codex adapter + profiles.** Files per S10 `adapters/codex/*`, `profiles/chatgpt.md`,
`profiles/claude-projects.md`. MUST verify platform claims against official OpenAI/Codex documentation
via web search/fetch; every capability.yaml entry annotated. Scope: only these files. Network: doc
lookup only.

**T5 — Capability spec + repo integration.** Files: `policy/capability-contract.md`,
`tools/tests/check-links.sh`, edits to `README.md` (r9 section + variants-superseded note + pointer to
adapter INSTALL/UPGRADE/UNINSTALL), `CHANGELOG.md` (prepend r9 entry), `metadata.json` (9.0.0-dev,
compatibility ["claude-code","codex"], core_file → policy/core.md). Scope: only these files. No network.

**T6 — Independent verification.** Separate verifier agent, input-curated per S8: receives requirements,
contracts, and the tree — not worker outputs/reasoning. Re-executes every acceptance command below plus
S6 vocabulary check, marker-spelling grep, and `tools/tests/check-links.sh`. Findings → planner → fix
dispatches.

Role separation: planner (this session) dispatches; workers T1–T5 are subagents writing disjoint paths
(C1: five seams, no shared files — T5 alone edits README/CHANGELOG/metadata); verifier T6 is a distinct
agent. Irreversible-op pre-mortem (C4): all changes are additions plus 3 tracked-file edits on a clean
tree — rollback = `git checkout -- README.md CHANGELOG.md metadata.json && git clean -fd policy adapters
profiles tools` (named new dirs only — never a bare `git clean` that could eat PLAN-r9.md); no history
rewriting, no pushes, no deletions of r8 content. T6 mechanically asserts r8 dirs untouched.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A3",
  "requirements": [
    {"id": "R1", "text": "Platform-neutral semantic policy core; vendor names only as adapter path references"},
    {"id": "R2", "text": "Assurance model A0-A4 with 3-question derivation and mandatory [ASSURANCE] marker"},
    {"id": "R3", "text": "Producer/independent/adversarial verification tiers bound to assurance levels with evidence rules"},
    {"id": "R4", "text": "Acceptance Contract v2 schema incl. negative cases, freshness, non-shell evidence path"},
    {"id": "R5", "text": "Two-layer Plan-Critique Gate: runnable deterministic validator + C0-C5 semantic judge"},
    {"id": "R6", "text": "State/effects/events as invariants + evidence, never prose-APIs; schemas only where validators consume them"},
    {"id": "R7", "text": "Capability contract spec + per-adapter capability.yaml with degradation rules"},
    {"id": "R8", "text": "Anti-patterns carried forward + new Prose-API and Adapter Sprawl entries"},
    {"id": "R9", "text": "Claude Code adapter: bootloader <=2500B, skill, 3 agents, settings example, capability.yaml"},
    {"id": "R10", "text": "Codex adapter doc-grounded with verified: annotations"},
    {"id": "R11", "text": "Guided profiles for ChatGPT and Claude.ai Projects with honesty statements"},
    {"id": "R12", "text": "Clean upgrade (from marker-less r6/r7/r8) and clean uninstall per adapter; installer preserves user content, proven by runnable roundtrip test"},
    {"id": "R13", "text": "Non-destructive repo integration; draft/not-eval-validated labeling; README/CHANGELOG/metadata updated"},
    {"id": "R14", "text": "Recovery decision model: scope, contamination, retry budget, evidence invalidation"},
    {"id": "R15", "text": "Context Health event triggers + fallback interval; marker kept with evidence"},
    {"id": "R16", "text": "Cross-file consistency: spec-sheet terminology, resolving links, vocabulary checks"}
  ],
  "tasks": [
    {"id": "T1", "title": "Policy core", "deps": [],
     "contract": {"requirement_ids": ["R1","R2","R3","R6","R8","R14","R15"],
      "criteria": "policy/{core,assurance-model,recovery,anti-patterns}.md exist, platform-neutral, carrying A0-A4 model, tiers, invariant-form state/effects, carried+new anti-patterns, recovery model, context-health events",
      "acceptance_command": "test -s policy/core.md -a -s policy/assurance-model.md -a -s policy/recovery.md -a -s policy/anti-patterns.md && grep -q '\\[ASSURANCE:' policy/core.md && grep -q 'A4' policy/assurance-model.md && grep -qi 'adversarial' policy/core.md && grep -qi 'Prose-API' policy/anti-patterns.md && grep -qi 'Adapter Sprawl' policy/anti-patterns.md && grep -qi 'retry' policy/recovery.md && ! grep -riE 'claude|codex|chatgpt|openai|anthropic' policy/core.md policy/assurance-model.md policy/recovery.md policy/anti-patterns.md | grep -vE 'adapters/|profiles/' | grep -q . && ! grep -qE 'claim_work_item|record_attempt|get_objective|agent\\(\\)|parallel\\(\\)|pipeline\\(\\)|ExitPlanMode' policy/core.md",
      "expected_signal": "exit 0",
      "risk": "vendor vocabulary or prose-APIs leaking into the neutral core (the r8 portability failure)",
      "negative_cases": ["grep for banned vendor tokens outside adapter-path references must find nothing", "grep for prose-API function names must find nothing"],
      "environment": "repo working tree, python3 + bash; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "T2", "title": "Contracts + gate + validator", "deps": [],
     "contract": {"requirement_ids": ["R4","R5"],
      "criteria": "acceptance-contract v2 spec + plan-critique doc (C0-C5 inherited, Layer1/Layer2, honest-limit) + runnable stdlib-only validator that passes the good fixture and THIS PLAN, and fails each bad fixture naming the defect",
      "acceptance_command": "test -s policy/acceptance-contract.md -a -s policy/plan-critique.md && grep -q 'negative_cases' policy/acceptance-contract.md && grep -qi 'produced_after_change\\|freshness' policy/acceptance-contract.md && grep -q 'C5' policy/plan-critique.md && grep -qi 'honest' policy/plan-critique.md && python3 tools/validate-plan tools/fixtures/plan-good.md && python3 tools/validate-plan PLAN-r9.md && d=$(mktemp -d) && ok=1 && for pair in missing-contract:contract cyclic:cycl uncovered-req:cover risk-without-negative:negative; do f=${pair%%:*}; k=${pair##*:}; cp tools/fixtures/plan-bad-$f.md $d/x.md; if python3 tools/validate-plan $d/x.md >$d/out 2>&1; then ok=0; fi; grep -qi $k $d/out || ok=0; done && test $ok = 1",
      "expected_signal": "PASS lines for good fixture and PLAN-r9.md; each bad fixture — re-run under a neutral filename — exits non-zero with a message containing its defect-class keyword",
      "risk": "validator green-lights structurally broken plans (rubber-stamp Layer 1)",
      "negative_cases": ["missing contract fixture rejected", "cyclic deps fixture rejected", "uncovered requirement fixture rejected", "risk-without-negative-cases fixture rejected"],
      "environment": "repo working tree, python3 + bash, mktemp scratch dirs for neutral-filename fixture copies; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "T3", "title": "Claude Code adapter + install tooling", "deps": [],
     "contract": {"requirement_ids": ["R9","R12"],
      "criteria": "complete adapter per S10 with bootloader <=2500B; installer with block markers, marker-less r6/r7/r8 upgrade detection, idempotence; roundtrip test proves user content survives install->upgrade->uninstall in a CLAUDE_DIR sandbox",
      "acceptance_command": "bash tools/tests/install-roundtrip.sh && test $(wc -c < adapters/claude-code/CLAUDE-block.md) -le 2500 && python3 -c \"import json;json.load(open('adapters/claude-code/settings.example.json'))\" && test -s adapters/claude-code/INSTALL.md -a -s adapters/claude-code/UPGRADE.md -a -s adapters/claude-code/UNINSTALL.md -a -s adapters/claude-code/skills/agentfw/SKILL.md -a -s adapters/claude-code/agents/agentfw-implementer.md -a -s adapters/claude-code/agents/agentfw-verifier.md -a -s adapters/claude-code/agents/agentfw-plan-critic.md && for k in filesystem shell isolated_agents parallel_agents persistent_state deterministic_permissions worktree_isolation scheduled_resume independent_review structured_output; do grep -q \"$k:\" adapters/claude-code/capability.yaml || exit 1; done && test $(grep -c 'verified:' adapters/claude-code/capability.yaml) -ge 10",
      "expected_signal": "roundtrip test prints PASS for: single-block idempotence, marker-less-r8 upgrade extraction, user-content byte-preservation after uninstall, no AGENTFW markers after uninstall; all exits 0",
      "risk": "upgrade or uninstall clobbers the user's non-AgentFW CLAUDE.md content (the live install at ~/.claude/CLAUDE.md carries a user MCP section today)",
      "negative_cases": ["after uninstall, grep AGENTFW in sandbox CLAUDE.md finds nothing while seeded user sentinel line is still present", "running install twice yields exactly one BEGIN marker"],
      "environment": "repo working tree, python3 + bash, CLAUDE_DIR mktemp sandboxes for install probes; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "T4", "title": "Codex adapter + profiles", "deps": [],
     "contract": {"requirement_ids": ["R10","R11"],
      "criteria": "Codex adapter files per S10 with doc-grounded capability.yaml (every key annotated verified:) and AGENTS.md bootloader <=2500B; profiles carry required honesty phrases",
      "acceptance_command": "test $(wc -c < adapters/codex/AGENTS.md) -le 2500 && for k in filesystem shell isolated_agents parallel_agents persistent_state deterministic_permissions worktree_isolation scheduled_resume independent_review structured_output; do grep -q \"$k:\" adapters/codex/capability.yaml || exit 1; done && test $(grep -c 'verified:' adapters/codex/capability.yaml) -ge 10 && grep -q 'not an adapter' profiles/chatgpt.md && grep -q 'no deterministic enforcement' profiles/chatgpt.md && grep -q 'not an adapter' profiles/claude-projects.md && grep -q 'no deterministic enforcement' profiles/claude-projects.md && test -s adapters/codex/INSTALL.md -a -s adapters/codex/UPGRADE.md -a -s adapters/codex/UNINSTALL.md -a -s adapters/codex/skills/agentfw/SKILL.md -a -s adapters/codex/config.example.toml",
      "expected_signal": "exit 0",
      "risk": "hallucinated Codex platform capabilities presented as fact (unverifiable adapter claims)",
      "negative_cases": ["a capability.yaml key lacking a verified: annotation fails the count check", "a profile missing the honesty phrases fails grep"],
      "environment": "repo working tree, python3 + bash; network for official platform-doc lookup only",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "T5", "title": "Capability spec + repo integration", "deps": [],
     "contract": {"requirement_ids": ["R7","R13"],
      "criteria": "capability-contract spec with the 10 keys + degradation rules; README r9 section (draft status + eval re-ledger + upgrade/uninstall pointers + variants-superseded note); CHANGELOG r9 entry; metadata 9.0.0-dev; link-checker script",
      "acceptance_command": "python3 -c \"import json;m=json.load(open('metadata.json'));assert m['version']=='9.0.0-dev' and 'codex' in m['compatibility']\" && head -5 CHANGELOG.md | grep -q 'r9' && grep -q 'draft' README.md && grep -qi 'UNTESTED' README.md && grep -q 'UNINSTALL' README.md && for k in filesystem shell isolated_agents parallel_agents persistent_state deterministic_permissions worktree_isolation scheduled_resume independent_review structured_output; do grep -q \"$k\" policy/capability-contract.md || exit 1; done && test -x tools/tests/check-links.sh",
      "expected_signal": "exit 0",
      "risk": "r9 presented as validated/released when no eval has run against it",
      "negative_cases": ["README lacking the draft status string fails grep", "metadata still 8.0.0 fails the assert"],
      "environment": "repo working tree, python3 + bash; no network",
      "evidence": "acceptance_command output and exit codes recorded in the worker report, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "T6", "title": "Independent verification", "deps": ["T1","T2","T3","T4","T5"],
     "contract": {"requirement_ids": ["R16","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10","R11","R12","R13","R14","R15"],
      "criteria": "input-curated verifier re-executes every T1-T5 acceptance command from the tree, plus vocabulary/marker/link consistency sweeps over ALL new files, r8-untouched assertion, roundtrip-script assertion review against T3's negative_cases, and spot-fetch of >=3 load-bearing capability verified: URLs (unfetchable => downgrade to unverified or file finding)",
      "acceptance_command": "bash tools/tests/check-links.sh && ! grep -riE 'claude|codex|chatgpt|openai|anthropic' policy/ | grep -vE 'adapters/|profiles/' | grep -q . && ! grep -rn '\\[ASSURANCE[^:]' policy/ adapters/ profiles/ | grep -q . && grep -rq '\\[CONTEXT HEALTH:' policy/ && ! grep -rn 'AGENTFW:BEGIN' policy/ && test -z \"$(git diff --name-only HEAD -- core references variants)\" && python3 tools/validate-plan PLAN-r9.md",
      "expected_signal": "verifier report: every acceptance command re-executed with recorded output; consistency sweeps clean; zero unresolved findings",
      "risk": "integration-only failures: terminology drift between workers, dangling cross-references, vendor vocabulary in T2/T5-written policy files, stray edits to r8 dirs",
      "negative_cases": ["a dangling relative link fails check-links", "a vendor token in ANY policy file outside an adapters/-profiles/ path reference fails the sweep", "an [ASSURANCE marker misspelling in any new file fails the sweep", "a worker edit to core/, references/, or variants/ fails the git-diff emptiness check"],
      "environment": "repo working tree, python3 + bash, CLAUDE_DIR mktemp sandboxes for install probes; no network",
      "evidence": "verifier report with re-executed acceptance_command outputs and exit codes, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "rerunnable": true}}
  ]
}
```

## Gate disposition

Assurance: **A3** (multi-file autonomous build; defects can escape any single producer; integration-only
failure modes) ⇒ both Plan-Critique layers required. Layer 1 (validate-plan) cannot run yet — the
validator is itself deliverable T2; per the temporal split, the block above is read as a spec at plan
time and MUST pass mechanically at T2 verification (it is T2's second positive fixture). Layer 2:
ONE semantic judge (structured default; docs/tooling on a clean reversible tree, not prod/infra) —
single-judge BLOCKER triggers a confirming pass before any re-plan; hard 2-pass cap; open blocker at cap
escalates to the human.

**Pass 1 record (2026-07-11, judge a6531b0bb634fa4aa):** VERDICT BLOCKERS — 2 blockers (7 deliverable
files unreachable by any acceptance_command; T6 consistency sweeps stated in prose but absent from the
command), 7 concerns. Both blockers quote literal command text and were confirmed by direct inspection of
the quoted strings (relaxation: mechanical confirmation of string-verifiable facts in lieu of a second
judge). Disposition: C2 local revise — all 7 unreached files added to T2/T3/T4 commands; T6 command now
carries the S6 vocabulary sweep, marker-misspelling and CONTEXT-HEALTH greps, r8-untouched git-diff
assertion; bad fixtures re-run under neutral filenames with defect-class keyword checks; `assurance`
field added to the S5 schema and this block; capability spec checked for all 10 keys; T6 instructed to
review the roundtrip script's assertions and spot-fetch capability `verified:` URLs; rollback scoped to
named paths. Plan proceeds as revised (pass 2 = the T6 re-execution of this same rubric over artifacts).
