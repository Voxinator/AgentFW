# Fixture: 1.2 plan missing required_plan_review_tier (expected: FAIL, defect class "review")

Otherwise valid A2 plan on the 1.2 schema — the single task's contract is
complete and carries an (empty, valid) `failure_surfaces` array — but the
plan level omits `required_plan_review_tier`, which schema 1.2 REQUIRES on
every plan. That omission is the ONLY defect. Layer 1 must exit non-zero
naming `required_plan_review_tier`.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "CLI parses a config file and rejects malformed input"}
  ],
  "tasks": [
    {"id": "T1", "title": "Config parser", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid config loads; malformed config exits non-zero with the offending key named",
      "acceptance_command": "python3 -m pytest tests/test_config.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0; pytest summary matches 'passed' with no 'failed'",
      "evidence": "pytest run log, produced_after_change",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "rerunnable": true}}
  ]
}
```
