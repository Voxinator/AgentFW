#!/usr/bin/env python3
"""Summarize per-trial channel-marker count."""
import json, os, re, sys

MARKER_PATTERNS = [
    r"<channel\|>", r"<\|channel\|>", r"<tool_call\|>", r"<start\|>",
    r"<end\|>", r"<message\|>", r"<return\|>",
    r"analysis\s*\n\s*<channel\|>", r"thought\s*\n\s*<channel\|>",
    r"<\|start\|>", r"<\|end\|>", r"<\|message\|>", r"<\|return\|>",
    r"<\|tool_call\|>",
]
MARKER_RE = re.compile("|".join(MARKER_PATTERNS), re.IGNORECASE)

BASE = "/tmp/r7.8-P3a-C1-sessions"

def count(path):
    with open(path) as f:
        try:
            data = json.load(f)
        except Exception:
            return 0, 0, False, 0
    turns_w_markers = 0
    total_marker_hits = 0
    assistant_turns = 0
    produced = False
    for m in data.get("messages", []):
        if m.get("role") != "assistant":
            continue
        assistant_turns += 1
        content = m.get("content") or ""
        if isinstance(content, list):
            content = "\n".join(b.get("text","") if isinstance(b,dict) else str(b) for b in content)
        if content.strip():
            produced = True
        hits = MARKER_RE.findall(content)
        if hits:
            turns_w_markers += 1
            total_marker_hits += len(hits)
    return turns_w_markers, total_marker_hits, produced, assistant_turns

trials = sorted(os.listdir(BASE))
grand_total_hits = 0
for t in trials:
    tpath = os.path.join(BASE, t)
    if not os.path.isdir(tpath): continue
    total_hits = 0
    total_turns_w = 0
    files = sorted(os.listdir(tpath))
    for f in files:
        if not f.endswith(".json"): continue
        tw, th, prod, at = count(os.path.join(tpath, f))
        total_turns_w += tw
        total_hits += th
    grand_total_hits += total_hits
    print(f"{t}: turns_w_markers={total_turns_w} total_hits={total_hits} sessions={len(files)}")

print(f"\nGRAND TOTAL marker hits across 5 trials: {grand_total_hits}")
