# PLAN — AgentFW v9.6 "the operator compass" (D-21 / D-22 / D-25) — rev 2

**Objective (root):** `operator-compass` — the operator must never again spend two days across
two runtimes on one objective without knowing that zero features have shipped. Every mechanism
in this plan exists to keep the operator oriented while an agent is inside a gate cycle.

**Revision note (rev 2, 2026-08-01):** local revise after Layer-2 pass 1 (dual, both judges
BLOCKERS — all C2/coverage class). Changes: T1/T2 acceptance commands now gate on the checker
selftest's exact output signal (`[ "$(…)" = "…_SELFTEST_OK" ]` — a zero-byte checker exits 0
even under a bare `--selftest` invocation, demonstrated during revision, so exit-code gating
alone was insufficient); T1 verifies the durable-ledger shape mechanically (R1 was verified
nowhere); T2's checker extension is now discriminated by a case-deletion mutation probe that
stays green under the shipped checker; T4 invokes `tools/check-skill-sync.py` (divergence probe
now mechanical, demonstrated red); T5 greps its full deliverable roster and `test -s`'s the
field report (an empty report previously passed, demonstrated); provenance citations corrected
to the installed capability snapshot; R3's `because` rewritten with the concrete
budget-remaining scenario one judge asked for. All four revised witness pairs re-recorded
against the new command digests.

**Field evidence:** the drydock failure-routing workstream, 2026-07-30 → 2026-08-01. Five review
rounds on one clause of one of thirteen requirements; zero of twelve sibling tasks dispatched;
15 governance-only commits; the treadmill ran across BOTH runtimes (Claude Code and Codex),
each restarting the counters, and the operator learned the delivered-feature count was zero only
by asking three escalating times. Companion reports:
`evaluation/field-report-2026-07-31-drydock-scope-accretion.md` (planning half) and the new
`evaluation/field-report-2026-08-01-drydock-zero-delivery.md` this plan ships (execution half).

**Design keystone (from the cross-runtime fact):** counters and scoreboards CANNOT live in a
session or a runtime. The objective ledger is a durable JSON file beside the plan
(`<plan>.ledger.json`), read and updated by whichever runtime touches the objective. A counter
that dies with the session cannot bound anything; drydock proved it twice in two runtimes.

## Assurance derivation

- **Q1 blast radius & reversibility:** policy documents, fixtures, one new stdlib checker, and
  adapter text inside this git repo — every edit trivially reversible; nothing destructive,
  no history rewriting, no external effects.
- **Q2 defect-escape probability:** real — the seams are policy↔fixture↔checker and
  policy↔both-adapters; a prose/mechanical divergence (D-16's documented failure class) escapes
  a producer-only check.
- **Q3 autonomy & irreversibility:** planner runs supervised; workers dispatched per task; no
  irreversible or outward-facing step. No A3 escalator applies.

⇒ **A2**, dual plan-review tier (declared above the derived single floor — chosen because this
plan changes the gate itself). Verification: producer always; independent judge at the seams
(all tasks here declare `independent`).

**Capability preflight note (declared degradation):** the INSTALLED capability snapshot
(`~/.claude/skills/agentfw/active-capabilities.yaml`, `generated: "20260731-195713"`) shows
`deterministic_permissions_configured: false` — the settings deny rules are not active on this
install. All work is repo-local reversible file edits, so the behavioral ask-tier and worker
scope budgets carry the control load; recommended once: enable the `settings.example.json` deny
set. Not a floor item; declared, not blocking. (The repo-root `active-capabilities.yaml` copy
is stale — `generated: "20260715-123112"`, no `command_resolution` block; T5's provenance work
includes refreshing it via `agentfw-install status`.)

## Requirements

**Musts (won't work without):**

- **R1 — Durable objective ledger.** Machine-readable `<plan>.ledger.json` beside every A2+
  plan: objective slug, `root_objective`, gate cycles, Layer-2 passes, workers dispatched,
  tasks verified, one appended entry per gate event with the writing runtime named. Both
  runtimes read/update the same file. The shape is machine-validated via the fixture's
  `ledger_example` record.
- **R2 — Scoreboard at every gate event.** Fixed marker
  `[SCOREBOARD: objective <slug> — musts built b/t · workers dispatched w · verified v · cycle n/2 · passes m/4]`
  emitted at every gate event, with a plain-language rendering in every D-20 operator digest.
  Counts derive from the ledger and `validate-plan --digest`, never from narration.
- **R3 — Zero-dispatch tripwire.** Two or more completed gate cycles on an objective with
  `workers_dispatched == 0` forces the D-2 exhaustion fork immediately (proactive override
  offer / rescope / halt) even when liveness budget remains. Machine-checked as a decision
  table, same pattern as D-2.
- **R4 — Budget & ledger inheritance.** A sub-objective — decomposed, renamed, re-planned, or
  resumed in another runtime — spends from the ROOT objective's ledger; liveness markers name
  the root slug; counters never reset on decomposition.
- **R5 — Session-start reconciliation.** Resuming a gated objective requires reading the ledger
  and re-deriving observed repo state by mechanical probes BEFORE any new gate cycle:
  `[RECONCILE: objective <slug> — ledger claims X, observed Y — MATCH|MISMATCH]`. A MISMATCH is
  corrected in the ledger before planning may continue.

**Deferred (next-increment ledger, per D-18 — deliberately NOT in this build):**

- R6 increment-shape critique check (first dispatch wave lands ≥1 requirement end-to-end)
- R7 dependency-edge audit + partial-dispatch escalation option
- R8 stranded-implementation disposition rule
- R9 blocker re-validation on age
- R10 cross-substrate consult lane (D-17)

## Machine-readable plan

```json agentfw-plan
{
  "version": "1.6",
  "assurance": "A2",
  "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "Durable per-objective ledger file (<plan>.ledger.json) recording cycles, passes, dispatched, verified, and writing runtime, shared across sessions and runtimes, shape machine-validated via the fixture's ledger_example record", "necessity": "must", "because": "counters that lived in conversation died at every session and runtime boundary — two days of drydock treadmill across Claude Code and Codex each restarted at cycle 1"},
    {"id": "R2", "text": "SCOREBOARD marker at every gate event plus plain-language rendering in every operator digest, counts derived from the ledger and validate-plan --digest", "necessity": "must", "because": "five gate rounds ran with zero shipped features and the operator had to ask three escalating times to learn it"},
    {"id": "R3", "text": "Zero-dispatch tripwire: >=2 completed gate cycles with zero dispatched workers forces the D-2 exhaustion fork even with budget remaining, machine-checked as a decision table", "necessity": "must", "because": "under an A3/A4-extended or future-raised cycle budget, cycles legitimately remain while zero workers have dispatched, and even at exhaustion the generic D-2 fork never names zero-delivery as the diagnosis — drydock's operator needed the delivery fact surfaced, not merely a stop"},
    {"id": "R4", "text": "Budget and ledger inheritance: sub-objectives, renames, re-plans, and cross-runtime resumes spend from the root objective's ledger; counters never reset on decomposition", "necessity": "must", "because": "the receipt-authority sub-objective minted fresh budgets while the thirteen parent requirements starved"},
    {"id": "R5", "text": "Session-start reconciliation: resuming a gated objective requires ledger-vs-observed-state probes and a RECONCILE marker before any new gate cycle; MISMATCH corrected first", "necessity": "must", "because": "fresh sessions inherited plan headers claiming progress while the repo contained zero implementation"},
    {"id": "R6", "text": "Increment-shape critique check: first dispatch wave must land at least one requirement end-to-end", "necessity": "nice-to-have"},
    {"id": "R7", "text": "Dependency-edge audit plus partial-dispatch escalation option", "necessity": "nice-to-have"},
    {"id": "R8", "text": "Stranded-implementation disposition rule for proof-built working code", "necessity": "nice-to-have"},
    {"id": "R9", "text": "Blocker re-validation on age (blockers open >=2 rounds must re-demonstrate failure)", "necessity": "nice-to-have"},
    {"id": "R10", "text": "Cross-substrate consult lane (D-17) for correlated-verifier blind spots", "necessity": "nice-to-have"}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "D-21: delivery ledger, scoreboard marker, zero-dispatch tripwire — policy section + decision-table fixture + stdlib checker",
      "deps": [],
      "contract": {
        "requirement_ids": ["R1", "R2", "R3"],
        "criteria": "policy/plan-critique.md gains a 'Delivery ledger, scoreboard & zero-dispatch tripwire (D-21)' section defining the durable <plan>.ledger.json shape (naming ledger.json explicitly), the [SCOREBOARD:] marker duty at every gate event, the digest rendering duty, and the tripwire fork; evaluation/fixtures/delivery-ledger.json encodes BOTH the decision table (zero-dispatch-at-threshold rows FORCE_FORK, dispatch or below-threshold rows CONTINUE, missing scoreboard is DEFECT, sub-objective row carries root_objective) AND a ledger_example record carrying the full ledger shape (objective, root_objective, cycles, layer2_passes, workers_dispatched, tasks_verified, gate_events[] each naming its writing runtime); tools/check-delivery-invariants.py (stdlib only) validates both, and its --selftest proves red/green discrimination for the tripwire AND the ledger shape, emitting exactly DELIVERY_SELFTEST_OK on success — the acceptance command gates on that exact output string, so a zero-byte or signal-less checker fails the command itself; a checker faking the signal without discriminating is caught at verification because the contracted fixture-mutation probes fail to go red under it",
        "acceptance_command": "bash -c '[ \"$(python3 tools/check-delivery-invariants.py --selftest)\" = \"DELIVERY_SELFTEST_OK\" ] && python3 tools/check-delivery-invariants.py evaluation/fixtures/delivery-ledger.json && grep -q \"SCOREBOARD\" policy/plan-critique.md && grep -q \"zero-dispatch\" policy/plan-critique.md && grep -q \"ledger.json\" policy/plan-critique.md && echo T1_D21_OK'",
        "expected_signal": "terminal line exactly T1_D21_OK with exit 0",
        "environment": "repo checkout, Python 3, no network; grep resolves to /usr/bin/grep per command_resolution in the installed active-capabilities.yaml (~/.claude/skills/agentfw/, generated 20260731-195713)",
        "evidence": "checker output and witness transcripts under evaluation/evidence/v9.6-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, change the two_cycles_zero_dispatch case action to CONTINUE — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, delete the SCOREBOARD marker paragraph from policy/plan-critique.md — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, replace check-delivery-invariants.py with a zero-byte file — the command must exit non-zero (selftest-signal gate)", "expected": "red"},
          {"mutation": "on a scratch copy, remove root_objective from the fixture's ledger_example — the command must exit non-zero", "expected": "red"}
        ],
        "witness_pair": {
          "red": {"tree": "bare scratch: no checker, no fixture, no policy section", "command_sha256": "6bb57a93138b08203f4e4c8902eee8c7496ba520abd980e92cf390e9e6a06d0c", "exit_code": 1, "evidence_path": "evaluation/evidence/v9.6-witness/T1-red.log"},
          "green": {"tree": "witness tree: prototype checker with signal-gated selftest + ledger_example validation, 6-case decision table + ledger_example fixture, policy stub carrying all three tokens", "command_sha256": "6bb57a93138b08203f4e4c8902eee8c7496ba520abd980e92cf390e9e6a06d0c", "exit_code": 0, "evidence_path": "evaluation/evidence/v9.6-witness/T1-green.log"}
        },
        "risk": "a hollow checker or prose-only tripwire would recreate the advisory-gauge failure this release exists to close",
        "negative_cases": [
          "a fixture row with completed_cycles >= threshold, workers_dispatched 0, and action CONTINUE exits non-zero",
          "a fixture row firing FORCE_FORK below threshold or with dispatched workers exits non-zero",
          "a scoreboard_emitted:false case with any action other than DEFECT exits non-zero",
          "a ledger_example missing any required key, or a gate event not naming its writing runtime, exits non-zero",
          "a zero-byte checker fails the selftest-signal gate (demonstrated during rev-2 witness recording)",
          "a checker that unconditionally prints the selftest signal passes the command but is flagged when the verifier executes the contracted mutation probes, which fail to go red under it (demonstrated by Layer-2 judges)"
        ]
      }
    },
    {
      "id": "T2",
      "title": "D-22: budget & ledger inheritance — amend D-2 policy section, extend liveness fixture and checker with root_objective enforcement",
      "deps": ["T1"],
      "contract": {
        "requirement_ids": ["R4"],
        "criteria": "policy/plan-critique.md's Global liveness budget section states that counters live in the durable ledger keyed by root_objective, that sub-objectives, renames, and cross-runtime resumes spend from the root ledger, and that liveness markers name the root slug; evaluation/fixtures/liveness-budget.json gains a sub_objective_inherits_root_counters case (root_objective set, counters_reset false) AND mentions root_objective in its description text (so the case-deletion mutation probe isolates checker enforcement from the grep leg); tools/check-liveness-invariants.py adds sub_objective_inherits_root_counters to REQUIRED_CASES, rejects any case carrying root_objective with counters_reset true, and its --selftest covers the inheritance rules, emitting exactly LIVENESS_SELFTEST_OK — the acceptance command gates on that exact output string (a zero-byte or signal-less checker fails the command; a signal-faking checker is caught at verification by the contracted mutation probes failing to go red)",
        "acceptance_command": "bash -c '[ \"$(python3 tools/check-liveness-invariants.py --selftest)\" = \"LIVENESS_SELFTEST_OK\" ] && python3 tools/check-liveness-invariants.py evaluation/fixtures/liveness-budget.json && grep -q \"root_objective\" evaluation/fixtures/liveness-budget.json && grep -q \"root_objective\" policy/plan-critique.md && echo T2_D22_OK'",
        "expected_signal": "terminal line exactly T2_D22_OK with exit 0",
        "environment": "repo checkout, Python 3, no network; grep resolves to /usr/bin/grep per command_resolution in the installed active-capabilities.yaml (~/.claude/skills/agentfw/, generated 20260731-195713)",
        "evidence": "checker output and witness transcripts under evaluation/evidence/v9.6-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, delete the sub_objective_inherits_root_counters case while leaving the root_objective mention in the fixture description — the command must exit non-zero under the delivered checker (this probe stays GREEN under the pre-v9.6 shipped checker, so it also detects a reversion; demonstrated during rev-2 witness recording)", "expected": "red"},
          {"mutation": "on a scratch copy, set counters_reset true on the sub_objective_inherits_root_counters case — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, replace check-liveness-invariants.py with a zero-byte file — the command must exit non-zero (selftest-signal gate)", "expected": "red"}
        ],
        "witness_pair": {
          "red": {"tree": "bare scratch: no checker, no fixture, no policy text", "command_sha256": "320d2f128593a71546f9bb4c676276c3c9b4be3aed3d3055349327b827b41887", "exit_code": 1, "evidence_path": "evaluation/evidence/v9.6-witness/T2-red.log"},
          "green": {"tree": "witness tree: prototype EXTENDED checker (REQUIRED_CASES + root_objective/counters_reset rule + inheritance selftest) + extended fixture + policy stub carrying the token", "command_sha256": "320d2f128593a71546f9bb4c676276c3c9b4be3aed3d3055349327b827b41887", "exit_code": 0, "evidence_path": "evaluation/evidence/v9.6-witness/T2-green.log"}
        },
        "risk": "inheritance that exists only in prose lets the next sub-objective mint a fresh budget exactly as drydock's receipt-authority did",
        "negative_cases": [
          "a fixture case with root_objective set and counters_reset true exits non-zero",
          "a fixture lacking the sub_objective_inherits_root_counters required case exits non-zero under the updated checker",
          "a zero-byte checker fails the selftest-signal gate"
        ]
      }
    },
    {
      "id": "T3",
      "title": "D-25: session-start reconciliation duty — recovery policy section, RECONCILE marker, plan-critique cross-reference",
      "deps": ["T1"],
      "contract": {
        "requirement_ids": ["R5"],
        "criteria": "policy/recovery.md gains a resume-reconciliation section: before any new gate cycle on a resumed A2+ objective, read the ledger, re-derive observed state with mechanical probes (validator run, evidence-file presence, repo greps for claimed deliverables), and emit [RECONCILE: objective <slug> — ledger claims X, observed Y — MATCH|MISMATCH]; a MISMATCH must be corrected in the ledger before planning continues, and a claimed-verified task whose acceptance evidence is absent reverts to unverified; policy/plan-critique.md cross-references the duty at gate entry",
        "acceptance_command": "bash -c 'grep -q \"RECONCILE\" policy/recovery.md && grep -q \"MISMATCH\" policy/recovery.md && grep -q \"RECONCILE\" policy/plan-critique.md && echo T3_D25_OK'",
        "expected_signal": "terminal line exactly T3_D25_OK with exit 0",
        "environment": "repo checkout, POSIX shell; grep resolves to /usr/bin/grep per command_resolution in the installed active-capabilities.yaml (~/.claude/skills/agentfw/, generated 20260731-195713)",
        "evidence": "grep output and witness transcripts under evaluation/evidence/v9.6-witness/, produced_after_change; independent reviewer reads the section against R5",
        "required_verification_tier": "independent",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, delete the reconciliation section from policy/recovery.md — the command must exit non-zero", "expected": "red"}
        ],
        "witness_pair": {
          "red": {"tree": "bare scratch: no policy files", "command_sha256": "952a6dd2e76386693cb33479f653ae86fc12ae30efdc1aa3e75c60e19ee3e1d8", "exit_code": 2, "evidence_path": "evaluation/evidence/v9.6-witness/T3-red.log"},
          "green": {"tree": "witness tree: recovery and plan-critique stubs carrying the marker and MISMATCH rule", "command_sha256": "952a6dd2e76386693cb33479f653ae86fc12ae30efdc1aa3e75c60e19ee3e1d8", "exit_code": 0, "evidence_path": "evaluation/evidence/v9.6-witness/T3-green.log"}
        },
        "risk": "without a blocking reconciliation rule, resumed sessions keep planning on top of fictional progress; token greps alone cannot distinguish a blocking rule from an advisory one — the independent reviewer's semantic reading (negative case 2) is the contracted compensation for this prose-deliverable ceiling",
        "negative_cases": [
          "removing the MISMATCH sentence from recovery.md turns the command red",
          "independent reviewer confirms the section requires correction BEFORE new cycles, not alongside them"
        ]
      }
    },
    {
      "id": "T4",
      "title": "Adapter & kernel sync: D-21/D-22/D-25 paragraphs inside the AGENTFW-SYNC block of both adapter SKILL.md files, scoreboard line in both kernel bootloaders",
      "deps": ["T1", "T2", "T3"],
      "contract": {
        "requirement_ids": ["R1", "R2", "R5"],
        "criteria": "adapters/claude-code/skills/agentfw/SKILL.md and adapters/codex/skills/agentfw/SKILL.md gain the scoreboard/ledger duty and the RECONCILE resume duty INSIDE the AGENTFW-SYNC fenced block so byte-identity is mechanically enforced by tools/check-skill-sync.py; adapters/claude-code/CLAUDE-block.md and adapters/codex/AGENTS.md each carry a one-line SCOREBOARD mention so the kernel names the marker; adapter text never contradicts policy (policy remains authoritative)",
        "acceptance_command": "bash -c 'python3 tools/check-skill-sync.py && grep -q \"SCOREBOARD\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"SCOREBOARD\" adapters/codex/skills/agentfw/SKILL.md && grep -q \"RECONCILE\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"RECONCILE\" adapters/codex/skills/agentfw/SKILL.md && grep -q \"SCOREBOARD\" adapters/claude-code/CLAUDE-block.md && grep -q \"SCOREBOARD\" adapters/codex/AGENTS.md && echo T4_SYNC_OK'",
        "expected_signal": "terminal line exactly T4_SYNC_OK with exit 0",
        "environment": "repo checkout, Python 3, POSIX shell; grep resolves to /usr/bin/grep per command_resolution in the installed active-capabilities.yaml (~/.claude/skills/agentfw/, generated 20260731-195713)",
        "evidence": "sync-checker output and witness transcripts under evaluation/evidence/v9.6-witness/, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, alter one adapter's sync-block paragraph so the pair differs by one word — the command must exit non-zero (check-skill-sync.py leg; demonstrated red during rev-2 witness recording)", "expected": "red"},
          {"mutation": "on a scratch copy, remove the codex SKILL.md paragraph entirely — the command must exit non-zero", "expected": "red"}
        ],
        "witness_pair": {
          "red": {"tree": "bare scratch: no adapter files, no sync tool", "command_sha256": "0ea9fbf1091098de8d787b38198a7025acfd386097b33323173ec328ca48aa99", "exit_code": 2, "evidence_path": "evaluation/evidence/v9.6-witness/T4-red.log"},
          "green": {"tree": "witness tree: the shipped check-skill-sync.py + two SKILL stubs with byte-identical AGENTFW-SYNC blocks carrying both tokens + two kernel stubs", "command_sha256": "0ea9fbf1091098de8d787b38198a7025acfd386097b33323173ec328ca48aa99", "exit_code": 0, "evidence_path": "evaluation/evidence/v9.6-witness/T4-green.log"}
        },
        "risk": "a mechanism the runtimes never see governs nothing — drydock's treadmill ran on the runtime whose adapter lagged a release behind; one adapter updated and the other forgotten is the exact D-3 failure the sync block exists to stop",
        "negative_cases": [
          "deleting either kernel bootloader's SCOREBOARD line turns the command red",
          "a one-word divergence between the two adapters' sync blocks turns the command red (mechanical, not reviewer-dependent)"
        ]
      }
    },
    {
      "id": "T5",
      "title": "Provenance: CANDIDATES.md entries D-21..D-27, zero-delivery field report, CHANGELOG entry, capability snapshot refresh",
      "deps": ["T1", "T2", "T3"],
      "contract": {
        "requirement_ids": ["R1", "R3", "R5"],
        "criteria": "CANDIDATES.md registers D-21 (ledger/scoreboard/tripwire), D-22 (inheritance), D-25 (reconciliation) with build status and anchors, plus proposed entries D-23 (increment-shape + dependency-edge audit), D-26 (stranded-implementation disposition), D-27 (blocker re-validation) and records D-24 (proof-cost inversion) as folded into D-21's rationale; evaluation/field-report-2026-08-01-drydock-zero-delivery.md is a non-empty report recording the execution-half evidence including the two-day cross-runtime treadmill and the zero-delivery accounting; CHANGELOG.md gains an unreleased v9.6.0 entry naming D-21, D-22, and D-25; the stale repo-root active-capabilities.yaml is refreshed via agentfw-install status. CONTRACT STRENGTHENED post-verification-rejection (2026-08-01): the acceptance command's token greps were replaced with the repo's discriminating registration check (tools/check-candidates.py, which requires the '## D-NN' section heading, all schema labels, and a status-board row per id) plus a v9.6.0 CHANGELOG heading anchor — the T5 judge demonstrated the original greps stayed green with the D-22 section deleted, an empty registration file, or a gutted CHANGELOG. Witness pair re-recorded against the new command digest; the as-written D-22 section-deletion probe now goes red",
        "acceptance_command": "bash -c 'python3 tools/check-candidates.py D-21 D-22 D-23 D-24 D-25 D-26 D-27 && grep -q \"^## v9\\.6\\.0\" CHANGELOG.md && grep -q \"D-21\" CHANGELOG.md && grep -q \"D-22\" CHANGELOG.md && grep -q \"D-25\" CHANGELOG.md && test -s evaluation/field-report-2026-08-01-drydock-zero-delivery.md && echo T5_DOCS_OK'",
        "expected_signal": "terminal line exactly T5_DOCS_OK with exit 0",
        "environment": "repo checkout, POSIX shell; grep resolves to /usr/bin/grep per command_resolution in the installed active-capabilities.yaml (~/.claude/skills/agentfw/, generated 20260731-195713)",
        "evidence": "grep output and witness transcripts under evaluation/evidence/v9.6-witness/, produced_after_change; independent reviewer checks the field report against the source transcript facts",
        "required_verification_tier": "independent",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {"mutation": "on a scratch copy, delete the D-22 entry from CANDIDATES.md — the command must exit non-zero", "expected": "red"},
          {"mutation": "on a scratch copy, truncate the field report to zero bytes — the command must exit non-zero (test -s leg; demonstrated red during rev-2 witness recording)", "expected": "red"}
        ],
        "witness_pair": {
          "red": {"tree": "bare scratch: no docs, no registration checker", "command_sha256": "c99f4da9aaa1a0f530746cf10dfd22713f3b314b30e49dfaa44c621fe704083a", "exit_code": 2, "evidence_path": "evaluation/evidence/v9.6-witness/T5-red.log"},
          "green": {"tree": "witness tree: shipped check-candidates.py + registered CANDIDATES + v9.6.0-headed CHANGELOG stub + non-empty report", "command_sha256": "c99f4da9aaa1a0f530746cf10dfd22713f3b314b30e49dfaa44c621fe704083a", "exit_code": 0, "evidence_path": "evaluation/evidence/v9.6-witness/T5-green.log"}
        },
        "risk": "mechanisms without registered provenance are invisible to the next session — the exact orientation failure this release closes",
        "negative_cases": [
          "removing the CHANGELOG v9.6.0 entry turns the command red",
          "a zero-byte field report turns the command red",
          "independent reviewer confirms the field report's counts (5 rounds, 0 dispatched, 15 governance commits, 2 runtimes) match the transcript"
        ]
      }
    }
  ]
}
```

## Witness evidence (rev 2)

All ten legs re-recorded 2026-08-01 after the pass-1 revision, whole-command-only, from tree
roots under the session scratchpad; transcripts in
`evaluation/evidence/v9.6-witness/T{1..5}-{red,green}.log`. Red legs exited non-zero on bare
scratch trees; green legs exited 0 on planner-authored witness trees. Additionally demonstrated
during rev-2 recording (producer-level, judge-repeatable from the preserved trees):
zero-byte-checker trees now fail T1 and T2 (selftest-signal gate); a one-word adapter
divergence fails T4 (check-skill-sync.py leg); a zero-byte field report fails T5 (`test -s`
leg); and T2's case-deletion mutation goes red under the extended prototype checker while
staying green under the shipped checker — the probe discriminates a reversion. Witness trees
preserved at the session scratchpad `witness/` directory for judge re-execution.

## Deliberately out of scope (D-18 next-increment ledger)

R6–R10 above. Also out: any throughput target or velocity opinion (the framework reports, never
optimizes — operator currency only), wall-clock caps, mechanical objective-identity detection,
and automated confidence-calibration tracking — all fail the guarantee-vs-encourage test or the
thesis boundary discussed 2026-08-01.
