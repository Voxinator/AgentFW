# AgentFW v9.1.0 release documentation and publication

## Scope and controls

- Promote the completed r9.x improvements to the backward-compatible minor release `v9.1.0`.
- Update current release documentation and metadata without rewriting historical v9.0.0 records.
- Run deterministic release tests only. Per the maintainer's standing constraint, do not run
  golden-task, behavioral-evaluation, or additional Layer-2 plan-critic rounds; this is a named
  relaxation of the normal A3 Layer-2 gate. Layer 1, producer tests, and fresh independent
  verification remain mandatory.
- Capability preflight: shell and isolated agents are available. The live Codex configuration uses
  `danger-full-access` with approvals disabled, so deterministic permissions are not configured.
  Degradation: scope edits to the repository, keep the human-requested push to a normal
  fast-forward of `main`, and prohibit force push, tag mutation, release creation, configuration
  changes, installs, and unrelated filesystem/network effects.
- Commit inventory includes the v9.1 implementation, tests/fixtures, release docs, harness
  plan/evidence, and the linked Bonksnake provenance chain. No tag or GitHub Release is created by
  this task.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A3",
  "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "Current project metadata and adopter-facing documentation identify AgentFW v9.1.0 as the current backward-compatible minor release."},
    {"id": "R2", "text": "The changelog and v9.1 release notes accurately summarize C-1 through C-6, schema 1.3, deterministic evidence, and the explicit absence of new behavioral evaluation rounds."},
    {"id": "R3", "text": "Current roadmap documentation no longer reserves r9.1 for the deferred ChatGPT Work adapter; that candidate moves to a future minor release without rewriting historical records."},
    {"id": "R4", "text": "The r9.x candidate list records all six candidates implemented and verified, and its linked Bonksnake plan/prompt provenance is included without claiming the halted build executed."},
    {"id": "R5", "text": "The release documentation remains internally linked and the full deterministic test suite stays green."},
    {"id": "R6", "text": "One scoped release commit is created on main and pushed to origin/main by normal fast-forward, with no tag, force push, or unrelated file inclusion."}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Version and release documentation",
      "deps": [],
      "contract": {
        "requirement_ids": ["R1", "R2", "R3", "R4", "R5"],
        "criteria": "metadata.json reports version 9.1.0/revision r9.1; README and current install/profile docs consistently describe v9.1.0 and move the deferred ChatGPT Work adapter to a future minor; CHANGELOG and RELEASE-NOTES-v9.1.0.md describe the six improvements and deterministic evidence without claiming a new behavioral evaluation; R9X-CANDIDATES marks C-1 through C-6 implemented and verified; all linked provenance documents are present; deterministic validator, installer, link, and capability checks pass.",
        "acceptance_command": "bash tools/tests/release-v9.1.sh",
        "expected_signal": "terminal line exactly RELEASE_V9_1_OK with exit 0",
        "environment": "macOS repository shell with Bash and Python 3; no network",
        "evidence": "evidence/release-v9.1.log produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "risk": "A stale current-version or roadmap claim could make the release identity inconsistent even when implementation tests pass.",
        "negative_cases": [
          "A metadata version other than 9.1.0 makes the release gate red.",
          "A current document still reserving r9.1 for the deferred adapter makes the release gate red.",
          "Any candidate left proposed or any missing linked provenance document makes the release gate red.",
          "A deterministic validator, installer, link, or capability regression makes the release gate red."
        ],
        "mutation_probes": [
          {"mutation": "On a scratch copy, revert metadata.json version to 9.0.0 and confirm the release gate exits nonzero.", "expected": "red"},
          {"mutation": "On a scratch copy, restore the current README claim that the deferred adapter is reserved for r9.1 and confirm the release gate exits nonzero.", "expected": "red"}
        ],
        "rerunnable": true,
        "constraints": {"allowed_paths": ["README.md", "CHANGELOG.md", "DESIGN.md", "metadata.json", "RELEASE-NOTES-v9.1.0.md", "R9X-CANDIDATES.md", "profiles/chatgpt-projects.md", "adapters/claude-code/INSTALL.md", "adapters/codex/INSTALL.md", "tools/tests/release-v9.1.sh", "evidence/release-v9.1.log"], "forbidden": ["network", "git commit", "git push", "tag creation", "GitHub Release", "user configuration"]}
      }
    },
    {
      "id": "T2",
      "title": "Commit and fast-forward publication",
      "deps": ["T1"],
      "contract": {
        "requirement_ids": ["R6"],
        "criteria": "After independent verification, the intended v9.1 inventory is staged explicitly, one release commit is created on main, origin/main is fetched immediately before publication, the push is refused unless it is a normal fast-forward, and after push local HEAD equals origin/main with a clean worktree. No tag or GitHub Release is created.",
        "acceptance_command": "bash -c 'set -euo pipefail; test \"$(git branch --show-current)\" = main; test -z \"$(git status --porcelain)\"; test \"$(git rev-parse HEAD)\" = \"$(git rev-parse origin/main)\"; subject=$(git log -1 --format=%s); grep -q \"AgentFW v9.1.0\" <<<\"$subject\" && echo PUBLISH_V9_1_OK'",
        "expected_signal": "terminal line exactly PUBLISH_V9_1_OK with exit 0",
        "environment": "Git repository on main with authenticated origin GitHub remote; network only for fetch and normal push",
        "evidence": "terminal git commit/fetch/push output produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": ["production_only"],
        "risk": "An unintended file could be published, or a stale remote could cause a rejected/non-fast-forward publication attempt.",
        "negative_cases": [
          "Any path outside the reviewed release inventory blocks staging.",
          "Any origin/main divergence blocks the push rather than invoking force.",
          "A dirty worktree or mismatched local/remote HEAD keeps the publication contract red."
        ],
        "mutation_probes": [
          {"mutation": "In a disposable repository, add an unreviewed path to the candidate inventory and confirm the explicit inventory check rejects it.", "expected": "red"}
        ],
        "rerunnable": true,
        "constraints": {"allowed_effects": ["git add explicit reviewed paths", "one git commit on main", "git fetch origin main", "normal git push origin main"], "forbidden": ["force push", "history rewrite", "tag creation/deletion", "GitHub Release", "branch deletion", "unrelated file staging"]}
      }
    }
  ]
}
```
