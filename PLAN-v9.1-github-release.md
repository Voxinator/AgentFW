# AgentFW v9.1.0 GitHub release

## Scope and controls

- Expand README's v9.1 section into an explicit six-fix list.
- Commit and fast-forward push that documentation/test update to `main`.
- Create annotated tag `v9.1.0` on the verified release commit, push that tag normally, and create
  a public, non-draft, non-prerelease GitHub Release using `RELEASE-NOTES-v9.1.0.md`.
- This plan supersedes only the publication boundary of `PLAN-v9.1-release.md`; that earlier plan's
  explicit no-tag scope remains a truthful record of the completed commit-only task.
- Per maintainer constraint: deterministic tests and one fresh independent verifier only—no
  golden-task, behavioral-evaluation, or Layer-2 plan-critic rounds. This is a named relaxation of
  the A3 semantic-plan gate, not of producer or independent verification.
- Live Codex permissions remain unconfigured (`danger-full-access`, approvals disabled).
  Degradation: repository-only edits, normal fast-forward Git operations, no force/history rewrite,
  no tag deletion/move, and GitHub effects limited to creating this one tag and Release.

```json agentfw-plan
{
  "version": "1.3",
  "assurance": "A3",
  "required_plan_review_tier": "dual",
  "requirements": [
    {"id": "R1", "text": "README's What's new in v9.1 section presents C-1 through C-6 as six explicit, adopter-readable fixes rather than one compressed paragraph."},
    {"id": "R2", "text": "The README expansion preserves the deterministic-evidence and no-new-behavioral-evaluation boundaries and keeps all release gates green."},
    {"id": "R3", "text": "A final scoped documentation commit is fast-forward pushed to origin/main before tagging."},
    {"id": "R4", "text": "Annotated tag v9.1.0 points exactly at the verified origin/main release commit locally and remotely."},
    {"id": "R5", "text": "GitHub Release v9.1.0 is public, non-draft, non-prerelease, targets tag v9.1.0, is titled AgentFW v9.1.0, and uses the committed release notes."}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "Expand README v9.1 fixes",
      "deps": [],
      "contract": {
        "requirement_ids": ["R1", "R2"],
        "criteria": "README's v9.1 section has six distinct bullets, one each for acceptance-command red paths/lint, schema 1.3 mutation probes, fixture hygiene, empirical critics, cap relaxations, and command-resolution evidence; it retains links to R9X-CANDIDATES and RELEASE-NOTES-v9.1.0, says schema 1.3 is additive, and does not claim new behavioral evaluation. The release gate mechanically asserts the six bullets and all deterministic suites pass.",
        "acceptance_command": "bash -c 'set -euo pipefail; for c in C-1 C-2 C-3 C-4 C-5 C-6; do grep -q -- \"- \\\\*\\\\*$c\" README.md; done; bash tools/tests/release-v9.1.sh && echo README_V9_1_FIXES_OK'",
        "expected_signal": "terminal line exactly README_V9_1_FIXES_OK with exit 0",
        "environment": "macOS repository shell with Bash and Python 3; no network",
        "evidence": "evidence/release-v9.1-readme.log produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": [],
        "risk": "A compressed or incomplete README could omit a shipped fix or overstate evidence even while the detailed release notes are correct.",
        "negative_cases": [
          "Removing any one of the six named README fixes makes the release gate red.",
          "Removing the release-note or candidate link makes the release gate red.",
          "Reintroducing a fresh-behavioral-evidence claim makes the release gate red."
        ],
        "mutation_probes": [
          {"mutation": "On a scratch copy, remove the C-6 command-resolution README bullet and confirm the release gate exits nonzero.", "expected": "red"}
        ],
        "rerunnable": true,
        "constraints": {"allowed_paths": ["README.md", "tools/tests/release-v9.1.sh", "evidence/release-v9.1-readme.log"], "forbidden": ["network", "git commit", "git push", "tag", "GitHub Release", "user configuration"]}
      }
    },
    {
      "id": "T2",
      "title": "Commit, tag, and GitHub Release",
      "deps": ["T1"],
      "contract": {
        "requirement_ids": ["R3", "R4", "R5"],
        "criteria": "After independent verification, explicitly stage only README.md, tools/tests/release-v9.1.sh, evidence/release-v9.1-readme.log, and this plan; create one commit on main and normal-push it after a fresh divergence check; create annotated tag v9.1.0 on that exact clean HEAD and normal-push the tag; create one public non-draft non-prerelease GitHub Release titled AgentFW v9.1.0 using the committed RELEASE-NOTES-v9.1.0.md; verify main, tag, and Release all resolve to the same commit.",
        "acceptance_command": "bash -c 'set -euo pipefail; test -z \"$(git status --porcelain)\"; test \"$(git rev-parse HEAD)\" = \"$(git rev-parse origin/main)\"; test \"$(git rev-list -n 1 v9.1.0)\" = \"$(git rev-parse HEAD)\"; remote=$(git ls-remote origin refs/tags/v9.1.0^{}); remote_commit=${remote%%[[:space:]]*}; test \"$remote_commit\" = \"$(git rev-parse HEAD)\"; draft=$(gh release view v9.1.0 --repo Voxinator/AgentFW --json isDraft --jq .isDraft); prerelease=$(gh release view v9.1.0 --repo Voxinator/AgentFW --json isPrerelease --jq .isPrerelease); name=$(gh release view v9.1.0 --repo Voxinator/AgentFW --json name --jq .name); tag=$(gh release view v9.1.0 --repo Voxinator/AgentFW --json tagName --jq .tagName); url=$(gh release view v9.1.0 --repo Voxinator/AgentFW --json url --jq .url); test \"$draft\" = false; test \"$prerelease\" = false; test \"$name\" = \"AgentFW v9.1.0\"; test \"$tag\" = v9.1.0; test -n \"$url\" && echo GITHUB_RELEASE_V9_1_OK'",
        "expected_signal": "terminal line exactly GITHUB_RELEASE_V9_1_OK with exit 0",
        "environment": "Authenticated GitHub CLI as Voxinator; clean main synchronized with origin; network limited to Git fetch/push and gh release create/view",
        "evidence": "terminal commit, fetch, tag, push, gh release create, and gh release view output produced_after_change",
        "integration_seam": true,
        "risk_class": "standard",
        "required_verification_tier": "independent",
        "failure_surfaces": ["production_only"],
        "risk": "The public tag or GitHub Release could target the wrong commit, expose incomplete notes, or publish before the README fix is verified.",
        "negative_cases": [
          "Any local/remote main divergence blocks commit publication.",
          "Any tag target different from verified HEAD blocks Release creation.",
          "Any existing tag or Release blocks creation rather than being moved or overwritten.",
          "Any draft/prerelease/name/tag mismatch keeps final verification red."
        ],
        "mutation_probes": [
          {"mutation": "In a disposable repository, place annotated tag v9.1.0 on the parent commit and confirm the tag-target equality check exits nonzero.", "expected": "red"}
        ],
        "rerunnable": true,
        "constraints": {"allowed_effects": ["one scoped commit and normal push to main", "one annotated v9.1.0 tag and normal tag push", "one public GitHub Release v9.1.0", "read-only GitHub verification"], "forbidden": ["force push", "history rewrite", "tag move/delete", "release overwrite/delete", "branch deletion", "unrelated staging"]}
      }
    }
  ]
}
```
