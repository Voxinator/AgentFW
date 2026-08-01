# Field report — drydock scope accretion & the cap treadmill (2026-07-31)

**Reporter:** maintainer (Brian), 2026-07-31, with a pasted transcript excerpt from a drydock
planning session (Wednesday evening, `docs/failure-routing-plan.md` on
`/Users/briantaylor/Projects/drydock`). Companion to the
[Noita planning-livelock report](field-report-2026-07-20-noita-planning-livelock.md) — same
treadmill, two new mechanisms visible.

**Maintainer's summary (verbatim):** *"it seems like I can hit the two pass limit over and over
again.. and it seems like unless I'm passing the failures over to Claude Code for analysis and
having claude code draft my responses.. the needle on passing these gates never moves."*

**Evidence-substrate note:** the transcript was pasted into an AgentFW maintenance conversation;
the verbatim quotes below ARE the durable record. The referenced drydock repo is local and IS a
git repository (verified 2026-07-31); the cold-start commands confirm the named artifacts still
exist.

## Finding 1 — post-gate scope accretion (D-7's trigger, D-2's scope-freeze case)

The plan had **Layer-1 PASS** and main as a clean basis at the session's start (10:05 PM). Over
the following ~35 minutes of product Q&A — each answer individually high-quality — four separate
requirement-births landed on the already-gated plan:

1. 10:22 PM — the agent itself: *"Two important gaps in the current plan"* (Architect
   reachability from a loaded failed plan; how a `p-2` revision rejoins the live plan) — *"I
   would add those two acceptance requirements before calling the end-to-end user journey fully
   specified."*
2. 10:32 PM — *"the plan needs an explicit requirement to project failureKind into the Plan
   Board/card data and render it on the story row."*
3. 10:36 PM — *"This consolidation should become an explicit UI requirement in the plan."*
   (the unified Resolve… dialog)
4. 10:39 PM — *"This session-retirement behavior is another requirement that should be added to
   the plan; F4 currently requires a fresh agent in the existing worktree but does not
   explicitly require terminating the previous writer."*

Every discovery defaulted INTO the gated plan. A plan that re-enters Layer 2 materially larger
presents fresh surface, yields fresh blockers, and hits the 2-pass cap again — the cap is
per-cycle, so the treadmill is structural. This is the same signature as Noita's v1→v2 revision
(+61% bytes / +80% tasks under critique) one level earlier: here the growth happened in
*conversation before revision*, which D-7's revision-time mass comparison would catch only at
the next gate entry.

## Finding 2 — correlated-verifier blind spot (D-17 evidence)

From the Claude-drafted handoff at the top of the transcript (carrying lessons to the GPT-5.6
session): *"The mutation that must go red for F1 and F2 is deleting the call site, not breaking
the function; that exact blind spot shipped twice in this repo and neither time was caught by
the verifiers, because the briefs told them to attack the helper."*

Same-family producer and verifiers shared the blind spot twice; the correction traveled only via
a cross-substrate handoff. Combined with the maintainer's summary (Claude-drafted responses are
what move Codex gate outcomes), this is direct evidence that same-family review failures are
correlated and a different model family resolves what sibling cycles cannot.

## Finding 3 — the ferrying is manual

The working remedy today is the maintainer hand-carrying blockers between runtimes. The
framework has no named step for it; the human is the transport layer.

## Disposition

- **D-2 (global liveness budget)** — BUILT 2026-07-31 in response to this report, exactly as
  accepted: per-objective cycle/pass budget, no-reset rule, forced fork at exhaustion. See
  `policy/plan-critique.md` § Global liveness budget; decision table
  `evaluation/fixtures/liveness-budget.json` enforced by `tools/check-liveness-invariants.py`.
- **D-18 (post-gate scope freeze)** — BUILT 2026-07-31 as the valve for Finding 1, with its own
  ledger identity (extracted from the D-2 build during review, then maintainer-approved the same
  day). Post-Layer-1 discoveries default to a next-increment ledger; folding one in spends a
  D-2 cycle. See CANDIDATES.md § D-18.
- **D-7 (plan-mass alarm)** — this report added as evidence; still proposed (issue #13). D-18
  is the valve; D-7 remains the leading-indicator alarm at revision time.
- **D-17 (cross-substrate consult)** — newly proposed from Finding 2/3; see CANDIDATES.md.

## Cold-start verification

```sh
ls /Users/briantaylor/Projects/drydock/docs/failure-routing-plan.md   # plan artifact exists
git -C /Users/briantaylor/Projects/drydock log --oneline -1 a191587    # QUESTION_RE fix cited in transcript
python3 tools/check-liveness-invariants.py evaluation/fixtures/liveness-budget.json  # LIVENESS_OK
grep -n "Global liveness budget" policy/plan-critique.md
```
