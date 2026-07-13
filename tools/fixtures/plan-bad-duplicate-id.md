# Fixture: duplicate requirement id (expected: FAIL, defect class "duplicate")

Otherwise valid A1 plan. Two distinct requirement records share the id R1,
and R1 is covered — so coverage stays silent and the ONLY defect is the
duplicate declaration, which makes the coverage claim ambiguous (one
covering task cannot prove both texts). Layer 1 must exit non-zero naming
R1 as a duplicate requirement id.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Endpoint returns the user list"},
    {"id": "R1", "text": "Endpoint honors the limit query parameter"}
  ],
  "tasks": [
    {"id": "T1", "title": "User list endpoint", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "GET /users returns 200 with a JSON array of users",
      "acceptance_command": "python3 -m pytest tests/test_users_list.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "rerunnable": true}}
  ]
}
```
