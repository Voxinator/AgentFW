# Track B-2b — PLAN authoring comparison

**Question (Brian's 2b):** Does the orchestrator-authored PLAN.md (skill
default) differ from a bootstrap-child-authored PLAN.md (r7.11 subprocess
pattern, retrofitted) in ways that affect downstream phase outcomes?

**Brian's call:** out-of-skill subprocess for the bootstrap-child path.
Retrofit-behind-a-flag introduces a confound (skill flag handling vs
authoring shape). Cleaner: skill-as-orchestrator-authoring run, vs
subprocess-bootstrap-child-then-handoff-to-skill run.

## Two arms, same scaffold

### Arm 2b-skill (skill-default authoring)
Standard r7-11-orchestrate skill drives PLAN.md authoring per its bootstrap
section (PHASE 0). One Hermes session start to finish. This is the same
codepath as Track A.

### Arm 2b-subprocess (bootstrap-child authoring, then hand off)
A subprocess Hermes session runs ONLY the PLAN.md bootstrap step:
- Reads USER-PROMPT.md
- Authors PLAN.md
- Exits (no phase work, no verify_phase)

Then a second Hermes session loads the r7-11-orchestrate skill and is told:
"PLAN.md exists at <path>; pick up from PHASE LOOP step 1."

This requires a small skill-side change OR a wrapper prompt that tells the
skill to skip PHASE 0. **Brian's preference is no skill change** — so the
wrapper prompt is the path.

## What we measure

Two PLAN.md outputs from the same USER-PROMPT.md, structurally diff'd:
- phase count
- phase decomposition shape (what each phase covers)
- Acceptance Command coverage
- Paths declarations (absolute vs relative, completeness)
- size estimates

Then both arms run the full phase loop with the SAME skill code, and we
compare:
- final verifier verdicts (strict, charitable)
- per-phase revision counts
- adherence counts

## Bootstrap-child driver (TODO)

Need a small `bootstrap-plan.sh` that:
1. Spawns a Hermes subprocess with a one-shot prompt: "Read USER-PROMPT.md
   at <path>. Author PLAN.md per the format taught by write_plan_md. Use
   write_plan_md to persist. Exit."
2. Waits for the subprocess to finish.
3. Confirms PLAN.md exists at expected path.

Then run-trial.sh in 2b-subprocess mode invokes bootstrap-plan.sh first,
then launches the skill with PHASE 0 marked complete via wrapper prompt.

## Brian's call (2026-05-03)

Wrapper prompt approach — `SKILL.md` stays identical between arms. The
arm difference is about whether the operator hands the skill a
pre-existing `PLAN.md` or not. That's a wrapper concern, not a skill
concern.

**Pre-flight check (before running 2b):** empirically verify how the
skill handles finding an existing `PLAN.md` in the scaffold root. Two
possible behaviors:

- **Graceful skip:** skill detects `PLAN.md` is already present and
  proceeds directly to PHASE LOOP step 1. No wrapper prompt change needed.
- **Overwrite or error:** skill tries to call `write_plan_md` again, or
  errors. The wrapper must explicitly tell the skill "PLAN.md exists,
  start from PHASE 1."

Run this pre-flight in a one-off scaffold (drop a hand-written PLAN.md
into a fresh reset, invoke the skill, observe). Document outcome here
before running arm 2b-subprocess.

## Pre-flight result — 2026-05-03

**Outcome: (c) — skill overwrites silently.** Run via
`hermes chat -q "Run r7.11 against /tmp/preflight-2b" -s r7-11-orchestrate -m gemma-4-26b-a4b-it-8bit --max-turns 40`.

- Pre-staged `PLAN.md` (sha `3fe0b04…`) was overwritten with the
  orchestrator's own decomposition (sha `d2655bb…`). The pre-staged
  content was discarded entirely; orchestrator did not even check for
  existence — it read `USER-PROMPT.md`, authored its own PLAN, and
  persisted via `write_plan_md` (errored, see below) → `write_file` (succeeded).
- Verdict: **2b-subprocess arm needs explicit wrapper-prompt language.**
  Proposed: prepend to the orchestrator prompt:
  > `PLAN.md` already exists at `<scaffold_root>/PLAN.md` and was authored
  > by a prior session. Read it and start from PHASE LOOP step 1. Do NOT
  > call `write_plan_md` or `write_file` to author or modify `PLAN.md`.
- Session: `20260503_183704_e9c27e` (1m 49s, 22 messages, 20 tool calls)

## Bonus findings surfaced by this pre-flight

These aren't 2b's question, but the run produced two findings worth
flagging to Brian as Track-A campaign risks:

### 1. `write_plan_md` raised `unhashable type: 'slice'`

```
❌ Error during OpenAI-compatible API call #5: unhashable type: 'slice'
  ┊ ✍️  write     /tmp/preflight-2b/PLAN.md  0.6s
```

The skill recovered by falling back to `write_file` for the same path,
but `write_plan_md` itself errored. May be a regression or different
code path than what the rc2 patch addressed. **Action: reproduce with a
fresh `hermes chat -q` call and surface to Brian if reproducible.**

### Update 2026-05-03 (run-3, rc2-patched)

After cherry-picking `c877201` (rc2: `write_plan_md` json.dumps fix) onto
`compat/hermes-v0.12` and re-staging Hermes, an identical pre-flight run
produced **end-to-end SUCCESS in 3m 41s**:

```
r7.11 SUCCESS
Phases: 2 verified_passed
Artifacts: src/calc.py, tests/test_calc.py
Acceptance: phase 2: .venv/bin/pytest tests/test_calc.py exited 0
```

- Slice error: GONE (write_plan_md succeeded, no write_file fallback)
- `end_session_for_handoff`: NOT CALLED
- PHASE LOOP: dispatch phase 1 → verify → revise (phase 1 needed retry)
  → verify → dispatch phase 2 → verify → SUCCESS marker

3/3 correlation across runs 1, 2, 3: slice-error-present → inappropriate-
handoff-called; slice-error-absent → handoff-not-called. Strong signal
that the slice error was load-bearing for the deviation. Not conclusive
at n=1 with rc2; Track A at n=5 will quantify reproducibility.

**One adherence finding even on the SUCCESS run:** `narrative_routing_count=1`.
Orchestrator advanced phase 1 → phase 2 without reading
verified-state.json between verify_phase and the next dispatch (skipped
PHASE LOOP step C). Worked because phase 1 was actually verified_passed,
but the same pattern on a failed verification would mis-route. Track-C
adherence will surface this at scale.

Evidence: `preflight-session-run3.json`, `preflight-tui-run3.log`,
`preflight-verified-state-run3.json` (all in this directory).

---

### Update 2026-05-04 — PLAN-shape comparison (preliminary, n=3 vs n=12)

Brian elevated 2b's importance after Track A trials 2 and 3 hit the
**cross-phase wiring trap** — the orchestrator-skill's PHASE 0 produces
decompositions that systematically separate definition from wiring.

Comparison of PLAN.md shapes across the same T6 USER-PROMPT.md:

| Source | Phases | Phase 1 path(s) | Cross-phase wiring tension |
|---|---|---|---|
| r7.11 item-8 trial 5.1 (bootstrap-child) | 4 | `src/export/serializers.py` (single file) | absorbed by phase 2's service layer |
| r7.11 item-8 trial 5.2 (bootstrap-child) | 4 | `src/export/serializers.py` (single file) | same |
| r7.11 item-8 trial 5.5 (bootstrap-child, 3-phase variant) | 3 | `src/export/serializers.py` (single file, "with ownership logic") | self-contained in phase 1 |
| **Track A trial 1 (orchestrator)** | 3 | **`src/export/csv.py`, `src/export/json.py`, `src/export/pdf.py`** | unsolvable in phase 1 → trial 1 spiraled less because lucky alignment with verifier; passed by accident |
| **Track A trial 2 (orchestrator)** | 3 | **`src/export/csv.py`, `src/export/json.py`, `src/export/pdf.py`, `src/export/formats.py`** | unsolvable → ESCALATE, 5 phase-1 revisions |
| **Track A trial 3 (orchestrator)** | 3 | **`src/export/csv.py`, `src/export/json.py`, `src/export/pdf.py`** | unsolvable → ESCALATE, 7 phase-1 revisions |

**Hypothesized mechanism:** the orchestrator-skill's PHASE 0 starts with
`ls -R <scaffold>` (visible at the top of every Track A tui.log). This
anchors authoring on observed scaffold stubs. The bootstrap-child in
r7.11 didn't have this constraint and authored from `USER-PROMPT.md`
alone, producing consolidated module decompositions (`serializers.py`
single file with internal dispatch) that pass `[CAT1:defined-unused]`
within phase 1's path scope.

**`bin/bootstrap-plan.py`** (added 2026-05-04) replicates the bootstrap-
child pattern: spawns a separate `hermes chat -q` session with no skill
loaded, prompted to author PLAN.md from USER-PROMPT.md alone (explicit
constraint: "do NOT explore the scaffold filesystem"). The 2b-subproc
arm uses this for the comparison.

`run-trial.sh --track B-2b-subproc` performs:
1. `reset.sh` (canonical scaffold, no PLAN.md)
2. `bootstrap-plan.py` to author PLAN.md from USER-PROMPT.md
3. Skill orchestrator launch with wrapper prompt: *"PLAN.md already exists … start from PHASE LOOP step 1. Do NOT call write_plan_md or write_file to author or modify PLAN.md."*
4. Standard archive + score + adherence

If 2b-subproc trials show consolidated PLAN shapes AND clear phase 1
wiring (no defined-unused trap), Brian's hypothesis is empirically
confirmed: the cross-phase wiring trap is a property of orchestrator
PHASE 0 authoring, not the skill's execution loop.

---

### 2. Orchestrator called `end_session_for_handoff` after phase 1

```
  ┊ 🔀 delegate  Implement phase 1 per PLAN.md (Core Implementation).  21.2s
  ┊ ✅ preparing verify_phase…
  ┊ ⚡ verify_ph   0.0s
  ┊ 🏁 preparing end_session_for_handoff…
```

`SKILL.md` is explicit: *"You do not need: end_session_for_handoff
(no session boundary to cross)"*. The orchestrator called it anyway.
Phase 1 verified_passed; phase 2 left as `pending`; session terminated.
This is **exactly the skill-adherence failure mode Brian's §5b track is
looking for** — the orchestrator was trained on the legacy bash-wrapper
runtime where `end_session_for_handoff` was the standard end-of-phase
signal, and that prior knowledge bled through despite the skill's
explicit "don't use this tool" guidance.

This is a Track A / Track C finding waiting to happen across n=5. The
adherence scorer needs to detect `end_session_for_handoff` calls and flag
them as an adherence violation. **Action: add an `inappropriate_session_end`
counter to `adherence.py`.**
