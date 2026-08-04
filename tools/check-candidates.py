#!/usr/bin/env python3
"""check-candidates.py — verify CANDIDATES.md ledger entries carry the full schema.

For each entry id (e.g. D-14) assert:
  - a "## D-14 ..." section heading exists,
  - its section body (up to the next "## " heading or EOF) contains ALL required schema labels,
  - a status-board row "| D-14 | ... |" exists.

A hollow heading, a blanked body, or a single missing label is a FAIL — so the mechanical check
distinguishes a real entry from a stub.

**Falsifier is per-entry, and conditional on --require-falsifier (v9.7 / D-28..D-36 hardening).**
The seven base labels (Status, Origin, Evidence, Problem, Proposed mechanism, Anchors,
Cold-start verification) are always required. Falsifier is an eighth label required only when
`--require-falsifier` is passed — this keeps pre-D-28 entries (which carry no Falsifier line)
validating exactly as they did before Falsifier was introduced, while letting newer callers opt
into the stricter eight-label schema. Whichever set is active, the label check runs against
`section_body()` — the slice from an entry's own "## D-N ..." heading up to the next top-level
heading or EOF. That is deliberate: the pass-1 failure mode this closes is a checker that instead
greps the WHOLE file for N occurrences of "Falsifier" and calls it satisfied for N ids — which
Falsifier lines gathered anywhere (even outside every entry section) would pass. Scoping the
search to each entry's own body makes that hollow-passability path impossible: a Falsifier line
living outside its id's section, or missing from one entry while its siblings carry theirs, is a
named per-id defect whenever Falsifier is in the required set.

Usage:
  check-candidates.py [--require-falsifier] D-14 D-15 [...]
                                           validate ids against CANDIDATES.md (exit 0 if sound)
  check-candidates.py --selftest          red/green self-test (needs no repo state)

Exit 0 + CANDIDATES_OK (or CANDIDATES_SELFTEST_OK) on success; exit 1 + named defects otherwise.
stdlib only.
"""
import re
import sys

BASE_LABELS = ("Status", "Origin", "Evidence", "Problem",
               "Proposed mechanism", "Anchors", "Cold-start verification")
FALSIFIER_LABEL = "Falsifier"
PATH = "CANDIDATES.md"


def section_body(text, eid):
    """The entry section: from '## <eid> ...' up to the next top-level '## ' heading or EOF."""
    m = re.search(r"^## " + re.escape(eid) + r"\b.*?(?=^## |\Z)", text, re.M | re.S)
    return m.group(0) if m else None


def check(text, eid, require_falsifier=False):
    errs = []
    body = section_body(text, eid)
    if body is None:
        return ["%s: no '## %s' section heading" % (eid, eid)]
    labels = BASE_LABELS + ((FALSIFIER_LABEL,) if require_falsifier else ())
    for label in labels:
        if label not in body:
            errs.append("%s: entry section is missing the '%s' label" % (eid, label))
    if not re.search(r"^\| *" + re.escape(eid) + r" *\|", text, re.M):
        errs.append("%s: no status-board row '| %s |'" % (eid, eid))
    return errs


# --- selftest ---------------------------------------------------------------

def _green_text():
    """A minimal two-entry CANDIDATES.md-shaped document — the selftest's green baseline."""
    return (
        "## Status board\n\n"
        "| id | Title | Status |\n"
        "|---|---|---|\n"
        "| D-90 | Selftest entry one | proposed |\n"
        "| D-91 | Selftest entry two | proposed |\n\n"
        "## D-90 · Selftest entry one\n\n"
        "**Status:** proposed\n\n"
        "**Origin:** synthetic selftest fixture.\n\n"
        "**Evidence:** synthetic.\n\n"
        "**Problem:** synthetic.\n\n"
        "**Proposed mechanism:** synthetic.\n\n"
        "**Anchors:** synthetic.\n\n"
        "**Cold-start verification:** synthetic.\n\n"
        "**Falsifier:** synthetic falsifier for D-90.\n\n"
        "## D-91 · Selftest entry two\n\n"
        "**Status:** proposed\n\n"
        "**Origin:** synthetic selftest fixture.\n\n"
        "**Evidence:** synthetic.\n\n"
        "**Problem:** synthetic.\n\n"
        "**Proposed mechanism:** synthetic.\n\n"
        "**Anchors:** synthetic.\n\n"
        "**Cold-start verification:** synthetic.\n\n"
        "**Falsifier:** synthetic falsifier for D-91.\n"
    )


def selftest():
    """Red/green self-test: accept the sound two-entry doc, reject every contracted unsound one."""
    failures = []
    green = _green_text()

    baseline_errs = check(green, "D-90") + check(green, "D-91")
    if baseline_errs:
        return ["selftest GREEN doc was rejected: %s" % "; ".join(baseline_errs)]

    # baseline, --require-falsifier direction: the green fixture carries Falsifier lines for
    # both entries, so it must ALSO pass when Falsifier is required.
    baseline_rf_errs = (check(green, "D-90", require_falsifier=True)
                         + check(green, "D-91", require_falsifier=True))
    if baseline_rf_errs:
        return ["selftest GREEN doc was rejected with --require-falsifier: %s"
                % "; ".join(baseline_rf_errs)]

    # RED 1: hollow heading — blank the D-90 body, leaving only its heading line.
    red1 = re.sub(
        r"^## D-90 · Selftest entry one\n\n.*?(?=^## D-91)",
        "## D-90 · Selftest entry one\n\n",
        green, flags=re.M | re.S,
    )
    if not check(red1, "D-90"):
        failures.append("RED 1 (blanked D-90 body, heading only) was accepted")

    # RED 2: delete the D-91 status-board row only; body is untouched.
    red2 = green.replace("| D-91 | Selftest entry two | proposed |\n", "")
    if not check(red2, "D-91"):
        failures.append("RED 2 (missing D-91 status-board row) was accepted")

    # RED 3: delete the Falsifier line from D-90 ONLY, leaving D-91's intact.
    # With --require-falsifier: must fail for D-90 and must NOT collaterally fail D-91
    # (proves the check is per-entry, not file-global).
    # Without the flag: the missing Falsifier line must be ACCEPTED — Falsifier is optional
    # unless explicitly required, so pre-existing (pre-D-28) entries keep validating.
    red3 = green.replace("**Falsifier:** synthetic falsifier for D-90.\n\n", "")
    if not check(red3, "D-90", require_falsifier=True):
        failures.append(
            "RED 3 (D-90 missing its own Falsifier line) was accepted WITH --require-falsifier")
    if check(red3, "D-91", require_falsifier=True):
        failures.append(
            "RED 3 side effect: removing D-90's Falsifier line collaterally broke D-91 — "
            "the check is not properly scoped per-entry")
    if check(red3, "D-90"):
        failures.append(
            "RED 3 (D-90 missing its own Falsifier line) was REJECTED without "
            "--require-falsifier — Falsifier must be optional by default")

    # RED 4: the pass-1 hollow-passability path — move BOTH Falsifier lines out of their
    # entries into one block after every section. Each entry's own body no longer carries one.
    # Only material when --require-falsifier is set; without it Falsifier isn't checked at all.
    red4 = green
    for eid in ("D-90", "D-91"):
        red4 = red4.replace("**Falsifier:** synthetic falsifier for %s.\n\n" % eid, "")
        red4 = red4.replace("**Falsifier:** synthetic falsifier for %s.\n" % eid, "")
    red4 += ("\n## Falsifiers (gathered outside any entry section)\n\n"
             "**Falsifier:** synthetic falsifier for D-90.\n\n"
             "**Falsifier:** synthetic falsifier for D-91.\n")
    if not check(red4, "D-90", require_falsifier=True):
        failures.append(
            "RED 4 (Falsifier lines gathered outside any section) was accepted for D-90 "
            "WITH --require-falsifier")
    if not check(red4, "D-91", require_falsifier=True):
        failures.append(
            "RED 4 (Falsifier lines gathered outside any section) was accepted for D-91 "
            "WITH --require-falsifier")
    if check(red4, "D-90") or check(red4, "D-91"):
        failures.append(
            "RED 4 (Falsifier lines gathered outside any section) was REJECTED without "
            "--require-falsifier — Falsifier must be optional by default")

    # RED 5: missing a non-Falsifier label (e.g. 'Problem') still fails, same as before.
    red5 = green.replace("**Problem:** synthetic.\n\n", "", 1)
    if not check(red5, "D-90"):
        failures.append("RED 5 (D-90 missing 'Problem' label) was accepted")

    # RED 6: no such heading at all.
    if not check(green, "D-99"):
        failures.append("RED 6 (no '## D-99' heading exists) was accepted")

    return failures


def main():
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        defects = selftest()
        if defects:
            print("FAIL: %d selftest defect(s):" % len(defects))
            for d in defects:
                print("  - " + d)
            return 1
        print("CANDIDATES_SELFTEST_OK")
        return 0

    require_falsifier = "--require-falsifier" in argv
    ids = [a for a in argv if a != "--require-falsifier"]
    if not ids:
        print("usage: check-candidates.py [--require-falsifier] <id> [<id> ...] | --selftest",
              file=sys.stderr)
        return 2
    try:
        with open(PATH, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print("FAIL: cannot read %s: %s" % (PATH, e))
        return 1
    errors = []
    for eid in ids:
        errors += check(text, eid, require_falsifier=require_falsifier)
    if errors:
        print("FAIL: %s — %d defect(s):" % (PATH, len(errors)))
        for e in errors:
            print("  - " + e)
        return 1
    print("CANDIDATES_OK: %s" % ", ".join(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
