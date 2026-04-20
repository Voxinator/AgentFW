# Plan — Hermes Flywheel × OpenSpec Integration (Prospective)

**Status:** PROSPECTIVE. Design-only. Do not implement until all activation gates below are cleared.
**Depends on:** Hermes Flywheel v2 shipped and proving economic case on Tetris Grid with fixtures alone (earliest ~r10+, conditional on r8 worker quality ≥70% and v1 dog-food success).
**Sibling docs:** `variants/hermes/DESIGN.md` (Hermes variant ship spec), flywheel design prospect (`Hermes Self-Improvement Flywheel — Design Prospect`, external), `/PLAN-openspec-interop.md` (base AgentFW ↔ OpenSpec loose-coupling plan — this plan inherits its posture).
**Audience:** You, six to nine months from now, when the flywheel has produced a real Tetris Grid win and the question "should we feed it OpenSpec specs?" becomes live.

---

## Objective

Position the Hermes Self-Improvement Flywheel to opt-in consume OpenSpec behavior contracts at three specific seams in v2.1+, while preserving the flywheel's ability to run end-to-end against any target using only fixtures and a composite metric. OpenSpec integration must be detectable, reversible, per-target, and add zero requirement on v1 (dog-food) or v2-initial (Tetris Grid with fixtures).

---

## Non-goals (category-error avoidance)

- **No OpenSpec in v1 (dog-food on `HERMES-variantD.md`).** The target is prompt-firmware; OpenSpec's own doctrine excludes implementation-detail from specs. Do not spec the harness.
- **No OpenSpec required in v2-initial.** Fixtures-alone must remain a sufficient eval surface. Adding `spec_source =` is always optional.
- **No adoption of delta-spec format as flywheel's native artifact format.** The proposer's output contract (`{rationale, diff, predicted_score_delta, confidence}`) stays as-is. target.toml stays TOML, not OpenSpec.
- **No reformatting of HERMES-CHANGELOG.md.** Auto-generated rationale stream is a different data shape than OpenSpec's archive. Cross-references are allowed; schema alignment is not.
- **No Python orchestration of OpenSpec calls inside Gemma.** Any `openspec` CLI invocation runs in the executor (process level), never from within a Gemma session. Preserves the Hermes variant's binding constraint.

---

## Design Principles (load-bearing)

1. **Opt-in per target.** Activation is a single field in target.toml: `spec_source = "openspec/specs/<domain>/spec.md"`. Absent → flywheel runs on fixtures alone, identically to v2-initial.
2. **Detection, not requirement.** Executor checks for `openspec/` directory + readable `spec_source`. If either is missing: log as warning, fall back to fixtures-only, continue. Never halts a nightly run.
3. **Reversible.** Removing the `spec_source` line from target.toml returns that target to fixtures-only behavior on the next run. No schema migration, no state rebuild.
4. **Gemma-friendly input shape.** OpenSpec content passed to Gemma respects the Jira-skill ceiling: simple flat structure, worked example of the expected reasoning move, no nested schema navigation. Spec content is delivered as pre-extracted plain text, not as a file path Gemma must parse.
5. **Inherits PLAN-openspec-interop.md posture.** Same loose-coupling stance — zero references in flywheel core docs, one contained integration seam, one opt-in playbook entry.
6. **Probe before adopt.** T5 (proposer grounding A/B probe) gates T2 and T4. If the probe shows Gemma performs worse with spec context, T2/T4 are abandoned and only T3 (judge seam, process-level, no Gemma cognitive load) proceeds.

---

## Activation Gates (must ALL be true before T1 starts)

| Gate | Criterion | Where verified |
|------|-----------|----------------|
| G1 | r8 worker quality holds at ≥70% on re-probe | `PROBE-RESULTS-r8.md` (doesn't exist yet) |
| G2 | Flywheel v1 (dog-food) has produced ≥1 week of digests that were actually read and acted on | `HERMES-CHANGELOG.md` accepted-diff entries |
| G3 | Flywheel v2 (Tetris Grid, fixtures-only) has shipped AND produced at least one non-gaming accepted diff on real Tetris code | Tetris Grid git log + flywheel digest archive |
| G4 | `/PLAN-openspec-interop.md` (base) has delivered its T1 (`playbooks/openspec-driven.md` exists and verified) | Repo grep |
| G5 | At least one Tetris Grid requirement has been hand-authored as an OpenSpec spec and validated with `openspec validate` | `openspec/specs/tetris-grid/spec.md` |
| G6 | OpenSpec version pinned in a `variants/hermes/.openspec-version` sentinel for drift detection | File exists |

If any gate is not green, this plan remains prospective.

---

## The Three Seams (recap of the fit analysis)

| Seam | Flywheel component | What OpenSpec contributes | Gemma cognitive load |
|------|--------------------|---------------------------|----------------------|
| **S1 Proposer grounding** | Proposer prompt context | Spec requirements appended as "target behavior contract" text | Moderate — Gemma must reason against requirements while generating diff |
| **S2 Judge criteria source** | Judge prompt context (shielded from proposer rationale) | Spec requirements passed as scoring criteria | Low-moderate — Gemma evaluates against enumerated criteria, a shape the Jira pattern already fits |
| **S3 Eval sub-metric** | Executor scoring pipeline | `openspec_requirements_satisfied` count as weighted composite term | Zero — runs in executor, no Gemma involvement |

S3 is the safest bet (no Gemma cognitive load). S2 is next (evaluation, not generation). S1 is riskiest (generation task, unknown if it helps or confuses Gemma-4-31B). Sequence reflects this risk gradient.

---

## Sub-Tasks

| ID | Description | Dependencies | Verification Method | Verification Criteria | Permission Scope | Status |
|----|-------------|--------------|---------------------|-----------------------|------------------|--------|
| T1 | Add optional `spec_source` field to target.toml schema. Parser treats absent/unreadable as fixtures-only mode with warning log. No other schema changes. | All G1–G6 green | schema-check | `target.toml` parser accepts schema with and without the field. Absent field → no behavior change vs. v2-initial. Unreadable path → warning logged, run proceeds. | read+write: `target.toml` parser and schema file only, deny: executor, proposer, judge code | planned |
| T2 | **S1 Proposer grounding.** When `spec_source` is set, executor reads the spec file, extracts requirements (structured scrape of `### Requirement:` + `#### Scenario:` blocks), passes as pre-formatted plain text in proposer prompt under a dedicated `<target_behavior_contract>` tag. | T1 verified, T5 probe PASS | expert-subagent | Judge checks: (a) spec content reaches proposer as flat text, not as file-path reference; (b) without `spec_source`, proposer prompt is byte-identical to v2-initial; (c) proposer's `rationale` field references the spec when present (spot-check 10 experiments); (d) Gemma does not hallucinate spec content when spec is malformed/missing. | read+write: proposer prompt builder only, deny: judge, executor scoring, target parser | planned |
| T3 | **S2 Judge criteria source.** When `spec_source` is set, judge receives spec requirements as scoring criteria instead of (or alongside) the default criteria list. Judge prompt retains the shielding rule: no proposer rationale, no worker context. | T1 verified | expert-subagent | Judge sub-agent shielding is preserved (grep for `rationale` or `proposer` tokens in judge prompt → zero hits). Requirement-level verdict structure: judge output enumerates which requirements are satisfied/violated/unclear. | read+write: judge prompt builder only, deny: proposer context, executor scoring | planned |
| T4 | **S3 Eval sub-metric `openspec_requirements_satisfied`.** Executor invokes `openspec validate --json` on sandbox snapshot; parses per-requirement satisfaction; adds weighted term to composite metric. Weight configured per-target in target.toml. | T1 verified, G6 (version pinned) | test:shell | Unit test: sandbox with known-passing spec → sub-metric = 1.0. Sandbox with known-failing spec → sub-metric <1.0. Missing `openspec` CLI → sub-metric is null, composite metric falls back to fixtures-only weights. Never throws to halt the loop. | read+write: executor scoring module only, run: `openspec validate`, deny: proposer, judge | planned |
| T5 | **Proposer-grounding A/B probe.** Before T2 merges, run 50 experiments with spec in prompt, 50 without, on a single Tetris Grid target. Compare accepted-diff rate, rationale quality (weekly spot-check shape), and convergence speed. | T1 verified, at least 1 real spec authored | human-review | Probe result is a short report: "spec-in-prompt helps / hurts / no-signal." If helps by ≥5 percentage points on accepted-diff rate: proceed with T2. If hurts by any margin: abandon T2, proceed with S2+S3 only. If no signal: defer T2 to v2.2. | read: all flywheel infra, write: `variants/hermes/PROBE-RESULTS-flywheel-spec-grounding.md` only | planned |
| T6 | Morning digest enrichment: when spec is configured for a target, digest section "Requirements Coverage" lists satisfied/violated/unclear requirements across the night's accepted diffs. No format change when spec absent. | T4 verified | human-review | Digest generator reads per-experiment `openspec_requirements_satisfied` data if present, renders new section; omits section entirely when null. Digest for spec-less targets is byte-identical to pre-T6. | read+write: digest generator only | planned |
| T7 | Standalone-invariant verification. Separate judge sub-agent reads final diff set from T1–T6 and confirms: (a) removing `spec_source =` from any target.toml returns that target to fixtures-only on next run; (b) uninstalling the `openspec` CLI produces warnings but no halts; (c) v1 dog-food config contains zero references to OpenSpec; (d) `variants/hermes/DESIGN.md` is byte-identical to pre-change. | T1–T6 that are activated all verified | expert-subagent | PASS iff all four invariants hold. Explicit fail if any flywheel component requires OpenSpec to operate, or if dog-food scope gained OpenSpec surface. | read: flywheel tree + diff, write: none | planned |

---

## Sequencing

- **T1 is the atomic enabler.** Ships alone in a small PR. Nothing else can merge until T1 is verified.
- **T5 (probe) gates T2.** Do not build the proposer seam before the probe. This is the "probe before adopt" principle made concrete.
- **T3 and T4 can run in parallel** after T1 — they touch disjoint files (judge prompt vs. executor scoring). Both carry lower risk than T2.
- **T6 (digest) runs after T4** — requires T4's data shape in the experiment log.
- **T7 is terminal.** Runs after every activated task has reached `verified`, not `completed`.
- **T2 is optional.** Abandonment is a valid outcome if T5 probe shows it doesn't help. T3+T4+T6 can ship without T2.

---

## Risk Areas

1. **Gemma chokes on OpenSpec input (S1 failure).** Gemma-4-31B's proven ceiling is simple tool surfaces with worked examples. Feeding it RFC 2119 + Given/When/Then may overwhelm. T5 probe is the defense; T2 is abandonable. If the probe shows harm, S2+S3 still provide meaningful uplift without Gemma cognitive load.
2. **Over-specification drag.** Writing a spec for Tetris Grid adds human ceremony that fixtures alone don't. G5 (at least one spec authored by hand) gates activation — if the author can't sustain it, the plan correctly stalls rather than forcing automation onto an unmaintained spec.
3. **Vocabulary collision.** Flywheel "target" ≠ OpenSpec "change"; flywheel "experiment" ≠ OpenSpec "proposal"; flywheel "accepted diff" ≠ OpenSpec "archived change." Mitigation: this plan's tables are the vocabulary bridge; the playbook (base interop `playbooks/openspec-driven.md`) carries the reader-facing glossary.
4. **Coupling creep into target.toml schema.** Future temptation: add `spec_change_ref =`, `spec_archive_on_accept =`, `openspec_workflow =`. Resist. Every new field is another coupling surface. This plan authorizes one field only: `spec_source`. Any additions require a separate plan amendment.
5. **OpenSpec drift.** v1.3 today, active development. G6 (pinned version sentinel) is the defense; executor should log current installed version vs. pinned version and refuse to run if major version drifts.
6. **Judge rubber-stamping against spec.** S2 could degrade to "spec validation passed → accept diff" without real evaluation. Mitigation: judge output must enumerate per-requirement verdicts (not just a pass/fail aggregate), and digest surfaces any requirement that is "always satisfied" across the night (suspect weakness in criterion).
7. **Interference with in-flight flywheel work.** Flywheel v1 hasn't shipped. Design for OpenSpec integration now could bias executor/proposer architecture toward spec-aware shapes prematurely. Mitigation: this plan stays prospective. Zero code written, zero architectural reservations carved into v1 or v2-initial.
8. **Collision with `/PLAN-openspec-interop.md` scope.** Base interop plan covers AgentFW ↔ OpenSpec; this plan covers flywheel ↔ OpenSpec. Overlap is in the `playbooks/openspec-driven.md` content. Mitigation: this plan does not modify the playbook; it only consumes the patterns the playbook establishes. If the playbook doesn't exist yet (G4 gate), this plan blocks.

---

## Opportunities

1. **Requirement-level regression visibility.** When Tetris Grid accumulates 20+ requirements, "fixture #7 regressed" is lower-signal than "requirement 'reconciliation correctness' regressed under scenario 'partial-fill timeout'." Morning digest becomes richer at the same attention cost.
2. **Higher-signal proposer (if T5 passes).** Gemma gets to steer toward intent, not just away from negative composite-metric drift. Rationales become more targeted: "this diff addresses requirement X under scenario Y."
3. **Generalization pattern for future targets.** Once S2+S3 work on Tetris Grid, extending to a second target requires only authoring a spec + adding `spec_source =`. Near-zero integration cost per additional target.
4. **Cross-traceability.** Each accepted diff can link to the requirements it satisfies. Six months later, the CHANGELOG entry plus the spec archive answer "why does this code exist?" without archaeology.
5. **r9/r10 cross-pollination.** Opus 4.7's larger context and `xhigh` effort (from r7 tuning research) make passing a full spec to a Claude-powered judge (if Hermes variant ever allows hybrid) cheap and natural. This plan's S2 design is already hybrid-compatible — it treats the judge as a sub-agent, not as Gemma-specifically.
6. **Evidence for or against the broader "spec-driven AI" thesis.** If T5 probe shows Gemma performs better with specs, that's real data for AgentFW's own positioning. If it shows no change or harm, that's also data — possibly more valuable. Either way, the probe earns its place.

---

## Context Budget

- **T1 (schema worker):** current target.toml parser code only. Does not need proposer, judge, or executor internals.
- **T2 (proposer seam worker):** proposer prompt builder, the spec-scraping helper, one sample spec file. Does NOT need judge or executor.
- **T3 (judge seam worker):** judge prompt builder + shielding rules from `references/prompt-design.md`. Does NOT need proposer, executor, or T2's work.
- **T4 (executor scoring worker):** executor scoring module, `openspec validate --json` output format docs, sample validated spec. Does NOT need proposer or judge.
- **T5 (probe runner):** full flywheel, one real Tetris Grid target with `spec_source` configured, one without. Runs the nightly loop twice. Does NOT need T2 or T4 code to exist — T5 can run the probe via feature-flag or branch.
- **T6 (digest worker):** digest generator + one sample experiment log with S3 data. Does NOT need proposer or judge.
- **T7 (terminal judge):** full flywheel diff set, this plan, Design Principles section for criteria anchor. Does NOT receive any implementer's reasoning or narrative output.

---

## Success Criteria

PASS requires all of:

1. `spec_source` is the only new field in target.toml; all other schema surfaces unchanged.
2. v1 dog-food target.toml contains zero references to OpenSpec.
3. v2-initial (fixtures-only) Tetris Grid target.toml contains zero references to OpenSpec.
4. Removing `spec_source =` from any target returns it to fixtures-only on next nightly run, without restart, migration, or state rebuild.
5. `variants/hermes/DESIGN.md` and `variants/hermes/HERMES-variantD.md` are byte-identical pre/post.
6. Flywheel runs end-to-end on a machine where `openspec` CLI is not installed (warning emitted, fixtures-only mode active).
7. T7 judge attests the standalone invariant.

FAIL signals:

- OpenSpec references in `HERMES-variantD.md`, `HERMES.md`, `DESIGN.md`, v1 dog-food configs, or `core/` of AgentFW.
- Any flywheel component that throws/halts when OpenSpec is absent.
- target.toml gains more than one spec-related field in this plan.
- HERMES-CHANGELOG.md adopts OpenSpec archive structure or vice versa.
- T5 probe is skipped, and T2 ships anyway.
- Flywheel v1 or v2-initial is delayed by this plan (it must stay strictly prospective until the activation gates clear).

---

## What this plan is NOT

- **Not authorization to write any code.** This is a design track. Implementation begins only after all six activation gates clear.
- **Not a commitment to adopt OpenSpec.** If the probe (T5) shows Gemma performs worse with spec grounding, T2 is dropped. If T3+T4 don't show digest-quality uplift after 4 weeks of nightly runs, they're rolled back.
- **Not a replacement for the base interop plan.** `/PLAN-openspec-interop.md` stays the canonical AgentFW-wide integration plan. This document is a downstream, flywheel-specific consumer.
- **Not sized for the current moment.** Read this again in Q3 2026, after v2 has shipped a real win, not before.

---

## Next Action

None. Plan is prospective until activation gates G1–G6 are green. When that day arrives, first action is re-reading this plan against the then-current state of the flywheel and OpenSpec — both will have drifted — and updating the gates and seam descriptions before dispatching T1.
