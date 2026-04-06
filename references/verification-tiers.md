# Verification Tiers

Not all work is verified the same way. Know which tier you're operating in and adjust accordingly.

## Tier 1: Machine-Checkable

The code compiles or it doesn't. Tests pass or fail. The output matches a schema or it doesn't. **For Tier 1 work, always run the check.** Don't assume correctness — verify it.

**Enforcement:** A task **CANNOT** transition from `completed` to `verified` without machine-check output recorded in PROGRESS.md. A judge that reasons about compilation without compiling has **NOT** performed Tier 1 verification. The verification artifact (build log, test output, linter report) must be attached to the task entry.

If machine-checkable verification is available for a task but was not performed, the task remains at `completed` regardless of any other review. No exceptions.

Examples: code compilation, test suites, linting, schema validation, API contract checks, build pipelines.

## Tier 2: Expert-Checkable with Clear Criteria

The output can be evaluated by someone with domain expertise against known criteria. A product strategy that three experienced PMs would assess consistently. A legal brief that practitioners would agree is sound or unsound. An engineering design that reviewers would converge on.

**For Tier 2 work, make the criteria explicit.** Write down what "correct" looks like before you start. Structure your output so the human can sniff-check efficiently — they shouldn't have to reverse-engineer your reasoning to evaluate it.

Examples: product requirements, architecture designs, business analysis, research synthesis, technical writing, process documentation.

## Sniff-Check Enablement

The human's most valuable skill in this framework is **sniff-checking** — rapidly evaluating whether work is correct without redoing it from scratch. Structure your outputs to make sniff-checking easy:

- Lead with the key decisions and their rationale
- Flag areas of uncertainty explicitly rather than burying them
- Provide verification evidence inline (test results, sources, logical chain)
- Make assumptions visible so they can be challenged
- Use clear structure so the reviewer can jump to the areas that matter most

---

For meta-verification of AgentFW itself — evaluating whether the framework is actually improving outcomes — see `evaluation/golden-tasks.md`.
