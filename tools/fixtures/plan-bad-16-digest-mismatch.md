# Fixture: 1.6 witness green leg digested over only the LAST leg of the command (expected: FAIL, witness digest mismatch)

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
      "title": "Leg-skipping forgery",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/leg1.py && python3 tests/leg2.py && echo PLAN16_DM_OK'",
        "expected_signal": "terminal line exactly PLAN16_DM_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "witness_pair": {
          "red": {
            "tree": "bare scratch",
            "command_sha256": "6b99a119af24fe7123897fae263efba4225de2ef34a134a44e4a8ebc108ffb11",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/dm-red.txt"
          },
          "green": {
            "tree": "witness-tree",
            "command_sha256": "d23df3adfb300b649df29e9dd12af33652e7a7df59593075379422bb71090d66",
            "exit_code": 0,
            "evidence_path": ".agentfw/evidence/fixture/witness/dm-green.txt"
          }
        }
      }
    }
  ]
}
```
