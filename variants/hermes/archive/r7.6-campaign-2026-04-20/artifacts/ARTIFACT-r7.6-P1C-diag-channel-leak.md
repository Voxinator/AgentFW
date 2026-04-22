[TASK CLASS: structured]
Justification: Read-only diagnostic, multi-source evidence, design-only fix recommendations. Single artifact.

# ARTIFACT — r7.6-P1C diagnostic: channel-marker leakage in Arm A trial 11

**Scope:** Root-cause the `thought\n<channel|>` final-content observed in Arm A trial 11 (T6 run1, parent `20260419_203110_ce514c`, child `20260419_203116_b3e1c1`). Read-only. No runtime changes. Did not disturb the running Arm B probe (`pgrep -af hermes` confirmed `probe-r7.6-armB-T5-moe-run5` active mid-investigation; no overlap).

---

## 1. Root cause (one paragraph)

The Gemma 4 26B MoE on oMLX (`gemma-4-26B-A4B-it-MLX-8bit`) periodically emits **Harmony-format channel-header fragments** (`<channel|>` and `thought\n<channel|>`) as the entire visible `content` of assistant turns. The tool-call path is structurally fine — every affected turn parses a proper `tool_calls` array — but the visible content stream never produces natural language. The target session accumulates 15/20 such polluted assistant turns; its final assistant content is literally `thought\n<channel|>` (18 chars), which trips the judge's `< 20 chars` COMPLETION gate. The mechanism is an **oMLX-side chat-template regression for this specific MoE variant**: internal Harmony reasoning-channel sentinels that should be consumed by the decoder bleed into the visible-content stream. This is **not Hermes/Harmony format mismatch at the protocol level** (Gemma models do not "natively" use Harmony; `<|channel|>` is the gpt-oss reasoning-header token and its presence here is a stray-token-leakage artifact of the 8-bit MoE's chat template, not a mis-matched format on Hermes's side). Hermes has no Harmony-aware content normalizer; the raw content is persisted verbatim into the session JSON, which is what the judge reads. Citations: child session `messages[*].content` values in `/home/parallels/.hermes/sessions/session_20260419_203116_b3e1c1.json`; pre-existing diagnosis in `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-inv-2-sigterm-truncation.md` (H2F root cause, §1.3) and `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-P1A-impl-notes.md` (variantH mechanical fix, Change 2).

**Is Harmony valid for this model?** No. Harmony (`<|start|>role<|channel|>analysis<|message|>...`) is the gpt-oss-20B/120B chat protocol. Gemma uses a different chat template (`<start_of_turn>role\ncontent<end_of_turn>`). What we are seeing is the MLX 8-bit quant of the 26B A4B MoE producing the **string `<channel|>`** as visible output — it is not performing Harmony format; it is leaking a token fragment that the model's training data contained. No HERMES.md/variant configures Harmony. The marker is a pollution signature, not a protocol.

---

## 2. Evidence

### 2.1 Verbatim last 3 assistant messages from child `20260419_203116_b3e1c1`

All three are the final stretch (msgs 18, 19, 20 of the 20 assistant turns, truncated at 500 chars — none exceed that anyway):

| # | content (verbatim) | tool_calls[0].name | tool_calls[0].args (preview) |
|---|---|---|---|
| 18 | `thought\n<channel|>` | `search_files` | `{"file_glob": "hermes/**/*.py", "pattern": "def", "target": "content"}` |
| 19 | `<channel|>` | `search_files` | `{"file_glob": "hermes/**/*", "pattern": "*", "target": "files"}` |
| 20 (final) | `thought\n<channel|>` | `search_files` | `{"file_glob": "hermes/**/*", "pattern": "*", "target": "files"}` |

The message is **not truncated** in the wire-level sense — the tool_calls array is intact, arguments are valid JSON, the session JSON is well-formed, the session terminates cleanly with `exit_reason=completed`. The "truncation" is purely inside the visible-content channel.

### 2.2 Full assistant-content distribution across the target child's 20 assistant turns

Compact array from the session JSON:

```
["", "", "thought\n<channel|>", "thought\n<channel|>", "<channel|>", "",
 "thought\n<channel|>", "<channel|>", "thought\n<channel|>", "<channel|>",
 "thought\n<channel|>", "<channel|>", "thought\n<channel|>", "<channel|>",
 "thought\n<channel|>", "<channel|>", "", "thought\n<channel|>", "<channel|>",
 "thought\n<channel|>"]
```

- 4 turns: `""` (empty, tool-call only)
- 9 turns: `"thought\n<channel|>"` (18 chars)
- 7 turns: `"<channel|>"` (10 chars)
- **0 turns produced any natural-language prose.** The child ran structured `search_files` calls on bogus patterns (`hermes/**/*`) for all 20 turns without ever synthesizing, then hit the turn cap.

### 2.3 Scan across all 20 Arm A children (`[total_asst, channel-leak_asst]` per SID)

| Global N | SID | Task | Tot asst | Leaky asst | Judge COMPLETION | Last content (trunc 80) |
|---|---|---|---|---|---|---|
| 1 | 20260419_202058_1ba6de | T4 | 2 | 0 | PASS | `The worker was unable to find the files you specified...` |
| 2 | 20260419_202132_50f846 | T4 | 2 | 0 | PASS | `The worker was unable to find the files you specified...` |
| 3 | 20260419_202238_5347d7 | T4 | 2 | 0 | PASS | `The worker was unable to find the files you specified...` |
| 4 | 20260419_202309_a7614f | T4 | 2 | 0 | PASS | `I attempted to dispatch a worker to perform the refactor...` |
| 5 | 20260419_202341_b5c773 | T4 | 2 | 0 | PASS | `The worker couldn't find the files you specified...` |
| 6 | 20260419_202413_7754a1 | T5 | 3 | 0 | PASS | `The investigation is complete. The intermittent stale data...` |
| 7 | 20260419_202603_0a9b34 | T5 | 10 | 8 | PASS | `<channel|>I've attempted to investigate the stale data...` |
| 8 | 20260419_202706_b5b0d7 | T5 | 16 | 14 | PASS | `thought\n<channel|>I've completed my investigation into...` |
| 9 | 20260419_202831_b11dcf | T5 | 17 | 13 | PASS | `<channel|>I've attempted to locate the source code...` |
| 10 | 20260419_203003_57b4e2 | T5 | 2 | 0 | PASS | `I've tried to locate the dashboard at /media/psf/...` |
| **11** | **20260419_203116_b3e1c1** | **T6** | **20** | **16** | **FAIL** | `thought\n<channel|>` **← only pure-marker final** |
| 12 | 20260419_203613_d66559 | T6 | 12 | 9 | FAIL* | `thought\n<channel|>` |
| 13 | 20260419_203833_c7b356 | T6 | 6 | 5 | PASS | `<channel|>It appears the worker is successfully performing...` |
| 14 | 20260419_204008_f427ed | T6 | 6 | 3 | FAIL* | `<channel|>The current file list suggests this is a Python-based...` |
| 15 | 20260419_204143_1337e5 | T6 | 10 | 8 | FAIL* | `<channel|>It seems I'm hitting a recurring issue...` |
| 16 | 20260419_204636_4ddafd | T10 | 2 | 0 | PASS | `I have completed Phase 1 of the migration plan...` |
| 17 | 20260419_204816_751167 | T10 | 7 | 5 | FAIL* | `<channel|>The previous attempts to create the migration plan...` |
| 18 | 20260419_205339_9534b8 | T10 | 9 | 5 | PASS | `The migration plan for moving your 80GB Postgres 12 database...` |
| 19 | 20260419_205531_e43f0d | T10 | 10 | 7 | PASS | `thought\n<channel|>The migration project has been initialized...` |
| 20 | 20260419_205805_806204 | T10 | 8 | 6 | PASS | `<channel|>This is a high-stakes migration. Given the 80GB...` |

*FAIL* in this table reflects what the judge actually caught — trials 12/14/15/17/20 all show `"last assistant content too short: 'thought\\n<channel|>'"` style evidence verbatim in their judge verdict JSON.

**Totals:**
- Children with any channel-marker leakage in assistant content: **13/20 (65%)**.
- Children whose LAST assistant content was exclusively pure marker (what trips the judge): **trials 11, 12, 14, 15, 17, 20 = 6/20 (30%)**. (Trial 14 matches `<channel|>` + very short Python-project prose; the judge's `< 20 chars` gate tripped on the leading pure-marker substring before the prose — judge evidence quotes `'thought\\n<channel|>'` so the judge is reading the fragment as the whole content even though prose exists. Investigate further if needed.)
- Trials with leakage that COMPLETION **missed** because prose followed the marker: trials 7, 8, 9, 13, 18, 19 = **6/20 (30%)** — COMPLETION=PASS despite polluted content chains.

### 2.4 Relation to mid-turn corruption vs final-turn corruption

The target session's pattern (pure marker on **every** post-msg5 turn) is systematic, not a "mid-stream interruption." There is no progressive corruption; the very first assistant turns 1–2 are empty (normal tool-call turns), and from msg 3 onward the model emits the marker on every content-producing turn. The final turn is not worse than mid-session turns — they are all equally degraded.

### 2.5 Model, session integrity, and what confirms it's not truncation

- `model = "gemma-4-26B-A4B-it-MLX-8bit"` (child session JSON).
- `turns = 20` of 20 budget (TURN_EFFICIENCY=PASS per judge; not over budget).
- Session JSON ends cleanly with `role=tool` (last msg is the 41st overall). No partial write, no JSON corruption.
- Parent `20260419_203110_ce514c` received a clean `delegate_worker_v2` tool result with `exit_reason=completed`, `duration≈296s`.
- `arm-A-outcomes.txt` trial g11 recorded `OUTCOME RESULT=COMPLIANT attempts=1 elapsed=303s`. **The dispatch pipeline is healthy; only the model's content channel is polluted.**

---

## 3. Scope

**Systematic, not rare.** 13/20 Arm A children (65%) show channel-marker leakage in at least some assistant turns. 6/20 (30%) have the pure-marker-as-final-content pattern that mechanically trips the COMPLETION gate. The distribution is **task-correlated**: all 5 T4 trials are clean (T4 children run 30s and emit only 2 assistant turns — one tool call, one final prose summary — insufficient conversation length for the leakage to accumulate). T5, T6, T10 (the "structured"/"long-horizon" tasks that extend beyond 5 assistant turns) show leakage in 13/15 = 87%.

**Does COMPLETION miss it elsewhere?** **YES, substantially.** In 6/20 trials the LAST assistant message happens to include real prose appended AFTER the marker (e.g., `"<channel|>I've attempted to investigate..."`) — COMPLETION's 20-char gate passes on length, and CORRECTNESS's subject-token check may also pass. These trials silently succeed the judge despite polluted content chains. The r7.6-P1A variantH work already recognized this gap and added a dedicated `VIOLATION:EMPTY_SYNTHESIS` detector with two triggers (`direct_channel_marker_only` and `backpatch_stub_detected`) to plug it at the probe-check layer — but the P1C judge (`judge-trial.py`) does not import or use those detectors; it applies the older r7.5 F.1 rubric only.

---

## 4. Prior art

The failure mode is **extensively pre-characterized** in this repo. The channel leak is not new to Arm A trial 11; it has a named root-cause label (H2F), a dedicated mechanical fix (variantH Change 2), an orthogonal probe-check gate (variantH check.py G2), and a pre-existing validation set.

- **`/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-inv-2-sigterm-truncation.md`** (TL;DR §, lines 8–17; H2F §1.3 lines 52–67): identifies this exact Gemma-MoE chat-template regression as the true cause of the 8 r7.5 "SIGTERM-labelled" trials. Lists the three observed marker variants: `""`, `"<channel|>"`, `"thought\n<channel|>"`.
- **`/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-inv-3-pseudo-tool-call.md`** §1.5 (lines 80–94): explicitly separates Gemma-Format-1 pseudo-tool-call from channel-marker-leakage as two distinct failure modes. Trial 20 (r7.5) had `<channel|>thought<channel|>` leak + fabricated summary — already catalogued.
- **`/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.6-P1A-impl-notes.md`** Change 2 (lines 95–128): implements `_r76_channel_marker_only()` detector in `~/.hermes/hermes-agent/run_agent.py:417–445` + G2 `VIOLATION:EMPTY_SYNTHESIS` in `probe-variantH-check.py`. The detector's regex matches exactly the three variants observed here. Unit tests at lines 230–247 of that artifact cover `""`, `"<channel|>"`, `"thought\n<channel|>"`, `"<|channel>thought\n<channel|>"` — all passing.
- **`PROGRESS.md`** §r7.5 worker-quality (lines 143–149): failure mode 3 "Malformed pseudo-tool-call text in content rather than structured tool_calls (4/20)" — one of those 4 was the trial-20 channel-leak case.
- **VM state verified during this investigation:** `run_agent.py` md5 `08dc5ff7…` (not canonical); grep confirms `_r76_channel_marker_only` is **present** (2 hits: definition + call site at ~L9044). `gemma_parser.py` md5 `de6e6f12…` matches the P1A staged version. So variantH IS staged during the P1C probe, but the P1C judge doesn't consult the G2 detector — only its own older rubric.

The gap exposed by trial 11 is therefore **not a new finding** about the model; it is a gap in the P1C **judge harness** — the judge rubric does not incorporate the EMPTY_SYNTHESIS detector that variantH/check.py already implements.

---

## 5. Recommended next step

Two layers, both low-effort. Layer A first (cheap, judge-side, no runtime risk); Layer B optional (addresses generation rather than detection).

### Layer A (primary) — Judge-side EMPTY_SYNTHESIS verdict

Add a channel-marker pollution check to `/tmp/probe-r7.6-P1C-logs/judge-trial.py` in `eval_completion()` (currently lines 151–185). The existing `_r76_channel_marker_only` logic from `run_agent.py:417–441` can be ported verbatim. Concrete edit:

- **File:** `/tmp/probe-r7.6-P1C-logs/judge-trial.py`
- **Function:** `eval_completion(messages)`, around line 176 (immediately after the `< 20` short-content check, before the hanging-conjunction check).
- **Change:** import `re`, add module-level regex `_CHANNEL_MARKER_ONLY_RE = re.compile(r"^\s*(?:(?:<\|?channel\|?>\s*)|(?:thought\s*<\|?channel\|?>\s*)|(?:<\|?channel\|?>\s*thought\s*<\|?channel\|?>\s*))+\s*$", re.IGNORECASE | re.DOTALL)`, then in `eval_completion()` return `(False, f"channel-marker pollution (len={len(content)})")` when the regex matches.
- **Bonus:** scan *all* assistant messages (not only the last) — if ≥3 prior assistants are pure-marker, emit `channel_pollution_depth` diagnostic in the rationale. Catches the currently-masked trials 7, 8, 9, 13, 18, 19.
- **Do NOT edit** `run_agent.py` (already fixed), `gemma_parser.py` (unrelated to this failure), or any VM file.

Effort: ~20 lines of Python in the judge. No re-run of Arm A probes needed — judge-trial.py can replay against the existing child JSONs; a one-liner replay loop over `arm-A-outcomes.txt` will regenerate `arm-A-verdicts.txt`.

**Why this before Layer B:** the generation-side behavior on this specific oMLX 8-bit 26B A4B MoE is outside Hermes's control surface without a server-side template patch; the probe *can* be correct about what happened without needing to fix the model. Current state is that the probe is systematically blind to 6/20 polluted-but-prose-appended trials.

### Layer B (secondary) — Surface the fix that already exists

VariantH's check.py G2 detector already implements this exact check via `detect_empty_synthesis()`. The P1C judge doesn't use it because P1C judges via its own in-process rubric rather than re-running `probe-variantH-check.py`. Two options:

- **B1:** refactor judge-trial.py to shell out to `probe-variantH-check.py` for completion/scope verdicts and merge results (higher coupling, but single source of truth). File to edit: `judge-trial.py` `judge()` function.
- **B2:** extract `detect_empty_synthesis()` from `probe-variantH-check.py` (lines referenced in P1A §Change 3 "Detector logic") into a shared module and import into both check.py and judge-trial.py. Cleaner; one worker-day.

B2 is the recommendable long-term path. B1 is faster but fragile (judge depends on a wrapper artifact).

### Explicit non-recommendation

- **Do NOT** try to fix Gemma's chat template client-side. The marker originates in the oMLX server's template rendering (or the 8-bit quantization's training-data contamination). Hermes can't suppress it without an `on_chunk` filter that strips `<channel|>` / `thought\n<channel|>` from the content stream — and that would destroy legitimate prose that happens to contain those strings. Content-level filtering is the wrong layer.
- **Do NOT** raise the judge's `< 20` threshold. Trial 11's content IS 18 chars — raising to 50 would hide fewer false-positives but wouldn't address the fundamental "marker-is-the-whole-content" class.

---

## 6. Falsifiability

The root cause claim (**"model-side chat-template regression on Gemma 4 26B A4B MoE 8-bit, surfacing Harmony-style channel sentinels as visible content"**) would be falsified by any of the following observations:

1. **A dense Gemma (e.g., `gemma-4-31b-it-4bit`) probe under identical Arm A conditions (variantF+G+H staged, no overlay) produces the same `<channel|>` / `thought\n<channel|>` content in assistant turns.** If dense shows it too, the regression is not MoE-specific — it would point either to Hermes's rendering path or to a shared layer like the OpenAI-compatible `chat/completions` wrapper. Evidence to check: any r7 or r7.2 dense child session on disk (`/home/parallels/.hermes/sessions/session_*.json` from those dates) grep'd for `<channel|>` in `.messages[].content`.

2. **A direct `curl` to the oMLX endpoint with `{"model": "gemma-4-26B-A4B-it-MLX-8bit", "messages": [...]}` produces clean content fields** (no `<channel|>`). If the raw API response is clean, the marker is being injected by a Hermes-side layer (prompt builder, tool-call decoder, `copilot_acp_client.py`, etc.) — not the model. This is the direct falsification test. Effort: 10 min; non-destructive; can be done while Arm B runs (separate endpoint request).

3. **The marker appears in NON-Gemma model sessions on the same VM** (e.g., `qwen-*`, or any other oMLX-hosted model used historically). If present there, it's a Hermes-side or oMLX-server-side bug, not a Gemma-specific template issue.

4. **A model update/re-quantization of `gemma-4-26B-A4B-it-MLX-8bit`** eliminates the marker on identical probe conditions. Confirms the chat-template-in-quantization hypothesis.

Conversely, the claim is *reinforced* by: (a) all other Gemma A4B MoE sessions on disk showing the same marker; (b) `<|channel|>` being a known gpt-oss/Harmony reasoning-header token that a multi-source training mix could plausibly contaminate; (c) the Hermes-side rendering being bit-identical to other models' (same `persist_session`, same JSON serialization) with no Gemma-specific content rewriter.

The **secondary claim** (**"judge's COMPLETION gate misses polluted-but-prose-appended trials"**) would be falsified if running the Layer A-patched judge against the 20 Arm A child JSONs produced ≤1 additional FAIL beyond the current 9. I predict +6 (trials 7, 8, 9, 13, 18, 19 flip FAIL). If instead 0–1 flip, the pure-marker prefix isn't actually leading the final content in those cases — re-inspect raw bytes.

---

## 7. Environmental / safety footnotes

- **Arm B probe is actively running** on the VM at the time of this investigation (`probe-r7.6-armB-T5-moe-run5`, pid 898951). All work here was read-only (`jq`, `grep`, `ls`, `md5sum` only); no session files touched; tripwires not re-baselined to avoid interference.
- **VM-side state during the target trial:** HERMES.md md5 `01c0e77b…` (variantF), run_agent.py md5 `08dc5ff7…` (variantH P1A changes present — `_r76_channel_marker_only` function verified), gemma_parser.py md5 `de6e6f12…` (variantH F3A' prefix-tolerant patch present). So P1A's runtime detector IS active but operates only on the empty-follow-up-after-tool-calls code path — it doesn't rewrite in-flight visible content on normal turns. The detector was designed to gate a *specific* fallback (back-patching to `"Calling the X tool..."`), not to cleanse content chain-wide. This is by design; see `ARTIFACT-r7.6-P1A-impl-notes.md:117–128`.
- **Wrapper / check-script versions used by P1C:** P1C's `judge-trial.py` is NOT `probe-variantH-check.py`. It's a separate in-process rubric evaluator written against the r7.5 F.1 brief. The two checkers have overlapping but not identical failure-mode coverage. This diagnostic is the first time (from this session's evidence) that the divergence has been made explicit.

---

*End of artifact.*
