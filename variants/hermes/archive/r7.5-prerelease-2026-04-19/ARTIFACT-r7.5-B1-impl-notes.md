# ARTIFACT — r7.5 B.1 Wrapper SIGTERM Tier-1 Mitigation Impl Notes

**Worker:** B.1 implementation worker (Tier 1 wrapper-side, no VM changes)
**Date:** 2026-04-19
**Target file:** `/Users/briantaylor/Projects/AgentFW/probe-variantG-wrapper.sh`
**Research dependency:** `ARTIFACT-r7.4-sigterm-research.md`
**Design dependency:** `PLAN-r7.4-wrapper-sigterm-fix-design.md` §3 Phase 2a
**Coordination:** Workstream B.2 (`probe-variantG-check.py` adds `--expected-prompt-prefix` / `ERROR:WRONG_SESSION` verdict). Both workers ran concurrently; my wrapper builds the coupling, documented below.

---

## File state

| | md5 | line count |
|---|---|---|
| Before (from A.1 scaffold) | `39e50bf78d66ce01c3c73a4640eede95` | 259 |
| After (this worker's edits) | `42b51b4c1dbd7f87aa53b4e9e49a5982` | 378 |

Delta: **+119 lines** (net additions — no deletions beyond the 4 lines replaced inside the fallback block for the new candidate-iteration logic).

`bash -n` exit code: **0** (silent — syntax clean).

---

## Change 1 — `TIMEOUT_PER_TURN` env override

**Line:** 34 (was previously line 34 in A.1 scaffold, unchanged position).

**Unified diff:**

```diff
@@ -33,1 +33,1 @@
-TIMEOUT_PER_TURN=900
+: "${TIMEOUT_PER_TURN:=900}"  # r7.5-B1: env-overridable; default preserves r7.4 MoE comparability
```

**Rationale:** The `:=` POSIX parameter expansion idiom: if the caller exported `TIMEOUT_PER_TURN=N` before invoking the wrapper, `N` is used; otherwise the variable is assigned `900`. Preserves the r7.4 MoE default (important for cross-variant comparability) while allowing T6 / T10 long-horizon trials in r7.5 to use longer budgets without a wrapper edit.

**Smoke test (inline expansion check):**
```bash
$ TIMEOUT_PER_TURN=1500 bash -c ': "${TIMEOUT_PER_TURN:=900}"; echo $TIMEOUT_PER_TURN'
1500
$ bash -c ': "${TIMEOUT_PER_TURN:=900}"; echo $TIMEOUT_PER_TURN'
900
```

---

## Change 2 — Anti-child-attachment content-match + WRONG_SESSION verdict

**Line ranges:**
- EXPECTED_PREFIX_B64 computation: 167–174 (early main-flow, bound once per trial).
- Fallback block restructure: 204–322 (replaces the old 187-line-204 block). New helper `read_candidate_prefix_hex` lives at lines 242–275. Candidate-iteration loop at 277–298. Acceptance + WRONG_SESSION emission at 299–322.
- `run_check` coupling with B.2: lines 68–78 (passes `--expected-prompt-prefix-b64 $EXPECTED_PREFIX_B64`).

**What changed, narrative:**

1. **Early-bound expected prefix** (line 174). Compute `EXPECTED_PREFIX_B64` once from `printf '%s' "$TASK_TEXT" | head -c 80 | base64 | tr -d '\n'`. Raw-byte safe (handles newlines, quotes, non-ASCII). Reused by both the fallback content-match and every `run_check` invocation.

2. **Fallback candidate collection** (lines 224–229). Unchanged from A.1 scaffold — source-tag scan is primary, most-recent-post-sentinel is last-resort. Removed the final `tail -1` collapse: we now need the FULL candidate list so we can content-check each one in order, not just the newest.

3. **Candidate iteration with content-match** (lines 277–298). For each candidate session JSON, read its `messages[0].content` on the VM via a short Python snippet that: (a) opens the JSON, (b) prefers the first user-role message in `messages[]` (defensive against any future system-turn prepend — Hermes research Q8 confirmed `[0].role: user` in practice, but we don't hardwire that assumption), (c) utf-8-encodes the content, (d) takes first 80 bytes raw, (e) emits hex. Compare locally to `EXPECTED_PREFIX_HEX` (same 80 bytes of `TASK_TEXT`). Accept the first match; break on success.

4. **Partial-write retry** (lines 246–272). If the VM-side read returns empty hex (content missing or session mid-flush), sleep 1s and retry once. If still empty, skip that candidate and continue to the next. Chosen budget: 1 retry × 1s. More would add latency during batch runs for pathological session-disk-sync cases that shouldn't exist in practice (AtomicJSONWrite is tmpfile+rename, so partial-write windows are sub-ms).

5. **WRONG_SESSION emission** (lines 314–316). When `CANDIDATE_COUNT > 0` but no candidate content-matches, emit:
   ```
   OUTCOME run=$RUN_NUM MODEL=$MODEL RESULT=ERROR detail=WRONG_SESSION final_session=<last_cand_sid> reason=content_mismatch candidates=$CANDIDATE_COUNT chain="A0:rc=$RC | fallback_rejected"
   ```
   Exit 0 (same convention as other ERROR results — exit code is for process success, not result class).

6. **B.2 check-script coupling** (lines 68–78). `run_check` now passes `--expected-prompt-prefix-b64 $EXPECTED_PREFIX_B64` to the check script. On B.2's side (out of my scope), the check script should:
   - Decode base64.
   - Read first user message from session JSON.
   - Compare first 80 bytes.
   - On mismatch, return `ERROR:WRONG_SESSION` as the first stdout line.
   The existing VERDICT loop (lines 239–242 in the final file) already treats `ERROR:*` verdicts as `RESULT=WRAPPER_ERROR detail=ERROR:WRONG_SESSION` — no further handling needed. This is a defense-in-depth layer: even if my fallback content-match accepts a bogus session (it shouldn't), B.2's in-check verification will catch it.

### Choice of N=80

Confirmed no 80-char prefix collisions across the 10 probe tasks in `probe-tasks.md`:

| # | First ~80 chars (truncated for display) |
|---|---|
| 1 | `What's the capital of France?` (29 chars) |
| 2 | `In /home/parallels/scratch/scratch.py there is a variable named \`foo\`. Rename ` |
| 3 | `On line 47 of auth.py there's a NullPointerException when \`user\` is None. Add ` |
| 4 | `Refactor the auth module to use the new session store. Three files need change` |
| 5 | `The dashboard sometimes shows stale data after a user hits Save. It's intermit` |
| 6 | `Build a new export feature for our product. Users should be able to export th` |
| 7 | `Summarize this meeting transcript in under 200 words.\n\n[INSERT 2000-TOKEN TR` |
| 8 | `Write a one-off script to count files larger than 10MB in ~/Downloads and pri` |
| 9 | `The Jira daily briefing cron has been silently failing on some days — no noti` |
| 10 | `Migrate our Postgres 12 database to Postgres 16 with zero downtime. Production` |

All 10 diverge within the first 10–15 characters. 80 is generous headroom: it tolerates minor edits (punctuation, trailing whitespace, a re-phrased preamble) without being brittle; and it's short enough that we don't accidentally compare the whole prompt body where quoting artifacts could creep in.

**If a future task set adds two prompts that share an 80-char prefix:** bump to N=160 at both the B64 computation (line 174) and the Python `[:80]` slice in `read_candidate_prefix_hex` (line 260), then document in HANDOFF.

### Edge cases

| Case | Handling |
|---|---|
| `TASK_TEXT` contains embedded newlines | Raw-byte compare via utf-8 encode → byte slice. No shell-quote parsing. Both sides use identical byte-stream derivation. Safe. |
| `TASK_TEXT` contains double quotes / backticks | Same — raw-byte compare bypasses shell quoting. Safe. |
| `TASK_TEXT` is shorter than 80 bytes (e.g. Task 1: 29 chars) | `head -c 80` silently returns fewer bytes; both sides are truncated identically; compare still works. Safe. |
| `messages[0].role != "user"` (future system-turn prepend) | Helper iterates `messages[]` and picks the first user-role entry. Falls back to `messages[0]` only if no user message found. Defensive. |
| Session JSON partially written (race between `ls` and `json.load`) | `json.load` throws, helper catches Exception → returns empty hex → retry after 1s → if still empty, candidate is skipped (not treated as WRONG_SESSION). |
| Source-tag scan returns multiple candidates | Now iterates all; content-checks each; accepts first match. Old A.1 behavior (`tail -1` single collapse) is superseded. |
| All candidates fail content-match | Emit `ERROR:WRONG_SESSION`; exit 0. No silent child-session attachment. |
| Zero candidates returned (neither source-tag nor last-resort finds anything) | Emit `ERROR:NO_SESSION_ID` (unchanged from A.1 semantics). |

### Edge cases deferred to Tier 3 (VM side)

| Case | Deferred to | Why |
|---|---|---|
| SIGTERM actually landing during parent's LLM call → no session JSON ever exists | Tier 3 Option A (install `signal.signal(SIGTERM, ...)` in `cli.main()`) | Tier 1 can only rescue when SOMETHING is written to disk. If parent process is killed before any `_persist_session` runs and no child exists either, there's nothing to recover. My wrapper correctly emits `NO_SESSION_ID` in that case — the distinction between "no parent JSON, only a child (child was a false positive)" and "nothing at all" is now observable. |
| SIGKILL-after-grace killing the parent mid-persist (truncated JSON) | Tier 3 | Would manifest as `json.load` failure → empty hex → skipped candidate. Acceptable degraded behavior. |
| Multiple concurrent trials racing for the same session-dir slot | Tier 3 | Sentinel is per-run; source-tag is per-run. Collision only if two trials with the same `SOURCE_PREFIX-run${RUN_NUM}` are in-flight, which is a harness-level invariant violation. Out of scope. |

---

## Change 3 — `MAX_RETRIES` shrink for fallback-recovered sessions

**Line ranges:**
- `FALLBACK_USED=false` initialization: line 205.
- `FALLBACK_USED=true` on acceptance: line 301.
- Retry-budget shrink: lines 329–334 (immediately before the `while [[ $ATTEMPT -le $MAX_RETRIES ]]` loop).

**Unified diff (logical):**

```diff
@@ line 205
+FALLBACK_USED=false

@@ line 301 (inside successful content-match branch)
+    FALLBACK_USED=true

@@ lines 329–334 (before retry loop)
+if [[ "$FALLBACK_USED" == "true" ]]; then
+  log "FALLBACK_USED=true → shrinking MAX_RETRIES from $MAX_RETRIES to 1 for this trial"
+  MAX_RETRIES=1
+  CHAIN="$CHAIN | fallback_recovered_content_verified"
+fi
```

### Trade-off rationale

**(+)** **Fewer bogus NO_MARKER / cascade outcomes.** A trial that required fallback recovery has already burned ~900s to a SIGTERM. Giving it 3 more attempts — each of which can SIGTERM again — triples the risk of a cascade where each retry consumes budget without producing a correct session. A single retry at MAX_RETRIES=1 is the minimum rescue budget: one chance to correct, then commit to RETRY_EXHAUSTED.

**(–)** **A correctly-recovered-but-one-correction-short session now fails where it would have succeeded.** Hypothetically, a session where the model emitted a genuine NO_MARKER on the first turn, where a single correction would still SIGTERM, but a second correction would have succeeded — that session now reaches RETRY_EXHAUSTED after one correction instead of two. Lose a possible recovery.

**Net: positive.** Change 2's content-match ensures the fallback session IS the right session before any retry is attempted. Combined with the observation from `ARTIFACT-r7.4-phase-d-dense-results.md` (T5-run1 line 70, T5-run7 line 73) that the r7.4 failure mode was *mis-attachment leading to NO_MARKER cascades on the wrong session*, not *correct session needing more retries*, Change 3 prunes the dominant failure mode at the cost of a long-tail edge case that's empirically rare.

**If this trade-off is wrong:** the Phase 3 smoke test will show RETRY_EXHAUSTED rates on fallback-recovered trials going UP instead of down. If that happens, bump `MAX_RETRIES=1` to `MAX_RETRIES=2` — still an improvement over 3 — and document.

---

## Coordination with B.2

- **B.2 deliverable (not yet observed from this worker):** `probe-variantG-check.py` with `--expected-prompt-prefix` (or `--expected-prompt-prefix-b64` — see contract below) CLI arg, and `ERROR:WRONG_SESSION` verdict.
- **Coupling contract I built:**
  - Flag: `--expected-prompt-prefix-b64 <base64>` (rationale: base64 is shell-safe without escape gymnastics; raw strings with newlines/quotes break on the ssh command line).
  - Payload: base64(first 80 bytes of TASK_TEXT).
  - Expected check-script behavior: decode, read first user message from session JSON, compare first 80 bytes, emit `ERROR:WRONG_SESSION` as the first stdout line on mismatch.
- **If B.2 instead implemented `--expected-prompt-prefix` with raw text**, a coupling mismatch will surface in Phase 3 smoke (likely as `ERROR:CHECK_FAILED` from argparse rejection). Mitigation: a one-line fix on either side to align the flag name. Low risk; the integration-test smoke is the right checkpoint for this, not my wrapper-only verification.
- **My wrapper is correct even if B.2 hasn't landed:** the `ERROR:WRONG_SESSION` verdict-handling path in the wrapper's retry loop is already covered by the existing `ERROR:*` → `WRAPPER_ERROR` branch (lines 239–242 of final file). No new verdict-handling code was needed on my side.
- **Did I wait for B.2?** No — the coupling is one-way (wrapper sends, check responds). My edits stand independently; if B.2 takes longer, the wrapper just sends an argument the check script ignores (if B.2's argparse uses `parse_known_args`) or fails loudly (if it uses `parse_args` strict). Either outcome is observable at Phase 3.

---

## Verification summary

```
$ bash -n probe-variantG-wrapper.sh && echo OK
OK

$ grep -c "WRONG_SESSION" probe-variantG-wrapper.sh
4

$ grep -c "TIMEOUT_PER_TURN" probe-variantG-wrapper.sh
5    # was 2 in A.1 scaffold (definition + first ssh call); now 5 (definition, log, both ssh calls, and no-hardcode)

$ grep -c "FALLBACK_USED" probe-variantG-wrapper.sh
4    # init, set-true, retry-shrink condition, (comment mentioning it)
```

All three threshold checks pass.

---

## What would disprove this design

1. **Content-match false negative.** If Hermes ever *normalizes* the user prompt before persisting (e.g., stripping trailing whitespace, collapsing repeated spaces, re-encoding), the first 80 bytes of `messages[0].content` won't byte-match `TASK_TEXT[:80]`. Symptom: every fallback trial gets rejected as WRONG_SESSION even when the session is correct. Refutation test: inspect 3 known-good persisted session JSONs on the VM; confirm `messages[0].content` is byte-identical to the input prompt (modulo utf-8 encoding). If Hermes normalizes, switch the comparison to a normalized form (lowercase + whitespace-collapse) or relax to first 40 chars.

2. **Base64 coupling mismatch with B.2.** If B.2 implemented `--expected-prompt-prefix` expecting raw text, the wrapper's base64 payload will not compare equal to the session's raw content. Symptom: every trial returns `ERROR:WRONG_SESSION` from the check script even when both the wrapper's fallback accepted it. Refutation test: run Phase 3 smoke with `MODEL=gemma-4-31b-it-4bit TIMEOUT_PER_TURN=60` on Task 1 (short prompt, no SIGTERM expected); verify VERDICT is `COMPLIANT` not `ERROR:WRONG_SESSION`.

3. **SIGTERM cascade still occurs because content-match keeps selecting SOMETHING.** If the failure mode is actually "parent JSON is written but truncated, and we accept it, then SIGTERM kills us again on the retry," then MAX_RETRIES=1 shrink is insufficient and the right fix is upstream (Tier 3 Option A). Refutation test: compare fallback-recovered trial outcomes across Phase 3 runs with (a) Tier 1 only, (b) Tier 1 + Tier 3. If (a) still shows >20% WRAPPER_ERROR on long tasks, Tier 3 is required.

4. **80-byte prefix collides in a future task set.** If a later probe includes two tasks with an identical 80-char opener (e.g., two variations on "Refactor the auth module..."), the content-match accepts the wrong one. Refutation test: inspect all trial prompts at dispatch time; if any pair shares an 80-char prefix, fail fast with a loud error.

---

## Files touched

- **Wrote:** `/Users/briantaylor/Projects/AgentFW/probe-variantG-wrapper.sh` (edit)
- **Wrote:** `/Users/briantaylor/Projects/AgentFW/ARTIFACT-r7.5-B1-impl-notes.md` (this file)

## Files explicitly NOT touched

- `probe-variantG-check.py` — B.2's domain.
- `probe-variantF-wrapper.sh`, `probe-variantF-check.py` — frozen r7.4 baseline.
- `HERMES.md`, `run_agent.py`, `cli.py` on the VM — Tier 3 territory, not Tier 1.
- No probe trials were run.
