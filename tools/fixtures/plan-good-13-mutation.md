# Fixture: valid 1.3 integration-seam plan (expected: PASS)

Schema 1.3 is additive over 1.2. This A2 integration-seam contract carries a
valid mutation probe, and its acceptance command gates the terminal signal
behind the producer check with no earlier pipe.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid configuration loads and malformed configuration exits non-zero",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo PLAN13_OK'",
      "expected_signal": "terminal line exactly PLAN13_OK with exit 0",
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
