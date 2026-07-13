# Fixture: duplicated JSON key (expected: FAIL, defect class "duplicate")

Otherwise valid A2 plan whose block declares `"tasks"` TWICE — first empty,
then valid. A last-wins JSON parser silently keeps the second and PASSes,
while a human reading top-down may believe the plan has no tasks. Layer 1
must exit non-zero naming the duplicated key `tasks` instead of accepting
the ambiguity.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "Exporter writes a CSV with a stable header"}
  ],
  "tasks": [],
  "tasks": [
    {"id": "T1", "title": "Exporter", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "export of the sample dataset produces the expected header and row count",
      "acceptance_command": "python3 -m pytest tests/test_export.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}}
  ]
}
```
