# Fixture: 1.3 integration seam with an empty mutation roster (expected: FAIL)

An empty array has the right type but does not satisfy the at-least-one rule.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [{"id": "R1", "text": "Malformed configuration is rejected"}],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "malformed configuration exits non-zero",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo EMPTY_OK'",
      "expected_signal": "terminal line exactly EMPTY_OK with exit 0",
      "environment": "repo checkout, Python 3, no network",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "mutation_probes": [],
      "rerunnable": true}}
  ]
}
```
