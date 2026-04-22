#!/usr/bin/env python3
"""Extract first tool call from a Hermes session JSON.

Usage: probe-r7.3-l1-firsttool.py <session-id-or-path>

Prints: first_tool=<name> tools_count=<N> total_tool_calls=<M>
"""
import json
import os
import sys


def find_session(arg: str) -> str:
    if os.path.exists(arg):
        return arg
    candidate = f"/home/parallels/.hermes/sessions/session_{arg}.json"
    if os.path.exists(candidate):
        return candidate
    return arg


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: probe-r7.3-l1-firsttool.py <session-id-or-path>")
        return 2
    path = find_session(sys.argv[1])
    try:
        with open(path) as f:
            session = json.load(f)
    except FileNotFoundError:
        print(f"first_tool=NO_SESSION tools_count=0 total_tool_calls=0 path={path}")
        return 1
    except Exception as exc:
        print(f"first_tool=ERROR detail={exc.__class__.__name__} path={path}")
        return 1
    tools = session.get("tools", []) or []
    tools_count = len(tools)
    msgs = session.get("messages", []) or session.get("history", []) or []
    first_tool = "NONE"
    total_tool_calls = 0
    for m in msgs:
        # Look for assistant tool_calls
        if isinstance(m, dict):
            calls = m.get("tool_calls") or m.get("toolCalls") or []
            for c in calls:
                name = None
                if isinstance(c, dict):
                    fn = c.get("function") or {}
                    if isinstance(fn, dict):
                        name = fn.get("name")
                    if not name:
                        name = c.get("name")
                if name:
                    total_tool_calls += 1
                    if first_tool == "NONE":
                        first_tool = name
    print(
        f"first_tool={first_tool} tools_count={tools_count} total_tool_calls={total_tool_calls} path={path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
