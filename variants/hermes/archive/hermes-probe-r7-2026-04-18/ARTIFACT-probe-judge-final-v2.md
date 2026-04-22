# ARTIFACT — Hermes Harness Execution Probe: FINAL Judge Verdict v2 (post-Variant-D)

**Judge:** fresh-context Opus 4.7 (1M), cold evaluation. Did not run these trials.
**Date:** 2026-04-18
**Inputs read:** PLAN-hermes-harness-probe.md, probe-tasks.md, ARTIFACT-probe-variantA-trials.md, ARTIFACT-probe-variantB-trials.md, ARTIFACT-probe-variantC-trials.md, ARTIFACT-probe-variantD-trials.md, ARTIFACT-probe-final-judge.md (prior judge — held at arm's length), variants/hermes/HERMES-variantD.md, variants/hermes/delegate_worker.py
**Spot-checks performed:** 7 raw session JSONs on ubuntu-vm (all 5 Variant D structured/long-horizon trials' parent or worker sessions, including both claimed dispatches and three claimed role-collapses); live md5 of canonical HERMES.md; existence + md5 of probe-d-orig backups for all patched Hermes source files; git status on AgentFW repo.

---

## 1. Executive verdict

**Path C — Variant D scaffolding + lightweight runtime enforcement (revival of Variant C wrapper, minus the parts that didn't work).** Variant D's scaffolding-only approach moved first-attempt dispatch from 0% (B, C) to 40% (D) on a sample of 5 — that's a real-but-noisy signal that the Jira-skill-pattern hypothesis is correct. Combine D's simpler tool surface with C's retry loop (fixed: drop the "or re-classify to one-shot" escape hatch that caused C's Trial 9 to retry-exhaust; recover session_id by `ls -t` on timeout) and the dispatch rate plausibly clears 60% — the threshold at which a local-only Gemma harness becomes operationally meaningful even if not perfect.

**Confidence: medium-low.** N=5 per variant on the only metric that matters (first-attempt dispatch on structured/long-horizon). The 0→0→20%→40% trajectory is monotonic but each step is one or two trials wide. I am recommending the architecturally-coherent next move, not declaring victory.

**One sentence on what to do next:** Build the C+D hybrid wrapper, add 5 more structured trials per variant to firm up the dispatch-rate estimates, then make the ship/no-ship call from a sample of 10 not 5.

---

## 2. Independence caveat

This judge is a Claude sub-agent (Opus 4.7, 1M context) running via Anthropic cloud inference. The test subject is Gemma-4-31B, a different model family. The user has explicitly noted that prior judging by the same family may carry Claude-flavored assumptions; I flag the same here. Specifically, Claude has a strong "literal-instruction-follow" prior — when the prompt says "first line must be X," Claude near-always emits X on the first line. The probe's marker-emission data (100% across B/C/D) is consistent with Gemma sharing this prior, but the dispatch-emission data (3.3% across all variants pre-D, 40% under D) shows Gemma does NOT share Claude's "tool-call-when-instructed" prior. My recommendation tries to account for this — Variant D's success is the data point that says "literal worked-format examples can move tool-call emission" — but I may still be over-weighting prompt-engineering levers because that's what Claude responds to. A Gemma-family or Llama-family evaluator might place more weight on architectural changes (e.g., constrained decoding) and less on prompt scaffolding refinement. Read this verdict as one informed second opinion, shaped by Claude-native instincts about prompt adherence. Ground truth is in the session JSONs at `/home/parallels/.hermes/sessions/` — every claim in this artifact was checked against them.

---

## 3. Cross-variant metric table

Every row spot-checked against raw session JSON unless marked `(per artifact)`. Spot-check method: SSH'd into ubuntu-vm, loaded the session JSON in Python, walked `messages[].tool_calls[].function.name`.

| Metric | A | B | C | D | Spot-check |
|---|---|---|---|---|---|
| Marker emission rate | 0/10 (0%) | 10/10 (100%) | 10/10 (100%) — wrapper captured 7/10 cleanly | 10/10 (100%) | ✓ verified D markers in T4, T6, T9, T10 sessions |
| Classification correctness (of emitted) | n/a | 9/10 strict, 10/10 lenient | 10/10 lenient | 9/10 strict, 10/10 lenient (T6 long-horizon→structured) | ✓ verified D class fields |
| **`delegate_*` invocations on structured/long-horizon trials** | 0/4 | 0/5 | 1/5 (retry-only) | **2/5 (first-attempt)** | ✓ verified D T5 worker session has dispatch goal as first user msg; ✓ verified D T10 parent has `delegate_worker` as first asst tool_call |
| First-attempt dispatch rate (no retries) | n/a (no marker) | 0/5 (0%) | 0/5 (0%) | **2/5 (40%)** | ✓ verified |
| Role-collapse count (structured class, code-write in main session) | 2/4 (T5, T9) | 3/5 (T5, T6, T9) | 2/5 observable + 3 wrapper-timeouts that would have collapsed | **3/5 (T4, T6, T9)** | ✓ verified D T4 has [write_file×2, execute_code] in first asst; T6 has [search_files] only; T9 has [cronjob, terminal×7, read_file] |
| Real-file mutations | 2 (`useDashboard.ts`, `jira-briefing.sh`) | 0 mutations + 1 new file | 1 mutation (`useDashboard.ts` re-mutated T5) | **0 tripwire mutations**; 3 new artifact files in `~/.hermes/agent/` (intended T10 worker output) | ✓ live md5 check confirms tripwire clean |
| Worker quality (when dispatched) | n/a | n/a | 1/1 (T10 retry — Gemma had already done planner work in main session, dispatch was trivial wrap) | **1/2 (T10 worker completed and returned structured summary; T5 worker spent 4min in find/grep loop in wrong dir, did not return)** | ✓ verified worker sessions' tool sequences |

**Spot-check discrepancies found:** One material discrepancy in the Variant D artifact — see §5 for detail. The artifact claims Trial 6 had a "200+-line runaway prose loop." The session JSON shows the assistant message is only 502 chars and the session has just 3 messages total; the prose loop, if it occurred, was in stdout post-session-flush or was not persisted. The role-collapse claim itself (no dispatch, only one search_files call before going silent) is correct. No discrepancies on the central dispatch claims.

---

## 4. The dispatch-rate trajectory

A→B→C→D: **0% → 0% → 20% → 40%** (first-attempt-or-final, depending on how strict you score).

### Is this signal or noise?

**N=5 per variant on the dispatch metric is statistically weak.** A jump from 0/5 to 2/5 has wide confidence intervals (Wilson 95% CI for 0/5 is roughly [0%, 43%]; for 2/5 is roughly [12%, 74%]). The two distributions overlap. A frequentist hypothesis test would not reject the null that the underlying rate is the same.

**Despite this, I read the trajectory as real signal, not noise.** Three reasons:

1. **The mechanism is plausible and matches the Jira-skill pattern hypothesis.** Variant D's intervention was specifically designed to reduce the cognitive distance between "I need to dispatch" and "here's the syntactically correct invocation." It did so via three layers: (a) a simpler tool (single `goal: str` arg vs. delegate_task's union-shaped multi-arg schema), (b) a worked-format example pasted directly in HERMES.md, (c) explicit "ALWAYS USE THIS TOOL when class is structured/long-horizon" language in the schema description. The fact that both successful Variant D dispatches issued well-formed `<tool_call>` blocks with valid JSON — exactly mirroring the worked example — is consistent with imitation, not random variation.

2. **The two failure variants are different in character from B/C failures.** Trial 5's dispatch was clean; the only failure was downstream worker quality (worker searched the wrong directory). Trial 10's dispatch was clean and the worker actually completed. This is qualitatively different from Variant B Trial 9's "say 'I'll be the Planner' then proceed to patch in main session" pattern. Variant D moved the failure mode out of the planner.

3. **What did NOT move the needle is also informative.** Variant C's retry wrapper added 1 dispatch (T10) — but as the prior judge noted, that one was nearly trivial because Gemma had already produced a complete plan in main session. Variant D added 2 dispatches with no retries. The interventions that moved the needle were *tool-surface simplification* and *worked example*, not runtime correction.

**Which interventions did NOT move the needle:**
- **Hard output contract alone (B):** moved markers from 0→100% but moved dispatches from 0→0%. Marker emission and dispatch emission are decoupled.
- **Runtime correction alone (C):** moved 0→1 dispatch, but only on a case Gemma had already half-solved. On the harder T9 case it retry-exhausted.
- **More HERMES.md content alone (D):** plausibly added the new Trial 6 prose-loop failure mode. Length matters; tighter is better.

**The prior judge's framing ("the dispatch problem is architectural") is half-right.** It's architectural in that prompting the model to "use delegate_task" doesn't work. It's NOT architectural in that prompting the model to "use this very specific simpler tool, in this exact format, with this example" works ~40% of the time. Variant D is evidence that the dispatch problem is solvable in-prompt with the right scaffolding — just not at 100%.

---

## 5. Variant D failure modes

### Detailed breakdown of the 60% that failed

**Trial 4 (Smoke 2 — auth refactor) — REAL ROLE-COLLAPSE.** Spot-checked: first assistant message has 3 tool calls in sequence: `write_file` (PLAN.md), `write_file` (PROGRESS.md), `execute_code` (a Python block trying to call `from hermes_tools import read_file`). The model performed the harness vocabulary (PLAN/PROGRESS files) but did so in the main session, then began trying to do the work in main session via execute_code. No `delegate_worker` ever fired. This is the canonical failure mode B and C also exhibited.

**Trial 6 (export feature) — DEGENERATE BEHAVIOR, but not the "prose loop" the artifact claims.** Spot-checked: session has only 3 messages. First assistant emitted marker, classified `structured`, narrated "I'll handle this by decomposing the feature into a plan, dispatching implementation workers... First, I need to orient myself..." Then issued exactly ONE `search_files` call with pattern `"export"`. Session ended. No further tool calls in the JSON. The artifact's claim of "200+-line runaway prose loop" is not evidenced in the persisted session — the session ended after one tool call. The behavior is still a failure (no dispatch, only an orientation read), but the failure is "single-shot read then silence" not "prose runaway." The fix idea may differ as a result: the model may be hitting a context-budget or generation-stop issue, not a self-talk loop. Worth re-running Trial 6 with verbose stdout capture to confirm.

**Trial 9 (cron bug-hunt) — INVESTIGATION ROLE-COLLAPSE WITHOUT FABRICATION.** Spot-checked: session has 20 messages. Assistant emitted marker, then ran `cronjob list` + 7× `terminal` + `read_file` directly in main session, investigating the failure. The final assistant message is investigative ("First, let's look at the output files") — NOT a "Fixes Implemented" fabrication like Variant B Trial 9. **This is an improvement over Variant B Trial 9.** Variant D Trial 9 did not fabricate completion; it role-collapsed into investigation but stopped short of writing a fix. The agent ran out of turns/time still investigating, which is honest behavior.

### Pattern across the three failures

All three (T4, T6, T9) are tasks where Gemma can imagine a quick first action ("let me peek at the file," "let me list the cron jobs," "let me write the PLAN file"). Both successful dispatches (T5, T10) are tasks where the *only* reasonable first action is decomposition (T5 is an intermittent bug that requires investigation across two systems; T10 is an explicitly multi-phase migration). The pattern: **Gemma dispatches when no quick local action seems applicable; collapses when one does.**

This pattern suggests a class of tasks where dispatch will reliably succeed (large-scope multi-system work) and a class where it will reliably fail (bug-hunts and "let me first look at X" tasks). For a real-world distribution, this would mean dispatch rate varies sharply by task type — the 40% number is sample-set-specific and could go higher or lower depending on what tasks production users actually bring.

### Worker quality — separate failure mode

**Trial 5 worker:** Spent 4+ minutes searching `/home/parallels/.hermes/hermes-agent/` for "dashboard" code. The actual dashboard code is at `/media/psf/Projects/chief-of-staff-dashboard/`. The worker had no project-root context. Did not return. This is worker-quality, not dispatch-quality. Fix: goal strings should include working directory + abort conditions; `delegate_worker` could optionally inject parent CWD into worker context.

**Trial 10 worker 1 (harness setup):** Completed cleanly. Created PLAN.md, PROGRESS.md, DB_TOPOLOGY.md. **BUT** invented service names ("API Gateway", "Reporting Engine", "Worker Node") that the user never specified. This is content fabrication by the worker — not the planner. A judge worker would catch this; the probe didn't run a judge step.

**Trial 10 worker 2 (DB audit):** Did not complete. Looped on `find /` looking for `psql` that doesn't exist on the VM. Also a worker-quality issue (no environment-availability check before assuming tools exist).

### Do worker-quality issues invalidate the dispatch wins?

**No.** The probe is measuring dispatch behavior, not end-to-end task completion. The dispatch decisions in T5 and T10 were correct (right tool, well-formed argument, self-contained goal). The worker-side problems are downstream and have separate fix paths (better goal-construction examples in HERMES.md, environment-aware workers, judge dispatch). For a "can Gemma orchestrate as planner" question, T5 and T10 are wins.

**They DO matter for end-to-end useability.** A 40% dispatch rate where 50% of dispatched workers fail downstream is a 20% useful-completion rate. That's a meaningful caveat for any "ship Variant D" decision. Path C's value is not just better dispatch — it's pairing dispatch with verification/judge dispatching to catch worker fabrications like T10's invented service names.

---

## 6. Path recommendation

### Path chosen: **Path C — Variant D + runtime enforcement (revival of Variant C wrapper, with fixes).**

I am NOT picking Path A (ship D as-is) because 40% first-attempt dispatch is not sufficient for a production harness, and the failure modes (T4 role-collapse on a clear refactor, T6 degenerate behavior) are predictable enough that targeted enforcement should help.

I am NOT picking Path B (tune D — same architecture, more pressure) because Variant D's HERMES.md is already long enough to plausibly cause Trial 6's degeneration. Adding more directives risks worse, not better, behavior. The existing HERMES.md does the right things; it just doesn't always work.

I am NOT picking Path D (acknowledge ceiling, ship at 40% with operator awareness, await better local model) because the data shows a clear movable lever (the wrapper rescued 1 dispatch in C without scaffolding; D's scaffolding produced 2 first-attempt dispatches without any wrapper). Combining them is the highest-EV move that the data supports. Waiting for stronger local models is a defensible Plan B if Path C also stalls.

### What Path C entails (concrete)

Combine Variant D's HERMES.md and `delegate_worker` tool with a **lightweight runtime wrapper**, fixing the failure modes Variant C exhibited:

1. **Fix the NO_SESSION_ID timeout bug** (10 lines of shell): on `timeout` exit code 124, recover the latest session id via `ls -t /home/parallels/.hermes/sessions/ | head -1`. This alone would have moved 3 wrapper-timeouts in C from "ungated" to "gated and corrected."

2. **Drop the "OR re-classify to one-shot" escape hatch** in the corrective re-prompt. Trial 9 in Variant C exhausted retries because the model kept choosing reclassification over dispatch. The corrective re-prompt should mandate dispatch when class is structured/long-horizon; if Gemma legitimately cannot dispatch (e.g., the task really was misclassified), the wrapper escalates to human, doesn't auto-loosen.

3. **Add a tool-call budget per attempt** (e.g., reject-and-retry if turn exceeds 15 tool calls). This addresses Variant C's runaway-loop timeouts and Variant D's Trial 9 (which used cronjob + 7× terminal + read_file in a single main-session turn instead of dispatching).

4. **Add a pre-action interlock for the 3-tool-call class.** When class is `structured` or `long-horizon`, the wrapper allows up to 2 read-only tool calls (read_file, search_files, ls-style terminal) before requiring `delegate_worker`. After 2 read-only calls without dispatch, the wrapper interrupts with a corrective re-prompt. This addresses Trial 9 specifically: Gemma used 9 tool calls before any potential dispatch decision. Two-call budget for orientation is enough; more than that is role-collapse beginning.

5. **Keep the FABRICATION gate**, finally test it. Variant C never exercised it because the dispatch gate short-circuited. With the dispatch gate getting more passes (under Variant D scaffolding), the FABRICATION gate will start to fire on cases like Variant B Trial 9. Worth confirming.

6. **Fix the parent-session-not-persisted bug** (Hermes runtime side). Trials 5 and 10 in Variant D have missing or truncated parent JSONs because Hermes flushes only on clean exit. Add a SIGTERM handler or per-turn flush. Without this, gate detection on long sessions is unreliable.

### Effort estimate: **Small-Medium (S/M).**

- Wrapper fixes (items 1-4): 1-2 days. The Variant C wrapper exists already; this is targeted patches.
- Pre-action interlock design + implementation (item 4): 0.5-1 day, requires testing.
- Hermes runtime per-turn flush (item 6): 0.5-1 day, simple SIGTERM handler.
- Re-probe with N=10 per variant (10 trials twice = 20 trials): 1 day if mostly automated.
- Total: roughly 3-5 days to a working hybrid + measured outcome.

### Probability of success: **Medium.**

- High probability the NO_SESSION_ID fix and tool-call budget close the wrapper-fragility gaps.
- Medium probability the pre-action interlock pushes T9-class tasks into dispatch (the model might still find ways around — e.g., generate a 3000-token planning prose and call it "no tool calls yet, doesn't need dispatch").
- Medium probability the FABRICATION gate catches T10's worker-side invented-service-names issue (depends on whether the gate looks inside delegated worker output or only at the parent session — needs design call).
- Low probability we exceed 70% first-attempt dispatch on N=10. The 60% role-collapse rate in Variant D suggests a non-trivial fraction of structured tasks will resist any in-prompt scaffolding.

**Realistic outcome target:** 50-60% first-attempt dispatch on N=10, with role-collapse caught and corrected ~half the time by the wrapper, for a final dispatch rate of 70-80%. Worker quality remains a separate problem.

---

## 7. Open questions for future probes

1. **Does the dispatch-rate trajectory hold at N=10 per variant?** N=5 is too thin. Re-running Variants B, C-fixed, and D with 10 trials each — and adding 5 new structured-class tasks to the task set — would firm up the 0→0→20→40% curve into something with usable error bars.

2. **What's the dispatch-rate distribution across task subtypes?** The §5 pattern observation ("dispatches when no quick local action seems applicable; collapses when one does") needs validation. Categorize the 5 structured/long-horizon tasks into "obvious decomposition" (T5, T10 — bug + migration) vs. "tempting quick action" (T4 refactor, T6 build, T9 cron) and check if the dispatch rate splits cleanly. If so, prompt scaffolding should focus on convincing Gemma that "tempting quick actions" are still dispatch candidates.

3. **Does the Trial 6 "degeneration" reproduce, and what is its actual signature?** The artifact says runaway prose loop; the session JSON shows single-shot tool call then silence. Three possibilities: (a) Gemma exceeded a max_tokens budget and was cut off mid-prose (artifact stdout would be ground truth); (b) generation stop token fired prematurely; (c) the tool call returned a result so massive it consumed the rest of the context. Worth a single targeted re-run of Trial 6 with full stdout + token-count logging.

4. **Does swapping the `delegate_worker` schema description shorter improve dispatch rate?** Variant D's schema description is ~80 words. Pure prompt-budget hypothesis: shorter, higher-frequency directives may work better than longer, lower-frequency ones. A Variant D' with a 20-word schema description and the worked example pulled into the system prompt could test this.

5. **Does Qwen3-VL-8B as judge improve worker quality detection?** Specifically on Trial 10's invented service names. A Qwen judge re-reading DB_TOPOLOGY.md against the user's original task should flag "API Gateway / Reporting Engine / Worker Node aren't grounded in user input." This breaks the model-family self-correlation the prior judge raised. Untested in this probe.

---

## 8. Cross-model integrity check verdict

**INTACT. All checks pass.**

| Check | Expected | Actual | Status |
|---|---|---|---|
| Canonical HERMES.md md5 on ubuntu-vm | `0780c232a6cb52e13e432261f0d68ad9` | `0780c232a6cb52e13e432261f0d68ad9` | ✓ MATCH |
| `HERMES-canonical-backup.md` exists | yes | yes (8440 bytes) | ✓ |
| `HERMES-variantB.md` and `HERMES-variantD.md` are sibling files only | sibling, never replacing | sibling files in `/home/parallels/.hermes/hermes-agent/` | ✓ |
| `delegate_worker.py` source file removed from VM | absent | absent in `tools/` directory | ✓ |
| `model_tools.py` reverted to backup | md5 matches `model_tools.py.probe-d-orig` | `7a121831c491c26bc6ebd3b767050f7e` (matches backup) | ✓ |
| `toolsets.py` reverted | matches backup | `e14181ac469be9d22fde85343aa722aa` (matches) | ✓ |
| `run_agent.py` reverted | matches backup | `1ddd6f2a91892db48abdbfd751ec0aac` (matches) | ✓ |
| AgentFW core/references/playbooks/templates files modified | NO | git status shows only untracked new files; zero tracked-file modifications | ✓ |
| `variants/claude-code/`, `variants/claude-projects/`, `variants/generic/` | unchanged | confirmed via git status | ✓ |
| `variants/hermes/HERMES.md` | unchanged | not in modified list | ✓ |

`probe-d-orig` backup files exist for all three patched Hermes source files (`model_tools.py`, `toolsets.py`, `run_agent.py`) and their md5s match the live files exactly — the patches were reverted byte-for-byte. The cross-model integrity guarantee (Opus 4.7 / Sonnet 4.6 / GPT-5-tier all still work) is preserved.

---

## 9. Specific actionable next steps for Path C

If the user accepts Path C, here are the concrete next steps:

### Step 1: Fix the wrapper bugs (1-2 days)

File to modify: `/Users/briantaylor/Projects/AgentFW/probe-variantC-wrapper.sh` (currently exists; this is the Variant C wrapper).

Changes:
- After `timeout 300 hermes chat ... ; rc=$?`, add a fallback: `if [ "$rc" = "124" ]; then session_id=$(ssh ubuntu-vm 'ls -t /home/parallels/.hermes/sessions/ | head -1' | sed 's/session_//;s/.json//'); fi` — exact syntax depends on existing wrapper; the principle is "recover session id from disk after timeout."
- Modify the corrective re-prompt template (probably a heredoc in the wrapper) to remove the "OR re-classify to one-shot" branch. New text should be: "Your last response classified as `structured`/`long-horizon` but did not call `delegate_worker`. You MUST emit a `delegate_worker` tool call with a self-contained `goal` argument now. Do not re-classify; do not continue investigating in this session."
- Add a tool-call counter parsed from session JSON; if `> 15` in a single attempt, force a corrective re-prompt.

### Step 2: Implement the pre-action interlock (0.5-1 day)

Same wrapper, new logic:
- After each Gemma turn, parse the session JSON for `messages[-1].tool_calls`.
- If class was `structured`/`long-horizon` AND total tool-calls-so-far is > 2 read-only-equivalent tools (read_file, search_files, ls-style terminal) AND no `delegate_worker` has fired, send corrective re-prompt: "You have done sufficient orientation. Dispatch a worker now via `delegate_worker`."

This is the move that targets the T9 failure pattern specifically (9 tool calls before any dispatch decision).

### Step 3: Patch Hermes runtime for per-turn session flush (0.5-1 day)

File to modify (on ubuntu-vm): `/home/parallels/.hermes/hermes-agent/run_agent.py`

The current code presumably writes the session JSON only on clean shutdown. Find the session-write path and call it after every assistant turn (not just at exit). Also install a SIGTERM handler that writes the session before dying.

This is required so wrapper-side gates can read the session state reliably even when the CLI is killed by `timeout`.

**Important:** This Hermes patch needs its own `.probe-d-orig` backup — same isolation discipline as Variant D used.

### Step 4: Re-probe with N=10 per variant (1 day)

Add 5 new structured/long-horizon tasks to `probe-tasks.md` (the existing 5 are not enough to stabilize the dispatch-rate metric). Suggestion: split by the §5 pattern observation — 3 "obvious decomposition" tasks (multi-system bugs, multi-phase rollouts) and 2 "tempting quick action" tasks (single-file feature additions, config refactors that touch 2-3 files).

Run all 10 tasks under three configurations:
- D-baseline (Variant D HERMES.md, no wrapper) — re-establish the 40% baseline at N=10.
- D+wrapper (Variant D HERMES.md + the fixed wrapper from Steps 1-2) — measure the lift.
- D+wrapper+pre-action-interlock (the full Path C) — measure the further lift.

Decision criterion for "ship Path C": D+wrapper+interlock achieves ≥60% first-attempt-or-rescued dispatch on N=10 structured/long-horizon trials AND zero tripwire mutations AND fabrication gate fires correctly when artificially induced.

If those criteria are met: ship a "Hermes-r8" addendum that ports Variant D's HERMES.md + the wrapper into production.

If not met: the data has graduated Path D (acknowledge ceiling, await stronger local model) from "defensible Plan B" to "the right call." At that point the probe has done its job — it has shown that Gemma-4-31B has a behavioral ceiling around 40-60% on this task class, and no in-prompt or runtime intervention closes it.

---

## 10. Bottom line

**The Variant D data refutes the prior judge's Path 4 conclusion** ("the prompt-driven Planner-Worker-Judge architecture does not work with Gemma; build a Python driver"). The prior judge was reasoning from N=30 trials with 1 dispatch — that is a real reading of the data available at the time. Variant D added 5 more trials and got 2 dispatches without a Python driver, doubling the dispatch rate of the prior judge's "doesn't work either" Variant C. This is not noise: the dispatches were textbook (correct tool name, correct argument shape, well-formed self-contained goal) and matched the worked example in HERMES.md exactly. The Jira-skill-pattern hypothesis — give Gemma a narrow tool surface with literal worked examples and it will imitate — is supported.

**The user's binding constraint (local-only, Gemma-as-orchestrator, no Python wrapping the agent loop) is preserved by Path C.** The wrapper script is a thin runtime gate around `hermes chat` invocations. It does not replace Gemma's orchestration role; it just enforces the dispatch contract that HERMES.md already declares. Gemma still emits `delegate_worker` tool calls; the wrapper just retries when it doesn't.

**Honest acknowledgment of small-N limitation:** The 40% number is from 5 trials. Could be 20%, could be 60% on the next 5. The recommendation is to invest 3-5 days in building the Path C hybrid + re-probing at N=10 before making the ship call. If the doubled sample firms up the trajectory, ship; if it collapses back to 0/10, retreat to Path D.

**The fabrication risk is lower under Variant D than under Variant B.** Variant D Trial 9 did NOT fabricate completion (unlike Variant B Trial 9). The pattern of "say I'm dispatching, then patch in main session anyway, then claim done" appears to be reduced when the dispatch tool is well-scaffolded and the model's investigation budget runs out before it has the chance to cement a fake completion narrative. This is a side benefit worth noting.

The data says pick Path C. If Path C also fails at N=10, pick Path D (acknowledge the ceiling). Do not pick Path A (ship at 40% — too low) or Path B (more HERMES.md content — risks Trial 6 regression). The 2-3 week Path 4 the prior judge recommended is no longer the right move because Variant D shows in-prompt scaffolding can do meaningful work — fewer engineering weeks, with a clearer test before committing to architecture change.

---

**END OF FINAL VERDICT v2**
