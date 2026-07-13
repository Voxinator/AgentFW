# Fixture: valid plan (expected: PASS)

An A2 plan with three requirements, three tasks at real seams, complete
contracts, risks paired with negative_cases, and acyclic deps. Layer 1 must
exit 0 on this file.

```json agentfw-plan
{
  "version": "1",
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
      "expected_signal": "exit 0; pytest summary line matches 'passed' with no 'failed'",
      "risk": "silent acceptance of malformed config (typo'd key ignored, default applied)",
      "negative_cases": ["config with unknown key 'retrys' exits non-zero naming the key",
                          "empty config file exits non-zero"],
      "rerunnable": true}},
    {"id": "T2", "title": "Rate limiter", "deps": ["T1"],
     "contract": {"requirement_ids": ["R2"],
      "criteria": "200 parallel requests against limit=50/window admit exactly 50",
      "acceptance_command": "python3 tests/limiter_load.py --parallel 200 --limit 50",
      "expected_signal": "line matching 'PASS.*admitted=50' and exit 0",
      "risk": "concurrency — counter drift under parallel writers",
      "negative_cases": ["201st request within the window is rejected with 429",
                          "parallel writers never admit more than the cap"],
      "rerunnable": true}},
    {"id": "T3", "title": "Docs", "deps": ["T1", "T2"],
     "contract": {"requirement_ids": ["R3"],
      "criteria": "docs list every config key the parser accepts and both rate-limit knobs",
      "acceptance_command": "python3 tools/check_docs_keys.py docs/config.md",
      "expected_signal": "PASS: all parser keys documented; exit 0",
      "risk": "docs drift — a key exists in code but not in docs",
      "negative_cases": ["a key present in the parser but absent from docs/config.md fails the check"],
      "rerunnable": true}}
  ]
}
```
