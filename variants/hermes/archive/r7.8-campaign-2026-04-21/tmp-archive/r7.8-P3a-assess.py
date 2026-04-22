#!/usr/bin/env python3
"""Examine final assistant content per session to assess PASS/FAIL."""
import json, os

BASE = "/tmp/r7.8-P3a-C1-sessions"

def last_assistant(path):
    with open(path) as f:
        data = json.load(f)
    last = None
    last_tc = 0
    for m in data.get("messages", []):
        if m.get("role") == "assistant":
            c = m.get("content") or ""
            if isinstance(c, list):
                c = "\n".join(b.get("text","") if isinstance(b,dict) else str(b) for b in c)
            last = c
            tcs = m.get("tool_calls") or []
            last_tc = len(tcs) if tcs else last_tc
    return last, last_tc

for t in sorted(os.listdir(BASE)):
    tpath = os.path.join(BASE, t)
    if not os.path.isdir(tpath): continue
    print(f"\n=== {t} ===")
    for f in sorted(os.listdir(tpath)):
        if not f.endswith(".json"): continue
        la, last_tc = last_assistant(os.path.join(tpath, f))
        sid = f.replace("session_","").replace(".json","")
        print(f"  {sid} (last_tc={last_tc}):")
        if la:
            print(f"    {la[:400]!r}")
        else:
            print(f"    (empty)")
