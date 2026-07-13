# Fixture: task without an id (expected: FAIL, defect class "empty")

Otherwise valid A1 plan on the 1.1 schema. The second task record carries a
complete contract but NO `id` field — the ONLY defect. The task-id precheck
runs BEFORE coverage/dependency/cycle validation, so Layer 1 must exit
non-zero with a defect naming task index #1 and the missing/empty id — not
a downstream KeyError, not a silent skip.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Parser handles valid input"},
    {"id": "R2", "text": "Parser rejects invalid input"}
  ],
  "tasks": [
    {"id": "T1", "title": "Happy path", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid input parses to the expected AST",
      "acceptance_command": "python3 -m pytest tests/test_parse_ok.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}},
    {"title": "Rejection path", "deps": [],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "invalid input exits non-zero with a diagnostic",
      "acceptance_command": "python3 -m pytest tests/test_parse_reject.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}}
  ]
}
```
