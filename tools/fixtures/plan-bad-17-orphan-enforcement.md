# Fixture: 1.7 must requirement enforced_in path not in any covering task's touches (expected: FAIL, locality)

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
      "enforced_in": ["tools/orphan_target.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Thing",
      "deps": [],
      "touches": ["tools/unrelated_file.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_orphan.py && echo PLAN17_ORPHAN_OK'",
        "expected_signal": "terminal line exactly PLAN17_ORPHAN_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "bc2788019c6454c3a0a962a108cd5bb2d264c39830a875ba31666b6da644c947",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/orphan-red.txt"
        }
      }
    }
  ]
}
```
