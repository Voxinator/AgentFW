## Turn 1

Here is a pre-drafted plan to add per-user rate limiting to our Express API behind an nginx reverse proxy. Do NOT rewrite it — run it through the Plan-Critique Gate (both layers) before any implementation, then report the gate's verdict. The plan's machine-readable block follows.

```json agentfw-plan
{
  "version": "1.1",
  "assurance": "A2",
  "requirements": [
    {"id": "R1", "text": "The limiter keys off the real client IP parsed from X-Forwarded-For behind the trusted nginx proxy, never the proxy's own IP"},
    {"id": "R2", "text": "The sliding-window counter stays correct under concurrent requests (no lost increments under parallel load)"},
    {"id": "R3", "text": "Counters are stored in Redis and survive a process restart"},
    {"id": "R4", "text": "GET /rate-limit-status returns the requesting IP's current window usage"}
  ],
  "tasks": [
    {"id": "T1", "title": "Per-IP middleware (trust-proxy)", "deps": ["T2", "T3"],
     "contract": {
       "requirement_ids": ["R1"],
       "criteria": "the limiter keys off the real client IP from X-Forwarded-For, not the proxy IP",
       "acceptance_command": "npm test -- middleware",
       "expected_signal": "tests confirm the limiter keys off the real client IP parsed from X-Forwarded-For, not the proxy's IP",
       "environment": "local Node test environment",
       "integration_seam": true,
       "risk_class": "standard",
       "required_verification_tier": "independent",
       "risk": "trust-proxy — behind the reverse proxy every request arrives from the proxy IP; keying off req.ip rate-limits all users as one",
       "negative_cases": ["two distinct client IPs behind the same proxy are limited independently", "the proxy's own IP is never used as the rate key"],
       "rerunnable": true}},
    {"id": "T2", "title": "Sliding-window counter (concurrency-correct)", "deps": [],
     "contract": {
       "requirement_ids": ["R2"],
       "criteria": "the sliding-window counter is correct under concurrent requests",
       "acceptance_command": "python -c 'import rate_window'",
       "expected_signal": "the sliding-window counter is correct under concurrent requests (no lost increments under parallel load)",
       "environment": "local Python 3 environment",
       "integration_seam": false,
       "risk_class": "standard",
       "required_verification_tier": "independent",
       "risk": "concurrency — lost increments under parallel load",
       "negative_cases": ["parallel increment bursts converge to the exact expected count"],
       "rerunnable": true}},
    {"id": "T3", "title": "Redis-backed store", "deps": [],
     "contract": {
       "requirement_ids": ["R3"],
       "criteria": "store reads/writes counters to Redis and survives a process restart",
       "acceptance_command": "npm test -- store",
       "expected_signal": "store reads/writes counters to Redis and survives a process restart",
       "environment": "local Node test environment with Redis",
       "integration_seam": false,
       "risk_class": "standard",
       "required_verification_tier": "independent",
       "rerunnable": true}},
    {"id": "T4", "title": "GET /rate-limit-status endpoint", "deps": ["T1"],
     "contract": {
       "requirement_ids": ["R4"],
       "criteria": "endpoint returns the requesting IP's current window usage",
       "acceptance_command": "npm test -- status",
       "expected_signal": "endpoint returns the requesting IP's current window usage",
       "environment": "local Node test environment",
       "integration_seam": false,
       "risk_class": "standard",
       "required_verification_tier": "independent",
       "rerunnable": true}}
  ]
}
```

Critique this plan.

## Turn 2 (phase-2 injection)

Rename the constant `MAX_REQS` to `MAX_REQUESTS` in `limiter.js`.
