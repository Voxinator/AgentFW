# Track B-2a — content-type semantic break

**Question (Brian's 2a):** Does verifier-from-orchestrator-context catch a
semantic concern, or does the orchestrator's bias toward dispatch
interpretation affect what gets flagged?

**Concrete break:** `/api/export.json` returns `Content-Type: text/csv`.
Endpoint name promises one thing; response declares another. A contract
violation tier 3.5 *should* flag.

## Test design (DRAFT — review before authoring)

Two control issues to address:

1. **Worker non-determinism.** If we let a normal worker implement phase 1
   and *hope* it produces the broken content-type, we don't have a clean
   test. The break has to be deterministic.

2. **Orchestrator-bias surfacing.** Brian's question is whether the
   orchestrator's dispatch-bias filters tier 3.5's finding when it routes.
   That requires the orchestrator to see the verdict and decide.

**Proposed mechanism** (cleanest): pre-stage the broken implementation in
`src/api/export.py` as if a worker had just produced it. Phase 1's
delegate_task context says: *"Implementation already drafted in
src/api/export.py — confirm files in place, run pytest, return without
modifying impl files."* This makes the worker deterministic. The
orchestrator then runs `verify_phase(tier=3.5)` and reads the verdict.

What we measure:
- Did tier 3.5 emit a semantic concern about the content-type mismatch?
- Did the orchestrator advance to phase 2 anyway (dispatch-bias) or halt?
- Did the orchestrator's terminal message reflect the concern or paper over it?

Cross-validates Track C: this scaffold's trajectory feeds adherence.py and
will surface narrative-routing if present.

## What this directory needs (TODO before running 2a)

- `USER-PROMPT.md` — task description biased toward "json export endpoint"
  (so semantic concern is salient)
- `verify-config.json` — sets tier 3.5 active for phase 1
- `src/api/export.py` (pre-staged) — the broken impl (pseudo-code below)
- `tests/test_api_export.py` (pre-staged) — passing pytest that doesn't
  exercise content-type assertion (so tier 3.7 is happy and the contract
  bug only surfaces at tier 3.5)
- Worker context override that says "impl already in place; just confirm"

## Pre-stage candidate (sketch — not yet written)

```python
# src/api/export.py
from fastapi import APIRouter, Response

router = APIRouter()

@router.get("/api/export.json")
def export_json():
    payload = "id,name\n1,alice\n"
    return Response(content=payload, media_type="text/csv")  # ← contract violation
```

Test passes (returns 200 with body), but content-type is wrong for the
endpoint name.

## Brian's call (2026-05-03)

Pre-stage broken impl + worker-confirms-only. **Refinement:** the worker
delegate_task context must say *"verify the existing implementation
matches the spec"*, NOT *"create the file"*. This avoids the worker
accidentally rewriting broken code into correct code, which would defeat
the test. The broken `src/api/export.py` stays byte-identical across trials.

Concrete worker-context override (used by run-trial.sh when `--track B-2a`):

> Scaffold root: {scaffold_root}. The implementation at
> `src/api/export.py` was authored by a prior session. Your job: verify
> that the file exists, that the test suite at `tests/` passes, and
> return. Do NOT modify `src/api/export.py`. Do NOT rewrite it. Do NOT
> "improve" it. If a test fails, report the failure and stop — do not
> attempt to fix the implementation.
