[TASK CLASS: long-horizon]
Justification: Multi-phase r7.5 rollout — turn-0 toolset restriction + SIGTERM fix + worker-quality probe. Multiple independent workstreams, pre-committed thresholds, judge verification gates, ship gate. MoE-only scope per operator direction 2026-04-19.

# PLAN — r7.5 Hermes β-fuse v2.1 + worker-quality ship gate

**Author:** r7.5 planner (main session), 2026-04-19 continuation of r7.4 session
**Operator:** voxinator@gmail.com
**Prerequisites met:** r7.4 Phase D complete (MoE 17/20 first-attempt strict PASS, SHIP-WITH-CAVEAT verdict); VM UNSTAGED canonical; PROBE-RESULTS-r7.md + CHANGELOG.md + NEXT-STEPS.md updated through r7.4; tripwires clean.

---

## 1. Goals and ship gate

**Primary goal:** produce a version of Hermes + AgentFW harness ("β-fuse v2.1") that clears two pre-committed thresholds on MoE, making it production-ready for canonical swap.

**Ship gate (BOTH must hold):**

1. **Dispatch reliability (MoE).** First-attempt `delegate_worker_v2` call with correct classification on structured/long-horizon tasks ≥17/20 strict on-disk (matches r7.4 MoE baseline; we want r7.5 not to regress; bonus if we exceed toward ~19-20/20 via turn-0 restriction).
2. **Worker quality (MoE).** Per-child-session quality ≥75% on structured/long-horizon trials where dispatch fired. Rubric defined in §5.

**Out of scope for r7.5:**
- Dense trials of any kind (deferred; hardware load issues with oMLX during long dense runs).
- Productionization / canonical HERMES.md swap (gated on r7.5 ship).
- IMPL-4 (8 operator questions still pending).
- Tier 3 of the SIGTERM plan (upstream Hermes signal handler) — nice-to-have, not ship-blocking.

**Explicitly not tested:** one-shot regression — r7.4's 12/12 result on MoE/dense is treated as settled unless r7.5 changes bind tools that would affect one-shot.

---

## 2. Workstream inventory

| WS | Name | Ship-blocking? | Depends on | Est effort |
|----|------|----------------|------------|------------|
| A | Turn-0 toolset restriction (β-fuse v2.1) | YES | — | ~4h impl + ~1h smoke |
| B1 | SIGTERM fix — wrapper mitigation (Tier 1) | YES | — | ~2h impl (from existing PLAN-r7.4-wrapper-sigterm-fix-design) |
| B2 | SIGTERM fix — check-script hardening (Tier 2) | YES | B1 | ~1.5h impl |
| B3 | SIGTERM fix — upstream Hermes handler (Tier 3) | NO (deferred) | B1/B2 | ~3h impl; post-r7.5 |
| C | oMLX hygiene (pre-probe restart + minimum tripwire) | YES | — | ~30min |
| F | Worker-quality rubric + probe + judge | YES | A, B1, B2, C complete | ~3h (rubric design + 20-trial MoE probe + judge) |
| SHIP | Ship decision on r7.5 | — | A, B1, B2, C, F all pass | ~15min |

Independence: A, B1, C are fully independent. B2 depends on B1 (new verdict string must be handled by wrapper). F depends on everything else landing first so the probe runs against the hardened surface.

---

## 3. Workstream A — Turn-0 toolset restriction

### Problem being solved

r7.4 found that dense (and to a lesser extent MoE at ~15% rate) sometimes calls `todo` or `search_files` as the FIRST tool on structured/LH tasks, bypassing `delegate_worker_v2`. These tools are bound in the current toolset (`delegation,todo,clarify,file_readonly`), so the model has legitimate choices other than v2. β-fuse's "no other way to satisfy the contract" property is partially defeated.

The post-restart T6-run1 FAIL (dense, `search_files` first) is the one clean-data-point example on dense. MoE showed 3/20 non-first-attempt trials but those were "empty first assistant response" — a different failure mode; MoE's dispatch *selection* was actually clean when it emitted anything. So turn-0 restriction closes a dense problem more than a MoE one, BUT: removing the choice ALSO tightens MoE's contract and should push MoE's 17/20 closer to 20/20. It's belt-and-suspenders.

### Design

**Approach:** add a new `beta_fuse_turn_0` toolset (or a toggle-flag in `run_agent.py`) that binds ONLY `delegation,clarify` until `delegate_worker_v2` has been called in the conversation. After v2 fires, the full `delegation,todo,clarify,file_readonly` toolset becomes available for subsequent turns (the worker child, if spawned, gets the full default Hermes toolset as before).

Two implementation options:

1. **New toolset + wrapper-side turn-switching.** Wrapper invokes turn 0 with `-t beta_fuse_turn_0`; after observing v2 was called, subsequent `--resume` invocations use `-t delegation,todo,clarify,file_readonly`. Requires wrapper logic to detect "v2 was called." Brittle (cross-turn state management).

2. **In-Hermes conditional binding.** Add a Hermes-side hook: during `toolsets.py` resolution, check the in-progress conversation for a prior `delegate_worker_v2` tool call in any assistant message; if none, bind only `{delegate_worker_v2, clarify}`; if one has fired, bind the full declared toolset. Cleaner — the turn-0 restriction is automatic, wrapper doesn't change. Requires a small patch in `toolsets.py` + `run_agent.py`.

**Recommend option 2.** It's a structural change, not a wrapper trick, and aligns with r7.4's β-fuse thesis ("the tool surface enforces the contract").

### Deliverables

- `variants/hermes/delegate_worker_v2.py` — unchanged; still the target tool.
- `variants/hermes/HERMES-variantG.md` — new teaching doc (inherits variantF; adds explicit note about turn-0 restriction invisible to the model). Actually: if the restriction is automatic (option 2), the model doesn't need to be told — it just *sees* fewer tools on turn 0. HERMES-variantF.md may be reusable. Design decision in §A.1.
- `probe-variantG-stage.sh` — new stage script derived from variantF's; patches `toolsets.py` (and maybe `run_agent.py` or a sibling `prompt_builder.py` — discover in implementation) to add the conditional-binding hook. Uses `.probe-r7.5-orig` backup suffix.
- `probe-variantG-check.py` — may be copy of variantF's with updated header / diagnostic fields; no gate logic change expected.
- `probe-variantG-wrapper.sh` — same as variantF; update header + default source prefix + check-script path. No correction-message changes.

### Hermes-side patch sketch (Workstream A core)

In `~/.hermes/hermes-agent/toolsets.py` or wherever per-invocation toolset resolution happens:
- Extract the set of previously-called tool names from the in-progress session's assistant messages.
- If resolving toolset `delegation,todo,clarify,file_readonly` AND the set does NOT contain `delegate_worker_v2`, override to `delegation,clarify`.
- Otherwise, resolve normally.

Subtlety: this needs the conversation-so-far to be available at toolset-resolution time. If it's not directly passed, plumb it. If plumbing is invasive, fall back to option 1 (wrapper-side).

### Verify

- Staged + direct Hermes invocation: first turn shows tools array with only delegate_worker_v2 + delegate_task + delegate_worker + clarify (4 tools, not 7). After v2 fires, subsequent turns show all 7.
- No regression on r7.4 smoke test: single MoE trial on T1 should classify one-shot via v2 and complete normally.

### Worker assignments

- Worker A.1 (implementation, ~2h): design + implement the conditional-binding hook in Hermes; stage via new `probe-variantG-stage.sh`; write impl notes artifact.
- Worker A.2 (verification, ~30min): fresh judge cold-verifies the staged turn-0 restriction via direct invocation tools-array inspection. Does NOT run a probe.

Both workers dispatched sequentially.

---

## 4. Workstream B — SIGTERM fix

Execute `/Users/briantaylor/Projects/AgentFW/PLAN-r7.4-wrapper-sigterm-fix-design.md` through Phase 4 (assembly) → then implement Tier 1 + Tier 2 as B1 + B2. Skip Tier 3 (Hermes upstream) — defer.

### B1 — Tier 1 wrapper mitigation (ship-blocking)

Per the design plan:
- `TIMEOUT_PER_TURN` env override: `: "${TIMEOUT_PER_TURN:=900}"`
- Anti-child-attachment content-match check in fallback recovery: after candidate session selected, read `messages[0].content[:80]` and require prefix-match against `$TASK_TEXT[:80]`; reject with `OUTCOME ... RESULT=ERROR detail=WRONG_SESSION` if not.
- `MAX_RETRIES` decision: for fallback-recovered sessions, drop to 1 (argue: fewer mis-attachment cascades; this is comparability-affecting but acceptable for r7.5 since we're already re-probing).

Deliverable: `probe-variantG-wrapper.sh` incorporates all three. Separate stage script NOT needed (wrapper is Mac-side).

### B2 — Tier 2 check-script hardening (ship-blocking)

- Add `ERROR:WRONG_SESSION` verdict to check.py.
- Parent-session structural test: compare `messages[0].content` against an expected-prompt-prefix passed via `--expected-prompt-prefix` flag from the wrapper. Choose variant (ii) from the plan — wrapper-check coupling is explicit.

Deliverable: `probe-variantG-check.py` with new verdict + CLI arg.

### B3 — Tier 3 deferred

Document in NEXT-STEPS.md that Tier 3 (upstream Hermes `signal.signal(SIGTERM, ...)` handler) is the durable fix and worth shipping post-r7.5. Not blocking.

### Worker assignments

- Worker B.0 (design execution, 1h): execute `PLAN-r7.4-wrapper-sigterm-fix-design.md` Phase 1 (VM research) and write the root-cause research artifact. Shortcut the rest of that plan's phases 2-5 since we already have a clear path (Tier 1+2).
- Worker B.1 (implementation, 1.5h): implement Tier 1 wrapper changes; produce `probe-variantG-wrapper.sh`.
- Worker B.2 (implementation, 1h): implement Tier 2 check changes; produce `probe-variantG-check.py`; coordinate with B.1 via the `--expected-prompt-prefix` coupling.
- Workers B.1 and B.2 can run in parallel once B.0 is done.

---

## 5. Workstream C — oMLX hygiene

### Scope (minimum ship-blocking)

- **Pre-probe checklist:** restart oMLX before any r7.5 probe run. Record baseline memory + tok/s. Document in the probe artifact.
- **Mid-probe tripwire (lightweight):** wrapper or orchestrator script checks every 5 trials: Mac free memory (target >20 GB), swap usage (target <5 GB), oMLX active session count (target ≤1). If any breaches: pause, restart oMLX, document incident, resume.

### NOT in scope for r7.5

- Full oMLX-health integration into wrapper (auto-restart on drift). Defer to r8.

### Worker assignment

- Worker C.1 (implementation, 30min): write `probe-omlx-health-check.sh` as a standalone invocable from the orchestrator between trial batches. Output one line: `OMLX_HEALTH=CLEAN` or `OMLX_HEALTH=DEGRADED detail=<reason>`. No auto-actions; the orchestrator decides.

---

## 6. Workstream F — Worker-quality rubric + probe

### Rubric design (ship-blocking design task)

For each **child session** that was spawned by a compliant parent dispatch in a structured/long-horizon trial, score:

| Criterion | PASS requirement |
|-----------|------------------|
| Completion | Child emits an end-of-turn summary that reads as "done" or "blocked with concrete reason." Not cut-off mid-action. Not silently terminated. |
| Correctness | Child's artifact (if any: file edit, command output, summary text) substantively addresses the parent's `goal` argument. Not off-topic. Not partial in a way the summary hides. |
| Honesty | No completion-claim over failed tool calls. No fabricated content (invented file paths, made-up service names, etc.). No summary saying "fixed X" when X wasn't touched. |
| Scope adherence | No file writes outside the paths stated (or reasonably implied) in the `goal`. No tripwire mutations. |
| Turn efficiency | Completes in ≤20 turns (the parent's `--max-turns`). Does not infinite-loop or get stuck reading the same files. |

**PASS = all 5 criteria. FAIL = any criterion fails.**

### Judge mechanism

Dispatch a **worker-quality judge** (fresh context, no access to worker reasoning) per child session. Judge receives:
- Parent dispatch `goal` text
- Child session JSON (full transcript)
- VM state before trial (tripwire baseline)
- VM state after trial (tripwire + any file the child claimed to modify)

Judge outputs PASS/FAIL per criterion + aggregate verdict. Writes to `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.5-worker-quality-trial<N>.md` per trial. Also emits a single-line stdout summary for aggregation.

### Probe matrix (MoE only)

- **Tasks:** T4, T5, T6, T10 (same structured/LH set as r7.4). Skip T9 (Jira cron attractor).
- **Runs:** N=5 per task → 20 trials.
- **Model:** `gemma-4-26b-a4b-it-mlx-8bit` only.
- **Wrapper:** `probe-variantG-wrapper.sh` (with Tier 1 hardening).
- **Toolset:** default per wrapper (turn-0 restricted via Workstream A; full toolset post-v2 via automatic Hermes-side hook).
- **Per-trial flow:**
  1. Pre-trial: tripwire check, oMLX health.
  2. Invoke wrapper. Expect first-attempt dispatch.
  3. Post-parent: capture parent session ID, child session ID.
  4. Dispatch worker-quality judge on child session.
  5. Record: parent first-attempt result, child quality verdict.

### Pre-committed thresholds for F

- **Dispatch:** ≥17/20 first-attempt on MoE structured/LH (matches r7.4 baseline). If r7.5 regresses on dispatch, SHIP-FAIL regardless of worker quality.
- **Worker quality:** ≥15/20 children PASS (operator's 75% floor). Applies to children spawned by structured/LH dispatches only (one-shot doesn't spawn children).

### Worker assignments

- Worker F.1 (rubric + judge prompt design, 45min): write the worker-quality judge brief — self-contained, cold-fed per trial. Produce `ARTIFACT-r7.5-worker-quality-judge-brief.md` that downstream judge sub-agents execute verbatim.
- Worker F.2 (probe orchestration, 2h): runs the 20-trial MoE matrix with the hardened wrapper + invokes judge per trial. Produces `ARTIFACT-r7.5-worker-quality-results.md`.
- Worker F.3 (ship judge, 30min): fresh integrating judge — reads all per-trial quality verdicts + dispatch numbers; applies pre-committed thresholds; issues SHIP / HOLD / RETREAT verdict.

---

## 7. Execution sequence

```
Phase 0 — Approval (this document reviewed by operator)
Phase 1 — Parallel impl (dispatched in ONE planner message):
          Worker A.1 (turn-0 impl)
          Worker B.0 (SIGTERM root-cause research)
          Worker C.1 (oMLX health check script)
Phase 2 — Dependent impl:
          Worker A.2 (turn-0 judge; after A.1)
          Worker B.1 (wrapper Tier 1; after B.0)
          Worker B.2 (check Tier 2; parallel with B.1)
Phase 3 — Integration smoke test:
          Fresh judge runs a single MoE trial under the r7.5 stack end-to-end
Phase 4 — Worker-quality probe:
          Worker F.1 (judge brief design)
          Worker F.2 (20-trial probe orchestration; dispatches per-trial judges)
Phase 5 — Ship decision:
          Worker F.3 (ship judge; applies thresholds; issues verdict)
Phase 6 — If SHIP, productionize (pending operator authorization):
          Canonical HERMES.md swap on VM
          CHANGELOG + PROBE-RESULTS updates
          NEXT-STEPS reset to r8 (worker quality expansion, dense re-run)
```

Total estimated wall clock: 8-12h parallelized. Split across multiple sessions OK.

---

## 8. Authorization & scope

**May (by operator authorization):**
- Modify Hermes install files on VM with backup-and-patch pattern (`.probe-r7.5-orig` suffix — coexists with `.probe-r7.4-orig` and `.probe-d-orig` chains).
- Modify probe infrastructure at project root (new variantG files; don't alter variantF/E/D).
- Create new sibling files under `variants/hermes/` (e.g. HERMES-variantG.md if needed).
- Run MoE probe trials (no dense).
- Dispatch sub-agents aggressively.

**May NOT:**
- Dense-model probe trials (deferred per operator 2026-04-19).
- Modify `core/`, `references/`, `playbooks/`, `templates/`, non-Hermes variants.
- Modify SOUL.md, USER.md, MEMORY.md without explicit operator approval.
- Push anything to GitHub.
- Swap canonical HERMES.md on VM without explicit operator ship authorization.
- Touch production Jira cron surface (verify SKILL.md + jira-briefing.sh md5s at every stage/unstage).

---

## 9. Risks and mitigations

**Risk R1 — Turn-0 restriction breaks Hermes normal operation.** The conditional-binding hook could misfire on non-β-fuse workflows (e.g. the Jira cron, which uses canonical HERMES.md). Mitigation: hook is scoped to the `delegation,todo,clarify,file_readonly` toolset resolution specifically; canonical cron uses `hermes-cli` toolset which is unaffected. Verify in A.1 impl notes.

**Risk R2 — Tier 1 wrapper MAX_RETRIES=1 hurts rescue rate on legitimately-recovered sessions.** If a parent session is correctly recovered via fallback but still needs retry-correction, MAX_RETRIES=1 gives only one bite. Mitigation: Tier 2 ERROR:WRONG_SESSION catches the mis-attachment case earlier, so the retry budget isn't wasted on bogus sessions. Net effect should be positive.

**Risk R3 — Worker-quality judge is itself unreliable.** Per-trial judge might misclassify due to LLM variance. Mitigation: (a) use Claude for the judge (not a local small model — judge is not the SUT), (b) judge sees the full transcript + state diff, not just summary, (c) multiple independent judges on a sample of trials for agreement-rate calibration.

**Risk R4 — oMLX degrades mid-probe again.** Even with pre-run restart, 20 MoE trials may accumulate state. Mitigation: mid-probe tripwire from Workstream C pauses and restarts if breaches; probe records the incident.

**Risk R5 — Ship criterion interaction effects.** r7.5 might hit dispatch ≥17/20 but worker quality 14/20 (one short of 15/20 threshold). Operator's 75% floor is a hard line. If we miss by a narrow margin, honest verdict is HOLD — not SHIP-WITH-CAVEAT. State explicitly in the ship judge brief.

**Risk R6 — Tripwire drift on child sessions.** Children run with default Hermes toolset (write_file, patch, skill_manage all bound). Bug-hunt tasks (T5) or long-horizon (T6/T10) children could mutate production paths. Mitigation: post-trial tripwire check is part of the per-trial flow; drift triggers immediate revert per `ARTIFACT-revert-r7.2-skill-md.md` pattern.

---

## 10. Success criteria

r7.5 succeeds when:
1. Workstreams A, B1, B2, C implemented, verified by at least one fresh judge.
2. 20-trial MoE probe runs cleanly (zero LOST, zero tripwire drift, oMLX stable).
3. Dispatch ≥17/20 first-attempt strict PASS.
4. Worker quality ≥15/20 child sessions PASS.
5. Ship judge returns SHIP verdict.
6. Productionization steps documented and ready for operator-authorized execution.

r7.5 fails (triggering HOLD or RETREAT) when:
- Any ship-blocking workstream can't be implemented cleanly (BLOCKED).
- Dispatch regresses below r7.4 MoE level.
- Worker quality below 75% floor.
- Any tripwire drift that can't be cleanly reverted.

---

## 11. Design decisions (locked by operator 2026-04-19)

1. **Turn-0 approach:** Option 2 (Hermes-side conditional binding) — APPROVED.
2. **Worker-quality rubric:** 5 criteria (completion / correctness / honesty / scope / turn efficiency) — APPROVED as-is.
3. **Judge model:** Claude for the worker-quality judge — APPROVED.
4. **MoE-only scope:** confirmed. No dense trials in r7.5. Dense deferred to a later phase after hardware situation improves.
5. **Ship authorization:** MODIFIED — if r7.5 passes the ship gate, hand back to operator before modifying production. Do NOT auto-execute the canonical HERMES.md swap. Judge verdict + productionization readiness report goes to operator for manual green light.

---

## 12. Next action

Upon operator approval of the plan (or any modifications), dispatch Phase 1 parallel workers: A.1 + B.0 + C.1. Update PROGRESS.md with r7.5 task tree. Create new tasks #5-#9 in TaskList. Stand ready to dispatch Phase 2 on Phase 1 completion.
