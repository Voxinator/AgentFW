# Fixture: 1.7 A2+ contract with NO red_witness (expected: FAIL, missing red witness)

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
      "enforced_in": ["tools/fixtures/mrw_thing.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Thing",
      "deps": [],
      "touches": ["tools/fixtures/mrw_thing.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_mrw.py && echo PLAN17_MRW_OK'",
        "expected_signal": "terminal line exactly PLAN17_MRW_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output, produced_after_change",
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
