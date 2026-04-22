---
type: A2 hook-point research (S2)
date: 2026-04-20
campaign: r7.7 Path A
worker: S2
---
# A2 hook-point research

## 1. Hook point (grep-anchored)

Grep anchor (reproducible, line-number-resistant):

```bash
grep -n 'def run_conversation' ~/.hermes/hermes-agent/run_agent.py
# => 6800:    def run_conversation(
```

For the terminal `_persist_session` call, anchor with the PRECEDING comment
line rather than a raw line number:

```bash
grep -n '# Persist session to both JSON log and SQLite' ~/.hermes/hermes-agent/run_agent.py
# The NEXT line (literal: "        self._persist_session(messages, conversation_history)")
# is the A2 hook insertion point.
```

- `def run_conversation` at `run_agent.py:6800`.
- First `_persist_session` inside body at `run_agent.py:9109` (the terminal
  one; preceding comment `# Persist session to both JSON log and SQLite`).
- **Additional `_persist_session` calls in `run_conversation`:** YES —
  numerous. All calls between `run_agent.py:7497` and `run_agent.py:8687`
  live inside the main tool-loop body / exception handlers (mid-turn
  persistence for crash-safety). Raw list of in-function persist calls:
  7497, 7517, 7597, 7637, 7653, 7666, 7797, 7947, 8055, 8080, 8183, 8210,
  8294, 8364, 8414, 8447, 8556, 8609, 8687, 9109. Additionally
  `_save_session_log` (bare, no SQLite flush) at 7631, 8605, 8901, 8960, 9008.
- **Critical distinction:** The mid-turn calls (7497..8687) are exception-
  path crash-safety saves — they persist *partial* state when something goes
  wrong. The terminal call at 9109 is the only "happy path" final persist.
  **A2 should gate only 9109, not the mid-turn saves**, because:
  1. Mid-turn saves cover abnormal termination (keyboard interrupt, API
     error loops hitting `break`). Gating them risks dropping state.
  2. Fabrication detection is a happy-path concern — if the loop crashed,
     the final assistant message likely doesn't even exist yet.
  3. The terminal 9109 is the only path reached when `final_response is not
     None and completed == True`, which is the condition A2 cares about.
- Total file length: `9461` lines.

## 2. Hook-region structure

The 50-line window around the hook (9060–9110), lightly annotated:

```python
                    # ...role-alternation error-path tool-stub synthesis...
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        # [synthesize error tool responses for unanswered ids]
                        ...
                    break

                # Non-tool errors don't need a synthetic message injected.
                # [retry loop continues]

                # If we're near the limit, break to avoid infinite loops
                if api_call_count >= self.max_iterations - 1:
                    final_response = f"I apologize, but I encountered..."
                    messages.append({"role": "assistant", "content": final_response})
                    break
        # <-- END OF while api_call_count < self.max_iterations LOOP (started 7111)

        if final_response is None and (
            api_call_count >= self.max_iterations
            or self.iteration_budget.remaining <= 0
        ):
            if self.iteration_budget.remaining <= 0 and not self.quiet_mode:
                print(f"\n⚠️  Iteration budget exhausted ...")
            final_response = self._handle_max_iterations(messages, api_call_count)

        # Determine if conversation completed successfully
        completed = final_response is not None and api_call_count < self.max_iterations

        # Save trajectory if enabled
        self._save_trajectory(messages, user_message, completed)

        # Clean up VM and browser for this task after conversation completes
        self._cleanup_task_resources(effective_task_id)

        # Persist session to both JSON log and SQLite       <-- A2 HOOK GOES HERE (just above)
        self._persist_session(messages, conversation_history)

        # Plugin hook: post_llm_call
        if final_response and not interrupted:
            try:
                from hermes_cli.plugins import invoke_hook as _invoke_hook
                _invoke_hook("post_llm_call", ...)
            except Exception as exc:
                logger.warning("post_llm_call hook failed: %s", exc)

        # [extract reasoning, build result dict, fire on_session_end, return result]
```

- **Loop / try / context:** The hook site is in the **post-loop** body of
  `run_conversation` — OUTSIDE the `while api_call_count < max_iterations`
  loop, OUTSIDE any `try/except`. It is flat function body at indent level 8.
  No surrounding `with`/`try`. `_cleanup_task_resources` has already been
  invoked immediately before, which means VM / browser resources may
  already be released — **the child-agent reasoning path may still work,
  but any tool dependent on task-scoped VM state may no longer function.**
  A2's retry must use only pure text-turn model inference (no new tool
  calls), NOT call tools that expect the cleaned-up task resources.
- **Return behavior:** After the hook, control continues to plugin hook
  invocation, reasoning extraction, the `result = {...}` dict build, and
  finally `return result` at line 9230. A2 can cleanly run before 9109;
  if A2 mutates `messages` or `final_response`, those mutations flow
  through to the `result` dict and the post-return callers see them.
- **How the final assistant message arrives:** The final assistant message
  is the LAST `{"role": "assistant", ...}` entry in `messages`. It is
  appended during normal tool-loop execution (inside the while-loop body)
  OR synthesized as the "repeated errors" message in the exception path.
  A2 scans `messages[-1]` (last assistant turn) for fabrication claims.
- **Safe to inject correction-message + re-run one turn before
  `_persist_session`?** **CONDITIONAL-YES**, with caveats:
  1. `_cleanup_task_resources(effective_task_id)` has already fired
     (9104), so the retry turn MUST NOT depend on task VM state. Model
     inference itself works (OpenAI-compat client is an agent-level
     resource, unaffected by task cleanup). Tool calls requiring the
     cleaned VM (terminal, browser, execute_code with sandbox) will
     fail or operate on stale state.
  2. Mitigation: A2's corrective turn should be **low-machinery** — just
     append a `{"role": "user", "content": "<correction text>"}` message
     and call the same inference primitive the main loop uses
     (`OpenAI client.chat.completions.create`), with tools=`valid_tool_names`
     restricted to the writer set only. Do NOT re-enter the full
     `run_conversation` loop (would re-trigger cleanup, re-run plugins,
     and recurse infinitely).
  3. Simpler alternative (recommended for first cut): Do NOT re-run model
     inference at all. If fabrication detected, **append a corrective
     user message + an assistant apology stub**, set `a2_gate_outcome =
     "FABRICATED"`, and let the session-end path close out. This
     sacrifices the "give the model a chance to correct" affordance but
     is vastly simpler and has zero re-entrancy risk. The child will
     simply be marked failed; parent retries via normal delegate-pool
     logic.

## 3. Write-tool set verification

| Tool | Exists? | file:line | File-write semantics |
|------|---------|-----------|----------------------|
| `write_file` | Y | `tools/file_tools.py:571` (`write_file_tool`); registered name `write_file` in `toolsets.py:37` | Writes to disk via `FileOperations.write_file` (atomic temp + rename; `file_operations.py:257, 568`). DEFINITIVE file write. |
| `patch` | Y | `tools/file_tools.py:595` (`patch_tool`); registered in `toolsets.py:37` | Writes to disk via `FileOperations.patch_replace` / `patch_v4a` (`file_operations.py:262, 268, 626, 687`). DEFINITIVE file write. |
| `execute_code` | Y | `tools/code_execution_tool.py:866`; registered in `toolsets.py:56` | Python/shell execution in sandboxed VM. Can write files via user code. OPAQUE — no guarantee a file was actually written (code could print "Created X" without writing). **KEEP in set, but understand it's a write-*capable* tool, not a write-*guaranteeing* one.** |
| `terminal` | Y | `tools/terminal_tool.py:997` (`terminal_tool`); registered in `toolsets.py` | Persistent shell session; `tee`, `>`, `cat <<EOF` can write files. OPAQUE, same caveat as `execute_code`. KEEP in set. |
| `skill_manage` | Y | `tools/skill_manager_tool.py:569`; registered in `toolsets.py:41, 110` | **BOTH.** Actions `create`, `edit`, `patch`, `write_file` DO perform filesystem writes (`.write_text`, `mkdir(parents=True, exist_ok=True)`, atomic fd-based writes at `skill_manager_tool.py:256, 263, 309, 504`). Actions `delete` and `remove_file` do writes (rmtree). So `skill_manage` IS a write-capable tool. HOWEVER: it writes to the **skills registry directory** (`~/.hermes/skills/<name>/`), NOT to arbitrary paths the user/child might claim. If the child says "Created `/tmp/report.md`" and only called `skill_manage`, that claim is still fabrication. |

**Recommendation on `skill_manage`:** Keep it in the write-tool set but
with a caveat in the fabrication detector: if the child's claim
references a path OUTSIDE `~/.hermes/skills/`, `skill_manage` should NOT
count as a matching write. This requires path-aware matching, not just
tool-name matching. If path-aware matching is out of scope for A2,
**drop `skill_manage` from the set** and accept that skill-creation
children will be flagged — those are rare in the fabrication-prone
worker scenarios r7.7 targets.

**Recommended final set (conservative):**
`{write_file, patch, execute_code, terminal}`

**Recommended final set (inclusive):** `{write_file, patch, execute_code,
terminal, skill_manage}` — but only matches if claim-path is within
skills directory, otherwise treat as no-match.

## 4. SIGTERM safety design

**Existing SIGTERM handler** (at the CLI layer, NOT agent layer):
- `cli.py:8432` defines `_signal_handler(signum, frame)` that raises
  `KeyboardInterrupt`. Registered at `cli.py:8438` for SIGTERM and
  `cli.py:8440` for SIGHUP. `atexit.register(_run_cleanup)` at
  `cli.py:8428, 8692`.
- **Coverage gap:** The handler exists only when the interactive CLI is
  active. When `run_conversation` is invoked via gateway
  (`gateway/platforms/api_server.py:1318, 1484`), `gateway/run.py` paths,
  ACP (`acp_adapter/server.py:420`), or batch/rl (`rl_cli.py:415, 432`,
  `batch_runner.py`), no SIGTERM handler is guaranteed — each entrypoint
  installs its own or none.
- The existing handler raises `KeyboardInterrupt`. This WILL propagate
  up through `run_conversation`'s while-loop. The `interrupted = True`
  path is taken at the top of the loop (line 7117). The loop will break
  and fall through to line 9109, where `_persist_session` DOES still run.
  So in the CLI case, **the existing handler already ensures persistence
  on SIGTERM**.
- However, A2's retry-turn, if implemented via direct
  `client.chat.completions.create(...)` call BEFORE line 9109, is NOT
  protected by the while-loop's `interrupted` check (it's outside the
  loop). A long-running model inference inside A2 could be SIGTERM'd
  mid-call, and the KeyboardInterrupt would propagate UP past
  `_persist_session`, dropping the session.

**Proposed A2 SIGTERM handler (pseudocode):**

```python
# Inside run_conversation, just before A2 scan + retry
a2_safe_state = {"messages": messages, "conv_hist": conversation_history,
                 "final_response": final_response, "persisted": False}

def _a2_emergency_persist(signum, frame):
    if a2_safe_state["persisted"]:
        return
    a2_safe_state["persisted"] = True
    try:
        self._persist_session(a2_safe_state["messages"],
                              a2_safe_state["conv_hist"])
    finally:
        # Chain to pre-existing handler if any
        if _prev_handler and callable(_prev_handler):
            _prev_handler(signum, frame)
        else:
            raise KeyboardInterrupt()

import signal as _sig
_prev_handler = _sig.signal(_sig.SIGTERM, _a2_emergency_persist)
try:
    # ... A2 scan + retry logic (may take up to 120s) ...
    _run_a2_gate(messages, ...)
finally:
    _sig.signal(_sig.SIGTERM, _prev_handler or _sig.SIG_DFL)

# Fall through to line 9109. If SIGTERM already fired, persisted==True,
# so the normal call at 9109 is fine (it'll re-flush but _flush_messages_
# to_session_db tracks _last_flushed_db_idx so it's a no-op).
```

**Wall-clock cap:** 60s per retry × 2 retries = 120s total A2 budget.
Mechanism: `threading.Timer` (not `signal.alarm`, which doesn't work in
non-main threads and collides with the existing handler). A `Timer`
scheduled for 60s that sets a flag checked in the retry's
`stream_callback`, or uses `asyncio.wait_for` if the client is async. A
simpler alternative: `concurrent.futures.ThreadPoolExecutor` with
`future.result(timeout=60)` — on timeout, abandon the retry and proceed.

**Safe fallback on timeout / SIGTERM during A2:**
1. Abandon further retry attempts.
2. Mark `a2_gate_outcome = "TIMEOUT"` (distinct from "FABRICATED").
3. Append a system-note message to `messages` documenting the incident.
4. Fall through to `_persist_session(messages, ...)` at 9109. Session
   is saved with the incident recorded — parent delegate receives a
   clear signal.
5. Re-raise KeyboardInterrupt (only if SIGTERM was the cause, not
   timeout) after persistence completes.

**Signal-handler constraint:** `signal.signal` can only be called from
the MAIN Python thread. `run_conversation` is frequently called from
worker threads (gateway, delegate children). Guard with
`threading.current_thread() is threading.main_thread()`; if not main,
**skip the A2 signal-handler install and rely on wall-clock timeout
only**. SIGTERM in worker threads lands on the main thread anyway, and
the main thread's handler (if any) takes over.

## 5. Concurrency / re-entrancy

- **`run_conversation` invocation pattern:** Predominantly **serial per
  agent instance**, but **concurrent across instances**. Evidence:
  - `delegate_tool.py:373`: `child.run_conversation(user_message=goal)`
    — child is a DIFFERENT agent instance with its own `_session_messages`,
    own `persist_session` flag, own `session_id`. So two parallel delegated
    children each have their own hook-site state. No shared-state race.
  - `cli.py:4851, 4984`: `bg_agent.run_conversation(...)` /
    `btw_agent.run_conversation(...)` — background agents, again separate
    instances, dispatched via `threading.Thread` (seen at `run_agent.py:1731,
    1821, 4204, 4719`).
  - Within a single agent instance, `run_conversation` is NOT re-entrant
    on itself in the same thread. Multi-turn CLI calls it once per user
    turn, serially.
- **Concurrency primitives in the agent:** `self._client_lock`
  (`run_agent.py:612`, RLock) guards the OpenAI client. `self._active_children_lock`
  (617) guards child tracking. `_openai_client_lock` method (3511) returns
  a thread-local lock. Parallel tool dispatch uses
  `_execute_tool_calls_concurrent` (5947) with a thread pool.
- **Risks for A2:**
  1. **Shared `_session_db` writer.** `_persist_session` writes to SQLite.
     If the same agent instance's `_persist_session` is called from two
     threads (e.g., background review at `run_agent.py:1821` + main
     thread's A2 retry), SQLite-level locking *should* serialize, but
     long A2 retries extend the window where a background flush could
     interleave. Mitigation: the existing `_last_flushed_db_idx`
     idempotency (1852 comment) already handles this.
  2. **Two sibling delegated children finishing A2 simultaneously.**
     Each has its own `self.*`, so no state clash. But both install a
     SIGTERM handler — `signal.signal` is process-global, last-writer-
     wins. If S1 child installs handler, S2 child installs handler, S1
     removes handler (finally block) — S2's handler gets clobbered with
     the DEFAULT (not preserved). Mitigation: guard install with
     `threading.current_thread() is main_thread()` (only one main-thread
     child can run this at a time, by definition — sub-threads skip
     install) and/or use a global lock around install/restore.
  3. **`_cleanup_task_resources` racing with A2 retry.** Cleanup has
     already run at 9104, freeing task VM. If A2's retry somehow spawns
     new tool calls that touch task state, they'll fail. Mitigation:
     A2 retry MUST NOT enable tool calls (pure text response only) or
     A2 must run BEFORE `_cleanup_task_resources` (move hook up to
     before line 9104). **Recommendation: move A2 scan+retry to BEFORE
     `_cleanup_task_resources`** — hook just after `completed = ...`
     computation at line 9100, before `_save_trajectory` (or after
     `_save_trajectory` but before `_cleanup_task_resources`). This
     keeps VM / browser / task state live for A2's retry turn.
  4. **`step_callback`, `stream_callback`, plugin hooks.** The A2 retry,
     if it calls inference, should either (a) set
     `self._stream_callback = None` temporarily to avoid double-streaming
     to the UI, or (b) provide its own callback that marks the retry as
     an A2 correction visually. Otherwise the user may see two
     consecutive assistant "final" messages.

## 6. Ready for S4 impl? **YES** with design choices flagged

Blockers: none hard. Design decisions S4 must make:
1. **Move hook up, or leave at 9109?** Recommendation: move to just
   before `_cleanup_task_resources(effective_task_id)` so the retry's
   tools still work. Document the new hook via the preceding comment
   anchor `# Clean up VM and browser for this task`.
2. **Retry approach:** (a) simple "mark FABRICATED, no retry" — zero
   re-entrancy risk; (b) direct `client.chat.completions.create` call
   with restricted tools — medium risk, highest fidelity; (c) re-enter
   `run_conversation` recursively — **rejected, infinite-loop risk**.
   Recommendation: start with (a) for r7.7 and revisit (b) in r7.8 only
   if (a)'s false-negative rate is too high.
3. **`skill_manage` inclusion:** drop for now (simpler, smaller false-
   positive risk). Re-add when path-aware matching is built.
4. **SIGTERM handler:** only install when on main thread; always install
   wall-clock Timer fallback.

## 7. Surprises vs I2 report

1. **Hook-line shift: I2 cited 9109; still 9109.** Confirmed stable at
   snapshot time. But the grep anchor (`# Persist session to both JSON
   log and SQLite`) is still the correct long-term anchor — raw line
   numbers shift with every commit. The I2 report was evidently
   captured against the same tree state.
2. **`_persist_session` is NOT unique within `run_conversation`.** I2's
   "first persist_session call" framing is technically correct but
   potentially misleading. There are ~20 call sites inside the function
   (all mid-turn crash-safety). A2 must ONLY gate the terminal one
   (9109). Gating any of the mid-turn calls would degrade crash
   recovery.
3. **`_cleanup_task_resources` fires BEFORE `_persist_session`
   (line 9104 vs 9109).** This was not flagged by I2. It means the
   "9109 hook" is too late to reliably run a tool-using retry, because
   task VM may be torn down. **Hook should move up by 10 lines.**
4. **`skill_manage` is more nuanced than binary.** I2 flagged the
   "METADATA ONLY / FILE WRITE" ambiguity; the answer is "file write,
   but to a restricted namespace". Path-aware matching is needed for
   full correctness.
5. **Gateway and ACP entrypoints lack SIGTERM handlers.** I2 did not
   enumerate the 8+ callers of `run_conversation`; the CLI's SIGTERM
   handler is not representative of all paths. A2 needs its own
   handler install (guarded to main-thread-only) to be safe across
   entrypoints.
6. **SIGTERM during A2 retry, if on non-main thread, cannot install a
   handler at all** — `signal.signal` raises `ValueError` off-main-
   thread. This is why a wall-clock Timer is the required primary
   mechanism, with the signal handler as belt-and-suspenders for the
   main-thread CLI case.

## Artifact references (absolute paths)

- `/Users/briantaylor/Projects/AgentFW/PLAN-r7.7-path-A-child-structural-fixes.md`
- VM remote: `~/.hermes/hermes-agent/run_agent.py` (9461 lines)
- VM remote: `~/.hermes/hermes-agent/tools/skill_manager_tool.py`
- VM remote: `~/.hermes/hermes-agent/tools/file_operations.py`
- VM remote: `~/.hermes/hermes-agent/toolsets.py`
- VM remote: `~/.hermes/hermes-agent/cli.py` (SIGTERM install at 8438)
- VM remote: `~/.hermes/hermes-agent/tools/delegate_tool.py:373` (child dispatch)
