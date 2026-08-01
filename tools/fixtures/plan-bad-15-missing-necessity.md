# Fixture: 1.5 plan with an unlabeled requirement (expected: FAIL, keyword necessity)

R2 carries no `necessity` field — unlabeled scope cannot be audited for
inflation.

```json agentfw-plan
{
  "version": "1.5",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected",
     "necessity": "must",
     "because": "without rejection, a bad config silently corrupts every downstream run"},
    {"id": "R2", "text": "Config errors name the offending key"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1", "R2"],
      "criteria": "valid configuration loads; malformed configuration exits non-zero naming the key",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo PLAN15_OK'",
      "expected_signal": "terminal line exactly PLAN15_OK with exit 0",
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
