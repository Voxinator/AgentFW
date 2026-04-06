# Domain Application Guidelines

## For Code Work
- Decompose by module/feature/component
- Verify via compilation, tests, linting
- Use git-style atomic changes (one logical change per unit of work)
- Leave code comments explaining non-obvious decisions
- Maintain a test suite that grows with the implementation
- See `references/verification-tiers.md` for Tier 1 verification details. See `core/permissions.md` for scoping worker access to specific modules.

### Compiled Languages (C++, Rust, Go, Java, C#, Swift, Unreal Engine C++)

The judge **MUST** execute a build as the first verification step. Reasoning-only review does not constitute Tier 1 verification. Build output (success or error log) must be included in the verification artifact.

**Build verification is non-negotiable** — code that doesn't compile has not been verified regardless of how correct it looks. A judge that reviews C++ without compiling has performed zero verification.

### Interpreted Languages (Python, JavaScript, TypeScript, Ruby)

The judge **MUST** execute the relevant test suite or linter. If no tests exist, the judge must at minimum run the entry point or import the module to verify no syntax/import errors.

Reasoning about whether code "looks correct" without executing it is not Tier 1 verification for any language.

### Long-Running Services (Web Apps, Gateways, Daemons)

When modifying code for a running service — web applications, API servers, agent gateways (e.g., OpenClaw, Hermes), background workers, or any long-running process — **the worker or judge MUST restart the service** after applying changes. The change is not verifiable until the service is running the new code.

Automate this. Do not leave "restart the server" as a manual step for the human. If you know the service command (e.g., `npm run dev`, `flask run`, `systemctl restart`, `docker compose restart`), run it. If you don't know it, check for common patterns (package.json scripts, Procfile, docker-compose.yml, systemd units) or ask.

**A code change to a running service that hasn't been restarted has not been deployed, and therefore has not been verified.** This is the runtime equivalent of writing compiled code without building it.

## For Product/Strategy Work
- Decompose by analysis dimension (market, technical, financial, user)
- Verify via explicit criteria and stakeholder-checkable structure
- Lead with decisions and recommendations, support with evidence
- Make assumptions and risks visible
- Structure for executive sniff-checking (summary → detail → evidence)
- See `references/verification-tiers.md` for Tier 2 (expert-checkable) verification patterns.

## For Research/Analysis
- Decompose by question/hypothesis
- Verify via source quality, logical consistency, and coverage
- Separate facts from interpretation
- Flag confidence levels explicitly
- Provide enough context for the reviewer to evaluate independently
- See `references/prompt-design.md` for context budget guidance when dispatching research sub-agents.

## For Documentation/Writing
- Decompose by section/audience/purpose
- Verify via completeness checklist and readability
- Structure for the reader's workflow, not the writer's
- Include verification artifacts (did I cover all the requirements?)
- See `references/verification-tiers.md` for completeness checklist verification.
