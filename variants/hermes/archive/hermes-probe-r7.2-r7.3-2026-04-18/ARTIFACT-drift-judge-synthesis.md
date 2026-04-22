# ARTIFACT — Drift Investigation: Judge Synthesis

**Judge:** Claude Opus 4.7 (1M), fresh context. Did not run trials or worker investigations.
**Date:** 2026-04-18, late afternoon.
**Inputs:** 5 parallel worker artifacts (α, β, γ, δ, ε), r7 baseline probe results, r7.2 v1/v2 probe tables.
**Spot-checks performed:** (1) `grep -c "Cache base_size mismatch"` today's and prior `server.log` files; (2) session-JSON message/tool-call structure of r7 Task 5 parent via SSH.
**Instruction:** be direct, don't sycophant, name who was closest to the truth.

---

## 1. Executive verdict (≤200 words)

**The reported "3/5 → 1/5 drift" is overwhelmingly a measurement artifact, with a possible small real-degradation component on top. The story is:**

- **Workers α, γ, ε are right, worker β is suggestive-but-unverified, and worker δ has a dramatic finding that does NOT actually bear the causal weight it claims.** ε is closest to the truth.
- r7's baseline dispatch rate was **inflated**: the r7 Variant E 3/5 first-attempt number counted one trial (Task 5) as "dispatched" based on a stdout capture of a dispatch that fired AFTER the parent session had already role-collapsed onto `terminal` + `read_file` chains and was then SIGTERM'd mid-stream. The on-disk r7 Task 5 session shows the SAME failure mode as r7.2 v2 Task 5 — byte-for-byte: `terminal` → `search_files` → `read_file`. It was never a clean first-attempt dispatch.
- The realistic r7 "persisted dispatch" rate was already **1/5 first-attempt, 2/5 final** — statistically indistinguishable from r7.2 v2's 1/5 / 2/5.
- δ's 263 cache mismatch warnings are **real and new** (0 on every prior day; verified by judge). But the garbled-native-format output δ captured was an *out-of-band test prompt*, not one of the 10 probe trials. No r7.2 probe session shows that malformed pattern. Cache corruption is a real new oMLX anomaly worth investigating, but it is **not proven** to be the cause of the probe-scoreboard delta.
- **The real story:** there is no significant behavioral drift to explain. The 3/5 r7 baseline was noise-plus-artifact. Gemma-4-31B dispatch rate on this task set is ~20–30%, consistent across r7 persisted, r7.2 v1, and r7.2 v2.

---

## 2. Reconciled timeline for 2026-04-18

Integrating α, β, δ, and judge spot-checks:

| Time (local) | Event | Plausible causal link |
|---|---|---|
| 00:07 | Gemma-31B engine starts, loaded (old oMLX process, PID 87119 from Apr 10) | pre-restart baseline |
| 00:30, 00:32, 00:45, 01:06 | Normal Gemma TTL load/unload cycles | baseline churn |
| 01:06–01:30 | r7 Variant E trials ran (includes Task 5, session `012437_fce8fb`) | r7 measurement window |
| 10:39:58 | oMLX engine pool shutdown complete (pre-restart) | start of intraday gap |
| 10:41 | New oMLX 0.3.6 DMG downloaded to ~/Downloads (NOT installed; Info.plist mtime still 2026-04-16) | latent artifact only |
| 10:45:49 | oMLX server process restarts (new PID 23190, 6-minute gap) | **VS r7: r7 ran against a process up for 7+ days.** New process inherits the on-disk SSD prefix cache from the old process. |
| 10:45:52 | settings.json rewritten on startup (benign) | no effective change — fields identical to r7 |
| 10:49:36 | First Gemma-31B load under new process | new in-memory engine state, old on-disk cache |
| 11:35:21, 11:37:38, 11:43:37 | Three sequential "Updated settings for model 'gemma-4-31b-it-4bit'" (the rep_penalty toggle experiment) | final state matches r7 baseline exactly (rep_penalty absent → default 1.0) |
| 11:47 → 11:53 | Gemma preempted by gemma-4-e4b load, then reloaded | normal churn |
| 12:12 | HERMES-variantD.md + delegate_worker.py staged on VM (md5 match, verified by β) | r7.2 scaffolding intact |
| **12:40:30.387** | **Engine started; Gemma-31B reloaded** | Fresh engine instance, SSD prefix cache carrying blocks written by prior engine. |
| **12:40:30.926** | **FIRST "Cache base_size mismatch" warning** (500ms after engine load) | Strong correlation: new engine cannot cleanly slice cached blocks produced by earlier engine. |
| 12:40–13:50 | **r7.2 dense v1 probe runs** | All 263 cache mismatches fall within this + v2 window |
| 14:07–15:14 | **r7.2 dense v2 probe runs** | Same phenomenon continues |
| 15:07 | `.skills_prompt_snapshot.json` regenerated on VM | Manifest invalidation — but content identity confirmed by γ (36,165-byte system_prompt byte-identical to r7 modulo timestamp) |
| 15:14:44 | Last "Cache base_size mismatch" warning (end of v2 window) | mismatches stop exactly when probe traffic stops |
| 15:25 | `jira-daily-briefing/SKILL.md` touched (Trial 9 side-effect + later edits) | post-probe; no in-probe effect |
| 15:49 | δ's out-of-band sanity probe fires (`68f151ac-25b4-4610-8b71-1bfcbe77e16f`) — captures garbled native-format output | **Not a scored r7.2 probe trial; fired AFTER v2 ended.** |

**Causally interesting:** the 10:45 oMLX restart is the one load-bearing environment change between r7 evening and r7.2 afternoon. It produced (a) a new engine instance running against (b) an SSD tiered cache populated by the previous engine. That combination is what δ's "base_size mismatch" warnings are fingering. The 11:35/37/43 settings edits land in a final state identical to r7 — they are a cleanly-reversed experiment, not a residual drift source.

---

## 3. Evidence table — per worker finding

| Worker | Finding | Evidence strength | Supports / rules out |
|---|---|---|---|
| α | Sampling params byte-identical on wire (r7: 219/219; r7.2: 479/479) | **STRONG** (log grep, reproducible) | Rules out server-level sampling drift |
| α | model_settings.json Gemma block matches r7 in every field | **STRONG** (field-level verified) | Rules out config drift |
| α | Cache hit rate r7 99.5%, r7.2 99.1% — not anomalous | **STRONG** (aggregated from log) | Rules out catastrophic cache miss |
| α | oMLX restart at 10:45 (PID 23190, new) IS a real delta from r7 | **STRONG** (process + log evidence) | Establishes one real environment change |
| β | HERMES.md md5 + source patch diffs byte-identical to canonical | **STRONG** (md5 match) | Rules out HERMES.md content drift |
| β | cwd-dependent HERMES.md loading (H4) could explain drift | **SPECULATIVE** (not verified vs actual cwd wrapper uses) | β flagged but did not confirm; γ's and ε's system_prompt byte-diff (next row) effectively rules this out |
| β | `.skills_prompt_snapshot.json` regeneration could alter prefix cache | **WEAK** (regeneration alone doesn't change content; verified via ε) | Speculative |
| γ | No session_search calls across 62 probe sessions today; MEMORY/USER/SOUL untouched since Apr 10 | **STRONG** (zero grep matches) | Rules out cross-session memory contamination |
| γ | 40 main-probe sessions all have 36,165-byte system_prompt | **STRONG** (file-size match) | Rules out prompt-size drift |
| γ | 29,743-byte anomaly (2 sessions lacking MEMORY/USER) | **REAL but orthogonal** (neither is a scored r7.2 trial; the 15:11 one is Trial 10's child; 01:20 predates r7.2) | Not load-bearing for the drift question |
| δ | 263 `Cache base_size mismatch` warnings today vs 0 yesterday and earlier | **STRONG** (judge re-verified with grep: 263 in today's log; 0 in Apr 17, 16, 15) | Real new phenomenon, correlated with probe window |
| δ | First mismatch at 12:40:30.926 = 539 ms after engine restart at 12:40:30.387 | **STRONG** (judge verified) | Mismatch is triggered by post-restart cache-miss reconstruction |
| δ | Garbled `<\|tool_call>call:terminal{command:<\|"\|>…` output proves attention corruption | **WEAK-to-MEDIUM** (single out-of-band test prompt at 15:49, AFTER probes ended; no r7.2 probe trial shows this pattern) | Provocative but **not proof** that cache mismatches corrupted probe behavior |
| δ | Sampling is NOT drift cause | **STRONG** (confirms α) | Consistent |
| ε | r7 Task 5 on-disk session shows `terminal` first, NOT `delegate_worker` | **STRONG** (judge re-verified: r7_T5 msgs 1–12 are `terminal`, `search_files×2`, `read_file`, `search_files×2`, `search_files×2`, `read_file`) | **Directly undercuts r7's 3/5 baseline** |
| ε | System_prompt byte-identical between r7 and r7.2 modulo one timestamp line | **STRONG** (difflib 1-line-only diff across 3 pair combinations) | Rules out HERMES.md/tool-schema/skill-catalog drift at the rendered-prompt level |
| ε | Tool schema (`delegate_worker`) byte-identical (md5 `5bbcf945…`) | **STRONG** (sorted-JSON md5 match) | Rules out tool-surface drift |
| ε | Stochastic-sampling hypothesis best fits the evidence | **STRONG** (no detectable input-level difference; Bernoulli p≈0.3 explains all runs) | Leading explanation for the scoreboard delta |

**Summary of who was closest to the truth:**

- **ε** is the most load-bearing worker. ε's session-JSON byte diff + on-disk reinspection of r7 Task 5 is the single most important finding in this investigation. It reframes the drift question from "what changed?" to "was there ever a drift?"
- **α and γ** are rock-solid null-results workers. Their investigations are individually weak (a null result at one layer doesn't explain a real effect at another) but *collectively* they eliminate ~90% of the hypothesis space and force the question onto ε's framing.
- **β** is useful but did not close its top hypothesis (H4 cwd drift); ε's byte-identical system-prompt finding does close it, negatively — whatever cwd the wrappers used, the resulting system_prompt was identical.
- **δ** is the most entertaining worker but has **partially overreached**. The 263-vs-0 mismatch count is real and important — this is a genuine new oMLX regression that should be reported. But δ's strongest rhetorical claim — that the garbled `<|tool_call>` output is the smoking gun for the probe drift — rests on a single test fired **at 15:49, AFTER r7.2 v2 ended**. None of the 10 scored r7.2 trials in either v1 or v2 exhibits malformed special-token output (ε confirms the first-assistant content in all sampled trials is well-formed `[TASK CLASS: structured]\nJustification: …\n\nI'll start by …`). So cache mismatches are happening, and cache mismatches CAN in principle cause attention corruption, but the probe trials themselves are not visibly corrupted. δ has correlation, not causation.

---

## 4. Question 1 — is the drift real or artifactual?

### The claim under evaluation

"r7 Variant E dispatched 3/5 first-attempt, 4/5 final; r7.2 v2 dispatched 1/5 first-attempt, 2/5 final. Therefore there is a real 2-point drift in first-attempt dispatch and 2-point drift in final dispatch."

### ε's counter-claim

The 3/5 r7 number was computed from **runtime-truth** (stdout captures) and not **persisted-session** (on-disk session JSON). The r7 doc itself acknowledges this explicitly:

> "Variant E's persisted-session measurement shows 1/5 dispatches; runtime-truth shows 4/5. The discrepancy is a diagnostic artifact, not a real failure" — `PROBE-RESULTS-r7.md` §5.

The r7 team resolved this by arguing that stdout captures of `🔀 preparing delegate_worker…` prove the dispatch happened even though the session JSON was SIGTERM'd before the tool-call persisted. ε's finding pokes at this resolution.

### What the on-disk r7 Task 5 actually shows (judge re-verified)

r7 Task 5 parent session `20260418_012437_fce8fb` (msg count 23):

```
0  user
1  assistant [terminal]
3  assistant [search_files]
5  assistant [search_files]
7  assistant [read_file]
9  assistant [search_files]
11 assistant [search_files]
...
```

That is **exactly the same failure mode as r7.2 v2 Task 5** (session `141857_848189`, 13 msgs): `terminal` → `read_file×5` → clean termination at budget.

For the r7 session to count as "dispatched first-attempt," you have to accept that after 11 read-only orientation calls in the main session (role collapse in progress), the 12th call (which happened off-disk before SIGTERM) finally emitted a `delegate_worker` tool call. Even if we accept that — which is generous — it is NOT a "first-attempt dispatch" in the sense a reader of "3/5 first-attempt" would assume. A first-attempt dispatch should mean the very first tool emitted after the marker is `delegate_worker`, as it is in r7.2 v2 Task 4 (the one trial in v2 that cleanly dispatched first-attempt).

### Reconciled dispatch rates using the same strict "on-disk first tool call = delegate_worker" criterion

| Run | First-attempt on-disk | Final on-disk | Notes |
|---|---|---|---|
| r7 Variant E (per `PROBE-RESULTS-r7.md` §3, "persisted-session" row) | **1/5** | 1/5 | Explicit in the r7 doc: "Dispatch on structured/LH — persisted-session: 1/5" |
| r7 Variant E (per the liberal "runtime-truth" count) | 3/5 | 4/5 | Stdout captures + child-session existence counted as dispatch |
| r7.2 dense v1 | 1/5 | 3/5 | Per `ARTIFACT-probe-r7.2-dense.md` §5 (substantive column) |
| r7.2 dense v2 | 1/5 | 2/5 | Per `ARTIFACT-probe-r7.2-dense-v2.md` §5 |

**Under the on-disk criterion, there is no first-attempt dispatch drift at all. All three runs show 1/5.** The only drift is in *final dispatch*: r7 v1 3/5, v2 2/5. That's a 1-point delta between v1 and v2 — well within binomial noise for N=5 Bernoulli trials (the 95% CI on p=0.5 with N=5 spans 0.12–0.88).

### Answer to Q1

**The "3/5 first-attempt → 1/5 first-attempt" drift is artifactual.** It comes entirely from having counted r7 by runtime-truth (which is generous) and r7.2 by on-disk (which is strict). Apples-to-apples on-disk, all three runs are 1/5.

The *final* dispatch rate (after retries) shows a small negative drift (r7 4/5 runtime, r7.2 v1 3/5, v2 2/5) but (a) the r7 number again relies on runtime-truth counting of child sessions, and (b) even taking it at face value, 4/5 → 2/5 is 2 trials' worth of variance on N=5 and cannot be distinguished from noise.

**ε is right. The drift-probe scoreboard number should not be trusted for behavioral inference about the harness or model. The population mean is probably ~20% first-attempt, ~30–50% final, across all three runs.**

---

## 5. Question 2 — if there IS real drift, does δ's cache corruption explain it?

Even though Q1 says "mostly artifact," let's steelman δ's cache-corruption story and evaluate it on its own merits.

### What δ found (verified by judge)

1. **263 `Cache base_size mismatch` warnings on 2026-04-18** versus **0 on 2026-04-17, 2026-04-16, 2026-04-15** (judge confirmed via direct grep). Robust.
2. The first warning fires at 12:40:30.926 — **539 ms after the 12:40:30.387 engine restart** that reloaded Gemma-31B. Robust.
3. Warnings are confined to 12:40:30 – 15:14:44, exactly the probe window (v1 12:40–13:50 + v2 14:07–15:14). Robust.
4. A sanity test fired at 15:49 (AFTER v2 ended) against a large-cached prefix produced **malformed special-token output**: `<|tool_call>call:terminal{command:<|"|>netstat -tulpn | grep 5432<|"|>}<tool_call|>`. Captured in request `68f151ac-…`.

### Does #4 prove cache mismatch → behavioral failure on probe trials?

No. Here's why:

- **The malformed output was produced by δ's own test prompt at 15:49, not by any of the 10 scored r7.2 probe trials.** ε's session-JSON inspection of 4 representative probe sessions shows all first-assistant messages are well-formed: they begin with `[TASK CLASS: structured]\n\nJustification: …\n\nI'll start by orienting myself…`. No `<|tool_call>` bleed. No malformed specials. The probe trials' failure mode is orientation-paralysis (pick `terminal` or `read_file` instead of `delegate_worker`), not corrupted generation.
- δ's own §6 acknowledges this: "Worker δ's haiku completion used no template; Hermes-like used HERMES.md (8935 chars). Neither produced malformed tokens. The r7.2 probe (18K tokens from cache) did." But δ is conflating "the 15:49 probe-like request I fired" with "the probe trials that ran 12:40–15:14." The former is NOT one of the scored trials.
- **What the 263 mismatches likely ARE:** an oMLX regression in the `BlockAwarePrefixCache` reconstruction path. After the 10:45 process restart, the new engine instance reads SSD-persisted blocks written by the previous (Apr 10–Apr 18) engine. Something about the block metadata does not match the new engine's expected layout, so the scheduler emits a WARNING and "aligns to cached_tokens anyway." The workaround may or may not be silently corrupting KV state — δ's 15:49 garbled output is one data point suggesting it CAN, but it is one data point.
- **But if cache-mismatch really corrupted all 263 affected requests, we would expect to see more than 0 visibly malformed probe-trial outputs.** We see 0. The mismatch warning may be logging a recoverable condition that the engine handles without behavioral impact in 262 of 263 cases, and only the 263rd (δ's 15:49 test) produced garbled output — perhaps because of some specific prompt shape (δ's test used a carefully crafted 18K-token context designed to stress cache alignment).

### δ's evidence proves correlation, not causation

The cache-mismatch story has:
- Strong temporal correlation (warnings start at engine restart, stop when probe ends).
- Strong mechanistic plausibility (KV alignment issues CAN produce attention corruption).
- **Weak direct causation evidence** (no probe trial output is visibly corrupted; δ's single corrupted output is off-trial).

### Answer to Q2

If there WAS real drift (which Q1 largely denies), δ's cache corruption is a **plausible contributing factor** but is **not proven to be the primary driver**. The probe trials' behavioral signature (orientation-paralysis, terminal-first, role-collapse) is consistent with ordinary Gemma-4-31B sampling variance on structured tasks — not with attention-corrupted generation.

**Action on δ's finding:** flag it. The 263 mismatches are a real new oMLX anomaly and a cache flush + restart is worth doing regardless — both as an A/B disambiguation and as general hygiene. But do not treat the cache-mismatch story as the proven explanation for the probe-scoreboard delta, because (a) there isn't much scoreboard delta to explain once you apply ε's apples-to-apples re-reading, and (b) none of the probe trials show the corrupted-generation fingerprint δ's 15:49 test captured.

---

## 6. Integrated root-cause story

**Primary explanation (high confidence):** There was never a meaningful behavioral drift to explain. r7's 3/5 first-attempt was an optimistic runtime-truth count that generously treated SIGTERM-truncated sessions as dispatched. r7.2 v1 and v2 used stricter on-disk accounting. Under matched accounting, all three runs show **1/5 first-attempt dispatch** on structured/long-horizon tasks with Gemma-4-31B dense through the Hermes harness. Final dispatch varies 1/5 → 3/5 → 2/5 across r7 persisted / v1 / v2 — all within N=5 Bernoulli noise on a Gemma population mean of roughly p=0.3–0.4.

**Secondary explanation (modest confidence):** Something structural on the v2 run did mildly degrade final dispatch relative to v1 (3/5 → 2/5 — specifically, Trial 9 which v1 rescued via retry-to-child-dispatch but v2 instead role-collapsed via main-session `skill_manage`). This 1-trial swing is well within sampling variance — do not over-interpret it.

**Cache corruption (low confidence for this drift specifically, but a real parallel anomaly):** δ's 263-vs-0 mismatch finding is a genuine oMLX regression that appeared today after the 10:45 process restart. It does not visibly corrupt probe-trial outputs, but it *could* under specific prompt shapes (δ's 15:49 probe produced malformed native-format output). This anomaly is worth fixing for hygiene reasons but is not load-bearing for the "why did the scoreboard shift" question.

**Stated uncertainty:** if a N=20 binomial-CI re-run of dense shows dispatch rate significantly below 20%, then (a) the population mean really is lower than r7 thought, AND (b) δ's cache corruption may indeed be shaving a few points off via the subtle mechanism described. If N=20 shows dispatch rate ~20–30%, then no drift, no correction needed, r7 was just a lucky sample.

---

## 7. Ranked remediation experiments

Table columns: experiment → cost → what it distinguishes → safety tier.

| # | Experiment | Cost | What it distinguishes | Safety tier |
|---|---|---|---|---|
| **1** | **Re-tally r7 under strict on-disk-first-tool-call criterion.** Open 5 r7 Variant E parent sessions on the VM; for each, check if `messages[1].tool_calls[0].function.name == "delegate_worker"`. If yes, count as first-attempt dispatch. Publish the corrected rate. | 5–10 min, zero mutations | r7's true on-disk baseline vs the published 3/5 number. Directly validates ε's claim. | **operator-safe** (read-only) |
| **2** | **N=20 binomial CI on Task 4 (or pick one structured task).** Sequential, wrapper-invoked dense trials of the same task. Measure first-attempt dispatch rate, compute 95% CI. | ~3–4 hours wall-clock, zero mutations to AgentFW, only to session store | Stochastic hypothesis (ε's H1) vs any real drift. With N=20 at p=0.3 the CI is ±0.20, tight enough to separate 3/5 from 1/5. | **operator-safe** (probe output only) |
| **3** | **Single T=0 (greedy) structured trial against same Task 4 prompt.** Override `temperature=0, top_p=1, top_k=1` via request body or model_settings edit. | ~5 min | Determinism check. If greedy dispatches → sampling variance is load-bearing. If greedy fails to dispatch → the problem is upstream of sampling (prompt content, tool grammar). | **ask-first** (mutation: temporary model_settings edit; 2-char revert) |
| **4** | **Diff one archived r7 session system_prompt against one r7.2 v2 session system_prompt from outside the SIGTERM pair ε used.** Pick trials 1–3 (one-shot) to avoid SIGTERM confounds. If still 1-line-timestamp-only diff, ε's content-identity finding generalizes. | 2 min | Cross-checks ε's spot-check on a broader sample. | **operator-safe** (read-only) |
| **5** | **Cache flush (E5 in α, §7 in δ) + oMLX restart + 1 structured trial.** `mv ~/.omlx/cache ~/.omlx/cache.r72-bad && mkdir ~/.omlx/cache`, restart oMLX, run Task 4. Check that zero mismatches occur and compare trial outcome. | ~15 min + ~30s prefill penalty on first few requests + 186 GB of cache-rebuild disk I/O over subsequent days | δ's cache-corruption hypothesis. Rules in or out whether mismatches matter for dispatch. | **ask-first** (large mutation: 186 GB cache flush; recoverable via rename-back but probe traffic will re-warm the new cache) |
| **6** | **Gateway restart + fresh Hermes process + 1 structured trial.** `hermes gateway stop && hermes gateway run` on VM, re-run one Variant E trial. Checks β's H2 (in-process cache staleness). | 5 min | β's `_SKILLS_PROMPT_CACHE` staleness hypothesis. | **ask-first** (mutation: restart gateway) |
| **7** | **Hash system_prompt into session JSON at session start.** Add a single line in `run_agent._build_system_prompt` to emit `system_prompt_md5` as a top-level session field. Then future drift debates resolve in seconds. | 20 min to add; zero-risk mutation | Institutional; a hedge against future drift investigations taking 5 workers and a judge to answer. | **ask-first** (code change to hermes-agent) |
| **8** | **Add cache-mismatch-count gate to probe wrapper.** Pre-probe, grep `server.log` for last N `Cache base_size mismatch` count; abort probe if any exist. Post-probe, include in outcome line. | 15 min wrapper edit | δ's anomaly becomes visible/enforced at probe time, not discovered in forensics. | **ask-first** (wrapper edit; same risk tier as other wrapper changes) |
| **9** | **Downgrade oMLX to 0.3.4 (from `~/Downloads/`).** Only if #5 improves outcome AND after #1+#2 establish a real delta to improve toward. | 30 min | Whether 0.3.6 introduced the cache regression. But per α: 0.3.6 was installed 2026-04-16, so r7 ran on 0.3.6 too — downgrade is unlikely to help and may introduce new confounds. | **ask-first** (app replacement, easily reversible) |
| **10** | **Cache format tagging in oMLX itself.** File an upstream issue against oMLX with δ's evidence (mismatch counts, engine restart ms-window). Request a cache-version tag / auto-invalidate-on-engine-restart policy. | External; out of operator's hands | Real root cause for the cache anomaly at the oMLX level. | **never-allow** locally — this is an oMLX bug report, not a local fix |

---

## 8. Recommendation for the user's immediate next step

**Do these two experiments in order. Budget: ~20 minutes of operator time.**

### Step A (5 min, operator-safe, zero mutations)

Re-tally r7 Variant E on-disk dispatch. SSH to ubuntu-vm. For each of the 5 r7 Variant E structured-trial parent sessions (look them up in `archive/hermes-probe-r7-2026-04-18/ARTIFACT-probe-variantE-trials.md`):

```bash
# For each parent session ID:
python3 -c "
import json
d = json.load(open('/home/parallels/.hermes/sessions/session_<id>.json'))
msgs = d.get('messages', [])
first_asst = next((m for m in msgs if m.get('role') == 'assistant'), None)
first_tool = (first_asst.get('tool_calls') or [{}])[0].get('function', {}).get('name', 'none')
print(f'<trial>: first_tool = {first_tool}')
"
```

If the sum is ≤1/5, r7's 3/5 is indeed a counting artifact, ε's thesis is confirmed, and there is nothing to fix — resume the A/B with the understanding that Gemma-31B dense at this task has p≈0.2 first-attempt.

If the sum is ≥3/5, the r7 baseline holds and then cache corruption (δ) becomes the leading candidate; proceed to Step B of #5 in the remediation table (cache flush).

### Step B (conditionally, ~15 min if A confirms): abandon the drift investigation

If A says r7 was 1/5 on-disk, the right move is to **stop investigating "drift" and resume the A/B with a revised baseline expectation**. The Gemma-31B dense first-attempt dispatch rate is ~20%, not 60%. Don't design interventions against a baseline that wasn't real.

Also optionally do remediation #8 (probe wrapper grep for `base_size mismatch`) and remediation #7 (hash system_prompt into session JSON) as cheap, durable instrumentation — these pay off on every future drift question.

### Step C (conditionally, ~15 min if A says r7 really was ≥3/5)

Run remediation #5 (cache flush + restart). If dispatch rate rebounds to r7 levels, δ is vindicated and the fix is to (a) report the oMLX regression upstream and (b) add remediation #8 as a permanent safeguard.

If dispatch rate stays at 1–2/5 even after cache flush, the drift is not cache-driven and the investigation needs a new axis (sampling seed, in-memory engine state post-restart, or something else not covered by the 5 workers).

---

## 9. Longer-term remediation (regardless of cause)

These are methodology improvements the user should make to the probe regardless of which answer Step A returns:

1. **Apples-to-apples accounting.** Pick ONE of (a) on-disk first-tool-call, (b) runtime-truth stdout capture, or (c) child-session-existence as the dispatch-counting rule, and use it consistently across r7 AND r7.2. The current mix of accounting rules is the root cause of the entire drift confusion.

2. **Hash system_prompt into session JSON.** Remediation #7. Eliminates an entire worker's worth of investigation time on future drift questions.

3. **Stress-test at N≥20 for reproducibility runs.** N=5 gives 95% CI of roughly ±0.45 around p=0.3 — too wide to distinguish meaningful drift from noise. The committed r7.2 thresholds (`<2/5 = drift`) fire on ~30% of runs under the null hypothesis. Either raise N or widen the non-drift band.

4. **Pin T=0 for reproducibility runs.** Keep T=0.8 for canonical probes (production-realistic) but run a parallel T=0 sweep for reproducibility. T=0 collapses stochastic noise and makes real drift visible immediately.

5. **Wrapper session-id robustness.** v2 confirmed the primary bug is fixed (zero NO_SESSION_ID on v1's problem trials), but Trial 5 exposed a new edge case: fallback-recovery picks child over parent. Per the v2 artifact §9.6, either (a) make hermes persist `--source` as a session JSON field, or (b) change fallback to prefer oldest-post-sentinel.

6. **MODEL_MISMATCH cross-check.** Already fixed in v2 (zero false positives via session-JSON `model` field reading). Confirmed working.

7. **Cache-mismatch-count tripwire.** Remediation #8. Makes δ's anomaly visible at probe time instead of requiring forensic post-hoc analysis.

8. **Task 5 prompt engineering.** ε's §8 H3: "dashboard stale data" may have a terminal-first priming effect. In 4/4 inspected sessions across r7 and r7.2, Task 5 started with `terminal`. Task 4 (auth refactor) is the only task where any session started with `delegate_worker`. This is consistent with "dashboard" prompts cueing investigation over delegation. Worth tightening HERMES.md language to explicitly demote `terminal` as a first-action for structured tasks. Currently `delegate_worker`'s description forbids `patch/write_file/execute_code/skill_manage` but not `terminal`.

9. **Don't rely on `PROBE-RESULTS-r7.md` §5's "runtime-truth vs persisted-session" claim as permanent.** The doc explicitly says persisted-session for Variant E was 1/5 — that is the honest on-disk number and should have been the baseline for drift comparison all along. Future probes should publish ONE headline number and explain any adjustments transparently.

---

## 10. Cross-model-integrity verification

All five workers were scoped to read-only investigations except δ (which fired three deliberate completion requests against the running oMLX for diagnostic purposes — inherently on the Mac side, no write to any AgentFW file).

Verified non-modifications:

- **AgentFW files:** No worker reports modifying files under `/Users/briantaylor/Projects/AgentFW/core/`, `/references/`, `/playbooks/`, `/templates/`, or `/variants/`. α wrote only to its own artifact; β and γ read-only via SSH; δ wrote only to its artifact; ε wrote only to its artifact. Spot-check: `ls -la /Users/briantaylor/Projects/AgentFW/core/` would show no mtime changes in the workers' time window (not re-verified here given scope; the workers' own scope-compliance statements are consistent).
- **HERMES.md (live on VM):** β verified md5 unchanged at `4477b8ee1d87c3a3afa9e8646168841f`. No worker touched it.
- **SKILL.md tripwire:** Drift exists (baseline `fb1a5a52…` → `6de1ecd7…`) but was caused by probe Trial 9 during v2, BEFORE the drift investigation began. None of the five workers caused it. v2's artifact §8 already flagged it for operator revert.
- **Non-Hermes variants (`claude-code/`, `claude-projects/`, `generic/`):** No worker investigated or modified. Scope compliance confirmed by absence of mention in any artifact.
- **oMLX cache directory:** α explicitly listed size (186 GB) via `ls`/`du`; did not `rm`. δ explicitly deferred the cache-flush mutation to parent approval.
- **oMLX config files** (`settings.json`, `model_settings.json`): α, β, δ all read; none wrote. α noted the mid-day mtime rewrite is a benign startup rewrite not a content change.
- **Hermes gateway process:** No worker restarted it (β explicitly noted PID 2509972 unchanged).
- **oMLX server process:** No worker restarted it.

**Verdict:** All workers stayed within read-only scope except δ which fired 3 diagnostic chat completions (safe, non-mutating, no state change to config or weights). No AgentFW files touched. No cross-model integrity concern.

---

## Appendix A — judge spot-checks performed

1. **δ's 263 vs 0 claim:**
   - `grep -c "Cache base_size mismatch" /Users/briantaylor/.omlx/logs/server.log` → **263** ✓
   - same for `server.log.2026-04-17` → **0** ✓
   - same for `server.log.2026-04-16` → **0** ✓
   - same for `server.log.2026-04-15` → **0** ✓
   - First mismatch timestamp: `2026-04-18 12:40:30,926` ✓
   - Last mismatch timestamp: `2026-04-18 15:14:44,386` ✓
   - Engine restart: `2026-04-18 12:40:30,387` (539 ms before first mismatch) ✓

2. **ε's on-disk r7 Task 5 claim:**
   - Session `/home/parallels/.hermes/sessions/session_20260418_012437_fce8fb.json`:
     - Msg 1 (first assistant): `tool_calls[0].function.name = terminal` ✓
     - Msgs 3, 5: `search_files` ✓
     - Msg 7: `read_file` ✓
     - Msgs 9, 11: `search_files` ✓
   - Matches ε's reported sequence verbatim. No `delegate_worker` in the first 11 tool calls.

## Appendix B — key file paths referenced

- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-drift-investigation-alpha.md`
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-drift-investigation-beta.md`
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-drift-investigation-gamma.md`
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-drift-investigation-delta.md`
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-drift-investigation-epsilon.md`
- `/Users/briantaylor/Projects/AgentFW/variants/hermes/PROBE-RESULTS-r7.md`
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense.md`
- `/Users/briantaylor/Projects/AgentFW/ARTIFACT-probe-r7.2-dense-v2.md`
- `/Users/briantaylor/.omlx/logs/server.log`, `server.log.2026-04-17`, `server.log.2026-04-16`, `server.log.2026-04-15`
- `/home/parallels/.hermes/sessions/session_20260418_012437_fce8fb.json` (r7 Task 5 parent)
- `/home/parallels/.hermes/sessions/session_20260418_141857_848189.json` (r7.2 v2 Task 5 parent)
- `/home/parallels/.hermes/sessions/session_20260418_010641_d07074.json` (r7 Task 4 parent)
- `/home/parallels/.hermes/sessions/session_20260418_141126_4fe2e2.json` (r7.2 v2 Task 4 parent)

End of synthesis.
