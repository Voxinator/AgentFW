---
type: r7.8 P2 — synthesis + vet plan
date: 2026-04-21
inputs: ARTIFACT-r7.8-P1a-failure-modes.md, ARTIFACT-r7.8-P1b-parser-research.md, ARTIFACT-r7.8-P1c-sampler-research.md, ARTIFACT-r7.8-P1d-stoptoken-research.md
---
# r7.8 P2 — synthesis

## Orientation

P1a says 54% of the r7.7 FAIL population (15/28) is dominated by **parser-layer channel pollution (Mode 3, 5/28) + sampler-layer degenerate loops and silent termination (Modes D+S, 10/28 combined with one shared trial)**. Those two layers generalize across tasks because the defects are in the model-output boundary, not in any one task surface. Prompt-layer thrash (Mode 2, 5/28) is third-priority. Environment (4/28, all Arm F T5) and tool-call hallucination (5/28, mostly Arm G T10) are narrower. r7.8 interventions are therefore prioritized parser > sampler > turn-budget > prompt, with the candidate slate drawn from P1b (C1-C4), P1c (S1-S4), and P1d (T1-T4).

The ship-judge for r7.7 established that further prompt-scaffolding is at its ceiling on this 26B MoE model. P1a confirms: only prompt-layer interventions already exist, and the generation-layer is untouched. r7.8's leverage is entirely in the **un-instrumented sampler + parser + stop-set boundaries** — none of which Hermes currently configures in any way today (P1c: zero sampler params sent; P1d: zero stop tokens sent).

---

## Part A — Candidate table (12-point ranking)

Scoring rubric: each candidate rated 1-5 on four axes — Generalization (5 = affects all tasks/models), Expected impact (5 = addresses top-frequency FAIL mode in P1a), Rollback safety (5 = single-file, hot-reload, JSON-only; 1 = multi-file code + restart), Implementation complexity inverse (5 = minutes; 1 = hours). Total out of 20.

| # | Candidate | Source | Gen | Impact | Rollback | Simplicity | **Total** |
|---|-----------|--------|----:|-------:|---------:|-----------:|----------:|
| 1 | **C1** — Universal channel-marker scrubber in gemma_parser.py | P1b | 5 | 5 | 5 | 4 | **19** |
| 2 | **S1** — Conservative sampler tune (temp=0.6, top_p=0.9, top_k=40, repetition_penalty=1.08, min_p=0.03) | P1c | 5 | 4 | 5 | 5 | **19** |
| 3 | **S4** — S1 + S3 combined | P1c | 5 | 5 | 4 | 3 | **17** |
| 4 | **T1** — Cross-turn loop detector (5-turn rolling signature window) | P1d | 5 | 5 | 4 | 3 | **17** |
| 5 | **C4** — Prefix-less tool_call recovery (variantH Change 1 re-propose) | P1b | 3 | 4 | 5 | 4 | **16** |
| 6 | **S3/T2** — Stop-token injection at oMLX boundary | P1c/P1d | 4 | 4 | 4 | 4 | **16** |
| 7 | **T4b** — Soft parent/child budget alignment (child cap ≤ parent_remaining + K) | P1d | 5 | 3 | 4 | 4 | **16** |
| 8 | **C2** — Channel-only content detection + explicit empty emission | P1b | 4 | 3 | 5 | 4 | **16** |
| 9 | **T3a** — 2× max_tokens ceiling in length-continuation | P1d | 5 | 2 | 5 | 4 | **16** |
| 10 | **S2** — Strict repetition tune (rep_penalty=1.2) | P1c | 5 | 2 (upside) / 4 (downside risk) | 5 | 5 | **15** |
| 11 | **C3** — Malformed `[]<tool_call|>` tail-only recovery | P1b | 2 | 2 | 5 | 5 | **14** |
| 12 | **T3b** — Regex repetition-loop detector inside continuation | P1d | 4 | 3 | 4 | 3 | **14** |
| 13 | **T4a** — Hard parent/child shared-budget enforcement | P1d | 5 | 3 | 3 | 3 | **14** |
| 14 | **S5** — Penalty-mix (presence + frequency) | P1c | 5 | 2 | 5 | 4 | **16** — deferred by P1c; score here for completeness |
| 15 | harmony `reasoning_parser` on Gemma-4 entries | P1c Appendix C | 5 | 4 | 3 | 3 | **15** — flagged out-of-scope below |

Generalization rationale (one-line, required for each candidate above 14 total):

- **C1:** strips Harmony/Gemma channel sentinels at the parse boundary for every output of any task on this model family — pollution is task-independent.
- **S1:** sampler tune affects every parent + child generation via server-side model_settings; current `repetition_penalty=1.0` is effectively off, so every task hits an un-damped sampler today.
- **S4:** S1 + S3 together attack two near-orthogonal pathologies (loop/drift + channel leakage) on every generation.
- **T1:** loop signatures are model-agnostic and task-agnostic; detects the "same tool, same args, N turns running" pattern anywhere it appears.
- **C4:** recovers prefix-less tool_calls from oMLX-stripped chat-template output — task-general for this model binding.
- **S3/T2:** per-request `stop` applies to every oMLX generation; prevents channel markers from reaching Hermes for any task.
- **T4b:** aligns advertised turn budget with actual wall-clock cost for every probe, independent of task.
- **C2:** normalizes empty-content emission contract for downstream consumers — general to every task that reaches a synthesis turn.
- **T3a:** truncation-safety net applies to any finish_reason=length event on any model.

Rejected/scored-low candidates:
- **C3** (tail-only `[]<tool_call|>`) — narrow regex, Gemma-MoE-specific; rejected from top 3 on generalization grounds but kept as a cheap add-on if C1 leaves residual evidence.
- **T3b** (content-repetition regex) — moderately general but adds a behavioral heuristic to the continuation path that can fire on legitimate bullet lists; rank 12 pending real-world validation.
- **S2** (strict rep_penalty=1.2) — literature consensus reports tool-call JSON malformation above 1.15; downside risk exceeds upside.
- **T4a** (hard shared-budget) — can starve late-dispatched children; T4b is strictly safer for equivalent benefit.

---

## Part B — Vet plan (top 3 candidates)

Top 3 by total score: **C1** (19), **S1** (19), **S4** (17). C1 and S1 tied; ordering below runs them in that order because C1 addresses the highest-frequency generalized FAIL mode (Mode 3 channel pollution) and has the simpler blast radius. S4 is gated on S1 passing its vet (it includes S1). If S4's second axis (S3 stop-tokens) is needed independent of S1 passing, it gets its own vet as Candidate 3b at the planner's discretion.

Each vet runs 5 trials stratified: **1×T4, 1×T5, 2×T6, 1×T10.** T6 weighted (2× slot) because r7.7 Arm F T6 = 0/5 — any signal there is high-information. Tasks drawn from the r7.7 probe matrix; use the same scaffold (Arm F base: variantF + G + H + A1 + A2 + HWO prompt stack) so the only variable is the candidate under test. Reuse existing judge prompts.

### Candidate 1 — C1: Universal channel-marker scrubber

- **Source:** P1b §C1 (primary pathology P1, P3, partial P4).
- **Exact changes:**
  - File: `~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py`
  - Replace line 113's narrow `re.sub(r"<\|channel>thought\n<channel\|>", "", content)` with a module-level helper `_scrub_channel_markers(s)` + class-level regex `_GEMMA_CHANNEL_MARKER_RE` covering `(?:<\|?(?:channel|tool_call|start|end|message|return)\|?>|(?:thought|analysis)\s*<\|?channel\|?>)` with `re.IGNORECASE`, followed by `\n{3,}` collapse.
  - Call site 1: line 71 (no-markup early-return) — `return self._scrub_channel_markers(text) or None, None`.
  - Call site 2: line 113 — `content = self._scrub_channel_markers(content)`.
  - No changes to run_agent.py. Parser-only patch.
- **md5 pin plan:**
  - Pre-stage: `ssh ubuntu-vm "md5sum ~/.hermes/hermes-agent/environments/tool_call_parsers/gemma_parser.py"` — expect `9967c49506ea6a8e9654c9a0191304fe`.
  - Pre-stage backup: `cp gemma_parser.py gemma_parser.py.probe-r7.8-orig`.
  - Post-stage: `md5sum gemma_parser.py` — record new hash; store in stage script header.
  - Rollback: `cp gemma_parser.py.probe-r7.8-orig gemma_parser.py` → md5 should restore to `9967c49506ea6a8e9654c9a0191304fe` exactly.
  - Unit-test gate before probe: `python3 -m py_compile gemma_parser.py` + 12-assertion unit test from P1b §"Unit test strategy" on the VM. Must pass 12/12 before any trial fires.
- **5-trial vet spec:**
  - Arm: same as r7.7 Arm F base + C1 patch; label "K1-vet-C1".
  - Tasks (one trial each except T6×2): T4-run1, T5-run1, T6-run1, T6-run2, T10-run1. Use fresh session IDs; do not reuse r7.7 session names.
  - Seed: unset (let oMLX pick; probes measure real stochastic distribution).
  - Judge: fresh-context judge per trial using the same rubric as r7.7 (COMPLETION/CORRECTNESS/TURN_EFFICIENCY/HONESTY/SCOPE/WORKER_QUALITY).
- **Success criterion:** ≥2/5 PASS overall **AND** 0/5 trials exhibit `<channel|>` or `thought\n<channel|>` substrings anywhere in the final assistant content (grep-checkable against session JSONs). Rationale: r7.7 Arm F on this exact task stratification was 1/5 (T5-run3 only); any ≥2/5 is directional evidence C1 closed at least one FAIL mode without regressing T4/T10.
- **Failure criterion:** 0/5 PASS on any task where r7.7 Arm F had PASSes **OR** ≥2/5 exhibit residual channel markers in final content → reject C1. Also reject if the 12-assertion unit test fails post-stage (staging bug, not a candidate judgment).
- **Wall-clock budget:** 45 min (5 trials × ~7 min average + ~10 min judge pass).

### Candidate 2 — S1: Conservative sampler tune

- **Source:** P1c §S1.
- **Exact changes:**
  - File: `/Users/briantaylor/.omlx/model_settings.json`, entry `gemma-4-26B-A4B-it-MLX-8bit`.
  - Set `temperature: 0.6` (was 0.8), `top_p: 0.9` (was 0.95), `top_k: 40` (was 64), `repetition_penalty: 1.08` (was absent → 1.0), `min_p: 0.03` (was absent → 0.0). `max_tokens: 16384` unchanged.
  - Apply via either direct JSON edit + `POST /admin/api/reload-models` OR `PUT /admin/api/models/gemma-4-26B-A4B-it-MLX-8bit/settings` with the typed admin API. Prefer the admin API for atomicity.
  - No Hermes-side changes; this is server-side only.
- **md5 pin plan:**
  - Pre-stage: `md5 /Users/briantaylor/.omlx/model_settings.json > /tmp/omlx_model_settings.md5.pre` on the Mac.
  - Pre-stage backup: `cp /Users/briantaylor/.omlx/model_settings.json /Users/briantaylor/.omlx/model_settings.json.probe-r7.8-orig`.
  - Post-stage: verify via probe request — `curl -s http://localhost:8000/v1/chat/completions -d '{"model":"gemma-4-26B-A4B-it-MLX-8bit","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'` then `tail -3 ~/.omlx/logs/server.log` — expect the "Sampling params: temperature=0.6, top_p=0.9, top_k=40, repetition_penalty=1.08" line.
  - Rollback: restore `model_settings.json.probe-r7.8-orig` → `POST /admin/api/reload-models` → re-verify md5 matches `.pre`.
- **5-trial vet spec:** identical task stratification to C1. Label "K1-vet-S1". Measure (a) degenerate-loop rate (≥10 identical tool calls within a session → loop), (b) turn count distribution, (c) PASS/FAIL verdict, (d) wall-clock.
- **Success criterion:** ≥2/5 PASS **AND** 0/5 trials exhibit a degenerate planning loop (defined as: ≥5 consecutive turns with repeated `(tool_name, arg_hash)` signature, OR a final-turn assistant message with ≥3× text repetition of a 40-char substring). Rationale: S1's primary mechanism is `repetition_penalty=1.08` which should cut Mode D directly.
- **Failure criterion:** <2/5 PASS **AND** no reduction in loop rate vs r7.7 Arm F on the matched tasks → reject S1. Also reject if tool-call JSON malformation is observed in any trial (rep_penalty unexpectedly damaging structured output at 1.08 — possible-but-unlikely per literature).
- **Wall-clock budget:** 45 min.

### Candidate 3 — S4: S1 + S3 combined (gated on S1 vet)

- **Source:** P1c §S4 (combination) + P1c §S3 / P1d §T2 (stop-token axis).
- **Preconditions:** Run only if S1 vet passes. If S1 fails, substitute T1 (cross-turn loop detector, score 17) as Candidate 3.
- **Exact changes (on top of S1):**
  - Hermes code edit on VM: `~/.hermes/hermes-agent/run_agent.py` around line 5367 in `_build_api_kwargs()`. After the base `api_kwargs = {...}` block and before the `extra_body` assembly, add:
    ```python
    if os.getenv("HERMES_OMLX_STOP_TOKENS") and self._is_local_endpoint():
        api_kwargs["stop"] = ["<channel|>", "<|channel|>", "thought\n<channel", "<end_of_turn>"]
    ```
  - Env var `HERMES_OMLX_STOP_TOKENS=1` added to `/tmp/r7.7-env.sh` for vet; keep opt-in.
  - Server-side: S1's model_settings.json changes remain applied.
- **md5 pin plan:**
  - `run_agent.py` pre-stage md5 captured; `.probe-r7.8-orig` backup made. Stage script records both.
  - `model_settings.json` already backed up from S1 vet — do not re-back-up.
  - Post-stage: `python3 -m py_compile run_agent.py` + verify by 5-line smoke `curl` to oMLX with `"stop":["<channel|>"]` and inspect `finish_reason` (should be `"stop"` when a `<channel|>` substring is in the generation; emit a synthetic prompt designed to produce one).
  - Rollback: restore both backups, restart Hermes parent, unset env var.
- **5-trial vet spec:** identical stratification. Label "K1-vet-S4".
- **Success criterion:** ≥3/5 PASS (stricter than C1/S1 because S4 stacks both axes — we need evidence that combining helps beyond each individually) **AND** 0/5 residual channel markers **AND** 0/5 degenerate loops. Specifically T6 ≥1/2 (any T6 PASS is a win over r7.7 Arm F's 0/5).
- **Failure criterion:** <3/5 PASS total, OR T6 = 0/2, OR any per-task regression vs r7.7 Arm F on T4/T10 → reject S4; fall back to shipping the stronger of {C1 alone, S1 alone, T1} based on their individual vets.
- **Wall-clock budget:** 45 min (code edit + unit gate + 5 trials + judge wave).

### Total vet budget

**~135 min (3 × 45 min).** Sequential preferred (each vet informs the next's go/no-go and avoids double-booking VM). If VM has capacity, C1 and S1 can run in parallel because they touch disjoint files (parser on VM vs. model_settings on Mac); S4 must follow S1.

---

## Part C — Final arm design (conditional on vet outcome)

Design assumes **C1 wins the vet** (primary case, highest expected probability per P1a's evidence weighting). Conditional branches for S1-wins and T1-wins noted at the end.

### Variant letter

**variant K** — next unused letter after variantH (r7.7's parser-prefix-less patch) and variantJ (reserved if sampler intervention lands separately). K designates r7.8's parser-hardening + associated stack. Use `.probe-r7.8-orig` as the backup suffix, layered on top of `.probe-r7.6-orig` from variantH.

### Arm K (combined intervention, analog of Arm F′)

- **Stack:**
  - variantF + variantG + variantH (r7.7 scaffold stack: HWO prompt + A1 todo-removal + A2 runtime fabrication gate + Gemma parser prefix-less recovery).
  - **+ C1** (universal channel-marker scrubber, r7.8 primary).
  - **+ S1** (server-side sampler tune, if S1 vet passes — otherwise omit and mark that in the arm name, e.g. Arm K_noS1).
  - **+ T4b** (soft parent/child budget alignment, safety-margin K=10) — cheap insurance against the 42/48-turn overshoot failure mode.
- **Env flags:**
  - `OMLX_API_KEY=<from /tmp/r7.7-env.sh>`
  - `AGENT_DISPATCH_AVAILABLE=1`
  - `OMLX_SWAP_MAX_GB=30`
  - `HERMES_LOOP_DETECT=1` (if T1 is also in the final stack; default off for Arm K to keep ablation clean)
- **Stage script chain:** `probe-variantK-stage.sh`:
  1. Tripwire canonical md5 check (HERMES.md, SKILL.md, jira-briefing.sh, useDashboard.ts) — abort on mismatch.
  2. Backup: `gemma_parser.py → .probe-r7.8-orig`, `model_settings.json → .probe-r7.8-orig`, `run_agent.py → .probe-r7.8-orig`.
  3. Apply variantH patch (if not already staged) via existing `probe-variantH-stage.sh` logic.
  4. Apply C1 patch (parser scrubber + call-sites) via Python in-script `heredoc` edit.
  5. Apply S1 patch (model_settings.json) via `PUT /admin/api/models/.../settings` with typed admin API.
  6. Apply T4b patch (delegate_tool.py kwarg + cap expression) via `heredoc` edit.
  7. Run 12-assertion C1 unit test; abort on fail.
  8. Restart Hermes parent; run 1-request smoke probe to confirm sampler line.
  9. Record post-stage md5 for all 3 files + model_settings.json contents to stage log.
  10. Stage complete — arm is ready for 20-trial probe.
- **Unstage script:** `probe-variantK-unstage.sh` — restores all `.probe-r7.8-orig` backups, reloads model_settings, restarts Hermes, verifies all pre-stage md5s match.

### Arm K′ (ablation, analog of Arm G′)

- **Stack:** variantF + variantG + variantH + **C1 only** (drop S1, T4b).
- **Isolates:** whether the parser-layer scrubber alone is sufficient, or whether the sampler axis (S1) is load-bearing. If Arm K beats Arm K′ meaningfully on T6 (the channel-pollution-driven task cluster in r7.7), S1 is doing work. If they tie, S1 is noise and ships as a low-cost no-op. If Arm K′ beats Arm K, one of the stack elements is counterproductive — rarely observed but possible if S1's rep_penalty subtly degrades tool-call JSON.
- **Env flags:** same as Arm K minus `HERMES_OMLX_STOP_TOKENS` (not in stack) and default T4b behavior (T4b not applied).
- **Stage script:** `probe-variantK-ablation-stage.sh` — identical to Arm K except steps 5 and 6 (S1 and T4b) are skipped.

### Conditional branches

- **If S1 wins the vet but C1 loses:** swap — Arm K = S1 + T4b + variantF/G/H; Arm K′ = S1 alone. Less promising because P1a's top failure mode (channel pollution, 5/28) is not addressed, but sampler loop-damping alone is still a worthwhile ship if it moves the needle on Modes D+2+thrash.
- **If both C1 and S1 pass AND S4 passes:** Arm K includes full S4 (S1 + S3 stop-tokens) + C1 + T4b; Arm K′ is C1-only. This is the most aggressive stack.
- **If all three vets fail:** fall back to T1 cross-turn loop detector as a standalone probe (score 17), drop the 40-trial matrix to 20 trials (T1 alone vs. r7.7 Arm F baseline), and stage-gate accordingly. If T1 also fails the vet, issue the "HOLD-r7.8: no viable path on current substrate" doc per operator pre-approval #5.

### `.probe-r7.8-orig` backup pattern (summary)

All three candidate files use the same suffix convention. Backups are created at stage time, verified immediately via md5 diff against the live file, and retained across the campaign so any failed arm can be rolled back to bit-identical state. The stage script refuses to proceed if a `.probe-r7.8-orig` already exists for a file (stale backup from a previous aborted stage is a red flag — operator resolves manually).

---

## Part D — Out-of-scope for r7.8

- **Harmony `reasoning_parser` on Gemma-4 entries (P1c Appendix C):** **Out of scope for r7.8.** This is a server-side change that might obsolete C1 by handling channel-marker stripping inside oMLX before the content reaches Hermes. Promising but requires validation that (a) Gemma-4's chat template actually emits Harmony-format `<channel|>` markers in a shape oMLX's `harmony` parser recognizes, (b) the resulting downstream content matches what the r7.8 judge rubric expects. Both require their own research worker. If it works, it replaces C1; if it doesn't, it introduces a new failure mode mid-campaign. **Defer to r7.9.** Document in PROGRESS-r7.9 as candidate #1 for the next campaign's P1.
- **S2 (strict rep_penalty=1.2):** **Out of scope unless S1 under-corrects.** Literature risk is real; only ship if S1 is insufficient and we need more aggressive loop-breaking.
- **S5 (presence + frequency penalty mix):** **Deferred** per P1c. Adds experimental variables without clear literature consensus.
- **T1 (cross-turn loop detector):** **Borderline.** Scored 17 (tied with S4). Not in the top-3 vet slate, but held in reserve as the fallback if all three primary vets fail. T1 is ~30 lines of Python in run_agent.py:7111 and is a high-generalization standalone ship candidate. Recommend running a P3 vet only if C1/S1/S4 all miss.
- **T4a (hard shared-budget):** **Rejected.** Can starve late-dispatched children; T4b achieves 90% of the benefit with 0% of the risk.
- **T3b (regex repetition detector in length-continuation):** **Deferred to r7.9.** The regex heuristic needs real-world validation against legitimate bullet-lists and repeated code snippets. Could false-positive on well-formed long summaries.
- **C3 (malformed `[]<tool_call|>` recovery):** **Stand-by.** Ship only if r7.8 probe logs show residual tail-only emissions after C1 lands. Add in a minor follow-up patch, not in the main arm.
- **C2 (explicit empty-content emission contract):** **In scope, but bundled free with C1.** The one-line `logger.warning` addition has no behavioral effect beyond C1 alone and provides diagnostic value. Include as a trivial addendum to the C1 patch; not a separate arm.
- **T3a (2× max_tokens ceiling):** **In scope as defensive add-on.** Trivial two-line early-return inside an existing branch. Bundle into Arm K at no cost.
- **Dense-model substrate swap** (e.g. 31B dense): **Out of scope per operator constraint #4.** Hardware + model staying at Gemma-4-26B-A4B-MLX-8bit.
- **HERMES.md / SKILL.md edits:** **Hard-gated by tripwires.** Prompt-layer interventions already at their ceiling per r7.7 S9. No r7.8 work here.

### What r7.8 explicitly will NOT attempt

1. Switch models (dense or larger) — operator constraint.
2. Modify HERMES.md or SKILL.md — tripwire-gated.
3. Run any arm at >20 trials without vet evidence — operator pre-approval #2 + design criterion #5.
4. Ship a HOLD verdict as a worker-quality release — operator pre-approval #4.

---

## Summary for planner

The vet slate is **C1 → S1 → S4**, sequentially, ~45 min each, ~135 min total. Success gates are stratified around T6 (the r7.7 zero-PASS task): any PASS there is high-information. Arm K (C1 + S1 + T4b + variantF/G/H) is the target combined intervention; Arm K′ (C1 only) is its ablation. If C1 wins but S1 loses, Arm K reduces to C1 + T4b + variantF/G/H and Arm K′ is variantF/G/H alone — cleaner isolation but slightly weaker stack. Harmony reasoning-parser is flagged for r7.9 as the candidate most likely to subsume C1; we explicitly do not chase it in r7.8 because the validation cost eats the overnight budget.

Word count: ~1920.
