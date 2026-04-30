# PHASE-AWARENESS-NOTE — proposed addendum to DESIGN-r7.11-architecture.md

**Author**: r7.11 item-2 worker, 2026-04-26.
**Status**: proposal for the planner to consider; not landed in the design doc.

## Issue

DESIGN §3 specifies tier-2 import resolution checks "imports resolve against project + venv" but does not specify behavior when verifying phase N of a multi-phase project where a later phase will write the import target. The worked example: phase 1 writes `src/export/csv.py` which does `from src.export.formats import Formatter`; phase 2 writes `src/export/formats.py`. At phase-1 verify time, `formats.py` does not yet exist on disk. A naive resolver fails phase 1, even though PLAN.md is internally consistent and the project will work once both phases run.

## Recommendation

**Land the addendum in §3, immediately after the verification-tiers table, as a new sub-section titled "Phase-awareness in tier-2 import resolution."** §3 is where the verifier's behavior is specified, and tier-2 is the only tier where this matters; §4 is about state artifacts and shouldn't carry verifier semantics. Co-locating the rule with the tier-2 row keeps the doctrine where a future implementer of tiers 3 or 3.5 will read it.

## Draft text (paste-ready)

> ### Phase-awareness in tier-2 import resolution
>
> When `verify_phase` is called on phase N, it receives the full phase plan from PLAN.md (the `project_phases` list). The verifier computes a *tolerated-deferred set* equal to the union of declared paths from all phases other than N. An import in a phase-N file whose target resolves to a path in the tolerated-deferred set is recorded as `deferred (declared in phase M)` and does NOT cause `passed=false`. Imports that don't resolve project-relative, don't resolve via `importlib.util.find_spec`, and aren't in the tolerated set remain integrity issues.
>
> This is what makes the verifier sound when phases write disjoint pieces of a single import graph. Worked example: phase 1 writes `src/export/csv.py` which does `from src.export.formats import Formatter`; phase 2 writes `src/export/formats.py`. At phase-1 verify time, `formats.py` is not yet on disk, but it is declared in phase 2's paths — the verifier defers the import and passes phase 1. At phase-2 verify time, `formats.py` IS on disk, so the import resolves project-relative directly. Phase ordering matters only for what's already on disk; the verifier's pass/fail signal is invariant under it as long as `project_phases` is provided.
>
> Resolution is project-relative first, venv second; ambiguity is resolved by taking the most-specific module/package match under `scaffold_root`. The verifier never executes user code — `find_spec` is metadata-only.
