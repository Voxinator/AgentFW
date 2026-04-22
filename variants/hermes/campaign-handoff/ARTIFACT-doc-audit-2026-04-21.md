---
type: pre-release doc audit
date: 2026-04-21
scope: Hermes variant of AgentFW
---
# Pre-release doc audit

## Audit target

Next pre-release: **no worker-quality gate has been met through r7.8.** The r7.5 tag (`r7.5-hermes-prerelease`, commit `001a1a9`) remains immutable on GitHub and its headline thesis (β-fuse dispatch validated; worker-quality HOLD) is still correct. What has drifted on-disk is the *surrounding narrative*: three additional HOLD campaigns (r7.6/7.7/7.8) and a generation-layer ceiling finding (Arm K' vanilla baseline at 4/20, matching r7.6 Arm A) now exist only as untracked Mac-local artifacts. A user cloning this repo today sees the r7.5 release notes + r7.5-era NEXT-STEPS agenda and has no way to know the r7.6 agenda has been fully worked through and rejected as insufficient. Document the state honestly so any next tag reflects HOLD status + campaign learnings, not claimed progress.

## Files reviewed + state

### Canonical (should stay frozen for r7.5 tag; annotate if drifted)

| File | Current state | Needs update? | Scope of update |
|------|---------------|---------------|-----------------|
| `variants/hermes/HERMES.md` | md5 `0780c232a6cb52e13e432261f0d68ad9` — MATCHES canonical. Untouched since r7.5 tag. | **No.** Canonical invariant holds across all 40+40+40 probe trials through r7.8. | — |
| `variants/hermes/HERMES-variantF.md` | md5 `24e8d1c0f7e1e0e95b26c38af974b8ce`; tag md5 `01c0e77bb2a6e753a8ea9063784a25e0`. **DRIFTED.** | **Yes** — but as a tracked-drift, not a fix. Single addition: "Retry Re-Classification" anti-pattern #6 (Fix 4, r7.6-P1C, 2026-04-19). This is the only content mutation on a tracked canonical-ish file since the tag. | Next tag should either (a) commit the drift + annotate that variantF has moved past its tag state for worker-quality probes, or (b) revert the drift on disk to preserve tag-parity. Fix 4 itself was not decisively load-bearing in r7.7 Arm F (7/20 PASS, within noise), so reversion is defensible. |
| `variants/hermes/HERMES-variantD.md`, `-variantE.md`, `-variantB.md` | Frozen; match tag. | No. | — |
| `variants/hermes/delegate_worker_v2.py` | **DRIFTED** from tag md5 `d31876fe987331a26c8640202334fd46`. Adds `_resolve_parent_toolsets` + A1 child-toolset restriction (env-gated on `HERMES_CHILD_TOOLSET_RESTRICT`). | **Yes, same two-option choice as variantF.md.** Env-gated so *behaviorally* identical to tag with flag unset; but the code surface is +64 lines of new functionality. | Commit with "A1 probe infrastructure, env-gated, off by default" annotation, OR revert and keep on a branch. r7.7 judge verdict was HOLD; A1 did not win. |
| `variants/hermes/IMPLEMENTATION.md` | Historical r7 install doc, frozen. | No. | — |
| `variants/hermes/DESIGN.md` | States "Dispatch-layer thesis validated; worker-quality ship gate not yet met" — accurate per r7.5. | **Yes, minor.** Doesn't mention that worker-quality failed again under r7.6 HWO scaffolding, r7.7 A1+A2 child-toolset, or r7.8 T1 loop detector. An installer reading DESIGN today would think r7.6 work is still pending. | Add a short "Campaign history through r7.8" paragraph or link to an updated PROBE-RESULTS. |
| `variants/hermes/INSTALL.md` | Accurate install-procedure-wise. | No (install procedure has not changed). | — |
| `variants/hermes/DEPENDENCIES.md` | Accurate. `OMLX_SWAP_MAX_GB` note exists nowhere — a r7.7 finding added that 5.5 was too aggressive and 30 is the tuned value. | **Yes, minor.** Add tuned `OMLX_SWAP_MAX_GB=30` + note about pre-probe oMLX restart (per MEMORY.md `omlx_degradation_contaminates_probes`). | One-paragraph addition. |

### Campaign-arc docs (evolve with findings)

| File | Current state | Needs update? | Scope |
|------|---------------|---------------|-------|
| `variants/hermes/PROBE-RESULTS-r7.md` | §17 ends at r7.4 β-fuse. §18 is r7.3 P1 resolution. **No §19+ for r7.5 / r7.6 / r7.7 / r7.8.** The document's title "r7, r7.2, r7.3" and its executive summary reference only A→E variants. This is the *most stale* document in the tree. | **Yes — largest update needed.** A user following the campaign-arc doc stops at r7.4 and has no pointer to the r7.5 pre-release notes or any subsequent campaign. | Add §19 (r7.5 worker-quality gate introduction + HOLD-narrow), §20 (r7.6 Arms A/B HWO-scaffold campaign, 4/20 vs 8/17 — HOLD), §21 (r7.7 Arms F/G A1+A2+HWO campaign, 7/20 and 5/20 — HOLD), §22 (r7.8 Arms K/K' T1 loop detector vs vanilla baseline, 2/20 and 4/20 — HOLD + substrate-ceiling finding). Prefer concise summary tables + links to MORNING-SUMMARY artifacts rather than re-litigating each campaign. |
| `variants/hermes/NEXT-STEPS.md` | Documents the r7.6 agenda (W1-W6) as *not yet done*. In reality W1-W6 are collectively the r7.6/7.7 agenda and all landed as HOLD. | **Yes, substantial.** The existing "r7.6 agenda" section is now the ship log for what was attempted and rejected; the new "next steps" are the r7.9 Option α/β/γ/δ branches from r7.8 MORNING-SUMMARY. | Reframe: keep r7.6 agenda block but annotate each W# with its verdict. Add "r7.9 options" section reflecting substrate-ceiling finding. |
| `CHANGELOG.md` | r7.5 entry is complete and accurate for what shipped at that tag. **No r7.6, r7.7, or r7.8 entries** — there was nothing to tag, but there was work, findings, and a ceiling diagnosis. | **Yes, optional.** CHANGELOG can either (a) add unreleased "r7.6–r7.8 campaign arc — HOLD, ceiling finding" block under a `## Unreleased` heading, or (b) stay silent until there is something to ship. Option (a) is more honest for a dev reading the file; option (b) preserves the "only ships get CHANGELOG entries" discipline. | Short `## Unreleased — r7.6/7.7/7.8 campaigns (HOLD, no tag)` paragraph + table. |
| `variants/hermes/HERMES-WORKER.md` | **UNTRACKED on Mac.** Created 2026-04-19 for r7.6 child-session doctrine. Listed nowhere in the r7.5 tag. | **Yes, decide-then-act.** Either commit (with annotation: probe-local, layered in by `probe-variantH-stage.sh`, did not clear ship gate), OR delete. Currently lives in a half-state: it's in the canonical `variants/hermes/` directory but isn't tracked, so a clone doesn't see it. | See "Untracked" tables below. |

### Release-notes / CHANGELOG

| File | Current state | Needs update? | Scope |
|------|---------------|---------------|-------|
| `RELEASE-NOTES-r7.5-hermes-prerelease.md` | Accurate for r7.5. "What's NEXT (r7.6 agenda)" section is now stale (agenda was worked, result was HOLD). | **Yes, add postscript; do NOT rewrite the body.** The tag is immutable on GitHub; rewriting the body creates a confusing dual-history. Instead, prepend a short "UPDATE 2026-04-21" note at the top pointing to the r7.6/7.7/7.8 campaign-arc artifacts + the substrate-ceiling finding, and leave the original content intact below. | 10-20 line preamble: "This release notes file captures r7.5. Three subsequent HOLD campaigns (r7.6 HWO; r7.7 A1+A2; r7.8 T1 loop detector) did not close the worker-quality gate. The r7.5 pre-release tag on GitHub is immutable and still reflects the state at its creation. For post-tag campaign arc, see `ARTIFACT-r7.{6,7,8}-MORNING-SUMMARY.md`." |
| `CHANGELOG.md` | See above. | See above. | See above. |

### Untracked Mac-only files that SHOULD be committed before next tag

| File | Why | Commit? |
|------|-----|---------|
| `ARTIFACT-r7.{6,7,8}-MORNING-SUMMARY.md` | Top-of-campaign narratives for the three HOLD campaigns; the r7.8 one holds the "substrate is ceiling" finding. | **Y** |
| `ARTIFACT-r7.6-synthesis-verdict.md`, `ARTIFACT-r7.7-S9-ship-judge.md` | Load-bearing HOLD verdicts; anchor for why the HWO scaffold / A1+A2 work didn't clear. | **Y** |
| `CALIBRATION-r7.6-judge-protocol.md` | Reusable fresh-context judge protocol used across r7.6/7.7/7.8. | **Y** |
| `PLAN-r7.6-P1C-*.md`, `PLAN-r7.7-path-A-*.md` | Plans that produced the campaigns; historical, not active. | **Y** |
| `variants/hermes/HERMES-WORKER.md` | r7.6 child-session doctrine; probe-local. Same tier as `HERMES-variantB/D/E/F.md`. | **Y with "probe-only; not canonical" header** |
| `variants/hermes/write_before_claim_gate.py` | A2 detect-only gate module; probe-infra sibling of `delegate_worker_v2.py`. | **Y** |
| `variants/hermes/test_delegate_worker_v2_a1.py` | A1 unit tests; cheap to retain. | **Y** |
| `probe-variantH-{stage.sh,wrapper.sh,check.py}` | r7.6 harness layered on G. Sibling of already-shipped `probe-variantF/G-*`. | **Y** |
| `probe-variantI-*`, `probe-variantJ-{A1-stage,A2-stage,wrapper}.sh` | r7.7 Path A split-stage harness + env-forwarding wrapper. | **Y** — reproducibility of r7.7 numbers. |
| `probe-preflight.sh` | r7.7 pre-probe env check; sibling of `probe-omlx-health-check.sh` (in tag). | **Y** |

### Untracked Mac-only files that should NOT be committed

| File or glob | Why excluded |
|--------------|--------------|
| `ARTIFACT-r7.6-judge-brief-*` (~44), `-verdict-*` (~40), `-worker-quality-arm{A,B}-*` (40) | Per-trial audit-trail. Aggregate in MORNING-SUMMARY + synthesis-verdict. |
| `ARTIFACT-r7.7-judge-Arm{F,G}-T*-run*` (40), `ARTIFACT-r7.8-judge-Arm{K,KP}-T*-run*` (40) | Same — per-trial verdicts. |
| `ARTIFACT-r7.6-{P1C-*,inv-*}`, `ARTIFACT-r7.7-{S0,S7,S8,planreview,A1,A2}-*`, `ARTIFACT-r7.8-P{1,2,3,5}*` (~45) | Per-phase process artifacts; covered by MORNING-SUMMARY at the summary level. |
| `PROGRESS-r7.7.md`, `PROGRESS-r7.8.md` | Session-state; already gitignored by pattern. |
| `probe-variant{H,I}-wrapper.sh.pre-rev2-fix{3,4}` | Script backups. `.gitignore`'s `*.pre-*-orig` doesn't match; extend glob or delete. |
| `/tmp/r7.8-judge-briefs/*` | Ephemeral; add `/tmp/r7.{6,7,8}-*` to gitignore or purge. |
| `.DS_Store` files | Already gitignored. |

## Recommendation: is a new pre-release warranted?

**No ship thesis for a second pre-release exists.** r7.5's thesis (β-fuse dispatch validated) still holds. Every subsequent campaign is exploratory work *against* a failing worker-quality gate, not progress *through* it. Three consecutive HOLD verdicts plus an "interventions land in noise band" finding is not shippable.

**Option A — annotate, no new tag.** Commit campaign-arc docs + probe-infra + RELEASE-NOTES postscript to main. r7.5 tag stays immutable. No false progress signal.

**Option B — new pre-release capturing all learned state.** Misleading: tag semantics = "milestone forward," not "plateau documented." A tag named `r7.8-hermes-campaign-arc` on a HOLD verdict confuses anyone who finds it on GitHub.

**Option C — defer until real worker-quality ship.** Purest tag semantics, but campaign-arc evidence still needs a home on main.

**Recommendation: Option A.** Commit campaign-arc docs on main; defer tag to the r7.9 (or later) campaign that actually closes the worker-quality gate. This matches r7.7/r7.8 MORNING-SUMMARY guidance: "Path A code stays on Mac as research artifacts… Pre-release tag `r7.5-hermes-prerelease` remains the operator-facing milestone."

The "substrate is ceiling" finding is load-bearing enough to deserve its own referenceable doc — recommend `variants/hermes/CEILING-FINDING-r7.8.md`, 1-2 pages, cross-linked from PROBE-RESULTS §22 and NEXT-STEPS.

## Concrete edits needed before a hypothetical next pre-release

1. **`RELEASE-NOTES-r7.5-hermes-prerelease.md`** — prepend 10-20 line "UPDATE 2026-04-21" preamble listing r7.6/7.7/7.8 HOLD verdicts + ceiling finding + link to PROBE-RESULTS §19-22. Do not rewrite body (tag is immutable).
2. **`variants/hermes/PROBE-RESULTS-r7.md`** — add §19 (r7.5 HOLD-narrow), §20 (r7.6 HWO 4/20, 8/17), §21 (r7.7 A1+A2+HWO 7/20, 5/20), §22 (r7.8 T1 loop detector + ceiling finding, 2/20 vs 4/20). Doc stops at r7.4 today — biggest gap.
3. **`variants/hermes/NEXT-STEPS.md`** — annotate each r7.6 W1-W6 agenda item with verdict; add "r7.9 options α/β/γ/δ" from r7.8 MORNING-SUMMARY.
4. **`CHANGELOG.md`** — add `## Unreleased — r7.6/7.7/7.8 (HOLD, no tag)` block, one paragraph per campaign + link to MORNING-SUMMARY.
5. **`variants/hermes/DESIGN.md`** — one paragraph: three subsequent HOLD campaigns landed in noise band of vanilla substrate; link to §22.
6. **`variants/hermes/DEPENDENCIES.md`** — add `OMLX_SWAP_MAX_GB=30` + pre-probe oMLX restart (r7.7 findings).
7. **Tracked-file drift: `HERMES-variantF.md`.** Either (a) commit Fix 4 anti-pattern #6 as tracked drift, or (b) revert to tag md5. Preferred: commit; Fix 4 is reading-layer only.
8. **Tracked-file drift: `delegate_worker_v2.py`.** Same choice. Preferred: commit, A1 is env-gated off by default.
9. **Commit `variants/hermes/HERMES-WORKER.md`** with probe-local header (mirror of HERMES-variantB/D/E/F.md convention). Currently in ambiguous half-tracked state.
10. **Commit `write_before_claim_gate.py` + `test_delegate_worker_v2_a1.py`** under `variants/hermes/`.
11. **Commit probe-variantH/I/J scripts** + `probe-preflight.sh`. Needed for reproducibility of r7.6/7.7 numbers.
12. **Commit campaign-arc artifacts** (selective): `ARTIFACT-r7.{6,7,8}-MORNING-SUMMARY.md`, `ARTIFACT-r7.6-synthesis-verdict.md`, `ARTIFACT-r7.7-S9-ship-judge.md`, `CALIBRATION-r7.6-judge-protocol.md`, `PLAN-r7.6-P1C-*.md`, `PLAN-r7.7-path-A-*.md`.
13. **Create `variants/hermes/CEILING-FINDING-r7.8.md`** — 1-2 page standalone doc for the Arm K' = 4/20 = r7.6 Arm A result, cross-linked from PROBE-RESULTS §22.
14. **Extend `.gitignore`** to catch `*.pre-rev2-fix*` or rename backups on disk to match `*.pre-*-orig` pattern.

## Files to purge before tag

Even under Option A (no new tag), before any commit-and-push event, purge or archive:

1. **~200 per-trial files** — `ARTIFACT-r7.6-judge-brief-*` (~44), `-verdict-*` (~40), `-worker-quality-arm{A,B}-*` (40), `ARTIFACT-r7.7-judge-Arm{F,G}-*` (40), `ARTIFACT-r7.8-judge-Arm{K,KP}-*` (40). Audit-trail only; aggregate preserved in MORNING-SUMMARY + synthesis/S9 verdicts. If preservation required, stash in `archive/hermes-probe-r7.{6,7,8}-2026-04-{20,20,21}/` (matches existing `archive/hermes-probe-r7-2026-04-18/` convention).
2. **~45 per-phase artifacts** — `ARTIFACT-r7.6-P1C-{fix,diag}-*`, `-inv-{1..4}-*`, `ARTIFACT-r7.7-{S0,S7,S8,planreview,A1,A2}-*`, `ARTIFACT-r7.8-P{1,2,3,5}*`. Process noise; archive or purge.
3. **Probe-script backups** — `probe-variant{H,I}-wrapper.sh.pre-rev2-fix{3,4}`. Delete from working tree.
4. **PROGRESS files** — `PROGRESS-r7.{7,8}.md`. Already gitignored by pattern.
5. **`/tmp/r7.8-judge-briefs/`** — ephemeral; purge or extend gitignore glob.

Total purge-or-archive: ~290 Mac-local files. Net commit target: ~25 files (3 campaign-arc summaries, 4-5 protocol/plan docs, 6-8 probe-infra scripts, HERMES-WORKER.md + 2 helper scripts, 2 tracked-file drift commits, 6 doc edits).

---

**Audit summary.** HERMES.md canonical md5 intact across all campaigns — the strongest single invariant in the project. Two tracked files drifted (variantF.md +1 anti-pattern line; delegate_worker_v2.py +64 env-gated lines); both should be committed-with-annotation or reverted. Largest documentation gap: PROBE-RESULTS-r7.md stops at r7.4 and NEXT-STEPS.md reads r7.6 agenda as pending. Largest narrative gap: r7.8's substrate-ceiling finding has no permanent home. Recommended: Option A (annotate + commit campaign-arc on main, no new tag). Defer any new pre-release tag until a real worker-quality ship.
