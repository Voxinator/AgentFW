# Plan — [Task Name]

## Objective
[What this plan achieves and why. One to three sentences. If you can't state it clearly, you don't understand the task yet.]

## Sub-Tasks

| ID | Description | Dependencies | Verification Method | Verification Criteria | Permission Scope | Status |
|----|-------------|-------------|--------------------|-----------------------|-----------------|--------|
| T1 | | none | build | | [allowed paths, allowed ops, forbidden ops] | planned |
| T2 | | T1 | test:pytest | | [allowed paths, allowed ops, forbidden ops] | planned |
| T3 | | none | lint:eslint | | [allowed paths, allowed ops, forbidden ops] | planned |

**Permission Scope format:** List allowed read/write paths, allowed commands, and explicit denials. Example: `read+write: src/cache/, tests/cache/ | run: pytest tests/cache/ | deny: git commit, dependency changes`

**Verification Method** must be one of: `build`, `test:<command>`, `lint:<command>`, `schema-check`, `human-review`, `expert-subagent`. Free-text criteria like "verify correctness" are not valid — the planner commits to a concrete verification method at planning time, before seeing implementation output.

**Verification Method is locked at planning time.** Changing it after implementation requires an explicit plan amendment with stated justification.

## Sequencing
[Which tasks can run in parallel? Which are sequential? Why?

Tasks with no dependencies on each other run in parallel. Tasks that consume another task's output are sequential. State this explicitly — don't make the worker guess.]

## Risk Areas
[What could go wrong? What's fragile? What assumptions are we making that might be wrong?

Be specific. "It might not work" is not a risk. "The cache invalidation logic assumes all mutations go through the API layer, but batch jobs bypass it" is a risk.]

## Context Budget
[What context does each worker need to do its job? Just as important: what do they NOT need?

Workers should get the minimum context required. Don't dump the entire codebase description into every worker prompt. A worker building the cache layer needs the API handler interface and the config format. It does not need the authentication module's internals or the deployment pipeline documentation.]
