# Fixture: 1.5 task building a fluff requirement (expected: FAIL, keyword necessity)

T2 spends a task on R2, which the plan itself labels fluff — fluff is
recorded and dropped, never built.

```json agentfw-plan
{
  "version": "1.5",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected",
     "necessity": "must",
     "because": "without rejection, a bad config silently corrupts every downstream run"},
    {"id": "R2", "text": "Config parser emits telemetry on parse timing",
     "necessity": "fluff"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid configuration loads and malformed configuration exits non-zero",
      "acceptance_command": "bash -c 'python3 tests/test_config.py && echo PLAN15_OK'",
      "expected_signal": "terminal line exactly PLAN15_OK with exit 0",
      "environment": "repo checkout, Python 3, no network",
      "evidence": "test output and red-path output, produced_after_change",
      "required_verification_tier": "independent",
      "integration_seam": true,
      "risk_class": "standard",
      "failure_surfaces": [],
      "risk": "a hollow validator could accept malformed configuration",
      "negative_cases": ["an unknown configuration key exits non-zero"],
      "mutation_probes": [
        {"mutation": "on a scratch copy, replace validation with unconditional success", "expected": "red"}
      ],
      "rerunnable": true}},
    {"id": "T2", "title": "Parse-timing telemetry", "deps": ["T1"],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "parse timing is emitted to the telemetry sink",
      "acceptance_command": "bash -c 'python3 tests/test_telemetry.py && echo PLAN15_T_OK'",
      "expected_signal": "terminal line exactly PLAN15_T_OK with exit 0",
      "environment": "repo checkout, Python 3, no network",
      "evidence": "test output, produced_after_change",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "none",
      "failure_surfaces": [],
      "rerunnable": true}}
  ]
}
```
