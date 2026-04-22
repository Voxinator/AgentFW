[TASK CLASS: structured]
Justification: Multi-phase research + design deliverable producing a single artifact. Independent sub-problems (VM root-cause research, three design tiers, sequencing/risk synthesis) are independently verifiable. Benefits from planner/worker/judge role separation. No production changes — design-only scope.

# PLAN — r7.4 wrapper SIGTERM fix design

**Goal.** Produce `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-wrapper-sigterm-fix-design.md` — a design-only document that an implementation worker in a later session can execute verbatim, covering (1) confirmed root cause of the SIGTERM-truncation → parent-session-loss → fallback-mis-attachment cascade, (2) three-tier fix design (wrapper mitigation, check-script hardening, upstream Hermes fix) with exact file paths, line numbers, and near-diffs, (3) deployment sequencing, and (4) risk analysis — especially r7.4 methodology-comparability risk.

**Non-goals.** No implementation. No writes to wrapper/check/HERMES-variantF/VM Hermes source. No probe runs. No disturbance of the running gap-fill worker. No edits under `core/`, `references/`, `playbooks/`, `templates/`, or non-Hermes variants.

**Operator.** voxinator@gmail.com. Date: 2026-04-19.

---

## 1. Decomposition

The work decomposes into six phases. Phases 2a/2b/2c are independent and parallelizable once Phase 1 is landed.

| # | Phase | Mode | Role | Deliverable |
|---|-------|------|------|-------------|
| 0 | Orientation | main session | planner | Internal — state-snapshot note |
| 1 | VM root-cause research | sub-agent (research worker) | worker | `ARTIFACT-r7.4-sigterm-research.md` (exact file:line for session save, atexit handler, signal handling) |
| 2a | Tier 1 design — wrapper mitigation | sub-agent (design worker) | worker | `ARTIFACT-r7.4-tier1-wrapper-design.md` with unified diff against `probe-variantF-wrapper.sh` |
| 2b | Tier 2 design — check-script hardening | sub-agent (design worker) | worker | `ARTIFACT-r7.4-tier2-check-design.md` with unified diff against `probe-variantF-check.py` |
| 2c | Tier 3 design — upstream Hermes SIGTERM handler | sub-agent (design worker) | worker | `ARTIFACT-r7.4-tier3-hermes-design.md` with proposed patch + test plan |
| 3 | Sequencing & risk synthesis | main session | planner | Integrated into final artifact |
| 4 | Assembly | main session | planner | `ARTIFACT-r7.4-wrapper-sigterm-fix-design.md` — FINAL |
| 5 | Judge verification | sub-agent (fresh judge) | judge | `ARTIFACT-r7.4-wrapper-sigterm-fix-judge-verdict.md` |

Phase 0 can start immediately (reads only). Phase 1 gates 2a/2b/2c. Phase 3 requires 2a–2c complete. Phase 4 is pure synthesis. Phase 5 is shielded from all prior reasoning.

---

## 2. Phase-by-phase protocol

### Phase 0 — Orientation (main session, ~5 min)

**Scope:** always-allow (reads only).

Read the following to refresh context if resuming cold:

- `HANDOFF-2026-04-19.md` — broader project state
- `PROGRESS.md` — task-state ground truth
- `ARTIFACT-r7.4-phase-d-dense-results.md` — concrete incident evidence (T5-run1, T5-run7 mis-attachment; "Wrapper fault observed" section at lines 22–23; "Remaining work for a follow-up worker" at line 115 already names the three mitigations)
- `probe-variantF-wrapper.sh` lines 130–220 (extract_session_id, fallback recovery construction)
- `probe-variantF-check.py` lines 100–160 (marker gate, `extract_classification`)

**Verification:** the planner can name (a) the existing TIMEOUT_PER_TURN source of truth (env var already? hardcoded?), (b) the current FALLBACK_CANDIDATES resolution order, (c) the check's current marker-gate behavior. No file written.

**Exit:** proceed to Phase 1.

### Phase 1 — VM root-cause research (worker, ~45 min)

**Worker prompt (self-contained brief):**

> You are a research worker with read-only scope on the Ubuntu VM at `ssh ubuntu-vm`. Your job is to confirm or refute the hypothesis that `probe-variantF-wrapper.sh` loses the parent session JSON when `timeout 900` SIGTERMs `hermes chat` mid-turn because the session-persistence path in Hermes is registered as an `atexit` handler that does not fire under SIGTERM.
>
> **Scope.**
> - READ-ONLY on VM. No edits. No `touch`/`mv`/`rm` on VM. No starting/stopping of running processes (a gap-fill worker is actively using hermes — do not disturb).
> - Allowed: `ssh ubuntu-vm <read-only shell command>`, `grep`, `rg`, `sed -n`, `awk`, `cat`, `head`, `tail`, `jq` on session JSONs. `python3 -c "..."` for inspection.
> - `find ~/.hermes/sessions -name 'session_*.json' -newer <something>` is fine. Reading any file under `~/.hermes/hermes-agent/` is fine.
> - Do NOT touch tripwires: `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/{SKILL.md,jira-briefing.sh}` and `/media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts`.
>
> **Questions to answer with exact file:line citations.**
> 1. Which file+function in `~/.hermes/hermes-agent/` owns session persistence (writing the `session_*.json` to disk)? Find it by: `ssh ubuntu-vm 'rg -n "atexit|save.*session|session.*save|_flush|to_json|write_json" ~/.hermes/hermes-agent/agent/run_agent.py'` and adjacent modules. Report exact file + function name + line range.
> 2. Is that persistence path registered via `atexit.register(...)`, via a signal handler, via a context manager `__exit__`, via an explicit finalizer called from the main loop, or some combination? Cite the registration site.
> 3. Does the main conversation loop periodically flush, or only at end-of-session? Look for `.save(`, `.flush(`, `json.dump(` calls inside the turn loop.
> 4. What signals does the process currently handle? `rg -n "signal\.|SIGTERM|SIGINT|SIGHUP" ~/.hermes/hermes-agent/`. Cite any existing handlers.
> 5. What does `atexit` do on SIGTERM? Confirm (from Python docs + code behavior) whether the existing save path actually runs when `timeout` sends SIGTERM to hermes. If the save path is `atexit`-only, Python does NOT run atexit on uncaught SIGTERM (it terminates before cleanup). This is the probable root cause — confirm with a citation.
> 6. Does SIGINT (Ctrl-C) trigger the save path via Python's default KeyboardInterrupt → atexit flow? (Yes normally — a SIGINT becomes KeyboardInterrupt which unwinds through `sys.exit`, which runs atexit. Confirm or refute.)
> 7. Are there any existing explicit save-on-shutdown hooks we could reuse — e.g., a `session.checkpoint()` method, a `--autosave-interval` flag, a periodic flush tied to message boundaries? Enumerate them with line refs.
> 8. Cross-check one concrete incident. Read session JSON `20260419_132928_e11ccb` on VM (the orphan child from T5-run1 per `ARTIFACT-r7.4-phase-d-dense-results.md` line 70). Extract `messages[0].content[:200]` and confirm it is the dispatched goal string ("Investigate and fix...") and NOT the trial prompt ("The dashboard sometimes shows stale data..."). This proves the mis-attachment pattern empirically.
>
> **Deliverable.** Write `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-sigterm-research.md` with:
> - Ordered answers to all 8 questions, each with file path + line number citations.
> - A "Root Cause" section (≤150 words) that states the confirmed failure chain.
> - A "Hook points" section enumerating the options for landing Tier 3 (what function to register as a SIGTERM handler target, what flag mechanism is signal-safe given Python's signal-module constraints).
> - If any hypothesis is disproven, say so explicitly — do not force-fit the pre-registered hypothesis.
>
> **Report-back length:** the artifact can be long; your summary back to the planner should be ≤200 words highlighting the one-line root cause and the recommended Tier 3 hook point.

**Verification gate:** the artifact must contain at least one file-path + line-number citation for every question 1–7. Question 8 must contain the actual extracted `messages[0].content[:200]` string.

**Blast radius if wrong:** Tier 3 design points at the wrong function. Mitigated by Phase 5 judge reading the artifact cold and checking that the hook point exists where claimed.

### Phase 2a — Tier 1: Wrapper mitigation design (worker, ~30 min)

**Depends on:** Phase 1 complete (to know whether wrapper-side hardening alone is sufficient mitigation or whether the recovery path needs to be even stricter).

**Worker prompt (self-contained brief):**

> You are a design worker. Your job is to produce a unified diff against `/Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh` that (a) makes `TIMEOUT_PER_TURN` respect an env override, (b) adds an anti-child-attachment check in fallback recovery, and (c) considers whether to shrink MAX_RETRIES for fallback-recovered sessions.
>
> **Scope.**
> - READ `probe-variantF-wrapper.sh` and `probe-variantE-wrapper.sh` (the derived-from baseline).
> - READ `ARTIFACT-r7.4-sigterm-research.md` (Phase 1 output) for root-cause confirmation.
> - READ `ARTIFACT-r7.4-phase-d-dense-results.md` for concrete incidents (T5-run1, T5-run7).
> - DO NOT EDIT the wrapper or any production file. You are producing a design artifact only.
>
> **Design requirements.**
>
> **Change 1 — `TIMEOUT_PER_TURN` env override.** Locate the current assignment (likely a hardcoded `TIMEOUT=900` or `TIMEOUT_PER_TURN=...`). Propose the minimal `: "${TIMEOUT_PER_TURN:=900}"` idiom so callers can export `TIMEOUT_PER_TURN=1500`. Cite exact line.
>
> **Change 2 — Anti-child-attachment check.** In the fallback-recovery block (currently around lines 172–200 of `probe-variantF-wrapper.sh`; verify exact boundaries before writing the diff), after a candidate session JSON is selected, add a verification step: SSH-read the candidate's `messages[0].content` via `jq -r ".messages[0].content" <path>`, take the first N characters (propose N — suggest N=80), and require they match the first N characters of `$TASK_TEXT` (the trial prompt). Reject the candidate with a loud error when they don't match — emit `OUTCOME ... RESULT=ERROR detail=WRONG_SESSION final_session=<id>` and exit 0 (same exit-0 convention the wrapper already uses for ERROR results).
>
> Justify the choice of N. Justify whether to use exact-prefix match or substring match. Consider edge cases: (i) the trial prompt contains shell-special characters, (ii) hermes may prepend a system turn before messages[0] (verify from Phase 1 research whether `messages[0]` is always user or could be system), (iii) what if the sentinel-filtered candidate is the correct session but the JSON has not yet flushed messages[0]? Propose a grace retry with a capped delay.
>
> **Change 3 — MAX_RETRIES shrink for fallback-recovered sessions.** Decide: when a session is recovered via the last-resort fallback (most-recent-newer-than-sentinel, not source-tag match), should `MAX_RETRIES` drop to 1 to prevent cascade-on-mis-attachment? Argue both sides (pro: fewer NO_MARKER-cascade false negatives; con: a correctly-recovered session then gets only one retry, reducing effective rescue rate). Recommend a default and cite the precise variable and line.
>
> **Deliverable.** Write `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-tier1-wrapper-design.md`:
> - Unified diff (plain `diff -u` style) against the current `probe-variantF-wrapper.sh`. Each hunk labeled and explained.
> - Per-hunk rationale section: what it changes, why, what edge cases it handles, what it intentionally does NOT handle.
> - "Edge cases flagged" section: (a) TASK_TEXT contains single quotes or newlines, (b) session JSON is partially written when read, (c) source-tag match returns multiple candidates, (d) retry with `hermes chat --resume` after WRONG_SESSION rejection is not desired (we want a clean failure, not a loop).
> - "What would disprove this design" section: if a smoke test came back with X, we would know we got it wrong.
>
> **Report-back length:** ≤200 words.

**Verification gate:** diff must apply cleanly against `probe-variantF-wrapper.sh` at the version in the working tree today. Judge will verify by running `git diff --check`-equivalent reasoning.

**Blast radius if wrong:** wrapper breaks on future probes. Mitigated by (a) not applying until r7.4 data collection is done (see §4 risk) and (b) Phase 5 judge verifying line-number targeting is current.

### Phase 2b — Tier 2: Check-script hardening design (worker, ~30 min)

**Worker prompt (self-contained brief):**

> You are a design worker. Your job is to produce a unified diff against `/Users/briantaylor/Projects/AgentFW/probe-variantF-check.py` that structurally distinguishes parent sessions from child (worker-dispatched) sessions, emitting a new `ERROR:WRONG_SESSION` verdict that the wrapper can handle.
>
> **Scope.** READ-ONLY design. Same context and reads as Phase 2a. Additional read: `probe-variantE-check.py` for the pre-v2 baseline.
>
> **Design requirements.**
>
> **Signal design.** Today the check emits verdicts like `COMPLIANT`, `VIOLATION:NO_MARKER`, `VIOLATION:ROLE_COLLAPSE`, `ERROR:...`. Add `ERROR:WRONG_SESSION`. Specify exact verdict-string to keep wrapper parsing simple (`echo | head -1`).
>
> **Parent-session test.** The structural signature of a parent session is: `messages[0].role == "user"` AND `messages[0].content` is a trial prompt (either matches the curated set of T1/T2/T4/T5/T6/T8/T10 prompt patterns, or — more generally — does NOT look like a dispatched goal). The structural signature of a child session is: `messages[0].content` is a single assertive imperative ("Investigate and fix...", "Refactor...", etc.) that was passed as the `goal` arg of `delegate_worker_v2`.
>
> Choose a gate. Options:
>   (i) **Hard whitelist** — script hardcodes the T1…T10 prompt fingerprints (first 60 chars each) and rejects anything not matching. Brittle if prompts change.
>   (ii) **Trial-prompt injection** — wrapper passes `--expected-prompt-prefix "..."` to the check; the check compares. Couples wrapper and check but is precise.
>   (iii) **Heuristic** — accept `messages[0].content` as a parent if it contains multi-sentence exposition (length > X, punctuation pattern); reject if it's a short imperative. Fragile.
>
> Recommend one. The operator's read on the evidence is that (ii) is probably the right trade-off but weigh it explicitly.
>
> **Placement.** Where in `extract_classification` or upstream of it does this gate belong? Before v2-tool search? After it? Cite the exact insertion line.
>
> **Interaction with Tier 1.** Tier 1 (wrapper-side) gate catches the mis-attachment before the check ever sees it. Tier 2 is a belt-and-suspenders check if Tier 1 is ever bypassed or wrong. Argue the case for Tier 2 existing even with Tier 1 in place, and identify the narrow case where Tier 2 alone saves us.
>
> **Deliverable.** Write `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-tier2-check-design.md`:
> - Unified diff against `probe-variantF-check.py` at its current HEAD version.
> - Per-hunk rationale, including choice of gate variant (i/ii/iii) with trade-off discussion.
> - If variant (ii) is chosen, a mirror diff against `probe-variantF-wrapper.sh` showing where the wrapper passes `--expected-prompt-prefix`. (Note: this is the ONLY place Phase 2a and Phase 2b couple. Call this out so Phase 3 sequencing can account for it.)
> - "What would disprove this design" section.
>
> **Report-back length:** ≤200 words.

**Verification gate:** diff must apply against `probe-variantF-check.py` at HEAD. Judge verifies that the new verdict string is consistent with existing wrapper parsing (grep the wrapper for how verdicts are matched).

**Blast radius if wrong:** false positives reject legitimate parent sessions → spurious ERROR:WRONG_SESSION. Mitigated by Tier 1 being applied first in deployment order (so Tier 2 is defense-in-depth).

### Phase 2c — Tier 3: Upstream Hermes SIGTERM handler design (worker, ~60 min)

**Worker prompt (self-contained brief):**

> You are a design worker proposing an upstream patch to `~/.hermes/hermes-agent/agent/run_agent.py` to register a SIGTERM handler that triggers the existing session-save path. This is a research + design task — you DO NOT write the patch to the VM, you propose it in an artifact.
>
> **Scope.**
> - READ-ONLY on VM. Exactly like Phase 1's scope.
> - READ `ARTIFACT-r7.4-sigterm-research.md` for the authoritative hook-point identification.
> - NO edits anywhere. NO probe runs. NO process restarts.
>
> **Design requirements.**
>
> **Hook point.** Use the function identified in Phase 1 Q7 (existing save path) or Q1 (session-persistence owner). Cite exact file:line.
>
> **Signal handler design.** Python signal handlers have constraints:
>   - Only the main thread can install handlers.
>   - Handlers should do minimal work — I/O is technically allowed but risky if it re-enters the interrupted code's locks. Safe pattern: handler sets a flag; main loop checks flag and performs save at a safe point.
>   - `signal.signal(signal.SIGTERM, _on_sigterm)` vs the deprecated `signal.set_wakeup_fd`. Pick one and justify.
>
> Propose an architecture: handler-sets-flag + main-loop-polls-flag? Or direct save-from-handler with `signal.siginterrupt(SIGTERM, False)`? Weigh the trade-offs. In particular: if `timeout` sends SIGTERM mid-model-inference, can the main loop reach the flag-check before SIGKILL arrives (default `timeout` sends SIGTERM then SIGKILL after ~10s; this is wide enough for a flush)?
>
> **SIGINT question.** Phase 1 Q6 established whether SIGINT already triggers save via atexit. If YES, Tier 3 need only install SIGTERM. If NO, also propose SIGINT coverage. State explicitly.
>
> **Double-fault safety.** What if the save path itself raises in the handler? Propose a try/except that at minimum dumps a minimal "interrupted" stub so the wrapper's fallback has something to match on.
>
> **Test plan.** How would you verify this without touching production? Propose:
>   - Minimal reproduction: a small Python script that wraps a fake "turn loop" with the same atexit/signal pattern, send SIGTERM, verify the save path fires.
>   - Dry-run against a Hermes dev copy (NOT the live VM install). If no dev copy exists, propose what a side-by-side `~/.hermes-dev/` would look like and whether the operator should stand one up.
>   - Post-deploy check: run a short probe, kill the hermes process with `kill -TERM`, verify `session_*.json` wrote messages[0] and messages[1].
>   - Regression check: confirm normal end-of-session save (atexit path) still fires when no SIGTERM is involved.
>
> **Compatibility.** Is this a fork-local patch or does it have a path to upstream contribution? Identify the Hermes upstream repo (if knowable from the VM install — check for `.git/config`), the contribution workflow, and whether the maintainers have prior SIGTERM discussion (do NOT open issues or PRs — just report whether a contribution path exists).
>
> **Deliverable.** Write `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-tier3-hermes-design.md`:
> - Proposed patch as a unified diff against the exact file at the VM's current HEAD version. Cite `sha256` of the source file at the time of writing.
> - Architecture rationale (flag-vs-direct, SIGINT coverage, double-fault safety).
> - Full test plan as above.
> - "Contribution path" section.
> - "What would disprove this design" section. E.g., "if the Phase-1 research found that the save path is not safely re-entrant, this flag-based architecture is wrong and we need X instead."
>
> **Report-back length:** ≤250 words.

**Verification gate:** Judge verifies the hook function exists at the claimed line. Judge attempts to reason about signal-safety given Phase 1's constraints.

**Blast radius if wrong (and if ever implemented):** Hermes crashes under SIGTERM, or hangs, or corrupts session JSON. Mitigated by (a) test plan demanding a side-by-side dev environment before merging, (b) fork-local deployment so live VM never runs it until probed.

### Phase 3 — Sequencing & risk synthesis (main session, ~15 min)

**Scope:** planner reading the three tier artifacts plus Phase 1 research, synthesizing into (a) deployment order, (b) independent-vs-dependent tier analysis, (c) r7.4 methodology-comparability risk assessment, (d) minimum viable change to unblock r7.4 dense gap-fill.

**Questions to answer:**

1. Which of T1/T2/T3 can land independently? Answer structurally — e.g., T1 is self-contained, T2 is self-contained unless Tier 2 chose variant (ii) which requires wrapper coupling, T3 is independent but requires VM-side deployment discipline.
2. What is the minimum change to unblock r7.4 dense gap-fill (T5/T6/T10 remaining runs)? Candidates: (a) just extend TIMEOUT via env override (Tier 1 change 1 only — trivial); (b) add the anti-child-attachment check (Tier 1 change 2). Pick one and justify.
3. What is the full fix? Answer: all three tiers landed.
4. **r7.4 methodology comparability.** MoE data was collected with the un-hardened wrapper at 900s. Dense gap-fill is running now at 900s. If we change the wrapper between now and re-runs, is cross-leg comparison still valid? Identify the specific changes that break comparability (e.g., changing MAX_RETRIES changes rescue rate) vs those that don't (e.g., adding WRONG_SESSION detection only affects trials that would have been bogus anyway). Recommend: hold Tier 1 changes 2+3 until r7.4 is fully collected; Tier 1 change 1 (env override) is comparability-safe because it only activates when `TIMEOUT_PER_TURN` is explicitly set.
5. What's the contribution path for Tier 3 upstream? From Phase 2c.

**Output:** integrated into §3, §4, §5 of the final artifact. No separate intermediate file.

### Phase 4 — Assembly (main session, ~20 min)

**Scope:** write `ARTIFACT-r7.4-wrapper-sigterm-fix-design.md` by integrating:

- Phase 1 research (Root-Cause Analysis section)
- Phase 2a/2b/2c artifacts (three-tier design sections, with the diffs inlined)
- Phase 3 synthesis (deployment sequencing + risk analysis sections)

**Structure of the final artifact:**

```
[TASK CLASS: structured]
Justification: ...

# ARTIFACT — r7.4 wrapper SIGTERM fix design

## 1. Executive summary
  - One-line root cause
  - Three-tier overview
  - Minimum-viable-change callout
## 2. Root-cause analysis
  - Failure chain
  - Confirmed via: Phase 1 citations + empirical evidence (T5-run1 incident, child-session content string)
  - Hook points enumerated
## 3. Tier 1 — Wrapper mitigation
  - Change 1: TIMEOUT_PER_TURN env override (unified diff + rationale)
  - Change 2: anti-child-attachment check (unified diff + rationale + edge cases)
  - Change 3: MAX_RETRIES decision (recommendation + rationale)
  - What would disprove this design
## 4. Tier 2 — Check-script hardening
  - Gate design (variant choice i/ii/iii + rationale)
  - Unified diff
  - Interaction with Tier 1 (defense-in-depth case)
  - What would disprove this design
## 5. Tier 3 — Upstream Hermes SIGTERM handler
  - Hook point + file:line
  - Signal-handler architecture
  - SIGINT coverage decision
  - Double-fault safety
  - Unified diff
  - Test plan (including dev-environment recommendation)
  - Contribution path
  - What would disprove this design
## 6. Deployment sequencing
  - Independence matrix
  - Minimum change to unblock r7.4 dense gap-fill
  - Full-fix deployment order
## 7. Risk analysis
  - Per-tier failure modes
  - r7.4 methodology comparability — explicit hold-until-data-complete recommendations
  - Tripwire safety across each tier
## 8. Appendix — exact file versions at time of design
  - md5/sha256 of probe-variantF-wrapper.sh, probe-variantF-check.py, and the VM's run_agent.py
```

**Verification gate:** every section 3/4/5 must cite file:line for the target of each diff. Section 6 must identify minimum-viable-change. Section 7 must address comparability.

### Phase 5 — Judge verification (fresh sub-agent, ~20 min)

**Judge prompt (minimal, shielded):**

> You are a fresh judge with no prior context. Evaluate `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-wrapper-sigterm-fix-design.md` against the verification criteria below. You do NOT receive the design worker's reasoning beyond the artifact itself. Read only: the artifact, the target files (`probe-variantF-wrapper.sh`, `probe-variantF-check.py`), and — for Tier 3 — the VM file at the cited path via `ssh ubuntu-vm`.
>
> **Verification criteria.**
> 1. Every unified diff in the artifact applies cleanly against the current file version. Verify line numbers are still valid.
> 2. Every file:line citation in Root-Cause Analysis points at a real symbol in the real file.
> 3. The "minimum viable change to unblock r7.4 dense gap-fill" recommendation is coherent — implementable from the artifact alone, with comparability implications addressed.
> 4. Tier 2's gate variant choice is justified. Tier 3's signal-handler architecture is signal-safe under Python's constraints.
> 5. Each tier section includes a "What would disprove this design" entry.
> 6. Risk analysis names at least one concrete breakage for each tier.
> 7. No production changes were made in the course of producing the artifact (check `git status` — only untracked new artifact files should be present).
>
> **Verdict:** APPROVE | REVISE | RESTART. Write to `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.4-wrapper-sigterm-fix-judge-verdict.md`. If REVISE, list specific fixes. If RESTART, identify which phase produced the fatal flaw.

**On judge failure:** planner dispatches a new worker for the flagged tier only; original worker context is not reused. Re-run Phase 5 after fix.

---

## 3. Task state

| ID | Task | Status | Depends on | Verifier |
|----|------|--------|------------|----------|
| 0 | Orientation | pending | — | self |
| 1 | VM research | pending | 0 | judge (via phase 5) |
| 2a | Tier 1 design | pending | 1 | judge |
| 2b | Tier 2 design | pending | 1 | judge |
| 2c | Tier 3 design | pending | 1 | judge |
| 3 | Sequencing & risk | pending | 2a, 2b, 2c | judge |
| 4 | Assembly | pending | 3 | judge |
| 5 | Judge verification | pending | 4 | self-terminating |

2a, 2b, 2c run in parallel — a single planner-message dispatches all three after Phase 1 lands.

---

## 4. Authorization & scope

**May:**
- Dispatch read-only research workers with SSH access to VM.
- Dispatch design workers that produce artifact files under `/Users/briantaylor/Projects/AgentFW/` root (new files only — no edits to tracked files).
- Read any file on the VM that isn't a tripwire.
- Read session JSONs under `~/.hermes/sessions/`.

**May NOT:**
- Edit `probe-variantF-wrapper.sh`, `probe-variantF-check.py`, `variants/hermes/HERMES-variantF.md`, or any file under `variants/hermes/`.
- Edit any file on the VM at all.
- Run any probe.
- Touch tripwires (HERMES.md, SKILL.md, jira-briefing.sh, useDashboard.ts).
- Start/stop any VM process. The gap-fill worker is actively running.
- Edit `core/`, `references/`, `playbooks/`, `templates/`, or non-Hermes variants.
- Commit to git or push remotes.

**Worker scope declaration template** (each dispatched worker receives):
- Allowed paths: (enumerated per phase above)
- Allowed operations: read, grep, jq, Python inspection, artifact-file write in project root
- Forbidden operations: all edits to tracked files; any VM writes; process control on VM
- Side-effect budget: artifact-file writes only (new files, not overwrites of tracked files)
- Escalate if: tripwire md5 changes observed during research; gap-fill worker process appears to be stalled; Phase 1 research discovers the save path does not exist as hypothesized

---

## 5. Success criteria

The plan succeeds when:
1. `ARTIFACT-r7.4-wrapper-sigterm-fix-design.md` exists at project root.
2. Phase 5 judge returns APPROVE.
3. An implementation worker in a later session can implement each tier from the spec alone — exact file paths, exact line numbers, exact diffs or near-diffs, with rationale and edge cases flagged.
4. No production files were modified. `git status` shows only new untracked artifact files attributable to this plan.
5. Tripwires are clean at plan end (re-verify before finalizing Phase 4).

**Falsifiability — what would prove the plan was wrong:**
- If Phase 1 research discovers the session-save path is NOT `atexit`-based (e.g., already has a SIGTERM handler that's buggy for a different reason), Tier 3's proposed architecture may be fundamentally misframed. The plan explicitly allows Phase 1 to disprove the hypothesis — the worker brief says "If any hypothesis is disproven, say so explicitly."
- If the wrapper's current fallback-recovery block doesn't look like what's assumed in §2a (e.g., the gap-fill worker is actively mutating the wrapper as I write this — it isn't, the wrapper is only being *read* by active probes), Tier 1 diffs will be off-line. Mitigated by Phase 5 judge re-checking line numbers at verification time.
- If r7.4 dense gap-fill is actually *not* blocked by this issue (e.g., the T5/T6/T10 runs are already succeeding through some other path), then Phase 3's "minimum viable change" becomes a lower priority recommendation. Phase 0 will surface this by checking `PROGRESS.md` task status for the gap-fill worker at plan-start.

---

## 6. Known traps

- **The gap-fill worker is actively invoking the wrapper.** Do NOT edit `probe-variantF-wrapper.sh` at any point. Do NOT touch it even for "harmless" whitespace. Any mutation mid-run corrupts the probe. This is a hard rule — the entire plan is design-only explicitly to honor this.
- **Tripwires.** `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` and `jira-briefing.sh` back Monday 8am Jira-cron. Check md5s before Phase 1 research start and at plan end.
- **Source tag not persisted in session JSON** (per HANDOFF §8). The wrapper already scans by `--source` flag content grep — the Phase 2a worker should not assume `--source` is in the JSON's top-level fields.
- **Hermes binary is in ~/.hermes/hermes-agent/venv/bin/hermes.** The source is a sibling to the venv. Changes to source take effect on next invocation (no restart needed — Python interpreter reloads).
- **MoE/dense comparability.** r7.4 MoE data was collected at 900s timeout. Dense gap-fill is running at 900s. If Tier 1 change 1 (env override with default=900) is applied, nothing changes unless a caller exports `TIMEOUT_PER_TURN=1500`. This is comparability-safe. All other Tier 1 changes potentially affect rescue rate — hold them.
- **Don't create intermediate artifacts that end up untracked and confuse future agents.** Phases 1, 2a, 2b, 2c each produce a named artifact; these are the PLAN's structured outputs, not clutter. Name them exactly as specified so a future agent greps find them.

---

## 7. Estimated timeline

Sequential: ~3h15m. Parallelized (Phases 2a/2b/2c concurrent): ~2h15m.

| Phase | Sequential | Parallel |
|-------|------------|----------|
| 0 | 5m | 5m |
| 1 | 45m | 45m |
| 2a | 30m | 30m (concurrent) |
| 2b | 30m | (concurrent) |
| 2c | 60m | 60m (gates rest) |
| 3 | 15m | 15m |
| 4 | 20m | 20m |
| 5 | 20m | 20m |

---

## 8. Next action

Upon plan approval: execute Phase 0 (orientation), then dispatch Phase 1 research worker. Do not begin Phase 2a/2b/2c until Phase 1 artifact exists and planner has read it.
