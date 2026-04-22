#!/usr/bin/env python3
"""Scan captured session JSON for channel-marker residue in assistant content."""
import json
import os
import re
import sys

# Build comprehensive channel-marker regex — MUST match P1b enumeration
MARKER_PATTERNS = [
    r"<channel\|>",
    r"<\|channel\|>",
    r"<tool_call\|>",
    r"<start\|>",
    r"<end\|>",
    r"<message\|>",
    r"<return\|>",
    r"analysis\s*\n\s*<channel\|>",
    r"thought\s*\n\s*<channel\|>",
    # Bonus — harmony-style
    r"<\|start\|>",
    r"<\|end\|>",
    r"<\|message\|>",
    r"<\|return\|>",
    r"<\|tool_call\|>",
]
MARKER_RE = re.compile("|".join(MARKER_PATTERNS), re.IGNORECASE)

BASE = "/tmp/r7.8-P3a-C1-sessions"

def scan_session(path):
    with open(path) as f:
        try:
            data = json.load(f)
        except Exception as e:
            return {"error": str(e)}
    messages = data.get("messages", [])
    total_assistant = 0
    marker_turns = 0
    examples = []
    produced_any_content = False
    for m in messages:
        if m.get("role") != "assistant":
            continue
        total_assistant += 1
        content = m.get("content") or ""
        if isinstance(content, list):
            # content blocks
            content = "\n".join(
                b.get("text", "") if isinstance(b, dict) else str(b) for b in content
            )
        if content.strip():
            produced_any_content = True
        hits = MARKER_RE.findall(content)
        if hits:
            marker_turns += 1
            if len(examples) < 3:
                examples.append({"preview": content[:200], "hits": hits[:5]})
    return {
        "assistant_turns": total_assistant,
        "marker_turns": marker_turns,
        "produced_content": produced_any_content,
        "examples": examples,
        "session_id": data.get("session_id") or os.path.basename(path).replace("session_", "").replace(".json", ""),
        "classification": data.get("classification"),
    }

def main():
    trials = sorted(os.listdir(BASE))
    for t in trials:
        tpath = os.path.join(BASE, t)
        if not os.path.isdir(tpath):
            continue
        print(f"\n=== {t} ===")
        files = sorted(os.listdir(tpath))
        for f in files:
            if not f.endswith(".json"):
                continue
            path = os.path.join(tpath, f)
            res = scan_session(path)
            sid = res.get("session_id")
            if "error" in res:
                print(f"  ERROR {f}: {res['error']}")
                continue
            print(f"  {sid}: assistant_turns={res['assistant_turns']} "
                  f"marker_turns={res['marker_turns']} "
                  f"has_content={res['produced_content']} "
                  f"class={res.get('classification')}")
            for ex in res["examples"]:
                print(f"    MARKER: {ex['hits']} | preview: {ex['preview']!r}")

if __name__ == "__main__":
    main()
