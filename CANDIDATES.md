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
| D-2 | Global liveness budget across plan cycles | accepted (design in [R92-CANDIDATES.md](R92-CANDIDATES.md)) — issue #8 |
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
