# Fixture: 1.6 witness_pair shape defects — wrong pair key and string exit_code (expected: FAIL, invalid witness pair/record)

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
    },
    {
      "id": "R2",
      "text": "Second deliverable is verified",
      "necessity": "must",
      "because": "without it the second surface ships unchecked"
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Wrong pair keys",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/a.py && echo PLAN16_S1_OK'",
        "expected_signal": "terminal line exactly PLAN16_S1_OK with exit 0",
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
            "command_sha256": "c1f3246d8504580ab1ae685ff69fcc686d35750c23dd37bcc280506c1a8bbc16",
            "exit_code": 1,
            "evidence_path": "e/red.txt"
          },
          "verde": {
            "tree": "witness-tree",
            "command_sha256": "c1f3246d8504580ab1ae685ff69fcc686d35750c23dd37bcc280506c1a8bbc16",
            "exit_code": 0,
            "evidence_path": "e/green.txt"
          }
        }
      }
    },
    {
      "id": "T2",
      "title": "Wrong leg shape",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R2"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/b.py && echo PLAN16_S2_OK'",
        "expected_signal": "terminal line exactly PLAN16_S2_OK with exit 0",
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
            "command_sha256": "7342f9d8488d3284bf3098727a172080a891685ca179a20572f402a0493cd6ec",
            "exit_code": 1,
            "evidence_path": "e/red2.txt"
          },
          "green": {
            "tree": "witness-tree",
            "command_sha256": "7342f9d8488d3284bf3098727a172080a891685ca179a20572f402a0493cd6ec",
            "exit_code": "0",
            "evidence_path": "e/green2.txt"
          }
        }
      }
    }
  ]
}
```
