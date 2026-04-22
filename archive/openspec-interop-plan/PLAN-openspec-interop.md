# Plan — OpenSpec Interop (Loose Coupling)

## Objective

Position AgentFW to work synergistically with OpenSpec (Fission AI, https://github.com/Fission-AI/OpenSpec) when it is present in a project, while preserving AgentFW's ability to stand alone without any external spec tooling. Deliver this as an additive, reversible layer that does not alter AgentFW's core identity as a meta-cognitive harness.

## Non-goals

- Do NOT adopt OpenSpec's delta-spec format, RFC 2119 vocabulary, or Given/When/Then structure as AgentFW's native artifact format.
- Do NOT require OpenSpec (the CLI or the file convention) to be installed for AgentFW to function.
- Do NOT reference OpenSpec from `core/` or `references/` except via the Reference Index entry that points to the new playbook.
- Do NOT compete with OpenSpec on the artifact layer. AgentFW governs agent behavior; OpenSpec governs work products.

## Design Principles (load-bearing)

1. **Opt-in coupling.** Interop is activated by the presence of an `openspec/` directory in the project, or explicit user request. Nothing in the always-loaded core mentions OpenSpec.
2. **Standalone invariant.** Golden tasks GT-1 through GT-7 MUST continue to pass unchanged after interop work lands. This is the structural acceptance test.
3. **Additive preferred over modificative.** The primary change is a new file in `playbooks/`. Edits to existing files are limited to index anchors and at most one cross-reference note.
4. **Tool-agnostic framing where possible.** Describe the underlying pattern ("external behavior-contract specs as judge shielding input") so the playbook remains useful even if OpenSpec is replaced by Spec Kit, Kiro, or a bespoke AGENTS.md.
5. **Reversible.** Deleting `playbooks/openspec-driven.md` and the Reference Index line returns AgentFW to its exact prior state. No hidden state, no schema migration.
6. **Sourced.** Every claim about OpenSpec behavior in the playbook cites an OpenSpec doc URL so drift is detectable.

## Sub-Tasks

| ID | Description | Dependencies | Verification Method | Verification Criteria | Permission Scope | Status |
|----|-------------|--------------|---------------------|-----------------------|------------------|--------|
| T1 | Draft `playbooks/openspec-driven.md`. Scenario playbook describing: detection heuristic (is `openspec/` present?); role mapping (main session as planner dispatches OpenSpec commands; workers run `/opsx:apply`; judges run `/opsx:verify` cold); judge-shielding recipe (pass the delta spec, not the proposal reasoning); task-state mapping (AgentFW `completed`→OpenSpec artifact `done`; `verified`→archive eligible); permission scope defaults for `/opsx:apply` workers; "when to bail out of OpenSpec" (diagnostics, trivial fixes, research). Include 2 worked examples: one brownfield feature, one bug-fix that proposes a delta. | none | expert-subagent | Judge checks: (a) zero references to OpenSpec in `core/` or `references/` introduced by this task; (b) playbook is self-contained and readable without running AgentFW elsewhere; (c) every OpenSpec behavioral claim cites a URL; (d) playbook explicitly names what AgentFW contributes that OpenSpec does not (roles, permissions, judge shielding, diagnostics, context-health); (e) playbook names one "do not do this" per direction (don't dump AgentFW state into OpenSpec artifacts; don't let OpenSpec fluidity override AgentFW gates). | read: entire AgentFW tree, write: `playbooks/openspec-driven.md` only, run: none, deny: edits to core/, references/, evaluation/, templates/ | planned |
| T2 | Add a single Reference Index entry in `core/harness-core.md` under the Reference Index section pointing to the new playbook. Must remain a single line. Description should read as tool-specific ("OpenSpec-driven…") not as a general pattern — keeps it clearly opt-in. | T1 verified | human-review | Diff shows exactly one added line in the Reference Index block. No other changes. Line length under ~120 chars. No edits to Critical Rules, Harness Mindset, Core Pattern, Architecture, or any other section. | read+write: `core/harness-core.md`, deny: every other path | planned |
| T3 | (OPTIONAL) Add one cross-reference note in `references/prompt-design.md` under judge-shielding guidance: "If the project uses an external behavior-contract spec (see `playbooks/openspec-driven.md` for OpenSpec specifically), that spec is an ideal judge input — it is already shielded from worker reasoning by construction." Tool-agnostic framing; OpenSpec named only as the example. | T1 verified | human-review | One added sentence or short paragraph. No restructure. No edits to other files. Note is phrased generically; the pointer to OpenSpec is the only tool-specific element. If reviewer judges this edit adds friction to readers who don't use external specs, abandon this task rather than merge it. | read+write: `references/prompt-design.md`, deny: every other path | planned |
| T4 | (OPTIONAL) Add GT-8 interop regression to `evaluation/golden-tasks.md`. Scenario: "Given a project with an `openspec/` directory and a pending change folder, implement and verify the change using AgentFW roles." Pass criteria: main session dispatches a worker for `/opsx:apply`, dispatches a DIFFERENT sub-agent for verify, judge receives the delta spec (not worker reasoning), `completed` gate blocks archive until `verified`. Fail signals: single-context implement-and-verify; judge receives proposal.md reasoning; archive runs before verified. | T1 verified | human-review | New GT-8 section appended. GT-1..GT-7 unchanged (diff-verifiable). Pass/fail criteria concrete. Includes setup step: "if openspec CLI not installed, skip and note in eval report" (keeps suite runnable without OpenSpec). | read+write: `evaluation/golden-tasks.md`, deny: every other path | planned |
| T5 | Standalone-invariant verification. A separate judge sub-agent reads the final diff set from T1..T4 and confirms: zero imports/requires of OpenSpec behavior into AgentFW's loading path; GT-1..GT-7 text is byte-identical to pre-change; a reader who never opens `playbooks/openspec-driven.md` experiences AgentFW identically. Judge does NOT see the implementer's reasoning; receives only the diff and this criterion list. | T1, T2, and any completed optional tasks (T3, T4) all verified | expert-subagent | Verdict: PASS if all invariants hold. Specifically fails if: any non-index line of `core/` references OpenSpec; any change to Critical Rules; any change to golden tasks GT-1..GT-7; any new required file for AgentFW to function. | read: full AgentFW tree + plan diff, write: none, deny: all mutations | planned |

## Sequencing

- **T1 must complete and verify before T2/T3/T4** — the playbook is the contract; everything else is anchors that point to it.
- **T2, T3, T4 are independent** of each other and can run in parallel workers after T1 verifies. Each writes to a distinct file.
- **T5 is the terminal gate.** It runs only after every other activated task has reached `verified`, not `completed`.
- **T3 and T4 are optional.** Merge them only if T2 has already verified AND T3/T4 themselves each pass their own judge gate without pushback. If either feels like scope creep when drafted, abandon it — the plan degrades gracefully to just T1+T2+T5.

## Risk Areas

1. **Scope creep into core.** The most likely failure mode. A well-meaning reviewer or future edit will want to add "if using OpenSpec, do X" into `core/harness-core.md` or a reference file. T5's judge is the structural defense; the `deny:` clauses in T2/T3 scopes are the tactical defense.
2. **Playbook rot.** OpenSpec is in active development (v1.3.0 released 2026-04-11; 5 commits in the four days prior to 2026-04-15). Mitigation: cite OpenSpec doc URLs for every behavioral claim so a future auditor can diff against current docs; include a "Last verified against OpenSpec vX.Y" line at the top of the playbook.
3. **Vocabulary collision.** AgentFW "task" ≠ OpenSpec "change"; AgentFW `completed` ≠ OpenSpec artifact `done`; AgentFW `PLAN.md` ≠ OpenSpec `proposal.md`+`design.md`. Mitigation: the playbook leads with a Vocabulary Table before any workflow description. Readers who skim still see the mapping.
4. **Philosophy-tension confusion.** OpenSpec preaches "dependencies are enablers, not gates." AgentFW preaches mandatory gates. A naive reader combining them may conclude the gates are optional. Mitigation: playbook has an explicit "Gates vs. Fluidity" section stating that AgentFW gates govern *agent behavior* while OpenSpec fluidity governs *artifact editing*; a worker may freely edit `proposal.md` mid-apply but may not skip the judge dispatch.
5. **Collision with in-flight r7 Opus 4.7 tuning work** (`PLAN-r7-opus47-tuning.md`, `ARTIFACT-worker-a.md`). Mitigation: interop work touches only `playbooks/openspec-driven.md` (new), one line of `core/harness-core.md`, and optionally `references/prompt-design.md` / `evaluation/golden-tasks.md`. r7 work should not need to touch `playbooks/`. Coordinate merge order with the other session before landing T2.
6. **Abstraction overreach.** Tempting to extract a generic `references/external-spec-integration.md` covering OpenSpec + Spec Kit + Kiro + bespoke AGENTS.md. Resist until there is a second concrete integration demanding it. One concrete playbook is evidence; two is a pattern; one-plus-speculation is complexity-accumulation (AgentFW anti-pattern #3).
7. **Standalone users pay a readability tax.** Every byte added to `core/` or `references/` is read by users who don't use OpenSpec. T2's single-line rule and T3's opt-out-if-it-adds-friction gate are the defense.
8. **Dogfooding risk.** Building the playbook itself with AgentFW's harness (a worker drafts, a judge evaluates) is the right demonstration, but the judge needs concrete criteria or it degenerates to rubber-stamp compliance (anti-pattern #9). T1's criteria list is intentionally specific and machine-checkable where possible (e.g., "zero references to OpenSpec in `core/`" is grep-able).

## Opportunities

1. **Positioning.** Ships a concrete answer to "how does AgentFW relate to OpenSpec/Spec Kit/Kiro?" — question that will recur as spec-driven tooling proliferates. Clean interop doc avoids accidental competition framing.
2. **Distribution.** OpenSpec has ~41k stars. A well-crafted playbook is candidate material for a PR into OpenSpec's docs/cookbook or a short post, expanding AgentFW's audience without diluting its identity.
3. **Dogfooding as the build.** The playbook can itself be the subject of an AgentFW harness demonstration — main session plans (this document), a worker drafts, a separate judge verifies. The process produces both the deliverable AND a live proof that the framework works.
4. **Gap discovery.** Writing the judge-shielding recipe for external specs may reveal that `references/prompt-design.md` is under-specified on "how to pass external artifacts to a judge." If T3 hits that gap, the note earns its place; if not, T3 is correctly dropped.
5. **Pattern seed (deferred).** If Spec Kit or Kiro interop is later requested, the OpenSpec playbook becomes the reference model and T6 (`references/external-spec-integration.md` — explicitly out of scope for this plan) becomes the right next move. Deferring this is the disciplined choice today.
6. **r7 cross-pollination.** Opus 4.7's `xhigh` effort and 1M context make it better suited to parse an external delta spec in full rather than being handed a summary. The interop playbook's judge-shielding recipe can be tuned for this in r7 without coupling the two efforts — interop lands model-agnostic, r7 refines independently.

## Context Budget

- **T1 (drafter worker):** the AgentFW README and `core/harness-core.md` (for the framework's self-description and Reference Index format); `references/prompt-design.md` (for judge-shielding norms); `playbooks/feature-dev.md` and `playbooks/bug-hunting.md` (for playbook style fidelity); OpenSpec's `README.md`, `docs/concepts.md`, `docs/opsx.md`, `docs/commands.md` (for accurate behavioral claims). Worker does NOT need: evaluation suite, templates other than `PLAN.md`, or any ARTIFACT-* / PLAN-* files from in-flight work.
- **T2 (anchor worker):** `core/harness-core.md` only, specifically the Reference Index section. Zero other context.
- **T3 (optional):** the judge-shielding paragraph(s) of `references/prompt-design.md`. Zero other context.
- **T4 (optional):** `evaluation/golden-tasks.md` and `evaluation/eval-protocol.md` for format fidelity. Zero other context.
- **T5 (terminal judge):** the full diff of T1..T4, the Design Principles section of this plan, and the pre-change content of `core/` files for byte-compare. Does NOT receive any task's implementation reasoning or worker output narrative.

## Success Criteria

PASS requires all of:

1. `playbooks/openspec-driven.md` exists, is self-contained, cites URLs, and includes the Vocabulary Table + Gates-vs-Fluidity section.
2. `core/harness-core.md` gains exactly one Reference Index line. No other changes.
3. Grep of `core/` for `openspec` (case-insensitive) returns exactly one hit — the Reference Index line.
4. Golden tasks GT-1..GT-7 are byte-identical to pre-change (no regressions to the standalone contract).
5. A reader who never opens `playbooks/openspec-driven.md` experiences AgentFW behavior identically to today. T5's judge attests.
6. If OpenSpec is not installed on the reader's machine, every AgentFW reference file still loads and parses.

FAIL signals:

- Any change to Critical Rules, Harness Mindset, Core Pattern, Planner-Worker-Judge Architecture, Permission Protocol, or Classification Gate.
- OpenSpec references appearing outside `playbooks/openspec-driven.md`, the single Reference Index line, and (if T3 lands) one named-example pointer in `references/prompt-design.md`.
- Any new file AgentFW's loading path requires.
- Playbook drifts into re-explaining OpenSpec's full workflow instead of describing the integration seam — duplicates their docs, rots faster.

## Next Action

Awaiting user approval of this plan. On approval, dispatch T1 worker with the Context Budget above and the T1 Verification Criteria as success contract. Do not dispatch T2/T3/T4 until T1 has been verified by a separate judge.
