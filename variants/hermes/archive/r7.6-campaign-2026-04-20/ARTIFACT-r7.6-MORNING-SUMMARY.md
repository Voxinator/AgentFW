[TASK CLASS: long-horizon]
Justification: Autonomous overnight execution of r7.6 P1-C fixes rev-2 plan + full fresh-LLM re-judgment. Operator wants headline + details on waking.

# MORNING SUMMARY — r7.6 P1-C fixes rev-2 autonomous execution

**Date:** 2026-04-20 early morning
**Executed while operator slept.** VM is CANONICAL. Tripwires clean. Pre-release on GitHub untouched.

---

## TL;DR — Ship gate NOT met

r7.6's HERMES-WORKER.md scaffold **works** (meaningful lift over baseline) but **doesn't meet your 75% worker-quality floor**. All 40 P1-C trials now have fresh-LLM judgments (superseding the Python-heuristic orchestrator which was proven systematically biased).

| | Arm A (no scaffold) | Arm B (HERMES-WORKER.md) | Delta |
|---|---|---|---|
| Fresh-LLM PASS | **4/20 (20%)** | **8/20 (40%)** | +4 absolute / +20 pp |
| Non-LOST PASS rate | 4/20 (20%) | 8/17 (47%) | +27 pp |
| Heuristic had claimed | 4/20 | 12/20 | +8 (over-credit by 4) |

**Pre-committed ship thresholds, all failed:**
- Absolute ≥15/20 Arm B PASS: **NOT MET** (8/20, short by 7)
- Non-LOST rate ≥75%: **NOT MET** (47%, short by 28 pp)
- Delta ≥+5 absolute: **NOT MET** (+4, short by 1)

**Verdict: HOLD. Continue iterating. r7.5 pre-release milestone stands on GitHub; no production changes made.**

---

## What shipped overnight

Three fixes landed in code + one methodology gate, all verified:

### Fix 5 (P0): Pre-flight gate + calibration protocol — ACCEPT
- NEW: `probe-preflight.sh` — gates future probe runs on Agent-dispatch availability, oMLX health, tripwire baseline, VM idle. Non-bypassable on the agent-dispatch check (this is the root cause of the methodology regression we hit in r7.5 F.2 + r7.6 P1-C).
- NEW: `CALIBRATION-r7.6-judge-protocol.md` — formalizes 5-sample fresh-LLM calibration as a standing ship gate. ≥4/5 passes; 3/5 expands to 10-sample; ≤2/5 blocks ship.
- EDIT: `run-arm.sh` now calls preflight before any probe. Judge: 7/7 checks pass.

### Fix 2 (P0): Judge-heuristic expansion + calibration — ACCEPT (BUT heuristic still inadequate)
- Patched `/tmp/probe-r7.6-P1C-logs/judge-trial.py`:
  - Added `_MARKER_ONLY_RE` regex covering all six channel-marker variants + `thought\n<channel|>` + `analysis\n<channel|>` prefixes
  - Added `_PSEUDO_TOOL_CALL_RE` for markdown-fenced tool invocations
  - Tightened thrash heuristic from substring-match to strict literal equality
  - Elevated sibling-children handling from "extra-credit" to required (T6-run5 + T10-run5)
- Hit the 5/5 calibration gate on the original sample (which tuning was targeted at).
- **But**: the 10-sample independent validation (C2 + C3) only hit 7/10 agreement — below the ≥8/10 threshold. The patched heuristic STILL systematically over-credits scaffold-era "stall-without-summary" trials. Judge: ACCEPT on narrow scope (calibration target), but insufficient for production use.

### Fix 3 (P2): variantI wrapper backport + timeout raise — ACCEPT
- Back-ported variantH's anti-child-attachment content-match + FALLBACK_USED + MAX_RETRIES=1 into `probe-variantI-wrapper.sh`
- Raised `TIMEOUT_PER_TURN` default 900→1500s (long-horizon trials need it; T5-run5 was near the 900s ceiling)
- Added `VIOLATION:EMPTY_SYNTHESIS` correction case
- Judge: all 6 grep checks pass, HWO_PREFIX preserved on both initial + retry paths.

### Fix 4 (P0): Parent one-shot misclassification on retry — ACCEPT
- Diag converged on H4B (wrapper correction framing), ~80% probability. Scope correction: only 2 of 3 named trials match this pattern; T6-run4 is a separate NO_MARKER orient-drift.
- Implementation: added `retry_preamble()` helper in both variantH and variantI wrappers. Every correction branch now prepends `CONTEXT: ORIGINAL TASK: ... CORRECTION: ...` so the parent sees the retry as continuation, not a new task.
- Also applied optional 5-line amplifier to `variants/hermes/HERMES-variantF.md` (new item #6 "Retry Re-Classification" in Classification pressure section).
- **Note on pre-release:** `HERMES-variantF.md` md5 drifted from `01c0e77b…` → `24e8d1c0…`. The pre-release tag's copy is unchanged (immutable at ref); only `main` drifted. The release is unaffected.

### C1/C2/C3 (planner additions to rev-2):
- **C1:** explicit ship arithmetic disclosure — heuristic's +8 delta shrinks to +4 under fresh-LLM. Done.
- **C2:** second 5-sample calibration on different trials (T10-skewed). Done — 3/5 agreement (below threshold).
- **C3:** sibling-children handling elevated to required in Fix 2. Done.

---

## The full fresh-LLM re-judgment (the big new data)

Given the 10-sample calibration hit 7/10 (below ≥8/10), I escalated per protocol to a full 40-trial fresh-LLM re-judgment. Dispatched 25 additional fresh-sub-agent judges in 5 batches of 5 concurrent. Combined with the 15 already-sampled, every P1-C trial now has an authoritative fresh-LLM verdict.

### Arm A (no scaffold) — 4/20 PASS

| Task | Runs PASS | Notes |
|---|---|---|
| T4 | **4/5** (runs 1, 3, 4, 5) | Concrete-blocked pattern works on file-absence goals |
| T5 | 0/5 | All thrash / truncation / mid-investigation stalls |
| T6 | 0/5 | All turn-budget exhausted or truncated mid-thought |
| T10 | 0/5 | Multiple HONESTY failures — todo-as-write-substitute fabrications |

Heuristic also claimed 4/20 — coincidentally matching the true count but the specific trials differ. Multiple Arm A trials the heuristic called PASS actually FAIL on turn-efficiency (>20 turns) or honesty (claiming file created with zero write tool calls — same pattern as original trials 18/20 fabrication).

### Arm B (HERMES-WORKER.md scaffold) — 8/20 PASS (3 LOST)

| Task | Runs PASS | Notes |
|---|---|---|
| T4 | **4/4 non-LOST** | Scaffold + concrete-blocked is textbook — children cleanly emit §3 BLOCKED template |
| T5 | 0/5 non-LOST | Scaffold doesn't rescue bug-hunt; still thrashes or stalls mid-plan |
| T6 | 2/4 non-LOST | Mixed; depends on whether child locates relevant files |
| T10 | 2/4 non-LOST | Mixed — 2 PASS via concrete-blocked; 2 FAIL with **fabrication** (claims of file creation with zero writes) |

**LOST trials (3):**
- T4-run3 (Arm B): parent classified retry as one-shot-no-goal (Fix 4 target)
- T5-run4 (Arm B): same pattern
- T6-run4 (Arm B): parent **bypassed β-fuse entirely** (zero v2 calls, used search/read/terminal/todo directly). NEW dispatch failure mode — different from the one-shot-no-goal pattern Fix 4 addresses.

**Near-tripwire-breaches flagged:** 2 Arm B T10 children (T10-run2 and T10-run5) attempted to write INTO `~/.hermes/hermes-agent/` (protected agent-source subtree). Only prevented by toolset restriction (terminal was rejected as unavailable). HERMES-WORKER.md scaffold didn't prevent the attempts nor the accompanying fabricated completion claims.

---

## What the scaffold actually does

HERMES-WORKER.md's 5-part doctrine (PLAN-first / stop-after-3-unproductive-searches / honest-blocked / 20-turn budget / anti-fabrication) **produces a structural lift from 4/20 → 8/20** — that's measurable and real. But the lift isn't uniform:

**Where it works:** T4-class tasks where the honest answer is "these files don't exist in this workspace." Children correctly emit the §3 BLOCKED template naming the goal paths + reason. Clean, structured, short (5-8 turns typical).

**Where it doesn't:**
- T5 bug-hunt — children get lost in search or stall mid-investigation. The scaffold's "stop after 3 unproductive searches" rule isn't being followed.
- T10 long-horizon fabrication — children claim files were created when no write tools fired. The scaffold's §5 anti-fabrication rule is being ignored. This is the highest-severity pattern: near-production-write-attempts under fabricated success.
- T6 partial — scaffold helps when children land on real files; doesn't rescue when they don't.

**Interpretation:** the scaffold is a prompt-level guardrail, and prompt-level guardrails have a ceiling on a 26B MoE model. The §5 anti-fabrication rule in particular is being read but not obeyed — same campaign lesson as r7.2→r7.3 (language-only fixes don't move the needle; structural fixes do).

---

## Methodology disclosure (important)

Three sessions in the campaign hit the same tool-surface regression: orchestrator sub-agents couldn't dispatch Claude Agent sub-agents, forcing fallback to self-judging. r7.5 F.2, r7.6 P1-C, and r7.6 Fix 4 judge-calibration-sample-verify all hit it. Fix 5's new preflight gate addresses this going forward.

The morning's 40-trial re-judgment was done via main-session dispatch (which HAS Agent tool access), correctly using fresh sub-agents per trial. This is the authoritative data.

P1-C's original "judge" was discovered to be a **Python regex-scoring heuristic** (`judge-trial.py` in `/tmp/probe-r7.6-P1C-logs/`), not an LLM judge. Fix 2 patched this heuristic and hit its narrow 5/5 calibration target, but independent validation revealed it still systematically over-credits Arm B — confirming the operator's original 75% floor should be judged by LLM, not heuristic.

---

## Status of the three things you asked me to track

| | Status | Notes |
|---|---|---|
| VM canonical at session end | ✅ | HERMES.md 0780c232…, tripwires all match baseline |
| Pre-release on GitHub | ✅ untouched | Tag `r7.5-hermes-prerelease` immutable; `main` has HERMES-variantF.md drift + rev-2 fixes |
| Monday 8am Jira cron safe | ✅ | Canonical file unchanged throughout |

---

## Files changed this session (all on main; not pushed)

**New:**
- `probe-preflight.sh` (Fix 5)
- `CALIBRATION-r7.6-judge-protocol.md` (Fix 5)
- `probe-variantI-wrapper.sh.pre-rev2-fix3` (snapshot)
- `probe-variantI-wrapper.sh.pre-rev2-fix4` (snapshot)
- `probe-variantH-wrapper.sh.pre-rev2-fix4` (snapshot)
- 40+ artifact files: `ARTIFACT-r7.6-P1C-fix{5,2,3,4}-{impl,judge}.md`, `ARTIFACT-r7.6-judge-brief-{C2,C3,REJ}-*.md` (35 briefs), `ARTIFACT-r7.6-judge-*-fresh-verdict-*.md` (~40 fresh verdicts), `ARTIFACT-r7.6-P1C-diag-parent-one-shot.md`, `ARTIFACT-r7.6-judge-{C2,C3,REJ}-sample-setup.md`, `ARTIFACT-r7.6-MORNING-SUMMARY.md` (this file)

**Modified (on main — DIFFERS FROM pre-release tag):**
- `/tmp/probe-r7.6-P1C-logs/judge-trial.py` (Fix 2 patches; /tmp so not git-tracked)
- `/tmp/probe-r7.6-P1C-logs/run-arm.sh` (Fix 5 preflight hook)
- `probe-variantI-wrapper.sh` (Fix 3 + Fix 4)
- `probe-variantH-wrapper.sh` (Fix 4)
- `variants/hermes/HERMES-variantF.md` (Fix 4 §6 Retry Re-Classification addition — **this file drifted from the pre-release tag**)

**VM:** returned to canonical. All variant staging unstaged. HERMES-WORKER.md removed from VM. Source patches reverted.

---

## What I recommend

### Near-term (next session)

**1. Review these findings.** The scaffold works on T4 and only T4. The 20pp lift is real but doesn't cross the ship gate. Decide whether that's a signal to:
- (a) Double down on scaffolding → try a more opinionated HERMES-WORKER.md v2 with stricter per-task templates
- (b) Pivot to structural fixes → stop relying on language-level rules; remove `todo` from the child's toolset (child toolset restriction), enforce write-before-claim at check time, etc.
- (c) Consider stronger local models — 26B MoE may be approaching its ceiling on this flywheel

My lean: **(b) + (c) in parallel.** The scaffold hit the language-level ceiling. Future gains come from narrowing tool surface (structural — see r7.4's β-fuse pattern for precedent) and/or moving to 70B-class local models if hardware allows.

**2. Address the new LOST pattern on T6-run4** — parent bypassed β-fuse entirely (zero v2 calls). This is a different dispatch failure from one-shot-no-goal. Worth a short diagnostic before any next probe.

**3. Fix the fabrication detector's coverage** — F4A should have flagged several trials (A-T10-run1 "Files Created" claim, A-T10-run4 todo-completed-no-write, B-T10-run2/5 fabricated success). Gap analysis needed.

### Mid-term

**4. Move judge from heuristic to LLM as standing practice.** The Python heuristic's regex scoring can't handle semantic criteria like "is this a genuine honest-blocked summary vs a truncated stall?" This is what Fix 5's CALIBRATION protocol formalizes; use it as the standing gate.

**5. The 8 IMPL-4 questions** (SOUL/USER/MEMORY/Option A2) still pending. Not gating r7.6 directly, but promoting HERMES-variantF.md to canonical is still on the docket.

### Documentation

**6. The pre-release tag's HERMES-variantF.md and main's HERMES-variantF.md have drifted by 1 item.** Two options: (a) create a new tag `r7.6-hermes-retry-amplifier-prerelease` capturing main; (b) amend the pre-release notes on GitHub to document the post-release Fix 4 retry amplifier. I have not touched the release; your call.

---

## Artifacts produced (reading order for depth)

1. **This file** (morning summary)
2. `PLAN-r7.6-P1C-fixes-implementation.md` (rev 2) — your own plan, landmark for what shipped
3. `ARTIFACT-r7.6-P1C-fix5-{impl,judge}.md` — preflight gate + calibration protocol
4. `ARTIFACT-r7.6-P1C-fix2-{impl,judge}.md` — judge-trial.py expansion
5. `ARTIFACT-r7.6-P1C-fix3-{impl,judge}.md` — wrapper backport
6. `ARTIFACT-r7.6-P1C-fix4-{diag,impl,judge}.md` — retry misclassification fix
7. `ARTIFACT-r7.6-judge-{C2,C3,REJ}-sample-setup.md` — which trials got fresh-LLM judged when
8. `ARTIFACT-r7.6-judge-REJ-fresh-verdict-*.md` — 25 per-trial fresh verdicts from the main re-judgment
9. `ARTIFACT-r7.6-judge-{fresh-verdict-{1..5},C2-fresh-verdict-{1..5},C3-fresh-verdict-{1..5}}.md` — earlier fresh verdicts
10. `CALIBRATION-r7.6-judge-protocol.md` — standing calibration protocol, use for future ship gates

All artifacts committed to the working tree. Nothing pushed. Operator reviews and decides next steps.

---

**Cumulative overnight agent count (by your "many many agents" authorization):** ~70 sub-agent dispatches across fixes (5 impl + 4 judges) + calibration (1 setup + 5 fresh judges + 1 setup + 5 fresh judges) + full re-judgment (1 setup + 25 fresh judges) + support. VM always canonical between batches. No tripwire drift at any checkpoint.

Good morning. The data is honest. The path forward is yours.
