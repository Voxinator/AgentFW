# Archive — Hermes Harness Execution Probe (r7, 2026-04-17/18)

This directory preserves 19 intermediate artifacts from the r7 Hermes-variant probe sweep. All findings are consolidated into the canonical docs at:

- `variants/hermes/DESIGN.md` — architecture + rationale
- `variants/hermes/IMPLEMENTATION.md` — install / rollback / exact diffs
- `variants/hermes/PROBE-RESULTS-r7.md` — measurement results, metric tables, verdict
- `variants/hermes/NEXT-STEPS.md` — follow-up work

Use the archive when you need raw evidence: session-by-session data, mid-probe judge reasoning, revert histories. The consolidated docs cite this archive by filename.

---

## Contents by phase

### Phase 1 — Initial deep-dive investigation (before probe sweep)
- `PLAN-deep-dive-hermes-r6.md` — plan for the investigation that opened the session (understand the r6 Hermes addendum, probe the live Hermes install)
- `ARTIFACT-workerA-addendum.md` — analysis of the pre-existing r6 Hermes addendum (PLAN-r6-hermes-addendum.md) — what it changes, what it assumes, gaps
- `ARTIFACT-workerB-agentfw.md` — AgentFW architecture analysis (core, references, playbooks, variants, evolution r5→r6→r7)
- `ARTIFACT-workerC-hermes-live.md` — live recon of the Hermes install on ubuntu-vm: model routing, HERMES.md loading, delegate_task source, session storage
- `ARTIFACT-judge-hermes-r6-synthesis.md` — first judge: three-way fit analysis between r6 addendum, AgentFW, and live install. Central finding: Hermes describes the harness but doesn't execute it.

### Phase 2 — Probe design and pre-flight
- `ARTIFACT-probe-blockers-resolved.md` — four pre-probe questions answered (session log location, HERMES.md drift check, sampling config, fresh-session mechanism)

### Phase 3 — Probe execution (Variants A through E)
- `ARTIFACT-probe-variantA-trials.md` — baseline control (current canonical HERMES.md, no harness gates). 0/10 marker emission, 0 dispatches, 2 destructive real-file mutations.
- `ARTIFACT-probe-variantB-trials.md` — hard output contract (classification gate + Critical Rules). 10/10 marker emission, 0 dispatches, 1 fabrication event.
- `ARTIFACT-probe-variantC-trials.md` — Variant B + generic runtime retry wrapper. 10/10 markers, 1/5 dispatch after retries, 3 wrapper errors from SIGTERM.
- `ARTIFACT-probe-variantD-trials.md` — Variant B + simpler tool surface (delegate_worker) + dispatch scaffolding. 10/10 markers, 2/5 first-attempt dispatch, 0 destructive mutations. The breakthrough.
- `ARTIFACT-probe-variantE-trials.md` — Variant D + role-collapse retry wrapper. 10/10 markers, 3/5 first-attempt / 4/5 final dispatch, 0 mutations. The ship candidate.

### Phase 4 — Judges (cold-context scoring passes)
- `ARTIFACT-probe-judge-verdict.md` — judge after Variant B: marker-only, recommended Path 2 (build Variant C wrapper).
- `ARTIFACT-probe-final-judge.md` — judge after Variants A/B/C: concluded "dispatch unmovable, externalize orchestration" (Path 4). **This verdict was later invalidated by the Variant D data** — marking here for audit trail.
- `ARTIFACT-probe-judge-final-v2.md` — judge after Variants A/B/C/D: diverged from v1, recommended Path C (combine D tool surface + C wrapper).
- `ARTIFACT-probe-judge-final-v3.md` — **final judge, after all 5 variants: SHIP verdict on Variant E, architectural thesis validated.**

### Phase 5 — Revert operations (Gemma-caused real-file mutations)
- `ARTIFACT-revert-varA-mutations.md` — surgical revert of 3 real-file mutations from Variant A trials (`useDashboard.ts`, `jira-briefing.sh`, harness files). Surgical str_replace inverse based on session tool_call data; no git ops (the affected directories weren't git repos).
- `ARTIFACT-revert-varC-mutations.md` — surgical revert of 1 real-file mutation from Variant C Trial 5 (`useDashboard.ts` re-mutated).

### Phase 6 — Superseded probe infrastructure
- `probe-variantC-wrapper.sh` — older retry wrapper targeting upstream `delegate_task`. Replaced by `probe-variantE-wrapper.sh` (targets `delegate_worker`, adds ROLE_COLLAPSE gate).
- `probe-variantC-check.py` — older gate checker. Replaced by `probe-variantE-check.py`.

---

## Chronology

```
2026-04-17 ~13:00 — Session starts; PLAN-deep-dive-hermes-r6.md written
2026-04-17 ~13:45 — Worker A, B, C dispatched in parallel
2026-04-17 ~15:15 — First judge (hermes-r6-synthesis)
2026-04-17 ~15:45 — Probe plan written (/PLAN-hermes-harness-probe.md, still at top level)
2026-04-17 ~16:30 — Probe blockers resolved
2026-04-17 ~18:10 — Variant A trials (30 min, baseline)
2026-04-17 ~18:25 — Revert Variant A mutations
2026-04-17 ~20:30 — Variant B trials
2026-04-17 ~20:45 — Variant B judge
2026-04-17 ~21:00 — Variant C built (wrapper + check)
2026-04-17 ~21:40 — Variant C trials
2026-04-17 ~21:55 — Revert Variant C mutation
2026-04-17 ~22:05 — Variants A/B/C final judge (recommended Path 4 — later invalidated)
2026-04-17 ~22:20 — Variant D designed and built (delegate_worker + HERMES-variantD.md)
2026-04-17 ~23:00 — Variant D trials (breakthrough: 40% dispatch)
2026-04-17 ~23:25 — Variant D final judge v2 (recommended Path C)
2026-04-18 ~00:05 — Variant E designed and built
2026-04-18 ~00:30 — Variant E trials (80% dispatch runtime-true)
2026-04-18 ~01:05 — Variant E final judge v3 (SHIP)
2026-04-18 ~04:00 — Documentation consolidation (this archive setup)
```

---

## How to use the archive

**If you need to verify a specific claim** in the consolidated docs (`PROBE-RESULTS-r7.md` etc.), find the matching trial artifact here. Each `ARTIFACT-probe-variant*-trials.md` has session paths, first-assistant-line snippets, tool-call sequences, and aggregate metrics.

**If you need to replay a judge's reasoning**, read the judge artifacts in chronological order:
1. `ARTIFACT-judge-hermes-r6-synthesis.md` (pre-probe; sets up the central question)
2. `ARTIFACT-probe-judge-verdict.md` (after B)
3. `ARTIFACT-probe-final-judge.md` (after A/B/C — the wrong-verdict that got invalidated)
4. `ARTIFACT-probe-judge-final-v2.md` (after D)
5. `ARTIFACT-probe-judge-final-v3.md` (after E — the SHIP verdict)

**If you need to understand a mutation revert**, `ARTIFACT-revert-varA-mutations.md` and `ARTIFACT-revert-varC-mutations.md` describe how surgical str_replace was used to revert Gemma's real-file edits without using git ops (since the target directories weren't git repos and contained uncommitted work).

**If you're adapting the probe infrastructure**, the Variant C wrapper + check are kept here as reference. Prefer the Variant E versions at `/Users/briantaylor/Projects/AgentFW/probe-variantE-{wrapper.sh,check.py}`.

---

## Do NOT modify archive contents

The archive is append-only (except for this README, which may be updated with further chronology/cross-references as the story evolves). If a future probe sweep (r7.1, r8) produces its own artifacts, create a sibling directory (`archive/hermes-probe-r7.1-YYYY-MM-DD/`) rather than adding to this one.

Rationale: each archive directory is a self-contained snapshot of one probe sweep, frozen at the time of the consolidation. Integrity of the historical record matters — the Path 4 judge verdict was wrong, but we preserve it as an audit trail showing the reasoning at the time.
