# Fixture: valid 1.6 plan with witness pairs (expected: PASS + witness pair note)

```json agentfw-plan
{
  "version": "1.6",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {
      "id": "R1",
      "text": "Malformed configuration is rejected",
      "necessity": "must",
      "because": "without rejection, a bad config silently corrupts every downstream run"
    },
    {
      "id": "R2",
      "text": "Config errors name the offending key",
      "necessity": "must",
      "because": "without the key name, an operator cannot fix the config they are told is broken"
    },
    {
      "id": "R3",
      "text": "Config file supports comments",
      "necessity": "nice-to-have"
    },
    {
      "id": "R4",
      "text": "Config hot-reloads without restart",
      "necessity": "nice-to-have"
    },
    {
      "id": "R5",
      "text": "Config parser emits telemetry on parse timing",
      "necessity": "fluff"
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Configuration validation",
      "deps": [],
      "contract": {
        "requirement_ids": [
          "R1",
          "R2"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_config.py && echo PLAN16_OK'",
        "expected_signal": "terminal line exactly PLAN16_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
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
        "witness_pair": {
          "red": {
            "tree": "bare scratch: deliverable stubbed to nothing",
            "command_sha256": "9d8a951712de82b09aa95c94fc2462e04558fe9d52886a1fc8ef61cf87dfa810",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/red.txt"
          },
          "green": {
            "tree": "witness-tree: minimal stub satisfying the contract",
            "command_sha256": "9d8a951712de82b09aa95c94fc2462e04558fe9d52886a1fc8ef61cf87dfa810",
            "exit_code": 0,
            "evidence_path": ".agentfw/evidence/fixture/witness/green.txt"
          }
        },
        "risk": "a hollow validator could accept malformed configuration",
        "negative_cases": [
          "an unknown configuration key exits non-zero"
        ]
      }
    },
    {
      "id": "T2",
      "title": "Comment support (human-pulled nice-to-have)",
      "deps": [
        "T1"
      ],
      "contract": {
        "requirement_ids": [
          "R3"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_comments.py && echo PLAN16_C_OK'",
        "expected_signal": "terminal line exactly PLAN16_C_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "none",
        "failure_surfaces": [],
        "rerunnable": true,
        "witness_pair": {
          "red": {
            "tree": "bare scratch: deliverable stubbed to nothing",
            "command_sha256": "36572a84ed9d429b4adee3f6542e5c2fc8c9b1c808856ac86909e41e5d144237",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/red.txt"
          },
          "green": {
            "tree": "witness-tree: minimal stub satisfying the contract",
            "command_sha256": "36572a84ed9d429b4adee3f6542e5c2fc8c9b1c808856ac86909e41e5d144237",
            "exit_code": 0,
            "evidence_path": ".agentfw/evidence/fixture/witness/green.txt"
          }
        }
      }
    }
  ]
}
```
