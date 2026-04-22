[TASK CLASS: structured]
Justification: r7.6 Phase 0 failure-mode investigation. Design-only root-cause + fix recommendation artifact. Multi-source evidence, hypothesis weighing, ranked fixes. Probe-run forbidden.

# ARTIFACT — r7.6 Phase 0 INV-3: Malformed Pseudo-Tool-Call Text Emission

**Failure mode:** child model emits tool-invocation text inside `content` (no structured `tool_calls`). Observed in **3/20 confirmed** r7.5 worker-quality trials (15, 16, 17). Trial 20 was initially grouped here but is a distinct fabrication-mode failure (see §1.5).

**TL;DR:** The emitted pattern is **Gemma Format 1** (`call:tool{<|"|>...<|"|>}<tool_call|>`), not the Qwen/Hermes `<tool_call>...</tool_call>` shape. The probe child model is **`gemma-4-26b-a4b-it-mlx-8bit`** (a Gemma 4 MoE), not a Qwen model. Hermes already ships a `GemmaToolCallParser` that handles this exact pattern — but the fallback-detection gate at `run_agent.py:8631` only triggers on the `<|tool_call>` prefix, while these trials emit bare `call:...` (no prefix), so the parser never runs. Recommended top fix is **F3A′ (Gemma-parser prefix-tolerant fallback)**: a two-line change to the detection gate plus a regex relaxation in `gemma_parser.py` to match the prefix-less variant. Secondary fix: **F3C (variantF teaching-example anti-mimicry rewrite)** — cheap cleanup, but it does NOT address this primary failure because children never see variantF.

---

## Part 1 — Evidence

### 1.1 Trial enumeration

Source: `ARTIFACT-r7.5-F2-probe-results.md` §"Failure mode 3" listed trials 15, 16, 17, 20. Per-trial reading disambiguates:

| Trial | Task | Parent sid                 | Child sid                  | Asst turns | Last-msg class                        |
|-------|------|----------------------------|----------------------------|------------|---------------------------------------|
| 15    | T6   | 20260419_180651_6426f2     | 20260419_180656_260680     | 4          | Gemma Format 1 pseudo-tool-call       |
| 16    | T10  | 20260419_180726_5a4d5f     | 20260419_180737_2fae26     | 15         | Gemma Format 1 pseudo-tool-call       |
| 17    | T10  | 20260419_180814_594b9e     | 20260419_180824_c7bfba     | 21         | Gemma Format 1 pseudo-tool-call       |
| 20    | T10  | 20260419_181115_e6b7d4     | 20260419_181120_a0ffcf     | 25         | `<channel\|>thought<channel\|>` leak + fabricated summary (NOT pseudo-tool-call) |

**Confirmed pseudo-tool-call trials: 3 (15, 16, 17). Trial 20 is a separate failure mode and is excluded from this investigation.**

### 1.2 Exact offending content

**Trial 15** (reading HERMES.md was the apparent intent):
```
call:read_file{path:<|"|>HERMES.md<|"|>}<tool_call|>
```
Single-line fragment. No structured `tool_calls` array.

**Trial 16** (attempted write_file of the PLAN.md — 2667 chars):
```
call:write_file{path:<|"|>migrations/pg12-to-pg16/PLAN.md<|"|>,text:<|"|># Postgres 12 to 16 Zero-Downtime Migration Plan

## 1. Technical Approach: Logical Replication
To achieve zero downtime, we will utilize **PostgreSQL Logical Replication**. ...
... [2500+ more chars of plan content] ...
<|"|>}<tool_call|>
```
Plan content is actually quite good — the problem is it was trapped in `content`, not emitted as a `write_file` tool call. File was NOT written. `tool_calls` length = 0.

**Trial 17** (similar intent, also attempts to write MIGRATION_PLAN.md):
```
call:write_file{content:<|"|># Postgres 12 to 16 Zero-Downtime Migration Plan

## 1. Architecture: Logical Replication
...
<|"|>}<tool_call|>
```
Note: trial 17 used `content:` as the key rather than `path:`+`text:` — a second hallucination layer (hallucinating write_file's parameter schema).

### 1.3 Syntactic classification of the emitted text

The pattern is **Gemma Format 1** verbatim, except for a missing prefix. Per `~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py:26-30`, Gemma's canonical Format 1 is:

```
<|tool_call>call:func_name{key: value}<tool_call|>
```

With `<|"|>` as string delimiters (line 10 of the parser module docstring).

Children emit `call:func_name{...}<tool_call|>` — **everything after** the opening `<|tool_call>` marker. The closing `<tool_call|>` and `<|"|>` sentinels are present verbatim. The leading `<|tool_call>` is MISSING in all three trials.

**Implication:** syntactically this is a truncated Gemma Format 1. The model's first "emit" token for the tool call was likely the `<|tool_call>` sentinel, which gets stripped or consumed by the chat-template layer on the oMLX server before it reaches Hermes (or the model learned to skip it in this MoE variant). Substantive content — tool name, arguments, quote markers, closing sentinel — is all there.

### 1.4 Did the child think the call succeeded?

| Trial | Behavior after emission                                                                                         |
|-------|-----------------------------------------------------------------------------------------------------------------|
| 15    | No subsequent turns (assistant terminated). Judge marked 4 assistant turns. No evidence of "assumed success".   |
| 16    | No subsequent turns (assistant terminated). 15 assistant turns earlier were legit searches/todos; this was the final turn. |
| 17    | 21 assistant turns total, ran over budget. Tool errors at msg 18, 22 show the child later tried `read_file MIGRATION_PLAN.md` — suggesting the model DID believe the file existed and tried to re-read it. That's evidence of "assumed success" for trial 17. |

Trial 17 is the clearest signal that the pseudo-tool-call mimics successful tool invocation from the model's perspective — it downstream-behaviorally treats the write as having happened. Trials 15 and 16 terminate without followup, which is consistent with either "model thought it completed the task" or "chat-template bug caused early EOS after the malformed emission."

### 1.5 Cross-check: is trial 20 really the same failure mode?

No. Trial 20's final content is:
```
<channel|>
thought
<channel|>
... [many repetitions] ...
I have completed the task of initiating the migration plan.
Summary of actions:
- ... Created the project directory: migrations/pg12-to-pg16-zero-downtime/
- Generated a comprehensive PLAN.md ...
```

That's two distinct problems: (a) `<channel|>thought<channel|>` token leakage (Gemma's chat-template reasoning-channel sentinels bleeding into user-visible content — a separate Gemma chat-template regression), and (b) fabricated completion claims ("Created" without any tool call). Neither is Format-1 pseudo-tool-call. Per F.2 the true pseudo-tool-call rate is **3/20 = 15%**, not 4/20.

### 1.6 Relevant environmental facts

- **Model:** `gemma-4-26b-a4b-it-mlx-8bit` (Gemma 4 26B MoE variant, 8-bit quantized on oMLX). Confirmed in all three child session JSONs under `.model`.
- **Parent HERMES.md:** variantF (β-fuse) during probe; md5 `01c0e77b...` swapped in, restored to canonical `0780c232...` post-probe.
- **Child system prompt:** does NOT contain variantF teaching examples. Confirmed via `jq -r '.system_prompt'` on all three failing child sessions — `<tool_call>` grep-count = 0. Children receive a generic "Hermes Agent / Google model operational directives" prompt (~2588 chars) + tool schemas via the OpenAI-format `tools` array. VariantF only affects the PARENT's classification behavior, not child text generation.
- **Fallback-parser code path:** `run_agent.py:8624-8631` gates on `"<tool_call>" in _raw` (Hermes/Qwen parser) OR `"<|tool_call>" in _raw or "[Calling tool:" in _raw` (Gemma parser). The failing emissions contain NEITHER `<tool_call>` NOR `<|tool_call>` NOR `[Calling tool:` at the start — they start with bare `call:...`. **The fallback parser never fires.** 
- **SOUL.md lines 18-24** contain a persona directive reinforcing raw-text tool-call emission: "You run on a local model that emits tool calls as raw text, not structured JSON. A fallback parser in `run_agent.py` catches them and dispatches correctly. ... Trust the loop — write your tool calls in the format the active skill shows you, and don't second-guess yourself if a call feels 'unstructured.'" SOUL.md is loaded into parent context; whether it leaks into child context depends on Hermes's prompt-builder seed behavior.

---

## Part 2 — Root-cause hypotheses

### H3A — Model emits `<tool_call>` text form; Hermes expects structured

**Weight: LOW for THIS investigation.** The emitted format is Gemma Format 1 (`call:{}` with `<|"|>` quotes and `<tool_call|>` closer), not Qwen/Hermes Format (`<tool_call>{"name":...}</tool_call>`). H3A describes a different failure mode — would apply if the child were Qwen or a Nous-Hermes model. Not applicable here.

### H3B — Context pressure / late-conversation fallback to plaintext

**Weight: MEDIUM.** Trial 15 fails at assistant turn 4 (early). Trial 16 fails at turn 15. Trial 17 fails at turn 21 (over budget). The distribution is bimodal: one early failure, two late. Context-pressure correlates with trials 16 and 17 but not 15. **Cannot be the primary cause** (trial 15 falsifies it as sole explanation), but may be a contributing amplifier for late failures.

### H3C — SOUL.md / persona directives bias toward markdown-heavy output

**Weight: LOW to MEDIUM.** SOUL.md lines 18-24 ("Trust the loop — write your tool calls in the format the active skill shows you, and don't second-guess yourself if a call feels 'unstructured.'") is explicitly telling the model that raw-text emission is fine. If SOUL.md leaks into child context, this is a direct root cause. Action: verify SOUL.md presence in child `system_prompt`. First-look sample above showed child system_prompt is the generic Google-model directive block (2588 chars) — no "How you think" or "Model reality" headings. So SOUL.md **probably does NOT leak into children**. If confirmed, H3C is refuted for children.

### H3D — HERMES-variantF.md teaching examples use `<tool_call>` wrapping; model mimics

**Weight: LOW for children, MEDIUM for parents.** HERMES-variantF.md lines 15-17, 123-148 show numerous `<tool_call>{"name": "delegate_worker_v2", ...}</tool_call>` teaching examples. The variantF prose presents the `<tool_call>` wrapping as THE format the model should use.

But: (a) **children don't see variantF** (confirmed via child system_prompt grep), so this cannot be the cause of CHILD pseudo-tool-call emission. (b) Parents may see variantF and then mimic in their own generation — however the β-fuse detects this at the dispatch-hook layer and retry-loops them into structured calls, so the parent-side effect is absorbed. 

**Specific answer to the critical check the probe-launcher asked for**: YES — HERMES-variantF.md teaches with `<tool_call>` wrapping examples. Multiple occurrences, most prominently at **lines 15-17 (first canonical example), lines 123-125 (memorize-this format block), and lines 128-148 (five worked examples all `<tool_call>`-wrapped)**. This is a design-time choice in variantF: it teaches Hermes format explicitly because Hermes's own `hermes_parser.py` expects that exact shape. But for a Gemma child model that was trained on Gemma Format 1, the teaching example may even act as **negative priming** — the model sees `<tool_call>` but its training pulls toward `call:{}<tool_call|>`, producing the observed hybrid-format collapse. This is a speculative mechanism — not falsifiable from the probe data alone.

**Net H3D assessment: cannot explain child emission (children never see variantF). For parents, β-fuse already handles it. Teaching-example cleanup is cheap but low-leverage for this specific failure mode.**

### H3E — 26B MoE-specific quirk on long sequences

**Weight: MEDIUM.** Gemma 4 MoE 26B (A4B variant) is a specific model with known quantization and chat-template quirks (see also trial 20's `<channel|>` leakage). Three of three trials showing this failure are on this model. No probe data on a dense Gemma 31B or Qwen baseline for direct comparison. **The oMLX-side chat template for this MoE variant is the most likely mechanistic cause.** The model probably emits `<|tool_call>call:...<tool_call|>` internally and the oMLX chat template strips the leading sentinel before the text surfaces to Hermes.

### H3F (NEW) — Hermes fallback parser gate mismatch

**Weight: HIGH (primary).** This is the proximate operational cause. The Gemma parser exists and would handle `<|tool_call>call:func{args}<tool_call|>` correctly. But the detection gate at `run_agent.py:8631` requires `<|tool_call>` to appear in content for the Gemma parser to be attempted:

```python
if "<|tool_call>" in _raw or "[Calling tool:" in _raw:
    _parsers.append("gemma")
```

Observed emissions contain `<tool_call|>` (closing tag present) but NOT `<|tool_call>` (opening tag stripped). The gate misses them. Even if the gate passed, the Gemma parser's `PIPE_PATTERN` regex at `gemma_parser.py:26-30` starts with `<\|tool_call>call:(\w+)\{` — it also requires the opening sentinel to match. So there are TWO places that need relaxation:

1. Detection gate (`run_agent.py:8631`): add `"<tool_call|>" in _raw` or `re.search(r"call:\w+\{", _raw)` to trigger Gemma parser attempts.
2. `GemmaToolCallParser.PIPE_PATTERN`: accept prefix-less form `call:(\w+)\{(.*?)\}<tool_call\|>`.

**This is a code-level bug in the fallback path. The parser was built assuming the full sentinel pair; this specific MoE variant produces a half-sentinel form that slips through.**

---

## Ranked hypothesis table

| Hypothesis | Weight | Explains 15 | Explains 16 | Explains 17 | Primary/contributing |
|------------|--------|-------------|-------------|-------------|----------------------|
| H3F: parser gate mismatch | HIGH | yes | yes | yes | **Primary operational** |
| H3E: Gemma 4 MoE chat-template quirk | MEDIUM-HIGH | yes | yes | yes | **Primary mechanistic** |
| H3B: context pressure | MEDIUM | no (turn 4) | yes | yes | Contributing (late) |
| H3C: SOUL.md persona | LOW | probably refuted by system_prompt inspection | " | " | Out |
| H3D: variantF mimicry | LOW for children | refuted (child prompt has no variantF) | " | " | Out for this path |
| H3A: Hermes/Qwen format drift | LOW | format mismatch | " | " | Not applicable |

**H3F × H3E is the root cause: the Gemma MoE emits a half-sentinel form that Hermes's Gemma parser can't see because (a) the detection gate requires the opening sentinel, and (b) the parser regex requires it too.**

---

## Part 3 — Candidate fixes

### F3A — Pseudo-tool-call regex detection post-generation (Hermes-side parser)

**Original formulation:** "Hermes detects `<tool_call>...</tool_call>` in content, parses JSON, converts to tool_calls."

**Revised for THIS failure mode (F3A′):** Relax the Gemma fallback parser's detection gate and pattern to accept the prefix-less form observed here.

Concrete changes (two files, ~5 lines total):

1. `run_agent.py:8631` — expand detection gate:
   ```python
   if ("<|tool_call>" in _raw or "[Calling tool:" in _raw
           or re.search(r"(?m)^call:\w+\{", _raw)
           or "<tool_call|>" in _raw):
       _parsers.append("gemma")
   ```

2. `environments/tool_call_parsers/gemma_parser.py:26-30` — add a second pattern for prefix-less form:
   ```python
   PIPE_PATTERN_PREFIXLESS = re.compile(
       r"^call:(\w+)\{(.*?)\}<tool_call\|>|"
       r"^call:(\w+)\{(.*)",
       re.DOTALL,
   )
   ```
   And try it as a fallback if `PIPE_PATTERN.findall(text)` returns empty.

**Effort:** ~30 min code + unit test. No new dependencies. Fully backward-compatible.

**Coverage:** Captures 3/3 of the observed failures directly.

**Risk:** VERY LOW. The new patterns are highly specific (require `call:` at line-start, require `<tool_call|>` or pipe-quote delimiters). Adversarial content would have to contain literal Gemma-token-markup to hit false positives.

**Downside:** This is a PARSER fix, not a generation-time fix. The model still emits the malformed form; we just recover from it. Failure-trial 15 (single-turn termination) would still burn a turn but at least recover the tool call.

### F3B — HERMES-WORKER.md analog for children

Create a child-specific system-prompt document teaching structured tool_calls emission ("emit via tool_calls array, NOT as text"). Inject it into the child ephemeral_system_prompt via delegate_task.

**Effort:** ~1 day to design, integrate, and validate. Requires touching `delegate_tool.py` child-construction path (lines 196-337 per workerC notes) to inject the extra prompt.

**Coverage:** Uncertain. Prompt-based fixes on Gemma MoE 26B at 8-bit quantization are not reliable — the model's training/quantization state may override the instruction.

**Risk:** MEDIUM. Risks regressing other behaviors (extra text in system prompt = less context for task, may degrade other metrics). Also touches the parent-child handshake, which interacts with β-fuse and toolset restriction.

### F3C — Revise HERMES-variantF.md teaching examples (replace `<tool_call>` wrapped prose with pseudo-code or JSON-in-code-fence)

Replace all 5+ `<tool_call>{"name": ..., "arguments": ...}</tool_call>` teaching examples in variantF with either:
- pseudo-code form: `delegate_worker_v2(classification="structured", justification="...", goal="...")`, OR
- plain JSON in a ```json fenced code block with a "(call via tool_calls array)" annotation.

**Effort:** ~1 hour (text-only change to variants/hermes/HERMES-variantF.md).

**Coverage:** Does NOT address this failure mode for CHILDREN (children don't see variantF — confirmed). May improve parent dispatch reliability in edge cases, but F.2 shows parent dispatch is already at 16/20 (close to threshold) — marginal value. No expected impact on the 3/20 child-side pseudo-tool-call rate.

**Risk:** LOW (text-only, backward compatible with β-fuse's classification contract as long as the tool-call semantics remain clear).

### F3D — Stop-sequence tuning (add `<tool_call>` / `<|tool_call>` as stop tokens)

**Status:** NOT APPLICABLE to this failure. The model emits the malformed text WITHOUT the `<tool_call>` opening sentinel — it's already truncated. Adding the sentinel as a stop would only help in the Qwen/Hermes-format case (which isn't what's happening). Moreover, using `<tool_call>` as a stop is dangerous because valid structured tool_calls use the same sentinel in some templates. Skip.

### F3E — Retry-on-pseudo-tool-call (soft-error + re-prompt)

If the Gemma-parser gate (F3A′) catches the pseudo-tool-call post-hoc, there's no need for re-prompt retry: the parsed call is directly executed. But if F3A′ is not feasible (e.g., JSON inside the args is malformed enough that parsing fails), we could issue a soft-error message back to the model: "Your last response contained tool-call-shaped text but no structured tool_calls. Please re-emit as a structured tool_calls array."

**Effort:** ~2 hours (new retry hook in agent_loop or equivalent).

**Coverage:** Secondary safety net. Pairs well with F3A′ — parse first, if parse fails then retry.

**Risk:** LOW-MEDIUM. Adds a retry cycle that burns 1 turn. Trial 15 already terminates in 4 turns; adding a retry doesn't hurt. Trial 17 is already at 21 turns (over budget) — a retry would push it further over.

### F3F — Anti-mimicry rewrite of HERMES examples

Same as F3C. See above — does not address the child-side failure (children don't see variantF).

---

## Part 4 — Ranked recommendation

### Primary: F3A′ (relaxed Gemma-parser detection gate + prefix-less pattern)

**Why:**
- Directly addresses the observed failure pattern (100% coverage of trials 15, 16, 17).
- Minimal code change (~5 lines across two files).
- No behavior change for non-Gemma models or correctly-formed Gemma emissions.
- Operates at the CORRECT layer — parsing, not prompting. Prompt-level fixes on a quantized MoE are unreliable; parser-level fixes are deterministic.
- Trial 16's 2667-char Plan content would be recovered as a real `write_file` call, turning a FAIL into a likely PASS.

**Effort estimate:** 30-45 minutes code + unit tests. One focused worker dispatch.

### Secondary: F3E (soft-error retry on pseudo-tool-call)

**Why:** Backstop for cases where F3A′ parses the name/shape but JSON arg parsing fails (e.g., unescaped quotes inside `text:` fields — trial 17 has this risk because multi-line markdown content in Gemma's pipe-quote wrapping can get confused). Independent of F3A′; can layer on top.

**Effort estimate:** ~2 hours.

### Tertiary: F3C (variantF teaching-example rewrite)

**Why:** Not load-bearing for this failure mode (children don't see variantF), but cheap and reduces parent-side mimicry risk marginally. File as a low-priority cleanup, not a ship-gating fix.

**Explicit non-recommendation:**
- F3D (stop-sequence) — inapplicable to half-sentinel form.
- F3B (child-side teaching doc) — higher effort, uncertain on quantized MoE; attempt only if F3A′+F3E underperform in validation.

---

## Part 5 — Validation test plan

### Objective

Confirm F3A′ (with or without F3E) reduces pseudo-tool-call FAIL rate from 3/20 (baseline) to ≤1/20 on the same task mix, with no regression on the other r7.5 failure modes.

### Method

Two conditions, identical in every other dimension to the r7.5 F.2 probe:

- **Condition A (baseline):** current Hermes code (gate & parser unchanged). Re-run to confirm 3/20 rate holds — guards against trial variance.
- **Condition B (with F3A′):** Hermes patched with relaxed Gemma-parser detection gate + prefix-less pattern.

Same 4 task types: T4 (structured), T5 (structured), T6 (long-horizon), T10 (long-horizon). Same `gemma-4-26b-a4b-it-mlx-8bit` child model. Same 20-turn budget, 900s wall-clock per trial. Same parent HERMES.md variantF. **5 trials per task × 4 tasks × 2 conditions = 40 trials total.** 

### Measurement

For each trial, classify the final child state:
- `STRUCTURED_TOOL_CALL` — child emitted at least one structured tool_call in its final turn (target state)
- `PSEUDO_TOOL_CALL_UNRECOVERED` — child emitted Gemma-format text, parser did NOT recover (baseline failure mode)
- `PSEUDO_TOOL_CALL_RECOVERED` — child emitted Gemma-format text, F3A′ parsed & executed it (success path for the fix)
- `OTHER_FAILURE` — truncation / fabrication / budget / other (unchanged modes)

Key statistics:
- Pseudo-tool-call emission rate (STRUCTURED_TOOL_CALL vs any PSEUDO_TOOL_CALL): expect unchanged across conditions (F3A′ is a parser fix, not a generation fix).
- Pseudo-tool-call RECOVERY rate within PSEUDO cases: expect 0% in A, ≥80% in B.
- Overall worker-quality PASS rate: expect +2 to +3 trials in B vs A (only the `PSEUDO_TOOL_CALL_RECOVERED` cases that result in a real write + clean termination will flip PASS).

### Significance test

Primary comparison: recovery rate of pseudo-tool-call emissions. Given small n (expected ~3 PSEUDO per 20 trials per condition = ~6 total per arm if replication holds), use Fisher's exact test on a 2×2 table (recovered vs not recovered by condition).

### Failure modes of the validation itself

- **If the re-run doesn't reproduce pseudo-tool-call at 3/20 in Condition A**, we have too few positives to power the test. Mitigation: expand to 10 trials per task type (40 trials per condition) OR concentrate runs on T10 (2 of 3 observed failures were T10).
- **If F3A′ parses but then mis-executes** (wrong tool name, wrong args), we need a SCOPE-clean assertion to avoid probe-induced state damage. Mitigation: include the standard tripwire md5 checks pre/post each trial.

### Regression checks

- Existing structured tool_call emissions in Condition B must still pass. Run the existing golden-task evaluation suite (`evaluation/golden-tasks.md`) against patched Hermes before Condition B trials begin.
- Existing Gemma Format 1 emissions (with full `<|tool_call>...<tool_call|>`) must still be parseable. Include 2-3 synthetic unit tests in the parser test file with both forms.

### Decision rule

- F3A′ **SHIP** if: (a) Condition B recovery rate ≥ 80% of pseudo-tool-call emissions, (b) golden-tasks regression pass unchanged, (c) no SCOPE tripwire drift in any Condition B trial.
- F3A′ **HOLD** if: recovery rate < 50% (parser pattern underspecified) OR any regression in golden tasks.
- F3A′ **ESCALATE TO F3E** if: recovery rate 50-80% (parser helps but doesn't fully cover; add retry layer).

---

## Part 6 — Open questions / followups for F.3 / r7.6

1. **SOUL.md child-injection verification.** §1.6 asserts SOUL.md does NOT leak into children based on a one-session inspection. If SOUL.md DOES leak (even partially), its "trust the loop" persona line could be actively reinforcing pseudo-tool-call emission. A 2-session audit would settle this.
2. **Chat-template source of the half-sentinel.** The `<|tool_call>` prefix is missing from the emission — is this an oMLX server-side chat-template strip, or is the model itself emitting only the partial closer? Direct inspection of the oMLX-server-side chat template for `gemma-4-26b-a4b-it-mlx-8bit` (on the Parallels host at `10.211.55.2`) would resolve this. Out of scope for this investigation — read-only VM scope only — but worth logging as a followup.
3. **Is Gemma 4 31B dense affected?** The failing trials are all on the 26B MoE. If the 31B dense variant (Hermes's configured default) emits full sentinels correctly, F3A′ is uniquely needed for the MoE. If the 31B also emits half-sentinels occasionally, F3A′ is broader-value.
4. **Why does trial 16's content have the full `path:<|"|>...<|"|>,text:<|"|>...<|"|>` but trial 17 has `content:<|"|>...<|"|>`?** The child is hallucinating the `write_file` parameter schema in trial 17. This is a separate issue — even if F3A′ parses the text, the args would fail schema validation. F3E retry-path is the recovery.

---

## Summary

Root cause: **Gemma 4 26B MoE emits Gemma Format 1 tool calls with the opening `<|tool_call>` sentinel stripped** (likely at the oMLX chat-template layer). Hermes's `GemmaToolCallParser` exists and handles the full sentinel pair correctly — but **both the detection gate at `run_agent.py:8631` and the parser regex at `gemma_parser.py:26-30` require the opening sentinel to match**. The half-sentinel form slips through unmatched.

Top fix: **F3A′ — extend the Gemma-parser detection gate and add a prefix-less regex pattern**. ~5 LOC, ~30-45 min dev + test, 100% coverage of the observed failures, parser-level (deterministic), no prompt-level gambling.

HERMES-variantF.md teaching-example mimicry (H3D) is NOT the primary cause for children, because children never see variantF — confirmed by inspecting child system_prompts. The teaching examples DO use `<tool_call>` wrapping (YES, lines 15-17, 123-125, 128-148 of `variants/hermes/HERMES-variantF.md`) — fixing them (F3C) is cheap cleanup with marginal parent-side benefit, not a ship-gating fix.
