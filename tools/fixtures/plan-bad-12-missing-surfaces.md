# Fixture: 1.2 A2 contract missing failure_surfaces (expected: FAIL, defect class "failure_surface")

Otherwise valid A2 plan on the 1.2 schema with `required_plan_review_tier`
declared (`single` — correct: no dual trigger). T1's contract is complete
under the 1.1 rules but omits `failure_surfaces`, which schema 1.2 REQUIRES
in every contract at A2+ (an EMPTY array would have been valid — absence is
the defect, not emptiness). That omission is the ONLY defect. Layer 1 must
exit non-zero naming `failure_surfaces`.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "CLI parses a config file and rejects malformed input"}
  ],
  "tasks": [
    {"id": "T1", "title": "Config parser", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid config loads; malformed config exits non-zero with the offending key named",
      "acceptance_command": "python3 -m pytest tests/test_config.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0; pytest summary matches 'passed' with no 'failed'",
      "evidence": "pytest run log, produced_after_change",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}}
  ]
}
```
