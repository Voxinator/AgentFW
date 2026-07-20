# Fixture: 1.3 plan carrying a schema-1.4 overrides ledger (expected: FAIL)

Schema 1.3 remains valid, but it must not fail open on the field introduced
by 1.4. A plan recording an overrides ledger declares version 1.4. The plan
is otherwise fully valid, so the version defect is the only rejection.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "overrides": [
    {"blocker": "C2: the acceptance command cannot distinguish a hollow parser",
     "assumption": "the fixture corpus exercises the hollow-parser path",
     "followup_test": "add a hollow-parser red-path probe to the harness",
     "authorized_turn": "human turn 2026-07-18T14:02 'ship it under that assumption'"}
  ],
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid configuration loads and malformed configuration exits non-zero",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo CARRY14_OK'",
      "expected_signal": "terminal line exactly CARRY14_OK with exit 0",
      "environment": "repo checkout, Python 3, no network",
      "evidence": "test output and red-path output, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "a hollow validator could accept malformed configuration",
      "negative_cases": ["an unknown configuration key exits non-zero"],
      "mutation_probes": [
        {"mutation": "on a scratch copy, replace validation with unconditional success", "expected": "red"}
      ],
      "rerunnable": true}}
  ]
}
```
