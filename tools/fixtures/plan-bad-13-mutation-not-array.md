# Fixture: 1.3 mutation_probes is not an array (expected: FAIL)

Even where probes are optional, carrying the field binds its schema type.

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
      "acceptance_command": "python3 tools/check.py",
      "expected_signal": "exit 0",
      "mutation_probes": {"mutation": "replace the checker", "expected": "red"}}}
  ]
}
```
