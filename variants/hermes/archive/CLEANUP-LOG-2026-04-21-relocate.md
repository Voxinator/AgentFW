---
type: Hermes-variant relocation log
date: 2026-04-21
operator-direction: AgentFW is a general-purpose harness; Hermes is ONE variant; root must stay framework-only
scope: Relocate all Hermes-specific material from AgentFW project root into `variants/hermes/`
---
# Hermes relocation log

## Root before relocation

Project root held 105 top-level file entries (plus dirs). Hermes-related items categorized as follows:

- **r7.4 campaign artifacts at root**: 10 ARTIFACTs + 1 PLAN (`PLAN-r7.4-wrapper-sigterm-fix-design.md`) = 11 files
- **r7.5 prerelease artifacts at root**: 9 ARTIFACTs + 20 worker-quality trials + 1 PLAN (`PLAN-r7.5.md`) + 1 RELEASE-NOTES = 31 files
- **Probe scripts at root**: 29 `probe-*.sh`/`probe-*.py`/`probe-*.md` (including `.pre-*-orig` and `.pre-rev2-fix*` backup variants)
- **Active handoff docs at root**: 3 (`HANDOFF-post-r7.8.md`, `HANDOFF-2026-04-19.md`, `ARTIFACT-doc-audit-2026-04-21.md`)
- **MORNING-SUMMARY-latest.md symlink at root**: 1
- **Hermes-specific progress + plan + verifier at root**: 4 (`PROGRESS.md`, `PLAN-hermes-harness-probe.md`, `PLAN-r6-hermes-addendum.md`, `ARTIFACT-doc-verifier-judgment.md`)
- **`/archive/` dir**: held Hermes campaign archives (r7.6, r7.7, r7.8) + two pre-r7.4 Hermes probe archives (hermes-probe-r7-2026-04-18, hermes-probe-r7.2-r7.3-2026-04-18) + prior cleanup log + 3 AgentFW-framework r3 playbook archives

Total Hermes-specific files relocated: **79 files from root + entire `/archive/` Hermes tree (≈ 600+ files incl. nested campaign archives)**.

## Target structure created

```
variants/hermes/
├── archive/                                      # NEW
│   ├── CLEANUP-LOG-2026-04-21.md                 # moved from /archive/ (untracked)
│   ├── CLEANUP-LOG-2026-04-21-relocate.md        # NEW — this log
│   ├── hermes-probe-r7-2026-04-18/               # git mv from /archive/
│   ├── hermes-probe-r7.2-r7.3-2026-04-18/        # git mv from /archive/
│   ├── r7.4-campaign/                            # NEW — holds r7.4 artifacts
│   ├── r7.5-prerelease-2026-04-19/               # NEW — holds r7.5 artifacts + trials + release notes
│   ├── r7.6-campaign-2026-04-20/                 # mv from /archive/ (untracked)
│   ├── r7.7-campaign-2026-04-20/                 # mv from /archive/ (untracked)
│   └── r7.8-campaign-2026-04-21/                 # mv from /archive/ (untracked)
├── probe/                                        # NEW — active probe infrastructure
│   └── 29 probe-*.sh/py/md files
└── campaign-handoff/                             # NEW — active Hermes campaign handoff docs
    ├── ARTIFACT-doc-audit-2026-04-21.md
    ├── HANDOFF-2026-04-19.md
    ├── HANDOFF-post-r7.8.md
    └── MORNING-SUMMARY-latest.md                 # symlink → ../archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md
```

## Moves executed

### B) `/archive/` Hermes subtree relocation

- **Git-tracked (preserved history via `git mv`):**
  - `archive/hermes-probe-r7-2026-04-18/` (20 tracked files) → `variants/hermes/archive/hermes-probe-r7-2026-04-18/`
  - `archive/hermes-probe-r7.2-r7.3-2026-04-18/` (31 tracked files) → `variants/hermes/archive/hermes-probe-r7.2-r7.3-2026-04-18/`
- **Untracked (plain `mv`):**
  - `archive/r7.6-campaign-2026-04-20/` (500+ files) → `variants/hermes/archive/r7.6-campaign-2026-04-20/`
  - `archive/r7.7-campaign-2026-04-20/` (200+ files) → `variants/hermes/archive/r7.7-campaign-2026-04-20/`
  - `archive/r7.8-campaign-2026-04-21/` (240+ files) → `variants/hermes/archive/r7.8-campaign-2026-04-21/`
  - `archive/CLEANUP-LOG-2026-04-21.md` → `variants/hermes/archive/CLEANUP-LOG-2026-04-21.md`

### C) Probe scripts (29 files) → `variants/hermes/probe/`

**Git-tracked (15 files, moved via `git mv`):**
- `probe-omlx-health-check.sh`
- `probe-r7.3-l1-driver.sh`
- `probe-r7.3-l1-firsttool.py`
- `probe-reproducibility.md`
- `probe-swap.sh`
- `probe-tasks.md`
- `probe-variantD-stage.sh`
- `probe-variantE-check.py`
- `probe-variantE-wrapper.sh`
- `probe-variantF-check.py`
- `probe-variantF-stage.sh`
- `probe-variantF-wrapper.sh`
- `probe-variantG-check.py`
- `probe-variantG-stage.sh`
- `probe-variantG-wrapper.sh`

**Untracked (14 files, plain `mv`):**
- `probe-preflight.sh`
- `probe-variantE-wrapper.sh.pre-r7.3-l2-orig`
- `probe-variantE-wrapper.sh.pre-r7.3-orig`
- `probe-variantH-check.py`
- `probe-variantH-stage.sh`
- `probe-variantH-wrapper.sh`
- `probe-variantH-wrapper.sh.pre-rev2-fix4`
- `probe-variantI-stage.sh`
- `probe-variantI-wrapper.sh`
- `probe-variantI-wrapper.sh.pre-rev2-fix3`
- `probe-variantI-wrapper.sh.pre-rev2-fix4`
- `probe-variantJ-A1-stage.sh`
- `probe-variantJ-A2-stage.sh`
- `probe-variantJ-wrapper.sh`

### D) Handoff docs (3 files + 1 symlink) → `variants/hermes/campaign-handoff/`

**Untracked (plain `mv`):**
- `HANDOFF-post-r7.8.md`
- `HANDOFF-2026-04-19.md`
- `ARTIFACT-doc-audit-2026-04-21.md`

**Symlink retargeted:**
- `MORNING-SUMMARY-latest.md` at root → removed
- Recreated inside `variants/hermes/campaign-handoff/MORNING-SUMMARY-latest.md` pointing to `../archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md` (relative path — resolves correctly)

### E) r7.4 / r7.5 sweep (42 root-level files)

**`variants/hermes/archive/r7.4-campaign/` (12 files, all git-tracked, moved via `git mv`):**
- 10 `ARTIFACT-r7.4-*.md` (p1-judge-verdict, p1-terminal-binding, phase-a-impl-notes, phase-c-judge-verdict, phase-d-dense-gapfill, phase-d-dense-results, phase-d-moe-results, ship-judge-verdict-v2, ship-judge-verdict, sigterm-research)
- 1 `PLAN-r7.4-wrapper-sigterm-fix-design.md`
- 1 `PROGRESS-r7.4.md` (was `PROGRESS.md` at root, untracked — plain `mv` + rename)

**`variants/hermes/archive/r7.5-prerelease-2026-04-19/` (31 files, all git-tracked, moved via `git mv`):**
- 9 `ARTIFACT-r7.5-*.md` major (A1-impl-notes, A2-judge-verdict, B1-impl-notes, B2-impl-notes, F1-judge-brief, F2-probe-results, SHIP-judge-verdict, git-commit-plan, phase3-smoke-verdict)
- 20 `ARTIFACT-r7.5-worker-quality-trial-{01..20}.md`
- 1 `PLAN-r7.5.md`
- 1 `RELEASE-NOTES-r7.5-hermes-prerelease.md`

### Misc Hermes files relocated into existing campaign dirs

- `PLAN-hermes-harness-probe.md` → `variants/hermes/archive/hermes-probe-r7-2026-04-18/` (git mv; fits its source campaign)
- `PLAN-r6-hermes-addendum.md` → `variants/hermes/archive/hermes-probe-r7-2026-04-18/` (git mv; fits historically — sibling of existing `PLAN-deep-dive-hermes-r6.md`)
- `ARTIFACT-doc-verifier-judgment.md` → `variants/hermes/archive/hermes-probe-r7.2-r7.3-2026-04-18/` (git mv; this artifact verifies the r7.2/r7.3 probe docs)

## Root after relocation

```
AgentFW/
├── .claude/
├── .git/
├── .gitignore
├── .DS_Store
├── ADDENDUM-sonnet-4-6.md                # AgentFW framework (Sonnet 4.6 addendum)
├── ARTIFACT-judge-plan-r7.md             # AgentFW framework (judges PLAN-r7)
├── ARTIFACT-judge-probe-runbook.md       # AgentFW framework (judges evaluation/PROBE-r7-runbook.md)
├── ARTIFACT-judge-r7-ship.md             # AgentFW framework (r7 ship readiness)
├── ARTIFACT-judge.md                     # AgentFW framework (r6 tuning feasibility)
├── ARTIFACT-worker-a.md                  # AgentFW framework (r6 model-sensitive surface map)
├── ARTIFACT-worker-b.md                  # AgentFW framework (Opus 4.7 dossier)
├── bootstrap.md                          # AgentFW framework
├── CHANGELOG.md                          # AgentFW framework
├── DESIGN.md                             # AgentFW framework design spec
├── LICENSE
├── metadata.json                         # AgentFW framework
├── PLAN-openspec-interop.md              # AgentFW framework (OpenSpec interop plan)
├── PLAN-r6.md                            # AgentFW framework (r6 plan)
├── PLAN-r7-opus47-tuning.md              # AgentFW framework (Opus 4.7 tuning feasibility)
├── PLAN-r7.md                            # AgentFW framework (r7 cross-model tuning plan)
├── README.md                             # AgentFW framework
├── archive/                              # NOW holds 3 r3 framework-playbook archives + .DS_Store only
├── core/
├── evaluation/
├── playbooks/
├── references/
├── templates/
└── variants/                             # incl. variants/hermes/ (enlarged)
```

**Root file count: 18** (down from 105 top-level file entries before relocation).

**Root `/archive/` remaining contents (3 AgentFW framework artifacts — NOT Hermes, intentionally retained):**
- `agentic-harness-playbook_r3.md` (AgentFW r3 playbook)
- `agentic-harness-playbook-pm_r3.md` (AgentFW r3 PM playbook)
- `agentic-harness-project-instructions_r3.md` (AgentFW r3 instructions)

These are AgentFW framework history (r3 precursor docs), not Hermes variant artifacts. Leaving them at `/archive/` (not inside `variants/hermes/archive/`) is consistent with operator direction ("Hermes is ONE variant; root must stay framework-only" → framework history stays at framework root, not under a variant).

## Verification

- **Secret scan** — `grep -rn '<raw-key>' /Users/briantaylor/Projects/AgentFW/variants/hermes/` returns **0 matches** (operator knows the literal). PASS.
- **OMLX API key literal scan** — regex `OMLX_API_KEY\s*=\s*["']?[A-Za-z0-9_\-]{10,}` against `variants/hermes/` returns **0 matches**. PASS (previously redacted in prior cleanup's tmp-archive).
- **Symlink integrity** — `variants/hermes/campaign-handoff/MORNING-SUMMARY-latest.md` resolves (relative path `../archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md` → valid file; head -1 returns `[TASK CLASS: long-horizon]`). PASS.
- **`variants/hermes/` structure consistent with spec** — YES. `archive/` + `probe/` + `campaign-handoff/` created; existing code/canonical .md files untouched.
- **Git rename tracking** — 127 renames tracked (all `R` entries in `git status --short`). History preserved for all previously-tracked files (hermes-probe-r7/7.2-7.3 archives, 15 probe scripts, 11 r7.4 artifacts + PLAN, 30 r7.5 artifacts + PLAN + RELEASE-NOTES, 3 misc PLAN/ARTIFACT moves).
- **Root purity** — `ls /Users/briantaylor/Projects/AgentFW/ | grep -iE 'r7|hermes|probe|calibration'` returns: `ARTIFACT-judge-plan-r7.md`, `ARTIFACT-judge-probe-runbook.md`, `ARTIFACT-judge-r7-ship.md`, `PLAN-r7-opus47-tuning.md`, `PLAN-r7.md`. All five are AgentFW framework-level (r7 is the framework revision, not a Hermes probe campaign). No Hermes-campaign artifacts remain at root.

## Files operator may want to review

1. **`/archive/` at root (3 framework-history files + `.DS_Store`)** — Classified as AgentFW framework precursors, not Hermes. If operator prefers to keep root entirely clean of any `archive/` dir, these could move to a new `framework-history/` or similar. Flagged as ambiguous: they predate the "AgentFW vs variant" split, so could be argued either way.
2. **`.DS_Store` files** — macOS Finder metadata, cosmetic. Present at root, at `/archive/`, and inside several moved dirs. Not touched; operator may add to `.gitignore` if not already.
3. **Root `ARTIFACT-judge*.md` and `ARTIFACT-worker-{a,b}.md`** — All classified as AgentFW framework (r6/r7 tuning research, r7 ship judge, PROBE-r7-runbook judge). Prior cleanup log flagged these as "pre-campaign" and left them at root. This relocation reaffirms that classification. If operator wants them in an archived-framework-research dir, it's a separate cleanup.
4. **Git staging** — Per scope constraint, NO `git add` or `git commit` performed. `git status` shows ~127 renames + ~5 untracked dirs + 1 modified file (`variants/hermes/HERMES-variantF.md`, untouched by this relocation). Operator to stage/commit.
5. **Pre-rev2-fix backup probe files** (`.pre-rev2-fix3`, `.pre-rev2-fix4`, `.pre-r7.3-l2-orig`, `.pre-r7.3-orig`) — moved to `variants/hermes/probe/` alongside active scripts. If operator prefers a separate `probe/backup/` subdir, trivial follow-up.
6. **r7.4-campaign naming** — Created as `r7.4-campaign` (no date suffix) vs `r7.5-prerelease-2026-04-19` (dated) because r7.4 artifacts span Apr 19 and no single campaign date was obvious. Operator may rename for consistency.
7. **`PROGRESS.md` → `PROGRESS-r7.4.md`** — Renamed on move to disambiguate from future framework-level `PROGRESS.md` at root. Content was Hermes r7.4 β-fuse progress. Operator may want a fresh framework-level `PROGRESS.md` at root later.
