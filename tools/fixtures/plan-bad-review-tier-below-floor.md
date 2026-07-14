# Fixture: 1.2 A3 plan declaring required_plan_review_tier "single" (expected: FAIL, defect class "review")

Otherwise valid A3 plan on the 1.2 schema. The declared
`required_plan_review_tier` is a VALID enum value — but "single" is below
the floor mechanically derived from assurance A3 (A3/A4 => dual; the task's
empty `failure_surfaces` and standard `risk_class` add no independent
trigger). That misclassification is the ONLY defect. Layer 1 must exit
non-zero spelling out the derivation (diagnostic names the floor and dual).

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A3",
  "required_plan_review_tier": "single",
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
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "rerunnable": true}}
  ]
}
```
