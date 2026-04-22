---
type: r7.8 P1b — Gemma parser research + candidate interventions
date: 2026-04-21
---
# r7.8 P1b — Gemma parser research

## Parser architecture (current state, r7.7 baseline)

- **file:** `~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py`
- **md5 (r7.7 baseline, LIVE; matches `.probe-r7.6-orig` backup):** `9967c49506ea6a8e9654c9a0191304fe`
- **line-count:** 137
- **current staging state:** variantH NOT staged. `PIPE_PATTERN_PREFIXLESS` count=0. Treat live file as r7.7-baseline; variantH patches in `probe-variantH-stage.sh` are proposed-not-installed.
- **Entry point:** single `GemmaToolCallParser.parse(self, text)` at lines ~59-119. Registered under `"gemma"` via decorator (line 21) in `__init__.py`. Called only from `run_agent.py:8624-8650`, gated at `run_agent.py:8631` (`"<|tool_call>" in _raw or "[Calling tool:" in _raw`).
- **Helpers:** `_clean_pipe_quotes` (39-41) strips `<|"|>`; `_parse_pipe_args` (43-63) JSON → regex-tier fallbacks; `PIPE_PATTERN` (24-28) full-sentinel; `BRACKET_PATTERN` (30-34) `[Calling tool: NAME({...})]`.

### Happy-path trace

1. Caller in `run_agent.py:8624-8650` has `assistant_message` with no structured `tool_calls` but non-empty `content`. It picks parsers by string-match of `<|tool_call>` or `[Calling tool:` and calls `parser.parse(_raw)`.
2. `parse()` line 65 sets `has_pipe`/`has_bracket`. If neither, returns `(text, None)` unchanged — no scrubbing on this branch.
3. If `has_pipe`: iterate `PIPE_PATTERN.finditer`. Extract name, args via `_parse_pipe_args` (JSON → key:'val' regex → key:val regex). Strip `<|"|>`. Build `ChatCompletionMessageToolCall`.
4. If `has_bracket`: iterate `BRACKET_PATTERN.finditer`. Parse JSON args with fallback `+"}"` or wrap as `{"command": ...}`.
5. If no tool_calls accumulated, return `(text, None)`.
6. Compute `first_marker` = earliest index of `<|tool_call>` or `[Calling tool:` (lines 106-110). Slice `content = text[:first_marker].strip()`.
7. Apply ONE content sanitizer: `content = re.sub(r"<\|channel>thought\n<channel\|>", "", content).strip()` (line 113). **Only channel-marker scrubber in the parser.**
8. Return `(content or None, tool_calls)`.

### variantH patch summary (proposed, not live)

From `/Users/briantaylor/Projects/AgentFW/probe-variantH-stage.sh`:

- **Change 1(a)** — `run_agent.py:~8631` detection-gate relaxation: accept `<tool_call|>` closer OR bare `re.search(r"(?m)^call:\w+\{", _raw)` prefix-less form, not just `<|tool_call>` opening sentinel.
- **Change 1(b).1** — `gemma_parser.py:~26-30` add `PIPE_PATTERN_PREFIXLESS` regex.
- **Change 1(b).2** — `gemma_parser.py:~65` relax `has_pipe` to match the same three variants as the detection gate.
- **Change 1(b).3** — `gemma_parser.py:~100` (before `if has_bracket:`) add a secondary `finditer` loop over `PIPE_PATTERN_PREFIXLESS` when the primary yielded no matches.
- **Change 1(b).4** — `gemma_parser.py:~106-110` extend the `first_marker` scan to include the prefix-less `call:` position.
- **Change 2** — `run_agent.py:~8908-8936` helpers `_r76_channel_marker_only` + `_R76_EMPTY_SYNTHESIS_TRAILER`; in the empty-follow-up fallback, when ANY assistant in the chain has channel-marker-only content, skip the back-patch and set `final_response` to a diagnostic trailer instead of the misleading "Calling the X tool..." stub.

Change 1 targets the **pseudo-tool-call** pathology (r7.6 inv-3). Change 2 targets the **empty-synthesis masking** pathology (r7.6 inv-2). Both are infrastructural fixes layered on top of a model whose surface output is partly unparseable.

## Remaining pathologies (from r7.7 FAIL evidence)

Drawn from the three session probes cited in the worker inputs plus the r7.6 artifacts.

### P1 — `<channel|>` marker fragments persist in content after parse

- Line 113 sanitizer is exact-match re.sub for literal `<|channel>thought\n<channel\|>` only. **One variant of six** observed (`ARTIFACT-r7.6-P1C-fix2-impl.md` §Change 1: `<channel|>`, `<|channel|>`, `<tool_call|>`, `<start|>/<end|>/<message|>/<return|>`, `thought\n<channel|>`, `analysis\n<channel|>`).
- Evidence: Arm G T6-run3 — 21 channel-fragment turns. Arm F T6-run2 — 14 turns of `search_files` with `thought\n<channel|>` fragments.
- Scrubber runs only when tool_calls were recovered; pure channel pollution (no markup) hits `return (text, None)` at line 71 unchanged. **Dominant pathology.**

### P2 — malformed `[]<tool_call|>` tail survives

- Arm F T6-run5 (`20260420_204954_688f43`): final content `[]<tool_call|>`.
- `has_pipe = False` (no opening sentinel) → early return at line 71, no scrub.
- Even with variantH staged: `PIPE_PATTERN_PREFIXLESS` requires `^call:\w+\{` — `[]<tool_call|>` lacks that, so text still returns unchanged.

### P3 — empty content with channel-fragment-only turns

- Arm G T6-run3: 21 consecutive channel-marker-only turns.
- Parser bypasses entirely (no sentinels), returns `(text, None)`. Pollution flows downstream.
- **Key:** parser is invisible to this pathology — the parse function is never meaningfully invoked.

### P4 — truncation mid-turn leaves unfinished `thought\n...`

- Arm F T6-run2: `thought\n<channel|>` fragments across 14 turns.
- `PIPE_PATTERN` has truncation-recovery alt (`<|tool_call>call:(\w+)\{(.*)`), but only fires when opening sentinel is present. oMLX strips it — branch is dead.

### P5 — degenerate loop patterns

- Cross-turn state, not a parser-local problem. Judge thrash detector (`ARTIFACT-r7.6-P1C-fix2-impl.md` §Change 4) handles this. **Deprioritized** for r7.8 parser work.

## Candidate interventions

Four candidates, ranked below in § "Ranking".

### C1: Universal channel-marker scrubber at parse-return (highest generalization)

- **Target:** `environments/tool_call_parsers/gemma_parser.py:113` (replace the narrow re.sub) AND `gemma_parser.py:71` (add scrub on the no-tool-call path so pure channel pollution is also cleaned).
- **Change:**
  ```python
  # Replace gemma_parser.py:113 single-variant sub with comprehensive scrub.
  # Also apply on the early-return path so pure channel pollution is cleaned
  # even when no tool_calls are recovered.

  _GEMMA_CHANNEL_MARKER_RE = re.compile(
      r"(?:"
      r"<\|?(?:channel|tool_call|start|end|message|return)\|?>"
      r"|(?:thought|analysis)\s*<\|?channel\|?>"
      r")",
      re.IGNORECASE,
  )

  def _scrub_channel_markers(self, s):
      """Strip Harmony/Gemma channel sentinel leakage from content."""
      if not s:
          return s
      scrubbed = _GEMMA_CHANNEL_MARKER_RE.sub("", s)
      # Collapse resulting empty runs of whitespace; preserve paragraph breaks.
      scrubbed = re.sub(r"\n{3,}", "\n\n", scrubbed)
      return scrubbed.strip()
  ```
  Call sites:
  1. Line 71 (before `return text, None` on the no-markup path): `return self._scrub_channel_markers(text) or None, None`.
  2. Line 113 (replace the exact-match `re.sub`): `content = self._scrub_channel_markers(content)`.

- **Generalization:** This scrubber is MODEL-agnostic. Any downstream system receiving Gemma parser output benefits — worker replies, judge reads, human-facing CLI output, session log JSON. It does not depend on task type, HERMES.md variant, prompt, or the specific classification pipeline. It simply says "channel sentinels are never valid visible content for this model family; strip them at the boundary."

- **Rollback:** `cp gemma_parser.py gemma_parser.py.probe-r7.8-orig` before patch. The unstage script restores byte-identical content. Md5-pin against `9967c49506ea6a8e9654c9a0191304fe` before staging to detect drift from other variants.

- **Unit tests (no probe run):**
  ```python
  # Positive: each variant alone
  assert parser._scrub_channel_markers("<channel|>") == ""
  assert parser._scrub_channel_markers("<|channel|>") == ""
  assert parser._scrub_channel_markers("thought\n<channel|>") == ""
  assert parser._scrub_channel_markers("<start|><end|>") == ""
  # Positive: pollution around real content
  assert parser._scrub_channel_markers("<channel|>Hello<channel|>") == "Hello"
  # Negative: don't eat legit prose
  assert parser._scrub_channel_markers("See channel 4") == "See channel 4"
  # Boundary: 21-turn pollution flattens to empty
  assert parser._scrub_channel_markers("<channel|>thought\n<channel|>" * 21) == ""
  # Full parse path: a realistic FAIL example
  content, calls = parser.parse("<channel|>thought\n<channel|>")
  assert content is None
  assert calls is None
  ```
  Run with `python3 -c "from environments.tool_call_parsers import get_parser; ..."` on the VM. Completes in <1s, vets the scrubber without invoking oMLX or running the probe harness.

### C2: Channel-only content detection with explicit empty-content emission

- **Target:** `environments/tool_call_parsers/gemma_parser.py:71` (the no-markup early return) and a new emission contract.
- **Change:** Build on C1. After scrubbing, if the result is empty but the ORIGINAL input was non-empty AND matched `_GEMMA_CHANNEL_MARKER_RE` at least once, return a sentinel tuple `(None, None)` with an optional side-channel log (logger.warning). The calling code in `run_agent.py:8639` already treats `_parsed_content is None` as "clear content"; the warning signals to upstream diagnostics that this was a pollution-only turn.
  ```python
  def parse(self, text):
      # ... existing has_pipe/has_bracket setup ...
      if not has_pipe and not has_bracket:
          scrubbed = self._scrub_channel_markers(text)
          if scrubbed != text.strip():
              logger.warning(
                  "gemma_parser: channel-marker-only content detected "
                  "(input_len=%d, scrubbed_len=%d)", len(text), len(scrubbed),
              )
          return (scrubbed or None, None)
      # ... rest unchanged ...
  ```

- **Generalization:** This extends the parser's responsibility from "recover tool_calls" to also "normalize visible content." The emission contract — `(None, None)` means "assistant turn is semantically empty" — is general. Any downstream code that looks at content (session-log writer, CLI render, HERMES judge prompts) gets a consistent signal, not variable-length junk.

- **Rollback:** Same pattern — `.probe-r7.8-orig` backup. The logger.warning is informational and can be muted via log-level config if it proves noisy.

- **Unit tests:**
  ```python
  content, calls = parser.parse("<channel|>thought\n<channel|>")
  assert content is None and calls is None
  # Real content passes through untouched
  content, calls = parser.parse("Here is the answer: 42.")
  assert content == "Here is the answer: 42." and calls is None
  # Mixed: partially polluted
  content, calls = parser.parse("<channel|>Real content<channel|>")
  assert content == "Real content" and calls is None
  ```

### C3: Malformed-tail recovery for `[]<tool_call|>` / `<tool_call|>`-only

- **Target:** `environments/tool_call_parsers/gemma_parser.py:71` — after the no-markup check, before returning.
- **Change:** Detect tail-only closer patterns that indicate a truncated tool_call emission where the name+args never emerged. Strip them and fall through to empty content rather than preserving the garbage.
  ```python
  _GEMMA_TAIL_ONLY_RE = re.compile(
      r"^\s*(?:\[\s*\])?\s*<tool_call\|>\s*$",
      re.DOTALL,
  )
  # After the has_pipe/has_bracket check:
  if not has_pipe and not has_bracket:
      if _GEMMA_TAIL_ONLY_RE.match(text):
          logger.warning("gemma_parser: tail-only closer detected, discarding")
          return None, None
      # ... C1 scrub path ...
  ```

- **Generalization:** This is narrower than C1/C2 — it targets a specific malformed emission pattern (`[]<tool_call|>`, `<tool_call|>` by itself). BUT it generalizes in the sense that it handles truncation-artifact shapes that no caller can reasonably want to display or feed back to the model. The specific regex could be extended to cover other observed tail-only closers. FLAG: this IS somewhat task/model-specific; the pattern appears only on Gemma 4 MoE. Keep it in the Gemma parser only — do not lift to a shared module. Task-generality is medium, not high.

- **Rollback:** Same `.probe-r7.8-orig` pattern. Regex is narrowly anchored (`^...$`) so it cannot fire on prose containing the closer as a substring.

- **Unit tests:**
  ```python
  content, calls = parser.parse("[]<tool_call|>")
  assert content is None and calls is None
  content, calls = parser.parse("<tool_call|>")
  assert content is None and calls is None
  # Don't fire on legit content with the closer embedded
  content, calls = parser.parse("Some prose <tool_call|> more prose")
  # Current behavior: has_pipe=False (no opening sentinel), returns text unchanged.
  # After C1: scrubbed to "Some prose  more prose".
  ```

### C4: Prefix-less tool_call recovery (variantH Change 1, re-propose)

- **Target:** `gemma_parser.py:24-28` (add `PIPE_PATTERN_PREFIXLESS`), `gemma_parser.py:65` (relax `has_pipe`), `gemma_parser.py:100` (add fallback finditer loop), `gemma_parser.py:106-110` (extend `first_marker`). Plus `run_agent.py:8631` detection-gate relaxation.
- **Change:** Identical to variantH Change 1 as specified in `probe-variantH-stage.sh:312-452`. Two regex additions, one detection-gate relaxation, one marker-scan extension. Full code in the stage script already.
- **Generalization:** HIGH for Gemma MoE users. The observed behavior — oMLX chat-template stripping the opening `<|tool_call>` sentinel — is an environmental property of the oMLX-gemma-4-26b-a4b-it-mlx-8bit binding, not a task property. Any task that uses this model hits this pathology; the fix is task-agnostic.
- **Rollback:** variantH already defines `.probe-r7.6-orig` backups. For r7.8 we should add a layered `.probe-r7.8-orig` on top: bump the backup suffix. Stage script refactor trivial.
- **Unit tests:**
  ```python
  # Prefix-less form is now recovered
  text = 'call:read_file{path:<|"|>HERMES.md<|"|>}<tool_call|>'
  content, calls = parser.parse(text)
  assert calls and calls[0].function.name == "read_file"
  assert json.loads(calls[0].function.arguments) == {"path": "HERMES.md"}
  # Full-sentinel form still works (regression)
  text = '<|tool_call>call:read_file{path:<|"|>HERMES.md<|"|>}<tool_call|>'
  content, calls = parser.parse(text)
  assert calls and calls[0].function.name == "read_file"
  # Truncated prefix-less form (no closer)
  text = 'call:write_file{path:<|"|>plan.md<|"|>,text:<|"|>content...'
  content, calls = parser.parse(text)
  assert calls and calls[0].function.name == "write_file"
  ```
  r7.6-inv-3 already documents three real-session test vectors (trials 15, 16, 17) — include them verbatim as regression cases.

## Ranking

Ranking is by (impact × generalization × rollback-safety), with secondary weight on r7.7 evidence coverage.

1. **C1 — Universal channel-marker scrubber.** Highest impact and highest generalization. Directly addresses P1, P3, and partially P4 (any `thought\n<channel|>` truncation gets scrubbed). Covers all six channel-sentinel variants from `ARTIFACT-r7.6-P1C-fix2-impl.md` Change 1 — far broader than the current line-113 single-variant sub. Generalizes across every task type because it operates on the raw model-output boundary. Rollback is trivial (single-file backup). The ONLY risk is false positives on prose literally containing `<channel|>` substrings, mitigated by the IGNORECASE + word-boundary-adjacent anchoring.

2. **C4 — Prefix-less tool_call recovery.** High impact and high generalization for Gemma 4 MoE. Already scoped, prototyped, and lint-tested in variantH. The r7.6 inv-3 evidence is strong (3/3 FAIL trials recovered in the bench). The reason this ranks below C1: C1 fixes a dominant ongoing pathology (channel pollution in EVERY FAIL session per Arm G T6-run3, Arm F T6-run2 evidence), whereas C4 fixes a specific-but-lower-frequency pattern (3/20 trials in r7.5 baseline). Impact × frequency favors C1. Still, layer C4 alongside C1 — they compose cleanly.

3. **C2 — Channel-only content detection with explicit empty-content emission.** Depends on C1 (uses the same scrubber). Adds the diagnostic emission contract which helps downstream judges and CLI. Without C1 it cannot fire. With C1 it's a cheap extension (one log line + one conditional). Rank 3 because the value-add over C1 alone is incremental — mostly diagnostic, not behavioral.

4. **C3 — Malformed-tail recovery.** Narrowest scope, Gemma-MoE-specific, lowest frequency in the sample. Flagged as task-borderline (could be model-specific); keep in the Gemma parser but do not promote to a shared utility. Ship only if C1 leaves observable `[]<tool_call|>` tails in session logs post-deployment.

### Composition strategy for r7.8

- Stage C1 + C4 together as the primary r7.8 parser patch. C1 gives broad channel-pollution cleanup; C4 gives Gemma-MoE tool-call recovery.
- Add C2 as a tiny addendum — one logger.warning, no behavior change beyond C1.
- Gate C3 on post-deployment evidence: if r7.8 probe shows residual tail-only emissions, add C3 in a minor patch.

### Generalization summary

- **C1:** general across all tasks and all channel-polluted outputs. Highest generalization score.
- **C2:** general (extends C1's emission contract).
- **C3:** model-family-specific (Gemma MoE tail patterns). Task-general within that model family; not applicable to others. Flagged.
- **C4:** model-family-specific (Gemma MoE prefix-stripping). Task-general within that model family; not applicable to others. Documented as operationally needed for the probe's target model.

### Unit-test strategy (composite)

Write a single `test_gemma_parser_r78.py` with the union of the test vectors above: 12 assertions covering the six channel variants (C1), the tail-only patterns (C3), the prefix-less recovery (C4), and the empty-content contract (C2). Run with `python3 -m pytest` or plain `python3 -c "exec(open(...))"`. Executes in <1s on the VM. Zero probe-harness dependency. Must pass before staging any patch — this is the r7.8 P1b equivalent of the r7.6-P1C rev-2 calibration gate (except at the unit-test layer instead of the judge layer).

### Rollback pattern (all candidates)

```bash
# Pre-stage
ssh ubuntu-vm "cp ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py \
               ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py.probe-r7.8-orig"
ssh ubuntu-vm "md5sum ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py.probe-r7.8-orig"
# Expect: 9967c49506ea6a8e9654c9a0191304fe

# Apply patch (Python script in stage wrapper)

# Post-stage sanity
ssh ubuntu-vm "python3 -m py_compile ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py"
ssh ubuntu-vm "python3 -c 'from environments.tool_call_parsers import get_parser; p = get_parser(\"gemma\"); print(p.parse(\"<channel|>thought\\n<channel|>\"))'"
# Expect: (None, None)

# Unstage (if verdict reject)
ssh ubuntu-vm "cp ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py.probe-r7.8-orig \
               ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py"
ssh ubuntu-vm "md5sum ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py"
# Expect: 9967c49506ea6a8e9654c9a0191304fe (matches baseline)
```

## Cross-cutting observations

- **Parser is invoked as FALLBACK only** (run_agent.py:8624-8650, gated on no structured tool_calls). Fixes affect only the pathological path; they cannot regress well-formed structured-tool_call sessions. Blast radius is bounded.
- **Line-113 channel scrubber is under-scoped ~6x** (one variant out of six). Expanding it is the single most leveraged change.
- **variantH Change 2 operates at run_agent.py, not parser.** C2 here is complementary — parser emits `(None, None)` + warning; run_agent decides trailer behavior. Compose without conflict.
- **Parser has no cross-turn state.** P5 (degenerate loops) belongs in run_agent.py or the judge.
- **Line 113's `re.sub` lacks `re.IGNORECASE`.** C1 closes this gap.

## Summary recommendation

For r7.8 P1b, stage **C1 + C4** as a unified patch; add **C2** as a one-line addendum. Defer **C3** pending r7.8 evidence. Verify with the 12-assertion unit test on the VM before enabling any probe run. Layer `.probe-r7.8-orig` backups over `.probe-r7.6-orig`. Expected outcome: channel-pollution turns produce clean empty-content rather than multi-kilobyte `<channel|>` transcripts; Gemma Format 1 pseudo-tool-calls (inv-3 trials 15/16/17) are recovered into structured `tool_calls`. Blast radius stays inside `gemma_parser.py` plus a two-line run_agent.py gate edit — no HERMES.md, no non-Gemma parser, no classification-pipeline impact.
