# Fixture: 1.5 block carrying the schema-1.6 witness_pair field (expected: FAIL, version)

```json agentfw-plan
{
  "version": "1.5",
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
      "title": "Old schema with new field",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_old.py && echo PLAN15_W_OK'",
        "expected_signal": "terminal line exactly PLAN15_W_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "witness_pair": {
          "red": {
            "tree": "bare scratch: deliverable stubbed to nothing",
            "command_sha256": "c6251a0167b50945919c11fc21698499e02e73a5ec775c8bdad79f31c98a408f",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/red.txt"
          },
          "green": {
            "tree": "witness-tree: minimal stub satisfying the contract",
            "command_sha256": "c6251a0167b50945919c11fc21698499e02e73a5ec775c8bdad79f31c98a408f",
            "exit_code": 0,
            "evidence_path": ".agentfw/evidence/fixture/witness/green.txt"
          }
        }
      }
    }
  ]
}
```
