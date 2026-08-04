# Fixture: 1.7 task covering a must requirement with no touches field (expected: FAIL, locality)

```json agentfw-plan
{
  "version": "1.7",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {
      "id": "R1",
      "text": "The deliverable is verified by a runnable command",
      "necessity": "must",
      "because": "without a runnable check, a wrong implementation ships undetected",
      "enforced_in": ["tools/enforced_target.py"]
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
        "acceptance_command": "bash -c 'python3 tests/test_missing_touches.py && echo PLAN17_MT_OK'",
        "expected_signal": "terminal line exactly PLAN17_MT_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "991977e6371e09702b2c48749b43a13e06ba49fdc4e403b16ac07f44a2034a31",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/mt-red.txt"
        }
      }
    }
  ]
}
```
