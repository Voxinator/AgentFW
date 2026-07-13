# AgentFW r9 — Assurance Kernel (Claude Code bootloader)

Before any material action, derive an assurance level and emit the marker. Full policy lives in the
**agentfw** skill — invoke it for A2 and above.

## Derive assurance (3 questions, one line each)
- **Q1 Blast radius & reversibility:** what does this touch; can it be trivially undone?
- **Q2 Defect-escape probability:** can a defect plausibly escape the producer's own checks
  (integration seams; production-only behavior: concurrency, trust-proxy, streaming, clock)?
- **Q3 Autonomy & irreversibility:** unsupervised? any step irreversible or outward-facing?

| Level | Typical | Minimum controls |
|---|---|---|
| A0 | lookup / tiny reversible edit | direct execution; producer check |
| A1 | bounded single-seam change | lightweight plan; producer tests (machine-checked) |
| A2 | multi-component / integration seams | invoke agentfw skill; decompose; independent verification at seams |
| A3 | production bug, security, infra, autonomous multi-file | skill; independent workers + verifier; full acceptance contracts; both plan-critique layers |
| A4 | irreversible / destructive / critical autonomous | A3 + adversarial verification + explicit human authorization + rollback proof |

Emit `[ASSURANCE: A0|A1|A2|A3|A4 — <one-line justification>]` before material action. A0 may be a
single short line. No silent gate-skips: skipping a gate requires naming the relaxation.

## Non-negotiables
- **Verification evidence.** Nothing is *verified* without recorded machine-check output produced
  after the change. The producer always runs its own checks; an independent judge verifies at A2
  seams and at all A3+.
- **Input curation.** A judge receives only requirements + current state + acceptance criteria —
  never the producer's reasoning or self-assessment.
- **Side effects flow through native controls** — `settings.json` permissions (allow/ask/deny) and
  hooks — never through prose promises.
- Never name or simulate a capability the current runtime does not expose.

Everything else — role separation, acceptance contracts, plan critique (C0–C5), recovery, context
health — is in the agentfw skill. For A2+ work, load it before planning.
