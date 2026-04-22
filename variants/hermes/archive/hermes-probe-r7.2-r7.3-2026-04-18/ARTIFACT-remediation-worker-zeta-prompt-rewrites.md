# ARTIFACT — Worker ζ — Prompt Rewrite Candidates for HERMES-variantD Dispatch Lift

**Scope:** READ-ONLY investigation + design. No files modified. Four concrete rewrite
variants proposed as A/B candidates to lift Gemma-dense first-attempt dispatch rate
above the current ~1/5 baseline on Variant D.

**Source artifacts audited:**
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/HERMES-variantD.md` (211 lines)
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/delegate_worker.py` (79 lines; schema block at lines 20–50)

---

## 1. Current language audit — weak spots

### 1a. HERMES-variantD.md

**Weak spot A — Section ordering.** `HOW TO DISPATCH WORKERS — CRITICAL` sits at lines
109–158, roughly middle of the document. It is followed by Permission Protocol, Session
Protocol, and Core Pattern. Attention-bias on long prompts typically favors the first
~20% and last ~15% of tokens; the dispatch scaffolding currently lives in the attention
trough.

**Weak spot B — Escape hatches multiply.** Dispatch-softening language appears in at
least five places:
- L140–143: `When NOT to use delegate_worker: … Class is one-shot … Quick factual answer
  or orientation read … single tool call — just run it.`
- L153–157: `Role separation can be relaxed ONLY when: … one-shot … trivial … lookups …
  human co-driving.`
- L82: `If you catch yourself doing any of these mid-response, stop and re-classify.`
  — invites post-hoc re-classification to `one-shot` to escape dispatch duty.
- L143: `The task is literally a single tool call (e.g., run one terminal command) —
  just run it.` — Gemma can rationalize "I just need to grep one thing" as single tool
  call, then snowball into an investigation.
- L156: `Quick lookups and orientation reads` — unbounded; orientation can expand.

Each of these individually is reasonable, but together they create a menu of
self-talk escape routes. On a dense 31B model, the path of least resistance is to pick
the hedge that authorizes direct action.

**Weak spot C — "Must" is followed by "unless".** L111 says
`you MUST dispatch work to a subagent … instead of writing code directly`, and L140
immediately softens with `When NOT to use delegate_worker`. The contradiction is
adjacent in token space; the model sees both simultaneously.

**Weak spot D — Worked examples are narrow.** The two `<tool_call>` examples (L119–127)
cover (i) implementation worker for middleware, (ii) verification judge for middleware.
There are no worked examples for:
- Bug-hunt / multi-hypothesis investigation (Trial 5, 9-pathology task)
- Long-horizon planning-only dispatch (Trial 6, 10-step migration)
- Discovery / exploration dispatch (early-session orientation at scale)
- Parallel investigation dispatch (multiple hypotheses in parallel)

Dense models pattern-match to worked examples. Missing shapes means missing behavior.

**Weak spot E — `delegate_task` vs `delegate_worker` confusion leaks through.** L132
and L135 and L138 all spend tokens disambiguating. This is necessary given the wrapper
rationale, but it dilutes the imperative.

### 1b. delegate_worker.py schema (L20–50)

**Weak spot F — Imperative is buried.** The description opens with a mechanism
description: "Spawn ONE worker subagent to complete a task in an isolated, fresh
context. The worker has its own conversation, terminal, and toolset; only the final
summary is returned to you." The `ALWAYS USE THIS TOOL` imperative is in paragraph 2,
line 26–29. Models often attend most strongly to the first sentence of a tool
description.

**Weak spot G — "ALWAYS" is surrounded by qualifying prose.** L26 says
`ALWAYS USE THIS TOOL when the task class is structured or long-horizon.` — but the
very next sentence enumerates forbidden tools, which reads as a list the model can
diff against its intent. If Gemma only "needs to read", it silently excludes itself
from `ALWAYS`.

**Weak spot H — "Do NOT call patch, write_file, terminal, execute_code, or
skill_manage" omits `search_files`.** The observed failure mode is Gemma orienting
with reads before dispatching. Reads are not on the forbidden list. The schema allows
the pathology.

**Weak spot I — No "FIRST tool call" language.** The schema never says
`your FIRST tool call for a structured task must be delegate_worker`. Temporal
ordering is under-specified; the model can satisfy "eventually dispatch" while
front-loading a pile of self-orientation that blows the turn budget and re-classifies
mid-stream.

---

## 2. Variant R1 — Aggressive imperative (schema-level)

**Target:** `delegate_worker.py` lines 22–34, the `description` field.

**Before (current):**
```python
"description": (
    "Spawn ONE worker subagent to complete a task in an isolated, fresh "
    "context. The worker has its own conversation, terminal, and toolset; "
    "only the final summary is returned to you.\n\n"
    "ALWAYS USE THIS TOOL when the task class is `structured` or "
    "`long-horizon`. Do NOT call patch, write_file, terminal, "
    "execute_code, or skill_manage directly from the main session for "
    "such tasks — dispatch to a worker via this tool instead.\n\n"
    "Pass everything the worker needs in the single `goal` argument — "
    "the worker has no memory of your conversation. Include: what to do, "
    "which files matter, what constraints apply, and what 'done' looks "
    "like. Be specific and self-contained."
),
```

**After (R1 proposal):**
```python
"description": (
    "USE THIS TOOL FIRST for ANY task classified as `structured` or "
    "`long-horizon`. If the task class is `structured` or `long-horizon`, "
    "your FIRST tool call MUST be `delegate_worker`. Do not read files, "
    "search, or run terminal commands first — pass any orientation needs "
    "into the worker's `goal` instead.\n\n"
    "This tool spawns ONE worker subagent with a fresh context, its own "
    "terminal, and its own toolset. Only the worker's final summary "
    "returns to you.\n\n"
    "FORBIDDEN from the main session on `structured`/`long-horizon` "
    "tasks: patch, write_file, terminal, execute_code, skill_manage, "
    "read_file, search_files, grep. Dispatch instead.\n\n"
    "Pass everything the worker needs in the single `goal` argument — "
    "the worker has no memory of your conversation. Include: what to do, "
    "which files matter, what constraints apply, and what 'done' looks "
    "like. Be specific and self-contained."
),
```

**Key shifts:**
- Imperative moved to sentence 1.
- "FIRST tool call MUST be" adds temporal ordering.
- Forbidden list extended to include `read_file`, `search_files`, `grep` — closes the
  orientation-leak pathology (Weak spot H).
- Explicit instruction: "pass orientation needs into the worker's goal" gives the
  model the alternative behavior to substitute.

---

## 3. Variant R2 — Remove escape hatch

**Target A:** `HERMES-variantD.md` L82.

Before:
```
If you catch yourself doing any of these mid-response, stop and re-classify.
```

After:
```
If you catch yourself doing any of these mid-response, stop. Do not re-classify
downward to avoid dispatch — a task that has entered execution as `structured`
stays `structured`. Dispatch the remaining work to a worker.
```

**Target B:** `HERMES-variantD.md` L153–157.

Before:
```
**Role separation can be relaxed ONLY when:**
- Class is `one-shot` (by definition below the threshold)
- Trivial changes with purely mechanical verification
- Quick lookups and orientation reads
- The human is actively co-driving as judge
```

After:
```
**Role separation can be relaxed ONLY when class is `one-shot`.** Orientation
reads, "trivial" changes, and "quick lookups" are NOT exceptions — if the task
required a `structured` classification, it requires dispatch. The only path out
of dispatch is a legitimate `one-shot` classification at the session start, not
a mid-task re-evaluation.
```

**Target C:** `HERMES-variantD.md` L140–145.

Before:
```
**When NOT to use `delegate_worker`:**
- Class is `one-shot` (handle directly, no dispatch).
- Quick factual answer or orientation read.
- The task is literally a single tool call (e.g., run one terminal command) — just run it.
```

After:
```
**When NOT to use `delegate_worker`:**
- Class is `one-shot` — and ONLY when class is `one-shot`. The class gate is the
  single arbiter of whether dispatch is required.
```

**Target D:** Wrapper correction message (if the runtime wrapper emits a correction
nudge when it detects a non-dispatch first action on `structured` class — this file
was not read in scope, but the variant assumes one exists). Strip any language of the
form "if you believe dispatch is unnecessary, re-classify to one-shot" and replace
with "this task is classified `structured`; your next tool call must be
`delegate_worker`."

**Key shift:** Remove the self-reclassification escape route. Force the binary:
dispatch, or block.

---

## 4. Variant R3 — More worked examples

**Target:** `HERMES-variantD.md`, insert after L127 (existing verification judge
example) and before L129 ("Rules:").

**New content to insert:**

```
Example — bug-hunt with multiple hypotheses:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "Investigate why the /api/orders endpoint returns 500 intermittently under load. Enumerate hypotheses before testing any one of them. At minimum consider: (1) DB connection-pool exhaustion, (2) race condition in the order-ID generator, (3) timeout on the downstream inventory service, (4) memory pressure from a recent deploy. For each hypothesis, state what evidence would confirm or refute it, then gather that evidence (logs, metrics, code inspection). Do NOT commit to a root cause until all hypotheses have been evaluated. Files of interest: src/api/orders.js, src/db/pool.js, src/services/inventory.js, and any recent commits in the last 14 days. Report back with: ranked hypotheses, evidence gathered per hypothesis, and recommended next diagnostic step. Do NOT apply a fix."}}
</tool_call>

Example — long-horizon plan (plan only, no execution):

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "Produce a phased migration plan for moving the user-auth module from session cookies to JWT. Output a PLAN.md with: (1) phases with explicit entry/exit criteria, (2) files touched per phase, (3) rollback procedure per phase, (4) verification strategy per phase (what tests, what manual checks), (5) ordering constraints between phases. Do NOT write any implementation code. Do NOT modify any source files outside PLAN.md. Read: src/auth/, src/middleware/session.js, and tests/auth/. Return the PLAN.md contents and a one-paragraph summary of the critical path."}}
</tool_call>

Example — discovery / exploration dispatch:

<tool_call>
{"name": "delegate_worker", "arguments": {"goal": "Map the payment-processing subsystem. Produce a SYSTEM_MAP.md covering: (1) entry points (where external requests land), (2) internal call graph (which module calls which), (3) external dependencies (third-party APIs, DBs, queues), (4) error-handling boundaries, (5) test coverage per module. Search under src/payments/, src/billing/, and any adjacent modules referenced from those. Do NOT modify code. Return SYSTEM_MAP.md contents plus a flagged list of suspicious or undertested areas."}}
</tool_call>
```

**Rationale:** Dense models pattern-match to worked examples. Adding three canonical
shapes — multi-hypothesis bug-hunt, plan-only long-horizon, discovery — gives Gemma
the templates it currently lacks for Trials 5, 6, 9, and 10. Each example is
self-contained and uses the same `<tool_call>` format it already emits correctly when
it chooses to dispatch.

---

## 5. Variant R4 — Reorder sections

**Target:** `HERMES-variantD.md` — structural reordering only; text bodies unchanged.

**Current order (lines):**
1. First-Line Output Contract (L7–28)
2. Why this matters (L31–37)
3. Classification criteria (L39–69)
4. Classification pressure — named failure modes (L73–82)
5. Planner-Worker-Judge Architecture (L86–105)
6. **HOW TO DISPATCH WORKERS — CRITICAL (L109–158)**
7. Permission Protocol (L161–173)
8. Session Protocol (L177–198)
9. Core Pattern (L202–211)

**Proposed R4 order:**
1. First-Line Output Contract (unchanged, stays first — it is the hard contract)
2. Why this matters
3. Classification criteria
4. Classification pressure — named failure modes
5. Planner-Worker-Judge Architecture
6. Permission Protocol
7. Session Protocol
8. Core Pattern
9. **HOW TO DISPATCH WORKERS — CRITICAL** (moved from middle to last)

**Rationale:** Long-context attention on decoder-only transformers biases toward
first and last segments of the prompt. The classification marker contract already owns
the first position (correctly — marker emission is the gating behavior we want
strongest). Moving the dispatch scaffolding to the last position gives it the
secondary attention peak. Permission Protocol, Session Protocol, and Core Pattern are
policy/background that can live in the attention trough without hurting behavior —
they don't need per-token salience the way the dispatch rules do.

**Speculative caveat:** Attention-geometry arguments are model-family-dependent.
Gemma-4-31B's RoPE-scaled positional encoding may or may not exhibit the same
end-bias as Claude/GPT families. R4 is the highest-uncertainty variant; it should be
tested but is lower-priority than R1–R3 on expected value.

---

## 6. Risk/value scoring

| Variant | Expected lift | Lift reasoning | Regression risk | Reversibility | Measurement cost |
|---------|---------------|----------------|-----------------|---------------|------------------|
| **R1 — Aggressive imperative (schema)** | **High** | Schema description is read at every tool-binding; imperative in sentence 1 + explicit "FIRST tool call" + extended forbidden list directly targets the observed pathology (orienting-before-dispatching). | **Low-Medium.** Could over-dispatch on `one-shot` tasks if the model gets "FIRST tool call" stuck and forgets the class gate. Mitigated: imperative is conditioned on `structured`/`long-horizon`. | Full. Text edit in `delegate_worker.py`. Revert = git checkout. | 15 trials (T4+T5+T9, N=5) ≈ 1 hour. |
| **R2 — Remove escape hatch** | **Medium-High** | Closes the self-reclassification route which is the suspected Gemma rationalization path. But removing hedges may cause the model to dispatch in marginal cases where `one-shot` is correct. | **Medium.** Potential regression on one-shot classification precision. The hedges also protect against over-dispatch; removing them tightens the dispatch funnel in both directions. | Full. Text edits in HERMES-variantD.md (and possibly wrapper correction message). | 15 trials (T4+T5+T9) + 5 one-shot-sanity trials (T1 or T2) ≈ 1.3 hours. |
| **R3 — More worked examples** | **Medium** | Pattern-matching lift on missing shapes (bug-hunt, long-horizon plan, discovery). Addresses Trials 5, 6, 9, 10 specifically. Does not change the imperative strength — a model that wasn't dispatching at all won't start because of more examples, but a model that's already borderline will get unambiguous templates. | **Low.** Additive content; doesn't remove or weaken any existing rule. Only risk is prompt-length inflation pushing other content further into the trough. | Full. Text insert in HERMES-variantD.md. | 15 trials (T4+T5+T9) ≈ 1 hour. Bonus: specifically re-run Trials 5, 6, 9, 10 since those are what R3 directly targets. |
| **R4 — Reorder sections** | **Low-Medium** | Attention-bias argument is plausible but model-family-dependent for Gemma. Biggest wins from reordering are usually marginal (~5–15%) vs content changes (~20–50%). | **Low.** No text changed; only section order. Worst case: slight regression on Session Protocol adherence if that content needs salience. | Full. Pure reordering in HERMES-variantD.md. | 15 trials (T4+T5+T9) ≈ 1 hour. |

---

## 7. First-test recommendation

**Recommend R1 — Aggressive imperative (schema-level).**

**Why first:**

1. **Highest expected lift.** The observed pathology is Gemma doing orientation reads
   before dispatching. R1 directly forbids that pattern in the schema description —
   the exact surface the model attends to when deciding whether to call the tool.
   R2/R3/R4 operate on HERMES.md which is system-prompt-level and may be partially
   attention-starved on long inputs; the schema description is always freshly
   attended at tool-selection time.

2. **Lowest cost.** Single-file edit (`delegate_worker.py`, L22–34 only). No changes
   to HERMES-variantD.md. Measurement is the standard 15-trial run.

3. **Lowest regression risk on non-dispatch metrics.** R1 is conditioned explicitly
   on `structured` or `long-horizon` class. It does not touch the classification
   gate, marker emission, or justification language. One-shot behavior should be
   untouched.

4. **Cleanest signal.** Because R1 changes only the schema, any lift observed is
   attributable to the schema rewrite — not confounded by prompt restructuring.
   This gives the highest-information-per-trial result.

**How to stage:**

1. Copy `delegate_worker.py` to `delegate_worker.py.bak-r1`.
2. Apply the R1 diff to `delegate_worker.py` (section 2 above).
3. No changes to `HERMES-variantD.md`.
4. Restart the Hermes runtime so the new schema is loaded into the tool registry.
5. Run dense-Gemma trials: Task 4 (refactor), Task 5 (bug-hunt / 9-pathology),
   Task 9 (multi-file investigation). N=5 each, 15 total.
6. Metrics to capture per trial:
   - First-attempt dispatch: did the first tool call after marker emission =
     `delegate_worker`? (primary)
   - Marker emission: `[TASK CLASS: ...]` on line 1? (regression check)
   - Classification correctness: did the class match human judgment? (regression check)
   - Turn budget: how many turns until dispatch? (secondary — R1 targets first-turn)
7. Compare to baseline (current Variant D, ~1/5 first-attempt).
8. Decision rule: if R1 lifts to ≥3/5 without regressing marker emission or
   classification precision, promote R1 and layer R3 on top. If R1 lifts to 2/5
   or shows regression, revert and test R2 solo next.

**Sequencing for subsequent rounds (if R1 succeeds):**
- Round 2: R1 + R3 (layer worked examples on top).
- Round 3: R1 + R3 + R2 (tighten escape hatches once dispatch is reliable).
- R4 tested last, independently, as an attention-geometry probe.

**Sequencing if R1 fails:**
- Round 2: R2 solo (escape-hatch removal without the aggressive schema).
- If that also fails, the problem is not prompt-level and the remediation shifts
  to runtime enforcement (wrapper that blocks non-dispatch first actions on
  `structured` class).

---

## Appendix — Out-of-scope observations

Not addressed by R1–R4, but worth flagging for the operator:

- **Runtime wrapper enforcement.** If prompt-level variants plateau below target,
  the next tier is a runtime wrapper in `delegate_worker.py` or its call site that
  intercepts non-dispatch tool calls when class is `structured`/`long-horizon` and
  returns a correction message. This is structural, not textual, and should sit
  downstream of the prompt-rewrite A/B.

- **Class gate hoisting.** The marker is emitted as text, not as a structured field.
  A future variant could require the class to be emitted as the first tool call
  (`emit_classification` tool) so the runtime has a machine-readable handle to gate
  subsequent tool calls on. Larger change; out of scope for R1–R4.

- **Batch-mode worked example.** L145 mentions sequential `delegate_worker` calls
  for multiple independent workers, but there is no worked example. If Trial data
  shows Gemma bunching independent work into one `goal` (over-stuffed worker), add
  a batch-dispatch example in a future round.

**End of artifact.**
