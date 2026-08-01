#!/usr/bin/env python3
"""check-delivery-invariants.py — machine-check the delivery ledger + zero-dispatch tripwire (D-21).

The liveness budget (D-2) bounds how much review an objective may spend; it does not notice the
failure mode that actually burns the budget: cycle after cycle of gate work that dispatches NO
worker. Review spend rises, delivered work stays at zero, and every individual cycle looks lawful
because the only counters anyone reads are review counters. D-21 adds the missing counter — a
durable per-objective ledger recording workers dispatched and tasks verified alongside cycles and
Layer-2 passes — plus a tripwire: two completed gate cycles with zero dispatched workers force the
D-2 exhaustion fork immediately, even when budget remains.

Two claims must be falsifiable rather than prose, and this checker is where they are made so:

  1. **Tripwire.** At or above the threshold with `workers_dispatched == 0`, the only lawful action
     is FORCE_FORK. A decision table mapping that state to CONTINUE is the treadmill the tripwire
     exists to stop. Symmetrically, FORCE_FORK below the threshold or with workers actually
     dispatched is a false trip, and a gate event without a `[SCOREBOARD: ...]` marker is a DEFECT,
     because an unmeasured ledger cannot fire any tripwire at all.
  2. **Ledger shape.** The fixture's `ledger_example` must carry the full durable `<plan>.ledger.json`
     record — objective AND root_objective (a sub-objective that forgets its root laundries the
     counters exactly the way a rename does), the four counters, and a non-empty `gate_events` list
     in which EVERY entry names the runtime that wrote it. Two runtimes read and append to the same
     file; an unattributed entry makes the trail unauditable.

Case names are load-bearing: a `*_zero_dispatch` case that declares dispatched workers, or a
`*_with_dispatch` case that declares none, is fixture laundering — flipping the input instead of the
action — and is rejected on its own.

Usage:
  check-delivery-invariants.py <fixture.json>   validate a decision-table fixture (exit 0 if sound)
  check-delivery-invariants.py --selftest       red/green self-test (needs no repo state)

Exit 0 + DELIVERY_OK (or DELIVERY_SELFTEST_OK) on success; exit 1 + named defects otherwise.
stdlib only.
"""
import json
import sys

ACTIONS = ("CONTINUE", "FORCE_FORK", "DEFECT")
LEDGER_KEYS = ("objective", "root_objective", "cycles", "layer2_passes",
               "workers_dispatched", "tasks_verified", "gate_events")
LEDGER_COUNTERS = ("cycles", "layer2_passes", "workers_dispatched", "tasks_verified")
LEDGER_NAMES = ("objective", "root_objective")
REQUIRED_CASES = (
    "first_cycle_no_dispatch_yet",
    "two_cycles_zero_dispatch",
    "two_cycles_with_dispatch",
    "sub_objective_zero_dispatch",
    "scoreboard_missing_at_gate_event",
)


def _is_count(value):
    """True for a JSON non-negative integer (JSON booleans are ints in Python — exclude them)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_name(value):
    return isinstance(value, str) and value.strip() != ""


def check_ledger(led):
    """Return violations of the durable <plan>.ledger.json shape (empty = sound)."""
    errors = []
    if not isinstance(led, dict):
        return ["fixture needs a 'ledger_example' object carrying the full durable "
                "<plan>.ledger.json shape — a decision table with no ledger record proves "
                "nothing about the artifact the tripwire reads"]
    for key in LEDGER_KEYS:
        if key not in led:
            errors.append(
                "ledger_example is missing required key '%s' — the durable ledger shape is "
                "%s, and a record missing any of them cannot be counted from" % (key, ", ".join(LEDGER_KEYS)))
    for key in LEDGER_NAMES:
        if key in led and not _is_name(led.get(key)):
            errors.append("ledger_example.%s must be a non-empty string slug — an unnamed "
                          "objective cannot inherit counters across plans" % key)
    for key in LEDGER_COUNTERS:
        if key in led and not _is_count(led.get(key)):
            errors.append("ledger_example.%s must be a non-negative integer counter" % key)
    events = led.get("gate_events")
    if "gate_events" in led:
        if not isinstance(events, list) or not events:
            errors.append("ledger_example.gate_events must be a non-empty list — one appended "
                          "entry per gate event is the whole audit trail")
        else:
            for i, event in enumerate(events):
                if not isinstance(event, dict):
                    errors.append("ledger_example.gate_events[%d] must be an object" % i)
                    continue
                if not _is_name(event.get("event")):
                    errors.append("ledger_example.gate_events[%d] must name the gate event "
                                  "in a non-empty 'event' field" % i)
                if not _is_name(event.get("runtime")):
                    errors.append(
                        "ledger_example.gate_events[%d] does not name its writing runtime — "
                        "both runtimes append to the same ledger, so an unattributed entry "
                        "makes the trail unauditable" % i)
    return errors


def check(table):
    """Return a list of invariant violations for a delivery decision table (empty = sound)."""
    errors = []
    tripwire = table.get("tripwire")
    threshold = tripwire.get("zero_dispatch_cycles") if isinstance(tripwire, dict) else None
    if not (isinstance(threshold, int) and not isinstance(threshold, bool) and threshold >= 1):
        errors.append("fixture needs a 'tripwire' object with a positive integer "
                      "'zero_dispatch_cycles' threshold")
        return errors
    errors.extend(check_ledger(table.get("ledger_example")))
    cases = table.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixture has no non-empty 'cases' list")
        return errors

    seen = set()
    actions_seen = set()
    tripped_seen = under_seen = root_seen = False
    for i, case in enumerate(cases):
        name = case.get("case")
        if not _is_name(name):
            errors.append("case at index %d has no 'case' name" % i)
            name = "<index %d>" % i
        seen.add(name)
        action = case.get("action")
        if action not in ACTIONS:
            errors.append("case '%s': 'action' must be one of %s"
                          % (name, "|".join(ACTIONS)))
            continue
        actions_seen.add(action)

        scoreboard = case.get("scoreboard_emitted", True)
        if scoreboard not in (True, False):
            errors.append("case '%s': 'scoreboard_emitted' must be a JSON boolean" % name)
            continue
        if scoreboard is False:
            if action != "DEFECT":
                errors.append(
                    "case '%s': a gate event with no [SCOREBOARD:] marker is a DEFECT, not "
                    "'%s' — an unemitted scoreboard is how a zero-dispatch objective stays "
                    "invisible" % (name, action))
            continue
        if action == "DEFECT":
            errors.append(
                "case '%s': DEFECT is reserved for a missing scoreboard marker; a case with "
                "scoreboard_emitted true must resolve to CONTINUE or FORCE_FORK" % name)
            continue

        cycles = case.get("completed_cycles")
        dispatched = case.get("workers_dispatched")
        if not _is_count(cycles) or not _is_count(dispatched):
            errors.append("case '%s': 'completed_cycles' and 'workers_dispatched' must be "
                          "non-negative integers" % name)
            continue
        if "zero_dispatch" in name and dispatched != 0:
            errors.append(
                "case '%s': a '*_zero_dispatch' case must declare workers_dispatched: 0 — "
                "flipping the input instead of the action is fixture laundering" % name)
        if name.endswith("with_dispatch") and dispatched == 0:
            errors.append(
                "case '%s': a '*_with_dispatch' case must declare workers_dispatched > 0 — "
                "flipping the input instead of the action is fixture laundering" % name)
        if name.startswith("sub_objective") and not _is_name(case.get("root_objective")):
            errors.append(
                "case '%s': a sub-objective case must carry its 'root_objective' — a "
                "sub-objective that forgets its root resets the delivery counters the same "
                "way a rename resets the liveness counters" % name)
        if _is_name(case.get("root_objective")):
            root_seen = True

        if cycles >= threshold and dispatched == 0:
            tripped_seen = True
            if action != "FORCE_FORK":
                errors.append(
                    "case '%s': %d completed cycles with zero workers dispatched must "
                    "FORCE_FORK, not '%s' — the zero-dispatch tripwire fires even when "
                    "liveness budget remains" % (name, cycles, action))
        else:
            under_seen = True
            if action == "FORCE_FORK":
                errors.append(
                    "case '%s': FORCE_FORK fired at %d/%d cycles with %d workers dispatched — "
                    "the tripwire must not fire below the threshold or once work has been "
                    "dispatched" % (name, cycles, threshold, dispatched))

    for required in REQUIRED_CASES:
        if required not in seen:
            errors.append("missing required case '%s'" % required)
    if not tripped_seen or not under_seen:
        errors.append("table is vacuous: it needs at least one tripped (>= threshold, zero "
                      "dispatch) and one untripped case")
    for action in ACTIONS:
        if action not in actions_seen:
            errors.append("table is vacuous: no case exercises action '%s'" % action)
    if not root_seen:
        errors.append("table is vacuous: no case carries a 'root_objective', so the "
                      "sub-objective rollup is never exercised")
    return errors


def _green():
    """A minimal sound table, used as the self-test's green baseline and red-mutation base."""
    return {
        "tripwire": {"zero_dispatch_cycles": 2},
        "ledger_example": {
            "objective": "selftest-objective",
            "root_objective": "selftest-objective",
            "cycles": 2,
            "layer2_passes": 3,
            "workers_dispatched": 0,
            "tasks_verified": 0,
            "gate_events": [
                {"event": "layer1_pass", "runtime": "claude-code"},
                {"event": "layer2_verdict", "runtime": "codex"},
            ],
        },
        "cases": [
            {"case": "first_cycle_no_dispatch_yet", "completed_cycles": 1,
             "workers_dispatched": 0, "scoreboard_emitted": True, "action": "CONTINUE"},
            {"case": "two_cycles_zero_dispatch", "completed_cycles": 2,
             "workers_dispatched": 0, "scoreboard_emitted": True, "action": "FORCE_FORK"},
            {"case": "two_cycles_with_dispatch", "completed_cycles": 2,
             "workers_dispatched": 3, "scoreboard_emitted": True, "action": "CONTINUE"},
            {"case": "sub_objective_zero_dispatch", "completed_cycles": 2,
             "workers_dispatched": 0, "root_objective": "parent-goal",
             "scoreboard_emitted": True, "action": "FORCE_FORK"},
            {"case": "scoreboard_missing_at_gate_event", "scoreboard_emitted": False,
             "action": "DEFECT"},
        ],
    }


def _mutate(fn):
    """Deep-copy the green baseline, apply fn, return the mutated table."""
    table = json.loads(json.dumps(_green()))
    fn(table)
    return table


def _set_action(index, action):
    def apply(table):
        table["cases"][index]["action"] = action
    return apply


def selftest():
    """Red/green self-test: accept the sound table, reject every contracted unsound one."""
    baseline = check(_green())
    if baseline:
        return ["selftest GREEN table was rejected: %s" % "; ".join(baseline)]

    reds = [
        ("tripwire: zero dispatch at threshold -> CONTINUE", _set_action(1, "CONTINUE")),
        ("tripwire: FORCE_FORK below threshold", _set_action(0, "FORCE_FORK")),
        ("tripwire: FORCE_FORK with workers dispatched", _set_action(2, "FORCE_FORK")),
        ("tripwire: sub-objective zero dispatch -> CONTINUE", _set_action(3, "CONTINUE")),
        ("scoreboard: missing marker -> CONTINUE instead of DEFECT",
         _set_action(4, "CONTINUE")),
        ("scoreboard: sub-objective case drops its root_objective",
         lambda t: t["cases"][3].pop("root_objective")),
        ("laundering: '*_zero_dispatch' case declares dispatched workers",
         lambda t: (t["cases"][1].update({"workers_dispatched": 4, "action": "CONTINUE"}))),
        ("ledger: missing root_objective", lambda t: t["ledger_example"].pop("root_objective")),
        ("ledger: missing workers_dispatched counter",
         lambda t: t["ledger_example"].pop("workers_dispatched")),
        ("ledger: gate event without a writing runtime",
         lambda t: t["ledger_example"]["gate_events"][1].pop("runtime")),
        ("ledger: empty gate_events trail",
         lambda t: t["ledger_example"].update({"gate_events": []})),
        ("ledger: non-integer counter",
         lambda t: t["ledger_example"].update({"tasks_verified": "several"})),
        ("ledger: record absent entirely", lambda t: t.pop("ledger_example")),
    ]
    failures = []
    for label, mutation in reds:
        if not check(_mutate(mutation)):
            failures.append("selftest RED table (%s) was accepted" % label)
    return failures


def main(argv):
    if len(argv) != 2:
        print("usage: check-delivery-invariants.py <fixture.json> | --selftest")
        return 1
    if argv[1] == "--selftest":
        defects = selftest()
        if defects:
            for defect in defects:
                print("DEFECT: %s" % defect)
            return 1
        print("DELIVERY_SELFTEST_OK")
        return 0
    try:
        with open(argv[1], encoding="utf-8") as fh:
            table = json.load(fh)
    except (OSError, ValueError) as exc:
        print("DEFECT: cannot read fixture: %s" % exc)
        return 1
    if not isinstance(table, dict):
        print("DEFECT: fixture must be a JSON object")
        return 1
    defects = check(table)
    if defects:
        for defect in defects:
            print("DEFECT: %s" % defect)
        return 1
    print("DELIVERY_OK: %d cases, tripwire at %d zero-dispatch cycles, ledger_example '%s' "
          "with %d gate events"
          % (len(table["cases"]), table["tripwire"]["zero_dispatch_cycles"],
             table["ledger_example"]["objective"],
             len(table["ledger_example"]["gate_events"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
