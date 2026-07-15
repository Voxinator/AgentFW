# Fixture: 1.3 integration seam without mutation probes (expected: FAIL)

The contract is otherwise valid, but schema 1.3 requires at least one
mutation probe at every integration seam.

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
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo SEAM_OK'",
      "expected_signal": "terminal line exactly SEAM_OK with exit 0",
      "environment": "repo checkout, Python 3, no network",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "rerunnable": true}}
  ]
}
```
