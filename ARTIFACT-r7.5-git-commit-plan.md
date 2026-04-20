[TASK CLASS: structured]
Justification: Git commit plan for r7.5-hermes-prerelease; classifies every untracked/modified file and specifies the commit command sequence. Produced under a git-read-only worker scope — no git state changes made by this worker.

# ARTIFACT — r7.5 git commit plan

**Author:** git-preparation worker (read-only git scope)
**Date:** 2026-04-19
**Session branch:** main
**Remote:** origin = https://github.com/Voxinator/AgentFW.git

---

## Summary

- Total files classified: **74** (2 modified-tracked, 72 untracked entries including 2 archive directories)
- **COMMIT:** 64 files (2 modified, 62 untracked — of which 2 are archive directories containing 21 + 29 = 50 files total)
- **LEAVE-LOCAL:** 5 files (PROGRESS.md, HANDOFF-*.md, 2× wrapper `.pre-*-orig` backups, PLAN-openspec-interop.md)
- **GITIGNORE-ADD:** 4 new pattern categories (PROGRESS.md, HANDOFF-*.md / SESSION*.md, `*.pre-*-orig` / `*.probe-*-orig`, `/tmp/probe-*`)
- **BLOCKER:** 1 secret-scan hit (live oMLX API key `<REDACTED>` in `archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md`). MUST be redacted or the file must be excluded before any commit fires. Details in Secret Scan section.

### Deviations from handoff spec

The handoff's suggested commit command sequence references several files that **do not currently exist** in the working tree. The planner should reconcile with D1 before executing:

| Handoff-referenced file | Exists? | Action |
|--|--|--|
| `variants/hermes/INSTALL.md` | NO | D1 did not deliver. Either create or drop from stage list. |
| `variants/hermes/DEPENDENCIES.md` | NO | D1 did not deliver. Either create or drop from stage list. |
| `RELEASE-NOTES-r7.5-hermes-prerelease.md` | NO | D1 did not deliver. The commit message references it — either create or rewrite the message. |
| `probe-variantE-stage.sh` | NO | Never existed. Drop from stage list. |
| `metadata.json` edit | **NO edit pending** | `metadata.json` is tracked and currently unmodified. Nothing to stage unless D1 revisits. |

The commit plan below reflects the **actual working-tree state** as of 2026-04-19. If the operator wants the three missing docs (INSTALL, DEPENDENCIES, RELEASE-NOTES) before the tag, they should dispatch a doc-writing worker first and have this worker re-run.

---

## Classification table

Legend: **C** = COMMIT, **LL** = LEAVE-LOCAL (working tree only, not this commit), **GI** = matched by gitignore-pattern-add (will be silently ignored going forward).

### Tracked modifications

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 1 | `CHANGELOG.md` | M | **C** | Adds r7.1, r7.2, r7.3, r7.4 release notes. Ship-required. |
| 2 | `README.md` | M | **C** | +25/-4 lines, consistent with changelog update. Ship-required. |

### Untracked — `.gitignore` (this worker's edit)

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 3 | `.gitignore` | M (by this worker) | **C** | Adds session-state + backup patterns. Must ship with the commit to prevent accidental future commits of PROGRESS.md etc. |

### Untracked — release/docs

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 4 | `variants/hermes/DESIGN.md` | ?? | **C** | Durable design spec for the Hermes variant. |
| 5 | `variants/hermes/IMPLEMENTATION.md` | ?? | **C** | Ship doc — install/activate/rollback for the Hermes VM. |
| 6 | `variants/hermes/NEXT-STEPS.md` | ?? | **C** | Session-handoff doc rolled into release as the forward plan. |
| 7 | `variants/hermes/HERMES-variantB.md` | ?? | **C** | Sibling variant preserved for re-probe. |
| 8 | `variants/hermes/HERMES-variantD.md` | ?? | **C** | Ship-candidate sibling (r7 era). |
| 9 | `variants/hermes/HERMES-variantE.md` | ?? | **C** | Sibling variant (r7.3 escape-hatch-stripped). |
| 10 | `variants/hermes/HERMES-variantF.md` | ?? | **C** | β-fuse variant (r7.4 / r7.5). Core ship artifact. |
| 11 | `variants/hermes/PROBE-RESULTS-r7.md` | ?? | **C** | Consolidated campaign history. |
| 12 | `variants/hermes/PLAN-flywheel-openspec-prospect.md` | ?? | **C** | Forward-looking design explored during r7.x. Durable. |
| 13 | `variants/hermes/delegate_worker.py` | ?? | **C** | v1 tool (deprecated but retained side-by-side). Ship-required. |
| 14 | `variants/hermes/delegate_worker_v2.py` | ?? | **C** | β-fuse tool. Core ship artifact. |

### Untracked — r7.4 ARTIFACT evidence (all COMMIT)

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 15 | `ARTIFACT-r7.4-p1-judge-verdict.md` | ?? | **C** | Campaign evidence. |
| 16 | `ARTIFACT-r7.4-p1-terminal-binding.md` | ?? | **C** | Campaign evidence. |
| 17 | `ARTIFACT-r7.4-phase-a-impl-notes.md` | ?? | **C** | Campaign evidence. |
| 18 | `ARTIFACT-r7.4-phase-c-judge-verdict.md` | ?? | **C** | Campaign evidence. |
| 19 | `ARTIFACT-r7.4-phase-d-dense-gapfill.md` | ?? | **C** | Campaign evidence. |
| 20 | `ARTIFACT-r7.4-phase-d-dense-results.md` | ?? | **C** | Campaign evidence. |
| 21 | `ARTIFACT-r7.4-phase-d-moe-results.md` | ?? | **C** | Campaign evidence. |
| 22 | `ARTIFACT-r7.4-ship-judge-verdict.md` | ?? | **C** | HOLD verdict (v1) — historical. |
| 23 | `ARTIFACT-r7.4-ship-judge-verdict-v2.md` | ?? | **C** | Authoritative SHIP-WITH-CAVEAT verdict. |
| 24 | `ARTIFACT-r7.4-sigterm-research.md` | ?? | **C** | SIGTERM diagnosis — durable technical note. |

### Untracked — r7.5 ARTIFACT evidence (all COMMIT)

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 25 | `ARTIFACT-r7.5-A1-impl-notes.md` | ?? | **C** | Campaign evidence. |
| 26 | `ARTIFACT-r7.5-A2-judge-verdict.md` | ?? | **C** | Campaign evidence. |
| 27 | `ARTIFACT-r7.5-B1-impl-notes.md` | ?? | **C** | Campaign evidence. |
| 28 | `ARTIFACT-r7.5-B2-impl-notes.md` | ?? | **C** | Campaign evidence. |
| 29 | `ARTIFACT-r7.5-F1-judge-brief.md` | ?? | **C** | Judge brief (forward-defining). |
| 30 | `ARTIFACT-r7.5-F2-probe-results.md` | ?? | **C** | Probe results. |
| 31 | `ARTIFACT-r7.5-SHIP-judge-verdict.md` | ?? | **C** | Ship-gate verdict. |
| 32 | `ARTIFACT-r7.5-phase3-smoke-verdict.md` | ?? | **C** | Phase-3 smoke verdict. |
| 33–52 | `ARTIFACT-r7.5-worker-quality-trial-{01..20}.md` | ?? | **C** (20 files) | Per-trial quality rubric — the evidence trail the worker-quality gate is measured on. |

### Untracked — probe infrastructure (all COMMIT unless noted)

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 53 | `probe-omlx-health-check.sh` | ?? | **C** | Probe infra. |
| 54 | `probe-r7.3-l1-driver.sh` | ?? | **C** | Probe infra. |
| 55 | `probe-r7.3-l1-firsttool.py` | ?? | **C** | Probe infra. |
| 56 | `probe-reproducibility.md` | ?? | **C** | Reproducibility doc — durable. |
| 57 | `probe-swap.sh` | ?? | **C** | Probe infra (variant swap helper). |
| 58 | `probe-tasks.md` | ?? | **C** | Task bank for probes — durable. |
| 59 | `probe-variantD-stage.sh` | ?? | **C** | Probe infra. |
| 60 | `probe-variantE-check.py` | ?? | **C** | Probe infra. |
| 61 | `probe-variantE-wrapper.sh` | ?? | **C** | Probe infra. |
| 62 | `probe-variantE-wrapper.sh.pre-r7.3-l2-orig` | ?? | **LL + GI** | Session-local one-time backup. Matched by new pattern `*.pre-*-orig`. |
| 63 | `probe-variantE-wrapper.sh.pre-r7.3-orig` | ?? | **LL + GI** | Session-local one-time backup. Matched by new pattern `*.pre-*-orig`. |
| 64 | `probe-variantF-check.py` | ?? | **C** | Probe infra. |
| 65 | `probe-variantF-stage.sh` | ?? | **C** | Probe infra. |
| 66 | `probe-variantF-wrapper.sh` | ?? | **C** | Probe infra. |
| 67 | `probe-variantG-check.py` | ?? | **C** | Probe infra (r7.5 v2.1 turn-0 toolset variant). |
| 68 | `probe-variantG-stage.sh` | ?? | **C** | Probe infra. |
| 69 | `probe-variantG-wrapper.sh` | ?? | **C** | Probe infra. |

### Untracked — plans

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 70 | `PLAN-r7.4-wrapper-sigterm-fix-design.md` | ?? | **C** | Durable design doc for r7.4. |
| 71 | `PLAN-r7.5.md` | ?? | **C** | Durable plan for the r7.5 campaign. |
| 72 | `PLAN-hermes-harness-probe.md` | ?? | **C** | Pre-dates r7.4 but is the original campaign charter — durable context for the probe infrastructure that ships. |
| 73 | `PLAN-openspec-interop.md` | ?? | **LL** | Speculative OpenSpec-interop design. Not tied to r7.x campaign. Keep local; ship in a future commit when/if pursued. |

### Untracked — session state (LEAVE-LOCAL)

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 74 | `PROGRESS.md` | ?? | **LL + GI** | Session tracker. Per hard rule: never commit. Matched by new pattern. |
| 75 | `HANDOFF-2026-04-19.md` | ?? | **LL + GI** | Session handoff doc. Per hard rule: never commit. Matched by new pattern `HANDOFF-*.md`. |

### Untracked — other docs

| # | File | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 76 | `ARTIFACT-doc-verifier-judgment.md` | ?? | **C** | Doc-verifier judgment on release docs. Campaign evidence. |

### Untracked — archive directories

| # | Path | State | Classification | Rationale |
|---|------|-------|----------------|-----------|
| 77 | `archive/hermes-probe-r7-2026-04-18/` (21 files) | ?? | **C** — see BLOCKER | Raw evidence from r7.0/r7.1 sweep. SEE SECRET SCAN: one file in this directory contains the live oMLX API key. MUST redact or exclude before commit. |
| 78 | `archive/hermes-probe-r7.2-r7.3-2026-04-18/` (29 files) | ?? | **C** | Raw evidence from r7.2/r7.3 sweep. Secret scan clean. Commit wholesale. |

---

## Secret scan

**Patterns checked (case-insensitive) across the entire working tree:**
- Literal: `<REDACTED>` (the operator's local oMLX API key per CLAUDE.md hard rule)
- `Authorization:` / `Bearer ` / `api[_-]?key` / `secret[_-]?key` / `password\s*=`
- AWS access-key pattern `AKIA[0-9A-Z]{16}`
- OpenAI-style secret pattern `sk-[a-zA-Z0-9]{20,}`

### Findings

**CRITICAL — 1 hit to act on:**

- `archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md` line 87:
  ```yaml
  api_key: <REDACTED>
  ```
  This is a literal quote of the operator's live oMLX API key from `~/.hermes/config.yaml`. **MUST NOT be committed in plaintext.** The surrounding context (lines 82–88) is a `~/.hermes/config.yaml` YAML excerpt showing the Parallels host target `http://10.211.55.2:8000/v1`.

**BLOCKER resolution — operator must pick one:**

  **Option A (recommended): redact in place before committing.**
  Single-line edit: replace `  api_key: <REDACTED>` with `  api_key: <REDACTED>` on line 87. One file changes. Rest of archive commits wholesale. Low risk — the surrounding prose doesn't depend on the literal key.

  **Option B: exclude just that one file from the archive commit.**
  `git add archive/hermes-probe-r7-2026-04-18` includes everything; to exclude, stage individually. More commands, same outcome, but leaves the secret in the local working tree.

  **Option C: gitignore the entire `archive/hermes-probe-r7-2026-04-18/` directory.**
  Simplest but loses 20 legitimate evidence files from the release. Not recommended.

  **Do NOT proceed with commit until the operator chooses.** This plan's commit sequence (below) assumes **Option A** and inserts a redaction step before staging.

**Other hits (all benign, no action needed):**

- `ARTIFACT-r7.5-phase3-smoke-verdict.md`, `probe-omlx-health-check.sh`, `PLAN-r7.5.md` — reference `OMLX_API_KEY` as an environment-variable NAME only, no values. CLEAN.
- `archive/hermes-probe-r7.2-r7.3-2026-04-18/ARTIFACT-impl-2-escape-hatch-removal.md` — "Authorization: 'GO GO GO' mandate" — English phrase, not a credential. CLEAN.
- `archive/hermes-probe-r7.2-r7.3-2026-04-18/ARTIFACT-drift-investigation-alpha.md` — mentions `auth.api_key` as a field name in a config object, no value. CLEAN.
- `evaluation/PROBE-r7-runbook.md` — references `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` as env-var NAMES only, no values. Already tracked, not in this commit set regardless. CLEAN.
- `archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md` line 250 — `api_key=effective_api_key` variable assignment, no literal value. CLEAN on its own; in-same-file hit above is the only real finding.

**LAN IP `10.211.55.2`** appears in several archived files (Parallels guest-to-host bridge). This is RFC-private space and a local-only address. Not a secret; safe to ship. (Already referenced in CHANGELOG.md diff, so precedent is established.)

---

## .gitignore delta

**Before:** 5 lines (+1 blank trailing = 6)
**After:** 22 lines (5 original + 1 blank + 16 new)
**Net added:** 16 lines across 4 commented sections.

**Full new content appended:**

```
# Added 2026-04-19 for r7.5-hermes-prerelease — session-state files
# Ephemeral per-conversation artifacts (progress trackers, session handoffs).
# If one of these ever needs to ship, commit with `git add -f <path>`.
PROGRESS.md
HANDOFF-*.md
SESSION_LOG.md
SESSION-*.md

# Probe infrastructure backups — session-local one-time snapshots.
# Naming convention: <script>.pre-<revision>-orig or .probe-*-orig
*.pre-*-orig
*.probe-*-orig

# Local tmp + logs for probe runs
/tmp/probe-*
```

**Patterns added beyond the handoff spec:**
- `SESSION_LOG.md` and `SESSION-*.md` — covered the handoff's hard rule "Anything with the word 'HANDOFF' or 'SESSION' in the filename → LEAVE-LOCAL + gitignore pattern." The handoff only listed `HANDOFF-*.md` explicitly; added the `SESSION` family to satisfy the full rule.

**Files in working tree that will be silently ignored by the new rules going forward:**
- `PROGRESS.md` (currently untracked)
- `HANDOFF-2026-04-19.md` (currently untracked)
- `probe-variantE-wrapper.sh.pre-r7.3-l2-orig` (currently untracked)
- `probe-variantE-wrapper.sh.pre-r7.3-orig` (currently untracked)

None of these are currently tracked, so no `git rm --cached` is needed.

---

## Commit command sequence (for planner to execute AFTER operator sign-off)

> **HARD PREREQUISITES before running any `git add`:**
>
> 1. **Resolve the secret BLOCKER.** Operator chooses Option A/B/C above. Assumed: Option A.
> 2. **Decide on missing D1 deliverables.** If the operator wants `RELEASE-NOTES-r7.5-hermes-prerelease.md`, `variants/hermes/INSTALL.md`, `variants/hermes/DEPENDENCIES.md` shipped with this tag, have a worker create them first and re-run this plan. Otherwise remove their references from the commit message draft below.

```bash
# ──────────────────────────────────────────────────────────────
# Step 0. Operator-gated pre-flight.
# ──────────────────────────────────────────────────────────────

cd /Users/briantaylor/Projects/AgentFW
git status --short   # confirm working tree matches this plan

# ──────────────────────────────────────────────────────────────
# Step 1. REDACT THE LIVE API KEY (Option A from secret scan).
#         Do this as a separate small edit — NOT via this worker.
#         Planner or operator dispatches a minimal sed-equivalent edit:
#         replace `api_key: <REDACTED>` with `api_key: <REDACTED>` in
#         archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md
#
#         Verify the literal key is absent (substitute the actual literal here,
#         not shown to avoid re-introducing it in this artifact):
#         grep -rn "<the-literal-key>" . --exclude-dir=.git --exclude-dir=.claude
#         Expected output: (empty — zero matches)
#
#         Positive verification that redaction was applied:
grep -n "api_key:" archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md
#         Expected output: one line containing "api_key: <REDACTED>"

# ──────────────────────────────────────────────────────────────
# Step 2. Stage tracked modifications.
# ──────────────────────────────────────────────────────────────
git add .gitignore
git add CHANGELOG.md README.md

# ──────────────────────────────────────────────────────────────
# Step 3. Stage Hermes variant deliverables.
# ──────────────────────────────────────────────────────────────
git add variants/hermes/DESIGN.md
git add variants/hermes/IMPLEMENTATION.md
git add variants/hermes/NEXT-STEPS.md
git add variants/hermes/HERMES-variantB.md
git add variants/hermes/HERMES-variantD.md
git add variants/hermes/HERMES-variantE.md
git add variants/hermes/HERMES-variantF.md
git add variants/hermes/PROBE-RESULTS-r7.md
git add variants/hermes/PLAN-flywheel-openspec-prospect.md
git add variants/hermes/delegate_worker.py
git add variants/hermes/delegate_worker_v2.py

# ──────────────────────────────────────────────────────────────
# Step 4. Stage probe infrastructure (explicit — no globs that
#          could pick up *.pre-*-orig or session files).
# ──────────────────────────────────────────────────────────────
git add probe-omlx-health-check.sh
git add probe-r7.3-l1-driver.sh
git add probe-r7.3-l1-firsttool.py
git add probe-reproducibility.md
git add probe-swap.sh
git add probe-tasks.md
git add probe-variantD-stage.sh
git add probe-variantE-check.py
git add probe-variantE-wrapper.sh
git add probe-variantF-check.py
git add probe-variantF-stage.sh
git add probe-variantF-wrapper.sh
git add probe-variantG-check.py
git add probe-variantG-stage.sh
git add probe-variantG-wrapper.sh

# ──────────────────────────────────────────────────────────────
# Step 5. Stage plans.
# ──────────────────────────────────────────────────────────────
git add PLAN-r7.4-wrapper-sigterm-fix-design.md
git add PLAN-r7.5.md
git add PLAN-hermes-harness-probe.md

# ──────────────────────────────────────────────────────────────
# Step 6. Stage r7.4 + r7.5 artifacts.
#         The ARTIFACT-r7.4-*.md and ARTIFACT-r7.5-*.md globs are
#         safe here — every file at these prefixes is expected to commit.
# ──────────────────────────────────────────────────────────────
git add ARTIFACT-r7.4-*.md
git add ARTIFACT-r7.5-*.md
git add ARTIFACT-doc-verifier-judgment.md

# ──────────────────────────────────────────────────────────────
# Step 7. Stage archive directories.
#         NOTE: assumes Option-A redaction completed in Step 1.
# ──────────────────────────────────────────────────────────────
git add archive/hermes-probe-r7-2026-04-18
git add archive/hermes-probe-r7.2-r7.3-2026-04-18

# ──────────────────────────────────────────────────────────────
# Step 8. OPTIONAL: only if D1-reserved docs were created after
#         this plan.
# ──────────────────────────────────────────────────────────────
# git add RELEASE-NOTES-r7.5-hermes-prerelease.md  # only if created
# git add variants/hermes/INSTALL.md                # only if created
# git add variants/hermes/DEPENDENCIES.md           # only if created

# ──────────────────────────────────────────────────────────────
# Step 9. Verify the staged set BEFORE committing.
# ──────────────────────────────────────────────────────────────
git status
git diff --cached --stat
git diff --cached -- archive/hermes-probe-r7-2026-04-18/ARTIFACT-workerC-hermes-live.md \
  | grep -i "api_key"
#         Expected output: line showing "api_key: <REDACTED>" in the staged diff
#         (the literal key must NOT appear — check by grep'ing the staged diff
#          for the literal key itself; substitute the literal in operator shell)

# Confirm LEAVE-LOCAL files remain untracked and NOT staged:
git status --short | grep -E "^(\?\?|M) +(PROGRESS\.md|HANDOFF-|PLAN-openspec-interop\.md|.*\.pre-.*-orig)"
# Expected output: `?? PROGRESS.md` (ignored now — will actually be absent
#                  from output since .gitignore will hide it)
#                  `?? HANDOFF-2026-04-19.md` (ignored — will be absent)
#                  `?? PLAN-openspec-interop.md` (untracked, not ignored)
#                  `?? probe-variantE-wrapper.sh.pre-r7.3-orig` (ignored — absent)
#                  `?? probe-variantE-wrapper.sh.pre-r7.3-l2-orig` (ignored — absent)
# After .gitignore is staged and the new patterns take effect on unstaged files,
# only `PLAN-openspec-interop.md` should still appear as `??` in git status.

# ──────────────────────────────────────────────────────────────
# Step 10. Commit. Message draft in the next section.
# ──────────────────────────────────────────────────────────────
# (see "Commit message (draft)" below — paste into a HEREDOC)

# ──────────────────────────────────────────────────────────────
# Step 11. Tag + push — HOLD pending operator sign-off on the
#          final message AND the tag name.
# ──────────────────────────────────────────────────────────────
# git tag -a r7.5-hermes-prerelease -m "Hermes Variant r7.5 — β-fuse dispatch pre-release"
# git push origin main
# git push origin r7.5-hermes-prerelease
#
# Then on GitHub:
#   - create Release from tag r7.5-hermes-prerelease
#   - mark as PRE-RELEASE
#   - title: "Hermes Variant r7.5 — β-fuse dispatch pre-release"
#   - body: link to RELEASE-NOTES-r7.5-hermes-prerelease.md OR paste the
#           caveats summary from CHANGELOG.md § r7.4 if RELEASE-NOTES
#           doc was not produced
```

---

## Commit message (draft — match prior style of `a6679b7`)

```
Hermes variant r7.5 pre-release — β-fuse dispatch layer validated, worker-quality gate not yet met

Pre-release milestone for the Hermes-Agent variant of AgentFW. Captures
the substantial progress of the r7.2 -> r7.5 probe campaign:

- β-fuse architecture (delegate_worker_v2 tool — required first action
  with classification+justification+goal args) validated on both Gemma-4-31B
  dense (11.5x dispatch lift over r7.3 baseline) and Gemma-4-26B-A4B MoE
  (~17x lift)
- r7.4 variantF: SHIP-WITH-CAVEAT per judge on dispatch gate (MoE 17/20
  strict first-attempt, 100% v2-adoption on compliant, 0 one-shot regression)
- r7.5 v2.1 (turn-0 toolset restriction): dispatch layer intact (MoE 16/20
  strict first-attempt — off by one from r7.4 baseline, within MoE empty-
  first-response noise); NEW worker-quality ship gate introduced (>=15/20
  PASS floor) — NOT MET (3/20 PASS; four failure modes identified as r7.6
  scope: search_files thrash, SIGTERM truncation, pseudo-tool-call text,
  fabrication)
- Full probe infrastructure: probe-variant{D,E,F,G}-* scripts, oMLX
  health check, per-trial worker-quality rubric + judge brief
- Complete evidence trail: per-phase impl notes, judge verdicts, 20
  per-trial quality judgments, campaign history in
  variants/hermes/PROBE-RESULTS-r7.md

STATUS: pre-release. Not production-ready. Worker-quality ship gate is
the remaining bar. See CHANGELOG.md r7.4 section for caveat details.

Cross-model integrity: no changes to core/, references/, playbooks/,
templates/, or non-Hermes variants. All r7.5 work scoped to
variants/hermes/ and probe infrastructure.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

HEREDOC form for the actual invocation:

```bash
git commit -m "$(cat <<'EOF'
Hermes variant r7.5 pre-release — β-fuse dispatch layer validated, worker-quality gate not yet met

Pre-release milestone for the Hermes-Agent variant of AgentFW. Captures
the substantial progress of the r7.2 -> r7.5 probe campaign:

- β-fuse architecture (delegate_worker_v2 tool — required first action
  with classification+justification+goal args) validated on both Gemma-4-31B
  dense (11.5x dispatch lift over r7.3 baseline) and Gemma-4-26B-A4B MoE
  (~17x lift)
- r7.4 variantF: SHIP-WITH-CAVEAT per judge on dispatch gate (MoE 17/20
  strict first-attempt, 100% v2-adoption on compliant, 0 one-shot regression)
- r7.5 v2.1 (turn-0 toolset restriction): dispatch layer intact (MoE 16/20
  strict first-attempt — off by one from r7.4 baseline, within MoE empty-
  first-response noise); NEW worker-quality ship gate introduced (>=15/20
  PASS floor) — NOT MET (3/20 PASS; four failure modes identified as r7.6
  scope: search_files thrash, SIGTERM truncation, pseudo-tool-call text,
  fabrication)
- Full probe infrastructure: probe-variant{D,E,F,G}-* scripts, oMLX
  health check, per-trial worker-quality rubric + judge brief
- Complete evidence trail: per-phase impl notes, judge verdicts, 20
  per-trial quality judgments, campaign history in
  variants/hermes/PROBE-RESULTS-r7.md

STATUS: pre-release. Not production-ready. Worker-quality ship gate is
the remaining bar. See CHANGELOG.md r7.4 section for caveat details.

Cross-model integrity: no changes to core/, references/, playbooks/,
templates/, or non-Hermes variants. All r7.5 work scoped to
variants/hermes/ and probe infrastructure.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**Note on commit-message references:** the handoff's sample referenced `RELEASE-NOTES-r7.5-hermes-prerelease.md`; since that file does not exist in the working tree as of this plan, the draft above points to `CHANGELOG.md r7.4 section` instead. If operator/planner creates the RELEASE-NOTES doc before committing, swap the pointer.

---

## Tag + release sequencing (for planner to confirm with operator)

**Suggested tag:** `r7.5-hermes-prerelease`
- Follows the bare-name convention of existing tags (`r5`, `r6` — confirmed via `git log --format=fuller -3`).
- Adds `-hermes-prerelease` disambiguator since this is Hermes-variant-scoped, not a core AgentFW release.

**Alternative:** `hermes-v0.1-prerelease`
- Cleaner if the operator intends the Hermes variant to track independent semver from AgentFW core going forward.

**Pre-release flag:** YES. This is explicitly pre-release per CHANGELOG ("Not production-ready. Worker-quality ship gate is the remaining bar.").

**Release title suggestion:** `Hermes Variant r7.5 — β-fuse dispatch pre-release`

**Release body:** link to `RELEASE-NOTES-r7.5-hermes-prerelease.md` if created; otherwise, an inline summary drawn from CHANGELOG.md r7.4 section (SHIP-WITH-CAVEAT caveats + worker-quality gate not-met status).

**RECOMMENDATION:** planner confirms with operator on (a) tag name, (b) whether RELEASE-NOTES doc should be produced before tagging, (c) whether the three handoff-referenced missing docs (INSTALL.md, DEPENDENCIES.md) are must-have for the tag or deferred to r7.6, **before** tagging/pushing.

---

## Hard-rule compliance self-check

| Rule | Status |
|--|--|
| READ-ONLY on git state | PASS — no `git add/commit/push/tag/rm/mv` invoked by this worker. `git status`, `git diff`, `git log`, `git ls-files --error-unmatch` read-only. |
| ONLY write `.gitignore` + commit plan artifact | PASS — exactly two files modified: `.gitignore` (edit) and `ARTIFACT-r7.5-git-commit-plan.md` (new). |
| Explicit file listing (no `git add .` / `-A`) | PASS — every file staged by name; only two globs used (`ARTIFACT-r7.4-*.md`, `ARTIFACT-r7.5-*.md`) and both are bounded prefixes where 100% of matches are ship-expected. |
| Secret scan required | PASS — full scan performed; one hit found and flagged as BLOCKER with three mitigation options. |
| Flag ambiguity for operator | PASS — flagged: (a) API-key redaction option choice, (b) missing D1 deliverables, (c) tag-name choice, (d) PLAN-openspec-interop.md LEAVE-LOCAL rationale (could be operator-overridden to COMMIT). |
