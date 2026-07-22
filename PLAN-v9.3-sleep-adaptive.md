# PLAN — AgentFW v9.3: Sleep Mode (D-15) + Adaptive Dispatch (D-14)

Build provenance for the v9.3 cycle. Design of record: `CANDIDATES.md` D-14/D-15. Approved plan:
`~/.claude/plans/velvet-dancing-moler.md` (2026-07-21). Assurance **A2** (multi-component,
revertible-in-repo, real seams; additive/non-destructive), with A3 controls on the live-install
and release seams.

## Naming (settled)
- **Adaptive** (default) vs **Uniform/Mirror** (opt-out) — model axis; gate = **flagship cap**.
- **Sleep mode** / **unattended posture** — interaction axis; third posture beside `headless`.

## Resolved decisions (maintainer, 2026-07-21)
1. Build this session.
2. **Flagship cap:** any tier below the flagship is free (incl. up-escalation); only the
   adapter-declared flagship tier needs the authenticated-channel lever.
3. **Two independent dials:** Adaptive default-on; sleep mode a separate posture; optional "away"
   preset may flip both.

## Substrate facts (verified 2026-07-21)
- `tools/validate-capability` `SPEC_KEYS` is 10 and rejects **unexpected top-level keys** ⇒ the
  tier ladder lives as **sub-fields under `model_selection`** (`tiers`, `flagship`, `floor`).
- Kernel blocks: claude-code = `adapters/claude-code/CLAUDE-block.md`; codex = `adapters/codex/AGENTS.md`.
- Release gate: `tools/tests/release-v9.2.sh` (env-var driven; ends `RELEASE_V9_2_OK`). v9.3 clones
  it to `tools/tests/release-v9.3.sh`; the v9.2 gate is retired to historical (it asserts v9.2.0
  current-facing text the README bump will change).
- Capability preflight: `isolated_agents` / `parallel_agents` / `independent_review` active;
  `scheduled_resume` `partial/unverified` ⇒ D-15's truly-unattended variant degrades honestly
  (present-but-AFK works via the authenticated channel).

## Layer-2 pass 1 (dual, 2026-07-21) — outcome
Both disjoint-input critics returned BLOCKERS; both independently confirmed the **design is
coherent** (sleep does not launder authorization; flagship-cap reuses the D-1 channel; the
verifier tier-floor is orthogonal to the verification-tier binding). Every blocker was **C2
acceptance-command strength** (noun-grep commands defeated by hostile fixtures) ⇒ **local revise**.
This plan is the revision: behavioral claims become executed checks, the partial-update trap is
closed in the validator, and each checker is a contracted deliverable with its own red-path.

## Harness calibration (declared)
Producer = main session (design coherence for the kernel change). Independence enforced at the
judge tier: Layer-2 `agentfw-plan-critic` before dispatch; independent `agentfw-verifier` after,
re-executing every `acceptance_command` and every mutation probe on scratch copies. Layer-1
`validate-plan` first.

## Sequencing
T7 (sync checker) + T1 (capability schema) + T6 (ledger) → T2 (policy) → T5 (posture invariant
checker + fixture + eval) and T3 (agents+skills+kernels) → T4 (release gate). Then confirmed steps:
live install (both runtimes), open issues #20/#21.

```json agentfw-plan
{ "version": "1.4", "assurance": "A2", "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "D-14 adaptive dispatch: orchestrator right-sizes model per subagent; flagship-cap gate reuses the authenticated-channel lever; verifier AND plan-critic never cast below a declared floor tier; Uniform/Mirror opt-out."},
    {"id": "R2", "text": "New capability key model_selection with adapter-declared tier ladder (tiers/flagship/floor sub-fields, validator-enforced); absent/unconfigured degrades honestly to Uniform; validator + both instances + capability-contract.md updated to 11 keys with no stale ten-key prose."},
    {"id": "R3", "text": "D-15 sleep/unattended posture: entered by a scoped authenticated human turn; auto-selects the recommended option at non-floor forks; at the floor (incl. flagship-cap) behaves like headless — halt/degrade, never auto-authorize."},
    {"id": "R4", "text": "Inline surfacing of Adaptive/Uniform/flagship-cap and the sleep posture + markers, byte-synced across both adapter SKILLs by a proven checker, plus a one-line pointer in both kernel blocks."},
    {"id": "R5", "text": "Release gate asserts 11-key schema green on both instances and the SKILL sync; a machine-executed invariant proves the flagship gate and the sleep floor-halt (fixture + checker with red-path), documented in a D-6-shape eval cell."},
    {"id": "R6", "text": "Ledger entries D-14 and D-15 recorded in CANDIDATES.md with the standard seven-label schema and status-board rows, mechanically verified."}
  ],
  "tasks": [
    { "id": "T7", "title": "Build check-skill-sync.py (proven checker)", "deps": [],
      "contract": { "requirement_ids": ["R4"],
        "criteria": "tools/check-skill-sync.py compares the AGENTFW-SYNC-delimited block between the two adapter SKILL.md files and exits non-zero on any difference; --selftest proves red-on-desync and green-on-identical using temporary copies.",
        "acceptance_command": "bash -c 'python3 tools/check-skill-sync.py --selftest && echo T7_OK'",
        "expected_signal": "terminal line exactly T7_OK with exit 0",
        "environment": "repo root; python3", "evidence": "selftest output produced_after_change",
        "integration_seam": true, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy of tools/check-skill-sync.py, force the block comparison to always report equal", "expected": "red"}],
        "risk": "a sync checker that cannot detect a desync makes R4/R5 unverifiable",
        "negative_cases": ["--selftest desync fixture stays green ⇒ FAIL"], "rerunnable": true }},
    { "id": "T1", "title": "Capability schema: model_selection (11th key, ladder-enforced)", "deps": [],
      "contract": { "requirement_ids": ["R2"],
        "criteria": "validate-capability recognises exactly 11 keys incl. model_selection, REQUIRES model_selection to carry tiers/flagship/floor sub-fields, and prints its key count from len(SPEC_KEYS) (no literal 10/11 count strings); both instances declare model_selection with available/configured/verified plus the three sub-fields; capability-contract.md documents the key and the degrade-to-Uniform rule with no stale ten-key prose.",
        "acceptance_command": "bash -c 'python3 tools/validate-capability adapters/claude-code/capability.yaml && python3 tools/validate-capability adapters/codex/capability.yaml && grep -q model_selection policy/capability-contract.md && grep -q sub-field tools/validate-capability && ! grep -rInE \"(ten|eleven|10|11) (spec |capability )?keys\" tools/validate-capability policy/capability-contract.md adapters/claude-code/capability.yaml adapters/codex/capability.yaml && echo T1_OK'",
        "expected_signal": "terminal line exactly T1_OK with exit 0 (both instances PASS)",
        "environment": "repo root; python3", "evidence": "validator PASS output produced_after_change",
        "integration_seam": true, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy of adapters/claude-code/capability.yaml, remove the model_selection block", "expected": "red"}, {"mutation": "on a scratch copy of adapters/claude-code/capability.yaml, delete the flagship sub-field from model_selection", "expected": "red"}, {"mutation": "on a scratch copy of tools/validate-capability, revert SPEC_KEYS to the original 10 keys", "expected": "red"}, {"mutation": "on a scratch copy of policy/capability-contract.md, seed the stale phrase 'the ten capability keys'", "expected": "red"}],
        "risk": "schema/instance drift or a stale key-count silently disables the Adaptive-vs-Uniform gating fact (the partial-update trap)",
        "negative_cases": ["an instance missing model_selection ⇒ FAIL", "model_selection without tiers/flagship/floor ⇒ FAIL", "a stale 'the 10 capability keys' string present ⇒ FAIL"], "rerunnable": true }},
    { "id": "T6", "title": "Ledger entries D-14/D-15 + check-candidates.py", "deps": [],
      "contract": { "requirement_ids": ["R6"],
        "criteria": "CANDIDATES.md carries D-14 and D-15 full entries, each containing all seven labels (Status, Origin, Evidence, Problem, Proposed mechanism, Anchors, Cold-start verification) and a status-board row; tools/check-candidates.py verifies, per id, that the entry section contains every label and a matching status-board row.",
        "acceptance_command": "bash -c 'python3 tools/check-candidates.py D-14 D-15 && echo T6_OK'",
        "expected_signal": "terminal line exactly T6_OK with exit 0",
        "environment": "repo root; python3", "evidence": "checker output produced_after_change",
        "integration_seam": false, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy of CANDIDATES.md, blank the D-15 entry body leaving only its heading", "expected": "red"}, {"mutation": "on a scratch copy of CANDIDATES.md, remove only the 'Cold-start verification' label from the D-15 entry", "expected": "red"}],
        "risk": "a hollow heading passing as a full entry breaks the design-of-record",
        "negative_cases": ["an entry missing any of the seven labels ⇒ FAIL", "a missing status-board row ⇒ FAIL"], "rerunnable": true }},
    { "id": "T2", "title": "Policy: model-dispatch + sleep posture", "deps": ["T1"],
      "contract": { "requirement_ids": ["R1", "R3"],
        "criteria": "policy/model-dispatch.md exists covering Adaptive, Uniform/Mirror opt-out, the flagship cap, the verifier/plan-critic floor, the adapter-declared ladder, and honest degradation; assurance-model.md adds the unattended/sleep posture beside headless with floor non-delegability and headless-style floor halt; recovery.md and plan-critique.md reflect sleep auto-selection with floor halt; core.md indexes the new file. Floor-non-delegability is behaviorally proven by T5.",
        "acceptance_command": "bash -c 'test -f policy/model-dispatch.md && grep -qi flagship policy/model-dispatch.md && grep -qi uniform policy/model-dispatch.md && grep -qi floor policy/model-dispatch.md && grep -qi \"sleep\\|unattended\" policy/assurance-model.md && grep -qi headless policy/assurance-model.md && grep -qi floor policy/assurance-model.md && grep -q model-dispatch policy/core.md && echo T2_OK'",
        "expected_signal": "terminal line exactly T2_OK with exit 0",
        "environment": "repo root", "evidence": "grep/test output produced_after_change plus independent coherence read; behavior gated by T5",
        "integration_seam": false, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, remove the sleep-posture paragraph from assurance-model.md", "expected": "red"}],
        "risk": "incoherent floor-delegation semantics would let sleep mode launder authorization (behaviorally caught by T5)",
        "negative_cases": ["model-dispatch.md missing ⇒ FAIL", "Uniform toggle undocumented ⇒ FAIL", "core.md index not updated ⇒ FAIL"], "rerunnable": true }},
    { "id": "T5", "title": "Posture invariant: fixture + checker + eval (behavioral proof)", "deps": ["T2"],
      "contract": { "requirement_ids": ["R5", "R3"],
        "criteria": "tools/check-posture-invariants.py reads a canonical decision-table fixture (evaluation/fixtures/sleep-posture.json) and asserts flagship-cap is in the floor set, every floor-class fork maps to HALT (never auto-authorize), and non-floor forks may map to auto-recommended; --selftest proves a conformant table passes and a laundering table (flagship→auto at the floor) is rejected. evaluation/eval-v9.3-sleep-adaptive.md is the D-6-shape scenario doc referencing the fixture and the SLEEP-HALT marker.",
        "acceptance_command": "bash -c 'python3 tools/check-posture-invariants.py --selftest && python3 tools/check-posture-invariants.py evaluation/fixtures/sleep-posture.json && test -f evaluation/eval-v9.3-sleep-adaptive.md && grep -q SLEEP-HALT evaluation/eval-v9.3-sleep-adaptive.md && echo T5_OK'",
        "expected_signal": "terminal line exactly T5_OK with exit 0",
        "environment": "repo root; python3", "evidence": "selftest + fixture-validation output produced_after_change",
        "integration_seam": false, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy of evaluation/fixtures/sleep-posture.json, map the flagship-cap fork to auto-authorize", "expected": "red"}, {"mutation": "on a scratch copy of evaluation/fixtures/sleep-posture.json, delete the HALT action from a floor-class fork", "expected": "red"}],
        "risk": "without an executed invariant the sleep floor-halt is unfalsifiable (the D-6 lesson)",
        "negative_cases": ["a laundering table passes ⇒ FAIL", "the checker ignores the table ⇒ FAIL"], "rerunnable": true }},
    { "id": "T3", "title": "Agents + both SKILLs (synced) + both kernel blocks", "deps": ["T2", "T7"],
      "contract": { "requirement_ids": ["R1", "R4"],
        "criteria": "both adapter SKILL.md carry a verbatim-identical AGENTFW-SYNC block (Adaptive default + Uniform toggle + flagship cap + sleep posture + markers) that check-skill-sync.py passes; agentfw-verifier.md AND agentfw-plan-critic.md state the model tier floor; agentfw-implementer.md states adaptive right-sizing; both kernel blocks (CLAUDE-block.md and codex AGENTS.md) gain a one-line pointer.",
        "acceptance_command": "bash -c 'python3 tools/check-skill-sync.py && grep -qi floor adapters/claude-code/agents/agentfw-verifier.md && grep -qi floor adapters/claude-code/agents/agentfw-plan-critic.md && grep -qiE \"adaptive|right-siz\" adapters/claude-code/agents/agentfw-implementer.md && grep -qiE \"sleep|flagship\" adapters/claude-code/CLAUDE-block.md && grep -qiE \"sleep|flagship\" adapters/codex/AGENTS.md && grep -qi uniform adapters/claude-code/skills/agentfw/SKILL.md && grep -qi flagship adapters/claude-code/skills/agentfw/SKILL.md && echo T3_OK'",
        "expected_signal": "terminal line exactly T3_OK with exit 0",
        "environment": "repo root; python3", "evidence": "check-skill-sync PASS output produced_after_change",
        "integration_seam": true, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, change one word inside the synced block in only the codex SKILL", "expected": "red"}, {"mutation": "on scratch copies, empty the AGENTFW-SYNC block in BOTH SKILLs so they stay byte-identical but contentless", "expected": "red"}],
        "risk": "unsynced skills mean one runtime silently lacks the new behavior (the D-3 failure mode)",
        "negative_cases": ["desynced blocks ⇒ check-skill-sync FAIL", "plan-critic def missing the floor ⇒ FAIL", "a kernel block missing the pointer ⇒ FAIL"], "rerunnable": true }},
    { "id": "T4", "title": "Release gate v9.3 + notes + version", "deps": ["T1", "T3", "T5", "T7"],
      "contract": { "requirement_ids": ["R5"],
        "criteria": "tools/tests/release-v9.3.sh (modeled on release-v9.2.sh) asserts v9.3.0 identity (metadata 9.3.0/r9.3; current-facing README/CHANGELOG/DESIGN/RELEASE-NOTES-v9.3.0.md) and RUNS validate-capability on both instances via both parser paths, check-skill-sync.py, check-posture-invariants.py --selftest, check-candidates.py D-14 D-15, and the existing validate-plan/install-roundtrip/check-links suites; it prints RELEASE_V9_3_OK. The superseded release-v9.2.sh is retired to historical.",
        "acceptance_command": "bash -c 'bash tools/tests/release-v9.3.sh && grep -q 9.3.0 metadata.json && echo T4_OK'",
        "expected_signal": "terminal line exactly T4_OK with exit 0 after RELEASE_V9_3_OK",
        "environment": "repo root; python3 with PyYAML", "evidence": "gate stdout produced_after_change",
        "integration_seam": true, "risk_class": "standard", "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy pointed to by AGENTFW_RELEASE_ROOT, desync the two SKILL blocks and run release-v9.3.sh", "expected": "red"}, {"mutation": "on a scratch copy, set metadata.json version to 9.2.0", "expected": "red"}, {"mutation": "on a scratch AGENTFW_RELEASE_ROOT, launder evaluation/fixtures/sleep-posture.json (flagship fork to auto) and run release-v9.3.sh", "expected": "red"}],
        "risk": "a gate that green-lights drift or the wrong version defeats the distribution-integrity lesson",
        "negative_cases": ["desynced skills ⇒ gate exits non-zero", "wrong version in metadata ⇒ FAIL", "gate omits a checker ⇒ its mutation stays green"], "rerunnable": true }}
  ]}
```

## Build outcome (2026-07-21)
**COMPLETE — independently VERIFIED.** All 7 tasks (T1–T7) producer-checked; the independent
`agentfw-verifier` re-executed all 7 acceptance commands (green, exact signals) and all 15
contracted mutation probes (each RED), plus 5 directed negatives and 4 hostile probes (clean).
`release-v9.3.sh` → `RELEASE_V9_3_OK`. Governance path: Layer-1 PASS → Layer-2 dual pass 1
(BLOCKERS, design confirmed coherent) → local revise → Layer-2 dual pass 2 (BLOCKERS, C2
command-strength) → cap reached → human authorized **mutation-gated dispatch** → build → VERIFIED.
Pending confirmed steps (human-gated): live install to both runtimes; open issues #20/#21; commit.

## Verification (end-to-end, post-build)
- `validate-capability` PASS on both instances at 11 keys with ladder sub-fields enforced;
  `check-skill-sync.py` PASS; `check-posture-invariants.py --selftest` PASS; desync/laundering → FAIL → revert.
- Independent `agentfw-verifier` re-executes T1/T3/T4/T5/T7 acceptance + every mutation probe on scratch copies.
- `release-v9.3.sh` prints `RELEASE_V9_3_OK`; the SKILL-desync and wrong-version probes fail the gate.
- Confirmed steps last: live install to both runtimes; open issues #20/#21.
