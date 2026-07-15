# Fixture: 1.3 pipe before a gating && (expected: FAIL)

The pipeline can hide the producer check's exit status before the terminal
signal gate.

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
      "acceptance_command": "bash -c 'python3 tools/check.py | tail -n 1 && echo PIPE_OK'",
      "expected_signal": "terminal line exactly PIPE_OK with exit 0"}}
  ]
}
```
