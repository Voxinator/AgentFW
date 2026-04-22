# ARTIFACT-r7.7-planreview-I4-state-verification

**Role:** Worker I4 (state verification, read-only).
**Date:** 2026-04-20.
**Plan under review:** `PLAN-r7.7-path-A-child-structural-fixes.md`.
**Scope:** verify every factual state claim in §3 "Current state" and §14 "Environment + artifact map." No mutations, no recommendations — drift report only.

---

## 1. Repo md5 verification table

Plan §14 expected md5s vs actual filesystem md5s (computed 2026-04-20).

| File | Plan-expected md5 | Actual md5 | Verdict |
|------|-------------------|------------|---------|
| `probe-preflight.sh` | `65b88ec02c1a1b07c88dc195f765331f` | `65b88ec02c1a1b07c88dc195f765331f` | MATCH |
| `CALIBRATION-r7.6-judge-protocol.md` | `2ddd2eac5fa26b9f7a1465fb3046503d` | `2ddd2eac5fa26b9f7a1465fb3046503d` | MATCH |
| `variants/hermes/delegate_worker_v2.py` | `d31876fe987331a26c8640202334fd46` | `d31876fe987331a26c8640202334fd46` | MATCH |
| `variants/hermes/HERMES-variantF.md` (working tree) | `24e8d1c0f7e1e0e95b26c38af974b8ce` | `24e8d1c0f7e1e0e95b26c38af974b8ce` | MATCH |
| `variants/hermes/HERMES-WORKER.md` | `f866f52bbee28335964ec50d06bbac68` | `f866f52bbee28335964ec50d06bbac68` | MATCH |
| `probe-variantH-check.py` | `873935f65e1bb91942dde1139dd57f92` | `873935f65e1bb91942dde1139dd57f92` | MATCH |
| `probe-variantI-wrapper.sh` | `f1022e994a46838c180e4bf8da4171ee` | `f1022e994a46838c180e4bf8da4171ee` | MATCH |
| `probe-variantH-wrapper.sh` | `64b75e00efc1056dcb1883a54e162033` | `64b75e00efc1056dcb1883a54e162033` | MATCH |
| `/tmp/probe-r7.6-P1C-logs/judge-trial.py` | `709ef98a...` (prefix, post-Fix-2) | `709ef98a644b42d46a03a10aaf728f2a` | MATCH |

**All 9 file md5 claims in §14 match.**

### Pre-release tag cross-check

- Plan claim §3: `r7.5-hermes-prerelease:variants/hermes/HERMES-variantF.md` md5 = `01c0e77b…`.
- Actual: `git show 'r7.5-hermes-prerelease:variants/hermes/HERMES-variantF.md' | md5 -q` → `01c0e77bb2a6e753a8ea9063784a25e0`.
- Verdict: **MATCH** (prefix `01c0e77b` confirmed).

---

## 2. Referenced artifacts existence table

Plan §5 pre-flight reading list + §14 "Artifacts to read first" / "reference as evidence" spot-check.

| Filename | Exists | Notes |
|----------|--------|-------|
| `ARTIFACT-r7.6-MORNING-SUMMARY.md` | Y | untracked |
| `PLAN-r7.6-P1C-fixes-implementation.md` | Y | untracked |
| `CALIBRATION-r7.6-judge-protocol.md` | Y | untracked; md5 match |
| `ARTIFACT-r7.4-sigterm-research.md` | Y | in repo (tracked; `ls -la` returned file) |
| `ARTIFACT-r7.5-F1-judge-brief.md` | Y | in repo (tracked) |
| `ARTIFACT-r7.6-judge-REJ-sample-setup.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix2-impl.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix3-impl.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix4-impl.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix5-impl.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix2-judge.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix3-judge.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix4-judge.md` | Y | untracked |
| `ARTIFACT-r7.6-P1C-fix5-judge.md` | Y | untracked |

**All plan-referenced artifacts exist.** All r7.6 work-products are in the untracked (`??`) bucket, nothing committed.

---

## 3. Git state

### Tag + main status

- `r7.5-hermes-prerelease` tag present (matches plan §3).
- HEAD log head (`git log --oneline -5`):
  - `001a1a9` Hermes variant r7.5 pre-release — β-fuse dispatch layer validated, worker-quality gate not yet met
  - `a6679b7` AgentFW r7 — cross-model tuning without non-target regression
  - `b639def` AgentFW r6 — context degradation resistance
  - `da4830c` Add long-running service restart rule and r5 eval results
  - `0803792` Update docs and metadata to r5

### Drift from tag

- `git log --oneline r7.5-hermes-prerelease..HEAD` → **empty output**. HEAD commit equals the tag commit.
- `git log --oneline r7.5-hermes-prerelease..HEAD -- variants/hermes/HERMES-variantF.md probe-variantI-wrapper.sh probe-variantH-wrapper.sh` → **empty**.
- Committed HEAD HERMES-variantF.md md5: `01c0e77bb2a6e753a8ea9063784a25e0` (same as tag).
- Working-tree HERMES-variantF.md md5: `24e8d1c0f7e1e0e95b26c38af974b8ce` (plan's "post-Fix-4" value).
- `git diff --stat HEAD -- variants/hermes/HERMES-variantF.md`: `1 insertion(+)` — exactly matches plan's "Fix 4 added item #6" description.

**DRIFT NOTICE (semantics):** Plan §3 states "main branch has drifted post-tag" with three bulleted items. Git's ground truth is:

- HEAD commit == tag commit (zero committed drift).
- HERMES-variantF.md is **uncommitted working-tree modification** (status `M`), not a committed drift.
- `probe-variantI-wrapper.sh` and `probe-variantH-wrapper.sh` are **not modified** in working tree (neither appears in `git status`) — meaning the "Fix 3 + Fix 4 patches" on them are ALREADY part of the HEAD (= tag) commit. They did NOT drift post-tag; they were committed in the pre-release.

This is a subtle semantic inaccuracy in the plan's narrative. "Main has drifted" implies committed divergence; the actual state is "one file has an uncommitted edit, and a mountain of untracked artifacts exist." A fresh clone with `git checkout r7.5-hermes-prerelease` would get the exact same committed content as a fresh clone of `main` — the only difference is the uncommitted edit doesn't carry.

### Uncommitted summary

- 1 modified (staged or unstaged): `M variants/hermes/HERMES-variantF.md` (+1 line).
- 0 staged.
- **164 untracked** files (see §6).

---

## 4. VM state

VM reachable via `ssh ubuntu-vm`. All checks completed.

### Canonical md5s table

| Path | Plan-expected | Actual | Verdict |
|------|---------------|--------|---------|
| `~/.hermes/hermes-agent/HERMES.md` | `0780c232a6cb52e13e432261f0d68ad9` | `0780c232a6cb52e13e432261f0d68ad9` | MATCH |
| `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` | `fb1a5a5208a6cf2fcb8252aac10397eb` | `fb1a5a5208a6cf2fcb8252aac10397eb` | MATCH |
| `~/.hermes/skills/.../jira-briefing.sh` | `a1dce6e989527686124d0860830627c9` | `a1dce6e989527686124d0860830627c9` | MATCH |
| `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts` | `5503ee1c2ef7d635a020eea275e41239` | `5503ee1c2ef7d635a020eea275e41239` | MATCH |

All four canonical tripwire md5s MATCH exactly. VM canonical state is intact.

### Staging-state table

| Claim (plan §3) | Actual on VM | Verdict |
|-----------------|--------------|---------|
| "All staging unstaged. VM is CANONICAL." | Tripwire md5s match canonical; no `delegate_worker_v2.py` in `tools/`; `toolsets.py` does not reference `delegate_worker_v2` (grep -c = 0). | MATCH (net state = canonical / unstaged). |
| "Source patches: `delegate_worker.py`, `delegate_worker_v2.py` present with `.probe-d-orig`, `.probe-r7.4-orig`, `.probe-r7.5-orig`, `.probe-r7.6-orig` backup chains" | Actual top-level backups found: `model_tools.py.probe-d-orig`, `model_tools.py.probe-r7.4-orig`, `run_agent.py.probe-d-orig`, `run_agent.py.probe-r7.4-orig`, `run_agent.py.probe-r7.5-orig`, `run_agent.py.probe-r7.6-orig`, `toolsets.py.probe-d-orig`, `toolsets.py.probe-r7.3-orig`, `toolsets.py.probe-r7.4-orig`. **No `delegate_worker*.py.probe-*-orig` files at top level.** | **DRIFT** — plan names the wrong files. The real backup chain covers `model_tools.py`, `run_agent.py`, `toolsets.py`. `delegate_worker.py` / `delegate_worker_v2.py` are NOT the files with backup chains on VM. |
| `delegate_worker_v2.py` staged at `~/.hermes/hermes-agent/tools/` | File does not exist at that path. | Consistent with "unstaged" headline; plan bullet ambiguity again. |
| HERMES-WORKER.md NOT on VM | `ls ~/.hermes/hermes-agent/HERMES-WORKER.md` → No such file or directory. | MATCH. |

**Key drift:** plan §3 lists the wrong filenames for which VM source files have `.probe-*-orig` backup chains. The real files with those chains are `model_tools.py`, `run_agent.py`, `toolsets.py` — the Hermes internals, not the β-fuse tool files. This matters because the plan §10 "May" scope says "Modify Hermes install files on VM with backup-and-patch pattern (`.probe-r7.7-orig` suffix — coexists with `.probe-d-orig`, ..., `.probe-r7.6-orig`)" and the fresh agent following the plan will look for the wrong files if they trust the bullet list.

### Hermes version

- Plan claim §14: `v2026.4.8` / commit `86960cdb chore: release v0.8.0 (2026.4.8) (#6135)`.
- Actual VM `git log --oneline -3`:
  - `86960cdb chore: release v0.8.0 (2026.4.8) (#6135)` ✓
  - `8b0afa0e fix: aggressive worktree and branch cleanup to prevent accumulation (#6134)`
  - `ab21fbfd fix: add gateway coverage for session boundary hooks, move test to tests/cli/`
- Tag list: `v2026.4.16`, `v2026.4.3`, `v2026.4.8` all present.
- Verdict: **MATCH** on claimed version + commit hash + tag.

### Python version

- Plan claim §14: Python 3.11.15 in Hermes venv.
- Actual: `/home/parallels/.hermes/hermes-agent/venv/bin/python3 --version` → `Python 3.11.15`.
- Verdict: **MATCH**.

---

## 5. Secret scan

### What's in the repo

`grep -rn '<raw-key>' . --exclude-dir=.git --exclude-dir=node_modules` (operator knows the value) found hits in exactly two files:

1. `./PLAN-r7.7-path-A-child-structural-fixes.md:104` — the plan under review itself.
   Content: narrative sentence stating the dev key lives in `OMLX_API_KEY` env var; inline raw value redacted 2026-04-20.
2. `./PLAN-r7.7-path-A-child-structural-fixes.md:562` — same plan, meta-discussion in §12 referencing the archived leak; inline raw value redacted 2026-04-20.

No other on-disk hits. The archive file the plan §12 references is already redacted (grep did not match it), as plan §12 claims.

### What's in the plan (flagged prominently)

**The plan itself is the ONLY current secret-leak source in the repo.**

- Line 104 places the raw key value in narrative prose.
- Line 562 is unavoidably a meta-reference (discussing the historical leak); that line could stay redacted-only.

Either way, the plan violates its own §12 rule ("ANY new artifact that documents api_key lines MUST use `<REDACTED>` placeholder"). If the plan is ever committed as-is, a new secret-instance lands in git history. The pre-commit scan the plan prescribes WILL flag this plan file — the fresh agent must not be surprised by that trip.

### What was in global MEMORY (context)

The global CLAUDE.md MEMORY entry labelled "reference_omlx_api_key" already stores the key in `OMLX_API_KEY` env var ("local dev only; never commit to repo"). The plan restates the raw value inline redundantly.

---

## 6. Artifact growth

- Handoff context note referenced "~50+" untracked lines.
- Actual: `git status --porcelain | grep '^??' | wc -l` = **164 untracked**.
- The context note was taken from a truncated view of the user message — the real untracked surface is ~3x larger.

### Sample categories (by prefix)

- **ARTIFACT-r7.6-*** — ~140 files (MORNING-SUMMARY, P1/P1A/P1B/P1C variants, inv-*, judge-C2/C3/REJ fresh-verdicts, judge-brief-*, judge-calibration, judge-fresh-verdict-*, judge-sample-setup, synthesis-verdict, worker-quality-armA-01..20, worker-quality-armB-01..20).
- **ARTIFACT-r7.7-*** — 2 files (planreview-I1-campaign-arc, this file — note sibling worker has already produced I1).
- **CALIBRATION-r7.6-judge-protocol.md** — 1 file (referenced in plan §14).
- **PLAN-r7.6-P1C-fixes-implementation.md** — 1 file (style precedent per plan §5).
- **PLAN-r7.7-path-A-child-structural-fixes.md** — 1 file (the plan under review itself is untracked).
- **probe-preflight.sh, probe-variantH-check.py, probe-variantH-stage.sh, probe-variantH-wrapper.sh, probe-variantH-wrapper.sh.pre-rev2-fix4, probe-variantI-stage.sh, probe-variantI-wrapper.sh, probe-variantI-wrapper.sh.pre-rev2-fix3, probe-variantI-wrapper.sh.pre-rev2-fix4** — 9 files, all probe infrastructure + rev2 fix backup artifacts.
- **variants/hermes/HERMES-WORKER.md** — 1 file (referenced heavily in plan but is untracked, not tracked).

### Sanity check against plan §14 "new artifacts" claim

Plan §14 does not enumerate untracked artifacts explicitly; the only hint is §3 "Plus many new artifacts from the overnight r7.6 work (see §14)" and §14 "Artifacts to reference as evidence (if needed)" which names:

- `ARTIFACT-r7.6-judge-REJ-fresh-verdict-*.md` ✓ present (22 files: 5 arms × tasks).
- `ARTIFACT-r7.6-judge-fresh-verdict-{1..5}.md`, `-C2-*`, `-C3-*` ✓ all present.
- `ARTIFACT-r7.6-P1C-fix{2,3,4,5}-{impl,judge}.md` ✓ all 8 present.

Plan's enumerated evidence artifacts are all present.

**Uncalled-out surface (plan does not name these but they exist):**
- `ARTIFACT-r7.6-worker-quality-armA-01..20.md` + `-armB-01..20.md` — 40 files, large.
- `ARTIFACT-r7.6-judge-brief-*` — ~30 files.
- `ARTIFACT-r7.6-judge-calibration.md`, `-synthesis-verdict.md`, `-sample-setup.md`.
- `probe-variantH-stage.sh`, `probe-variantI-stage.sh`, `*.pre-rev2-fix*` backup scripts.
- `variants/hermes/HERMES-WORKER.md` itself.
- `PLAN-r7.7-path-A-child-structural-fixes.md` (the plan under review is untracked).
- `CALIBRATION-r7.6-judge-protocol.md` (also untracked despite being called a "standing calibration protocol").

The plan under-counts the uncommitted-artifact footprint significantly. A fresh agent would find >100 more loose files than the plan prepares them for.

---

## 7. Summary — drift found vs expected

### MATCH (plan is accurate)

- **All 9 repo-file md5s in §14 match exactly** (including `/tmp/probe-r7.6-P1C-logs/judge-trial.py` at `709ef98a644b42d46a03a10aaf728f2a`).
- **Pre-release tag `r7.5-hermes-prerelease` exists and is immutable**; tagged-version HERMES-variantF.md md5 `01c0e77bb2a6e753a8ea9063784a25e0` matches prefix cited.
- **All plan-referenced artifacts in §5 / §14 exist.**
- **All four VM canonical tripwire md5s match exactly** (HERMES.md, SKILL.md, jira-briefing.sh, useDashboard.ts).
- **Hermes version on VM matches exactly** (v2026.4.8 / commit `86960cdb` / tag present).
- **Python 3.11.15 on VM matches plan.**
- **HERMES-WORKER.md not on VM — matches plan.**
- **VM net state IS "canonical / unstaged"** — no visible probe patches on VM.
- Working-tree HERMES-variantF.md md5 is the "post-Fix-4" value `24e8d1c0...` as claimed (+1 line diff from HEAD matches "added item #6").

### DRIFT (plan claim is wrong or misleading)

1. **§3 "main branch has drifted post-tag" is semantically incorrect.** `git log r7.5-hermes-prerelease..HEAD` is empty. HEAD commit IS the tag commit. What the plan calls "drift" is (a) one uncommitted working-tree edit to HERMES-variantF.md, and (b) 164 untracked files. A fresh clone of main is identical to a fresh clone of the tag. Narrative implies committed divergence that does not exist.
2. **§3 claim that `probe-variantI-wrapper.sh` and `probe-variantH-wrapper.sh` "drifted" post-tag is incorrect.** Neither appears in `git status`; they are unchanged since the HEAD/tag commit. Whatever "Fix 3 + Fix 4 patches" the plan references are already IN the pre-release commit (or they simply weren't applied and the plan is describing intentions). The "drifted" framing is wrong.
3. **§3 bullet naming "delegate_worker.py, delegate_worker_v2.py present with `.probe-*-orig` backup chains" is factually incorrect.** The files on VM with those backup chains at the top level are `model_tools.py`, `run_agent.py`, `toolsets.py`. The `delegate_worker*.py` files are NOT present at `~/.hermes/hermes-agent/` top level and do NOT have backup chains there. A fresh agent looking for `delegate_worker.py.probe-r7.4-orig` on the VM will not find it.
4. **§14 md5 list omits `/tmp/probe-r7.6-P1C-logs/judge-trial.py`'s full hash.** Only a prefix is given (`709ef98a...`); the full actual hash is `709ef98a644b42d46a03a10aaf728f2a`. This is a minor completeness gap, not a correctness drift, but the plan's own pre-flight §5 step 2 would fail a strict md5 compare because the baseline is written as an ellipsis.
5. **Untracked file count is 164, roughly 3x the "~50+" informally tracked.** Not a plan-claim drift per se (plan doesn't state a count), but the cleanup / commit cost is understated.
6. **Many artifacts referenced in the plan are themselves untracked** including `variants/hermes/HERMES-WORKER.md`, `CALIBRATION-r7.6-judge-protocol.md`, the plan-under-review itself, and all P1C evidence files. Plan §6.5 / §10 authorization implicitly assumes these are "in the repo" — they are on disk but not in git history.

### Secret leak (flagged prominently)

- **The plan `PLAN-r7.7-path-A-child-structural-fixes.md` leaked the oMLX dev key on line 104 in raw form** (narrative sentence of §3 "oMLX operational knowledge"). Redacted 2026-04-20 immediately on detection.
- The plan violates its own §12 policy ("ANY new artifact that documents api_key lines MUST use `<REDACTED>` placeholder").
- The key also appears on line 562 in §12 meta-discussion (acceptable as a historical reference, redactable).
- **No other files in the repo currently contain the literal string** (the archive file the plan §12 cites has been redacted, per successful grep negative match on that path).
- **If the plan is committed as-is, a fresh secret-instance lands in git history** and git's own `core.excludesfile` / `grep --exclude-dir=.git` won't help once the blob is in the objects DB.

### UNREACHABLE

- None. VM was reachable throughout; all checks completed.

---

*End of state verification. No mutations performed. Observe-only.*
