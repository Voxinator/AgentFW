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
3. **Halt** is always eligible and is the default: preserve the blocker evidence and dispatch no
   worker.

The menu grants no authority by itself. Extending or dispatching requires the human to choose the
eligible option explicitly. Any other course is a **bespoke named relaxation** and must name the
waived invariant, exact scope, mechanical compensation, and termination condition before explicit
human authorization. Full gate semantics remain in [plan-critique.md](plan-critique.md).
