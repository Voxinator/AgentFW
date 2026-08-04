# Fixture: 1.7 nice-to-have requirement with unenforced enforced_in paths (expected: PASS —
# deferred/unenforced scope on a non-must requirement is not a locality defect)

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
    },
    {
      "id": "R2",
      "text": "A nicety that has not been built yet",
      "necessity": "nice-to-have",
      "enforced_in": ["tools/some/unenforced/path.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Thing",
      "deps": [],
      "touches": ["tools/enforced_target.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_nth.py && echo PLAN17_NTH_OK'",
        "expected_signal": "terminal line exactly PLAN17_NTH_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "d71847121a2b7c55ae301cc3f1b7be4fd1d9fdef5f45f00767b91f42d4f4def4",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/nth-red.txt"
        }
      }
    }
  ]
}
```
