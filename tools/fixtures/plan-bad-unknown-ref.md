# Fixture: unknown requirement reference (expected: FAIL, defect class "cover")

Otherwise valid A2 plan. The single declared requirement R1 IS covered, so
the uncovered-requirement rule stays silent; T1's `requirement_ids` also
names R99, which is declared nowhere — the ONLY defect. Layer 1 must exit
non-zero reporting that T1 references unknown requirement R99. This is the
probe that PASSed against the first build of this validator.

```json agentfw-plan
{
  "version": "1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "Exporter writes a CSV with a stable header"}
  ],
  "tasks": [
    {"id": "T1", "title": "Exporter", "deps": [],
     "contract": {"requirement_ids": ["R1", "R99"],
      "criteria": "export of the sample dataset produces the expected header and row count",
      "acceptance_command": "python3 -m pytest tests/test_export.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}}
  ]
}
```
