# Fixture: cyclic dependencies (expected: FAIL, defect class "cycl")

Otherwise valid A1 plan. T1 deps T2 and T2 deps T1 — the ONLY defect.
Layer 1 must exit non-zero reporting the dependency cycle.

```json agentfw-plan
{
  "version": "1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Exporter writes CSV"},
    {"id": "R2", "text": "Importer reads CSV"}
  ],
  "tasks": [
    {"id": "T1", "title": "Exporter", "deps": ["T2"],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "export of the sample dataset produces a CSV with the expected header and row count",
      "acceptance_command": "python3 -m pytest tests/test_export.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}},
    {"id": "T2", "title": "Importer", "deps": ["T1"],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "import of the exported CSV round-trips to the original dataset",
      "acceptance_command": "python3 -m pytest tests/test_import.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}}
  ]
}
```
