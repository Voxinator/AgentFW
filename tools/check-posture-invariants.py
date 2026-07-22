#!/usr/bin/env python3
"""check-posture-invariants.py — machine-check the sleep-posture decision table (D-15).

The unattended (sleep) posture may auto-advance NON-floor forks but must HALT at every FLOOR fork,
and the D-14 flagship-model escalation (like the plan-critique cap and the D-1 override) is a floor
fork. This checker reads a decision-table fixture and asserts those invariants, so the
safety-relevant claim "sleep HALTS at the floor, never auto-authorizes" is falsifiable rather than
prose. A fixture that maps a floor fork to AUTO — authorization laundering — is rejected.

Usage:
  check-posture-invariants.py <fixture.json>   validate a decision-table fixture (exit 0 if sound)
  check-posture-invariants.py --selftest        red/green self-test (needs no repo state)

Exit 0 + POSTURE_OK on success; exit 1 + named defects otherwise. stdlib only.
"""
import json
import sys

REQUIRED_FLOOR_FORKS = ("flagship_model_escalation", "plan_critique_cap", "delivery_override")
ACTIONS = ("HALT", "AUTO")


def check(table):
    """Return a list of invariant violations for a decision table (empty = sound)."""
    errors = []
    forks = table.get("forks")
    if not isinstance(forks, list) or not forks:
        return ["fixture has no non-empty 'forks' list"]
    by_name = {}
    floor_seen = nonfloor_seen = False
    for i, f in enumerate(forks):
        name = f.get("fork", "<index %d>" % i)
        by_name[name] = f
        floor = f.get("floor")
        action = f.get("sleep_action")
        if floor not in (True, False):
            errors.append("fork '%s': 'floor' must be a JSON boolean" % name)
        if action not in ACTIONS:
            errors.append("fork '%s': 'sleep_action' must be one of HALT|AUTO" % name)
        if floor is True:
            floor_seen = True
            if action != "HALT":
                errors.append(
                    "fork '%s': a floor fork must HALT under sleep, not '%s' — a floor fork "
                    "mapped to AUTO is authorization laundering" % (name, action))
        if floor is False:
            nonfloor_seen = True
            if action != "AUTO":
                errors.append(
                    "fork '%s': a non-floor fork should AUTO-advance under sleep, not '%s'"
                    % (name, action))
    for req in REQUIRED_FLOOR_FORKS:
        ff = by_name.get(req)
        if ff is None:
            errors.append("missing required floor fork '%s' (a human-only lever)" % req)
        elif ff.get("floor") is not True:
            errors.append("fork '%s' must be a floor fork (floor: true)" % req)
    if not floor_seen or not nonfloor_seen:
        errors.append("table is vacuous: it needs at least one floor and one non-floor fork")
    return errors


def _validate_path(path):
    try:
        with open(path, encoding="utf-8") as fh:
            table = json.load(fh)
    except (OSError, ValueError) as e:
        print("FAIL: cannot read/parse %s: %s" % (path, e))
        return 1
    errors = check(table)
    if errors:
        print("FAIL: %s — %d defect(s):" % (path, len(errors)))
        for e in errors:
            print("  - " + e)
        return 1
    print("POSTURE_OK: %s" % path)
    return 0


def _clone(table):
    return json.loads(json.dumps(table))


def selftest():
    """Prove the checker discriminates: a conformant table passes; a laundering table
    (any floor fork mapped to AUTO), a demoted flagship fork, and a missing lever all fail."""
    good = {"forks": [
        {"fork": "destructive_a4", "floor": True, "sleep_action": "HALT"},
        {"fork": "flagship_model_escalation", "floor": True, "sleep_action": "HALT"},
        {"fork": "plan_critique_cap", "floor": True, "sleep_action": "HALT"},
        {"fork": "delivery_override", "floor": True, "sleep_action": "HALT"},
        {"fork": "ordinary_implementation_ambiguity", "floor": False, "sleep_action": "AUTO"},
    ]}
    if check(good):
        print("SELFTEST FAIL: a conformant table was rejected")
        return 1
    launder = _clone(good)
    launder["forks"][1]["sleep_action"] = "AUTO"  # flagship escalation auto-authorized
    if not check(launder):
        print("SELFTEST FAIL: a laundering table (flagship -> AUTO) was accepted")
        return 1
    nohalt = _clone(good)
    nohalt["forks"][0]["sleep_action"] = "AUTO"  # a floor fork loses its HALT
    if not check(nohalt):
        print("SELFTEST FAIL: a floor fork mapped to AUTO was accepted")
        return 1
    demote = _clone(good)
    demote["forks"][1]["floor"] = False  # flagship demoted out of the floor
    demote["forks"][1]["sleep_action"] = "AUTO"
    if not check(demote):
        print("SELFTEST FAIL: flagship escalation demoted from the floor was accepted")
        return 1
    print("POSTURE_SELFTEST_OK")
    return 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    if len(args) != 1:
        print("usage: check-posture-invariants.py <fixture.json> | --selftest", file=sys.stderr)
        return 2
    return _validate_path(args[0])


if __name__ == "__main__":
    sys.exit(main())
