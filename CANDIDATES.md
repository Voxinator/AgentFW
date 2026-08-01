# CANDIDATES — rolling improvement ledger

This is the **single, permanent backlog** for AgentFW improvement candidates. It replaces the
per-release pattern (`R9X-CANDIDATES.md`, `R92-CANDIDATES.md`), which required a new file and a
rename every cycle. Those files remain as **frozen historical snapshots**; new candidates land
HERE, statuses flip HERE, and release notes snapshot whatever shipped.

**Rules of the ledger**
- Entry ids `D-N` are monotonic and never reused or renumbered. D-1–D-6 were born in
  [R92-CANDIDATES.md](R92-CANDIDATES.md); their full designs stay there, with status mirrored here.
- Every entry carries: `Status` (proposed | accepted | in-progress | SHIPPED in vX.Y.Z | rejected),
  `Origin` (the incident/analysis that produced it), `Evidence` (verbatim quotes + where to
  re-verify), `Problem`, `Proposed mechanism`, `Anchors` (the exact AgentFW files a build will
  touch), and `Cold-start verification` (commands a fresh session runs BEFORE planning, so it
  confirms the substrate instead of trusting this document or hallucinating it).
- Statuses are flipped by the maintainer or by the release that ships the entry; a shipped entry
  records the version, commit, and release-notes link.
- The maintainer calibration (2026-07-20) governs every entry: minimal safety floor, cheap
  human-held levers, economy as a first-class constraint —
  *"governance that is not economical does not get used, and an unused framework governs
  nothing."* Full text: [R92-CANDIDATES.md § Maintainer calibration](R92-CANDIDATES.md).

**⚠ Evidence-substrate warning for future sessions:** the D-7…D-13 evidence lives in
`/Users/briantaylor/Projects/NoitaMobileSpec` — a **local, unversioned working directory (NOT a
git repository; verified 2026-07-20: `git log` → `fatal: not a git repository`)**. It has no
history and may have changed since this ledger was written. The verbatim quotes below ARE the
durable record; the Cold-start verification commands tell you whether the live substrate still
matches. If it doesn't, trust the quotes as historical evidence and note the drift.

---

## Status board

| id | Title | Status |
|---|---|---|
| D-1 | Human delivery override (assumption-gated dispatch) | **SHIPPED in v9.2.0** @ `e59d6dc`/`3148554` — [notes](RELEASE-NOTES-v9.2.0.md), issue #7 closed |
| D-2 | Global liveness budget across plan cycles | **IMPLEMENTED on main** (unreleased) — build record below; issue #8 |
| D-3 | Inline recovery-menu surfacing in adapter skills | partially shipped in v9.2.0 (override path only); remainder accepted — issue #9 |
| D-4 | Fail visibly on install/policy drift (`ACTIVE_POLICY_STALE`) | accepted — issue #10 |
| D-5 | Governance-cost instrumentation (`PLANNING_LIVELOCK_RISK`) | accepted — issue #11 |
| D-6 | Reversible-prototype-treadmill regression eval | accepted; gates v9.2.x behavioral claims — issue #12 |
| D-7 | Plan-mass alarm (growth-under-critique trigger) | proposed — issue #13 |
| D-8 | Verification-cycle cap (judge/rejudge discipline) | proposed — issue #14 |
| D-9 | Version-control preflight (`workspace_versioned` probe) | proposed — issue #15 |
| D-10 | Confidence-class evidence vocabulary for research tasks | proposed — issue #16 |
| D-11 | Soak/duration probes as a named verifier duty | proposed — issue #17 |
| D-12 | Contract-prose proportionality (fixtures over criteria prose) | proposed — issue #18 |
| D-13 | Evidence lifecycle (judge scratch hygiene) | proposed — issue #19 |
| D-14 | Adaptive dispatch (flagship-cap model right-sizing) | **IMPLEMENTED on main** (ships with v9.3.0) — build [PLAN-v9.3-sleep-adaptive.md](PLAN-v9.3-sleep-adaptive.md) |
| D-15 | Sleep mode (unattended recommended-choice posture) | **IMPLEMENTED on main** (ships with v9.3.0) — build [PLAN-v9.3-sleep-adaptive.md](PLAN-v9.3-sleep-adaptive.md) |
| D-16 | Operator-relaxed enforcement (full-access / bypass as a declared lever) | **IMPLEMENTED on main** (unreleased) |
| D-17 | Cross-substrate consult (uncorrelated blocker-resolution lane) | proposed |
| D-18 | Post-gate scope freeze (next-increment ledger for late discoveries) | **IMPLEMENTED on main** (unreleased) — maintainer-approved 2026-07-31 |
| D-19 | Necessity tiers + C6 demote-duty (requirement-inflation defense) | **IMPLEMENTED on main** (unreleased) — maintainer-approved 2026-07-31 |
| D-20 | Operator digest (plain-language gate artifact + speak-twice rule) | **IMPLEMENTED on main** (unreleased) — maintainer-approved 2026-07-31 |
| D-21 | Delivery ledger, scoreboard & zero-dispatch tripwire | **IMPLEMENTED on main** (unreleased) — built 2026-08-01 |
| D-22 | Budget & ledger inheritance (`root_objective`) | **IMPLEMENTED on main** (unreleased) — built 2026-08-01 |
| D-23 | Increment-shape check + dependency-edge audit + partial dispatch | proposed |
| D-24 | Proof-cost inversion | **folded into D-21's rationale** — no standalone mechanism (see D-21) |
| D-25 | Session-start reconciliation (`RECONCILE` marker) | **IMPLEMENTED on main** (unreleased) — built 2026-08-01 |
| D-26 | Stranded-implementation disposition | proposed |
| D-27 | Blocker re-validation on age | proposed |

---

## Source analysis for D-7…D-13 (2026-07-20)

Retrospective of the **NoitaMobileSpec** build — a 3-day project (2026-07-18 → 07-20) produced by
Codex CLI (`gpt-5.6-sol` producers/judges) governed by an AgentFW r9 install, analyzed the day
v9.2.0 shipped. Companion record:
[the livelock field report](evaluation/field-report-2026-07-20-noita-planning-livelock.md)
(published with v9.1.1) covers the M2/M2A planning livelock; this analysis covers the whole
project, including the phases that SUCCEEDED.

**What the project is:** `/Users/briantaylor/Projects/NoitaMobileSpec` — a source-grounded spec +
implementation of a browser-playable Noita-inspired vertical slice. Layout (verified 2026-07-20):
`claims/ content/ evidence/ fixtures/ game/ inventories/ plans/ schemas/ sources/ tools/`.

**What got BUILT under governance (the record understates it):**
- Content-contract phase (t1–t8, 2026-07-18): canonical JSON mechanic ledgers with confidence
  classes; producer/judge cycles per ledger section.
- M0 (plan `plans/milestone-0-plan-v2.md`, 15,198 B, 7 tasks): a **1,330-line Rust simulation
  kernel** (`game/rust/src/lib.rs`, test module from line 1050) compiled to WASM and shipped at
  `game/public/wasm/noita_mobile_sim.wasm`, plus fixed-step scheduler, replay, service-worker
  cache (`game/src/runtime/`, `game/src/cache/`).
- M1 (plan `plans/milestone-1-visual-plan-v2.md`, 12,051 B, 4 tasks): renderer + presentation
  model with mutation-resistant acceptance (producer/judge/fix/rejudge logs `m1-v1*`–`m1-v3*` in
  `game/evidence/`, 89 files there total).
- M2/M2A: **planning only** — zero dispatched implementation workers; one excellent artifact,
  `plans/m2a-material-policy.canonical.json` (2,969 B: every contested ambiguity frozen into one
  digest-bound canonical policy).

**Headline numbers (all re-derivable; commands in the entries below):**
- Plan mass: M2 v1 `30,236 B / 5 tasks` → M2 v2 `48,742 B / 9 tasks` (**+61% bytes, +4 tasks
  under critique**) → M2A `19,245 B / 4 tasks`. Contrast M0: `15,198 B` shipped 1,330 lines of
  Rust.
- Verification vs production in the spec-phase evidence dir (`evidence/*.log`): **36 judge logs
  vs 27 producer logs; 32 rejudge/fix logs**. Worst case task t6 (Holy Mountain): **11 logs** —
  producer, judge, rejudge, rejudge2, rejudge3, fix cycles, `t6-fix4-strict-probe.py`,
  `t6-fix4-type-judge.log` (judges judging judges).
- Evidence pollution: `evidence/m0-t1-judge-tmp.DLprVu/` — **800 files of judge scratch**
  fossilized in the evidence directory.
- No VCS: the entire project, including the shipped kernel, has no git history.

**The single best governance moment in the record** (quote verbatim from
`game/evidence/` M0 release-judge log tail, 2026-07-19):

> VERDICT REJECTED
> REASON Live production persistence fails after approximately 2,730 simulation ticks (~45.5
> seconds), violating T5 persistence and therefore T7 clean integration acceptance despite the
> current verify:m0 command exiting 0.

The producer's contracted gate was green; the independent judge ran a live soak and caught a
production-shaped defect the contract never reached. This is the independent-verification tier
paying for itself in one line — and the origin of D-11.

**The honesty moment** (quote verbatim from `evidence/t6-producer.log` head, 2026-07-18):

> Native portal, rubble-settling, and guardian timing remain unresolved_no_trusted_capture.
> Native price distributions remain unresolved. Timing/prices unresolved.

Followed by an honest `REJECTED` — the evidence-class discipline kept hallucinated game
mechanics out of the canonical ledgers. Origin of D-10.

**Shared signature of everything wasteful:** unbounded recursion in a governance loop with no
mass, cycle, or substrate check. D-1 closed the human-facing case; D-7/D-8/D-9 close the three
remaining ones.

---

## D-7 · Plan-mass alarm (growth-under-critique trigger)

**Status:** proposed · **Priority:** high · **Effort:** small (policy + optional validator metric)

**Origin:** NoitaMobileSpec M2 planning spiral, 2026-07-19/20.

**Evidence (verbatim numbers, re-derived 2026-07-20):**
`plans/milestone-2-material-runtime-plan.md` = 30,236 B / 5 tasks →
`plans/milestone-2-material-runtime-plan-v2.md` = 48,742 B / 9 tasks →
`plans/milestone-2a-material-kernel-plan.md` = 19,245 B / 4 tasks. The v1→v2 revision — produced
*in response to critique* — grew the plan **+61% by bytes and +80% by task count**. The livelock
followed one plan-generation later. Contrast the healthy baseline: M0's 15,198 B plan shipped a
1,330-line kernel.

**Problem:** a revision that GROWS the plan is a critique gate functioning as a scope generator —
the leading indicator of livelock, visible a full cycle before D-2's pass/cycle budget would
trip. Nothing in current policy measures plan mass across revisions.

**Evidence update (2026-07-31):** the drydock failure-routing session
([field report](evaluation/field-report-2026-07-31-drydock-scope-accretion.md)) showed the same
accretion happening in *conversation before revision* — four requirement-births in ~35 minutes
on a Layer-1-PASSED plan, each ending "should be added to the plan." The default-route valve for
that case shipped as D-18 (post-gate scope freeze, 2026-07-31); D-7 remains the revision-time
mass alarm and is still worth building as the leading indicator.

**Proposed mechanism:** after each Layer-2-driven revision, compare the machine-readable block's
byte size and task count to the prior revision. Growth beyond a threshold (proposal: >25% bytes
or any net task increase during a *reduction* revision) forces the D-2 fork — rescope proposal /
D-1 override offer / halt — instead of another critique pass. Report the delta in the revision
record either way. Optional deterministic support: `tools/validate-plan` already parses the
block; a `--mass` flag emitting `bytes=N tasks=M` makes the comparison trivially scriptable.
NOT a floor item; the alarm forces the fork, the human still chooses.

**Anchors:** `policy/plan-critique.md` (post-blocker protocol + compose/stop section; interacts
with the D-2 design in [R92-CANDIDATES.md](R92-CANDIDATES.md) § D-2 — D-7 is the leading
indicator, D-2 the budget), `tools/validate-plan` (optional metric), both adapter SKILL.md
Layer-2 paragraphs.

**Cold-start verification:**
```sh
wc -c /Users/briantaylor/Projects/NoitaMobileSpec/plans/milestone-2-material-runtime-plan*.md \
      /Users/briantaylor/Projects/NoitaMobileSpec/plans/milestone-2a-material-kernel-plan.md
grep -c '"id": *"T\|"id":"T' /Users/briantaylor/Projects/NoitaMobileSpec/plans/milestone-2-material-runtime-plan-v2.md
```

## D-8 · Verification-cycle cap (judge/rejudge discipline)

**Status:** proposed · **Priority:** high · **Effort:** small-medium (policy)

**Origin:** NoitaMobileSpec content-contract phase, task t6 (Holy Mountain), 2026-07-18.

**Evidence (re-derived 2026-07-20):** in `/Users/briantaylor/Projects/NoitaMobileSpec/evidence/`:
36 `*.log` files containing "judge" vs 27 containing "producer"; 32 rejudge/fix logs. Task t6
alone: 11 logs — `t6-producer.log`, `t6-judge.log`, `t6-rejudge.log`, `t6-rejudge2.log`,
`t6-rejudge3.log`, fix-producer cycles, plus `t6-fix4-strict-probe.py` and
`t6-fix4-type-judge.log` — the last two being *meta-verification of the verifier*.

**Problem:** the plan gate has a hard 2-pass cap; **verification has no cap at all**. The same
unbounded-recursion dynamic the plan cap prevents exists on the verify side: judge → fix →
rejudge → stricter judge → judge-of-the-judge, open-ended. Some t6 churn was genuinely earned (it
ended in an honest REJECTED), but the tail was calibration churn with no convergence rule.

**Proposed mechanism:** per task, after N verification rounds (proposal: 3 — judge, fix+rejudge,
final rejudge) with the verdict still contested, STOP dispatching judges and escalate to the
human with the evidence trail — the same closed-menu shape as the plan-gate cap: (1) one named
final round, (2) D-1 override where the contested findings are assumption-class, (3) accept the
REJECTED verdict and re-plan, (4) halt. Safety floor unchanged: a verifier's floor-class finding
(destructive effect, security defect, vacuous command) is never talked down by round-counting —
the cap governs how long you can keep *re-litigating*, not what class of finding stands.

**Anchors:** `policy/plan-critique.md` (mirror of the cap language), `policy/acceptance-contract.md`
(verification-tier execution rules), `policy/recovery.md` §7 (menu cross-reference), both
SKILL.md verification paragraphs. Feeds D-5's counters (rounds-per-task is a first-class metric).

**Cold-start verification:**
```sh
ls /Users/briantaylor/Projects/NoitaMobileSpec/evidence/*.log | grep -c judge
ls /Users/briantaylor/Projects/NoitaMobileSpec/evidence/*.log | grep -c producer
ls /Users/briantaylor/Projects/NoitaMobileSpec/evidence/t6-*
```

## D-9 · Version-control preflight (`workspace_versioned` probe)

**Status:** proposed · **Priority:** high — safety-adjacent, not just economy · **Effort:** medium

**Origin:** NoitaMobileSpec entire project, discovered 2026-07-20.

**Evidence (verbatim, 2026-07-20):** `cd /Users/briantaylor/Projects/NoitaMobileSpec && git log`
→ `fatal: not a git repository (or any of the parent directories): .git`. A 3-day,
~31,000-file project — including a shipped WASM kernel and 95+ evidence logs — with **no version
control at any point**, built under a framework whose policy demands "rollback and recoverability
premises must be substrate-verified" (`policy/assurance-model.md`). Every plan-level backup claim
was hand-rolled file copies; nothing ever checked.

**Problem:** AgentFW's capability preflight probes command resolution (`grep`, `sed`, `find`,
`md5`, `sqlite3` — see `tools/agentfw-install status` output and `adapters/*/capability.yaml`)
but never asks whether the WORKSPACE is under version control. An unversioned workspace cannot
honestly satisfy any substrate-verified rollback premise, silently weakens every "trivially
reversible" Q1 answer in assurance derivation, and voids the reversibility assumptions D-1's
override and the destructive-effect rules both lean on.

**Proposed mechanism:** new capability key `workspace_versioned` with an activation probe
(`git -C <workspace> rev-parse --is-inside-work-tree` or platform equivalent). At A2+, an
unversioned workspace is a DECLARED degradation in the plan (existing degradation rules,
`policy/capability-contract.md`); any contract whose `risk`/rollback premise assumes revertibility
in an unversioned workspace is a Layer-2 C4 blocker. The skill SHOULD offer `git init` as the
first remediation (cheap, reversible, in-calibration). NOT a hard gate on A0/A1 work — economy.

**Anchors:** `policy/capability-contract.md` (10 capability keys + activation_probe pattern),
`adapters/claude-code/capability.yaml` + `adapters/codex/capability.yaml`,
`tools/agentfw-install` (status probe output + `active-capabilities.yaml` writer),
`tools/validate-capability` (schema — new key), `policy/assurance-model.md` (substrate-verified
rollback premises), both SKILL.md §0 capability preflights.

**Cold-start verification:**
```sh
git -C /Users/briantaylor/Projects/NoitaMobileSpec log --oneline 2>&1 | head -1   # expect: fatal
grep -n "activation_probe" /Users/briantaylor/Projects/AgentFW/adapters/claude-code/capability.yaml | head -3
tools/agentfw-install status | head -20   # from the AgentFW repo root; note NO workspace/VCS probe today
```

## D-10 · Confidence-class evidence vocabulary for research tasks

**Status:** proposed · **Priority:** medium · **Effort:** small (policy vocabulary + contract guidance)

**Origin:** NoitaMobileSpec content-contract phase — the part that WORKED.

**Evidence (verbatim from `evidence/t6-producer.log`, 2026-07-18):** "Native portal,
rubble-settling, and guardian timing remain unresolved_no_trusted_capture. Native price
distributions remain unresolved." — followed by an honest `REJECTED` rather than fabricated
mechanics. The project's claim system distinguishes (per its `plans/plan-critique.txt` and
`claims/`+`schemas/` dirs — read those for the exact enum): **official** (source-verified) /
**community_documented** (cross-checked community capture) / **implementation_decision**
(deliberately chosen, not claimed native) / **unresolved_no_trusted_capture** (honestly unknown).
Three days of adversarial game-mechanics research produced ZERO hallucinated facts in the
canonical ledgers.

**Problem:** AgentFW's evidence classes (`policy/acceptance-contract.md`) govern *machine-check*
evidence well, but research-shaped tasks (facts about an external system you don't control) have
no standard vocabulary for claim provenance. This field-proven taxonomy is better than anything
in `policy/` today, and it composes naturally with D-1: an `implementation_decision` is exactly a
recorded assumption + follow-up test wearing research clothes.

**Proposed mechanism:** adopt the four-class vocabulary into `policy/acceptance-contract.md` (or
a short `policy/research-evidence.md`) as the standard claim-provenance enum for research
deliverables: every factual claim in a research artifact carries a class; `official` and
`community_documented` require the capture/cross-check that earned them; `implementation_decision`
requires the decision record (D-1 ledger shape); `unresolved_no_trusted_capture` is always legal
and never blockable as "incomplete" — the honest-unknown class is what PREVENTS both
hallucination and research livelock. Verify the exact NoitaMobileSpec enum spelling from its
`claims/` + `schemas/` dirs before standardizing.

**Anchors:** `policy/acceptance-contract.md` (evidence classes), `policy/anti-patterns.md`
(the fabrication anti-pattern this prevents), both SKILL.md non-shell-work paragraphs.

**Cold-start verification:**
```sh
ls /Users/briantaylor/Projects/NoitaMobileSpec/claims/ /Users/briantaylor/Projects/NoitaMobileSpec/schemas/
grep -rn "unresolved_no_trusted_capture\|implementation_decision\|community" /Users/briantaylor/Projects/NoitaMobileSpec/schemas/ | head -5
```

## D-11 · Soak/duration probes as a named verifier duty

**Status:** proposed · **Priority:** medium-high · **Effort:** small (policy text)

**Origin:** the single best governance moment in the NoitaMobileSpec record.

**Evidence (verbatim from the M0 release-judge log in
`/Users/briantaylor/Projects/NoitaMobileSpec/game/evidence/`, 2026-07-19):**

> VERDICT REJECTED — REASON Live production persistence fails after approximately 2,730
> simulation ticks (~45.5 seconds), violating T5 persistence and therefore T7 clean integration
> acceptance **despite the current verify:m0 command exiting 0.**

**Problem:** the catch came from a live soak the judge improvised — no contract re-run would ever
have found a 45-second-in failure. `policy/plan-critique.md`'s "Contract-bounded verification has
a ceiling" already mandates off-contract hostile probes and names input-shaped ones (empty
inputs, duplicates, seeded content, bypass paths). The TIME axis — soak, endurance, cadence,
production-shaped duration — is not named, so whether it happens depends on judge imagination.

**Proposed mechanism:** add duration probes to the named off-contract probe families: for any
task whose deliverable RUNS (server, loop, simulation, cache, scheduler — mechanically: contracts
with non-empty `failure_surfaces`, or runtime-shaped `risk_class`/`environment`), the verifier at
independent+ tier SHOULD run at least one probe an order of magnitude longer than the acceptance
command's own horizon, and MUST record the duration it chose and why. Keep it SHOULD+record, not
MUST — economy; the record makes the omission visible instead of silent.

**Anchors:** `policy/plan-critique.md` ("Contract-bounded verification has a ceiling" section),
`policy/acceptance-contract.md` (verifier duties), `agentfw-verifier` agent definition
(`adapters/claude-code/agents/agentfw-verifier.md`).

**Cold-start verification:**
```sh
grep -rn "off-contract" /Users/briantaylor/Projects/AgentFW/policy/plan-critique.md | head -3
ls /Users/briantaylor/Projects/NoitaMobileSpec/game/evidence/ | grep -i "release-judge\|m0-t7"
```

## D-12 · Contract-prose proportionality (fixtures over criteria prose)

**Status:** proposed · **Priority:** medium · **Effort:** small (guidance) — larger if schema-enforced

**Origin:** NoitaMobileSpec M1 contracts vs the M2A canonical-policy artifact.

**Evidence (2026-07-20):** M1 v2 task criteria are single-sentence walls of hundreds of words
(see `plans/milestone-1-visual-plan-v2.md` T-V1/T-V2/T-V3 criteria; anchored signals like
`^PASS M1-V2 renderer: 7 painter layers, 3 quality tiers, 3 accessibility modes, readability
floors, and 10 mutants verified$`). It worked, but the contract prose became a second codebase —
maintenance and drift live there. Meanwhile the livelocked M2A session independently invented the
right pattern: `plans/m2a-material-policy.canonical.json` (2,969 B) — every contested specific
frozen into ONE digest-bound, machine-readable canonical artifact that contracts can reference by
digest instead of restating in prose.

**Problem:** C4 requires "harness proportional" but nothing prices contract prose; nothing steers
authors from 500-word criteria sentences toward versioned fixture/policy files.

**Proposed mechanism:** guidance in `policy/acceptance-contract.md` (+ prompt-design reference):
when criteria enumerate more than ~5 discriminating specifics, move the specifics into a
versioned, digest-referenced fixture/policy artifact (the M2A pattern; also the schema-1.4 ledger
pattern) and have the criteria assert conformance-to-artifact. Optionally: Layer-2 C4 flags
criteria beyond a soft length threshold as a concern (never a floor item).

**Anchors:** `policy/acceptance-contract.md`, `references/prompt-design.md` (verified present
2026-07-20), `policy/plan-critique.md` C4/C5 text.

**Cold-start verification:**
```sh
awk 'length($0)>500' /Users/briantaylor/Projects/NoitaMobileSpec/plans/milestone-1-visual-plan-v2.md | wc -l
head -c 400 /Users/briantaylor/Projects/NoitaMobileSpec/plans/m2a-material-policy.canonical.json
```

## D-13 · Evidence lifecycle (judge scratch hygiene)

**Status:** proposed · **Priority:** low · **Effort:** small

**Origin:** NoitaMobileSpec evidence directory, 2026-07-20.

**Evidence:** `evidence/m0-t1-judge-tmp.DLprVu/` — **800 files** of judge working scratch
fossilized inside the evidence directory (of 869 total files there, i.e. ~92% of the "evidence"
by file count is one leaked temp dir). Also: judge logs end with codex MCP auth-error noise
(`WARN codex_mcp::rmcp_client … Auth required`) — runtime noise inside evidence, the same
leak-channel class the 2026-07-13 publication-hygiene incident already documented for transcripts.

**Problem:** evidence directories have a hygiene rule for PUBLICATION
(`evaluation/eval-protocol.md`) but no lifecycle rule for the working set: scratch in, never out;
noise in, never scrubbed. Evidence quality degrades and honest audit gets harder — 800 junk files
bury 69 real logs.

**Proposed mechanism:** one short rule in `policy/acceptance-contract.md` (evidence section):
judge/producer scratch lives OUTSIDE the evidence store (scratch dirs; deleted or explicitly
archived on completion); evidence files are append-only, named by task+role+round, and a
completed milestone's evidence set is listed in a small manifest so leaks are detectable
(`ls | diff manifest -` is the whole audit). Feeds D-5's artifact counts.

**Anchors:** `policy/acceptance-contract.md` (evidence rules), `evaluation/eval-protocol.md`
(publication-hygiene precedent to mirror), agent definitions (worker/verifier scratch-path
instructions).

**Cold-start verification:**
```sh
find /Users/briantaylor/Projects/NoitaMobileSpec/evidence -type f | wc -l
find /Users/briantaylor/Projects/NoitaMobileSpec/evidence/m0-t1-judge-tmp* -type f 2>/dev/null | wc -l
```

---

## D-2 · Global liveness budget across plan cycles (build record)

**Status:** IMPLEMENTED on main (unreleased) · built 2026-07-31 · design of record:
[R92-CANDIDATES.md](R92-CANDIDATES.md) § D-2 · issue #8

**Origin:** maintainer field report 2026-07-31 — *"I can hit the two pass limit over and over
again"* on Codex; the needle only moved when Claude Code analyzed failures and drafted responses.

**Evidence:**
[field-report-2026-07-31-drydock-scope-accretion.md](evaluation/field-report-2026-07-31-drydock-scope-accretion.md)
(verbatim maintainer summary + drydock transcript quotes), plus the original NoitaMobileSpec
M2→M2A demonstration in [R92-CANDIDATES.md](R92-CANDIDATES.md) § D-2.

**Problem:** the 2-pass cap bounds each cycle but a fresh cycle resets it — *"bounded locally
and unbounded operationally"* — so the treadmill recurs at the objective level.

**Proposed mechanism (as built — matches the accepted design exactly):** review expenditure
accrues per OBJECTIVE — `cycles` and `layer2_passes`, budget **2 cycles / 4 Layer-2 passes** for
reversible A2 (A3/A4 may extend by exactly one named human-authorized cycle, once). A fresh plan
for the same objective never resets the counters; objective identity is declared honestly and
recorded in the `[LIVENESS: objective <slug> — cycle n/2, layer2 passes m/4]` marker trail. At
exhaustion, `[LIVENESS-EXCEEDED: …]` forbids further plan/critique cycles; the forced fork is
halt (open floor blocker, or human declines) / rescope proposal (C5 or unavailable substrate) /
**proactive** delivery-override offer. Sleep halts at exhaustion exactly as at the 2-pass cap.
**Build-scope note (recorded for the precedent):** the initial build folded a "scope freeze
after Layer 1" corollary into D-2 beyond the accepted design. During maintainer review it was
extracted to its own candidate, **D-18** — briefly on a misread of the maintainer's *"That
sounds like scope creep to me!"* (which described the drydock transcript's plan, not the
corollary) — and the maintainer then approved the mechanism explicitly ("I like your
suggestions"). Net result, kept deliberately: D-2 ships exactly as accepted, and the corollary
ships as D-18 with its own identity, evidence, and verification. New mechanisms get their own
ledger entries even when they ship the same day.

**Anchors:** [policy/plan-critique.md](policy/plan-critique.md) (§ Global liveness budget),
both adapter `SKILL.md` §3 (identical D-2 paragraph),
`evaluation/fixtures/liveness-budget.json` + `tools/check-liveness-invariants.py` (the D-12
fixture-over-prose pattern: exhausted ⇒ only halt/rescope/override-offer; same-objective never
resets; floor blocker at exhaustion ⇒ halt).

**Cold-start verification:**
```sh
python3 tools/check-liveness-invariants.py --selftest                       # LIVENESS_SELFTEST_OK
python3 tools/check-liveness-invariants.py evaluation/fixtures/liveness-budget.json  # LIVENESS_OK
grep -n "Global liveness budget" policy/plan-critique.md adapters/*/skills/agentfw/SKILL.md
```

## D-17 · Cross-substrate consult (uncorrelated blocker-resolution lane)

**Status:** proposed · **Priority:** medium · **Effort:** medium

**Origin:** maintainer field report 2026-07-31 (drydock) — the needle on Codex gate outcomes
moved only when the maintainer hand-carried blockers to Claude Code and pasted back its analysis.

**Evidence:** two independent signals in the
[field report](evaluation/field-report-2026-07-31-drydock-scope-accretion.md). (1) The
call-site-deletion mutation blind spot *"shipped twice in this repo and neither time was caught
by the verifiers, because the briefs told them to attack the helper"* — same-family producer and
verifiers share blind spots, so their failures are correlated. (2) The cross-substrate handoff
(Claude → GPT-5.6) is what carried the corrective lesson; the maintainer is currently the
transport layer.

**Problem:** when a producer fails the same rubric check across consecutive cycles, the
framework's only escalations are more same-family passes (correlated, empirically non-converging)
or human levers. The one empirically working remedy — consulting a different model family — has
no named step, so it costs manual ferrying and is invisible to the audit trail.

**Proposed mechanism (sketch, for maintainer review):** a named recovery escalation between
"another cycle" and "human override": when the same rubric check blocks across two cycles for one
objective, or at D-2 liveness exhaustion when the human extends, blocker-resolution routes to a
**consult context on a different substrate/model family** before any further same-family cycle.
The consult is input-curated like a judge (requirements + blockers + contracts, never the
producer's reasoning), produces a resolution draft the producer must adopt-or-rebut on the
record, and is marked `[CONSULT: cross-substrate — <blocker ids> → <substrate>]`. Adapter-side:
each capability instance declares whether a second substrate is reachable (e.g. Claude Code CLI
from Codex, `codex exec` from Claude Code) — degraded honestly to "human ferries the consult"
when absent, which is today's behavior made explicit. Open questions: does the consult count
against the D-2 budget (proposal: no — it resolves blockers, it doesn't re-review the plan);
tier/cost governance for the consult context (flagship-cap rules apply unchanged).

**Anchors (if accepted):** `policy/recovery.md` (the escalation), `policy/plan-critique.md`
(post-blocker protocol cross-reference), both adapter `capability.yaml` (consult-lane
declaration) + `SKILL.md`, `policy/capability-contract.md` (degradation rule).

**Cold-start verification:**
```sh
grep -n "shipped twice" evaluation/field-report-2026-07-31-drydock-scope-accretion.md
git -C /Users/briantaylor/Projects/drydock log --oneline -1 a191587   # transcript's cited fix exists
```

## D-18 · Post-gate scope freeze (next-increment ledger for late discoveries)

**Status:** IMPLEMENTED on main (unreleased) · maintainer-approved 2026-07-31 · **Effort:** small

**Origin:** extracted from the D-2 build, 2026-07-31, so the mechanism would carry its own
ledger identity rather than ride an accepted design; approved by the maintainer the same day
("I like your suggestions") after the drydock transcript showed the exact infestation it
prevents.

**Evidence:** drydock finding 1
([field report](evaluation/field-report-2026-07-31-drydock-scope-accretion.md)): four
requirement-births in ~35 minutes of post-Layer-1-PASS conversation, each ending "should be
added to the plan" — plus the Noita v1→v2 revision growing +61% bytes / +80% tasks under
critique (D-7's numbers). Every discovery defaulted INTO the gated plan; nothing in policy names
a different destination for it.

**Problem:** a gated plan has no scope boundary. Good design conversation after Layer-1 PASS
generates requirements faster than cycles close them, so the gate re-opens ever larger — the
accretion side of the treadmill, which D-2's budget bounds but does not prevent.

**Proposed mechanism (built):** requirements discovered AFTER a plan's Layer-1 PASS — in review,
conversation, or design exploration — default to a recorded **next-increment ledger** beside the
plan, never silently into the gated plan. Folding a discovery in is an explicit human choice
that reopens the gate and spends a cycle from the D-2 budget; the default is to ship the gated
increment and plan the discoveries against the next one. Same conversion discipline the D-1
override applies to waived blockers: growth becomes forward work, not plan mass. Interacts with
D-7 (the alarm) and D-2 (the budget); this is the valve.

**Anchors:** [policy/plan-critique.md](policy/plan-critique.md) (the "Scope freeze after
Layer 1" bullet in the D-2 liveness-budget section), both adapter `SKILL.md` §3 D-2 paragraphs,
`evaluation/fixtures/liveness-budget.json` (case `scope_reopened_after_layer1_pass`: reopening
is a NEW_CYCLE spend, counters never reset).

**Cold-start verification:**
```sh
grep -n "Scope freeze after Layer 1" policy/plan-critique.md
grep -n "next-increment ledger" adapters/claude-code/skills/agentfw/SKILL.md adapters/codex/skills/agentfw/SKILL.md
grep -n "scope_reopened_after_layer1_pass" evaluation/fixtures/liveness-budget.json
```

## D-19 · Necessity tiers + C6 demote-duty (requirement-inflation defense)

**Status:** IMPLEMENTED on main (unreleased) · maintainer-approved 2026-07-31 ("Yes absolutely")
· **Effort:** medium

**Origin:** maintainer design conversation 2026-07-31, immediately after the D-2/D-18 build:
*"there's probably different levels of justification.. like the feature wont pass or work
without this addition.. and then there's nice to haves.. and then there true fluff.. It seems
like AgentFW doesn't do anything to prevent from this kind of invention."*

**Evidence:** the drydock field report
([field-report-2026-07-31-drydock-scope-accretion.md](evaluation/field-report-2026-07-31-drydock-scope-accretion.md)):
four post-gate requirement-births, all defaulting inward, none carrying a necessity claim a
judge could attack. Structural cause: every gate check asks "what's missing?" (coverage);
nothing ever asks "would the objective fail without this?" — adding reads as diligence, cutting
is nobody's job, so the critique gate is a scope generator by construction.

**Problem:** requirements carry no necessity classification, so a judge cannot distinguish
load-bearing scope from invention, and no mechanism ever prunes.

**Proposed mechanism (built):** plan schema **1.5** (additive over 1.4; new schema of record).
Every requirement carries `necessity` ∈ `must` | `nice-to-have` | `fluff` (the maintainer's
three levels: won't work without it / nice to have / true fluff); a `must` also carries a
plain-language `because` naming the concrete failure without it. `validate-plan` enforces the
labels deterministically (new stable defect keyword `necessity`): unlabeled requirement,
unjustified must, and any task serving fluff are defects; coverage becomes tier-aware (an
uncovered nice-to-have is valid deferred scope — the block doubles as the D-18 next-increment
ledger); a task serving only nice-to-haves emits a non-fatal `scope note:`. Layer 2 gains **C6,
the anti-coverage check**: the judge independently attempts to name the failure behind every
must-claim; a claim that fails the attempt is **DEMOTED, not debated** — a scope correction,
never a blocker, never a re-plan trigger. Coverage stops under-building the musts; C6 stops
over-claiming them.

**Anchors:** `tools/validate-plan` (schema 1.5 + `--digest`), `tools/fixtures/plan-good-15-*` +
`plan-bad-15-*` + `plan-bad-14-carrying-15-field.md`, `tools/tests/validate-plan.sh`,
[policy/plan-critique.md](policy/plan-critique.md) (rule 15, C6, keyword contract), both adapter
`SKILL.md` §3, `adapters/claude-code/agents/agentfw-plan-critic.md` (C6 duty + verdict line),
both kernel bootloaders (C0–C6).

**Cold-start verification:**
```sh
bash tools/tests/validate-plan.sh                                    # ALL CHECKS PASSED
python3 tools/validate-plan tools/fixtures/plan-bad-15-must-no-because.md   # FAIL, necessity keyword
python3 tools/validate-plan --digest tools/fixtures/plan-good-15-necessity.md  # digest: must=2 ...
grep -n "C6 necessity audit" policy/plan-critique.md adapters/claude-code/agents/agentfw-plan-critic.md
```

## D-20 · Operator digest (plain-language gate artifact + speak-twice rule)

**Status:** IMPLEMENTED on main (unreleased) · maintainer-approved 2026-07-31 ("Yes absolutely")
· **Effort:** small (policy + adapter SKILL paragraphs; validator support ships with D-19)

**Origin:** the same 2026-07-31 conversation: *"the models don't always do a good job of
communicating what's going on IN ENGLISH.. it reads like internal chatter of the model to
itself - and much of it is not really easily parsed by the operator... even if I do read it -
I can't always clearly identify requirement inflation."*

**Evidence:** the framework's own output register — markers, rubric letters, candidate numbers
— is audit-speak addressed to a future grep, and nothing ever required an operator-readable
rendering. The one human lever the whole gate depends on (the maintainer spotting inflation and
deciding) was being fed machine-facing text.

**Problem:** governance output the operator cannot parse is governance that does not govern —
the economy calibration applied to language.

**Proposed mechanism (built):** every gate event (Layer-1 result, Layer-2 verdict, escalation
menu, override offer) is accompanied by a fixed-shape **operator digest** written for someone
who has never read the policy — no candidate numbers, rubric letters, or marker syntax: what
the plan builds; scope counts by necessity (musts / nice-to-haves built-vs-deferred / dropped),
which on schema 1.5 MUST match `validate-plan --digest` (a digest whose numbers differ from the
block is fiction); an ADDED/REMOVED delta since the last version, one plain line per change
with tier and "because" — the operator's inflation detector, with a new post-gate must-have
called out explicitly; review cost in plain numbers; and a one-line ask. Plus the
**speak-twice rule**: any marker the operator is expected to act on carries one plain sentence
beside it. Prose never overrides the block: where they disagree, the block is authoritative and
the mismatch is itself a defect.

**Anchors:** [policy/plan-critique.md](policy/plan-critique.md) (§ Operator digest),
`tools/validate-plan --digest` (the count oracle), both adapter `SKILL.md` §3 (identical
D-20 paragraph).

**Cold-start verification:**
```sh
grep -n "## Operator digest" policy/plan-critique.md
grep -n "speak-twice\|Speak twice" policy/plan-critique.md adapters/*/skills/agentfw/SKILL.md
python3 tools/validate-plan --digest tools/fixtures/plan-good-15-necessity.md  # the count oracle
```

## D-21 · Delivery ledger, scoreboard & zero-dispatch tripwire

**Status:** IMPLEMENTED on main (unreleased) · built 2026-08-01 · **Priority:** high ·
**Effort:** medium — build provenance:
[PLAN-v9.6-operator-compass.md](PLAN-v9.6-operator-compass.md)

**Origin:** maintainer field report 2026-08-01 — the **execution half** of the drydock
failure-routing workstream (the 2026-07-31 report covered the planning half). The operator spent
roughly two days, across BOTH runtimes, on one objective and did not know that zero features had
shipped.

**Evidence:**
[field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md).
Five review rounds on the receipt-authority sub-objective — one clause of 1 of 13 requirements;
**zero of 12 sibling tasks dispatched**; ~15 failure-routing commits, every one a governance
artifact (plans, authorizations, verdicts, handoffs) and none product behavior; the treadmill ran
across Claude Code AND Codex, each runtime restarting the counters. Maintainer's verbatim summary:
*"I've been on this treadmill with BOTH Claude code and yesterday and most of today with Codex..
on the same problem.. and not even aware that it hadn't produced a single fucking feature from the
plan"* — the delivered-feature count surfaced only after the operator asked three escalating times.

**Problem:** D-2 counts what review **spends**; nothing counted what the objective **delivers**.
That asymmetry is the treadmill's hiding place: every cycle is individually lawful, the budget
markers all read in-range, and an objective can burn its entire allowance with zero workers
dispatched and zero tasks verified, because no counter of delivered work exists to contradict the
review counters. Worse, the counters that did exist lived in the session — so a compaction, a new
session, or a runtime hop reset them to zero for free.

**Proposed mechanism (built):** three parts, one file. (1) **The durable ledger** —
`<plan>.ledger.json` beside the plan, belonging to the objective rather than the plan file:
`objective`, `root_objective`, `cycles`, `layer2_passes`, `workers_dispatched`, `tasks_verified`,
and an append-only `gate_events` list with **one entry per gate event, each naming the runtime
that wrote it**. Both runtimes read and update the same file; `cycles`/`layer2_passes` are D-2's
numbers — one ledger, not two. (2) **The scoreboard marker at EVERY gate event** —
`[SCOREBOARD: objective <slug> — musts built b/t · workers dispatched w · verified v · cycle n/2 ·
passes m/4]`, counts taken from the ledger and from `validate-plan --digest`, never from
narration; the D-20 operator digest must render it in plain language ("two review cycles so far;
nothing has been built yet"), and a gate event without the marker is a defect, not an omission.
(3) **The zero-dispatch tripwire** — two or more completed gate cycles with `workers_dispatched`
still 0 immediately force the D-2 exhaustion fork (proactive override offer / rescope / halt)
**even when liveness budget remains**; it latches (only dispatched work clears it), and it must
not fire below the threshold or after dispatch. Machine-checked as a decision table plus a ledger
shape record, the D-12 fixture-over-prose pattern.

**Rationale note — D-24 (proof-cost inversion) is FOLDED in here, not built separately.** The
observation from the same session: when the verification apparatus for an increment costs more
than directly reviewing the artifact it verifies, the correct move is to stop building apparatus.
It is a true diagnosis with **no mechanical rendering** — any cost threshold is a judgment about
the operator's currency, and a framework that guesses it would be inventing a velocity opinion
(explicitly out of scope, `PLAN-v9.6-operator-compass.md` § Deliberately out of scope). So D-24
keeps its ledger id for provenance but ships no standalone mechanism; the **zero-dispatch tripwire
is its enforceable shadow** — the one case where proof cost has provably overtaken delivery (two
complete review cycles of apparatus, zero dispatched work) is detected mechanically and forced to
a human fork.

**Anchors:** [policy/plan-critique.md](policy/plan-critique.md) (§ Delivery ledger, scoreboard &
zero-dispatch tripwire (D-21)), `evaluation/fixtures/delivery-ledger.json` (decision table +
`ledger_example` shape record), `tools/check-delivery-invariants.py` (stdlib;
`--selftest` proves red/green discrimination),
[PLAN-v9.6-operator-compass.md](PLAN-v9.6-operator-compass.md) +
`PLAN-v9.6-operator-compass.ledger.json` (the first ledger in the wild), both adapter
`SKILL.md` AGENTFW-SYNC blocks and both kernel bootloaders.

**Cold-start verification:**
```sh
python3 tools/check-delivery-invariants.py --selftest                                  # DELIVERY_SELFTEST_OK
python3 tools/check-delivery-invariants.py evaluation/fixtures/delivery-ledger.json
grep -n "SCOREBOARD\|zero-dispatch\|ledger.json" policy/plan-critique.md | head
python3 tools/check-candidates.py D-21 D-22 D-23 D-24 D-25 D-26 D-27            # CANDIDATES_OK
```

## D-22 · Budget & ledger inheritance (one ledger per root objective)

**Status:** IMPLEMENTED on main (unreleased) · built 2026-08-01 · **Priority:** high ·
**Effort:** small — build provenance:
[PLAN-v9.6-operator-compass.md](PLAN-v9.6-operator-compass.md)

**Origin:** the same 2026-08-01 field report — the drydock objective was decomposed into a
`receipt-authority` sub-objective that reviewed itself for five rounds while the 13 parent
requirements starved, and the same objective was then resumed in a second runtime that started
counting at cycle 1.

**Evidence:**
[field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md):
the treadmill ran across BOTH runtimes over ~2 days, **each restarting the counters**, on one
sub-clause of one requirement. D-2 shipped the no-reset rule as an honesty obligation on the
model's objective-identity declaration; decomposition, rename, and runtime hop were the three
cheap ways to satisfy the letter of it and still buy a fresh budget.

**Problem:** a per-objective budget that any decomposition, rename, or runtime hop can re-mint is
not a budget. The failure is not dishonesty — a sub-objective genuinely *is* a different
objective by name — it is that no rule said which ledger a derived objective spends from.

**Proposed mechanism (built):** the counters live in the durable D-21 ledger keyed by
**`root_objective`** — the root the work rolls up to, equal to `objective` when the objective *is*
the root. Every derived objective spends from the **root's** ledger, never a fresh one: a
sub-objective produced by decomposing the goal, a renamed or re-planned objective, and a
**cross-runtime resume** (Claude Code ↔ Codex, or a new session of either) all read the root
ledger, add to it, and write it back. Counters never reset on decomposition, rename, or a runtime
hop — those are exactly treadmill laundering. Liveness markers name the **root** slug, with the
sub-objective alongside if it differs (`<root-slug> (sub: <sub-slug>)`), so the marker trail
cannot show one rooted budget under two names; a resumed session reads the ledger before emitting
its first marker, and a missing/unreadable ledger is said out loud and re-derived, never restarted
at zero.

**Anchors:** [policy/plan-critique.md](policy/plan-critique.md) (§ Global liveness budget — the
"Budget & ledger inheritance — one ledger per root objective (D-22)" bullet),
`evaluation/fixtures/liveness-budget.json` (case `sub_objective_inherits_root_counters`),
`tools/check-liveness-invariants.py` (`REQUIRED_CASES` + rejection of any case naming a
`root_objective` while declaring `counters_reset: true`), both adapter `SKILL.md` §3.

**Cold-start verification:**
```sh
python3 tools/check-liveness-invariants.py --selftest                                    # LIVENESS_SELFTEST_OK
python3 tools/check-liveness-invariants.py evaluation/fixtures/liveness-budget.json      # LIVENESS_OK
grep -n "root_objective" policy/plan-critique.md evaluation/fixtures/liveness-budget.json | head
```

## D-23 · Increment-shape check + dependency-edge audit + partial dispatch

**Status:** proposed · **Priority:** high · **Effort:** medium (two critique checks + one
escalation option)

**Origin:** the 2026-08-01 drydock analysis — the shape of the plan, not the review of it, is what
guaranteed zero delivery.

**Evidence:** the drydock failure-routing plan serialized **all 12 sibling tasks behind one
sub-clause** of 1 of its 13 requirements; the receipt-authority sub-objective then absorbed five
review rounds, and because everything depended on it, nothing else could be dispatched. No check
in C0–C6 attacks dependency edges or the shape of the first increment — the gate can pass a plan
whose entire first wave is blocked behind a single contested node and never say so.
([field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md)).

**Problem:** the critique gate reviews requirement coverage, contract strength, and necessity, but
never asks *"what does the first dispatch wave actually deliver, and what is it hostage to?"* A
fully-serialized plan is indistinguishable at the gate from a deliverable one, so a single stuck
task starves the whole objective while every marker stays lawful.

**Proposed mechanism:** three related pieces, sized to be built together. (1) **Increment-shape
check** — the first dispatch wave must land at least one requirement END-TO-END; a plan whose
first wave delivers no complete requirement is flagged (concern, not floor) with the reshape named.
(2) **Dependency-edge audit** — a new Layer-2 duty (or a `validate-plan` metric) that reports the
dependency fan-in of the plan's most-depended-upon task and flags a wave where every task shares
one blocking ancestor. (3) **Partial dispatch as a named escalation option** — when one task is
blocked at the gate, the recovery menu offers dispatching the tasks NOT downstream of it, instead
of the current all-or-nothing hold. Interacts with D-21: partial dispatch is exactly what clears
the zero-dispatch tripwire honestly.

**Anchors (if accepted):** `policy/plan-critique.md` (new check + menu option),
`tools/validate-plan` (dependency-edge metric; `deps` are already parsed),
`policy/recovery.md` (partial-dispatch option in the blocked-task menu), both adapter
`SKILL.md` §3, `adapters/claude-code/agents/agentfw-plan-critic.md`.

**Cold-start verification:**
```sh
grep -n '"deps"' tools/validate-plan | head            # dependency edges are already parsed
grep -n "C6 necessity audit" policy/plan-critique.md   # the rubric this would extend
grep -n "12 sibling tasks\|serialized" evaluation/field-report-2026-08-01-drydock-zero-delivery.md
```

## D-24 · Proof-cost inversion (folded into D-21)

**Status:** **folded into D-21's rationale, 2026-08-01** — id retained for provenance; no
standalone mechanism will be built under this number.

**Origin:** the 2026-08-01 maintenance conversation, alongside D-21 — the observation that in the
drydock rounds the apparatus built to PROVE an increment repeatedly cost more than reading the
increment would have.

**Evidence:** the same execution-half record
([field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md)):
~15 commits of plans, authorizations, verdicts, and handoffs against zero product behavior. The
verification apparatus for one sub-clause outweighed the sub-clause by every available measure.

**Problem:** there is a real inversion point — beyond it, building more proof machinery is
strictly worse than direct human review of the artifact — and the framework has no way to notice
crossing it.

**Proposed mechanism (none — deliberately folded):** every rendering attempted required a cost
threshold, and any threshold the framework picks is a velocity/economics opinion it has no
standing to hold (the framework reports; it never optimizes — see
`PLAN-v9.6-operator-compass.md` § Deliberately out of scope). Rather than ship an unenforceable
SHOULD, the diagnosis is recorded inside **D-21's rationale**, and D-21's **zero-dispatch
tripwire is its enforceable shadow**: the single case where proof cost has provably overtaken
delivery — two complete review cycles, zero workers dispatched — is detected mechanically and
forced to a human fork. If a future session finds a mechanical rendering of the general case, it
gets a NEW id; this one stays closed so the ledger records the judgment, not a silent drop.

**Anchors:** [CANDIDATES.md](CANDIDATES.md) § D-21 (rationale note),
[policy/plan-critique.md](policy/plan-critique.md) (§ Delivery ledger — the tripwire),
[PLAN-v9.6-operator-compass.md](PLAN-v9.6-operator-compass.md) (§ Deliberately out of scope).

**Cold-start verification:**
```sh
grep -n "D-24" CANDIDATES.md                             # rationale note inside D-21 + this entry
grep -n "zero-dispatch tripwire" policy/plan-critique.md
```

## D-25 · Session-start reconciliation (`RECONCILE` marker)

**Status:** IMPLEMENTED on main (unreleased) · built 2026-08-01 · **Priority:** high ·
**Effort:** small (policy) — build provenance:
[PLAN-v9.6-operator-compass.md](PLAN-v9.6-operator-compass.md)

**Origin:** the 2026-08-01 field report — fresh drydock sessions inherited plan headers and
handoffs claiming progress while the repository contained zero implementation of the objective.

**Evidence:**
[field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md):
the two-day treadmill spanned multiple sessions and both runtimes; each new context started from
the previous context's CLAIMS. The operator's own count of delivered features could not be
recovered from any artifact — it had to be extracted by asking three escalating times.

**Problem:** a resumed context inherits the ledger's claims, not the world. A session that ended
mid-cycle, a compaction that dropped the last verdict, or a runtime hop that never saw the failing
run each leaves a ledger asserting counters and verified tasks the tree may no longer support.
Planning on top of a stale ledger is a late discovery waiting to happen, one gate cycle later and
with the evidence gone — and D-21's ledger, once durable, becomes exactly the artifact worth
lying to yourself with.

**Proposed mechanism (built):** a blocking four-step duty on resuming a gated **A2+** objective in
a context that did not itself record the ledger's latest state — before any new gate cycle, Layer-1
run, Layer-2 dispatch, or worker dispatch. (1) Read the ledger at its `root_objective` (D-22); a
missing or unreadable ledger is itself a MISMATCH, said out loud and re-derived, never restarted at
zero. (2) Re-derive observed state with **mechanical probes** — re-run the plan validator, check
that the evidence file each claimed-verified task names exists and is non-empty, grep the repo for
the claimed deliverables; a claim confirmed by reasoning is not confirmed. (3) Emit
`[RECONCILE: objective <slug> — ledger claims X, observed Y — MATCH|MISMATCH]` with the D-20
speak-twice plain sentence beside it. (4) On MISMATCH, correct the ledger FIRST — a claimed-verified
task whose acceptance evidence is absent reverts to unverified and `tasks_verified` decrements;
corrections may only move the ledger toward observed reality, never spend down `cycles` or
`layer2_passes` (that would make a resume a way to buy budget, the laundering D-22 closes).

**Anchors:** [policy/recovery.md](policy/recovery.md) (§ 8 Session-start reconciliation),
[policy/plan-critique.md](policy/plan-critique.md) (gate-entry cross-reference in the liveness
section: "Gate entry on a resumed objective — reconcile first (D-25)"), both adapter `SKILL.md`
AGENTFW-SYNC blocks, `evaluation/fixtures/reconcile.json` +
`tools/check-reconcile-invariants.py` (decision table added pre-release, closing the T3
verifier's "only new duty with no machine check" finding).

**Cold-start verification:**
```sh
grep -n "RECONCILE" policy/recovery.md policy/plan-critique.md | head
grep -n "MISMATCH" policy/recovery.md | head
grep -n "reconcile first" policy/plan-critique.md
python3 tools/check-reconcile-invariants.py --selftest
python3 tools/check-reconcile-invariants.py evaluation/fixtures/reconcile.json
```

## D-26 · Stranded-implementation disposition

**Status:** proposed · **Priority:** medium · **Effort:** small (policy rule)

**Origin:** the 2026-08-01 drydock analysis — working code built to satisfy a proof obligation,
reviewed twice, and then left where nothing could ship it.

**Evidence:** **1,300 working, twice-adversarially-reviewed lines** left in a fixtures directory
and never landed
([field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md)).
The lines existed, passed review, and contributed nothing to the delivered-feature count that
stayed at zero.

**Problem:** the framework has rules for code that fails review and rules for code that passes and
lands, but none for code that passes review in a location that is not the product — prototypes,
witness trees, fixture implementations, spike branches. Such work is invisible to every counter
(it is not `tasks_verified`, it is not delivery) and decays silently. D-21's scoreboard makes the
gap measurable; it does not say what to DO with the stranded work.

**Proposed mechanism:** a disposition rule — any implementation produced in a non-product location
that survives review carries an explicit, recorded disposition at the next gate event: **land** it
(with the task that will), **fold** it into the next-increment ledger (D-18) with the location, or
**discard** it (say so, so nobody re-derives it in a month). No disposition is a defect the same
way a missing scoreboard is. The rule should be cheap — one line per stranded artifact — and
should name the D-18 ledger as the default destination.

**Anchors (if accepted):** `policy/plan-critique.md` (D-18 next-increment ledger section — the
natural home), `policy/acceptance-contract.md` (evidence/scratch lifecycle, interacts with D-13),
`adapters/claude-code/agents/agentfw-implementer.md` (worker reports its stranded artifacts).

**Cold-start verification:**
```sh
grep -n "next-increment ledger" policy/plan-critique.md
grep -n "1,300\|stranded" evaluation/field-report-2026-08-01-drydock-zero-delivery.md
```

## D-27 · Blocker re-validation on age

**Status:** proposed · **Priority:** medium · **Effort:** small (policy rule)

**Origin:** the 2026-08-01 drydock analysis — the blocker list grew monotonically across five
rounds and nothing ever asked whether an old blocker still reproduced.

**Evidence:** **6 blockers accumulated over 5 review rounds** with no duty on anyone to
re-demonstrate that they still fail
([field-report-2026-08-01-drydock-zero-delivery.md](evaluation/field-report-2026-08-01-drydock-zero-delivery.md)).
Each round's fixes changed the artifact underneath the older findings, yet the older findings kept
their standing unexamined.

**Problem:** a blocker is a claim about a specific artifact state. Once the artifact changes, the
claim is stale — but the gate treats an open blocker as durable until someone argues it away.
Stale blockers are pure treadmill fuel: they keep an objective in review on evidence that may no
longer exist, and re-litigating them costs cycles D-2 charges to the objective.

**Proposed mechanism:** any blocker still open after N rounds (proposal: 2) must be
**re-demonstrated against the current artifact** — a recorded probe/command showing it still
fails — or it is DROPPED, in the same demote-not-debate spirit as D-19's C6. The re-demonstration
is the blocker-holder's duty, not the producer's rebuttal burden. Safety-floor findings are
exempt from dropping but not from re-demonstration: they stand, and their evidence is refreshed.
Interacts with D-8 (verification-cycle cap) — D-8 bounds how long you may re-litigate, D-27 bounds
how long a finding may coast.

**Anchors (if accepted):** `policy/plan-critique.md` (post-blocker protocol),
`policy/acceptance-contract.md` (verifier duties), both judge prompts
(`adapters/claude-code/agents/agentfw-plan-critic.md`, `agentfw-verifier.md`).

**Cold-start verification:**
```sh
grep -n "post-blocker\|Post-blocker" policy/plan-critique.md | head
grep -n "6 blockers" evaluation/field-report-2026-08-01-drydock-zero-delivery.md
```

## D-14 · Adaptive dispatch (flagship-cap model right-sizing)

**Status:** IMPLEMENTED on main (unreleased; ships with v9.3.0) · **Priority:** high · **Effort:** medium — build provenance: [PLAN-v9.3-sleep-adaptive.md](PLAN-v9.3-sleep-adaptive.md)

**Origin:** maintainer design session 2026-07-21 (the sleep-mode / adaptive-dispatch conversation), grounded in the standing economy calibration.

**Evidence:** the maintainer calibration (2026-07-20, [R92-CANDIDATES.md](R92-CANDIDATES.md) § Maintainer calibration): economy is "a first-class design constraint … the magic is in the middle." An orchestrator that clones its own premium tier onto every subagent pays flagship rates for mechanical work — the concrete cost this closes. Re-derivable: the v9.2 build fanned parallel workers all at one tier.

**Problem:** nothing let the orchestrator right-size a subagent's model to its task; every dispatch inherited one tier. There was no economic-escalation axis parallel to the effects axis (A0–A4), so buying an expensive model was ungoverned while deleting a file was heavily gated — an asymmetry against the economy calibration.

**Proposed mechanism (built):** **Adaptive** dispatch is the default — the orchestrator casts a per-subagent tier fit to the task; any tier below the adapter-declared flagship is free (incl. up-escalation), and casting **at or above the flagship** tier is an economic escalation requiring a genuine turn on the authenticated human channel (the D-1 channel, pointed at cost). The **judge of record is held at or above a declared floor tier** — economy never cheapens verification. **Uniform/Mirror** is the opt-out. The core stays **model-agnostic**: the adapter declares the concrete ladder in `model_selection.{tiers,flagship,floor}`; absent or unconfigured ⇒ honest degradation to Uniform. New 11th capability key `model_selection`, with validator-enforced sub-fields.

**Anchors:** [policy/model-dispatch.md](policy/model-dispatch.md) (new), [policy/capability-contract.md](policy/capability-contract.md) (11th key + degradation), `tools/validate-capability` (`SPEC_KEYS` + sub-field enforcement + `len()` counts), `adapters/*/capability.yaml` (`model_selection` block), `adapters/claude-code/agents/agentfw-{verifier,plan-critic,implementer}.md` (tier floor / adaptive), both adapter `SKILL.md` AGENTFW-SYNC block, [policy/assurance-model.md](policy/assurance-model.md) (verification-tier binding line).

**Cold-start verification:**
```sh
python3 tools/validate-capability adapters/claude-code/capability.yaml   # PASS — 11 declared
grep -n "model_selection\|MODEL_SELECTION_SUBFIELDS" tools/validate-capability | head
grep -ni "flagship\|floor tier\|Uniform" policy/model-dispatch.md | head
```

## D-15 · Sleep mode (unattended recommended-choice posture)

**Status:** IMPLEMENTED on main (unreleased; ships with v9.3.0) · **Priority:** high · **Effort:** medium — build provenance: [PLAN-v9.3-sleep-adaptive.md](PLAN-v9.3-sleep-adaptive.md)

**Origin:** maintainer design session 2026-07-21, as the interaction-axis twin of D-14.

**Evidence:** the same economy calibration plus the reversible-prototype-treadmill lesson (D-6): a human should be able to leave and have the agent keep delivering on recommended choices, without the framework either stalling or over-authorizing. The livelock incidents ([field report](evaluation/field-report-2026-07-20-noita-planning-livelock.md)) show the cost of a human who must babysit every fork.

**Problem:** the framework had two interaction postures (interactive-authenticated, headless) but no way for a present-then-absent human to pre-delegate the *recommended* resolution of ordinary forks while keeping the safety floor non-negotiable. Without it, unattended runs either stall at every fork or an ad-hoc "just proceed" launders authorization the floor reserves.

**Proposed mechanism (built):** a third **unattended (sleep) posture**. Entered by a genuine authenticated-channel human turn with a scope; entry itself is the (non-standing) authorization. While asleep, the agent auto-takes the **recommended** option at NON-floor forks (`[AUTO-CHOICE: sleep …]`) and, at any FLOOR blocker, behaves exactly like a headless run — halt/degrade, record, wait (`[SLEEP-HALT: floor <class> — awaiting human]`) — because auto-accept is standing text, which is never authorization. The floor is non-delegable (the six safety-floor classes **plus** the D-14 flagship escalation); the plan-critique cap and the D-1 override stay **human-only levers** sleep never auto-pulls. The floor-halt invariant is machine-checked by a decision-table fixture + checker (the D-12 fixture-over-prose pattern), so "sleep HALTS at the floor" is falsifiable, not prose. Truly-unattended resumption depends on `scheduled_resume` (partial/unverified on both runtimes ⇒ present-but-AFK is the supported variant).

**Anchors:** [policy/assurance-model.md](policy/assurance-model.md) (the posture, beside headless), [policy/recovery.md](policy/recovery.md) + [policy/plan-critique.md](policy/plan-critique.md) (cap stays human-only under sleep), both adapter `SKILL.md` AGENTFW-SYNC block + kernel blocks, `tools/check-posture-invariants.py` + `evaluation/fixtures/sleep-posture.json` + [evaluation/eval-v9.3-sleep-adaptive.md](evaluation/eval-v9.3-sleep-adaptive.md).

**Cold-start verification:**
```sh
python3 tools/check-posture-invariants.py --selftest        # POSTURE_SELFTEST_OK
python3 tools/check-posture-invariants.py evaluation/fixtures/sleep-posture.json
grep -n "Unattended (sleep) posture\|SLEEP-HALT" policy/assurance-model.md | head
```

## D-16 · Operator-relaxed enforcement (full-access / bypass as a declared lever)

**Status:** IMPLEMENTED on main (unreleased) · **Priority:** high · **Effort:** small

**Origin:** maintainer field report 2026-07-31 — a Codex install with `sandbox_mode =
"danger-full-access"` could not get any AgentFW plan past the gate, while the Claude Code
runtime under `bypassPermissions` continued fine. The maintainer's stated intent: recommend the
floor, then move on; the framework must never pester an operator who chose relaxation for a
long-running project.

**Evidence:** `adapters/codex/capability.yaml` (pre-fix) probed `sandbox_mode present and not
"danger-full-access"` for both `filesystem` and `deterministic_permissions`, each `required_for`
A2+/A3+; the capability contract's gating rule made those tiers "unreachable" when not ACTIVE;
plan-critics then mapped the condition to safety-floor item 5 ("unavailable required substrate"),
which is never waivable — a hard block with no human lever. The Claude Code adapter escaped only
by omission: its probe checked deny-rule *presence* in settings and never read the active
permission mode. Grounding for the bypass residuals: https://code.claude.com/docs/en/permissions
("Skips permission prompts" + its listed exceptions); deny-rule/hook behavior under bypass is
undocumented and therefore never claimed.

**Problem:** a deliberate operator relaxation (full access / bypass permissions) was classified
as *missing substrate*, converting a human-held economic choice into an unwaivable blocker on
one runtime and an unexamined silence on the other. Both violate the calibration: minimal safety
floor, cheap human-held levers, recommend-then-move-on.

**Proposed mechanism (built):** the capability contract now distinguishes **unconfigured** (never
activated ⇒ gates as absent, unchanged) from **operator-relaxed** (an explicit relaxed mode in
live config ⇒ a standing human lever). Operator-relaxed handling is fixed at four steps:
recommend the floor ONCE at plan time; declare `[FLOOR-RELAXED: operator — <mode>]` citing
documented residuals only; compensate behaviorally (destructive/irreversible/outward effects
gate on a genuine human turn — already A3/A4 policy — and workers keep explicit side-effect
budgets); PROCEED — never Layer-2 material, never safety-floor item 5, never re-raised per task.
Sleep/headless posture is unchanged: floor blockers still halt; relaxation never widens what an
unattended run may auto-take. Both adapters' probes now resolve relaxed modes to this rule
symmetrically.

**Anchors:** [policy/capability-contract.md](policy/capability-contract.md) (§ Operator
relaxation), `adapters/codex/capability.yaml` (`filesystem` + `deterministic_permissions`
probes), [adapters/codex/config.example.toml](adapters/codex/config.example.toml),
[adapters/codex/AGENTS.md](adapters/codex/AGENTS.md) + both adapter `SKILL.md` §0/§4,
`adapters/claude-code/capability.yaml` (bypass residuals, honestly bounded),
[adapters/claude-code/CLAUDE-block.md](adapters/claude-code/CLAUDE-block.md).

**Cold-start verification:**
```sh
python3 tools/validate-capability adapters/codex/capability.yaml          # PASS
python3 tools/validate-capability adapters/claude-code/capability.yaml    # PASS
grep -n "Operator relaxation is a lever" policy/capability-contract.md
grep -rn "FLOOR-RELAXED" adapters/ | wc -l                                # ≥ 6 sites
```

---

## What the analysis says AgentFW already does well (keep; do not "fix")

For balance, and so future sessions don't invent problems: the independent-verification tier
caught a production-shaped defect the producer's green gate missed (D-11 quote); the
evidence-class discipline produced zero fabricated mechanics across three days of adversarial
research (D-10 quote); the early plan gate caught vacuous spec validation
(`plans/plan-critique.txt`, C0/C2/C3 blockers — the same C2 class the v9.2.0 build's own gate
caught twice); and the M2A session, even mid-livelock, produced the canonical frozen-policy
artifact that D-12 and schema 1.4 now generalize. The waste was never in verification quality —
it was in unbounded governance loops, which D-1 (shipped), D-2 (accepted), and D-7/D-8/D-9
(proposed) close.
