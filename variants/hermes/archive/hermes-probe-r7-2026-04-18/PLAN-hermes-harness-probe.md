# PLAN: Hermes Harness Execution Probe

**Created:** 2026-04-17
**Classification:** structured
**Mode:** guided (user executes, reports back)
**Budget:** ~2-4 hours of evaluator time; ~30 min of Gemma inference; no code changes to Hermes until results land.

## Goal

Measure whether Gemma-4-31B, running as the Hermes primary model with HERMES.md loaded, can actually execute the AgentFW harness — not just describe it. The answer determines whether the "local-only harness" path (coercive runtime gates + subprocess workers) is viable or whether we need to fall back to constrained decoding.

## Decision the probe supports

Three possible outcomes drive three different downstream plans:

| Marker emission rate | Classification correctness | Recommended path |
|----------------------|----------------------------|------------------|
| ≥70% under strict framing (variant B) | ≥80% on clear tasks | **Path 1: Soft-gate harness.** Runtime retry loop + HERMES.md tightening. Ship r6-hermes addendum mostly as-is. |
| 30-70% under strict framing | Any | **Path 2: Coercive runtime.** Hermes runtime intercepts non-conforming responses, auto-retries, blocks non-dispatching turns on structured tasks. r6-hermes H3/H4 redesigned around runtime enforcement. |
| <30% under strict framing | Any | **Path 3: Constrained decoding.** Grammar-forced output (GBNF/outlines) makes marker emission structurally unavoidable. Larger engineering cost; r6-hermes significantly re-scoped. |

All three preserve AgentFW's cross-model integrity (the claude-code / claude-projects / generic variants are untouched). Only HERMES.md and the Hermes runtime change.

## Metrics (what we measure)

For each trial, score binary or categorical:

1. **Marker emission** (binary) — Did response open with `[TASK CLASS: …]`? Regex: `^\[TASK CLASS: (one-shot|structured|long-horizon)\]` within first 20 lines.
2. **Classification correctness** (3-way) — Was the chosen class right? Graded against the task's ground-truth label (assigned when authoring the task set).
3. **Delegation behavior** (categorical: dispatched / role-collapsed / refused) — For tasks labeled `structured`, did the response (a) call `delegate_task`, (b) start implementing in main session, or (c) refuse/ask clarification?
4. **Justification quality** (2-way: real / rubber-stamp) — Does the `Justification:` line cite concrete task features, or is it generic filler ("complex task, needs harness")? Human-judged, short rubric.
5. **Role-separation violation count** — How many tool calls in the same turn wrote code after a `structured` classification without dispatching? Grep on session log.

Primary metric: **marker emission rate × classification correctness** (compound). Secondary: delegation rate on `structured` tasks.

## Task set (N=10)

Ten tasks spanning three categories. Small enough to run quickly; large enough that variance signals rather than noise dominates. Each has a ground-truth class label and a one-line "trap" noting the common misclassification to watch for.

| # | Task | Ground truth | Trap |
|---|------|--------------|------|
| 1 | "What's the capital of France?" | one-shot | — (baseline sanity) |
| 2 | "Rename the variable `foo` to `bar` in `scratch.py` (one occurrence)." | one-shot | Could be over-classified as structured |
| 3 | "Add a null check on line 47 of `auth.py` — if `user` is None, return early." | one-shot | Borderline; acceptable as structured if reasoning is real |
| 4 | "Refactor the auth module to use the new session store. Three files touched; tests must still pass." | structured | Pull to one-shot because "refactor" feels mechanical |
| 5 | "Find and fix the bug where the dashboard shows stale data after a save. Intermittent." | structured | Pull to one-shot; multiple hypotheses exist but surface looks like "one bug" |
| 6 | "Build a new export feature: CSV/JSON/PDF formats, with permissions, tests, and docs." | long-horizon (or structured, acceptable) | Pull to structured-without-plan |
| 7 | "Summarize this meeting transcript." (paste 2K tokens) | one-shot | Auxiliary-model routing — should not trigger harness |
| 8 | "Write a throwaway script to count files larger than 10MB in `~/Downloads`." | one-shot | Over-classified as structured |
| 9 | "Investigate why the Jira daily briefing cron is silently failing some days." | structured (bug-hunting) | Pull to one-shot; requires DIAGNOSTIC.md |
| 10 | "Migrate our Postgres 12 database to Postgres 16, zero downtime." | long-horizon | Pull to structured; spans sessions, real risk |

Authoring ground truth: Brian assigns labels up-front. Disagreements with the probe are the probe's wrong, not the task's.

## Variants (framing strengths tested)

**Variant A — Baseline.** Current HERMES.md. No changes. Establishes the floor.

**Variant B — Hard output contract.** HERMES.md patched with Sonnet-4.6-style literal framing:
```
Your FIRST line of every response to a new task must be exactly:
[TASK CLASS: <one-shot|structured|long-horizon>]
Justification: <one concrete sentence citing a specific feature of the task>

If you begin any other way, the harness will reject your response.
```
Plus: remove hedging language ("should," "try to") from rule-bearing sections. Audit for softeners.

**Variant C — Runtime-enforced retry.** Variant B's HERMES.md + Hermes runtime interceptor: if first line of Gemma's response doesn't match the marker regex, reject the response and re-prompt with `Your response did not begin with [TASK CLASS: …]. Emit it now, then continue.` Max 3 retries; then surface a hard failure. No code yet — just a mock in the probe harness (e.g., a shell script that detects missing markers and re-queries).

**Variant D — Constrained decoding** (ONLY if A+B+C yield <30%). Grammar-forced first-token sequence using llama.cpp GBNF or outlines. Ensures the marker is structurally the first thing emitted. Tested on 3 tasks only; larger lift.

Run A, B, C in sequence. Gate to D based on B+C results.

## Experimental design

- **Trials per variant:** 10 tasks × 1 run = 10 trials per variant (A, B, C). Total: 30 trials. Variant D gated.
- **Fresh context per trial.** Each task is a NEW Hermes session. No accumulation. (This isolates marker emission from long-context degradation — a separate probe.)
- **Fixed temperature.** Whatever Hermes currently uses in production. Document the value in results.
- **No chain-of-thought coaxing.** Present only the user task; do not add "remember to classify" reminders. The probe is measuring what happens when HERMES.md is the only instruction.
- **Blind-ish scoring.** Brian scores marker emission and classification correctness from the raw jsonl logs, not from live observation, to reduce confirmation bias.

## Instrumentation

Worker C identified these evidence sources:

- **Session logs:** `~/.hermes/` (exact path to be confirmed when you run the probe — check `~/.hermes/sessions/` and `~/.hermes/logs/agent.log`). Sessions are jsonl; turns are parseable.
- **Model API calls:** Logged per-turn including model name, latency, token counts. Useful for confirming which model served each turn (expect Gemma for primary, Qwen for compression/aux).
- **Tool calls:** `delegate_task` invocations are visible in the jsonl as structured tool-use blocks. Grep pattern: `"tool_name":"delegate_task"`.

Scoring script (to be written after the probe design is approved):
```
# Pseudocode
for each session.jsonl in probe run:
    first_assistant_line = first non-empty content in first assistant turn
    marker_emitted = regex_match(r'^\[TASK CLASS: (one-shot|structured|long-horizon)\]', first_assistant_line)
    class_chosen = extracted class from marker
    delegate_calls = count of tool_name==delegate_task in session
    tool_calls_writing_code = count of Write/Edit-equivalent tools in main session
    record (task_id, variant, marker_emitted, class_chosen, delegate_calls, write_calls)
```

## Execution order

1. **Build the task set doc** — `probe-tasks.md` with the 10 tasks + ground-truth labels. Brian authors; I can draft.
2. **Variant A run** — 10 fresh sessions against current HERMES.md. Collect jsonl. Score.
3. **Checkpoint:** if Variant A unexpectedly shows ≥50% marker emission, pause and re-examine — Worker C's zero-emission observation may have been context-specific.
4. **Variant B patch** — draft revised HERMES.md section with hard output contract. Save as `HERMES-variantB.md`; swap in for the probe (do not overwrite production HERMES.md yet).
5. **Variant B run** — 10 fresh sessions. Score.
6. **Variant C mock** — wrapper script that intercepts responses missing marker, re-prompts up to 3x. Run 10 sessions through the wrapper. Score.
7. **Gate check** — if Variant C ≥70%, stop and write up recommendations. If <30%, plan Variant D.
8. **Optional Variant D** — constrained-decoding run on 3 tasks. Engineering cost: ~half a day to wire GBNF through the MLX server or swap to a llama.cpp path for this test.

## Pass/fail thresholds (pre-committed)

Pre-commit to thresholds BEFORE running so outcome doesn't get rationalized post-hoc:

- **A ≥50%:** surprise; investigate why live observation showed 0%. Probably something about how Worker C's session sample was selected.
- **B ≥70% AND classification correctness ≥80%:** Path 1 viable. Ship r6-hermes addendum mostly as-is with Variant B's HERMES.md framing.
- **B 30-70%:** Variant C required; Path 2 is the target.
- **C ≥70%:** Path 2 viable. r6-hermes H3/H4 redesigned around runtime interceptors.
- **C <30%:** Path 3; plan Variant D and accept larger engineering cost.
- **B or C <20% on clearly-labeled one-shot tasks:** Gemma is classifying everything as structured — inverse failure. Means the framing over-triggers; loosen Variant B, don't tighten further.

## Isolation rule (non-negotiable)

The probe MUST NOT modify or risk regressing any AgentFW functionality outside the Hermes variant. Goal is to vet whether a **modified version** works with Hermes, not to mutate the shared framework.

**Mutable during the probe:**
- New files anywhere named `PLAN-*`, `ARTIFACT-*`, `probe-*` (scratch workspace; never product)
- `variants/hermes/HERMES-variantB.md` (new sibling file, not a replacement)
- `variants/hermes/HERMES-variantC-wrapper.py` (new, probe-local wrapper; not invoked by production Hermes)
- Anything under a new `probe/` directory if one is created

**Immutable during the probe:**
- `core/harness-core.md` and everything under `core/`
- All files under `references/`, `playbooks/`, `templates/`
- `variants/claude-code/CLAUDE.md`, `variants/claude-projects/custom-instructions.md`, `variants/generic/system-prompt.md`
- `variants/hermes/HERMES.md` itself (production version stays until a path is picked AND golden tasks re-pass)
- `evaluation/golden-tasks.md`, `eval-protocol.md`
- Everything in `PLAN-r6.md`, `PLAN-r7.md`, existing `ARTIFACT-*` files from prior runs

**Regression gate before any `variants/hermes/HERMES.md` change lands:**
1. Run existing golden tasks (GT-1 through GT-5) against the `claude-code` variant. All must pass at r7-baseline level (`evaluation/results-*-2026-04-17.md`). No regression.
2. If GT-6-hermes / GT-7-hermes (defined in `PLAN-r6-hermes-addendum.md` §H13) are implemented, run those too.
3. Diff the Hermes variant against `core/harness-core.md` and confirm only allowed divergences remain (per r6 addendum §H12).

The cross-model integrity guarantee (Opus 4.7 / Sonnet 4.6 / GPT-5-tier all still work) is the binding constraint. Any probe finding that would require touching `core/` is a STOP — escalate to Brian, do not commit.

## Out of scope for this probe

- Measuring marker persistence over long context (>5 turns). Separate probe.
- Measuring `delegate_task` return handling (worker artifact parsing, judge dispatch). Gated on markers working first.
- Measuring Qwen3-VL-8B as judge. Gated on delegation working first.
- Modifying production HERMES.md. Probe uses `HERMES-variantB.md`; production stays on current HERMES.md until results land AND regression gate passes.
- Modifying anything in `core/`, `references/`, `playbooks/`, `templates/`, or non-Hermes variants. If the probe reveals a need to, STOP and escalate.

## Deliverable

`ARTIFACT-probe-hermes-harness-results.md` with:
- Raw counts per variant per metric
- Pre-committed threshold comparison
- Selected path (1, 2, or 3) with reasoning
- Recommended next plan (r6-hermes path-specific, OR constrained-decoding spike)

## Resolved blockers (2026-04-17, see ARTIFACT-probe-blockers-resolved.md)

1. **Session logs:** `/home/parallels/.hermes/sessions/` on ubuntu-vm. Files named `YYYYMMDD_HHMMSS_<hex>.jsonl` (6-hex CLI, 8-hex gateway). No auto-rotate.
2. **HERMES.md drift: none.** md5 `0780c232a6cb52e13e432261f0d68ad9` matches canonical `variants/hermes/HERMES.md` byte-for-byte. The canonical is the live.
3. **Sampling:** Hermes sends NO temperature/top_p/top_k on Gemma turns — server defaults only. `run_agent.py:5367-5385` deliberately omits them. **Probe must record oMLX server's temp setting before run 1** (ssh to the macOS host at 10.211.55.2 or query the MLX server config).
4. **Fresh session:** `cd ~/.hermes/hermes-agent && ./venv/bin/hermes chat -Q -q "<prompt>" --source probe-r7-run<i>`. CLI generates a new `session_id` per invocation. 30 sequential calls are independent. No gateway restart.
5. **SOUL.md inclusion: LEAVE IN.** (Decision 2026-04-17, Brian.) SOUL.md (~2.4KB identity prompt) is part of production runtime config and will always be injected. Probe measures production-realistic behavior, not AgentFW-in-isolation.

## Baseline null-test caveat (important)

The current canonical HERMES.md (md5 above) does NOT contain a classification gate, Critical Rules preamble, or `[TASK CLASS]` directive. Those arrived in AgentFW core at r5/r6 but have not been ported into the Hermes variant. The r6 Hermes addendum plans to port them; that port is exactly what Variant B will test.

**Implication:** Variant A (baseline) is expected to yield ~0% marker emission — because the instruction to emit the marker is not present in the prompt. Variant A serves as a control, not as a test of "can Gemma follow AgentFW." The real test starts at Variant B.

If Variant A yields non-zero emission, that's a signal Gemma is emitting markers from prior training exposure to AgentFW-style patterns (possible since HERMES.md is in public releases), not from current instruction.

## Task states

- [ ] Probe plan reviewed by Brian
- [ ] Task set doc drafted (`probe-tasks.md`)
- [ ] Variant A run
- [ ] Variant A scored
- [ ] Variant B HERMES.md patch drafted
- [ ] Variant B run
- [ ] Variant B scored
- [ ] Variant C wrapper script
- [ ] Variant C run
- [ ] Variant C scored
- [ ] Results artifact written
- [ ] Path decision committed
