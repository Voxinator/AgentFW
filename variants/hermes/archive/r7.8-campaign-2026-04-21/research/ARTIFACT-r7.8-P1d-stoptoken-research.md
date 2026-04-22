---
type: r7.8 P1d — stop-token + truncation research
date: 2026-04-21
---
# r7.8 P1d — stop-token + truncation research

Read-only research worker. Budget: 60-90 min. Goal: characterize how Hermes handles `finish_reason`, mid-turn truncation, stop-tokens, and loop detection; propose interventions that let failures self-terminate cleanly instead of producing degenerate output.

All line references point at canonical host VM files rooted at `/home/parallels/.hermes/hermes-agent/` unless otherwise noted. File hashes verified live.

---

## 1. Turn budget (current state)

**Enforcement site:** `run_agent.py:7111` — `while api_call_count < self.max_iterations and self.iteration_budget.remaining > 0:` plus `run_agent.py:7125` (`self.iteration_budget.consume()`) and post-loop exhaustion branch at `run_agent.py:9092-9098`.

**What it limits:** **Per-agent only.** `IterationBudget` (defined `run_agent.py:168-209`) is constructed fresh for each `AIAgent` instance. The parent gets one. Each child spawned through `tools/delegate_tool.py:_build_child_agent` (line ~287-316) is explicitly given `iteration_budget=None` → fresh budget. This is documented in the class docstring:

> Each agent (parent or subagent) gets its own IterationBudget. ... Each subagent gets an independent budget capped at `delegation.max_iterations` (default 50) — this means total iterations across parent + subagents can exceed the parent's cap.
> — `run_agent.py:170-175`

**Where the parent's cap comes from:** CLI flag `--max-turns=20` → `run_agent.py:9251` (`main(..., max_turns: int = 10)`) → `run_agent.py:9391` (`max_iterations=max_turns`) → `AIAgent.__init__` → `self.iteration_budget = IterationBudget(max_iterations)` at `run_agent.py:533`.

**Where the child's cap comes from:** `tools/delegate_tool.py:544-545`:

```python
default_max_iter = cfg.get("max_iterations", DEFAULT_MAX_ITERATIONS)  # DEFAULT=50
effective_max_iter = max_iterations or default_max_iter
```

Live `/home/parallels/.hermes/config.yaml` contains `delegation: max_iterations: 50`. Grep confirmed.

**Why overshoot observed in r7.7 Arm G T5-run2 (42 > 20):** *The overshoot is not a bug; the "20-turn budget" is a parent-only cap.* The child session `20260420_215905_3e1c1e` had its own independent 50-turn budget. It ran 42 assistant turns before producing a summary (presumably because the model *volunteered* to wrap up rather than hit the 50 ceiling). The same applies to Arm G T10-run5 (48 turns, child session `20260420_225429_27586a` — also hit the length-continuation path before exhausting the 50-cap). This is a **documented, intentional design choice** but it means the harness's advertised "20 turns" has no load-bearing relationship to child behavior, which is where the expensive thrash happens. A probe harness specifying `--max-turns 20` reasonably expects that to bound total wall-clock cost; it does not.

---

## 2. `finish_reason=length` handling (current state)

**Entry site:** `run_agent.py:7548` after `finish_reason` is normalized at `run_agent.py:7543-7546`.

**Flow (chat_completions mode):**

1. **Log** truncation: `⚠️ Response truncated (finish_reason='length') ...` (line 7549, `force=True`).
2. **Thinking-exhaustion short-circuit** (lines 7553-7606): if the content after the `<think>` block is empty OR content is entirely `None`, treat as "model burned output budget on reasoning with nothing left" → return `partial=True` with user-facing **⚠️ Thinking Budget Exhausted** message. **No continuation retry.** This path short-circuits early (good) but also *fires on any model that returned no visible content*, including Gemma MoE emitting a channel-marker fragment.
3. **Continuation path** (lines 7608-7644): if `not assistant_message.tool_calls` and `length_continue_retries < 3`:
   - Append the partial assistant message + a `[System: Your previous response was truncated...]` user prompt.
   - Set `restart_with_length_continuation = True` → outer loop retries *the same turn* (does **not** consume another `iteration_budget` slot per refund at `run_agent.py:8430-8431`).
4. **After 3 retries exhausted:** return with `partial=True, error="Response remained truncated after 3 continuation attempts"` (lines 7648-7660).
5. **If turn had `tool_calls`** (length truncation *in the middle of a tool_call emission*): falls through to the rollback branch at lines 7648-7674 — rolls back to last complete assistant turn and returns `partial=True`.

**Observed failure mode in r7.7 Arm G T10-run5:** messages[-2] is the `[System: Your previous response was truncated...]` continuation prompt; messages[-1] resumed the **same degenerate self-talk loop** (`Actually, I'll try write_file. (I'll try write_file) Actually, I'll try execute_command. ...`) for tens of KB. The continuation retry doesn't break loops — it just asks the model to keep going, and the model keeps generating the same garbage. After 3 continuations the session returned `partial=True`, but the degenerate content was still persisted into the session JSON as the final assistant message, which is what the judge read.

**Gap:** The continuation system assumes the truncated content was *progress*. When the content is a pathological loop, continuation accelerates the garbage rather than short-circuiting it.

---

## 3. Loop detection (current state)

**There is no cross-turn loop detection.**

What exists:

- `_deduplicate_tool_calls` at `run_agent.py:2857-2872`: dedupes identical `(tool_name, arguments)` pairs **within a single assistant turn** only. If the assistant emits `search_files(*dashboard*)` five times in the same turn, four are dropped. If the assistant emits `search_files(*dashboard*)` across five consecutive turns, all five fire.
- `duplicate_interim` check at `run_agent.py:8590-8598`: used only in the **Codex incomplete-response retry** path to avoid appending the same incomplete message twice. Scope: within a single turn's retries. Not a loop detector.
- No per-turn tool_call history is kept; no n-gram or rolling-window check on `(name, normalized_args)` exists; no hash-of-last-K comparison.

**Scanned files:** `run_agent.py`, `agent/anthropic_adapter.py`, `agent/auxiliary_client.py`, `tools/delegate_tool.py`. Zero hits for `recent_tool_calls`, `tool_history`, `loop_detect`, `same_call`, `last_tool`, any rolling-window tool-call comparison. The only signals the model gets are budget nudges (`_get_budget_warning` at `run_agent.py:6586-6609`), which inject a `[BUDGET WARNING: ...]` system line into the last user message at 70% and 90% of `max_iterations`. That nudge plus budget exhaustion is the **only ceiling** that stops thrash today.

**Observed failure mode in r7.7 Arm G T5-run2:** 40 consecutive `search_files` calls on variations of `*dashboard*`, `*chief*`, `*staff*`, `*tasks*`, `*api*` (evidence in `ARTIFACT-r7.7-judge-ArmG-T5-run2.md` §Evidence). The child never progressed. The budget warning at 35/50 (70%) and 45/50 (90%) fired but did not change behavior — the model emitted a budget nudge in the last 15 turns and kept searching. Eventually the model produced a summary spontaneously at turn 42 (still under the 50-turn ceiling). Had the model not given up voluntarily, the ceiling would have been 50 turns + `_handle_max_iterations` summary request.

---

## 4. Stop-token set (current state)

**What is passed to oMLX (and every other OpenAI-compatible endpoint):** an **empty stop set**. The `stop` parameter is never added to `api_kwargs`.

**Evidence:** `api_kwargs` dict is constructed at `run_agent.py:5367-5450` (function `_build_api_kwargs`). Keys that get populated: `model`, `messages`, `timeout`, `tools`, `max_tokens`, `extra_body`, `extra_headers`. There is **no `stop`, `stop_sequences`, or `stop_tokens` key** set anywhere on the chat-completions path. Grepping `run_agent.py` for the literal string `"stop"` returns only:

- Error handling / retry branches that test *returned* `finish_reason == "stop"`.
- Anthropic adapter mapping for `stop_reason → "stop"` at `agent/anthropic_adapter.py:1361`.
- A few `finish_reason = "stop"` assignments (synthetic stubs, e.g. auxiliary_client).

There is no `client.chat.completions.create(..., stop=[...])` call site anywhere in the Hermes codebase (grep confirmed, `run_agent.py:4196`, `:5788`, `:6736`, `:6777` — none of them pass a `stop` field).

**Channel markers (`<channel|>`, `<|channel|>`, `thought\n<channel|>`) in stop set?** **No — they cannot be, because the stop set does not exist.** This is the key finding. The r7.6 P1C `ARTIFACT-r7.6-P1C-diag-channel-leak.md` documented that 13/20 Arm A children (65%) emit channel-marker fragments, 6/20 (30%) had a final message that was *purely* the marker. P1A introduced a *post-hoc* `_r76_channel_marker_only()` detector at `run_agent.py:~417-445` to **classify** polluted content as a VIOLATION; it does not stop the decoder from emitting the marker in the first place.

A stop-sequence injection at the API layer is straightforward for OpenAI-compatible endpoints (`stop=["<channel|>", "<|channel|>"]`), and oMLX's OpenAI-compatible surface forwards `stop` to the sampler. This is orthogonal to any chat-template fix on the model side.

---

## 5. Candidate interventions

Four candidates. All four are independently rollback-safe (each is a single self-contained patch).

### T1: Cross-turn loop detector

**Target:** `run_agent.py:7111` (the main loop header). Insert a cheap rolling-window check just after `api_call_count += 1` (line 7122) and before `self.iteration_budget.consume()`.

**Change (pseudocode):**

```python
# After api_call_count += 1 (line 7122):
_last_tool_signatures = getattr(self, "_last_tool_signatures", [])
# Compute signature of the PRIOR assistant turn's tool_calls (before we
# make a new API call).  Use (name, canonicalized_args_hash).
prior_assistant = next((m for m in reversed(messages)
                        if m.get("role") == "assistant"
                        and m.get("tool_calls")), None)
if prior_assistant:
    sigs = tuple(
        (tc["function"]["name"],
         hashlib.md5(
             json.dumps(
                 json.loads(tc["function"]["arguments"] or "{}"),
                 sort_keys=True
             ).encode()
         ).hexdigest()[:8]
        )
        for tc in prior_assistant["tool_calls"]
    )
    _last_tool_signatures.append(sigs)
    _last_tool_signatures = _last_tool_signatures[-5:]  # keep last 5 turns
    self._last_tool_signatures = _last_tool_signatures

    # Trigger if the last 5 turns all produced the same tool-call signature.
    if len(_last_tool_signatures) == 5 and len(set(_last_tool_signatures)) == 1:
        # Force summary termination — append a direct escape-hatch prompt
        # and break before consuming another budget slot.
        messages.append({
            "role": "user",
            "content": (
                "[System: You have emitted the same tool call 5 turns in a row. "
                "This indicates a loop. Stop calling tools. Summarize what you "
                "have found, what you could not find, and what the concrete "
                "blocker is. Respond with natural language only.]"
            ),
        })
        self._last_tool_signatures = []  # reset so the summary call is not blocked
        # fall through to normal API call — next response is the summary
```

Normalize args to strip probe nonce / timestamps before hashing. Threshold configurable (default 5; could expose as `delegation.loop_detection_threshold`).

**Generalization:** Applies to every task and every model. Loop signatures are model-agnostic — `search_files` thrash, `read_file` thrash on same path, repeated `execute_command echo test`, etc. Matches brief's "last 5 identical tool on same query family" FAIL signature exactly as judged in Arm G T5-run2.

**Rollback:** Single guard `if os.environ.get("HERMES_LOOP_DETECT", "1") == "1":` around the block. Or keep the PR isolated to one `@staticmethod` + one call site; revert by reverting the commit.

**Vet plan (small-sample):** Rerun Arm G T5-run2 scenario cold 3× with the same oMLX Gemma-MoE + identical goal; expect assistant turn count to drop from ~42 to ≤10, with the final message being a coherent "I could not find repo at X; found only Y" summary. Secondary check: run Arm F T4/T5/T10 (where loop does not occur) to confirm no regression — turn counts should be unchanged within ±1.

---

### T2: Channel-marker stop-token injection

**Target:** `run_agent.py:5367` (`_build_api_kwargs`). Add a `stop` field when the endpoint is local/oMLX or when the model is known to leak Harmony tokens.

**Change:**

```python
# After api_kwargs = {...} block, before extra_body assembly:
if self._is_local_endpoint() or "gemma" in (self.model or "").lower():
    # Channel-marker stop tokens — prevent oMLX Gemma-MoE chat-template
    # regressions from leaking Harmony reasoning-header fragments into
    # visible content (documented in ARTIFACT-r7.6-P1C-diag-channel-leak).
    api_kwargs["stop"] = ["<channel|>", "<|channel|>", "<|start|>"]
```

Add a config escape hatch: `config.yaml: local.stop_tokens: [...]` merged in if present.

**Generalization:** Partial. Very targeted at the oMLX Gemma-MoE failure surface. But since stop-sequence support is standard OpenAI-compatible behavior, the same mechanism extends to any future model that leaks a known fragment. The list is editable without code changes (if lifted to config).

**Rollback:** Pop the key. One-line revert.

**Vet plan:** Rerun the 20-trial Arm A probe from P1C. Expect:
- `""` empty-content turns: unchanged (not the failure mode).
- `<channel|>` / `thought\n<channel|>` pure-marker terminal turns: **drop to zero**. The model should instead produce proper natural-language content or at worst a shorter fragment that does not contain the marker substring. Counter-check with `_r76_channel_marker_only()` detector: should return 0/20 on the 20 children.
- Measure: no regression on task outcomes (COMPLETION/CORRECTNESS). If the `<channel|>` token was *all* the model wanted to emit, stopping there may produce empty content instead — in which case T2 and T3 compose.

---

### T3: Per-turn `max_tokens` raise + stricter `finish_reason=length` handling

**Target:** `run_agent.py:7608-7644` (length continuation block).

**Change:** Two sub-changes.

**T3a** — on any `finish_reason=length` where the continuation is appended, compute a **token-cost ceiling**: if the cumulative continuation tokens already exceed `2 × self.max_tokens`, do not continue; return `partial=True, error="response_exceeded_2x_budget"` instead. Guards against the Arm G T10-run5 "degenerate loop burns 30KB of `I'll try X...`" case.

**T3b** — apply a **content-repetition check** inside the continuation branch:

```python
if assistant_message.content and truncated_response_prefix:
    # Detect degenerate repetition: if the last 200 chars of the
    # concatenated content repeat the same 40-char substring more than
    # 3 times, we're in a loop — do not continue.
    concat = (truncated_response_prefix + assistant_message.content)[-400:]
    import re
    m = re.search(r"(.{20,80})\1\1", concat)
    if m:
        # Terminate with partial, not another continuation.
        self._persist_session(messages, conversation_history)
        return {
            "final_response": None,
            "messages": messages,
            "api_calls": api_call_count,
            "completed": False,
            "partial": True,
            "error": "Degenerate loop detected in truncated content; terminated early.",
        }
```

**Generalization:** T3a is universal (applies to any model that overruns). T3b applies to any model emitting textual self-repetition under continuation (observed concretely on Gemma-MoE but the repetition check is model-agnostic).

**Rollback:** T3a is a two-line early-return inside an existing branch. T3b is a single regex check. Both are guarded by the existing `finish_reason == "length"` branch so they cannot affect healthy turns.

**Vet plan:** Rerun Arm G T10-run5 scenario 3×; expect max assistant-turn count to stop at the turn of first loop-detection (≤8 turns instead of 48) with `partial=True`. Confirm zero false-positives on 10 healthy Arm F runs (pick the ones that returned a long natural summary — the repetition check must not fire on legitimate bullet lists).

---

### T4: Turn-budget enforcement fix (parent/child alignment)

**Target:** `tools/delegate_tool.py:544-545` and `run_agent.py:533`.

**Change:** Honor a parent-scoped *aggregate* cap when requested. Two sub-options:

**T4a — Hard cap:** Add a new kwarg `inherit_parent_budget: bool` to `delegate_task`. When true, pass the parent's `iteration_budget` object (not `None`) into the child. Children share the parent's budget atomically (the existing `IterationBudget._lock` already supports concurrent access). Result: `--max-turns 20` becomes a real ceiling across parent + all children.

```python
# delegate_tool.py:315
iteration_budget=(
    parent_agent.iteration_budget if inherit_parent_budget else None
),
```

**T4b — Soft cap (less risky):** Keep child's independent budget, but **cap it at `min(delegation.max_iterations, parent.iteration_budget.remaining + K)` where K is a safety margin (e.g. 10)**. This way, a child spawned late in a 20-turn parent run gets only 10-30 turns, not a full fresh 50. Safer for a dispatch-heavy architecture where shared budget might starve later dispatches.

Pick T4b as the default — it's safer, doesn't break the "children can finish their work" invariant, and still fixes the "child blows past parent's advertised budget by 2x+" problem. Expose T4a as an opt-in for research harnesses that want a hard wall-clock ceiling.

**Generalization:** High. This affects every dispatch-heavy run. Fixes the entire class of "probe says --max-turns 20, child consumes 42" surprise.

**Rollback:** One-line kwarg change in `delegate_tool.py` + one-line ceiling computation. Revertible.

**Vet plan:** Rerun Arm F + Arm G batches (20 trials each) with T4b enabled (safety margin K=10). Measure:
- Child turn counts should now obey `parent_remaining + 10` at spawn time.
- COMPLETION/CORRECTNESS rates unchanged or improved (children stop thrashing earlier).
- Wall-clock per probe should drop measurably (5-15%) since degenerate children self-terminate at 25-30 turns instead of 48-50.

---

## 6. Ranking

Ranked by **expected quality lift per unit of implementation + rollout risk**, given the evidence in r7.6 P1C and r7.7 Arm F/G artifacts.

1. **T1 — Cross-turn loop detector.** Highest general-purpose lift. Directly fixes the root failure pattern that wrecked Arm G (T5-run2 = 40 search_files thrash; T10-run5 = 45 search_files thrash → degenerate self-talk). Model-agnostic, task-agnostic, cheap (~30 lines + a hash), fully reversible. Only real risk: false positive on a legitimate iterative tool loop (e.g. reading 5 consecutive files in a known directory). Mitigate by keeping the threshold at 5 and by normalizing args so near-identical-but-distinct calls (`read_file path=a`, `read_file path=b`) don't collide.

2. **T4 (T4b variant) — Parent/child budget alignment.** Second-highest lift because it bounds wall-clock on every run, not just the ones that loop. Turns the "20-turn budget" promise into reality without breaking children that genuinely need more turns (safety margin K). Low implementation risk; one-line behavior change.

3. **T3 — Per-turn max_tokens cap + repetition check in length-continuation.** Directly addresses the Arm G T10-run5 degenerate-content-in-continuation failure, and T3a is a universal truncation-safety net. Slightly higher complexity than T1 (needs the regex heuristic), slightly lower general-purpose coverage than T1 (only fires on length-truncated turns, not on healthy turns that happen to be in a thrash loop).

4. **T2 — Channel-marker stop-token injection.** Narrowest. Targets exclusively the oMLX Gemma-MoE chat-template regression documented in `ARTIFACT-r7.6-P1C-diag-channel-leak.md`. Extremely cheap to ship, but the failure mode is already partially mitigated by the P1A `_r76_channel_marker_only()` detector downstream. Worth shipping *alongside* T1 because it's ~3 lines and eliminates a known pollution surface — but on its own, it does not move the needle on the non-oMLX targets that r7.8 wants to generalize to.

**Recommendation:** Ship T1 + T4b together as the r7.8 P1d fix — they compose naturally (T4b bounds the worst case; T1 short-circuits the common case). Add T3a (2x-budget ceiling in length-continuation) as a defensive patch since it's trivial. Defer T3b and T2 to a follow-up if the smoke run still shows content-layer pathology.

---

## 7. Confidence and open questions

**High confidence (verified directly):**
- Turn budget is strictly per-agent; child gets fresh `IterationBudget(50)`. Config value verified in `~/.hermes/config.yaml`.
- No `stop` parameter is ever passed to any chat-completions endpoint.
- No cross-turn loop detection of any kind exists in Hermes.
- `_deduplicate_tool_calls` only acts within a single assistant turn.

**Medium confidence:**
- oMLX honors the OpenAI `stop` parameter on its `/v1/chat/completions` endpoint. Assumed from the OpenAI-compatible surface; should be confirmed with a 5-line smoke test before shipping T2 (single `curl` with `"stop":["<channel|>"]` and inspect response).
- Loop-detection threshold of 5 is adequate. Could be 4 or 6; only evidence is judge rubric's "last 5 identical" signature, which itself was a heuristic.

**Open questions for a follow-up:**
- What fraction of r7.7 Arm G FAILs would have been avoided by T1 alone vs. T1+T4b? Answerable by replaying the 20 sessions through a simulated loop-detector offline on the stored session JSONs — no VM runtime needed.
- Does oMLX tokenize `<channel|>` as a single token? If it's split across two tokens the `stop` trick works; if it's inside a special-token boundary the sampler may not match. Worth a sanity check against oMLX's tokenizer if T2 is picked up.

---

Word count: ~1850. File paths and line numbers verified against live VM state. Read-only: no runtime state was mutated during this investigation.
