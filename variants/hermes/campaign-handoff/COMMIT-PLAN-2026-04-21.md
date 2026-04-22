---
type: commit plan for r7.5-hermes-prerelease campaign-arc update
date: 2026-04-21
scope: Option A — annotate campaign-arc on main; no new tag
---
# Commit plan — post-r7.8 campaign arc → pre-release annotation

## Scope

- Update main branch with r7.6/7.7/7.8 campaign arc findings.
- Leave `r7.5-hermes-prerelease` tag untouched (immutable on GitHub).
- r7.5 pre-release on GitHub gets an updated **release description** (manual operator step via `gh release edit`).
- No new tag. No push without operator review.

---

## Files prepared by this worker (ready for operator review + staging)

### Net new files

- `variants/hermes/CEILING-FINDING-r7.8.md` — standalone substrate-ceiling finding doc (~800 words).
- `variants/hermes/RELEASE-NOTES-r7.5-hermes-prerelease.md` — main-branch copy of r7.5 release notes + campaign-arc addendum section. (The original release-notes file remains archived at `variants/hermes/archive/r7.5-prerelease-2026-04-19/RELEASE-NOTES-r7.5-hermes-prerelease.md`.)
- `variants/hermes/campaign-handoff/COMMIT-PLAN-2026-04-21.md` — this file.

### Edited existing files

- `variants/hermes/PROBE-RESULTS-r7.md` — appended §19 (r7.5 pre-release + worker-quality gate), §20 (r7.6 HWO campaign), §21 (r7.7 Path A), §22 (r7.8 T1 + ceiling finding), §23 (campaign-arc aggregate table). Revision history entry added.
- `variants/hermes/NEXT-STEPS.md` — rewrote for post-r7.8 state. Points to `campaign-handoff/HANDOFF-post-r7.8.md` as source of truth. One paragraph each on options α/β/γ/δ. Constraints + methodology rules + first-5-minutes checklist carried from handoff.
- `CHANGELOG.md` — new `r7.5-campaign-arc (2026-04-21, post-tag) — HOLD` entry above the existing r7.5 entry.

### Files NOT touched (deliberately, per constraints)

- `variants/hermes/HERMES.md` (canonical, md5 `0780c232…` — must stay frozen).
- `variants/hermes/HERMES-variantF.md` (already drifted +1 line from r7.6 Fix 4; drift is annotated in the release notes addendum and PROBE-RESULTS §20; no further edits).
- `variants/hermes/delegate_worker_v2.py` (already drifted +64 env-gated lines from r7.7 A1; drift is annotated; no further edits).
- `variants/hermes/HERMES-variantB.md`, `-variantD.md`, `-variantE.md`, `IMPLEMENTATION.md`, `INSTALL.md`, `DEPENDENCIES.md`, `DESIGN.md` (canonical for r7.5; no changes needed for Option A).
- `core/`, `references/`, `templates/`, `playbooks/`, `evaluation/` (framework-level canonical; no Hermes commentary).
- `README.md`, `metadata.json` (no framework-level version bump for a HOLD addendum).

---

## Suggested commit sequence

### Commit 1: variants/hermes/ doc updates

Files:
- `variants/hermes/PROBE-RESULTS-r7.md` (§19-§23 appended + revision history)
- `variants/hermes/NEXT-STEPS.md` (rewritten for post-r7.8)
- `variants/hermes/CEILING-FINDING-r7.8.md` (new)
- `variants/hermes/RELEASE-NOTES-r7.5-hermes-prerelease.md` (new at variant root; archive copy preserved)

Suggested message:

```
Hermes: document r7.6/7.7/7.8 campaign arc + substrate-ceiling finding

Three post-r7.5 campaigns (r7.6 HWO scaffold, r7.7 A1+A2 structural,
r7.8 T1 generation-layer) all landed HOLD on worker quality. r7.8
ablation established vanilla MoE = ~20% on T4-T5-T6-T10 eval; all
tested agentic-layer interventions land within 1-2σ noise band at
n=20. Per r7.7 S9 autopsy + r7.8-P1a: ~2/3 of FAILs are generation-
layer, not agentic-layer.

r7.5-hermes-prerelease tag remains the operator-facing milestone.
No canonical framework changes. Updates scoped under variants/hermes/.

- PROBE-RESULTS-r7.md §19-§23 — campaign-arc record
- CEILING-FINDING-r7.8.md (new) — standalone ceiling-finding doc
- NEXT-STEPS.md — rewrite pointing to campaign-handoff/HANDOFF-post-r7.8.md
- RELEASE-NOTES-r7.5-hermes-prerelease.md (new at variant root) —
  main-branch copy + campaign-arc addendum section

See variants/hermes/campaign-handoff/HANDOFF-post-r7.8.md for the
r7.9 option framing (α substrate / β generation-layer / γ broader
eval / δ combined).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Commit 2: framework CHANGELOG

Files:
- `CHANGELOG.md` (new `r7.5-campaign-arc` entry above r7.5)

Suggested message:

```
CHANGELOG: add r7.5 Hermes campaign-arc addendum entry

Three post-tag campaigns (r7.6/7.7/7.8) on Hermes variant all HOLD.
Pointer to variants/hermes/CEILING-FINDING-r7.8.md + full record.
No canonical framework changes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Commit 3 (optional — operator choice): commit plan + audit artifact

Files:
- `variants/hermes/campaign-handoff/COMMIT-PLAN-2026-04-21.md` (this file)
- `variants/hermes/campaign-handoff/ARTIFACT-doc-audit-2026-04-21.md` (if not already tracked)

Suggested message:

```
Hermes: commit doc audit + commit plan for r7.5 campaign-arc update

Historical record of the 2026-04-21 doc audit and the commit plan
that produced the campaign-arc annotation on main. Useful for future
sessions picking up r7.9 cold — they can see what was decided and why.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Commit 4 (operator choice): handoff + morning summaries + S9 ship judges

The following campaign artifacts are currently tracked on disk under `variants/hermes/` (already relocated from repo root in the 2026-04-21 cleanup). If the operator wants them captured in git as part of the campaign-arc record:

Files:
- `variants/hermes/campaign-handoff/HANDOFF-post-r7.8.md` (authoritative r7.9 decision doc)
- `variants/hermes/campaign-handoff/MORNING-SUMMARY-latest.md` (symlink to r7.8 morning summary)
- `variants/hermes/archive/r7.6-campaign-2026-04-20/ARTIFACT-r7.6-MORNING-SUMMARY.md`
- `variants/hermes/archive/r7.6-campaign-2026-04-20/CALIBRATION-r7.6-judge-protocol.md`
- `variants/hermes/archive/r7.7-campaign-2026-04-20/ARTIFACT-r7.7-MORNING-SUMMARY.md`
- `variants/hermes/archive/r7.7-campaign-2026-04-20/artifacts/ARTIFACT-r7.7-S9-ship-judge.md`
- `variants/hermes/archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md`

Verify with `git status` which of these are untracked vs already tracked; stage only untracked.

Suggested message:

```
Hermes: commit campaign-arc handoff + morning summaries + ship judges

Preserves the load-bearing top-of-campaign artifacts for r7.6/7.7/7.8.
Per-trial verdicts and per-phase process artifacts are left archived
locally (not committed) to keep the repo lean.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### Commit 5 (operator choice): archive data disposition

The full `archive/r7.{6,7,8}-campaign-*/` trees contain ~290 per-trial + per-phase files. Options:

- **(a) Commit them all** — preserves research trail in git. Biggest bloat.
- **(b) Exclude via .gitignore pattern + keep Mac-local for reference.** Recommended.
- **(c) Commit only the top-level per-campaign morning summaries + index files** (covered by Commit 4 above).

**Recommendation: (b).** Individual trial JSONs + per-trial verdicts are dense research artifacts; keep them archived locally but don't bloat the repo. The CEILING-FINDING, morning summaries, and handoff carry the signal. If (b) is chosen, extend `.gitignore` to match:

```
variants/hermes/archive/r7.6-campaign-2026-04-20/judge-verdicts/
variants/hermes/archive/r7.6-campaign-2026-04-20/batch-trials/
variants/hermes/archive/r7.6-campaign-2026-04-20/artifacts/
variants/hermes/archive/r7.6-campaign-2026-04-20/plans/
variants/hermes/archive/r7.6-campaign-2026-04-20/tmp-archive/
variants/hermes/archive/r7.7-campaign-2026-04-20/judge-verdicts/
variants/hermes/archive/r7.7-campaign-2026-04-20/batch-trials/
variants/hermes/archive/r7.7-campaign-2026-04-20/artifacts/
variants/hermes/archive/r7.7-campaign-2026-04-20/plans/
variants/hermes/archive/r7.7-campaign-2026-04-20/tmp-archive/
variants/hermes/archive/r7.8-campaign-2026-04-21/judge-verdicts/
variants/hermes/archive/r7.8-campaign-2026-04-21/batch-trials/
variants/hermes/archive/r7.8-campaign-2026-04-21/artifacts/
variants/hermes/archive/r7.8-campaign-2026-04-21/plans/
variants/hermes/archive/r7.8-campaign-2026-04-21/tmp-archive/
variants/hermes/archive/r7.8-campaign-2026-04-21/research/
variants/hermes/archive/r7.8-campaign-2026-04-21/vet-logs/
variants/hermes/archive/r7.6-campaign-2026-04-20/PROGRESS-r7.6.md
variants/hermes/archive/r7.7-campaign-2026-04-20/PROGRESS-r7.7.md
variants/hermes/archive/r7.8-campaign-2026-04-21/PROGRESS-r7.8.md
```

(Add alongside existing `.gitignore` patterns; confirm by reviewing `.gitignore` before appending.)

---

## GitHub release update (operator manual step)

After push:

```
gh release view r7.5-hermes-prerelease
# Review existing description

gh release edit r7.5-hermes-prerelease \
  --notes-file variants/hermes/RELEASE-NOTES-r7.5-hermes-prerelease.md
```

This updates the **release description** on GitHub without retagging. The underlying commit + tag stay immutable.

---

## Pre-push checklist

- [ ] `git status` shows expected new files + edits only; no unexpected modifications to canonical framework files.
- [ ] `grep -rn '<raw-key>' . --exclude-dir=.git --exclude-dir=.claude` = 0 matches. (Pre-commit secret-scan tripwire; operator knows the literal to grep for.)
- [ ] Tripwire files unchanged: `variants/hermes/HERMES.md`, `SKILL.md` (operator's Hermes install, not in this repo), `jira-briefing.sh`, `useDashboard.ts`.
- [ ] `git diff variants/hermes/HERMES.md` = empty (canonical untouched).
- [ ] `git diff variants/hermes/HERMES-variantF.md` = pre-existing r7.6 drift only (not re-edited by this worker).
- [ ] `git diff variants/hermes/delegate_worker_v2.py` = pre-existing r7.7 drift only.
- [ ] `git log r7.5-hermes-prerelease..HEAD` shows only the commits listed above.
- [ ] No `OMLX_API_KEY` values or `/tmp/r7.*-env.sh` content in any staged file.
- [ ] `core/`, `references/`, `templates/`, `playbooks/`, `evaluation/` untouched.
- [ ] No changes to non-Hermes variants (`variants/claude-code/`, `variants/claude-projects/`, `variants/generic/`).

---

## What the operator does next

1. Review this plan + the 4 updated/new files (PROBE-RESULTS-r7.md, NEXT-STEPS.md, CEILING-FINDING-r7.8.md, RELEASE-NOTES-r7.5-hermes-prerelease.md) + CHANGELOG.md.
2. Decide on Commits 3/4/5 (optional: commit plan itself, handoff+summaries, archive-gitignore).
3. Stage and commit per the sequence above.
4. Run the pre-push checklist.
5. Push to `main`.
6. Run `gh release edit r7.5-hermes-prerelease --notes-file variants/hermes/RELEASE-NOTES-r7.5-hermes-prerelease.md` to update the GitHub release description.
7. Verify on GitHub: tag + underlying commit unchanged; release description updated; addendum section visible.

---

## Not done by this worker (explicitly)

- No staging (`git add`).
- No commits.
- No pushes.
- No GitHub API calls.
- No edits to canonical framework files.
- No edits to the two drifted tracked files (HERMES-variantF.md, delegate_worker_v2.py).
- No new tag.
- No changes to `README.md` or `metadata.json` (per constraint: framework-level version bump not warranted for a HOLD addendum).

Operator decides + executes all of the above. This worker's output is files-on-disk + this plan.
