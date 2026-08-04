# Fixture: 1.7 contract carrying the demoted witness_pair field (expected: FAIL, witness demotion)

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
      "enforced_in": ["tools/fixtures/wp_thing.py"]
    }
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Still carrying the old green leg",
      "deps": [],
      "touches": ["tools/fixtures/wp_thing.py"],
      "contract": {
        "requirement_ids": [
          "R1"
        ],
        "criteria": "the deliverable behaves as required and a wrong implementation exits non-zero",
        "acceptance_command": "bash -c 'python3 tests/test_wp.py && echo PLAN17_WP_OK'",
        "expected_signal": "terminal line exactly PLAN17_WP_OK with exit 0",
        "environment": "repo checkout, Python 3, no network",
        "evidence": "test output and witness transcripts, produced_after_change",
        "required_verification_tier": "producer",
        "integration_seam": false,
        "risk_class": "standard",
        "failure_surfaces": [],
        "rerunnable": true,
        "red_witness": {
          "tree": "bare scratch: deliverable stubbed to nothing",
          "command_sha256": "b3385874dd8d1fbda57dc97c38cf6e59b931484ed08e38af5b63b72c82a782f2",
          "exit_code": 1,
          "evidence_path": ".agentfw/evidence/fixture/red-witness/wp-red.txt"
        },
        "witness_pair": {
          "red": {
            "tree": "bare scratch: deliverable stubbed to nothing",
            "command_sha256": "b3385874dd8d1fbda57dc97c38cf6e59b931484ed08e38af5b63b72c82a782f2",
            "exit_code": 1,
            "evidence_path": ".agentfw/evidence/fixture/witness/wp-red.txt"
          },
          "green": {
            "tree": "witness-tree: minimal stub satisfying the contract",
            "command_sha256": "b3385874dd8d1fbda57dc97c38cf6e59b931484ed08e38af5b63b72c82a782f2",
            "exit_code": 0,
            "evidence_path": ".agentfw/evidence/fixture/witness/wp-green.txt"
          }
        }
      }
    }
  ]
}
```
