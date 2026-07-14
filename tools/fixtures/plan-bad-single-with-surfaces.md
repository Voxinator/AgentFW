# Fixture: 1.2 plan declaring "single" while a task carries non-empty failure_surfaces (expected: FAIL, defect class "review")

Otherwise valid A2 plan on the 1.2 schema. Every field is individually valid
— `required_plan_review_tier: "single"` is a legal enum value and T1's
`failure_surfaces: ["concurrency"]` is a legal enum subset — but a NON-EMPTY
`failure_surfaces` on any task mechanically floors the plan-review tier at
dual. The declared "single" is below that floor; the misclassification is
the ONLY defect. Layer 1 must exit non-zero naming the floor/dual
derivation.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Rate limiter caps requests at N per window under parallel load"}
  ],
  "tasks": [
    {"id": "T1", "title": "Rate limiter", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "200 parallel requests against limit=50/window admit exactly 50",
      "acceptance_command": "python3 tests/limiter_load.py --parallel 200 --limit 50",
      "environment": "repo checkout, python3, loopback only — parallel load runs locally",
      "expected_signal": "line matching 'PASS.*admitted=50' and exit 0",
      "risk": "concurrency — counter drift under parallel writers",
      "negative_cases": ["201st request within the window is rejected with 429"],
      "evidence": "load-run output with admitted count, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": ["concurrency"],
      "rerunnable": true}}
  ]
}
```
