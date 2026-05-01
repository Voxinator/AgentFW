# HANDOFF — r7.11 Internal RC Achieved (campaign-close runbook)

**Author**: session 2026-04-26 → 2026-04-30 (r7.11 design + build + items 0-9 complete)
**Operator**: <internal>
**Status**: **INTERNAL RC ACHIEVED.** Cleanup phase complete. r7.12 planning pending (next session).
**Self-containment**: this doc + the referenced artifacts is everything a fresh session needs to pick up cold for r7.12 planning, post-mortem, or commit-prep.

---

## 1. Where we are right now (TL;DR)

**r7.11 internal RC achieved at item 9** (n=5 confirmation: 3/5 strict completion; pre-committed RC threshold met). The campaign question — *does r7.11 close the synthesis-trust gap on T6-class workloads?* — is empirically answered **yes**: 0/5 trials reproduced the trial-3 failure mode; every SUCCESS trial had perfect verifier-acceptance alignment; every ESCALATE trial fired correctly on a real, operator-actionable issue.

**Next decision-point: r7.12 architecture review** (deferred to a separate session — see §7).

The r7.11 architecture (verified-state multi-session resumable, with verification gates between phases, bootstrap session for parent-driven decomposition, and execution-tier verification via tier 3.7 acceptance-runner) is **fully built, empirically validated, and shipped to internal RC**:

- 6/6 implementation items + 7 extensions (LocalProcessTransport, bootstrap mode, write_plan_md staging, F-4 path fix, tier 3.7 acceptance-runner, F-9 orphan-detection, worker-3 path-norm fix) all judge-accepted
- **227/227 tests passing** across 7 test files
- 12 trial archives preserved on Mac (full session evidence)
- All r7.11-scope followups CLOSED (B1, F-7, F-8, F-9 B/C, F-11); 6 followups DEFERRED to r7.12 (F-1, F-2, F-3, F-10, F-12, plus 2 new from n=5)

---

## 2. Campaign arc — chronological summary

- **r7.5–r7.10**: parent decomposition explored; CEILING FINDING + minimum-mechanism (`write_plan_md`) validated; budget-n5 found 0/25 strict completion content-verified. Architecture decision: multi-session resumable with verification gates. Designed as r7.11.
- **r7.11 design (2026-04-26)**: §6-section design doc. Refined through A1–A5 + Q1–Q5. Operator signed off.
- **r7.11 build (2026-04-26 → 2026-04-29)**: items 0-7 + initial extensions (see §4 for full list).
- **Item 8 — T6 trial sequence (2026-04-28 → 2026-04-30)**:
  - **Trial 1**: BOOTSTRAP FAILURE — parent produced unparseable PLAN.md (no `write_plan_md` staged). Fixed by extending `probe-r7.11-stage.sh` to also stage `write_plan_md`.
  - **Trial 2**: VERIFICATION FAILURE on phase 2 (`fastapi` unresolvable). Bootstrap+phase 1 worked; phase 2 escalated correctly. Surfaced **F-5** (tier-2 doesn't see scaffold venv).
  - **Trial 3**: SYNTHESIS-FAB FAILURE — wrapper SUCCESS but pytest exit 1. All 4 phases verified_passed per architecture, but actual tests failed. Surfaced **F-7** (synthesis-trust gap: no tier executes the acceptance criterion). Also surfaced **F-9** (parent creates parallel files alongside untouched baseline stubs) and **F-8** (parent batched 3 phases in one session). Resolved F-5 via **B1** (PYTHONPATH-injection at probe time only — canonical-preserving variant of "pip install in Hermes venv").
  - **Trial 4**: VERIFIER REGRESSION — F-9 part B (orphan-detection) had path-normalization bug; declared file misclassified as orphan; CAT4 self-collision; phase 1 max-revs escalate. Parent diagnosed correctly. Worker-3 fix landed (`Path.resolve()` normalization on both sides).
  - **Trial 4b**: F-7 TEACHING BUG — tier 3.7 fired correctly with `[ENVIRONMENT:command-not-found: cd]`; the `write_plan_md` worked-example used shell syntax (`cd ... && pytest ...`) that doesn't compose with `shlex.split` + `subprocess.run`. Architecture composed end-to-end; teaching needed correction. Surfaced **F-11**. Manual pytest exit 0 (synthesis IS real; just blocked by teaching). F-9 part C (empty stubs) worked; F-8 nudge produced 4 sessions; B1 worked; worker-3 fix held.
  - **Trial 4c**: STRICT COMPLETION (post-F-11 fix). Tier 3.7 ACCEPTANCE_PASSED, pytest 7/7 exit 0, 4 sessions, all phases verified_passed.
  - **Trial 4d**: STRICT COMPLETION (n=2 reproducibility). Same shape as 4c with 11 tests. Architecture composes deterministically modulo parent stochasticity.
- **Item 9 — T6 n=5 (2026-04-29 → 2026-04-30)**: 5 sequential trials with pristine reset between each.
  - **5.1**: SUCCESS (4-phase, 13min, ACCEPTANCE_PASSED, pytest 6/6 exit 0)
  - **5.2**: SUCCESS (4-phase, 20min, ACCEPTANCE_PASSED, pytest 15/15 exit 0)
  - **5.3**: ESCALATE — phase 3 max revisions on `[CAT2:imported-unused] APIRouter`; parent recovery exhausted. Architecture caught real code-quality issue; parent couldn't fix in 3 revisions. Surfaced parent-recovery-quality variance.
  - **5.4**: ESCALATE — bootstrap anomalous_exit fail-fast; parent wrote PLAN.md but didn't fire `end_session_for_handoff`. Architecture's documented fail-fast policy fired correctly. Surfaced bootstrap-handoff ceremonial-sentinel-firing variance.
  - **5.5**: SUCCESS (3-phase, 6min, ACCEPTANCE_PASSED, pytest 10/10 exit 0)
  - **Result: 3/5 strict. RC threshold met per pre-committed interpretation.**

---

## 3. r7.11 architecture (the design — unchanged from sign-off)

Full design at `r7.11/DESIGN-r7.11-architecture.md`. Six sections:

1. **Preamble**: synthesis-trust framing (mechanism robust; synthesis is the failure surface)
2. **Lifecycle**: parent-as-orchestrator; session boundaries are tool calls (BOOTSTRAP → phases → COMPLETE/ESCALATE)
3. **Tool surface**: `write_plan_md` (carry-forward + acceptance_command teaching), `verify_phase` (tiers 1/2/3 + opt-in 3.5 + new tier 3.7 acceptance-runner; tier 4 deferred to r7.12), `end_session_for_handoff`, `escalate_to_operator`
4. **State artifacts**: PLAN.md (parent-facing) + `verified-state.json` (machine-authoritative). §4.A/B/C addendum: verified-state.json + PLAN.md are the EXCLUSIVE cross-session channel.
5. **Wrapper substrate**: thin Python driver. Polls sentinels, drives `hermes chat` per phase, archives session JSONs, makes routing decisions via verified-state.json (read-only).
6. **Failure modes**: F1 revise-loop bound, F2 parent fabrication mitigation, F3 verifier ignore mitigation, F4 verify-correctness, F5 spec-ambiguity (residual).

Plus appendix mapping r7.10 components carried forward + decisions table for Q1–Q5.

**Architectural patterns that generalize beyond Hermes** (relevant for AgentFW core; see r7.11 README):
- Verified-state-between-phases as the synthesis-trust mechanism
- Execution-tier verification (tier 3.7 pattern) closes static-only verification gaps
- Wrapper-as-dumb-substrate / parent-as-orchestrator architecture
- Tool-description teaching as the working doctrine-delivery mechanism
- Sentinel-file-driven session boundaries with file-authoritative state
- Tiered verifier with structured exit-code interpretation

---

## 4. r7.11 build state (everything in `variants/hermes/r7.9-research/r7.11/`)

### Modules + tests (all stdlib; 227/227 tests passing)

| Module | Tests | Status |
|--------|-------|--------|
| `verified_state.py` | `test_verified_state.py` 21/21 | ✓ |
| `verify_phase.py` | `test_verify_phase.py` 103/103 | ✓ (tier 3.7 + F-9 part B + worker-3 path-norm landed) |
| `verify_phase_tool.py` | `test_verify_phase_tool.py` 26/26 | ✓ (parse_plan_md acceptance_command landed) |
| `handoff_tools.py` | `test_handoff_tools.py` 14/14 | ✓ (F-8 nudge in END_SESSION_TOOL_DESCRIPTION) |
| `hermes_multi.py` | `test_hermes_multi.py` 26/26 | ✓ (B1 PYTHONPATH-injection landed) |
| `content_verify.py` | `test_content_verify.py` 21/21 | ✓ (F-4 fix landed) |
| `probe-r7.11-{stage,unstage,smoke}.sh` | `test_probe_r7_11.py` 16/16 | ✓ |

### Schema + reference docs

- `SCHEMA-verified-state.md`, `VERIFY-CONFIG-SCHEMA.md`, `SENTINEL-SCHEMAS.md`
- `PHASE-AWARENESS-NOTE.md`, `TIER3-NOTES.md`, `TIER35-NOTES.md`
- `HOWTO-r7.11-stage.md`, `HOWTO-r7.11-multi.md`
- `r7.x-followups.md` (F-1 through F-12 with closure status)

### Trial reports

- `REPORT-r7.11-item8-trial-1.md` — bootstrap failure → write_plan_md staging fix
- `REPORT-r7.11-item8-trial-2.md` — phase 2 verification failure → F-5 surfaced
- `REPORT-r7.11-item8-trial-4b.md` — F-11 teaching bug surfaced; ~280 lines
- `REPORT-r7.11-item8-trial-4cd-reproducibility.md` — n=2 baseline brief
- `REPORT-r7.11-item9-n5.md` — full n=5 report; 3/5 strict; RC threshold met
- (Trial 3, 4, 4c, 4d outcomes captured in the surfacing turns + memory; not separate report files but archived in full)

### Trial archives (12 total — full session evidence preserved)

`item8-trial-{1,2,3,4,4b,4c,4d}-archive/` + `item8-trial-{5.1,5.2,5.3,5.4,5.5}-archive/`. Each contains scaffold state, PLAN.md, verified-state.json, .session-archive/ (manifest + per-session JSONs + stdout/stderr).

---

## 5. Final canonical state (post-unstage; for cold-start verification)

After cleanup-phase unstage, the VM should reflect canonical Hermes installation with NO r7.11 mutations.

### Canonical tripwires (must match baseline)

```bash
ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md \
                       ~/.hermes/hermes-agent/run_agent.py \
                       ~/.hermes/hermes-agent/toolsets.py \
                       ~/.hermes/hermes-agent/model_tools.py'
```

Expected post-cleanup baseline values (verified 2026-04-30 immediately after r7.11 unstage):
- `HERMES.md`: `0780c232a6cb52e13e432261f0d68ad9` (canonical, never mutated by r7.11)
- `run_agent.py`: `94ad8712678df5e96b9f407446edf249` (canonical, never mutated by r7.11)
- `toolsets.py`: `5d126e7f1987468c0514cbc474ba12eb` (restored from `.probe-r7.11-orig` by unstage)
- `model_tools.py`: `10aaf53294ba39569844ebac7076e9c9` (restored from `.probe-r7.11-orig` by unstage)

### Files that should NOT exist post-unstage

```bash
ssh ubuntu-vm 'ls ~/.hermes/hermes-agent/tools/r7_11_lib 2>&1
ls ~/.hermes/hermes-agent/tools/r7_11_*.py 2>&1
ls ~/.hermes/hermes-agent/tools/write_plan_md.py 2>&1
find ~/.hermes/hermes-agent -name "*.probe-r7.11-orig" 2>&1'
```

All four should report "No such file or directory" / empty (verified 2026-04-30).

### Files that SHOULD restore to baseline (md5 match canonical)

- `~/.hermes/hermes-agent/toolsets.py` — restored from `.probe-r7.11-orig` backup during unstage
- `~/.hermes/hermes-agent/model_tools.py` — same (NOTE: lives at hermes-agent/ root, not tools/)

The unstage script's Phase 1 + 2 restores these from the `.probe-r7.11-orig` backups, removes the backup files, then Phase 5 verifies canonical md5 match for HERMES.md + run_agent.py and py_compile sanity for toolsets.py + model_tools.py.

### Scaffold state

`/tmp/r7.11-item8-scaffold/` may stay on VM (operator-discretion). It contains the trial-5.5 final state. Not in canonical Hermes; safe to leave or remove.

---

## 6. Followups status (r7.x-followups.md)

### CLOSED in r7.11

- **B1** (F-5 resolution: PYTHONPATH-injection at probe time only, in `LocalProcessTransport.launch_hermes`) — closed via worker-1 implementation, judge-1 ACCEPT, trial-4b empirical confirmation
- **F-4** (content_verify absolute-path handling) — closed 2026-04-29 via `_resolve_plan_path` helper
- **F-7** (verify_phase passes despite acceptance failing — synthesis-trust gap) — closed via tier 3.7 acceptance-runner (worker-1, judge-1 ACCEPT, trial-4c+4d+5.1+5.2+5.5 empirical confirmation)
- **F-8** (parent batches phases instead of handing off) — closed via STANDARD PATTERN nudge in `END_SESSION_TOOL_DESCRIPTION` + `write_plan_md` description; trial-4b through 5.5 confirm per-phase handoff held in 5/5 post-fix trials
- **F-9 part B** (tier-3 doesn't catch orphan-stub collisions) — closed via `_discover_orphan_files` + extended `_cat4_duplicate_definition` (worker-2, judge-2 ACCEPT) + worker-3 path-normalization fix (worker-3, judge-3 ACCEPT, trial-4b+4c+4d+5.x empirical confirmation: 0 false-positives)
- **F-9 part C** (scaffold-baseline `src/api/export.py` ships active code mistaken for finished impl) — closed via emptying file to docstring-only + new `CONVENTION.md`
- **F-11** (write_plan_md worked-example uses shell syntax) — closed via direct edit (single-executable form + GOOD/BAD examples); trial-4c+4d+5.x confirm parent picks up the corrected pattern

### DEFERRED to r7.12

- **F-1** (Hermes SQLite SessionDB regression since 2026-04-25 — `--resume` history loading silently fails). Independent Hermes-layer investigation. Not blocking r7.11 (architecture uses verified-state.json as exclusive cross-session channel).
- **F-2** (Hermes tool-handler return-type triggers slice error — upstream `tools/registry.py:dispatch` coercion). Workaround in r7.11 shims (json.dumps); upstream fix candidate.
- **F-3** (scaffold third-party deps gap) — superseded by F-5/B1; archived as historical context.
- **F-10** (tier-3.5 INCONCLUSIVE on phase 1 despite valid .py file — likely path-walker analogue of F-4). Small spike; gates F-7-path-A if ever pursued.
- **F-12** (content_verify heuristic flags intentional baseline stubs as defects, plus `unwired-api` false-positive on `permissions.py`) — r7.12 rubric tuning.
- **NEW from n=5 trial 5.3**: parent-recovery-quality on tier-3-catches. Parent revised 3 times trying to fix `[CAT2:imported-unused]`; each revision failed to address the issue. Mitigation candidates: increase max_revisions default; sharper corrective_dispatch with specific lines to remove; tier-4 semantic judge to catch revision-quality regressions before re-verify.
- **NEW from n=5 trial 5.4**: bootstrap-handoff ceremonial-sentinel-firing. Parent wrote PLAN.md but didn't fire `end_session_for_handoff`; wrapper's BOOTSTRAP_FAILED_ANOMALOUS_EXIT fail-fast fired. Mitigation candidates: stronger bootstrap-completion teaching in write_plan_md description; wrapper retry on bootstrap anomalous_exit if PLAN.md was successfully written (degrade fail-fast to "try once more then escalate").

---

## 7. Next steps — r7.12 planning (deferred to next session)

**Do NOT start r7.12 in this session.** The findings from n=5 (5.3 parent-recovery quality, 5.4 bootstrap-handoff ceremony) plus the deferred items (F-1, F-2, F-10, F-12) plus architectural questions r7.12 may surface (tier 4 semantic verifier, generalization beyond T6, AgentFW-core vs Hermes-variant separation, the Hermes-as-interface vs wrapper-as-interface architectural framing) are non-trivial scope decisions that deserve their own session with the campaign result as input — not compressed into r7.11 cleanup.

### r7.12 carry-forward findings (surfaced post-cleanup-discussion 2026-05-01)

**A. Operator UX critique** (the campaign drifted from product thesis): r7.11's wrapper became operator-facing infrastructure (Mac-side `hermes_multi.py` + manual scaffold prep + log tailing). Original thesis was Hermes-as-interface (operator talks to Hermes; Hermes orchestrates). The verified-state mechanism is the load-bearing innovation and carries forward; the wrapper-as-orchestrator topology does not generalize to chat UX. r7.12 architectural question: **for each component, which delegation primitive composes best with verified-state-as-truth + Discord-as-interface?**

**B. Hermes has TWO delegation primitives, not one** — they compose; r7.12 likely uses both:
| Primitive | Process model | Ownership | Output composition | When |
|---|---|---|---|---|
| Hermes `delegate_task` (in-process) | Same Python process; threaded; child AIAgent inherits parent runtime; agent-loop intercept | Parent owns children; interrupt propagates | Final summary into parent context; intermediate via progress callback (CLI tree-view OR gateway-batched) | Per-phase work within a single session; parallel fan-out (3 concurrent default); when output should compose into parent conversation |
| Subprocess multi-session (`hermes_multi.py` pattern) | Separate `hermes chat` invocations; per-session context budget | Wrapper owns subprocess lifecycle | `verified-state.json` + sentinels (filesystem only) | Cross-context-window long-horizon work; CI-style automated runs; fresh-context isolation per phase |

Initial r7.12 component-by-primitive sketch:
- Operator-facing surface: in-process Hermes session (the conversation IS the interface)
- Per-phase work dispatch: `delegate_task` for parallel fan-out within a phase
- Cross-phase state: `verified-state.json` on disk (carried forward from r7.11)
- Tier 3.7 acceptance verification: unchanged from r7.11 — runs against the workspace regardless of who wrote it (in-process or subprocess)
- Long-horizon escalation: subprocess multi-session as a tool the parent can invoke when context limits approach; operator never sees it directly

**C. Synthesis-trust invariant must hold across the in-process delegation boundary** — this is r7.11-RC-blocker-equivalent if missed in r7.12. `delegate_task` children return summaries that compose into parent context; that summary IS parent-narrative relative to the verifier. **`verify_phase` must always run against the workspace, not against the child's summary, even for in-process delegation.** Otherwise the F-7 synthesis-trust gap reopens inside the in-process pattern. (Already structurally true in r7.11 — verify_phase takes `scaffold_root`, not agent state — but worth being explicit so it's not bolted on retroactively.)

**D. Two-primitive composability framing is the right shape**, not "pick one and force everything through it." r7.12's value comes from using each primitive where it composes best. Architectural decisions framed as impossibilities ("can't do X") should be challenged: which primitive does the constraint apply to?

**E. Campaign-meta lesson** (carries to discipline, not just r7.12): architectural claims about Hermes must ground in the substrate's actual capabilities, not in the model of "what tools of that name might do." The same synthesis-untethered-from-verified-state pattern that produced trial 3's failure mode can produce architectural-decision failure modes in conversation. Apply r7.11 discipline (verify against actual state) to r7.12 design conversations.

**r7.12 planning session inputs (when convened)**:
- This HANDOFF (campaign-close runbook)
- `REPORT-r7.11-item9-n5.md` (the empirical baseline)
- `REPORT-r7.11-item8-trial-4b.md` (the F-7 surfacing — explains the synthesis-trust framing in detail)
- All 12 trial archives (full session evidence; queryable for variance analysis)
- `r7.x-followups.md` (full followup ledger with closure status)
- Project memory entries (RC achieved + pointers)

---

## 8. Hard constraints (carry forward)

- **Canonical at session end** — HERMES.md + run_agent.py md5 must match baseline. After r7.11 cleanup unstage: ALL r7.11 mutations rolled back; canonical mode confirmed.
- **Operator pre-approvals (historical, for archive context)**: `.probe-r7.11-*` backup convention pre-authorized; VM mutation under that convention pre-authorized; `OMLX_API_KEY` is local-dev only; per-scaffold deps installation in scaffold's `.venv/` is fine.
- **Read-only invariant on `verified-state.json`**: ONLY `verify_phase` writes. Empirically validated across all 12 trials.
- **No git commits without explicit authorization.** Operator pre-authorized a sanitization+commit pass after cleanup; that's a separate operator-supervised step.
- **No Hermes-canonical mutation outside `.probe-*` convention** without explicit authorization.

---

## 9. Cold-start checklist for next session (r7.12 planning OR commit-prep)

```
1. Read this HANDOFF top-to-bottom.
2. Read REPORT-r7.11-item9-n5.md for the campaign-close baseline.
3. Verify VM canonical state per §5 commands. Halt if drift.
4. Confirm absence of staged firmware (no r7_11_lib, no shims, no write_plan_md, no .probe-r7.11-orig).
5. Confirm 227/227 tests still pass (no regressions during commit-prep / r7.12 planning).
6. Decide session intent: r7.12 architecture review OR commit-prep (sanitization + branch commit + tag).
   - r7.12 architecture review: load deferred-followups context; scope tier-4 semantic verifier
     question; scope AgentFW-core-vs-Hermes-variant separation question.
   - Commit-prep: sanitization grep pass; produce hermes-r7.11-rc1 branch; tag hermes-r7.11-rc1;
     do NOT merge to main; do NOT push trial archives in this commit (separate session).
```

---

## 10. The campaign question, answered

**Does r7.11 close the synthesis-trust gap on T6-class workloads?**

Yes. Empirical evidence (n=5):
- 0/5 trials reproduced the trial-3 failure mode (verifier-pass + acceptance-fail)
- 3/5 SUCCESS trials had perfect verifier-acceptance alignment (tier 3.7 ACCEPTANCE_PASSED + manual pytest exit 0)
- 2/5 ESCALATE trials fired correctly on real, operator-actionable issues (parent recovery exhaustion; bootstrap ceremony miss)
- Every architectural component held in every trial that exercised it
- No silent passes when reality says fail

**The architecture works.** Reliability rate (3/5 = 60%) clears the pre-committed RC threshold (≥3/5). Remaining variance is parent-side (recovery quality, ceremonial sentinel-firing), surfaced cleanly for r7.12 reliability tuning.

Plan. Dispatch. Judge. Iterate. Don't collapse roles in the main session.
