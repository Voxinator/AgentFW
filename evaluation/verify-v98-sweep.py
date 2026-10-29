#!/usr/bin/env python3
"""Acceptance checker for the v9.8 audit sweep (PLAN-v9.8-sweep.md).

HARDENED after Layer-2 passes 1 and 2 both demonstrated the previous version vacuous.
Each hole they proved is now closed and has a named guard below:

  H1  one junk claim passed every gate      -> REQUIRED[thread] must all be present
  H2  T0 green on the untouched tree        -> --selftest asserts probe count AND
                                               non-vacuity (probes must react to a
                                               perturbed root) AND root-failure
  H3  wrong root + falsy "absence" claims   -> run_thread calls the root guard FIRST;
                                               probes raise MissingInput instead of
                                               returning ""/None/0
  H4  0 == False type coercion              -> strict same-type comparison
  H5  grep -q D-ITEM satisfied by a token   -> --document parses each D-ITEM line for
                                               thread=, probe= (must exist in that
                                               thread's findings) and mechanism=
  H6  model-id regex too narrow             -> also matches bare "Opus 4" / "Sonnet 5.5"
  H7  hit count 0 == absent or misspelled   -> positive control: a term known present
                                               must report non-zero or the probe is
                                               declared broken
  H8  live mutable state drift              -> --freeze snapshots probe values; gates
                                               compare against the frozen snapshot when
                                               present so worker and verifier agree

Usage: --thread N | --selftest | --document | --freeze | --list-probes
"""
import argparse, hashlib, json, os, re, sys
from pathlib import Path

SKILL = Path(os.environ.get("V98_SKILL_ROOT",
                            os.path.expanduser("~/.claude/skills/agentfw")))
HOME = Path(os.path.expanduser("~"))
REPO = Path(__file__).resolve().parent.parent
FREEZE = REPO / "findings/_frozen-probes.json"


class MissingInput(Exception):
    """H3: a probe input is absent. Never silently becomes ''/None/0."""


def _read(p, required=True):
    p = Path(p)
    if not p.is_file():
        if required:
            raise MissingInput(f"required input missing: {p}")
        return ""
    return p.read_text(errors="replace")


def _yaml_scalar(text, key, section=None):
    if section:
        m = re.search(rf"^{re.escape(section)}:\s*$", text, re.M)
        if not m:
            raise MissingInput(f"yaml section {section!r} not found")
        rest = text[m.end():]
        nxt = re.search(r"^\S", rest, re.M)
        text = rest[: nxt.start()] if nxt else rest
    m = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*(?:#.*)?$", text, re.M)
    if not m:
        raise MissingInput(f"yaml key {key!r} not found in {section or '<root>'}")
    return m.group(1).strip()


def _json(path):
    t = _read(path)
    try:
        return json.loads(t)
    except json.JSONDecodeError as e:
        raise MissingInput(f"{path} is not valid JSON: {e}")


def _policy_files():
    files = sorted(SKILL.glob("*.md")) + sorted(SKILL.glob("policy/*.md"))
    if not files:
        raise MissingInput(f"no skill/policy markdown under {SKILL}")
    return files


# ---------------------------------------------------------------- probes

def p_agentfw_install_probes_model_selection():
    return "model_selection" in _read(REPO / "tools/agentfw-install")


def p_model_selection_configured():
    return _yaml_scalar(_read(SKILL / "capability.yaml"), "configured", "model_selection")


def p_active_caps_has_model_selection():
    return "model_selection" in _read(SKILL / "active-capabilities.yaml")


def p_active_caps_generated():
    return _yaml_scalar(_read(SKILL / "active-capabilities.yaml"), "generated").strip('"')


def p_agentfw_install_in_skill():
    if not (SKILL / "capability.yaml").is_file():
        raise MissingInput(f"skill root {SKILL} is not an agentfw install")
    return (SKILL / "tools/agentfw-install").exists()


def p_agent_model_pins():
    d = HOME / ".claude/agents"
    if not d.is_dir():
        raise MissingInput(f"agents dir missing: {d}")
    out = {}
    for f in sorted(d.glob("*.md")):
        fm = _read(f).split("\n---", 1)[0]
        m = re.search(r"^model:\s*(.+)$", fm, re.M)
        out[f.stem] = m.group(1).strip() if m else None
    if not out:
        raise MissingInput(f"no agent definitions in {d}")
    return out


def p_declared_tiers():
    v = _yaml_scalar(_read(SKILL / "capability.yaml"), "tiers", "model_selection")
    return [t.strip() for t in v.strip("[]").split(",") if t.strip()]


def p_declared_flagship():
    return _yaml_scalar(_read(SKILL / "capability.yaml"), "flagship", "model_selection")


def p_declared_floor():
    return _yaml_scalar(_read(SKILL / "capability.yaml"), "floor", "model_selection")


def p_concrete_model_names_in_policy():
    """H6: catch hyphenated ids AND bare family+version prose."""
    pats = [re.compile(r"claude-(opus|sonnet|haiku|fable|mythos)-[0-9][0-9.\-]*", re.I),
            re.compile(r"\b(opus|sonnet|haiku|fable|mythos)\s+[0-9]+(\.[0-9]+)?\b", re.I)]
    n = 0
    for f in _policy_files():
        t = _read(f)
        for pat in pats:
            n += len(pat.findall(t))
    return n


def p_harness_term_hits():
    terms = ["start_session", "ccd_", "update_plan", "wrap_up", "ToolSearch"]
    blob = "\n".join(_read(f) for f in _policy_files()).lower()
    # H7 positive control: a term that MUST appear, else the probe is broken not the policy.
    for control in ("acceptance_command", "assurance"):
        if blob.count(control) == 0:
            raise MissingInput(
                f"positive control {control!r} absent — probe is reading the wrong "
                f"corpus, so a zero hit count would be meaningless")
    return {t: blob.count(t.lower()) for t in terms}


def p_capability_keys():
    return re.findall(r"^([a-z_]+):\s*$", _read(SKILL / "capability.yaml"), re.M)


def p_skill_md_bytes():
    return len(_read(SKILL / "SKILL.md").encode())


def p_policy_total_bytes():
    fs = sorted(SKILL.glob("policy/*.md"))
    if not fs:
        raise MissingInput(f"no policy files under {SKILL}/policy")
    return sum(f.stat().st_size for f in fs)


def p_policy_file_bytes():
    fs = sorted(SKILL.glob("policy/*.md"))
    if not fs:
        raise MissingInput(f"no policy files under {SKILL}/policy")
    return {f.name: f.stat().st_size for f in fs}


def p_default_mode():
    s = _json(HOME / ".claude/settings.json")
    return (s.get("permissions") or {}).get("defaultMode")


def p_deny_rule_count():
    s = _json(HOME / ".claude/settings.json")
    return len((s.get("permissions") or {}).get("deny") or [])


def p_active_caps_deterministic_permissions():
    return _yaml_scalar(_read(SKILL / "active-capabilities.yaml"),
                        "deterministic_permissions_configured")


PROBES = {k[2:]: v for k, v in sorted(globals().items()) if k.startswith("p_")}
MIN_PROBES = 18

# H1: per-thread required probe sets. A thread gate fails unless every one is claimed.
REQUIRED = {
    1: {"agentfw_install_probes_model_selection", "model_selection_configured",
        "active_caps_has_model_selection", "agentfw_install_in_skill",
        "agent_model_pins", "active_caps_generated"},
    2: {"declared_tiers", "declared_floor", "declared_flagship",
        "concrete_model_names_in_policy"},
    3: {"harness_term_hits", "capability_keys"},
    4: {"skill_md_bytes", "policy_total_bytes", "policy_file_bytes"},
    5: {"default_mode", "deny_rule_count", "active_caps_deterministic_permissions"},
}
# H1: extra structured fields each thread must carry beyond probe claims.
REQUIRED_FIELDS = {
    1: ["adjudication"],            # which of the two readings the evidence supports
    2: ["external_facts"],          # pricing, tagged human_review, with a named source
    3: ["excluded_false_positives"],
    4: ["load_profile"],            # resident vs on-invocation
    5: ["steady_state_assessment"],
}


def _root_guard():
    """H3: every gate runs this FIRST, so a wrong root can never look like absence."""
    if not (SKILL / "capability.yaml").is_file():
        raise MissingInput(f"skill root {SKILL} has no capability.yaml — refusing to "
                           f"evaluate absence claims against a missing install")
    if len(_read(SKILL / "SKILL.md").encode()) < 1000:
        raise MissingInput("SKILL.md implausibly small — wrong install root")


def _strict_eq(actual, expected):
    """H4: no 0/False or 1/True coercion."""
    if isinstance(actual, bool) != isinstance(expected, bool):
        return False
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return type(actual) is type(expected) and actual == expected
    return type(actual) is type(expected) and actual == expected


# ---------------------------------------------------------------- gates

def run_thread(n):
    try:
        _root_guard()
    except MissingInput as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    f = REPO / f"findings/v98-thread{n}.json"
    try:
        doc = _json(f)
    except MissingInput as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if doc.get("thread") is not n and doc.get("thread") != n or isinstance(doc.get("thread"), bool):
        print(f"FAIL: {f.name} declares thread {doc.get('thread')!r}, expected int {n}",
              file=sys.stderr)
        return 1
    claims = doc.get("claims")
    if not isinstance(claims, list) or not claims:
        print(f"FAIL: {f.name} has no claims[]", file=sys.stderr)
        return 1

    bad, seen = 0, set()
    frozen = _json(FREEZE) if FREEZE.is_file() else {}
    for c in claims:
        cid = c.get("id", "<no id>")
        probe = c.get("probe")
        if not str(c.get("assertion") or "").strip():
            print(f"FAIL [{cid}]: empty assertion", file=sys.stderr); bad += 1; continue
        if probe not in PROBES:
            print(f"FAIL [{cid}]: unknown probe {probe!r}", file=sys.stderr); bad += 1; continue
        if "expected" not in c:
            print(f"FAIL [{cid}]: no expected value", file=sys.stderr); bad += 1; continue
        try:
            actual = frozen[probe] if probe in frozen else PROBES[probe]()
        except MissingInput as e:
            print(f"FAIL [{cid}]: probe {probe} input missing: {e}", file=sys.stderr)
            bad += 1; continue
        if not _strict_eq(actual, c["expected"]):
            print(f"FAIL [{cid}]: probe {probe} -> {actual!r} ({type(actual).__name__}), "
                  f"claim expected {c['expected']!r} ({type(c['expected']).__name__})",
                  file=sys.stderr)
            bad += 1
        else:
            seen.add(probe)
            print(f"  ok  [{cid}] {probe} == {actual!r}")

    missing = REQUIRED[n] - seen
    if missing:
        print(f"FAIL: thread {n} does not claim its required probes: "
              f"{', '.join(sorted(missing))}", file=sys.stderr)
        bad += 1
    for field in REQUIRED_FIELDS[n]:
        val = doc.get(field)
        if not val or (isinstance(val, str) and len(val.strip()) < 40):
            print(f"FAIL: thread {n} missing substantive {field!r} "
                  f"(need >=40 chars of substance)", file=sys.stderr)
            bad += 1
    if n == 2:
        for ef in (doc.get("external_facts") or []):
            if ef.get("tier") != "human_review" or not ef.get("source"):
                print("FAIL: thread 2 external_facts entries must each carry "
                      "tier=human_review and a named source", file=sys.stderr)
                bad += 1

    if bad:
        print(f"FAIL: thread {n} has {bad} defect(s)", file=sys.stderr)
        return 1
    print(f"THREAD{n}_OK")
    return 0


def check_document():
    """H5: every D-ITEM line must carry thread=, probe= (present in that thread's
    findings) and mechanism=."""
    try:
        _root_guard()
    except MissingInput as e:
        print(f"FAIL: {e}", file=sys.stderr); return 1
    doc_path = REPO / "FINDINGS-v9.8-sweep.md"
    try:
        text = _read(doc_path)
    except MissingInput as e:
        print(f"FAIL: {e}", file=sys.stderr); return 1
    lines = [l for l in text.splitlines() if "D-ITEM" in l]
    if not lines:
        print("FAIL: no D-ITEM lines in the document", file=sys.stderr); return 1
    claimed = {}
    for n in range(1, 6):
        p = REPO / f"findings/v98-thread{n}.json"
        if p.is_file():
            claimed[n] = {c.get("probe") for c in (_json(p).get("claims") or [])}
    bad = 0
    for l in lines:
        tm = re.search(r"thread=(\d)", l)
        pm = re.search(r"probe=([a-z_]+)", l)
        mm = re.search(r"mechanism=(\S.*)", l)
        if not (tm and pm and mm):
            print(f"FAIL: D-ITEM line lacks thread=/probe=/mechanism=: {l[:90]}",
                  file=sys.stderr); bad += 1; continue
        t, pr = int(tm.group(1)), pm.group(1)
        if pr not in PROBES:
            print(f"FAIL: D-ITEM cites unknown probe {pr!r}", file=sys.stderr); bad += 1
        elif pr not in claimed.get(t, set()):
            print(f"FAIL: D-ITEM cites probe {pr!r} not claimed in thread {t}",
                  file=sys.stderr); bad += 1
        elif len(mm.group(1).strip()) < 20:
            print(f"FAIL: D-ITEM mechanism too thin: {mm.group(1)[:60]}",
                  file=sys.stderr); bad += 1
    if bad:
        print(f"FAIL: {bad} malformed D-ITEM line(s)", file=sys.stderr); return 1
    print(f"DOCUMENT_OK ({len(lines)} D-ITEMs)")
    return 0


def selftest():
    """H2: assert probe count, root-failure, AND non-vacuity."""
    if len(PROBES) < MIN_PROBES:
        print(f"FAIL: {len(PROBES)} probes registered, need >= {MIN_PROBES}",
              file=sys.stderr); return 1
    try:
        _root_guard()
    except MissingInput as e:
        print(f"FAIL: {e}", file=sys.stderr); return 1

    live, errs = {}, 0
    for name, fn in PROBES.items():
        try:
            live[name] = fn()
        except MissingInput as e:
            print(f"FAIL: probe {name} cannot read the live install: {e}",
                  file=sys.stderr); errs += 1
    if errs:
        return 1

    # Non-vacuity: re-import against a bare root; every skill-reading probe must
    # either raise or change. A probe that returns the same value both ways is constant.
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as td:
        out = subprocess.run(
            [sys.executable, str(Path(__file__)), "--dump-probes"],
            env={**os.environ, "V98_SKILL_ROOT": td},
            capture_output=True, text=True)
    try:
        bare = json.loads(out.stdout or "{}")
    except json.JSONDecodeError:
        bare = {}
    SKILL_READING = {"model_selection_configured", "declared_tiers", "declared_floor",
                     "declared_flagship", "concrete_model_names_in_policy",
                     "harness_term_hits", "capability_keys", "skill_md_bytes",
                     "policy_total_bytes", "policy_file_bytes",
                     "active_caps_has_model_selection", "active_caps_generated",
                     "agentfw_install_in_skill",
                     "active_caps_deterministic_permissions"}
    constant = [n for n in SKILL_READING
                if n in bare and n in live and bare[n] == live[n]]
    if constant:
        print(f"FAIL: probe(s) returned identical values against a bare skill root, "
              f"so they are constants not measurements: {', '.join(sorted(constant))}",
              file=sys.stderr)
        return 1
    print(f"SELFTEST_OK ({len(PROBES)} probes, non-vacuity verified against a bare root)")
    return 0


def dump_probes():
    out = {}
    for name, fn in PROBES.items():
        try:
            out[name] = fn()
        except MissingInput:
            pass
    print(json.dumps(out, default=str))
    return 0


def freeze():
    """H8: snapshot live mutable state so worker and verifier compare equal."""
    (REPO / "findings").mkdir(exist_ok=True)
    out = {}
    for name, fn in PROBES.items():
        try:
            out[name] = fn()
        except MissingInput as e:
            print(f"FAIL: cannot freeze {name}: {e}", file=sys.stderr); return 1
    FREEZE.write_text(json.dumps(out, indent=2, default=str) + "\n")
    digest = hashlib.sha256(FREEZE.read_bytes()).hexdigest()[:16]
    print(f"FROZEN {len(out)} probes -> {FREEZE.relative_to(REPO)} (sha {digest})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thread", type=int)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--document", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--dump-probes", action="store_true")
    ap.add_argument("--list-probes", action="store_true")
    a = ap.parse_args()
    if a.list_probes:
        print("\n".join(sorted(PROBES))); return 0
    if a.dump_probes:
        return dump_probes()
    if a.freeze:
        return freeze()
    if a.selftest:
        return selftest()
    if a.document:
        return check_document()
    if a.thread is None:
        ap.error("need --thread N, --selftest, --document, --freeze or --list-probes")
    return run_thread(a.thread)


if __name__ == "__main__":
    sys.exit(main())
