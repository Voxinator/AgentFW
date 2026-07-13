# Fixture: legacy "version": "1" block (expected: FAIL by default, defect class "version"/"legacy"; PASS under --legacy)

A fully valid v1 plan — under the ORIGINAL v1 rules it has no defect at
all. Default validation must reject it naming the legacy schema version
and pointing at `--legacy`; `validate-plan --legacy` must PASS it. That
default-reject / --legacy-accept PAIR is this fixture's test: --legacy
exists for historical provenance only, never for authoring new plans.

```json agentfw-plan
{
  "version": "1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Endpoint returns the user list"}
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
