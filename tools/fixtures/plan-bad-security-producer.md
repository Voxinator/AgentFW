# Fixture: A2 security-class contract declaring tier "producer" (expected: FAIL, defect class "tier")

Otherwise valid A2 plan on the 1.1 schema. T1's contract is complete and its
`required_verification_tier` is a VALID enum value — but the contract sets
`risk_class: "security"`, which mechanically derives a minimum tier of
`adversarial` at EVERY assurance level. Declaring `producer` below that
derived floor is the ONLY defect (no `integration_seam` bump: it is false).
Layer 1 must exit non-zero spelling out the derivation.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "Session tokens are signed and tamper-evident"}
  ],
  "tasks": [
    {"id": "T1", "title": "Token signing", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "a token with a flipped payload byte is rejected with a signature error",
      "acceptance_command": "python3 -m pytest tests/test_token_signing.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0, no 'failed' in summary",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "security",
      "rerunnable": true}}
  ]
}
```
