# REPORT-skill-item9-n5.md (template)

Mirrors the structure r7.11 README references for `REPORT-r7.11-item9-n5.md`.
**Final structure may need adjustment when Brian's actual report lands.**

---

## Campaign metadata

- **Campaign:** skill-validation-2026-05
- **Question:** Does `r7-11-orchestrate` (the SKILL) hold the same RC threshold
  that `hermes_multi.py` (the SUBPROCESS) cleared at r7.11 item 9?
- **Pre-committed thresholds:**
  - Strict completion: acceptance command exits 0 AND zero HIGH findings under
    consolidation rules.
  - Charitable completion: strict, OR HIGH findings only on files whose tier-3.7
    acceptance test exercises them.
  - RC threshold: n=5, ≥3/5 strict.
- **Launch method:** OPTION A (TUI piped via `launch-tui.py`).
- **Model:** gemma-4-26b-a4b-it-8bit
- **Python:** 3.11.x in scaffold .venv (Hermes ABI match)
- **Scaffold:** `r7.10/scaffold-baseline/` (T6 fastapi+reportlab capability curve)
- **Skill SHA:** _(filled from manifest)_
- **AgentFW commit:** _(filled from manifest)_

## Trial-by-trial summary

Per Brian's call (2026-05-03): adherence is reported for every trial, INCLUDING
SUCCESS trials. A 5/5 strict outcome with 5/5 zero narrative_routing is a
different reliability story than 5/5 strict with 5/5 narrative_routing > 0.
Same work output, different architectural reliability. Adherence is where
the architectural argument gets made — surface it.

| Trial | Wallclock | Phases | Revisions | Strict | Charitable | seq | skip_vp | narr_route | inapp_end | partial_succ |
|-------|-----------|--------|-----------|--------|------------|-----|---------|------------|-----------|--------------|
| 1     | _s_       | _N_    | _N_       | _y/n_  | _y/n_      | _OK/V_ | _N_   | _N_        | _N_       | _y/n_        |
| 2     | _s_       | _N_    | _N_       | _y/n_  | _y/n_      | _OK/V_ | _N_   | _N_        | _N_       | _y/n_        |
| 3     | _s_       | _N_    | _N_       | _y/n_  | _y/n_      | _OK/V_ | _N_   | _N_        | _N_       | _y/n_        |
| 4     | _s_       | _N_    | _N_       | _y/n_  | _y/n_      | _OK/V_ | _N_   | _N_        | _N_       | _y/n_        |
| 5     | _s_       | _N_    | _N_       | _y/n_  | _y/n_      | _OK/V_ | _N_   | _N_        | _N_       | _y/n_        |

Columns: `seq` = sequential_loop_adherence; `skip_vp` = skipped_verify_phase_count;
`narr_route` = narrative_routing_count; `inapp_end` = inappropriate_session_end_count;
`partial_succ` = partial_success_misreport.

**Strict aggregate: _N_/5** — _RC threshold met / not met_.
**Charitable aggregate: _N_/5**.
**Adherence-clean aggregate (all five counts == 0): _N_/5.**

## Distribution analysis

- **Wallclock:** min/median/max
- **Revision counts:** distribution by phase
- **Phases chosen:** how skill decomposed the task across trials (count by N)
- **Failure modes:** catalog of what failed and why

## Architecture validation

For each trial, verifier-acceptance alignment:
- SUCCESS trial → did acceptance command pass? Were verifier findings empty?
- ESCALATE trial → did escalation fire on a real, operator-actionable issue?

Track-C adherence summary:
- Sequential loop adherence: _N_/5 trials clean
- Skipped verify_phase incidents: _N_ across 5 trials
- Narrative-routing incidents: _N_ across 5 trials
- Partial-SUCCESS misreports: _N_ across 5 trials

## Comparison to r7.11 item 9 (subprocess baseline)

| Metric | Subprocess (r7.11) | Skill (this campaign) | Delta |
|--------|--------------------|-----------------------|-------|
| Strict 5-trial pass rate | _N_/5 | _N_/5 | _±_ |
| Median wallclock | _s_ | _s_ | _±_ |
| Failure modes | _list_ | _list_ | _new/missing_ |

## Verdict

_one of: skill clears RC threshold (≥3/5 strict) and is r7.12 entry-point candidate
| skill misses RC threshold (<3/5 strict) and r7.12 needs further design conversation
| skill clears RC but adherence problems suggest specific scaffold-class fragility_

## Open follow-ups for r7.12

_(populated after analysis)_

---

## Track B — semantic check + PLAN authoring + resume probes

### B-2a (semantic content-type mismatch)

- Tier 3.5 finding: _yes / no_
- Orchestrator routing decision: _halted / advanced-anyway / advanced-with-warning_
- Conclusion: _verifier-from-orchestrator-context catches semantic concerns / is
  affected by dispatch-bias / inconclusive_

### B-2b (PLAN authoring comparison)

PLAN.md structural diff between orchestrator-authoring and subprocess-bootstrap:
- Phase count:
- Decomposition shape:
- Acceptance Command coverage:
- Path declaration completeness:

Downstream phase outcomes (same scaffold, different PLAN authors):
- arm 2b-orchestrator: _strict y/n, charitable y/n, revisions, wallclock_
- arm 2b-subprocess: _strict y/n, charitable y/n, revisions, wallclock_

### B-2c (resume scenario)

- Mid-phase-2 kill behavior observed: _description_
- Skill resume behavior on restart: _resumes correctly / errors / restarts from PHASE 0_
- Minimal change to add resume support: _scope estimate_

---

## Archive index

- `archives/trial-A-1/` — trial 1 (manifest, scaffold.tar, session.json,
  verified-state.json, score.json, adherence.json, tui.log)
- `archives/trial-A-2/` … through trial-A-5
- `archives/trial-B-2a/` — semantic break trial
- `archives/trial-B-2b-orchestrator/` — PLAN authoring arm 1
- `archives/trial-B-2b-subprocess/` — PLAN authoring arm 2
- `archives/trial-B-2c/` — resume probe
