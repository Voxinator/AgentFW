# Fixture: invalid 1.3 mutation-probe entry shapes (expected: FAIL)

The four entries exercise the object, non-empty mutation, expected-red, and
exact-key requirements independently.

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
      "acceptance_command": "bash -c 'python3 tools/check.py && echo SHAPE_OK'",
      "expected_signal": "terminal line exactly SHAPE_OK with exit 0",
      "mutation_probes": [
        "replace the checker",
        {"mutation": " ", "expected": "red"},
        {"mutation": "replace the checker with unconditional success", "expected": "green"},
        {"mutation": "remove the required assertion", "expected": "red", "note": "extra key"}
      ]}}
  ]
}
```
