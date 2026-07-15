# Fixture: 1.3 non-terminal expected signal (expected: FAIL)

The expected signal appears before another clause, so the later clause does
not gate the claimed success signal.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A0",
  "required_plan_review_tier": "single",
  "requirements": [{"id": "R1", "text": "A checker reports success"}],
  "tasks": [
    {"id": "T1", "title": "Checker", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "the checker exits zero on valid input",
      "acceptance_command": "bash -c 'python3 tools/check.py && echo EARLY_OK && python3 tools/postcheck.py'",
      "expected_signal": "terminal line exactly EARLY_OK with exit 0"}}
  ]
}
```
