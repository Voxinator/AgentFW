# Fixture: valid 1.7 plan with a red witness (expected: PASS + red witness note)

```json agentfw-plan
{
  "version": "1.7",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {
      "id": "R1",
      "text": "Malformed configuration is rejected",
      "necessity": "must",
      "because": "without rejection, a bad config silently corrupts every downstream run",
      "enforced_in": ["tools/config_validator.py"]
    },
    {
      "id": "R2",
      "text": "Config errors name the offending key",
      "necessity": "must",
      "because": "without the key name, an operator cannot fix the config they are told is broken",
      "enforced_in": ["tools/config_validator.py", "tools/config_errors.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Configuration validation",
      "deps": [],
      "touches": ["tools/config_validator.py", "tools/config_errors.py"],
      "contract": {
        "requirement_ids": [
          "R1",
          "R2"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_thing.py && echo PLAN17_OK'",
        "expected_signal": "terminal line exactly PLAN17_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and red-witness transcript, produced_after_change",
        "required_verification_tier": "independent",
        "integration_seam": true,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "mutation_probes": [
          {
            "mutation": "on a scratch copy, replace the implementation with an unconditional-success stub",
            "expected": "red"
          }
        ],
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "60d2f922dc0d8f366cfe813c2360b406583a1decc851885705e1a0f0749a8e3f",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/red.txt"
        },
        "risk": "a hollow validator could accept malformed configuration",
        "negative_cases": [
          "an unknown configuration key exits non-zero"
        ]
      }
    }
  ]
}
```
