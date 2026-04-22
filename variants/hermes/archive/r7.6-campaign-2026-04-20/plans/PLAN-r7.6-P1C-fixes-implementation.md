[TASK CLASS: structured]
Justification: Multi-fix implementation plan spanning judge code, wrapper, parent/child contracts, and methodology gating. Each fix has its own failure mode, rollback, and verification. Role-separated worker/judge dispatch required.

# PLAN — r7.6-P1C fixes implementation (rev 2, 2026-04-19 23:15)

## Revision log

- **rev 1 (2026-04-19 ~20:30):** initial 3-fix plan authored against diagnostic artifacts, before Arm B was complete.
- **rev 2 (2026-04-19 23:15, this rev):** post-Arm-B + post-T10-completion + post-fresh-judge-sample update. Incorporates:
  - Arm B final results (20/20 — T6-run5 + T10 × 5 added by run-only worker at 23:08).
  - 5-trial fresh-judge sample (ARTIFACT-r7.6-judge-fresh-verdict-{1..5}.md at 23:02): agreement 3/5 (below ≥4/5 threshold). Two disagreement classes found.
  - HERMES-WORKER.md overlay confirmed as the primary remedy (Arm A 3/20 → Arm B 9/11 non-LOST = +67 pp).
  - New error modes surfaced: parent one-shot misclassification under retry context (3/14 LOST on Arm B); pseudo-tool-call rendered as markdown text; `<tool_call|>` marker variant.

**What changed structurally:**
- Fix 1 (turn-budget preamble) → **DEPRECATED**. HERMES-WORKER.md overlay already does this work. Kept in "deferred / arm-A-only" section for completeness.
- Fix 2 (channel-marker detector port) → **expanded**. Regex widened to cover `<tool_call|>`; added pseudo-tool-call-as-markdown detector; added calibration-diff gate against fresh judge.
- Fix 3 (variantH→I wrapper backport) → **downgraded from P0 to P2 defense-in-depth**. Data shows the bug manifests as LOST (correctly handled by judge), not false-COMPLIANT (as diag 3 originally claimed). Still worth landing but no longer urgent.
- **NEW Fix 4 — parent one-shot misclassification on retry.** 3/14 Arm B trials classified as one-shot-no-goal from retry context. New failure mode not present in Arm A.
- **NEW Fix 5 — judge calibration & Agent-tool pre-flight gate.** Fresh-judge sample agreement 3/5; two systematic-error classes in orchestrator-judge. Plus methodology regression: Agent/Task dispatch missing across r7.5-F.2 and r7.6-P1C sessions.

---

## 1. Summary & sequencing (rev 2)

| # | Fix | Priority | Files touched | Worker est. | Gating dep |
|---|-----|----------|---------------|-------------|------------|
| 1 | Turn-budget preamble in task-input | **DEPRECATED** (overlay obsoletes) | `probe-tasks.md` | — | — |
| 2 | Expanded channel-marker + pseudo-tool-call detector | **P0** | `judge-trial.py` | ~60 min | Arm B done ✓ |
| 3 | Back-port variantH anti-child-attachment to variantI | **P2** (defense-in-depth) | `probe-variantI-wrapper.sh` | ~60 min | Arm B done ✓ |
| 4 | Parent one-shot misclassification guard | **P0** | `HERMES-variantF.md` and/or `delegate_worker_v2.py` and/or `probe-variantI-wrapper.sh` correction path | ~90 min (investigation-heavy) | Fix 5 pre-flight |
| 5 | Judge calibration audit + Agent-tool pre-flight gate | **P0** (methodology) | new pre-flight script + `run-arm.sh` caller | ~45 min + fresh-agent-session time | — |

Priority order: **Fix 5 first** (methodology gate), **then Fix 2 and Fix 4 in parallel** (independent targets), **Fix 3 last** (low urgency). Fix 1 is not scheduled.

---

## 2. Pre-flight checks (main session, before any worker)

**2.1 — Agent-tool availability.** NEW gate per Fix 5:
```
# In the orchestrator-candidate session, verify Agent dispatch works.
# If the session lacks Agent/Task access, ABORT and escalate — don't proceed with fallback judging.
```
Implementation: a 1-line "spawn trivial echo sub-agent" probe. If it fails, planner must move to a session where Agent dispatch is available before running any probe or judge.

**2.2 — VM status.**
```
ssh ubuntu-vm 'pgrep -af hermes || echo NONE'
```
Arm B is complete (unstaged at 22:40, restaged+unstaged at 23:08 for run-only T10 completion). VM should show `NONE`. If not, abort.

**2.3 — Tripwire baseline.**
```
ssh ubuntu-vm 'md5sum ~/.hermes/hermes-agent/HERMES.md \
  /media/psf/Projects/chief-of-staff-dashboard/src/hooks/useDashboard.ts \
  ~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh \
  ~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md'
```
Expected (canonical, per ARTIFACT-r7.6-P1C-run-only.md):
- HERMES.md = `0780c232a6cb52e13e432261f0d68ad9`
- SKILL.md = `fb1a5a5208a6cf2fcb8252aac10397eb`
- jira-briefing.sh = `a1dce6e989527686124d0860830627c9`
- useDashboard.ts = `5503ee1c2ef7d635a020eea275e41239`

**2.4 — File-under-edit baselines.**
```
md5 /Users/briantaylor/Projects/AgentFW/probe-variantF-wrapper.sh \
    /Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh \
    /Users/briantaylor/Projects/AgentFW/probe-variantH-check.py \
    /Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh \
    /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md \
    /Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py \
    /Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-WORKER.md \
    /tmp/probe-r7.6-P1C-logs/judge-trial.py
```

**2.5 — Preserve all P1C evidence.**
```
cp -a /tmp/probe-r7.6-P1C-logs /tmp/probe-r7.6-P1C-logs.snapshot-rev2
```
Also preserve the 5 fresh-judge verdicts + setup + calibration artifacts:
```
cp /Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-judge-{calibration,sample-setup,fresh-verdict-*,brief-*}.md \
   /tmp/probe-r7.6-P1C-logs.snapshot-rev2/
```

**2.6 — Git status sanity.** None of the target files (judge-trial.py in /tmp; probe-variantI-wrapper.sh untracked per git status) are tracked. Rollback is via the snapshot at §2.5, not via git.

---

## 3. Fix 1 — Turn-budget preamble (DEPRECATED)

**Status:** NOT SCHEDULED in rev 2.

**Rationale for deprecation.** HERMES-WORKER.md (variantI overlay, already deployed) teaches the child worker directly:
- §1: PLAN-first contract (forces the worker to emit `PLAN: ...` as its first utterance)
- §3: BLOCKED template (forces structured stop-early when files are missing)
- §5: anti-fabrication guidance

Evidence that this is working at runtime:
- ARTIFACT-r7.6-P1C-run-only.md T10-run1 child-final-content: `"BLOCKED: I lack the necessary tools (write_file, patch, or terminal) to create the directory migrations/postgres-12-to-16/ ..."` — exactly the HERMES-WORKER.md §3 template.
- Arm B non-LOST PASS rate: 9/11 (82%) vs Arm A 3/20 (15%). +67 pp on the same tasks, same model, same toolset — the only difference is HERMES-WORKER.md overlay.

**Decision:** a turn-budget preamble appended to `probe-tasks.md` would be redundant for Arm B (overlay covers it) and would bias any future cross-condition comparison. **Not scheduled.** If a future probe deliberately runs without overlay and hits the turn-efficiency cascade again, revisit Fix 1 as a minimal-impact preamble (not overlay-equivalent).

**Out-of-band note:** rev 1 of this plan claimed this fix was the primary remedy for the turn-efficiency cascade. That claim was wrong in emphasis — overlay, not preamble, is the primary remedy. Rev 2 corrects the record.

---

## 4. Fix 2 — Expanded judge-side detector (P0)

### 4.1 Design

Port + extend the channel-marker detector into `/tmp/probe-r7.6-P1C-logs/judge-trial.py`. Two classes of detection, both as gates in `eval_completion()` and `eval_correctness()`.

**Class A — marker-only content (expanded regex).** The rev-1 regex covered only `<channel|>`. Rev 2 widens to all observed pure-marker variants:

```python
_MARKER_ONLY_RE = re.compile(
    r"^\s*(?:"
    r"(?:<\|?(channel|tool_call|start|end|message|return)\|?>\s*)"  # any known sentinel
    r"|(?:thought\s*<\|?channel\|?>\s*)"                             # known "thought\n<channel|>" pattern
    r"|(?:analysis\s*<\|?channel\|?>\s*)"                            # Harmony analysis header
    r")+\s*$",
    re.IGNORECASE | re.DOTALL,
)
```

Observed variants justifying each alternative:
- `<channel|>`, `<|channel|>` — 13/20 Arm A children (diag §2.3) + 7+ Arm B children (per P1C table per-trial failure notes).
- `thought\n<channel|>` — trial 11 final content (diag §2.1).
- `<tool_call|>` — armB-T6-run2 (fresh verdict 4: "sentinel leakage in assistant content at indices 5, 7, 9, 11, 13, 15, 21, 23, 25, 27, 29, 31, 33").
- `analysis`/`return`/`message` — seen in Harmony-format training-data spillover (ARTIFACT-r7.6-inv-3-pseudo-tool-call.md).

**Class B — pseudo-tool-call rendered as markdown text.** New requirement from fresh verdict 3 (armB-T5-run1): the orchestrator passed a trial where the worker halted mid-plan and emitted `search_files(pattern="*tasks*", target="files", path=".../server")` as **markdown-fenced text** instead of as a structured tool call. Fresh judge caught it; orchestrator did not.

Detector: in `eval_completion()`, AFTER the marker-only gate, scan the last assistant content for code-fenced text that matches a tool-call invocation pattern and is NOT followed by a real tool result:

```python
_PSEUDO_TOOL_CALL_RE = re.compile(
    r"^\s*```[\w]*\s*\n?"                                 # code fence
    r"(?:search_files|read_file|write_file|patch|terminal|todo|clarify|delegate_\w+)"
    r"\s*\([^)]*\)\s*\n?```?\s*$",
    re.IGNORECASE | re.DOTALL,
)

def eval_completion(messages):
    ...
    # After marker-only check:
    if _PSEUDO_TOOL_CALL_RE.search(content.strip()):
        # Also verify there's no corresponding real tool call at the same turn
        last = final_assistant_msg(messages)
        if not (last.get("tool_calls") or []):
            return False, f"pseudo-tool-call as markdown (no structured tool_call): {content.strip()[:120]!r}"
```

**Class C — chain-depth diagnostic.** Scan all assistant messages; count marker-only turns. Emit as `channel_pollution_depth` in rationale. Does NOT by itself flip verdicts — informational only. Retained from rev 1.

### 4.2 Calibration-diff gate (NEW)

After porting the detectors, run the judge against the 5 fresh-verdict samples (briefs 1-5) and diff against the fresh-judge results. The calibration gate:

- **Post-fix agreement with fresh judge on the 5 samples must be ≥4/5.**
- Currently (rev-1 judge): 3/5 (60%). Specifically:
  - Trial 2 (armA-T4-run4): fresh says PASS, orchestrator says FAIL (thrash false positive) — **judge is too strict on `search_files` query similarity**.
  - Trial 3 (armB-T5-run1): fresh says FAIL (pseudo-tool-call mid-halt), orchestrator says PASS — Class B detector addresses this.
- Post-fix predictions:
  - Trial 3 should flip to FAIL (Class B catches the pseudo-tool-call) — **agreement +1 (3 → 4/5)**. Gate clears.
  - Trial 2 stays disagreed unless Fix 2 ALSO relaxes the thrash detector. The pre-existing `eval_turn_efficiency` loop-detector at lines 389-449 treats "`session.ts|middleware.ts|auth.test.ts`, `session`, `\\.ts$`, `\\.py$`" as near-identical; fresh judge reads them as "progressively narrowed." **Decision:** tighten the near-identical detector to require ≥3 *literally identical* queries in a row, not substring-match heuristic (rev-1 judge line 437's `q[i] in q[i-1]` is the offending check). This flips trial 2 to PASS — **agreement 5/5**.

Both changes required to clear the calibration gate.

### 4.3 Worker brief

**Scope.** May edit `/tmp/probe-r7.6-P1C-logs/judge-trial.py`. MUST NOT edit `probe-variantH-check.py`, VM `run_agent.py` (already has a detector — don't conflict), any other file.

**Task.**
1. Port `_MARKER_ONLY_RE` (§4.1 Class A) to module level (~line 49).
2. Port `_PSEUDO_TOOL_CALL_RE` (§4.1 Class B) to module level.
3. In `eval_completion()` (~line 176), add BOTH gates after the short-content check. Return FAIL with the specified reason strings.
4. In `eval_turn_efficiency()` (lines 437-447), replace the substring-match near-identical heuristic (`q[i] in q[i-1] or q[i-1] in q[i]`) with strict literal-equality (`q[i] == q[i-1]`). Keep the ≥3-consecutive requirement.
5. Add `channel_pollution_depth` diagnostic to `rationale["completion"]`.
6. Run the 5-sample calibration diff (§4.4) and attach results.

**Verification before reporting.**
- Syntax: `python3 -c "import ast; ast.parse(open('/tmp/probe-r7.6-P1C-logs/judge-trial.py').read())"`.
- Unit checks per §4.1 — verify regex matches each cited variant.
- Replay against all 20 Arm A + 20 Arm B children (40 trials).
- Calibration diff per §4.2 against the 5 fresh-verdict samples: expected final state 5/5.

**Deliverable.** Patched `judge-trial.py` + `/tmp/probe-r7.6-P1C-logs.post-fix2/arm-{A,B}-verdicts.replay.txt` + a calibration comparison table.

### 4.4 Judge verification gate (fresh sub-agent)

**Judge brief (shielded).**
1. Diff patched vs snapshot judge-trial.py. Confirm both regexes present, near-identical heuristic removed.
2. Replay must show:
   - armA-T4-run4 (trial 2) flips FAIL → PASS.
   - armB-T5-run1 (trial 3) flips PASS → FAIL.
   - All 11 previously-FAIL trials with channel-marker-only final content (Arm A + Arm B) stay FAIL.
   - All Arm A "search_files variety" trials that currently pass (trial 1, 3, 5) stay PASS.
3. Calibration agreement vs fresh verdicts = 5/5.
4. No additional unexpected flips on the other 32 trials (verify with full diff).

### 4.5 Risks & rollback

- **Risk: strict literal-equality heuristic lets some genuine thrash slip through.** *Mitigation:* the search-thrash cases the rev-1 judge caught on Arm A (trials 4, 13, 17, 18, 19) deserve re-inspection — some may have TRULY identical queries. Report the N actually-identical subset.
- **Risk: pseudo-tool-call regex false-positives on legitimate prose.** E.g., a summary saying "I would call `search_files(...)` if I had more turns" is legitimate reflection, not a halted mid-tool. *Mitigation:* the regex requires the pattern to be the ENTIRE stripped content, not a substring — narrow enough.
- **Rollback:** restore from `/tmp/probe-r7.6-P1C-logs.snapshot-rev2/judge-trial.py`.

### 4.6 Falsifiability

Calibration diff is the falsifier. If post-fix agreement < 5/5 on the 5 samples, the chosen regex / heuristic is wrong; do NOT ship the fix and re-dispatch with more data.

---

## 5. Fix 3 — variantH anti-child-attachment back-port to variantI (P2, defense-in-depth)

### 5.1 Re-scope rationale

The rev-1 plan treated this as urgent because the Arm B T4-run3 / T5-run4 SIGTERM cascades produced "false-COMPLIANT attempts=3 elapsed=914s." The final data shows a different picture:

- Both trials now show `WORKER_QUALITY=LOST` (child_sid=NO_GOAL) in the orchestrator verdict. The judge correctly refused to count them.
- The 6-trial run-only completion (T6-run5 + T10 × 5) hit ZERO SIGTERM events. All COMPLIANT attempts=1.
- The cascades are real and will recur on long tasks under overlay — but the judge's LOST handling prevents them from contaminating the PASS/FAIL denominator.

**Revised priority:** P2 defense-in-depth. Worth landing for methodological cleanliness (prevents wrapper wasting 914s on each SIGTERM'd trial — time budget hygiene) but not ship-gating.

### 5.2 Design

Unchanged from rev 1 (port variantH lines 63-74, 160-172, 200-295 to variantI). Optional add: per-verdict case for `VIOLATION:EMPTY_SYNTHESIS` in `correction_for()`.

Additionally in rev 2: **raise `TIMEOUT_PER_TURN` default to 1500s for overlay-on probes.** Data from P1C:
- Arm B T6-run2: 538s (vs Arm A 140s — 3.8× slower).
- Arm B T5-run5: 872s (near the 900s ceiling, completed COMPLIANT).
- T5-run4 / T4-run3 hit 900s and SIGTERM'd.

At `TIMEOUT_PER_TURN=1500`, the three SIGTERM cases would have had a chance to complete. Cost: longer worst-case trials. Benefit: fewer SIGTERM cascades needing the anti-child-attachment guard.

### 5.3 Worker brief

**Scope.** May edit `probe-variantI-wrapper.sh`. Must read variantH wrapper + check for reference. No probe runs during edit. Must verify Arm B complete (§2.2).

**Task.**
1. Snapshot `probe-variantI-wrapper.sh.pre-rev2-fix3`.
2. Raise `TIMEOUT_PER_TURN` default from 900 to 1500 (line 29 per diag §5). Add env override idiom `: "${TIMEOUT_PER_TURN:=1500}"` if not already present.
3. Port Block 1 (run_check + EXPECTED_PREFIX_B64).
4. Port Block 2 (anti-child-attachment fallback).
5. Add header comment `# Fix 3 (rev 2, r7.6-P1C) — anti-child-attachment + timeout raise 2026-04-19`.
6. `bash -n` syntax check.
7. Grep verification: `expected-prompt-prefix` count ≥2; `EXPECTED_PREFIX_B64` count ≥2; `TIMEOUT_PER_TURN` count ≥1 with default 1500.

### 5.4 Judge verification

Unchanged from rev 1 — diff against variantH, confirm tripwires, confirm HERMES_WORKER_OVERLAY plumbing preserved.

### 5.5 Post-land validation

Artificial SIGTERM probe unchanged. Plus: one Arm B-style T5 trial at the new 1500s timeout to confirm no regression on already-passing configurations.

### 5.6 Sequencing note

Fix 3 can run in parallel with Fixes 2 and 4. No file overlap.

---

## 6. Fix 4 — Parent one-shot misclassification on retry (NEW, P0)

### 6.1 Problem

Three Arm B trials (T4-run3, T5-run4, T6-run4) classified as `one-shot` with no `goal` field, producing LOST verdicts. Evidence from fresh verdict 5 + run-only artifact:

- T4-run3 parent session `20260419_212256_d885e6` contains 2 `delegate_worker_v2` calls, both `classification=one-shot`, both with justifications referencing "user is correcting a protocol violation / providing corrective instruction regarding the AgentFW protocol."
- These are *retry* sessions where the wrapper sent a correction message. The parent classified the correction message ITSELF as a one-shot task (meta / protocol compliance) rather than re-dispatching the original structured task.

This is a β-fuse contract violation: the parent should preserve the original classification across retry rounds. Arm A did NOT show this because its SIGTERM-fallback cascade lands in NO_MARKER rather than one-shot-no-goal. The overlay (Arm B) puts the child in a state where it *can* classify the correction as one-shot — a new state introduced by HERMES-WORKER.md.

### 6.2 Hypothesis tree

Before any edit, a research sub-agent must distinguish three possibilities:

- **H4A — HERMES-variantF.md lacks guidance on retry classification.** The β-fuse spec doesn't explicitly say "on retry, maintain original classification." If so, fix is a ~5-line addition to HERMES-variantF.md's classification gate.
- **H4B — The wrapper's correction message is mis-formatted.** The wrapper's default correction (`probe-variantI-wrapper.sh` line 138 `*)` branch) may inadvertently frame the correction as a new task rather than a retry of the original. Fix is to rewrite the correction to re-inject the original task text.
- **H4C — `delegate_worker_v2.py` accepts `classification=one-shot` without `goal`, silently.** Schema may allow it. If so, fix is a schema-level requirement that one-shot calls produce a terse acknowledgment as the goal, not `None` / empty.

Likely cause is H4B (retry context pollution) with H4A as contributing factor. H4C is the structural backstop.

### 6.3 Worker brief — investigation phase (READ-ONLY first)

**Scope.** Read-only investigation on VM + local files. No edits until root-cause confirmed.

**Task.**
1. Fetch the three parent sessions' message chains:
   - `ssh ubuntu-vm 'jq ".messages" /home/parallels/.hermes/sessions/session_20260419_212256_d885e6.json'` (T4-run3).
   - Same for `20260419_214432_52b6a8` (T5-run4) and `20260419_221749_e5e803` (T6-run4).
2. For each: identify at what message index the wrapper's correction was injected, what the parent's response to the correction was, and what the `delegate_worker_v2` argument's `justification` field contains.
3. Check `/Users/briantaylor/Projects/AgentFW/probe-variantI-wrapper.sh` lines 130-150 (correction_for function) — what exactly is being injected?
4. Check `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantF.md` — is there any clause covering retry classification?
5. Check `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker_v2.py` — schema requirements on `goal`.
6. Assess H4A / H4B / H4C. Weigh evidence.

**Deliverable.** `ARTIFACT-r7.6-P1C-diag-parent-one-shot.md` (similar format to prior diag artifacts): root cause, evidence, recommended fix + affected files + approximate diff, falsifiability.

### 6.4 Worker brief — implementation phase (conditional on investigation)

**Scope depends on diag output:**

- **If H4A dominant:** edit `HERMES-variantF.md` to add a retry-classification clause (~5 lines). Worker scope: that file only.
- **If H4B dominant:** edit `probe-variantI-wrapper.sh::correction_for()` to re-inject the original task text in corrections. Worker scope: wrapper only. Also update `probe-variantH-wrapper.sh` symmetrically (H4B would also affect variantH; handle in same PR to avoid drift).
- **If H4C dominant:** edit `delegate_worker_v2.py` schema to require `goal` for ALL classifications (not just structured/long-horizon). This is a protocol change requiring coordination.

Plan covers all three branches. Pick at implementation time based on diag.

### 6.5 Verification

5-trial smoke on Arm B T4 + Arm B T5 with artificial retry injection (test the retry path without going through SIGTERM). Pass criteria: all retries preserve the original structured classification; no one-shot-no-goal outcomes.

### 6.6 Risks

- **Risk: fix alters behavior on legitimate one-shot tasks (T1/T2/T8).** *Mitigation:* smoke-probe 2 × T1 after fix. Expect COMPLIANT attempts=1, classification=one-shot.
- **Risk: fix interacts with Fix 2.** *Mitigation:* Fix 2 is judge-side; Fix 4 is probe-side. No file overlap.

---

## 7. Fix 5 — Judge calibration + Agent-tool pre-flight gate (NEW, P0)

### 7.1 Problem

Two related methodology findings from rev 2 data:

**7.1a — Orchestrator-judge has systematic error in both directions.** Fresh-judge sample agreement = 3/5:
- **False FAIL:** trial 2 (armA-T4-run4) — orchestrator flagged search thrash on queries that fresh judge reads as "progressively narrowed."
- **False PASS:** trial 3 (armB-T5-run1) — orchestrator missed a pseudo-tool-call halt-in-progress that fresh judge caught.

Fix 2 §4.2 addresses both specific cases structurally. But the CALIBRATION PROCESS itself is the real fix: there should be a standing gate that sample-verifies orchestrator verdicts against fresh-judge verdicts before any ship decision.

**7.1b — Agent/Task dispatcher missing in orchestrator sessions.** ARTIFACT-r7.6-judge-calibration.md documents that the intended fresh-sub-agent calibration was BLOCKED because the session lacked Agent dispatch. Same regression seen in r7.5-F.2 per the P1C results artifact disclosure. This is a stable property of the probe-orchestration session configuration, not a transient issue.

### 7.2 Design

Two artifacts:

**7.2a — Pre-flight gate `probe-preflight.sh`.** New file at project root. Runs BEFORE any probe:
- Checks Agent/Task dispatch with a trivial "spawn echo sub-agent" probe. Exits nonzero if unavailable.
- Checks oMLX health.
- Checks VM tripwire canonical state.
- Reports pass/fail to stdout; exits nonzero on any check fail.

`run-arm.sh` (orchestrator caller) must invoke `probe-preflight.sh` as its first step and abort on nonzero exit.

**7.2b — Calibration protocol** (document, not code). New file `CALIBRATION-r7.6-judge-protocol.md`:
- 5-trial fresh-judge sample on every probe campaign (stratified per rev-1 §sample-setup: 2 PASS / 2 FAIL / 1 LOST across ≥2 tasks and both arms).
- Concordance threshold ≥4/5 (or ≥6/7 on 7-sample).
- If concordance < threshold, do NOT ship-gate on the probe aggregate; re-run judge or expand sample.
- Artifact template for fresh-judge briefs (base on existing `ARTIFACT-r7.6-judge-brief-N.md` format).
- Hard rule: orchestrator-in-process judging is a documented fallback, not the primary path.

### 7.3 Worker brief

**Scope.** May create two new files:
- `/Users/briantaylor/Projects/AgentFW/probe-preflight.sh` (new).
- `/Users/briantaylor/Projects/AgentFW/CALIBRATION-r7.6-judge-protocol.md` (new).

May edit:
- `/tmp/probe-r7.6-P1C-logs/run-arm.sh` to call `probe-preflight.sh` first.

No probe runs, no VM edits.

**Task.**
1. Write `probe-preflight.sh` per §7.2a. Should be idempotent, log to stdout with clear gate names, exit with specific codes for each failure class.
2. Write `CALIBRATION-r7.6-judge-protocol.md` per §7.2b. Include: sample-selection algorithm, concordance threshold decision tree, fresh-judge brief template (reference existing `ARTIFACT-r7.6-judge-brief-*.md` as examples), escalation path when concordance fails.
3. Edit `run-arm.sh` to call `./probe-preflight.sh` at top. Abort on nonzero.
4. `bash -n` syntax check on both scripts.

**Verification.**
- Run `probe-preflight.sh` in current session: should pass (Arm B unstaged, tripwires canonical). Verify log clarity.
- Run from a session WITHOUT Agent access (if available): should fail the Agent check.
- Grep `run-arm.sh` for preflight call.

### 7.4 Judge verification

Fresh sub-agent reads the new protocol document + the preflight script, confirms:
- Protocol's concordance thresholds match operator pre-commit.
- Preflight script's Agent-check is not bypassable via env var.
- `run-arm.sh` actually calls it.

### 7.5 Sequencing

Fix 5 runs FIRST in the Fix-order, because Fixes 2/3/4 need working Agent dispatch for their judge verification gates. Pre-flight gate confirms that dispatch is available.

### 7.6 Risks

- **Risk: Pre-flight is too strict; blocks legitimate probes.** *Mitigation:* each gate has `--skip-X` override flags that log a warning and continue; intended for cases where the operator knowingly accepts the risk. Agent-tool gate has NO skip flag — that's the point.
- **Risk: Protocol becomes aspirational.** *Mitigation:* protocol includes a concrete checklist that ship-judge artifacts must reference.

---

## 8. Sequencing matrix (rev 2)

| Step | Action | Runs in | Blocks | Blocked by |
|------|--------|---------|--------|------------|
| S0 | §2 pre-flight checks | main session | all | — |
| S1 | Fix 5 worker (preflight + calibration protocol) | sub-agent | Fix 2, 3, 4 verification | S0 |
| S2 | Fix 5 judge | fresh sub-agent | — | S1 |
| S3 | Fix 2 worker (judge expanded detectors) | sub-agent | — | S2 |
| S4 | Fix 4 worker — diag phase | sub-agent | Fix 4 impl | S2 |
| S5 | Fix 4 worker — impl phase | sub-agent | Fix 4 verify | S4 |
| S6 | Fix 3 worker (wrapper backport + timeout raise) | sub-agent | — | S2 |
| S7 | Fix 2 judge | fresh sub-agent | — | S3 |
| S8 | Fix 4 judge | fresh sub-agent | — | S5 |
| S9 | Fix 3 judge | fresh sub-agent | — | S6 |
| S10 | Arm B-repeat probe with all fixes active | main + workers | — | S7, S8, S9 |
| S11 | Ship artifact update | main | — | S10 |

S3, S4, S6 run in parallel after S2. S7, S8, S9 run in parallel after their respective workers. S10 is the validation probe (no new trials — re-run judge on the 40 existing child sessions + a fresh 3-trial T10 probe to confirm no regression).

**Fix 1 remains unscheduled.**

---

## 9. Authorization & scope (rev 2)

| Fix | May edit | Must NOT edit |
|-----|----------|----------------|
| 2 | `judge-trial.py` | `probe-variantH-check.py`, VM `run_agent.py` |
| 3 | `probe-variantI-wrapper.sh` | `probe-variantH-*`, `probe-variantF-*`, VM files |
| 4 diag | NONE (read-only) | — |
| 4 impl | EXACTLY ONE of {`HERMES-variantF.md`, `probe-variantI-wrapper.sh` + `probe-variantH-wrapper.sh`, `delegate_worker_v2.py`} per diag outcome | all others |
| 5 | `probe-preflight.sh` (new), `CALIBRATION-r7.6-judge-protocol.md` (new), `run-arm.sh` | anything else |

Global forbidden:
- `core/`, `references/`, `playbooks/`, `templates/`, non-Hermes variants.
- Tripwires (HERMES.md, SKILL.md, jira-briefing.sh, useDashboard.ts).
- Any VM write without explicit operator approval.
- Git commits without operator approval.
- Running a probe while another probe is active.

---

## 10. Success criteria (rev 2)

**Plan-level:**
1. All four scheduled fixes (2, 3, 4, 5) land with their judge verdicts PASS.
2. Post-Fix-2 calibration agreement on the 5 fresh samples = 5/5 (up from 3/5).
3. Fix 4 diag plus fix eliminates one-shot-no-goal cascades (verify on artificial retry probe).
4. Fix 5 pre-flight aborts any future probe in an Agent-dispatch-less session.
5. S10 re-judge of existing 40 child sessions with patched judge: expected flips per §4.4 (trial 2 FAIL→PASS, trial 3 PASS→FAIL; no other flips outside §4.4 prediction).
6. Tripwires remain canonical throughout.
7. `PROGRESS.md` updated at plan-end.

**Per-fix rollback criterion:**
- Fix 2: restore from `/tmp/probe-r7.6-P1C-logs.snapshot-rev2/judge-trial.py`.
- Fix 3: restore from `probe-variantI-wrapper.sh.pre-rev2-fix3`.
- Fix 4: restore the ONE file edited, per diag outcome. Snapshot before edit.
- Fix 5: remove new files; revert `run-arm.sh` edit.

---

## 11. Open questions (rev 2)

These are NOT pre-blockers to Fix work but must resolve before ship-gating:

1. **Does the +6 PASS delta (Arm B 9 vs Arm A 3) hold after Fix 2 recalibration?** Trial 3 flips FAIL → reduces Arm B by 1 → delta becomes +5. Trial 2 flips PASS → increases Arm A by 1 → delta becomes +4. Still above the operator's ≥+5 threshold on the rate-basis, but on absolute the gap narrows. Must be reported explicitly in any ship artifact.
2. **Does T10 (5 Arm B trials) under HERMES-WORKER.md §5 anti-fabrication actually work?** Run-only artifact shows T10 children at 6/6 COMPLIANT dispatch but some final contents are `thought\n<channel|>` (channel leak) — need fresh-judge sample on T10 before ship claims anti-fabrication.
3. **Is the oMLX slice-unhashable error (Arm B T4-run3 A1/A2 per diag §3) a transient or structural bug?** Not observed in the 6 later T10 runs. Watch for recurrence.
4. **Should HERMES-WORKER.md be promoted from overlay-only to canonical for the child worker's system prompt?** Strong evidence it helps; operator decision pending.

---

## 12. Known traps (rev 2)

- **Fixes now have inter-dependencies through calibration.** Fix 2's calibration-diff gate is the arbiter for whether the orchestrator-judge can be trusted. If Fix 2 fails its gate, the +6 ship signal is uncalibrated and NONE of the P1C aggregate data should be ship-gated on without a full fresh-judge re-pass.
- **HERMES-WORKER.md is already deployed and working.** Don't touch it in the course of these fixes. It's earned its canonical-promotion candidacy via the delta signal — but that's a separate future plan, not in scope here.
- **The pseudo-tool-call detector (Fix 2 Class B) risks false positives on legitimate reflective prose.** Watch for this during replay; if false positives > 0 on Arm A trials 1/3/5 (known-clean PASSes), tighten the regex.
- **Fix 4's one-shot-misclassification fix may interact with HERMES.md canonical preconditions.** If H4A is chosen (edit HERMES-variantF.md), that's NOT the canonical HERMES.md — canonical-on-VM stays at `0780c232…`. But if future promotion of HERMES-variantF.md to canonical is proposed, Fix 4's addition propagates.
- **Previous Fix 1's preamble approach would INTERFERE with HERMES-WORKER.md's §1 PLAN-first contract** (both try to be the first-thing-the-worker-reads). Double good reason to leave Fix 1 deprecated.
- **Run-only artifact observation: T6-run5 parent re-dispatched twice** (sibling children at 225521_775cf5 and 225547_3a9890). **Implication:** the "one primary child per parent" judging assumption doesn't always hold. Fix 2 should scan all children per parent and use the BEST child for quality assessment. Flagged for Fix 2 worker as "extra-credit" — not required for rev-2 gate.

---

## 13. Estimated timeline (rev 2)

| Step | Est. time |
|------|-----------|
| §2 pre-flight | 15m |
| Fix 5 worker + judge | 1h 15m |
| Fix 2 worker (including full 40-trial replay) | 1h 15m |
| Fix 2 judge | 30m |
| Fix 4 diag | 1h |
| Fix 4 impl + verify | 1h |
| Fix 3 worker + judge | 1h 30m |
| S10 re-judge + T10 fresh-sample | 1h |
| S11 PROGRESS + ship-artifact update | 20m |

Sequential: ~7h. Parallelized (Fixes 2, 3, 4 after Fix 5): ~5h. Fresh-judge dispatches dominate wall-clock.

---

## 14. Next action

Upon plan approval:
1. Run §2 pre-flight (including the new Agent-tool probe).
2. Dispatch Fix 5 worker (P0 methodology gate).
3. Once Fix 5 judge approves, dispatch Fixes 2, 3, 4-diag in parallel.
4. Dispatch Fix 4-impl after its diag completes.
5. After all fixes judge-pass, run S10 validation.

Operator confirmation required before first worker dispatch.
