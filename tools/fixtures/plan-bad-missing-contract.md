# Fixture: incomplete contract (expected: FAIL, defect class "contract")

Otherwise valid A1 plan. T2's contract has an empty acceptance_command — the
ONLY defect. Layer 1 must exit non-zero naming T2 and the contract defect.

```json agentfw-plan
{
  "version": "1",
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
    {"id": "T2", "title": "Rejection path", "deps": ["T1"],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "invalid input exits non-zero with a diagnostic",
      "acceptance_command": "",
      "expected_signal": "exit 1 with 'parse error' on stderr",
      "rerunnable": true}}
  ]
}
```
