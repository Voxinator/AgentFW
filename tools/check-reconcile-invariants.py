#!/usr/bin/env python3
"""check-reconcile-invariants.py — machine-check the resume-reconciliation decision table (D-25).

Session-start reconciliation is the duty that stops a resumed session from planning on top of
fictional progress: read the objective's ledger, re-derive observed state mechanically, emit
[RECONCILE: ... MATCH|MISMATCH]. Its safety-relevant claims must be falsifiable rather than
prose: (1) a MISMATCH blocks planning — the only lawful action is correcting the ledger FIRST,
never proceeding alongside; (2) a claimed-verified task whose acceptance evidence is absent is
itself a MISMATCH and reverts to unverified; (3) the ratchet — reconciliation corrections never
spend down cycles or layer2_passes, or "reconcile" becomes a resume-shaped budget refund (the
laundering D-22 exists to stop). This checker reads a decision-table fixture and asserts those
invariants; a table letting a MISMATCH proceed, an evidence-less verified claim survive, or a
correction refund budget is rejected.

Usage:
  check-reconcile-invariants.py <fixture.json>   validate a decision-table fixture (exit 0 if sound)
  check-reconcile-invariants.py --selftest        red/green self-test (needs no repo state)

Exit 0 + RECONCILE_OK on success; exit 1 + named defects otherwise. stdlib only.
"""
import json
import sys

ACTIONS = ("PROCEED", "CORRECT_FIRST")
REQUIRED_CASES = (
    "resume_match_proceeds",
    "resume_mismatch_corrects_first",
    "claimed_verified_evidence_absent",
)
BOOL_FIELDS = ("mismatch", "evidence_absent_for_claimed_verified", "counters_decremented")


def check(table):
    """Return a list of invariant violations for a decision table (empty = sound)."""
    errors = []
    cases = table.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixture has no non-empty 'cases' list")
        return errors
    by_name = {}
    match_seen = mismatch_seen = False
    for i, c in enumerate(cases):
        name = c.get("case", "<index %d>" % i)
        by_name[name] = c
        for field in BOOL_FIELDS:
            if c.get(field) not in (True, False):
                errors.append("case '%s': '%s' must be a JSON boolean" % (name, field))
        action = c.get("action")
        if action not in ACTIONS:
            errors.append("case '%s': 'action' must be one of %s" % (name, "|".join(ACTIONS)))
            continue
        if c.get("mismatch") is True:
            mismatch_seen = True
            if action != "CORRECT_FIRST":
                errors.append(
                    "case '%s': a MISMATCH must CORRECT_FIRST — planning that continues on top "
                    "of a ledger known to be wrong is the fictional-progress failure this duty "
                    "exists to stop" % name)
        if c.get("mismatch") is False:
            match_seen = True
            if c.get("evidence_absent_for_claimed_verified") is True:
                errors.append(
                    "case '%s': absent acceptance evidence for a claimed-verified task IS a "
                    "mismatch — declaring MATCH over it is reconciliation laundering" % name)
        if c.get("evidence_absent_for_claimed_verified") is True \
                and c.get("reverts_to_unverified") is not True:
            errors.append(
                "case '%s': a claimed-verified task with absent evidence must revert to "
                "unverified in the ledger — narrated verification is not verification" % name)
        if c.get("counters_decremented") is True:
            errors.append(
                "case '%s': reconciliation corrections never spend down cycles or "
                "layer2_passes — a resume-shaped budget refund is treadmill laundering" % name)
    for req in REQUIRED_CASES:
        if req not in by_name:
            errors.append("missing required case '%s'" % req)
    if not match_seen or not mismatch_seen:
        errors.append("table is vacuous: it needs at least one MATCH and one MISMATCH case")
    return errors


def _green():
    return {
        "cases": [
            {"case": "resume_match_proceeds", "mismatch": False,
             "evidence_absent_for_claimed_verified": False,
             "counters_decremented": False, "action": "PROCEED"},
            {"case": "resume_mismatch_corrects_first", "mismatch": True,
             "evidence_absent_for_claimed_verified": False,
             "counters_decremented": False, "action": "CORRECT_FIRST"},
            {"case": "claimed_verified_evidence_absent", "mismatch": True,
             "evidence_absent_for_claimed_verified": True,
             "reverts_to_unverified": True,
             "counters_decremented": False, "action": "CORRECT_FIRST"},
        ],
    }


def selftest():
    """Red/green self-test: accept a sound table, reject unsound ones."""
    green = _green()
    if check(green):
        return ["selftest GREEN table was rejected: %s" % check(green)]
    reds = []
    proceed = json.loads(json.dumps(green))
    proceed["cases"][1]["action"] = "PROCEED"  # mismatch -> proceed
    if not check(proceed):
        reds.append("selftest RED table (MISMATCH -> PROCEED) was accepted")
    launder = json.loads(json.dumps(green))
    launder["cases"][2]["mismatch"] = False  # absent evidence declared MATCH
    if not check(launder):
        reds.append("selftest RED table (absent evidence declared MATCH) was accepted")
    refund = json.loads(json.dumps(green))
    refund["cases"][1]["counters_decremented"] = True  # correction refunds budget
    if not check(refund):
        reds.append("selftest RED table (correction refunds budget) was accepted")
    unreverted = json.loads(json.dumps(green))
    del unreverted["cases"][2]["reverts_to_unverified"]  # evidence absent, no revert
    if not check(unreverted):
        reds.append("selftest RED table (absent evidence without revert) was accepted")
    return reds


def main(argv):
    if len(argv) != 2:
        print("usage: check-reconcile-invariants.py <fixture.json> | --selftest")
        return 1
    if argv[1] == "--selftest":
        defects = selftest()
        if defects:
            for d in defects:
                print("DEFECT: %s" % d)
            return 1
        print("RECONCILE_SELFTEST_OK")
        return 0
    try:
        with open(argv[1], encoding="utf-8") as fh:
            table = json.load(fh)
    except (OSError, ValueError) as exc:
        print("DEFECT: cannot read fixture: %s" % exc)
        return 1
    defects = check(table)
    if defects:
        for d in defects:
            print("DEFECT: %s" % d)
        return 1
    print("RECONCILE_OK: %d cases" % len(table["cases"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
