# PROGRESS — r7.8 (overnight autonomous campaign)

**Started:** 2026-04-20 late evening (handed off from r7.7)
**Operator:** Brian Taylor (asleep; approval pre-given)
**Reference plan:** r7.7's PLAN + MORNING-SUMMARY as ground truth for the state; r7.8 plan builds on top.
**North star:** **The harness is the product.** General-purpose harness on local inference through Hermes. Interventions must generalize across task types — not benchmark-tune T4/T5/T6/T10.

---

## Operator pre-approvals (for this autonomous run)

1. **oMLX protocol:** threshold `OMLX_SWAP_MAX_GB=30` stays; halt ONLY on observed SIGTERM in Hermes processes (not on DEGRADED alone). Operator has not seen pathological stale-session behavior since r7.1 at this scale.
2. **Intervention scope:** generation-layer modifications authorized (Gemma parser, sampler params via config/env, stop-token post-processor, Hermes generation loop with care). All with `.probe-r7.8-orig` backup + md5 pin pre/post + clean rollback. **Small-sample vet (2-5 trials) before committing to full 20-trial arm.**
3. **Probe matrix:** 2 arms × 20 = 40 trials (1 intervention + its ablation). Same pattern as r7.7 Arm F/G.
4. **Ship threshold:** no explicit floor for r7.8 ship-authorization (operator reviews campaign). **60% (12/20) is the signal threshold** for operator's external conversation about 31B-dense trials. Not a ship gate — just an "interesting enough" bar.
5. **No viable intervention found in planning:** produce a "HOLD-r7.8: no viable path on current substrate" doc + halt gracefully. Do NOT force a long-shot for its own sake.
6. **VM canonical at exit:** non-negotiable. Unchanged from r7.7.
7. **Tripwires + pre-release tag:** untouched. Hard limit.
8. **Context handoff:** if main-session context exhausts mid-campaign, write a clean handoff doc + PROGRESS-r7.8.md update and halt; a fresh morning session can pick up cold.

---

## Phases

| Phase | Goal | Budget | Status |
|-------|------|--------|--------|
| P1 — Research | Parallel sub-agents: failure-mode classification, parser analysis, sampler research, stop-token research | 1-2h | pending |
| P2 — Synthesis | Roll up P1 into ranked candidate interventions, each with "why this generalizes" justification | 30m | pending |
| P3 — Small-sample vet | 2-5 trials per top 2-3 candidates | 1h | pending |
| P4 — Design winner arms | Pick candidate + design Arm F′ + Arm G′ | 15m | pending |
| P5 — Probe matrix | 40 trials (20+20), batched, no detachment | 6-8h | pending |
| P6 — Judge matrix | 40 fresh-LLM judges in waves | 2h | pending |
| P7 — S9′ ship judge | Fresh-context verdict | 15m | pending |
| P8 — Morning summary | r7.8 campaign artifact for operator review | 30m | pending |

**Total estimate: 11-14h.** Overnight feasibility tight. Hand-off trigger if I approach context limits.

---

## Design criteria (applied to every candidate intervention)

Each candidate must pass ALL of:
1. **Generalization:** one-line "why this generalizes beyond T4/T5/T6/T10" (not "it helps T10")
2. **Rollback:** file md5 pinned pre-change; unstage returns bit-identical to pre-stage
3. **Substrate alignment:** targets the generation-layer failure modes identified in r7.7 S9 (channel pollution, finish_reason=length, degenerate loops, silent termination) — NOT already-addressed behavioral modes
4. **Operator-hardware-compatible:** Gemma-4-26B-A4B-MLX-8bit (MoE); no dense unless operator requests; no Qwen; no 122B
5. **Vet-first:** smallest-possible-trial-count spot check before 20-trial commitment

Failing any criterion = candidate rejected.

---

## Known constraints carried forward from r7.7

- Tripwire canonicals (hard gate on every stage script + mid-probe check):
  - `HERMES.md` = `0780c232a6cb52e13e432261f0d68ad9`
  - `SKILL.md` = `fb1a5a5208a6cf2fcb8252aac10397eb`
  - `jira-briefing.sh` = `a1dce6e989527686124d0860830627c9`
  - `useDashboard.ts` = `5503ee1c2ef7d635a020eea275e41239`
- Hermes version: v2026.4.8 / commit `86960cdb` / Python 3.11.15
- Model: Gemma-4-26B-A4B-MLX-8bit
- Pre-release tag: `r7.5-hermes-prerelease` immutable
- oMLX: `localhost:8000` on Mac / `10.211.55.2:8000` from VM
- Env file: `/tmp/r7.7-env.sh` (owner-only; OMLX_API_KEY + AGENT_DISPATCH_AVAILABLE=1 + OMLX_SWAP_MAX_GB=30)

---

*Campaign begins. Operator reviews in the morning.*
