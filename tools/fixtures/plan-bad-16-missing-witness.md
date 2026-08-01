# Fixture: 1.6 contract with NO witness_pair (expected: FAIL, missing witness pair)

```json agentfw-plan
{
  "version": "1.6",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {
      "id": "R1",
      "text": "The deliverable is verified by a runnable command",
      "necessity": "must",
      "because": "without a runnable check, a wrong implementation ships undetected"
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Thing",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_thing.py && echo PLAN16_MW_OK'",
        "expected_signal": "terminal line exactly PLAN16_MW_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true
      }
    }
  ]
}
```
