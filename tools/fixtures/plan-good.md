# Fixture: valid plan (expected: PASS)

An A2 plan on the 1.1 schema with three requirements, three tasks at real
seams, complete contracts (each carrying a `required_verification_tier` at
or above the floor mechanically derived from assurance + `integration_seam`
+ `risk_class`, a non-empty `environment`, `evidence`, and a boolean
`rerunnable`), risks paired with negative_cases, and acyclic deps. T2 sits
on an integration seam at A2, so its derived floor is `independent` — and
it declares exactly that.
Layer 1 must exit 0 on this file. This is the canonical GOOD example of a
1.1 block.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "CLI parses a config file and rejects malformed input"},
    {"id": "R2", "text": "Rate limiter caps requests at N per window under parallel load"},
    {"id": "R3", "text": "Docs describe the config schema and the rate-limit knobs"}
  ],
  "tasks": [
    {"id": "T1", "title": "Config parser", "deps": [],
     "contract": {"requirement_ids": ["R1"],
      "criteria": "valid config loads; malformed config exits non-zero with the offending key named",
      "acceptance_command": "python3 -m pytest tests/test_config.py -q",
      "environment": "repo checkout, python3 + pytest, no network",
      "expected_signal": "exit 0; pytest summary line matches 'passed' with no 'failed'",
      "risk": "silent acceptance of malformed config (typo'd key ignored, default applied)",
      "negative_cases": ["config with unknown key 'retrys' exits non-zero naming the key",
                          "empty config file exits non-zero"],
      "evidence": "pytest run log, produced_after_change",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}},
    {"id": "T2", "title": "Rate limiter", "deps": ["T1"],
     "contract": {"requirement_ids": ["R2"],
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
      "constraints": "no network beyond loopback; sandbox only",
      "rerunnable": true}},
    {"id": "T3", "title": "Docs", "deps": ["T1", "T2"],
     "contract": {"requirement_ids": ["R3"],
      "criteria": "docs list every config key the parser accepts and both rate-limit knobs",
      "acceptance_command": "python3 tools/check_docs_keys.py docs/config.md",
      "environment": "repo checkout, python3, no network",
      "expected_signal": "PASS: all parser keys documented; exit 0",
      "risk": "docs drift — a key exists in code but not in docs",
      "negative_cases": ["a key present in the parser but absent from docs/config.md fails the check"],
      "evidence": "checker output listing documented keys, produced_after_change",
      "required_verification_tier": "producer",
      "integration_seam": false,
      "risk_class": "standard",
      "rerunnable": true}}
  ]
}
```
