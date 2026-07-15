# Fixture: 1.3 A3 contract without mutation probes (expected: FAIL)

The task is not an integration seam, proving that assurance A3 independently
requires a non-empty mutation-probe roster in every contract.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A3",
  "required_plan_review_tier": "dual",
  "requirements": [{"id": "R1", "text": "The generated reference stays synchronized"}],
  "tasks": [
    {"id": "T1", "title": "Reference synchronization", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "the generated reference matches its source",
      "acceptance_command": "bash -c 'python3 tools/check_reference.py && echo A3_OK'",
      "expected_signal": "terminal line exactly A3_OK with exit 0",
      "environment": "repo checkout, Python 3, no network",
      "evidence": "checker output, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "negative_cases": ["removing a generated row makes the checker fail"],
      "rerunnable": true}}
  ]
}
```
