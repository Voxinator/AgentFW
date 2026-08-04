# Fixture: 1.7 enforced_in path is a strict substring of a touched path — the discriminating
# fixture: a substring-based matcher wrongly PASSes this; exact-element matching FAILs it
# (expected: FAIL, locality)

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
      "enforced_in": ["tools/validate-plan"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Thing",
      "deps": [],
      "touches": ["tools/validate-plan.sh"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_substring.py && echo PLAN17_SUB_OK'",
        "expected_signal": "terminal line exactly PLAN17_SUB_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "773af3a7502ec908eb9982677c6be67d4c1fe7560009eb35d1d807ec82a5ef84",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/sub-red.txt"
        }
      }
    }
  ]
}
```
