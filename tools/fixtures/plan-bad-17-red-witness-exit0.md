# Fixture: 1.7 red_witness declares exit_code 0 — an impossible red leg (expected: FAIL, witness exit code)

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
      "enforced_in": ["tools/fixtures/exit0_thing.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Impossible-to-fail red leg",
      "deps": [],
      "touches": ["tools/fixtures/exit0_thing.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_exit0.py && echo PLAN17_E0_OK'",
        "expected_signal": "terminal line exactly PLAN17_E0_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and red-witness transcript, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "1c7e4a1f1a8efb95543d8389c3467f8b76bd8efc8427b4923ed6c563e130b692",
          "exit_code": 0,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/e0-red.txt"
        }
      }
    }
  ]
}
```
