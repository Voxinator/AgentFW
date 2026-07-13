# Fixture: A2 integration-seam contract declaring tier "producer" (expected: FAIL, defect class "tier")

Otherwise valid A2 plan on the 1.1 schema. T1's contract is complete and its
`required_verification_tier` is a VALID enum value — but the contract sets
`integration_seam: true`, and at A2 a seam mechanically derives a minimum
tier of `independent`. Declaring `producer` below that derived floor is the
ONLY defect. Layer 1 must exit non-zero spelling out the derivation.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "Exporter and importer round-trip the sample dataset across the module boundary"}
  ],
  "tasks": [
    {"id": "T1", "title": "Export/import round-trip", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "exporting then importing the sample dataset reproduces it record-for-record across the exporter/importer seam",
      "acceptance_command": "python3 -m pytest tests/test_roundtrip.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0, no 'failed' in summary",
      "required_verification_tier": "producer",
      "integration_seam": true,
      "risk_class": "standard",
      "rerunnable": true}}
  ]
}
```
