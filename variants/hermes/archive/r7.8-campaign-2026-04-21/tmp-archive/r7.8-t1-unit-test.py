#!/usr/bin/env python3
"""r7.8 T1 — unit test for _r78_count_consecutive_identical_tool_calls.

Loads run_agent.py, extracts the static method, and tests it against
synthetic messages lists.
"""
import sys, importlib.util

# Load the module directly from run_agent.py
spec = importlib.util.spec_from_file_location(
    "run_agent_for_test", "/home/parallels/.hermes/hermes-agent/run_agent.py"
)
# We do NOT exec the module — it has top-level side effects. Instead
# monkey-patch: extract the function definition from the source and eval it.
src = open("/home/parallels/.hermes/hermes-agent/run_agent.py").read()

# Locate the helper's source text — from line with def _r78_count... to the
# next blank/dedent-out-of-staticmethod.  Use simple string slicing.
start_marker = "    @staticmethod\n    def _r78_count_consecutive_identical_tool_calls(messages: list, current_sig: tuple) -> int:"
end_marker = "    @staticmethod\n    def _deduplicate_tool_calls(tool_calls: list) -> list:"

s = src.index(start_marker)
e = src.index(end_marker)
helper_block = src[s:e]

# Strip the @staticmethod decorator and the leading class indentation (4 spaces).
lines = helper_block.splitlines()
# Drop the @staticmethod line.
lines = [l for l in lines if l.strip() != "@staticmethod"]
# Remove 4-space class indent from each line.
dedented = "\n".join(l[4:] if l.startswith("    ") else l for l in lines)

ns = {}
exec(dedented, ns)
fn = ns["_r78_count_consecutive_identical_tool_calls"]

def mk_assistant_msg(name, args):
    return {
        "role": "assistant",
        "tool_calls": [{"function": {"name": name, "arguments": args}}],
    }

def mk_tool_result(content="ok"):
    return {"role": "tool", "content": content}

# Test 1: 6 consecutive identical tool_calls — walking back from current,
# expect 6 (including current).
# messages list represents history WITHOUT the current turn; current sig is
# passed separately.
msgs_6 = []
for _ in range(5):  # 5 prior identical
    msgs_6.append(mk_assistant_msg("search_files", '{"pattern": "*.md"}'))
    msgs_6.append(mk_tool_result())
cur_sig = ("search_files", '{"pattern": "*.md"}')
got = fn(msgs_6, cur_sig)
expected = 6
assert got == expected, f"Test 1 FAIL: expected {expected} got {got}"
print(f"Test 1 PASS: 6 consecutive identical → {got}")

# Test 2: 4 consecutive + 1 different (different breaks immediately).
# history: [diff, same, same, same, same] → current is 5th same → walking
# back: 4 more same, then diff breaks → count = 5.
msgs_diff = [mk_assistant_msg("read_file", '{"path":"foo"}')]
for _ in range(4):
    msgs_diff.append(mk_assistant_msg("search_files", '{"pattern":"*.md"}'))
    msgs_diff.append(mk_tool_result())
got = fn(msgs_diff, ("search_files", '{"pattern":"*.md"}'))
expected = 5
assert got == expected, f"Test 2a FAIL: expected {expected} got {got}"
print(f"Test 2a PASS: 4 prior same + 1 different earlier → {got}")

# Test 2b: prior = single different call only → count = 1
msgs_single_diff = [mk_assistant_msg("read_file", '{"path":"foo"}')]
got = fn(msgs_single_diff, ("search_files", '{"pattern":"*.md"}'))
expected = 1
assert got == expected, f"Test 2b FAIL: expected {expected} got {got}"
print(f"Test 2b PASS: single prior different → {got}")

# Test 3: cardinality break — prior turn had 2 tool_calls → break.
msgs_multi = [{
    "role": "assistant",
    "tool_calls": [
        {"function": {"name": "search_files", "arguments": '{"pattern":"*.md"}'}},
        {"function": {"name": "read_file", "arguments": '{"path":"x"}'}},
    ],
}]
got = fn(msgs_multi, ("search_files", '{"pattern":"*.md"}'))
expected = 1
assert got == expected, f"Test 3 FAIL: expected {expected} got {got}"
print(f"Test 3 PASS: multi-tool prior turn breaks run → {got}")

# Test 4: empty history → count = 1
got = fn([], ("search_files", '{"pattern":"*.md"}'))
expected = 1
assert got == expected, f"Test 4 FAIL: expected {expected} got {got}"
print(f"Test 4 PASS: empty history → {got}")

# Test 5: tool / user messages between assistants are ignored (skip).
msgs_interleaved = []
for _ in range(3):
    msgs_interleaved.append(mk_assistant_msg("search_files", '{"pattern":"*.md"}'))
    msgs_interleaved.append(mk_tool_result())
    msgs_interleaved.append({"role": "user", "content": "noise"})
got = fn(msgs_interleaved, ("search_files", '{"pattern":"*.md"}'))
expected = 4  # 3 prior + current
assert got == expected, f"Test 5 FAIL: expected {expected} got {got}"
print(f"Test 5 PASS: interleaved user/tool msgs skipped → {got}")

print("\nALL UNIT TESTS PASS")
