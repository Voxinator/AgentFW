# Recovery — the Decision Model

Failures are expected; the assurance model exists because one-shot perfection is unrealistic. The
platform (where one exists) supplies the rollback mechanics — checkpoints, isolated workspaces,
journals. This policy supplies the DECISION: what failed, what it contaminated, and which action fits.
Don't patch forward blindly — an error midway propagates through everything downstream.

## 1. Scope the failure

| Scope | Definition | Example |
|---|---|---|
| **local** | defect contained in one work item; its contract was right | a failing unit test inside the item's own files |
| **contract** | the work is faithful to its acceptance contract, but the contract was wrong or too weak | the acceptance command passed while the requirement's real lever was never exercised |
| **architectural** | the decomposition or approach is wrong; multiple items inherit the flaw | two "independent" tasks turn out to share a hidden seam and produce contradictory changes |
| **environmental** | the substrate changed or lied | a dependency upgrade broke the build; flaky infrastructure; credentials expired mid-run |

## 2. Blast radius & contamination
Before acting, enumerate what the failure invalidates: downstream items built on the failed one, AND
evidence recorded under the now-false assumption. **Invalidate explicitly, never silently** — mark each
contaminated item and evidence artifact in the authoritative store with the reason. A verdict recorded
against a broken contract is contaminated even when the work item itself happens to be fine.

## 3. Retry budget
**Max 2 retries per failure without a fresh context.** A third attempt in the same context is the same
context making the same mistake with more conviction. A fresh context is not amnesia: it carries forward
the requirements, the findings so far, and the assumptions that FAILED — never the accumulated
in-context state that produced the failure. Restart with the lesson, not the mess.

## 4. Late-discovery rule
An error surfacing after multiple unverified steps is **architectural regardless of apparent severity**
— e.g., a build attempted after three unverified changes reveals a defect from step one. Do not fix
forward across unverified work. Roll back to the last verified checkpoint and re-plan with the findings
as input. The error itself is the smaller problem: it signals a missing verification gate. Record which
steps lacked verification, and close that gate before dispatching anything else.

## 5. Fix forward vs. roll back
Rollback is not automatically the safe choice — it can be the destructive one (unwinding a partially
applied external effect, discarding verified work bundled with the failure). **Fix forward** when the
failure is local, the blast radius is fully enumerated, and the fix is itself verifiable. **Roll back**
when contamination is uncertain, when unverified work has accumulated (rule 4), or when the failed step
is cheap to replay. Decide on contamination, not on sunk cost — in either direction.

## 6. Action set

| Action | When |
|---|---|
| **fix_forward** | local scope; enumerated blast radius; verifiable fix |
| **redispatch** | local/contract scope with retry budget remaining — same task, fresh context, lesson attached |
| **replan** | contract or architectural scope — the plan or contract is the defect; fix it before dispatching any worker against it |
| **rollback** | contamination uncertain, or unverified work accumulated — return to the last verified checkpoint |
| **escalate** | environmental scope beyond declared control; retry budget exhausted; any irreversible or out-of-scope step — STOP and hand the decision up |

Every recovery decision is recorded in the authoritative store — scope, contamination, action, lesson —
so a later context inherits the conclusion, not the investigation.

## 7. Plan-gate cap recovery

When the Layer-2 plan-critique cap is reached with an open blocker, stop and escalate. The standard
recovery menu is deliberately closed:

1. **Extend the gate by exactly one named Layer-2 pass** only when open blockers span multiple
   rubric checks or any open blocker is non-C2. The human authorization names the pass. It is one
   complete pass at the previously derived judge count, cannot become an open-ended retry, and cannot
   be extended again.
2. **mutation-gated dispatch** only when every open blocker is C2-local and every blocker has a
   one-to-one contracted, mechanically executable `mutation_probes` compensation with expected result
   red. The independent verifier executes all such probes on fresh scratch copies. A non-C2 blocker,
   a missing mapping, a prose-only check, or an unexecutable mutation makes this option ineligible.
3. **assumption-gated dispatch (human delivery override)** on a genuine human delivery-intent turn
   ("implement now", "stop reviewing", or equivalent) — available at any point after Layer-2
   findings exist, not only at the cap. Safety-floor blockers are never waivable and stay
   dispatch-blocking; every other open blocker converts to a recorded assumption plus a required
   follow-up test in the affected task's contract, and one subsequent genuine human confirmation
   turn dispatches immediately. Full semantics — the trigger duty, the six-item safety floor,
   provenance, the audit marker, waived-stays-waived — live in
   [plan-critique.md](plan-critique.md).
4. **Halt** is always eligible and is the default: preserve the blocker evidence and dispatch no
   worker.

The menu grants no authority by itself. Extending or dispatching requires the human to choose the
eligible option explicitly. Any other course is a **bespoke named relaxation** and must name the
waived invariant, exact scope, mechanical compensation, and termination condition before explicit
human authorization. Full gate semantics remain in [plan-critique.md](plan-critique.md).

Under the **unattended (sleep) posture** (`assurance-model.md`) this menu stays human-only: the cap
is a governance-cost decision the paying human must make, so a session in sleep mode selects the
default (**Halt**, option 4) and waits — it never auto-selects option 1/2/3, which require an
explicit authorized turn. Sleep mode auto-advances only non-floor recovery (local/contract-scope
retries), never a cap escalation, a destructive gate, or a flagship model escalation.

## 8. Session-start reconciliation — read the ledger before the next gate cycle (D-25)

A resumed context inherits the ledger's CLAIMS, not the world. The claims are cheap to trust and
cheap to be wrong: a session that ended mid-cycle, a compaction that dropped the last verdict, a
runtime hop that never saw the failing run — each leaves a `<plan>.ledger.json`
(`plan-critique.md` § Delivery ledger, D-21) asserting counters and verified tasks that the tree
may no longer support. Planning on top of a stale ledger is the late-discovery rule (§4) waiting
to happen, one gate cycle later and with the evidence gone.

**When the duty fires.** On resuming a gated **A2+ objective** in a context that did not itself
record the ledger's latest state — a new session, recovery after compaction, or a runtime hop
(Claude Code ↔ Codex) — and BEFORE any new gate cycle for that objective. It is the first gate
event's precondition, not a step inside it. No new plan, no Layer-1 run, no Layer-2 dispatch, and
no worker dispatch precedes it.

**The duty, in order — all four steps are blocking:**

1. **Read the ledger.** Load the objective's `<plan>.ledger.json` at its `root_objective` (D-22):
   `cycles`, `layer2_passes`, `workers_dispatched`, `tasks_verified`, and `gate_events`. A
   missing or unreadable ledger is itself a MISMATCH result — say so and re-derive, never restart
   the counts at zero.
2. **Re-derive observed state with mechanical probes, never from narration or memory.** At
   minimum: re-run the plan validator (`tools/validate-plan` over the plan's block) for the
   plan's current Layer-1 status; check that the **evidence file each claimed-verified task
   names actually exists** and is non-empty; and grep the repo for the deliverables those tasks
   claim to have produced. The probes are commands with recorded output — a ledger claim
   confirmed by reasoning is not confirmed.
3. **Emit the marker,** naming the root objective slug and both sides of the comparison:
   `[RECONCILE: objective <slug> — ledger claims X, observed Y — MATCH|MISMATCH]`
   Per the speak-twice rule (`plan-critique.md` § Operator digest, D-20) the marker carries one
   plain sentence beside it, e.g. "the record says three tasks were verified; the evidence file
   for one of them is missing, so it counts as unverified again."
4. **On MISMATCH, correct the ledger FIRST.** Planning may not continue until the ledger reflects
   observed reality; the correction is never made alongside a new cycle, in parallel with
   planning, or deferred to the next gate event. Specifically: **a claimed-verified task whose
   acceptance evidence is absent reverts to unverified** in the ledger, and `tasks_verified` is
   decremented to match. Corrections may only move the ledger toward observed reality —
   reconciliation never spends down `cycles` or `layer2_passes` (that would make a resume a way
   to buy budget, the laundering D-22 closes). Append the correction as a `gate_events` entry
   naming this runtime, then re-emit the marker; the cycle begins only once it reads MATCH.

A MATCH is recorded the same way and costs nothing further — the ledger stood up to its probes,
and the objective proceeds to its gate cycle with counters intact.

**Why blocking.** Reconciling alongside the new cycle means the cycle's first decisions are made
on the unreconciled claims — the defect the duty exists to catch escapes into exactly the plan
built to act on it, and the resulting work is contaminated under §2 rather than prevented.

**Machine check.** The duty's decision rules are encoded as a decision table
(`evaluation/fixtures/reconcile.json`, enforced by `tools/check-reconcile-invariants.py`): a
MISMATCH row that proceeds, an absent-evidence claim declared MATCH or left verified, or a
correction that spends down `cycles`/`layer2_passes` is rejected — the same fixture-plus-checker
discipline as D-2 and D-21.
