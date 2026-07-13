# Fixture: uncovered requirement (expected: FAIL, defect class "cover")

Otherwise valid A1 plan. R2 is covered by no task's requirement_ids — the
ONLY defect. Layer 1 must exit non-zero naming R2 as uncovered.

```json agentfw-plan
{
  "version": "1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Endpoint returns the user list"},
    {"id": "R2", "text": "Endpoint honors the limit query parameter"}
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
