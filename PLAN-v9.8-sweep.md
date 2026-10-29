# PLAN — v9.8 audit sweep (objective `v98-sweep`)

**Assurance: A2.** Multi-file analysis across the installed AgentFW v9.7.0 policy set and
capability model, feeding a v9.8 planning cycle. Blast radius: new files only
(`findings/`, `FINDINGS-v9.8-sweep.md`, `evaluation/verify-v98-sweep.py`); no existing
policy, skill, or settings file is modified by any task. Reversible by deletion.
Defect-escape probability is the driver: analytical claims about a verification
framework's own seams cannot be judged by the context that formed them.

**`[FLOOR-RELAXED: operator — bypassPermissions]`** — floor recommended once this session
(auto mode), declined by the operator. Residuals: explicit ask rules, connector ask
settings, `requiresUserInteraction` MCP tools, root/home `rm` circuit breaker.
Destructive/irreversible/outward effects gate on a genuine human turn. Not re-raised.

## Declared degradations

1. **`model_selection.configured` is undeclarable on this install — but the capability
   itself works.** `tools/agentfw-install` never probes `model_selection` (zero
   occurrences); `active-capabilities.yaml` (generated 2026-08-04) therefore records no
   entry; and `agentfw-install` is not copied into the installed skill, so §0's mandated
   refresh is unreachable without the repo checkout. Per `capability.yaml`'s gating rule
   an unverified `available: true` counts as false, so the framework must treat adaptive
   dispatch as absent. **Empirically it is not:** this objective dispatched both Layer-2
   judges with an explicit `model: sonnet` and both ran at that tier. The defect is the
   missing probe and the consequent undeclarable state, not an absent parameter. This
   objective therefore uses adaptive dispatch with every tier cast explicitly, and
   declares that its `configured` state cannot be established by the shipped installer.
2. **R8 depends on one external fact** (current model pricing) that no installed judge
   can re-derive: `agentfw-verifier` and `agentfw-plan-critic` hold Read/Glob/Grep/Bash
   and no web access. R8 is therefore `nice-to-have`, demoted from R2 under the C6
   scope-correction rule after both Layer-2 passes found the must-claim unprovable. T2's
   gate requires the fact be recorded as an `external_facts` entry tagged
   `tier: human_review` with a named source — the gate enforces the tagging, a human
   reviewer owns the value.
3. **The acceptance instrument is planner-authored, and that is now mechanically
   bounded.** `evaluation/verify-v98-sweep.py` is the planner's measuring instrument.
   Its `--selftest` proves its own non-vacuity by re-running every skill-reading probe
   against a bare root and failing if any returns an unchanged value, so a constant
   masquerading as a measurement is caught by machine check rather than by narration.
   T0 is an independent worker task that writes an adversarial suite reproducing all
   eight holes the Layer-2 judges demonstrated; the judge of record re-executes both.
4. **T3's harness-primitive list is an external fact.** The five probed strings
   (`start_session`, `ccd_`, `update_plan`, `wrap_up`, `ToolSearch`) occur nowhere in
   the repo or install, so a zero hit count shows the policy does not mention them — it
   cannot show the platform offers them. T3's gate carries a positive control (a term
   that must appear, else the probe is declared broken rather than the policy clean) and
   requires an `excluded_false_positives` record. The claim that these are real platform
   primitives is `human_review` tier, like pricing. Declared after Layer-2 pass 1 raised
   it as an undeclared peer of degradation 2.

## Operator scope confirmation

The operator pulled the full five-thread scope into this increment in their own turn
("Full sweep"), which covers the Layer-1 scope notes on T4 and T5 and both judges' C6
finding that optional threads gate a must. Recorded here rather than assumed.

## Requirements

| id | necessity | text |
|---|---|---|
| R1 | must | Thread 1 — document the D-14 adaptive-dispatch declaration gap with mechanically re-derived evidence |
| R2 | must | Thread 2 — validate the declared tier ladder against the current model set and record the gap structure |
| R3 | must | Thread 3 — enumerate capability-model coverage gaps for desktop-harness primitives |
| R4 | nice-to-have | Thread 4 — measure the resident/invoked context cost of the skill + policy set |
| R5 | nice-to-have | Thread 5 — assess the operator posture against the relaxation rule as actually configured |
| R6 | must | every finding is mechanically re-derivable; no claim survives that the files do not support |
| R7 | must | one prioritized D-item document assembled from the verified findings |

## Tasks

- **T0** harden the acceptance instrument (independent adversarial review of the checker)
- **T1–T5** one worker per thread, each writing only its own findings file
- **T6** assemble the prioritized D-item document (integration seam)

```json agentfw-plan
{ "version": "1.7", "assurance": "A2", "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "necessity": "must",
     "text": "Document the D-14 adaptive-dispatch declaration gap with mechanically re-derived evidence: that model_selection is unprobed, that the install cannot refresh it, and what the policy's own gating rule then implies.",
     "because": "The shipped installer cannot establish model_selection.configured, so every install must treat adaptive dispatch as absent and fall back to Uniform without ever declaring it; the fallback is undeclared in the product, not merely in one run, and recurs on every install until the probe exists.",
     "enforced_in": ["findings/v98-thread1.json"]},
    {"id": "R2", "necessity": "must",
     "text": "Establish that the adapter declares a complete tier ladder with floor and flagship naming rungs that exist in it, and that the semantic policy text contains zero concrete model ids.",
     "because": "A floor or flagship naming a rung absent from the ladder makes the economic gate unevaluable, and a concrete model id in policy text breaks the model-agnostic core on the next model release.",
     "enforced_in": ["findings/v98-thread2.json"]},
    {"id": "R3", "necessity": "must",
     "text": "Enumerate which desktop-harness primitives the capability model does not cover, and which policy duties may double-book against a native substrate.",
     "because": "An unmodeled delegation primitive gets used with no assurance gating at all, and a duplicated ledger makes the framework's own counters disagree with the platform's.",
     "enforced_in": ["findings/v98-thread3.json"]},
    {"id": "R4", "necessity": "nice-to-have",
     "text": "Measure the byte and estimated-token cost of SKILL.md and each policy file, and identify which files load for which role.",
     "enforced_in": ["findings/v98-thread4.json"]},
    {"id": "R5", "necessity": "nice-to-have",
     "text": "Assess the operator-relaxation rule against the install as actually configured, including whether the probed deny-rule state matches the live settings.",
     "enforced_in": ["findings/v98-thread5.json"]},
    {"id": "R8", "necessity": "nice-to-have",
     "text": "Record the current model set's pricing and the cost gap structure between adjacent ladder rungs as an external, human_review-tier fact with a named source.",
     "enforced_in": ["findings/v98-thread2.json"]},
    {"id": "R6", "necessity": "must",
     "text": "Every finding is mechanically re-derivable from the live install: each claim names a probe, and the checker fails the claim when the probe disagrees.",
     "because": "An audit of a verification framework that itself rested on narration would reproduce the exact defect it is auditing.",
     "enforced_in": ["evaluation/test-v98-instrument.sh"]},
    {"id": "R7", "necessity": "must",
     "text": "One prioritized D-item document assembled from the verified thread findings, each item naming its evidence and its proposed mechanism.",
     "because": "Five JSON files are not a decision input; without one artifact the operator cannot act on the sweep.",
     "enforced_in": ["FINDINGS-v9.8-sweep.md"]}
  ],
  "tasks": [
    { "id": "T0", "title": "Author an adversarial suite against the acceptance instrument", "deps": [],
      "touches": ["evaluation/test-v98-instrument.sh"],
      "contract": { "requirement_ids": ["R6"],
        "criteria": "evaluation/test-v98-instrument.sh reproduces all eight holes the Layer-2 judges demonstrated against the previous instrument and asserts each is now red: H1 a single junk claim in every thread file; H2 the selftest passing on an instrument with a skill-reading probe stubbed to a constant; H3 a wrong skill root with falsy absence claims; H4 an int 0 claimed against a boolean probe; H5 a document containing only the token D-ITEM; H6 a bare 'Opus 4' style model id escaping the policy scan; H7 a probe reading the wrong corpus reporting a clean zero; H8 live mutable state differing between two reads. The suite exits non-zero if ANY hole is open, and prints one line per hole.",
        "acceptance_command": "bash -c 'bash evaluation/test-v98-instrument.sh && echo T0_OK'",
        "expected_signal": "terminal line exactly T0_OK with exit 0",
        "environment": "repo root /Users/briantaylor/Projects/AgentFW; python3; bash; live skill install at ~/.claude/skills/agentfw; the instrument honours V98_SKILL_ROOT for root perturbation",
        "evidence": "evidence/v98-T0-green.log, produced after the suite is written",
        "integration_seam": false, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [
          {"mutation": "on a scratch copy, revert the instrument's _root_guard call in run_thread and confirm the suite reports H3 open", "expected": "red"},
          {"mutation": "on a scratch copy, revert _strict_eq to plain != and confirm the suite reports H4 open", "expected": "red"},
          {"mutation": "on a scratch copy, remove the REQUIRED per-thread probe sets and confirm the suite reports H1 open", "expected": "red"}],
        "red_witness": {"tree": "no-suite-present",
          "command_sha256": "7e7bfe189b43649587d5e6cc2c8e0167eb21da574cdc041b8774433a350e558e",
          "exit_code": 127, "evidence_path": "evidence/v98-T0-red.log"},
        "risk": "A suite that only asserts the happy path would re-certify a vacuous instrument, which is exactly the defect both Layer-2 passes demonstrated.",
        "negative_cases": ["reverting any one hardening guard in the instrument makes the suite report that hole open", "a suite that exits 0 while a hole is open fails its own mutation probes"],
        "rerunnable": true }},

    { "id": "T1", "title": "Thread 1 — D-14 declaration gap", "deps": ["T0"],
      "touches": ["findings/v98-thread1.json"],
      "criteria_note": "adjudicate the two competing readings; do not pick by preference",
      "contract": { "requirement_ids": ["R1"],
        "criteria": "findings/v98-thread1.json records, each bound to a named probe: that tools/agentfw-install never probes model_selection; that capability.yaml leaves it configured: unknown; that active-capabilities.yaml contains no model_selection entry and is stale; that agentfw-install is absent from the installed skill; and the current agent model pins. It adjudicates between the 'prose-not-native-control' reading and the 'undeclared degradation' reading, stating which the evidence supports and why.",
        "acceptance_command": "bash -c 'python3 evaluation/verify-v98-sweep.py --thread 1 && echo T1_OK'",
        "expected_signal": "terminal line exactly T1_OK with exit 0",
        "environment": "repo root; python3; live skill install",
        "evidence": "evidence/v98-T1-green.log, produced after the findings file is written",
        "integration_seam": false, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, change one claim's expected value and assert the gate goes red", "expected": "red"}],
        "red_witness": {"tree": "bare-findings-dir",
          "command_sha256": "f500cacc578a4a976c0e3b5bb26d42a2a8197020a84a8422b9106c5c58cea801",
          "exit_code": 1, "evidence_path": "evidence/v98-T1-red.log"},
        "risk": "Misattributing a correct-but-silent degradation as a policy breach would send v9.8 at the wrong mechanism.",
        "negative_cases": ["a claim whose expected value disagrees with the probe fails the gate", "a claim naming an unregistered probe fails the gate"],
        "rerunnable": true }},

    { "id": "T2", "title": "Thread 2 — tier ladder vs current model set", "deps": ["T0"],
      "touches": ["findings/v98-thread2.json"],
      "contract": { "requirement_ids": ["R2", "R8"],
        "criteria": "findings/v98-thread2.json records the declared tiers, floor and flagship via probes, and that policy text contains zero concrete model ids. The pricing input is recorded as an explicitly human_review-tier external fact with its source named, never as a probed value, and the gap structure between adjacent rungs is stated.",
        "acceptance_command": "bash -c 'python3 evaluation/verify-v98-sweep.py --thread 2 && echo T2_OK'",
        "expected_signal": "terminal line exactly T2_OK with exit 0",
        "environment": "repo root; python3; live skill install",
        "evidence": "evidence/v98-T2-green.log, produced after the findings file is written",
        "integration_seam": false, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, assert a tiers list that differs from capability.yaml and confirm the gate goes red", "expected": "red"}],
        "red_witness": {"tree": "bare-findings-dir",
          "command_sha256": "db9c80b63110460d1c51ca1e9e25c5fa7c7b836a3cf49ce5ac13417be0d4d210",
          "exit_code": 1, "evidence_path": "evidence/v98-T2-red.log"},
        "risk": "An external fact presented as mechanically verified would be indistinguishable from a probed one on review.",
        "negative_cases": ["a wrong tiers list fails the gate", "a wrong floor or flagship value fails the gate"],
        "rerunnable": true }},

    { "id": "T3", "title": "Thread 3 — capability-model harness blind spots", "deps": ["T0"],
      "touches": ["findings/v98-thread3.json"],
      "contract": { "requirement_ids": ["R3"],
        "criteria": "findings/v98-thread3.json records the probed hit counts for harness primitives and the full capability key list, and identifies which policy duties (notably the v9.6 ledger) may duplicate a native substrate. Each generic-word false positive (for example 'artifact' or 'defer' used in ordinary prose) is excluded explicitly rather than counted.",
        "acceptance_command": "bash -c 'python3 evaluation/verify-v98-sweep.py --thread 3 && echo T3_OK'",
        "expected_signal": "terminal line exactly T3_OK with exit 0",
        "environment": "repo root; python3; live skill install",
        "evidence": "evidence/v98-T3-green.log, produced after the findings file is written",
        "integration_seam": false, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, assert a nonzero hit count for start_session and confirm the gate goes red", "expected": "red"}],
        "red_witness": {"tree": "bare-findings-dir",
          "command_sha256": "034ee65a2100660f6900b7ee7975133d44c43e4d7de4f23e8401be127e7e9785",
          "exit_code": 1, "evidence_path": "evidence/v98-T3-red.log"},
        "risk": "A false 'already covered' reading would leave an ungated delegation primitive in place.",
        "negative_cases": ["an inflated hit count fails the gate", "a capability key list that omits a real key fails the gate"],
        "rerunnable": true }},

    { "id": "T4", "title": "Thread 4 — context economics", "deps": ["T0"],
      "touches": ["findings/v98-thread4.json"],
      "contract": { "requirement_ids": ["R4"],
        "criteria": "findings/v98-thread4.json records probed byte sizes for SKILL.md, the policy total and each policy file, and states which files load for which role, distinguishing always-resident listing cost from on-invocation cost.",
        "acceptance_command": "bash -c 'python3 evaluation/verify-v98-sweep.py --thread 4 && echo T4_OK'",
        "expected_signal": "terminal line exactly T4_OK with exit 0",
        "environment": "repo root; python3; live skill install",
        "evidence": "evidence/v98-T4-green.log, produced after the findings file is written",
        "integration_seam": false, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, assert a byte size that differs from the real file and confirm the gate goes red", "expected": "red"}],
        "red_witness": {"tree": "bare-findings-dir",
          "command_sha256": "dd0f49b3255572aeb0e37dc87b599c5f380682f45a2ea59943717a2a7fd5db18",
          "exit_code": 1, "evidence_path": "evidence/v98-T4-red.log"},
        "risk": "An inflated context figure would justify a split that costs routing quality for no real saving.",
        "negative_cases": ["a wrong byte size fails the gate", "a policy file map missing a real file fails the gate"],
        "rerunnable": true }},

    { "id": "T5", "title": "Thread 5 — operator posture", "deps": ["T0"],
      "touches": ["findings/v98-thread5.json"],
      "contract": { "requirement_ids": ["R5"],
        "criteria": "findings/v98-thread5.json records the live defaultMode and deny-rule count via probes alongside the stale probed value in active-capabilities.yaml, and states whether the relaxation rule as written matches an install where relaxation is the steady state rather than the exception.",
        "acceptance_command": "bash -c 'python3 evaluation/verify-v98-sweep.py --thread 5 && echo T5_OK'",
        "expected_signal": "terminal line exactly T5_OK with exit 0",
        "environment": "repo root; python3; live skill install",
        "evidence": "evidence/v98-T5-green.log, produced after the findings file is written",
        "integration_seam": false, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [{"mutation": "on a scratch copy, assert a defaultMode that differs from live settings and confirm the gate goes red", "expected": "red"}],
        "red_witness": {"tree": "bare-findings-dir",
          "command_sha256": "6ebf8933ed05f49a2250256f2d1be886f2e2c18c20c0aefc36b02ed0a68f942e",
          "exit_code": 1, "evidence_path": "evidence/v98-T5-red.log"},
        "risk": "Reporting a configured enforcement floor that is not actually active would overstate the install's guarantees.",
        "negative_cases": ["a wrong defaultMode fails the gate", "a wrong deny-rule count fails the gate"],
        "rerunnable": true }},

    { "id": "T6", "title": "Assemble the prioritized D-item document",
      "deps": ["T1", "T2", "T3", "T4", "T5"],
      "touches": ["FINDINGS-v9.8-sweep.md"],
      "contract": { "requirement_ids": ["R7"],
        "criteria": "FINDINGS-v9.8-sweep.md exists, is non-empty, contains at least one line matching D-ITEM, and every D-item names the thread and probe evidence behind it plus a proposed mechanism. All five thread gates and the instrument selftest pass at assembly time, so the document cannot be assembled over unsupported claims.",
        "acceptance_command": "bash -c 'python3 evaluation/verify-v98-sweep.py --selftest && for n in 1 2 3 4 5; do python3 evaluation/verify-v98-sweep.py --thread $n || exit 1; done && python3 evaluation/verify-v98-sweep.py --document && echo T6_OK'",
        "expected_signal": "terminal line exactly T6_OK with exit 0",
        "environment": "repo root; python3; live skill install; all five findings files present",
        "evidence": "evidence/v98-T6-green.log, produced after the document is written",
        "integration_seam": true, "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "mutation_probes": [
          {"mutation": "on a scratch copy, delete one thread findings file and confirm the seam command goes red", "expected": "red"},
          {"mutation": "on a scratch copy, corrupt one claim's expected value and confirm the seam command goes red", "expected": "red"},
          {"mutation": "on a scratch copy, empty FINDINGS-v9.8-sweep.md and confirm the seam command goes red", "expected": "red"}],
        "red_witness": {"tree": "bare-findings-dir-no-document",
          "command_sha256": "6e9fbcc9d12a848ece4b342fb4836c8486ba1db58d9dc1a0f0f1478a67c2044d",
          "exit_code": 1, "evidence_path": "evidence/v98-T6-red.log"},
        "risk": "The seam is where an unsupported claim would enter the operator-facing artifact.",
        "negative_cases": ["a missing thread file fails the seam", "a corrupted claim fails the seam", "an empty document fails the seam", "a document with no D-ITEM line fails the seam"],
        "rerunnable": true }}
  ]}
```

## Dispatch register

Uniform posture (degradation 1): every worker is cast explicitly rather than inherited.
Judges held at `floor` per §8; producers right-sized below it.
