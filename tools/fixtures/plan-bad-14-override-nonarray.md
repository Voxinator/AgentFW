# Fixture: 1.4 overrides ledger as a string, not an array (expected: FAIL)

A prose summary is not a ledger: `overrides` must be a JSON array of
four-field objects, or the mechanical record of assumption-gated dispatch
records nothing.

```json agentfw-plan
{
  "version": "1.4",
  "assurance": "A0",
  "required_plan_review_tier": "single",
  "overrides": "waived C2 on a human turn 'ship it'",
  "requirements": [{"id": "R1", "text": "A checker reports success"}],
  "tasks": [
    {"id": "T1", "title": "Checker", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "the checker exits zero on valid input",
      "acceptance_command": "bash -c 'python3 tools/check.py && echo NONARR14_OK'",
      "expected_signal": "terminal line exactly NONARR14_OK with exit 0"}}
  ]
}
```
