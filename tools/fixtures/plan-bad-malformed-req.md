# Fixture: malformed requirement record (expected: FAIL, defect class "empty")

Otherwise valid A1 plan. The second requirement record has an id but an
EMPTY `text` — the ONLY defect. Both declared ids are covered, so coverage
stays silent. Layer 1 must exit non-zero naming record #1 and the empty
'text' field (malformed requirement record).

```json agentfw-plan
{
  "version": "1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Parser handles valid input"},
    {"id": "R2", "text": ""}
  ],
  "tasks": [
    {"id": "T1", "title": "Parser", "deps": [],
     "contract": {"requirement_ids": ["R1", "R2"],
      "criteria": "valid input parses to the expected AST",
      "acceptance_command": "python3 -m pytest tests/test_parse.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}}
  ]
}
```
