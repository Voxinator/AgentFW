# Fixture: 1.1 A2 contract with rerunnable as the STRING "true" (expected: FAIL, defect class "contract")

Otherwise valid A2 plan on the 1.1 schema. T1's contract is complete —
consistent tier, non-empty environment, risk paired with negative_cases —
but `rerunnable` is the quoted string "true", not the JSON boolean true.
That type defect is the ONLY defect (the field is PRESENT, so the v1
missing-rerunnable rule stays silent). Layer 1 must exit non-zero naming the
non-boolean contract field.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "Exporter writes a CSV with a stable header"}
  ],
  "tasks": [
    {"id": "T1", "title": "Exporter", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "export of the sample dataset produces the expected header and row count",
      "acceptance_command": "python3 -m pytest tests/test_export.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0; pytest summary matches 'passed' with no 'failed'",
      "risk": "header drift breaks downstream ingestion",
      "negative_cases": ["a renamed column fails the header assertion"],
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": "true"}}
  ]
}
```
