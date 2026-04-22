#!/usr/bin/env python3
"""r7.8 T1 patch — cross-turn loop detector.

Inserts a helper staticmethod and a main-loop hook into run_agent.py.
Env-gated via HERMES_LOOP_DETECTOR=1 (default off preserves r7.7 behavior).
"""
import sys
import re
import ast
import hashlib
from pathlib import Path

TARGET = Path("/home/parallels/.hermes/hermes-agent/run_agent.py")
src = TARGET.read_text()
orig_md5 = hashlib.md5(src.encode()).hexdigest()
print(f"orig md5: {orig_md5}")
assert orig_md5 == "94ad8712678df5e96b9f407446edf249", f"baseline md5 mismatch: {orig_md5}"

# ---------- 1. Helper staticmethod injection ----------
# Insert right before "@staticmethod\n    def _deduplicate_tool_calls" (line 2856).
DEDUP_ANCHOR = """    @staticmethod
    def _deduplicate_tool_calls(tool_calls: list) -> list:"""
assert src.count(DEDUP_ANCHOR) == 1, "dedup anchor not unique"

HELPER = '''    @staticmethod
    def _r78_count_consecutive_identical_tool_calls(messages: list, current_sig: tuple) -> int:
        """r7.8 T1 — count consecutive identical tool_calls in assistant history.

        Walks backwards through messages; for each assistant turn with exactly
        one tool_call matching current_sig (name + arguments), increments count.
        Stops at the first non-matching assistant turn. Ignores tool/user/system
        messages interleaved between assistant turns.

        Args:
            messages: full messages list INCLUDING the current turn's assistant
                      message already appended.  We skip the final entry.
            current_sig: (function_name, function_arguments) tuple for the
                         current turn.

        Returns:
            int: number of consecutive identical tool_calls ending with the
                 current turn (>=1 since current counts).
        """
        count = 1
        # Walk backwards, skipping the current turn (last assistant msg may or
        # may not be appended yet — caller passes messages excluding current).
        for msg in reversed(messages):
            if msg.get("role") != "assistant":
                continue
            tcs = msg.get("tool_calls") or []
            if len(tcs) != 1:
                break  # different cardinality breaks the run
            tc = tcs[0]
            fn = tc.get("function") or {}
            prev_sig = (fn.get("name"), fn.get("arguments"))
            if prev_sig != current_sig:
                break
            count += 1
        return count

    @staticmethod
    def _deduplicate_tool_calls(tool_calls: list) -> list:'''

src2 = src.replace(DEDUP_ANCHOR, HELPER, 1)
assert src2 != src, "helper insertion failed"

# ---------- 2. Main-loop hook injection ----------
# Insert right after `assistant_message.tool_calls = self._deduplicate_tool_calls(...)`
# and before `assistant_msg = self._build_assistant_message(...)`.
HOOK_ANCHOR = """                    assistant_message.tool_calls = self._deduplicate_tool_calls(
                        assistant_message.tool_calls
                    )

                    assistant_msg = self._build_assistant_message(assistant_message, finish_reason)"""
assert src2.count(HOOK_ANCHOR) == 1, "hook anchor not unique"

HOOK = '''                    assistant_message.tool_calls = self._deduplicate_tool_calls(
                        assistant_message.tool_calls
                    )

                    # ── r7.8 T1 — cross-turn loop detector (env-gated) ─────
                    # Detect runs of ≥5 consecutive identical single tool_calls.
                    # At 5: inject a system warning. At 6: terminate session with
                    # partial=True, error="loop_detected".  Default OFF — set
                    # HERMES_LOOP_DETECTOR=1 to enable.  Model-agnostic + task-agnostic.
                    if os.environ.get("HERMES_LOOP_DETECTOR") == "1" and len(assistant_message.tool_calls) == 1:
                        _r78_tc = assistant_message.tool_calls[0]
                        _r78_cur_sig = (_r78_tc.function.name, _r78_tc.function.arguments)
                        _r78_run_len = self._r78_count_consecutive_identical_tool_calls(
                            messages, _r78_cur_sig
                        )
                        _r78_THRESH_WARN = 5
                        _r78_THRESH_TERM = 6
                        if _r78_run_len >= _r78_THRESH_TERM:
                            self._vprint(
                                f"{self.log_prefix}🛑 r7.8 loop detector: {_r78_run_len} consecutive identical tool_calls "
                                f"({_r78_cur_sig[0]}) — terminating session.",
                                force=True,
                            )
                            # Append the assistant message so the terminal state is preserved.
                            _r78_final_msg = self._build_assistant_message(assistant_message, finish_reason)
                            messages.append(_r78_final_msg)
                            self._persist_session(messages, conversation_history)
                            return {
                                "final_response": None,
                                "messages": messages,
                                "api_calls": api_call_count,
                                "completed": False,
                                "partial": True,
                                "error": f"loop_detected: {_r78_run_len} consecutive identical tool_calls ({_r78_cur_sig[0]})",
                            }
                        elif _r78_run_len == _r78_THRESH_WARN:
                            self._vprint(
                                f"{self.log_prefix}⚠️  r7.8 loop detector: {_r78_run_len} consecutive identical tool_calls "
                                f"({_r78_cur_sig[0]}) — injecting warning.",
                                force=True,
                            )
                            # Append the current assistant message + tool result(s) will
                            # happen below normally.  After that the warning arrives as
                            # the next user-role message before the next API call.
                            # We append a system-role message AFTER tool results so the
                            # next API call sees the warning last.  The easiest hook is
                            # to stash a flag and append after tool execution.
                            self._r78_loop_warning_pending = True
                            self._r78_loop_warning_sig = _r78_cur_sig[0]

                    assistant_msg = self._build_assistant_message(assistant_message, finish_reason)'''

src3 = src2.replace(HOOK_ANCHOR, HOOK, 1)
assert src3 != src2, "hook insertion failed"

# ---------- 3. Post-tool-execution warning injection ----------
# After tool execution completes in the loop, if _r78_loop_warning_pending is
# set, append a system message telling the model to stop repeating.
# Hook point: right after self._execute_tool_calls(...) call.
EXEC_ANCHOR = """                    self._execute_tool_calls(assistant_message, messages, effective_task_id, api_call_count)

                    # Signal that a paragraph break is needed before the next"""
assert src3.count(EXEC_ANCHOR) == 1, "exec anchor not unique"

EXEC_PATCH = '''                    self._execute_tool_calls(assistant_message, messages, effective_task_id, api_call_count)

                    # ── r7.8 T1 — inject warning after tool execution ──────
                    if getattr(self, "_r78_loop_warning_pending", False):
                        _r78_warn_name = getattr(self, "_r78_loop_warning_sig", "tool")
                        messages.append({
                            "role": "user",
                            "content": (
                                f"[System: r7.8 loop detector — you have emitted the same tool call "
                                f"({_r78_warn_name}) 5 turns in a row. If this is not intentional, "
                                "stop calling tools and produce a natural-language summary explaining "
                                "what you have found, what you could not find, and the concrete blocker. "
                                "One more identical call will terminate the session.]"
                            ),
                        })
                        self._r78_loop_warning_pending = False

                    # Signal that a paragraph break is needed before the next'''

src4 = src3.replace(EXEC_ANCHOR, EXEC_PATCH, 1)
assert src4 != src3, "exec-patch insertion failed"

# ---------- 4. AST-validate the patched source ----------
try:
    ast.parse(src4)
    print("AST parse: OK")
except SyntaxError as e:
    print(f"AST parse FAILED: {e}")
    sys.exit(1)

# ---------- 5. Write ----------
TARGET.write_text(src4)
new_md5 = hashlib.md5(src4.encode()).hexdigest()
print(f"new md5: {new_md5}")
assert new_md5 != orig_md5, "md5 unchanged"
print("PATCH APPLIED OK")
