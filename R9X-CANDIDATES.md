# r9.x improvements — implemented in v9.1.0

Completed list. Each entry retains the observed scenario, root cause, implemented fix, and landing
artifact. It started 2026-07-15 from the Bonksnake fixture-build gate exercise. The linked
[PLAN-bonksnake-fixture.md](PLAN-bonksnake-fixture.md) and
[PROMPTS-v9-paces.md](PROMPTS-v9-paces.md) are provenance only: the plan was halted at its gate by
maintainer decision after the 2-pass cap hit with open blockers; no workers were dispatched, the
Bonksnake target was not built, and the prompt battery was not executed for this v9.1.0 release.

Source run summary: A2 plan, dual review tier (validator-derived), 2 full dual judge passes
(4 `agentfw-plan-critic` runs), 3 plan revisions. **Every blocker across both passes was C2
command-strength class; decomposition/approach were judged clean throughout.** Judges found the
gaps by *executing* acceptance commands against hostile stubs, not by reading them.

---

## C-1 · Red-path self-probe of acceptance commands (producer-level, pre-Layer-2)

**Status:** implemented and verified · **Priority:** high · **Effort:** small (policy text) + medium (lint)

**Scenario (demonstrated):** rev 1 shipped commands that could neither pass on green nor fail on
red — `node --test ... | tail -n 4` masked the exit code AND the expected signal `# fail 0` never
appears in node v25.8.2's piped spec-reporter output. Rev 2 shipped levers that lived only in
criteria prose: a 2-line script hardcoding both output tokens satisfied T5's full acceptance
command without importing the code under test.

**Root cause:** the planner simulates command behavior in its head; judges execute it. Load-bearing
constraints drift into criteria prose with no command clause carrying them — the exact C2 failure
mode, produced twice in a row by a frontier model under a framework explicitly designed around C2.

**Fix:**
1. Playbook/prompt-design: before Layer-2 dispatch, the planner MUST red-path each
   acceptance_command — run it against at least one deliberately-broken stub (hardcoded tokens,
   empty test file, stale tag, seeded leak) and record the nonzero/red result. Signal rules:
   exit-code gated, no pipes before `&&`, terminal signal ordered last so every clause gates it.
2. Optional Layer-1 lint (validate-plan): deterministically flag known weak shapes — pipe before a
   gating `&&` (`| tail`, `| head`, `| grep` mid-chain), expected_signal emitted by an `echo` with
   no preceding gate, expected_signal not terminal in the chain. Layer 1 can't judge strength, but
   it can reject known-weak *shapes*.

**Lands in:** `references/prompt-design.md`, SKILL.md §3; optionally `tools/validate-plan`.

---

## C-2 · Mutation probes as first-class contract fields

**Status:** implemented and verified · **Priority:** high · **Effort:** medium (schema 1.3 + validator + verifier prompt)

**Scenario (demonstrated):** green signals reachable with hollow implementations — an empty test
file exits 0 under `node --test` (so `SIM_SUITE_GREEN` prints over a zero-test suite); a
self-attesting repro script passes its own output greps. The rev-3 fix was an ad-hoc 11-row
"contracted mutation probe" roster in dispatch prose: for each lever, a named mutation on a
scratch copy that MUST flip the command red, or the task is not verified.

**Root cause:** negative_cases describe assertions the command runs; nothing in the schema binds
"this command detects a broken implementation" — verification strength is unfalsifiable until a
judge hand-builds stubs.

**Fix:** add `mutation_probes[]` to Acceptance Contract (schema 1.3): each entry = {mutation,
expected: red}. Layer 1 requires ≥1 at integration seams and all A3+; the verifier executes them
on a scratch copy as a mandatory step, not dispatch-section prose.

**Lands in:** `policy/acceptance-contract.md`, `tools/validate-plan`, `agents/agentfw-verifier.md`.

---

## C-3 · Leak-channel checklist for fixture/eval-artifact builds

**Status:** implemented and verified · **Priority:** medium-high · **Effort:** small (new reference doc)

**Scenario (demonstrated):** fixture intent leaked through six channels beyond file contents, each
found by a judge probe: (1) committed checker scripts that grep for the planted payload; (2) file
NAMES (`repro-tunneling.js` in the tree hands the A3 subject the repro); (3) commit messages;
(4) the reflog — amended-away commits stay readable because `git worktree` forks share the `.git`
object store; (5) ref/tag names (`git tag -l` shows `v9-fixture` inside every probe worktree);
(6) worker-transcribed contract constraints ("do NOT add swept collision") and natural-reading
hint comments ("enemies faster than 1 cell/tick can pass through — fine for now").

**Root cause:** contamination guards default to file contents; the other channels are invisible
until someone attacks them. Also: the banned-word rule and the guard's grep patterns were two
artifacts with no identity assertion — they diverged (rule banned `fixture`; greps didn't match it).

**Fix:** a `references/fixture-hygiene.md` enumerating all channels (names / contents / messages /
refs / reflog / comments / committed tooling) with the guard patterns and the worker banned-word
rule generated from ONE list; validation tooling always lives outside the artifact under test;
append-only history; neutral ref names.

**Lands in:** new `references/fixture-hygiene.md`; cross-link from prompt-design.

---

## C-4 · Bake empirical probing into the plan-critic agent definition

**Status:** implemented and verified · **Priority:** medium · **Effort:** small

**Scenario (demonstrated):** ~all blocker-grade findings across 4 judge runs came from *executed*
probes (hostile stub vs T5's command; scratch repo vs T6's guard; reporter-format probe vs T1/T2
signals) — behavior elicited by dispatcher prompt emphasis ("empirically probe where feasible"),
not guaranteed by `agentfw-plan-critic.md` itself. A dispatcher who prompts lazily gets a
read-only judge and loses the entire defect class.

**Root cause:** judge empiricism is dispatch-prompt-dependent; the agent definition doesn't
require findings to cite live output.

**Fix:** `agentfw-plan-critic.md`: for C2, the judge SHOULD execute acceptance commands against
minimal hostile stubs where feasible and MUST tag each C2 finding as demonstrated (live output
quoted) or reasoned (no execution). Downstream, demonstrated findings are non-negotiable;
reasoned ones are contestable.

**Lands in:** `agents/agentfw-plan-critic.md`, `policy/plan-critique.md`.

---

## C-5 · Name the standard relaxation menu for cap-with-open-blocker escalations

**Status:** implemented and verified · **Priority:** medium · **Effort:** small

**Scenario (observed):** the 2-pass cap hit with open blockers while defect class was narrowing
monotonically (plumbing → enforcement gaps). Escalation fired correctly, but the human received an
ad-hoc option set invented on the spot (extend +1 pass / mutation-gated dispatch / halt) with no
policy backing for any of them.

**Root cause:** recovery policy defines the cap and the escalation but not the decision space at
the escalation point, so every cap escalation improvises its relaxations.

**Fix:** `policy/plan-critique.md` (or recovery.md) names the standard menu + criteria: (a) extend
by exactly one named pass when open blockers span multiple checks or any is non-C2; (b)
mutation-gated dispatch permitted only when ALL open blockers are C2-local AND each has a
contracted mechanical compensation (per C-2); (c) halt. Anything else remains a bespoke named
relaxation.

**Lands in:** `policy/plan-critique.md`, `policy/recovery.md`.

---

## C-6 · Preflight records resolved binaries for command-critical utilities

**Status:** implemented and verified · **Priority:** low · **Effort:** small

**Scenario (observed):** contract environment fields claimed "grep (macOS system utilities)"; a
judge found the live Bash-tool shell resolves `grep` to a ugrep 7.5.0 wrapper function —
behaviorally compatible for the flags used (verified by the judge), but the environment claim was
false as written, and an incompatible wrapper would have broken guard commands invisibly.

**Fix:** `agentfw-install status` (active-capabilities.yaml) additionally records
`command -v`/`type` resolution for utilities acceptance commands lean on (grep, sed, find, md5,
sqlite3), so environment fields cite the resolved reality.

**Lands in:** `tools/agentfw-install`, capability.yaml notes.
