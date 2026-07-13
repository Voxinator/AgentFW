# Fixture: empty A2 plan (expected: FAIL, defect class "empty")

Structurally valid JSON block at assurance A2 whose `requirements` and
`tasks` arrays are both PRESENT but empty — so the rejection comes from the
A2+ substance check ("empty"), not from a JSON or missing-field error.
Layer 1 must exit non-zero naming the empty lists. This is the probe that
PASSed against the first build of this validator.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [],
  "tasks": []
}
```
