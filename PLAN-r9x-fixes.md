# AgentFW r9.x candidate fixes

## Scope and operating constraints

- Implement C-1 through C-6 from `R9X-CANDIDATES.md`.
- Assurance: A2. The work is reversible repository editing across policy, validation, prompts,
  references, and installer seams. There are no destructive, production, or outward-facing steps.
- Capability preflight: local shell and isolated subagents are available. The live Codex install has
  `sandbox_mode = "danger-full-access"` and `approval_policy = "never"`, so deterministic permissions
  are not configured. Degradation: constrain all workers to named repository paths; do not install,
  commit, push, modify user configuration, access the network, or touch the existing untracked source
  files outside this plan and task evidence.
- Named relaxation authorized by the maintainer: skip Layer-2 plan-critic/evaluation passes. This does
  not relax Layer-1 validation, producer checks, persisted evidence, or one input-curated independent
  verification pass over the completed fixes.
- Workers may create `evidence/r9x-*.log` containing raw producer command output.

## Recovery record

- Independent verification found a contract-scope integration defect after T1/T2/T3 were green:
  `policy/plan-critique.md` still named schema 1.2 as the schema of record and omitted the schema
  1.3 mutation-probe/command-shape Layer-1 rules. Contaminated evidence: T1 and T2 command results
  were insufficient to establish cross-policy schema consistency; T3 evidence is unaffected.
- Recovery action: fresh-context, narrowly scoped fix-forward in `policy/plan-critique.md` plus a
  deterministic regression assertion in `tools/tests/validate-plan.sh`; then rerun the affected
  producer commands and one fresh independent verification pass. No behavioral evaluation round.

```json agentfw-plan
{
  "version": "1.2",
  "assurance": "A2",
  "required_plan_review_tier": "single",
  "requirements": [
    {"id": "R1", "text": "C-1: require producer red-path self-probes and reject known weak acceptance-command shapes in the new schema."},
    {"id": "R2", "text": "C-2: add mutation_probes as first-class schema 1.3 contract fields and require verifier execution."},
    {"id": "R3", "text": "C-3: add a fixture/eval-artifact leak-channel hygiene reference with one-source pattern discipline."},
    {"id": "R4", "text": "C-4: make empirical C2 probing and demonstrated/reasoned tagging intrinsic to the plan-critic definition and policy."},
    {"id": "R5", "text": "C-5: define the standard cap-with-open-blocker relaxation menu and eligibility rules."},
    {"id": "R6", "text": "C-6: have installer status persist actual command resolution for command-critical utilities."}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Schema 1.3, mutation probes, and acceptance-command lint",
      "deps": [],
      "contract": {
        "requirement_ids": ["R1", "R2"],
        "criteria": "Schema 1.3 is the schema of record while 1.1/1.2 stay valid; 1.3 validates mutation_probes entries shaped as {mutation: non-empty string, expected: red}, requires at least one for integration seams and every A3/A4 contract, and rejects known weak acceptance-command shapes. Both adapter skill examples and prose describe producer red-path probing, terminal signal ordering, and schema 1.3. Positive and hostile fixtures exercise every new rule.",
        "acceptance_command": "bash -c 'set -euo pipefail; bash tools/tests/validate-plan.sh; for p in PLAN-*.md; do python3 tools/validate-plan \"$p\" >/dev/null; done; echo T1_OK'",
        "expected_signal": "terminal line exactly T1_OK with exit 0",
        "environment": "macOS repository shell; Python 3 stdlib and Bash; no network",
        "evidence": "evidence/r9x-t1.log produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "risk": "A schema/documentation mismatch or weak-shape false negative could allow hollow acceptance commands to pass.",
        "negative_cases": [
          "A 1.3 integration-seam contract without mutation_probes is rejected.",
          "A mutation probe with expected other than red or an empty mutation is rejected.",
          "A pipe before a gating &&, an unguarded echo signal, or a non-terminal signal is rejected under 1.3.",
          "A valid 1.3 contract passes while representative 1.1 and 1.2 plans remain valid."
        ],
        "rerunnable": true,
        "constraints": {"allowed_paths": ["tools/validate-plan", "tools/fixtures", "tools/tests/validate-plan.sh", "policy/acceptance-contract.md", "adapters/claude-code/skills/agentfw/SKILL.md", "adapters/codex/skills/agentfw/SKILL.md", "evidence/r9x-t1.log"], "forbidden": ["network", "install", "commit", "push"]}
      }
    },
    {
      "id": "T2",
      "title": "Fixture hygiene, empirical critic behavior, and cap recovery menu",
      "deps": [],
      "contract": {
        "requirement_ids": ["R3", "R4", "R5"],
        "criteria": "Fixture hygiene enumerates contents, names, messages, refs, reflog, comments, and committed tooling; guard patterns and worker banned words share one source; validation tooling remains outside the artifact; history and refs remain neutral. Plan critics empirically probe C2 where feasible and label findings demonstrated or reasoned. Plan-critique/recovery policy defines extend-one-pass, mutation-gated dispatch, and halt with exact eligibility and bespoke-relaxation handling. The verifier executes all mutation probes on scratch copies before a verified verdict.",
        "acceptance_command": "bash -c 'set -euo pipefail; test -s references/fixture-hygiene.md; grep -q \"demonstrated\" adapters/claude-code/agents/agentfw-plan-critic.md; grep -q \"mutation_probes\" adapters/claude-code/agents/agentfw-verifier.md; grep -q \"mutation-gated\" policy/plan-critique.md; grep -q \"extend.*exactly one\\|exactly one.*pass\" policy/recovery.md; bash tools/tests/check-links.sh >/dev/null; echo T2_OK'",
        "expected_signal": "terminal line exactly T2_OK with exit 0",
        "environment": "macOS repository shell with POSIX utilities; no network",
        "evidence": "evidence/r9x-t2.log produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "risk": "Policy may remain dispatch-prompt-dependent or permit mutation-gated dispatch outside its narrow safe preconditions.",
        "negative_cases": [
          "The hygiene reference is incomplete if any named leak channel or the one-source identity rule is absent.",
          "A reasoned C2 finding cannot be presented as demonstrated without live output.",
          "Mutation-gated dispatch is forbidden if any blocker is not C2-local or lacks a contracted mechanical compensation.",
          "Extending the cap is not an open-ended retry; it is exactly one named pass under stated conditions."
        ],
        "rerunnable": true,
        "constraints": {"allowed_paths": ["references/prompt-design.md", "references/fixture-hygiene.md", "policy/plan-critique.md", "policy/recovery.md", "adapters/claude-code/agents/agentfw-plan-critic.md", "adapters/claude-code/agents/agentfw-verifier.md", "evidence/r9x-t2.log"], "forbidden": ["network", "install", "commit", "push"]}
      }
    },
    {
      "id": "T3",
      "title": "Command-resolution status preflight",
      "deps": [],
      "contract": {
        "requirement_ids": ["R6"],
        "criteria": "agentfw-install status reports and persists both command -v and type resolution for grep, sed, find, md5, and sqlite3 in active-capabilities.yaml, safely encodes functions/wrappers and missing commands, and the roundtrip suite proves real system paths plus hostile wrapper/missing-command behavior without changing user settings.",
        "acceptance_command": "bash -c 'set -euo pipefail; o=$(bash tools/tests/install-roundtrip.sh); grep -q \"ALL CHECKS PASSED\" <<<\"$o\"; grep -q \"command_resolution\" tools/agentfw-install; echo T3_OK'",
        "expected_signal": "terminal line exactly T3_OK with exit 0",
        "environment": "macOS Bash test sandboxes with Python 3; no network and no writes outside mktemp sandboxes/evidence",
        "evidence": "evidence/r9x-t3.log produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "risk": "Status could claim a system utility while the live shell resolves a wrapper/function, or emit invalid YAML for hostile resolution text.",
        "negative_cases": [
          "An exported grep wrapper/function is recorded as such rather than mislabeled as the system grep.",
          "An unavailable command is recorded explicitly without making status fail.",
          "Generated active-capabilities.yaml remains parseable under hostile resolution strings."
        ],
        "rerunnable": true,
        "constraints": {"allowed_paths": ["tools/agentfw-install", "tools/tests/install-roundtrip.sh", "adapters/claude-code/capability.yaml", "evidence/r9x-t3.log"], "forbidden": ["network", "live install", "user configuration", "commit", "push"]}
      }
    }
  ]
}
```
