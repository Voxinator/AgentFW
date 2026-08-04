# Fixture: 1.7 red_witness command_sha256 does not match the contract's acceptance_command (expected: FAIL, witness digest mismatch)

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
      "enforced_in": ["tools/fixtures/digest_thing.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Digest drift",
      "deps": [],
      "touches": ["tools/fixtures/digest_thing.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_digest.py && echo PLAN17_DG_OK'",
        "expected_signal": "terminal line exactly PLAN17_DG_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and red-witness transcript, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/dg-red.txt"
        }
      }
    }
  ]
}
```
