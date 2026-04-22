# ARTIFACT — r7.6 Phase 1-A implementation notes

Unified implementation of inv-3 F3A' (Gemma parser prefix-tolerant fallback)
+ inv-2 G1 (channel-marker content normalizer + synthesis trailer) + inv-2 G2
(VIOLATION:EMPTY_SYNTHESIS check.py verdict). All three are Gemma-MoE chat-
template correctness surgery on the same oMLX+Hermes stack, landed as a
single "Variant H" workstream per the r7.6 synthesis verdict's Insight 1.

## Files created / edited

| Path (local)                                                           | md5                                |
|------------------------------------------------------------------------|-------------------------------------|
| /Users/briantaylor/Projects/AgentFW/probe-variantH-stage.sh            | a565137ec10c376f59ec5a4df4dac0cf   |
| /Users/briantaylor/Projects/AgentFW/probe-variantH-check.py            | 51dd89b6ef750779dc8d75a6a348fd19   |
| /Users/briantaylor/Projects/AgentFW/probe-variantH-wrapper.sh          | 6958c8bbc3567d1d221e04e5706ecee9   |

VM-side patched files (when staged, restored to pre-state after replay-verification):

| Path (VM)                                                                          | canonical md5 (= .probe-r7.6-orig)  | staged md5                          |
|------------------------------------------------------------------------------------|--------------------------------------|--------------------------------------|
| ~/.hermes/hermes-agent/run_agent.py                                                | 94ad8712678df5e96b9f407446edf249     | 1cdbc45f6584f67e2ff78b7e80a239c3    |
| ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py              | 9967c49506ea6a8e9654c9a0191304fe     | de6e6f12b1fc74bfb865bb66aa9111d9    |

Pre-existing backup chains preserved (not overwritten):
- `run_agent.py.probe-d-orig` (pre-r7 baseline)
- `run_agent.py.probe-r7.4-orig` (pre-variantF)
- `run_agent.py.probe-r7.5-orig` (pre-variantG)
- `run_agent.py.probe-r7.6-orig` (NEW — pre-variantH)

## Change 1 — inv-3 F3A' Gemma parser prefix-tolerant fallback

### 1(a) run_agent.py detection gate (~L8633)

**Before** (unique anchor — original line numbers per working file):
```
                    if "<|tool_call>" in _raw or "[Calling tool:" in _raw:
                        _parsers.append("gemma")
```

**After:**
```
                    # r7.6-P1A inv-3 F3A': accept half-sentinel /
                    # prefix-less Gemma Format 1 in addition to the full
                    # sentinel pair. Gemma 4 26B MoE on oMLX emits the
                    # pattern "call:fn{...}<tool_call|>" with the opening
                    # "<|tool_call>" stripped; the parser's prefix-less
                    # fallback recovers these.
                    if ("<|tool_call>" in _raw
                            or "[Calling tool:" in _raw
                            or "<tool_call|>" in _raw
                            or re.search(r"(?m)^call:\w+\{", _raw) is not None):
                        _parsers.append("gemma")
```

`re` is already imported at module-level in run_agent.py on this build; no
import change needed.

### 1(b) environments/tool_call_parsers/gemma_parser.py

Four sub-edits all in this file:

1. **After `PIPE_PATTERN` (~L26-30) — add `PIPE_PATTERN_PREFIXLESS`:**
   ```python
   PIPE_PATTERN_PREFIXLESS = re.compile(
       r"^call:(\w+)\{(.*?)\}<tool_call\|>|"
       r"^call:(\w+)\{(.*)",
       re.DOTALL | re.MULTILINE,
   )
   ```
   **Deviation from inv-3 spec:** inv-3 suggested `(?m)` inline flag. Python
   3.11's re module rejects `(?m)` mid-pattern with alternation ("global flags
   not at the start of the expression"). Moved to the `re.MULTILINE` flag arg.
   Semantically equivalent — the `^` anchors still match post-newline line
   starts.

2. **`has_pipe` detection relaxation (~L67):**
   ```python
   has_pipe = (
       "<|tool_call>" in text
       or "<tool_call|>" in text
       or re.search(r"(?m)^call:\w+\{", text) is not None
   )
   ```
   (Here `(?m)` is fine because it's at the start of a fresh pattern.)

3. **Parse-loop fallback (before `if has_bracket:` ~L100):** if
   `has_pipe and not tool_calls` (primary pattern matched sentinel in the
   string but yielded no tool-calls), try the prefix-less pattern and append
   any extracted calls using the same argument-parsing helpers.

4. **Content-stripping marker scan (~L126):** extend `first_marker` calculation
   to also consider the earliest prefix-less `^call:\w+{` match so the
   content returned to the caller is stripped cleanly.

## Change 2 — inv-2 G1 channel-marker normalizer + synthesis trailer

### Helpers (new, top of run_agent.py before `class AIAgent`)

Added module-level:
```python
import re as _re_r76
_R76_CHANNEL_MARKER_ONLY_RE = _re_r76.compile(
    r"^\s*(?:"
    r"(?:<\|?channel\|?>\s*)"
    r"|(?:thought\s*<\|?channel\|?>\s*)"
    r"|(?:<\|?channel\|?>\s*thought\s*<\|?channel\|?>\s*)"
    r")+\s*$",
    _re_r76.IGNORECASE | _re_r76.DOTALL,
)
def _r76_channel_marker_only(s): ...   # True iff pure channel-marker leakage
_R76_EMPTY_SYNTHESIS_TRAILER = (
    "[child session exited with no synthesis — content was channel-marker "
    "pollution only]"
)
```

### Fallback block edit (run_agent.py ~L8908-8936)

**Before** (`fallback = getattr(self, '_last_content_with_tools', None); if fallback:` block):
back-patched the penultimate tool-calling assistant's `content` to
`"Calling the X tool..."` unconditionally, then set `final_response` from the
stripped `fallback`.

**After:** scan `messages[]` for any assistant with channel-marker-only
content via `_r76_channel_marker_only`. If any found, SKIP the back-patch and
set `final_response = _R76_EMPTY_SYNTHESIS_TRAILER` — leaving `messages[]`
untouched so the probe check.py G2 detector sees the polluted chain directly.
Otherwise, preserve the original back-patch path verbatim.

## Change 3 — probe-variantH-check.py VIOLATION:EMPTY_SYNTHESIS (inv-2 G2)

Derived from probe-variantG-check.py. New logic inserted at two points in
the verdict flow:

1. **After first_assistant / cls extraction**, when `cls is None` AND the
   session lacks a parent-context signal (`--expected-prompt-prefix` not
   provided), try `detect_empty_synthesis(messages)` BEFORE emitting
   `VIOLATION:NO_MARKER`. More specific → wins precedence.

2. **After ROLE_COLLAPSE, before FABRICATION** (per task spec), run the same
   detector for child sessions that did emit a classification (e.g. via text
   marker) but still reached an empty-synthesis terminal.

Detector logic (`detect_empty_synthesis`):
- Rule 1: last assistant's content is empty OR matches the channel-marker
  regex AND final action is NOT productive (delegate_*/write-type) →
  `VIOLATION:EMPTY_SYNTHESIS`.
- Rule 2: last assistant's content matches the Hermes back-patch stub
  regex (`^Calling the .+? tools?\.\.\.$`) AND some earlier assistant has
  channel-marker-only content AND final action is NOT productive →
  `VIOLATION:EMPTY_SYNTHESIS`.
- Otherwise: skip (COMPLIANT or other verdict logic continues).

Parent sessions are skipped by gating on `expected_prefix is not None` for
the "parent context" signal — this flag is only passed by the wrapper when
scoring parents.

Diag fields emitted in the JSON second line:
- `trigger`: `direct_channel_marker_only` or `backpatch_stub_detected`
- `last_content_preview`, `final_action_productive`,
  `polluted_preceding_count`, `polluted_preceding_samples`

**P1-B anchor present:** comment block at the position where P1-B's
fabrication-detector patch will be merged:
```python
# === P1-B FABRICATION:NO_WRITE_TOOL DETECTION WILL BE INSERTED HERE ===
# ... (detailed instructions for the planner's merge step) ...
# === END P1-B INSERTION POINT ===
```
Located just before the existing FABRICATION detection block.

## Change 4 — probe-variantH-stage.sh

Derived structurally from probe-variantG-stage.sh (layered-backup pattern
with md5-verified idempotency). Key design choices:

- Single-script application of both Changes 1(a) and 1(b) and Change 2 in
  one remote `bash -s` heredoc. Python embedded via `python3 - <<PYEOF` for
  multi-line anchored replacement (sed would be brittle for the 18-line
  fallback-block replacement).
- Does NOT invoke variantG or variantF stage scripts. Per operational note
  in the header: variantH patches are toolset-independent and land
  INDEPENDENTLY on whatever current state run_agent.py has. If the operator
  wants β-fuse + turn-0 restriction + variantH together, they stack the
  three stage scripts manually.
- `.probe-r7.6-orig` backups created on first stage, preserved across
  re-stage / unstage cycles. Stacks with existing .probe-d-orig,
  .probe-r7.4-orig, .probe-r7.5-orig backup chains.
- `py_compile` both patched files after stage (catches syntax regressions
  immediately — caught the `(?m)` inline-flag issue on first iteration;
  see Unit-test results below).

Subcommands: `stage` / `unstage` / `status` (+ `verify` alias for `status`).

## Change 5 — probe-variantH-wrapper.sh

Clone of probe-variantG-wrapper.sh with only these changes:
- `SOURCE_PREFIX` default → `probe-r7.6-varH`
- `CHECK_REMOTE` → `/tmp/probe-variantH-check.py`
- `LOCAL_CHECK` → `/Users/briantaylor/Projects/AgentFW/probe-variantH-check.py`
- Header docstring rewritten
- `/tmp/varG-r*` tempfile names renamed to `/tmp/varH-r*`
- Clarified comment on toolset selection to note that variantH patches are
  independent of the β-fuse toolset (variantG's turn-0 hook is the part
  that depends on it)

Tier 1 SIGTERM mitigation (fallback-recovery content-verification +
shrink-retries-on-fallback) preserved verbatim from variantG.

## Unit-test results

### Change 1 (inv-3 F3A') — parser extraction on the 3 pseudo-tool-call trials

Ran on staged code (VM state: variantH STAGED, variantF/G UNSTAGED).
Test harness: loaded child session JSON, found the last assistant message
whose content contains `call:` + `<tool_call|>`, passed that content string
to `GemmaToolCallParser.parse()`, inspected returned `tool_calls`.

| Trial | Child SID                  | Content signature                                | Extracted name  | Args preview                                      |
|-------|----------------------------|--------------------------------------------------|------------------|---------------------------------------------------|
| 15    | 20260419_180656_260680     | `call:read_file{path:<\|"\|>HERMES.md<\|"\|>}<tool_call\|>` | `read_file`     | `{"path": "HERMES.md"}`                          |
| 16    | 20260419_180737_2fae26     | `call:write_file{path:<\|"\|>migrations/pg12.../PLAN.md<\|"\|>,text:<\|"\|># Postgres...` (2667-char content) | `write_file`    | `{"path": "migrations/pg12-to-pg16/PLAN.md", "text": "# Postgres 12 to 16 Zero-Downtime Migration Plan\n\n## 1. Technical Approach..."}` |
| 17    | 20260419_180824_c7bfba     | `call:write_file{content:<\|"\|># Postgres...` (5735-char content) | `write_file`    | `{"content": "# Postgres 12 to 16 Zero-Downtime Migration Plan\n\n## 1. Architecture..."}` — note trial 17 hallucinates the `content:` arg key instead of `path:`+`text:` (per inv-3 §1.2); the parser still extracts it but a downstream schema validation would fail on this call |

**All 3 trials re-parsed successfully with the PIPE_PATTERN_PREFIXLESS
fallback.** Trial 17's hallucinated-schema issue is a known secondary problem
(inv-3 §Part 6 Q4) — outside the scope of the parser fix; F3E retry path
would be needed to recover it, but that's not r7.6-P1A's scope.

### Change 2 (inv-2 G1) — channel-marker helper on the 10-case test suite

Ran directly against `_r76_channel_marker_only` extracted from the staged
run_agent.py (via `exec()` on the helper block).

| Input                                         | Expected | Got   | Status |
|-----------------------------------------------|----------|-------|--------|
| `""`                                          | True     | True  | OK     |
| `"<channel\|>"`                                | True     | True  | OK     |
| `"thought\n<channel\|>"`                       | True     | True  | OK     |
| `"<\|channel>thought\n<channel\|>"`             | True     | True  | OK     |
| `"<channel\|>thought\n<channel\|>"`             | True     | True  | OK     |
| `"Calling the read_file tool..."`             | False    | False | OK     |
| `"Some real prose here"`                      | False    | False | OK     |
| `"   "`  (whitespace)                          | True     | True  | OK     |
| `"<channel\|> <channel\|> thought <channel\|>"` | True     | True  | OK     |
| `"<channel\|>\nreal text"`                     | False    | False | OK     |

**10/10 pass.** Detector is specific: flags pure-pollution without
false-positiving on prose-with-marker or real content.

### Change 3 (inv-2 G2) — check.py replay on the 8 reframed trials

Ran `python3 /tmp/probe-variantH-check.py <session_path>` (no
`--expected-prompt-prefix` since these are child sessions) on each:

| Trial | Child SID                  | Verdict                        | Trigger                 |
|-------|----------------------------|--------------------------------|-------------------------|
| 6     | 20260419_175731_46919a     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (10 polluted preceding) |
| 7     | 20260419_175833_46abf5     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (11 polluted preceding) |
| 9     | 20260419_180153_6e9c84     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (2 polluted preceding)  |
| 10    | 20260419_180417_3748c0     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (3 polluted preceding)  |
| 11    | 20260419_180511_79a472     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (2 polluted preceding)  |
| 12    | 20260419_180532_5b455e     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (8 polluted preceding)  |
| 13    | 20260419_180604_d35ad2     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (2 polluted preceding)  |
| 14    | 20260419_180630_333820     | VIOLATION:EMPTY_SYNTHESIS      | backpatch_stub_detected (8 polluted preceding)  |

**8/8 reframed trials now emit VIOLATION:EMPTY_SYNTHESIS.**

### Regression checks (non-target sessions should NOT fire EMPTY_SYNTHESIS)

- **3 pseudo-tool-call trials (15, 16, 17)** replayed against check.py:
  all emit `VIOLATION:NO_MARKER` (not EMPTY_SYNTHESIS) — correct; their last
  assistant has real prose content (the Gemma Format 1 pseudo-tool-call
  text), not channel-marker pollution.
- **2 sample parent sessions** (20260419_175717_2dc2aa,
  20260419_180651_6426f2) replayed without --expected-prompt-prefix: both
  emit `COMPLIANT`. Parents structurally don't match the child-session
  empty-synthesis pattern.

No regressions observed.

## Placeholder anchor for P1-B

In `probe-variantH-check.py`, at the position between the EMPTY_SYNTHESIS
detection block and the existing FABRICATION block:

```
    # === P1-B FABRICATION:NO_WRITE_TOOL DETECTION WILL BE INSERTED HERE ===
    # P1-B is producing a unified-diff patch merging inv-4 F4A fabrication-
    # detector logic (completion-claim phrase + zero write-type tool calls
    # ⇒ VIOLATION:FABRICATION:NO_WRITE_TOOL). Do not implement here; the
    # planner will merge P1-B's patch at this exact anchor location.
    # === END P1-B INSERTION POINT ===
```

Confirmed present via `grep -n "P1-B"` on the local file.

## VM state at return

Staged variantH for replay-testing, then UNSTAGED. Final VM state:

```
HERMES.md        0780c232a6cb52e13e432261f0d68ad9   (canonical — expected)
SKILL.md         fb1a5a5208a6cf2fcb8252aac10397eb   (canonical — expected fb1a5a52...)
jira-briefing.sh a1dce6e989527686124d0860830627c9   (canonical — expected a1dce6e9...)
run_agent.py     94ad8712678df5e96b9f407446edf249   (= pre-variantH; variantH UNSTAGED)
gemma_parser.py  9967c49506ea6a8e9654c9a0191304fe   (= pre-variantH; variantH UNSTAGED)
```

VariantG: UNSTAGED (0 `_resolve_tools_for_turn_r75a` references).
VariantF: UNSTAGED (0 `delegate_worker_v2` references, no tool file present).
VariantD: not touched in this scope.

All tripwires canonical. VM is clean.

## Deviations from inv-3 / inv-2 specs

1. **PIPE_PATTERN_PREFIXLESS regex flag form.** inv-3 §Part 3 F3A' §step 2
   suggested inline `(?m)` flag. Python 3.11+ rejects that placement with
   alternation; moved to the `re.MULTILINE` kwarg. Semantically identical,
   no behavioral difference.

2. **Channel-marker regex scope.** inv-2 §Part 6 Q1 flagged the open
   question of which Harmony-format variants to match. Chose to match the
   3 observed variants plus empty-string (which is how the raw content
   field manifests when the chat-template layer strips to nothing).
   Specifically NOT matching: `<|start|>`, `<|channel|>` with content, or
   other Harmony tokens beyond the observed subset. Widening can be added
   if future failures surface new variants.

3. **EMPTY_SYNTHESIS detector also runs when cls is None** (not only when
   cls exists). This is broader than the task spec's "alongside existing
   verdicts" wording. Rationale: all 8 reframed trials in the replay set
   have `cls is None` (they're children without a TASK CLASS marker), so
   gating EMPTY_SYNTHESIS to run ONLY after cls-extraction would miss
   every one of them. The cls==None path now routes to EMPTY_SYNTHESIS
   BEFORE NO_MARKER; if EMPTY_SYNTHESIS doesn't fire, falls through to
   NO_MARKER as before. Parent sessions are protected by the
   `--expected-prompt-prefix` gate (wrappers always pass this).

4. **Stage script does not auto-invoke variantF/variantG stage scripts.**
   Per scope rationale in header comment: variantH's patches are toolset-
   independent; operators composing a full β-fuse+turn-0+variantH stack
   run the three stage scripts manually in order. Cleaner separation of
   concerns and easier partial staging for debugging.

No deviations required a decision outside the scope of this worker. All
three inv specs' core requirements are met.
