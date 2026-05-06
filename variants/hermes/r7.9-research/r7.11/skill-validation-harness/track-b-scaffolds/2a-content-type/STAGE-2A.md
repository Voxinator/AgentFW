# How 2a is staged

`run-trial.sh --track B-2a` does:

1. `reset.sh <work>` — pristine baseline + py3.11 venv (per Track A)
2. `pip install fastapi httpx` into the venv (the broken impl + tests need them)
3. `cp -R overlay/* <work>/` — drops in:
   - `USER-PROMPT.md`: "verify, don't modify" task description
   - `PLAN.md`: pre-staged phase 1 (verify-only) — pre-flight 2b determines whether this is honored
   - `verify-config.json`: tier 3.5 active (`runtime_smoke_test_default: true`)
   - `src/api/export.py`: broken impl (JSON-named endpoint, text/csv response)
   - `tests/test_api_export.py`: weak tests that pass on broken impl
4. SHA the broken `src/api/export.py` → record in manifest as `pre_staged_sha256`
5. Drive skill via `launch-tui.py`
6. After completion: re-SHA `src/api/export.py` → record as `final_sha256`. **If they differ, the worker rewrote the implementation — flag in manifest as a worker-context-failure** (Brian's specific concern).

Comparing pre/post SHA gives a deterministic check: did the worker
preserve the byte-identical broken impl across the trial?

## Pre-staged PLAN.md decision (per pre-flight 2b)

If pre-flight 2b shows:
- **(a) graceful skip** — leave `PLAN.md` in overlay; skill uses it as-is
- **(b) overwrite-with-error** — strip `PLAN.md` from overlay; let
  orchestrator author. Test relies on USER-PROMPT.md being clear enough
  (it is: "Single-phase task: verify, do NOT modify")
- **(c) hard error** — strip `PLAN.md` AND prepend wrapper prompt:
  *"PLAN.md exists at <path>; start from PHASE LOOP step 1."*
