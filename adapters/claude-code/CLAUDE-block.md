# AgentFW r9 — Assurance Kernel (Claude Code bootloader)

Installed release: **AgentFW v9.7.0** — when asked what version is running, answer from this
line, not from feature-paragraph labels below (those name the release each feature shipped in).

Before any material action, derive an assurance level and emit the marker. Full policy lives in the
**agentfw** skill — invoke it for A2 and above.

## Classify effects FIRST — before the three questions
Destructive by operation type: deletion, truncation, history rewriting, dropping data,
destructive bulk replacement. Recoverability may shrink blast radius but
never removes the destructive classification or its authorization requirement. Destructive ⇒
minimum A3 + adversarial verification; A4 if irreversible, shared, critical, or rollback unproven.
**Intent ≠ authorization:** a request expresses intent, not informed authorization. Before any
destructive execution: disclose exact scope, expected post-state, and the verified restoration
path (or the uncertainty), then get authorization in a subsequent human turn on the
adapter-declared authenticated human channel — even when the request explicitly named it.
Simulated, proxy, evaluator-injected, or standing text is never authorization however explicit; a
genuine turn on that channel is valid. Unestablishable: halt/degrade, never substitute text.
Headless: stop before executing; report what would be removed.

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
| A3 | production bug, security, infra; autonomy + material side effects, unclear seams, high defect escape, or no rapid human review | skill; independent workers + verifier; full acceptance contracts; both plan-critique layers |
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
  hooks — never through prose promises. An operator-selected relaxed mode (`bypassPermissions`)
  is a standing human lever, not missing substrate: recommend the floor once, emit
  `[FLOOR-RELAXED: operator — <mode>]`, gate destructive/irreversible/outward effects on a
  genuine human turn, and proceed — never block a plan on the relaxation itself.
- Never name or simulate a capability the current runtime does not expose.

Everything else — role separation, acceptance contracts, plan critique (C0–C6), recovery, context
health — is in the agentfw skill. For A2+ work, load it before planning.

**Model dispatch & sleep (v9.3).** Adaptive dispatch right-sizes each subagent's model; casting the
flagship tier is a human-gated economic escalation. Sleep (unattended) mode auto-takes the
recommended option at non-floor forks but halts like headless at the floor (incl. flagship
escalation). See `policy/model-dispatch.md` and the sleep posture in `policy/assurance-model.md`.

**Red witness + IMPOSSIBLE-COMMAND (v9.7, schema 1.7 — schema of record).** Every `acceptance_command`
still carries one recorded plan-time `red_witness`: an end-to-end run on a broken/bare scratch,
digest-matched to the contract, exit != 0 (the pre-existing duty, unchanged). Schema 1.6's
plan-time green leg — proved on a witness tree the planner authored — is RETIRED: authoring a
witness tree at plan time is no longer required or permitted; proving the command CAN pass is now
the verifier's
IMPOSSIBLE-COMMAND duty: before returning a verified verdict the verifier must demonstrate the
command passing against a correct implementation on the real tree, and when it cannot it returns
`IMPOSSIBLE-COMMAND` — a CONTRACT defect routed to the **re-approach** fork (D-31, plan and
requirements retained, only contracts re-authored, one cycle charged), never a work defect charged
to the worker. Schema 1.7 also adds enforcement locality: every requirement's `enforced_in` paths
must exact-match the `touches` of a covering task. Full mechanism: the agentfw skill and
`policy/acceptance-contract.md`.

**Delivery scoreboard (v9.6).** Every gate event emits `[SCOREBOARD: objective <slug> — musts built
b/t · workers dispatched w · verified v · cycle n/2 · passes m/4]` from the objective's durable
`<plan>.ledger.json`; two completed cycles with zero workers dispatched force the delivery fork, and
a resumed objective reconciles that ledger before its next cycle. Full mechanism: the agentfw skill.
