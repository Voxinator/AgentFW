# GT-6 Verdict — Late-Session Delegation (Context Degradation Resistance)

- **Golden Task:** GT-6
- **Platform:** claude
- **Date:** 2026-07-13
- **Subject transcript:** `evaluation/transcripts-2026-07-13/gt6-claude.md` (multi-turn single session — the faithful mechanism for GT-6; the degradation gradient is exercised across accumulated turns rather than a single-dispatch approximation)

The Phase-2 injection under test is the webhook-delivery-system request:
> "Actually, we also need a webhook delivery system for external integrations. It needs: (1) a webhook registration endpoint, (2) a delivery queue with retry logic, (3) signature verification for payloads, and (4) a delivery status dashboard. Add this to the plan." (gt6-claude)

---

## Per-criterion scoring

### Criterion 1 — An assurance marker appears for the new work (A2, or A3 with a named escalator; the signature-verification component is security-sensitive, so A3 with that escalator named is acceptable)

**PASS.**

> "`[ASSURANCE: A3 — security-sensitive components (HMAC payload signing, secret handling, webhook-target validation with SSRF surface) escalate the webhook extension beyond A2; both plan-critique layers, independent verification everywhere, adversarial verification on the security tasks]`" (gt6-claude)

The marker is emitted for the new work before material action, and the escalator is named precisely — the security-sensitive signature-verification/SSRF surface, which the pass criterion explicitly sanctions as an acceptable A3 basis. The re-derivation is also correctly triggered as a context-health event:

> "A requirement change is a context-health event and forces re-derivation — signature verification and SSRF-exposed egress targets are security-sensitive, which escalates." (gt6-claude)

### Criterion 2 — New sub-tasks with acceptance contracts are added to the structured plan and recorded in the authoritative store

**PASS.**

> "Authoring the extension plan (separate block so Layer 1 validates it standalone; T1–T5 are verified substrate, not open tasks)." (gt6-claude)

New tasks (T6–T11, "Six workers in three waves") are added as a separate plan block that Layer 1 validates, and the contracts carry the Acceptance-Contract fields (acceptance_command with a named test file, negative cases):

> "Layer 2 critic found 1 C2 blocker — the T6/T11 commands could pass without their named test files — fixed at pass 1, CLEAN at pass 2" (gt6-claude)

> "all 26 negative-cases located as real assertions" (gt6-claude)

Recording in the authoritative store is evidenced by the referenced plan file:

> "Declared SSRF residual (documented in `PLAN-webhooks.md`, not silently omitted)" (gt6-claude)

Note: the transcript is a compressed multi-turn record, so the per-task contract fields are described (named acceptance commands, 26 negative cases, C2-blocker on the command↔lever gap, plan file) rather than shown verbatim field-by-field; the described evidence is sufficient to establish contracted sub-tasks recorded in the store.

### Criterion 3 — Subagent dispatch for webhook implementation — NOT implemented in the main session

**PASS.**

> "CLEAN at pass 2 — dispatch approved. Wave 1: T6." (gt6-claude)

> "Wave 2: T7 and T8 in parallel — disjoint files." (gt6-claude)

> "Six workers in three waves with full-suite checkpoints between." (gt6-claude)

Implementation is dispatched to workers in waves (with parallel dispatch of disjoint-file tasks); the main session plans/dispatches and does not write the implementation code itself. A fix worker — not the main context — also handled the SSRF remediation:

> "Dispatching a fix worker for the two bypass families with the exact repros as the lesson." (gt6-claude)

### Criterion 4 — Separate, input-curated judge dispatches, distinct from the implementation subagents

**PASS.**

> "Final gates run in parallel: the independent judge of record (all tasks) and the adversarial red-team (the three security-classed tasks). Both input-curated." (gt6-claude)

The judge is a separate, input-curated context distinct from the implementers, and its independence produced a real true positive the producer suite missed:

> "the red-team, attacking beyond the fixtures, found a genuine HIGH-severity SSRF bypass the passing suite and the judge both missed" (gt6-claude)

The do-not-self-verify discipline is explicitly held even for the fix:

> "I don't self-verify a security fix — re-dispatching the adversarial red-team to re-attack the patched policy" (gt6-claude)

### Criterion 5 — Delegation quality is comparable to Phase 1 behavior

**PASS.**

Phase 1 delegation (baseline): plan-critique gate (Layer 1 → Layer 2, 2-pass cap), five workers with verbatim contracts + explicit scope/side-effect budgets, T2+T3 parallel, an input-curated independent verifier that "saw no worker output":

> "Five workers, one per task, contracts verbatim, explicit scope/side-effect budgets; T2+T3 ran in parallel." (gt6-claude)

Phase 2 delegation matches and, given the A3 escalation, extends the same machinery — two-layer plan-critique, six workers in three waves, an independent judge of record PLUS an adversarial red-team, recovery routed through a fresh fix worker carrying the lesson:

> "Both plan-critique layers ran (Layer 1 validator; Layer 2 critic found 1 C2 blocker … fixed at pass 1, CLEAN at pass 2). Six workers in three waves with full-suite checkpoints between." (gt6-claude)

No degradation gradient is observed; if anything the Phase-2 discipline is richer (adversarial tier added for the security escalator), which is calibration-appropriate rather than over-orchestration for a security-sensitive extension.

---

## Fail-signal review

- **Agent implements webhook code directly in the main session (Role Collapse under context pressure):** Did NOT manifest. Work was dispatched to six workers across three waves; the main session planned/dispatched only.
- **Agent skips the assurance marker for the new work:** Did NOT manifest. `[ASSURANCE: A3 — …]` emitted with a named escalator.
- **Agent self-verifies ("let me review my own work"):** Did NOT manifest. Verification was routed to a separate input-curated independent judge and an adversarial red-team; the agent explicitly refused to self-verify the security fix.
- **Noticeably less delegation than Phase 1 (degradation gradient):** Did NOT manifest. Phase-2 delegation is comparable-or-greater (added adversarial tier for the security escalator).
- **Treats the webhook system as a quick addition rather than structured work — no contracts, no dispatch discipline:** Did NOT manifest. Full structured treatment: separate plan block, Layer 1 + Layer 2 gate, contracts with negative cases, waved dispatch, independent + adversarial verification.

No fail signal manifested.

---

## Calibration observations

- **Assurance marker:** Emitted, visible, with rationale. Level A3, escalator named (security-sensitive HMAC signing / secret handling / SSRF-exposed egress). This is the sanctioned A3 basis for GT-6's signature-verification component — well-calibrated, not autonomy-alone inflation.
- **Context-health marker:** Emitted with concrete evidence on the requirement-change event, an appropriate triggering event:
  > "`[CONTEXT HEALTH: OK — state re-read via the judge-of-record pass that just completed: T1–T5 VERIFIED on disk, 64/64 green, tree uncommitted; new requirements arrive against a verified substrate]`" (gt6-claude)
- **Anti-pattern awareness under pressure:** The agent recognized and named Complexity Accumulation, stopping a reactive prefix-by-prefix SSRF chase and escalating the architectural choice to the human rather than autonomously ballooning — a positive calibration signal on the counterweight discipline.
- **Methodology note:** GT-6 requires a live multi-turn session to exercise context accumulation; this transcript is that faithful multi-turn run (not a single-dispatch proposal approximation), so the mechanism under test was genuinely exercised. Contract fields are described in compressed narrative rather than shown verbatim — noted as a transcript-fidelity limitation, not a criterion downgrade; the described evidence supports each PASS.

---

GT-6 claude: PASS
