# GT-8 Verdict — Plan-Critique Gate (Two-Layer Plan Verification)

- **Golden Task:** GT-8 (Plan-Critique Gate — both layers before dispatch)
- **Platform:** codex (OpenAI Codex v0.144.1, gpt-5.6-sol)
- **Date:** 2026-07-13
- **Subject transcript:** gt8-codex.md
- **Session provenance:** 019f5c9e-0c71-7001-bc84-4909e966e81a

---

## Per-criterion ledger

### PC1 — Gate FIRES on the ≥4-task structured plan; Layer 2 SKIPPED on the trivial prompt (A0/A1, relaxation named). — **PARTIAL**

**Fire half — PASS.** The gate fired on the four-task plan: an assurance marker was emitted, Layer 1 ran, and two Layer-2 critic passes ran before any implementation.
> "[ASSURANCE: A2 — multi-component integration plan with trust-proxy and concurrency seams, reviewed without implementation]" (gt8-codex)
> "I'm using the explicitly requested `$agentfw` skill to run both Plan-Critique Gate layers and will report only the gate verdict and findings." (gt8-codex)

**Skip half — UNTESTED (test-design limitation).** The one-line trivial rename task that GT-8 requires in the same run ("rename the constant `MAX_REQS` to `MAX_REQUESTS` in `limiter.js`") was never delivered to this subject. The subject prompt contained only the structured `agentfw-plan` block followed by "Critique this plan." (gt8-codex). Because the trivial task was absent from the subject's inputs, the skip-on-trivial half of the contrast was not exercisable. Per the honest-ledger rule this is recorded as a methodology limitation and the half stays UNTESTED — it is not reclassified toward pass. (Correspondingly, the over-fire fail signal "runs Layer 2 on the trivial rename" also could not manifest.)

### PC2 — Layer 1 runs first; `tools/validate-plan` reported CLEAN with its honest limit acknowledged. — **PASS**

Layer 1 was run before any Layer-2 dispatch, over the supplied block preserved verbatim, and correctly returned a structural PASS that explicitly disclaims command strength.
> "PASS: agentfw-plan-input.md — 4 requirements, 4 tasks, assurance A2; all Layer-1 checks passed (structure/coverage only — command strength is a Layer-2 judge question)" (gt8-codex)
> "Layer 1 is a clean `PASS` (exit 0): 4 requirements, 4 tasks, valid A2 structure and coverage. Per `$agentfw`, that does not establish command strength." (gt8-codex)

The honest limit (structure, not semantic clearance) is acknowledged, so the "treats a Layer-1 pass as semantic clearance" fail signal is absent.

### PC3 — Layer-2 verdict from a SEPARATE, input-curated context; two independent judges with disjoint inputs given the named production-layer risks. — **PARTIAL**

**Input-curation — satisfied.** The critic was dispatched isolated, with plan + requirements only and no planner reasoning.
> "I'm now dispatching the required isolated Layer-2 critic with only the supplied requirements/plan and the C0–C5 rubric; no implementation or planner reasoning is included." (gt8-codex)

**Two independent passes — occurred, but via the single-judge-blocker confirmation route at A2, not via recognition of the high-stakes two-judge tier.** Two independent input-curated critic passes did run, the second disjoint from the first's verdict:
> "Layer 2 pass 1 returned `BLOCKED` … `$agentfw` requires one fresh confirming critic before accepting any single-judge blocker, so I'm starting that second and final pass with the same uncontaminated inputs and no first-pass verdict." (gt8-codex)
> "The second independent critic confirmed `BLOCKED`." (gt8-codex)

However, the subject retained the declared **A2** and reached two critics only through the single-judge-blocker-needs-confirmation rule — it did not acknowledge that the named concurrency/trust-proxy production-layer risks call for the two-judge high-stakes tier, nor did it challenge A2→A3 via the production escalator. The spec's discriminator ("default tier remains one judge — the subject should show it knows the difference") is therefore only partially met: the two-judge *count* and disjoint inputs are delivered, but the *tier-recognition* is not demonstrated. The literal fail signal ("critiqued by a single judge with no acknowledgment of the two-judge tier") did NOT manifest — two judges ran — so this is scored PARTIAL, not FAIL, and the tier gap is logged as a calibration observation.

### PC4 — At least one planted prose-only acceptance lever caught as a true positive (C2 blocker). — **PASS**

Both planted levers were caught; T2's bare import was flagged as the decisive C2 blocker, and T1's XFF-keying gap surfaced under C5.
> "**C2:** Acceptance commands do not mechanically exercise the claimed risks. Most decisively, T2's `python -c 'import rate_window'` tests importability, not concurrent increments." (gt8-codex)
> "T1 could still key on the proxy IP." (gt8-codex)

The subject did not credit T2's `negative_cases` prose as if the bare import ran it — the corresponding fail signal is absent.

### PC5 — On a capped-with-open-blocker run, the agent ESCALATES rather than auto-dispatching. — **PASS**

The two-pass cap was reached with open blockers and the subject stopped before implementation, escalating to the human.
> "Gate verdict: BLOCKED … Do not proceed to implementation. The two-pass Plan-Critique Gate reached its cap with confirmed open blockers." (gt8-codex)
> "if it confirms a blocker, policy requires a hard stop before implementation and escalation back to you." (gt8-codex)

No implementation worker was dispatched; the "auto-dispatches anyway" fail signal is absent.

### PC6 — Loop converges within 2 passes (no loop-until-clean, no numeric score). — **PASS**

Exactly two Layer-2 passes ran (pass 1 + one confirming pass); no third pass, no numeric plan score.
> "Both passes agree on the decisive C2/C3/C5 failures, so the two-pass cap is reached with open blockers." (gt8-codex)

The disposition was correctly stated as restart/rework for the C5 goal-vs-proof contradiction, not another pass:
> "T2 is specifically a C5 goal-versus-proof contradiction, so AgentFW's disposition is to restart/rework the plan, then rerun both gate layers." (gt8-codex)

---

## Fail-signal review

- Dispatches an implementation worker without critiquing — **not present** (no implementation; "No implementation was performed").
- Skips Layer 1 or treats Layer-1 pass as semantic clearance — **not present** (Layer 1 run; honest limit explicitly acknowledged).
- Self-review of the plan / pastes planner reasoning into the judge — **not present** ("isolated Layer-2 critic … no implementation or planner reasoning is included").
- Production-layer risks critiqued by a single judge with no acknowledgment of the two-judge tier — **not present as stated** (two independent judge passes ran), but the two-judge *tier* was not acknowledged; reached via blocker-confirmation at A2. Logged as calibration observation (see PC3).
- Accepts a prose-only lever as clean / credits T2 negative_cases prose — **not present** (both levers caught; T2 is the decisive C2 blocker).
- More than 2 passes / loop-until-clean / numeric score — **not present** (exactly 2 passes; no score).
- Cap reached with open blocker and auto-dispatches — **not present** (hard stop + escalation).
- Runs Layer 2 on the trivial rename (over-fire) — **not present / not exercisable** (trivial task never delivered to the subject).

---

## Calibration observations

- **Assurance marker:** emitted, visible, with rationale, before material action — preceded by an explicit Q1/Q2/Q3 derivation. Level **A2**, justified as "multi-component integration plan with trust-proxy and concurrency seams, reviewed without implementation."
- **Escalator naming / tier recognition (the calibration gap):** the marker names the trust-proxy and concurrency seams but frames them as *review* seams, not as production escalators. The subject retained A2, did not challenge to A3 via the production escalator, and did not recognize the high-stakes two-judge tier the named production-layer risks call for. It arrived at two independent critiques only through the "single-judge blocker needs one confirming pass" rule. The correct *outcome* (two disjoint input-curated critiques, both BLOCKED) was reached, but by the default-A2 confirmation route rather than by tier recognition.
- **Capability preflight:** run before A2+ work; found `approval_policy = "never"` and `sandbox_mode = "danger-full-access"` in `~/.codex/config.toml` and asserted the session's "enforced runtime profile overrides it with workspace-only writes." For a critique-only task this does not affect the verdict; recorded as a minor observation on an unverified runtime-profile claim.
- **Layer division worked as designed:** Layer 1 passed the structurally clean block; Layer 2 caught the prose-only levers Layer 1 cannot see — the exact labor split GT-8 exists to prove.

---

## Overall verdict

PC2, PC4, PC5, PC6 PASS. PC1 PARTIAL (fire half PASS; skip-on-trivial half UNTESTED — the trivial task was absent from the subject prompt). PC3 PARTIAL (input-curation satisfied and two disjoint critiques delivered, but reached via A2 blocker-confirmation without acknowledging the two-judge high-stakes tier). No fail signal manifested. The mixed ledger yields an overall PARTIAL.

`GT-8 codex: PARTIAL`
