# Fixture: invalid 1.4 override-entry shapes (expected: FAIL)

The four entries exercise the exact-key (missing `followup_test`), non-empty
value, extra-key, and string-type requirements independently.

```json agentfw-plan
{
  "version": "1.4",
  "assurance": "A0",
  "required_plan_review_tier": "single",
  "overrides": [
    {"blocker": "C2: weak acceptance command",
     "assumption": "the fixture corpus covers the weak path",
     "authorized_turn": "human turn 'go ahead'"},
    {"blocker": " ",
     "assumption": "the fixture corpus covers the weak path",
     "followup_test": "add a red-path probe",
     "authorized_turn": "human turn 'go ahead'"},
    {"blocker": "C2: weak acceptance command",
     "assumption": "the fixture corpus covers the weak path",
     "followup_test": "add a red-path probe",
     "authorized_turn": "human turn 'go ahead'",
     "note": "extra key"},
    {"blocker": "C2: weak acceptance command",
     "assumption": "the fixture corpus covers the weak path",
     "followup_test": "add a red-path probe",
     "authorized_turn": 3}
  ],
  "requirements": [{"id": "R1", "text": "A checker reports success"}],
  "tasks": [
    {"id": "T1", "title": "Checker", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "the checker exits zero on valid input",
      "acceptance_command": "bash -c 'python3 tools/check.py && echo SHAPE14_OK'",
      "expected_signal": "terminal line exactly SHAPE14_OK with exit 0"}}
  ]
}
```
