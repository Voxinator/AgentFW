# Assurance Model — A0–A4

Replaces r8's task classes. Assurance is derived per unit of work from exactly three questions, emitted
as `[ASSURANCE: Ax — <one-line justification>]` before any material action, and challengeable like any
other decision. Controls scale with the level; the level never scales with how much work you feel like doing.

## Derivation — exactly 3 questions
- **Q1 Blast radius & reversibility:** what does this touch; can it be trivially undone?
- **Q2 Defect-escape probability:** can a defect plausibly escape the producer's own checks (integration seams, production-only behavior: concurrency, trust-proxy, streaming, clock)?
- **Q3 Autonomy & irreversibility:** is the agent operating unsupervised; is any step irreversible or outward-facing?

## Levels

| Level | Typical | Controls |
|---|---|---|
| A0 | lookup/explanation/tiny reversible edit | direct execution; producer check |
| A1 | bounded single-seam implementation | lightweight plan; producer tests (machine-checked) |
| A2 | multi-component / integration seams | decompose; independent verification at seams; Layer-1 plan validation; Layer-2 critique if ambiguity/shared values |
| A3 | production bug, security, infra, multi-file autonomous | independent workers + independent verifier; full acceptance contracts; both Plan-Critique layers; checkpoints |
| A4 | irreversible/destructive/critical autonomous | A3 + adversarial verification + explicit human authorization + rollback proof (restorability, not just backup integrity) |

**Worked examples:**
- **A0 — a lookup.** "What does this config flag do?" Q1: touches nothing. Q2: a wrong answer is caught
  on read. Q3: supervised, nothing irreversible. Direct answer; `[ASSURANCE: A0 — read-only lookup]` as
  a single short line.
- **A1 — a bounded function change.** Fix an off-by-one in one function that already has a test file.
  Q1: one file, trivially revertible. Q2: low — a unit test catches the realistic defect. Q3:
  supervised. Light plan, producer runs the tests, output recorded.
- **A2 — a multi-module feature.** Add an export feature spanning a data layer, a formatter, and a
  command surface. Q1: several files, still revertible. Q2: high at the seams — each module can pass its
  own checks while the integration fails. Decompose at the seams; each seam's acceptance is re-executed
  by an independent context; the plan passes mechanical validation before the first dispatch.
- **A3 — a production auth bug.** Sessions intermittently expire behind a reverse proxy. Q1:
  production, outward-facing users. Q2: high — the defect reproduces only in the deployed layer
  (trust-proxy behavior). Q3: partially autonomous. Independent producers plus an independent verifier;
  the acceptance must exercise the proxy layer itself, not a local stub; checkpoints between steps.
- **A4 — a history-rewriting migration.** Purge a leaked credential from repository history. Q1:
  destructive, shared history, not trivially undone. Q3: irreversible and outward-facing. Complete
  inventory of refs, tags, worktrees, and untracked files with each one's post-op state; rehearse on a
  mirror before touching the live repo; adversarial verification; PROVEN restorability — a restore
  actually executed, not a backup that merely exists — and explicit human authorization.

## Escalators
Any ONE bumps the level to ≥A3 regardless of the three answers:
- production / live infrastructure
- security-sensitive surface
- destructive / history-rewriting operation
- autonomous multi-file change

## Verification-tier binding
**Producer** verification always, at every level. **Independent** at A2 integration seams and all A3+.
**Adversarial** at A4, and for security/destructive work regardless of level. Evidence rules — recorded
machine-check output, freshness, the restart rule — live in `policy/core.md`.

## Why the marker is mandatory — and visible
The marker is a forcing function in an attention-based system. Classification gates behavior only if it
is emitted where the rest of the session can attend to it: a recorded-but-unemitted classification is a
decision nothing ever re-reads, and behavior silently drifts from it. Emitting `[ASSURANCE: Ax — …]`
costs one line and buys three things: the level is derived *before* the work shapes the justification;
a human or judge can challenge a misclassification at the moment it is cheapest to fix; and audit
becomes mechanical — a missing marker is a violation you can grep for, not a vibe. Skipping any control
the level demands requires naming the relaxation aloud; silence is not a relaxation. Adapters may hide
the marker from end-user display, but the model must still emit it — a marker that exists only as an
intention is Rubber-Stamp Compliance's quieter sibling.
