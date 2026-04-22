---
type: archive + cleanup log
date: 2026-04-21
scope: r7.6 + r7.7 + r7.8 campaigns
---

# Archive + cleanup log

## Root before cleanup
- 348 `.md` files at `/Users/briantaylor/Projects/AgentFW/*.md`
- Categories seen at root:
  - r7.6 campaign artifacts: investigations (inv-1..4), judge briefs (main + C2 + C3 + REJ), fresh verdicts, P1 merge verdict, P1A/B/C impl + diag + fix + judge artifacts, synthesis verdict, worker-quality trials (armA/armB 01..20), MORNING-SUMMARY, CALIBRATION doc, plan
  - r7.7 campaign artifacts: A1/A2 (diag+impl+judge±redo), S0 preflight, S7 smoke, S8-F/G B1..B4 trials + judge briefs built, S9 ship judge, ArmF/ArmG per-trial judge verdicts (T4/T5/T6/T10 runs 1-5), planreview artifacts (I1..I4, R1/R2, EDIT-DIFF, JUDGE, SYNTHESIS), MORNING-SUMMARY, PROGRESS, plan
  - r7.8 campaign artifacts: P1a..P1d research, P2 synthesis, P3a/P3b/P3c vet logs, P5 judge briefs built, K + KP batch trials B1..B4, ArmK + ArmKP per-trial judge verdicts (T4/T5/T6/T10 runs 1-5), MORNING-SUMMARY, PROGRESS
  - Pre-r7.6 items (r7.4, r7.5, generic judge/worker/doc artifacts, release notes, plans, handoff, core docs) — left in place, out of scope
  - Framework directories (`core/`, `references/`, `templates/`, `playbooks/`, `evaluation/`, `variants/`) — untouched
  - Active probe infra scripts (`probe-*.sh`, `probe-*.py`) — untouched

## Archive structure created

```
archive/
  r7.6-campaign-2026-04-20/
    artifacts/            24 files (inv 1-4, P1-merge-verdict, P1A impl-notes, P1B fab-detector + prime-fix, P1C diag/impl/fix/run-only, synthesis-verdict)
    plans/                 1 file  (PLAN-r7.6-P1C-fixes-implementation.md)
    judge-verdicts/       85 files (judge-brief*, fresh-verdict*, C2/C3/REJ/sample-setup variants, calibration)
    batch-trials/         40 files (worker-quality-armA/armB 01..20)
    tmp-archive/         347 files (probe-r7.6-armA/armB stdout+wrapper logs for T4/T5/T6/T10 runs 1-5 moe and smoke variants + 3 P1C-logs snapshot dirs)
    ARTIFACT-r7.6-MORNING-SUMMARY.md (top-level)
    CALIBRATION-r7.6-judge-protocol.md (top-level)

  r7.7-campaign-2026-04-20/
    artifacts/            21 files (A1+A2 diag/impl/judge[-redo], S0 preflight, S7 smoke, S8-F/G judge-briefs-built, S9 ship-judge, planreview I1-I4 + R1 + R2 + EDIT-DIFF + JUDGE + SYNTHESIS)
    plans/                 1 file  (PLAN-r7.7-path-A-child-structural-fixes.md)
    judge-verdicts/       40 files (ArmF + ArmG per-trial judges T4/T5/T6/T10 runs 1-5)
    batch-trials/          9 files (S8-F-B1..B4, S8-G-B1..B4 trial summaries, S8-armF-trials)
    tmp-archive/         134 files (r7.7-a2-corpus, r7.7-judge-briefs dir, r7.7-s0-retry-preflight.log, r7.7-s6-corpus, r7.7-s6-redo-trial, s7-t4/t10 prompts+logs, r7.7-S8-armF-logs, armG-logs + armG-B2/B3/B4-logs, S8-prompts, per-trial dirs for F-B2..B4 + G-B1/B2/B4, per-trial .meta/.stdout/.stderr for F-B1-T4-run2, run-trial.sh for each batch, r7.7-S8-trial-T6-run1.qHoMPu, r7.7-env.sh.REDACTED)
    ARTIFACT-r7.7-MORNING-SUMMARY.md (top-level)
    PROGRESS-r7.7.md (top-level)

  r7.8-campaign-2026-04-21/
    artifacts/             1 file  (P5-judge-briefs-built)
    plans/                 0 files
    judge-verdicts/       40 files (ArmK + ArmKP per-trial judges T4/T5/T6/T10 runs 1-5)
    batch-trials/          8 files (K-B1..B4 + KP-B1..B4 trials)
    vet-logs/              3 files (P3a-C1-vet, P3b-S1-vet, P3c-T1-vet)
    research/              5 files (P1a failure-modes, P1b parser, P1c sampler, P1d stoptoken, P2 synthesis)
    tmp-archive/         178 files (r7.8-C1-gemma_parser.py, r7.8-gemma_parser-baseline.py, r7.8-check-before.tmp, r7.8-judge-briefs dir, K-B1..B4-logs dirs, KP-B1..B4-logs dirs, K-B1..B4 results/summary/err, KP-B3 trial1..5.out, KP-B4-summary.log, K-B3 stderr, runner.sh for K-B1..B4 + KP-B2..B4, P3a-C1-logs + P3a-C1-sessions dirs, P3b-S1-logs, P3c-T1-logs, P3a-assess.py / scan.py / scan-summary.py, P3a-run-trial.sh, P3b-S1-run-trial.sh, t1-vet-runner.sh, t1-patch.py, t1-unit-test.py)
    ARTIFACT-r7.8-MORNING-SUMMARY.md (top-level)
    PROGRESS-r7.8.md (top-level)
```

Totals:
- r7.6: 497 md/artifact files + 347 tmp files = 499 root-level .md items moved, 347 tmp items copied
- r7.7: 71 artifact files + 134 tmp items = 73 root-level .md items moved, 134 tmp items copied
- r7.8: 57 artifact files + 178 tmp items = 59 root-level .md items moved, 178 tmp items copied

## /tmp files copied (summary by campaign)

- **r7.6 (tmp-archive: 347 files)**: `probe-r7.6-armA-*`, `probe-r7.6-armB-*`, `probe-r7.6-smoke-armB-*` stdout/wrapper logs for T4/T5/T6/T10 runs 1-5 (moe variant), and the three `probe-r7.6-P1C-logs*` directories (original, `post-fix2`, `snapshot-rev2`). No `/tmp/r7.6-*` matches existed.
- **r7.7 (tmp-archive: 134 files)**: S0 preflight log, A2 corpus, judge-briefs, s6 corpus + redo, s7-t4 + s7-t10 prompts/logs, S8 batch runner scripts (7), S8 per-trial timestamped dirs (14), armF-logs, armG-logs + B2/B3/B4-logs, S8-prompts, S8 trial temp dir, S8-F-B1 per-trial .meta/.stdout/.stderr, plus redacted env.
- **r7.8 (tmp-archive: 178 files)**: C1 parser files, judge-briefs, K batch logs (B1-B4), KP batch logs (B1-B4), runner scripts (7), K results + stderr + summary, KP-B3 per-trial outs, KP-B4 summary, P3a-C1-logs + sessions, P3b-S1-logs, P3c-T1-logs, P3a + P3b + t1 runner + analysis scripts.

## Secret redaction

- `/tmp/r7.7-env.sh` contained `OMLX_API_KEY=<LITERAL-KEY>` on line 1 (literal value intentionally not reproduced in this report). Redacted variant written to `archive/r7.7-campaign-2026-04-20/tmp-archive/r7.7-env.sh.REDACTED` with `OMLX_API_KEY=<REDACTED>`. Original `/tmp/r7.7-env.sh` not copied to archive.
- Verification: `grep -rn <literal-key> /Users/briantaylor/Projects/AgentFW/archive/` returned **0 matches** post-copy across the entire archive tree (including this report). PASS.

## Root after cleanup

Root `.md` file count: **67** (including the `ARTIFACT-doc-audit-2026-04-21.md` written by the sibling audit worker and the `MORNING-SUMMARY-latest.md` symlink).

### Remaining root entries by category

- **Canonical doctrine / meta**: `CHANGELOG.md`, `DESIGN.md`, `README.md`, `LICENSE`, `bootstrap.md`, `metadata.json`, `ADDENDUM-sonnet-4-6.md`
- **Active handoff**: `HANDOFF-2026-04-19.md` (pre-existing; post-r7.8 handoff not yet present)
- **MORNING-SUMMARY symlink**: `MORNING-SUMMARY-latest.md` → `archive/r7.8-campaign-2026-04-21/ARTIFACT-r7.8-MORNING-SUMMARY.md`
- **r7.4 / r7.5 artifacts (out of scope — untouched)**: `ARTIFACT-r7.4-*.md` (10), `ARTIFACT-r7.5-*.md` (11 major + 20 worker-quality trials), `PLAN-r7.4-*.md`, `PLAN-r7.5.md`, `RELEASE-NOTES-r7.5-hermes-prerelease.md`
- **Generic pre-campaign judge/worker artifacts (out of scope — untouched)**: `ARTIFACT-doc-verifier-judgment.md`, `ARTIFACT-judge-plan-r7.md`, `ARTIFACT-judge-probe-runbook.md`, `ARTIFACT-judge-r7-ship.md`, `ARTIFACT-judge.md`, `ARTIFACT-worker-a.md`, `ARTIFACT-worker-b.md`
- **Older plans (out of scope — untouched)**: `PLAN-hermes-harness-probe.md`, `PLAN-openspec-interop.md`, `PLAN-r6-hermes-addendum.md`, `PLAN-r6.md`, `PLAN-r7-opus47-tuning.md`, `PLAN-r7.md`
- **Top-level PROGRESS**: `PROGRESS.md` (pre-existing, not campaign-specific)
- **Sibling worker audit report**: `ARTIFACT-doc-audit-2026-04-21.md` (written in parallel)
- **Active probe infra (preserved)**: `probe-preflight.sh`, `probe-omlx-health-check.sh`, `probe-variant{D,E,F,G,H,I,J}-{stage,wrapper,check}.{sh,py}`, plus `probe-variantJ-A1-stage.sh`, `probe-variantJ-A2-stage.sh`, and `.pre-*-orig` / `.pre-rev2-fix*` backup variants for E/H/I.
- **Other probe assets**: `probe-r7.3-l1-driver.sh`, `probe-r7.3-l1-firsttool.py`, `probe-swap.sh`, `probe-reproducibility.md`, `probe-tasks.md`
- **Framework directories (untouched)**: `core/`, `references/`, `templates/`, `playbooks/`, `evaluation/`, `variants/` (incl. `variants/hermes/`)
- **Git metadata (untouched)**: `.git/`, `.gitignore`, `.DS_Store`, `.claude/`

### Git status

All moved files were untracked (r7.6/7/8 campaigns never committed), so `git status` shows no `deleted:` / `renamed:` entries for the moves. Only the new `archive/r7.{6,7,8}-campaign-*` dirs appear as untracked, plus the pre-existing untracked probe scripts and the operator-written MEMORY / sibling audit files. Staging is left to the operator.

## What needs operator attention post-cleanup

1. **r7.4 / r7.5 campaign files still at root**: Not in scope of this task. If operator wants them archived too, dispatch a follow-up with the same pattern (e.g. `archive/r7.4-r7.5-campaigns-archive/`).
2. **Generic pre-r7 artifacts** (`ARTIFACT-judge*.md`, `ARTIFACT-worker-{a,b}.md`, `ARTIFACT-doc-verifier-judgment.md`): These predate the campaign-numbered convention. Operator should decide whether they belong in an older-artifacts archive or stay as historical doctrine.
3. **MORNING-SUMMARY-latest.md symlink** points to r7.8's morning summary (current latest). Update manually if r7.9+ lands.
4. **`/tmp` cleanup**: All campaign data successfully copied to archive (not moved). Operator may safely purge `/tmp/r7.{6,7,8}-*`, `/tmp/probe-r7.6-*`, `/tmp/r7.7-env.sh`, etc. when ready. VM probe backup files (`.probe-*-orig` on VM) NOT touched per scope.
5. **PROGRESS.md at root** is the top-level (non-campaign) progress doc — left in place. r7.7 / r7.8 campaign-specific progress files moved into their archive dirs.
6. **Any plan-review artifacts** classified as `artifacts/` under r7.7 since they're research output feeding into the plan; move them to `research/` if operator prefers that semantic split.
7. **Sibling audit report** `ARTIFACT-doc-audit-2026-04-21.md` left at root — operator can decide final resting place after reading.
