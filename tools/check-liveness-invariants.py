#!/usr/bin/env python3
"""check-liveness-invariants.py — machine-check the liveness-budget decision table (D-2).

The global liveness budget bounds review expenditure per OBJECTIVE across plan cycles. Its three
safety-relevant claims must be falsifiable rather than prose: (1) once the budget is exhausted,
no new plan/critique cycle may run — the only lawful actions are HALT, RESCOPE, or a proactive
OVERRIDE_OFFER (and exhausted + open floor blocker is always HALT); (2) a fresh plan for the same
objective never resets the counters — a table that resets on rename is treadmill laundering;
(3) budget & ledger inheritance (D-22) — a case naming a `root_objective` spends from that root's
durable ledger, so decomposing into a sub-objective, renaming, or resuming in another runtime
never resets the counters. This checker reads a decision-table fixture and asserts those
invariants; a fixture mapping an exhausted budget to NEW_CYCLE/CONTINUE, resetting counters on a
same-objective plan, or resetting them on a rooted sub-objective, is rejected.

Usage:
  check-liveness-invariants.py <fixture.json>   validate a decision-table fixture (exit 0 if sound)
  check-liveness-invariants.py --selftest        red/green self-test (needs no repo state)

Exit 0 + LIVENESS_OK on success; exit 1 + named defects otherwise. stdlib only.
"""
import json
import sys

ACTIONS = ("CONTINUE", "NEW_CYCLE", "HALT", "RESCOPE", "OVERRIDE_OFFER")
EXHAUSTED_LEGAL = ("HALT", "RESCOPE", "OVERRIDE_OFFER")
REQUIRED_CASES = (
    "exhausted_open_floor_blocker",
    "exhausted_quality_blockers_only",
    "exhausted_human_declines_override",
    "fresh_plan_same_objective",
    "renamed_plan_same_objective",
    "sub_objective_inherits_root_counters",
)
BOOL_FIELDS = ("budget_exhausted", "open_floor_blocker", "same_objective", "counters_reset")


def check(table):
    """Return a list of invariant violations for a decision table (empty = sound)."""
    errors = []
    budget = table.get("budget")
    if not isinstance(budget, dict) or not all(
            isinstance(budget.get(k), int) and not isinstance(budget.get(k), bool)
            and budget.get(k) > 0
            for k in ("cycles", "layer2_passes")):
        errors.append("fixture needs a 'budget' object with positive integer "
                      "'cycles' and 'layer2_passes'")
    cases = table.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixture has no non-empty 'cases' list")
        return errors
    by_name = {}
    exhausted_seen = under_seen = False
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
        if name.startswith("exhausted_") and c.get("budget_exhausted") is not True:
            errors.append(
                "case '%s': an 'exhausted_*' case must declare budget_exhausted: true — "
                "flipping the flag instead of the action is fixture laundering" % name)
        if c.get("budget_exhausted") is True:
            exhausted_seen = True
            if action not in EXHAUSTED_LEGAL:
                errors.append(
                    "case '%s': an exhausted budget permits only %s, not '%s' — an exhausted "
                    "objective granted another cycle is the treadmill this budget exists to stop"
                    % (name, "/".join(EXHAUSTED_LEGAL), action))
            if c.get("open_floor_blocker") is True and action != "HALT":
                errors.append(
                    "case '%s': exhausted budget + open floor blocker must HALT, not '%s' — "
                    "the floor is never resolved by rescoping or an override offer"
                    % (name, action))
        if c.get("budget_exhausted") is False:
            under_seen = True
        if "root_objective" in c:
            root = c.get("root_objective")
            if not isinstance(root, str) or not root:
                errors.append(
                    "case '%s': 'root_objective' must be a non-empty string naming the root "
                    "objective whose ledger this case spends from" % name)
            if c.get("counters_reset") is True:
                errors.append(
                    "case '%s': a case naming a root_objective spends from that root's ledger — "
                    "resetting counters on decomposition, rename, or a cross-runtime resume is "
                    "treadmill laundering" % name)
        if c.get("same_objective") is True and c.get("counters_reset") is True:
            errors.append(
                "case '%s': a same-objective plan must never reset the counters — a rename or "
                "renarrowing that resets the budget is treadmill laundering" % name)
    for req in REQUIRED_CASES:
        if req not in by_name:
            errors.append("missing required case '%s'" % req)
    if not exhausted_seen or not under_seen:
        errors.append("table is vacuous: it needs at least one exhausted and one "
                      "under-budget case")
    return errors


def selftest():
    """Red/green self-test: the checker must accept a sound table and reject unsound ones."""
    green = {
        "budget": {"cycles": 2, "layer2_passes": 4},
        "cases": [
            {"case": r, "budget_exhausted": r.startswith("exhausted"),
             "open_floor_blocker": r == "exhausted_open_floor_blocker",
             "same_objective": True, "counters_reset": False,
             "action": ("HALT" if r in ("exhausted_open_floor_blocker",
                                        "exhausted_human_declines_override")
                        else "OVERRIDE_OFFER" if r == "exhausted_quality_blockers_only"
                        else "NEW_CYCLE")}
            for r in REQUIRED_CASES
        ],
    }
    # the inheritance case (D-22) is a sub-objective spending from its root's ledger
    green["cases"][-1]["root_objective"] = "root-objective-slug"
    green["cases"][-1]["same_objective"] = False
    if check(green):
        return ["selftest GREEN table was rejected: %s" % check(green)]
    reds = []
    laundered = json.loads(json.dumps(green))
    laundered["cases"][1]["action"] = "NEW_CYCLE"  # exhausted_quality_blockers_only
    if not check(laundered):
        reds.append("selftest RED table (exhausted -> NEW_CYCLE) was accepted")
    reset = json.loads(json.dumps(green))
    reset["cases"][3]["counters_reset"] = True  # fresh_plan_same_objective
    if not check(reset):
        reds.append("selftest RED table (same-objective counter reset) was accepted")
    floored = json.loads(json.dumps(green))
    floored["cases"][0]["action"] = "OVERRIDE_OFFER"  # exhausted_open_floor_blocker
    if not check(floored):
        reds.append("selftest RED table (floor blocker -> OVERRIDE_OFFER) was accepted")
    flagged = json.loads(json.dumps(green))
    flagged["cases"][1]["budget_exhausted"] = False  # exhausted_quality_blockers_only
    flagged["cases"][1]["action"] = "NEW_CYCLE"
    if not check(flagged):
        reds.append("selftest RED table (exhausted_* flag laundering) was accepted")
    inherited = json.loads(json.dumps(green))
    inherited["cases"][-1]["counters_reset"] = True  # sub_objective_inherits_root_counters
    if not check(inherited):
        reds.append("selftest RED table (rooted sub-objective resets counters) was accepted")
    rootless = json.loads(json.dumps(green))
    rootless["cases"][-1]["root_objective"] = ""
    if not check(rootless):
        reds.append("selftest RED table (empty root_objective) was accepted")
    dropped = json.loads(json.dumps(green))
    del dropped["cases"][-1]
    if not check(dropped):
        reds.append("selftest RED table (missing inheritance case) was accepted")
    return reds


def main(argv):
    if len(argv) != 2:
        print("usage: check-liveness-invariants.py <fixture.json> | --selftest")
        return 1
    if argv[1] == "--selftest":
        defects = selftest()
        if defects:
            for d in defects:
                print("DEFECT: %s" % d)
            return 1
        print("LIVENESS_SELFTEST_OK")
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
    print("LIVENESS_OK: %d cases, budget %s cycles / %s layer2 passes"
          % (len(table["cases"]), table["budget"]["cycles"], table["budget"]["layer2_passes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
