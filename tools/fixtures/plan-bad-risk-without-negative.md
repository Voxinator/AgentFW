# Fixture: risk without negative_cases (expected: FAIL, defect class "negative")

Otherwise valid **A1** plan (deliberately below A3, so the only rule that can
fire is risk ⇒ negative_cases, not the A3/A4 all-contracts rule). T1 carries a
risk but no negative_cases — the ONLY defect. Layer 1 must exit non-zero
naming T1 and the missing negative_cases.

```json agentfw-plan
{
  "version": "1",
  "assurance": "A1",
  "requirements": [
    {"id": "R1", "text": "Session token refresh works across clock skew"}
  ],
  "tasks": [
    {"id": "T1", "title": "Token refresh", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "refresh succeeds with client clock skewed +/-5 minutes",
      "acceptance_command": "python3 -m pytest tests/test_refresh_skew.py -q",
      "expected_signal": "exit 0, no 'failed' in summary",
      "risk": "clock — skewed client clock invalidates tokens early",
      "rerunnable": true}}
  ]
}
```
