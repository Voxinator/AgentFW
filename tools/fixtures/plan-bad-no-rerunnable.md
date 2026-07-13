# Fixture: missing rerunnable at A2 (expected: FAIL, defect class "contract")

Otherwise valid A2 plan. T1's contract carries criteria, acceptance_command
and expected_signal but NO `rerunnable` field — the ONLY defect. There is
deliberately no `risk` field, so the risk⇒negative_cases rule stays silent.
Layer 1 must exit non-zero naming T1's incomplete contract.

```json agentfw-plan
{
  "version": "1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "Exporter writes a CSV with a stable header"}
  ],
  "tasks": [
    {"id": "T1", "title": "Exporter", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "export of the sample dataset produces the expected header and row count",
      "acceptance_command": "python3 -m pytest tests/test_export.py -q",
      "expected_signal": "exit 0, no 'failed' in summary"}}
  ]
}
```
