# Fixture: valid 1.4 plan without an overrides ledger (expected: PASS)

The schema-1.4 `overrides` field is OPTIONAL: a 1.4 block without it
validates identically to a 1.3 block.

```json agentfw-plan
{
  "version": "1.4",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid configuration loads and malformed configuration exits non-zero",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo PLAN14N_OK'",
      "expected_signal": "terminal line exactly PLAN14N_OK with exit 0",
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
