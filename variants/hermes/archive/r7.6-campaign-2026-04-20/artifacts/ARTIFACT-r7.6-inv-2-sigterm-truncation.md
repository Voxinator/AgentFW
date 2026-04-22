[TASK CLASS: structured]
Justification: Multi-part failure-mode investigation (evidence gathering + hypothesis ranking + candidate fixes + ranked recommendation + validation plan) with independently verifiable components. Design-only, single-artifact scope.

# ARTIFACT — r7.6 Phase 0 Investigator 2: "SIGTERM truncation of child sessions"

## TL;DR (≤200 words)

**The label is wrong.** The 8 r7.5 trials (6, 7, 9, 10, 11, 12, 13, 14) catalogued in `ARTIFACT-r7.5-F2-probe-results.md` §"Failure mode 2 — mid-tool truncation / SIGTERM (8 trials)" were **not SIGTERM'd**. VM inspection confirms:

- All 8 children have `exit_reason=completed` in the parent's `delegate_worker_v2` tool result, durations 6–57s (far below the 900s `timeout`).
- All 8 parent session JSONs persisted cleanly (`last_role=assistant`).
- All 8 child session JSONs persisted cleanly; they end with `role=tool` because Hermes' "empty-follow-up-after-tool-calls" fallback at `run_agent.py:8925–8936` back-patches the penultimate assistant's `content` to `"Calling the <X> tool..."` and `break`s out of the turn loop without appending a new final assistant message.
- Children are in-process threads (`ThreadPoolExecutor` at `delegate_tool.py:619`), not subprocesses — no separate timeout budget exists today.

**Root cause (top hypothesis, H2F, new):** The 26B MoE model emits harmony-format channel markers (`"thought\n<channel|>"`, `"<channel|>"`) as its only user-visible content. Tool_calls still parse, so the run continues, but every assistant turn is content-empty. On the turn after the final tool result, the model produces an empty assistant message; Hermes' fallback path exits cleanly, marking `completed=True` despite no synthesis. **SIGTERM is not the mechanism; model-format regression is.** Tier-3 upstream SIGTERM handling (F2A) is still valuable cross-cutting work, but it does not address the 8 "SIGTERM-labelled" r7.5 trials.

**Top fix:** F2G (new) — detect channel-marker-only assistant turns and fail loudly (prompt the model or terminate with a diagnostic final_response). Paired with F2A as defense-in-depth. Estimated effort: 3–4 hours for F2G, 4 hours for F2A; 5-trial × 2-task × 2-condition probe matrix to validate.

---

## Part 1 — Evidence

### 1.1 Which r7.5 trials were affected?

Per `ARTIFACT-r7.5-F2-probe-results.md:66`, the 8 trials assigned to failure mode 2 ("mid-tool truncation / SIGTERM") are **trials 6, 7, 9, 10, 11, 12, 13, 14** — all T5 or T6. The trials listed are exactly those with `last msg role=tool` and no final assistant synthesis.

### 1.2 Session-by-session inspection (VM read-only)

From `ssh ubuntu-vm` with `jq` on `~/.hermes/sessions/session_<id>.json` plus `stat(1)`:

| # | Task | Run | Parent SID | Child SID | Parent persisted? | Parent last_role | Parent dur | Child dur | Child msgs | Child last_role | Child asst turns | Child status (per parent tool result) | Child exit_reason | Child summary (first 60 bytes) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6 | T5 | 1 | 20260419_175717_2dc2aa | 20260419_175731_46919a | YES | assistant | 43s | 22s | 23 | tool | 11 | completed | completed | `<channel\|>` |
| 7 | T5 | 2 | 20260419_175806_786e60 | 20260419_175833_46abf5 | YES | assistant | 69s | 35s | 25 | tool | 12 | completed | completed | `thought\n<channel\|>` |
| 9 | T5 | 4 | 20260419_180146_c6a909 | 20260419_180153_6e9c84 | YES | assistant | 17s | 6s  | 7  | tool | 3  | completed | completed | `thought\n<channel\|>` |
| 10 | T5 | 5 | 20260419_180208_0d729b | 20260419_180417_3748c0 | YES | assistant | 152s | 16s | 9  | tool | 4  | completed | completed | `I have been searching for the "Chief of Staff Dashboard"...` |
| 11 | T6 | 1 | 20260419_180505_7c5bec | 20260419_180511_79a472 | YES | assistant | 17s | 6s  | 7  | tool | 3  | completed | completed | `thought\n<channel\|>` |
| 12 | T6 | 2 | 20260419_180527_70a84b | 20260419_180532_5b455e | YES | assistant | 26s | 17s | 21 | tool | 10 | completed | completed | `<channel\|>` |
| 13 | T6 | 3 | 20260419_180558_c3b9b6 | 20260419_180604_d35ad2 | YES | assistant | 15s | 6s  | 7  | tool | 3  | completed | completed | `thought\n<channel\|>` |
| 14 | T6 | 4 | 20260419_180620_f99cb5 | 20260419_180630_333820 | YES | assistant | 26s | 13s | 19 | tool | 9  | completed | completed | `thought\n<channel\|>` |

**Key columns for SIGTERM falsification:**
- **Child duration 6–57s** vs. `TIMEOUT_PER_TURN=900s` — the child finished within the first 6% of the budget.
- **Parent persisted cleanly (assistant last_role)** — parent was not killed mid-turn; it received the child's tool result and emitted a clean final response.
- **`exit_reason=completed`** — the delegate framework explicitly classified the child as completed (not `max_iterations`, not `interrupted`).
- **Child session JSON on disk** — the session was written by `_persist_session`. If SIGTERM had fired, research `ARTIFACT-r7.4-sigterm-research.md` §Q2 would predict zero JSON; we see full JSON with 7–25 messages.

Trial 10 (T5r5) is the outlier: 57s duration, 42 api_calls, a real `summary` string beginning `"I have been searching for the \"Chief of Staff Dashboard\"..."`. This is a different failure mode — the child genuinely ran but couldn't find the target codebase at the wrong cwd (`~/.hermes/hermes-agent/`). Its "last_role=tool" status is the same structural tail as 6/7/9/11/12/13/14 (back-patched penultimate assistant), so it was lumped into mode 2 in the F.2 aggregate. I keep it in the set but flag it separately.

### 1.3 Last persisted action shape

For trials 6, 7, 9, 11, 12, 13, 14, every one of the assistant messages preceding the trailing tool result has `content` equal to either `""`, `"thought\n<channel|>"`, `"<channel|>"`, or `"Calling the <X> tool..."` (back-patched). Example (trial 6, child `20260419_175731_46919a`, 11 assistant turns, raw inspection via `jq`):

```
msg 1  assistant, tc_count=1, content=""
msg 3  assistant, tc_count=1, content=""
msg 5  assistant, tc_count=1, content="thought\n<channel|>"
msg 7  assistant, tc_count=1, content="<channel|>"
msg 9  assistant, tc_count=1, content="<channel|>"
msg 11 assistant, tc_count=1, content="thought\n<channel|>"
msg 13 assistant, tc_count=1, content="<channel|>"
msg 15 assistant, tc_count=1, content="thought\n<channel|>"
msg 17 assistant, tc_count=1, content="<channel|>"
msg 19 assistant, tc_count=1, content="thought\n<channel|>"
msg 21 assistant, tc_count=1, content="Calling the read_file tool..."   # back-patched
msg 22 tool, role=tool                                                    # final persisted
```

The model never produced a proper natural-language assistant turn. The tool_calls parsed correctly (hence the 11 productive tool invocations), but the model's visible `content` was harmony-template leakage (`<channel|>`, `thought`) the entire run. On the turn after msg 22, the model emitted an assistant with **no tool_calls and empty/garbage content**, triggering the fallback at `run_agent.py:8908–8936`:

```
final_response = assistant_message.content or ""
if not self._has_content_after_think_block(final_response):
    fallback = getattr(self, '_last_content_with_tools', None)
    if fallback:
        # back-patch the last tool-calling assistant's content
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_names = [...]
                msg["content"] = f"Calling the {', '.join(tool_names)} tool..."
                break
        final_response = self._strip_think_blocks(fallback).strip()
        ...
        break
```

Because this runs BEFORE the hypothetical "next assistant turn is appended to messages[]," the final assistant message is NOT recorded in the session. The session ends with the last real tool result, and the `completed=True` signal propagates to the parent with `summary=<garbage>`.

### 1.4 What the parent's delegate_worker_v2 tool result says

For every one of the 8 trials, `parent.messages[role=tool].content` shows:

```json
{"results": [{"task_index": 0, "status": "completed", "summary": "<garbage-channel-leakage>", "api_calls": <6–42>, "duration_seconds": <5.9–57.2>, "model": "gemma-4-26b-a4b-it-mlx-8bit", "exit_reason": "completed", ...}]}
```

Every `exit_reason` is `"completed"`. Zero `"max_iterations"`. Zero `"interrupted"`. No SIGTERM anywhere. The parents then emit a natural final assistant turn (see parent `last_role=assistant` and `duration` 15–152s — including the short ones, nothing was truncated).

### 1.5 VM structure: children are threads, not subprocesses

Confirmed via `delegate_tool.py` inspection:
- `ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHILDREN)` at `delegate_tool.py:619`.
- `_run_single_child` at `delegate_tool.py:333+` calls `child.run_conversation(user_message=goal)` directly — in-process, same Python interpreter.
- Child is an `AIAgent` instance constructed at `delegate_tool.py:288+` with `parent_session_id=getattr(parent_agent, 'session_id', None)` and registered in `parent_agent._active_children`.

**Consequence:** children share the parent's process. Any SIGTERM that lands on the parent also kills every running child. There is no per-child timeout budget; children run unbounded against the parent's `timeout 900` wall-clock.

---

## Part 2 — Root-cause hypotheses (re-weighted given §1 evidence)

| Hyp | Statement | Weight | Evidence for/against |
|-----|-----------|--------|----------------------|
| H2A | Children legitimately need >15 min; 900s is too small | **LOW** | Children ran 6–57s. Bumping timeout changes nothing for the failed 8 trials. |
| H2B | Children stuck in productive-but-slow loop | **LOW** | Same. Children finished in seconds. |
| H2C | Children stuck in unproductive infinite loop; SIGTERM unmasks thrash | **LOW for THESE 8**; MEDIUM for different r7.5 trials | Trials 3, 4, 8, 17, 19 (mode 1 per F.2) exhibit this, NOT the 8 mode-2 trials. |
| H2D | Hermes `_persist_session` doesn't fire on SIGTERM | **IRRELEVANT to THESE 8** | No SIGTERM fired. Tier 3 still catches a different, real failure mode (parent-session loss when parents take >900s — see `ARTIFACT-r7.4-sigterm-research.md` §Q2, Q5), but THAT failure mode is what Tier 3 was designed for, NOT the 8 trials labelled "mode 2" in F.2. |
| H2E | Wrapper's child-timeout inherited from parent-timeout | **IRRELEVANT here** | True structurally, but not material: children finished in seconds. |
| **H2F** | **NEW. Model emits channel-marker leakage as visible `content`; Hermes' empty-follow-up fallback at `run_agent.py:8925–8936` silently ends the run with `completed=True` despite no real synthesis.** | **HIGH** | Every one of the 8 child sessions has 0 assistant turns with real prose content. All `content` fields are `""`, `"thought\n<channel|>"`, `"<channel|>"`, or back-patched `"Calling the X tool..."`. `exit_reason=completed`. The fallback path explicitly `break`s without persisting the final empty turn, producing the `last_role=tool` symptom that was mis-labeled as SIGTERM. |
| H2G | Hermes tool-parser is successfully extracting tool_calls from harmony-format output, so the run continues past many empty-content turns, until the model's last turn is empty AND has no tool_calls → fallback fires → `completed`. | HIGH (sub-hypothesis of H2F) | 11 valid tool invocations in trial 6 despite every `content` being garbage — tool_calls path clearly parsing the harmony format correctly while `content` is not being stripped of channel markers before persistence. |
| H2H | The F.2 judge conflated "last_role=tool" with "SIGTERM truncation" because both produce the same structural tail; no timing verification was done. | HIGH (methodology note) | F.2 judge's per-trial notes (e.g. trial 06: "SIGTERM/truncation mid-investigation. 11 assistants, last msg is role=tool") never cited child duration or exit_reason, only structural tail. The label propagated by pattern-match, not by evidence. |

**Synthesis:** H2F + H2G + H2H explain all 8 trials fully. H2D is a **real separate issue** (parent session loss on >900s runs) that exists independently but is not what made these 8 trials fail. Mixing them in the same investigation is why Tier 3 was designed — the prior framing was correct that SIGTERM-on-parent is a real gap; it was wrong that it explains the 8 r7.5 mode-2 trials.

**SIGTERM is not the root of the 8 mode-2 trials. Channel-marker leakage is.**

---

## Part 3 — Candidate fixes (updated)

| ID | Fix | What it addresses | Effort | Blast radius | Notes |
|----|-----|-------------------|--------|--------------|-------|
| F2A | Tier 3 upstream Hermes SIGTERM handler per `ARTIFACT-r7.4-sigterm-research.md` §"Hook Points" (Option A + Option B) — install `signal.signal(SIGTERM, ...)` in `cli.main()`, wrap `run_conversation` body in try/finally with inline `_persist_session`. | Parent-session loss for REAL >900s runs (long-horizon parents that haven't finished when `timeout` fires). Does NOT address the 8 r7.5 mode-2 trials. | ~4 hours (per B.0 research) | Low (new single-query signal handler mirrors interactive-mode handler at `cli.py:8432–8441`) | Still worth shipping as cross-cutting infrastructure. Every probe run going forward benefits. |
| F2B | Bump `TIMEOUT_PER_TURN` from 900s to 1500s or 1800s | H2A/H2B rescue if they were true | ~30 min (env var already in place per `ARTIFACT-r7.5-B1-impl-notes.md` Change 1; just export it) | None — env override is default-safe | Does nothing for the 8 mode-2 trials; the wrapper already supports `TIMEOUT_PER_TURN=N`. |
| F2C | Periodic session checkpoint (flush every 3 turns, not only at exit) | Parent-session loss under SIGTERM | ~6 hours (new flush trigger in `run_agent.py` turn loop) | Medium (touches hot path; could double write-amplification) | Partially redundant with F2A — F2A gets you the save on unwind; F2C saves you an in-flight turn that F2A would miss if SIGKILL followed SIGTERM too quickly. |
| F2D | Separate child-timeout budget (children get own `timeout` independent of parent's 900s) | Structural: parent-kills-child-too | Architecturally large (~8–12h) — requires delegating child dispatch to subprocess, not thread | High (changes concurrency model) | Moot for the 8 trials: children finished in 6–57s. |
| F2E | F2A + F2B combined | Two independent issues at once | ~4.5h | Low | Recommended as infrastructure bundle for r7.6 but does NOT fix the 8 r7.5 trials. |
| F2F | Anti-thrash turn-efficiency gate (per mode #1 investigator) | Infinite-loop search thrash (mode 1 trials 3, 4, 8, 17, 19) — DIFFERENT trials | ~4h | Medium | Investigator scope overlap. Not my scope to recommend here; mentioned for completeness. |
| **F2G** | **NEW. Detect channel-marker-only assistant content; fail loudly.** Two sub-options: **G1** — upstream content filter in `_build_assistant_message` (`run_agent.py`) that treats `"^(thought\s*)?<channel\|>\s*$"` as empty content, triggering the existing `(empty)` terminal at `run_agent.py:8976` (which sets `final_response="(empty)"` instead of the back-patched fallback). **G2** — wrapper/judge-side: detect `summary=~/^(thought\s*)?<channel\|>/` in the parent's `delegate_worker_v2` tool result and classify as worker-level FAIL with a distinct verdict (e.g. `WORKER_EMPTY_SYNTHESIS`) so F.2-equivalent probe aggregates stop mis-labelling it as SIGTERM. | **THE actual 8 r7.5 mode-2 trials** | G1: ~3–4h (upstream, small regex + turn-loop branch). G2: ~2h (one regex + one new verdict in check.py). | G1: Low (pure content normalisation). G2: None (check-only, no VM changes). | Top fix. G2 is the minimum-viable; G1 is the upstream fix. |
| F2H | Add a cheap "final-synthesis-present" gate in the check script: require `final_response` (mapped from `run_conversation`'s return) to pass a non-empty-non-marker test before `COMPLIANT` can be emitted. | Same as F2G but entirely check-side. | ~1h | None | Strictly weaker than F2G (doesn't fix upstream), stronger than doing nothing. |

---

## Part 4 — Ranked recommendation

### Top pick: **F2G (G2 + G1)** — 2h + 3–4h = 5–6h combined

**Why G2 first:** Pure wrapper/check-side. No VM writes. Can be landed in the same session that lands B.1/B.2 peers. Fixes aggregate reporting immediately — we stop mis-labelling 8/20 trials as SIGTERM when they're model-output failures. The new verdict (e.g. `WORKER_EMPTY_SYNTHESIS`) also flags the issue to the next probe's SHIP judge without muddying the "SIGTERM" signal. Effort: ~2h.

**Why G1 second:** The real fix. Filtering `"(thought\s*)?<channel|>"` as empty content at `_build_assistant_message` — or immediately after `assistant_message.content` is read at `run_agent.py:8908` — routes these trials through the existing `(empty)` terminal (line 8976) rather than the silent back-patch fallback. `final_response="(empty)"` is at least honest; it lets the F.2-equivalent judge distinguish "model produced no synthesis" from "model produced a clean summary and we lost it." Effort: ~3–4h including test coverage on a clone of `run_agent.py`.

### Second pick: **F2A — Tier 3 upstream SIGTERM handler** — ~4h

Still high-value because the original r7.4 research (`ARTIFACT-r7.4-sigterm-research.md`) empirically demonstrated real parent-session loss (orphan child `20260419_132928_e11ccb` with parent JSON absent) for runs that genuinely exceed 900s. That is a separate, real, cross-cutting failure mode that F2G does nothing about. All probe trials going forward (not just r7.6) would benefit. It is also the most upstream-contributable of the fixes here — the pattern mirrors Hermes' existing interactive-mode signal handler at `cli.py:8432–8441` (`ARTIFACT-r7.4-sigterm-research.md` §Q4); the upstream maintainers already chose that pattern for the REPL and would plausibly accept it for single-query mode with minor cleanup. Contribution path: local `.hermes/hermes-agent/` is a Python package; a PR to its origin repo (to be identified from `.git/config` on VM at implementation time) is feasible. Effort: ~4h for our side; upstreaming adds review latency but no additional implementation.

**Do both.** F2G addresses the immediate 8 r7.5 trials; F2A addresses the latent "parent takes longer than 900s" class. They do not interact.

### Third pick: **F2B — bump `TIMEOUT_PER_TURN`** — ~30 min

Recommend keeping the env override in place (already landed per B.1) but NOT raising the default above 900s until F2A lands. The default-900s preserves r7.4/r7.5 comparability; F2A (if it lands) removes the failure-mode that would motivate raising the default.

---

## Part 5 — Validation test plan

### Matrix

Fixed model: `gemma-4-26b-a4b-it-mlx-8bit` (the r7.5 MoE that produced the 8 failures; keeps comparability with F.2 aggregate).

| Task | Class | Why it's in the matrix |
|------|-------|------------------------|
| T5 | structured | 3/8 of the mode-2 trials; closest to the failure surface |
| T6 | long-horizon | 4/8 of the mode-2 trials; pure long-horizon |
| T10 | long-horizon | Not in mode-2 but exhibits the pseudo-tool-call / fabrication failures that overlap H2F's channel-marker emission pattern — useful as a harder test |

T4 deliberately excluded: its 5-trial T4 leg passed 3/5 in r7.5, so it isn't discriminating.

### Conditions (2 × 3 = 6 cells)

Conditions are independent and can be parallelised on the VM:

- **C0 — Baseline.** `probe-variantG-wrapper.sh` at its current r7.5 HEAD (md5 `42b51b4c1dbd7f87aa53b4e9e49a5982`), no additional Hermes-side changes. This reproduces the r7.5 baseline for the 8 mode-2 trials.
- **C1 — F2G (G2 only).** `probe-variantG-check.py` extended to detect `summary=~/^(thought\s*)?<channel\|>/` or equivalent content-empty signature in the child's delegate result, emitting `WORKER_EMPTY_SYNTHESIS`. No upstream VM change. Tests that aggregate reporting correctly reclassifies the failures.
- **C2 — F2G (G1 + G2).** Additionally patch a local copy of Hermes `run_agent.py` (side-by-side `~/.hermes-dev/` or in-place patch per `ARTIFACT-r7.4-sigterm-research.md` §"Hook Points" test-plan template) with the channel-marker filter at line ~8908. Tests that the upstream fix actually converts "silent completion with garbage summary" into "loud `(empty)` terminal," which probe judges should then correctly classify as WORKER_QUALITY=FAIL with the existing `COMPLETION` criterion.
- **C3 — F2A only.** Stand up Tier 3 upstream SIGTERM handler per B.0 research; run baseline wrapper. Tests that F2A is regression-neutral (the 8 trials should show THE SAME aggregate outcome as C0 because SIGTERM isn't involved for them). Included as a control: if F2A accidentally changes the aggregate, something else is going on.
- **C4 — F2E = F2A + F2G.** Combined deployment.
- **C5 — Extended-timeout control.** `TIMEOUT_PER_TURN=1500` with baseline wrapper. Tests H2A/H2B explicitly. Expected: no improvement (children already finish in 6–57s, so a longer parent timeout is immaterial for the 8 mode-2 trials).

### Trials per cell

**5 trials per task per condition = 15 trials per condition × 6 conditions = 90 trials total.** At ~1–3 minutes wall-clock per trial (plus wrapper overhead and judging), plausible to run in a single session with parallelism = 3 children per VM.

If budget tight, cut to T5 + T6 only (10 trials per condition × 6 = 60 trials) and skip T10.

### Measurements per trial

- `exit_reason` from parent's delegate tool result
- `duration_seconds` from same
- `summary` (raw)
- `last_role` of child session JSON
- `last_assistant_content` of child session JSON (raw; check for channel-marker pattern)
- Count of assistant turns with content matching `^(thought\s*)?<channel\|>\s*$`
- Check-script verdict (with new `WORKER_EMPTY_SYNTHESIS` available in C1+)
- Worker-quality per F.1 rubric (unchanged)
- Any SIGTERM evidence: parent session `last_role != assistant` OR parent duration ≥ 900s

### Success criteria (pre-committed thresholds)

| Criterion | Threshold | Fails the fix |
|-----------|-----------|---------------|
| C1 vs C0: aggregate reporting reclassifies mode-2 trials | Every mode-2 equivalent trial gets `WORKER_EMPTY_SYNTHESIS` instead of "SIGTERM" | If any mode-2 trial is still labelled SIGTERM under C1, the G2 regex is wrong |
| C2 vs C0: WORKER_QUALITY PASS rate on T5/T6 goes UP | ΔPASS ≥ 0 AND no new fabrication (HONESTY) failures | If PASS drops, the filter is too aggressive or breaks a legit path |
| C2 vs C1: the 8-trial cohort shows `final_response="(empty)"` instead of garbage | ≥90% of affected trials show `(empty)` | If upstream patch isn't catching the pattern, G1 regex needs widening |
| C3 vs C0: regression-neutral | Aggregate WORKER_QUALITY PASS within ±1 trial | If F2A regresses, implementation bug |
| C4 vs C2 and C3: no interaction effects | Aggregate PASS ≥ max(C2, C3) | If there's a regression in C4, F2A and F2G interfere |
| C5 vs C0: null result confirmed | Aggregate WORKER_QUALITY PASS within ±1 trial | If C5 passes significantly better than C0, H2A/H2B were real and the framing needs revisiting |

### Out-of-scope for this probe

- Testing true parent-SIGTERM (requires a deliberately slow >900s parent trial; not in scope for the 8-trial investigation)
- T10 model-level pseudo-tool-call regression (overlaps mode 3 — different investigator's scope)
- Gemma-4-31B "dense" leg (r7.6 is 26B-MoE-focused)

---

## Open questions

1. **Is the channel-marker regex `^(thought\s*)?<channel\|>` sufficient, or do we need the full Harmony format spec?** The 8-trial sample shows only those two patterns, but other `<channel|name=...|>` variants may exist. Recommend: before landing G1, widen the regex to match the Harmony spec's `<|channel|>` / `<channel|>` / `<|start|>` class of tokens and include a verbose-log dump of the raw `final_response` on every rejection so unexpected markers surface.

2. **Does the 26B MoE emit channel markers on T4 too?** T4 had 3/5 WORKER_QUALITY PASS. If the 2 fails in T4 are ALSO channel-marker trials, the failure mode is wider than "long-horizon-only" and the cross-task impact of G1 is larger than implied by this artifact's scope. Recommend one-line grep of child sessions for trials 3, 4 when the probe budget allows.

3. **Does F2A's scope-of-concern ever manifest for r7.5-style 20-turn trials?** Per the data: no — all 20 parents persisted cleanly. F2A's value is for longer runs (dense 10-trial suites with 50-turn budgets, etc.). Recommend F2A ship regardless but be explicit that it is NOT the fix for any r7.5 observed failure.

4. **Should the check-script's new `WORKER_EMPTY_SYNTHESIS` verdict be `ERROR:*` (wrapper-error class, like `ERROR:WRONG_SESSION`) or `VIOLATION:*` (compliance class, like `VIOLATION:NO_MARKER`)?** Recommendation: `VIOLATION:EMPTY_SYNTHESIS` because the worker DID dispatch — it met the β-fuse contract — it just produced empty output. That's a worker-quality compliance failure, not a wrapper-level attribution failure. Get this decision made before the B.2-equivalent worker lands.

5. **Upstreaming F2A:** is there an existing Hermes issue tracker where this gap has been discussed? The B.0 research did not check, and the plan in `PLAN-r7.4-wrapper-sigterm-fix-design.md` §2c (Phase 2c worker brief) explicitly defers this to implementation time. Recommend checking `~/.hermes/hermes-agent/.git/config` on VM at impl time to identify the upstream repo and search its issues.

---

## Appendix — citations to B.0 research (`ARTIFACT-r7.4-sigterm-research.md`)

- Session persistence is inline at `run_agent.py:9109` plus 18 error-path duplicates at 7497, 7517, 7597, 7637, 7653, 7666, 7797, 7947, 8055, 8080, 8183, 8210, 8294, 8364, 8414, 8447, 8556, 8609, 8687. (§Q2.)
- `cli.main()` single-query mode installs `atexit.register(_run_cleanup)` at `cli.py:8692` but no SIGTERM handler. (§Q4.)
- Interactive-mode handler at `cli.py:8430–8441` is the pattern to mirror. (§Q4.)
- `_run_cleanup` at `cli.py:586–625` does NOT call `_persist_session`. (§Q2.)
- `HermesAgent._persist_session` at `run_agent.py:1842–1854`; `_save_session_log` at `run_agent.py:2385–2452` (writing via `atomic_json_write` at 2440–2445). (§Q1.)
- Empirical orphan-child confirmation (session `20260419_132928_e11ccb`): parent absent, child present, `messages[0]` content is dispatched goal not trial prompt. (§Q8.)
- Tier 3 recommended Option A + Option B: install SIGTERM handler in `cli.main()` single-query path; wrap `run_conversation` in method-level try/finally. Total diff ~30–50 lines across `cli.py` + `run_agent.py`. (§"Hook Points" Recommendation.)

New evidence from this investigation (not in B.0):
- `_run_single_child` at `delegate_tool.py:333+` dispatches children as in-process thread tasks via `ThreadPoolExecutor` at line 619, sharing the parent's Python process.
- `run_conversation`'s "empty-follow-up-after-tool-calls" fallback at `run_agent.py:8908–8936` back-patches the penultimate tool-calling assistant's `content` to `"Calling the <X> tool..."` and `break`s out of the turn loop without appending the model's final empty turn — this is the mechanism producing the `last_role=tool` symptom previously attributed to SIGTERM.
- `completed = final_response is not None and api_call_count < self.max_iterations` at `run_agent.py:9100` — this gate lets garbage `<channel|>` content pass through as `completed=True` as long as it's non-None.
