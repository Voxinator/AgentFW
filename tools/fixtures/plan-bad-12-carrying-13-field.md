# Fixture: 1.2 plan carrying schema-1.3 mutation probes (expected: FAIL)

Schema 1.2 remains valid, but it must not fail open on the field introduced by
1.3. A plan using mutation probes declares version 1.3.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A0",
  "required_plan_review_tier": "single",
  "requirements": [{"id": "R1", "text": "A checker reports success"}],
  "tasks": [
    {"id": "T1", "title": "Checker", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "the checker exits zero on valid input",
      "acceptance_command": "python3 tools/check.py",
      "expected_signal": "exit 0",
      "mutation_probes": [
        {"mutation": "replace the checker with unconditional success", "expected": "red"}
      ]}}
  ]
}
```
