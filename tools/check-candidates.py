#!/usr/bin/env python3
"""check-candidates.py — verify CANDIDATES.md ledger entries carry the full schema.

For each entry id (e.g. D-14) assert:
  - a "## D-14 ..." section heading exists,
  - its section body (up to the next "## " heading or EOF) contains ALL seven schema labels,
  - a status-board row "| D-14 | ... |" exists.

A hollow heading, a blanked body, or a single missing label is a FAIL — so the mechanical check
distinguishes a real entry from a stub.

Usage: check-candidates.py D-14 D-15 [...]
Exit 0 + CANDIDATES_OK on success; exit 1 + named defects otherwise. stdlib only.
"""
import re
import sys

LABELS = ("Status", "Origin", "Evidence", "Problem",
          "Proposed mechanism", "Anchors", "Cold-start verification")
PATH = "CANDIDATES.md"


def section_body(text, eid):
    """The entry section: from '## <eid> ...' up to the next top-level '## ' heading or EOF."""
    m = re.search(r"^## " + re.escape(eid) + r"\b.*?(?=^## |\Z)", text, re.M | re.S)
    return m.group(0) if m else None


def check(text, eid):
    errs = []
    body = section_body(text, eid)
    if body is None:
        return ["%s: no '## %s' section heading" % (eid, eid)]
    for label in LABELS:
        if label not in body:
            errs.append("%s: entry section is missing the '%s' label" % (eid, label))
    if not re.search(r"^\| *" + re.escape(eid) + r" *\|", text, re.M):
        errs.append("%s: no status-board row '| %s |'" % (eid, eid))
    return errs


def main():
    ids = sys.argv[1:]
    if not ids:
        print("usage: check-candidates.py <id> [<id> ...]", file=sys.stderr)
        return 2
    try:
        with open(PATH, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print("FAIL: cannot read %s: %s" % (PATH, e))
        return 1
    errors = []
    for eid in ids:
        errors += check(text, eid)
    if errors:
        print("FAIL: %s — %d defect(s):" % (PATH, len(errors)))
        for e in errors:
            print("  - " + e)
        return 1
    print("CANDIDATES_OK: %s" % ", ".join(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
