# Fixture: 1.1 plan carrying the schema-1.2-only fields (expected: FAIL, defect class "version")

Otherwise valid A2 plan on the 1.1 schema — but it carries BOTH 1.2-only
fields: plan-level `required_plan_review_tier` and a per-contract
`failure_surfaces` (the exact fail-open shape probed against the shipped
pre-1.2 validator, which tolerated unknown fields on 1.1). Schema 1.1 does
not define these fields, so declaring them on a 1.1 block is the defect:
the declared-single-on-1.1 dodge must not validate. Layer 1 must exit
non-zero with diagnostics naming schema version 1.2 for each carried field.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "required_plan_review_tier": "single",
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
      "failure_surfaces": ["concurrency"],
      "rerunnable": true}}
  ]
}
```
