# Fixture: 1.7 must requirement with absent/empty enforced_in (expected: FAIL, locality)

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
      "enforced_in": []
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Thing",
      "deps": [],
      "touches": ["tools/some_file.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_missing_ei.py && echo PLAN17_MEI_OK'",
        "expected_signal": "terminal line exactly PLAN17_MEI_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "5f6fba4044e18317017e6e6661c3ff3e2f24b3afc6c79ba1ce0e276f3ed4b10c",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/mei-red.txt"
        }
      }
    }
  ]
}
```
