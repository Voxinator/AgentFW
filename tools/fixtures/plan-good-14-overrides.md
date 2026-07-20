# Fixture: valid 1.4 plan with a populated overrides ledger (expected: PASS)

Schema 1.4 is additive over 1.3. This A2 integration-seam contract satisfies
every 1.1-1.3 rule, and the plan-level overrides ledger records two
assumption-gated dispatches, each carrying all four required fields.

```json agentfw-plan
{
  "version": "1.4",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "overrides": [
    {"blocker": "C2: the acceptance command cannot distinguish a hollow parser",
     "assumption": "the fixture corpus exercises the hollow-parser path",
     "followup_test": "add a hollow-parser red-path probe to the harness",
     "authorized_turn": "human turn 2026-07-18T14:02 'ship it under that assumption'"},
    {"blocker": "C4: staging lacks the production TLS trust proxy",
     "assumption": "trust-proxy headers behave as in the recorded capture",
     "followup_test": "replay the recorded capture against staging before release",
     "authorized_turn": "human turn 2026-07-18T14:05 'accepted, log it'"}
  ],
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid configuration loads and malformed configuration exits non-zero",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo PLAN14_OK'",
      "expected_signal": "terminal line exactly PLAN14_OK with exit 0",
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
