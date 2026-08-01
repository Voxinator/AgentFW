# Fixture: 1.5 must-requirement without a `because` (expected: FAIL, keyword necessity)

R1 claims necessity "must" but names no failure that occurs without it — an
unjustified must-claim is exactly the inflation the tier exists to catch.

```json agentfw-plan
{
  "version": "1.5",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected",
     "necessity": "must"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid configuration loads and malformed configuration exits non-zero",
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
