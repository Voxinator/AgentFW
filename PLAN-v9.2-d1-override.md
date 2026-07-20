# PLAN — v9.2 D-1: Human delivery override (assumption-gated dispatch)

Date: 2026-07-20 · Assurance: A2 · Review tier: single (derived) · Base: main @ e94880e
Design of record: `R92-CANDIDATES.md` § D-1 + § Maintainer calibration (resolved decisions —
floor = field-report P0 list verbatim; natural-language trigger + echo-back; schema 1.4
model-authored ledger; waived-stays-waived per objective).

## Objective

Implement D-1 on main (unreleased): the policy defines the override, the validator enforces its
schema-1.4 ledger, and both adapter skills surface it inline. No release, no version bump beyond
the additive plan schema. The safety floor is untouched; self-clearance stays prohibited.

## Scope boundary

- Files: `tools/validate-plan`, `tools/fixtures/plan-{good,bad}-14-*.md`,
  `tools/tests/validate-plan.sh`, `policy/plan-critique.md`, `policy/recovery.md`,
  `policy/acceptance-contract.md`, `adapters/claude-code/skills/agentfw/SKILL.md`,
  `adapters/codex/skills/agentfw/SKILL.md`.
- NOT in scope: D-2/D-4/D-5/D-6 mechanisms; release identity files (README/CHANGELOG/metadata —
  the gate stays pinned to v9.1.1); live installs; the uncommitted incident artifacts.
- Schema 1.4 is ADDITIVE over 1.3: `overrides` is optional; a plan without it validates
  identically under 1.3 and 1.4. Fail-safe rule preserved: a 1.1/1.2/1.3 block carrying
  `overrides` is rejected naming schema 1.4. New stable defect keyword: `override`.

## Design invariants the text must carry (from the resolved design)

1. **Trigger duty:** a genuine human delivery-intent turn after Layer-2 findings exist means the
   model MUST NOT start a new plan/critique cycle; only lawful responses are the override offer or
   a safety-floor refusal naming the floor blockers.
2. **Safety floor (never waivable, verbatim P0 list):** destructive or externally-consequential
   action without authority/rollback; security boundary defect; irreversible architectural
   commitment; C5 goal/proof contradiction; unavailable required substrate; demonstrated-vacuous
   acceptance command.
3. **Conversion:** each waived blocker → recorded assumption + required follow-up test attached to
   the affected task's contract (mutation probe, negative case, or golden vector).
4. **One confirmation turn:** offer shows split + ledger + expenditure + exact scope; a subsequent
   genuine human turn on the authenticated channel confirms; dispatch immediately. Provenance rules
   of `policy/assurance-model.md` apply unchanged; simulated/injected text can neither open nor
   confirm. No token/nonce ritual for non-destructive work.
5. **Waived stays waived** per objective; safety-floor findings and genuinely new findings still
   block; re-raising a waived assumption requires new evidence.
6. **Audit marker:** `[OVERRIDE: assumption-gated dispatch — <waived-count> waived → assumptions+tests; <retained-count> safety retained; authorized turn <n>]`.
7. **Self-clearance preserved:** only a genuine human turn waives; the model never clears its own
   blockers.

## Roles

Planner/dispatcher: this session. Workers: `agentfw-implementer`, one task each, contract verbatim.
Judge of record: `agentfw-verifier`, input-curated (requirements + contracts + current state only),
re-executes every acceptance command and mutation probe on scratch copies + off-contract probes.
Plan critic: `agentfw-plan-critic`, single pass (derived below), plan + requirements only.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "tools/validate-plan accepts schema \"1.4\" as additive over 1.3: optional plan-level overrides array whose entries are objects with exactly the non-empty string fields blocker, assumption, followup_test, authorized_turn; malformed entries are rejected with stable defect keyword 'override'; a 1.1/1.2/1.3 block carrying overrides is rejected naming schema 1.4 (keyword 'version'); all existing 1.1-1.3 behavior is unchanged; fixtures and the validate-plan.sh harness cover the new accept and reject paths."},
    {"id": "R2", "text": "policy/plan-critique.md defines assumption-gated dispatch (human delivery override) as a standard menu option and standalone trigger: delivery-intent turn duty (MUST NOT start a new cycle), the six-item non-waivable safety floor, waived-blocker-to-assumption-plus-followup-test conversion, one-confirmation-turn flow with provenance per assurance-model.md, waived-stays-waived per objective, the [OVERRIDE: ...] marker, and preserved self-clearance prohibition; policy/recovery.md's cap-recovery menu carries the option; policy/acceptance-contract.md documents the followup-test conversion and the schema-1.4 overrides ledger fields."},
    {"id": "R3", "text": "Both adapter SKILL.md files (claude-code and codex) surface the override inline: the four-option escalation menu, the delivery-intent trigger duty, the safety floor, and schema 1.4 in the schema paragraph; the two files' override guidance stays keyed by identical load-bearing phrases, and both files still validate as single-block inputs to tools/validate-plan."},
    {"id": "R4", "text": "All existing deterministic suites remain green after every change: tools/tests/validate-plan.sh, tools/tests/check-links.sh, and tools/tests/release-v9.1.sh (still pinned to the v9.1.1 release identity)."}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Schema 1.4 overrides ledger in validate-plan + fixtures + harness",
      "deps": ["T2"],
      "contract": {
        "requirement_ids": ["R1", "R4"],
        "criteria": "validate-plan accepts version 1.4 (additive: every 1.1-1.3 rule enforced identically); optional plan-level 'overrides' JSON array; each entry an object with exactly {blocker, assumption, followup_test, authorized_turn}, all non-empty strings — wrong-type value, missing field, extra field, empty string, and non-array 'overrides' all rejected with keyword 'override'; 1.1/1.2/1.3 blocks carrying 'overrides' rejected with keyword 'version' naming schema 1.4; docstring updated; new fixtures: plan-good-14-overrides.md (valid 1.4, populated ledger), plan-good-14-no-overrides.md (valid 1.4 without the field), plan-bad-14-override-shape.md (four defective entries: missing followup_test, empty blocker, extra field, non-string value), plan-bad-14-override-nonarray.md (overrides as a string), plan-bad-13-carrying-14-field.md; validate-plan.sh gains expect_pass/expect_fail lines for all five with needles 'override' and 'version' respectively, plus an expect_policy_text check that plan-critique.md names schema 1.4. Runs AFTER T2 (T2 owns the policy text and the two pre-existing pinned harness needles this schema bump moves).",
        "acceptance_command": "bash -c 'cd /Users/briantaylor/Projects/AgentFW && python3 tools/validate-plan tools/fixtures/plan-good-14-overrides.md && python3 tools/validate-plan tools/fixtures/plan-good-14-no-overrides.md && grep -q \"plan-bad-14-override-shape.md. override\" tools/tests/validate-plan.sh && grep -q \"plan-bad-14-override-nonarray.md. override\" tools/tests/validate-plan.sh && grep -q \"plan-bad-13-carrying-14-field.md. version\" tools/tests/validate-plan.sh && bash tools/tests/validate-plan.sh && echo T1_OK'",
        "expected_signal": "terminal line exactly T1_OK with exit 0",
        "environment": "repo checkout at /Users/briantaylor/Projects/AgentFW on main, python3 in PATH, no network",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [
          {"mutation": "on a scratch copy of the repo, delete the branch in tools/validate-plan that rejects a 1.3 block carrying 'overrides', so plan-bad-13-carrying-14-field.md validates", "expected": "red"},
          {"mutation": "on a scratch copy, replace tools/validate-plan's main with an unconditional print('PASS'); sys.exit(0) stub", "expected": "red"},
          {"mutation": "on a scratch copy, remove the per-entry field checks so an overrides entry missing followup_test passes", "expected": "red"}
        ],
        "risk": "additive schema change silently altering 1.1-1.3 behavior, or the new checks being unreachable so malformed ledgers validate",
        "negative_cases": ["plan-bad-14-override-shape.md rejected with keyword 'override'", "plan-bad-13-carrying-14-field.md rejected with keyword 'version'", "all pre-existing plan-bad-* fixtures still rejected (harness re-runs them)"],
        "rerunnable": true
      }
    },
    {
      "id": "T2",
      "title": "Policy bundle: override semantics in plan-critique, recovery, acceptance-contract",
      "deps": [],
      "contract": {
        "requirement_ids": ["R2", "R4"],
        "criteria": "plan-critique.md: escalation menu gains option 4 'assumption-gated dispatch (human delivery override)' available at any point after Layer-2 findings exist (not only at cap); new subsection carrying all seven design invariants from this plan's 'Design invariants' section verbatim in substance (trigger duty with the literal phrase 'MUST NOT start a new plan', the six-item safety floor with each item's distinctive phrase intact — 'externally-consequential action', 'security boundary defect', 'irreversible architectural commitment', 'goal/proof contradiction', 'unavailable required substrate', 'demonstrated-vacuous acceptance command' — conversion rule, one-confirmation-turn + provenance, 'Waived stays waived', the '[OVERRIDE:' marker format, self-clearance preserved); Layer-1 rule list documents schema 1.4 and the 'override' defect keyword; the keyword contract adds 'override'; rule 1's version text becomes exactly: mode — `\"1.1\"`, `\"1.2\"`, `\"1.3\"`, or `\"1.4\"` and the schema-of-record line becomes exactly: **schema 1.4 is the schema of record**. T2 ALSO updates the two pinned needles in tools/tests/validate-plan.sh expect_policy_text lines to those exact new strings (it owns the text they pin — text and mirror move in one task). recovery.md section 7: menu gains the same option 4 with a cross-reference to plan-critique.md. acceptance-contract.md: documents the waived-blocker-to-followup-test conversion and the overrides ledger field shapes. check-links.sh AND validate-plan.sh both still pass at this task's completion (before T1's fixture additions).",
        "acceptance_command": "bash -c 'cd /Users/briantaylor/Projects/AgentFW && grep -q \"assumption-gated dispatch (human delivery override)\" policy/plan-critique.md && grep -q \"MUST NOT start a new plan\" policy/plan-critique.md && grep -q \"Waived stays waived\" policy/plan-critique.md && grep -qF \"[OVERRIDE:\" policy/plan-critique.md && grep -q \"demonstrated-vacuous acceptance command\" policy/plan-critique.md && grep -q \"security boundary defect\" policy/plan-critique.md && grep -q \"irreversible architectural commitment\" policy/plan-critique.md && grep -q \"unavailable required substrate\" policy/plan-critique.md && grep -q \"externally-consequential action\" policy/plan-critique.md && grep -q \"goal/proof contradiction\" policy/plan-critique.md && grep -q \"never clears its own blockers\" policy/plan-critique.md && grep -q \"assumption-gated dispatch (human delivery override)\" policy/recovery.md && grep -q \"followup_test\" policy/acceptance-contract.md && grep -q \"authorized_turn\" policy/acceptance-contract.md && bash tools/tests/check-links.sh && bash tools/tests/validate-plan.sh && echo T2_OK'",
        "expected_signal": "terminal line exactly T2_OK with exit 0",
        "environment": "repo checkout at /Users/briantaylor/Projects/AgentFW on main, no network",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [
          {"mutation": "on a scratch copy, delete the six-item safety-floor list from plan-critique.md's override subsection", "expected": "red"},
          {"mutation": "on a scratch copy, delete the 'Waived stays waived' rule from plan-critique.md", "expected": "red"},
          {"mutation": "on a scratch copy, remove the override option from recovery.md's menu", "expected": "red"}
        ],
        "risk": "the override text weakening the safety floor or the self-clearance prohibition, or policy files drifting from the resolved R92 design",
        "negative_cases": ["running the acceptance command against the pre-change files exits non-zero (recorded as the producer red-path)", "grep for the option in recovery.md fails if only plan-critique.md was edited"],
        "rerunnable": true
      }
    },
    {
      "id": "T3",
      "title": "Adapter skill sync: surface the override inline in both SKILL.md files",
      "deps": ["T2"],
      "contract": {
        "requirement_ids": ["R3", "R4"],
        "criteria": "Both adapters/claude-code/skills/agentfw/SKILL.md and adapters/codex/skills/agentfw/SKILL.md: the Layer-2/escalation guidance surfaces the four-option menu inline (extend one pass / mutation-gated dispatch / assumption-gated dispatch via human delivery override / halt) with the trigger duty and the six-item safety floor stated compactly; the schema paragraph names schema 1.4's optional overrides ledger; both files keyed by the identical load-bearing phrases 'assumption-gated dispatch (human delivery override)', 'Waived stays waived', and 'schema 1.4'; both files still validate as single-block validate-plan inputs; the full release gate stays green.",
        "acceptance_command": "bash -c 'cd /Users/briantaylor/Projects/AgentFW && grep -q \"assumption-gated dispatch (human delivery override)\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"assumption-gated dispatch (human delivery override)\" adapters/codex/skills/agentfw/SKILL.md && grep -q \"Waived stays waived\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"Waived stays waived\" adapters/codex/skills/agentfw/SKILL.md && grep -q \"MUST NOT start a new plan\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"MUST NOT start a new plan\" adapters/codex/skills/agentfw/SKILL.md && grep -q \"schema 1.4\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"schema 1.4\" adapters/codex/skills/agentfw/SKILL.md && grep -q \"demonstrated-vacuous acceptance command\" adapters/claude-code/skills/agentfw/SKILL.md && grep -q \"demonstrated-vacuous acceptance command\" adapters/codex/skills/agentfw/SKILL.md && python3 tools/validate-plan adapters/claude-code/skills/agentfw/SKILL.md && python3 tools/validate-plan adapters/codex/skills/agentfw/SKILL.md && bash tools/tests/release-v9.1.sh && echo T3_OK'",
        "expected_signal": "terminal line exactly T3_OK with exit 0",
        "environment": "repo checkout at /Users/briantaylor/Projects/AgentFW on main, python3 in PATH, no network",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [
          {"mutation": "on a scratch copy, remove the override menu block from the codex SKILL.md only, leaving claude-code edited", "expected": "red"},
          {"mutation": "on a scratch copy, corrupt the claude-code SKILL.md example plan block's JSON (drop a closing brace)", "expected": "red"}
        ],
        "risk": "adapter skills drifting from each other or from policy (the exact stale-skill failure mode the field report documented), or SKILL.md edits breaking the embedded example block the release gate validates",
        "negative_cases": ["running the acceptance command against the pre-change files exits non-zero (producer red-path)", "editing only one adapter fails the paired grep"],
        "rerunnable": true
      }
    }
  ]
}
```

## Producer red-path evidence (recorded before Layer 2)

Executed 2026-07-20 against the pre-change tree (T2/T3) and a broken scratch copy (T1),
before Layer-2 dispatch:

- **T2 red:** full acceptance chain vs pre-change `policy/` → exit 1 at the first grep
  (`assumption-gated dispatch (human delivery override)` absent from plan-critique.md).
- **T3 red:** first grep clause vs pre-change claude-code SKILL.md → exit 1 (phrase absent).
- **T1 red:** scratch copy = repo @ HEAD + new `plan-good-14-overrides.md` fixture + harness
  `expect_pass` line, validator UNMODIFIED → harness FAIL:
  `plan: unknown schema version '1.4' — known versions are "1" (legacy, --legacy only), "1.1",
  "1.2", and "1.3"` — proving the harness executes the new entry and the unmodified validator
  gates it red.

## Bespoke named relaxation (recorded, human-authorized)

Cap reached at pass 2 with ONE open C2 blocker (T1 acceptance vacuous under a null
implementation — demonstrated). Standard menu option 1 ineligible (single C2 blocker); option 2
ineligible (no 1:1 contracted probe covers the null-impl bypass). Human authorization (Brian,
genuine turn, this session, selecting "Probe-verified revision"):
- **Invariant waived:** fresh full Layer-2 pass over the post-cap revision.
- **Exact scope:** T1 acceptance_command strengthening + pass-2 concerns 2–5 needle/probe-path
  additions. No task added or removed; no criteria weakened.
- **Compensating mechanical control:** re-execute the pass-2 critic's demonstrated
  null-implementation probe verbatim against the REVISED T1 command — it must exit non-zero; plus
  Layer-1 re-validation. Recorded below.
- **Termination:** one probe execution; on red, worker dispatch begins; on green (bypass still
  open), HALT and re-escalate.

Mutation-probe path rule (pass-2 concern 5): every mutation probe executes the task's
acceptance_command with `cd /Users/briantaylor/Projects/AgentFW` substituted to the scratch-copy
root; probes never run against the live tree.

**Relaxation compensation evidence (recorded 2026-07-20, pre-dispatch):** pass-2 critic's null
implementation rebuilt verbatim on a fresh scratch copy (placeholder good fixtures, bad fixtures
as copies of `plan-bad-empty.md`, needle strings as comments in harness and validator, validator
unmodified). Revised T1 command against it: `FAIL: … expected exactly one json agentfw-plan
fenced block, found 0`, exit 1, no terminal `T1_OK`. Layer 1 re-run on the revised plan: PASS,
review tier single. Dispatch authorized per the relaxation's termination clause.

**Rev 2 (post pass-1 blockers):** T1 acceptance gained lever-existence gates (fixture files +
harness needle + validator "1.4" needle) — pass-1 demonstrated the bare harness run passed on an
unchanged tree; T1 now deps ["T2"]; T2 owns the two pinned harness `expect_policy_text` needles
its schema-of-record edit moves (exact replacement strings in criteria) and runs the full
validate-plan.sh at its own completion; T2/T3 gained per-floor-item and trigger-duty needles.
Revised commands re-probed red against the pre-change tree 2026-07-20: T1 exit 1 (first clause,
fixture absent), T2 exit 1 (first grep), T3 exit 1 (first grep).
