# Fixture: round-3 regression — a command whose legs cannot both hold; the honest green witness records exit 1, so the impossible command is REJECTED AT PLAN TIME

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
      "title": "Round-3-style contradictory gate",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'test -s out/receipt-changes.txt && test ! -s out/receipt-changes.txt && echo ROUND3_OK'",
        "expected_signal": "terminal line exactly ROUND3_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "witness_pair": {
          "red": {
            "tree": "bare scratch: out/ absent",
            "command_sha256": "40a489d81f146fbd02ec5cb347478500c34b903dd968655c2c4eaa6ea850130b",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/round3-red.txt"
          },
          "green": {
            "tree": "witness-tree: best honest attempt \u2014 no tree can satisfy both legs",
            "command_sha256": "40a489d81f146fbd02ec5cb347478500c34b903dd968655c2c4eaa6ea850130b",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/round3-green.txt"
          }
        }
      }
    }
  ]
}
```
