#!/usr/bin/env python3
"""check-reapproach-invariants.py — machine-check the re-approach fork decision table (D-31).

The re-approach fork is the fifth hard-2-pass-cap menu option and the fourth branch of the D-2
exhaustion fork: when the plan is sound but the acceptance CONTRACTS are wrong (verification
strategy re-axed onto the wrong ground, or a verifier returns an IMPOSSIBLE-COMMAND contract
defect), the correct move is to retain the plan and requirements, re-author only the contracts,
charge exactly one cycle, and re-enter Layer 1. Left unbounded and judged, this becomes exactly
the soft override the field report warns against — the same treadmill re-axed from plans onto
verification strategies. Two claims must be falsifiable rather than prose, and this checker is
where they are made so:

  1. **Eligibility is mechanically derived, never judged.** A re-approach is eligible iff every
     open blocker is `contract-mechanics` class AND no open blocker's finding `cites` a
     `requirement` id. A blocker citing only `task` or `contract` ids is contract-mechanics by
     construction; a blocker citing a requirement id means the requirement itself is in dispute,
     which re-authoring contracts cannot answer. No free-text field may override this derivation —
     a case's declared `eligibility` must equal the value derived from its `open_blockers`.
  2. **Bounded: at most once per objective.** A second selection for the same objective is
     INELIGIBLE regardless of how clean its blockers are — `already_used_this_objective: true`
     forces `action: INELIGIBLE` even when the blocker-derived `eligibility` is ELIGIBLE.
     An `IMPOSSIBLE-COMMAND` verifier verdict (a CONTRACT defect, `policy/acceptance-contract.md`)
     always routes to re-approach (`action: ROUTE_REAPPROACH`), independent of blocker composition
     or prior use — it is a different trigger, not a third eligibility input.

Case names are load-bearing: e.g. a `blocker-cites-task-id-only` case whose blockers cite a
requirement id, or a `non-contract-mechanics-blocker-open` case with no non-contract-mechanics
blocker, is fixture laundering — naming the healthy case while testing the unhealthy one (or vice
versa) — and is rejected on its own.

Usage:
  check-reapproach-invariants.py <fixture.json>   validate a decision-table fixture (exit 0 if sound)
  check-reapproach-invariants.py --selftest       red/green self-test (needs no repo state)

Exit 0 + REAPPROACH_OK (or REAPPROACH_SELFTEST_OK) on success; exit 1 + named defects otherwise.
stdlib only.
"""
import json
import sys

ACTIONS = ("ALLOW", "INELIGIBLE", "ROUTE_REAPPROACH")
ELIGIBILITY_VALUES = ("ELIGIBLE", "INELIGIBLE")
BLOCKER_CLASSES = ("contract-mechanics", "other")
CITES_VALUES = ("task", "contract", "requirement", None)
REQUIRED_CASES = (
    "eligible-first-selection",
    "second-selection-same-objective",
    "non-contract-mechanics-blocker-open",
    "blocker-cites-requirement-id",
    "blocker-cites-task-id-only",
    "impossible-command-verdict",
)


def _is_name(value):
    return isinstance(value, str) and value.strip() != ""


def _check_blockers(name, blockers, errors):
    """Validate open_blockers shape. Returns True if the list is well-formed."""
    if not isinstance(blockers, list):
        errors.append("case '%s': 'open_blockers' must be a (possibly empty) list" % name)
        return False
    ok = True
    for i, b in enumerate(blockers):
        if not isinstance(b, dict):
            errors.append("case '%s': open_blockers[%d] must be an object" % (name, i))
            ok = False
            continue
        if b.get("class") not in BLOCKER_CLASSES:
            errors.append(
                "case '%s': open_blockers[%d].class must be one of %s"
                % (name, i, "|".join(BLOCKER_CLASSES)))
            ok = False
        if b.get("cites", None) not in CITES_VALUES:
            errors.append(
                "case '%s': open_blockers[%d].cites must be one of task|contract|requirement|null"
                % (name, i))
            ok = False
    return ok


def _derive_eligibility(blockers):
    """Mechanical derivation: ELIGIBLE iff every blocker is contract-mechanics AND none cites a
    requirement id. Vacuously ELIGIBLE when there are no open blockers."""
    all_contract_mechanics = all(b.get("class") == "contract-mechanics" for b in blockers)
    none_cite_requirement = not any(b.get("cites") == "requirement" for b in blockers)
    return "ELIGIBLE" if (all_contract_mechanics and none_cite_requirement) else "INELIGIBLE"


def check(table):
    """Return a list of invariant violations for a re-approach decision table (empty = sound)."""
    errors = []
    if not isinstance(table, dict):
        return ["fixture must be a JSON object"]
    cases = table.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixture has no non-empty 'cases' list")
        return errors

    seen = set()
    actions_seen = set()
    eligibility_seen = set()
    already_used_true_seen = False
    cites_requirement_seen = False
    other_class_seen = False
    verdict_seen = False

    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append("cases[%d] must be an object" % i)
            continue
        name = case.get("case")
        if not _is_name(name):
            errors.append("case at index %d has no 'case' name" % i)
            name = "<index %d>" % i
        seen.add(name)

        blockers = case.get("open_blockers")
        if not _check_blockers(name, blockers, errors):
            continue
        derived = _derive_eligibility(blockers)

        declared_elig = case.get("eligibility")
        if declared_elig not in ELIGIBILITY_VALUES:
            errors.append(
                "case '%s': 'eligibility' must be one of %s"
                % (name, "|".join(ELIGIBILITY_VALUES)))
            continue
        if declared_elig != derived:
            errors.append(
                "case '%s': declared eligibility '%s' does not match the blocker-derived "
                "eligibility '%s' — eligibility is MECHANICALLY DERIVED from open_blockers "
                "(contract-mechanics class + no requirement citation), never asserted "
                "independently" % (name, declared_elig, derived))
        eligibility_seen.add(declared_elig)
        if derived == "ELIGIBLE":
            eligibility_seen.add("ELIGIBLE")

        already_used = case.get("already_used_this_objective", False)
        if already_used not in (True, False):
            errors.append(
                "case '%s': 'already_used_this_objective' must be a JSON boolean" % name)
            continue
        if already_used:
            already_used_true_seen = True

        verdict = case.get("verifier_verdict")
        if verdict not in (None, "IMPOSSIBLE-COMMAND"):
            errors.append(
                "case '%s': 'verifier_verdict' must be null or 'IMPOSSIBLE-COMMAND'" % name)
            continue
        if verdict == "IMPOSSIBLE-COMMAND":
            verdict_seen = True

        action = case.get("action")
        if action not in ACTIONS:
            errors.append("case '%s': 'action' must be one of %s" % (name, "|".join(ACTIONS)))
            continue
        actions_seen.add(action)

        if verdict == "IMPOSSIBLE-COMMAND":
            expected = "ROUTE_REAPPROACH"
        elif derived == "INELIGIBLE":
            expected = "INELIGIBLE"
        elif already_used:
            expected = "INELIGIBLE"
        else:
            expected = "ALLOW"
        if action != expected:
            errors.append(
                "case '%s': action '%s' but the mechanical derivation requires '%s' "
                "(blocker-eligibility=%s, already_used_this_objective=%s, verifier_verdict=%s)"
                % (name, action, expected, derived, already_used, verdict))

        if any(b.get("cites") == "requirement" for b in blockers):
            cites_requirement_seen = True
        if any(b.get("class") == "other" for b in blockers):
            other_class_seen = True

        # Case-name laundering guards: the name must match what the row actually exercises.
        if name == "eligible-first-selection":
            if already_used:
                errors.append(
                    "case '%s' must declare already_used_this_objective: false — it tests "
                    "the FIRST selection" % name)
            if derived != "ELIGIBLE":
                errors.append(
                    "case '%s' must use blockers that derive ELIGIBLE" % name)
            if action != "ALLOW":
                errors.append("case '%s' must resolve to action ALLOW" % name)
        if name == "second-selection-same-objective":
            if not already_used:
                errors.append(
                    "case '%s' must declare already_used_this_objective: true — the bound "
                    "'at most once per objective' is exactly what this case exercises" % name)
            if action != "INELIGIBLE":
                errors.append("case '%s' must resolve to action INELIGIBLE" % name)
        if name == "non-contract-mechanics-blocker-open":
            if not any(b.get("class") == "other" for b in blockers):
                errors.append(
                    "case '%s' must include a blocker with class 'other' — otherwise it is "
                    "not exercising a non-contract-mechanics blocker at all" % name)
            if action != "INELIGIBLE":
                errors.append("case '%s' must resolve to action INELIGIBLE" % name)
        if name == "blocker-cites-requirement-id":
            if not any(b.get("cites") == "requirement" for b in blockers):
                errors.append(
                    "case '%s' must include a blocker citing 'requirement' — otherwise it is "
                    "not exercising a requirement-id citation at all" % name)
            if action != "INELIGIBLE":
                errors.append("case '%s' must resolve to action INELIGIBLE" % name)
        if name == "blocker-cites-task-id-only":
            if any(b.get("cites") == "requirement" for b in blockers) or \
               any(b.get("class") != "contract-mechanics" for b in blockers):
                errors.append(
                    "case '%s' must contain ONLY contract-mechanics blockers citing task/"
                    "contract ids, never a requirement id or an 'other'-class blocker — the "
                    "predicate must not reject a healthy contract-mechanics blocker" % name)
            if action != "ALLOW":
                errors.append(
                    "case '%s' must resolve to action ALLOW — a blocker citing only task or "
                    "contract ids is contract-mechanics by construction" % name)
        if name == "impossible-command-verdict":
            if verdict != "IMPOSSIBLE-COMMAND":
                errors.append(
                    "case '%s' must carry verifier_verdict IMPOSSIBLE-COMMAND" % name)
            if action != "ROUTE_REAPPROACH":
                errors.append(
                    "case '%s' must resolve to action ROUTE_REAPPROACH — an IMPOSSIBLE-COMMAND "
                    "verdict routes to re-approach, never to a work-defect retry" % name)

    for required in REQUIRED_CASES:
        if required not in seen:
            errors.append("missing required case '%s'" % required)
    if not already_used_true_seen:
        errors.append(
            "table is vacuous: no case exercises already_used_this_objective true — the "
            "once-per-objective bound is never tested")
    if not cites_requirement_seen:
        errors.append(
            "table is vacuous: no case exercises a blocker citing a requirement id")
    if not other_class_seen:
        errors.append(
            "table is vacuous: no case exercises a non-contract-mechanics ('other' class) "
            "blocker")
    if not verdict_seen:
        errors.append(
            "table is vacuous: no case exercises the IMPOSSIBLE-COMMAND verdict routing")
    for action in ACTIONS:
        if action not in actions_seen:
            errors.append("table is vacuous: no case exercises action '%s'" % action)
    for elig in ELIGIBILITY_VALUES:
        if elig not in eligibility_seen:
            errors.append("table is vacuous: no case exercises eligibility '%s'" % elig)
    return errors


def _green():
    """A minimal sound table, used as the self-test's green baseline and red-mutation base."""
    return {
        "cases": [
            {
                "case": "eligible-first-selection",
                "open_blockers": [{"class": "contract-mechanics", "cites": "task"}],
                "already_used_this_objective": False,
                "verifier_verdict": None,
                "eligibility": "ELIGIBLE",
                "action": "ALLOW",
            },
            {
                "case": "second-selection-same-objective",
                "open_blockers": [{"class": "contract-mechanics", "cites": "task"}],
                "already_used_this_objective": True,
                "verifier_verdict": None,
                "eligibility": "ELIGIBLE",
                "action": "INELIGIBLE",
            },
            {
                "case": "non-contract-mechanics-blocker-open",
                "open_blockers": [{"class": "other", "cites": None}],
                "already_used_this_objective": False,
                "verifier_verdict": None,
                "eligibility": "INELIGIBLE",
                "action": "INELIGIBLE",
            },
            {
                "case": "blocker-cites-requirement-id",
                "open_blockers": [{"class": "contract-mechanics", "cites": "requirement"}],
                "already_used_this_objective": False,
                "verifier_verdict": None,
                "eligibility": "INELIGIBLE",
                "action": "INELIGIBLE",
            },
            {
                "case": "blocker-cites-task-id-only",
                "open_blockers": [
                    {"class": "contract-mechanics", "cites": "task"},
                    {"class": "contract-mechanics", "cites": "contract"},
                ],
                "already_used_this_objective": False,
                "verifier_verdict": None,
                "eligibility": "ELIGIBLE",
                "action": "ALLOW",
            },
            {
                "case": "impossible-command-verdict",
                "open_blockers": [],
                "already_used_this_objective": False,
                "verifier_verdict": "IMPOSSIBLE-COMMAND",
                "eligibility": "ELIGIBLE",
                "action": "ROUTE_REAPPROACH",
            },
        ],
    }


def _mutate(fn):
    """Deep-copy the green baseline, apply fn, return the mutated table."""
    table = json.loads(json.dumps(_green()))
    fn(table)
    return table


def _by_name(table, name):
    for case in table["cases"]:
        if case["case"] == name:
            return case
    raise KeyError(name)


def selftest():
    """Red/green self-test: accept the sound table, reject every contracted unsound one."""
    baseline = check(_green())
    if baseline:
        return ["selftest GREEN table was rejected: %s" % "; ".join(baseline)]

    reds = [
        ("second-selection: ALLOW despite already_used_this_objective true",
         lambda t: _by_name(t, "second-selection-same-objective").update({"action": "ALLOW"})),
        ("non-contract-mechanics blocker: ALLOW despite an 'other'-class blocker",
         lambda t: _by_name(t, "non-contract-mechanics-blocker-open").update({"action": "ALLOW"})),
        ("blocker-cites-requirement-id: ALLOW despite a requirement citation",
         lambda t: _by_name(t, "blocker-cites-requirement-id").update({"action": "ALLOW"})),
        ("blocker-cites-task-id-only: eligibility flipped to INELIGIBLE",
         lambda t: _by_name(t, "blocker-cites-task-id-only").update({"eligibility": "INELIGIBLE"})),
        ("blocker-cites-task-id-only: action flipped to INELIGIBLE",
         lambda t: _by_name(t, "blocker-cites-task-id-only").update({"action": "INELIGIBLE"})),
        ("impossible-command-verdict: action not ROUTE_REAPPROACH",
         lambda t: _by_name(t, "impossible-command-verdict").update({"action": "ALLOW"})),
        ("impossible-command-verdict: verdict removed but action stays ROUTE_REAPPROACH",
         lambda t: _by_name(t, "impossible-command-verdict").update({"verifier_verdict": None})),
        ("eligible-first-selection: already_used_this_objective flipped true, action kept ALLOW",
         lambda t: _by_name(t, "eligible-first-selection").update(
             {"already_used_this_objective": True})),
        ("laundering: non-contract-mechanics-blocker-open case with no 'other'-class blocker",
         lambda t: _by_name(t, "non-contract-mechanics-blocker-open").update(
             {"open_blockers": [{"class": "contract-mechanics", "cites": "task"}],
              "eligibility": "ELIGIBLE", "action": "ALLOW"})),
        ("laundering: blocker-cites-requirement-id case with no requirement citation",
         lambda t: _by_name(t, "blocker-cites-requirement-id").update(
             {"open_blockers": [{"class": "contract-mechanics", "cites": "task"}],
              "eligibility": "ELIGIBLE", "action": "ALLOW"})),
        ("laundering: blocker-cites-task-id-only case that actually cites a requirement",
         lambda t: _by_name(t, "blocker-cites-task-id-only").update(
             {"open_blockers": [{"class": "contract-mechanics", "cites": "requirement"}],
              "eligibility": "INELIGIBLE", "action": "INELIGIBLE"})),
        ("laundering: eligible-first-selection with a non-eligible blocker set",
         lambda t: _by_name(t, "eligible-first-selection").update(
             {"open_blockers": [{"class": "other", "cites": None}],
              "eligibility": "INELIGIBLE", "action": "INELIGIBLE"})),
        ("laundering: second-selection-same-objective with already_used false",
         lambda t: _by_name(t, "second-selection-same-objective").update(
             {"already_used_this_objective": False, "action": "ALLOW"})),
        ("missing required case: impossible-command-verdict dropped",
         lambda t: t["cases"].remove(_by_name(t, "impossible-command-verdict"))),
        ("structural: blocker missing 'class' field",
         lambda t: _by_name(t, "blocker-cites-task-id-only")["open_blockers"][0].pop("class")),
        ("structural: action outside the enum",
         lambda t: _by_name(t, "eligible-first-selection").update({"action": "MAYBE"})),
        ("structural: eligibility outside the enum",
         lambda t: _by_name(t, "eligible-first-selection").update({"eligibility": "SORT-OF"})),
        ("vacuous: no case ever declares already_used_this_objective true",
         lambda t: _by_name(t, "second-selection-same-objective").update(
             {"already_used_this_objective": False, "action": "ALLOW"})),
    ]
    failures = []
    for label, mutation in reds:
        if not check(_mutate(mutation)):
            failures.append("selftest RED table (%s) was accepted" % label)
    return failures


def main(argv):
    if len(argv) != 2:
        print("usage: check-reapproach-invariants.py <fixture.json> | --selftest")
        return 1
    if argv[1] == "--selftest":
        defects = selftest()
        if defects:
            for defect in defects:
                print("DEFECT: %s" % defect)
            return 1
        print("REAPPROACH_SELFTEST_OK")
        return 0
    try:
        with open(argv[1], encoding="utf-8") as fh:
            table = json.load(fh)
    except (OSError, ValueError) as exc:
        print("DEFECT: cannot read fixture: %s" % exc)
        return 1
    defects = check(table)
    if defects:
        for defect in defects:
            print("DEFECT: %s" % defect)
        return 1
    print("REAPPROACH_OK: %d cases" % len(table["cases"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
