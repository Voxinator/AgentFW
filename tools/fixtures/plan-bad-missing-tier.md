# Fixture: 1.1 A3 contract missing required_verification_tier (expected: FAIL, defect class "tier")

Otherwise valid A3 plan on the 1.1 schema. T1's contract carries criteria,
acceptance_command, expected_signal, environment, evidence, negative_cases,
integration_seam, risk_class, and a boolean rerunnable — but NO
`required_verification_tier`, the ONLY defect. Layer 1 must exit non-zero
naming the missing tier.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A3",
  "requirements": [
    {"id": "R1", "text": "Importer deduplicates records by natural key"}
  ],
  "tasks": [
    {"id": "T1", "title": "Importer", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "importing the sample twice yields exactly one record per natural key",
      "acceptance_command": "python3 -m pytest tests/test_import_dedupe.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0; pytest summary matches 'passed' with no 'failed'",
      "risk": "duplicate rows on re-import silently corrupt downstream counts",
      "negative_cases": ["re-importing the same file adds zero new rows",
                          "two records differing only in whitespace collapse to one"],
      "evidence": "pytest run log, produced_after_change",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}}
  ]
}
```
