# ARTIFACT — IMPL-3: β-fuse Architectural Spec (Layer 3)

Worker: IMPL-3 (READ-ONLY, SPEC ONLY). Designs the β-fuse architectural change that
fuses task classification into the dispatch tool surface, making "marker without
dispatch" representationally impossible.

**Status:** Design only. Deploy only IF Layers 1+2 fall short of targets
(dense first-attempt ≥7/15, MoE first-attempt ≥4/15). See §7.

**Source motivation:** Worker β's first-turn-divergence finding
(`ARTIFACT-remediation-worker-beta-first-turn.md`):
> MoE first-turn no-tool-call counts: 3/5 (Tasks 4, 6, 10). MoE literally
> terminates generation after the justification sentence with no tool call.
> This is a structural MoE behavior, not a tool-selection mistake.

The marker-and-dispatch are decoupled today: a model can satisfy
`[TASK CLASS: structured]` and stop in chatbot mode. β-fuse removes that seam.

---

## 1. Schema design — `delegate_worker_v2`

Renamed for clarity (the v2 name signals "use this, not the old one"). The
schema lifts the imperative to sentence 1 (per worker ζ's R1 finding: sentence 1
is the highest-attention slot). Required arguments make classification a
structural commitment, not a stylistic prefix.

```python
DELEGATE_WORKER_V2_SCHEMA = {
    "name": "delegate_worker_v2",
    "description": (
        # Sentence 1 — the imperative. Highest-attention slot.
        "Call this tool as your FIRST action on every task — including one-shots. "
        # Sentence 2 — what it does + why it's required.
        "It records your task classification (one-shot, structured, or "
        "long-horizon) and, for structured/long-horizon tasks, spawns a worker "
        "subagent in an isolated context. "
        # Sentence 3 — the anti-pattern this prevents.
        "There is no other way to satisfy the AgentFW classification contract; "
        "writing `[TASK CLASS: ...]` in prose without calling this tool is a "
        "protocol violation.\n\n"
        # Behavior block.
        "Behavior by classification:\n"
        "  * one-shot: returns immediately with an acknowledgement. You then "
        "    answer in the main session. Use this ONLY when zero files will be "
        "    modified, OR exactly one file under 20 lines with no cross-file "
        "    dependencies.\n"
        "  * structured / long-horizon: spawns a worker via delegate_task. "
        "    `goal` is REQUIRED and must be self-contained (worker has no "
        "    memory of your conversation). Do NOT call patch, write_file, "
        "    terminal, execute_code, or skill_manage in the main session for "
        "    these classes — dispatch.\n\n"
        "When in doubt between one-shot and structured, choose structured."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "classification": {
                "type": "string",
                "enum": ["one-shot", "structured", "long-horizon"],
                "description": (
                    "Task class. one-shot = zero or one trivial file change. "
                    "structured = multi-file, multi-component, or has "
                    "side-effects worth tracking. long-horizon = spans "
                    "multiple sessions or requires accumulated state."
                ),
            },
            "justification": {
                "type": "string",
                "minLength": 30,
                "description": (
                    "Concrete reason this task falls in the chosen class. "
                    "Reference the specific properties of THIS task (files "
                    "involved, side-effect surface, verification needs) — not "
                    "generic boilerplate. Minimum 30 characters."
                ),
            },
            "goal": {
                "type": "string",
                "description": (
                    "REQUIRED for structured and long-horizon. Self-contained "
                    "worker spawn instruction: what to do, which file paths "
                    "matter, what constraints apply, what 'done' looks like. "
                    "Worker knows nothing about your conversation. "
                    "OPTIONAL for one-shot (ignored if provided)."
                ),
            },
        },
        "required": ["classification", "justification"],
    },
}
```

Notes:

- `minLength: 30` on `justification` is enforced server-side (handler raises
  `InputValidationError` if shorter). Cheap structural defense against
  one-word justifications like "complex".
- `goal` is conditionally required by the handler, not by JSONSchema (the JSON
  Schema `if/then` keyword is unreliable across providers; do it in the handler).
- The schema description deliberately repeats "FIRST action" and "no other way"
  — the redundancy is the point. β-fuse's value comes from the model treating
  this tool call as the entry point, not the marker text.

---

## 2. Handler logic

```python
def delegate_worker_v2(classification, justification, goal=None,
                       parent_agent=None):
    # Argument validation
    if classification not in ("one-shot", "structured", "long-horizon"):
        return {"error": f"invalid classification: {classification!r}"}
    if not isinstance(justification, str) or len(justification) < 30:
        return {"error": "justification must be a string of at least 30 chars"}

    # One-shot: acknowledge and return. The classification + justification are
    # captured in the tool_call args (visible to the gate-checker). No child
    # spawn. The model continues in the main session.
    if classification == "one-shot":
        return {
            "ok": True,
            "classified": "one-shot",
            "message": (
                "Classified as one-shot. Proceed in the main session. "
                "Remember: if you find yourself touching more than one file or "
                "more than ~20 lines, stop and re-call delegate_worker_v2 with "
                "classification='structured'."
            ),
        }

    # Structured / long-horizon: goal is required.
    if not goal or not isinstance(goal, str):
        return {
            "error": (
                "goal is required for classification "
                f"{classification!r}. Provide a self-contained worker spawn "
                "instruction (what to do, file paths, constraints, success "
                "criteria)."
            )
        }

    # Spawn child via delegate_task internals (same path as legacy
    # delegate_worker).
    return delegate_task(
        goal=goal,
        context=None,
        toolsets=None,
        tasks=None,
        max_iterations=None,
        acp_command=None,
        acp_args=None,
        parent_agent=parent_agent,
    )
```

The handler is intentionally thin. All policy lives in the schema description
(model-facing) and the gate-checker (audit). The handler enforces only
argument shape.

---

## 3. check.py changes (`probe-variantE-check.py` → `probe-variantF-check.py`)

The dispatch gate is reformulated around delegate_worker_v2 as the ground-truth
classification signal. Backwards-compat: legacy `delegate_worker` and
`delegate_task` still satisfy the dispatch gate, with a recorded provenance flag.

### Conceptual diff

```python
# New constants
DELEGATE_WORKER_V2 = "delegate_worker_v2"
LEGACY_DISPATCH_TOOLS = frozenset(["delegate_worker", "delegate_task"])
ALL_DISPATCH_TOOLS = LEGACY_DISPATCH_TOOLS | {DELEGATE_WORKER_V2}

# New gate: classification source is the v2 tool_call args, not text marker
def extract_classification(messages):
    """
    Return (cls, source) where source in ('v2_tool', 'text_marker', None).
    v2_tool is preferred; text_marker is fallback for legacy sessions.
    """
    for m in messages:
        if m.get("role") != "assistant":
            continue
        for tc in (m.get("tool_calls") or []):
            fn = tc.get("function") or {}
            if fn.get("name") == DELEGATE_WORKER_V2:
                args = json.loads(fn.get("arguments") or "{}")
                cls = args.get("classification")
                if cls in ("one-shot", "structured", "long-horizon"):
                    return cls, "v2_tool"
        # Fallback: text marker on first assistant message only
        if m == first_assistant(messages):
            line = extract_first_line(m.get("content") or "")
            mt = MARKER_REGEX.match(line)
            if mt:
                return mt.group(1), "text_marker"
    return None, None
```

### New gate flow

```
1. cls, source = extract_classification(messages)
2. if cls is None: VIOLATION:NO_MARKER  (also fires if v2 was never called
   AND no text marker present)
3. if cls == "one-shot": COMPLIANT (subject to fabrication check)
4. if cls in ("structured", "long-horizon"):
     dispatch_idx = first index where tool name in ALL_DISPATCH_TOOLS
     if source == "v2_tool":
         # The v2 call IS the dispatch (it spawned the child).
         dispatch_idx is guaranteed >= 0 here.
     else:  # source == "text_marker" (legacy session)
         if dispatch_idx is None: VIOLATION:NO_DISPATCH:<cls>
     mutations_before = mutator tools called BEFORE dispatch_idx
     if mutations_before non-empty: VIOLATION:ROLE_COLLAPSE:<cls>
5. fabrication check unchanged
6. else: COMPLIANT
```

### Diagnostic additions

```python
diag["classification_source"] = source  # "v2_tool" | "text_marker" | None
diag["v2_call_count"] = sum(1 for c in calls if c == DELEGATE_WORKER_V2)
diag["v2_was_first_tool"] = (calls and calls[0] == DELEGATE_WORKER_V2)
```

`v2_was_first_tool` is the headline metric for adoption: under β-fuse, this
should be ≥95% on compliant runs.

### What does NOT change

- ROLE_COLLAPSE definition (mutator tool before dispatch). Still applies.
- FABRICATION check (last 3 tool errors + completion claim). Untouched.
- NO_ASSISTANT_RESPONSE. Untouched.

### Probe re-validation requirement

The check.py rewrite invalidates prior probe baselines. Before deploying β-fuse
to production HERMES.md, re-run the 15-task r7.3 probe matrix against
`probe-variantF-check.py` with both models. Require: dense ≥10/15 first-attempt,
MoE ≥6/15 first-attempt (above current Layer-1+2 ceiling).

---

## 4. HERMES.md changes (sketch)

Replace the current Critical-Rules-#1 wording and the Classification Gate
section. Diff sketch (additions in `+`, removals in `-`):

```diff
 ## CRITICAL RULES — These override all other guidance

-1. **CLASSIFY BEFORE ACTING.** Output `[TASK CLASS: one-shot | structured |
-   long-horizon]` before any work. No exceptions. No silent skipping.
+1. **CLASSIFY BEFORE ACTING.** Your FIRST action on every task — including
+   one-shots — MUST be a `delegate_worker_v2` tool call with `classification`
+   and `justification`. Prose markers like `[TASK CLASS: ...]` are NOT a
+   substitute. The tool call IS the classification.
 2. **DO NOT COLLAPSE ROLES.** ...
 3. **DO NOT SELF-VERIFY.** ...
 4. **CHECK PROGRESS.md BEFORE EVERY DISPATCH.** ...
 5. **WHEN IN DOUBT, DECOMPOSE.** ...
```

Replace the "MANDATORY: Classification Gate" subsection:

```diff
-### MANDATORY: Classification Gate
-
-Before any work begins, output a classification block:
-
-```
-[TASK CLASS: one-shot | structured | long-horizon]
-Justification: <one-line reason>
-```
-
-Omitting this classification is a protocol violation.
+### MANDATORY: Classification Gate (β-fuse)
+
+Before any work begins, your FIRST action must be:
+
+```
+delegate_worker_v2(
+  classification="one-shot" | "structured" | "long-horizon",
+  justification="<concrete, ≥30 chars, references THIS task's properties>",
+  goal="<self-contained worker spawn>"   # required for structured/long-horizon
+)
+```
+
+Skipping this tool call is a protocol violation regardless of how clearly you
+describe the task class in prose. The harness only sees tool calls.
```

Replace dispatch scaffolding examples to use `delegate_worker_v2`. Remove any
"if you truly believe dispatch isn't warranted, re-classify to one-shot"
escape-hatch language (per Layer 2's anti-escape-hatch principle): one-shot is
still a tool call, so there's no longer any way to "opt out" of the contract.

---

## 5. Migration plan

Three options considered:

| Option | Pro | Con |
|--------|-----|-----|
| **Big bang** — rename old `delegate_worker` → `delegate_worker_legacy`, ship v2 as the only first-class option | Forces clean break, no ambiguity for the model | Breaks any external skill / probe wrapper that hardcodes the `delegate_worker` name; correction messages in `probe-variantE-wrapper.sh` reference `delegate_worker` explicitly |
| **Side-by-side** — register both `delegate_worker` and `delegate_worker_v2`. HERMES.md teaches v2. Old still works but undocumented. | Zero breakage. Gradual adoption. Supports A/B testing v1 vs v2 in probes. | Model may pick the simpler one (`delegate_worker`) by accident, defeating β-fuse. Schema descriptions must heavily discourage v1. |
| **Schema-update-in-place** — add `classification` and `justification` as required to the existing `delegate_worker` | No new tool to introduce; minimal surface change. | Backwards-incompatible for any current caller. Worse: legacy probe runs and saved sessions can't be re-checked under the new schema since their tool calls lack the required fields. |

**Recommendation: Side-by-side with a deprecation arc.**

- **Phase 1 (deploy):** register both tools. Update `HERMES.md` to teach v2
  exclusively. Update `probe-variantE-wrapper.sh` correction messages to
  reference `delegate_worker_v2`. Update `probe-variantF-check.py` to prefer
  v2. Keep v1 callable but emit a `deprecation_warning` field in v1's response.
- **Phase 2 (validate):** run r7.4 probe matrix. Confirm v2 adoption ≥95% on
  first attempt across both models. Confirm legacy v1 calls drop to <5%.
- **Phase 3 (sunset):** if Phase 2 holds for two consecutive probe rounds,
  remove v1 from the registry. Migrate any in-flight skills at this point.

Why side-by-side over big bang: the probe wrapper itself (`correction_for` in
`probe-variantE-wrapper.sh`) hardcodes the `delegate_worker` name in the
correction-message templates. A big bang would require atomic update of (a)
HERMES.md, (b) the wrapper, (c) check.py, (d) the registry — across the
local repo and the VM. Side-by-side decouples those.

Why side-by-side over schema-update-in-place: schema-update-in-place loses the
ability to re-evaluate historical sessions, which is critical for A/B
attribution ("did β-fuse help, or was it the Layer-1+2 changes that already
landed?"). Two distinct tool names give us a clean signal in session logs.

---

## 6. Risk + cost

### Engineering cost (estimated)

| Item | Lines / hours |
|------|---------------|
| `delegate_worker_v2.py` (new) | ~80 lines, 0.5 hr |
| `probe-variantF-check.py` (rewrite of E with classification source detection) | ~60 net new lines, 1 hr |
| `HERMES.md` edits (Critical Rule #1, Classification Gate, dispatch examples) | ~40 lines changed, 0.5 hr |
| `probe-variantE-wrapper.sh` → `probe-variantF-wrapper.sh` (correction message updates, check script reference) | ~30 lines changed, 0.5 hr |
| `tools/registry.py` registration entry | ~15 lines, 0.25 hr |
| Probe matrix re-run (15 tasks × 2 models × 1 attempt baseline + retries) | 2 hr wall-clock |
| Diagnostic + writeup | 1 hr |
| **Total focused effort** | **~5 hours** |

### Risk surface

- **High — contract break.** Changes the tool that the model is required to
  call first. Any in-flight session using v1 surface during the transition will
  see inconsistent enforcement (gate may pass under v1 path but fail under v2
  expectations). Mitigation: side-by-side migration (§5).
- **High — gate re-validation.** `probe-variantF-check.py` has a different
  classification-source semantics than E. Existing PROBE-RESULTS-r7.md numbers
  cannot be compared apples-to-apples until re-run. Mitigation: explicit
  re-baseline before claiming improvement.
- **Medium — model adoption uncertainty.** β-fuse assumes that *making the
  classification a tool call* will overcome MoE's chatbot-mode termination.
  This is a hypothesis, not a guarantee. MoE could just as well terminate
  *before* emitting any tool call. Mitigation: Phase 2 measures
  `v2_was_first_tool` adoption rate empirically; if MoE adoption stays <70%,
  β-fuse failed and we revert.
- **Medium — scope creep risk.** The temptation will be to also add `verify`,
  `progress_update`, etc. as required tool calls. Resist. β-fuse is one
  surgical change.
- **Low — existing PROGRESS.md / PLAN.md tooling.** No interaction. β-fuse is
  upstream of all state-management tooling.

### What β-fuse does NOT solve

- It does not prevent role collapse *after* dispatch. Workers can still
  in-line implementation themselves. (Not in scope; Layer 2's structural
  enforcement covers this.)
- It does not prevent fabrication. (Layer 2's last-3-errors check covers
  this.)
- It does not improve classification *quality* — only that classification is
  recorded. A model that mis-classifies a 10-file refactor as "one-shot"
  passes the gate. (Acceptable: justification text + downstream gates catch
  this.)

---

## 7. When to deploy

**Skip Layer 3 (β-fuse) if:**

- Layers 1+2 lift dense first-attempt to ≥7/15 AND
- Layers 1+2 lift MoE first-attempt to ≥4/15

In that case, the simpler interventions are sufficient and the contract-break
cost of β-fuse is not justified.

**Deploy Layer 3 (β-fuse) if:**

- Layers 1+2 fall short of either threshold, AND
- The dominant residual failure mode is "marker-without-dispatch" (per
  worker β's classification — MoE's chatbot-mode termination after
  justification, or dense's "I'll orient first" then no dispatch on first
  attempt).

**Specifically for MoE:** β-fuse is targeted medicine for β's finding.
3/5 MoE structured tasks terminated with zero tool calls after the marker.
Making the marker itself a tool call closes that exact failure mode by
construction.

**Sequencing within deployment:**

1. Land schema + handler + registry entry. (No behavior change yet — tool
   exists but HERMES.md doesn't mention it.)
2. Update `probe-variantF-check.py` with backwards-compat (still accepts text
   markers on legacy sessions).
3. Update HERMES.md to teach v2 exclusively.
4. Update probe wrapper correction messages.
5. Run r7.4 probe matrix on both models. Compare to r7.3 baseline.
6. If adoption ≥95% and gate-pass improves by ≥3 points on at least one
   model: declare β-fuse a win and proceed to Phase 3 sunset of v1.
7. If adoption stalls or gate-pass does not improve: revert HERMES.md to the
   text-marker contract (rollback is a single-file edit), keep the v2 tool
   registered as opt-in, and document the negative result in
   `PROBE-RESULTS-r7.md` so future iterations don't repeat it.

---

## Appendix A — Files affected by full deployment

| File | Change | Lines |
|------|--------|-------|
| `variants/hermes/delegate_worker_v2.py` | NEW | ~80 |
| `variants/hermes/HERMES.md` | EDIT | ~40 |
| `variants/hermes/delegate_worker.py` | EDIT (add deprecation field in response) | ~5 |
| `probe-variantF-check.py` | NEW (derived from variantE) | ~190 |
| `probe-variantF-wrapper.sh` | NEW (derived from variantE, correction messages updated) | ~235 |
| `tools/registry.py` (or equivalent) | EDIT (register v2) | ~15 |
| `evaluation/PROBE-r7-runbook.md` | EDIT (add r7.4 baseline procedure) | ~20 |
| `PLAN-r7.md` or successor | EDIT (record β-fuse outcome) | ~10 |

Total: 1 new tool file, 1 new check.py, 1 new wrapper, ~5 edits. ~595 lines
written or changed across ~8 files.

## Appendix B — Why "v2" naming over alternatives

Considered: `classify_and_dispatch`, `task_entry`, `begin_task`, `dispatch`,
`delegate_classified`. Rejected because:

- `classify_and_dispatch` overstates what happens for one-shot (no dispatch
  occurs).
- `task_entry` / `begin_task` are too generic; the model may invent uses.
- `dispatch` collides with the verb used throughout HERMES.md prose for "spawn
  a worker," ambiguous when one-shot.
- `delegate_classified` is awkward and obscures the lineage from
  `delegate_worker`.

`delegate_worker_v2` reads as "the new version of the tool you already know,"
keeps adoption friction low, and signals the migration intent in the name
itself.
