# Fixture: valid 1.2 plan at single review (expected: PASS)

An A2 plan on the 1.2 schema, one requirement, one task at standard risk with
NO seam and an EMPTY `failure_surfaces` array — none of the dual triggers
(assurance A3/A4, a task risk_class of security/destructive, or a non-empty
`failure_surfaces`) apply, so the mechanically derived plan-review floor is
`single`. The plan declares `required_plan_review_tier: "single"` — exactly
at the floor. 1.1 rules also hold: `integration_seam` false, `risk_class`
standard, `required_verification_tier` at or above the A2 base floor
(`producer`), a non-empty `environment`, and `rerunnable` as a JSON boolean.
Layer 1 must exit 0 on this file, and the PASS output must carry
`review tier: single`.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "CLI --version prints the installed package version"}
  ],
  "tasks": [
    {"id": "T1", "title": "Wire --version flag", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "running the CLI with --version prints the version string from package metadata and exits 0",
      "acceptance_command": "python3 -m mypkg --version",
      "environment": "repo checkout, python3, no network",
      "expected_signal": "line matching '^mypkg [0-9]+\\.[0-9]+\\.[0-9]+$' and exit 0",
      "evidence": "command output showing the printed version string, produced_after_change",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "rerunnable": true}}
  ]
}
```
