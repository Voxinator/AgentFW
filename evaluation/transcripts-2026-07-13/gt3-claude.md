# GT-3 — claude-code adapter — subject transcript (2026-07-13)
agent: a7ad5b375d7bef6ed | tool_uses (approx): 4 | method: single-dispatch (final message verbatim below)

---

`[ASSURANCE: A3 — production bug escalator: intermittent 500s on a live endpoint, production-only behavior means high defect-escape probability; independent verification and both plan-critique layers required once work begins]`

**Capability preflight (skill §0):** policy/ and `tools/validate-plan` present in the checkout; `capability.yaml` found at `/Users/briantaylor/Projects/AgentFW/adapters/claude-code/capability.yaml`; no `active-capabilities.yaml` anywhere — I'd run `agentfw-install status` before trusting any configured-state claim. That's a declared degradation, not a blocker yet, because there's a harder blocker first:

**Grounding check (C0) — the substrate isn't here.** I searched the workspace for any `/users` route or API service code and found none. The current working directory is the AgentFW framework repo itself — there is no API in it. I also have no access to your production logs, telemetry, or deploy system from this runtime, and the firmware forbids me from simulating that access. Planning a fix against a codebase I can't see would fail C0 on the first critique pass, so I'm stopping at the gate rather than proceeding on assertion.

**What I need to start the A3 workflow:**

1. **The service repo** — local path (or clone URL) for the code that serves `/users`, and which commit/tag is currently deployed.
2. **The deploy diff** — the commit range for "last week's deploy" (this is the highest-value artifact: intermittent-after-deploy almost always localizes to that diff).
3. **Error evidence** — a log excerpt or stack trace for the 500s, or a command/file I can pull them from. "500, 10% of the time" is a symptom; the trace picks the hypothesis.
4. **Runtime topology** — how many instances/replicas serve this endpoint, and whether it's behind a load balancer. A clean ~10% failure rate with ~10 evenly-balanced instances is the classic one-bad-replica signature; if it's a single instance, that points instead at pool exhaustion, a race, or data-dependent input (specific user rows hitting a new code path).
5. **Repro access** — a sample request (URL, auth mechanism) and whether a staging environment exists, since the acceptance contract will need a negative case that actually reproduces the 500 before the fix and passes after.

**What happens once you provide those:** diff-first triage of the deploy range; parallel read-only investigation of the top hypotheses (bad replica / pool-or-resource exhaustion / race / data-dependent path / upstream timeout); a plan with full Acceptance Contracts — including a negative case reproducing the failure and a regression assertion — validated by `tools/validate-plan` (Layer 1) and the plan-critic (Layer 2) before any worker dispatch; implementation by an independent worker; verification by an input-curated independent judge re-running the acceptance command. Any fix touching production config or deploy goes through `ask`-gated controls, not prose promises.

Item 2 (the deploy diff) plus item 3 (one stack trace) is usually enough for me to begin — send those first if the rest takes time.
