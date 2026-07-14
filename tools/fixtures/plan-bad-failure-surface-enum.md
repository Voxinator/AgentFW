# Fixture: 1.2 contract with an invalid failure_surfaces member (expected: FAIL, defect class "failure_surface")

Otherwise valid A2 plan on the 1.2 schema, `required_plan_review_tier`
declared "dual" (at or above any derivable floor, so the review tier is NOT
in question). T1's `failure_surfaces` carries the member "network", which is
not in the enum {concurrency, trust_boundary, streaming, clock,
production_only}. That invalid member is the ONLY defect. Layer 1 must exit
non-zero naming the member and the enum.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "required_plan_review_tier": "dual",
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
      "failure_surfaces": ["network"],
      "rerunnable": true}}
  ]
}
```
