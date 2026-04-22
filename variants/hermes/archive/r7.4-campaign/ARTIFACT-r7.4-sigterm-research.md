# ARTIFACT — r7.4 SIGTERM Session-Loss Research

**Worker:** Phase-1 research worker (read-only on VM)
**Date:** 2026-04-19
**Scope:** Read-only investigation into why `probe-variantF-wrapper.sh` loses the parent session JSON when `timeout 900` fires against `hermes chat` mid-turn.
**Hypothesis under test:** Session persistence is registered as `atexit` and silently skipped under SIGTERM, causing the parent session to never be written.

**Headline finding:** The pre-registered hypothesis is **PARTIALLY DISPROVEN but the failure chain is CONFIRMED.** Session persistence is *not* an `atexit` handler — it is an **inline call** (`self._persist_session(...)`) that executes at the end of `run_conversation()` and at specific error return paths inside the turn loop. However, the symptom is the same: SIGTERM terminates the Python process *before* `run_conversation` returns, so the inline save is never reached. Additionally, the `cli.main()` single-query code path (what `hermes chat -q ...` runs) **does not install any SIGTERM handler** — the SIGTERM→KeyboardInterrupt handler at `cli.py:8432` is only registered inside the *interactive* `cli.run()` method, which single-query mode never enters.

**VM tripwire baseline — START and END both match (unchanged):**
- `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/SKILL.md` = `fb1a5a5208a6cf2fcb8252aac10397eb`
- `~/.hermes/skills/productivity/atlassian/jira-daily-briefing/jira-briefing.sh` = `a1dce6e989527686124d0860830627c9`

---

## Q1 — Which file+function owns session-JSON persistence?

**File:** `~/.hermes/hermes-agent/run_agent.py`

Two methods on the agent class (`HermesAgent`, the class defined around line 300) own the writing path:

| Role | Method | Lines | Purpose |
|------|--------|-------|---------|
| Public entry | `_persist_session(self, messages, conversation_history=None)` | **run_agent.py:1842–1854** | Thin orchestrator — calls `_save_session_log(messages)` then `_flush_messages_to_session_db(...)`. Honors `self.persist_session` flag. |
| JSON writer | `_save_session_log(self, messages=None)` | **run_agent.py:2385–2452** | Cleans assistant content, builds the `entry` dict, and writes atomically via `atomic_json_write(self.session_log_file, entry, indent=2, default=str)` (call site: **run_agent.py:2440–2445**). |

The destination path is computed at construction time:
- `run_agent.py:910–914` — `self.session_log_file = self.logs_dir / f"session_{self.session_id}.json"` where `self.logs_dir = get_hermes_home() / "sessions"`.
- Re-pointed after `/reset` or `--resume` at `run_agent.py:5875`.

Supporting: `atomic_json_write` is imported from `utils` at `run_agent.py:107` (tmpfile-then-rename semantics; does NOT flush under signal-induced death because the outer Python interpreter dies before reaching this call at all in the SIGTERM case).

---

## Q2 — How is that persistence path registered?

**The persistence path is NOT registered via `atexit`, NOT registered via a signal handler, and NOT via a context manager `__exit__`.** It is called **explicitly, inline, from many points inside `run_conversation()`**. This is the critical structural fact that was mis-stated in the pre-registered hypothesis.

Call-site census in `run_agent.py` (lines in the `run_conversation` body, as confirmed by grep):

- Normal end-of-turn save: `run_agent.py:9109` — final `self._persist_session(messages, conversation_history)` at the natural exit of the turn loop.
- Pre-return saves on error/guard paths inside the turn loop: `run_agent.py:7497, 7517, 7597, 7637, 7653, 7666, 7797, 7947, 8055, 8080, 8183, 8210, 8294, 8364, 8414, 8447, 8556, 8609, 8687`.
- Lower-level direct `_save_session_log` calls (bypass the SQLite flush): `run_agent.py:7631, 8605, 8901, 8960, 9008`.

**`atexit` grep results across the Hermes codebase** (`cli.py` only):

- `cli.py:21` — `import atexit`
- `cli.py:8428` — `atexit.register(_run_cleanup)` (inside `HermesCLI.run()`, interactive mode only)
- `cli.py:8608` — `atexit.register(_cleanup_worktree, wt_info)` (worktree cleanup, unrelated to session JSON)
- `cli.py:8692` — `atexit.register(_run_cleanup)` (inside `main()`, single-query mode; runs on normal exit)

**What does `_run_cleanup` do?** Read at `cli.py:586–625`. It cleans up terminals, browsers, MCP servers, auxiliary httpx clients, and fires the `on_session_finalize` plugin hook plus `shutdown_memory_provider`. **It does NOT call `_persist_session`, `_save_session_log`, or any session-JSON write.** Session persistence is orthogonal to `_run_cleanup`.

Conclusion: session-JSON persistence relies entirely on control flow reaching the inline `_persist_session` calls. Any forced exit that bypasses those calls results in data loss for the current turn's messages.

---

## Q3 — Does the main conversation loop periodically flush?

**Yes, but only at turn-level boundaries — not within a turn.** `_persist_session` fires every time the turn loop is about to return (success, error, or interrupt-request), and `_save_session_log` overwrites the JSON file atomically each time (`run_agent.py:2440`). The file contains the *full* message list (not append-only), so any save-point captures everything up to that point.

However, **within a single assistant turn** (while waiting on an in-flight LLM request or a long-running tool call), there is **no periodic flush** — no timer, no heartbeat, no per-message write. Greps for `autosave`, `auto_save`, `flush_interval`, `save_interval`, `periodic.*save` returned zero hits in `run_agent.py`, `cli.py`, and `hermes_cli/main.py`. The filesystem `CheckpointManager` (`run_agent.py:923–926`) snapshots git working trees before `write_file`/`patch`/`terminal` ops — it is unrelated to session JSON.

Consequence: if the process dies mid-turn (SIGTERM during an LLM call or long tool execution), only the *previous* turn's state is on disk. For a single-query invocation (`hermes chat -q ...`, which is one turn from hermes' point of view), that means **nothing** is on disk for the killed parent.

---

## Q4 — What signals does the process currently handle?

Relevant entries from `grep -rn "signal\.\|SIGTERM\|SIGINT\|SIGHUP" ~/.hermes/hermes-agent/ --include="*.py"` (venv/site-packages excluded):

1. **`cli.py:8430–8441` — interactive-mode signal handler (NOT reached by `hermes chat -q`):**
   ```
   8432:        def _signal_handler(signum, frame):
   8434:            logger.debug("Received signal %s, triggering graceful shutdown", signum)
   8435:            raise KeyboardInterrupt()
   8437:        try:
   8438:            import signal as _signal
   8439:            _signal.signal(_signal.SIGTERM, _signal_handler)
   8440:            if hasattr(_signal, 'SIGHUP'):
   8441:                _signal.signal(_signal.SIGHUP, _signal_handler)
   ```
   This handler is installed **inside the body of `HermesCLI.run()`** (the interactive REPL). `cli.main()` dispatches to `cli.run()` only in the non-query branch (`cli.py:8728: cli.run()`). The single-query branch (`cli.py:8696–8724`) calls `cli.agent.run_conversation(...)` directly and **never executes the signal-handler-install code**.

2. **Other `signal.` references** are all outbound — the gateway, terminal tool, process registry, and WhatsApp bridge use `os.kill(..., signal.SIGTERM)` to terminate child processes. None install inbound handlers relevant to the agent loop.

3. **No `SIGINT` handler is installed** at the Python level; Python's default SIGINT handler raises `KeyboardInterrupt` in the main thread.

4. **Zero `KeyboardInterrupt` handlers in `run_agent.py`** — confirmed by `grep -n KeyboardInterrupt ~/.hermes/hermes-agent/run_agent.py` returning empty. `run_conversation` has no top-level `try:` … `finally:` wrapping its body; `grep "^    finally:" run_agent.py` between lines 6800 and 9120 returns only nested `finally:` blocks inside tool loops, not a method-level one.

---

## Q5 — Does `atexit` fire on SIGTERM? Empirical confirmation of root cause.

**Python semantics (stdlib reference):** Handlers registered with `atexit.register` run only when the interpreter exits via `sys.exit()`, falling off the end of the program, or an unhandled exception that unwinds to top-level. They do **not** run when the process is terminated by an uncaught signal such as SIGTERM — the interpreter is killed before `atexit._run_exitfuncs` is invoked.

**Applied to Hermes in single-query mode:**

- `cli.main()` registers only `atexit.register(_run_cleanup)` at `cli.py:8692`. `_run_cleanup` would not save the session anyway (see Q2), but it is also *not invoked* under SIGTERM because Python's default SIGTERM action is process termination, not unwind.
- No `signal.signal(SIGTERM, ...)` is installed on the single-query path (Q4).
- Therefore when `timeout 900` on the wrapper side sends SIGTERM to the `hermes chat` process mid-turn, the process is terminated synchronously by the kernel. `run_conversation` is frozen mid-LLM-call, never returns, the inline `_persist_session` at `run_agent.py:9109` never executes, and no `session_<id>.json` is created for the parent session.

**Empirical confirmation** (Q8 below): the orphan child session `20260419_132928_e11ccb` exists on disk with `message_count: 25` and a `messages[0]` containing the delegate-dispatched goal text. The parent session for T5-run1 that would have contained the trial prompt ("The dashboard sometimes shows stale data...") is absent from `~/.hermes/sessions/`. This matches the predicted failure: child (a separate `hermes chat` call launched by the parent via `delegate_worker.py`, completing normally before the outer timeout fired) persisted; the parent (still mid-turn when SIGTERM fired) did not.

**Hypothesis correction:** The root mechanism is not "`atexit` doesn't fire on SIGTERM" — it's "*inline* save doesn't fire on SIGTERM because the interpreter is dead before the save line is reached, AND no SIGTERM handler converts the signal into a normal unwind." The observable effect (no parent JSON) is identical.

---

## Q6 — Does SIGINT (Ctrl-C) trigger the save path?

**Partially — but with an important caveat for Hermes specifically.**

Standard Python: SIGINT is delivered as `KeyboardInterrupt` in the main thread. If the exception propagates out of `run_conversation`, it unwinds through `cli.main()` and out of the process; `atexit` runs (calling `_run_cleanup`, which still doesn't save), and inline `_persist_session` in `run_conversation` does NOT run because the exception skips over the final save line at `run_agent.py:9109`.

**Hermes-specific check:** `run_conversation` has no method-level `try:` … `finally:` wrapper, and `grep KeyboardInterrupt ~/.hermes/hermes-agent/run_agent.py` returns empty. So a bare Ctrl-C during a long-running assistant turn will **also** skip the save, for the same reason as SIGTERM — Hermes relies entirely on reaching the *inline* save call, and an unhandled `KeyboardInterrupt` propagates past it.

There ARE `try:/except (Exception, KeyboardInterrupt)` blocks in `cli.py` (e.g. `cli.py:8499 except (Exception, KeyboardInterrupt) as e:` in the interactive-mode `run()` exit sequence) which call `_run_cleanup()` — again, no session save.

**Conclusion:** SIGINT does NOT reliably trigger the session-save path in Hermes. It is effectively in the same failure class as SIGTERM for session persistence. The pre-registered claim ("Yes normally — a SIGINT becomes KeyboardInterrupt which unwinds through `sys.exit`, which runs atexit") is correct for the *atexit* sequence, but irrelevant to Hermes because atexit does not perform the session save.

---

## Q7 — Existing explicit save-on-shutdown hooks we could reuse

Enumeration of every mechanism found:

1. **`HermesAgent._persist_session(messages, conversation_history=None)` — `run_agent.py:1842`.**
   Idempotent (guarded by `self.persist_session`), takes current messages, writes both JSON and SQLite. This is the natural target for a SIGTERM handler to call: `_active_agent_ref._persist_session(_active_agent_ref._session_messages)`.

2. **`HermesAgent._save_session_log(messages=None)` — `run_agent.py:2385`.**
   Lighter path — JSON only, no SQLite flush. Internally uses `atomic_json_write`. Good fallback if SQLite state would be too expensive to touch from a signal handler.

3. **Global `_active_agent_ref` — `cli.py:584, 2475`.**
   Module-level reference to the currently running agent; already used by `_run_cleanup` to call `shutdown_memory_provider`. Provides a clean, signal-safe-ish pointer for a handler to reach the agent's persist method.

4. **`HermesAgent._session_messages: List[Dict[str, Any]]` — `run_agent.py:918`.**
   The in-progress message list that `_persist_session` uses when no argument is passed. Updated by `_persist_session` itself (line 1851) but NOT continuously maintained elsewhere — so a SIGTERM-triggered save that passes this list may capture only the state from the *previous* `_persist_session` call, not the true in-progress `messages` list from the local `run_conversation` stack frame.
   **Limitation:** there is no reliable way to reach the *current* mid-turn `messages` local from outside `run_conversation` without extra plumbing (e.g., stashing `self._current_turn_messages = messages` at the top of the turn loop).

5. **`HermesAgent.interrupt(message=None)` — `run_agent.py:2460` (approx, based on grep for `def interrupt`).**
   Sets `self._interrupt_requested`; the turn loop polls this flag at safe points and, when set, runs `self._persist_session(messages, conversation_history)` and returns a "interrupted" result dict (see `run_agent.py:7631–7637, 8605–8609`). This is the cleanest signal-safe primitive already present — a SIGTERM handler that calls `agent.interrupt()` and then does nothing else would let the turn loop reach its next polling point and save naturally.
   **Caveat:** polling happens only at certain points (e.g., during retry sleeps, between tool calls). If the process is blocked on a synchronous LLM HTTP call with no interrupt polling, setting the flag alone will not cause an exit. The `timeout 900` typically fires while the parent is waiting on LLM output or a long tool call, so flag-only may be insufficient without additional cooperation from the HTTP client.

6. **`--autosave-interval`, `session.checkpoint()`, or any explicit shutdown-save flag:** none found. Grep for `autosave`, `checkpoint.*session`, `save_interval`, `flush_interval` in `run_agent.py` / `cli.py` / `hermes_cli/main.py` returned no relevant hits. The `CheckpointManager` is strictly a git-tree snapshot utility.

7. **Plugin hook `on_session_finalize`** (fired from `_run_cleanup` at `cli.py:617`) — fires only on normal exit, not on SIGTERM. Plugins registered here cannot rescue the session under SIGTERM.

---

## Q8 — Empirical cross-check: orphan session `20260419_132928_e11ccb`

**Verified on VM.** Path: `/home/parallels/.hermes/sessions/session_20260419_132928_e11ccb.json` (44943 bytes, mtime `Apr 19 13:30`).

```
session_id: 20260419_132928_e11ccb
message_count: 25
messages[0].role: user
messages[0].content[:400] =
"Investigate and fix the intermittent stale data issue in the Chief of Staff
Dashboard (/media/psf/Projects/chief-of-staff-dashboard).

Steps:
1. Identify the 'Save' operation and the corresponding data-fetching logic in
   the frontend.
2. Trace the request flow from the frontend to the backend/API to determine if
   the stale data is caused by a caching issue (e.g., SWR/React Query cache
   not being inv..."
```

**Interpretation:** `messages[0]` is the *dispatched-goal* prompt that a parent agent sent via `delegate_worker.py` to a subordinate `hermes chat` invocation. It is **NOT** the trial prompt ("The dashboard sometimes shows stale data...") that originated at the test harness. This confirms:

- The file `20260419_132928_e11ccb.json` is the **child/subagent** session, not the parent.
- The child received the expanded/refined task from its parent (the parent had already digested the trial prompt and issued a structured "Investigate and fix..." instruction to the delegate).
- The child completed its run cleanly (25 messages, session file fully written) — consistent with the child's `hermes chat` process terminating normally before the outer wrapper's `timeout 900` expired.
- The parent session JSON is absent — the parent was mid-turn (waiting on the child's output and/or still in its own LLM loop) when the wrapper-side SIGTERM fired, so its inline `_persist_session` was never reached.

The mis-attachment pattern described in `ARTIFACT-r7.4-phase-d-dense-results.md:70` is empirically confirmed.

---

## Root Cause (≤150 words)

When `probe-variantF-wrapper.sh` invokes `timeout 900 hermes chat -q "..."` and the timer expires mid-turn, `timeout` delivers SIGTERM to the `hermes` Python process. The process is running `cli.main()` in single-query mode, which has installed `atexit.register(_run_cleanup)` (cli.py:8692) but **no** `signal.signal(SIGTERM, ...)` handler — the SIGTERM→KeyboardInterrupt handler at cli.py:8432–8441 is installed only inside `HermesCLI.run()` (interactive mode), never reached by `-q`. Session-JSON persistence is an **inline** `self._persist_session(...)` call at `run_agent.py:9109` (and 18 error-path duplicates inside the turn loop), not an `atexit` hook. Under Python's default SIGTERM action the interpreter terminates before any of those inline calls execute, and even if atexit ran (it doesn't under uncaught SIGTERM) `_run_cleanup` does not touch the session. Result: the parent's `session_*.json` is never written — only the child (which finished before timeout) persists.

---

## Hook Points for a Tier 3 Fix

Three viable landing options, in decreasing order of cleanliness:

### Option A — Install a SIGTERM/SIGHUP handler in `cli.main()` single-query path

**Where:** `cli.py:8692` (alongside the existing `atexit.register(_run_cleanup)`).

**What:** Mirror the interactive-mode handler already at `cli.py:8432–8441`. Register a SIGTERM handler that:
1. Calls `_active_agent_ref._persist_session(_active_agent_ref._session_messages)` (or `._save_session_log()`) directly. This is NOT signal-safe in the strict C-level sense, but Python's signal handling runs the handler between bytecode instructions in the main thread, so calling pure-Python code (including `atomic_json_write`) is acceptable.
2. Then raises `KeyboardInterrupt` to unwind the stack (matching the interactive-mode behavior).

**Hook target function:** `HermesAgent._persist_session` (run_agent.py:1842). Reachable via the module global `_active_agent_ref` set at `cli.py:2475`.

**Known limitation:** `self._session_messages` is updated only by prior calls to `_persist_session` itself. The *current-turn* `messages` list is a local in the `run_conversation` stack frame and is not visible to the handler. To get full fidelity, add a line near the top of `run_conversation` (around `run_agent.py:6800–6850`): `self._current_turn_messages = messages` — then have the signal handler save that instead.

**Signal-safety note:** Python's `signal` module defers handler execution to the main thread between bytecodes; most stdlib calls are safe in practice, though blocking I/O in a handler is discouraged. `atomic_json_write` does a tmpfile + `os.replace` — brief and acceptable. If the main thread is blocked inside a C extension (e.g. an OpenSSL socket read in httpx), the handler will not run until the C call returns or is interrupted. In that scenario, SIGTERM via `timeout` will still terminate cleanly because `timeout` sends SIGKILL after a grace period, but the handler won't have fired — a residual risk.

### Option B — Wrap `run_conversation` body in `try: … finally: self._persist_session(messages, conversation_history)`

**Where:** `run_agent.py:6800` (start of method) through `run_agent.py:9109` (end). Wrap the entire body in a `try:` … `finally:` so that any exception — `KeyboardInterrupt`, `SystemExit`, or an explicit `sys.exit()` from a signal handler — still persists.

**What:** Combined with Option A's minimal SIGTERM→KeyboardInterrupt handler, this guarantees a save on *any* exceptional unwind. This is the most conservative structural fix — it removes the fragility of relying on 19 inline save points.

**Trade-off:** Touches the largest, most-edited function in Hermes. Diff review surface is large. Also, under a pure-SIGTERM-without-handler kill, the `finally:` still doesn't run (interpreter dies immediately) — so Option B REQUIRES Option A.

### Option C — Use the existing `interrupt()` cooperative-flag mechanism

**Where:** Register a trivial SIGTERM handler in `cli.main()` that calls `_active_agent_ref.interrupt()` and returns without raising. The turn loop polls `self._interrupt_requested` at several points (e.g. `run_agent.py:7631, 8605`) and runs `_persist_session` before returning.

**Trade-off:** Only fires at polling points. If the process is blocked on a 60s LLM HTTP call when SIGTERM arrives, nothing happens until the HTTP call returns naturally — by which time `timeout`'s follow-up SIGKILL will likely have already fired (`timeout` default is SIGTERM then SIGKILL after a short grace). So Option C is insufficient on its own for the wrapper scenario. It is, however, the cleanest fix for *cooperative* external shutdown (e.g. systemd stop, SSH disconnect) and could be combined with Options A/B for defense in depth.

### Recommendation

**Option A + Option B, applied together.** Option A converts SIGTERM into a normal Python exception, Option B guarantees the save path is reached on any unwind. Option C is a nice-to-have secondary hook. The blast radius of Option A alone is tiny (~15 lines inside `cli.main()` following the pattern of `cli.py:8432–8441`); Option B is larger but mechanical. Total Tier 3 diff: plausibly ~30–50 lines of `run_agent.py` + `cli.py`, no new dependencies, no test-suite risk beyond "ensure single-query mode still exits cleanly on normal completion."

---

## Summary of Hypothesis Status

| Pre-registered claim | Verdict |
|---|---|
| "Session-persistence path in Hermes is registered as an `atexit` handler" | **DISPROVEN.** Persistence is inline `_persist_session(...)` calls inside `run_conversation`. |
| "That `atexit` handler does not fire under SIGTERM" | **TRUE** for Python's atexit semantics, but **irrelevant** to Hermes because the session save is not in an atexit handler. The atexit handler that IS registered (`_run_cleanup`) does not save sessions. |
| "probe-variantF-wrapper.sh loses the parent session when `timeout 900` SIGTERMs mid-turn" | **CONFIRMED** empirically (orphan child JSON present, parent absent, messages[0] mismatch). |
| "SIGINT (Ctrl-C) triggers the save path via default KeyboardInterrupt → atexit flow" | **FALSE** for Hermes. No `try/finally` around `run_conversation`; `_run_cleanup` does not save; KeyboardInterrupt bypasses the inline save line the same way SIGTERM does. |

The *symptom* is as predicted. The *mechanism* is subtly different: it is not "atexit misses SIGTERM" but "no save path exists at all for non-normal exits from the single-query code path." Both Options A and B are needed to fully close the gap.
