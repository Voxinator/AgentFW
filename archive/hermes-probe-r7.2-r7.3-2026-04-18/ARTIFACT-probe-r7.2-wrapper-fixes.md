# ARTIFACT — probe-r7.2 wrapper fixes

Date: 2026-04-17
File modified: `/Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh` (only)
Final md5: `9fd987c5e18e6aa70a05426c473fc0a3`

## Fix 1 — Session-ID fallback recovery

**Before.** When `timeout 900` (previously 600) killed `hermes chat` mid-turn, stdout
lacked the `session_id: ...` marker and the wrapper exited
`RESULT=ERROR detail=NO_SESSION_ID` with no chance to evaluate the real session.

**After.** Before the `hermes chat` invocation (just after `log "task:..."`), the
wrapper now touches a per-run sentinel on the VM:
`/tmp/probe_sentinel_${SOURCE_PREFIX}_run${RUN_NUM}`. If the primary regex misses
the session_id on stdout, the wrapper SSHes to the VM and runs a two-stage
fallback scan:

1. `find ~/.hermes/sessions -name 'session_*.json' -newer $SENTINEL` piped through
   `grep -l "$SOURCE_TAG"` — match session files whose JSON content embeds the
   trial's `--source` tag.
2. If the source-tag scan yields nothing, last-resort: most-recently-modified
   post-sentinel session JSON (`-printf '%T@ %p\n' | sort -n | tail -1`).

Primary regex runs first and unchanged, so the fallback never fires on the happy
path. Only the NO_SESSION_ID `OUTCOME` line was modified — it now carries
`MODEL=$MODEL` to match the format of the other OUTCOME lines (previously missing).

**Design decisions the sketch left open.**
- Sentinel path uses `${SOURCE_PREFIX}_run${RUN_NUM}` rather than just `${RUN_NUM}`
  to avoid collisions between concurrent probe legs (dense + sparse) reusing
  run_num 0.
- Source-tag matching uses `grep -l "$SOURCE_TAG"` over the whole JSON file
  rather than a parsed `metadata.source` field — robust to Hermes schema
  variations and does not need a second python subshell.
- Last-resort by-time match is gated behind the source-tag scan; it only fires
  if nothing matched the tag. Prevents picking up an unrelated trial's session
  when tags are intact.

## Fix 2 — Replace log-tail MODEL check with session-JSON model check

**Before.** `tail -500 ~/.omlx/logs/server.log | grep -oE "model=${MODEL}"`
produced MM=MODEL_MISMATCH=no-recent-entry false positives when verbose
Qwen TRACE output rolled the relevant entry out of the tail window.

**After.** Introduced `compute_mm()` helper that SSHes to the VM, runs a small
python3 snippet to read `session_${SESSION_ID}.json`'s top-level `model` field,
and emits one of three MM suffixes:
- empty (match) — most common path
- ` MODEL_CHECK=session-json-missing` (JSON unreadable / field missing)
- ` MODEL_MISMATCH=<actual_model>` (real mismatch, reports the fallback model name)
- ` MODEL_CHECK=no-session` when called with empty SESSION_ID

`compute_mm` is called from the two call-sites that previously set `MM`:
COMPLIANT and RETRY_EXHAUSTED branches. The WRAPPER_ERROR branch (`VERDICT==ERROR:*`)
never set MM before and still does not — left untouched per "same contract".
`OMLX_SERVER_LOG` variable dropped from the config block (no remaining references
outside a comment).

## Fix 3 — TIMEOUT_PER_TURN 600 -> 900

One-line change at line 22. Buys 5 extra minutes for dense-model
structured/long-horizon turns that were brushing the old 600s ceiling.

## Verification

Syntax check:
```
$ bash -n /Users/briantaylor/Projects/AgentFW/probe-variantE-wrapper.sh && echo "syntax OK"
syntax OK
```

Live smoke test (verbatim OUTCOME line):
```
OUTCOME run=0 MODEL=gemma-4-31b-it-4bit RESULT=COMPLIANT attempts=1 elapsed=36s final_session=20260418_140358_e8e6c2 chain="A0:rc=0 | A0:COMPLIANT"
```

MM field absent (empty) => `compute_mm` confirmed session JSON model == MODEL.
Spot-checked the session JSON directly: `model = gemma-4-31b-it-4bit`. No
NO_SESSION_ID error, primary regex hit on first try, fallback path never fired.
Elapsed 36s (cold-ish load within the 10-15s expected range plus a few seconds
of tool-call overhead).
