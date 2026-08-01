# Fixture: valid 1.5 plan with necessity tiers (expected: PASS + scope note)

Schema 1.5 is additive over 1.4. Two must requirements (covered, each with a
plain-language `because`), one nice-to-have pulled into the increment by a
human (covered — produces the non-fatal scope note), one nice-to-have left
uncovered (valid: deferred to the next increment), and one fluff requirement
left uncovered (valid: recorded and dropped).

```json agentfw-plan
{
  "version": "1.5",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "Malformed configuration is rejected",
     "necessity": "must",
     "because": "without rejection, a bad config silently corrupts every downstream run"},
    {"id": "R2", "text": "Config errors name the offending key",
     "necessity": "must",
     "because": "without the key name, an operator cannot fix the config they are told is broken"},
    {"id": "R3", "text": "Config file supports comments",
     "necessity": "nice-to-have"},
    {"id": "R4", "text": "Config hot-reloads without restart",
     "necessity": "nice-to-have"},
    {"id": "R5", "text": "Config parser emits telemetry on parse timing",
     "necessity": "fluff"}
  ],
  "tasks": [
    {"id": "T1", "title": "Configuration validation", "deps": [],
     "contract": {"requirement_ids": ["R1", "R2"],
      "criteria": "valid configuration loads; malformed configuration exits non-zero naming the key",
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
    {"id": "T2", "title": "Comment support (human-pulled nice-to-have)", "deps": ["T1"],
     "contract": {"requirement_ids": ["R3"],
      "criteria": "a config containing # comments parses identically to one without",
      "acceptance_command": "bash -c 'python3 tests/test_comments.py && echo PLAN15_C_OK'",
      "expected_signal": "terminal line exactly PLAN15_C_OK with exit 0",
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
