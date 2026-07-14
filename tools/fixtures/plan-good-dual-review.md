# Fixture: valid 1.2 plan at dual review (expected: PASS)

An A3 plan on the 1.2 schema with two requirements, two tasks at real seams,
and complete contracts. Schema 1.2 additions are all present and consistent:
plan-level `required_plan_review_tier: "dual"` — exactly the floor
mechanically derived from assurance A3 (and independently triggered by T1's
non-empty `failure_surfaces`) — and every contract carries
`failure_surfaces` as an enum subset (T1 names `concurrency`, the layer its
risk exercises; T2's is the valid EMPTY array). A3's 1.1 rules also hold:
`evidence` and `negative_cases` everywhere, verification tiers at or above
the derived floor (independent). Layer 1 must exit 0 on this file. This is
the canonical GOOD example of a 1.2 block.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A3",
  "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "Rate limiter caps requests at N per window under parallel load"},
    {"id": "R2", "text": "Docs describe the rate-limit knobs and their defaults"}
  ],
  "tasks": [
    {"id": "T1", "title": "Rate limiter", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "200 parallel requests against limit=50/window admit exactly 50",
      "acceptance_command": "python3 tests/limiter_load.py --parallel 200 --limit 50",
      "environment": "repo checkout, python3, loopback only — parallel load runs locally",
      "expected_signal": "line matching 'PASS.*admitted=50' and exit 0",
      "risk": "concurrency — counter drift under parallel writers",
      "negative_cases": ["201st request within the window is rejected with 429",
                          "parallel writers never admit more than the cap"],
      "evidence": "load-run output with admitted count, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": ["concurrency"],
      "rerunnable": true}},
    {"id": "T2", "title": "Docs", "deps": ["T1"],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "docs list both rate-limit knobs with the defaults the limiter actually applies",
      "acceptance_command": "python3 tools/check_docs_keys.py docs/rate-limit.md",
      "environment": "repo checkout, python3, no network",
      "expected_signal": "PASS: all limiter knobs documented; exit 0",
      "risk": "docs drift — a knob exists in code but not in docs",
      "negative_cases": ["a knob present in the limiter but absent from docs/rate-limit.md fails the check"],
      "evidence": "checker output listing documented knobs, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": false,
      "risk_class": "standard",
      "failure_surfaces": [],
      "rerunnable": true}}
  ]
}
```
