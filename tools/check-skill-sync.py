#!/usr/bin/env python3
"""check-skill-sync.py — assert the AGENTFW-SYNC block is byte-identical across both adapter SKILLs.

The two adapter SKILL.md files (Claude Code, Codex) must carry a verbatim-identical block of
cross-adapter behavior. This is the D-3 discipline: progressive disclosure must never let one
runtime silently lack a feature the other has. The block is delimited by:

    <!-- AGENTFW-SYNC:v9.3:BEGIN -->  ...  <!-- AGENTFW-SYNC:v9.3:END -->

Usage:
  check-skill-sync.py             compare the two installed adapter SKILLs (exit 0 if identical)
  check-skill-sync.py --selftest  run an internal red/green self-test (needs no repo state)

Exit 0 + SKILL_SYNC_OK on match; exit 1 + a named defect otherwise. stdlib only.
"""
import os
import sys
import tempfile

BEGIN = "<!-- AGENTFW-SYNC:v9.3:BEGIN -->"
END = "<!-- AGENTFW-SYNC:v9.3:END -->"


def extract(path):
    """Return the text between BEGIN and END, or None if either marker is absent."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    if BEGIN not in text or END not in text:
        return None
    return text.split(BEGIN, 1)[1].split(END, 1)[0]


def compare(path_a, path_b):
    """List defects: a missing block on either side, or blocks that differ."""
    a = extract(path_a)
    b = extract(path_b)
    errors = []
    if a is None:
        errors.append("missing or malformed AGENTFW-SYNC block in %s" % path_a)
    if b is None:
        errors.append("missing or malformed AGENTFW-SYNC block in %s" % path_b)
    if not errors and a != b:
        errors.append("AGENTFW-SYNC blocks differ between the two adapter SKILLs")
    return errors


def _write(path, block):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("preamble\n%s%s%s\ntail\n" % (BEGIN, block, END))


def selftest():
    """Prove the checker is discriminating: green on identical, red on a one-word desync
    and on a missing block. A stub that always reports 'equal' fails this."""
    block = "\nAdaptive default; Uniform/Mirror opt-out; flagship cap; sleep posture; markers.\n"
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.md")
        b = os.path.join(d, "b.md")
        _write(a, block)
        _write(b, block)
        if compare(a, b):
            print("SELFTEST FAIL: identical blocks were reported as different")
            return 1
        _write(b, block.replace("Adaptive", "Uniformish"))  # one-word desync
        if not compare(a, b):
            print("SELFTEST FAIL: a one-word desync was not detected")
            return 1
        with open(b, "w", encoding="utf-8") as fh:
            fh.write("no markers here at all")
        if not compare(a, b):
            print("SELFTEST FAIL: a missing block was not detected")
            return 1
    print("SKILL_SYNC_SELFTEST_OK")
    return 0


def main():
    if "--selftest" in sys.argv[1:]:
        return selftest()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    a = os.path.join(root, "adapters/claude-code/skills/agentfw/SKILL.md")
    b = os.path.join(root, "adapters/codex/skills/agentfw/SKILL.md")
    errors = compare(a, b)
    if errors:
        print("FAIL: check-skill-sync — %d defect(s):" % len(errors))
        for e in errors:
            print("  - " + e)
        return 1
    print("SKILL_SYNC_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
